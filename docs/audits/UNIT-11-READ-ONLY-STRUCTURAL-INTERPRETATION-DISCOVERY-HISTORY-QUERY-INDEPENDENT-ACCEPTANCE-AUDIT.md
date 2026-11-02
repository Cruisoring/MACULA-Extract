# Unit 11 Independent Acceptance Audit

Read-Only Structural Interpretation Discovery & History Query Boundary

## 1. Decision

**ACCEPT WITH MINOR FINDINGS.**

- Findings: **0 BLOCKER, 0 MAJOR, 1 MINOR (M-1), 5 INFORMATIONAL (I-1..I-5).**
- AC-U11-01..37: **37 PASS, 0 FAIL, 0 SUPERSEDED.**
- Unit 11 lifecycle becomes **IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS)**.
- Nothing is remediated. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED. Unit 12 remains
  **NOT AUTHORIZED**. Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1 and Unit 9 audit M-1 stay unresolved
  and distinct from M-1 below.

## 2. Audited checkpoint and parent

| Item | Value |
|---|---|
| Audited implementation checkpoint | `deb83908b45738f1c7252d60b9fbaefda372719d` (`implement Unit 11 discovery and history queries`) |
| Sole parent (contract freeze) | `38e0d89f01a8dc4fd9ad83a967a2e2f56da06351` |
| Implementation diff | exactly `AGENTS.md`, `README.md`, `docs/architecture/README.md`, the Unit 11 contract (pure append of section 36; sections 1-35 untouched), `docs/governance/PHASE-STATUS.md`, new `scripts/projection_query.py` (283 lines), `tests/README.md`, new `tests/test_unit11.py` (670 lines) |
| Not touched | schema, Unit 10 production, candidate/evaluation modules, source code, fixtures, historical audits |

## 3. Starting repository state

Branch `master`, HEAD `deb8390`, one commit since the freeze. Staged and unstaged changes were
clean, and the only ignored artifact was `sblgnt-matthew.sqlite3`. `git diff --check` and
`git diff HEAD^ HEAD --check` were silent. No other database, WAL, SHM or journal file existed in the repository.

## 4. Audit independence methodology

All audit code lived outside the repository (session directory) and was not committed.

- **Raw-XML oracle** (stdlib `ElementTree`) parsed the pinned Matthew XML for descendant leaves,
  tree siblings, `Rule`/`ClType`/`Head`/`Start`/`End`. It did not use the repository parser or query layer.
- **Independent identity wire**: my own serializer reproduced the `candidate_id` of all 52 real
  candidates derived from chapters 1, 2, 10 and 12, and the frozen S-V-O id `129c3970...`.
- **Independent logical model** (`Spec`) computes, from the declared candidates and evaluations
  only, the expected discovery, evaluations, supersession edges, graph leaves and
  histories/components. Every Unit 11 API result was compared with the model across 7 scenarios (A-G).
- **Disposable stores** were built through the public Unit 10 writers. Corruption used raw SQL on copies
  with the append-only triggers dropped and then restored.
- **Runtime tracing**: a `sqlite3.Connection` subclass with an authorizer, `sys.addaudithook`
  for `open`/`sqlite3.connect`, and an OS rename-after-call test (Windows refuses to rename a file that has an
  open handle).
- Evidence types: TYPE A = independent oracle, TYPE B = implementer-style or private-hook probe,
  TYPE C = existing regression.

## 5. Contract integrity review

The contract was frozen at `38e0d89`. The implementation commit only appends section 36. That
section records implementation evidence and weakens no frozen criterion. Production, tests and
contract are byte-identical between the checkpoint and this audit's changes.

## 6. Complete production/API inspection

`scripts/projection_query.py` exports exactly 11 functions, `ProjectionQueryError`,
`ScriptureSelector`, `SupersessionEdge` and `StructuralInterpretationHistory` (frozen
dataclasses; no rowid, path or timestamp field). There is no write, derive or evaluate API.
Module-level mutable state is empty. A static scan found no `LIKE`/`GLOB`/`startswith`, SQL
string matching, `min`/`max` envelope logic, `Start`/`End` use, or derivation call.

Every call runs `_load()`:

1. `store._open(path)`: URI `mode=ro`, `query_only=ON`, `foreign_keys=ON`, `recursive_triggers=ON`;
   application id, `user_version=1`, catalog equality, metadata/DDL hash and `journal_mode=delete` all checked.
2. `store._contents(db)`: decodes and V1-validates every candidate row and every evaluation
   row (candidate echo, evaluation id recompute, history checks).
3. `_check_graph`: dangling, self, cross-candidate, cross-evaluator and cyclic supersession.
4. All errors are wrapped as `ProjectionQueryError`, except M-1 below.

Discovery is an in-memory filter over fully validated candidates using integer-tuple member
coordinates. Ordering keys use only logical fields, with `evaluation_id` as the last tie-breaker.

## 7. Independent scripture-selector analysis

- `MAT`, `MAT 1`, `MAT 1:2` and `MAT 1:2!n` selectors were swept against raw-XML-derived expectations.
- Token sweep `MAT 1:2!1..21`: the result equals the raw-XML expectation. `!6` and `!11` are empty; `!5/!7/!8/!9` return the S-V-O candidate.
- Integer coordinates, not string prefixes: `MAT 1:2` vs `MAT 1:20`, chapter 1 vs 10 vs 11, and token `!5` vs `!50` are all exact, in the real pool and in adversarial raw-inserted candidates.
- Malformed selector forms (non-selector objects, `None`, tuples, zero or negative numbers, over-long ints, bad ids) raise `ProjectionQueryError` before any database is opened. Exception: M-1 and I-2.

## 8. Independent persisted-discovery analysis

Discovery matched the model on 263 calls per store across scenarios A-G (18 candidates, 8
evaluations). A cross-verse candidate (`!8,!9` of 1:2 plus `!1` of 1:3) is found by both verses and by
chapter 1, and its scope is not expanded. Interior non-member tokens (gaps) are never discovered.
Candidates with no evaluations are always discoverable.

## 9. Raw-source Matthew 1:2 derivation

Raw XML node `400010020050040` is `Cat=CL`, `Rule=S-V-O`, `Head=1`, `Start=5`, `End=8`, with direct
children S (`...0012`), V (`...0070012`) and O (`...0080021`). Its descendant leaves are exactly
`MAT 1:2!5, !7, !8, !9`. My independent id computation matches the frozen fixture id.
Matthew 1:2 has 3 real clause candidates in the persisted pool (`!1-4`, S-V-O, `!10,12-18`).

## 10. Token-6 exclusion evidence

Token `MAT 1:2!6` (`conj`, node `400010020060010`) is a tree sibling under `Conj13CL`, not a descendant
of the anchor. `!6` discovery is empty in every scenario, and `!6` does not appear in any
history DTO repr or component ref. The real-Matthew integration test (run read-only by me) also passes.
A self-consistent forged candidate containing `!6` is a trust-boundary limit, recorded as I-1.

## 11. Candidate-first / unevaluated-candidate evidence

Discovery works with no `candidate_id` known in advance, and an empty valid store returns `()`.
Scenario A (candidate with zero evaluations): discoverable, and its history has empty tuples. Absent ids
return `None`, and a known candidate with no evaluations returns `()` (never confused with absent).

## 12. Evaluation visibility evidence

Scenario B: accepted, rejected and undetermined evaluations coexist and are returned unmodified.
No disposition is selected, merged, voted or resolved. Superseded records remain returnable by id and in
candidate listings.

## 13. Independent supersession graph analysis

Edges equal the independent model for all 7 scenarios (chains, forks, multi-evaluator candidates). Edges
come from the `supersedes` logical field only. Forged **hash-valid** records (written with
`compute_evaluation_id` and a raw INSERT) for dangling, cross-candidate, cross-evaluator and
cross-candidate-and-evaluator predecessors are all rejected on every API. Self-supersession and
cycles cannot be physically forged with valid content-addressed ids (ids hash `supersedes`), so they appear
as id mismatches in real files. The private `_check_graph` defence was also probed directly with forged
objects: 2-cycle, 3-cycle and self rejected, linear chain valid (TYPE B).

## 14. get_evaluation_history component analysis

`get_evaluation_history` returns the weakly connected component over supersession edges. Starting from any
member returns the same ordered component; an unrelated same-candidate evaluation returns only itself, and
other candidates or evaluators are never mixed in. This matches the model in all scenarios.

## 15. Unsuperseded graph-leaf analysis

Leaves equal the model (forks give several leaves; an isolated evaluation is a leaf). No API or field is named
or documented as current/final/canonical/winning. The names in `pq` source containing "current" are a local
loop variable and a negating docstring.

## 16. PK / insertion-order / path invariance

Four equivalent stores: reversed insertion order, random insertion order, scrambled explicit rowids
(10^9..10^12), and a path with spaces and Unicode. Each gave identical logical results over 263 calls
while physical rowids differed (up to 18/18 candidates and 8/8 evaluations). No DTO or repr contains a
rowid. Presentation order is a function of logical keys only (inspected: no rowid, time, listdir or index use).

## 17. Store corruption/tamper analysis

- 47 distinct mutation classes were each probed with all 15 API calls (705 probes), with every probe
  raising `ProjectionQueryError`. Classes: `user_version`, `application_id`, extra table/index, dropped or
  altered trigger, metadata hash/protocol drift, WAL journal mode, candidate JSON (array, invalid, non-canonical,
  duplicate key, extra/missing field, wrong protocol/kind/derivation version, token-6 scope without id recompute,
  status change, key vs echo mismatch), evaluation JSON equivalents, evaluation column vs echo mismatches
  (candidate_id, supersedes, label, event_key), orphan evaluation, hash-valid forged graph defects,
  byte garbage, truncation, a non-database file, and an empty file.
- **Leaf-level JSON fuzz**: 312 single-point candidate mutations and 398 evaluation mutations (value
  edits, key deletes, list reverse/drop/duplicate, ids not recomputed). Result: 0 successes, 0 non-`ProjectionQueryError`
  exceptions.
- A corrupt candidate row breaks even selectors that would not match it, so it can never be silently skipped.
- Source DB used as a projection store, directory as path and missing file: error, and the missing file is not created.

## 18. Read-only/authorizer results

Every Unit 11 call opened the projection with `mode=ro` (never `mode=rw`). Authorizer actions on the projection
connections over 15 API calls were only `SQLITE_PRAGMA`, `SQLITE_SELECT` and `SQLITE_READ`: no write, DDL, ATTACH,
DETACH, transaction or savepoint action. With `query_only` forced OFF inside the owned connection, `INSERT`, `UPDATE`,
`DELETE`, `CREATE`, `VACUUM` and `journal_mode=WAL` all failed ("attempt to write a readonly database"), so `mode=ro` is
enforced independently of the pragma. File SHA-256, mtime and directory listing were unchanged, and no
WAL/SHM/journal file appeared.

## 19. Connection-lifetime evidence

Connections are closed (tracked `close()` calls) and the file is renamable by the OS afterwards for
success, empty, exact-not-found, known-candidate-empty-history, corrupt candidate, corrupt evaluation,
corrupt graph and missing-file outcomes. Malformed ids and selectors open no connection.

## 20. Source-database-independence evidence

`derive_structural_candidates` was armed to raise during the query battery (scenario G: all selectors, histories
and evaluation histories): none raised. The audit hook observed no open of the source DB, `macula-greek` or any XML file;
the only non-projection open was the Unit 10 DDL file. After the source copy was deleted, the persisted candidate was still discovered.
The `:memory:` DDL-catalog connection of Unit 10 was not used on the query path in my trace (cached).

## 21. Matthew 1:1 Verbless firewall

Raw XML: clause `400010010010082` has `Rule=P2CL`, `ClType=Verbless`, 8 `noun` leaves and 0 verbs. Discovery
returns exactly the 3 Apposition candidates; every member token is a raw-XML noun leaf. No history DTO
value or field contains verb, copula, "is", Actor, Action, Patient, Event, Result, Identity or Property.

## 22. Semantic/scoring/consensus firewall

`projection_query.py` contains no confidence, probability, score, rank, weight, majority, consensus, winner,
canonical, preferred or latest vocabulary (the single "ranks" hit is a negating docstring). It has no
`len()`/`Counter`/`sum()` synthesis. Returned objects contain no scoring field. Clause component roles
(`subject-component`, `verbal-component`, `object-component`) pass through verbatim. The one field name matching
my keyword scan is Unit 8's existing `event_key` (an idempotency key), not a semantic Event.

## 23. Existing Unit 11 test-quality assessment

`tests/test_unit11.py` (33 tests, 1 opt-in) covers: Matthew 1:2 `!5/!7/!8/!9` hit and `!6` miss (TYPE A against
a disposable source and the real-Matthew opt-in), integer-vs-prefix scope variants (`1:2/1:20`, `!5/!50`, chapters 1/11),
no-evaluation discovery, all dispositions, supersession forks and components, read-only plus a tracked authorizer and
write-attempt test, connection closure, store identity failures, record corruption, source-removed independence,
PK/insertion/path invariance and a no-semantic-field check.

Strengths: independent oracle for token membership and the unevaluated-candidate path; byte-level read-only
assertions.

Weaknesses (all non-blocking): graph defects (test_27) patch `__post_init__` and `_contents`, so they are TYPE B
(my forged hash-valid raw rows cover them as TYPE A); test_48 scans only pq DTO field names; the corruption matrix
is narrower than the audit's 47 classes plus fuzz; the full-Matthew integration test is opt-in.

## 24. AC-U11-01..37 matrix

| AC | Result | Independent evidence |
|---|---|---|
| 01 candidate lookup by logical id only | PASS | no rowid in any DTO/repr; API takes ids only |
| 02 evaluation lookup by logical id only | PASS | same |
| 03 candidates self-consistent and recompute id | PASS | V1 on load; 52 real ids reproduced by my wire; fuzz 312/312 |
| 04 evaluations pass V1/history and recompute id | PASS | fuzz 398/398; 47-class matrix |
| 05 PK/insertion/path invariance | PASS | 4 stores x 263 calls identical |
| 06 selector discovery without ids | PASS | sweeps A-G |
| 07 token discovery iff exact scope contains ref | PASS | tokens 1..21 vs raw XML; `!5` vs `!50` |
| 08 verse discovery, no scope expansion | PASS | 1:2/1:20; cross-verse candidate |
| 09 chapter/book discovery by intersection | PASS | ch 1/10/11; `MAT` selector |
| 10 zero-evaluation candidates included | PASS | scenario A |
| 11 identifies only, selects no winner | PASS | scenario B; source scan |
| 12 no envelope/min-max/prefix/LIKE/range | PASS | AST/regex scan; interior-gap and `!50` probes |
| 13 verse `MAT 1:2` finds S-V-O | PASS | raw oracle |
| 14 tokens `!5,!7,!8,!9` find it | PASS | raw oracle |
| 15 `!6` does not | PASS | all scenarios |
| 16 exact scope `[5,7,8,9]` preserved | PASS | scope equals raw leaves |
| 17 all dispositions listed | PASS | scenario B |
| 18 opposing evaluations coexist | PASS | scenario B |
| 19 superseded records remain queryable | PASS | scenarios C/D |
| 20 edges from logical fields, no PK/time | PASS | 4-store invariance; forged graph |
| 21 forks represented, unresolved | PASS | scenario with fork |
| 22 leaves only, no "current" | PASS | graph leaf equality; source scan |
| 23 SQLite-enforced read-only; no write/DDL/ATTACH | PASS | `mode=ro` URI; authorizer; forced-OFF write attempts fail |
| 24 optional source verification keeps source unchanged | PASS | Unit 11 offers none (deferred); source SHA unchanged |
| 25 invalid store fails, never empty | PASS | version/app-id/catalog/hash/WAL/garbage cases |
| 26 corruption/mismatch fail closed incl. unvalidatable candidate | PASS | 47 classes plus fuzz 710/710 |
| 27 malformed/cross/self/cyclic supersession fails | PASS | forged hash-valid rows; `_check_graph` probes (TYPE B for cycles) |
| 28 connections close on every path | PASS | tracked close plus OS rename test |
| 29 no confidence/probability/score/rank/consensus | PASS | source and DTO scans |
| 30 no universal current; no PK/time precedence | PASS | ordering source inspection; invariance |
| 31 no semantic entity or role projection | PASS | DTO field/value scans |
| 32 Matthew 1:1 Verbless, no fabricated verb | PASS | raw XML and DTO scan |
| 33 no creation/write API | PASS | API inventory (11 read functions) |
| 34 Unit 10 schema/append-only/write unchanged | PASS | DDL byte-identical; Unit 10 tests 48 pass |
| 35 Units 1-10 behaviour unchanged | PASS | 376-test regression, all green |
| 36 no later-unit scope | PASS | diff of 8 authorized paths |
| 37 governance actions separate | PASS | freeze, implementation and this acceptance are three commits |

## 25. Findings grouped by severity

### BLOCKER
None.

### MAJOR
None.

### MINOR

**M-1 Oversized digit strings in verse/token string selectors raise `ValueError`, not `ProjectionQueryError`.**
`_parse_ref` (`scripts/projection_query.py`, `int(part)` at line 80) runs outside the `_load`
`except` wrapper. A verse or token ref string with more than 4300 digits makes Python's int-conversion limit raise
`ValueError` from `list_persisted_candidates_for_verse` and `list_persisted_candidates_for_token`
(for example `"MAT 1:" + "9"*5000`). 40-digit values correctly give `ProjectionQueryError`, and `ScriptureSelector`/chapter
inputs are already guarded. The call still fails closed: no result, no connection opened, no file created. Only the
documented exception type is wrong. Not remediated.

### INFORMATIONAL

- **I-1** The projection-only path accepts a self-consistent forged candidate that was raw-inserted past the
  writer (for example an id-recomputed S-V-O candidate containing `!6`); `!6` discovery then returns it. This is the
  same limit as Unit 10 I-1: V1 is projection-only and source-grounded V2 is deferred (contract open question 7).
  Unit 10's public writer and `verify_projection_store(path, source)` both reject the same candidate.
- **I-2** A selector built with `object.__new__(ScriptureSelector)` (unset slots) leaks `AttributeError`. This is programmer
  misuse of a frozen DTO, not reachable through the public constructor.
- **I-3** Every call validates the whole store, so any corrupt row anywhere fails every query, including pure candidate
  discovery. This is stricter than the contract requires (fail-closed by design) and costs O(store) per call.
- **I-4** Cycle and self-supersession rejection cannot be demonstrated on real stores with valid ids, and the
  implementer's test patches private hooks. The defence is exercised via private `_check_graph` probes only (TYPE B).
- **I-5** `projection_query` exposes the module attributes `store`, `structural` and `evaluated` (not part of the public inventory).

## 26. Tests actually run

All with `PYTHONDONTWRITEBYTECODE=1`, no Unit 3 discovery and no full Matthew build.

| Command | Result |
|---|---|
| `python -B -m scripts.verify_unit1` | exit 0 |
| `python -B -m scripts.source_schema` | exit 0 |
| `python -B -m unittest tests.test_unit11 -v` | Ran 33, OK (1 skipped: opt-in integration) |
| `python -B -m unittest tests.test_unit10 tests.test_unit11 -v` | Ran 81, OK (4 skipped) |
| `python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4 tests.test_unit5 tests.test_unit6 tests.test_unit7 tests.test_unit8 tests.test_unit8_amendment1 tests.test_unit9 tests.test_unit10 tests.test_unit11 -v` | Ran 376, OK (25 skipped, all "opt-in read-only existing full-Matthew integration") |
| `MACULA_UNIT11_INTEGRATION=1 MACULA_MATTHEW_DB=<repo>\sblgnt-matthew.sqlite3 python -B -m unittest tests.test_unit11.Unit11MatthewIntegrationTests -v` | Ran 1, OK (read-only; variables removed afterwards) |

Independent audit harness (outside Git): section A 26/26 PASS; section B 23 PASS plus 2 FAIL, both M-1; section C 82 PASS
plus 1 harness keyword false positive (`event_key`, see section 22). The harness itself had several setup defects that were fixed in the harness, not in the repository.

## 27. Existing DB preservation

`sblgnt-matthew.sqlite3`: 160,968,704 bytes, mtime `2026-11-01T04:57:39.4880565Z`, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`, `user_version` 2 and 75 `sqlite_master` rows, identical
before and after the audit (hashed with shared-read access because another process holds a handle). No
projection database existed in the repository. All audit databases were disposable copies outside it. A stray ignored
`scripts/__pycache__` created during the audit was removed.

## 28. Protected-repository preservation

- `C:\Works\macula-greek`: `main` at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean, unchanged.
- `C:\Projects\bible-research-merged`: `master` at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`, clean, unchanged.

## 29. Scope confirmation

This audit changes only this report and the governance/index documents (`docs/governance/PHASE-STATUS.md`,
`docs/architecture/README.md`, `README.md`, `AGENTS.md`). No production code, `tests/test_unit11.py`, schema, fixture or Unit 11
contract was modified, no finding was remediated, and no projection store, persistence, semantic projection, BRW integration,
localization, UI or Unit 12 was added.

## 30. Final statement

Unit 11's discovery and history queries match an independent raw-XML oracle and logical model, are projection-only,
SQLite-enforced read-only, fail closed under tampering and enforce the exact-scope token-6 exclusion and the
Verbless and epistemic firewalls. The single MINOR finding is a wrong exception type on pathological input, with
no incorrect data returned. **Unit 11 is IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS).** The Phase
remains AUTHORIZED, and Unit 12 is NOT AUTHORIZED.
