// Same header on every page: title, one line of help, actions on the right.  Owner: Janvia.
// Inside an opportunity the opportunity title is the h1, so pages there pass level={2}.
//   <PageHead title="Requirements" help="Check each line against its source, then freeze.">
//     <button>Freeze baseline</button>            <- children are the right-hand actions
//   </PageHead>
// `crumbs` renders a breadcrumb above the title for pages outside an opportunity (the opportunity header has its own).
export default function PageHead({ title, help, level = 1, crumbs, children }:
  { title: React.ReactNode; help?: React.ReactNode; level?: 1 | 2; crumbs?: React.ReactNode; children?: React.ReactNode }) {
  const Title = level === 1 ? "h1" : "h2";
  return (
    <div className="page-head">
      <div>
        {crumbs && <nav className="crumbs" aria-label="Breadcrumb">{crumbs}</nav>}
        <Title className="page-title">{title}</Title>
        {help && <p className="page-help">{help}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  );
}
