/**
 * Toast notification container — renders ephemeral success/error/info toasts
 * in the top-right corner.
 */
const ICONS = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}

export default function ToastContainer({ toasts }) {
  if (!toasts.length) return null
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span style={{ fontSize: '1rem', fontWeight: 700 }}>{ICONS[t.type]}</span>
          {t.message}
        </div>
      ))}
    </div>
  )
}
