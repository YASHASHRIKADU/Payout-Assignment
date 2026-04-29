import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// ── Merchants ──────────────────────────────────────────────────────────────
export const getMerchants = () => api.get('/merchants/')

// ── Balance ────────────────────────────────────────────────────────────────
export const getBalance = (merchantId) =>
  api.get(`/merchants/${merchantId}/balance/`)

// ── Ledger ─────────────────────────────────────────────────────────────────
export const getLedger = (merchantId) =>
  api.get(`/merchants/${merchantId}/ledger/`)

// ── Payouts ────────────────────────────────────────────────────────────────
export const getPayouts = (merchantId) =>
  api.get(`/merchants/${merchantId}/payouts/`)

export const createPayout = (merchantId, amountPaise, idempotencyKey) =>
  api.post(
    '/payouts/',
    { merchant_id: merchantId, amount_paise: amountPaise },
    { headers: { 'Idempotency-Key': idempotencyKey } }
  )
