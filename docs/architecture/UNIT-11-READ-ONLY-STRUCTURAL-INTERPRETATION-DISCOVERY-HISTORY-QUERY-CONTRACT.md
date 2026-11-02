# UNIT 11 — READ-ONLY STRUCTURAL INTERPRETATION DISCOVERY & HISTORY QUERY BOUNDARY

**Status:** CONTRACT FROZEN / NOT IMPLEMENTED

**Implementation authorization:** NOT AUTHORIZED

Freeze scope: design contract only. Freezing this contract does not authorize implementation,
tests, a production module, independent acceptance or any later Unit. The Phase remains
AUTHORIZED, not COMPLETE or CLOSED. Preconditions verified at freeze: Unit 10 is
IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT) per `docs/governance/PHASE-STATUS.md`,
which remains the authoritative lifecycle record.

## 1. Purpose

Unit 11 defines the smallest read-only consumer boundary over the physically separate, append-only structural-candidate and evaluated-interpretation store established by Unit 10.

It answers two connected questions:

1. **Discovery:** Given a scripture location such as `MAT 1`, `MAT 1:2`, or `MAT 1:2!5`, which persisted structural candidates are relevant?
2. **History:** Given a discovered `candidate_id` or a known `evaluation_id`, what candidate, evaluations, supersession relationships, and unsuperseded graph leaves are present?

Unit 11 reconstructs and queries existing records. It does not create, modify, rank, merge, resolve, semantically project, or persist them.

```text
Authoritative linguistic source facts
        ↓
SourceEvidence
        ↓
StructuralCandidate
        ↓
EvaluatedStructuralInterpretation
        ↓
Unit 10 separate append-only persistence store
        ↓
Unit 11 discovery and read-only history/query boundary
        ↓
STOP
```

## 2. Status and authorization boundary

This document is a design contract only.

It does not authorize:

- a production Unit 11 module;
- Unit 11 tests;
- changes to the Unit 10 schema or representation;
- changes to the authoritative source store;
- candidate or evaluation creation;
- semantic projection;
- BRW integration;
- localization or UI implementation;
- consensus, confidence, ranking, or canonical-answer computation;
- independent acceptance;
- any later Unit.

A future implementation requires separate, explicit authorization.

## 3. Core model

Unit 11 exposes two query layers.

### 3.1 Scripture discovery

The caller starts with a human-facing scripture selector:

```text
MAT
MAT 1
MAT 1:2
MAT 1:2!5
```

The selector discovers persisted candidates by inspecting their validated exact member-token scope.

### 3.2 Logical identity and history lookup

Discovery yields stable logical identities:

```text
candidate_id
```

The caller may then retrieve the complete candidate-centered history:

```text
candidate
+ all evaluations
+ explicit supersession edges
+ unsuperseded graph leaves
```

A content-derived ID is an identity and permalink mechanism. It is not the only discovery mechanism.

## 4. Epistemic boundary

Unit 11 adds no new epistemic object comparable to `StructuralCandidate` or `EvaluatedStructuralInterpretation`.

```text
stored record
≠ query precedence
≠ current truth
≠ semantic truth
```

Unit 11 has no concept of:

```text
best evaluation
correct evaluation
canonical evaluation
winning evaluation
preferred evaluation
latest truth
current truth
consensus
majority
confidence
score
rank
```

Persistence does not add authority. Retrieval does not add authority. Being unsuperseded does not add authority.

## 5. Store-access boundary

Unit 11 is a consumer of Unit 10.

Every Unit 11 projection-store connection MUST be SQLite-enforced read-only. If source-grounded verification is performed, the authoritative source database MUST also be read-only.

```text
source store       READ ONLY
projection store   READ ONLY
```

Unit 11 MUST NOT perform:

```text
INSERT
UPDATE
DELETE
REPLACE
UPSERT
CREATE
ALTER
DROP
ATTACH
DETACH
VACUUM
schema migration
```

Unit 11 MUST NOT invoke Unit 10 write APIs through its public query path. Existing Unit 10
read APIs are unchanged by this contract; whether Unit 11 reuses them is an implementation
decision, provided every Unit 11 result satisfies this contract.

## 6. Store validation

Before returning a successful query result, Unit 11 MUST verify the Unit 10 store contract required to reconstruct the requested records.

It MUST fail closed on:

- unsupported store version;
- catalog drift or missing required objects;
- malformed persisted JSON;
- unsupported record, candidate, derivation, or evaluation protocol;
- candidate identity mismatch;
- evaluation identity mismatch;
- contradictory same-ID representations;
- malformed supersession history, including dangling, cross-candidate, cross-evaluator,
  self-referential and cyclic supersession.

A malformed or incompatible store is an error, not an empty store.

Discovery cannot prove that a candidate row does not match a selector unless that row can be
decoded and validated. Selector discovery MUST therefore evaluate every persisted candidate
row, and any candidate row that cannot be validated is an ERROR, never a silent non-match.
Valid non-matching rows are excluded only after their exact scope has been validated.

## 7. Scripture selector

The logical selector is:

```python
ScriptureSelector(
    book: str,
    chapter: int | None = None,
    verse: int | None = None,
    token: int | None = None,
)
```

Constraints:

- `book` is required;
- `verse` requires `chapter`;
- `token` requires `chapter` and `verse`;
- `chapter`, `verse` and `token` are positive integers (booleans are rejected), matching the
  persisted token-ref grammar `BOOK C:V!W`, where `!W` is the token ordinal within the verse;
- the initial authorized corpus may remain restricted to `book="MAT"`;
- unsupported books or selector shapes fail explicitly;
- selector parsing does not decode source node IDs;
- a well-formed selector addressing a location that no persisted candidate touches yields
  EMPTY-DISCOVERY. Unit 11 does not consult the source store to decide whether the location exists.

This section freezes the logical selector fields. Whether callers supply a DTO or a strict
string form (open question 3) is a surface decision only. Any string form MUST parse to these
same fields under the persisted token-ref grammar, with no prefix, wildcard or fuzzy matching.

Selectors identify a scripture-address domain. They do not define or expand candidate membership.

## 8. Discovery semantics

### 8.1 Exact-token discovery

A candidate matches token `T` if and only if:

```text
T ∈ candidate.scope.member_token_refs
```

No numeric envelope, lexical string interval, SQLite PK interval, `Start`/`End`, row order, or inferred gap filling is permitted.

All selector-to-scope comparisons use the parsed integer coordinates `(book, chapter, verse,
token)` of the validated exact member token refs. String prefix, `LIKE`, `GLOB` or substring
matching is prohibited: `MAT 1:2` must not match `MAT 1:20!1`, and `MAT 1:2!5` must not match
`MAT 1:2!50`.

### 8.2 Verse discovery

A candidate matches verse `V` if and only if at least one exact persisted member token belongs to `V`.

```text
candidate.scope.member_token_refs ∩ verse(V) ≠ ∅
```

A verse match discovers the candidate. It does not replace or expand the candidate's exact scope with every token in the verse.

### 8.3 Chapter discovery

A candidate matches chapter `C` if and only if at least one exact persisted member token belongs to `C`.

A candidate may therefore be discovered by more than one verse or chapter if its exact scope crosses a boundary. Discovery must not require the candidate scope to be wholly contained in the selector.

### 8.3.1 Book discovery

A candidate matches book `B` if and only if at least one exact persisted member token belongs
to `B`. The same intersection-only, no-expansion rule applies.

### 8.4 Candidate-first rule

Discovery returns candidates, including candidates with zero evaluations.

The following remain distinct:

```text
candidate absent
candidate exists but has no evaluation
candidate evaluated as undetermined
candidate evaluated as rejected
candidate evaluated as accepted
```

Unit 11 MUST NOT implement evaluation-first discovery that hides unevaluated candidates.

## 9. Exact-scope firewall

Candidate membership is the validated ordered tuple of exact member token refs persisted by Unit 10.

Unit 11 MUST NOT reconstruct candidate membership using:

```text
min/max token ordinal
source Start/End
verse envelope
chapter envelope
lexical range between refs
string prefix / LIKE / GLOB matching of refs
SQLite PK range
rowid range
insertion order
```

Discovery containment and candidate scope are different relations:

```text
discovery_match(selector, candidate)
scope_membership(token, candidate)
```

A broad selector may discover a candidate without making every token in that selector a candidate member.

## 10. Matthew 1:2 mandatory discontinuity fixture

For the frozen Matthew 1:2 S-V-O candidate:

```text
anchor: 400010020050040
Rule: S-V-O

S = MAT 1:2!5
V = MAT 1:2!7
O = MAT 1:2!8, MAT 1:2!9

exact scope = (
    MAT 1:2!5,
    MAT 1:2!7,
    MAT 1:2!8,
    MAT 1:2!9,
)
```

`MAT 1:2!6` is not a member.

Required behavior:

```text
selector MAT 1:2   → candidate discovered
selector MAT 1:2!5 → candidate discovered
selector MAT 1:2!6 → candidate NOT discovered
selector MAT 1:2!7 → candidate discovered
selector MAT 1:2!8 → candidate discovered
selector MAT 1:2!9 → candidate discovered
```

Prohibited behavior:

```text
infer membership as 5..9
fill token 6 because it lies between 5 and 9
infer membership from raw Start=5 / End=8
```

Token 6 is a tree sibling rather than a descendant of the S-V-O subtree. Unit 11 preserves the resulting discontinuity instead of repairing it.

## 11. Candidate discovery operations

Proposed public operations:

```python
list_persisted_candidates_for_selector(
    projection_db_path,
    selector: ScriptureSelector,
)

list_persisted_candidates_for_chapter(
    projection_db_path,
    book,
    chapter,
)

list_persisted_candidates_for_verse(
    projection_db_path,
    verse_ref,
)

list_persisted_candidates_for_token(
    projection_db_path,
    token_ref,
)
```

The chapter, verse, and token operations may be convenience wrappers around the selector operation.

Every candidate returned by discovery MUST be fully reconstructed and validated. Discovery MUST NOT return an unvalidated physical row merely because an index matched.

## 12. Candidate lookup

```python
get_persisted_candidate(
    projection_db_path,
    candidate_id,
)
```

Semantics:

- malformed `candidate_id` → error;
- valid well-formed ID absent from a valid store → `None`;
- one valid representation → canonical reconstructed candidate;
- conflicting same-ID representation → error;
- corrupt representation → error.

No Unit 10 internal row identifier is part of the public result.

## 13. Evaluation lookup

```python
get_persisted_evaluation(
    projection_db_path,
    evaluation_id,
)
```

Semantics:

- malformed `evaluation_id` → error;
- valid well-formed ID absent → `None`;
- valid persisted record → canonical reconstructed evaluation;
- malformed candidate echo or identity mismatch → error;
- unsupported protocol/version → error.

Candidate and evaluation identities remain separate namespaces.

## 14. Candidate evaluation collection

```python
list_candidate_evaluations(
    projection_db_path,
    candidate_id,
)
```

This operation returns every valid persisted evaluation targeting the candidate.

It MUST NOT silently filter by:

- disposition;
- evaluator;
- protocol;
- supersession status;
- insertion order;
- timestamp.

Accepted, rejected, and undetermined records may coexist and must all remain visible.

## 15. Evaluation history

```python
get_evaluation_history(
    projection_db_path,
    evaluation_id,
)
```

The result exposes explicit supersession relationships.

```text
E1 accepted
 │
 ▼
E2 rejected
 │
 ▼
E3 undetermined
```

An edge means only:

> the same evaluator explicitly reconsidered the predecessor.

It does not mean that the successor is more true, more authoritative, canonical, or the universal current answer.

The exact return shape of `get_evaluation_history` is not frozen here (open question 9). Any shape MUST
expose the explicit persisted edges exactly, preserve forks without selecting a path, include no
current/final/best marker, and be reconstructed under the same validation as section 16.

## 16. Supersession integrity

For every non-null `supersedes` edge, Unit 11 MUST establish that:

1. the predecessor exists;
2. the predecessor is valid;
3. predecessor and successor target the same `candidate_id`;
4. predecessor and successor identify the same evaluator under Unit 8 rules;
5. the supersession graph is acyclic and no evaluation supersedes itself;
6. the explicit persisted edge is preserved exactly.

Missing, mismatched or cyclic predecessors fail closed.

Forks are valid history and remain unresolved:

```text
       E2
      /
E1 ──
      \
       E3
```

## 17. Unsuperseded evaluations

```python
list_unsuperseded_evaluations(
    projection_db_path,
    candidate_id,
)
```

An evaluation is unsuperseded if no valid persisted successor names it as predecessor.

This is a graph property only.

The API and DTO MUST NOT call graph leaves:

```text
current
final
best
correct
canonical
preferred
winning
consensus
```

## 18. Candidate-centered history view

The only proposed new aggregate read DTO is:

```python
@dataclass(frozen=True)
class StructuralInterpretationHistory:
    candidate: StructuralCandidate | ClauseStructureCandidate
    evaluations: tuple[EvaluatedStructuralInterpretation, ...]
    supersession_edges: tuple[SupersessionEdge, ...]
    unsuperseded_evaluation_ids: tuple[str, ...]
```

With:

```python
@dataclass(frozen=True)
class SupersessionEdge:
    predecessor_evaluation_id: str
    successor_evaluation_id: str
```

These are read models only. They have no independent persisted logical identity.
The `candidate` field holds either existing candidate DTO unchanged; the Matthew 1:2 S-V-O
candidate is a `ClauseStructureCandidate`.

## 19. Aggregate lookup operations

```python
get_structural_interpretation_history(
    projection_db_path,
    candidate_id,
)

get_structural_interpretation_histories_for_selector(
    projection_db_path,
    selector: ScriptureSelector,
)
```

Return conventions:

```text
malformed candidate ID
    → error

unknown candidate ID
    → None

known candidate, zero evaluations
    → history with empty evaluation and edge tuples

known candidate with evaluations
    → complete validated history

selector with no matching candidates
    → empty tuple

invalid store or corrupt matching record
    → explicit error
```

## 20. Ordering semantics

Collections MUST use a deterministic presentation order for API stability, but that order carries no epistemic precedence.

Precedence MUST NOT be derived from:

```text
SQLite rowid
surrogate PK
insertion order
filesystem order
wall clock
timestamp
lexical evaluation_id order
```

Supersession relationships are represented separately and are never inferred from collection order.

The exact deterministic presentation order remains an implementation-authorization decision.

## 21. Surrogate-PK firewall

No public Unit 11 API or DTO may expose, require, or interpret a persisted SQLite surrogate PK as external identity.

Forbidden public identities include:

```text
candidate_row_id
evaluation_row_id
history_row_id
projection_pk
SQLite rowid
```

Public lookup keys remain `candidate_id`, `evaluation_id`, and scripture selectors.

Unit 10 tables use logical-ID primary keys; the implicit SQLite `rowid` is a physical storage
detail. It is never an identity, ordering authority or public field.

Equivalent Unit 10 stores with the same logical records but different physical PK allocation, insertion order, or database path MUST yield logically equivalent Unit 11 results.

## 22. Verification boundary

### 22.1 Projection-only verification

Every reconstructed candidate MUST pass the frozen candidate self-consistency validation.

Every reconstructed evaluation MUST pass the frozen evaluation V1/history validation.

```text
row exists
```

does not imply:

```text
logical object is valid
```

### 22.2 Optional source-grounded verification

A separately named operation may accept both source and projection store paths and apply existing source-grounded V2 verification.

```text
persisted candidate
        ↓
V1 self-consistency
        ↓
public structural re-derivation
        ↓
field-for-field equality
```

Source-grounded verification does not migrate or reinterpret a record against another snapshot.

Whether V2 convenience APIs belong to the initial implementation remains open until implementation authorization.

## 23. Snapshot firewall

Candidates and evaluations remain bound to the source snapshot encoded in their logical identity.

Unit 11 MUST NOT automatically:

```text
upgrade
rebind
migrate
carry forward
equate
```

records across snapshots or derivation versions.

Cross-snapshot equivalence and migration remain separately authorized future work.

## 24. Matthew 1:1 Verbless firewall

Matthew 1:1 remains a mandatory negative fixture.

The source has a `P2CL` clause with `ClType=Verbless`, eight noun leaves, and no verb leaf.

A Unit 11 query MUST NOT fabricate:

```text
verb
copula
"is"
Actor
Action
Patient
Event
Result
Identity
Property
```

Retrieving an accepted structural evaluation does not transform it into a semantic assertion.

## 25. Semantic and scoring firewalls

The following mappings remain prohibited:

```text
S  → Actor
V  → Action/Event
O  → Patient/Result
P  → Identity/Property
A0 → Actor
A1 → Patient
A2 → Recipient/Result
```

Unit 11 also MUST NOT derive confidence, probability, percentage, score, rank, weight, consensus, or majority from evaluation counts, dispositions, graph position, evaluator count, or supersession depth.

## 26. Error semantics

Unit 11 distinguishes:

### NOT-FOUND

A syntactically valid requested logical ID does not exist in an otherwise valid store.

### EMPTY-DISCOVERY

A valid selector matches no persisted candidates.

### EMPTY-HISTORY

A candidate exists but has no evaluations.

### VALID-RESULT

A candidate, evaluation, discovery collection, or complete history is returned after validation.

### ERROR

The supplied store or requested record cannot be trusted.

Examples:

```text
invalid store version
catalog drift
malformed JSON
unsupported protocol
identity mismatch
same-ID conflict
dangling supersession
cross-candidate supersession
cross-evaluator supersession
cyclic or self-referential supersession
corrupt candidate echo
snapshot mismatch
```

ERROR MUST NOT be converted into `None`, an empty tuple, or an empty history.

## 27. Connection lifetime and side effects

Every Unit 11 API call SHALL:

- own or clearly borrow a read-only connection;
- close any owned connection on success;
- close it on not-found;
- close it on validation failure;
- close it on malformed history;
- leave source and projection database bytes unchanged.

No persistent query cache or automatic write-back is authorized.

## 28. Proposed public API freeze

The initial implementation, if separately authorized, SHOULD be limited to:

```python
list_persisted_candidates_for_selector(...)
list_persisted_candidates_for_chapter(...)
list_persisted_candidates_for_verse(...)
list_persisted_candidates_for_token(...)

get_persisted_candidate(...)
get_persisted_evaluation(...)
list_candidate_evaluations(...)
get_evaluation_history(...)
list_unsuperseded_evaluations(...)
get_structural_interpretation_history(...)
get_structural_interpretation_histories_for_selector(...)
```

Convenience chapter/verse/token functions may delegate to the selector primitive.

## 29. Explicit non-goals

Unit 11 does not:

- create or derive candidates;
- add a candidate family;
- create or modify evaluations;
- supersede a record;
- repair history;
- write or migrate the Unit 10 store;
- modify the source store;
- infer current truth;
- compute consensus, ranking, or confidence;
- perform semantic projection;
- create Actor/Action/Patient/Event/Result/Identity/Property;
- create an implicit copula;
- perform theology, translation, or localization;
- implement UI;
- integrate with `bible-research-merged`;
- perform cross-snapshot migration;
- add another book, N1904, or the full NT;
- remediate earlier findings;
- authorize a later Unit.

## 30. Acceptance criteria

### Identity and reconstruction

- **AC-U11-01** Candidate lookup uses only logical `candidate_id`; no SQLite surrogate identity is exposed.
- **AC-U11-02** Evaluation lookup uses only logical `evaluation_id`; no SQLite surrogate identity is exposed.
- **AC-U11-03** Every returned candidate passes frozen self-consistency validation and recomputes to its persisted `candidate_id`.
- **AC-U11-04** Every returned evaluation passes frozen V1/history validation and recomputes to its persisted `evaluation_id`.
- **AC-U11-05** Equal logical stores with changed PK allocation, insertion order, and DB path produce logically equal Unit 11 results.

### Discovery

- **AC-U11-06** Callers can discover persisted candidates from a scripture selector without knowing a `candidate_id` in advance.
- **AC-U11-07** Token discovery returns a candidate if and only if the exact validated persisted scope contains the queried token ref.
- **AC-U11-08** Verse discovery returns candidates whose exact scopes intersect the selected verse and does not expand those scopes.
- **AC-U11-09** Chapter and book discovery return candidates whose exact scopes intersect the selected chapter or book and do not require whole-scope containment.
- **AC-U11-10** Discovery includes candidates with zero evaluations.
- **AC-U11-11** Discovery identifies candidates only; it does not select accepted, current, canonical, preferred, winning, or semantic results.
- **AC-U11-12** No discovery operation fills scope discontinuities by min/max, `Start`/`End`, verse/chapter envelope, lexical range, string prefix/`LIKE`/`GLOB`, PK range, row order, or insertion order; matching uses parsed integer coordinates of the exact member refs.

### Matthew 1:2 discontinuity

- **AC-U11-13** Verse selector `MAT 1:2` discovers the frozen S-V-O candidate.
- **AC-U11-14** Token selectors `MAT 1:2!5`, `!7`, `!8`, and `!9` discover that candidate.
- **AC-U11-15** Token selector `MAT 1:2!6` does not discover that candidate.
- **AC-U11-16** Every returned DTO preserves exact scope `[5,7,8,9]`; token 6 never enters through discovery or reconstruction.

### History

- **AC-U11-17** Candidate evaluation listing returns every valid accepted, rejected, and undetermined record.
- **AC-U11-18** Opposing evaluations coexist and are never merged, voted, averaged, or resolved.
- **AC-U11-19** Superseded records remain present, valid, and queryable.
- **AC-U11-20** Supersession edges are reconstructed without PK, insertion order, or timestamp lineage.
- **AC-U11-21** Forked supersession is represented unchanged and remains unresolved.
- **AC-U11-22** Unsuperseded evaluations are graph leaves only and are never labelled current, correct, final, canonical, preferred, winning, or consensus.

### Read-only and fail-closed behavior

- **AC-U11-23** Projection-store access is SQLite-enforced read-only; Unit 11 performs no write, DDL, ATTACH, or DETACH action.
- **AC-U11-24** Optional source-grounded verification keeps the source database read-only and unchanged.
- **AC-U11-25** Invalid store version, catalog, protocol, or representation fails explicitly and is never reported as not-found or empty.
- **AC-U11-26** Candidate/evaluation corruption, identity mismatch, or unsupported logical protocol fails closed, including an unvalidatable candidate row that discovery would otherwise silently skip as a non-match.
- **AC-U11-27** Missing, malformed, cross-candidate, cross-evaluator, self-referential or cyclic supersession fails closed rather than silently truncating history.
- **AC-U11-28** Owned connections close on success, not-found, empty results, and every failure path.

### Epistemic firewalls

- **AC-U11-29** Unit 11 contains no confidence, probability, score, rank, majority, consensus, or winner calculation.
- **AC-U11-30** Unit 11 defines no universal current evaluation and derives no precedence from timestamp, rowid, PK, or storage order.
- **AC-U11-31** No semantic entity or unconditional S/V/O/P or Frame-role projection is produced.
- **AC-U11-32** Matthew 1:1 remains Verbless with no fabricated verb, copula, Action, Event, or semantic entity.

### Lifecycle and regression

- **AC-U11-33** Unit 11 exposes no candidate/evaluation creation or persistence-write API.
- **AC-U11-34** Unit 10 schema, append-only representation, and write behavior remain unchanged.
- **AC-U11-35** Existing Units 1-10 behavior and accepted identity semantics remain unchanged.
- **AC-U11-36** Unit 11 does not implement semantic projection, BRW integration, localization, UI, cross-snapshot migration, or a later Unit.
- **AC-U11-37** Contract freeze, implementation authorization, implementation checkpoint, and independent acceptance remain separate governance actions.

## 31. Suggested future test classes

Design guidance only:

```text
A. Store validation
B. Selector validation
C. Chapter discovery
D. Verse discovery
E. Exact-token discovery
F. Matthew 1:2 discontinuity and token-6 exclusion
G. Candidate retrieval
H. Evaluation retrieval
I. Candidate evaluation collection
J. Linear supersession
K. Forked supersession
L. Unsuperseded graph leaves
M. Aggregate history
N. PK / insertion-order / path invariance
O. Corruption and tamper rejection
P. Read-only enforcement and connection closure
Q. Matthew 1:1 Verbless firewall
R. Semantic and scoring negative tests
```

## 32. Open design questions before implementation authorization

1. **Module path:** suggested `scripts/projection_query.py`.
2. **Error type:** reuse Unit 10 store errors or define a Unit 11 query-specific error while preserving explicit not-found semantics.
3. **Selector representation:** frozen DTO versus strict scripture-ref string parser.
4. **Discovery index:** query persisted candidate JSON directly or add a Unit 10-compatible read index without changing logical representation. Any schema change requires separate authorization. Whatever strategy is chosen MUST satisfy sections 6, 8 and 9 (full-row validation, parsed integer coordinates, no prefix matching).
5. **Presentation order:** freeze a deterministic order that carries no precedence meaning.
6. **Validation lifetime:** validate on each call or once per owned read session with equivalent trust guarantees.
7. **Source-grounded V2 API:** include in initial implementation or defer to an amendment.
8. **Result pagination:** not required for the Matthew vertical slice unless separately justified and frozen.
9. **Evaluation-centered history shape:** the return shape of `get_evaluation_history` (for example, the candidate-centered aggregate, or an evaluation-anchored subgraph) constrained by section 15.

## 33. Implementation authorization

**Unit 11 implementation is NOT AUTHORIZED by this frozen contract.**

A future authorization should freeze:

1. repository starting checkpoint;
2. exact contract checkpoint;
3. production module path;
4. selector DTO/parser;
5. exact public API signatures;
6. DTO shapes;
7. deterministic presentation order;
8. error classes and return conventions;
9. projection-store validation rules;
10. discovery query/index strategy;
11. whether source-grounded V2 is included;
12. authorized changed paths;
13. tests and regression requirements;
14. Matthew 1:1 and 1:2 fixtures;
15. source/projection read-only enforcement;
16. Git checkpoint and stop boundary.

Implementation authorization does not imply independent acceptance.

## 34. Architectural stop line

```text
AUTHORITATIVE SOURCE
        ↓
LinguisticSourceFact
        ↓
SourceEvidence
        ↓
─────────────────────────────────────
DERIVED STRUCTURAL BOUNDARY
─────────────────────────────────────
        ↓
StructuralCandidate
        ↓
─────────────────────────────────────
EVALUATION BOUNDARY
─────────────────────────────────────
        ↓
EvaluatedStructuralInterpretation
        ↓
─────────────────────────────────────
UNIT 10 PERSISTENCE
─────────────────────────────────────
        ↓
append-only structural/evaluation history
        ↓
─────────────────────────────────────
UNIT 11 DISCOVERY & READ-ONLY HISTORY QUERY
─────────────────────────────────────
        ↓
scripture selector
candidate discovery
validated reconstruction
complete evaluation history
explicit supersession graph
unsuperseded graph leaves
        ↓
        X  STOP
```

Nothing beyond the stop line is defined, authorized, or implied:

```text
NO semantic projection
NO Actor / Action / Patient
NO Event / Result
NO Identity / Property
NO consensus
NO confidence
NO ranking
NO canonical/current truth
NO localization
NO UI
NO BRW integration
NO cross-snapshot migration
NO next Unit
```

**Unit 10 answers:** Can structural interpretation history be persisted without contaminating the authoritative source boundary?

**Unit 11 answers:** Can a UI or other consumer begin with a scripture location, discover the relevant persisted candidates, and query their complete history without changing exact membership, stored contents, or epistemic meaning?

**STOP.**

## 35. Contract-freeze reconciliation record

This section records the freeze-time review. It is not implementation evidence and not independent acceptance.

- Preconditions verified from the repository: Unit 10 is IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT) in `docs/governance/PHASE-STATUS.md`; the Unit 10 store keeps logical-ID primary keys, append-only triggers, a full candidate echo in every evaluation record, and no discovery index; Unit 8 permits forks, opposing evaluations and same-evaluator supersession only, with no "current evaluation".
- Matthew 1:2 negative fixture re-confirmed read-only against `fixtures/matthew-1-2-svo-candidate.expected.json` (candidate `sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`, anchor `400010020050040`, exact scope `MAT 1:2!5, !7, !8, !9`, `MAT 1:2!6` excluded) and against the current source-grounded derivation: tokens 5, 7, 8 and 9 derive the candidate; token 6 derives none.
- Bounded precision corrections applied at freeze, with no scope broadening: history DTO candidate type widened to both existing candidate DTOs; book-level discovery defined; integer-coordinate matching with a prefix/`LIKE`/`GLOB` prohibition; fail-closed handling of unvalidatable candidate rows during discovery; cyclic and self-referential supersession added to integrity and error lists; malformed-ID handling for aggregate lookup; selector validation and string-form reconciliation; rowid clarification; evaluation-history return shape recorded as open question 9.
- Unit 11 implementation, tests, a production module and independent acceptance remain NOT AUTHORIZED. Unit 12 is not defined or authorized. The Phase remains AUTHORIZED, not COMPLETE or CLOSED.

## 36. Authorized implementation evidence

This section is appended evidence only. No design section or acceptance criterion above was altered; where the earlier "CONTRACT FROZEN / NOT IMPLEMENTED" status and §35 describe the freeze checkpoint, this section supersedes their implementation state only. It is implementation validation, **not independent acceptance**.

- **Authorization and starting point:** a separate user task authorized the production implementation from clean `master` at the contract-freeze checkpoint `38e0d89f01a8dc4fd9ad83a967a2e2f56da06351`. No implementation commit identity is recorded here.
- **Paths:** [projection_query.py](../../scripts/projection_query.py) and [test_unit11.py](../../tests/test_unit11.py), with test instructions in [tests/README.md](../../tests/README.md) and the governance/index documents. No schema, Unit 10 production module, candidate/evaluation module, source module, fixture, historical audit or protected repository was changed.
- **Public API:** exactly the eleven functions of section 28, each taking `projection_db_path` first, plus `ProjectionQueryError`, `ScriptureSelector`, `SupersessionEdge` and `StructuralInterpretationHistory`. There is no write API and no current/latest/best/canonical/consensus alias.
- **Selector:** `ScriptureSelector(book, chapter=None, verse=None, token=None)` accepts only book `MAT` and positive non-bool integers up to 2**63-1, requires chapter before verse and verse before token, and is validated at construction and again on use before any database access. String forms `MAT 1:2` and `MAT 1:2!5` use strict ASCII full-match with no leading zeros or whitespace tolerance.
- **Matching:** every persisted candidate is reconstructed and validated by the existing Unit 10 read path (V1, candidate echo and history validation); any unvalidatable row raises instead of being skipped. Book, chapter and verse selectors match by intersection and a token selector matches iff the exact parsed integer coordinate is a member of the validated scope. No min/max, `Start`/`End`, envelope, lexical range, prefix, `LIKE`/`GLOB`, rowid, PK or insertion-order matching exists, and no source database, V2 re-derivation or schema/index/trigger is used.
- **Resolution of open question 9:** `get_evaluation_history` returns a tuple of evaluations forming the weakly connected same-candidate, same-evaluator supersession component (predecessors, successors and fork branches) in presentation order only, a one-item tuple for an isolated evaluation, and `None` when the identity is absent. `list_candidate_evaluations` and `list_unsuperseded_evaluations` return `None` for an absent candidate and `()` for a known candidate with none.
- **Return and error conventions:** malformed identifiers and selectors raise before database access; a valid absent identifier returns `None`; a selector with no match returns `()`; a known candidate without evaluations yields a history with empty tuples; corruption, store drift, missing/cross-candidate/cross-evaluator/self-referential/cyclic supersession always raise `ProjectionQueryError` (Unit 10 and SQLite errors are chained) and are never converted to `None` or `()`.
- **Ordering (presentation only, no precedence):** candidates by first member coordinate as integers, then kind, derivation kind, derivation version and candidate id; evaluations by candidate id, evaluator class, evaluator label, protocol id, protocol version and evaluation id; edges by predecessor then successor; unsuperseded ids lexically. Unsuperseded means graph leaf only.
- **Read-only enforcement:** the Unit 10 read-only profile (`mode=ro`, `query_only=ON`, `foreign_keys=ON`, `recursive_triggers=ON`, catalog/metadata/DDL-hash check) is reused; tests trace the SQLite authorizer for write/DDL/ATTACH actions, attempt a write through the opened connection and verify connection closure on success, not-found, empty and failure paths.
- **Matthew evidence:** a real read-only integration run against the existing source database stored the frozen S-V-O candidate `sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087` in a temporary projection store; selector `MAT 1:2` and tokens `!5`, `!7`, `!8`, `!9` discovered it with scope `!5,!7,!8,!9`, token `!6` discovered nothing, and Matthew 1:1 discovered only the three Apposition candidates with a Verbless ancestor and no fabricated verb, copula or Event.
- **Acceptance-criteria coverage** (tests in [test_unit11.py](../../tests/test_unit11.py)): AC-U11-01/02 `test_01`, `test_12`; 03/04 `test_20`, `test_32`, `test_44`; 05 `test_46`; 06-07 `test_05`, `test_07`, `test_30`, `test_31`; 08-09 `test_06`, `test_10`, `test_30`, `test_31`; 10 `test_08`; 11 `test_01`, `test_26`, `test_48`; 12 `test_01`, `test_30`, `test_31`; 13-16 `test_05`, `test_06`, `test_50`; 17-19 `test_20`, `test_21`; 20-22 `test_22`, `test_23`, `test_27`, `test_46`; 23 `test_40`, `test_41`; 24 `test_45`, `test_50`; 25 `test_43`; 26 `test_32`, `test_44`; 27 `test_27`; 28 `test_42`; 29-31 `test_01`, `test_48`; 32 `test_09`, `test_50`; 33 `test_01`; 34-35 `test_47` plus the Units 1-10 regression; 36-37 are structural governance boundaries (no scoring, semantic, persistence or acceptance code or status exists).
- **Results:** 32 fast tests plus 1 opt-in integration test pass; Units 10 and 11 together 81 tests OK with 4 explicit skips; Units 1, 2 and 4-11 together 376 tests OK with 25 explicit opt-in integration skips; `scripts.verify_unit1` and `scripts.source_schema` exit 0. Unit 3 discovery was not run, no full Matthew build ran and the second-build gate stayed disabled.
- **Unchanged:** the authoritative source database and the protected repositories were verified unchanged before the checkpoint; no projection database exists in the repository.
- **Status:** Unit 11 is IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE. No independent acceptance audit exists. Unit 12 is NOT AUTHORIZED. The Phase remains AUTHORIZED, not COMPLETE or CLOSED. Unit 5 M1 and Unit 7 audit M1 remain unresolved.
