/**
 * StatusBadge — renders a colour-coded pill badge with an animated pulse dot.
 */
export default function StatusBadge({ status }) {
  return (
    <span className={`badge badge-${status}`}>
      <span className={`pulse-dot ${status}`} />
      {status}
    </span>
  )
}
