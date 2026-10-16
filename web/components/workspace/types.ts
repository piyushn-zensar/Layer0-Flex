// The three panes of Requirement Traceability (J-18, C-34): shared names, so the layout, the messages and the panes agree.  Owner: Janvia.
export type Pane = 1 | 2 | 3;
export const PANES: Pane[] = [1, 2, 3];
export const PANE_NAMES: Record<Pane, string> = { 1: "Original RFP", 2: "Requirement register", 3: "Product mapping and responses" };
export const isPane = (n: unknown): n is Pane => n === 1 || n === 2 || n === 3;

/** The address a pane shows alone at (a detached window): /opportunities/{bid}/trace/pane/{n}. */
export const paneWindowPath = (bid: string, pane: Pane) => `/opportunities/${bid}/trace/pane/${pane}`;
/** True on a detached pane's address: that window has no top bar, bid header or walkthrough. */
export const isPaneWindowPath = (path: string | null | undefined) => /\/opportunities\/[^/]+\/trace\/pane\/[123]\/?$/.test(path ?? "");
