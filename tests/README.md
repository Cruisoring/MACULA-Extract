# Verification Tests

Unit 1 tests should verify the frozen source contract against the read-only upstream checkout at `C:\Works\macula-greek`.

Required checks:
- revision/path/SHA-256
- Matthew 1:1 shape and attribute accounting
- verbless and surface/normalized invariants
- Matthew 1:2 ordering and discontinuous-membership counterexamples
- source field identity distinctions

Tests must not fetch or modify upstream data. Unit 1 tests do not create SQLite databases;
the separate Unit 2 authorization permits temporary schema-test databases only.

## Run

From `C:\Projects\MACULA-Extract`, using Python 3.10 or later and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_unit1.py" -v
```

No third-party dependencies or downloads are required. `-B` avoids Python bytecode files. The first command returns a JSON verification summary only on success; errors are explicit on stderr with a nonzero exit code. It never writes a report or regenerates expected values.

Tests T1–T8 cover the actual pinned source and both frozen fixtures. Negative regressions reject revision/root/path/checksum/allowlist/policy drift, fixture mutation, placeholders, changed head/verbless/surface, incorrect ordering/membership, duplicate JSON keys, and unauthorized XML expansion. Mutations use in-memory XML/bytes or mocks, never the upstream file.

The fixture assertions are independently anchored to the authorized counts, identities, surfaces, and boundary members in tests; editing expectations to accommodate a future implementation does not make those tests pass. Machine-readable F-01–F-10, field identity, seven ordering concepts, and the forbidden semantic mappings are also verified.

This is source-contract verification, not ingestion or normalized reconstruction. The architecture spike remains historical evidence and is not rewritten by these tests.

## Unit 2

```powershell
python -B -m scripts.source_schema
python -B -m unittest discover -s tests -p "test_unit2.py" -v
python -B -m unittest discover -s tests -p "test_unit[12].py" -v
```

Unit 2 uses standard-library sqlite3/unittest, SQLite 3.37+ with STRICT and JSON support.
No packages, .NET build or network restore are needed. The XmlReader profile is a
contract, not a parser executed by these Python tests.

The schema verifier uses memory only. Schema tests otherwise use in-memory databases;
one persistence test creates a uniquely named temporary directory inside this repository,
closes its database connections and removes the directory on exit.

Current amended schema-v2 Unit 2 suite: **56 tests**. Coverage includes:
- actual DDL, deterministic empty bootstrap/version, repeat/unknown/transaction failure and atomic rollback;
- PK/FK, BLOB/checksum/size, schema catalog identity, immutable rows including REPLACE;
- namespace/BINARY/prefix identity, attribute absence/empty/order and ref versus Ref;
- distinct IDs/tags/glosses/morphology/raw enrichment and typed/generic consistency;
- canonical source-scoped locators, aliases/repeated siblings, duplicate rejection and PK-independent identities;
- ordered direct text/CDATA/comment/PI/document content and canonical text segmentation;
- parent/sibling/leaf/book scope, separate traversal/canonical order and exact ancestry membership;
- post-load extra/sibling/missing/self-membership rejection, equal-count wrong sets,
  rollback, retained cross-Tree FKs and absence of any per-row ancestry INSERT trigger;
- genuine live `MAT 1:16!13` text `ὁ`, punctuation, combining Unicode and non-BMP text;
- explicit CLI failures, unsafe parser profiles and no semantic/mapper/parser implementation.

SQL fixture helpers are test-only manual data construction, not XML processing.
The boundary test independently reads current fixed Matthew values, then constructs a
reduced synthetic Tree preserving the decisive `[6,5]` order and `[5,7,8,9]` ancestry.
Its local traversal ordinals start at zero; copied source Start/End retain their original
values. It does not claim to ingest the complete containing sentence or Matthew file.
Other synthetic shape tests establish representability, not XML-byte-to-record equality.

`validate_store` verifies schema/catalog, BLOB hashes and the consistency/completeness of
the XML/core records supplied to it, including complete ancestry membership equality
in both directions. Unit 3 establishes pinned-source parsing coverage and independent
normalized round-trip fidelity; Unit 2 validation alone does not certify it.

## Unit 3

```powershell
python -B -m unittest discover -s tests -p "test_unit3.py" -v
python -B -m unittest discover -s tests -p "test_*.py" -v
```

Unit 3 uses Python standard-library SQLite/Expat/unittest and the locally installed
.NET 9 SDK/runtime. The authoritative parser is actual System.Xml.XmlReader, not
ElementTree or Expat. Cleared NuGet sources prevent network dependency restoration;
all .NET intermediates and complete database builds are outside the repository.

The 23 Unit 3 tests use one shared complete production-style Matthew build by default,
exhaustive independent XML/core comparisons, an actual archived XML file and a
DB-only serialized reconstruction, all 733 single-character tokens, both frozen
Matthew regressions, namespace aliases/attributes/mixed content/empty CDATA,
BOM/UTF-16/combining/non-BMP text, parser failures/rollback/no publication,
protected-output/overwrite rejection, read-only consumption, PK/page-layout-independent
logical digests and F-2 consistent generic+typed tampering. Test 19 explicitly shifts
syntax-node surrogate PKs in its manual fixtures rather than assuming that archive/
element offsets also change SQLite-generated node IDs.

The second-build determinism test is retained with every original digest/parser/
completion assertion, but skipped by default as an explicit slow gate. To deliberately
request the second independent full build:

```powershell
$env:MACULA_UNIT3_SECOND_BUILD = "1"
python -B -m unittest discover -s tests -p "test_unit3.py" -v
Remove-Item Env:MACULA_UNIT3_SECOND_BUILD
```

Ordinary discovery runs the 22 other tests without implicitly constructing a second
Matthew database. Reconciliation may instead reuse a previously fully verified DB
through an external, read-only test fixture; current complete fidelity validation
and all selected assertions still run. Such reuse must be reported explicitly, not
claimed as a new full build or second-build determinism proof.

The tamper test intentionally uses a default writable SQLite connection (both PRAGMAs
initially OFF), performs matching REPLACE changes, restores the required verification
profile, observes the schema-v2 Unit 2 internal validator PASS, then requires the
independent original-source fidelity validator to FAIL. It does not weaken the
production build or published-consumer profile.
All connections close before temporary directories are removed; no DB/WAL/SHM/cache
or .NET bin/obj output should remain.
