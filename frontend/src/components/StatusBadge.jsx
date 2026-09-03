/**
 * StatusBadge — renders a coloured pill for claim/job/document statuses.
 * Maps the raw status string from the backend to a CSS class.
 */
export default function StatusBadge({ status }) {
  if (!status) return null;
  const cls = status.toLowerCase().replace(/\s+/g, '_');
  return <span className={`badge badge-${cls}`}>{status}</span>;
}
