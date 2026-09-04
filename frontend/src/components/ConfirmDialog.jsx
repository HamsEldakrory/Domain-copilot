/**
 * ConfirmDialog — renders a modal confirmation dialog.
 *
 * Props:
 *   open         {boolean}   — whether to show the dialog
 *   title        {string}    — dialog title
 *   message      {string}    — body message
 *   confirmLabel {string}    — confirm button text (default "Confirm")
 *   confirmClass {string}    — extra CSS class for confirm button
 *   onConfirm    {function}  — called on confirm
 *   onCancel     {function}  — called on cancel
 *   isLoading    {boolean}   — disables buttons while loading
 */
export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  confirmClass = 'btn-primary',
  onConfirm,
  onCancel,
  isLoading = false,
}) {
  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title">{title}</div>
        <div className="modal-body">{message}</div>
        <div className="modal-actions">
          <button
            className="btn btn-outline btn-sm"
            onClick={onCancel}
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            className={`btn ${confirmClass} btn-sm`}
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? <span className="spinner" /> : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
