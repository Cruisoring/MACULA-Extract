# Phase Status

## MACULA Greek Linguistic Source Store Phase

**Status:** AUTHORIZED

Authorized phase scope: SBLGNT Matthew source-store vertical slice.

### Unit 1 — Source Contract & Fixture Freeze
**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Unit 1 is limited to source contract, source verification, frozen fixtures, and associated tests. It does not authorize SQLite schema/importer/exporter or semantic projection.

Independent acceptance audit record: [docs/audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md) — Decision: ACCEPT. This acceptance does not authorize Unit 2, which remains NOT STARTED / NOT YET IMPLEMENTATION-AUTHORIZED.

Current completed scope: source contract + fail-closed source verification + frozen fixtures + fidelity constraints + Unit 1 tests only.

The Phase remains **AUTHORIZED**, not COMPLETE or CLOSED. Unit 1's independent acceptance (see audit record above) does not authorize Unit 2.

## Unit 1 execution evidence

- Implementation repository: `C:\Projects\MACULA-Extract` (hyphenated).
- Starting branch: `master`.
- Starting HEAD: `NONE` (authorized unborn repository, no prior commits).
- Starting index/staged and unstaged changes: empty.
- Eleven existing untracked bootstrap files were explicitly allowed: `.gitignore`, `AGENTS.md`, `README.md`, the contract, two architecture documents, two governance documents, two fixtures, and `tests/README.md`.
- No bootstrap or empty commit was created. The sole successful Unit 1 checkpoint must be the first root commit, containing the thirteen reviewed bootstrap/Unit 1 files.
- Upstream evidence: `C:\Works\macula-greek`, revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
- Authorized source: `SBLGNT/nodes/01-matthew.xml`.
- Expected and verified actual SHA-256: `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.
- Upstream and downstream worktrees remained clean; downstream HEAD remained `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`. No downstream governance audit was repeated.
- Historical Architecture Spike text remains unchanged; only three Markdown trailing-space hard breaks at lines 29–31 were removed to satisfy first-commit diff hygiene. Comparison with the supplied historical snapshot confirmed no other text differences.

### Actual validation

Commands run from the implementation repository:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_*.py" -v
git diff --cached --check
```

Results: source verifier PASS; complete project suite **26 tests PASS** (including T1–T8 and negative regressions); candidate diff hygiene PASS. Both Python files also passed an AST syntax check with `feature_version=(3, 10)`. No third-party framework, dependency installation, SQLite execution, or upstream acquisition was used. No separate static type-check or database round-trip is claimed.

Primary: 1 sentence, 1 tree, 26 nodes, 25 Node-to-Node relations, 8 noun tokens, 342 source attributes, 200 leaf attributes (25 per token), ClType=Verbless, 0 verb leaves, and distinct source surface/normalized values.

Boundary: tree/Start order `[6,5]`, exact ancestry membership `[5,7,8,9]`, interior envelope token `6` excluded.

### Acceptance matrix

| Criterion | Result | Evidence |
|---|---|---|
| AC-U1-01 | PASS | Correct root, master, unborn HEAD and initial Git state recorded; bootstrap work preserved. |
| AC-U1-02 | PASS | Fixed revision in machine-readable contract and T1. |
| AC-U1-03 | PASS | Exact authorized relative path pinned. |
| AC-U1-04 | PASS | Expected checksum frozen and actual source bytes verified. |
| AC-U1-05 | PASS | Single-file allowlist; drift and expansion rejected. |
| AC-U1-06 | PASS | Primary fixture frozen and validated. |
| AC-U1-07 | PASS | Primary shape, relations, attributes and Verbless checked by T2–T4. |
| AC-U1-08 | PASS | Eight token IDs/refs/morphIds and Greek surfaces checked by T5. |
| AC-U1-09 | PASS | Punctuated surface/Unicode remains distinct from NormalizedForm. |
| AC-U1-10 | PASS | Missing/present-empty contract and placeholder-negative regression. |
| AC-U1-11 | PASS | Actual ordering counterexample validated by T6. |
| AC-U1-12 | PASS | Exact membership and envelope exclusion validated by T7. |
| AC-U1-13 | PASS | Seven ordering/membership concepts frozen and verified. |
| AC-U1-14 | PASS | Case/namespace and identifier distinctions verified by T8. |
| AC-U1-15 | PASS | FunctionalTag/FormalTag retained as distinct source fields. |
| AC-U1-16 | PASS | Explicit forbidden semantic mappings; no generated roles/copula/events. |
| AC-U1-17 | PASS | No schema/database/importer/exporter/projection introduced. |
| AC-U1-18 | PASS | Entire available project suite: 26 tests PASS. |
| AC-U1-19 | PASS | Reviewed candidate passes diff hygiene. |
| AC-U1-20 | PASS | Only thirteen authorized bootstrap/Unit 1 files in candidate. |
| AC-U1-21 | PASS | No unexpected unstaged, untracked, ignored or staged files. |

Post-checkpoint verification must confirm one root commit without parents, the same authorized path set, and clean worktree/index/untracked state. The checkpoint hash is reported with the execution result, not fabricated inside its own commit.
