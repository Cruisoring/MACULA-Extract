# Unit 8 Amendment 1 Implementation Plan

## S-V-O Clause-Structure Evaluation Registry Extension

- **Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE (originally IMPLEMENTATION PLAN / NOT IMPLEMENTED; see section 24)
- **Target repository:** `C:\Projects\MACULA-Extract`
- **Expected starting checkpoint:** `ddd23c4bc51c651aea82722d747c44671f15832a`
- **Proposed checkpoint subject:** `extend Unit 8 evaluation to S-V-O candidates`

## 1. Purpose

Amend Unit 8 so the existing `human-structural-adequacy/1` evaluation protocol can evaluate the Unit 9 candidate tuple:

```text
clause-structure / source-rule-s-v-o / 1
```

The existing Apposition tuple remains supported:

```text
apposition / source-np-appos / 1
```

This amendment changes the closed candidate compatibility registry only. It does not change the meaning of `human-structural-adequacy/1`, the disposition vocabulary, evaluation identity, V1/V2 trust boundary, rationale model, source read-only boundary, persistence decision or semantic firewall.

## 2. Starting-state gate

Before editing:

```powershell
Set-Location C:\Projects\MACULA-Extract
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git --no-pager log -10 --oneline --decorate
git status --short
git status --porcelain=v1 --untracked-files=all
git diff --check
```

Require:

```text
root      = C:\Projects\MACULA-Extract
branch    = master
HEAD      = ddd23c4bc51c651aea82722d747c44671f15832a
worktree  = clean
index     = clean
untracked = none
```

If HEAD or repository state differs, stop. Do not reset, checkout, rebase, clean or amend history.

## 3. Read the actual implementation

Read from the actual starting HEAD:

```text
AGENTS.md
docs/governance/PHASE-STATUS.md
README.md
docs/architecture/README.md

scripts/evaluated_interpretations.py
scripts/structural_candidates.py

tests/test_unit8.py
tests/test_unit9.py
tests/README.md

fixtures/matthew-1-2-svo-candidate.expected.json

docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md
docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md
```

The actual repository is authoritative for current API names and lifecycle state. Historical synchronized copies must not downgrade Unit 8 or Unit 9.

## 4. Freeze the Amendment delta

Add:

```text
docs/architecture/UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md
```

Freeze this registry delta:

```text
human-structural-adequacy / 1

supports:
  apposition       / source-np-appos    / 1
  clause-structure / source-rule-s-v-o / 1
```

Do not change the protocol version. The criterion remains structural adequacy only.

Stop and design version 2 instead if S-V-O evaluation requires changing any of:

```text
criterion meaning
disposition meaning
evaluator class rules
rationale rules
identity serialization
V1/V2 verification semantics
```

## 5. Public API expected by the Amendment tests

The implementation should preserve the existing Unit 8 public API. The provided test module expects the following public names; if the actual implementation already exposes equivalent names, update the test adapters only, not production semantics:

```python
RationaleCitation(kind: str, id: str)
RationaleNote(text: str, language: str)

HumanEvaluationInput(
    candidate,
    evaluator_label,
    evaluation_protocol_id,
    evaluation_protocol_version,
    disposition,
    rationale_evidence,
    rationale_note,
    event_key,
    supersedes,
)

EvaluatedStructuralInterpretation

verify_candidate_v1(candidate)
verify_candidate_v2(db_path, candidate, lookup_token_ref)

create_evaluated_structural_interpretation(db_path, human_input)
```

V2 must call the public Unit 7/9 entry point:

```python
derive_structural_candidates(db_path, token_ref)
```

Do not add a Unit 8-only S-V-O derivation shortcut.

## 6. Production change

Primary path:

```text
scripts/evaluated_interpretations.py
```

Implement or extend a closed registry keyed by the complete tuple:

```text
(
  evaluation_protocol_id,
  evaluation_protocol_version,
  evaluator_class,
  candidate_kind,
  derivation_kind,
  derivation_version,
)
```

Supported entries after Amendment 1:

```text
human-structural-adequacy / 1 / human /
apposition / source-np-appos / 1

human-structural-adequacy / 1 / human /
clause-structure / source-rule-s-v-o / 1
```

Do not use candidate kind alone as the registry key.

Unknown kind, derivation or version must fail closed.

## 7. V1 requirements

V1 remains offline and database-independent.

For both candidate families it must:

1. validate closed candidate/protocol vocabularies;
2. validate non-empty snapshot, scope and evidence;
3. recompute `candidate_id` through candidate-owned canonical identity semantics;
4. require exact equality with the echoed `candidate_id`;
5. preserve candidate status `candidate`;
6. reject forged scope, evidence order, payload, Head, component order or component membership;
7. reject semantic/confidence fields.

Do not hard-code the frozen Unit 9 candidate hash as an exception.

## 8. V2 requirements

V2 remains source-grounded and read-only.

For any token ref in the candidate's exact scope:

```text
MAT 1:2!5
MAT 1:2!7
MAT 1:2!8
MAT 1:2!9
```

V2 must:

1. call public `derive_structural_candidates()`;
2. find the candidate by complete field equality;
3. require field-for-field equality, not candidate-ID-only equality;
4. reject token `MAT 1:2!6` as a scope lookup hint/member;
5. fail explicitly on snapshot/source/store errors.

The lookup hint is not stored and does not enter evaluation identity.

## 9. Rationale citations

Keep the existing citation vocabulary:

```text
syntax_node
token
```

Do not add candidate-specific citation kinds such as `subject-component`.

For the S-V-O candidate, valid syntax-node citations are the candidate evidence nodes:

```text
400010020050040  anchor
400010020050012  S child
400010020070012  V child
400010020080021  O child
```

Valid token citations are exactly:

```text
MAT 1:2!5
MAT 1:2!7
MAT 1:2!8
MAT 1:2!9
```

`MAT 1:2!6` and unrelated source nodes must be rejected.

Canonical citation order remains candidate evidence order followed by candidate scope order. Duplicate citations are rejected.

## 10. Evaluation semantics unchanged

Keep:

```text
record_protocol = macula.evaluated-structural-interpretation.v1
protocol        = human-structural-adequacy / 1
evaluator_class = human

dispositions:
  accepted
  rejected
  undetermined
```

Meanings remain unchanged:

- `accepted`: evaluator judged the structural proposal adequate under the protocol;
- `rejected`: evaluator judged it inadequate, not that the source is wrong;
- `undetermined`: evaluator recorded neither judgment;
- no record: not evaluated.

The candidate echo remains unchanged and non-authoritative. Evaluation never changes candidate status or candidate identity.

## 11. Semantic firewall

Do not introduce executable mappings or fields for:

```text
S -> Actor
V -> Action
V -> Event
O -> Patient
O -> Result
```

Do not add:

```text
actor
action
patient
event
result
identity
property
confidence
probability
certainty
score
percentage
weight
rank
```

The candidate payload may retain source structural codes `S`, `V`, `O`. Their presence does not create semantic roles.

## 12. Persistence and source-store firewall

No persistence is authorized.

Do not add:

```text
DDL
migration
source tables
evaluation tables
candidate tables
projection SQLite
sidecar database
JSON persistence
cache persistence
```

The source database remains read-only. Preserve bytes, SHA-256, `PRAGMA user_version`, catalog and indexes before/after tests.

## 13. Tests

Add:

```text
tests/test_unit8_amendment1.py
```

Add test support if the current repository does not expose a reusable disposable store builder:

```text
tests/support/__init__.py
tests/support/unit8_amendment1_store.py
```

The support builder is test-only. It must create both:

- a Unit 7 Apposition fixture matching the accepted candidate ID;
- the frozen Unit 9 Matthew 1:2 S-V-O fixture.

The supplied `test_unit8_amendment1.py` defines 40 fast logical tests and 3 opt-in real-Matthew integration tests covering:

```text
registry           A1-01..05
V1                 A1-06..12
evaluation         A1-13..19
rationale          A1-20..26
V2                 A1-27..30
regression         A1-31..33
firewalls          A1-34..37
read-only/identity A1-38..40
integration        INT-A1-01..03
```

If actual API names differ, update only the centralized test adapters:

```python
_citation
_note
_human_input
_create
_v1
_v2
```

Do not weaken assertions or add production-only test bypasses.

## 14. Existing test reconciliation

Review existing Unit 8 tests that assert S-V-O is unsupported.

Because Amendment 1 formally changes the Unit 8 registry, obsolete Unit 8 assertions should be updated or replaced, not left as permanent skips.

Preserve all still-valid assertions, especially:

```text
exact scope [5,7,8,9]
token 6 exclusion
forged envelope rejection
Apposition evaluation identity
Matthew 1:1 Verbless safety
semantic/confidence firewalls
read-only source behavior
```

Do not modify Unit 7 or Unit 9 tests merely to make the Amendment pass.

## 15. Authorized changed paths

Recommended authorized paths:

```text
scripts/evaluated_interpretations.py

tests/test_unit8.py
tests/test_unit8_amendment1.py
tests/support/__init__.py
tests/support/unit8_amendment1_store.py

docs/architecture/UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md
docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md

README.md
docs/architecture/README.md
docs/governance/PHASE-STATUS.md
AGENTS.md
tests/README.md
```

Treat these as read-only unless an actual defect unrelated to the Amendment creates a stop condition:

```text
scripts/structural_candidates.py
tests/test_unit9.py
fixtures/matthew-1-2-svo-candidate.expected.json
docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md
```

Prohibited:

```text
schema/*
scripts/source_importer.py
scripts/source_fidelity.py
scripts/source_query.py
historical audits/*
source fixtures/*
```

## 16. Validation order

Run from the repository root:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema

python -B -m unittest tests.test_unit8 -v
python -B -m unittest tests.test_unit8_amendment1.Unit8Amendment1FastTests -v
python -B -m unittest tests.test_unit9 -v
```

Opt-in integration:

```powershell
$env:MACULA_UNIT8_AMENDMENT1_INTEGRATION = '1'
$env:MACULA_MATTHEW_DB = 'C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3'
python -B -m unittest tests.test_unit8_amendment1 -v
```

Then execute the established guarded combined regression:

```text
reuse existing Matthew database read-only
fresh source-fidelity validation
no full Matthew population
Unit 3 second-build gate disabled
all skips explicitly reported
```

Do not prestate a final test count. Require zero unexpected failures and zero unexpected errors.

## 17. Preservation gates

Before and after implementation/testing record actual:

```text
C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3

size
SHA-256
PRAGMA user_version
complete sqlite_schema catalog
index inventory
```

Verify protected repositories before and after:

```text
C:\Works\macula-greek
C:\Projects\bible-research-merged
```

Verify the frozen Unit 9 fixture remains byte-for-byte unchanged:

```text
fixtures/matthew-1-2-svo-candidate.expected.json
```

Historical expected values may be used as warning references, but actual beginning values are authoritative for preservation comparison.

## 18. Acceptance gates

### G1 Registry

`human-structural-adequacy/1` supports both complete candidate tuples.

### G2 Criterion unchanged

No change to structural-adequacy meaning or protocol version.

### G3 V1 genericity

Apposition and ClauseStructure use the same untrusted-candidate V1 boundary.

### G4 V2 genericity

Both families use public `derive_structural_candidates()` and field-for-field equality.

### G5 Apposition stability

Existing Apposition candidate and evaluation identities remain unchanged.

### G6 Unit 9 exactness

The production clause candidate matches the frozen Unit 9 fixture and candidate ID.

### G7 Exact membership

Scope remains `[5,7,8,9]`; token 6 never enters candidate, citation or evaluation scope.

### G8 Firewalls

No semantic entities, semantic shortcuts, confidence or score fields.

### G9 Preservation

Source DB, source XML, fixture and protected repositories remain unchanged.

### G10 No persistence

Evaluation remains an immutable in-memory DTO/API only.

## 19. Contract and governance reconciliation

After technical validation:

1. append Amendment 1 implementation evidence to the amendment document;
2. add a narrow amendment reference to the base Unit 8 contract without rewriting frozen sections;
3. update governance/index documents to record:

```text
Unit 8:
IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

Unit 8 Amendment 1:
IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

Unit 9:
IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE

Phase:
AUTHORIZED
```

Preserve Unit 5 M1 and Unit 7 audit M1 as unresolved and distinct.

Do not claim independent acceptance.

## 20. Pre-commit gate

Review:

```powershell
git status --short
git --no-pager diff
git diff --check
```

Verify:

```text
only authorized paths changed
Unit 9 fixture unchanged
no schema changes
no Unit 9 production changes
no persistence
no semantic fields
no confidence fields
Apposition identities unchanged
S-V-O evaluation passes V1 and V2
source DB unchanged
protected repositories unchanged
```

Stage only authorized paths, then run:

```powershell
git --no-pager diff --cached --name-status
git diff --cached --check
```

## 21. Checkpoint

Create one checkpoint:

```text
extend Unit 8 evaluation to S-V-O candidates
```

Do not amend prior commits.

After commit verify:

```text
one new commit
sole parent = actual starting HEAD
master branch
clean worktree/index/untracked state
only authorized paths changed
frozen Unit 9 fixture unchanged
source database unchanged
```

## 22. Final report

Return:

```text
# Unit 8 Amendment 1 Implementation Result

## Starting state
## Registry delta
## Production changes
## V1 result
## V2 result
## Matthew 1:2 evaluation result
## Apposition regression
## Rationale/citation behavior
## Semantic firewall
## Tests actually run
## Skips
## Database preservation
## Protected repositories
## Changed paths
## Checkpoint
## Governance
## Stop line
```

Explicitly report:

```text
UNIT 8 AMENDMENT 1 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.
UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.
```

## 23. Stop line

After the Amendment checkpoint, stop.

Do not:

```text
perform independent acceptance
add persistence
create a projection store
add deterministic-policy protocols
add AI/model evaluator classes
create semantic roles
map S/V/O to Actor/Action/Patient/Event/Result
integrate BRW
add localization/UI
add another candidate family
begin another unit
```

## 24. Implementation evidence (appended at implementation)

Implemented from `master` at `ddd23c4bc51c651aea82722d747c44671f15832a`. The frozen
delta and all behavior are recorded in
[UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md](UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md).
Deviations from this plan, all reconciled without changing production semantics:

- Section 5 listed `HumanEvaluationInput`, `verify_candidate_v1/v2` and
  `RationaleCitation(kind, id)`; the actual frozen API differs, so the test module's
  adapters were updated, not production.
- The supplied citation-order test expected normalization; frozen Unit 8 rejects
  misordered citations, so the test asserts rejection plus accepted canonical order.
- A schema-valid store cannot carry the real Matthew snapshot; frozen ids are pinned in
  fast tests by an independent re-encoding under the frozen snapshot, and literally
  asserted against the real Matthew database in the integration tests.
- `tests/test_unit9.py::test_unit8_rejects_new_candidate_without_registry_amendment`
  asserts the pre-amendment behavior and fails by design; section 14 forbids editing
  Unit 9 tests, so it is filtered in memory and documented for a future authorized change.

**Status after implementation: IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.**
UNIT 8 AMENDMENT 1 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.
UNIT 9 INDEPENDENT ACCEPTANCE WAS NOT PERFORMED.
