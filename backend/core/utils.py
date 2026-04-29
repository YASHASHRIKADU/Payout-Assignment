"""
Shared utility functions for the Playto Payout Engine.
"""
from django.db.models import Sum

from core.constants import (
    LEDGER_CREDIT,
    LEDGER_DEBIT,
    VALID_TRANSITIONS,
    PAYOUT_PENDING,
    PAYOUT_PROCESSING,
)
from core.exceptions import InvalidStateTransitionError


def calculate_balance(merchant_id: str) -> dict:
    """
    Compute a merchant's balance entirely in the DB using SUM aggregation.
    Balance is NEVER stored — it is always derived on demand.

    Returns a dict with:
        available_balance (int, paise): credits - debits
        held_balance      (int, paise): sum of pending + processing payouts
    """
    # Import here to avoid circular imports at module load time.
    from apps.ledger.models import LedgerEntry
    from apps.payouts.models import Payout

    credits = (
        LedgerEntry.objects
        .filter(merchant_id=merchant_id, type=LEDGER_CREDIT)
        .aggregate(total=Sum("amount_paise"))["total"]
        or 0
    )
    debits = (
        LedgerEntry.objects
        .filter(merchant_id=merchant_id, type=LEDGER_DEBIT)
        .aggregate(total=Sum("amount_paise"))["total"]
        or 0
    )

    held = (
        Payout.objects
        .filter(
            merchant_id=merchant_id,
            status__in=[PAYOUT_PENDING, PAYOUT_PROCESSING],
        )
        .aggregate(total=Sum("amount_paise"))["total"]
        or 0
    )

    available = credits - debits

    return {
        "available_balance": available,
        "held_balance": held,
    }


def validate_state_transition(current: str, target: str) -> None:
    """
    Enforce the payout state machine.

    Allowed transitions:
        pending     → processing
        processing  → completed
        processing  → failed

    Any other transition raises InvalidStateTransitionError.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Cannot transition payout from '{current}' to '{target}'."
        )
