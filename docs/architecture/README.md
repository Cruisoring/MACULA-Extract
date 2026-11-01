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
Phase remains AUTHORIZED. Units 3 and 4 are IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE;
Unit 5 is NOT STARTED. No automatic independent acceptance is authorized.

The historical reports retain their original investigation-time statuses and relative
evidence links, some of which refer to their original session/TEMP location. Their
historical conclusions are not rewritten to describe Unit 2. The parser report was
pre-existing untracked input; the user separately authorized its inclusion and removal
of only ten trailing-space hard breaks (Q1-Q10), verified against its original bytes.
