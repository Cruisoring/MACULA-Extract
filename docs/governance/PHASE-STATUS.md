# Phase Status

## MACULA Greek Linguistic Source Store Phase

**Status:** AUTHORIZED

Authorized phase scope: SBLGNT Matthew source-store vertical slice.

### Unit 1 — Source Contract & Fixture Freeze
**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Unit 1 is limited to source contract, source verification, frozen fixtures, and associated tests. It does not authorize SQLite schema/importer/exporter or semantic projection.

Independent acceptance audit record: [docs/audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md) — Decision: ACCEPT. This acceptance itself did not authorize Unit 2. The user subsequently issued a separate formal Unit 2 implementation authorization.

Unit 1 completed scope: source contract + fail-closed source verification + frozen fixtures + fidelity constraints + Unit 1 tests only.

The Phase remains **AUTHORIZED**, not COMPLETE or CLOSED. Unit 1's independent acceptance (see audit record above) is distinct from the user's later Unit 2 authorization.

### Unit 2 — SQLite Source Schema & Parser Contract

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

The separately authorized schema/contract implementation passed the final pre-commit
gates recorded below. Checkpoint parent and final cleanliness are mandatory post-commit gates,
reported with the actual ending SHA rather than fabricated inside this document.

Independent acceptance audit record:
[UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md).

- Implementation checkpoint: `9c39f832e215023becb366cc8f59af004c43407d`.
- Independent audit decision: **ACCEPT WITH MINOR FINDINGS**.
- F-1 through F-4 remain recorded with their original findings and severities;
  this archival/governance checkpoint does not resolve them.

Unit 2 schema/parser contract independently accepted with minor findings.
Acceptance does not mean a production importer/parser/exporter exists, and does not
authorize Unit 3. F-2 remains: model consistency validation does not re-parse original
bytes and is not production round-trip certification of normalized records against
original bytes. Real importer/source-to-normalized fidelity verification remains
future, separately authorized work.

Scope: executable SQLite schema/version, empty-only bootstrap, XmlReader/occurrence
contracts, temporary schema verification and directly related documentation.
Production parser/importer/exporter, ingestion, integration and interpretation remain excluded.
See [Unit 2 schema contract](../architecture/UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md).

### Unit 2 Amendment 1 - Schema Version 2

**Status:** IMPLEMENTED

Checkpoint: `087865e3d822c7baa1f9d7e5313d46b5168bc670`.
The amendment removes `membership_ancestry` without a replacement per-row ancestry
trigger. PK/FK/unique constraints, reverse index, expected ancestry derivation and
unrelated immutability protections remain. Both membership set differences must be
empty before a successful authoritative build commits.
The original Unit 2 independent acceptance with minor findings and audit remain
historical evidence; they do not independently accept this amendment.
The amended schema-v2 technical baseline is frozen for this Unit 3 checkpoint.

### Unit 3 - SBLGNT Matthew Source Importer & Fidelity Round-Trip

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Independent acceptance audit record:
[HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)
(commit `716f2e44435f2a39e2599e860656812174dc4aa2`).

- Audited implementation checkpoint: `cc745c692a134cbdaef8c8d177c61e595b0ae31e`.
- Independent audit decision: **ACCEPT** (BLOCKER 0, MAJOR 0, MINOR 0, INFORMATIONAL 4).
- This acceptance covers Unit 3 only. It does not accept Unit 2 Amendment 1, which
  remains `IMPLEMENTED`; Unit 3 was judged on the observable fidelity of its output.
- The text below is the historical implementation-checkpoint record and is preserved
  unchanged; its statements that Unit 3 is "not independently accepted" were true at
  that checkpoint and are superseded by this status.

The user issued a separate formal Unit 3 implementation authorization after the
Unit 2 independent-acceptance archival checkpoint
`02b8d788dd3b7bf50b59a76eeda2632182b710f9`.
It permits only the fixed SBLGNT nodes Matthew source, actual System.Xml.XmlReader
importer, populated temporary SQLite builds, exact BLOB archive export, DB-only
normalized reconstruction and independent original-source fidelity comparison.

See the [Unit 3 pipeline contract](../architecture/UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md).
Unit 1, the amended schema-v2 Unit 2 technical baseline, historical architecture
reports and both audits remain frozen.
F-1 through F-4 retain their original findings and severities. Unit 3 adds independent
source fidelity verification at the F-2 boundary; it does not retroactively change
the Unit 2 audit decision or make Unit 2 acceptance an importer certification.

Unit 3 is not independently accepted. Phase remains AUTHORIZED, not COMPLETE or CLOSED.
No other books, N1904/full NT, companions, semantic projection, XmlPro dependency
or physical range mapper are authorized. The later, separate Unit 4 and Unit 5
authorizations permit only the read-only query slices below.

#### Unit 3 implementation checkpoint reconciliation evidence

Required parent: `087865e3d822c7baa1f9d7e5313d46b5168bc670`.
The unchanged Unit 1 verifier passed, followed by 26 Unit 1 tests and 56 amended
Unit 2 tests. All 22 Unit 3 tests not requiring a second full build passed with
zero failures/errors; the retained second-build determinism test was explicitly
skipped. A mock-only organization check confirmed one builder call in default
class setup; it did not create a database.

Full Matthew evidence: **REUSED PREVIOUS VERIFIED EVIDENCE**. Reconciliation created
zero additional full Matthew DBs and preserved the external verified DB byte-for-byte.
A fresh complete read-only schema/membership/source-fidelity validation reproduced
the previous logical digest and independent counts: 59,891 elements, 767,429
attributes, 179,675 content records, 1,134 sentences/Trees, 56,488 nodes, 18,329
tokens, 159,391 memberships and 733 single-character Greek tokens.
Actual byte export, normalized XML serialization/reparse, F-2 tamper rejection,
test 19 surrogate-PK invariance and Matthew 1:2 membership `[5,7,8,9]` excluding
token 6 all passed. This evidence is implementation validation, not independent acceptance.

### Unit 4 - Read-Only Matthew Verse / Token Query Slice

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Independent acceptance audit record:
[HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)
(commit `716f2e44435f2a39e2599e860656812174dc4aa2`).

- Audited implementation checkpoint: `76bdcf5b47fa660390180fdbf430400d3f2d3024`.
- Independent audit decision: **ACCEPT** (BLOCKER 0, MAJOR 0, MINOR 0, INFORMATIONAL 2).
- Local surrogate IDs in `TokenResult` are specified by the Unit 4 contract; the later
  concern is Unit 5 M1, which is unchanged and unresolved.
- The text below is the historical implementation-checkpoint record and is preserved
  unchanged; its statements that Units 3 and 4 are not independently accepted were true
  at that checkpoint and are superseded by this status.

The user separately authorized only `get_verse` and exact `get_token` over the
existing schema-v2 store, with caller-supplied paths and SQLite-enforced read-only
access. See the [Unit 4 query contract](../architecture/UNIT-4-MATTHEW-QUERY-SLICE.md).
Required checkpoint parent: `cc745c692a134cbdaef8c8d177c61e595b0ae31e`.

Pre-commit validation: unchanged Unit 1 verifier PASS; 26 Unit 1 and 56 Unit 2
tests PASS; 22 Unit 3 non-second-build regressions PASS through an external
read-only reuse fixture with fresh complete source-fidelity validation (the
second-build gate remains skipped); 11 Unit 4 fast and 4 existing full-Matthew
integration tests PASS. No full Matthew build was executed.

Matthew 1:1 returns exactly 8 scripture-ordered tokens with punctuation-preserving
surface distinct from normalized text. Matthew 1:2 returns token 5 before token 6;
exact Jesus-token morphology and explicit not-found behavior pass. Temporary-store
INSERT/UPDATE/DELETE attempts are rejected even with `query_only` disabled, proving
URI read-only enforcement. Schema and indexes are unchanged.

The ignored local database remains 160,968,704 bytes. Before/after SHA-256:
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`.
Its binary is not a source deliverable. Implementation validation does not
independently accept Unit 3 or Unit 4 and does not complete or close the Phase.

### Unit 5 - Read-Only Syntax Navigation

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

The user separately authorized deterministic syntax navigation under the
[Unit 5 contract](../architecture/UNIT-5-READ-ONLY-SYNTAX-NAVIGATION-CONTRACT.md).
Phase remains AUTHORIZED; Units 3 and 4 remain pending independent acceptance.
The implementation validation below did not itself constitute independent acceptance.
The subsequent separate acceptance and severity reconciliation supplied by the user
are recorded here; they do not authorize downstream integration.

#### Independent acceptance reconciliation

- Accepted implementation checkpoint: `842ba45fff04a7e0c492faeb9f4dc60a3ee6c2d5`.
- Decision: **ACCEPT WITH MINOR FINDINGS**.
- **BLOCKER: 0; MAJOR: 0; MINOR: 1.**
- **M1: unresolved (MINOR).** `get_members()` inherits Unit 4 `TokenResult`,
  exposing `token_id`, `node_id`, `tree_id`, `element_id` and `book_id` alongside
  source-oriented token identity. Independent surrogate-PK reallocation testing
  established that these local fields vary across equivalent builds while source
  identities, linguistic facts, exact membership and canonical ordering remain
  invariant. No Unit 5 lookup requires a caller-supplied SQLite surrogate PK.
- This is bounded governance reconciliation, not M1 remediation or another audit.
  Full Unit 5 audit-document archival is deferred for this personal project;
  no audit-report path is claimed.
- Unit 5 acceptance does not retroactively accept Units 3 or 4. Their statuses
  and all prior accepted decisions/finding severities remain unchanged.

#### Starting state and reviewed path scope

- Root: `C:\Projects\MACULA-Extract`; branch: `master`.
- Required starting HEAD / sole checkpoint parent:
  `8d82fa2f318ddee7600cd4007a1207599b336b9c`.
- Initial index and tracked worktree were clean; `git diff --check` passed.
- The only untracked file was the authorized Unit 5 contract. Its original bytes
  are preserved (SHA-256
  `BDDAF36845270AFB59454A573130FB7CAD8319EE4A07C008E308529B25A563C2`)
  and included in the reviewed checkpoint.
- Narrow paths: the existing query module, one new Unit 5 test module, root/test
  READMEs, architecture index, this governance record and the original contract.
  Frozen Unit 1-4 contracts, fixtures, schema, importer and audits are unchanged.
- Required commit subject: `implement read-only syntax navigation`.
  The actual checkpoint SHA is reported only after creation, not fabricated
  inside its own candidate diff.

#### Implemented source boundary

`get_node`, `get_children`, `get_ancestors_by_node`, `get_ancestors_by_token`
and `get_members` share the existing caller-supplied path / SQLite URI `mode=ro`,
`query_only=ON`, FK/recursive-trigger connection profile.
Exactly-one source-ID resolution uses BINARY `upstream_node_id` lookup within the
single active Matthew book/snapshot: zero returns explicit `None`, one resolves
to an internal SQLite PK, multiple matches raise `QueryError`. Multiple matching
Matthew snapshots also fail closed. Source ID encoding is never decoded.

Frozen `NodeResult` exposes source IDs, the actual relational parent source ID,
ordered sibling ordinal and nullable raw mirrors, not SQLite node/tree/element
identities. Both ancestor APIs exclude the starting node/leaf and order nearest
parent first, root last; cyclic or missing-parent topology fails explicitly.
Exact token entry reuses Unit 4's validation/lookup within one read-only connection.
Members use only the stored membership relation and unchanged Unit 4 token facts,
ordered by scripture coordinates. Raw Head plus ordered children is sufficient;
no extra Head/lexical-head API is introduced.

#### Actual validation evidence

Runtime: Python **3.13.7**, SQLite **3.50.4**, locally installed .NET SDK **9.0.310**.
The .NET bridge was built offline only for existing small Unit 3 parser regressions;
no dependency acquisition or full Matthew build was performed.

Commands executed from the implementation root:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4.Unit4FastTests -v
python -B -m unittest tests.test_unit5.Unit5FastTests tests.test_unit4.Unit4FastTests -v
python -B "C:\Users\cruis\.copilot\session-state\14e9ed43-442b-43e9-8b26-dc01e2012772\files\validate_unit5_reuse.py"
```

The disposable external session fixture overrides only Unit 3 class setup, opens
the existing database read-only, freshly runs complete schema/source-fidelity
validation, checks the previously verified logical digest, retains the slow-gate
skip and forbids full-source population. It selects the existing ignored
`sblgnt-matthew.sqlite3` and sets the Unit 4/5 integration flags and database-path
environment variables before loading their test modules. It is not a source
deliverable. Default Unit 3 discovery still has its unchanged full-build setup.

- Pre-change fast baseline: **93 PASS** (26 Unit 1, 56 Unit 2, 11 Unit 4), no skips.
- Final focused run: **27 PASS** (16 Unit 5 fast, 11 Unit 4 fast), no skips.
- Final combined regression/integration run: **140 run**, **139 PASS**, zero
  failures/errors, **1 documented skip**; all verbose result lines reviewed.
  Breakdown: Unit 1 **26**, Unit 2 **56**, Unit 3 **22 PASS + 1 skip**,
  Unit 4 **11 fast + 4 integration**, Unit 5 **16 fast + 4 integration**.
- Sole skip: `test_u3_01_two_full_builds_and_logical_digests`, exact reason
  `explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build`.
  No second-build determinism result is claimed.
- Unchanged Unit 1 source verifier and empty schema verifier: **PASS**.
  Both changed Python files passed Python 3.10 AST syntax validation.
  Pylance file checks could not find this repository outside the active editor
  workspace; no static type-check result is claimed.
- Matthew `MAT 1:1!3`: **9** source ancestors, nearest-first:
  N2NP, three Np-Appos, two NPofNP, Np2P, P2CL (`ClType=Verbless`), root.
  Exact source identities agree with independently read pinned XML.
- Matthew `400010020050040`: Rule S-V-O, Start/End `"5"`/`"8"`,
  direct children S/V/O in ordinals 0/1/2, raw Head `"1"` selects V.
  Exact members **[5,7,8,9]**, with **token 6 explicitly excluded**.
  Leaf self-membership and missing Head also pass.
- Source-ID ambiguity fails closed, surrogate-PK invariance passes, and
  temporary-store mutation is rejected even with `query_only` disabled.

Full Matthew evidence: **REUSED PREVIOUS VERIFIED EVIDENCE**, with fresh complete
BYTE/NORMALIZED/schema/membership validation and matching logical digest
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
There were **0 full Matthew builds**, no copy into Git, and no production SQLite
deliverable. Existing ignored database before/after: **160,968,704 bytes**, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`.
Schema version remains **2**; complete catalog/index inventory is unchanged.
No UI, translation alignment, database merge, localization runtime, semantic
projection, new corpus, XmlPro dependency, source mutation or schema migration
was introduced. This is implementation validation, not independent acceptance.

### Unit 6 - Read-Only Source Evidence Composition

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Independent acceptance audit record:
[HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)
(commit `716f2e44435f2a39e2599e860656812174dc4aa2`).

- Audited implementation checkpoint: `b7cc92e6e42979a64919edd173ff886591552344`.
- Independent audit decision: **ACCEPT** (BLOCKER 0, MAJOR 0, MINOR 0, INFORMATIONAL 4).
- Unit 5 M1 (inherited `TokenResult` local PKs) is unchanged and remains unresolved.
- The text below is the historical implementation-checkpoint record and is preserved
  unchanged; its statements that Units 3, 4 and 6 are pending were true at that
  checkpoint and are superseded by this status.

The user separately authorized the bounded
[Unit 6 contract](../architecture/UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md),
recorded before production implementation. Phase remains **AUTHORIZED**.
Unit 5's supplied independent acceptance is reconciled above, with M1 unresolved.
Units 3 and 4 remain pending independent acceptance. Unit 6 implementation validation
is not independent acceptance and does not authorize Unit 7 or downstream work.

#### Starting state and implementation boundary

- Repository: `C:\Projects\MACULA-Extract`; branch: `master`.
- Actual starting HEAD / required sole implementation parent:
  `842ba45fff04a7e0c492faeb9f4dc60a3ee6c2d5`.
- Index, tracked worktree and untracked state were clean; `git diff --check` passed.
  No historical reset or separate governance-only checkpoint was made.
- Frozen `SourceEvidence` and `get_source_evidence(db_path, token_ref)` compose
  Unit 4 exact token lookup, source-facing linked leaf, nearest-first ancestry
  excluding self, immediate-parent direct children in sibling order, and exact
  stored membership of the explicitly returned `membership_node`.
- `membership_node` is the immediate parent or, for a root token, the leaf itself.
  Root tokens have empty ancestry/parent-child tuples and leaf self-membership.
  Higher constituents are not silently substituted for this context.
- Existing Unit 5 children/member logic is narrowly extracted into shared query
  primitives. Existing public behavior and `TokenResult` fields remain unchanged.
  Every exposed node result uses the existing fail-closed source-ID resolver.
- One owned existing syntax read-only connection uses SQLite URI `mode=ro`,
  `query_only=ON`, FK/recursive triggers ON. Source IDs remain opaque; topology
  comes from real links and membership only from `node_token_membership`.
  Unknown exact refs return `None`; schema/access/ambiguity/cycle errors remain
  explicit `QueryError`. No XML backend, source write, cache or schema change exists.

#### Actual technical validation

Commands executed from the implementation root:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests -v
python -B -m unittest tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests tests.test_unit6 -v
python -B "C:\Users\cruis\.copilot\session-state\d4752c1a-b7ee-434b-aa08-3fdff754d062\files\validate_unit6_reuse.py"
```

The disposable external runner selects all six Unit modules together, opts into
existing Unit 4/5/6 integration, and overrides only Unit 3 class setup to reuse the
existing store read-only. Fresh complete schema/membership/BYTE/NORMALIZED fidelity
and logical-digest checks run before its existing assertions. The offline .NET
bridge is used only for the existing small parser regressions. A guard rejects
full-Matthew population. No second full import or new dependency is introduced.

- Frozen verifiers: **PASS**. Pre-change fast baseline: **109 PASS**, no skips.
- First focused run: **49 run**, **45 test methods PASS**, one PK-reallocation test
  method failed in four subtests, **3 integration skips** (not opted in). The test
  fixture had left `tree_id` autoallocated; explicit offset tree allocation fixed
  the fixture and established actual variance in all five inherited local IDs.
- Final combined run: **162 run**, **161 PASS**, **0 failures/errors**, **1 skip**.
  Unit 1: **26 PASS**; Unit 2: **56 PASS**; Unit 3: **22 PASS + 1 skip**;
  Unit 4: **11 fast + 4 integration PASS**; Unit 5: **16 fast + 4 integration PASS**;
  Unit 6: **19 fast + 3 integration PASS**.
- Sole final skip: `test_u3_01_two_full_builds_and_logical_digests`, reason
  `explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build`.
  No second-build determinism result is claimed.
- Changed Python files passed Python 3.10 AST syntax checks. Pylance file checks
  could not resolve the target repository outside the active editor workspace;
  no static type-check result is claimed.
- `MAT 1:1!3`: exact leaf `400010010030010`; nine nearest-first ancestors,
  N2NP / three Np-Appos / two NPofNP / Np2P / P2CL / source root.
  CL retains `ClType=Verbless`; the leaf is not duplicated into ancestry.
  Its named immediate-parent membership is exactly `MAT 1:1!3`.
- `MAT 1:2!5` reaches ancestor `400010020050040`, raw S-V-O / Start `"5"` /
  End `"8"` / Head `"1"`. Unit 5 inspection of that ancestor preserves direct
  S/V/O children and exact **[5,7,8,9]**, explicitly excluding 6. Unit 6's own
  real-fixture context is immediate parent `400010020050011`, with token 5 only.
  Synthetic composition directly exercises the discontinuous context as well.
- All source-level evidence is invariant across equivalent synthetic stores with
  all five local PKs reallocated. Local variance is asserted separately; M1 is
  neither hidden nor remediated. SQLite write rejection, even with query_only
  disabled, and connection closure on success/not-found/failure pass.

Full Matthew evidence: **REUSED PREVIOUS VERIFIED EVIDENCE** with fresh exhaustive
validation. Counts: 59,891 elements, 767,429 attributes, 179,675 content records,
1,134 sentences/Trees, 56,488 nodes, 18,329 tokens, 159,391 memberships and 733
single-character tokens. Logical digest:
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
Full Matthew builds: **0**.

Existing ignored `C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3` before/after:
**160,968,704 bytes**, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
`PRAGMA user_version=2`; complete catalog/index inventory unchanged.
The database is not a deliverable and is not committed.

Protected repositories remain clean and unchanged:
`C:\Works\macula-greek` at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
`C:\Projects\bible-research-merged` at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.
Actual pinned Matthew source SHA-256 remains
`FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.

The sole reviewed checkpoint contains only the query module, new Unit 6 test and
contract, root/test READMEs, architecture index and this bounded governance record.
Its actual SHA and sole parent are reported after Git creates it, not fabricated
inside its own commit. No schema, frozen fixtures, historical audits or protected
repository changes are authorized. M1, full audit archival, semantic projection,
downstream integration and UI/localization remain deferred. STOP after the Unit 6
checkpoint; no Unit 6 audit, independent acceptance or Unit 7 is performed.

### Unit 7 - Derived Structural Candidate Boundary

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED

Independent acceptance audit record:
[UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md).

- Audited implementation checkpoint: `9331d8a4bee4d20cb96f07752e45f578b0d31f39`.
- Independent audit decision: **ACCEPT WITH MINOR FINDINGS** (no BLOCKER, no MAJOR).
- **M1 (Unit 7 audit)** remains unresolved: the pre-implementation Unit 7 contract was
  untracked, so its original bytes cannot be independently reconstructed from Git;
  sections 1-39 integrity is corroborated but not independently provable.
  This is distinct from Unit 5 M1.
- I1-I6 are informational and recorded in the audit; none is remediated here.
- Subsequent reconciliation: Units 3, 4 and 6 were later independently accepted by a
  separate audit (see their sections). That does not alter this Unit 7 decision, M1 or
  I1-I6, and Unit 7 was not re-audited.

This acceptance covers only the Apposition-only, in-memory, read-only derived structural
candidate boundary. It does not accept Units 3, 4 or 6, does not resolve Unit 5 M1, and
does not authorize candidate persistence, evaluation, other candidate kinds, semantic
roles, Bible Research integration or Unit 8. Phase remains **AUTHORIZED**.

The user separately authorized the bounded initial implementation of the preserved
[Unit 7 contract](../architecture/UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md).
Phase remains **AUTHORIZED**. Unit 5 remains independently accepted, decision
**ACCEPT WITH MINOR FINDINGS**, with **M1 unresolved**. Units 3, 4 and 6 remain
pending independent acceptance; no implementation test is an independent audit.

#### Starting state and implementation scope

- Actual branch/starting HEAD: `master`,
  `b7cc92e6e42979a64919edd173ff886591552344`, the required sole checkpoint parent.
- Tracked worktree/index clean; only the user-created Unit 7 contract was untracked.
  Original raw SHA-256:
  `96FF803BAA32C2B8B4C2E4CA60AB1D86F01CE74BA0E4A7E121C4A3E61E110988`.
  Sections 1-39 and all 40 acceptance criteria are preserved. Reconciliation updates
  status, labels the former draft status as design history, and appends the separately
  authorized executable API/DTO/identity/ordering/error boundary.
- One new production module, `scripts/structural_candidates.py`, consumes unchanged
  Unit 6 SourceEvidence and existing read-only source navigation/member primitives.
  Only exact Np-Appos on self/nearest-first ancestry produces Apposition candidates.
  Frozen results carry explicit source-facing evidence, exact scope, linked source
  snapshot/file provenance, versioned canonical UTF-8/SHA-256 identity and candidate-only
  status. No local SQLite PK participates in candidate logical identity.
- Unknown exact refs return `None`; valid no-match refs return `()`; source/DB/schema/
  ambiguity/cycle/missing-evidence failures remain explicit `QueryError`.
- Authorized paths are only that production module, Unit 7 tests, the preserved
  contract, root/test READMEs, architecture index and this status record.
  Source schema/importer/query modules, frozen fixtures/contracts and audits are unchanged.

#### Technical validation

- Pre-change Unit 1/2/4/5/6 fast baseline: **128 PASS**, no failures/errors/skips.
- Unit 1 source verifier and empty schema verifier: **PASS**.
- Focused final Unit 7 run: **19 PASS** (16 fast + 3 existing-Matthew integration),
  no failures/errors/skips. Python 3.10 AST compatibility: **PASS** for both new Python
  files. Pylance cannot resolve this repository outside the active editor workspace;
  no editor static type-check result is claimed.
- Final guarded combined Unit 1-7 regression: **181 run, 180 PASS, 0 failures,
  0 errors, 1 skip**. Breakdown: Unit 1 **26**; Unit 2 **56**; Unit 3 **22 PASS +
  1 skip**; Unit 4 **15**; Unit 5 **20**; Unit 6 **22**; Unit 7 **19**.
  Sole skip: `test_u3_01_two_full_builds_and_logical_digests`, exact reason
  `explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build`.
- Full Matthew evidence: **REUSED PREVIOUS VERIFIED EVIDENCE** with fresh exhaustive
  BYTE/NORMALIZED/schema/membership validation and matching logical digest
  `F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
  The external disposable runner overrides only Unit 3 setup, uses the offline
  bridge for small parser regressions, and guards against full-Matthew population.
  Full Matthew builds: **0**; no second-build determinism result is claimed.
- `MAT 1:1!3`: exactly three Apposition anchors, nearest-first:
  `400010010030020`, `400010010030040`, `400010010030060`; ordered members are
  respectively `[3,4]`, `[3,4,5,6]`, `[3,4,5,6,7,8]`. Direct children are fixed
  source-topology expectations. CL/P2CL/Verbless and eight noun leaves remain
  unchanged; no verb/copula or semantic entity is fabricated.
- Boundary `400010020050040` retains exact members **[5,7,8,9]**, excluding 6.
  No S-V-O candidate is generated. Span mutations cannot change scope/identity.
- Equivalent synthetic stores reverse node/token PK order and reallocate all five
  inherited local IDs plus snapshot/file IDs. Entire candidate results/IDs remain
  equal. Source revision/manifest and controlled evidence/scope/version changes
  change identity. Separate processes/hash seeds/database locations remain equal.
- Read-only write rejection (including with query_only OFF), connection closure,
  traced read-only SQL, unchanged catalog/version/bytes and forbidden XML runtime
  gates pass. No candidate persistence or source-schema change occurs.

Existing ignored `C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3` before/after:
**160,968,704 bytes**, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
`PRAGMA user_version=2`; catalog/index inventory unchanged. It is not a deliverable.
Protected repositories/source retain their recorded Unit 6 revisions and checksum.

The actual reviewed checkpoint SHA/parent and final cleanliness are verified and
reported after commit creation, not fabricated within its own diff. Unit 7 independent
acceptance has since been recorded above (audit checkpoint reported after its commit).
Unit 6 independent acceptance, M1 remediation, full audit archival,
candidate persistence/evaluation, other candidate kinds, semantic roles/entities,
Bible Research integration, UI/localization and Unit 8 remain deferred.

### Unit 8 - Evaluated Structural Interpretation Boundary

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED - ACCEPT WITH MINOR FINDINGS
([audit](../audits/UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md); see
"Unit 8 and Amendment 1 independent acceptance" below). The checkpoint text in this
section is historical and records the pre-audit state.

The user separately authorized the bounded in-memory implementation from clean
`master` at `8f8b2e7642204378eb0e56e20d096b6233e409b2`, superseding the prior
design-only stop line for this implementation only.
The [contract implementation section](../architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation)
records the effective authorization; the design content and AC-U8-01 through
AC-U8-34 are preserved unchanged.

- Production module: `scripts/evaluated_interpretations.py`; tests: `tests/test_unit8.py`.
- Public API: `create_evaluated_interpretation`, `verify_evaluated_interpretation`,
  `compute_evaluation_id`. Frozen DTOs: `EvaluatedStructuralInterpretation`,
  `RationaleCitation`, `RationaleNote`, with tuple collections.
- Creation requires untrusted-candidate V1 using the frozen Unit 7 protocol and V2
  field-for-field public Unit 7 re-derivation. Verification without a database is
  V1/history only; with a database it also performs V2.
- Only `human-structural-adequacy` / `1`, class `human`, Apposition
  `source-np-appos` / `1`, is registered. Caller-supplied event keys, exact rationale
  text, restricted ordered citations and same-evaluator supersession are validated.
- Identity is `macula.evaluated-structural-interpretation.v1`, ordered canonical
  JSON/UTF-8, lowercase SHA-256 with prefix `eval-sha256:`; a literal frozen test
  vector and independent candidate recomputation cover both identity boundaries.
- Implementation validation: **50 Unit 8 fast + 1 opt-in read-only Matthew
  integration PASS; 0 failures/errors/skips**. **62 Unit 4-7 fast tests PASS
  (11/16/19/16); 0 failures/errors/skips**. Both
  `python -B -m scripts.verify_unit1` and `python -B -m scripts.source_schema` PASS.
  Python 3.10 syntax parsing/current-runtime compilation PASS. No Unit 3 discovery
  or second-full-build gate was run; Matthew was not rebuilt.
- Existing Matthew artifact preserved: **160,968,704 bytes**, SHA-256
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
  `user_version=2`, unchanged catalog/index inventory. Protected upstream and
  downstream repositories remain untouched.
- Checkpoint boundary: one implementation commit with sole parent
  `8f8b2e7642204378eb0e56e20d096b6233e409b2`. The actual resulting SHA, parent and
  final cleanliness are verified and reported after Git creates it, not fabricated
  inside its own diff. No earlier checkpoint is amended.
- This is implementation validation, **not an independent acceptance audit**.
  Unit 8 is not independently accepted; no acceptance audit exists.
- Unit 8 remains in-memory: no candidate/evaluation persistence, projection store,
  source-schema change, semantic roles, confidence, BRW integration or Unit 9.
- Unit 7 (ACCEPT WITH MINOR FINDINGS), Unit 5 (ACCEPT WITH MINOR FINDINGS), Units 3, 4
  and 6 (ACCEPT) and Unit 2 Amendment 1 (`IMPLEMENTED`) are unchanged. Unit 5 M1 and the
  Unit 7 audit M1 remain unresolved; no informational finding is treated as fixed.
- Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

### Unit 9 - S-V-O Clause Structural Candidate

**Status:** IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS; see
[Unit 9 independent acceptance](#unit-9-independent-acceptance) below)

**Production implementation:** implemented under separate authorization from
`22595753477d6ed36317bb685347d77ed1c0a567`.

The freeze-only evidence below is historical; the subsequent implementation
subsection is the current production/lifecycle record.

The user separately authorized the bounded design/fixture freeze from `master` at
`5bfd1d4b979aa0f4f42f101eeddf72118b46912a`, not Unit 9 production implementation.
The sole starting untracked file was the user-created
[Unit 9 contract](../architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md).
Its exact original bytes were preserved outside the repository before editing,
SHA-256 `EB61C1A305EDFA8DD6B2383BB5317B07E29489178F8278B85D1B43C00162F94C`.

The [freeze evidence](../architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#27-authorized-component-membership-freeze-evidence)
records independent raw-XML and read-only direct-SQLite oracles. Both confirm:

- anchor `400010020050040`, Rule `S-V-O`, raw Head `1`;
- direct S/V/O children `400010020050012`, `400010020070012`,
  `400010020080021`, in sibling ordinals 0/1/2;
- S=`("MAT 1:2!5",)`, V=`("MAT 1:2!7",)`,
  O=`("MAT 1:2!8", "MAT 1:2!9")`;
- exact anchor scope `("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")`;
  disjoint nonempty components form an exact partition, excluding token 6 everywhere.

The [expected fixture](../../fixtures/matthew-1-2-svo-candidate.expected.json)
contains no surrogate PK, DB path or timestamp. Its final LF/UTF-8 byte SHA-256 is
`6986B8A03465A4AD05533D12A714CE87CADE9ABD760555D4586F1758EEF9764C`.
Only after membership freeze, an independent canonical encoder computed:
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`.
No production candidate/query identity helper produced this expectation.

M1-M8: **8 independent mutation/invariance controls PASS; 0 failures/skips**.
They prove reduced-store partition checks and source-facing logical identity-input
invariance under PK reallocation/order reversal, **not production Unit 9 behavior**.
`python -B -m scripts.verify_unit1`: **PASS**, exit 0.
Existing Unit 7/8 suites were not rerun: their production/tests/accepted fixtures
and registry interactions are unchanged. No Unit 9 implementation tests exist.
No Matthew rebuild or Unit 3 second-build gate ran.

The existing source DB remains 160,968,704 bytes, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
`user_version=2`, with unchanged complete catalog and all table counts.
Upstream Matthew XML and both protected repositories remain unchanged.
Temporary audit scripts, outputs and synthetic stores are removed at closeout;
the original user-contract backup is retained.

Checkpoint boundary: one freeze-only commit with sole parent
`5bfd1d4b979aa0f4f42f101eeddf72118b46912a`; actual SHA and final cleanliness are
reported after Git creates it. No previous checkpoint is amended.
Unit 8 remains **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**, with no contract,
implementation or registry amendment. Unit 5 M1 and Unit 7 audit M1 remain unresolved.
Unit 9 production was not started. No persistence, semantic projection, BRW
integration or Unit 10. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

#### Unit 9 authorized production implementation

Starting root `C:\Projects\MACULA-Extract`, branch `master`, HEAD
`22595753477d6ed36317bb685347d77ed1c0a567`; tracked/index/untracked state clean.
The user separately authorized the frozen second structural family, not acceptance.
The [contract implementation evidence](../architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#28-authorized-production-implementation)
preserves the design sections and AC-U9-01 through AC-U9-26.

- Production: `scripts/structural_candidates.py`; tests: `tests/test_unit9.py`.
  Existing `derive_structural_candidates` returns Apposition or parallel frozen
  clause DTOs; Apposition's original DTO and identity encoding are preserved.
- Exact Rule `S-V-O`, direct Cats S/V/O at ordinals 0/1/2 and raw Head `1`
  gate a stored exact-membership partition. Invalid identities, topology, Head,
  membership, coordinates or snapshot context raise `QueryError`.
- Real Matthew: complete production DTO equals the independently frozen fixture;
  all four member lookups share
  `sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`.
  Scope `!5,!7,!8,!9`, S=`!5`, V=`!7`, O=`!8,!9`; `!6` is excluded.
- Unit 9: **39 fast + 3 read-only integration PASS**, 0 failures/errors/skips
  in the final regression. PK/path/hash-seed invariance, numeric token ordering,
  raw-span independence, malformed-store rejection and read-only write rejection
  pass. Complete pre-change Matthew 1:1 Apposition DTOs/IDs remain equal.
- Two-stage regression: guarded initial Units 1-9 run executed 272 tests:
  265 passed, 2 failed on frozen Unit 8 no-S-V-O expectations, 5 skipped.
  Final follow-up reran Units 1/2/4-9: **251 tests, 245 passed, 0 failures/errors,
  6 explicitly skipped**. Unit 3's already successful **22 passed + 1 second-build
  skip** was not needlessly rerun. Across final per-unit evidence: **267 passed,
  7 skipped**, not a claimed single 274-test execution.
- The six frozen Unit 7/8 no-S-V-O tests remain unchanged; their supported
  assertions are covered by Unit 9 replacements. Every skip is enumerated in
  [test instructions](../../tests/README.md#unit-9-production-implementation).
  Unit 8's unchanged evaluator still rejects new clause DTOs and forged envelopes;
  existing Apposition evaluations still verify offline and with source re-derivation.
- `python -B -m scripts.verify_unit1` and `python -B -m scripts.source_schema` PASS.
  Python 3.10 syntax parsing/current-runtime compilation PASS. Pylance could not
  syntax-check files outside its active workspace; no Pylance type-check pass is claimed.
- Existing Matthew was reused read-only; fresh complete BYTE/NORMALIZED/schema/
  membership fidelity passed with logical digest
  `F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
  The external guard recorded zero full-source population attempts. No full
  Matthew build or second-build gate ran.
- Before/after DB: 160,968,704 bytes, SHA-256
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
  `user_version=2`, all 75 measured catalog/index/trigger entries equal.
  Frozen fixture SHA remains
  `6986B8A03465A4AD05533D12A714CE87CADE9ABD760555D4586F1758EEF9764C`.
  Source XML and protected repositories remain unchanged.
- One implementation checkpoint has sole parent
  `22595753477d6ed36317bb685347d77ed1c0a567`; actual resulting SHA, parent and
  cleanliness are verified after Git creates it, not fabricated or amended here.

**UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.**
Unit 8 remains **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**, unchanged.
No Unit 8 registry amendment, persistence, semantic projection, BRW integration
or Unit 10. Unit 5 M1 and Unit 7 audit M1 remain unresolved.
Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

#### Unit 8 Amendment 1 authorized implementation

Starting root `C:\Projects\MACULA-Extract`, branch `master`, HEAD
`ddd23c4bc51c651aea82722d747c44671f15832a`; tracked/index clean. The two user-supplied
untracked files (the amendment plan and `tests/test_unit8_amendment1.py`) were preserved
and reconciled. The user separately authorized only the registry amendment, not acceptance.
The [amendment contract](../architecture/UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md)
supersedes the statements above that Unit 8 rejects clause DTOs; it changes only
`scripts/evaluated_interpretations.py` production behavior.

- Registry: `human-structural-adequacy/1` evaluates `apposition/source-np-appos/1` and
  `clause-structure/source-rule-s-v-o/1`. Protocol version, identity serialization,
  V1/V2 semantics, rationale/citation order and firewalls are unchanged.
- V1 independently verifies the clause candidate (scope, evidence, payload, Head, ordered
  disjoint components, recomputed candidate id); V2 re-derives through the public Unit 9 API.
- Tests: `tests/test_unit8_amendment1.py` (41 fast + 3 opt-in integration) with the
  disposable `tests/support/unit8_amendment1_store.py`. The two obsolete Unit 8 no-S-V-O
  assertions in `tests/test_unit8.py` were amended narrowly. Real Matthew: the frozen
  S-V-O id was evaluated from all of `MAT 1:2!5/7/8/9`; `!6` is excluded; the three
  Apposition ids are unchanged.
- Superseded Unit 9 test: `test_unit8_rejects_new_candidate_without_registry_amendment`
  asserts the pre-amendment behavior and now fails by design. Unit 9 tests were not
  edited (read-only for this amendment); it is filtered in memory and must be retired or
  rewritten by a future authorized change.
- Guarded combined regression (existing DB reused read-only, fresh fidelity verification,
  no full population, Unit 3 second-build gate disabled): Units 1, 2, 4-9 and the amendment
  ran 295 tests, 0 failures/errors, 5 explicit skips (the four Unit 7 superseded tests and
  the Unit 9 superseded test); Unit 3 ran 23 tests with 22 passes and its one disabled
  second-build skip. Both required verifiers PASS.
- Existing Matthew DB, frozen fixture and both protected repositories were verified
  unchanged. No persistence, semantic role or confidence field was added.

**UNIT 8 AMENDMENT 1 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.**
**UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.**
Unit 8, Unit 8 Amendment 1 and Unit 9 are each **IMPLEMENTED / PENDING INDEPENDENT
ACCEPTANCE**. Unit 5 M1 and Unit 7 audit M1 remain unresolved and distinct.
Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

#### Post-Amendment active-test reconciliation

Starting HEAD `ac215cb46bc2be814b6a76f671981449128dced2`; clean. Executable assertions
whose sole premises were lifecycle states superseded by Unit 9 and Unit 8 Amendment 1
were replaced in `tests/test_unit7.py` and `tests/test_unit9.py`:

- Unit 7's assertions that no S-V-O candidate existed for Matthew 1:2 (three Fast tests
  and the Matthew integration test, the last renamed
  `test_post_unit9_svo_preserves_unit7_exact_scope_invariants`);
- Unit 9's assertion that Unit 8 rejected S-V-O before a registry amendment (renamed
  `test_unit8_amendment_accepts_registered_svo_candidate`).

They were replaced by current regressions for exact S-V-O membership (scope
`[5,7,8,9]`, token 6 excluded) and explicit Unit 8 Amendment 1 registry compatibility.
The forged-envelope rejection remains active. `tests/README.md` gained a current
regression rule; its historical filter records are preserved.

Historical contracts, audits and implementation-time filter records were not rewritten.
No production behavior, schema, fixture, candidate/evaluation identity or lifecycle
status changed. No Unit or Amendment status was created.

Unit 7 remains **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS).
Unit 8, Unit 8 Amendment 1 and Unit 9 remain **IMPLEMENTED / PENDING INDEPENDENT
ACCEPTANCE**. Unit 5 M1 and Unit 7 audit M1 remain unresolved and distinct.
Phase remains **AUTHORIZED**.
(The Unit 8 and Amendment 1 statuses in this paragraph are superseded by the
independent acceptance section below; Unit 9's status is superseded by the Unit 9
independent acceptance section.)

#### Unit 8 and Amendment 1 independent acceptance

Starting HEAD `86c1aad9b2e2563b3c69057f93dd863f60619d5d`; clean. The user separately
authorized an independent acceptance audit of Unit 8 (checkpoint
`5bfd1d4b979aa0f4f42f101eeddf72118b46912a`) and Unit 8 Amendment 1 (checkpoint
`ac215cb46bc2be814b6a76f671981449128dced2`), including review of the reconciliation
commit `86c1aad`. Full report:
[UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md).

| Unit | Status | Independent decision |
|---|---|---|
| Unit 8 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | **ACCEPT WITH MINOR FINDINGS** (AC-U8-01..34: 34 PASS, 2 scope-narrowed per contract 8.2/34.1, 0 FAIL) |
| Unit 8 Amendment 1 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | **ACCEPT WITH MINOR FINDINGS** (auditor-derived checklist 10/10; the contract has no numbered criteria) |

- Independent raw-source derivation reproduced the three Matthew 1:1!3 Apposition ids and
  the frozen Matthew 1:2 S-V-O id; evaluation identity, including the frozen section 34.2
  vector, was reconstructed from literal JSON; V1/V2, closed registry, rationale/citation,
  event-key, supersession, surrogate-PK invariance, read-only, persistence and semantic
  firewall audits passed. Apposition evaluation ids are byte-identical to checkpoint
  5bfd1d4. Matthew 1:1 Verbless yields no clause candidate; the Matthew 1:2 token-6
  envelope forgery is rejected by V2.
- Regression: guarded run of 318 tests, 317 passed, 0 failures, 0 errors, 1 skip (Unit 3's
  disabled second-build gate); no obsolete-test filter; no full Matthew build.
- **MINOR M-1:** after `86c1aad` fixed the Unit 9 test, stale "fails by design / filtered
  in memory" statements remain in historical text (this file's Amendment 1 section, the
  Amendment contract and plan, historical `tests/README.md`). `AGENTS.md`'s live statement
  was corrected; historical prose and frozen contracts were not rewritten.
- Informational findings (I-1..I-8) are recorded in the audit and are not remediated.
- Existing Matthew DB (SHA-256 `E52DB7E2...25CE7E`), fixtures, production, schema,
  contracts and both protected repositories were verified unchanged.

**UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED** at that checkpoint (superseded by
the Unit 9 independent acceptance section below). Unit 9 was then **IMPLEMENTED /
PENDING INDEPENDENT ACCEPTANCE**. No production remediation, persistence, semantic
projection, BRW integration or next Unit is authorized. Unit 5 M1 and Unit 7 audit M1
remain unresolved and distinct. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

#### Unit 9 independent acceptance

Starting HEAD `35337d87bb93e9c19099ff3298afe6e3f36ea76c`; clean. The user separately
authorized an independent acceptance audit of Unit 9 (implementation checkpoint
`ddd23c4bc51c651aea82722d747c44671f15832a`). Full report:
[UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md](../audits/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md).

| Unit | Status | Independent decision |
|---|---|---|
| Unit 9 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | **ACCEPT WITH MINOR FINDINGS** (AC-U9-01..26: 25 PASS, 1 superseded by accepted Unit 8 Amendment 1, 0 FAIL) |

- Independent raw-XML derivation reproduced the frozen Matthew 1:2 S-V-O membership
  (`!5,!7,!8,!9`; S `!5`, V `!7`, O `!8,!9`; `!6` excluded) and identity
  `sha256:129c3970...ff087`, plus the three Matthew 1:1!3 Apposition ids. A full-corpus
  comparison of all 18,329 Matthew tokens (1,474 candidate instances: 523 S-V-O, 951
  Apposition) found 0 mismatches or errors.
- Surrogate-PK reallocation (5 modes), identity sensitivity (28 variants), hash-seed/path
  invariance, 37 store mutations, Start/End firewall, semantic-annotation invariance,
  authorizer-traced read-only behaviour, Matthew 1:1 Verbless negative and Unit 8
  Amendment 1 envelope-forgery rejection (stale and self-consistent) all passed.
- Regression: unfiltered run of 295 tests (Units 1, 2, 4-9 and Amendment 1), 295 passed,
  0 failures, 0 errors, 0 skips; both verifiers passed. Unit 3 was not re-run (its
  discovery performs a full build); no Matthew build occurred.
- **MINOR M-1:** the contract section 16 "token 6 appears in the anchor or a component"
  `QueryError` rule has no dedicated production check; a self-consistent store edit
  (`!6` added to anchor and O) yields a candidate. Not remediated.
- Informational findings I-1..I-5 are recorded in the audit and are not remediated.
- Existing Matthew DB (SHA-256 `E52DB7E2...25CE7E`), fixtures, production, schema,
  contracts and both protected repositories were verified unchanged.

No production remediation, persistence, semantic projection, BRW integration or next
Unit is authorized. Unit 9 audit M-1 is distinct from Unit 5 M1 and Unit 7 audit M1,
which remain unresolved. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

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

## Unit 2 final execution evidence (original schema version 1 checkpoint)

- Implementation root: `C:\Projects\MACULA-Extract`; branch: `master`.
- Starting checkpoint and required sole parent:
  `4cd957d7158cfbe0ea29a1afa56f09572fc877fa`.
- Prior Unit 1 root and independent acceptance checkpoints remain intact.
- Python **3.13.7**; SQLite **3.50.4** (STRICT/JSON available).
- Unit 1 tests: **26**; Unit 2 tests: **50**; total: **76**.
- Failures: **0**; errors: **0**; skips: **0**.
- Every verbose test-result line was checked, not only the runner summary.
- Unit 1 source verifier and empty in-memory schema verifier: **PASS**.
- New Python files also passed AST syntax validation with `feature_version=(3, 10)`.

Required commands, executed from the implementation root:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
python -B -m unittest discover -s tests -p "test_*.py" -v
git diff
git diff --cached
git diff --cached --name-status
git diff --check
git diff --cached --check
```

The complete candidate was reviewed. Both whitespace checks passed; no unstaged
implementation changes or untracked/generated files remained. The staged path set
was independently checked against exactly 14 authorized paths, including both
Unit 2 JSON contracts, DDL, both new scripts, Unit 2 tests, both architecture
documents, and AGENTS/README/fidelity/phase/test-documentation updates.
Staged text was compared with the reviewed worktree text, not inferred from `git add`.

Frozen Unit 1 contract, every fixture, verifier, tests, acceptance audit and historical
MACULA data architecture Spike matched the starting checkpoint in the index and
worktree. No production importer/exporter/ingestion, populated production database,
N1904/full NT implementation, XmlPro dependency/copied source, BRW projection,
Actor/Action/Patient/Event/Result entities, physical mapper or Unit 3 artifacts exist.
The complete implementation file/directory inventory contained no temporary
DB/SQLite/WAL/SHM/journal files, `__pycache__`, or unintended `bin`/`obj`.

Protected repositories remained clean with unchanged branches and HEADs:
- `C:\Works\macula-greek`: `main`,
  `8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
- `C:\Projects\bible-research-merged`: `master`,
  `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.
- Matthew SHA-256:
  `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.

Historical-report hygiene-only change:
- file:
  `docs/architecture/XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md`
- lines:
  653, 656, 659, 662, 665, 668, 671, 674, 677, 680
- change:
  exactly two trailing spaces removed from each line
- total:
  20 trailing-space bytes removed
- semantic/content differences:
  NONE
- verification:
  `old.rstrip() == new.rstrip()` for every changed line

The actual original TEMP report and cleaned archive were compared byte-for-byte:
only those ten line changes occurred; sizes were 64,392 / 64,372 bytes.
Original raw SHA-256:
`01245365D6ACAD070ED5E420D7D73356EA7C7A1C121F55866FB67AF0C8A4F551`.
Cleaned raw SHA-256:
`47F91C76D2A87EA981367936A7B415CA545900502FFE2CD11021DD0DC74DC242`.
They differ; the LF Git blob is verified separately from the raw CRLF report.

### Unit 2 acceptance gate mapping

The test evidence below is from the complete successful suite in
[test_unit2.py](../../tests/test_unit2.py), not a production XML ingestion claim.

| Criterion | Pre-commit result | Actual evidence / mandatory final gate |
|---|---|---|
| AC-U2-01 | PASS | Exact Git root, master, starting HEAD and two-checkpoint Unit 1 history verified. |
| AC-U2-02 | PASS | All frozen Unit 1 paths matched baseline in index/worktree; independent audit still ACCEPT. |
| AC-U2-03 | PASS | DDL executes without Python SQL functions; 12 tables with PKs and required FKs. |
| AC-U2-04 | PASS | Empty bootstrap dumps agree; repeat/unknown/active transaction rejected; SQL failure rolls back. |
| AC-U2-05 | PASS | Version 1 in user_version and singleton metadata; persistence and version/catalog drift tested. |
| AC-U2-06 | PASS | Snapshot edition/repository/revision/manifest and scoped file/book provenance represented. |
| AC-U2-07 | PASS | Exact BLOB/size/hash verified; wrong type/size/hash rejected; source immutability tested. |
| AC-U2-08 | PASS | Element expanded names, lexical QName/prefix and same-file parent scope tested. |
| AC-U2-09 | PASS | BINARY namespace/local-name attribute identity; alias duplicates rejected; case retained. |
| AC-U2-10 | PASS | Missing Notes has no row/NULL; present-empty English has a row/empty string; mismatches rejected. |
| AC-U2-11 | PASS | Ordered document/element/text/CDATA/comment/PI; duplicate ordinals and text segmentation tested. |
| AC-U2-12 | PASS | Versioned canonical ASCII JSON expanded-name ordinal paths; malformed/noncanonical paths rejected. |
| AC-U2-13 | PASS | External snapshot/file/hash/locator key equal across changed synthetic database PKs. |
| AC-U2-14 | PASS | Only nullable diagnostic line/column; no byte/UTF-16 offsets or physical mapper. |
| AC-U2-15 | PASS | Manual SQL sentence/Tree/Node/token core validates with real source-element links. |
| AC-U2-16 | PASS | Ordered generic/typed parent topology validated; wrong parent and cross-file links rejected. |
| AC-U2-17 | PASS | Head/Start/End/Length are raw nullable TEXT mirrors; absence has no inferred defaults. |
| AC-U2-18 | PASS | Boundary traversal [6,5,7,8,9] differs from canonical [5,6,7,8,9]. |
| AC-U2-19 | PASS | Ancestry view and membership include leaf self; incomplete/wrong/cross-Tree membership rejected. |
| AC-U2-20 | PASS | Live Matthew target 400010020050040 members [5,7,8,9]; raw span 5..8; token 6 excluded. |
| AC-U2-21 | PASS | ref scripture coordinates and Ref raw referent coexist independently. |
| AC-U2-22 | PASS | Id/nodeId/xml:id/morphId distinct TEXT fields; XML namespace and repeated cross-snapshot IDs tested. |
| AC-U2-23 | PASS | FunctionalTag N-GSM and FormalTag N-PRI coexist independently. |
| AC-U2-24 | PASS | Direct surface, Unicode, NormalizedForm and combining lemma remain distinct; substitution rejected. |
| AC-U2-25 | PASS | Live MAT 1:16!13, xml:id n40001016013, direct Greek text U+1F41 retained with length 1. |
| AC-U2-26 | PASS | Exact schema/script inventory and negative entity test: no BRW projection or semantic entities. |
| AC-U2-27 | PASS | Only schema/locator/verifier production scripts; manual SQL helpers are test-only, no importer/exporter. |
| AC-U2-28 | PASS | Stdlib-only imports; parser contract rejects XmlPro dependency; no copied source/assembly. |
| AC-U2-29 | PASS | XmlReader DTD Prohibit/resolver null/no validation, preserved content, explicit XInclude rejection; unsafe profiles rejected. |
| AC-U2-30 | PASS | Empty schema CLI and all 50 Unit 2 tests passed with no skips. |
| AC-U2-31 | PASS | Frozen source verifier and all 26 Unit 1 tests passed with no skips. |
| AC-U2-32 | PASS | Full staged/unstaged review and both diff --check commands passed. |
| AC-U2-33 | PASS | Independent staged name-status and exact 14-path/content checks; no other files changed. |
| AC-U2-34 | PASS | MACULA HEAD/branch/status and exact Matthew SHA-256 unchanged. |
| AC-U2-35 | PASS | Downstream HEAD/branch/status unchanged; pre-existing ignored downstream artifacts preserved. |
| AC-U2-36 | POST-CHECKPOINT | Immediately verify sole parent, exactly one new commit, reviewed paths, clean index/worktree/untracked/ignored inventory, and protected repositories. |

The unique checkpoint subject is `implement MACULA SQLite source schema contract`.
Do not amend, rebase or rewrite either prior checkpoint. The full ending SHA and
AC-U2-36 result must be reported from actual post-commit verification.
