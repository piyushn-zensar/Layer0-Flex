# Git workflow — three people on `main`, no merge conflicts

- Work on `main` in **small commits** and push often (at least every 1–2 hours of work).
- Before every push: `git pull --rebase` → `.venv/Scripts/python -m pytest -q` → `git push`.
- Never `git push --force`, never `git reset --hard` on shared history, never rewrite pushed commits.
- On a rebase conflict in a file you do not own: keep the owner's pushed version (during `git pull --rebase`,
  `git checkout --ours <file>` is the *upstream* side; `--theirs` is your local commit) and tell the owner.
  In a file you own: resolve, re-run tests, `git rebase --continue`.
- Commit message: `[<task ID>] <module>: <what changed>`, e.g. `[A-03] matching: cache matcher answers for Syracuse`.
  Add `[contract]` when a `service.py` public function is added or changed.
- Commit your tracker update with the work it describes.
- Never commit `.env`, `data/store/`, `.venv/`, or API keys. Do commit `data/llm_cache/` and `data/layout_cache/`.
- Only commit or push when the teammate asks you to.
