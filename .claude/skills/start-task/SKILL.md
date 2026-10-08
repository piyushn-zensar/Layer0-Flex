---
name: start-task
description: Start a Layer 0 task by its ID (P-xx, A-xx, J-xx) - pull the latest main, read the task and the files it touches, mark it "doing" in the teammate's tracker, and plan the change. Use when a teammate says "start P-04", "/start-task A-03", or "what should I work on next".
---

# Start a task

1. `git pull --rebase` (stop and report if the tree has uncommitted changes that conflict).
2. Identify the teammate: `git config user.name` → Piyush, Atharv or Janvia.
3. No ID given? Open `team/tracker/<name>.md` and propose the first `todo` task whose dependencies
   (in `team/PLAN.md`) are `done`. Ask before continuing.
4. Read the task row in `team/PLAN.md`, the matching section of `Documents/technical-architecture.md`,
   and the `service.py` docstring of every module the task touches.
5. Check ownership (`.claude/rules/ownership.md`). If the task needs a file the teammate does not own,
   say which, and offer the `contract-change` skill.
6. In `team/tracker/<name>.md`, set the task status to `doing` (only that row).
7. Give a short plan: files to change, the check you will run, and what "done" means for this task.
   For larger tasks, offer to hand the work to the `module-builder` agent.
