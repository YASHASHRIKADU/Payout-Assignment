"""
Idempotency service — safely stores and retrieves idempotency keys.
Uses DB unique_together as the ultimate race-condition guard.
"""
import logging
from datetime import timedelta

from django.db import IntegrityError
from django.utils import timezone

from core.constants import IDEMPOTENCY_TTL_HOURS
from core.exceptions import IdempotencyConflictError
from .models import IdempotencyKey

logger = logging.getLogger(__name__)


def get_cached_response(merchant_id: str, key: str):
    """
    Return the stored response for this (merchant, key) pair if it exists
    and has not expired. Returns None otherwise.
    """
    try:
        record = IdempotencyKey.objects.get(merchant_id=merchant_id, key=key)
    except IdempotencyKey.DoesNotExist:
        return None

    if not record.is_valid():
        # Key exists but expired — treat as new request.
        logger.info("Idempotency key '%s' has expired. Treating as new request.", key)
        return None

    logger.info("Idempotency cache hit for key '%s'.", key)
    return record.response


def store_response(merchant_id: str, key: str, response_data: dict) -> None:
    """
    Persist the response for this (merchant, key) pair.
    Silently ignores duplicate writes (another thread stored it first).
    Raises IdempotencyConflictError if the key exists but has a different response.
    """
    expires_at = timezone.now() + timedelta(hours=IDEMPOTENCY_TTL_HOURS)
    try:
        IdempotencyKey.objects.create(
            merchant_id=merchant_id,
            key=key,
            response=response_data,
            expires_at=expires_at,
        )
    except IntegrityError:
        # Race condition: another concurrent request stored the same key.
        # This is safe — both requests will return the same response
        # (the first one to commit wins).
        logger.warning(
            "Idempotency key '%s' already stored by a concurrent request.", key
        )
