# Unit 4 - Read-Only Matthew Query Slice

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.
Phase remains AUTHORIZED. Unit 3 remains pending independent acceptance.
Unit 5 is NOT STARTED; automatic independent acceptance is not authorized.

## Scope and API

[source_query.py](../../scripts/source_query.py) exposes exactly two query
capabilities over an existing schema-v2 source store:

```python
get_verse(db_path: str | Path, book_code: str, chapter: int, verse: int) -> VerseResult | None
get_token(db_path: str | Path, ref: str) -> TokenResult | None
```

The caller supplies the database path. There is no production local-path default,
build, migration, source acquisition, CLI, service, tree API or semantic projection.
Only the current Matthew store is validated as a product slice; other editions,
multiple snapshots and full NT are not supported by this checkpoint.

`VerseResult` is frozen and contains `book_code`, `chapter`, `verse` and an immutable
`tokens` tuple. `TokenResult` is frozen; both APIs return the same representation.
Database surrogate IDs are returned unchanged, not treated as scripture positions.

## Source field mapping

| Output | Existing source mirror |
|---|---|
| `token_id`, `book_id`, `node_id`, `tree_id` | Same-named token columns |
| `book_code` | `book.source_book_code` |
| `chapter`, `verse`, `verse_token_ordinal` | Same-named token scripture coordinates |
| `element_id`, `upstream_node_id`, `cat` | Same-named leaf syntax-node columns |
| `xml_id`, `morph_id` | Same-named token source identities |
| `ref` | `token.ref_raw` (source lowercase `ref`) |
| `surface` | `token.source_direct_text` |
| `unicode` | `token.unicode_raw` |
| `normalized` | `token.normalized_form` |
| `lemma` | `token.unicode_lemma` |
| `language` | `token.language_raw` |
| `case`, `gender`, `number`, `person` | Corresponding token `*_raw` columns |
| `tense`, `voice`, `mood`, `degree`, `type` | Corresponding token `*_raw` columns |
| `functional_tag`, `formal_tag`, `strong_number` | Same-named token columns |
| `english`, `mandarin`, `gloss` | Same-named separate token columns |
| `referent` | `token.referent_raw` (source uppercase `Ref`, not scripture `ref`) |

No source string is trimmed, normalized, case-converted, translated or substituted.
Absent optional facts remain `None`; present-empty facts remain `""`.
Surface is never filled from Unicode, normalized or lemma. No morphology is inferred.
`Cat` remains a source leaf category, not a semantic role.

## Connection and identity boundary

Reuse the existing Unit 3 consumer connection helper: SQLite file URI `mode=ro`,
`query_only=ON`, `foreign_keys=ON`, `recursive_triggers=ON`. Each API owns and closes
its dedicated connection, including on validation/query failure.

Before lookup, require `PRAGMA user_version=2` and the single schema identity row
(singleton 1, version 2, DDL/parser/locator hashes) matching the frozen Unit 2
identity helper. Preparing the full token SELECT verifies required book, token and
syntax-node tables/columns, even for a not-found query.
This is an identity/access gate, not a per-query full source-fidelity or membership
validation. No DDL, migration, archive scan or ancestry recomputation is performed.

Missing/unopenable/non-SQLite stores, incompatible versions/identity, missing query
columns and SQLite failures raise `QueryError`; they never become not-found.

## Ordering and exact/not-found policy

Resolve the exact BINARY source book code first. More than one matching book in
different snapshots raises `QueryError` rather than guessing an edition.
For a verse, use `token_scripture(book_id, chapter, verse, verse_token_ordinal)`
and `ORDER BY verse_token_ordinal`. Duplicate/non-increasing verse coordinates fail
explicitly. No node ID, row ID, XML traversal, Start/End or ancestry order is used.

Exact token input has coordinate form such as `MAT 1:1!3`: a non-whitespace book
code and positive decimal SQLite-integer chapter/verse/token coordinates without
leading zeroes. Malformed input raises `QueryError`. Verse arguments similarly
require a nonempty whitespace-free source code and positive integer coordinates
(not booleans). No case-insensitive identity guessing occurs.

The token query narrows by the same indexed scripture coordinates, then requires
exact BINARY `ref_raw` equality. Duplicate exact matches raise `QueryError`.
Missing book/verse/exact token returns `None`, including `MAT 99:99` and
`MAT 1:1!999`; no partial, nearest, fuzzy or empty-object fallback exists.

## Actual implementation validation

Required starting branch/HEAD and clean tracked state were verified:
`master`, `cc745c692a134cbdaef8c8d177c61e595b0ae31e`.
The repository already contained `*.sqlite3`; `git check-ignore -v` confirmed
`.gitignore:8:*.sqlite3`. No redundant ignore-pattern edit was needed.

The existing ignored `C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3` was used
only for read-only validation. Size before/after: **160,968,704 bytes**.
SHA-256 before/after:
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`.
No destructive test ran on this file. No generated SQLite is committed.

- Matthew 1:1: 8 tokens, exact refs `MAT 1:1!1` through `MAT 1:1!8`.
  First/third surface and lemma, StrongNumber 2424, and final surface punctuation
  versus normalized all passed.
- Matthew 1:2: scripture token 5 before 6; existing traversal has 6 before 5.
- Exact `MAT 1:1!3`: source Jesus surface/lemma, Genitive, Masculine, Proper, 2424.
- Missing verse/token: `None`. Temporary read-only INSERT/UPDATE/DELETE: rejected,
  even after disabling `query_only` (URI read-only remains enforced).
- Unit 1 verifier PASS; 26 Unit 1 and 56 Unit 2 tests PASS.
- Unit 3: 22 non-second-build tests PASS, one retained slow gate skipped, through
  external read-only fixture reuse with fresh exhaustive source-fidelity validation.
- Unit 4: 11 fast tests and 4 local integration tests PASS; final runs have zero
  failures/errors. Python 3.10 AST syntax checks passed. Pylance file checks could
  not resolve this repository outside the active editor workspace; no static
  type-check result is claimed.
- Full Matthew builds executed: **0**. Schema/index changes: **none**.

Measured single-call elapsed times, including connection/identity checks:

| Query | Elapsed |
|---|---:|
| Matthew 1:1 `get_verse` | 3.977 ms |
| Matthew 1:2 `get_verse` | 3.237 ms |
| `MAT 1:1!3` `get_token` | 2.639 ms |

Actual Matthew 1:1 token SELECT plan:

```text
SEARCH b USING INTEGER PRIMARY KEY (rowid=?)
SEARCH t USING INDEX token_scripture (book_id=? AND chapter=? AND verse=?)
SEARCH n USING INTEGER PRIMARY KEY (rowid=?)
```

The separate book-code lookup scans the covering book unique index; the current
store has one book row. The exact-token query searches `token_scripture` with all
four coordinates. There is no full token scan or ordering temporary B-tree.
No performance amendment/index or benchmark framework was needed.

See [test commands](../../tests/README.md#unit-4) for independent fast and opt-in
existing-file integration routes. These results are implementation validation,
not independent acceptance. STOP after the Unit 4 implementation checkpoint.
