---
name: contract-change
description: Request a change in a module or file the current teammate does not own (a new or changed service.py function, a template partial, a shared file) without editing it - drafts the request for the owner and a temporary workaround. Use when a task needs another person's module.
---

# Request a contract change

1. Name the owner from `.claude/rules/ownership.md` and the exact file.
2. Draft the request as a short chat message:
   - **What**: function name and signature (or template partial / data field), with the return shape.
   - **Why**: the task ID that needs it and what it unblocks.
   - **Urgency**: needed by (date and time, IST).
3. Propose a non-blocking workaround inside the teammate's own module (for example, call an existing
   service function and adapt the result) so work continues.
4. Only if the teammate says the owner is unavailable and it is blocking: make the smallest additive change
   (new function, no edits to existing ones), commit it separately with `[contract] <owner>` in the message,
   and add a line under "Blocked on / needs from others" in the teammate's tracker.
5. Never change an existing public function's signature in someone else's module.
