"""
Django-Q async task: process_payout
Simulates bank processing with 70% success / 20% fail / 10% stuck.
"""
import logging
import random
import time

from django.utils import timezone

from core.constants import (
    MAX_RETRY_COUNT,
    PAYOUT_COMPLETED,
    PAYOUT_FAILED,
    PAYOUT_PENDING,
    PAYOUT_PROCESSING,
    RETRY_BACKOFF,
    SIMULATION_FAIL_PCT,
    SIMULATION_STUCK_PCT,
    SIMULATION_SUCCESS_PCT,
    STUCK_THRESHOLD_SECONDS,
)
from .models import Payout
from .services import refund_payout, transition_payout

logger = logging.getLogger(__name__)


def process_payout(payout_id: str) -> None:
    """
    Main async task executed by Django-Q workers.

    Flow:
        1. Fetch payout, ensure it is still pending.
        2. Transition: pending → processing.
        3. Simulate bank delay.
        4. Roll dice: 70% success, 20% fail, 10% stuck.
        5. Handle each outcome atomically.
    """
    logger.info("[Task] Starting process_payout for payout_id=%s", payout_id)

    try:
        payout = Payout.objects.get(id=payout_id)
    except Payout.DoesNotExist:
        logger.error("[Task] Payout %s not found. Aborting.", payout_id)
        return

    # Only process pending payouts — idempotency guard for re-queued tasks.
    if payout.status != PAYOUT_PENDING:
        logger.warning(
            "[Task] Payout %s is in status '%s', expected 'pending'. Aborting.",
            payout_id,
            payout.status,
        )
        return

    # Transition to processing.
    payout = transition_payout(payout, PAYOUT_PROCESSING)
    logger.info("[Task] Payout %s → processing", payout_id)

    # Simulate network / bank latency.
    time.sleep(random.uniform(1, 3))

    # Determine outcome via weighted random.
    roll = random.randint(1, 100)

    if roll <= SIMULATION_SUCCESS_PCT:
        # ── SUCCESS ──────────────────────────────────────────────────────────
        _handle_success(payout)

    elif roll <= SIMULATION_SUCCESS_PCT + SIMULATION_FAIL_PCT:
        # ── FAILURE ──────────────────────────────────────────────────────────
        _handle_failure(payout)

    else:
        # ── STUCK ────────────────────────────────────────────────────────────
        _handle_stuck(payout)


def _handle_success(payout: Payout) -> None:
    """Mark the payout as completed."""
    transition_payout(payout, PAYOUT_COMPLETED)
    logger.info("[Task] Payout %s → completed ✓", payout.id)


def _handle_failure(payout: Payout) -> None:
    """Mark the payout as failed and issue a refund credit."""
    transition_payout(payout, PAYOUT_FAILED)
    refund_payout(payout)
    logger.info("[Task] Payout %s → failed + refunded ✗", payout.id)


def _handle_stuck(payout: Payout) -> None:
    """
    Simulate a stuck payout. Retry logic runs via the separate scheduled task
    `check_stuck_payouts`. For now, we simply log and let the payout remain
    in 'processing' state so the scheduler can pick it up.
    """
    logger.warning(
        "[Task] Payout %s is STUCK (simulated). Will be retried by scheduler.",
        payout.id,
    )
    # The task exits without transitioning — payout stays in 'processing'.
    # check_stuck_payouts() will detect it after STUCK_THRESHOLD_SECONDS.


def check_stuck_payouts() -> None:
    """
    Scheduled task (run every 60 s via Django-Q schedule).
    Finds all payouts that have been stuck in 'processing' for more than
    STUCK_THRESHOLD_SECONDS seconds and either retries or marks them failed.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django_q.tasks import async_task

    cutoff = timezone.now() - timedelta(seconds=STUCK_THRESHOLD_SECONDS)

    stuck = Payout.objects.filter(
        status=PAYOUT_PROCESSING,
        updated_at__lte=cutoff,
    )

    for payout in stuck:
        if payout.retry_count >= MAX_RETRY_COUNT:
            # Exhausted retries — fail it and refund.
            logger.warning(
                "[Scheduler] Payout %s exceeded max retries. Marking failed.",
                payout.id,
            )
            transition_payout(payout, PAYOUT_FAILED)
            refund_payout(payout)
        else:
            # Reset to pending and re-queue with exponential back-off.
            payout.retry_count += 1
            backoff = RETRY_BACKOFF.get(payout.retry_count, 45)
            payout.status = PAYOUT_PENDING
            payout.save(update_fields=["status", "retry_count", "updated_at"])

            logger.info(
                "[Scheduler] Retrying payout %s (attempt %d) with %ds back-off.",
                payout.id,
                payout.retry_count,
                backoff,
            )

            async_task(
                "apps.payouts.tasks.process_payout",
                str(payout.id),
                q_options={"delay": backoff},
            )
