# MACULA-Extract

Independent project for building a versioned, fidelity-preserving linguistic source store from fixed MACULA Greek source artifacts.

## Current phase
MACULA Greek Linguistic Source Store Phase

Unit 1: **IMPLEMENTED / INDEPENDENTLY ACCEPTED**.

Unit 2: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** - SQLite Source Schema & Parser Contract.
Independent decision: **ACCEPT WITH MINOR FINDINGS** ([audit](docs/audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Phase remains **AUTHORIZED**.

Unit 2 Amendment 1: **IMPLEMENTED** - schema version 2 uses post-load complete-set
membership validation instead of a per-row ancestry INSERT trigger.

Unit 3: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** - SBLGNT Matthew Source Importer & Fidelity Round-Trip.
Decision: **ACCEPT** ([audit](docs/audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Unit 4: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** - Read-Only Matthew Verse / Token Query Slice.
Decision: **ACCEPT** ([audit](docs/audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Unit 5: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** - Read-Only Syntax Navigation.
Decision: **ACCEPT WITH MINOR FINDINGS**; M1 remains unresolved (inherited token
DTO exposes build-local surrogate IDs). See [governance reconciliation](docs/governance/PHASE-STATUS.md).
The user separately authorized the bounded
[Unit 6 source evidence composition](docs/architecture/UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md).
Unit 6: **IMPLEMENTED / INDEPENDENTLY ACCEPTED**.
Decision: **ACCEPT** ([audit](docs/audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
The user separately authorized the bounded
[Unit 7 structural candidate boundary](docs/architecture/UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md).
Unit 7: **IMPLEMENTED / INDEPENDENTLY ACCEPTED**.
Independent decision: **ACCEPT WITH MINOR FINDINGS** ([audit](docs/audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Units 3, 4 and 6 are independently accepted (ACCEPT). Unit 2 Amendment 1 remains
`IMPLEMENTED` only; Unit 5 M1 and the Unit 7 M1 remain unresolved. Phase remains **AUTHORIZED**.
The separately authorized
[Unit 8 evaluated structural interpretation contract](docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md)
is **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS) at its
[in-memory implementation boundary](docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation).
No persistence is authorized.

Unit 9: **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**.
The separately authorized [S-V-O design and freeze](docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#27-authorized-component-membership-freeze-evidence)
and [expected fixture](fixtures/matthew-1-2-svo-candidate.expected.json) freeze
Matthew 1:2's independently verified S/V/O memberships and expected identity.
The [production implementation](docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#28-authorized-production-implementation)
Unit 8 Amendment 1: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS;
Unit 8 likewise, see the
[independent audit](docs/audits/UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Unit 9 independent acceptance was not performed.
The [amendment](docs/architecture/UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md)
extends only the closed `human-structural-adequacy/1` registry so Unit 9 S-V-O
candidates can also be evaluated in memory; Phase remains **AUTHORIZED**.

## Boundaries
- Upstream MACULA checkout is read-only evidence.
- SBLGNT `nodes` is the primary linguistic source for the authorized Matthew vertical slice.
- This project does not perform BRW semantic projection.
- Actor / Action / Patient / Event / Result interpretation is out of scope.
- Unit 1's accepted contract, fixtures, verifier and tests remain unchanged.
- Unit 2 permits schema/bootstrap/contracts and temporary schema tests, not a production importer/exporter or populated source database.
- The later, separate Unit 3 authorization permits the exact pinned Matthew pipeline only.
  Unit 1, the amended schema-v2 Unit 2 baseline and historical independent audits
  are preserved; this checkpoint does not change them.
- The separate Unit 4 authorization adds only read-only verse/token queries over an
  existing schema-v2 store. Unit 5's separate authorization adds only read-only
  syntax navigation. Unit 6 composes these source queries, not another full build,
  migration, interpretation or downstream integration. Separately authorized
  Unit 7 derives only in-memory Apposition structural candidates, not evaluated
  interpretations or semantic entities.

See `AGENTS.md`, `contracts/`, and `docs/governance/`.

## Unit 1 verification

Run from this repository with Python 3.10+ and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_unit1.py" -v
```

The verifier reads only the explicitly authorized upstream Matthew file, checks its Git root/revision and exact SHA-256, then checks the frozen fixtures. It does not acquire sources, normalize Greek, create databases, or update expectations. See [test instructions](tests/README.md), [fidelity constraints](docs/governance/FIDELITY-CONTRACT.md), and [phase status](docs/governance/PHASE-STATUS.md).

## Unit 2 schema verification

Python 3.10+ and SQLite 3.37+ with STRICT/JSON support, using only local standard-library dependencies:

```powershell
python -B -m scripts.source_schema
python -B -m unittest discover -s tests -p "test_unit2.py" -v
```

The first command creates and validates an empty **in-memory** database, then closes it.
That Unit 2 command does not run a production XML parser/importer or ingest data.

See the executable [DDL](schema/001-source-store.sql), [schema/identity documentation](docs/architecture/UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md),
[XmlReader profile](contracts/xmlreader-parser.unit2.json), and [locator contract](contracts/occurrence-locator.unit2.json).

## Unit 3 source fidelity pipeline

Python 3.10+, the locally installed .NET 9 SDK/runtime and Git; SQLite requirements
remain unchanged. There are no third-party package dependencies or downloads.
Use an existing temporary output directory; outputs must not already exist:

```powershell
python -B -m scripts.source_importer --output "$env:TEMP\matthew-source.sqlite3"
python -B -m scripts.source_fidelity --database "$env:TEMP\matthew-source.sqlite3" --archive-output "$env:TEMP\matthew-archive.xml" --normalized-output "$env:TEMP\matthew-normalized.xml"
python -B -m unittest discover -s tests -p "test_unit3.py" -v
```

The actual XmlReader importer stores the exact source-byte BLOB and complete generic/core
records. Publication requires schema-v2 validation, complete ancestry membership
set equality in both directions, and exhaustive independent Expat
source-versus-DB reconstruction equality. Byte export is distinct from normalized XML
serialization; normalized bytes need not reproduce the original lexical file.
Remove generated outputs when finished; no production database binary is a Git deliverable.
See the [Unit 3 contract](docs/architecture/UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md).
Default Unit 3 discovery shares one full Matthew build across the class. The
second-build determinism test remains an explicit slow gate; see [test instructions](tests/README.md).

## Unit 4 read-only source queries

The caller supplies an existing database path; no importer, network or .NET build
is run by these APIs:

```python
from scripts.source_query import get_token, get_verse

verse = get_verse(database_path, "MAT", 1, 1)
token = get_token(database_path, "MAT 1:1!3")
```

Results are immutable typed source facts. Missing verses/exact tokens return `None`;
invalid input, incompatible identity/schema and SQLite failures raise `QueryError`.
Verse tokens use canonical scripture order. Source text is not normalized or substituted.
Generated SQLite stays local and ignored; do not commit it or rebuild it for query tests.

```powershell
python -B -m unittest tests.test_unit4.Unit4FastTests -v
```

See the [Unit 4 query contract](docs/architecture/UNIT-4-MATTHEW-QUERY-SLICE.md)
for field mappings, read-only behavior and optional existing full-Matthew integration.

## Unit 5 read-only syntax navigation

The same caller-supplied database path and SQLite-enforced read-only boundary apply:

```python
from scripts.source_query import (
    get_node, get_children, get_ancestors_by_node, get_ancestors_by_token, get_members,
)

node = get_node(database_path, "400010020050040")
children = get_children(database_path, "400010020050040")
ancestors = get_ancestors_by_token(database_path, "MAT 1:1!3")
members = get_members(database_path, "400010020050040")
```

All node-entry APIs accept exact MACULA `Node@nodeId` strings (`source_node_id`),
not SQLite PKs or decoded ID components. Resolution is scoped to the single active
Matthew book/snapshot; multiple matching snapshots or source IDs raise `QueryError`.
Zero matches return `None`, consistently with Unit 4. Invalid input, incompatible
stores and topology integrity failures also raise `QueryError`, not not-found.

`NodeResult` is frozen and exposes only source identity, actual parent source
identity, sibling ordinal and nullable raw node mirrors. Missing fields remain
`None`; present-empty fields remain `""`. No SQLite node/tree/element PK is exposed.
Children are direct-only immutable tuples ordered by `sibling_ordinal`.
Both ancestor APIs exclude the starting node/leaf and return nearest parent first,
root last; known roots have `()` ancestry, distinct from unknown nodes (`None`).
Cycles fail explicitly.

Members are the exact stored `node_token_membership` set in scripture coordinate
order, using unchanged Unit 4 `TokenResult` facts. Its PK fields remain build-local
diagnostics, not persistent node identities. Leaf membership includes self.
The Matthew 1:2 S-V-O source node retains Start/End `"5"`/`"8"` but returns token
ordinals `[5,7,8,9]`, explicitly excluding 6. Head remains raw: `"1"` selects child
`V` from ordered children `S,V,O`; missing Head never defaults to child 0.
No optional Head/lexical-head API, runtime XML backend, cache or schema change is added.

```powershell
python -B -m unittest tests.test_unit5.Unit5FastTests -v
```

See the unchanged [Unit 5 contract](docs/architecture/UNIT-5-READ-ONLY-SYNTAX-NAVIGATION-CONTRACT.md),
[test instructions](tests/README.md#unit-5) and [implementation status](docs/governance/PHASE-STATUS.md).

## Unit 6 read-only source evidence composition

```python
from scripts.source_query import get_source_evidence

evidence = get_source_evidence(database_path, "MAT 1:1!3")
```

Frozen `SourceEvidence` composes the exact Unit 4 token, its source-facing leaf
`node`, nearest-parent-first `ancestors` (root last, leaf excluded), and
`parent_children` in sibling order. `membership_node` explicitly identifies the
immediate parent whose exact stored members appear in `contextual_members`.
For a root token, parent collections are empty and membership uses the leaf itself.
Higher constituents remain accessible through ancestor source IDs and Unit 5 APIs.

The same SQLite-enforced read-only boundary applies. Unknown exact refs return
`None`; invalid input, schema/access failures, ambiguous source identity and cycles
raise `QueryError`. No ID decoding, XML runtime, range-based membership or semantics
is introduced. Token DTOs remain unchanged: M1's five local PK fields are diagnostics,
not stable identities; source facts remain invariant across equivalent builds.

```powershell
python -B -m unittest tests.test_unit6.Unit6FastTests -v
```

See the [Unit 6 contract](docs/architecture/UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md),
[integration instructions](tests/README.md#unit-6) and
[current governance](docs/governance/PHASE-STATUS.md).

## Unit 7 derived structural candidates

```python
from scripts.structural_candidates import derive_structural_candidates

candidates = derive_structural_candidates(database_path, "MAT 1:1!3")
```

Exact source `Rule="Np-Appos"` on the selected linked node and its ancestors
produces an Apposition candidate, nearest match first and rootward thereafter.
Unit 9 additionally supports the bounded S-V-O family described below. Unknown exact
tokens return `None`; valid tokens without matching ancestry return `()`.
Source/database/ambiguity/navigation failures raise `QueryError`, not empty output.

Frozen candidates expose source-snapshot provenance, exact ordered token-ref scope,
anchor/child source evidence, ordered direct-child payload, explicit derivation
`source-np-appos` / `1` and status `candidate` only. SHA-256 identity uses a documented
canonical UTF-8 protocol without SQLite PKs, local paths, time or random values.
Apposition is structural, not an assertion of ontological identity. No confidence,
evaluation, copula, semantic role, persistence or source/schema mutation is added.
Unit 5 M1 remains unresolved; Unit 6 is independently accepted (ACCEPT).

```powershell
python -B -m unittest tests.test_unit9.Unit9FastTests -v
```

See the [Unit 7 contract](docs/architecture/UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md#41-authorized-initial-implementation)
and [test instructions](tests/README.md#unit-7).

## Unit 9 S-V-O clause structural candidates

The same `derive_structural_candidates(database_path, token_ref)` API returns a
tuple containing existing Apposition `StructuralCandidate` objects and/or frozen
`ClauseStructureCandidate` objects. Unknown exact refs return `None`; known refs
without a supported match return `()`. Errors remain `QueryError`.

The new family is `clause-structure / source-rule-s-v-o / 1`, status `candidate`.
Eligibility requires exact `Rule=S-V-O`, three direct S/V/O children in sibling
ordinals 0/1/2, raw `Head="1"` selecting V, and nonempty, unique, pairwise-disjoint
component memberships whose union exactly equals the anchor membership.
Membership uses stored `node_token_membership` and canonical scripture coordinates,
never Start/End arithmetic or decoded node IDs. Invalid topology, provenance,
Head, coordinates or partitions fail explicitly; legitimate structural nonmatches
produce no clause candidate.

`ClauseStructurePayload` preserves anchor, Rule, raw Head and ordered
`ClauseComponent` tuples (source ID/Cat/ordinal, structural component label and
exact member refs). Evidence is anchor, subject child, verbal child, object child.
The existing canonical identity protocol includes all these source-facing fields.
Nearest-first ordering is unchanged; exact mutually exclusive source Rules allow
at most one supported kind at any anchor, so no secondary kind sort is needed.

Matthew 1:2 anchor `400010020050040` yields S=`!5`, V=`!7`, O=`!8,!9`,
scope=`!5,!7,!8,!9`, excluding `!6`, and the independently frozen identity:
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`.
All four exact member lookups return the same candidate. Matthew 1:1 remains
Verbless with eight noun leaves, no verb leaves and unchanged Apposition IDs.

No semantic role, confidence, persistence, source-schema change or BRW integration
is introduced. Unit 8 Amendment 1 now allows human evaluation of this candidate type
(see below); no independent acceptance was performed. See [Unit 9 tests](tests/README.md#unit-9-production-implementation),
including explicit treatment of frozen pre-Unit-9 no-S-V-O assertions.

## Unit 8 evaluated structural interpretations

Unit 8 records a caller-supplied human disposition for one unchanged Unit 7
candidate; it does not generate a judgment or claim source truth.

```python
from scripts.evaluated_interpretations import (
    RationaleCitation, RationaleNote, create_evaluated_interpretation,
    verify_evaluated_interpretation,
)

record = create_evaluated_interpretation(
    database_path, candidate,
    evaluator_class="human", evaluator_label="example-reviewer",
    evaluation_protocol_id="human-structural-adequacy",
    evaluation_protocol_version="1", disposition="undetermined",
    rationale_evidence=(
        RationaleCitation("syntax_node", candidate.scope.source_node_id),
    ),
    rationale_note=RationaleNote("Further human assessment is needed.", "en"),
    event_key="caller-chosen-event:1",
)
verify_evaluated_interpretation(record)  # V1 and supplied history, offline
verify_evaluated_interpretation(record, db_path=database_path)  # also V2
```

Public frozen DTOs: `EvaluatedStructuralInterpretation`, `RationaleCitation(kind,
citation_id)` and `RationaleNote(text, language)`. Collections are tuples. Creation
requires candidate V1 recomputation using the frozen Unit 7 identity protocol and
V2 field-for-field re-derivation through the public Unit 7 API. Errors raise
`QueryError`; an unknown exact candidate is an explicit not-found error, never an
empty success. Direct DTO construction validates V1 content/identity only; use the
factory for source-grounded creation.

`compute_evaluation_id(candidate, *, evaluator_class, evaluator_label,
evaluation_protocol_id, evaluation_protocol_version, disposition,
rationale_evidence, rationale_note, event_key, supersedes=None)` validates V1
content and computes the frozen `eval-sha256:` identity without source/history
access. It does not generate `event_key`. Labels are unauthenticated assertions.

Creation and verification accept `prior_records=()` (a tuple, including complete
supersession ancestry). Same evaluator/event plus different content is rejected
within that supplied set. Supersession requires the same candidate and evaluator;
opposing evaluations and forks coexist without ranking or "latest wins".
The registry entries are human structural adequacy / version `1` for the Unit 7
Apposition candidate and, by [Amendment 1](docs/architecture/UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md),
for the Unit 9 `ClauseStructureCandidate` (`clause-structure` / `source-rule-s-v-o` / `1`).
Clause candidates pass the same V1/V2 checks; V1 additionally verifies the exact S-V-O
payload and component membership, and citations may name only the anchor, the three
child nodes and the exact scope tokens (never excluded token `MAT 1:2!6`), in canonical
order. Accepted and
rejected require citations, and every human disposition requires a nonblank note
with a verbatim BCP 47 language tag. Text is preserved without normalization.

Implementation checkpoint boundary: one commit whose sole parent is
`8f8b2e7642204378eb0e56e20d096b6233e409b2`; its actual SHA is reported after Git
creates it. Validation: **50 fast + 1 opt-in Matthew integration tests passed**;
**62 Unit 4-7 fast regressions passed**; Unit 1 and schema verifiers passed.
This is not independent acceptance. Unit 5 M1 and Unit 7 audit M1 remain unresolved.
Phase remains **AUTHORIZED**. No persistence, semantic roles, confidence, BRW
integration, source-schema changes or Unit 9.

See the [implementation contract](docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation)
and [Unit 8 test instructions](tests/README.md#unit-8).
