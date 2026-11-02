# Unit 10 Structural Interpretation Persistence Independent Acceptance Audit

## 1. Decision

**ACCEPT.**

- Audited implementation checkpoint: `dfe52ba1f78dfdd488862862efb3c3017a668c45`.
- AC-U10-01..30: **30 PASS, 0 FAIL, 0 SUPERSEDED.**
- Findings: **0 BLOCKER, 0 MAJOR, 0 MINOR, 6 INFORMATIONAL (I-1..I-6).**
- No production, schema, test, fixture or prior-contract file was changed by this audit.
  Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1 and Unit 9 audit M-1 remain unresolved and
  distinct. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED. **Unit 11 is NOT
  AUTHORIZED.**

The decision was derived last, from the evidence below. The implementation agent's expected
result and the implementation-reported figures were not used as evidence.

## 2. Audited checkpoint

| Item | Value |
|---|---|
| Implementation checkpoint | `dfe52ba1f78dfdd488862862efb3c3017a668c45` ("implement separate structural interpretation persistence"), also audit starting HEAD = `origin/master` |
| Production under audit | `scripts/projection_store.py` (350 lines), `schema/001-projection-store.sql` |
| Audit starting state | branch `master`, clean worktree/index, no untracked files, `git diff --check` clean; only ignored file `sblgnt-matthew.sqlite3` |

## 3. Contract-freeze checkpoint

`d690209f7dce140b61d0056446cec370afce2edd` ("freeze Unit 10 persistence contract"). The
contract blob at that commit (`6b170f845c8c84b0e1d47873bf4b9b48160d0080`) was retrieved with
`git show` and read as the normative requirement before the implementation was read.

## 4. Proven lineage

`efb0311da039da3c5bf7f2b0704ed2722ac5fbfb` (Unit 9 acceptance) -> `d690209` (freeze) ->
`dfe52ba` (implementation). Each of the two Unit 10 commits has exactly one parent. The
audit commit's sole parent is `dfe52ba`.

## 5. Audit independence methodology

Evidence order: (A) raw XML and Git, (B) an independent reference model and synthetic or
mutated disposable stores, (C) production inspection, (D) the existing test suites, run
last. All audit scripts lived outside the repository (a temporary directory, deleted at the
end), used only the Python standard library, and were run with `python -B`.

- The reference model (`audit_ref.py`) re-implements the candidate and evaluation identity
  serializers from the contract wire description, from the raw XML parsed with
  `ElementTree`, without importing production serialization.
- Nine scripted suites ran: **300 recorded checks, 0 failures**. Per suite: init/drift 46,
  behavior 103, tamper 43, PK/snapshot 32, firewalls 16, lifetime 14, alias 10,
  triggers/LOAD 28, same-ID conflict 8; plus the 3 frozen-literal identity recomputations
  and the 272-anchor corpus comparison.
- Defects in an audit helper (a mutation helper that left a connection open after a failed
  mutation) were fixed in the audit scripts and the affected suites rerun; none was a Unit
  10 defect.
- The existing `tests.test_unit10` was not used as primary evidence for any critical
  criterion and was run last.

## 6. Contract-integrity analysis

- d690209 changed exactly five documentation paths (`AGENTS.md`, `README.md`,
  `docs/architecture/README.md`, the Unit 10 contract, `docs/governance/PHASE-STATUS.md`),
  +356 lines, with no production, schema or test file.
- The contract diff `d690209..dfe52ba` is a **pure append** (`@@ -317,0 +318,142 @@`, 142
  insertions, 0 deletions): sections 1-12 are byte-unchanged; only the non-normative
  section 13 implementation validation was added. The two governance diffs in dfe52ba are
  lifecycle-status edits only.
- The normative contract was therefore reconstructable from Git before the implementation
  existed, and the implementation did not weaken it.

## 7. Implementation changed-path analysis

dfe52ba changed exactly nine paths, matching contract section 3: the five documentation
paths (modified), `schema/001-projection-store.sql` (A), `scripts/projection_store.py` (A),
`tests/README.md` (M), `tests/test_unit10.py` (A). No older production, test, fixture,
schema or audit file was touched. No binary, database or sidecar was committed.

## 8. Independent projection-schema analysis

Read from the DDL and inspected in a freshly bootstrapped store (RAW SQL):

- `application_id` 1297428784 (`0x4d553130`), `user_version` 1, journal mode `delete`.
- Three STRICT tables (`projection_metadata`, `candidate`, `evaluation`), 9 triggers (3 per
  table), 0 views, expected FKs; `UNIQUE(evaluator_label, event_key)`; the metadata row is
  `(1, macula.structural-interpretation-store.v1, sha256 of the LF-normalized DDL)`.
- No source table or source DDL exists in the store (exact table set check).
- Initialization is rejected with bytes unchanged for an existing valid store, an existing
  empty file (stays 0 bytes), an unknown non-empty DB, a source copy, a missing directory,
  and invalid paths (`""`, whitespace, `None`, `5`). An injected bootstrap failure removes
  the new file and a retry succeeds.
- All five path-taking APIs fail closed, file unchanged, on a source copy used as the store,
  an unknown DB, an empty file, and a source copy renamed `.u10`.

## 9. Source/projection trust-zone analysis

With a monkeypatched `sqlite3.connect` and an authorizer trace:

- `store_candidate` opened its source connections only with `mode=ro`, with no write/DDL/ATTACH
  authorizer actions on them; the projection was opened separately for writing; **no ATTACH
  occurred on any connection**; all connections were closed and no sidecars remained.
- A `mode=ro` source rejects DDL even without `query_only`.
- Aliasing is rejected (10 checks): the store as a hardlink of the source, the source as a
  hardlink of the store, the source path itself, and the same file via a case/dot variant,
  for `store_candidate`, `store_evaluation` and `verify_projection_store` with a source.
  Legitimate separate paths still work and the source copy bytes are unchanged.
- Connection closure was traced on nine failure paths (event conflict, forged candidate,
  invalid supersession, empty/garbage/missing source, missing store, corrupted store, write
  onto a corrupted store): all handles closed, no sidecars.
- A crash injected after the candidate INSERT but before the evaluation INSERT rolled back
  both (no orphan candidate), left no sidecar, and a retry succeeded.

## 10. Independent candidate identity reconstruction

From the raw XML alone (SHA-256 `FE1A8FED...C40F4`, 14,115,918 bytes, equal to the DB
`source_sha256`): the Matthew 1:2 S-V-O candidate id is
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`, equal to the frozen
literal. A full-corpus run found 175 Np-Appos and 97 S-V-O anchor nodes; the production
`derive_structural_candidates` output for all **272** matched the independent model
field-for-field (id, kind, derivation, snapshot, scope, evidence, payload): **0
mismatches**.

## 11. Independent evaluation identity reconstruction

The independent serializer reproduced both frozen literals without importing production
encoders: the human vector `eval-sha256:3115087c4d749fa4e1ea2e1f2d16c4d6142798ce2b4505cff930a5f12147257d`
and the supersession vector `eval-sha256:1c39cb8d35b4102e313d3a337b4b43c3ad6b73b5b35093574e4c191de6a46e21`.
Stored identities equal the model identity for an NFD/combining/emoji/trailing-whitespace
note and a label/language case (`el-GR`/`EL-gr`) that must stay exact.

## 12. Candidate round-trip evidence

24 candidates (12 S-V-O, 12 random Apposition; scope lengths 2,3,4,5,6,7,8,22) plus the
three Matthew 1:1 Apposition candidates were stored. Raw SQL showed: JSON is exactly
`{candidate_protocol, candidate}`, canonical (ASCII-escaped, sorted, compact), contains no
surrogate-PK key, and equals the independent model; reloaded frozen DTOs equal the model;
offline and V2 verify pass. Every field, scope/evidence/component order and the payload
survive; nothing is regenerated.

## 13. Evaluation round-trip evidence

Raw SQL showed the evaluation JSON is canonical and ASCII-escaped, preserves CRLF and
leading spaces losslessly, preserves rationale evidence order, and echoes a candidate equal
to the stored candidate row. Reload equals the original DTO; duplicates are byte-identical;
NFD/combining/emoji/trailing-whitespace notes, labels and language case are preserved
exactly; a fresh subprocess reloads the Greek note from the DB alone.

## 14. Append-only/idempotence/conflict evidence

- Identical candidate/evaluation re-store succeeds with the file **byte-identical**.
- Same-ID/different-content (stored row corrupted, genuine input offered; and genuine ID
  with forged altered content as input) is rejected at the production write boundary with the
  file bytes and logical state unchanged and no second record.
- Raw SQL against a valid store (28 checks, both `recursive_triggers` OFF and ON): UPDATE,
  DELETE, `INSERT OR REPLACE`, `REPLACE INTO`, `INSERT OR IGNORE`, UPSERT `DO UPDATE`,
  `UPDATE OR REPLACE` and plain duplicate INSERT on `candidate`/`evaluation`, and every
  mutation of `projection_metadata`, are rejected by the SQL guards; the file is
  byte-identical afterwards.
- Same evaluator + `event_key` with different content is rejected, also on a different
  candidate with no orphan candidate inserted; a different evaluator may reuse the event
  string and opposing judgments coexist; a raw INSERT reusing `(label, event_key)` is
  rejected by the DB; a fresh process confirms the persisted conflict.

## 15. Supersession evidence

The supersession vector id matches the frozen literal. A missing predecessor is rejected
with no partial successor; a valid successor leaves the predecessor row untouched (no
UPDATE) and both are listed with no winner; forks are permitted; a predecessor on another
candidate or from another evaluator is rejected with state unchanged; malformed `supersedes`
values (`not-an-id`, `eval-sha256:xyz`, `5`, `""`) and self-supersession cannot be
constructed; a self-consistent forged DTO with a missing predecessor is rejected at the
store.

## 16. Snapshot/version-history evidence

A private copy of the source with a different `dataset_snapshot.revision` yielded a
candidate with the same scope/payload and a distinct `candidate_id`. Storing it left the
snapshot-A candidate and evaluation rows byte- and rowid-identical; both coexist; the
evaluation of A stays on A and B has none (no same-scope transfer); offline verify passes;
V2 against either single source fails (fail closed, see I-5); an evaluation of A against the
snapshot-B source is rejected. Derivation version `2` has a distinct identity in the
independent model and a self-consistent candidate carrying it is rejected
("unsupported candidate derivation kind or version") with the store unchanged.

## 17. PK-allocation invariance

An independently authored fixture rebuilt the real source DB with **every surrogate PK/FK
remapped by a per-table bijection** (33 mapped columns across 10 tables; multiplicative
permutation modulo `2^31-1`, so PK order is not canonical order), **tables and rows
inserted in reversed order**, then indexes/views/triggers recreated. It passes the accepted
Unit 2 `validate_store` (FK/recursive triggers ON), `PRAGMA foreign_key_check` and
`integrity_check`, and the accepted Unit 3 `source_fidelity` (byte + normalized Expat
reference); its logical digest equals the real DB's (`F2A4A7C4...A78A72`). Findings:

- 17 candidates derived from the remapped source equal (frozen DTO `==`) the real-source
  candidates, with identical ids equal to the independent model.
- Store A (real source, forward insertion) and store B (remapped source, reversed
  insertion) hold **byte-identical** candidate and evaluation JSON, while their projection
  `rowid` allocations differ; evaluation ids are identical; round-trips equal; both stores
  verify offline and V2 against either source.
- No `token_id/node_id/tree_id/element_id/book_id/snapshot_id/file_id/rowid` key appears in
  any stored JSON; scope members are `MAT c:v!n` coordinates only.

## 18. Matthew 1:1 Verbless evidence

Raw XML: one P2CL with `ClType=Verbless`, 8 noun leaves, 0 verb leaves; Np-Appos nodes
`400010010030060` (!3-!8), `400010010030040` (!3-!6), `400010010030020` (!3-!4). All three
were persisted and round-trip equal the independent model; stored JSON has no verb, copula,
`xml_id`, `morph_id`, semantic, confidence or lemma/tense/gloss key; the source still has 0
verb-like tokens in MAT 1:1.

## 19. Matthew 1:2 exact-membership/token-6 evidence

Raw XML: node `400010020050040` (`Rule=S-V-O`, `Head=1`), children S `400010020050012`->!5,
V `400010020070012`->!7, O `400010020080021`->!8,!9; members exactly !5,!7,!8,!9. Token 6's
ancestors are `[400010020060010, 400010020010820, 400010020010821]`: it is not a descendant.
Raw projection storage (candidate and evaluation rows) contains exactly that scope and
components, and the string `1:2!6` appears nowhere. A candidate with `!6` added to the
anchor scope and O: stale-id form rejected by V1; re-identified (self-consistent) form
passes offline V1 and is rejected by V2 ("does not match source-grounded re-derivation or
snapshot"), also when presented to `store_evaluation` (no partial candidate inserted).

## 20. Source DB preservation

Before any audit test and again after every test and regression run (my own measurements):
size 160,968,704; SHA-256 `e52db7e2abdb1c2b9b4f93060312587a1363066378b7a0c9b8fb72475c25ce7e`;
mtime_ns `1793509059488056500`; `user_version` 2, `application_id` 0, journal `delete`; 12
tables, 2 views, 38 indexes, 23 triggers; catalog/index/trigger SHA-256 `56210406...0c8`,
`043161e8...48c`, `7ba5f63d...597`; row counts unchanged (59,891 / 767,429 / 179,675 /
1,134 / 1,134 / 56,488 / 18,329 / 159,391); no sidecars. The before/after baselines are
**identical**. Freshly run read-only: `scripts.source_schema`, `scripts.verify_unit1` and
`scripts.source_fidelity --database` (byte and normalized fidelity PASS; logical digest
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`). Audit tests that needed
a mutable source used private temporary copies (deleted).

## 21. Schema drift/tamper evidence

- Drift variants, all failing closed with the file unchanged: `application_id` 0/wrong;
  `user_version` 0/2/9999; dropped trigger; dropped table; added column; extra
  table/index/view; altered trigger body; `writable_schema` CHECK edit; metadata
  hash/protocol/row changes; WAL journal mode. An untouched copy is accepted.
- **37 tamper mutations** applied to disposable copies (triggers dropped and recreated
  identically): 21 candidate and 16 evaluation corruptions (scope member added/replaced,
  evidence/component order, payload head, derivation version, kind, protocol, snapshot,
  status, extra/missing field, wrong/bool type, tuple-as-string, noncanonical JSON,
  duplicate key, row-key/echo mismatch, deleted candidate, evaluation note/whitespace/
  disposition/protocol/citation order/drop, supersedes JSON vs column, event/label/candidate
  columns, echo, class, language, id). Three (malformed JSON, `NaN`, evaluation malformed
  JSON) were blocked by the DB `json_valid` CHECK at raw-SQL level. In all 34 others,
    offline verify **and** V2 verify raised `QueryError`, a new write attempt was rejected,
    and no API mutated the tampered file. Load behavior differs by design: evaluation loads
    and `list_evaluations_for_candidate` raised `QueryError` in the audit's per-case table,
    while `get_candidate` returned the stored DTO for decodable candidate-content tampers
    (see I-2) and raised `QueryError` for structurally invalid ones.
- A re-identified `!6` forgery inserted raw: offline verify passes (V1 only), V2 verify
  rejects (see I-1).
- LOAD never re-derives: with derivation/evaluation entry points patched to raise,
  `get_candidate`, `get_evaluation`, `list_evaluations_for_candidate` and offline
  `verify_projection_store` succeeded and opened no source DB; `verify_projection_store`
  with a source path re-derived (2 calls), the only explicit V2 path.

## 22. Existing-test results

Run last, unfiltered, against the existing DB read-only after fresh fidelity validation:
`tests.test_unit10`: **48 tests OK with opt-in** (45 fast + 3 integration); default
discovery 45 passed, 3 explicitly skipped (integration flag). Guarded combined regression
(external runner, byte-identical private reuse copy for Unit 3, fresh complete fidelity,
population above 1 MB prohibited, second-build gate disabled, no obsolete-test filters):

| Unit | Ran | Passed | Skipped | Fail/err |
|---|---:|---:|---:|---:|
| 1 | 26 | 26 | 0 | 0 |
| 2 | 56 | 56 | 0 | 0 |
| 3 | 23 | 22 | 1 | 0 |
| 4 | 15 | 15 | 0 | 0 |
| 5 | 20 | 20 | 0 | 0 |
| 6 | 22 | 22 | 0 | 0 |
| 7 | 19 | 19 | 0 | 0 |
| 8 | 51 | 51 | 0 | 0 |
| 8 Amendment 1 | 44 | 44 | 0 | 0 |
| 9 | 42 | 42 | 0 | 0 |
| 10 | 48 | 48 | 0 | 0 |
| **Total** | **366** | **365** | **1** | **0** |

The only skip is Unit 3 `test_u3_01_two_full_builds_and_logical_digests` (`explicit slow
gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build`). Full-source population
attempts blocked by the guard: 0; **full Matthew builds performed: 0** (18 small synthetic
populations only). The totals equal the implementation report but were measured here.
These are regression evidence only.

## 23. Findings by severity

**BLOCKER: none. MAJOR: none. MINOR: none.**

**INFORMATIONAL** (real characteristics, not acceptance failures, none remediated):

- **I-1** Candidate V1 passes a self-consistent re-identified forgery (for example `!6` added
  to scope/O with a recomputed id); only source-grounded V2 detects it. Matches the
  contract's negative vector. Offline `verify_projection_store` alone therefore cannot
  detect it.
- **I-2** `get_candidate` is non-verifying by contract: a decodable but corrupted candidate
  row (for example a changed scope under the same id) loads as a DTO. Evaluation loads
  re-run V1 and fail closed.
- **I-3** `store_candidate` runs full V1/history over existing content but V2 only for the
  new candidate; a V1-valid forged row already in a store does not block an unrelated valid
  write. Verification with a source path is the control.
- **I-4** The physical-separation (alias) check applies in the write APIs and in verify
  with a source path (both verified), not in read-only `get_*` calls.
- **I-5** A store holding records of more than one snapshot cannot pass V2 against any
  single source; this is the contract's "older records stay readable/offline verifiable
  without relinking" behavior.
- **I-6** `json_valid` and the append-only/event guards are DB-level defences in addition to
  production validation: malformed JSON could not even be injected by an owner-level raw
  UPDATE. No action needed.

Existing findings, kept exactly as recorded: **Unit 5 M1**, **Unit 7 audit M1** (and I1-I6),
the **Unit 8 audit M-1** (stale prose) and **Unit 9 audit M-1** (contract section 16
token-6 rule without a dedicated production check) remain unresolved. A self-consistently
corrupted **source** store (Unit 9 M-1) is outside Unit 10's control: V2 relies on the
existing public derivation. Unit 10 does not repair any prior finding.

## 24. AC-U10 matrix

Evidence classes: RS = RAW SOURCE, GC = GIT/CONTRACT, IS = INDEPENDENT SERIALIZER, SQL =
RAW SQL, SYN = SYNTHETIC STORE, ADV = ADVERSARIAL TEST, PI = PRODUCTION INSPECTION, REG =
REGRESSION ONLY. Requirements are abbreviated from the freeze.

| ID | Requirement | Result | Independent evidence |
|---|---|---|---|
| 01 | Separate versioned STRICT store; no source DDL | PASS | SQL, PI: identity/tables/triggers (section 8), exact table set |
| 02 | Exclusive atomic init; existing/unknown/source targets preserved | PASS | ADV: six rejected targets + failure cleanup |
| 03 | Version/catalog/hash drift fails closed | PASS | ADV, SQL: drift variants (section 21) |
| 04 | Both candidate families round-trip every field | PASS | IS, SQL, SYN: 24 + 3 stored, model equality |
| 05 | Human evaluations round-trip losslessly | PASS | SQL, IS, ADV: CRLF/NFD/emoji notes, subprocess reload |
| 06 | Candidate writes need V1 + public V2 | PASS | ADV: stale/re-identified/wrong-snapshot forgeries |
| 07 | Evaluation writes need V1/history + V2, no bypass | PASS | ADV, PI: forgeries, no bypass flags, closed API |
| 08 | Identical duplicates idempotent | PASS | ADV: byte-identical file |
| 09 | Conflicting same-ID content fails, no overwrite | PASS | ADV, SQL: corrupted-row and forged-input cases |
| 10 | Append-only triggers reject UPDATE/DELETE/REPLACE (recursive OFF too) | PASS | SQL: 28 raw statements, both pragma states |
| 11 | Identities recompute after reload; frozen vectors match | PASS | IS: 3 literals from raw XML + model |
| 12 | Exact scope/evidence/payload/component orders, no envelope expansion | PASS | RS, SQL: 272-anchor corpus, 1:2 exact scope |
| 13 | Supersession preserves predecessors/forks; bad edges rejected | PASS | ADV, SQL (section 15) |
| 14 | Global label/event conflicts rejected; judgments coexist | PASS | ADV, SQL (section 14) |
| 15 | Snapshot records coexist, no relink; wrong-source V2 fails | PASS | SYN, ADV (section 16) |
| 16 | Derivation-version distinctness; unknown version rejected | PASS | IS, ADV (section 16) |
| 17 | Changed PK/order source stores and projection row allocations yield equal logical DTOs/IDs | PASS | SYN: independent remap fixture (section 17) |
| 18 | Source `mode=ro`/`query_only`, no ATTACH, alias rejection | PASS | PI, ADV: authorizer trace, 10 alias checks |
| 19 | Real 1:1 stays Verbless/Apposition, no fabricated verb | PASS | RS, SQL (section 18) |
| 20 | Real 1:2 exactly !5,!7,!8,!9, S/V/O, no !6; forgery rejected | PASS | RS, SQL, ADV (section 19) |
| 21 | No semantic entities, roles, invented source IDs/tokens | PASS | PI: static scan of production/DDL/DTO keys, SQL |
| 22 | No theological fields, generated judgment, confidence, ranking | PASS | PI: static scan; stored key inventory |
| 23 | Malformed identity/JSON/types/unknown fields/protocol fail explicitly | PASS | ADV: 37 mutations, malformed ids, non-DTO inputs |
| 24 | LOAD never derives/evaluates; verification distinguishable | PASS | ADV: patched entry points, source-open spy |
| 25 | Handles close on success/error; rollback atomic | PASS | ADV: nine failure paths, injected mid-transaction crash |
| 26 | Source bytes/size/version/catalog/indexes/triggers/fidelity unchanged | PASS | SQL, RS: before/after baselines identical, fresh fidelity |
| 27 | Current Unit 7/8/Amendment/9 and applicable earlier regressions pass unfiltered | PASS | REG (own run, section 22) |
| 28 | Two sole-parent checkpoints, exact paths, clean tree, no binaries | PASS | GC (sections 4, 6, 7) |
| 29 | Protected repositories unchanged; zero full builds | PASS | GC, REG (section 26) |
| 30 | Existing findings stay open; no acceptance/BRW/new Unit before this audit | PASS | GC, PI: governance at dfe52ba and section 23 |

AC-U10-27 is REG by nature and is not claimed beyond it. No critical criterion rests on
`tests.test_unit10` alone.

## 25. Independent audit criteria

All audit-owned criteria passed: contract-freeze integrity, exact path set, independent
serializer vs three frozen literals, 272-anchor corpus, source-store/trust-zone isolation,
append-only SQL guards, same-ID conflicts, event-key integrity, supersession, snapshot
history, surrogate-PK/insertion-order/rowid invariance, tamper (37 mutations), drift,
connection lifetime/atomicity, alias/hardlink rejection, public-API closure, semantic and
scoring firewalls, Matthew 1:1 Verbless, Matthew 1:2 token 6, source-DB preservation,
fresh verifiers, unfiltered regression, protected repositories.

## 26. Protected-repository results

Before and after the audit, `git status` clean: `C:\Works\macula-greek` branch `main`,
`8423afe47b9e8f24b7772e808af45c7159a6fe7e`; `C:\Projects\bible-research-merged` branch
`master`, `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`. Upstream was read-only (no
fetch/pull/checkout/reset/clean); the downstream was not touched.

## 27. Scope confirmation

This audit changed only this report and the Unit 10 lifecycle references in `AGENTS.md`,
`README.md`, `docs/architecture/README.md` and `docs/governance/PHASE-STATUS.md`. It did
not modify `scripts/projection_store.py`, the projection schema, `tests/test_unit10.py`,
`structural_candidates.py`, `evaluated_interpretations.py`, source query/import/schema
modules, prior tests, fixtures or prior contracts, and added no persistence, semantic
projection, BRW integration, deterministic policy, AI evaluator, other books, N1904,
network acquisition or Unit 11. No full Matthew build occurred. Audit temporary files were
removed.

## 28. Final statement

**Unit 10 is IMPLEMENTED / INDEPENDENTLY ACCEPTED (decision ACCEPT).** The separate
append-only persistence boundary preserves the existing structural-candidate and human
evaluation identities and content, never writes the source, and fails closed under forgery,
drift, tamper and aliasing, as independently demonstrated. Six informational observations
are recorded and not remediated. Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1 and Unit 9
audit M-1 remain unresolved. **UNIT 11 IS NOT AUTHORIZED. PHASE REMAINS AUTHORIZED, NOT
COMPLETE OR CLOSED.**
