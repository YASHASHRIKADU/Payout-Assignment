"""
Application-wide constants for the Playto Payout Engine.
All money values are in PAISE (1 INR = 100 paise). Never use floats.
"""

# ---------------------------------------------------------------------------
# Payout status
# ---------------------------------------------------------------------------
PAYOUT_PENDING = "pending"
PAYOUT_PROCESSING = "processing"
PAYOUT_COMPLETED = "completed"
PAYOUT_FAILED = "failed"

PAYOUT_STATUS_CHOICES = [
    (PAYOUT_PENDING, "Pending"),
    (PAYOUT_PROCESSING, "Processing"),
    (PAYOUT_COMPLETED, "Completed"),
    (PAYOUT_FAILED, "Failed"),
]

# ---------------------------------------------------------------------------
# Valid state-machine transitions
# ---------------------------------------------------------------------------
VALID_TRANSITIONS = {
    PAYOUT_PENDING: {PAYOUT_PROCESSING},
    PAYOUT_PROCESSING: {PAYOUT_COMPLETED, PAYOUT_FAILED},
    PAYOUT_COMPLETED: set(),
    PAYOUT_FAILED: set(),
}

# ---------------------------------------------------------------------------
# Ledger entry types
# ---------------------------------------------------------------------------
LEDGER_CREDIT = "credit"
LEDGER_DEBIT = "debit"

LEDGER_TYPE_CHOICES = [
    (LEDGER_CREDIT, "Credit"),
    (LEDGER_DEBIT, "Debit"),
]

# ---------------------------------------------------------------------------
# Retry / worker constants
# ---------------------------------------------------------------------------
MAX_RETRY_COUNT = 3
STUCK_THRESHOLD_SECONDS = 30
IDEMPOTENCY_TTL_HOURS = 24

# Exponential back-off delays (seconds) per retry attempt (1-indexed)
RETRY_BACKOFF = {1: 5, 2: 15, 3: 45}

# ---------------------------------------------------------------------------
# Simulation probabilities (must sum to 100)
# ---------------------------------------------------------------------------
SIMULATION_SUCCESS_PCT = 70
SIMULATION_FAIL_PCT = 20
SIMULATION_STUCK_PCT = 10
