# 🏦 Playto Payout Engine

A production-grade merchant payout system with ledger-based balances, async processing, concurrency safety, and idempotency.

---

## 🗂 Project Structure

```
Payout Assignment/
├── backend/           Django + DRF + PostgreSQL + Django-Q
│   ├── config/        Settings, URLs, WSGI
│   ├── apps/
│   │   ├── merchants/ Merchant model + API
│   │   ├── ledger/    LedgerEntry model + Balance API
│   │   ├── payouts/   Payout model, API, service, tasks
│   │   └── idempotency/ IdempotencyKey model + service
│   ├── core/          Constants, exceptions, utilities
│   ├── tests/         Concurrency + idempotency tests
│   ├── seed.py        Database seeder
│   └── requirements.txt
└── frontend/          React + Vite + Tailwind CSS
    └── src/
        ├── api/       Axios client
        ├── components/ BalanceCard, PayoutForm, PayoutTable, StatusBadge
        ├── hooks/     useBalance, usePayouts, useMerchants, useToast
        └── pages/     DashboardPage
```

---

## ⚡ Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+

---

### 1. PostgreSQL Setup

```sql
CREATE DATABASE payout_db;
-- Default user: postgres / password: postgres
-- Or update backend/.env with your credentials
```

---

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (edit if needed)
# DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT are in .env

# Run migrations
python manage.py migrate

# Seed test data (3 merchants + ₹1,000 credit each)
python seed.py

# Start Django dev server
python manage.py runserver
```

---

### 3. Start Django-Q Worker (new terminal)

```bash
cd backend
venv\Scripts\activate
python manage.py qcluster
```

> **Important**: The Django-Q worker must be running for payouts to be processed asynchronously.

---

### 4. Register Stuck Payout Scheduler (optional)

In Django admin → Q Schedules → Add schedule:
- Name: `check_stuck_payouts`
- Func: `apps.payouts.tasks.check_stuck_payouts`
- Schedule type: Minutes → Every `1` minute

---

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/merchants/` | List all merchants |
| POST | `/api/v1/merchants/` | Create merchant |
| GET | `/api/v1/merchants/{id}/balance/` | Get derived balance |
| GET | `/api/v1/merchants/{id}/ledger/` | Get ledger entries |
| POST | `/api/v1/payouts/` | Create payout request |
| GET | `/api/v1/merchants/{id}/payouts/` | List merchant payouts |
| GET | `/api/v1/payouts/{id}/` | Get single payout |

### POST /api/v1/payouts/ — Required Headers

```
Idempotency-Key: <unique-uuid>
Content-Type: application/json
```

### POST /api/v1/payouts/ — Request Body

```json
{
  "merchant_id": "uuid",
  "amount_paise": 5000
}
```

---

## 🧪 Running Tests

```bash
cd backend
python manage.py test tests.test_concurrency
python manage.py test tests.test_idempotency

# Run all tests
python manage.py test tests
```

---

## 🔑 Key Design Decisions

### Money Integrity
- All amounts stored as **BIGINT paise** — never float
- Balance derived via `SUM(credits) - SUM(debits)` — never stored

### Concurrency Safety
- `SELECT FOR UPDATE` locks the Merchant row during balance check
- Ensures only one of two concurrent overdraft attempts succeeds

### Idempotency
- `unique_together(merchant, key)` enforced at DB level
- `IntegrityError` on duplicate write is silently swallowed (safe)
- Keys expire after 24 hours

### State Machine
- Strictly enforced in `core/utils.validate_state_transition()`
- Invalid transitions raise `InvalidStateTransitionError` (409)

### Async Processing
- Django-Q with ORM broker (no Redis required)
- Simulation: 70% success, 20% fail, 10% stuck
- Retries: exponential backoff (5s → 15s → 45s), max 3 attempts
- On failure/exhausted retries: atomic refund credit entry

---

## 🌱 Environment Variables (backend/.env)

```
DB_NAME=payout_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```
