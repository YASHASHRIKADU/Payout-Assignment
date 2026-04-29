"""
Payout API views — the most critical part of the system.
"""
import logging

from django_q.tasks import async_task
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.idempotency import service as idempotency_service
from apps.merchants.models import Merchant
from core.exceptions import MissingIdempotencyKeyError
from .models import Payout
from .serializers import PayoutCreateSerializer, PayoutResponseSerializer
from .services import create_payout

logger = logging.getLogger(__name__)


class PayoutCreateView(APIView):
    """
    POST /api/v1/payouts/

    Creates a new payout request following this strict flow:
      1. Validate Idempotency-Key header.
      2. Check idempotency cache → return cached response if hit.
      3. Validate request body.
      4. Call create_payout() — acquires row lock, checks balance, writes atomically.
      5. Enqueue process_payout Django-Q task.
      6. Store idempotency response.
      7. Return 201.
    """

    def post(self, request):
        # ── Step 1: Require Idempotency-Key header ───────────────────────────
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            raise MissingIdempotencyKeyError()

        # ── Step 2: Check idempotency cache ─────────────────────────────────
        merchant_id_raw = request.data.get("merchant_id")
        if merchant_id_raw:
            cached = idempotency_service.get_cached_response(
                merchant_id_raw, idempotency_key
            )
            if cached is not None:
                logger.info(
                    "Returning cached response for idempotency key '%s'.",
                    idempotency_key,
                )
                return Response(cached, status=status.HTTP_200_OK)

        # ── Step 3: Validate request body ────────────────────────────────────
        serializer = PayoutCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        merchant_id = serializer.validated_data["merchant_id"]
        amount_paise = serializer.validated_data["amount_paise"]

        # Ensure merchant exists (raises 404 if not).
        Merchant.objects.get(id=merchant_id)

        # ── Step 4: Atomic create (lock → balance check → debit) ─────────────
        payout = create_payout(
            merchant_id=str(merchant_id),
            amount_paise=amount_paise,
            idempotency_key=idempotency_key,
        )

        # ── Step 5: Enqueue background task ──────────────────────────────────
        async_task(
            "apps.payouts.tasks.process_payout",
            str(payout.id),
        )
        logger.info("Queued process_payout task for payout %s.", payout.id)

        # ── Step 6: Build response and store in idempotency cache ─────────────
        response_data = PayoutResponseSerializer(payout).data
        # Convert UUIDs / datetimes to strings for JSON storage.
        response_data = dict(response_data)
        response_data["id"] = str(response_data["id"])
        response_data["merchant"] = str(response_data["merchant"])

        idempotency_service.store_response(
            merchant_id=str(merchant_id),
            key=idempotency_key,
            response_data=response_data,
        )

        # ── Step 7: Return 201 ───────────────────────────────────────────────
        return Response(response_data, status=status.HTTP_201_CREATED)


class PayoutListView(generics.ListAPIView):
    """
    GET /api/v1/merchants/<merchant_id>/payouts/

    Returns all payouts for a merchant (most recent first).
    """
    serializer_class = PayoutResponseSerializer

    def get_queryset(self):
        merchant_id = self.kwargs["merchant_id"]
        return Payout.objects.filter(merchant_id=merchant_id)


class PayoutDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/payouts/<payout_id>/

    Returns a single payout record.
    """
    serializer_class = PayoutResponseSerializer
    queryset = Payout.objects.all()
    lookup_field = "id"
