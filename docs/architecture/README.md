# Architecture Notes

The separately authorized [Unit 10 persistence contract](UNIT-10-STRUCTURAL-INTERPRETATION-PERSISTENCE-CONTRACT.md)
is **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT; see the
[independent audit](../audits/UNIT-10-STRUCTURAL-INTERPRETATION-PERSISTENCE-INDEPENDENT-ACCEPTANCE-AUDIT.md)),
following dedicated freeze
`d690209f7dce140b61d0056446cec370afce2edd`.
It authorizes only a separate append-only derived/evaluation store after that checkpoint,
not source writes, new structural/evaluation semantics or BRW.
The [store module](../../scripts/projection_store.py) and independently versioned
[schema](../../schema/001-projection-store.sql) preserve the existing DTOs/identities.
Both write paths require source-grounded verification on separate read-only source
connections; loads never regenerate human evaluations. See the contract's appended
implementation validation and [tests](../../tests/README.md#unit-10-separate-persistence).
Historical stop lines below retain their checkpoint meaning.

The [Unit 11 discovery and history query contract](UNIT-11-READ-ONLY-STRUCTURAL-INTERPRETATION-DISCOVERY-HISTORY-QUERY-CONTRACT.md)
is **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE** (frozen design, then separately authorized
[implementation](../../scripts/projection_query.py) and [tests](../../tests/README.md#unit-11-discovery-and-history-queries)).
It provides read-only discovery of persisted candidates from a scripture selector by exact member-token
scope, then candidate-centered evaluation/supersession history, with no current-truth semantics. No schema
change, independent acceptance or Unit 12 is authorized.

Historical investigations remain evidence, not retrospective implementation specifications:

- [MACULA data architecture Spike](MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md)
- [XmlPro parser-reuse Spike](XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md)

Unit 1 freezes source identity and fixtures. The separately authorized
[Unit 2 source-schema contract](UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md) freezes the executable
SQLite representation, bootstrap/version policy and parser/locator boundaries.
Implemented Unit 2 Amendment 1 establishes schema version 2 with transactional
post-load complete membership validation instead of the per-row ancestry trigger.
Those artifacts did not authorize production ingestion. The later, separately authorized
[Unit 3 Matthew pipeline](UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md) adds actual XmlReader
import, byte archive export and independent normalized source fidelity verification.
No scope beyond pinned SBLGNT Matthew is authorized.
The separately authorized [Unit 4 query slice](UNIT-4-MATTHEW-QUERY-SLICE.md) adds
only read-only verse/token source queries over an existing schema-v2 Matthew store.
The separately authorized [Unit 5 syntax navigation contract](UNIT-5-READ-ONLY-SYNTAX-NAVIGATION-CONTRACT.md)
adds only source-ID lookup, relational children/ancestors and exact stored membership
through the same read-only boundary, with raw Head and source-oriented node results.
The separately authorized [Unit 6 source evidence composition](UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md)
composes the exact token, linked leaf, relational ancestry, immediate-parent children
and explicitly named exact membership context without interpreting source facts.
Unit 6 is IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT, see
[audit](../audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Phase remains AUTHORIZED. Units 3 and 4 are IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT,
same audit); Unit 2 Amendment 1 remains IMPLEMENTED only.
Unit 5 is IMPLEMENTED / INDEPENDENTLY ACCEPTED, decision ACCEPT WITH MINOR FINDINGS;
M1 remains unresolved. The separately authorized
[Unit 7 structural candidate boundary](UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md)
adds only in-memory, versioned Apposition candidates over explicit Np-Appos ancestry.
Source facts/composition remain in the query module; derived DTOs, snapshot-bound
SHA-256 identity and derivation live in a separate structural candidate module.
Unit 7 is IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS, see
[audit](../audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Unit 7 itself adds no evaluation or persistence.
The separately authorized [Unit 8 in-memory evaluation boundary](UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation)
is **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS, see
[audit](../audits/UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md)). Its frozen
`EvaluatedStructuralInterpretation`, `RationaleCitation` and `RationaleNote` DTOs
and `create_evaluated_interpretation`, `verify_evaluated_interpretation`,
`compute_evaluation_id` API live in `scripts/evaluated_interpretations.py`.
Creation requires independent candidate V1 recomputation plus public Unit 7 V2
re-derivation; verification is V1/history offline and also V2 with a database.
Only the human structural adequacy / `1` protocol is registered.
The implementation checkpoint has sole parent
`8f8b2e7642204378eb0e56e20d096b6233e409b2`; 50 Unit 8 fast tests, 1 opt-in
existing-Matthew integration, 62 Unit 4-7 fast regressions and both required
verifiers passed (implementation validation; independent acceptance is recorded above).
No persistence, semantic roles, confidence, BRW integration, source-schema change
or Unit 9 production is authorized by that implementation checkpoint.
Unit 5 M1 and Unit 7 audit M1 remain unresolved.
Phase remains AUTHORIZED; see [current governance](../governance/PHASE-STATUS.md).

The separately authorized [Unit 9 S-V-O production implementation](UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#28-authorized-production-implementation)
is **IMPLEMENTED / INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS, see
[audit](../audits/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md);
Unit 9 audit M-1 unresolved). Its preceding independent
raw XML and read-only SQLite freeze established exact
S=`MAT 1:2!5`, V=`MAT 1:2!7`, O=`MAT 1:2!8,!9`; token 6 is excluded.
The [source-facing fixture](../../fixtures/matthew-1-2-svo-candidate.expected.json)
freezes the expected canonical candidate identity after membership agreement.
Production now matches the complete unchanged fixture and frozen identity.
Parallel frozen clause DTOs preserve existing Apposition callers and IDs.
Generic exact membership retrieval and clause-specific topology/partition checks
live in the existing structural candidate module, over the owned read-only query
boundary. 39 Unit 9 fast and 3 real-Matthew integration tests passed; the two-stage
regression validated 267 tests, with 7 explicit skips (see test instructions).
Unit 8 is unchanged by Unit 9 itself; clause
evaluation support is added only by Unit 8 Amendment 1 below.
The validation above is implementation validation; independent acceptance is recorded
in the linked audit.
No persistence, semantic projection, BRW integration or Unit 10.

The separately authorized
[Unit 8 Amendment 1](UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md) is **IMPLEMENTED /
INDEPENDENTLY ACCEPTED** (ACCEPT WITH MINOR FINDINGS, separate decision in the same
[audit](../audits/UNIT-8-AND-AMENDMENT-1-INDEPENDENT-ACCEPTANCE-AUDIT.md)). It extends only the closed `human-structural-adequacy/1`
registry to `clause-structure` / `source-rule-s-v-o` / `1` (Unit 9
`ClauseStructureCandidate`) alongside the Apposition tuple, with generic V1 clause
verification and unchanged V2 re-derivation; evaluation remains in-memory. No
persistence, semantic roles, BRW integration or new Unit.

 [record post-Unit-4 product readiness findings](POST-UNIT-4-PRODUCT-READINESS-CONCLUSION.md)
 Document the post-Unit-4 read-only SQLite exploration and resulting
product-readiness conclusions.
Manual inspection confirms that the relational source store directly
supports token facts, syntax ancestry, ordered child navigation, exact
constituent membership, source Head navigation, and lexical-head
resolution without reconstructing a second authoritative syntax model.
Record Matthew 1:1 constituent and ancestor observations together with
the Matthew 1:2 S-V-O navigation example and its exact discontinuous
membership.
Adopt the resulting product direction:
SQLite source store
→ thin read-only navigation
→ localization
→ presentation
Keep manual SQLite observations distinct from independent acceptance.
Preserve the boundary between linguistic source facts and later semantic
interpretation.
Unit 3 and Unit 4 remained pending independent acceptance at that investigation
(both were later independently accepted; see the historical Units 3, 4 and 6 audit).
At that investigation, Unit 5 remained NOT STARTED; the later separate Unit 5
authorization does not independently accept that report or Units 3 and 4.

The historical reports retain their original investigation-time statuses and relative
evidence links, some of which refer to their original session/TEMP location. Their
historical conclusions are not rewritten to describe Unit 2. The parser report was
pre-existing untracked input; the user separately authorized its inclusion and removal
of only ten trailing-space hard breaks (Q1-Q10), verified against its original bytes.
