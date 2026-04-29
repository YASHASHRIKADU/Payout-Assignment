import uuid
from django.db import models
from apps.merchants.models import Merchant
from core.constants import PAYOUT_STATUS_CHOICES, PAYOUT_PENDING


class Payout(models.Model):
    """
    Represents a single payout request. Follows a strict state machine:
    pending → processing → completed | failed
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.PROTECT,
        related_name="payouts",
    )
    # Amount in paise — NEVER use float
    amount_paise = models.BigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=PAYOUT_STATUS_CHOICES,
        default=PAYOUT_PENDING,
        db_index=True,
    )
    retry_count = models.PositiveSmallIntegerField(default=0)
    # Idempotency key supplied by the caller (unique per merchant enforced below)
    idempotency_key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payouts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "status"]),
            models.Index(fields=["status", "updated_at"]),
        ]

    def __str__(self):
        return f"Payout({self.id} | {self.status} | {self.amount_paise} paise)"
