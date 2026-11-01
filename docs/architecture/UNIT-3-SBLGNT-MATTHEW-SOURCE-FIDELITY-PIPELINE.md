# Unit 3 - SBLGNT Matthew Source Importer & Fidelity Round-Trip

Status: IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.
Original authorization checkpoint: `02b8d788dd3b7bf50b59a76eeda2632182b710f9`.
Required implementation checkpoint parent: `087865e3d822c7baa1f9d7e5313d46b5168bc670`.

## Frozen baseline and scope

Unit 1 remains IMPLEMENTED / INDEPENDENTLY ACCEPTED. Unit 2 remains IMPLEMENTED /
INDEPENDENTLY ACCEPTED, with the original minor findings retained in its audit.
Unit 2 Amendment 1 is IMPLEMENTED at the required parent and establishes schema 2.
Unit 1 artifacts, the amended Unit 2 technical baseline, historical architecture
reports and both independent audits remain unchanged by this Unit 3 checkpoint.
Historical F-1 through F-4 remain recorded, without deletion or reclassification.
The Phase stays AUTHORIZED. Unit 4 is NOT STARTED; no subsequent Unit is authorized.

Only `C:\Works\macula-greek\SBLGNT\nodes\01-matthew.xml` is production input:
revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`;
SHA-256 `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`;
14,115,918 original bytes. The public importer accepts an output path, not an input
path/edition/book override. The frozen verifier rechecks actual Git root/revision,
the one allowlisted path and its complete original bytes before every production build.
No network, directory expansion, other books, N1904/full NT, companions, XmlPro,
semantic projection/BRW roles or physical byte/UTF-16 range mapper is introduced.

## Authoritative parser and local runtime

[XmlReaderBridge](../../parsers/XmlReaderBridge/Program.cs) actually calls
`XmlReader.Create` on the original standard-input byte stream. Its explicit settings:
DtdProcessing=Prohibit, XmlResolver=null, ValidationType=None,
ConformanceLevel=Document, CheckCharacters=true, and all three Ignore flags=false.
Expanded-name XInclude include is rejected; no include is acquired.
XML declaration/BOM decoding belongs to XmlReader, not a prior Python text decode.
Malformed syntax, duplicate expanded attributes, undeclared prefixes, invalid
characters/encoding and prohibited DTDs produce stderr errors and nonzero exit.
The complete marker appears only after successful reader exhaustion.

The bridge targets the locally available .NET 9 runtime. Its project has no package
references; NuGet sources are cleared and auditing is disabled. Build, CLI-home and
package/intermediate directories are isolated in one uniquely named system TEMP
directory and removed on exit. Missing SDK/reference packs fail explicitly, with no
download/fallback parser. No old benchmark resource bounds are adopted as safety facts:
the public route instead requires the exact 14,115,918-byte pinned source identity.

Ordinary Text/Whitespace/SignificantWhitespace events coalesce into one direct text
occurrence until a structural/content boundary. Every CDATA section (including empty),
comment and PI remains distinct. No Trim, NFC/NFD normalization, token substitution,
InnerText/descendant-text extraction or lexical field fallback is used.

## Import and amended SQLite schema 2

[source_importer](../../scripts/source_importer.py) writes the exact original BLOB,
snapshot/file/book identity and complete element/attribute/ordered-content ledgers.
Expanded URI/local names, QName/prefix evidence, attribute source order, presence/
empty values and zero-based element siblings are preserved. One-based same-expanded-
name sibling counts generate the unchanged version-1 occurrence locator.
Snapshot manifest identity hashes the exact frozen Unit 1 contract bytes; schema/
configuration/program identities use the existing universal-LF text-hash convention.
No source-byte EOL normalization is performed.

Sentence/Tree/Node wrappers are derived from actual XML nesting. All raw attributes
remain generic evidence; typed fields are nullable mirrors, not inferred defaults.
`ref`/`Ref`, all four IDs, both morphology tags and all surface/normalized/gloss/
enrichment fields stay separate. Leaf text concatenates only that leaf's direct text
and CDATA. Tree traversal and canonical numeric scripture ranks are stored separately.
Every leaf's actual XML Node ancestry, including self, supplies exact membership;
Start/End never supply an envelope. Unit 2 Amendment 1 removed the pathological
per-row `membership_ancestry` INSERT trigger, without a replacement per-row trigger.
The membership PK, reverse index, same-Tree foreign keys, expected ancestry view and
unrelated immutability protections remain active. The mandatory schema-v2 validator
requires both actual EXCEPT expected and expected EXCEPT actual to be empty.
Descending negative token surrogate IDs are retained implementation identities,
not linguistic identity or ordering evidence. Unit 3 does not disable or change
the amended schema-v2 constraints.

Production construction uses a dedicated main connection, FK/recursive triggers ON,
an isolated empty-schema candidate and BEGIN IMMEDIATE. Schema bootstrap remains
unchanged from the schema-v2 baseline. All imports, schema/internal validation,
complete post-load membership equality, independent source fidelity,
logical digest and historical count checks precede commit/publication. Active failed
transactions explicitly roll back; candidates close and temporary directories clean
up. A same-volume hard link publishes only a completed closed candidate, atomically
and without overwriting an existing destination. Protected repositories are rejected
as output targets. No production SQLite binary is a Git deliverable.

## Two distinct fidelity channels

**BYTE:** [archive_bytes](../../scripts/source_fidelity.py) selects only the original
BLOB. Exact bytes, size and checksum must equal the independently rechecked upstream
source. This does not prove normalized fidelity.

**NORMALIZED:** [reference_events](../../scripts/source_fidelity.py) independently
parses the original bytes with Python standard-library Expat, not the importer event
stream or typed records. It independently resolves namespace/QName evidence, source
order, locators, text/CDATA/comment/PI occurrences and XML-derived relational facts.
Expat's DefaultHandler is used for document-level whitespace, which CharacterDataHandler
does not report; only that lexical XML whitespace receives XML 1.0 CRLF/CR folding,
after coalescing across input chunks. Character-reference CR inside element content
is not destructively folded.

[db_xml_events](../../scripts/source_fidelity.py) independently reconstructs only
the element/attribute/content tables, never original_bytes. Complete ordered
start/attributes/locator/content/end events are compared occurrence by occurrence,
then all Sentence/Tree/Node/Token topology, mirrors, coordinates, dual orders and
exact ancestry memberships are compared to independently derived source facts.
The schema-v2 Unit 2 validator is also mandatory, not replaced by counts.

[normalized_xml](../../scripts/source_fidelity.py) serializes those DB-only events
to UTF-8 XML, retaining namespaces, explicit attribute values and distinct content
kinds. Character-reference CR and attribute TAB/LF/CR are escaped without substitution.
Its lexical bytes need not equal the original declaration/BOM/indentation/empty-tag/
quote spelling. Full-file tests reparse the resulting actual XML export independently
and compare it with the original source facts.

Published consumers use `mode=ro`, query_only=ON, FK=ON, recursive_triggers=ON.
F-2 is not erased: default writable connections may still REPLACE consistently.
The new test preserves the BLOB and schema, changes a generic attribute plus its
typed mirror through default-connection REPLACE, observes internal validation PASS
after restoring the required profile, then requires source fidelity FAIL.
This control concerns the fixed Matthew source pipeline, not broader production
certification or Unit 2 retroactive acceptance.

## Determinism and build evidence

Logical digest version: `macula.source-logical.v1`. SHA-256 covers canonical minimal
ASCII JSON lines: version, logical schema/source/book identities, complete DB-only
ordered XML events and all relational facts ordered by source locators. Internal
integer PKs, physical page layout, diagnostics and runtime/timing are excluded.
Relational endpoints use occurrence locators, not PKs. Tests separately vary PKs and
SQLite page sizes. Default tests share one full Matthew build; the retained
second-build determinism test requires explicit `MACULA_UNIT3_SECOND_BUILD=1`.
This slow gate is not implicitly run by default/focused discovery.

The build report records actual source/schema/parser/locator/importer/config/code
identities, parser/runtime, Python/SQLite versions, independent counts, BYTE and
NORMALIZED status, logical digest version/value, completed status and elapsed time.
Runtime and timing are evidence, not deterministic digest inputs.

The previously verified schema-v2 full production-style build completed in
68.517 seconds (73.319 including bridge bootstrap), under a 600-second hard timeout.
It produced 59,891 elements, 767,429 attributes, 179,675 content rows, 1,134
sentences/Trees, 56,488 nodes, 18,329 tokens, 159,391 exact memberships and 733
single-character tokens. Complete independent BYTE/NORMALIZED comparisons passed.
Its logical digest is
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`.
Only one full DB was built for that evidence; no second-build determinism result
is claimed. Test 19 now assigns genuinely different syntax-node PKs to its manual
fixtures and preserves the original PK-independent logical-digest assertions.

## Validation and checkpoint policy

Run the unchanged Unit 1 verifier and Unit 1/2 regression suites before Unit 3.
Run all 22 Unit 3 tests that do not require the explicit second build, including
actual full-source comparisons, export/reconstruction, Greek and Matthew boundaries,
membership validation and F-2. The 23rd, second-build determinism test remains
available as a documented explicit slow gate; skipping it does not claim its result.

Reconciliation may reuse the previous fully verified DB through an external
read-only test fixture, with a fresh complete source-fidelity validation and digest
comparison to that report. Such execution must state REUSED PREVIOUS VERIFIED
EVIDENCE rather than claim a new build. If a new full build is necessary, allow one
with a 600-second hard timeout, not a second DB. Temporary test exports and bridge
outputs are removed after connections close; an existing external DB is preserved.

Before the sole checkpoint: review all 14 authorized Unit 3 paths, verify the exact
staged set and cached whitespace check, and compare frozen/protected baselines.
No further Unit 1/2 technical change is authorized. Any test/fidelity failure stops
the checkpoint rather than weakens assertions. Unit 3 is implemented but requires
separate independent acceptance. Exact ending checkpoint, unique required parent,
14 committed paths and final worktree/index/generated-file cleanliness are verified
after committing. This checkpoint does not authorize Unit 4.
