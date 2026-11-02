# Unit 8 and Amendment 1 Independent Acceptance Audit

Audit-start HEAD: `86c1aad9b2e2563b3c69057f93dd863f60619d5d` (branch `master`, clean).
This audit is read-only with respect to production code, schema, fixtures, contracts,
tests, historical audits, the existing Matthew database and both protected repositories.
Audit-owned scripts and evidence lived outside this repository and were not committed.

## Decisions

### Unit 8

**ACCEPT WITH MINOR FINDINGS** (one MINOR documentation/governance finding, M-1;
no BLOCKER, no MAJOR). All 34 AC-U8 criteria pass; AC-U8-10 and AC-U8-12 pass only
under the contract's own scope narrowing (section 8.2 / 34.1: only the `human` class
has a registered protocol), see the matrix.

### Unit 8 Amendment 1

**ACCEPT WITH MINOR FINDINGS** (the same M-1, which concerns documentation of the
Amendment's own post-reconciliation test state; no BLOCKER, no MAJOR). The Amendment
contract defines no numbered acceptance criteria; the auditor-derived checklist below
passes in full.

The two decisions are independent. Neither accepts Unit 9, authorizes persistence,
semantic projection, BRW integration or any next Unit.

## Audited checkpoints

| Checkpoint | SHA | Parent | Role |
|---|---|---|---|
| Unit 8 implementation | `5bfd1d4b979aa0f4f42f101eeddf72118b46912a` | `8f8b2e7642204378eb0e56e20d096b6233e409b2` | Unit 8 in-memory boundary (8 paths) |
| Unit 8 Amendment 1 | `ac215cb46bc2be814b6a76f671981449128dced2` | `ddd23c4bc51c651aea82722d747c44671f15832a` | S-V-O registry extension (13 paths) |
| Reconciliation | `86c1aad9b2e2563b3c69057f93dd863f60619d5d` | `ac215cb46bc2be814b6a76f671981449128dced2` | Test/governance reconciliation (4 paths; reviewed, not accepted as a Unit) |

## Repository and protected-source baseline

- Repository: `C:\Projects\MACULA-Extract`, `master`, HEAD `86c1aad9...`, clean; no staged,
  unstaged or untracked entries.
- Upstream `C:\Works\macula-greek`: HEAD `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean.
- Downstream `C:\Projects\bible-research-merged`: HEAD
  `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`, clean.
- Source XML (SBLGNT Matthew) SHA-256
  `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.
- Existing Matthew database (git-ignored): 160,968,704 bytes, SHA-256
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
  `user_version=2`, catalog sha `c4a49e86...843dd`, index sha `22519ce2...f47`.
- Runtime: Python 3.13.7, SQLite 3.50.4.

## Audit independence

The audit did not import production code to derive expectations. Raw-source facts were
derived from the pinned XML with audit-owned code; candidate and evaluation identities were
reconstructed from literal JSON wire formats; reduced stores were audit-built. Production
public APIs were then exercised as the system under test, never to produce the oracle.

## Git lineage reconstruction

`8f8b2e7 -> 5bfd1d4 -> 2259575 (Unit 9 freeze) -> ddd23c4 (Unit 9 implementation) ->
ac215cb (Amendment 1) -> 86c1aad (reconciliation)`. Each audited checkpoint has a sole
parent as stated above. 86c1aad touches exactly PHASE-STATUS.md, tests/README.md,
tests/test_unit7.py and tests/test_unit9.py. Amendment 1 changed
`scripts/evaluated_interpretations.py` as its only production file, plus tests, tests/support,
the Amendment contract and plan, Unit 8 contract section 35 and governance/README files,
matching the Amendment's section 9 authorized paths.

## Contract integrity

The Unit 8 contract's AC-U8-01..34 and the Amendment contract are present and coherent.
The Unit 8 contract section 34 records the in-memory implementation authorization; the
Amendment confines itself to the registry (`clause-structure` / `source-rule-s-v-o` / `1`)
and generic V1 clause verification. No contract was edited by this audit.

## Independent raw-source Apposition derivation

For `MAT 1:1!3` the raw XML yields three Apposition candidates (anchor node ids and
independently reconstructed candidate identities):

- `400010010030020` -> `sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c`
- `400010010030040` -> `sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f`
- `400010010030060` -> `sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220`

Production re-derivation matches all three exactly.

## Independent raw-source S-V-O derivation

For `MAT 1:2`, node `400010020050040`: S = `...012` (token !5), V = `...012` (token !7),
O = `...021` (tokens !8, !9); exact scope is `!5,!7,!8,!9`. Token `!6` is leaf `δὲ`
(`400010020060010`) under a different `Conj13CL` ancestor (`400010020010820`) and is
excluded. Independent candidate id
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087` equals the frozen
fixture and production.

## Independent candidate identity reconstruction

Wire format: `json.dumps(v, ensure_ascii=True, separators=(",",":"), allow_nan=False)`
UTF-8, SHA-256, prefix `sha256:`, over
`["macula.structural-candidate.v1", [7 snapshot fields], kind, derivation kind, derivation
version, [scope node, [refs]], [[role, kind, node]...], payload]`. Reconstruction matched
production for all four real candidates and for two reduced stores whose surrogate keys
were remapped (affine and descending) with shuffled/reversed insertion.

## Independent evaluation identity reconstruction

Wire format `["macula.evaluated-structural-interpretation.v1", candidate_id, class, label,
protocol_id, protocol_version, disposition, [[kind, id]...], [note_text, note_lang],
event_key, supersedes]`, prefix `eval-sha256:`. The frozen Unit 8 section 34.2 vector was
reproduced from literal JSON bytes:
`eval-sha256:b13074925b58de0b3595d088e7f6c505906d1f34500e1af78bb017aa6eaf83b0`
(note `"  α\r\n"` preserved without normalization). Every field was shown to change the id.

## V1 audit

Both stale-id (class A) and self-consistent recomputed-id (class B) forgery were applied to
every field of both candidate families (231 checks, Part 2). Class A is rejected with
"does not recompute". Class B is rejected by V1 when structurally invalid. Registry
neighbours (version 2, wrong derivation, unknown kind, cross-family derivation) are rejected
at V1 and at `create`. Unknown protocol id/version/class/disposition are rejected and the
closed signature rejects confidence/probability/score/rank/actor/action/patient/theology/
source_fact keywords.

## V2 audit

V2 re-derives through the public `derive_structural_candidates` API on every call (spy
showed repeated public calls, no private Unit 7 helper). Explicit V1-passes/V2-rejects gate
cases: Apposition `scope.drop_last` and an S-V-O envelope with token 6 in V are rejected with
"does not match source-grounded re-derivation"; snapshot field changes give "candidate source
snapshot mismatch"; a forged first token gives "candidate not found in bound source store".
A nonexistent database yields an infrastructure `QueryError`, not not-found. Offline
`verify` is V1/history only; with `db_path` it also performs V2. Every member token of each
real candidate (12 lookups) re-derives its candidate.

## Closed registry audit

The registry is a closed frozenset of exactly two 6-tuples: Apposition `source-np-appos`/`1`
and `clause-structure`/`source-rule-s-v-o`/`1`, both under `human-structural-adequacy`/`1`,
class `human`. Neighbour and cross-family tuples fail at V1 and `create`. No
deterministic-policy protocol is registered.

## Apposition backward compatibility

The 5bfd1d4 module was loaded from git and compared with HEAD for all three real Apposition
candidates across accepted, undetermined and rejected dispositions: all evaluation ids and
record fields are byte-identical (13 compatibility checks pass). The 5bfd1d4 module rejects
the S-V-O candidate; HEAD accepts it. The only observable difference on pre-existing
negative paths is the local-PK error wording, which now also names the Unit 9 DTO
(informational, intended by the Amendment); protocol, class and citation error text is
identical.

## Rationale/citation audit

Positive canonical order is required. Token `MAT 1:2!6`, its leaf node, the conjunction
ancestor, wrong kind, reversed order, duplicates, token-before-node, and
accepted/rejected with empty citations are all rejected; `undetermined` with none is
accepted (109 checks, Part 3). Note text is preserved exactly; language tags are checked.

## Human evaluation semantics

Label 1-128 without control characters; event-key regex; note and BCP47 language checks;
non-human classes rejected ("only human has a registered protocol"); every field enters
the identity.

## Event-key/idempotence audit

Idempotent resubmission returns an equal record; a different key gives a distinct record;
reuse of `(label, key)` with different content conflicts (same or cross candidate); the same
key under another evaluator is accepted.

## Supersession/history audit

Chains A, A<-B, A<-B<-C accepted; missing, cross-candidate, cross-evaluator and
self-supersession predecessors rejected; a forged cycle is rejected by id recomputation
first (the cycle branch itself is reachable only via a hash collision, see I-4); forks are
permitted; there is no head/latest/consensus API. Opposing evaluators coexist; candidates
and DTOs remain frozen and unmutated.

## Surrogate-PK invariance

Two reduced stores with affine and descending PK remaps, shuffled/reversed insertion order
and different process hash seeds yield identical candidate and evaluation identities.
No local PK appears in any identity or DTO of Unit 8.

## Read-only source boundary

SQLite authorizer traces over the real database and both reduced stores (20 connections
each) show only `file:///...?mode=ro` URI connections with `query_only=ON` and only
`SQLITE_PRAGMA/READ/SELECT` actions. INSERT/UPDATE/DELETE/CREATE/DROP/ALTER, `PRAGMA
user_version`, `journal_mode=WAL`, VACUUM/REINDEX/ANALYZE and `query_only=OFF`+INSERT were
all blocked. The real database size, SHA-256 and mtime were unchanged and no sidecars were
created. Four audit probe expectations about `ATTACH DATABASE '<new file>'` did not hold: the
shared Unit 3/4 helper `source_fidelity.open_readonly` permits ATTACH of a new side file.
Unit 8 never issues ATTACH and the main databases were unchanged (I-5).

## Persistence boundary

Static search of the production modules and schema/contract files found no write, DDL,
ATTACH or persist patterns in Unit 8 code; no evaluation/rationale/disposition/supersession
structures in the schema; `evaluated_interpretations` is imported only by its own tests;
no `eval-sha256` in any JSON/SQL asset. Evaluation is in-memory only.

## Semantic/theological firewalls

No semantic-role, Actor/Action/Patient/Event/Result/Identity/Property entity, confidence,
probability, score or theological interpretation exists in production or DTOs. Word hits are
benign (`event_key`, `identity`, `IDENTITY_PROTOCOL`).

## Matthew 1:1 Verbless case

Matthew 1:1 yields only the three Apposition candidates and no clause candidate. The verbless
P2CL `400010010010082` has ClType Verbless, 8 leaves and 0 verb leaves. Evaluated as
`undetermined`, no verb/copula fields exist.

## Matthew 1:2 exact-scope/envelope-forgery case

Exact scope is `!5,!7,!8,!9`; genuine derivation of `MAT 1:2!6` is `()`. An Apposition-kind
envelope (anchor `400010020050040`, empty children, scope 5-9, token 6 included):

- stale id: V1 "does not recompute";
- recomputed id: V1 accepts (even with a token-6 citation), `create` rejects via V2 on the
  real store and both reduced stores, offline `verify` passes V1 only, and `verify` with
  `db_path` rejects.

An S-V-O-kind envelope with token 6 in S is V1-ok and V2-rejected (13 checks, Part 5).

## Reconciliation checkpoint review

86c1aad replaced only assertions whose sole premises were superseded lifecycle states:
Unit 7's no-S-V-O expectations (three fast tests and the integration test, renamed
`test_post_unit9_svo_preserves_unit7_exact_scope_invariants`) and Unit 9's
pre-Amendment rejection test (renamed `test_unit8_amendment_accepts_registered_svo_candidate`).
Current invariants are retained: exactly one `clause-structure`/`source-rule-s-v-o`/`1`
candidate for !5/!7/!8/!9, `MAT 1:2!6 -> ()`, scope `[5,7,8,9]` with token 6 excluded,
invariance under annotation mutation, and the unchanged forged-envelope rejection test.
No production, schema, fixture or contract change. The reconciliation is appropriate.
Residual stale prose is recorded as M-1.

## Unit 8 AC-U8-01..34 matrix

| Result | Criteria |
|---|---|
| PASS | AC-U8-01..09, 11, 13..34 (32 criteria) |
| PASS (scope-narrowed per section 8.2/34.1) | AC-U8-10, AC-U8-12 (only `human` has a registered protocol; no deterministic-policy protocol exists, so deterministic-evaluator criteria hold vacuously and the rejection of other classes was verified) |
| FAIL | none |

**34 PASS (2 scope-narrowed) / 0 FAIL.**

## Amendment 1 matrix

The Amendment contract has no numbered acceptance criteria. The following checklist is
**auditor-derived** from its sections 2-8 and is not a contract artifact.

| # | Derived criterion | Result |
|---|---|---|
| A1 | Registry extended only to the two named tuples; closed; neighbours rejected | PASS |
| A2 | Protocol id/version, criterion, identity formula and V1/V2 semantics unchanged | PASS |
| A3 | V1 independently verifies clause scope, evidence order, payload, Head, components and candidate id | PASS |
| A4 | V2 re-derives through the public Unit 9 API; token-6 forgery rejected | PASS |
| A5 | Citation and rationale ordering rules unchanged and enforced for S-V-O | PASS |
| A6 | Matthew 1:2 S-V-O evaluates; Matthew 1:1 Verbless stays `undetermined` | PASS |
| A7 | Apposition evaluation ids byte-identical to 5bfd1d4 | PASS |
| A8 | Candidate unmutated; DTOs frozen; no persistence/projection/semantic fields | PASS |
| A9 | Authorized paths only (section 9); Unit 9 production and tests, Unit 7 tests, schema, fixtures untouched | PASS |
| A10 | Test counts documented match actual (41 fast + 3 integration) | PASS |

**10 PASS / 0 FAIL.**

## Existing test reruns

`python -B -m scripts.verify_unit1` and `python -B -m scripts.source_schema` pass (schema
version 2). With the real integration environment variables, no skips:
`tests.test_unit8` 51 OK (50 fast + 1 integration), `tests.test_unit8_amendment1` 44 OK
(41 + 3), `tests.test_unit9` 42 OK, `tests.test_unit7` 19 OK.

Audit-owned checks: Part 1 74/74, Part 2 231/231, Part 3 109/109, Part 4 43/47 (the 4
non-passing are the ATTACH probe expectation, I-5), Part 5 13/13, Part 6 2/2, Part 7
(Apposition compatibility) 17/18 (the one non-pass is my expectation of identical
local-PK error wording, I-6). Totals: 494 checks; 489 met expectation; 5 are the
informational deviations above.

## Guarded combined regression

A guarded runner (outside the repository) loaded the whole suite and replaced Unit 3's
`setUpClass` with a byte-identical private temporary copy of the existing database plus a
fresh read-only fidelity verification, with a guard raising on any raw-population above
1 MB. Loaded and ran **318** tests (unit1 26, unit2 56, unit3 23, unit4 15, unit5 20, unit6 22,
unit7 19, unit8 51, amendment1 44, unit9 42): **317 passed, 0 failures, 0 errors, 1 skip**.

- The only skip is `test_unit3.Unit3Tests.test_u3_01_two_full_builds_and_logical_digests`,
  reason "explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build"
  (`MACULA_UNIT3_SECOND_BUILD` stayed unset).
- Obsolete-test filters used: **none** (all 86c1aad-reconciled tests pass unfiltered).
- Full Matthew builds: **none**; no full-source population attempts.

## Findings

### BLOCKER

None.

### MAJOR

None.

### MINOR

**M-1 - Stale "fails by design / filtered in memory" statements remain after 86c1aad.**
86c1aad renamed and fixed `tests/test_unit9.py::test_unit8_rejects_new_candidate_without_registry_amendment`
(now `test_unit8_amendment_accepts_registered_svo_candidate`, passing), but several current
or historical documents still state that the test fails by design and is filtered:
`AGENTS.md` (Unit 8 Amendment 1 implementation and stop boundary), `PHASE-STATUS.md`
(Amendment 1 section), the frozen Amendment contract section 8.3, the Amendment
implementation plan, and the historical portion of `tests/README.md` (which 86c1aad
supersedes with a "Current post-Amendment regression rule"). No behavior is affected. This
audit's governance update corrects only the live AGENTS.md statement with a pointer to
86c1aad; frozen contracts and historical prose are intentionally not rewritten.

### INFORMATIONAL

- **I-1** Ref `57f2f7f9a17794c56d34148c0f7b212f2c712a76` is an agent-harness checkpoint ref
  (not an ancestor of `master`); it is not part of the audited lineage.
- **I-2** Contract section 12.2/13 says "any token ref" while section 34.1 and Amendment
  section 4 say "first scope token"; behavior is equivalent for genuine candidates
  (verified for every member token).
- **I-3** V1 accepts a self-consistent Apposition-kind candidate with zero children and an
  S-V-O anchor; V2 is the mandatory source gate and offline `verify` is V1/history only by
  design.
- **I-4** Supersession cycle detection is unreachable in practice because id recomputation
  fails first; `prior_records` are V1-validated only in `create` (documented in 34.1).
- **I-5** The shared Unit 3/4 helper `source_fidelity.open_readonly` permits `ATTACH` of a
  new side file under `mode=ro`/`query_only=ON`. Outside Unit 8, which never issues ATTACH;
  the main databases were unchanged.
- **I-6** The pre-existing local-PK rejection message now also names the Unit 9 DTO
  (intended by the Amendment).
- **I-7** Documented test counts (50+1, 41+3) match actual counts.
- **I-8** Unit 5 M1 and Unit 7 audit M1 are distinct, unresolved, and not affected by Unit 8.

## Existing database preservation

The Matthew database is byte-identical before and after (size, SHA-256, `user_version=2`,
catalog/index digests). No `-wal`, `-shm`, `-journal` or new SQLite file exists; the only
`.sqlite3` is the pre-existing git-ignored `sblgnt-matthew.sqlite3`. Audit temporary
directories were removed; two older, unrelated `macula-unit3-*` temp directories predating
this audit were left untouched.

## Protected repositories

`C:\Works\macula-greek` (HEAD `8423afe4...`) and `C:\Projects\bible-research-merged`
(HEAD `0e4c9baa...`) are unchanged and clean; the source XML SHA is unchanged. No fetch,
pull, checkout or other mutation was performed.

## Scope confirmation

Changed by this checkpoint: this report and minimal governance status text only
(`docs/governance/PHASE-STATUS.md`, `AGENTS.md`, `README.md`, `docs/architecture/README.md`).
No production, schema, fixture, contract, historical-audit or test path changed. Unit 9
status, Phase status (AUTHORIZED), Unit 5 M1 and Unit 7 audit M1/I1-I6 are unchanged.

## Final statements

Unit 8: ACCEPT WITH MINOR FINDINGS. Unit 8 Amendment 1: ACCEPT WITH MINOR FINDINGS.
Phase remains AUTHORIZED, not COMPLETE or CLOSED.

UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.

NO PRODUCTION REMEDIATION WAS PERFORMED.
NO PERSISTENCE WAS AUTHORIZED.
NO SEMANTIC PROJECTION WAS AUTHORIZED.
NO BRW INTEGRATION WAS AUTHORIZED.
NO NEXT UNIT WAS AUTHORIZED.
