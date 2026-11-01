# Unit 5 — Read-Only Syntax Navigation Contract

## 1. Status and objective

**Status:** DRAFT FOR IMPLEMENTATION AUTHORIZATION

Unit 5 establishes deterministic, read-only navigation over the existing schema-v2 SBLGNT Matthew source store. It adds syntax-node lookup, ordered direct-child navigation, ancestor navigation, exact ancestry-derived token membership, and source Head navigation. It does not change the source schema or source facts.

Unit 5 builds on the existing Unit 4 verse/token query boundary. `get_verse()` and `get_token()` remain Unit 4 behavior and are regression dependencies, not new Unit 5 functionality.

## 2. Authorized public query surface

The Unit 5 public API SHALL provide behavior equivalent to:

```text
get_node(source_node_id)
get_children(source_node_id)
get_ancestors_by_node(source_node_id)
get_ancestors_by_token(token_ref)
get_members(source_node_id)
```

An internal helper equivalent to `resolve_head_child(...)` or `resolve_lexical_head(...)` MAY be implemented when useful, but lexical-head resolution is not required as a public Unit 5 API.

## 3. Source Node Identity Resolution

### 3.1 Terminology

`source_node_id` means the MACULA source `Node@nodeId`. In the current SQLite representation it corresponds to:

```text
syntax_node.upstream_node_id
```

`sqlite_node_id` means the current database-local surrogate primary key:

```text
syntax_node.node_id
```

These identities are not interchangeable.

```text
source_node_id
    ↓ resolve
sqlite_node_id
```

`source_node_id` is the Unit 5 API lookup identity within the active authorized source snapshot. `sqlite_node_id` is an internal relational implementation identity.

### 3.2 Snapshot scope

For Unit 5, a source-node lookup is conceptually scoped as:

```text
active source snapshot
+
source_node_id
```

The public API MAY accept only `source_node_id` because this Unit is restricted to the existing fixed SBLGNT Matthew store. This convenience SHALL NOT imply that a matching `nodeId` is globally identical across editions, revisions, snapshots, or future alternative Tree occurrences.

A future multi-edition or multi-revision contract MAY introduce an explicit compound `SourceNodeKey`, but that work is outside Unit 5.

### 3.3 Internal resolver

Unit 5 SHALL implement one internal resolution primitive equivalent to:

```python
_resolve_source_node_id(source_node_id: str) -> int
```

Its result is the current `sqlite_node_id`.

Resolution SHALL fail closed:

```text
0 matches  → explicit not-found
1 match    → success
>1 matches → explicit ambiguity / source-integrity failure
```

The resolver SHALL NOT conceal ambiguity with `LIMIT 1`, first-row selection, fuzzy matching, or fallback to another identifier scheme.

### 3.4 No topology inference from ID encoding

The implementation SHALL NOT parse or slice `source_node_id` digits to infer:

- parent identity;
- child identity;
- ancestry;
- scripture order;
- subtree membership;
- Head;
- verse boundaries.

Topology SHALL come from the relational parent/child representation and exact membership relation already stored in schema-v2.

### 3.5 No schema migration for resolution

Unit 5 SHALL NOT add a global constraint such as:

```sql
UNIQUE(upstream_node_id)
```

or otherwise migrate schema-v2 solely to implement source-node resolution.

Current-release upstream-ID uniqueness may be validated as release evidence, but is not promoted into a permanent cross-edition or cross-version schema axiom.

If the existing schema cannot satisfy this contract without a migration, implementation SHALL stop and report a blocker rather than silently changing the schema.

## 4. Public identity boundary

All node-oriented Unit 5 public APIs SHALL accept `source_node_id`. Consumers SHALL NOT be required to know or persist SQLite `syntax_node.node_id` values.

The normal public syntax-node representation SHOULD be source-oriented and include at least:

```text
source_node_id
parent_source_node_id
sibling_ordinal
id_raw
cat
rule
cl_type
start_raw
end_raw
head_raw
length_raw
```

The public contract SHALL NOT require consumers to persist:

```text
node_id
parent_node_id
tree_id
element_id
```

A diagnostic implementation MAY expose build-local PKs in explicitly debug-only output, but downstream application identity SHALL NOT depend on them.

## 5. `get_node(source_node_id)`

A valid source node SHALL resolve to one current SQLite row and return its source facts without semantic reinterpretation.

At minimum, the returned representation SHALL preserve the applicable raw/source mirrors:

```text
source_node_id
parent_source_node_id
sibling_ordinal
id_raw
cat
rule
cl_type
start_raw
end_raw
head_raw
length_raw
```

Missing source fields remain missing. For example, missing Head SHALL NOT become `0`.

An unknown `source_node_id` SHALL produce explicit not-found behavior. It SHALL NOT fall back to `Id`, `xml:id`, `morphId`, a root node, a similar string, or a numeric surrogate key.

## 6. `get_children(source_node_id)`

The implementation SHALL:

```text
source_node_id
→ resolve to sqlite_node_id
→ find rows whose parent_node_id equals that sqlite_node_id
→ ORDER BY sibling_ordinal
→ project each child back to source identity
```

Only direct children SHALL be returned. Descendants SHALL NOT be mixed into the result.

Child order SHALL use `sibling_ordinal`, not SQLite PK order, `nodeId` lexical/numeric order, Start/End, or canonical scripture order.

## 7. `get_ancestors_by_node(source_node_id)`

Ancestor navigation SHALL resolve the starting source node and follow the actual `parent_node_id` chain.

The public result SHALL project every ancestor back to source identity.

The ordering contract SHALL be deterministic. Recommended ordering:

```text
nearest parent first
→ ...
→ root last
```

If the starting node itself is included or excluded, the implementation contract and tests SHALL state that behavior explicitly.

## 8. `get_ancestors_by_token(token_ref)`

Token-based ancestry SHALL start from the exact token occurrence identified by `token_ref`, use its linked syntax leaf/node, and walk the actual parent chain.

It SHALL NOT resolve ancestry by Start/End containment, ref-prefix matching, Cat guessing, or parsing an upstream identifier.

Unit 4 exact token lookup behavior remains the token-entry authority.

## 9. `get_members(source_node_id)`

`get_members()` SHALL use exact node-token membership as its authority.

Conceptually:

```text
source_node_id
→ resolve to sqlite_node_id
→ node_token_membership
→ token occurrences
→ public token identities
```

Membership SHALL NOT be generated from:

```text
Start..End
min/max scripture ordinal
BETWEEN
canonical envelope
```

When an ordered list is returned for display/query convenience, member occurrences SHALL be ordered by canonical scripture order. Membership truth and display ordering remain separate concepts.

A leaf syntax node SHALL include its own linked token in its exact membership.

## 10. Head navigation

`head_raw` remains the source-provided zero-based index into the node's ordered direct children.

When Unit 5 resolves a Head child, it SHALL conceptually use:

```text
source node
→ ordered direct children
→ children[Head]
→ project selected child to source_node_id
```

Head SHALL NOT be interpreted as:

- `source_node_id`;
- SQLite `node_id`;
- scripture token ordinal;
- canonical position;
- Actor, Action, Patient, Event, or another semantic role.

Missing Head remains missing and SHALL NOT default to the first child.

## 11. Surrogate-PK invariance

Unit 5 tests SHALL NOT freeze a particular SQLite `node_id` as the expected identity of a source node.

Prohibited identity-style assertion:

```python
assert node.node_id == 12345
```

Source-level expectations SHOULD instead verify stable source facts such as:

```text
source_node_id
cat / rule / cl_type
parent and child source identities
sibling ordering
exact membership
```

Changing surrogate PK allocation across equivalent rebuilds SHALL NOT change the Unit 5 public identity or navigation result.

## 12. Read-only boundary

Unit 5 SHALL operate through the existing read-only source-store boundary.

The public syntax-navigation path SHALL NOT require:

```text
INSERT
UPDATE
DELETE
REPLACE
CREATE
DROP
ALTER
```

Unit 5 SHALL NOT write navigation caches, ancestor paths, resolved Head values, labels, explanations, or projections back into source tables.

## 13. Explicitly out of scope

Unit 5 does not authorize:

- schema version changes or schema migration;
- CUVS or other translation alignment;
- Bible Research database attachment or physical database merge;
- Bible Research UI, React/Vue components, syntax-tree presentation, or token cards;
- localization runtime implementation;
- Actor / Action / Patient / Event / Result projections;
- implicit copula generation or theological interpretation;
- N1904, full NT, another book, or companion-source integration;
- production XML reparsing as the runtime syntax-query backend;
- XmlPro dependency or parser reintroduction.

XML/source fixtures may remain independent test oracles. Runtime syntax navigation SHALL query the existing SQLite source store.

## 14. Core acceptance criteria

### AC-U5-01 — Starting repository state

Implementation SHALL record repository root, branch, starting HEAD, `git status --short`, and `git diff --check` before changes.

### AC-U5-02 — Protected prior boundaries

Unit 1 fixtures/source facts and the frozen schema-v2 source-store boundary SHALL remain unchanged unless separately authorized.

Unit 4 `get_verse()` / `get_token()` behavior SHALL remain regression-green.

### AC-U5-03 — Public source identity

All node-oriented Unit 5 public entry points SHALL accept MACULA `source_node_id`, corresponding to `Node@nodeId` / `syntax_node.upstream_node_id`.

They SHALL NOT require SQLite `syntax_node.node_id` as the durable public identifier.

### AC-U5-04 — Exactly-one resolver behavior

A valid `source_node_id` SHALL resolve to exactly one current SQLite node inside the active Unit 5 source scope.

### AC-U5-05 — Explicit not-found

Zero matches SHALL produce explicit not-found behavior, without fallback to any other identifier scheme.

### AC-U5-06 — Ambiguity fails closed

More than one match in the applicable lookup scope SHALL produce explicit ambiguity/source-integrity failure. First-row selection is prohibited.

### AC-U5-07 — Known Matthew boundary node

The source node:

```text
400010020050040
```

SHALL resolve successfully and retain:

```text
Rule  = S-V-O
Start = 5
End   = 8
```

### AC-U5-08 — Exact membership after source-ID resolution

For:

```text
get_members("400010020050040")
```

the canonical verse-token ordinals SHALL be exactly:

```text
[5, 7, 8, 9]
```

### AC-U5-09 — Envelope token 6 excluded

The same result SHALL explicitly exclude:

```text
6
```

This remains a dedicated regression criterion against future Start/End-envelope shortcuts.

### AC-U5-10 — Parent projection uses source identity

For a non-root node, `parent_source_node_id` SHALL identify the actual parent reached through `parent_node_id`.

Parent identity SHALL NOT be reconstructed from the digits of the child `source_node_id`.

### AC-U5-11 — Direct children only

`get_children()` SHALL return only direct children.

### AC-U5-12 — Child order uses sibling ordinal

Direct children SHALL be ordered by `sibling_ordinal`.

### AC-U5-13 — S-V-O child ordering

For the accepted Matthew 1:2 S-V-O clause fixture, the direct children SHALL preserve:

```text
[0] S
[1] V
[2] O
```

### AC-U5-14 — Head resolves to direct child

For the same fixture, when source `Head = 1`, Head navigation SHALL resolve to the ordinal-1 direct child, `V`.

### AC-U5-15 — Missing Head remains missing

A source node whose Head is absent SHALL NOT resolve Head to child 0 or any inferred default.

### AC-U5-16 — Matthew 1:1 ancestor navigation

Starting from token occurrence:

```text
MAT 1:1!3
```

ancestor navigation SHALL reproduce the preserved source topology through the noun/NP/apposition/NPofNP/P/CL/root chain and preserve `ClType=Verbless` at the applicable clause node.

Tests SHALL identify nodes through source facts/identity rather than freezing build-specific surrogate PKs.

### AC-U5-17 — Deterministic ancestor direction

Ancestor result ordering SHALL be explicitly defined and repeatable.

### AC-U5-18 — Exact membership authority

`get_members()` SHALL use the exact membership relation and SHALL NOT use Start/End arithmetic or scripture envelope reconstruction as authority.

### AC-U5-19 — Leaf membership includes self

For a leaf syntax node, `get_members()` SHALL return its own linked token occurrence.

### AC-U5-20 — Canonical member output order

When `get_members()` returns an ordered result, members SHALL be ordered in canonical scripture order without changing the underlying membership set.

### AC-U5-21 — Public DTO independent of surrogate PK

A caller SHALL be able to perform the authorized Unit 5 navigation operations without persisting SQLite `node_id`.

### AC-U5-22 — No fixed surrogate PK expectations

Tests and fixtures SHALL NOT establish a particular SQLite node INTEGER PK as a persistent source identity.

### AC-U5-23 — No global upstream-ID uniqueness migration

Unit 5 SHALL NOT add `UNIQUE(upstream_node_id)` or an equivalent global upstream-ID constraint.

### AC-U5-24 — No cross-snapshot identity inference

Unit 5 SHALL NOT claim that equal `source_node_id` values across different editions or revisions identify the same source occurrence.

### AC-U5-25 — No semantic invention

Unit 5 output SHALL NOT introduce Actor, Action, Patient, Event, Result, implicit copula, identity relation, or theological interpretation as source facts.

### AC-U5-26 — Read-only enforcement

The Unit 5 public query path SHALL continue to operate without source-store mutations and SHALL preserve the existing SQLite read-only boundary.

### AC-U5-27 — No schema change

Schema version, schema tables, and source columns SHALL remain unchanged. If implementation requires migration, STOP and report a blocker.

### AC-U5-28 — No runtime XML query backend

Production `get_node`, `get_children`, `get_ancestors*`, and `get_members` SHALL read the SQLite source store rather than reopening and reparsing upstream XML per request.

### AC-U5-29 — Regression gates

Before the Unit 5 checkpoint, all applicable Unit 1 through Unit 4 regression suites SHALL pass together with Unit 5 tests.

Implementation validation SHALL remain distinct from independent acceptance.

### AC-U5-30 — Git/diff hygiene

Before checkpoint:

```text
git diff --check             PASS
git diff --cached --check    PASS
```

The candidate SHALL contain no unauthorized schema migration, UI artifacts, translation-alignment artifacts, semantic projection, generated SQLite deliverable, or unintended temporary/cache artifacts.

## 15. Required negative tests

At minimum, Unit 5 SHALL include fail-closed coverage equivalent to:

```text
unknown source_node_id
→ explicit not-found

duplicate source_node_id in resolver test scope
→ explicit ambiguity failure

SQLite node_id accidentally supplied as source_node_id
→ must not silently reinterpret it as SQLite identity

source_node_id digits parsed to infer parent
→ prohibited

source_node_id digits parsed to infer membership
→ prohibited

children returned in PK order rather than sibling_ordinal
→ FAIL

membership expected as [5,6,7,8,9]
→ FAIL

membership expected as [5,6,7,8]
→ FAIL

missing Head treated as 0
→ FAIL

schema version changes
→ FAIL scope gate

global UNIQUE(upstream_node_id) added
→ FAIL scope gate

public DTO requires persisted SQLite node_id
→ FAIL contract test

source-store mutation through public query path
→ rejected
```

## 16. Definition of Done

Unit 5 is implementation-complete when the existing SQLite source store supports this stable chain:

```text
source_node_id
      │
      ▼
read-only resolver
      │
      ▼
SQLite relational syntax topology
      │
      ├── direct children
      ├── ancestors
      ├── exact members
      └── source Head
      │
      ▼
source-oriented public results
```

The decisive demonstration is:

```text
source_node_id = 400010020050040
Rule = S-V-O
Head = 1
children = S, V, O
exact members = [5,7,8,9]
6 is excluded
```

and, independently, token `MAT 1:1!3` can navigate its preserved source ancestor chain through the Matthew 1:1 Verbless structure without exposing a build-specific SQLite PK as its persistent identity.

## 17. Governance ending state

A successful implementation checkpoint SHALL update Unit 5 only to:

```text
IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE
```

It SHALL NOT be described as independently accepted until a separate acceptance audit is performed.

The Phase remains AUTHORIZED and is not COMPLETE or CLOSED merely because Unit 5 implementation succeeds.

## 18. Contract summary

> Unit 5 authorizes deterministic read-only navigation over the existing schema-v2 SBLGNT Matthew MACULA source store. A MACULA `Node@nodeId` is exposed to callers as `source_node_id` and resolved inside the active source snapshot to the current SQLite `syntax_node.node_id`. SQLite `node_id` is a build-local relational implementation key and SHALL NOT become the persistent public identity of a source node. Resolution fails explicitly on zero or ambiguous matches, topology is read from relational parent/child facts rather than decoded from upstream IDs, exact subtree membership comes only from the ancestry-derived membership relation, and Unit 5 does not authorize schema changes, cross-snapshot identity inference, translation alignment, UI work, localization runtime, semantic projection, another corpus, or source mutation.
