import { useState } from 'react'
import { useMerchants } from '../hooks/useMerchants'
import { useBalance } from '../hooks/useBalance'
import { usePayouts } from '../hooks/usePayouts'
import { useToast } from '../hooks/useToast'
import BalanceCard from '../components/BalanceCard'
import PayoutForm from '../components/PayoutForm'
import PayoutTable from '../components/PayoutTable'
import ToastContainer from '../components/ToastContainer'

/**
 * DashboardPage — the single-page dashboard for the Playto Payout Engine.
 *
 * Layout:
 *   Header → Merchant Selector → Balance Card → [Payout Form | Payout Table]
 */
export default function DashboardPage() {
  const { merchants, loading: merchantsLoading } = useMerchants()
  const [selectedMerchantId, setSelectedMerchantId] = useState('')
  const { balance, loading: balanceLoading, refetch: refetchBalance } = useBalance(selectedMerchantId)
  const { payouts, loading: payoutsLoading, refetch: refetchPayouts } = usePayouts(selectedMerchantId)
  const toast = useToast()

  const handleMerchantChange = (e) => {
    setSelectedMerchantId(e.target.value)
  }

  const handlePayoutSuccess = (msg) => {
    toast.success(msg)
    refetchBalance()
    refetchPayouts()
  }

  const handlePayoutError = (msg) => {
    toast.error(msg)
  }

  const selectedMerchant = merchants.find(m => m.id === selectedMerchantId)

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-base)' }}>
      <ToastContainer toasts={toast.toasts} />

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header style={{
        borderBottom: '1px solid var(--border)',
        background: 'rgba(17, 24, 39, 0.8)',
        backdropFilter: 'blur(12px)',
        position: 'sticky', top: 0, zIndex: 100,
        padding: '0 32px',
      }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-cyan))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '1.1rem', boxShadow: 'var(--glow-blue)',
            }}>💳</div>
            <div>
              <span className="gradient-text" style={{ fontWeight: 800, fontSize: '1.1rem', letterSpacing: '-0.01em' }}>
                Playto
              </span>
              <span style={{ fontWeight: 400, color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                {' '}Payout Engine
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>🟢 Live</span>
          </div>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 32px 64px' }}>

        {/* ── Page Title ── */}
        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontSize: '2rem', fontWeight: 800, letterSpacing: '-0.02em', marginBottom: 8 }}>
            Merchant Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Manage payouts, track balances, and monitor transaction history in real time.
          </p>
        </div>

        {/* ── Merchant Selector ── */}
        <div className="glass-card fade-in" style={{ padding: 24, marginBottom: 24 }}>
          <label
            htmlFor="merchant-select"
            style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 10 }}
          >
            🏪 Select Merchant
          </label>
          <div style={{ position: 'relative' }}>
            {merchantsLoading ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--text-muted)' }}>
                <div className="spinner" />
                Loading merchants…
              </div>
            ) : (
              <>
                <select
                  id="merchant-select"
                  className="select-field"
                  value={selectedMerchantId}
                  onChange={handleMerchantChange}
                >
                  <option value="">— Select a merchant —</option>
                  {merchants.map(m => (
                    <option key={m.id} value={m.id}>{m.name}</option>
                  ))}
                </select>
                <span style={{
                  position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)',
                  color: 'var(--text-muted)', pointerEvents: 'none',
                }}>▾</span>
              </>
            )}
          </div>
          {selectedMerchant && (
            <p style={{ marginTop: 10, fontSize: '0.78rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
              ID: {selectedMerchant.id}
            </p>
          )}
        </div>

        {/* ── Content (only shown when a merchant is selected) ── */}
        {!selectedMerchantId ? (
          <div style={{
            textAlign: 'center', padding: '64px 0',
            color: 'var(--text-muted)', fontSize: '1rem',
          }}>
            <div style={{ fontSize: '3rem', marginBottom: 16 }}>🏦</div>
            Select a merchant above to view their dashboard.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

            {/* Balance Card */}
            <BalanceCard balance={balance} loading={balanceLoading} />

            {/* Two-column layout on wider screens */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.6fr)',
              gap: 24,
              alignItems: 'start',
            }}>
              <PayoutForm
                merchantId={selectedMerchantId}
                onSuccess={handlePayoutSuccess}
                onError={handlePayoutError}
              />

              {/* Stats summary column */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {['pending', 'processing', 'completed', 'failed'].map(status => {
                  const count = payouts.filter(p => p.status === status).length
                  const colors = {
                    pending: 'var(--accent-yellow)',
                    processing: 'var(--accent-blue)',
                    completed: 'var(--accent-green)',
                    failed: 'var(--accent-red)',
                  }
                  const icons = { pending: '⏳', processing: '⚙️', completed: '✅', failed: '❌' }
                  return (
                    <div key={status} className="glass-card" style={{
                      padding: '16px 20px',
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    }}>
                      <span style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span>{icons[status]}</span>
                        <span style={{ textTransform: 'capitalize' }}>{status}</span>
                      </span>
                      <span style={{ fontSize: '1.4rem', fontWeight: 700, color: colors[status] }}>{count}</span>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Payout History Table */}
            <PayoutTable payouts={payouts} loading={payoutsLoading} />

          </div>
        )}
      </main>
    </div>
  )
}
