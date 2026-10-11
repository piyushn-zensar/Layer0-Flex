// All walkthrough chapters in order. Each chapter file is owned by the agent/page group it describes.  Owner: Piyush.
import type { TourChapter } from "./types";
import welcome from "./chapters/welcome";
import portfolio from "./chapters/portfolio";
import navigation from "./chapters/navigation";
import intake from "./chapters/intake";
import requirements from "./chapters/requirements";
import trace from "./chapters/trace";
import decisions from "./chapters/decisions";
import inbox from "./chapters/inbox";
import consolidation from "./chapters/consolidation";
import knowledge from "./chapters/knowledge";
import changes from "./chapters/changes";
import recap from "./chapters/recap";

export const CHAPTERS: TourChapter[] = [welcome, portfolio, navigation, intake, requirements, trace, decisions, inbox,
  consolidation, knowledge, changes, recap].sort((a, b) => a.order - b.order);
export const STEPS = CHAPTERS.flatMap((c) => c.steps.map((s) => ({ ...s, chapter: c.id })));
export * from "./types";
export * from "./helpers";
