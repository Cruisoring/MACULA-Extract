# UNIT 9 — S-V-O Clause Structural Candidate Contract

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE
**Implementation authorization:** NOT GRANTED BY THIS DOCUMENT
**Recommended repository path:** `C:\Projects\MACULA-Extract\docs\architecture\UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md`

## 1. Purpose

Unit 9 extends the derived structural-candidate boundary with one narrowly defined second candidate kind for MACULA source nodes whose source rule is exactly `S-V-O`.

The first worked fixture is Matthew 1:2, anchor source node `400010020050040`. Existing source evidence establishes that this node has `Rule="S-V-O"`, `Start="5"`, `End="8"`, direct children with source `Cat` values `S`, `V`, `O` in sibling ordinals `0`, `1`, `2`, raw `Head="1"`, and exact descendant membership `[MAT 1:2!5, MAT 1:2!7, MAT 1:2!8, MAT 1:2!9]`. `MAT 1:2!6` is a sibling/non-descendant and must remain excluded even though it falls inside the numeric Start/End envelope. [Sources: UNIT-1 independent acceptance audit; Unit 7 independent acceptance audit; PHASE-STATUS]

Unit 9 remains structural only. It does **not** assert:

- `S -> Actor`;
- `V -> Action` or `Event`;
- `O -> Patient` or `Result`;
- source Head -> semantic head/agent;
- any theological interpretation.

## 2. Existing invariants

Unit 9 inherits these boundaries:

1. The source SQLite store is immutable/read-only to downstream derivation.
2. Source IDs are opaque strings. No node-ID slicing may substitute for topology.
3. `parent_node_id + sibling_ordinal` is the structural topology mirror.
4. Exact membership comes from `node_token_membership`, not `Start/End` arithmetic.
5. Source sibling order, tree traversal order, canonical scripture order, source Start/End, and exact membership are distinct concepts.
6. Derived candidate identity must be independent of SQLite surrogate PK allocation, database location, process identity, Python `hash()`, clock, and insertion order.
7. Candidate status remains `candidate`. Evaluation is a downstream concern.
8. No confidence/probability/score is generated.
9. Unit 7 Apposition behavior and identities must remain unchanged.

[Sources: MACULA architecture spike; Unit 7 independent acceptance audit]

## 3. Candidate classification

Frozen proposed values:

```text
candidate_kind     = "clause-structure"
derivation_kind    = "source-rule-s-v-o"
derivation_version = "1"
status             = "candidate"
```

The candidate means only:

> Under derivation protocol `source-rule-s-v-o/1`, the bound source snapshot contains an eligible source node explicitly marked `Rule=S-V-O`, with the required ordered direct components and exact membership partition, and this deterministic derivation proposes that source structure as a `clause-structure` candidate.

It does not mean that MACULA has supplied Actor/Action/Patient/Event semantics.

## 4. Logical DTOs

The implementation should add a candidate type compatible with the established Unit 7 structural-candidate envelope without changing accepted Apposition behavior.

```python
@dataclass(frozen=True)
class ClauseComponent:
    source_node_id: str
    source_cat: str
    sibling_ordinal: int
    component_role: str
    member_token_refs: tuple[str, ...]


@dataclass(frozen=True)
class ClauseStructurePayload:
    anchor_source_node_id: str
    source_rule: str
    source_head_raw: str
    components: tuple[ClauseComponent, ...]


@dataclass(frozen=True)
class ClauseStructureCandidate:
    candidate_id: str
    candidate_kind: str
    derivation_kind: str
    derivation_version: str
    status: str
    source_snapshot: SourceSnapshot
    scope: CandidateScope
    evidence: tuple[EvidenceRef, ...]
    payload: ClauseStructurePayload
```

`component_role` is derivation vocabulary, not a semantic role. Version 1 uses:

```text
subject-component
verbal-component
object-component
```

Each component must also retain the exact source `Cat` string `S`, `V`, or `O`.

## 5. Matthew 1:2 anchor fixture

The initial positive fixture is:

```text
anchor source node: 400010020050040
source Rule:        S-V-O
source Head:        1
source Start:       5
source End:         8

ordered direct children:
0 -> 400010020050012 -> Cat=S
1 -> 400010020070012 -> Cat=V
2 -> 400010020080021 -> Cat=O

exact anchor scope:
MAT 1:2!5
MAT 1:2!7
MAT 1:2!8
MAT 1:2!9

explicit non-member:
MAT 1:2!6
```

The exact component memberships for the S, V, and O direct children are independently frozen from raw XML and read-only SQLite, with exact cross-oracle agreement (section 27):

```text
S = ("MAT 1:2!5",)
V = ("MAT 1:2!7",)
O = ("MAT 1:2!8", "MAT 1:2!9")
```

They must not be guessed from Start/End, source-node encoding, lexical assumptions, or the anchor scope.

[Sources: UNIT-1 independent acceptance audit; Unit 7 independent acceptance audit]

## 6. Eligibility gate for `source-rule-s-v-o/1`

A node produces a Unit 9 v1 candidate only if all of the following hold:

1. the source node resolves uniquely;
2. `Rule` is exactly `S-V-O` using source-exact comparison;
3. exactly three direct children exist;
4. direct-child sibling ordinals are exactly `0, 1, 2`;
5. their source `Cat` values are exactly `S, V, O` in that order;
6. all source-facing node IDs are present and unambiguous;
7. `Head` is present as canonical integer text;
8. v1 requires raw `Head="1"`;
9. `Head=1` resolves to the ordinal-1 `V` child;
10. the anchor exact membership is non-empty;
11. every direct child's exact membership is non-empty;
12. component memberships contain no duplicates;
13. component memberships are pairwise disjoint;
14. union(component memberships) equals the anchor membership exactly in both set-difference directions;
15. anchor/component membership is obtained only from materialized exact membership;
16. canonical token ordering uses stored scripture coordinates;
17. the source snapshot is complete.

A legitimate node that simply does not match the derivation protocol yields no v1 candidate. A contradictory/invalid source-store condition fails closed with `QueryError`.

## 7. Component membership query contract

### 7.1 Resolve the anchor

Resolve `upstream_node_id` by exact source identity within the supported Matthew source boundary. Internal SQLite PKs may be used for joins but must not leave the query boundary or enter candidate identity.

Result cardinality:

```text
0 rows  -> not found / no candidate
1 row   -> continue
>1 rows -> QueryError (ambiguous source identity)
```

Never derive the book, parent, membership, or identity by slicing `nodeId`.

### 7.2 Query direct children

Query rows whose `parent_node_id` is the resolved anchor PK and order by `sibling_ordinal`.

Required structural projection:

```text
(0, "S", "400010020050012")
(1, "V", "400010020070012")
(2, "O", "400010020080021")
```

The candidate protocol must use the relational parent link and sibling ordinal. SQLite PK order is irrelevant.

### 7.3 Batch membership query

Once the anchor and three direct-child local PKs are known, query membership for all four owners through one read-only connection:

```sql
WITH requested_nodes(owner_kind, owner_ordinal, local_node_id) AS (
    VALUES
        ('anchor',    -1, ?),
        ('component',  0, ?),
        ('component',  1, ?),
        ('component',  2, ?)
)
SELECT
    r.owner_kind,
    r.owner_ordinal,
    r.local_node_id,
    t.ref_raw,
    t.book_id,
    t.chapter,
    t.verse,
    t.verse_token_ordinal
FROM requested_nodes AS r
JOIN node_token_membership AS m
  ON m.node_id = r.local_node_id
JOIN token AS t
  ON t.token_id = m.token_id
ORDER BY
    CASE r.owner_kind WHEN 'anchor' THEN 0 ELSE 1 END,
    r.owner_ordinal,
    t.book_id,
    t.chapter,
    t.verse,
    t.verse_token_ordinal;
```

The exact production SQL may adapt to actual schema column names. The invariant is that component order comes from validated sibling ordinals, and token order comes from stored canonical scripture coordinates. It must not come from local PK order, `ref_raw` lexical sorting, tree-leaf order, or Start/End.

### 7.4 Membership result model

```python
@dataclass(frozen=True)
class ComponentMembership:
    source_node_id: str
    source_cat: str
    sibling_ordinal: int
    member_token_refs: tuple[str, ...]


@dataclass(frozen=True)
class ClauseMembershipPartition:
    anchor_source_node_id: str
    source_rule: str
    source_head_raw: str
    anchor_member_token_refs: tuple[str, ...]
    components: tuple[ComponentMembership, ...]
```

No local PK occurs in this public/logical result.

## 8. Component membership validation

### 8.1 Per-set validation

For the anchor and each component:

- membership must be non-empty;
- token refs must be unique;
- ordering must already be canonical scripture order;
- every ref must be a valid stored token occurrence in the same source/tree context.

### 8.2 Pairwise-disjoint rule

Let:

```text
S_set = exact membership of child ordinal 0
V_set = exact membership of child ordinal 1
O_set = exact membership of child ordinal 2
```

Required:

```text
S_set ∩ V_set = empty
S_set ∩ O_set = empty
V_set ∩ O_set = empty
```

Any overlap is a source/store consistency error. Do not repair or deduplicate it silently.

### 8.3 Exact-partition rule

Let `A` be the anchor membership and `U = S_set union V_set union O_set`.

Required:

```text
A - U = empty
U - A = empty
```

Checking only `U subset-of A` is insufficient because it would miss an anchor member not assigned to a component.

### 8.4 Matthew fixture firewall

For anchor `400010020050040`:

```text
A == (MAT 1:2!5, MAT 1:2!7, MAT 1:2!8, MAT 1:2!9)
MAT 1:2!6 not-in A
MAT 1:2!6 not-in S_set
MAT 1:2!6 not-in V_set
MAT 1:2!6 not-in O_set
```

Any result that introduces token 6 via `5..8`, minimum/maximum ref, verse-envelope expansion, or Start/End arithmetic is invalid.

## 9. Independent fixture freeze method

The initial component memberships must be frozen using two independent evidence paths.

### Oracle A: raw XML

1. locate source node `400010020050040` in the pinned Matthew nodes XML;
2. read its three direct child nodes in XML/source sibling order;
3. recursively walk descendant `Node` leaves under each child;
4. read each leaf's exact `ref`;
5. order the resulting refs by canonical scripture coordinates;
6. record the three component membership tuples.

### Oracle B: SQLite

1. resolve the same anchor and its direct children through relational topology;
2. read each owner's rows from `node_token_membership`;
3. order by stored scripture coordinates;
4. produce the three component membership tuples.

Required before freezing fixture literals:

```text
Oracle A component memberships == Oracle B component memberships
Oracle A anchor membership      == Oracle B anchor membership
```

The expected fixture must not be generated by the same production helper that it later tests.

## 9A. Component membership freeze procedure

This section freezes the **procedure**, not the component membership values themselves. The S/V/O membership literals and the final Matthew 1:2 candidate ID become contract facts only after every gate below succeeds.

### 9A.1 Preconditions and preservation baseline

Before deriving fixture values:

1. Verify the actual `MACULA-Extract` repository root, branch, HEAD and clean/dirty state.
2. Verify the pinned upstream `macula-greek` revision and the exact Matthew source SHA-256.
3. Record the existing read-only Matthew SQLite file size, SHA-256, `PRAGMA user_version`, and relevant row counts/catalog state if that database is used.
4. Record the protected upstream/downstream repository HEADs and status.
5. Create all audit/freeze scripts and temporary output **outside** the repository.
6. Do not edit the Unit 9 contract, fixture, production code, source XML, or SQLite database until the two independent oracles agree.

Historical expected source identity may be used only as an expectation; the freeze session must measure actual values again.

### 9A.2 Oracle A — raw XML component derivation

Use an independent standard XML parser. Do not import `scripts.structural_candidates`, `scripts.source_query`, Unit 9 helpers, or fixture values.

Procedure:

1. Read the pinned `SBLGNT/nodes/01-matthew.xml` bytes and verify their SHA-256.
2. Parse the XML independently.
3. Locate exactly one `Node` whose `nodeId` is `400010020050040`.
4. Assert from raw attributes that its `Rule` is exactly `S-V-O` and its raw `Head` is exactly `1`.
5. Enumerate only its **direct child `Node` elements** in actual XML order.
6. Require exactly three direct children and freeze their raw identities/Cats only if the sequence is exactly:

```text
400010020050012 / S
400010020070012 / V
400010020080021 / O
```

7. For each direct child independently, recursively walk descendant `Node` elements and collect **leaf Nodes only**.
8. Read each leaf's exact source `ref`; do not derive a ref from `Start`, `End`, `nodeId`, `xml:id`, `morphId`, position in the document, or another field.
9. Parse the ref into numeric scripture coordinates solely for canonical ordering.
10. Build four tuples:

```text
A_xml = anchor descendant refs in canonical order
S_xml = S-child descendant refs in canonical order
V_xml = V-child descendant refs in canonical order
O_xml = O-child descendant refs in canonical order
```

11. Independently validate:

```text
A_xml == (MAT 1:2!5, MAT 1:2!7, MAT 1:2!8, MAT 1:2!9)
MAT 1:2!6 not in A_xml
S_xml, V_xml, O_xml are non-empty
S_xml, V_xml, O_xml are pairwise disjoint
set(S_xml) union set(V_xml) union set(O_xml) == set(A_xml)
```

12. Emit an audit artifact outside the repository containing the raw-source result and its SHA-256. The artifact is evidence only, not yet the fixture.

### 9A.3 Oracle B — independent SQLite membership derivation

Use direct read-only SQLite access and audit-authored SQL. Do not call the Unit 9 production membership helper or generate the expected value through `derive_structural_candidates`.

Procedure:

1. Open the existing source store with SQLite URI `mode=ro` and enable the repository's read-only/query-only profile.
2. Resolve the anchor `upstream_node_id = 400010020050040` by exact/BINARY identity within the active Matthew snapshot/book context.
3. Require exactly one anchor row.
4. Query direct children by `parent_node_id`, ordered by stored `sibling_ordinal`.
5. Require exactly three children with ordinals/Cats/source IDs matching the XML-derived structural expectation.
6. Read anchor and three child memberships from `node_token_membership` joined to `token`.
7. Order each membership tuple using the stored numeric scripture coordinates, never token PK, node PK, lexical `ref_raw`, tree-leaf ordinal, Start/End, or row-return order.
8. Build:

```text
A_db
S_db
V_db
O_db
```

9. Validate the same non-empty, uniqueness, canonical-order, pairwise-disjoint and exact-partition invariants used for Oracle A.
10. Explicitly assert `MAT 1:2!6` is absent from all four tuples.
11. Emit a second audit artifact outside the repository containing the DB-derived result and its SHA-256.

### 9A.4 Cross-oracle equality gate

The freeze MUST stop unless all four tuples match exactly and in order:

```text
A_xml == A_db
S_xml == S_db
V_xml == V_db
O_xml == O_db
```

Also require equality of:

```text
anchor source node ID
raw Rule
raw Head
direct-child source IDs
direct-child Cats
direct-child order
```

A count-only comparison is insufficient.

If either oracle disagrees with the other, do not choose one as authoritative for the fixture. Record the discrepancy and stop.

### 9A.5 Anti-circularity gate

Before writing fixture literals, verify that:

- Oracle A has no imports from MACULA-Extract production query/candidate code;
- Oracle B does not call the Unit 9 membership/candidate builder;
- neither oracle reads the Unit 9 expected fixture;
- the production implementation is not used to compute the expected candidate ID before membership literals are frozen;
- no expected component membership was copied from `Start/End` or a hand-written assumption.

The freeze evidence must therefore be `raw XML -> independently derived expected` and `SQLite -> independently derived actual`, not `production -> expected -> production`.

### 9A.6 Freeze the fixture

Only after sections 9A.2–9A.5 pass, create/update:

```text
fixtures/matthew-1-2-svo-candidate.expected.json
```

Freeze at minimum:

```text
source_node_id / anchor
Rule
Head
direct children in sibling order
anchor exact membership
S exact membership
V exact membership
O exact membership
explicit excluded token MAT 1:2!6
source snapshot identity needed by the candidate protocol
```

The JSON should contain source-facing values only. Do not write SQLite `node_id`, `token_id`, `tree_id`, `element_id`, `book_id`, snapshot PK, file PK, database path, timestamps, or audit-local IDs.

Use a deterministic JSON formatting convention and record the fixture file SHA-256 after writing.

### 9A.7 Freeze the candidate identity only after membership

After the fixture is frozen:

1. Construct the canonical Unit 9 identity input from the frozen snapshot, anchor scope, evidence order, raw Head, ordered components and exact component memberships.
2. Independently serialize that identity input using the contract's canonical JSON/UTF-8 rules.
3. Independently compute the SHA-256 and freeze the resulting `candidate_id` into the fixture.
4. Run the production candidate builder only **after** the independent expected ID exists.
5. Require production `candidate_id` and complete source-facing DTO content to equal the independently frozen expectation.

This ordering prevents the production identity helper from becoming its own oracle.

### 9A.8 Required mutation proofs before accepting the freeze

Using disposable synthetic stores or copies, prove at minimum:

1. changing `Start` or `End` does not change exact component memberships;
2. inserting `MAT 1:2!6` into an envelope does not make it a member;
3. deleting one legitimate child membership causes partition validation failure;
4. adding an anchor-external token to a child causes failure;
5. making two child memberships overlap causes failure;
6. leaving an anchor member unassigned to every child causes failure;
7. reallocating SQLite surrogate PKs leaves all frozen source-facing values and the candidate ID unchanged;
8. reversing PK allocation/order does not alter sibling order or canonical token order.

These are validation proofs. They must not modify the real Matthew database.

### 9A.9 Preservation closeout

After the freeze session:

1. Recompute the real Matthew SQLite size/SHA/version/catalog evidence captured in 9A.1 and require equality.
2. Recheck the source XML SHA and protected repository HEAD/status.
3. Remove all temporary scripts, synthetic DBs, WAL/SHM/journal files and generated bytecode created by the freeze session.
4. Review `git status`, `git diff`, `git diff --check`, staged paths and untracked files.
5. The intended repository change set for a freeze-only checkpoint is limited to the Unit 9 design/fixture/governance documentation explicitly authorized by the user. Production candidate behavior must remain unchanged until implementation authorization.

### 9A.10 Freeze result record

The freeze report should explicitly state:

```text
Oracle A anchor membership
Oracle A S membership
Oracle A V membership
Oracle A O membership
Oracle B corresponding four tuples
Cross-oracle equality result
Excluded-token-6 result
Fixture SHA-256
Frozen candidate_id
Source DB before/after SHA-256 and user_version
Protected repository preservation
```

Do not report component memberships or candidate ID as frozen if any required equality, mutation, or preservation gate was skipped or failed.

## 10. Candidate scope

Candidate scope is the anchor's exact membership:

```text
scope.source_node_id = 400010020050040
scope.member_token_refs = (
    "MAT 1:2!5",
    "MAT 1:2!7",
    "MAT 1:2!8",
    "MAT 1:2!9",
)
```

`Start="5"` and `End="8"` remain source facts but are not candidate scope arithmetic.

## 11. Candidate evidence

Evidence order is source structural order:

```text
1. anchor
2. S direct child
3. V direct child
4. O direct child
```

Proposed evidence values:

```text
("anchor",        "syntax_node", "400010020050040")
("subject-child", "syntax_node", "400010020050012")
("verbal-child",  "syntax_node", "400010020070012")
("object-child",  "syntax_node", "400010020080021")
```

Do not add every descendant node/token as evidence. Exact token membership is represented in scope and component memberships.

## 12. Candidate payload

After component membership freeze, the Matthew payload is conceptually:

```python
ClauseStructurePayload(
    anchor_source_node_id="400010020050040",
    source_rule="S-V-O",
    source_head_raw="1",
    components=(
        ClauseComponent(
            source_node_id="400010020050012",
            source_cat="S",
            sibling_ordinal=0,
            component_role="subject-component",
            member_token_refs=("MAT 1:2!5",),
        ),
        ClauseComponent(
            source_node_id="400010020070012",
            source_cat="V",
            sibling_ordinal=1,
            component_role="verbal-component",
            member_token_refs=("MAT 1:2!7",),
        ),
        ClauseComponent(
            source_node_id="400010020080021",
            source_cat="O",
            sibling_ordinal=2,
            component_role="object-component",
            member_token_refs=("MAT 1:2!8", "MAT 1:2!9"),
        ),
    ),
)
```

## 13. Candidate identity

Reuse the established structural-candidate domain convention rather than creating a PK/path/time identity.

Recommended canonical identity input shape:

```text
[
  "macula.structural-candidate.v1",
  [snapshot fields...],
  "clause-structure",
  "source-rule-s-v-o",
  "1",
  [anchor-source-node-id, [ordered exact anchor refs...]],
  [
    ["anchor",        "syntax_node", anchor-id],
    ["subject-child", "syntax_node", S-id],
    ["verbal-child",  "syntax_node", V-id],
    ["object-child",  "syntax_node", O-id]
  ],
  [
    anchor-id,
    "S-V-O",
    "1",
    [
      ["subject-component", "S", 0, S-id, [ordered S refs...]],
      ["verbal-component",  "V", 1, V-id, [ordered V refs...]],
      ["object-component",  "O", 2, O-id, [ordered O refs...]]
    ]
  ]
]
```

Serialize using the existing canonical candidate convention:

```python
json.dumps(
    value,
    ensure_ascii=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

Then:

```text
candidate_id = "sha256:" + lowercase_sha256_hex
```

The final Matthew 1:2 candidate ID must not be frozen until the actual component memberships have been independently established.

## 14. Derivation API behavior

Prefer extending the existing structural-candidate entry point rather than inventing a parallel top-level derivation API:

```python
derive_structural_candidates(db_path, token_ref)
```

Return semantics remain:

```text
unknown exact token ref              -> None
valid token, no supported candidate -> ()
valid token with candidates          -> tuple[candidate, ...]
source/schema/topology inconsistency -> QueryError
```

For every member of the Matthew anchor scope:

```text
MAT 1:2!5
MAT 1:2!7
MAT 1:2!8
MAT 1:2!9
```

the derivation should expose the same S-V-O candidate with the same candidate ID when the anchor is on that token's self/ancestor path.

`MAT 1:2!6` must not expose that candidate because it is not a descendant/member of the anchor.

## 15. Ordering and deduplication

Candidate traversal remains source-topology-relative and deterministic.

Primary ordering recommendation:

```text
nearest-first by self/ancestor position
```

If two candidate kinds occur at the same anchor, use an explicit candidate-kind registry ordinal as a secondary key. Never use candidate hash, source-node lexical order, SQLite PK, timestamp, or insertion order.

Duplicate traversal paths to the same logical candidate must collapse deterministically, but candidates of different kinds must never be merged merely because they share a scope.

## 16. Fail-closed semantics

### No candidate

These are legitimate non-matches during ancestor scanning:

- `Rule` is not exactly `S-V-O`;
- direct children are not exactly S/V/O in ordinals 0/1/2;
- v1 raw Head is absent or is not `"1"`.

### QueryError / source inconsistency

Examples:

- ambiguous source node ID;
- malformed Head text;
- Head index outside the direct-child list;
- duplicate/missing sibling ordinals;
- missing source node identity;
- empty expected membership;
- duplicate membership refs;
- overlapping component membership;
- component union differs from anchor membership;
- membership token has incomplete canonical coordinates;
- Matthew fixture token 6 appears in the anchor or a component membership;
- required source snapshot evidence is incomplete.

### Unsupported semantic request

Requests for Actor, Action, Patient, Event, Result, semantic head, confidence, or theological interpretation are outside Unit 9.

## 17. Unit 8 interaction

Unit 9 does **not** automatically make the new candidate kind evaluable by Unit 8.

The Unit 8 contract uses a closed candidate/protocol registry and explicitly requires unknown candidate kinds/derivations to fail closed. A separate amendment is required before `human-structural-adequacy/1` may evaluate `clause-structure / source-rule-s-v-o/1`.

Until such an amendment exists:

```text
Unit 9 S-V-O candidate derivation: supported after implementation
Unit 8 evaluation of that kind:    unsupported/fail closed
```

This keeps structural derivation and evaluation-protocol expansion as separate changes.

## 18. Semantic firewall

Unit 9 must contain no executable or persistence mapping equivalent to:

```text
S -> Actor
V -> Action
V -> Event
O -> Patient
O -> Result
```

The component labels mean only source structural positions under this derivation protocol.

The architecture explicitly distinguishes MACULA source syntax/annotations from later evaluated semantic interpretation. Passive, states/relations, complements, speech, IO/OC/O2, PP/ADV, ellipsis and multi-clause structures prevent mechanical S/V/O-to-semantic-role conversion.

[Source: MACULA architecture spike]

## 19. Matthew 1:1 negative fixture

Matthew 1:1 remains a mandatory negative boundary:

```text
Rule=P2CL
ClType=Verbless
8 noun leaves
0 verb leaves
```

Unit 9 must not fabricate an S-V-O candidate, a copula, a Greek verb token, Action, Event, Actor, Patient, or synthetic source identity for this verse.

[Sources: UNIT-1 independent acceptance audit; Unit 7 independent acceptance audit]

## 20. Test design

At minimum, implementation tests should cover:

1. real Matthew anchor exact membership is `[5,7,8,9]`;
2. direct children are S/V/O in ordinals 0/1/2;
3. raw `Head="1"` resolves to the V child;
4. each component membership equals an independently frozen raw-XML oracle;
5. component sets are pairwise disjoint;
6. union(component memberships) equals anchor membership exactly;
7. token 6 is absent from anchor and all components;
8. every real anchor member lookup returns the same candidate ID;
9. token 6 lookup does not return that candidate;
10. Start/End mutation cannot add token 6 or alter exact membership-derived scope;
11. deleting a component membership row fails closed;
12. inserting a token outside the anchor into a child fails closed;
13. overlapping child membership fails closed;
14. an anchor member missing from all children fails closed;
15. child union extending beyond anchor fails closed;
16. surrogate-PK reallocation leaves the source-facing candidate equal;
17. child PK order changes do not change component order;
18. token PK order changes do not change canonical member order;
19. Matthew 1:1 Verbless produces no S-V-O candidate;
20. read-only source-store preservation;
21. existing Apposition results and IDs are unchanged;
22. no confidence or semantic-role fields exist;
23. candidate ID changes when snapshot, derivation version, exact scope, evidence order, Head, component structure or component memberships change;
24. candidate ID is unchanged by DB path/hash seed/PK allocation.

## 21. Acceptance criteria

- **AC-U9-01** Unit 9 introduces exactly one new structural candidate family for exact source `Rule=S-V-O` under derivation `source-rule-s-v-o/1`.
- **AC-U9-02** Candidate status is only `candidate`; Unit 9 performs no evaluation.
- **AC-U9-03** Anchor topology is resolved from relational source topology, never node-ID encoding.
- **AC-U9-04** Direct children are exactly S/V/O at source sibling ordinals 0/1/2.
- **AC-U9-05** v1 preserves raw Head and requires `Head="1"` selecting the V child.
- **AC-U9-06** Anchor and component memberships come only from exact materialized membership.
- **AC-U9-07** Component memberships are non-empty, unique and canonically ordered.
- **AC-U9-08** Component memberships are pairwise disjoint.
- **AC-U9-09** Component-membership union equals anchor membership in both set-difference directions.
- **AC-U9-10** Matthew 1:2 anchor scope is exactly `[5,7,8,9]` and excludes token 6.
- **AC-U9-11** Token 6 cannot enter any component membership through Start/End or envelope arithmetic.
- **AC-U9-12** Component memberships are independently frozen from raw XML and compared with SQLite, avoiding circular fixture generation.
- **AC-U9-13** Candidate evidence order is anchor, S child, V child, O child.
- **AC-U9-14** Candidate payload preserves source Rule, raw Head, ordered components, source Cats, sibling ordinals, source node IDs and exact component memberships.
- **AC-U9-15** Candidate identity is snapshot-, scope-, evidence-, derivation-, Head-, component- and membership-sensitive.
- **AC-U9-16** Candidate identity is independent of surrogate PKs, DB path, hash seed, time and insertion order.
- **AC-U9-17** Every anchor member lookup produces the same logical candidate; non-member token 6 does not.
- **AC-U9-18** Existing Unit 7 Apposition behavior and candidate IDs remain unchanged.
- **AC-U9-19** Source database remains read-only and schema version is unchanged.
- **AC-U9-20** No persistence, DDL, sidecar DB or source-schema change is introduced.
- **AC-U9-21** No Actor/Action/Patient/Event/Result or unconditional semantic-role mapping exists.
- **AC-U9-22** No confidence/probability/score exists.
- **AC-U9-23** Matthew 1:1 Verbless remains a negative fixture and no verb/copula is fabricated.
- **AC-U9-24** Unit 8 continues to reject the new candidate kind until a separate registry amendment explicitly supports it.
- **AC-U9-25** Unit 5 M1 and Unit 7 audit M1 remain unchanged; Unit 9 does not remediate either finding.
- **AC-U9-26** Phase status is not made COMPLETE/CLOSED by Unit 9.

## 22. Recommended implementation decomposition

Suggested internal responsibilities:

```text
_get_exact_memberships(...)
    -> generic exact-membership retrieval + canonical ordering

_get_clause_membership_partition(...)
    -> S-V-O topology / Head / partition validation

_build_clause_structure_candidate(...)
    -> snapshot + evidence + payload + canonical identity

derive_structural_candidates(...)
    -> existing public entry point, deterministic candidate ordering
```

`_get_exact_memberships` must not know about S/V/O or semantic roles.

## 23. Recommended repository artifacts

Primary design document:

```text
C:\Projects\MACULA-Extract\docs\architecture\UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md
```

Expected later implementation artifacts, only after explicit implementation authorization:

```text
C:\Projects\MACULA-Extract\scripts\structural_candidates.py
C:\Projects\MACULA-Extract\tests\test_unit9.py
```

Recommended fixture after independent component-membership freeze:

```text
C:\Projects\MACULA-Extract\fixtures\matthew-1-2-svo-candidate.expected.json
```

The fixture must not contain guessed component memberships or a guessed candidate SHA.

## 24. Explicit non-goals

Unit 9 does not include:

- Unit 8 independent acceptance;
- Unit 8 registry amendment;
- persistence of candidates/evaluations;
- projection/evaluation database design;
- semantic roles or ontology;
- BRW integration;
- theological interpretation;
- new books, N1904 or full NT;
- companion-source merge;
- deterministic evaluator protocol;
- AI/model evaluator;
- Unit 5 M1 remediation;
- Unit 7 audit M1 remediation.

## 25. Implementation authorization

This document is a **design artifact**. Creating or storing this design document does not itself modify production behavior.

A later implementation authorization should explicitly authorize:

- extension of `scripts/structural_candidates.py`;
- `tests/test_unit9.py`;
- independent raw-XML freeze of component membership fixture values;
- the new fixture JSON;
- bounded documentation/governance updates;
- regression testing proving existing Apposition candidates unchanged.

Until then:

```text
UNIT 9: DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED
```

## 26. Final stop line

```text
AUTHORITATIVE SOURCE
      |
      v
exact source topology + exact membership
      |
      v
Unit 7 AppositionCandidate
Unit 9 ClauseStructureCandidate (S-V-O only)
      |
      X  STOP

No automatic semantic-role projection.
No S->Actor.
No V->Action/Event.
No O->Patient/Result.
No persistence.
No Unit 8 support without a separate registry amendment.
```

## 27. Authorized component-membership freeze evidence

**Unit 9: DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED.**
**Production implementation: NOT YET PERFORMED.**

The user separately authorized this design/fixture freeze only, starting on clean
tracked `master` at `5bfd1d4b979aa0f4f42f101eeddf72118b46912a`.
The sole untracked input was this user-created contract. Its exact original bytes
were preserved outside the repository before editing; starting SHA-256:

```text
EB61C1A305EDFA8DD6B2383BB5317B07E29489178F8278B85D1B43C00162F94C
```

Only the current status/header hard-break whitespace, explicitly unfrozen
membership placeholders, and this additive evidence section are reconciled here.
All design criteria, AC-U9-01 through AC-U9-26, identity field ordering and semantic
firewalls are preserved. No production module or existing test is changed.

### 27.1 Source and independent oracles

Upstream HEAD was verified as `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
with a clean worktree. Actual raw `SBLGNT/nodes/01-matthew.xml` SHA-256:

```text
FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4
```

Two separate temporary standard-library audit scripts ran outside the repository:

- **Oracle A:** parsed the actual XML using ElementTree; located exactly one
  anchor by raw `nodeId`; read exact Rule/Head and direct children in XML order;
  recursively collected actual leaf `ref` attributes independently for each owner;
  ordered refs by parsed numeric scripture coordinates. Its actual result was
  printed and recorded before Oracle B ran.
- **Oracle B:** used direct `sqlite3` SQL, URI `mode=ro`, `query_only=ON`,
  `foreign_keys=ON`, `recursive_triggers=ON`; uniquely resolved the anchor in
  the active Matthew book/snapshot; followed `parent_node_id` and ordered by
  `sibling_ordinal`; queried materialized memberships and ordered tokens by
  stored book/chapter/verse/token coordinates.

Both independently confirmed anchor `400010020050040`, exact `Rule=S-V-O`,
raw `Head=1`, and these direct children:

| Ordinal | Source node ID | Source Cat | Exact component membership |
|---|---|---|---|
| 0 | `400010020050012` | `S` | `("MAT 1:2!5",)` |
| 1 | `400010020070012` | `V` | `("MAT 1:2!7",)` |
| 2 | `400010020080021` | `O` | `("MAT 1:2!8", "MAT 1:2!9")` |

Actual tuples, preserving order:

```text
A_xml = ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
S_xml = ("MAT 1:2!5",)
V_xml = ("MAT 1:2!7",)
O_xml = ("MAT 1:2!8", "MAT 1:2!9")

A_db = ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
S_db = ("MAT 1:2!5",)
V_db = ("MAT 1:2!7",)
O_db = ("MAT 1:2!8", "MAT 1:2!9")
```

**Cross-oracle equality: PASS.** All four tuples, anchor identity, Rule, raw Head,
ordered child IDs/Cats/ordinals, raw spans and all seven snapshot fields match.
Every component is nonempty and unique, pairs are disjoint, and the union equals
the anchor in both set-difference directions. `MAT 1:2!6` is absent from the anchor
and every component. Raw Start/End remain `5`/`8`, not membership arithmetic.

**Anti-circularity: PASS.** Oracle A imports no production code. Oracle B uses
audit-authored SQL, not production query/candidate/member helpers. Neither reads
the new Unit 9 fixture, calls `derive_structural_candidates`, hardcodes an expected
S/V/O component tuple or infers membership from Start/End or encoded node IDs.
Snapshot metadata for A comes from the pinned Unit 1 manifest and measured source;
B independently reads linked provenance. Both audit-result JSON artifacts had
SHA-256 `7064D12AB49E553A4698E96099A71580AEC032A626993C794FD4EB008F635002`.
Temporary scripts and outputs are removed during closeout.

### 27.2 Frozen fixture and identity

Fixture: [matthew-1-2-svo-candidate.expected.json](../../fixtures/matthew-1-2-svo-candidate.expected.json).
It contains only source-facing values: snapshot, future candidate envelope, exact
anchor/component refs, raw Rule/Head, source-ordered evidence and explicit excluded
token. `source_annotations` records raw Start/End outside identity; it cannot
expand scope. There are no local PKs, DB paths, timestamps or audit-local IDs.

Formatting: UTF-8/ASCII, two-space JSON indentation, LF, one final newline.
Final fixture byte SHA-256:

```text
6986B8A03465A4AD05533D12A714CE87CADE9ABD760555D4586F1758EEF9764C
```

The component literals were written only after the oracles agreed. A separate
audit-only encoder then independently constructed section 13's ordered identity
array from those frozen values, with the seven snapshot fields in Unit 7 order,
kind `clause-structure`, derivation `source-rule-s-v-o` / `1`, exact anchor scope,
anchor/S/V/O evidence, raw Head and ordered structural components with exact
memberships. It used the exact canonical JSON/UTF-8 serialization in section 13,
without a trailing newline and without any production identity helper.

Only after that computation was its result added to the fixture:

```text
sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087
```

This is an independently frozen **expected** identity, not production output.
The production-comparison steps in 9A.7 remain later implementation gates: no
Unit 9 builder exists or was created/run in this freeze-only task.

### 27.3 Mutation/invariance controls

Eight independent controls passed using disposable, reduced audit-only relational
stores outside the repository, not a modified or rebuilt Matthew store:

| Control | Actual exercise | Result |
|---|---|---|
| M1 | Change raw Start/End to `999`/`1` | Exact component/anchor memberships and logical identity input unchanged |
| M2 | Set an envelope `5..9` containing 6 | Token 6 still absent; exact membership and logical identity input unchanged |
| M3 | Delete legitimate S-child membership `MAT 1:2!5` | Partition validation rejects empty component |
| M4 | Add anchor-external `MAT 1:2!10` to O | Rejects component union extending beyond anchor |
| M5 | Add S's `MAT 1:2!5` to O | Rejects overlapping components |
| M6 | Remove O's `MAT 1:2!9`, retaining O's token 8 | Rejects unassigned anchor member with all components still nonempty |
| M7 | Reallocate snapshot/book/file/element/sentence/tree/node/token PKs | All frozen source-facing values and canonical logical identity input equal |
| M8 | Reverse node/token PK allocation and insertion order | S/V/O sibling order, canonical token order and partition unchanged |

M8 additionally distinguished numeric `!8,!9,!10` order from lexical and reversed
token-PK order. **8 passed, 0 failed, 0 skipped.** These demonstrate independent
logical-input invariance only; production candidate-ID PK invariance remains a
future Unit 9 implementation test, not a claimed result of this freeze.

### 27.4 Regression, preservation and governance

`python -B -m scripts.verify_unit1`: **PASS**, exit 0.
No existing production, Unit 7/8 test, accepted fixture or Unit 8 registry interaction
changed, so Unit 7/8 suites were not rerun for this documentation/fixture-only
checkpoint. No Unit 9 implementation tests exist or are claimed.
No Unit 3 discovery, second full build or Matthew rebuild was run.

Actual real database before/after:

- size: **160,968,704 bytes**;
- SHA-256:
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`;
- `PRAGMA user_version=2`, schema cookie `51`;
- full schema/catalog rows (including indexes, triggers and root pages) equal;
  canonical catalog SHA-256:
  `4DD7EC2FCE553C8B523841DDBE2D2D522BE975DDE1CA0C192D1A57ECA7AAE5A3`;
- all 12 table counts equal, including 18,329 tokens, 56,488 syntax nodes,
  159,391 memberships, 1,134 sentences/Trees, 59,891 XML elements,
  767,429 attributes and 179,675 content records;
- original file modification time unchanged; source XML SHA unchanged.

Protected repositories retain their clean starting states:
`C:\Works\macula-greek` at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
`C:\Projects\bible-research-merged` at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.
No temporary audit script/store/output or generated bytecode is retained in the
repository. Created audit intermediates are removed outside it as well; the exact
original user-contract backup is intentionally preserved.

One freeze-only checkpoint has sole parent
`5bfd1d4b979aa0f4f42f101eeddf72118b46912a`; its actual resulting SHA is reported
after Git creates it, not fabricated here or added by amending history.

Unit 8 remains **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**.
Unit 9 remains **DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED**.
Implementation is **NOT YET PERFORMED**. Phase remains **AUTHORIZED**.
Unit 5 M1 and Unit 7 audit M1 remain unresolved and unchanged.

**UNIT 9 PRODUCTION IMPLEMENTATION WAS NOT STARTED.**
No Unit 8 amendment, persistence, semantic projection, BRW integration or Unit 10.
Stop after the freeze checkpoint and wait for separate production authorization.

## 28. Authorized production implementation

The user separately authorized production implementation from clean `master` at
`22595753477d6ed36317bb685347d77ed1c0a567`, root `C:\Projects\MACULA-Extract`.
The required Git root/branch/HEAD/log/status/porcelain/whitespace checks passed.
This section supersedes the historical freeze-only production stop in section 27.
Sections 1-27, the frozen identity field ordering and AC-U9-01 through AC-U9-26
are preserved; only the current lifecycle header and this additive evidence change.
This is implementation validation, **not independent acceptance**.

### 28.1 API, immutable DTOs and eligibility

[structural_candidates.py](../../scripts/structural_candidates.py) extends the
existing `derive_structural_candidates(db_path, token_ref)` entry point:

```python
tuple[StructuralCandidate | ClauseStructureCandidate, ...] | None
```

Unknown exact token: `None`; known token without a supported match: `()`;
supported candidates: tuple; source/store/input failures: `QueryError`.
The existing Apposition `StructuralCandidate` class and payload remain intact.
Parallel frozen `ClauseStructureCandidate`, `ClauseStructurePayload` and
`ClauseComponent` dataclasses implement section 4 with tuple collections.
Clause classification is closed to `clause-structure / source-rule-s-v-o / 1`,
status `candidate`.

`_get_exact_memberships` resolves opaque source identities internally, batches
stored memberships through the owned read-only SQLite connection, and checks
canonical coordinates, duplicate refs, source/tree context and linked snapshot.
Local PKs never leave this internal boundary or enter candidate identity.
`_get_clause_membership_partition` checks exact Rule, ordered direct-child
Cats/ordinals, raw Head and the nonempty, unique, disjoint exact partition.
It uses no Start/End arithmetic, node-ID decoding or reconstructed membership.
Malformed Head, out-of-range Head, duplicate/missing ordinals, missing/ambiguous
identities and contradictory memberships/provenance fail explicitly.
As section 16 specifies, absent Head or canonical in-range Head `0`/`2` is a
legitimate v1 nonmatch, not repaired to `1`.

Traversal remains self/nearest-ancestor first. The exact supported Rules are
mutually exclusive, so at most one supported candidate kind exists per anchor;
there is no secondary hash/PK/lexical sort or duplicate traversal path.
Mixed Apposition/clause ancestry is tested in nearest-first order.

### 28.2 Frozen production comparison and invariance

The committed fixture was read-only expected data throughout. Production did not
regenerate its memberships, snapshot, identity input or expected candidate ID.
The complete real-Matthew candidate DTO equals its frozen source-facing content:

- anchor `400010020050040`, Rule `S-V-O`, raw Head `1`;
- S node `400010020050012`, ordinal 0, membership `("MAT 1:2!5",)`;
- V node `400010020070012`, ordinal 1, membership `("MAT 1:2!7",)`;
- O node `400010020080021`, ordinal 2, membership
  `("MAT 1:2!8", "MAT 1:2!9")`;
- anchor scope `("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")`;
- `MAT 1:2!6` absent from anchor/components and does not expose this candidate;
- evidence order anchor, subject child, verbal child, object child;
- naturally computed ID
  `sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`.

All four member lookups return the same candidate. Section 13's ordered identity
array and canonical ASCII-escaped UTF-8 bytes are independently asserted.
Controlled snapshot/version/scope/evidence/Rule/Head/component/member mutations
change identity. Reallocated snapshot/book/file/element/sentence/tree/node/token
PKs, reversed node/token PK ordering, database location and Python hash seed
preserve the complete candidate. Numeric `!8,!9,!10` ordering is tested.
Raw Start/End mutation preserves scope, payload and ID. Missing, overlapping,
external and unassigned memberships fail explicitly on disposable synthetic stores.

Matthew 1:1 remains P2CL/Verbless, eight noun leaves and zero verb leaves.
All three Apposition IDs and complete DTO content match the measured pre-change
baseline. The original Apposition canonical identity test remains unchanged.
Unit 8's production, tests, contract and closed registry are unchanged. New clause
DTO evaluation fails closed; existing Apposition records still verify offline/V2.

### 28.3 Validation actually performed

[test_unit9.py](../../tests/test_unit9.py) contains **39 fast tests + 3 opt-in
real-Matthew integration tests**. Final execution: **42 passed, 0 failures/errors,
0 skips** within the filtered combined follow-up.
Both required commands passed:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
```

The guarded external Units 1-9 run reused the existing Matthew database read-only,
with fresh complete BYTE/NORMALIZED/schema/membership validation and logical digest
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
It recorded zero full-source population attempts. Unit 3's second-build gate
remained disabled.

Initial combined run: **272 executed, 265 passed, 2 failures, 0 errors, 5 skips**.
Both failures were additional frozen Unit 8 assertions that S-V-O was unsupported.
Those source files were not edited. Replacement Unit 9 tests retain forged-envelope
rejection and real Apposition evaluation assertions alongside the new clause behavior.
Final follow-up of Units 1/2/4-9: **251 executed, 245 passed, 0 failures/errors,
6 skips**. Unit 3's successful **22 passed + 1 explicit second-build skip** from
the initial run remains valid; no production code changed between these runs.
Thus final per-unit evidence is **267 passed, 7 explicitly skipped**, not a claim
that a single 274-test suite ran. The six superseded Unit 7/8 tests and the retained
Unit 3 skip are individually listed in [test instructions](../../tests/README.md#unit-9-production-implementation).

Python 3.10 syntax parsing and current-runtime compilation passed without bytecode
output. Pylance's active workspace did not expose these external-repository files
to its syntax checker; no Pylance/type-check success is claimed.
Temporary fixture-construction/diagnostic expectation failures were corrected
before the final successful run; the external implementation report records attempts.

### 28.4 Preservation, checkpoint and stop

Real source DB before/after: **160,968,704 bytes**, `user_version=2`, SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`;
all 75 measured catalog/index/trigger entries equal. SQLite URI `mode=ro` rejects
temporary-store write attempts even with `query_only=OFF`; owned connections close.
No production DDL, migration, persistence, cache or sidecar is introduced.
The frozen fixture remains 2,368 bytes, SHA-256
`6986B8A03465A4AD05533D12A714CE87CADE9ABD760555D4586F1758EEF9764C`.
Protected repositories retain clean status and their measured HEADs:
upstream `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
downstream `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.
Matthew XML SHA remains
`FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.

Changed paths are limited to the production module, new Unit 9 tests, this contract,
root README, architecture index, phase status, AGENTS and test instructions.
Unit 1/schema/importer/fidelity/Unit 7 contract/Unit 8/historical audits are unchanged.
One implementation checkpoint has sole parent
`22595753477d6ed36317bb685347d77ed1c0a567`; its actual resulting SHA, parent,
subject and clean final state are verified and reported after Git creates it,
not fabricated inside its own diff or added by amending history.

Unit 9: **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**.
Unit 8: **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**, unchanged.
Phase: **AUTHORIZED**, not COMPLETE or CLOSED.
Unit 5 M1 and Unit 7 audit M1 remain unresolved.

**UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.**
No Unit 8 registry amendment. No persistence. No semantic projection.
No BRW integration. No Unit 10. Stop after the implementation checkpoint.
