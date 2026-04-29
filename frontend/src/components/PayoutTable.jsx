import StatusBadge from './StatusBadge'

function paiseToRupees(paise) {
  return (paise / 100).toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function shortId(id) {
  return id ? id.slice(0, 8) + '…' : '—'
}

/**
 * PayoutTable — live-refreshing table of payout records.
 * Receives payouts array from the usePayouts hook (polled every 5s).
 */
export default function PayoutTable({ payouts, loading }) {
  return (
    <div className="glass-card fade-in" style={{ padding: 28 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
          📋 Payout History
        </h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {loading && <span className="spinner" style={{ width: 14, height: 14 }} />}
          Auto-refreshes every 5s
        </div>
      </div>

      {payouts.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          No payouts yet. Submit your first payout above ↑
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Payout ID</th>
                <th>Amount</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Created</th>
                <th>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {payouts.map(p => (
                <tr key={p.id}>
                  <td>
                    <code style={{ fontSize: '0.82rem', color: 'var(--accent-blue)', background: 'rgba(59,130,246,0.08)', padding: '2px 6px', borderRadius: 4 }}>
                      {shortId(p.id)}
                    </code>
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    ₹{paiseToRupees(p.amount_paise)}
                  </td>
                  <td>
                    <StatusBadge status={p.status} />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    {p.retry_count > 0 ? (
                      <span style={{ color: 'var(--accent-yellow)', fontWeight: 600 }}>{p.retry_count}</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>0</span>
                    )}
                  </td>
                  <td>{formatDate(p.created_at)}</td>
                  <td>{formatDate(p.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
