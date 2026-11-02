# Unit 7 Independent Acceptance Audit

## Decision

**ACCEPT WITH MINOR FINDINGS** (BLOCKER: 0; MAJOR: 0; MINOR: 1; INFORMATIONAL: 6)

This audit concerns Unit 7 only. It does not accept Unit 3, Unit 4 or Unit 6,
does not remediate Unit 5 M1, and does not authorize Unit 8.

## Audited checkpoint

- Repository: `C:\Projects\MACULA-Extract`; branch `master`.
- Checkpoint (HEAD at audit start): `9331d8a4bee4d20cb96f07752e45f578b0d31f39`.
- Sole parent: `b7cc92e6e42979a64919edd173ff886591552344`.
- Subject: `implement structural candidate boundary`. No later commits exist.
- Changed paths (`git diff-tree`): `M README.md`, `M docs/architecture/README.md`,
  `A docs/architecture/UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md`,
  `M docs/governance/PHASE-STATUS.md`, `A scripts/structural_candidates.py`,
  `M tests/README.md`, `A tests/test_unit7.py`.
  Schema, importer, query modules, contracts, fixtures and earlier tests are unchanged
  (`git diff HEAD^ HEAD` over those paths is empty).
- Starting cleanliness: worktree/index clean, no untracked files; `git diff --check` and
  `git diff HEAD^ HEAD --check` clean; only the ignored `sblgnt-matthew.sqlite3` present.

## Audit independence

Implementation-report statements were treated as claims only. Evidence classes:

- **Raw-source independent derivation:** `xml.etree.ElementTree` over the upstream
  Matthew XML, with no repository code, before any production call.
- **Independent synthetic reconstruction:** a separately authored schema-v2 fixture
  (two stores, different allocations) with an independently coded expected-result
  model and an independently coded identity hash.
- **Production inspection:** direct reading of `scripts/structural_candidates.py` and
  the `scripts/source_query.py` primitives it reuses.
- **Existing test reruns:** run last and not relied upon alone.

All throwaway audit scripts and stores were kept outside the repository and removed.

## Contract integrity

- The Unit 7 contract was a user-created **untracked** file before the checkpoint, so
  Git holds no pre-implementation blob (single add commit; no dangling or reflog copy).
  The recorded original raw SHA-256 could not be reproduced because the exact original
  status/transition wording is not recoverable (see **M1**).
- Independent full reading of the committed contract found all 40 criteria
  `AC-U7-01..40` (exactly 40 `^AC-U7-NN$` lines), and the MUST/MUST NOT language,
  Start/End-envelope prohibition, `[5,7,8,9]` exclusion of token 6, Verbless fixture,
  no-confidence, no-evaluation, no-persistence, opaque-ID, snapshot-binding and
  identity-PK prohibitions all present and unweakened.
- Corroboration: the SHA-256 of the committed text from `## 1. Purpose` up to the
  `40. IMPLEMENTATION AUTHORIZATION` heading equals the "before/after" slice digest the
  implementer recorded (`EE5082A4...EE05C92`). That recorded value is itself an
  implementation claim, so this is corroboration, not independent proof.
- Section 41 is purely additive: it states the executable API, DTOs, identity protocol,
  error semantics and stop line, and narrows nothing in sections 1-39.
- `PHASE-STATUS.md` diff removes no lines; every other unit status is unchanged.

## Independent source verification

- `C:\Works\macula-greek`: HEAD `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean.
- `SBLGNT/nodes/01-matthew.xml`: 14,115,918 bytes; SHA-256
  `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4` (matches expectation).
- 56,488 `Node` elements; no duplicate `nodeId`.

## Matthew 1:1 independent Apposition derivation

Derived from raw XML by walking the actual parent chain from leaf `MAT 1:1!3`
(`nodeId` `400010010030010`). Ancestors nearest-first: `...030011` (N2NP),
`...030020`, `...030040`, `...030060` (all `Np-Appos`), then `NPofNP` x2, `Np2P`,
`P2CL` and root `S`.

| # | anchor nodeId | Rule | direct children (XML order) | descendant leaf refs (canonical) |
|---|---|---|---|---|
| 1 | `400010010030020` | Np-Appos | `400010010030011`, `400010010040011` | !3, !4 |
| 2 | `400010010030040` | Np-Appos | `400010010030020`, `400010010050020` | !3, !4, !5, !6 |
| 3 | `400010010030060` | Np-Appos | `400010010030040`, `400010010070020` | !3, !4, !5, !6, !7, !8 |

These are the Np-Appos ancestors of `MAT 1:1!3`.

**Production comparison** (`derive_structural_candidates(real_db, "MAT 1:1!3")`): exactly
three candidates, nearest-first, with anchor, scope node, scope refs, children, evidence
(anchor then children) and snapshot fields all equal to the independent expectation.
For all eight tokens of 1:1, production Np-Appos ancestry equals the independently
walked raw-XML ancestry.

## Candidate identity independent verification

Canonical input (read from code and `contract section 41`): JSON array
`[protocol, [family, edition, repository_uri, revision, manifest_sha256, relative_path,
source_sha256], kind, derivation_kind, derivation_version, [scope_node, [ordered refs]],
[[role, kind, source_node_id]...], [anchor, [ordered children]]]`, serialized with
`ensure_ascii=True`, compact separators, `allow_nan=False`, UTF-8, then SHA-256.
It contains none of: token/node/tree/element/book/snapshot/file PKs, DB path, clock,
UUID, `hash()`, object repr, PID or insertion order.

Independently serialized and hashed outside the production helpers, with snapshot
values read via my own SQL and member/child data taken from raw XML, all three real
IDs reproduced exactly:

1. `sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c`
2. `sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f`
3. `sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220`

Sensitivity (via DTOs, compared with production helper and independent hash): the ID
changes with derivation version, revision, manifest, source SHA, scope node, scope
membership, evidence identity, evidence order and child payload order. It does not
change across `PYTHONHASHSEED` 0, 1, 12345 and random, a relocated and renamed DB
file, or the reallocated store.

## Surrogate-PK invariance

Two independently built temporary stores (`A`, `B`) with identical logical provenance,
source node IDs, refs, topology, sibling order and memberships, but different `element_id`, `tree_id`, `snapshot_id`, `book_id`, `file_id`, `node_id`
and `token_id` allocations, with node and token PK order reversed or permuted in B.
Node PK order of the two siblings `np-b`/`np-a` differs from sibling order in B.
Candidate ID, kind, derivation,
status, snapshot, scope node, ordered scope refs, evidence and payload were equal across
A and B and also equal an independently modelled expectation. Inherited
`TokenResult` surrogate fields differ, as expected under open Unit 5 M1.

## Source snapshot binding

`SourceSnapshot` is read from the selected token's linked `dataset_snapshot` and
`source_file` rows: family `MACULA Greek`, edition `SBLGNT`, repository URI, revision
`8423afe4...`, manifest SHA-256 `894CD81C...` (matches the Unit 1 contract file hash
I recomputed), relative path `SBLGNT/nodes/01-matthew.xml` and file SHA-256
`FE1A8FED...`. No snapshot PK is used. Changing revision, manifest or file SHA changes
identity; DTOs are frozen so nothing is upgraded in place.

## Matthew 1:1 Verbless safety

Fresh raw-source facts: MAT 1:1 has one CL with `Rule=P2CL`, `ClType=Verbless`;
8 leaves, all `Cat=noun`; zero verb leaves. Production output for 1:1 consists only of
the three Apposition candidates whose payloads contain node IDs and token refs. No
verb token, copula, "is", Action, Event, Actor, Patient, Identity, Property, fake
ref, `xml:id` or `morphId` is produced.

## Matthew 1:2 exact membership

Raw XML node `400010020050040`: `Rule=S-V-O`, `Start=5`, `End=8`, direct children
`...050012` (S), `...070012` (V), `...080021` (O). Recursive descendant leaves:
`MAT 1:2!5, !7, !8, !9`. `MAT 1:2!6` has ancestors `...010820`, `...010821` only, so it
is a non-descendant despite the numeric envelope. Production `_scope` on the real
store returns exactly `[5,7,8,9]`. It reads materialized `node_token_membership` via
`query._members` and never uses `Start`/`End`. The synthetic Np-Appos nodes, whose
non-member token 6 lies numerically inside their span, also exclude it.

## Epistemic boundary

`AppositionCandidate` output is a structural proposal only: it carries node IDs,
token refs, derivation `source-np-appos`/`1` and status `candidate`. Head, Cat, Frame,
Ref, SubjRef, Notes, English, Mandarin and Gloss are never selected into candidate
fields (`_SNAPSHOT_SQL` reads only snapshot/file provenance). Production contains no
Actor/Action/Patient/Event/Result/Identity/Property semantics (hits are only
identifiers such as `_identity_bytes`). `status` accepts only `candidate`;
`accepted`/`rejected` and unknown kinds raise `QueryError`; no confidence or
probability exists.

## Read-only / persistence boundary

- Production connects through the accepted query layer
  (`source_query._connect_readonly` is `source_fidelity.open_readonly`:
  `file:...?mode=ro`, `PRAGMA query_only=ON`). An SQLite authorizer installed on the
  connections opened per derivation saw only SELECT/READ/PRAGMA actions; no write,
  DDL, ATTACH or DETACH. INSERT/UPDATE/DELETE/CREATE through the production
  connection fail with "attempt to write a readonly database". Two connections are
  opened per derivation and both are closed.
- A Python audit hook recorded no `.xml` file opened during derivation.
- `schema/001-source-store.sql`, `source_query.py`, `source_schema.py`,
  `source_importer.py` and `source_fidelity.py` unchanged; `SCHEMA_VERSION` 2.
  No candidate/evidence/scope tables, sidecar DB, cache, JSON persistence or migration.
- No XmlPro dependency/reuse (only pre-existing `xmlpro_dependency: false` guards).
- Source IDs are only used in exact-equality SQL parameters and as opaque strings; no
  slicing, parsing or decoding anywhere in the module.

## Test independence assessment

- **TYPE A:** this audit's raw-XML and independent-fixture comparisons; the
  fixed-literal serialization check in `test_identity_serialization_is_explicit_utf8_and_sha256`;
  Matthew integration expectations (hard-coded anchors/children/scopes that agree with
  my raw derivation).
- **TYPE B:** DTO/contract tests, ordering tests, snapshot-binding and sensitivity tests.
- **TYPE C:** none found as sole support for a critical claim. Negative tests mutate
  real stores and hit the production paths (`_scope`, resolver, ancestors, snapshot).
- PK-invariance test reallocates all five inherited local IDs plus node/token PK order.

## Tests actually run

| Command | Result |
|---|---|
| `python -B -m scripts.verify_unit1` | exit 0 |
| `python -B -m scripts.source_schema` | exit 0 |
| `python -B -m unittest tests.test_unit7 -v` | 19 run, 16 OK, 0 fail/error, **3 skipped** (opt-in Matthew integration) |
| same with `MACULA_UNIT7_INTEGRATION=1` | 19 run, 19 OK, 0 skips, DB unchanged |
| `tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests tests.test_unit6.Unit6FastTests` | 46 OK |
| `tests.test_unit1 tests.test_unit2` | 82 OK |

Unit 3 tests were not rerun (no Unit 3 files changed; the second full build was not
triggered and `MACULA_UNIT3_SECOND_BUILD` was not set). Python 3.13.7.

## Findings

### BLOCKER
None.

### MAJOR
None.

### MINOR

**M1 - Pre-implementation contract bytes cannot be independently reconstructed.**
The Unit 7 contract was untracked user work before the checkpoint, and the single
commit adds it whole. Git/reflog/dangling-object inspection found no prior blob, and
the implementer's recorded original raw SHA-256 `96FF803B...0988` could not be
reproduced because the exact original status/transition wording is not recoverable
(about 700 plausible variants tried). The claim "sections 1-39 unchanged" is therefore
corroborated (matching slice digest, complete re-read, all 40 AC and prohibitions
present) but not independently provable. It does not invalidate Unit 7: every
contract boundary was independently tested against the implementation as committed.
It remains unresolved.

### INFORMATIONAL

- **I1:** `derive_structural_candidates` reads through two separate read-only
  connections (`get_source_evidence`, then candidate construction), not one snapshot.
  Harmless for an immutable source store, but not atomic.
- **I2:** DTO construction validates only kind and status. It does not recompute
  `candidate_id`, and role/kind `Literal`s are static-only, so `replace()` can produce
  inconsistent DTOs. There is no deserialization path today.
- **I3:** Matthew integration tests are opt-in and skip by default; their expected
  values are literals, not parsed from raw XML at test time (this audit did that).
- **I4:** Scope comes from the materialized, schema-validated membership table (not
  re-derived per query). Agreement with raw XML was verified for the three 1:1
  anchors and `400010020050040` only; broad membership correctness rests on the still
  pending Unit 3 acceptance.
- **I5:** `_resolve_source_node_id` hard-codes book `MAT` (inherited Unit 5 behavior).
- **I6:** Unit 5 M1 persists in inherited `TokenResult`; Unit 7 DTOs contain no local IDs.

## AC-U7 contract acceptance matrix

Contract wording per `AC-U7-NN` in the contract; evidence is this audit's own.

| AC | Requirement (short) | Result | Independent evidence |
|---|---|---|---|
| 01 | Facts vs candidates distinct classes | PASS | Separate frozen candidate DTOs/module, not `SourceEvidence`/`NodeResult`. |
| 02 | Derivation identity/version | PASS | `source-np-appos` / `1`, present and in identity hash. |
| 03 | Source-oriented evidence refs | PASS | `EvidenceRef` role/kind/source node ID. |
| 04 | Identity independent of surrogate PKs | PASS | Stores A/B; independent hash. |
| 05 | Bound to source snapshot | PASS | Snapshot fields read from linked rows; match own SQL. |
| 06 | Exact source scope retained | PASS | Scope equals raw-XML descendant leaves. |
| 07 | No envelope from discontinuous membership | PASS | Token 6 excluded in real and synthetic scopes. |
| 08 | Deterministic evidence order | PASS | Anchor then children in sibling order; scope canonical. |
| 09 | Deterministic generation | PASS | Equal across hash seeds, relocated DB, reallocated store. |
| 10 | Logically idempotent | PASS | Repeated derivation equal. |
| 11 | Missing evidence fails closed | PASS | Missing membership / anchor omits token raise `QueryError`. |
| 12 | Ambiguity fails closed | PASS | Ambiguous source node ID raises `QueryError`. |
| 13 | Navigation errors/cycles not successes | PASS | Cycle, dangling parent, NULL ID raise `QueryError`. |
| 14 | No source-store mutation | PASS | Authorizer: no write actions; DB hash unchanged. |
| 15 | No schema mutation | PASS | Schema/source modules unchanged; version 2. |
| 16 | Not evaluated/accepted/rejected | PASS | Status only `candidate`; others raise. |
| 17 | No synthetic confidence | PASS | No such field/value. |
| 18 | MAT 1:1 Verbless, no fabricated verb | PASS | Raw: P2CL/Verbless, no verb leaves; no verb output. |
| 19 | No auto Action/Event from 1:1 | PASS | Output only 3 Apposition candidates. |
| 20 | S not unconditionally Actor | PASS | No such mapping. |
| 21 | V not unconditionally Action/Event | PASS | No such mapping. |
| 22 | O not unconditionally Patient/Result | PASS | No such mapping. |
| 23 | P not unconditionally Identity/Property | PASS | No such mapping. |
| 24 | Frame roles not converted | PASS | Frame never read. |
| 25 | MAT 1:2 scope `[5,7,8,9]` | PASS | Production `_scope` on `400010020050040`; no S-V-O candidate kind exists. |
| 26 | Token 6 excluded | PASS | Same. |
| 27 | Node IDs opaque, not decoded | PASS | No slicing/parsing in module. |
| 28 | No ID slicing as hidden topology | PASS | Identity uses opaque IDs only. |
| 29 | Annotations distinct from payload | PASS | No source annotations copied. |
| 30 | Implicit candidates not masquerading as tokens | PASS | None generated. |
| 31 | No invented surface/ref/xml:id/morphId | PASS | None generated. |
| 32 | Scripture vs structural order distinct | PASS | Fixture child order differs from lexical and PK order. |
| 33 | Payload semantics/version ownership | PASS | Typed payload owned by derivation version. |
| 34 | Unknown kinds fail | PASS | `QueryError` on construction and identity. |
| 35 | Localization cannot change semantics | PASS | No localized field enters candidates. |
| 36 | No theological interpretation | PASS | None produced. |
| 37 | Snapshot change cannot silently upgrade | PASS | Revision/manifest/file SHA change the ID. |
| 38 | Traceable candidate to evidence to snapshot | PASS | Node IDs and snapshot fields exposed. |
| 39 | Reallocated PKs equivalent | PASS | Stores A/B equal at source level. |
| 40 | Prior regressions intact | PASS | Units 1, 2, 4, 5, 6 suites and verifiers pass; Unit 3 sources unchanged, not rerun. |

40 passed, 0 failed.

## Independent audit criteria

| Criterion | Result | | Criterion | Result |
|---|---|---|---|---|
| AC-IA7-01 | PASS | | AC-IA7-19 | PASS |
| AC-IA7-02 | PASS | | AC-IA7-20 | PASS |
| AC-IA7-03 | PASS with M1 | | AC-IA7-21 | PASS |
| AC-IA7-04 | PASS | | AC-IA7-22 | PASS |
| AC-IA7-05 | PASS | | AC-IA7-23 | PASS |
| AC-IA7-06 | PASS | | AC-IA7-24 | PASS |
| AC-IA7-07 | PASS | | AC-IA7-25 | PASS |
| AC-IA7-08 | PASS | | AC-IA7-26 | PASS |
| AC-IA7-09 | PASS | | AC-IA7-27 | PASS |
| AC-IA7-10 | PASS | | AC-IA7-28 | PASS |
| AC-IA7-11 | PASS | | AC-IA7-29 | PASS |
| AC-IA7-12 | PASS | | AC-IA7-30 | PASS |
| AC-IA7-13 | PASS | | AC-IA7-31 | PASS |
| AC-IA7-14 | PASS | | AC-IA7-32 | PASS |
| AC-IA7-15 | PASS | | AC-IA7-33 | PASS |
| AC-IA7-16 | PASS | | AC-IA7-34 | PASS |
| AC-IA7-17 | PASS | | AC-IA7-35 | PASS |
| AC-IA7-18 | PASS | | AC-IA7-36 | PASS |

## Existing database preservation

`C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3`: 160,968,704 bytes, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
`PRAGMA user_version=2`; 12 tables, 38 indexes, 23 triggers, 2 views. Bytes and version
identical before and after all audit operations (opened only read-only). Not rebuilt or
committed.

## Protected repository state

Before and after: `C:\Works\macula-greek` at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
clean; `C:\Projects\bible-research-merged` at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`,
clean. Neither was modified.

## Scope confirmation

| Item | Introduced? |
|---|---|
| Candidate persistence | NO |
| Evaluated interpretation | NO |
| Semantic roles | NO |
| Actor/Action/Patient/Event/Result/Identity/Property | NO |
| BRW integration | NO |
| Schema change | NO |
| Runtime XML parsing | NO |
| XmlPro | NO |
| Unit 8 | NO |

## Final statement

**Independently accepted:** the Unit 7 derived structural candidate boundary at
checkpoint `9331d8a4bee4d20cb96f07752e45f578b0d31f39` (Apposition-only, in-memory,
`derive_structural_candidates`), decision ACCEPT WITH MINOR FINDINGS, M1 open.

**Not accepted or changed:** Units 3, 4 and 6 remain IMPLEMENTED / PENDING INDEPENDENT
ACCEPTANCE; Unit 5 remains ACCEPT WITH MINOR FINDINGS with M1 unresolved; the Phase
remains AUTHORIZED; no Unit 8, persistence, evaluation or semantic projection is
authorized.
