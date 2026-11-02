# Architecture Notes

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
[audit](../audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md)). No evaluation, persistence,
semantic roles, automatic independent acceptance or Unit 8 is authorized;
see [current governance](../governance/PHASE-STATUS.md).

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
