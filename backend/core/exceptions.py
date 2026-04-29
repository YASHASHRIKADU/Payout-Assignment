"""
Custom exception classes for the Playto Payout Engine.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


# ---------------------------------------------------------------------------
# Domain exceptions
# ---------------------------------------------------------------------------


class PayoutEngineError(Exception):
    """Base exception for all payout engine domain errors."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "An unexpected error occurred."

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class InsufficientBalanceError(PayoutEngineError):
    """Raised when a merchant's available balance is too low for the payout."""
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = "Insufficient balance to process this payout."


class InvalidStateTransitionError(PayoutEngineError):
    """Raised when an illegal payout state transition is attempted."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Invalid payout state transition."


class IdempotencyConflictError(PayoutEngineError):
    """Raised when an idempotency key collision is detected."""
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Idempotency key conflict."


class MissingIdempotencyKeyError(PayoutEngineError):
    """Raised when the Idempotency-Key header is absent."""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 'Idempotency-Key' header is required."


# ---------------------------------------------------------------------------
# DRF exception handler override
# ---------------------------------------------------------------------------


def custom_exception_handler(exc, context):
    """
    Wraps domain exceptions in a standard JSON envelope:
    { "error": "<message>", "code": "<exception class name>" }
    """
    # Let DRF handle its own exceptions first.
    response = exception_handler(exc, context)

    if isinstance(exc, PayoutEngineError):
        return Response(
            {
                "error": exc.detail,
                "code": type(exc).__name__,
            },
            status=exc.status_code,
        )

    if response is not None:
        # Re-wrap DRF errors in the same envelope.
        return Response(
            {
                "error": response.data,
                "code": "ValidationError",
            },
            status=response.status_code,
        )

    return response
