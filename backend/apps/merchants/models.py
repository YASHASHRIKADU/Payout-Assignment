import uuid
from django.db import models


class Merchant(models.Model):
    """
    Represents a merchant (freelancer/agency) in the payout system.
    Balance is NEVER stored here — it is derived from LedgerEntries.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "merchants"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Merchant({self.name})"
