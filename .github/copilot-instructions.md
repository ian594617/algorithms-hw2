# Copilot instructions

## Project requirements

- Read `SPEC.md` and `PLAN.md` before implementing a feature. If they conflict or
  leave a behavior ambiguous, clarify the requirement before coding.
- Use only the Python standard library for application code.
- Never use `dict`, `set`, or Python's built-in `hash()` in `src/`. Hash string keys
  with the specified Horner recurrence:
  `h = (31 * h + ord(character)) % capacity`.
- Generate short codes from sequential IDs encoded with base62, never from hashes.
- Keep both hash-table implementations on the same public interface. Preserve
  explicit exceptions and HTTP status codes from `SPEC.md`; do not hide errors behind
  successful responses or silent fallbacks.

## Tests and implementation

- For new behavior, write focused boundary tests before production code and run them
  to confirm the expected failure. Then implement the behavior and run `make test`.
- Do not delete, weaken, or rewrite tests to make an implementation pass. If a test
  expectation is incorrect, explain why and make the smallest evidence-based correction.
- Re-run the relevant tests after changes. Also run `make experiment` for experiment
  changes and exercise web routes locally for server changes.
- Keep manual checks, such as Codespaces port visibility and phone access, marked
  incomplete until a person verifies them.

## Git and issue workflow

- Work one issue at a time on `feature/<issue-number>-<short-name>` branched from
  `develop`.
- Preserve pre-existing working-tree changes. Stage only files belonging to the
  current issue, and verify the staged file list before committing.
- Use commit subjects in the form `Step N: concise description (#N)`. Push the
  feature branch, merge it into `develop`, then push `develop`.
- If a branch switch or merge would overwrite local work, or if a merge conflicts,
  stop and report the problem instead of discarding changes or resolving it silently.
- Comment on the relevant GitHub issue with verified progress. Do not close an issue
  while user review or a required manual check is still outstanding.
