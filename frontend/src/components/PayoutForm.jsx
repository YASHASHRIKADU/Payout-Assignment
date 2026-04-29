import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { createPayout } from '../api/client'

/**
 * PayoutForm — accepts an amount in ₹, auto-generates an idempotency key,
 * converts to paise, and submits to the API.
 */
export default function PayoutForm({ merchantId, onSuccess, onError }) {
  const [amountRupees, setAmountRupees] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    const rupees = parseFloat(amountRupees)
    if (!rupees || rupees <= 0) {
      onError('Please enter a valid amount.')
      return
    }

    // Convert to paise — use Math.round to avoid floating-point issues.
    const amountPaise = Math.round(rupees * 100)
    const idempotencyKey = uuidv4()

    setSubmitting(true)
    try {
      const res = await createPayout(merchantId, amountPaise, idempotencyKey)
      setAmountRupees('')
      onSuccess(`Payout of ₹${rupees.toFixed(2)} submitted! (ID: ${res.data.id?.slice(0, 8)}…)`)
    } catch (err) {
      const msg = err?.response?.data?.error || 'Payout request failed.'
      onError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="glass-card fade-in" style={{ padding: 28 }}>
      <h2 style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 20 }}>
        💸 Request Payout
      </h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <label
            htmlFor="payout-amount"
            style={{ display: 'block', fontSize: '0.82rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 8 }}
          >
            Amount (₹)
          </label>
          <div style={{ position: 'relative' }}>
            <span style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: 'var(--text-muted)', fontWeight: 600, fontSize: '1rem',
            }}>₹</span>
            <input
              id="payout-amount"
              type="number"
              min="1"
              step="0.01"
              placeholder="0.00"
              className="input-field"
              style={{ paddingLeft: 32 }}
              value={amountRupees}
              onChange={(e) => setAmountRupees(e.target.value)}
              disabled={submitting}
              required
            />
          </div>
          {amountRupees && parseFloat(amountRupees) > 0 && (
            <p style={{ marginTop: 6, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              = {Math.round(parseFloat(amountRupees) * 100).toLocaleString('en-IN')} paise
            </p>
          )}
        </div>

        <div style={{
          background: 'rgba(59,130,246,0.06)',
          border: '1px solid rgba(59,130,246,0.15)',
          borderRadius: 8,
          padding: '10px 14px',
          fontSize: '0.78rem',
          color: 'var(--text-muted)',
        }}>
          🔑 An idempotency key will be auto-generated (UUID v4) when you submit.
        </div>

        <button
          id="submit-payout-btn"
          type="submit"
          className="btn-primary"
          disabled={submitting || !merchantId}
          style={{ marginTop: 4 }}
        >
          {submitting ? (
            <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}>
              <span className="spinner" style={{ width: 16, height: 16 }} />
              Submitting…
            </span>
          ) : (
            'Submit Payout'
          )}
        </button>
      </form>
    </div>
  )
}
