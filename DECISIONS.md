# Decisions

Index of `decisions/*.md`. One line each: what was decided, and what it cost.

A decision with no cost was not a decision — it was a preference. If you cannot name what
you gave up, the interview for that phase is not finished.

| Phase | Decision | What it cost |
|---|---|---|
| 00 | system may auto-rerun the failing test on low confidence, but never release/stop | gives up a fully "hands-off" system in exchange for keeping release/stop strictly human — accepted because rerun is reversible and has no effect outside the CI run |
