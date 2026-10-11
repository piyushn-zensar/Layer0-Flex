// Loading indicators.  Owner: Janvia.
//   <Spinner />                              a 16px ring (decorative; pair it with text or a label)
//   <Busy label="Saving…" />                 ring + text, role="status" so the change is announced
//   <Skeleton lines={3} />                   grey shimmer lines while a page's first fetch is in flight
// `busy` on a page is still a string or boolean in state; these only render it.

export function Spinner({ size = "md", label }: { size?: "sm" | "md"; label?: string }) {
  return <span className={`spinner ${size === "sm" ? "sm" : ""}`.trim()} role={label ? "status" : undefined} aria-label={label} aria-hidden={label ? undefined : true} />;
}

export function Busy({ label = "Working…", className = "" }: { label?: string; className?: string }) {
  return <span className={`busy ${className}`.trim()} role="status"><Spinner /> {label}</span>;
}

export function Skeleton({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  const widths = ["", "w-75", "w-50"];
  return (
    <div className={className} aria-busy="true" aria-label="Loading">
      {Array.from({ length: lines }, (_, i) => <span key={i} className={`skeleton ${widths[i % widths.length]}`.trim()} />)}
    </div>
  );
}

export default Spinner;
