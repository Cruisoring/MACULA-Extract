# Unit 10 - Separate Structural Interpretation Persistence Boundary

## 1. Authorization and freeze

**CONTRACT FROZEN / IMPLEMENTATION NOT STARTED** at the dedicated freeze checkpoint.
This section describes that checkpoint; subsequent implementation evidence may only
be appended, not substituted for sections 1-12.

Starting repository: `C:\Projects\MACULA-Extract`, branch `master`, clean HEAD
`efb0311da039da3c5bf7f2b0704ed2722ac5fbfb`, sole parent
`35337d87bb93e9c19099ff3298afe6e3f36ea76c`.
The separate user authorization permits this contract checkpoint followed by exactly
one implementation checkpoint whose sole parent is the contract checkpoint.
Neither checkpoint is independent acceptance. Unit 11 is NOT AUTHORIZED.

The actual current [governance](../governance/PHASE-STATUS.md), accepted
[Unit 7](UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md),
[Unit 8 section 34](UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation),
[Amendment 1](UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md), and
[Unit 9](UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md) own all prior semantics.
Their historical persistence prohibitions are superseded only for this separate store.
Historical contracts/audits, including findings, are not edited.

## 2. Ownership and supported objects

Source fact -> derived candidate -> evaluated structural interpretation -> separate
DERIVED / EVALUATION STORE -> STOP.

Persistence grants no source, semantic or theological authority. The source schema,
version, rows and bytes remain unchanged. No ATTACH or connection spans trust zones.
Only the current canonical frozen Python DTOs are returned, never storage models.
The current accepted registry was inspected, not inferred from old conversation:

| Candidate kind | Derivation | Evaluation protocol / class |
|---|---|---|
| apposition | source-np-appos / 1 | human-structural-adequacy / 1 / human |
| clause-structure | source-rule-s-v-o / 1 | human-structural-adequacy / 1 / human |

No new kind, derivation, disposition, evaluator class or protocol is registered.
Unit 8's V1 verifier owns this closed compatibility boundary.

## 3. Exact authorized paths

Freeze checkpoint changes exactly:

- `docs/architecture/UNIT-10-STRUCTURAL-INTERPRETATION-PERSISTENCE-CONTRACT.md`
- `docs/architecture/README.md`
- `README.md`
- `docs/governance/PHASE-STATUS.md`
- `AGENTS.md`

Implementation changes exactly the above five documentation paths, plus:

- `scripts/projection_store.py` (new)
- `schema/001-projection-store.sql` (new; independent schema namespace)
- `tests/test_unit10.py` (new)
- `tests/README.md`

No old production/test/helper/fixture/schema/audit file is authorized for editing.
Existing disposable test builders may be reused without modification.
External guarded runners and evidence may live in the session workspace; runtime
SQLite files and .NET outputs must remain temporary and outside the repository.

## 4. Frozen public API

In `scripts/projection_store.py`, using the existing `source_query.QueryError`:

```python
initialize_projection_store(path) -> None
store_candidate(store_path, candidate, *, source_db_path) -> None
get_candidate(store_path, candidate_id) -> StructuralCandidate | ClauseStructureCandidate | None
store_evaluation(store_path, evaluation, *, source_db_path) -> None
get_evaluation(store_path, evaluation_id) -> EvaluatedStructuralInterpretation | None
list_evaluations_for_candidate(store_path, candidate_id) -> frozenset[EvaluatedStructuralInterpretation]
verify_projection_store(store_path, source_db_path=None) -> None
```

Paths are `str | Path`. Both write APIs require a non-None source database, with
no validation bypass. Evaluation storage atomically inserts its candidate if absent.
Missing valid lookup identities return None / an empty frozenset; invalid identity,
schema, content or I/O raises QueryError, never not-found. No current/latest API.
The frozenset has no ranking or insertion/time ordering.

LOAD reconstructs the stored object; it never re-derives a replacement or performs
an evaluator judgment. Decoding enforces a closed typed representation; existing
canonical DTO constructors retain their own intrinsic validation (evaluation
construction necessarily recomputes V1). Explicit VERIFY performs full V1/history,
and optional V2. Candidate LOAD does not claim V1 or V2 certification.

## 5. Storage representation and identity

One separate local SQLite file, with STRICT tables:

- `projection_metadata`: singleton, store protocol and LF-normalized DDL SHA-256.
- `candidate`: candidate_id TEXT primary logical key and canonical record_json TEXT.
- `evaluation`: evaluation_id TEXT primary logical key, candidate_id foreign key,
  evaluator_label, event_key, nullable supersedes foreign key, canonical record_json.
  UNIQUE(evaluator_label, event_key) enforces the current human event history rule.

Primary keys are content IDs, not INTEGER aliases. SQLite's incidental rowids are
never queried or exposed. Supersedes is a predecessor identity, never an update.
The candidate foreign key and candidate echo must agree field-for-field.
Metadata is not an identity input. No source surrogate PK, database path, process,
clock, Python hash, insertion order or generated random key enters logical content.

Candidate JSON is an object with exactly `candidate_protocol` and `candidate`.
The protocol equals `macula.structural-candidate.v1`; `candidate` contains exactly
all canonical dataclass field names, recursively. Evaluation JSON contains exactly
all canonical evaluation dataclass fields, including the complete candidate echo.
All tuple fields become JSON arrays and are reconstructed as tuples.
Nested payload shape is selected by the exact candidate kind; unknown fields,
missing fields, duplicate object keys, wrong primitive types, non-finite numbers,
noncanonical JSON and unsupported protocols fail closed.

Canonical persistence JSON:
`json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)`.
Dictionary order is irrelevant; array order is preserved. UTF-8/Unicode strings
round-trip exactly, including CR/LF, combining marks, leading/trailing whitespace,
language tag case, labels and caller-supplied event keys.
This JSON is NOT a new candidate or evaluation identity protocol.
Unit 7/9 and Unit 8 continue to own their ordered-array identity bytes.
No field is dropped: all seven snapshot fields, exact scope, ordered evidence,
payload, status, protocol, provenance, disposition, citations, note, event and edge
are preserved. No envelope/interval expansion or normalization is permitted.

## 6. Verification and write gates

Candidate V1 reuses the already accepted Unit 8
`evaluated_interpretations._verify_candidate` implementation unchanged. This narrowly
documented internal dependency avoids duplicating the frozen independent V1 encoder;
no private derivation/identity helper from Unit 7/9 is used.
Candidate V2 calls public `derive_structural_candidates` with its first exact member
and requires full DTO equality. Both run before candidate insertion.

Evaluation writes call public `verify_evaluated_interpretation` with source_db_path
and the complete stored evaluation history, so both identities, registry, rationale,
field presence, event uniqueness and supersession receive V1/history + V2.
Source access uses the unchanged mode=ro/query_only=ON/FK=ON/recursive_triggers=ON
query boundary, on separate, closed connections. No writable source connection.

Before any append, existing store contents receive offline V1/history verification;
thus a damaged or conflicting predecessor cannot be used. Transactions serialize
read-check-append with BEGIN IMMEDIATE. Offline store verification checks the exact
catalog/version, integrity_check, foreign_key_check, all JSON and relational echoes,
all candidate V1 identities and all evaluation V1/history. With source_db_path it
additionally V2-verifies every stored candidate/evaluation. A different snapshot
fails V2; offline history remains bound to its original snapshot.

The production source is assumed immutable and already publication-validated.
This task freshly runs schema-v2 complete ancestry and independent Expat fidelity
verification before real-Matthew use. Unit 10 does not repair Unit 9 M-1 or introduce
a second source parser. V2 has the accepted derivation's existing trust limits.

## 7. Append-only and supersession

Identical logical ID plus identical complete canonical content: idempotent success.
Identical logical ID plus different stored logical content: QueryError and rollback.
No UPDATE/DELETE/REPLACE/upsert on records. BEFORE UPDATE and DELETE triggers reject
mutation; BEFORE INSERT guards reject duplicate logical IDs even under REPLACE
with recursive_triggers OFF. Application idempotence reads and compares before INSERT.
Metadata is likewise immutable. Direct arbitrary DROP/DDL by an owner of a SQLite
file is outside append-only API guarantees, but exact-catalog verification detects
schema drift; this is not authentication, tamper-proof storage or signatures.

Persist predecessor before successor. Validate complete predecessor ancestry,
same candidate, same evaluator, no self-edge/cycle, valid identity and unique
label/event. Forks and opposing evaluations coexist. Neither insertion order,
rowid nor time selects a winner. Historical human notes are primary records, never
automatically regenerated or replaced by a fresh evaluation.

## 8. Initialization, connections and local durability

Only a nonexistent path may be initialized; even an existing empty file is rejected.
Create exclusively; bootstrap in a transaction; close all connections on all paths.
On failure remove only the newly created file (no pre-existing file/sidecar).
Repeated initialization, unknown/nonempty/source DBs, unknown/higher version and
catalog changes fail closed without migration or success-shaped partial stores.

Independent database identity:
application_id `0x4d553130` (decimal `1297428784`), user_version `1`,
store protocol `macula.structural-interpretation-store.v1`.
Source database user_version remains 2 and is not the same lifecycle.
Exact expected catalog is derived from the bundled DDL in an in-memory database;
metadata DDL hash and exact catalog must both match.

Readers use URI mode=ro and query_only=ON; controlled writers first validate through
a read-only preflight (so a source/unknown DB is never opened writable), then use
mode=rw, revalidate inside their transaction, FK/recursive_triggers ON.
Require DELETE journal mode; writers use synchronous=FULL and a 5-second SQLite
busy timeout. Initialization selects those settings. Source and projection paths
must not alias (including hard links). All handles close on success and exception.
SQLite atomic commit/durability is limited by these settings, OS/filesystem and
hardware guarantees; no crash-proof or distributed durability claim is made.
No cloud, sync, backup service, crypto, accounts or multi-user resolution is added.

## 9. Frozen vectors (independent expectations)

Candidate positive vector: every canonical candidate field in the accepted
[Matthew 1:2 fixture](../../fixtures/matthew-1-2-svo-candidate.expected.json),
excluding fixture-only annotations/excluded refs. Seven snapshot fields and ordered
scope/evidence/payload are selected by explicit field names, never dictionary order.
The unchanged Unit 7/9 compact ASCII-escaped ordered-array protocol independently
recomputes:

`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`

This literal was independently reproduced from the frozen source-facing fixture
before Unit 10 production implementation; production serialization is not an oracle.
The integration test also compares actual reloaded DTO fields with this fixture.

Human vector's literal evaluation identity bytes (no newline):

```json
["macula.evaluated-structural-interpretation.v1","sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087","human","unit10-vector","human-structural-adequacy","1","undetermined",[["syntax_node","400010020050040"],["token","MAT 1:2!5"]],["  \u03b1\r\n","el"],"unit10:1",null]
```

Expected `eval-sha256:3115087c4d749fa4e1ea2e1f2d16c4d6142798ce2b4505cff930a5f12147257d`.

Supersession vector: same candidate/label/protocol/citations/note, disposition
`accepted`, event_key `unit10:2`, supersedes the above evaluation ID.
Expected `eval-sha256:1c39cb8d35b4102e313d3a337b4b43c3ad6b73b5b35093574e4c191de6a46e21`.
Both expected evaluation hashes were independently computed from literal arrays.

Negative vector: keep the positive candidate ID but add `MAT 1:2!6` to anchor
scope and O membership. V1 must reject the stale ID; reidentifying this forgery
passes structural V1 but V2 against the genuine source must reject it.
Disposable raw-SQL corruption under an existing candidate/evaluation ID must also
cause write/verify failure, never overwrite. No production validation bypass exists.

Snapshot changes yield distinct identities; older records stay readable/offline
verifiable without relinking. Hypothetical derivation version 2 changes the identity
wire but is unsupported by the current registry and MUST NOT be stored. Tests prove
distinctness independently and fail-closed rejection, not a new registration.

## 10. Acceptance criteria

Each criterion needs concrete implementation evidence, not independent acceptance.

| ID | Required result |
|---|---|
| AC-U10-01 | Separate, recognizably versioned STRICT store; no source DDL/migration |
| AC-U10-02 | Exclusive atomic initialization; existing/unknown/source targets preserved |
| AC-U10-03 | Exact version/catalog/hash drift fails closed |
| AC-U10-04 | Both accepted candidate families round-trip every field as frozen DTOs |
| AC-U10-05 | Human evaluations round-trip every field/text/citation/event without regeneration |
| AC-U10-06 | Candidate writes require independent V1 and public source V2 |
| AC-U10-07 | Evaluation writes require V1/history + V2, no bypass |
| AC-U10-08 | Identical candidate/evaluation duplicates are idempotent |
| AC-U10-09 | Conflicting same-ID content fails without overwrite |
| AC-U10-10 | Append-only triggers reject UPDATE/DELETE/REPLACE, including recursive OFF |
| AC-U10-11 | Identities independently recompute after reload; literal frozen vectors match |
| AC-U10-12 | Exact scope/evidence/payload/component orders survive, no envelope expansion |
| AC-U10-13 | Supersession preserves predecessors/forks; bad/missing/cross edges rejected |
| AC-U10-14 | Global stored label/event conflicts rejected; multiple judgments coexist |
| AC-U10-15 | Snapshot records coexist without migration/relink; wrong-source V2 fails |
| AC-U10-16 | Derivation-version identity distinctness, unknown version rejected |
| AC-U10-17 | Two equivalent source stores with changed PK/order and projection row allocations yield equal logical DTOs/IDs |
| AC-U10-18 | Source mode=ro/query_only trust zone; no ATTACH; alias rejection |
| AC-U10-19 | Real Matthew 1:1 remains Verbless/Apposition, no fabricated verb/copula |
| AC-U10-20 | Real Matthew 1:2 exact !5,!7,!8,!9, S/V/O, no !6; forgery rejected |
| AC-U10-21 | No semantic entities, roles, invented source IDs/tokens or unconditional mappings |
| AC-U10-22 | No theological fields, generated judgment, confidence, probability or ranking |
| AC-U10-23 | Malformed identity/JSON/types/unknown fields/protocol fail explicitly |
| AC-U10-24 | LOAD never derives/evaluates; explicit verification is distinguishable |
| AC-U10-25 | All connection/transaction handles close on success/error; rollback is atomic |
| AC-U10-26 | Existing source bytes/size/version/catalog/indexes/triggers/logical fidelity unchanged |
| AC-U10-27 | Current Unit 7/8/Amendment/9 and applicable earlier regressions pass unfiltered |
| AC-U10-28 | Two sole-parent checkpoints, exact allowed paths, clean final tree, no binaries |
| AC-U10-29 | Protected upstream/downstream Git states unchanged; zero full Matthew builds |
| AC-U10-30 | Existing findings remain open; no acceptance/BRW/new Unit; stop after implementation |

## 11. Validation procedure and baseline

Use stdlib unittest/SQLite only, Python 3.10+ and existing offline .NET for earlier
synthetic Unit 3 regressions. Focused `tests.test_unit10` has fast disposable stores
and opt-in integration (`MACULA_UNIT10_INTEGRATION=1`, `MACULA_MATTHEW_DB`).
Cover bootstrap, round-trips, stale/reidentified forgery, corrupted storage, malformed
IDs/types, snapshot/derivation changes, supersession, event reuse, PK/order shifts,
read-only/source separation, forbidden fields, closure and schema drift.
Do not compare only with production's own encoder.

Run current prior suites without obsolete-test filters. For Unit 3 use an external
guarded setup that reuses a byte-identical private temporary source copy, freshly
validates fidelity, and prohibits full-source population/builds. Preserve its disabled
second-build skip; report skips separately. Full Matthew builds performed: 0.
Temporary reduced stores may change PK allocations and insertion order; real source
and protected repositories may not be changed.

Measured before implementation:
source DB 160,968,704 bytes,
SHA-256 `e52db7e2abdb1c2b9b4f93060312587a1363066378b7a0c9b8fb72475c25ce7e`,
user_version 2; 38 indexes, 23 triggers.
Catalog/index/trigger SHA-256 over compact ASCII JSON of
`(type,name,tbl_name,sql)` ordered by type,name:
`56210406d16bc95c3f8c251b646aa74105887fd6645e5430560dda0610a649c8`,
`043161e8c83ee11710b6e59debb012582ad55b8bf0ec25a0487382ffc9d8748c`,
`7ba5f63d365e9755e1878e0211f4f3a3fe2a9588ed33e761af3dd4dbe30c6597`.
Fresh schema/complete ancestry/independent Expat fidelity PASS:
59,891 elements, 767,429 attributes, 179,675 content, 1,134 sentences/Trees,
56,488 nodes, 18,329 tokens, 159,391 memberships, 733 single-character tokens.
Logical digest `F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.

Protected before states (ordinary Git status clean):
`C:\Works\macula-greek`: main, `8423afe47b9e8f24b7772e808af45c7159a6fe7e`;
`C:\Projects\bible-research-merged`: master, `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.
No network acquisition or protected repository mutation.

## 12. Stop line and findings

Keep Unit 5 M1, Unit 7 audit M1, Unit 8/Amendment findings and Unit 9 M-1 at their
original severities/statuses. Unit 9 M-1 is not repaired by genuine-source V2 tests.
No semantic roles/entities, theology, confidence, automatic candidate acceptance,
BRW integration, other books/N1904/full NT, source migration, cross-version mapping,
UI/localization, AI evaluator, deterministic-policy registration or Unit 11.
Implementation completion must say **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**.
Phase remains AUTHORIZED, not COMPLETE or CLOSED. Independent acceptance needs a
new separate task. Append implementation evidence below only after the freeze.

## 13. Implementation validation

**IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.** This is implementer evidence,
not an independent acceptance audit. Sections 1-12 are preserved from freeze commit
`d690209f7dce140b61d0056446cec370afce2edd`, whose sole parent is the exact starting
checkpoint `efb0311da039da3c5bf7f2b0704ed2722ac5fbfb`.
The implementation checkpoint's sole parent must be that freeze; actual SHA,
parent and clean status are checked and reported after Git creates it.
No amend/rebase/squash, third checkpoint, push or protected-repository mutation.

### 13.1 Delivered boundary

New [production module](../../scripts/projection_store.py),
[independent DDL](../../schema/001-projection-store.sql) and
[Unit 10 tests](../../tests/test_unit10.py). All seven APIs in section 4 are
implemented with the frozen signatures/return shapes. Only canonical existing
Unit 7/8/9 DTOs are loaded. The current two-kind registry and all earlier production
files remain unchanged.

Store identity is application_id 1297428784, user_version 1, independent protocol
`macula.structural-interpretation-store.v1`; all three tables are STRICT.
The exact catalog and normalized DDL hash are checked on every open. Initialization
is exclusive and transactional; appends use BEGIN IMMEDIATE, DELETE journal and
synchronous FULL with FK/recursive triggers ON. Source connections remain mode=ro
and query_only ON. No connection issues ATTACH.

Candidate/evaluation lossless round-trips and reload identity recomputation pass,
including all three Apposition records and the real S-V-O candidate. Human text
preserves whitespace, CR/LF, combining marks, non-BMP text, language tag case,
label/event strings, citation order and supersession. Independent real-vector
hashes match all three literals in section 9. A separate Python process reloads
and verifies the same persisted evaluation without any source derivation.

Idempotent duplicates leave the projection file byte-identical. Same-ID stale
content, reidentified source forgery and corrupted stored content fail closed,
without overwriting. Superseded records, opposing judgments and forks remain
queryable/verifiable; missing/cross-candidate/cross-evaluator/self/malformed edges
and conflicting event reuse fail. No global current/latest is created.

Two schema-validated logically equal source stores use offset/reversed node/token
PKs, reassigned snapshot/book/file/tree/element keys and reversed INSERT sequences;
projection insertion order is reversed too. Both candidate and evaluation rowids
actually differ while all returned logical DTOs, candidate/evaluation identities
and persisted logical content remain equal. No rowid escapes into a DTO.

### 13.2 Commands and exact counts

Executed successfully:

- `python -B -m unittest tests.test_unit10` with integration opt-in:
  **48 run, 48 passed: 45 fast + 3 real-Matthew integration; 0 skipped**.
- External guarded whole-suite discovery, with all integration flags enabled:
  **366 run, 365 passed, 0 failures, 0 errors, 1 skipped**.
  Earlier Units 1-9 contribute 318 tests, 317 passed / 1 skipped.
- Per-module counts: Unit 1 26, Unit 2 56, Unit 3 23, Unit 4 15, Unit 5 20,
  Unit 6 22, Unit 7 19, Unit 8 51, Amendment 1 44, Unit 9 42, Unit 10 48.
- The sole skip is
  `test_unit3.Unit3Tests.test_u3_01_two_full_builds_and_logical_digests`:
  the explicitly disabled second-build gate. No obsolete-test filters.
- Unit 3's setup used a byte-identical private temporary source copy, freshly
  verified by complete schema/Expat fidelity; a >1 MB population guard recorded
  **0 full-population attempts**. The real offline System.Xml.XmlReader ran on
  synthetic regression inputs (18 synthetic population calls).
- `python -B -m scripts.verify_unit1` PASS.
- `python -B -m scripts.source_schema` PASS (source schema version 2).
- `python -B -m scripts.source_fidelity --database ...` PASS before use; complete
  fresh read-only fidelity after regressions also PASS, same counts/digest as section 11.
- Python 3.10 syntax parsing/current-runtime in-memory compilation PASS for both
  new Python files. Editor problems reported no errors in either.
- Contract documentation checks: 30 unique sequential criteria, local links resolve,
  frozen prefix unchanged, exact staged paths and `git diff --check` PASS.

**Full Matthew builds performed: 0.** All projection/reduced/copy database files
and offline .NET outputs were temporary and cleaned; no runtime DB binary is committed.

### 13.3 AC-to-evidence matrix

Test numbers below identify the correspondingly prefixed methods in
[test_unit10.py](../../tests/test_unit10.py). There are **30 PASS / 0 FAIL**;
post-commit safety evidence is verified after commit, not assumed from pre-commit tests.

| AC | Result | Concrete evidence |
|---|---|---|
| AC-U10-01 | PASS | 01, 04, 30; independent application/protocol/version, STRICT tables, no old source path changed |
| AC-U10-02 | PASS | 02-03, 41; existing empty/unknown/source bytes preserved; failed bootstrap removed and retriable |
| AC-U10-03 | PASS | 05-06, 44-45; higher version, identity/catalog/trigger/index/hash/journal drift rejected |
| AC-U10-04 | PASS | 07, 46, 48; four real candidates and both DTO families compare every field |
| AC-U10-05 | PASS | 08, 37, 40, 47-48; all dispositions, exact UTF-8 note/label/event/language, cross-process reload |
| AC-U10-06 | PASS | 16-17, 19; stale-ID V1 and reidentified-envelope V2 rejection, source mandatory |
| AC-U10-07 | PASS | 17-19, 21-26; public V1/history/V2, closed registry and no bypass flags |
| AC-U10-08 | PASS | 10, 46; duplicate candidate/evaluation idempotent and file byte-identical |
| AC-U10-09 | PASS | 11-12, 26; conflicting stored same-ID content fails and is not overwritten |
| AC-U10-10 | PASS | 13; metadata/candidate/evaluation UPDATE/DELETE/REPLACE rejected with recursive OFF |
| AC-U10-11 | PASS | 07-08, 46-48; independent ordered-array recompute and frozen candidate/human/supersession literal hashes |
| AC-U10-12 | PASS | 07, 17, 39, 46; exact arrays/components/evidence survive without range expansion |
| AC-U10-13 | PASS | 20-24, 26, 47; predecessor preservation, invalid edges/content rejected, forks coexist |
| AC-U10-14 | PASS | 24-25; opposing dispositions coexist, stored label/event reuse rejected across candidates |
| AC-U10-15 | PASS | 27; two source revisions coexist offline, old evaluation preserved, wrong snapshot V2 fails |
| AC-U10-16 | PASS | 28; independent version-2 wire produces distinct ID, current registry rejects its storage |
| AC-U10-17 | PASS | 29; shifted source PKs/reversed INSERTs, different projection candidate/evaluation rowids, equal logical records |
| AC-U10-18 | PASS | 04, 30-31, 43; read-only preflight, URI/query_only source enforcement, no ATTACH, hardlink rejection |
| AC-U10-19 | PASS | 39, 48; real Verbless clause, eight nonverb leaves, three unchanged Apposition IDs/evaluations |
| AC-U10-20 | PASS | 17, 39, 46-47; real scope !5,!7,!8,!9, exact S/V/O, no !6; reidentified envelope rejected |
| AC-U10-21 | PASS | 09, 34, 38-39, 48; closed fields, no semantic/source-identity fabrication, unchanged canonical DTOs |
| AC-U10-22 | PASS | 24, 32, 38; no ranking/theology/confidence fields, no regenerated judgment or latest API |
| AC-U10-23 | PASS | 14-15, 18, 33-36, 44; malformed IDs, wrong primitives/literals, unknown/missing/duplicate fields, JSON/protocol errors |
| AC-U10-24 | PASS | 32, 40; LOAD/offline VERIFY succeed with derive/evaluate blocked; explicit V2 invokes derivation |
| AC-U10-25 | PASS | 03, 41-43; captured handles all closed on success/errors; injected post-candidate failure rolls back |
| AC-U10-26 | PASS | Full before/after preservation and freshly repeated schema/Expat fidelity, section 13.4 |
| AC-U10-27 | PASS | Unfiltered 366-test guarded run: current prior 318 tests, 317 pass / sole slow-gate skip |
| AC-U10-28 | PASS | Freeze five paths / implementation nine paths, sole-parent chain, Git-retrievable contract, final clean-tree gate |
| AC-U10-29 | PASS | Before/after protected branch/HEAD/status identical; guarded full-population attempts 0, builds 0 |
| AC-U10-30 | PASS | Existing audits/production unchanged; no remediation, acceptance, BRW or Unit 11; explicit stop |

### 13.4 Preservation and findings

Actual final source DB equals the measured section 11 baseline on all:
160,968,704 bytes; SHA-256
`e52db7e2abdb1c2b9b4f93060312587a1363066378b7a0c9b8fb72475c25ce7e`;
user_version 2; exact catalog/index/trigger digests and 38 indexes/23 triggers.
Fresh complete ancestry/schema and independent Expat byte/normalized fidelity PASS,
same logical digest `F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.

Protected repositories before/after are unchanged:
upstream main at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean;
downstream master at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`, clean.
The pre-existing ignored source DB is preserved, not deleted or committed.

No new unresolved Unit 10 defect was observed. Initial validation caught two
Unit 10 test-fixture errors (a mock argument named `uri` collided with SQLite's
keyword; a reopened disposable snapshot connection lacked verification PRAGMAs).
Both were corrected solely in the new test file and rerun successfully.
No older Unit was modified to make tests pass.

Honest limits remain those frozen above: file owners can replace DDL/bytes;
content hashes are not authentication; SQLite guarantees depend on OS/hardware;
V2 inherits accepted immutable-source/query assumptions; the internal shared V1
dependency is explicit. No scalability/distributed durability claim is made.
Unit 5 M1, Unit 7 audit M1, Unit 8 findings and Unit 9 M-1 retain original status and
severity. Unit 10 is **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**.
Unit 11 is **NOT AUTHORIZED**. Phase is AUTHORIZED, not COMPLETE or CLOSED. STOP.
