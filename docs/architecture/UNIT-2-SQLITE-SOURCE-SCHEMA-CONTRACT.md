# Unit 2 - SQLite Source Schema & Parser Contract

## Scope and evidence

This contract defines an executable SQLite representation for the SBLGNT Matthew
vertical slice. It does not implement production XML parsing, importer/exporter,
ingestion, BRW projection, localization, or physical range mapping.

The [accepted Unit 1 source contract](../../contracts/macula-sblgnt-matthew.unit1.json)
and fixtures remain unchanged. Primary input remains Clear-Bible/macula-greek,
revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`,
`SBLGNT/nodes/01-matthew.xml`, SHA-256
`FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.

The historical [data Spike](MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md)
and [parser Spike](XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md) remain historical
evidence. Unit 2 implements only its separately authorized subset, not the original
Spike's broader suggested one-book importer/exporter implementation unit.

## Version and bootstrap

- [DDL](../../schema/001-source-store.sql): schema version **2**, Unit 2 Amendment 1.
  The filename remains the bootstrap DDL path, not a production migration sequence.
- [Bootstrap/validator](../../scripts/source_schema.py): `bootstrap(connection)`,
  `validate_store(connection)` and a memory-only verification CLI.
- `PRAGMA user_version=2` plus a singleton `schema_version` row identify the version.
  The row also records DDL, parser-contract and locator-contract SHA-256 values.
- Code/config hashes use UTF-8 text with LF line endings, preserving every other
  character. This avoids Git `core.autocrlf` differences becoming different schema
  definitions. **Original source bytes and their checksums are never normalized.**
- Empty, unversioned main database only; no existing user objects, temp shadows,
  attachments, application ID, version, or active transaction.
- Repeated bootstrap always fails explicitly as already initialized/version mismatch;
  it is not an idempotent ingestion API or a general migration framework.
- DDL and version insertion run in one transaction. SQL failure rolls it back.
  Bootstrap does not mutate or repair an unknown database.
- Version 1 databases are not accepted as version 2 and are not migrated in place.
  Rebuild from the fixed published source into a fresh version 2 database.
- SQLite 3.37+ with STRICT and JSON support. Actual validation runtime:
  Python 3.13.7, SQLite 3.50.4. No network dependency.
- Every source-schema connection must enable `foreign_keys=ON` and
  `recursive_triggers=ON`. Validation refuses disabled enforcement. Recursive
  triggers prevent REPLACE's implicit deletion from bypassing source immutability.

## Authority and relational core

**Original bytes > generic XML occurrence/attribute/content > deterministic typed mirrors.**
The typed layer is not another writable interpretation of the source.

| Table | PK / key relationships | Purpose |
|---|---|---|
| `schema_version` | singleton 1 | schema and contract identity |
| `dataset_snapshot` | snapshot integer PK; unique edition/repository/revision/manifest | source-scoped release identity |
| `book` | integer PK; snapshot FK; snapshot/book-code unique | scripture book registry, distinct from physical file |
| `source_file` | integer PK; snapshot FK; optional same-snapshot book FK; snapshot/path unique | exact BLOB, uppercase SHA-256, byte size, format, encoding evidence |
| `xml_element` | integer PK; file FK; same-file parent FK; file/scheme/version/locator unique | all source wrappers/elements, names, lexical evidence and ordering |
| `xml_attribute` | integer PK; owner FK; unique owner/ordinal and owner/expanded name | source presence/value ledger, including unknown fields |
| `xml_content` | integer PK; file/owner/child FKs; owner/ordinal and child occurrence unique | ordered element/text/CDATA/comment/PI occurrences, including document level |
| `sentence` | integer PK; file/book and element/file FKs; file/ordinal unique | raw ref, source element and sentence order |
| `tree` | integer PK; sentence and element FKs; sentence/ordinal unique | all alternative source Trees |
| `syntax_node` | integer PK; Tree/element FKs; same-Tree parent FK; parent/sibling order unique | complete ordered Node nesting and raw nodeId/Id/Cat/Rule/ClType/Start/End/Head/Length |
| `token` | integer PK; unique leaf node; same-Tree node FK; book FK; separate Tree-local order keys | source text, identities, coordinates, morphology and raw enrichment |
| `node_token_membership` | (node,token) PK; same-Tree FKs | rebuildable exact descendant-leaf closure |

Two views: `typed_attribute_mirror` exposes all named source-attribute mirrors;
`expected_node_token_membership` computes ancestry, including leaf self.
No redundant authoritative tree-edge table, speculative Frame grammar, or global
lemma/word-sense registry is introduced.

All source and typed-mirror rows reject UPDATE/DELETE. Rebuild into a fresh schema
or append a separately scoped snapshot, rather than overwrite accepted facts.
Membership alone permits deletion/recomputation. INSERT retains PK and same-Tree
FK enforcement, but no per-row semantic ancestry trigger. Rows can be transiently
semantically invalid during a build; mandatory post-load validation rejects them.
Published source stores should additionally use read-only connection/file boundaries.
Schema catalog validation detects removed/altered tables, views, indexes or triggers.

## Typed mirror and presence rules

- All raw strings/IDs use TEXT and BINARY semantics, not encoded numeric identities.
- Missing source attribute: no `xml_attribute` row. Present-empty: row with value `""`.
- Nullable raw mirror: NULL only for absence; a real empty attribute mirrors as `""`.
- `Id`, XML-namespace `xml:id`, `nodeId`, `morphId`, `ref` and `Ref` remain distinct.
- `FunctionalTag` and `FormalTag` have independent columns and generic attributes.
- Token source direct text, Unicode, NormalizedForm and UnicodeLemma remain independent.
  Direct text is the ordered concatenation of direct text/CDATA, not descendant InnerText.
- Morphology remains raw Case/Gender/Number/Person/Tense/Voice/Mood/Type/Degree/HasDet.
- English/Mandarin/Gloss remain separate raw fields; no Chinese labels/translation are generated.
- LexDomain/LN/Frame/Ref/SubjRef/Notes/LowfatException/status remain raw strings.
  Unknown fields and annotations on nonleaf nodes remain fully representable generically.
- No role dictionary, target parser or same-book resolution constraint is invented.
  Repeated roles, multiple IDs, sentinel and not-loaded target strings remain intact.

FK/CHECK/UNIQUE constraints alone do not establish generic/typed equality.
`validate_store` is the mandatory model-completion gate: exact DDL/catalog and metadata,
FK/integrity, archive SHA, canonical locators, ordered content, named source wrappers,
complete supplied sentence/Tree/Node mirrors, source attributes, direct token text,
scripture coordinates, both orders, and complete exact membership.
It reports explicit failures; no silent defaults or repaired-source success.

This validator does **not** parse original BLOBs or certify that every original XML
event was persisted. Archive-only records can exist before parsing. Future importer
coverage and independent XML/normalized round-trip checks remain required.

## Unit 2 Amendment 1

Original Unit 2 schema version 1 was independently accepted with minor findings.
The [original independent audit](../audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md)
is historical evidence and remains unchanged; it does not certify this amendment.

Amendment 1 removes the pathological `membership_ancestry` BEFORE INSERT trigger
without any replacement per-row ancestry trigger. The original trigger reran a
global recursive ancestry computation for every membership row. Version 2 retains
the membership table, PK, reverse index, same-Tree foreign keys, expected ancestry
view, and all unrelated immutability protections.

Exact membership remains actual XML ancestry-derived descendant closure, including
leaf self-membership and discontinuous sets. Start/End, ranges and scripture
envelopes never supply membership.

Before any successful authoritative import may commit, `validate_store` must prove
both set differences empty:

```sql
SELECT node_id, token_id, tree_id FROM node_token_membership
EXCEPT
SELECT node_id, token_id, tree_id FROM expected_node_token_membership;

SELECT node_id, token_id, tree_id FROM expected_node_token_membership
EXCEPT
SELECT node_id, token_id, tree_id FROM node_token_membership;
```

Extra same-Tree non-ancestor or sibling membership may pass INSERT, but must fail
final validation. Missing ancestor/leaf-self membership and an injected Matthew
1:2 token 6 must also fail. Cross-Tree membership remains directly rejected by
composite foreign keys. Equal counts are not sufficient evidence of equal sets.

The production build owns one `BEGIN IMMEDIATE` transaction for loading and all
completion gates. Full store validation, complete membership equality and Unit 3
independent source-versus-DB fidelity must succeed before COMMIT/publication;
any failure rolls back and must not publish a partial successful store.

The source is a fixed published MACULA artifact. The importer preserves its
linguistic analysis rather than rejudging or repairing it. XML-to-SQLite mapping
correctness remains this project's responsibility; post-load topology and set
validation enforce that boundary.

The amended DDL has a new SHA-256 identity, schema metadata and user_version 2.
Parser and locator contracts remain unchanged. The existing uncommitted Unit 3
importer contract synchronizes only its schema_version to 2 and is not part of
the Unit 2 amendment checkpoint. Other Unit 3 work remains preserved.

### Amendment validation evidence

Unit 1 regression: 26 tests PASS. Amended Unit 2 regression: 56 tests PASS.
The combined focused run executed 82 tests with no failures or errors.
Negative cases cover extra non-ancestor/sibling rows, missing ancestor/leaf-self
rows, equal-count wrong sets, Matthew 1:2 token 6 injection, cross-Tree FK rejection,
and rollback after post-load membership validation failure.

Before/after SQL catalog comparison found only the removed `membership_ancestry`
trigger and the schema-version CHECK changing from 1 to 2. All other catalog
objects are identical. Version 2 DDL SHA-256 (LF text identity):
`57692AC583E90831F2F3279776CCB98FE5541E0DC16C78C333997B7CECCB1503`.

Each scale ran once with the current Unit 3 implementation and full integrity/
source-fidelity gates. Timings are observed seconds, not new millisecond contracts.
Scale totals include offline bridge compilation; their DB reconstruction is reused
for digest generation, matching the preceding diagnostic scope.

| Sentences | Membership rows | Generation | Insertion | Final membership validation | Total |
|---|---:|---:|---:|---:|---:|
| 1 | 71 | 0.000044 | 0.000354 | 0.000828 | 6.175 |
| 10 | 3,470 | 0.001759 | 0.020593 | 0.017413 | 6.753 |
| 50 | 11,890 | 0.005656 | 0.072799 | 0.068875 | 10.039 |
| 100 | 18,347 | 0.008293 | 0.112402 | 0.171949 | 12.511 |
| Full Matthew, 1,134 | 159,391 | 0.081334 | 1.124624 | 1.431885 | 73.319 |

Exactly one full production-style build completed under a 600-second supervising
process timeout: 68.517 seconds for the production builder, 73.319 including the
bridge. It used the original production validation/digest flow without reconstruction
caching and published only after its successful commit. Complete independent BYTE
and NORMALIZED source comparisons passed: 59,891 elements, 767,429 attributes,
179,675 content records, 1,134 sentences/Trees, 56,488 nodes, 18,329 tokens,
159,391 memberships and 733 single-character tokens. The production database is
outside Git. A second full build was not started.

## Occurrence identity

The [locator contract](../../contracts/occurrence-locator.unit2.json) and
[pure encoder](../../scripts/occurrence_locator.py) define:

```text
scheme = macula.xml-expanded-ordinal-path
version = 1
locator = [["","Sentences",1],["","Sentence",1],["","Trees",1],["","Tree",1],["","Node",1]]
```

It is minimal ASCII JSON, with JSON escaping and no Unicode normalization. Each
segment is exact namespace URI/local name plus a **one-based ordinal among direct
element siblings with that same expanded name**. Prefix aliases never enter identity;
URI delimiter characters and supplementary Unicode cannot make path parsing ambiguous.
The complete path must be canonical and agree with persisted parents/siblings.

External source key:

```text
(edition, repository_uri, revision, manifest_sha256,
 relative_path, source_sha256, scheme, scheme_version, locator)
```

For the authorized source, manifest identity is SHA-256 of exact frozen Unit 1
contract bytes, which contain the fixed revision and single-file allowlist.
SQL synthetic tests use explicitly synthetic source manifests, not actual production snapshots.

Database PK, lexical prefix, upstream ID, source span and physical offset are not key inputs.
Attribute identity adds owner + expanded name; ordered direct-content identity adds
owner/document + canonical content ordinal/kind. Line/column columns are nullable diagnostics.
No byte/UTF-16 range columns, mapper or XmlPro Scope implementation is required or supplied.

## Ordering, membership and Head

Keep separate:
- zero-based element sibling ordinal (all direct element children);
- zero-based syntax sibling ordinal (direct Node children);
- zero-based sentence/Tree ordinal and Node-path tree traversal;
- zero-based Tree-local leaf ordinal;
- raw TEXT source Start and End (nullable, not computed defaults);
- positive scripture book/chapter/verse/word coordinates;
- zero-based Tree-local canonical ordinal, independently sorted by coordinates,
  with tree-leaf ordinal as a tie-breaker for alternative occurrences;
- exact ancestry membership.

Whole-book scripture retrieval uses the coordinate index, not the local canonical ordinal.
Upstream nodeId/xml:id/morphId indexes are scoped for retrieval, not global uniqueness:
alternate Trees/snapshots can repeat those values without losing occurrences.

Membership is all actual descendant token leaves; a leaf has its own self membership.
Start/End/min-max do not create members. The reduced live-value boundary test proves:
tree order `[6,5,7,8,9]`, canonical order `[5,6,7,8,9]`, target node
`400010020050040` membership `[5,7,8,9]`, source span `"5".."8"`, excluded token 6.
This test is not complete Matthew ingestion or a production round-trip.

Head is preserved as raw TEXT and presence, with zero-based direct Node sibling order
available to later deterministic resolution. No default zero, resolved head FK,
lexical-head algorithm or semantic Actor is generated.

## Parser contract

The [XmlReader contract](../../contracts/xmlreader-parser.unit2.json) requires
System.Xml.XmlReader over original verified bytes:
DTD Prohibit, resolver null, ValidationType None, Document conformance,
character checking, preserved whitespace/comments/PI, exact expanded-name identities,
all attributes, no external acquisition or implicit XInclude, and explicit include rejection.
Malformed input fails closed. XML-required EOL/entity semantics are distinct from
application Trim, Greek normalization, HTML decoding or substitution, all prohibited.

Canonical direct content coalesces adjacent ordinary text/whitespace events only;
each original CDATA section/comment/PI remains distinct. Value chunks are accumulated
within their reader node, never treated as independent content occurrences.
Original bytes retain declaration, quote, entity, BOM and lexical EOL fidelity.

Resource thresholds are not frozen from experimental benchmarks; future implementation
must justify and declare them. XmlPro is not referenced or copied.
Python ElementTree appears only in existing source verification and schema tests;
it does not implement or replace the production XmlReader boundary.

## Indexes and deferred work

Explicit indexes cover archive checksum, XML parents/names/content order, raw sentence ref,
Tree/syntax relationships, scoped upstream IDs, scripture coordinates, lemma and reverse membership.
UNIQUE indexes cover source occurrences/order, not global linguistic IDs.
Morphology-combination indexing remains workload-driven, not speculative.

Deferred: production parser/importer/exporter, exact original-file coverage,
source and normalized round-trip, production/database distribution and permission gates,
full Matthew/NT/N1904 or companions, reference grammar/resolution, richer lexical tables,
license/component mapping, cross-version relinking, optional physical mapper, benchmarks,
localization, BRW projection/integration and Unit 3.

## Historical-report hygiene evidence

The user authorized archiving the pre-existing parser report in this same checkpoint,
then separately authorized pure trailing-whitespace cleanup.
Only original lines **653, 656, 659, 662, 665, 668, 671, 674, 677, 680** changed:
two ASCII spaces were removed from each Q1-Q10 question line.
For every changed line, `old.rstrip() == new.rstrip()`; all other bytes are unchanged.
The CRLF original was independently reconstructed from Git's LF index and its established SHA.

- Original raw SHA-256: `01245365D6ACAD070ED5E420D7D73356EA7C7A1C121F55866FB67AF0C8A4F551`.
- Cleaned raw SHA-256: `47F91C76D2A87EA981367936A7B415CA545900502FFE2CD11021DD0DC74DC242`.
- Original/cleaned byte sizes: 64,392 / 64,372; exactly 20 trailing-space bytes removed.
- Investigation findings, decisions, benchmark values, source identity, fidelity requirements,
  fixtures and independent acceptance findings were not changed.
