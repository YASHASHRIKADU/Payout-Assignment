from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, status

from apps.merchants.models import Merchant
from core.utils import calculate_balance
from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


class BalanceView(APIView):
    """
    GET /api/v1/merchants/<merchant_id>/balance/

    Returns the merchant's available and held balances derived from
    DB aggregations — balance is NEVER stored.
    """

    def get(self, request, merchant_id):
        # Raise 404 if merchant doesn't exist.
        Merchant.objects.get(id=merchant_id)
        balances = calculate_balance(merchant_id)
        return Response(
            {
                "merchant_id": str(merchant_id),
                "available_balance": balances["available_balance"],
                "held_balance": balances["held_balance"],
            }
        )


class LedgerEntryListView(generics.ListAPIView):
    """
    GET /api/v1/merchants/<merchant_id>/ledger/

    Returns all ledger entries for a merchant (most recent first).
    """
    serializer_class = LedgerEntrySerializer

    def get_queryset(self):
        merchant_id = self.kwargs["merchant_id"]
        return LedgerEntry.objects.filter(merchant_id=merchant_id)
