# Architecture Notes

Historical investigations remain evidence, not retrospective implementation specifications:

- [MACULA data architecture Spike](MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md)
- [XmlPro parser-reuse Spike](XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md)

Unit 1 freezes source identity and fixtures. The separately authorized
[Unit 2 source-schema contract](UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md) freezes the executable
SQLite representation, bootstrap/version policy and parser/locator boundaries.
Production importer/exporter, ingestion and Unit 3 remain unauthorized.

The historical reports retain their original investigation-time statuses and relative
evidence links, some of which refer to their original session/TEMP location. Their
historical conclusions are not rewritten to describe Unit 2. The parser report was
pre-existing untracked input; the user separately authorized its inclusion and removal
of only ten trailing-space hard breaks (Q1-Q10), verified against its original bytes.
