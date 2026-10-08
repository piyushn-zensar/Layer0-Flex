---
name: sync
description: Safely share work with the team - run tests, review the diff against ownership rules, commit in small pieces with task IDs, update the tracker, pull --rebase and push. Use when a teammate says "sync", "push my work", "commit this", or at the end of a work session.
---

# Sync with the team

Only commit and push because the teammate asked (this skill being invoked counts).

1. `git status` — list what changed. Anything under `.env`, `data/store/`, `.venv/`? Stop and fix `.gitignore` use.
2. `.venv/Scripts/python -m pytest -q` — must pass. If it fails, fix what you caused or stop and report.
3. Review against `.claude/rules/ownership.md` (or run the `boundary-reviewer` agent). Files outside the
   teammate's paths are not committed; report them.
4. Update `team/tracker/<name>.md`: status of the tasks touched, a one-line log entry with today's date.
5. Commit in small, logical pieces: `[<task ID>] <module>: <what>` (add `[contract]` if a `service.py`
   public function changed). Include the tracker update with the work it describes.
6. `git pull --rebase`. On conflict follow `.claude/rules/git-workflow.md`; re-run the tests after the rebase.
7. `git push` (never `--force`).
8. Tell the teammate: commits pushed, anything others must pull for (new dependency, model change → reseed,
   new cache files), and post-worthy notes for the team chat.
