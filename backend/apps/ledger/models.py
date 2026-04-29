from django.db import models
from apps.merchants.models import Merchant
from core.constants import LEDGER_TYPE_CHOICES


class LedgerEntry(models.Model):
    """
    Immutable double-entry ledger record.
    Every financial event (credit or debit) creates one row.
    Balance = SUM(credits) - SUM(debits) via DB aggregation.
    """
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.PROTECT,
        related_name="ledger_entries",
    )
    type = models.CharField(max_length=10, choices=LEDGER_TYPE_CHOICES)
    # Store in paise (integer) — NEVER use float
    amount_paise = models.BigIntegerField()
    # Unique external reference (payout_id, seed_id, etc.)
    reference_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["merchant", "type"]),
        ]

    def __str__(self):
        return (
            f"LedgerEntry({self.type} | {self.amount_paise} paise "
            f"| merchant={self.merchant_id})"
        )
