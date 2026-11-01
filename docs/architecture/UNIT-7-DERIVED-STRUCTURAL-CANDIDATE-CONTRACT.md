# UNIT 7 — DERIVED STRUCTURAL CANDIDATE BOUNDARY

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

## 1. Purpose

Unit 7 freezes the boundary between:

1. authoritative linguistic source facts;
2. deterministic source-evidence composition;
3. derived structural candidates; and
4. evaluated structural interpretation.

Unit 7 introduces the contract for the third item only:

DERIVED STRUCTURAL CANDIDATES.

A structural candidate is a versioned, reproducible proposal derived from
explicit source evidence.

A candidate is NOT:

- a MACULA source fact;
- an amendment to MACULA;
- an evaluated interpretation;
- a theological conclusion;
- a human-confirmed assertion;
- a BRW Actor/Action/Patient/Event/Result entity;
- a Chinese explanation;
- a Bible translation.

The central invariant is:

    source evidence
          ↓
    deterministic/versioned derivation
          ↓
    structural candidate
          ↓
    future evaluation
          ↓
    evaluated interpretation

The arrows are one-way.

No downstream candidate or evaluation may mutate, replace or redefine its
source evidence.

============================================================
2. PRECONDITIONS
============================================================

Unit 7 assumes the existence of the preceding read-only source-store/query
boundary.

At minimum the source side must be capable of providing immutable,
source-oriented evidence containing:

- exact token occurrence;
- source syntax-node identity;
- source syntax facts;
- ancestry;
- ordered local structural context;
- exact node-token membership where applicable.

Unit 7 MUST consume source information through the accepted read-only query
boundary.

It MUST NOT create a second source parser, importer or alternate linguistic
source of truth.

============================================================
3. THREE DISTINCT EPISTEMIC OBJECT CLASSES
============================================================

The system SHALL distinguish the following classes.

### 3.1 LinguisticSourceFact

A statement that the fixed source snapshot actually contains a particular
linguistic value or relationship.

Examples:

- a source node has Cat=O;
- a source node has Rule=S-V-O;
- a source clause has ClType=Verbless;
- a token has Voice=Passive;
- a token has a particular ref;
- tokens are exact members of a source node;
- a source annotation contains a particular Frame/Ref/SubjRef/Notes value.

The authoritative source store owns these facts.

Unit 7 MUST NOT create or modify them.

### 3.2 StructuralCandidate

A versioned derived proposal produced from one or more explicit source facts.

A candidate asserts only:

    given evidence E,
    derivation D proposes structural relation/type C.

The candidate is independently identifiable and inspectable.

It MUST retain sufficient evidence references to explain what source facts
caused it to be proposed.

### 3.3 EvaluatedStructuralInterpretation

A later decision accepting, rejecting, refining or otherwise evaluating a
structural candidate.

Evaluation is explicitly OUT OF SCOPE for Unit 7.

The existence of a candidate MUST NOT imply that an evaluated interpretation
exists.

============================================================
4. UNIT 7 AUTHORITY BOUNDARY
============================================================

Unit 7 SHALL be authoritative only for:

- candidate representation;
- evidence linkage;
- derivation identity/versioning;
- deterministic candidate identity;
- candidate scope;
- candidate ordering where ordering exists;
- explicit non-evaluated status.

Unit 7 SHALL NOT be authoritative for:

- truth of the candidate;
- theological meaning;
- discourse meaning;
- semantic-role truth;
- ontology entity identity;
- human interpretation;
- translation.

A candidate is derivation output, not source truth.

============================================================
5. SOURCE EVIDENCE REFERENCES
============================================================

Every candidate MUST contain at least one explicit evidence reference.

Evidence references MUST identify source-facing occurrences.

Preferred evidence targets are:

- source node identity;
- exact token ref;
- source annotation occurrence;
- a SourceEvidence result whose constituent source identities remain
  inspectable.

SQLite surrogate identifiers MUST NOT constitute the durable evidence
protocol.

In particular, the following MUST NOT be required as persistent evidence
identity:

- token_id;
- node_id;
- tree_id;
- element_id;
- book_id;
- parent_node_id.

Database-local coordinates MAY exist internally while resolving evidence,
but a persisted candidate MUST remain reconstructable from source-oriented
evidence identity.

============================================================
6. SOURCE SNAPSHOT BINDING
============================================================

A candidate MUST be bound to the source snapshot from which its evidence was
derived.

The binding MUST be strong enough to prevent a candidate generated against
one source revision from silently being treated as evidence against another
revision.

A future MACULA update SHALL NOT silently upgrade an existing candidate.

If candidate derivation is rerun against different source bytes or a
different accepted source snapshot, the result belongs to a distinct source
context.

Cross-version candidate migration/reconciliation is OUT OF SCOPE.

============================================================
7. DERIVATION IDENTITY
============================================================

Every candidate MUST identify the derivation that produced it.

The minimum logical derivation identity is:

    derivation_kind
    derivation_version

The exact implementation representation is not frozen here.

Examples of appropriate conceptual identities:

    predicate-structure / 1
    apposition-structure / 1
    genitive-attachment / 1

These names are illustrative only.

A derivation version change MUST be observable.

Changing the implementation logic while retaining the same derivation
version MUST NOT silently change candidate meaning.

============================================================
8. CANDIDATE IDENTITY
============================================================

Candidate identity MUST NOT depend on SQLite surrogate PK allocation.

Candidate identity SHOULD be deterministically derivable from stable logical
inputs equivalent to:

- source snapshot identity;
- derivation kind;
- derivation version;
- candidate kind;
- candidate scope;
- ordered evidence identities where order is semantically relevant.

Implementation MAY use a local database PK for relational convenience.

That local PK is NOT durable candidate identity.

Equivalent source stores using different SQLite PK allocation MUST produce
the same logical candidate identity.

============================================================
9. CANDIDATE SCOPE
============================================================

Every candidate MUST declare its source scope.

Scope answers:

    "What exact part of the source does this candidate make a proposal
     about?"

Candidate scope MUST be represented through exact source occurrences or
their exact source membership.

Scope MUST NOT be inferred merely from:

- numerical Start/End envelopes;
- min/max scripture token ordinals;
- source-node-ID slicing;
- SQLite PK ranges.

Discontinuous source membership MUST remain discontinuous.

A scope containing source members [5,7,8,9] MUST NOT silently become
[5,6,7,8,9].

============================================================
10. EVIDENCE ROLE
============================================================

Candidate evidence SHALL distinguish evidence identity from evidence role.

A candidate may therefore conceptually contain evidence such as:

    EvidenceRef(
        role="anchor",
        source_node_id="..."
    )

or:

    EvidenceRef(
        role="member",
        token_ref="MAT ..."
    )

or another equivalent representation.

Evidence-role vocabulary is Unit-7-owned metadata.

It MUST NOT overwrite or masquerade as source Cat, Rule, Frame, Ref,
SubjRef or any other upstream field.

============================================================
11. MINIMUM STRUCTURAL CANDIDATE SHAPE
============================================================

The conceptual minimum record is:

    StructuralCandidate(
        candidate_id,
        candidate_kind,
        derivation_kind,
        derivation_version,
        source_snapshot,
        scope,
        evidence,
        payload,
        status
    )

This is a logical shape, not frozen Python syntax or frozen SQL DDL.

### Required semantics

candidate_id
    Stable logical identity of this derived proposal.

candidate_kind
    Versioned vocabulary identifying what kind of structural proposal is
    being made.

derivation_kind
    Identity of the derivation rule/family.

derivation_version
    Explicit version of that derivation.

source_snapshot
    Source context against which the candidate was derived.

scope
    Exact source-oriented occurrence scope.

evidence
    One or more explicit source-facing evidence references.

payload
    Candidate-specific derived structural data.

status
    MUST identify the object as non-evaluated.

============================================================
12. STATUS
============================================================

Unit 7 supports only the epistemic status:

    CANDIDATE

or a semantically equivalent single value.

Unit 7 MUST NOT introduce evaluation statuses such as:

    accepted
    rejected
    confirmed
    correct
    preferred
    canonical
    human_verified
    theologically_valid

Those belong to a future evaluation contract.

Operational diagnostics such as derivation failure are not candidate
evaluation statuses.

============================================================
13. CANDIDATE KIND VOCABULARY
============================================================

Candidate kinds MUST be explicit and versionable.

Unit 7 MUST NOT begin with a universal ontology of all biblical meaning.

The initial vocabulary SHOULD remain deliberately narrow and structural.

Candidate kinds MAY describe relationships such as:

- source constituent grouping;
- predicate-bearing structural region;
- argument-like structural attachment;
- complement attachment;
- apposition;
- modifier attachment;
- coordination;
- structural dependency.

These are contract-level categories, not an authorization to implement all
of them.

The implementation unit that follows this contract MUST separately state
which candidate kinds it actually implements.

============================================================
14. SOURCE CATEGORY IS NOT SEMANTIC ROLE
============================================================

The following transformations are explicitly prohibited as unconditional
derivations:

    Cat=S  -> Actor
    Cat=V  -> Action
    Cat=V  -> Event
    Cat=O  -> Patient
    Cat=O  -> Result
    Cat=P  -> Identity
    Cat=P  -> Property

Likewise:

    Frame A0 -> Actor
    Frame A1 -> Patient
    Frame A2 -> Result

MUST NOT be treated as universally valid mappings merely because the source
contains those codes.

Candidate derivation MUST preserve the difference between:

- evidence contained in the source; and
- a proposal inferred from that evidence.

============================================================
15. MATTHEW 1:1 VERBLESS SAFETY FIXTURE
============================================================

Matthew 1:1 is a mandatory negative semantic fixture.

The source evidence contains:

    CL
    Rule=P2CL
    ClType=Verbless

and no verb leaf.

A Unit 7 derivation MUST NOT manufacture a source token representing:

- "is";
- an implicit copula;
- a verb.

Unit 7 MUST NOT create merely from this fixture:

- Action;
- Event;
- semantic Actor;
- semantic Patient.

If an implementation proposes a structural predicate candidate for a
verbless source structure, it MUST:

1. remain explicitly a candidate;
2. cite the actual source clause/predicate evidence;
3. contain no fabricated token;
4. distinguish structural predication from lexical verb presence;
5. remain unevaluated.

============================================================
16. MATTHEW 1:2 DISCONTINUOUS-SCOPE SAFETY FIXTURE
============================================================

The source node:

    400010020050040

has source facts including:

    Rule=S-V-O
    Start="5"
    End="8"

and exact canonical membership:

    [5,7,8,9]

Token 6 is not a member.

Any candidate scoped to that exact source subtree MUST preserve:

    [5,7,8,9]

and MUST exclude token 6.

No Unit 7 logic may define candidate scope as:

    all canonical tokens between min and max.

This fixture is a mandatory proof that derived structures preserve exact
source occurrence scope.

============================================================
17. PASSIVE-VOICE SAFETY RULE
============================================================

A passive source form prevents a general equation:

    grammatical subject == semantic actor.

Therefore a future candidate derivation may use passive morphology as
evidence, but Unit 7 MUST NOT define a rule that always converts a
syntactic subject into Actor.

Missing explicit actor evidence MUST remain missing.

A derivation MUST NOT invent an actor solely because its target model would
prefer one.

============================================================
18. P / OC / O2 SAFETY RULE
============================================================

P, OC and O2 MUST remain distinguishable source contexts.

Unit 7 MUST NOT collapse them into a single unconditional relation such as:

    identity
    property
    result

A future derivation MAY propose one of those interpretations if separately
specified evidence and derivation rules justify it.

Such output remains a candidate pending evaluation.

============================================================
19. ELLIPSIS / IMPLICIT MATERIAL
============================================================

Source ClType or other source annotations may indicate structures involving
ellipsis or omission.

Unit 7 MUST distinguish:

- explicit source occurrence;
- source annotation indicating omission;
- derived candidate for an implicit structural position.

A derived implicit position MUST NOT masquerade as a source token.

No invented Greek surface, lemma, ref, xml:id or morphId may be assigned to
an implicit candidate.

============================================================
20. SOURCE ANNOTATIONS
============================================================

Source annotations such as:

    Frame
    Ref
    SubjRef
    Notes
    LexDomain
    LN

MAY be used as candidate evidence when their meaning is relevant to an
authorized derivation.

Their raw source values MUST remain separately inspectable.

Candidate derivation MUST NOT rewrite the source annotation.

The mere appearance of strings such as "Event" or "Result" in an upstream
annotation does not create a downstream evaluated Event or Result entity.

============================================================
21. DETERMINISM
============================================================

Given:

- the same fixed source snapshot;
- the same source evidence;
- the same derivation version;
- the same derivation configuration;

Unit 7 candidate generation MUST be deterministic.

At minimum:

- candidate logical identities are equal;
- candidate kinds are equal;
- evidence identities and roles are equal;
- candidate scopes are equal;
- candidate payloads are equal;
- deterministic candidate ordering is equal.

SQLite surrogate-PK allocation MUST NOT affect these results.

============================================================
22. IDEMPOTENCE
============================================================

Repeated derivation over equivalent source evidence MUST NOT create a new
logical candidate merely because the process was rerun.

Where candidates are persisted, repeated execution MUST be reconcilable by
logical candidate identity rather than database insertion order.

Database-specific persistence mechanics are not frozen in this contract.

============================================================
23. DERIVATION FAILURE
============================================================

A derivation that lacks sufficient evidence MUST fail by producing no
candidate or an explicit derivation diagnostic.

It MUST NOT repair insufficient evidence by guessing.

Examples:

- no semantic actor evidence -> do not invent Actor;
- missing Head -> do not silently use child 0;
- absent source field -> do not substitute an inferred default;
- ambiguous source identity -> fail closed;
- cyclic/inconsistent source navigation -> propagate failure;
- unresolved source evidence -> do not create a success-shaped candidate.

"No candidate" is different from:

    candidate rejected.

Rejection belongs to evaluation.

============================================================
24. SOURCE IMMUTABILITY
============================================================

Candidate generation MUST NOT write to the authoritative source store.

It MUST NOT:

- UPDATE source tables;
- INSERT semantic fields into source tables;
- replace source values;
- resolve ambiguity by modifying source facts;
- materialize candidate identity into source rows;
- add Actor/Action/Patient/Event/Result columns to source tables.

A future persistent candidate store MUST be logically separate from the
authoritative linguistic source store.

============================================================
25. PERSISTENCE BOUNDARY
============================================================

This contract does not require Unit 7 to implement persistence.

For a future persistent projection store:

- source evidence references SHALL be source-oriented;
- candidate identity SHALL be stable against source-store PK reassignment;
- candidate rows SHALL preserve derivation version;
- evaluated interpretation SHALL remain separately represented;
- deleting/rebuilding projections SHALL NOT alter the source store.

Physical ATTACH, cross-database FK design and integration with another
database are NOT authorized here.

============================================================
26. NO THEOLOGICAL AUTHORITY
============================================================

Unit 7 does not determine theological truth.

Candidate generation MUST NOT label derived output as:

    biblical meaning
    intended meaning
    correct theology
    doctrine
    God's intended role
    authoritative interpretation

Structural candidates are computational proposals grounded in explicit
linguistic evidence.

============================================================
27. NO PRESENTATION-DRIVEN SEMANTICS
============================================================

Localization and UI vocabulary MUST NOT change candidate semantics.

Examples:

A Chinese presentation label for source Cat=S MUST NOT cause that source
category to become Actor.

A friendly label for P MUST NOT cause a candidate to become Identity.

A visualization edge MUST NOT become a semantic relation merely because it
is drawn as one.

Presentation belongs downstream of candidate identity.

============================================================
28. NO CONFIDENCE FABRICATION
============================================================

Unit 7 MUST NOT manufacture numerical confidence scores without a separately
authorized, defined and validated scoring model.

Do not default to values such as:

    confidence = 1.0
    confidence = 0.5
    probability = 90%

Absence of an evaluation model means confidence is absent, not 100%.

============================================================
29. ORDERING
============================================================

Where candidates or evidence have an order, that ordering MUST be defined by
the contract.

Do not accidentally use:

- SQLite PK order;
- insertion order;
- unordered set iteration;
- lexical source-node-ID sorting.

Where token evidence is presented in canonical scripture order, use the
accepted canonical source ordering.

Where structure requires sibling/source order, preserve the relevant source
ordering explicitly.

The two orders MUST NOT be conflated.

============================================================
30. TRACEABILITY
============================================================

A consumer inspecting any candidate MUST be able to answer:

1. What candidate kind is this?
2. Which derivation/version produced it?
3. Against which source snapshot?
4. What exact source occurrences are in scope?
5. What evidence supports it?
6. Which parts are source facts?
7. Which parts are derived?
8. Has it been evaluated?

For Unit 7, the answer to question 8 is always:

    NO — candidate only.

============================================================
31. REPRODUCIBILITY
============================================================

A candidate should be reconstructable from:

- frozen source snapshot;
- source evidence identities;
- derivation kind/version;
- required derivation configuration.

Incidental machine state MUST NOT determine structural meaning.

In particular, logical output MUST NOT depend on:

- SQLite surrogate IDs;
- temporary directory;
- connection identity;
- wall-clock timestamp;
- random UUID generated per run;
- insertion order;
- Python object identity.

A storage implementation MAY record operational metadata separately.

It MUST NOT make such metadata part of the candidate's logical meaning.

============================================================
32. CANDIDATE PAYLOAD
============================================================

Candidate payload SHALL be typed according to candidate kind.

Unit 7 MUST NOT force every future structural proposal into one unrestricted
JSON blob with unknowable semantics.

Likewise it MUST NOT prematurely freeze a gigantic universal relational
ontology.

The contract therefore establishes:

    common candidate envelope
        +
    candidate-kind-specific payload

Every payload schema must itself be versioned directly or through the
derivation/candidate-kind version contract.

Unknown candidate kinds must fail explicitly rather than be approximately
interpreted as a familiar kind.

============================================================
33. RELATION TO SOURCEEVIDENCE
============================================================

SourceEvidence is evidence composition.

StructuralCandidate is derivation output.

The boundary is:

    SourceEvidence
          ↓
    derive(..., derivation_version)
          ↓
    StructuralCandidate

SourceEvidence MUST NOT contain candidate conclusions merely to make
derivation convenient.

StructuralCandidate MUST NOT copy source fields and relabel them as
derived truth.

The source and candidate representations should remain visibly different.

============================================================
34. MINIMUM INITIAL IMPLEMENTATION SLICE
============================================================

This contract intentionally does NOT authorize the full projection system.

The first implementation authorized under this contract SHOULD prove the
candidate infrastructure with the smallest structurally meaningful,
non-semantic derivation.

Recommended first slice:

    APPOSITION STRUCTURAL CANDIDATE

because source Rule=Np-Appos represents an explicit structural rule while
the downstream object can remain a purely structural relationship proposal.

The implementation may derive a candidate equivalent to:

    AppositionCandidate(
        scope=<source np node>,
        members=<exact source membership>,
        evidence=<Np-Appos node and direct children>,
        derivation=<version>
    )

It MUST NOT infer that the two referents are ontologically identical.

"Apposition" here remains a structural candidate category.

Alternative initial candidate kinds require separate explicit authorization.

============================================================
35. INITIAL UNIT 7 API SHAPE
============================================================

A future Unit 7 implementation MAY expose an API equivalent to:

    derive_structural_candidates(db_path, token_ref)

or:

    get_structural_candidates(db_path, token_ref)

The actual API is NOT frozen by this architecture contract.

Before implementation authorization, the implementation prompt SHALL choose:

- production module location;
- public function name;
- initial candidate kind(s);
- whether generation is purely in-memory or persisted;
- exact DTOs;
- tests;
- governance checkpoint boundary.

============================================================
36. TEST CONTRACT FOR FUTURE IMPLEMENTATION
============================================================

Any Unit 7 implementation MUST test at least:

### Identity / reproducibility

- same evidence + derivation version -> same logical candidate;
- surrogate-PK reallocation -> same logical candidate;
- evidence ordering is deterministic;
- insertion order does not define identity.

### Evidence

- every candidate has evidence;
- evidence references resolve to source-oriented occurrences;
- evidence cannot be replaced by database PK identity;
- missing evidence fails closed.

### Scope

- exact source membership;
- discontinuous membership preserved;
- Matthew 1:2 token 6 exclusion;
- no Start/End envelope expansion.

### Epistemic separation

- candidate is not source fact;
- candidate is not evaluated interpretation;
- no accepted/rejected status in Unit 7;
- no fabricated confidence.

### Verbless

- Matthew 1:1 creates no source verb/copula;
- no unconditional Action/Event candidate;
- ClType=Verbless remains evidence.

### Semantic safety

- S does not automatically become Actor;
- V does not automatically become Action/Event;
- O does not automatically become Patient;
- P does not automatically become Identity/Property;
- Frame A0/A1/A2/AA2 are not unconditional BRW-role mappings.

### Read-only boundary

- authoritative source DB unchanged;
- source DB writes rejected;
- schema unchanged unless a later prompt separately authorizes projection
  persistence outside the source store.

============================================================
37. ACCEPTANCE INVARIANTS
============================================================

A Unit 7 implementation is acceptable only if all of the following hold.

AC-U7-01
Source facts and candidates are represented as distinct object classes.

AC-U7-02
Candidates contain explicit derivation identity/version.

AC-U7-03
Candidates contain explicit source-oriented evidence references.

AC-U7-04
Candidate logical identity is independent of SQLite surrogate PKs.

AC-U7-05
Candidates are bound to a defined source snapshot.

AC-U7-06
Exact source scope is retained.

AC-U7-07
Discontinuous membership is not converted to an envelope.

AC-U7-08
Evidence order is deterministic where order is meaningful.

AC-U7-09
Candidate generation is deterministic.

AC-U7-10
Repeated generation is logically idempotent.

AC-U7-11
Missing evidence fails closed.

AC-U7-12
Source ambiguity fails closed.

AC-U7-13
Source navigation errors/cycles are not converted into successful candidates.

AC-U7-14
No source-store mutation occurs.

AC-U7-15
No source schema mutation occurs unless separately authorized.

AC-U7-16
No candidate is represented as evaluated/accepted/rejected.

AC-U7-17
No synthetic confidence score is generated.

AC-U7-18
Matthew 1:1 remains explicitly Verbless with no fabricated source verb.

AC-U7-19
Matthew 1:1 does not automatically generate Action/Event from the clause.

AC-U7-20
S is not unconditionally Actor.

AC-U7-21
V is not unconditionally Action/Event.

AC-U7-22
O is not unconditionally Patient/Result.

AC-U7-23
P is not unconditionally Identity/Property.

AC-U7-24
Upstream Frame roles are not unconditionally converted to BRW semantic roles.

AC-U7-25
Matthew 1:2 exact scope preserves [5,7,8,9] where that source node is used.

AC-U7-26
Matthew 1:2 token 6 remains excluded from that source-node scope.

AC-U7-27
Source-node IDs remain opaque and are not decoded to infer topology.

AC-U7-28
Candidate identity does not use source-node-ID slicing as hidden topology.

AC-U7-29
Source annotations remain distinguishable from derived payload.

AC-U7-30
Implicit/elliptical structural candidates do not masquerade as source tokens.

AC-U7-31
No invented Greek surface/ref/xml:id/morphId is produced for implicit material.

AC-U7-32
Canonical scripture order and source structural order remain distinguishable.

AC-U7-33
Candidate-kind payload has explicit semantics and version ownership.

AC-U7-34
Unknown candidate kinds fail explicitly.

AC-U7-35
Localization/UI labels cannot change candidate semantics.

AC-U7-36
No theological interpretation is generated.

AC-U7-37
Source snapshot changes cannot silently upgrade an existing candidate.

AC-U7-38
A consumer can trace candidate -> evidence -> fixed source context.

AC-U7-39
Equivalent stores with reassigned surrogate PKs yield equivalent source-level
candidate output.

AC-U7-40
Existing accepted source-fidelity and read-only query regressions remain intact.

============================================================
38. EXPLICITLY OUT OF SCOPE
============================================================

Unit 7 contract does NOT authorize:

- evaluated interpretation;
- human-review workflow;
- acceptance/rejection UI;
- confidence scoring;
- probabilistic semantic inference;
- LLM interpretation;
- theological inference;

- Actor;
- Action;
- Patient;
- Event;
- Result;
- Identity;
- Property

as production semantic entities;

- BRW database integration;
- physical DB merge;
- ATTACH-based projection persistence;
- cross-database foreign keys;

- Chinese explanation generation;
- Bible translation;
- source Mandarin concatenation as translation;

- N1904;
- full NT;
- other books;
- companion-source ingestion;
- MARBLE/wordsense/adjunct merge;

- source schema migration;
- Unit 5 M1 remediation;
- XmlPro use;
- XML re-parsing at projection runtime;
- physical byte-range mapping;
- network access;

- Unit 8 implementation.

============================================================
39. ARCHITECTURAL STOP LINE
============================================================

Unit 7 freezes this boundary:

AUTHORITATIVE SOURCE

    immutable linguistic facts
              │
              ▼
    read-only SourceEvidence
              │
              ▼

--------------------------------------------------
DERIVED / REBUILDABLE BOUNDARY
--------------------------------------------------

              │
              ▼
      StructuralCandidate
              │
              ▼

--------------------------------------------------
EVALUATION BOUNDARY — FUTURE UNIT
--------------------------------------------------

              │
              ▼
 EvaluatedStructuralInterpretation

Source facts may cause candidates.

Candidates never become source facts.

Candidates never become evaluated interpretations merely by being generated.

============================================================
40. IMPLEMENTATION AUTHORIZATION
============================================================

This document alone does NOT authorize Unit 7 production implementation.

A separate implementation authorization must specify:

- actual starting repository checkpoint;
- disposition of Unit 6 independent acceptance;
- candidate kind(s) authorized;
- exact public API;
- persistence policy;
- test scope;
- authorized changed paths;
- regression requirements;
- checkpoint/governance behavior.

Design-time status before the separate implementation authorization:

Unit 7 status:

    CONTRACT DRAFT / NOT IMPLEMENTED

Phase remains governed separately.

============================================================
41. AUTHORIZED INITIAL IMPLEMENTATION
============================================================

The user separately authorized the initial implementation against actual HEAD
`b7cc92e6e42979a64919edd173ff886591552344` on `master`. Sections 1-39 and all
AC-U7 criteria above remain unchanged. The design-time alternatives and examples
are not additional production authorization. This implementation is not independent
acceptance. Unit 6 remains IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE; Unit 5's
ACCEPT WITH MINOR FINDINGS and unresolved M1 remain unchanged. Phase is AUTHORIZED.

### Executable boundary

[structural_candidates.py](../../scripts/structural_candidates.py) owns derived
DTOs and derivation; [source_query.py](../../scripts/source_query.py) remains the
unchanged source-fact / SourceEvidence layer.

```python
derive_structural_candidates(
    db_path: str | Path, token_ref: str,
) -> tuple[StructuralCandidate, ...] | None
```

Exact token entry uses `get_source_evidence`. Discovery inspects the linked node
itself, then the existing nearest-parent-first ancestry toward root. Only exact
`Rule="Np-Appos"` produces a candidate. No unrelated subtree is searched.
Unknown exact refs return `None`, following the source-query convention. Valid
tokens with no matching structure return `()`. Invalid refs, schema/provenance
failures, ambiguous identities, missing evidence and topology errors raise
`QueryError`; they never become empty successful candidate output.

The existing read-only connection and source resolver/children/member primitives
are reused without changing Unit 4-6. All candidate anchor and direct-child source
identities resolve unambiguously within the active Matthew snapshot. Scope uses
only materialized exact membership in canonical scripture order; every member
requires an actual ref agreeing with its stored coordinates. Missing membership
or omission of the selected anchor token fails explicitly. This is not a new
per-query exhaustive source-fidelity validator.

### Frozen result objects and vocabulary

- `SourceSnapshot`: source family, edition, repository URI, revision, manifest
  SHA-256, source-relative path and source-file SHA-256, read from the selected
  token's actual linked snapshot/file provenance. No SQLite snapshot PK is identity.
- `EvidenceRef`: role `anchor` or `child`, kind `syntax_node`, opaque source node ID.
- `CandidateScope`: owning source node ID and exact ordered `member_token_refs`.
- `AppositionCandidatePayload`: anchor source node ID and direct
  `child_source_node_ids` in actual sibling order; no primary/secondary/head role.
- `StructuralCandidate`: candidate ID, kind, derivation kind/version,
  source snapshot, scope, ordered evidence, typed payload and status.

The sole production kind is `apposition`; the sole derivation is `source-np-appos`
version `1`; the sole status is `candidate`. Unknown candidate kinds and evaluation
statuses fail explicitly. Payload version ownership is the derivation version.
There is no confidence field, evaluation model or semantic identity claim.

### Candidate identity protocol

Protocol tag: `macula.structural-candidate.v1`.
Canonical input is the following ordered JSON array:

```text
[
  protocol,
  [source_family, edition, repository_uri, revision, manifest_sha256,
   relative_path, source_sha256],
  candidate_kind, derivation_kind, derivation_version,
  [scope_source_node_id, [ordered_member_token_refs...]],
  [[role, kind, source_node_id]...],
  [payload_anchor_source_node_id, [ordered_child_source_node_ids...]]
]
```

Serialization uses `json.dumps(ensure_ascii=True, separators=(",", ":"),
allow_nan=False).encode("utf-8")`, without a trailing newline. Field order is explicit;
no dictionary iteration order defines identity. Evidence is anchor first, then
direct children in sibling order. Membership uses the distinct canonical scripture
order. IDs are `sha256:` followed by the lowercase SHA-256 hex digest of these bytes.
No SQLite PK, source-ID decoding, local filesystem path, timestamp, Python hash,
process identity or random value enters the protocol. Different source context
or derivation version produces distinct identity; old DTOs are not upgraded.

### Validation and stop line

[test_unit7.py](../../tests/test_unit7.py) has 16 synthetic tests and 3 opt-in
existing-Matthew integration tests. See [test commands](../../tests/README.md#unit-7)
and [actual governance evidence](../governance/PHASE-STATUS.md).
Matthew 1:1 has exactly three nested candidates for `MAT 1:1!3`, anchored at
`400010010030020`, `400010010030040`, `400010010030060`, in that order.
Matthew 1:2 exact scope remains `[5,7,8,9]`, excluding 6; S-V-O is not a candidate kind.

All generation is in memory over the existing SQLite read-only boundary.
No source/schema mutation, persistence/cache/sidecar, XML runtime, new dependency,
semantic entity/role, evaluation, implicit copula, Bible Research integration,
UI/localization or Unit 8 is implemented or authorized.