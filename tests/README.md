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

## Unit 4

Fast tests do not open or require the full-Matthew local artifact:

```powershell
python -B -m unittest tests.test_unit4.Unit4FastTests -v
```

The 11 fast tests bootstrap tiny temporary schema-v2 fixtures using the existing
Unit 2 SQL fixture helper. They cover scripture versus traversal/row order, shared
verse/token models, raw morphology/identity/text/tag/gloss distinctions, absence
versus empty, exact/case-sensitive lookup, invalid arguments, not-found, missing/
incompatible stores, ambiguous snapshots, existing index use and no ancestry query.
INSERT/UPDATE/DELETE are attempted only on temporary fixtures and rejected by SQLite
both with and without `query_only`, independently proving URI `mode=ro`.

Optional full-Matthew integration uses only an already existing file:

```powershell
$env:MACULA_UNIT4_INTEGRATION = "1"
$env:MACULA_UNIT4_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit4.Unit4MatthewIntegrationTests -v
Remove-Item Env:MACULA_UNIT4_INTEGRATION
Remove-Item Env:MACULA_UNIT4_DATABASE
```

Without the opt-in flag or an existing database, the 4 integration tests skip.
They verify all Matthew 1:1 refs/surfaces, lemmas, punctuation versus normalized,
Matthew 1:2 canonical order against reversed traversal, exact `MAT 1:1!3`
morphology, and not-found behavior. They never call an importer or attempt writes.
The production query API does not contain this local path.

For Unit 4's zero-full-build validation, Unit 3 was run with an external in-memory
class-setup override reusing the existing read-only database, fresh complete
schema/source-fidelity validation, temporary small parser regressions, the retained
second-build skip, and a guard forbidding full-source population. All 22 selected
tests passed; no full build occurred. This is not an independent acceptance.
Do not use ordinary Unit 3/all-test discovery for a zero-build task: its unchanged
default setup constructs a complete Matthew database.

## Unit 5

Fast tests use only tiny temporary schema-v2 stores and the existing Unit 2 manual
SQL fixture helper. No full Matthew database, XML importer, .NET build or network
is needed:

```powershell
python -B -m unittest tests.test_unit5.Unit5FastTests -v
python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests -v
```

The 16 fast tests cover exact zero/one/multiple source-ID resolution, no surrogate or
other-ID fallback, opaque parent identities, raw/empty/missing DTO values,
direct sibling order deliberately opposite PK order, nearest-first ancestry
excluding self, exact Unit 4 token entry, cycle/dangling-parent errors, exact
membership `[5,7,8,9]` excluding 6, leaf self-membership, scripture order across
verses, missing Head, SQLite URI read-only enforcement and unchanged schema.
Equivalent manual stores explicitly allocate different node and token PKs;
public node navigation and source-level member facts must remain identical.
Destructive negative tests operate only on these temporary stores.

Optional full-Matthew integration independently compares navigation with the pinned
upstream XML as a test oracle, never as the production query backend:

```powershell
$env:MACULA_UNIT5_INTEGRATION = "1"
$env:MACULA_UNIT5_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit5.Unit5MatthewIntegrationTests -v
Remove-Item Env:MACULA_UNIT5_INTEGRATION
Remove-Item Env:MACULA_UNIT5_DATABASE
```

The 4 integration tests require the opt-in flag and an already existing database;
otherwise they skip with reason `opt-in read-only existing full-Matthew integration`.
They verify `MAT 1:1!3`'s source ancestor chain and Verbless clause, Matthew 1:2
direct S/V/O children, Head=1, exact membership/excluded 6, root/leaf absence and
not-found. Byte size, SHA-256 and schema/index inventory must match before/after.
The ignored database is neither copied nor rebuilt nor committed.
For Unit 1-4 regression validation, use the documented external Unit 3 read-only
setup override rather than ordinary discovery. Retain the explicit second-build
slow-gate skip; neither reuse nor implementation tests are independent acceptance.

## Unit 6

```powershell
python -B -m unittest tests.test_unit6.Unit6FastTests -v
python -B -m unittest tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests tests.test_unit6.Unit6FastTests -v
```

Synthetic tests manually construct tiny temporary schema-v2 stores. They verify
frozen composition, exact source identities/facts, explicit not-found/failure
semantics, leaf/root behavior, nearest-first ancestry, immediate-parent child order
opposite PK order, named membership scope, discontinuous members `[5,7,8,9]`
excluding 6, materialized rather than reconstructed membership, duplicate source
identities, cycles/missing parents, and unchanged SQLite schema/bytes.
Equivalent stores reallocate all five inherited token surrogate IDs and compare
all other token facts, node facts, ancestry, children and member identity/order.
Local PK variance is tested separately; Unit 5 M1 remains unresolved.
SQLite rejects writes even with `query_only=OFF`; production composition uses one
owned read-only connection and closes it on success, not-found and failure.

```powershell
$env:MACULA_UNIT6_INTEGRATION = "1"
$env:MACULA_UNIT6_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit6.Unit6MatthewIntegrationTests -v
Remove-Item Env:MACULA_UNIT6_INTEGRATION
Remove-Item Env:MACULA_UNIT6_DATABASE
```

The 3 opt-in integration tests otherwise skip explicitly. Fixed expected source
facts verify `MAT 1:1!3`, nine ancestors, P2CL/Verbless and source root; Matthew
1:2 composition reaches `400010020050040` with raw S-V-O/5/8/1 facts. Existing
Unit 5 APIs inspect that higher ancestor's S/V/O children and `[5,7,8,9]`
membership (6 excluded), also checked against independently read pinned XML.
Unit 6's `contextual_members` remains its named immediate-parent membership,
not silently promoted to the clause. Database size/hash/version/catalog must match
before and after. XML is only a test oracle, never the runtime query backend.

For Unit 1-6 regressions reuse the existing database through the documented external
Unit 3 read-only setup override, fresh full fidelity validation and retained
second-build skip. Do not invoke default Unit 3 discovery and inadvertently rebuild
Matthew. This is implementation validation, not independent acceptance.

## Unit 7

```powershell
python -B -m unittest tests.test_unit7.Unit7FastTests -v
```

The 16 fast tests manually construct validated tiny schema-v2 stores. They verify
explicit Np-Appos-only self/nearest-first ancestry discovery, unrelated-node exclusion,
frozen typed candidate-only DTOs, ordered direct children/evidence, canonical exact
membership including discontinuities, Start/End independence, missing evidence,
unknown versus empty versus error, source ambiguity/cycles, snapshot provenance,
canonical identity bytes and SHA-256. Equivalent stores reverse node/token PK order
and reallocate all five inherited local IDs, plus snapshot/file IDs. Entire candidate
DTO equality must hold; inherited TokenResult variance remains explicit (M1 unresolved).
Controlled identity changes and separate processes/hash seeds/database locations
test versioning and reproducibility. Temporary read-only write attempts, SQL tracing,
connection closure, unchanged bytes/catalog/version and forbidden runtime XML prove
no source mutation or candidate persistence.

```powershell
$env:MACULA_UNIT7_INTEGRATION = "1"
$env:MACULA_UNIT7_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit7 -v
Remove-Item Env:MACULA_UNIT7_INTEGRATION
Remove-Item Env:MACULA_UNIT7_DATABASE
```

The 3 integration tests otherwise skip explicitly using the existing opt-in convention.
Fixed Matthew 1:1 expectations assert all three Np-Appos anchors, their ordered direct
children, exact token refs and repeatable identities. The clause remains Verbless,
with eight noun leaves and no invented verb/copula or semantic entity. The Unit 7
scope helper tests Matthew 1:2 node `400010020050040` membership `[5,7,8,9]`,
excluding 6, without deriving an S-V-O candidate. Size/hash/version/catalog must match.

For combined Unit 1-7 regressions, use the same external Unit 3 read-only class-setup
override, fresh exhaustive BYTE/NORMALIZED/schema/membership validation and logical
digest check, with a guard forbidding full Matthew population. Keep the existing
second-build slow-gate skip. Do not invoke default Unit 3 discovery for this zero-build
task. Implementation validation does not independently accept Units 3, 4, 6 or 7.
