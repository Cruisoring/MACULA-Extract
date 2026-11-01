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

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

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

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

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

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

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
