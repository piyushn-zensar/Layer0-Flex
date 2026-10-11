// Empty-state block for a list or table with nothing in it.  Owner: Janvia.
//   <EmptyState title="No opportunities yet" hint="Create one, or run the demo seed.">
//     <Link className="button" href="/opportunities/new">New opportunity</Link>
//   </EmptyState>
// Inside a table use the plain markup instead: <tr><td colSpan={n} className="muted">Nothing assigned.</td></tr>.

export default function EmptyState({ title, hint, children, className = "" }:
  { title: string; hint?: React.ReactNode; children?: React.ReactNode; className?: string }) {
  return (
    <div className={`empty ${className}`.trim()}>
      <div className="empty-title">{title}</div>
      {hint && <p>{hint}</p>}
      {children && <div className="row" style={{ justifyContent: "center" }}>{children}</div>}
    </div>
  );
}
