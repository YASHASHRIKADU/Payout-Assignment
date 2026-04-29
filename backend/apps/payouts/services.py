"""
Payout service layer — contains all critical business logic.
All money operations run inside atomic transactions with row-level locking.
"""
import logging
import uuid

from django.db import transaction
from django.db.models import Sum

from apps.ledger.models import LedgerEntry
from apps.merchants.models import Merchant
from core.constants import (
    LEDGER_CREDIT,
    LEDGER_DEBIT,
    PAYOUT_COMPLETED,
    PAYOUT_FAILED,
    PAYOUT_PENDING,
    PAYOUT_PROCESSING,
)
from core.exceptions import InsufficientBalanceError
from core.utils import calculate_balance, validate_state_transition
from .models import Payout

logger = logging.getLogger(__name__)


def create_payout(merchant_id: str, amount_paise: int, idempotency_key: str) -> Payout:
    """
    Atomically:
    1. Lock the merchant row (SELECT FOR UPDATE) — blocks concurrent requests.
    2. Derive balance via DB aggregation.
    3. Reject if balance insufficient.
    4. Create Payout (pending).
    5. Create LedgerEntry (debit).

    Returns the new Payout instance.
    """
    with transaction.atomic():
        # Lock the merchant row — serialises concurrent payout requests for this merchant.
        merchant = (
            Merchant.objects.select_for_update().get(id=merchant_id)
        )

        # Derive available balance inside the lock.
        balances = calculate_balance(merchant_id)
        available = balances["available_balance"]

        logger.info(
            "Payout attempt: merchant=%s amount=%d available=%d",
            merchant_id,
            amount_paise,
            available,
        )

        if available < amount_paise:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {available} paise, "
                f"Requested: {amount_paise} paise."
            )

        # Create the payout record.
        payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=amount_paise,
            status=PAYOUT_PENDING,
            idempotency_key=idempotency_key,
        )

        # Immediately deduct funds via a ledger debit so the balance reflects
        # the held amount straight away (no double spend window).
        LedgerEntry.objects.create(
            merchant=merchant,
            type=LEDGER_DEBIT,
            amount_paise=amount_paise,
            reference_id=f"payout_debit_{payout.id}",
        )

        logger.info("Payout %s created and debit ledger entry written.", payout.id)

    return payout


@transaction.atomic
def transition_payout(payout: Payout, new_status: str) -> Payout:
    """
    Move a payout to a new status, enforcing the state machine.
    Uses select_for_update to prevent concurrent workers from double-processing.
    """
    # Re-fetch with a row lock inside this transaction.
    payout = Payout.objects.select_for_update().get(id=payout.id)
    validate_state_transition(payout.status, new_status)
    payout.status = new_status
    payout.save(update_fields=["status", "updated_at"])
    return payout


@transaction.atomic
def refund_payout(payout: Payout) -> None:
    """
    Atomically reverse a failed payout by adding a credit ledger entry.
    Called when a payout transitions to FAILED.
    """
    payout = Payout.objects.select_for_update().get(id=payout.id)

    # Guard: only refund if actually failed.
    if payout.status != PAYOUT_FAILED:
        logger.warning(
            "refund_payout called on payout %s with status %s — skipping.",
            payout.id,
            payout.status,
        )
        return

    LedgerEntry.objects.create(
        merchant_id=payout.merchant_id,
        type=LEDGER_CREDIT,
        amount_paise=payout.amount_paise,
        reference_id=f"payout_refund_{payout.id}",
    )
    logger.info(
        "Refund credit of %d paise issued for payout %s.", payout.amount_paise, payout.id
    )
