# Unit 8 Amendment 1: S-V-O Evaluation Registry

- **Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE
- **Amends:** [Unit 8 Evaluated Structural Interpretation Contract](UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md) (sections 1-34 unchanged)
- **Starting checkpoint:** `ddd23c4bc51c651aea82722d747c44671f15832a` (`implement S-V-O clause structural candidate`)
- **Checkpoint subject:** `extend Unit 8 evaluation to S-V-O candidates`
- **Plan:** [UNIT-8-AMENDMENT-1-IMPLEMENTATION-PLAN.md](UNIT-8-AMENDMENT-1-IMPLEMENTATION-PLAN.md)

## 1. Purpose and boundary

`human-structural-adequacy/1` is extended from one to two candidate families by amending
the closed evaluation compatibility registry only. The criterion, disposition vocabulary,
evaluator-class rules, rationale model, identity serialization, V1/V2 trust boundary,
read-only source boundary, persistence decision and semantic firewall are unchanged.
Evaluation remains an immutable in-memory DTO/API.

## 2. Registry

Public `evaluated_interpretations.REGISTRY` is a closed `frozenset` of complete tuples
`(protocol id, protocol version, evaluator class, candidate kind, derivation kind,
derivation version)`:

```text
human-structural-adequacy / 1 / human / apposition       / source-np-appos    / 1
human-structural-adequacy / 1 / human / clause-structure / source-rule-s-v-o  / 1
```

Any other tuple is rejected. The protocol stays at version 1 because none of the
criterion, disposition, evaluator, rationale, identity or V1/V2 semantics change
(contract section 34 would otherwise require a version 2). Evaluation identity bytes are
untouched: an Apposition evaluation produces the same `evaluation_id` as before.

## 3. V1 (offline candidate verification)

`compute_evaluation_id` accepts a Unit 7 `StructuralCandidate` or a Unit 9
`ClauseStructureCandidate`; the exact Python type must match the registered kind. For a
clause candidate V1 independently requires:

- complete registry tuple, source snapshot fields and `status == "candidate"`;
- nonempty canonical single-book scope, with the scope node equal to the anchor;
- evidence exactly `anchor, subject-child, verbal-child, object-child` (syntax nodes);
- payload rule `S-V-O` and raw Head `"1"`;
- exactly three components in order `S`, `V`, `O` with roles
  `subject-component`, `verbal-component`, `object-component`, ordinals `0, 1, 2`, node
  IDs equal to the evidence children, canonical member refs, pairwise disjoint, and
  whose union equals the exact scope;
- `candidate_id` recomputed from the candidate echo (the Unit 9 wire format is
  re-implemented in Unit 8; no private Unit 9 helper is imported) and equal to the
  carried value.

Forged scope, evidence order, payload, Head, component order or membership, derivation
or candidate id are all rejected before any source access. Existing error messages
(`not a local PK`, `unsupported candidate kind`, `unsupported candidate derivation kind
or version`) are preserved; the type message now names both permitted candidate types.

## 4. V2 (source re-derivation)

V2 is unchanged and generic. `verify_evaluated_interpretation(record, db_path=...)`
calls the public `structural_candidates.derive_structural_candidates` with the first
scope token and requires field-for-field equality of the carried candidate with a
derived one. Consequences:

- the first scope token is the lookup hint; for `MAT 1:2` that is `MAT 1:2!5`, and every
  member token `5, 7, 8, 9` derives the same single candidate;
- token `MAT 1:2!6` derives no clause candidate and cannot be introduced by a forged
  envelope: a forged, reidentified candidate reports
  `candidate echo does not match source-grounded re-derivation`.

## 5. Rationale citations

Unchanged rules apply. Citations may reference only the candidate's own evidence
(`syntax_node`: anchor, then the three children) and exact scope (`token`). Canonical
order is evidence order followed by scope order; duplicates and incorrectly ordered
citations are **rejected** (the caller supplies canonical order; it is not normalized).
Token 6 and unrelated nodes are rejected. `accepted`/`rejected` need at least one
citation; `undetermined` may have none.

## 6. Matthew 1:2 and Apposition regression

The frozen Unit 9 fixture `fixtures/matthew-1-2-svo-candidate.expected.json` is
unchanged. The real-Matthew S-V-O candidate
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087` can be
evaluated from each of `MAT 1:2!5/7/8/9`. The three Matthew 1:1 Apposition identities
(`sha256:ca5dc518…05c3c`, `sha256:ba4de096…c4c1f`, `sha256:af5656c7…78220`), their
Verbless safety and their evaluations are unchanged.

## 7. Firewalls

No semantic role, Actor/Action/Patient/Event/Result mapping, confidence, probability,
score or rank is introduced. `S`/`V`/`O` remain source categories echoed inside the
candidate. No persistence API, projection store, deterministic or AI evaluator class,
new Unit, SQLite write or surrogate key enters a record or identity. Source stores are
read-only.

## 8. Tests

- `tests/test_unit8_amendment1.py`: 41 fast tests (the user-supplied 40 reconciled to the
  actual public API, plus a surrogate-key invariance test) and 3 opt-in real-Matthew tests
  (`MACULA_UNIT8_AMENDMENT1_INTEGRATION=1`, `MACULA_MATTHEW_DB`).
- `tests/support/unit8_amendment1_store.py`: disposable validated schema-v2 builder
  (Matthew 1:1 Np-Appos chain and the Matthew 1:2 S-V-O clause with interior connector
  token 6, using real node IDs).
- `tests/test_unit8.py`: two stale "S-V-O yields `()`" assertions were updated narrowly.

### 8.1 Synthetic snapshot and frozen identifiers

`source_file.sha256` must equal the SHA-256 of the stored bytes, so a schema-valid
disposable store cannot carry the real Matthew snapshot. Candidate ids derived from it
differ from the frozen real-snapshot ids **only** through `source_snapshot`. The builder
therefore self-validates every non-snapshot field against the frozen fixture and
re-encodes each derived candidate under the frozen snapshot with an independent encoder to
prove the frozen ids (the S-V-O id and all three Apposition ids). Fast tests assert the
frozen ids through that recompute; the integration tests assert the literal ids against
the real Matthew database.

### 8.2 Test-adapter reconciliation

The supplied spec assumed `HumanEvaluationInput`, `verify_candidate_v1/v2`, and
`RationaleCitation(kind, id)`. The actual frozen API is
`create_evaluated_interpretation(db_path, candidate, *, ...)`,
`verify_evaluated_interpretation(record, *, db_path)`, `compute_evaluation_id` and
`RationaleCitation(kind, citation_id)`. Adapters in the test module bridge the two without
changing production. The supplied citation-order test expected silent normalization,
which contradicts frozen Unit 8 behavior (misordered citations are rejected, section 5);
it was reconciled to assert rejection plus accepted canonical order. The V2 adapter
additionally requires the supplied lookup token itself to expose the candidate, because
production V2 always uses the first scope token.

### 8.3 Superseded historical assertions

Unit 8's two obsolete assertions are amended (Matthew 1:2 now yields exactly one
`ClauseStructureCandidate`, refs `5, 7, 8, 9`, and no Apposition). The four Unit 7
assertions already superseded by Unit 9 remain unedited and are filtered in memory per
`tests/README.md`. `tests/test_unit9.py::test_unit8_rejects_new_candidate_without_registry_amendment`
asserted the pre-amendment behavior (an S-V-O candidate is rejected by Unit 8). That is
exactly the behavior this amendment replaces, so the test now fails by design. Unit 9
tests are read-only for this amendment and were not edited; it is filtered in memory
like the other superseded tests and replaced by
`test_unit8_amendment1.test_a1_02_clause_structure_registry_entry_is_supported`. A future
authorized change should retire or rewrite it.

## 9. Authorized paths and stop line

Changed: `scripts/evaluated_interpretations.py`, `tests/test_unit8.py`,
`tests/test_unit8_amendment1.py`, `tests/support/`, this document, the Unit 8 contract
(new section 35 only), README/governance/index documents and the plan evidence.
Untouched: Unit 9 production and tests, Unit 7 tests, schema, importer, fidelity, query,
fixtures and historical audits.

This amendment does not claim independent acceptance. After the checkpoint: stop.
