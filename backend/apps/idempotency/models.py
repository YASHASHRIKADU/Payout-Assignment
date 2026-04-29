from django.db import models
from django.utils import timezone
from apps.merchants.models import Merchant


class IdempotencyKey(models.Model):
    """
    Stores the response for a given (merchant, idempotency_key) pair so that
    duplicate requests return identical responses.
    Keys automatically expire after IDEMPOTENCY_TTL_HOURS (24 h).
    """
    merchant = models.ForeignKey(
        Merchant,
        on_delete=models.CASCADE,
        related_name="idempotency_keys",
    )
    key = models.CharField(max_length=255)
    # The exact JSON response body that was returned for this key.
    response = models.JSONField()
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "idempotency_keys"
        # DB-level uniqueness — prevents race condition duplicates.
        unique_together = [("merchant", "key")]
        indexes = [
            models.Index(fields=["expires_at"]),
        ]

    def is_valid(self) -> bool:
        """Return True if this key has not yet expired."""
        return timezone.now() < self.expires_at

    def __str__(self):
        return f"IdempotencyKey({self.key} | merchant={self.merchant_id})"
