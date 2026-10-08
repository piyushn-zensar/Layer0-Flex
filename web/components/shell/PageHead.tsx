// Same header on every page: title, one line of help, actions on the right.  Owner: Janvia.
// Inside an opportunity the opportunity title is the h1, so pages there pass level={2}.
export default function PageHead({ title, help, level = 1, children }:
  { title: string; help?: string; level?: 1 | 2; children?: React.ReactNode }) {
  const Title = level === 1 ? "h1" : "h2";
  return (
    <div className="page-head">
      <div>
        <Title className="page-title">{title}</Title>
        {help && <p className="page-help">{help}</p>}
      </div>
      {children && <div className="page-actions">{children}</div>}
    </div>
  );
}
