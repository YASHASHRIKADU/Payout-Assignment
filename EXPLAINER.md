# 📖 EXPLAINER — Playto Payout Engine

## Overview

This document explains the architectural decisions and implementation details behind the Playto Payout Engine.

---

## 1. 💰 Money Integrity — Why BIGINT Paise?

**Problem**: Floating-point arithmetic is non-deterministic for financial calculations.
```python
# This is WRONG — never do this
balance = 1.10 + 2.20  # = 3.3000000000000003 !!
```

**Solution**: Store all monetary values as **integers in paise** (1 INR = 100 paise):
```python
amount_paise = models.BigIntegerField()  # ₹10.50 = 1050 paise
```

**Balance calculation** uses DB-level SUM aggregation — never stored, always derived:
```python
Balance = SUM(credit entries) - SUM(debit entries)
```

This makes the ledger **append-only** and **auditable** — every financial event leaves a permanent record.

---

## 2. 🔒 Concurrency — SELECT FOR UPDATE

**Problem**: Two simultaneous payout requests for ₹60 when balance = ₹100 could both read the same balance and both succeed — causing an overdraft.

**Solution**: Use PostgreSQL row-level locking inside a transaction:

```python
with transaction.atomic():
    # Lock the merchant row — all other requests for this merchant WAIT here
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    
    # Now calculate balance — guaranteed no other transaction can modify it
    balance = calculate_balance(merchant_id)
    
    if balance < amount_paise:
        raise InsufficientBalanceError()
    
    # Create payout + debit — atomically
    payout = Payout.objects.create(...)
    LedgerEntry.objects.create(type='debit', ...)
```

**What happens with two concurrent requests:**
```
Thread A: LOCK(merchant) → balance=10000 → 6000 ok → debit 6000 → COMMIT
Thread B: LOCK(merchant) → WAITS → balance=4000 → 6000 FAIL → 402
```

---

## 3. 🔁 Idempotency — Same Key = Same Response

**Problem**: Network retries can cause the same payout to be created twice.

**Solution**: Require an `Idempotency-Key` header on every POST `/api/v1/payouts/` request:

1. Check if `(merchant_id, key)` exists in `IdempotencyKey` table
2. If found and not expired → return the **exact same JSON response** (no new payout created)
3. If not found → process normally, then store the response

**Race condition safety**: The `IdempotencyKey` model has `unique_together = [("merchant", "key")]` at the DB level. If two concurrent requests with the same key both try to insert, one gets an `IntegrityError` which is silently swallowed — both return the same response.

**TTL**: Keys expire after 24 hours (configurable via `IDEMPOTENCY_TTL_HOURS`).

---

## 4. 🧠 State Machine — Enforced Transitions

The payout lifecycle follows a strict state machine:

```
pending ──────► processing ──────► completed
                     │
                     └───────────► failed
```

Any other transition (e.g., `completed → pending`, `failed → completed`) raises an `InvalidStateTransitionError` (HTTP 409). This is enforced in `core/utils.validate_state_transition()` and applied at every status update.

---

## 5. 🔄 Async Processing — Django-Q (ORM Broker)

**Why Django-Q?** — The requirements forbid Redis and Celery. Django-Q with ORM broker stores tasks in the PostgreSQL database itself — no additional infrastructure needed.

**Flow:**
1. Payout created → `async_task("apps.payouts.tasks.process_payout", payout_id)` queued
2. Django-Q worker process picks up the task
3. `process_payout()` simulates bank processing:
   - Sleep 1–3 seconds (latency simulation)
   - Roll a random number: 70% success, 20% fail, 10% stuck
4. Outcome handled atomically

**Running the worker:**
```bash
python manage.py qcluster
```

---

## 6. 🔁 Retry Logic — Exponential Backoff

When a payout gets **stuck** (stays in `processing` > 30 seconds):

| Retry Attempt | Backoff Delay |
|---------------|---------------|
| 1st retry     | 5 seconds     |
| 2nd retry     | 15 seconds    |
| 3rd retry     | 45 seconds    |
| > 3 retries   | Mark FAILED + refund |

The `check_stuck_payouts()` scheduled task runs every 60 seconds, finds stuck payouts, and either re-queues them with backoff or fails them.

---

## 7. 💸 Refund Logic — Atomic Credit

When a payout fails (whether from simulation or exhausted retries):

```python
@transaction.atomic
def refund_payout(payout):
    # Re-fetch with lock
    payout = Payout.objects.select_for_update().get(id=payout.id)
    
    # Add a credit entry — atomically reverses the debit
    LedgerEntry.objects.create(
        merchant=payout.merchant,
        type='credit',
        amount_paise=payout.amount_paise,
        reference_id=f"payout_refund_{payout.id}",
    )
```

The credit entry reverses the original debit — balance is restored without touching any stored value.

---

## 8. 🌐 Frontend Architecture

**Tech stack**: React 19 + Vite + Tailwind CSS v4 + Axios

**Key design choices:**
- **No auth** — merchant selector dropdown (as per scope)
- **Auto-polling** — `usePayouts` hook polls every 5 seconds for live status updates
- **Paise → Rupees** conversion done in the UI layer only — API always works in paise
- **UUID idempotency key** auto-generated on every form submission (no user input required)
- **Dark glassmorphism** design with animated status badges

---

## 9. 🏗 Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│  MerchantSelector → BalanceCard → PayoutForm → PayoutTable  │
└─────────────────────────────┬────────────────────────────────┘
                              │ Axios (HTTP)
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   Django REST Framework                      │
│  POST /payouts/  GET /balance/  GET /payouts/               │
└──────────┬───────────────────────────┬───────────────────────┘
           │                           │
           ▼                           ▼
┌─────────────────────┐    ┌──────────────────────────────────┐
│  Payout Service     │    │         Django-Q Worker          │
│  select_for_update  │    │  process_payout(payout_id)       │
│  balance check      │    │  70% success / 20% fail / 10%    │
│  atomic debit       │    │  stuck → retry with backoff      │
└─────────┬───────────┘    └───────────────┬──────────────────┘
          │                                │
          ▼                                ▼
┌──────────────────────────────────────────────────────────────┐
│                        PostgreSQL                            │
│  merchants | ledger_entries | payouts | idempotency_keys     │
│  django_q (ORM broker tables)                               │
└──────────────────────────────────────────────────────────────┘
```
