# UI foundation: tokens, classes and primitives

Plain CSS (`app/globals.css`) and plain React (`components/ui/*`), no dependencies. Every class the pages used before
still works; this page says which ones to reach for now. Page groups own their own stylesheet in `app/styles/`
(`overview.css`, `requirements.css`, `trace.css`, `consolidation.css`), loaded after `globals.css` from `app/layout.tsx`.

## Tokens (`:root` in globals.css)

| Group | Tokens |
|---|---|
| Neutrals | `--bg` page, `--card` white, `--ink` text, `--ink-2` secondary text, `--muted` / `--muted-2` grey text, `--line` / `--line-2` borders, `--surface-2` / `--surface-3` grey fills |
| Brand | `--nav` navy bar, `--nav-ink` bar text, `--accent` blue, `--accent-hover`, `--accent-ink`, `--accent-soft`, `--sel` selected row, `--hl-sel` selected highlight |
| Status tones | `--ok`, `--info`, `--pending`, `--bad`, each with `-ink` (text on tint), `-bg` (tint) and `-line` (border); `--neutral-ink/-bg/-line`. `--warn` and `--danger` are aliases of `--bad` (`.warn` is the error text class on every page) |
| Spacing | `--s1` 4 · `--s2` 8 · `--s3` 12 · `--s4` 16 · `--s5` 24 · `--s6` 32 |
| Radii, shadows | `--radius` 8, `--radius-sm` 6, `--radius-pill`; `--shadow-1` card, `--shadow-2` floating; `--focus` ring |
| Type | `--fs-xs` 11 · `--fs-sm` 12 · `--fs-md` 13 · `--fs` 14 · `--fs-lg` 15 · `--fs-xl` 18 · `--fs-2xl` 20; `--font`, `--font-mono` |
| Layout | `--page-x` gutter (16px under 640px), `--content-max` 1600, `--topbar-h` 52 |

Use the tokens in page stylesheets (`color: var(--pending-ink)`), never new hex values for a status.

## Class names

Foundation (globals.css). Old names stay; "new" marks what was added in this pass.

| Area | Classes |
|---|---|
| Page | `.content` container; `.page-head` > `.page-title` + `.page-help` + `.page-actions` (use `<PageHead>`); `.crumbs` breadcrumb |
| Cards | `.card`; new `.card-head` (title row: `h2` + `.muted` + `.card-actions`), `.card-actions`; `details.card`; `.card.warn` is an error card |
| Tables | `table` (boxed, hover rows); new `table.dense`, `table.zebra`, `table.sticky-head`, `td.num`, `.table-scroll` wrapper; `.col-*` widths per page (`.rows th.col-unit` is new for trace pane 3); `tr.rejected`, `tr.inactive`, `tr.selected` |
| Forms | `.form` (row, wraps) and `.form.compact` (column; bare buttons no longer stretch); `label` holds the caption; `.check` for a checkbox row; `.inline` for a button pair; `.grow`, `.narrow`, `.wide`; new `.field-hint`; `aria-invalid="true"` turns a field red |
| Buttons | `button` / `.button` primary; `.secondary`; new `.danger` (and `.danger.secondary`); `.link`; new sizes `.sm` (28px, what `.row-actions` buttons are) and `.lg`; `:disabled` is grey with `not-allowed` |
| Badges | `.badge` / `.tag` pills; new `.badge.lg`; tone classes `.t-ok .t-info .t-pending .t-bad .t-neutral`; legacy `status-*`, `sev-*`, `opp-status-*`, `cons-state-*`, `cons-status-*`, `trace-status`, `tag.CTO/.SEMI_CUSTOM/.ETO` all map onto the same five tones; `.chip` / `.chip.on` (or `aria-pressed="true"`) filter chips |
| Messages | new `.alert` + `.info .success .warn .error` (with `.alert-body`, `.alert-title`, `.alert-close`); `.notice` (success) / `.notice.warn` (error) for plain markup under a `<PageHead>`; `.empty` + `.empty-title`; `.skeleton` (`.w-75 .w-50`); `.spinner` (`.sm`), `.busy`; `.toasts` / `.toast` (rendered by the provider); `.dialog-backdrop` / `.dialog` / `.dialog-actions` |
| Text | `.muted`, `.mono`, `.quote`, `.warn` (red 12px text), `.ok` (green text) |
| Utilities | `.row` (flex, wraps), `.stack` (column), `.grid-2`, `.right` (push right), `.text-right`, `.nowrap`, `.truncate`, `.sr-only`, `.per-req` (320px scroll box for long lists) |
| Shell | `.topbar`, `.brand` + `.brand-mark` + `.brand-sub`, `.topnav a.active`, `.topbar-right`, `.actor`; `.opp-head`, `.stepper li.done/.current`, `.step-no`, `.step-later` (Changes, same anatomy as a step) |

Responsive: under 1100px the three trace panes stack, the top bar wraps onto two rows, the stepper wraps, and any
`table` that is a direct child of `.content`, `.card` or `.form` scrolls sideways inside its box. Use `.table-scroll` for
a table elsewhere. Under 640px the gutter is 16px.

## Status colour scheme (one for the whole app)

| Tone | Means | Strings |
|---|---|---|
| ok (green) | done | approved, accepted, validated, applied, answered, met, pass, CTO, in scope, **submitted** final response (`kind="opp"`) |
| info (blue) | handed over, moving | submitted (unit answer), frozen, go, dispatched, consolidating, exception |
| pending (amber) | waiting on someone | proposed, assigned, queued, reading, review, pending, partial, medium, warn, SEMI_CUSTOM, modified |
| bad (red) | needs action | returned, blocked, no-go, not met, removed, over, fail, high, ETO |
| neutral (grey) | inactive | rejected, merged, split, duplicate, withdrawn, discarded, new, low, unknown, NONE |

Prefer `<StatusBadge>`; if you must write a class, use the tone (`badge t-bad`) or the legacy `status-<value>` name, which maps to the same tone.

## Primitives (`components/ui`, import from `@/components/ui`)

```tsx
import { Alert, Busy, ConfirmDialog, EmptyState, Skeleton, Spinner, StatusBadge, useConfirm, useToast } from "@/components/ui";
import { errorMessage } from "@/lib/api";
```

| Primitive | Use |
|---|---|
| `useToast()` | `const toast = useToast(); post(url).then(() => toast.success("Baseline frozen."), (e) => toast.error(errorMessage(e)));` Replaces `window.alert` for outcomes. `success` / `info` auto-dismiss in 5 s, `error` in 8 s; `show(kind, text)`. Provider is in `app/layout.tsx`. |
| `useConfirm()` | `const [ask, confirmDialog] = useConfirm();` render `{confirmDialog}` once, then `if (await ask({ title: "Discard the change set?", message: "The baseline stays as it is.", confirmLabel: "Discard", danger: true })) run();` Replaces `window.confirm`. |
| `<ConfirmDialog>` | The controlled form: `open title message? confirmLabel? cancelLabel? danger? busy? onConfirm onCancel`. Esc or backdrop cancels, Tab stays inside, focus starts on Confirm. |
| `<Alert kind="error">` | Inline message; `kind` info / success / warn / error, optional `title`, `onClose`. Errors and warnings are `role="alert"`, the rest `role="status"`. Renders nothing when empty, so `<Alert kind="error">{error}</Alert>` is safe. |
| `<StatusBadge status="validated" />` | Coloured pill for any status string; `kind` `"status"` (default) / `"opp"` / `"severity"` / `"offering"` / `"compliance"`, `label` to show other text, `className` to add e.g. `lg`. `toneOf(status, kind)` gives the tone name; `offeringLabel("SEMI_CUSTOM")` is "Semi-custom", the text every offering badge and select shows. |
| `<EmptyState title hint>` | Dashed block for an empty list; children are the actions. Inside a table keep `<td colSpan className="muted">`. |
| `<Spinner size? label?>`, `<Busy label="Saving…" />`, `<Skeleton lines={3} />` | Loading. `Busy` is `role="status"`; `Skeleton` for a first fetch (`if (!data) return <Skeleton />`). |
| `errorMessage(e)` (lib/api.ts) | One line from a rejected request: the API's detail without `Error:` or a `409:` prefix, with a fallback. Use it for every toast or alert text. |
| `<PageHead title help level? crumbs?>` (components/shell) | Children are the right-hand actions. `level={2}` inside an opportunity. |

Header refresh: after an action that changes the opportunity status (freeze, go/no-go, dispatch, apply/discard), call
`window.dispatchEvent(new Event("opp-status-changed"))` after your `reload()` so the stepper and status badge update at once.
