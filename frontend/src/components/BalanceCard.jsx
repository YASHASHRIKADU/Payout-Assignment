/**
 * BalanceCard — displays available and held balances for the selected merchant.
 * Balance values are in paise — converted to ₹ for display.
 */
function paiseToRupees(paise) {
  return (paise / 100).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function StatTile({ label, value, color, icon }) {
  return (
    <div
      style={{
        flex: 1,
        background: 'rgba(15, 20, 35, 0.6)',
        border: `1px solid ${color}30`,
        borderRadius: 12,
        padding: '20px 24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <span style={{ fontSize: '1.2rem' }}>{icon}</span>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          {label}
        </span>
      </div>
      <div style={{ fontSize: '1.8rem', fontWeight: 700, color }}>
        ₹{value}
      </div>
    </div>
  )
}

export default function BalanceCard({ balance, loading }) {
  if (loading) {
    return (
      <div className="glass-card fade-in" style={{ padding: 28, display: 'flex', alignItems: 'center', gap: 12 }}>
        <div className="spinner" />
        <span style={{ color: 'var(--text-muted)' }}>Loading balance…</span>
      </div>
    )
  }

  if (!balance) return null

  return (
    <div className="glass-card fade-in" style={{ padding: 28 }}>
      <h2 style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: 20 }}>
        💼 Merchant Wallet
      </h2>
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
        <StatTile
          label="Available Balance"
          value={paiseToRupees(balance.available_balance)}
          color="var(--accent-green)"
          icon="✅"
        />
        <StatTile
          label="Held (Pending)"
          value={paiseToRupees(balance.held_balance)}
          color="var(--accent-yellow)"
          icon="⏳"
        />
      </div>
    </div>
  )
}
