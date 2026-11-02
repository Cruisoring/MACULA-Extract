# Historical Units 3, 4 and 6 Independent Acceptance Audit

## Executive Decisions

Three separate decisions; there is no collective acceptance.

- **Unit 3: ACCEPT** (BLOCKER 0; MAJOR 0; MINOR 0; INFORMATIONAL 4)
- **Unit 4: ACCEPT** (BLOCKER 0; MAJOR 0; MINOR 0; INFORMATIONAL 2)
- **Unit 6: ACCEPT** (BLOCKER 0; MAJOR 0; MINOR 0; INFORMATIONAL 4)

Unit 7 dependency impact: **NO REAUDIT REQUIRED / PRIOR ACCEPTANCE REMAINS VALID**.
Unit 7 is neither re-accepted nor rejected here. Unit 2 Amendment 1 is not accepted
here.

Governance reconciliation: **DEFERRED TO NEXT TASK PER USER DIRECTION** (see
Governance Implications). No governance, README, contract, schema, production or test
file was changed by this audit.

## Audit Nature and Independence

This is a historical, retrospective acceptance audit of Units 3, 4 and 6, which were
implemented and left `IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE`. It follows a strict
no-repair rule: nothing was fixed, only observed.

Implementation reports and test literals were treated as claims, not oracles. Fresh
oracles were built from the raw upstream XML (Python `xml.dom.minidom`, which shares no
code with the .NET `XmlReader` production parser or with the in-repo Expat reference)
and from independent SQL. Production code was exercised only as the system under test.
Existing tests were run last as regression evidence and are never the sole basis for a
conclusion. All audit scripts, historical tree exports and disposable stores lived
outside the repositories and were removed.

The three historical trees were materialised with `git archive` (no checkout, reset or
detach of the repository). The real database was only opened `mode=ro`; every
write/corruption experiment ran on a disposable copy.

## Evidence Classification

| Class | Meaning |
|---|---|
| **A** | Fresh independent oracle: raw XML via `minidom`, or independent SQL, compared with production output or the existing database. |
| **B** | Audit-authored behavioural probe: disposable corrupted/mutated stores, SQLite authorizer on the production-opened connection, negative inputs, independently built stores. |
| **C** | Direct production/contract code inspection. |
| **D** | Existing repository tests and verifiers, used as regression/supporting evidence only. |

## Repository / Source / Database Baseline

- Primary repo `C:\Projects\MACULA-Extract`: branch `master`, HEAD
  `20a8016d34f578d6b5f7c4b85b457bce18539399` (`record Unit 7 independent acceptance`),
  worktree clean, only ignored item `sblgnt-matthew.sqlite3`; `git diff --check` clean.
- `C:\Works\macula-greek`: `main`, `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean.
- `C:\Projects\bible-research-merged`: `master`, `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`;
  ignored `dist/`, `node_modules/`, `tsconfig.tsbuildinfo`; otherwise clean.
- Source `SBLGNT/nodes/01-matthew.xml`: 14,115,918 bytes, SHA-256
  `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`.
- Environment: Python 3.13.7, SQLite 3.50.4, .NET SDK 9.0.310 (runtime 9.0.12).
- Real DB BEFORE audit: size 160,968,704; SHA-256
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`; `user_version=2`;
  journal mode `delete`; no WAL/SHM/journal; 75 catalog objects, catalog digest
  `7437bb4a55c2e49f343dae7bfa46f062c9686871dd0c44f19879aaaedd2923eb`
  (sha256 of `"\n".join(repr(row))` over `select type,name,tbl_name,sql from sqlite_master order by type,name`).
- Row counts: schema_version 1, dataset_snapshot 1, book 1, source_file 1, xml_element
  59,891, xml_attribute 767,429, xml_content 179,675, sentence 1,134, tree 1,134,
  syntax_node 56,488, token 18,329, node_token_membership 159,391.

## Historical Checkpoint Mapping

| Unit | Commit | Parent | Subject |
|---|---|---|---|
| 3 | `cc745c692a134cbdaef8c8d177c61e595b0ae31e` | `087865e3d822c7baa1f9d7e5313d46b5168bc670` | implement SBLGNT Matthew source-fidelity pipeline |
| 4 | `76bdcf5b47fa660390180fdbf430400d3f2d3024` | `cc745c692a134cbdaef8c8d177c61e595b0ae31e` | implement read-only Matthew source query slice |
| 6 | `b7cc92e6e42979a64919edd173ff886591552344` | `842ba45fff04a7e0c492faeb9f4dc60a3ee6c2d5` | implement read-only source evidence composition |

Related, not audited here: `842ba45` Unit 5; `8d82fa2` post-Unit-4 readiness doc;
`9331d8a` Unit 7; `20a8016` Unit 7 acceptance; Unit 2 `9c39f83` (implementation),
`02b8d78` (acceptance), `087865e` (Amendment 1, schema v2).

Currency of the code under audit:

- Unit 3 production files (`scripts/source_importer.py`, `scripts/source_fidelity.py`,
  `scripts/xmlreader_bridge.py`, `parsers/XmlReaderBridge/*`,
  `contracts/source-importer.unit3.json`) and `tests/test_unit3.py` are unchanged since
  `cc745c6`; schema/`source_schema.py` last changed at `087865e`. HEAD therefore equals
  the historical state for Unit 3.
- `scripts/source_query.py` changed at `76bdcf5` (Unit 4), `842ba45` (Unit 5) and
  `b7cc92e` (Unit 6). Unit 4 was audited against the historical `76bdcf5` blob (and
  re-checked at HEAD); Unit 6 `source_query.py` at HEAD is byte-identical to
  `b7cc92e` (SHA-256 `A2DF10BA82F43236BB88C576F855ECA1BCEBAC1658BA66E6D4C0070295F96077`
  for both), and `git diff b7cc92e HEAD` over it and `tests/test_unit6.py` is empty.
- None of the Unit 3, 4 or 6 contracts contains numbered acceptance criteria. Each
  matrix below is therefore an **audit-derived criterion matrix** built from the
  contract's explicit MUST / MUST NOT statements. Its IDs (`A3-nn`, `A4-nn`, `A6-nn`)
  are audit-assigned and are not original contract IDs.


# Unit 3

## Contract Responsibility

`docs/architecture/UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md`: import the one
pinned Matthew file through the authoritative .NET `XmlReader` into schema v2 with a
lossless generic ledger, typed nullable mirrors, ancestry-derived membership and two
fidelity channels (BYTE and NORMALIZED), atomically published, without a semantic
layer.

## Audited Checkpoint

`cc745c6` (parent `087865e`, as the contract requires). 14 paths changed. Contract
parent requirement matches git.

## Production Inspection

(Class C) `Program.cs`: `XmlReader.Create` with DtdProcessing=Prohibit,
XmlResolver=null, CheckCharacters on, all Ignore flags off, XInclude rejected; Text /
Whitespace events coalesce, CDATA/comment/PI stay distinct. No `XmlPro`, `lxml`, HTML
decoding, case folding, trimming or Start/End arithmetic. Attribute lookup is by exact
key; `xml:id` is recognised by namespace. Membership is computed from the actual
element stack ancestry. The importer opens a dedicated connection, `BEGIN IMMEDIATE`,
rolls back on active failure, links (`os.link`) a closed completed candidate into place
without overwrite, and rejects protected-repository output targets.

## Independent Raw-Source Oracle

(Class A) `minidom` over the raw bytes, never production code, compared with the
existing real DB:

- Archived BLOB equals the raw bytes (length 14,115,918, same SHA-256).
- Generic XML ledger: 59,891 elements, 767,429 attributes and the ordered content
  (including 2 comments and the document-level newline text). Raw-derived and DB-derived
  ledger digests are identical; 0 mismatches.
- Relational facts: 1,134 sentences, 1,134 trees, 56,488 nodes (parent, sibling,
  typed attributes with absent -> NULL) all match. All 18,329 token rows match
  (canonical and tree-leaf ordinals, chapter/verse/word, `xml:id`, direct text and 30
  typed attributes). The 159,391 ancestry-derived membership pairs match exactly.
- Oracle and DB relational digests are identical:
  `F762243E144C1799EC3458EB2F1670A2A411F5E1C7D1FBEFAF968142B4F2D87D`.

## Parser Boundary

(A/B/C) Beyond the code inspection above, the production bridge was exercised on
disposable inputs and raised `ImportFailure` for: malformed XML, a DOCTYPE, XInclude,
an invalid character, a duplicate attribute, an undeclared prefix and bad encoding.
Source facts established independently: CRLF line endings (101,458 CR bytes), no CDATA,
DOCTYPE or xmlns; the only entities are 96 `&quot;`; text is LF-folded by `XmlReader`
and `minidom` alike.

## Byte Archive Fidelity

(A) Production CLI on the real DB (read-only):
`python -B -m scripts.source_fidelity --database <real DB> --archive-output C:\Temp\audit346\archive.xml --normalized-output C:\Temp\audit346\normalized.xml`
returned BYTE PASS. The archive export is byte-identical to the source (SHA-256
`FE1A8FED...C40F4`, 14,115,918 bytes). A 1-byte source drift on a copy produces
"BYTE fidelity failed".

## Full-Matthew Normalized Fidelity

(A) Same CLI run: NORMALIZED PASS, logical digest
`F2A4A7C42FB3828B46B29DF388D583D497959CBD9B5E65CDAD876F7A85878A72`. The normalized
export (14,013,952 bytes, SHA-256
`D94127C809C5F1A4BFCEF0AD18A2D820B40805E7DABF4664650016E40F93F14E`) is not
byte-identical to the original, as the contract expects, but my independent `minidom`
ledger of that export equals the raw-source ledger
(`CCD0165657B8E162E202E6031E284FCA9CBA3278FCCAEEBE1DC22992BECA9A4C`, 59,891 elements).

## Matthew 1:1

(A) 1 Tree, 26 Nodes, 25 Node-to-Node relations, 8 leaves (all noun); `ClType=Verbless`
only on node `400010010010082`. The final token has surface and Unicode `Ἀβραάμ.` but
NormalizedForm `Ἀβραάμ`; the three surface fields stay separate in the DB.

## Matthew 1:2 Exact Membership

(A) Node `400010020050040`: Start=5, End=8, Head=1, Length=4, `Rule=S-V-O`. Raw
ancestry gives member tokens [5,7,8,9]; the DB membership (canonical order) is
identical; token 6 is numerically inside the Start/End span but is not a descendant
and is excluded. Tree-leaf ordinals are 1:2!5 -> 5 and 1:2!6 -> 4 while canonical
ordinals are 4 and 5, so the dual orders are stored independently.

## Missing vs Present-Empty

(A) 15,827 raw attributes carry empty values (Type 12,444; Mandarin 2,734; English 603;
LexDomain 23; LN 23); the generic rows and typed columns preserve `""`, and absent
facts are NULL, distinct from `""`.

## Namespace / Case / Identifier Fidelity

(A) 1,999 tokens carry both lowercase `ref` and uppercase `Ref`, stored in separate
columns; refs are unique (18,329). `FunctionalTag` differs from `FormalTag` on 215
tokens. `nodeId` (source node identity) and `Id` are separate; `xml:id` is stored by
namespace, not by prefix.

## One-Character Greek

(A) 733 one-character tokens in the raw source equal 733 in the DB; `MAT 1:16!13`
direct text `ὁ` is identical in both and passes through the production reader. No
empty direct-text leaf exists.

## PK Independence

(B) A store was built from the real Matthew 1:2 sentence (`MAT 1:2!1-1:6!7`) through
production `_populate`, then a second store with every surrogate PK remapped (element
1 -> 1001, node 1 -> 301, token -82 -> -7859). Both pass `verify_fidelity`; the
production logical digest is equal across the two (prefix `AAA444C92A7CC9EF`), as are
the 1:2 membership [5,7,8,9] and all token facts excluding PKs.

## Fail-Closed / Transactional Behavior

(B on disposable copies; C; D) Deleting a membership row makes `verify_fidelity`
raise SchemaError ("incomplete/incorrect ancestry membership"); source drift raises a
BYTE failure; parser failures raise `ImportFailure`. Atomic publication, overwrite
refusal and protected-output rejection are code-inspected (`source_importer.py`) and
covered by `test_u3_14`..`test_u3_17`, which passed.

## Immutability

(B) On a default writable connection UPDATE/DELETE are trigger-rejected on every table
except `node_token_membership` DELETE (the documented Unit 2 Amendment 1 design: no
per-row ancestry trigger; the mandatory validator catches it, proven above).
`INSERT OR REPLACE` on `token` remains possible (documented residual F-2; covered by
`test_u3_18`). The published consumer profile (`mode=ro` + `query_only`, via
`open_readonly`) rejects INSERT, UPDATE, DELETE, CREATE, DROP and INSERT OR REPLACE,
including with `query_only=OFF`.

## Tests Actually Run

All with `$env:PYTHONDONTWRITEBYTECODE=1` and `python -B`, from the repository root
at HEAD (equal to the historical state for Unit 3):

- `python -B -m scripts.verify_unit1` -> rc 0 (source SHA matches; primary 26
  nodes/25 relations/8 tokens/0 verbs/Verbless; boundary pair [6,5], members
  [5,7,8,9], excluded 6).
- `python -B -m scripts.source_schema` -> rc 0, schema version 2.
- `python -B -m unittest discover -s tests -p "test_unit3.py" -v` -> one fresh full
  build in TEMP (85.5 s with .NET 9.0.12); 23 tests, 22 passed, 0 failures, 0 errors,
  1 skipped (`test_u3_01`, the explicit second-build gate, deliberately not run). The
  fresh build's logical digest equals the existing DB's `F2A4...8A72`
  (corroboration only; no second-build determinism claim is made).
- Production fidelity CLI on the real DB (above).

`MACULA_UNIT3_SECOND_BUILD` was not set.

## Acceptance Criteria Matrix

Audit-derived (the contract has no numbered ACs).

| ID | Requirement (source: contract section) | Result | Evidence | Class |
|---|---|---|---|---|
| A3-01 | Only the pinned source (revision, SHA, 14,115,918 bytes) is production input (Frozen baseline) | PASS | Source SHA/size recomputed; macula-greek HEAD recorded | A |
| A3-02 | Authoritative `XmlReader` with the stated settings; failures are explicit (Parser) | PASS | Code inspection + 7 negative inputs | B, C |
| A3-03 | Text/CDATA/comment/PI preserved; no trim/normalisation (Parser) | PASS | Ledger digest equality; 2 comments; 0 mismatches | A |
| A3-04 | Exact original BLOB archived; BYTE channel (Fidelity) | PASS | Archive export SHA equals source | A |
| A3-05 | Complete element/attribute/ordered-content ledger (Import) | PASS | 59,891 / 767,429 / ordered content, 0 mismatches | A |
| A3-06 | Typed fields are nullable mirrors; absent vs present-empty preserved (Import) | PASS | 15,827 empty attributes preserved; NULL != "" | A |
| A3-07 | `ref`/`Ref`, the four IDs, both tags and enrichment stay separate (Import) | PASS | 1,999 dual-case tokens; 215 tag differences | A |
| A3-08 | Leaf text is direct text only; one-character Greek intact (Import) | PASS | 733 = 733; `MAT 1:16!13` `ὁ` | A |
| A3-09 | Tree traversal and canonical ranks stored separately (Import) | PASS | 1:2!5/!6 dual ordinals | A |
| A3-10 | Membership from actual ancestry; Start/End never an envelope (Import) | PASS | 159,391 pairs exact; 1:2 [5,7,8,9] excludes 6 | A |
| A3-11 | NORMALIZED channel independent of original BLOB; export re-parses to source facts (Fidelity) | PASS | NORMALIZED PASS; independent ledger of the export equals raw ledger | A |
| A3-12 | Logical digest excludes surrogate PKs and layout (Determinism) | PASS | PK-remapped store digest equal; fresh-build digest equals DB digest | B, D |
| A3-13 | Counts: 59,891 / 767,429 / 179,675 / 1,134 / 56,488 / 18,329 / 159,391 / 733 (Determinism) | PASS | Independent oracle counts | A |
| A3-14 | Schema/fidelity failure never publishes; atomic no-overwrite publication; protected outputs refused (Import) | PASS | Code inspection; `test_u3_14`..`17` passed; disposable-copy failures | B, C, D |
| A3-15 | Published consumers read-only; F-2 not erased (Fidelity) | PASS | Read-only profile probes; F-2 residual confirmed and documented | B, D |
| A3-16 | No semantic layer, no network, no other books/editions (Scope) | PASS | Code inspection; no such code present | C |

## Findings

- **BLOCKER:** none.
- **MAJOR:** none.
- **MINOR:** none.
- **INFORMATIONAL:**
  - **I3-1:** `node_token_membership` DELETE is not trigger-blocked on a writable
    connection. This is the documented Unit 2 Amendment 1 design; the validator detects
    it (verified). Whether that design is acceptable is a Unit 2 Amendment matter and is
    not decided here.
  - **I3-2:** F-2 (`INSERT OR REPLACE` by a default writable connection) remains an
    acknowledged, documented, tested residual.
  - **I3-3:** `encoding_evidence` is a constant string rather than a per-file
    measurement.
  - **I3-4:** The in-repo "independent" reference parser is Python Expat. My `minidom`
    oracle is a second, separately coded route, but it also rests on Expat; the
    byte-level truth is anchored by the exact-byte BLOB/SHA channel, not by parser
    diversity alone.

## Decision

**Unit 3: ACCEPT.** The existing DB is faithful to the raw source on every independently
derived axis, including byte, normalized, relational and membership fidelity.


# Unit 4

## Contract Responsibility

`docs/architecture/UNIT-4-MATTHEW-QUERY-SLICE.md`: exactly two read-only, caller-path
capabilities, `get_verse(db_path, book_code, chapter, verse) -> VerseResult | None` and
`get_token(db_path, ref) -> TokenResult | None`, returning frozen source-faithful facts
in canonical scripture order, with explicit not-found vs error semantics.

## Audited Checkpoint

`76bdcf5` (parent `cc745c6`). Audited from its `git archive` tree, then re-run at HEAD.

## Independent SQL Oracle

(A) `minidom`-derived expectations for all 26 source-mapped fields, plus surrogate IDs
from independent SQL (`token` join `syntax_node`), compared with the historical
production module:

- `get_verse` over **all 1,068 raw verses**: 0 mismatches.
- `get_token` over **all 18,329 raw tokens**: 0 mismatches.
- The identical run against the HEAD module: 0 / 0 mismatches.

## Verse Query

(A) 1:1 returns 8 tokens in order. All 1,068 verses match including token count/order.

## Exact Token Query

(A) `MAT 1:1!3`: Ἰησοῦ, lemma Ἰησοῦς, Genitive Masculine Singular Proper, StrongNumber
2424, N-GSM/N-GSM, cat noun, xml_id `n40001001003`, morph_id `40001001003`, nodeId
`400010010030010`; identical to independent SQL.

## Ordering

(A) The API orders by `verse_token_ordinal` (1:2: token 5 before 6) while the Tree
leaf order is 6 before 5; no node/row/Start/End/ancestry order is used.

## Surface vs Normalized

(A) Final 1:1 token: surface/Unicode `Ἀβραάμ.` and normalized `Ἀβραάμ` stay separate;
surface is never filled from another field; present-empty and absent values survive
the API unchanged.

## Not-Found / Error Semantics

(B) Returns `None`: absent token, verse or book, and lowercase `mat`. Raises
`QueryError`: malformed refs (`MAT 1:1`, leading zero, `!0`, empty, `None`, surrounding
whitespace, huge coordinate), invalid chapter/verse (0, -1, `True`, `'1'`, 2**63),
invalid book code (empty, whitespace, `None`), a missing path (message
"unable to open database file"; no file created), a non-SQLite file, a directory,
`user_version=1`, wrong identity hashes and a missing identity row.

## Read-Only Enforcement

(B) Through production `_open_readonly` on a disposable copy: `query_only=1`,
`foreign_keys=1`, `recursive_triggers=1`; INSERT/UPDATE/DELETE/CREATE/DROP/`PRAGMA
user_version` are rejected ("attempt to write a readonly database") and are still
rejected with `query_only=OFF`, so URI `mode=ro` is independently effective. The copy
hash is unchanged, no sidecars appear, and the connection is closed.

## Caller-Supplied Path

(C) No hard-coded DB path, environment lookup or drive path in `source_query.py`; no
build, migration or acquisition code.

## PK / Source Identity

(A, C) Surrogate IDs (`token_id`, `book_id`, `node_id`, `tree_id`, `element_id`) are
returned unchanged and equal independent SQL, which is exactly what the Unit 4
contract specifies ("Database surrogate IDs are returned unchanged"). Their later
exposure through Unit 5/6 is the separate, recorded Unit 5 M1 debt.

## Tests Actually Run

- Historical tree `C:\Temp\audit346\tree_76bdcf5` and HEAD, each with
  `MACULA_UNIT4_INTEGRATION=1` and `MACULA_UNIT4_DATABASE=C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3`:
  `python -B -m unittest tests.test_unit4.Unit4FastTests tests.test_unit4.Unit4MatthewIntegrationTests -v`
  -> 15 tests (11 fast + 4 integration), all OK, 0 skipped, in both trees.
- Audit oracle `u4_oracle.py` against historical and HEAD modules (above).

## Acceptance Criteria Matrix

Audit-derived (the contract has no numbered ACs).

| ID | Requirement (source: contract section) | Result | Evidence | Class |
|---|---|---|---|---|
| A4-01 | Exactly two query capabilities with the stated signatures; caller supplies path (Scope/API) | PASS | Source inspection; public names only `QueryError`, `TokenResult`, `VerseResult`, `get_token`, `get_verse` | C |
| A4-02 | Frozen DTOs, same representation for token and verse (Scope/API) | PASS | Dataclass inspection; shared model | C, D |
| A4-03 | Field mapping from the stated mirrors (Source field mapping) | PASS | 18,329 tokens x 26 fields, 0 mismatches | A |
| A4-04 | No trim/normalise/case-fold/substitute; absent `None`, present-empty `""` (Mapping) | PASS | Oracle + present-empty facts | A |
| A4-05 | Surface not filled from other fields; `Cat` stays a source category (Mapping) | PASS | 1:1 final token; `cat` equals source | A |
| A4-06 | Dedicated `mode=ro`, `query_only`, FK, recursive triggers; connection closed on every path (Connection) | PASS | Probe + tests | B, D |
| A4-07 | Schema v2 and identity gate; unopenable/non-SQLite/incompatible raise `QueryError` (Connection) | PASS | 10+ negative stores | B |
| A4-08 | Canonical scripture order, not node/row/tree order (Ordering) | PASS | 1:2 order; all verses match | A |
| A4-09 | Exact BINARY ref; no case guessing; malformed input raises (Ordering) | PASS | Negative input matrix | B |
| A4-10 | Missing book/verse/token -> `None`; no fallback (Ordering) | PASS | `MAT 99:99`, `MAT 1:1!999`, lowercase `mat` | B |
| A4-11 | Multiple snapshots/ambiguous book or token identity fail closed (Ordering) | PASS | Code inspection; `test_multiple_snapshot_book_identity_fails_closed` | C, D |
| A4-12 | No DDL, migration, archive scan or membership recomputation (Connection) | PASS | Code inspection; `test_query_uses_scripture_index_and_no_membership` | C, D |
| A4-13 | Surrogate IDs returned unchanged (API) | PASS | Equal to independent SQL | A |

## Findings

- **BLOCKER:** none.
- **MAJOR:** none.
- **MINOR:** none.
- **INFORMATIONAL:**
  - **I4-1:** Local surrogate IDs are part of `TokenResult` by contract; the later
    downstream concern is Unit 5 M1, not a Unit 4 violation.
  - **I4-2:** The identity gate is, by design, not a per-query full-fidelity check; Unit 4
    trusts Unit 3 validation (acknowledged in the contract).

## Decision

**Unit 4: ACCEPT.**


# Unit 6

## Contract Responsibility

`docs/architecture/UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md`:
`get_source_evidence(db_path, token_ref) -> SourceEvidence | None`, a frozen composition
of exact token (`TokenResult`), its source-facing leaf `NodeResult`, nearest-first
`ancestors` (excluding the leaf, root last), `parent_children` (direct children of the
immediate parent by sibling order, including the leaf), `membership_node` (immediate
parent, or the leaf for a root) and `contextual_members` (stored membership of that
node in scripture order); fail-closed on schema/identity/graph defects; read-only; no
semantic interpretation.

## Audited Checkpoint

`b7cc92e` (parent `842ba45`). The Unit 6 code and tests are byte-identical at HEAD, so
the audit used the HEAD module and cross-ran the historical tree export.

## Independent Composition Oracle

(A) `u6_oracle` built every expectation from the raw XML (`minidom`): leaf facts,
the Node-element ancestor chain, the parent's Node children in document order, the
membership node, and the descendant leaves of that node sorted by (chapter, verse,
token ordinal). For **all 18,329 raw leaves** it compared the full `SourceEvidence`
(token fields, node fields, every ancestor, every child, membership node, and every
contextual member with all its fields) with the production result from the historical
`b7cc92e` module: **0 mismatches**. Observed range: ancestor counts 2..23, contextual
member counts 1..82. No Matthew leaf is a Tree root (0 raw root leaves).

## Evidence Composition

(A) `MAT 1:1!3`: leaf `400010010030010` (cat noun); nine ancestors nearest-first with
(rule/ClType): `...030011` N2NP, `...030020`/`...030040`/`...030060` Np-Appos,
`...020070`/`...010080` NPofNP, `...010081` Np2P, `...010082` P2CL with
`ClType=Verbless`, `...010083` the source root `S`. `membership_node` is the immediate
parent `...030011` and its single member is `MAT 1:1!3`; `parent_children` is the leaf
alone.

## Ordering

(A) Ancestors are nearest first and root last; children follow `sibling_ordinal`
(0-based document order) rather than PK order; members follow scripture order. All
verified against raw document order for all 18,329 tokens.

## Exact Scope

(A) Node `400010020050040`: `S-V-O`, Start "5", End "8", Head "1", Length "4"; children
S `...050012`, V `...070012`, O `...080021` in sibling order. The stored membership
(Unit 5 `get_members`) is `MAT 1:2!5, !7, !8, !9`, excluding 6. Unit 6 does not promote
this to a higher ancestor: each leaf's `contextual_members` is the stored membership of
its own immediate parent (e.g. `MAT 1:2!8` -> parent `...080020` -> members 8, 9;
`MAT 1:2!6` -> its large parent `...010820`, which spans many verses and is listed
exactly as stored). Raw-derived descendant leaves equal the stored members everywhere.

## Error Propagation

(B) On disposable copies (immutability triggers dropped so corruption could be set up),
the production composition raised `QueryError` for: dangling parent of the leaf
("missing or cross-Tree syntax parent"); dangling parent of an ancestor; cross-Tree
parent; a cycle ("cyclic syntax ancestry"); duplicate source node ID between the leaf
and a sibling and between an ancestor and a node in another tree ("ambiguous
source_node_id within active Matthew snapshot"); NULL and empty source ID on the leaf
and NULL on a sibling ("linked syntax node has no source_node_id"). Never an empty
bundle. A known-empty stored membership returns `()` and a synthetic root leaf returns
`ancestors=()`, `parent_children=()`, `membership_node == node` as the contract states.
Unknown valid refs (`MAT 99:99!99`, `JHN 1:1!1`, lowercase `mat`) return `None`;
invalid refs (`MAT 1:1`, `MAT 01:1!1`, empty, `None`, leading space, `!0`) raise
`QueryError`. One observation (I6-1): when a token's `node_id` points at a node that
does not exist (only possible in a foreign-key-violating store), the composition
returns `None` because the Unit 4 token query inner-joins `syntax_node`.

## Read-Only Behavior

(B) With an authorizer installed on the production-opened connection for
`get_source_evidence(real DB, "MAT 1:1!3")`: action classes observed were only
SELECT (10), READ (274) and PRAGMA (4: `query_only=ON`, `foreign_keys=ON`,
`recursive_triggers=ON`, `user_version` read); no INSERT/UPDATE/DELETE/DDL/ATTACH/
TRANSACTION-write. One connection was used and it was closed after the call. The real
DB hash was unchanged and no sidecar appeared.

## Semantic Exclusion

(C) `SourceEvidence`, `NodeResult` and the composition code contain no
StructuralCandidate, confidence/probability, accepted/rejected, Actor/Action/Patient/
Event/Result, Identity/Property, copula or theological semantics (a keyword scan of
`source_query.py` matched only the type names and the mechanical DB-identity check).
`NodeResult` carries raw source strings (`Start`/`End`/`Head`/`Length` as text) and no
interpretation.

## PK / Source Identity

(A, C) `NodeResult` is source-facing (source node IDs only, no local PK). `TokenResult`
inherits local PKs from Unit 4, which is the recorded, unresolved Unit 5 M1 and is
acknowledged in the Unit 6 contract; it is not a Unit 6 defect. The existing
PK-reallocation test passed. Every composed node/ancestor/child is also required to
resolve uniquely in the active Matthew snapshot.

## Tests Actually Run

- Historical tree `C:\Temp\audit346\tree_b7cc92e` and HEAD, with
  `MACULA_UNIT6_INTEGRATION=1` and `MACULA_UNIT6_DATABASE=C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3`:
  `python -B -m unittest tests.test_unit6.Unit6FastTests tests.test_unit6.Unit6MatthewIntegrationTests -v`
  -> 22 tests (19 fast + 3 integration), all OK, 0 skipped, in both trees.
- Audit oracle (all 18,329 tokens), authorizer/corruption probes and the Matthew 1:1/1:2
  spot checks above.

## Acceptance Criteria Matrix

Audit-derived (the contract has no numbered ACs).

| ID | Requirement (source: contract section) | Result | Evidence | Class |
|---|---|---|---|---|
| A6-01 | Single public `get_source_evidence`, frozen `SourceEvidence` with the six fields (API) | PASS | Source inspection | C |
| A6-02 | Exact Unit 4 token composed unchanged (API/Boundaries) | PASS | 18,329 tokens, 0 mismatches | A |
| A6-03 | Leaf `NodeResult` with exact raw source strings, absent `None` (Boundaries) | PASS | 18,329 leaves, 0 mismatches | A |
| A6-04 | Ancestors nearest-first, root last, leaf excluded (Boundaries) | PASS | Depths 2..23 all match; 1:1!3 nine ancestors | A |
| A6-05 | `parent_children` = parent's direct children by sibling order, including leaf (Boundaries) | PASS | All tokens; sibling vs PK order test | A, D |
| A6-06 | `membership_node` = immediate parent (leaf for a root); not promoted (Boundaries) | PASS | All tokens; `...050040` kept distinct from leaf parents | A |
| A6-07 | `contextual_members` = stored membership in scripture order; empty known membership is `()` (Boundaries) | PASS | All tokens (1..82 members); emptied-membership probe | A, B |
| A6-08 | Root token: `ancestors=()`, `parent_children=()` (API) | PASS | Synthetic root probe + test (no Matthew root leaf exists) | B, D |
| A6-09 | Unknown valid ref -> `None`; invalid ref -> `QueryError` (Failure semantics) | PASS | Negative matrix | B |
| A6-10 | Schema/identity/missing-parent/missing-source-ID/duplicate/cycle failures raise, never empty evidence (Failure semantics) | PASS WITH FINDING (I6-1) | 8 corruption scenarios; I6-1 on a FK-violating missing token-node link | B |
| A6-11 | Read-only `mode=ro` + `query_only`; owned connection closed; no writes/caches/XML (Read-only) | PASS | Authorizer trace; tests | B, D |
| A6-12 | No semantic interpretation or candidate vocabulary (Scope) | PASS | Code scan | C |
| A6-13 | Source-facing node identity; local PKs only via inherited `TokenResult` (Boundaries) | PASS WITH FINDING (I6-2, Unit 5 M1) | DTO inspection; PK-realloc test | C, D |
| A6-14 | Active-snapshot restriction; multiple snapshots fail closed (Failure semantics) | PASS | Code inspection; `test_multiple_matthew_snapshots_fail_closed` | C, D |

## Findings

- **BLOCKER:** none.
- **MAJOR:** none.
- **MINOR:** none.
- **INFORMATIONAL:**
  - **I6-1:** A token whose `node_id` references a missing node (only reachable by
    violating the schema's foreign key) yields `None` instead of `QueryError`, because
    the accepted Unit 4 token query inner-joins `syntax_node`. The Unit 6 contract names
    missing source identities and parents, not a missing token-to-node row; a validated
    store cannot exhibit this.
  - **I6-2:** `TokenResult` still exposes local PKs (inherited Unit 5 M1, unresolved and
    out of scope).
  - **I6-3:** The source-ID resolver scans the full `syntax_node_upstream` index per
    node (about 2.7 ms each; roughly 12 resolutions per call), so the all-token oracle run
    took about 3,581 s end to end. This is a performance observation, not a correctness
    issue.
  - **I6-4:** Root-token behaviour could be exercised only synthetically because the
    Matthew source has no leaf that is a Tree root.

## Decision

**Unit 6: ACCEPT.**


# Existing Independently Accepted Units

These Units were not re-audited and are not re-accepted here.

## Unit 1

Recorded `IMPLEMENTED / INDEPENDENTLY ACCEPTED`; audit
`docs/audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md`. Its verifier
`python -B -m scripts.verify_unit1` was run only as a regression gate (rc 0).

## Unit 2

Recorded `IMPLEMENTED / INDEPENDENTLY ACCEPTED` (original schema-v1 checkpoint); audit
`docs/audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md`. **Unit 2
Amendment 1 (schema v2, `087865e`) is recorded only as `IMPLEMENTED` and is NOT accepted
by this audit.** Unit 3 was judged on the observable fidelity of its output and the
behaviour of the frozen schema-v2 baseline, not on the merits of removing the
membership ancestry trigger (see I3-1).

## Unit 5

Recorded `IMPLEMENTED / INDEPENDENTLY ACCEPTED` in `docs/governance/PHASE-STATUS.md`
with M1 unresolved; no Unit 5 audit file exists under `docs/audits/`. Not re-audited.
Its navigation primitives are exercised here only as inputs of Unit 6.

## Unit 7

Recorded `IMPLEMENTED / INDEPENDENTLY ACCEPTED` (ACCEPT WITH MINOR FINDINGS) by
`docs/audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md`; its own
M1 (unreconstructable pre-implementation contract bytes) remains unresolved. Not
re-audited, re-accepted or rejected.

## Unit 7 Dependency Impact Assessment

**NO REAUDIT REQUIRED / PRIOR ACCEPTANCE REMAINS VALID.** This is a narrow premises
review only.

- `git diff --name-status b7cc92e HEAD` shows no change to any Unit 3, 4 or 6 source,
  schema or test file (only the Unit 7 additions, the Unit 7 audit and governance/README
  text).
- Unit 7 (`scripts/structural_candidates.py`) depends on `get_source_evidence`,
  `_open_syntax_readonly`, `_resolve_source_node_id`, `_members` and `_token_key`.
  All of these were found conformant here (all 18,329 evidence bundles equal the raw
  oracle).
- The Unit 7 audit's informational item I4 states that broad membership correctness
  "rests on the still pending Unit 3 acceptance". That premise is now independently
  supported: all 159,391 stored membership pairs equal the raw ancestry, and the
  Matthew 1:2 [5,7,8,9] scope was re-derived. The Unit 7 audit's I5 (hard-coded `MAT`)
  and M1 are untouched.
- No contradiction with any Unit 7 premise (membership, exact scope, read-only query,
  evidence composition, source snapshot data, DB immutability) was found. Unit 7 tests
  were not rerun.


# Cross-Unit Findings

- **X-1:** The Unit 3 acceptance is conditioned on the frozen schema-v2 baseline as
  delivered; Unit 2 Amendment 1 itself remains un-accepted. Its membership-trigger
  removal is compensated in practice by the mandatory validator, which this audit
  demonstrated.
- **X-2:** Unit 5 M1 (PK exposure through `TokenResult`) spans Units 4, 5 and 6 and is
  neither remediated nor reclassified here.
- **X-3:** Stale historical wording remains in the contracts (for example, Unit 4 says
  Unit 5 is not started; Unit 6 says Units 3 and 4 are pending). These reflect their
  checkpoint dates and are left unchanged.
- **X-4:** `_resolve_source_node_id` hard-codes book `MAT` (inherited Unit 5 behaviour,
  also Unit 7 I5).


# Existing Database Preservation

`sblgnt-matthew.sqlite3` was opened only `mode=ro` (or hashed with shared read access);
all write/corruption tests used disposable copies.

| Check | BEFORE | AFTER (before commit) |
|---|---|---|
| Size | 160,968,704 | 160,968,704 |
| SHA-256 | `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E` | identical |
| `user_version` | 2 | 2 |
| Journal mode | delete | delete |
| Catalog objects / digest | 75 / `7437bb4a...23eb` | identical |
| WAL/SHM/journal sidecars | none | none |

The DB is untracked (ignored) and was not committed.


# Protected Repository Preservation

- `C:\Works\macula-greek`: `main`, `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, clean,
  unchanged.
- `C:\Projects\bible-research-merged`: `master`, `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`,
  only the pre-existing ignored items, unchanged.
- Primary repo: no tracked file changed other than this new report; no checkout, reset
  or detach was performed.

Two pre-existing `macula-unit3-*` directories in the user TEMP folder date from an
earlier day than this audit and were not created or touched by it.


# Scope Confirmation

This audit did not: change production, test, schema or contract files; touch
`docs/governance/PHASE-STATUS.md`, `README.md` or `docs/architecture/README.md`; run
the second full Unit 3 build; implement or design Unit 8, candidate evaluation or
persistence; add semantic roles or BRW integration; modify XmlPro, `macula-greek` or
`bible-research-merged`; rebuild the full NT, import N1904/companions or use the
network; fix Unit 5 M1 or Unit 7 M1; re-audit Units 1, 2, 5 or 7; or accept Unit 2
Amendment 1.


# Governance Implications

Governance reconciliation: **DEFERRED TO NEXT TASK PER USER DIRECTION.** None of the
following has been applied. Given the decisions above, the next task should apply:

1. `docs/governance/PHASE-STATUS.md`: change the Unit 3 (line 63), Unit 4 (line 105) and
   Unit 6 (line 253) status lines from `IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE` to
   `IMPLEMENTED / INDEPENDENTLY ACCEPTED`, each referencing this report
   (decision ACCEPT, no findings above INFORMATIONAL). Leave Unit 2 Amendment 1 (line
   50) as `IMPLEMENTED`; leave Unit 5 M1 and Unit 7 M1 unresolved.
2. `README.md`: update the Unit 3 (line 17), Unit 4 (line 18) and Unit 6 (line 24)
   status lines, and the sentence at line 215 that says Unit 6 remains pending.
3. `docs/architecture/README.md`: update the Unit 6 status (line 25) and the sentence at
   line 56 that says Units 3 and 4 remain pending.
4. Contract status headers (`UNIT-3-...md`, `UNIT-4-...md`, `UNIT-6-...md`, line 3 of
   each) may be updated to the accepted state, keeping their checkpoint-dated historical
   notes.
5. Optionally note, without editing the Unit 7 audit, that its I4 premise is now
   independently corroborated by this audit.
6. Re-run `grep -n "PENDING INDEPENDENT ACCEPTANCE"` over those files afterwards to
   confirm only Unit 2 Amendment 1 wording (if any) remains outstanding.


# Final Statement

Unit 3: ACCEPT. Unit 4: ACCEPT. Unit 6: ACCEPT. Each was judged on its own
responsibility using independently derived evidence (raw-XML and SQL oracles over the
complete Matthew data), with tests used only as regression support. Unit 7's prior
acceptance remains valid; Unit 2 Amendment 1, Unit 5 M1 and Unit 7 M1 are unchanged.
Governance reconciliation is deferred to the next task. No Unit 8, candidate
evaluation/persistence, semantic role mapping, BRW integration, schema change or
production repair was introduced.
