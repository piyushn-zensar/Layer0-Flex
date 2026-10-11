// Inline message block: info / success / warn / error.  Owner: Janvia.
//   <Alert kind="error">{error}</Alert>
//   <Alert kind="success" title="Dispatched" onClose={() => setNotice(undefined)}>12 new assignments sent.</Alert>
// Errors and warnings are role="alert" (announced at once); info and success are role="status".
// `.notice` / `.notice.warn` in globals.css are the plain-markup equivalents when a component is overkill.

export type AlertKind = "info" | "success" | "warn" | "error";

export default function Alert({ kind = "info", title, children, onClose, className = "" }:
  { kind?: AlertKind; title?: string; children?: React.ReactNode; onClose?: () => void; className?: string }) {
  if (!children && !title) return null;
  return (
    <div className={`alert ${kind} ${className}`.trim()} role={kind === "error" || kind === "warn" ? "alert" : "status"}>
      <div className="alert-body">{title && <span className="alert-title">{title}</span>}{children}</div>
      {onClose && <button type="button" className="alert-close" aria-label="Dismiss" onClick={onClose}>×</button>}
    </div>
  );
}
