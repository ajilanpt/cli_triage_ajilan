# Session handoff — 2026-09-23

Transient working note for the next Claude Code session, not a lab deliverable. Safe to
delete once phase 11 is underway and this context is no longer needed.

## Where we are
Phases 00–10 are complete and pass `uv run lab.py check NN`. Everything is committed (see
`git log`). Next: `uv run lab.py next` → phase 11 (fusion and the arbiter).

## Environment additions this session
- **PyTorch and sentence-transformers are now installed** (system Python, not a venv —
  `uv run python` here resolves to the real system interpreter at
  `C:\Users\Data Analyst\AppData\Local\Programs\Python\Python313\python.exe`, so `uv pip
  install` doesn't work; use that interpreter's own `-m pip install` directly if another
  dependency is needed). Both are recorded in `requirements.txt`.
- The `sentence-transformers` model (`all-MiniLM-L6-v2`) is cached locally under
  `C:\Users\Data Analyst\.cache\huggingface\hub` after phase 09 — no re-download needed.

## A real performance trap, hit twice
Reopening/reseeking the same big `.tgz` archive (square-okhttp, ~497MB) multiple times via
`tarfile` hangs or is extremely slow on this machine — measured, not theoretical. The fix,
used in `ci_triage/infra.py`... actually the fix lives in `ci_triage/sequences.py`'s
`read_all_run_logs`: read the whole archive **once** into an in-memory list of `maven.log`
text, then reuse that list for every subsequent pass (deterministic-test detection, verdict
computation, etc.). Any new phase-11+ code that touches the raw archives again should import
and reuse `read_all_run_logs`/`project_test_sequences`/`build_project_documents` rather than
re-deriving its own archive-reading loop.

## What phase 11 inherits
- **`ci_triage/contracts.py`'s `Evidence` dataclass** is the shape every observer must emit
  into before fusion combines them. None of the three observers (07/08/09) have actually been
  rewritten to emit `Evidence` records yet — phase 10 only defined the contract and the
  independence rules; wiring the observers to actually produce `Evidence` instances is
  implied but not yet done, and phase 11 will likely need it.
- **The independence finding matters concretely for fusion**: observers 2 (sequence) and 3
  (retrieval) are correlated (same root source, phase 05's TRUSTED-run gate over the same 3
  raw archives) — see `decisions/10-independence.md`. A naive "count how many observers
  agree" fusion strategy would double-count that correlation. Phase 11's comparison of fusion
  strategies should weight or gate on this.
- **Observer scope mismatch, still unresolved**: observer 1 (tabular) works across all 25
  FlakeFlagger projects; observers 2 and 3 only have real data for 3 projects (the ones with
  raw archives). Phase 11's fusion/evaluation will need to decide how to handle cases where
  only 1 of 3 observers has anything to say (e.g. any of the 22 projects without raw
  archives) — this hasn't been designed yet.

## Working-style note (still true, worked well this session)
Decision-dialogue method: explain the concept with the running incident, ask one question,
wait for a real answer, don't reveal expected/reference results before a prediction is
written down. The builder benefits from concrete worked examples (actual real data pulled
from the archives, not hypotheticals) when a concept doesn't land on the first explanation —
several times this session, showing one real log/number resolved confusion faster than more
explanation would have. When the builder says "I don't know" to a prediction question, that's
a legitimate answer to record, not a stall — don't push for a guess.
