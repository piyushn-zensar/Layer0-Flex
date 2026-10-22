"use client";
// A step that is done shows its recorded state instead of a live form (21 Oct review: the end state must not look unfinished).  Owner: Janvia.
//   <ChangeGate done={decided} canChange={bm} label="Change participation…">{the form}</ChangeGate>
// not done -> the form as it is; done and the person may change it -> a "Change…" button that opens the form again (with Cancel);
// done and the person may not -> nothing: the recorded state around it stays visible, no greyed form, no "Only the bid manager…" note.
import { useState } from "react";

export default function ChangeGate({ done, canChange, label = "Change…", children }:
  { done: boolean; canChange: boolean; label?: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);
  if (!done) return <>{children}</>;
  if (!canChange) return null;
  if (!open) return <div className="row"><button type="button" className="secondary sm" onClick={() => setOpen(true)}>{label}</button></div>;
  return <>{children}<div className="row"><button type="button" className="secondary sm" onClick={() => setOpen(false)}>Cancel</button></div></>;
}
