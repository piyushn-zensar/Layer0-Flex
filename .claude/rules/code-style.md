# Code style — small, boring, finished

- Match the surrounding code: naming, comment density, docstring-as-contract at the top of `service.py`.
- Reuse before writing: check `app/core`, the module's own service, and `reference/` (port, don't reinvent).
- Standard library and already-installed packages first. A new dependency needs a reason in the commit message and
  goes in `requirements.txt` (or `requirements-parsing.txt` if only the parser needs it).
- No speculative abstractions: no base class with one subclass, no config for a value that never changes.
- Deliberate shortcuts get a `# ponytail:` comment naming the limit and the upgrade path.
- Non-trivial logic leaves one runnable check: an `if __name__ == "__main__":` assert block, or an assert in
  `tests/test_smoke.py`. Run it before pushing.
- Web: client components fetch through `web/lib/api.ts` (`useApi`, `post`); style with the classes in
  `web/app/globals.css` (owner: Janvia) instead of inline styles; no new npm packages without asking.
