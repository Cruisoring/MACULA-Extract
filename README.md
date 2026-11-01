# MACULA-Extract

Independent project for building a versioned, fidelity-preserving linguistic source store from fixed MACULA Greek source artifacts.

## Current phase
MACULA Greek Linguistic Source Store Phase

Unit 1: **IMPLEMENTED / INDEPENDENTLY ACCEPTED**.

Unit 2: **IMPLEMENTED / INDEPENDENTLY ACCEPTED** - SQLite Source Schema & Parser Contract.
Independent decision: **ACCEPT WITH MINOR FINDINGS** ([audit](docs/audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Phase remains **AUTHORIZED**.

Unit 2 Amendment 1: **IMPLEMENTED** - schema version 2 uses post-load complete-set
membership validation instead of a per-row ancestry INSERT trigger.

Unit 3: **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE** - SBLGNT Matthew Source Importer & Fidelity Round-Trip.
Unit 4: **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE** - Read-Only Matthew Verse / Token Query Slice.
Unit 5: **NOT STARTED**; no later Unit or automatic independent acceptance is authorized.

## Boundaries
- Upstream MACULA checkout is read-only evidence.
- SBLGNT `nodes` is the primary linguistic source for the authorized Matthew vertical slice.
- This project does not perform BRW semantic projection.
- Actor / Action / Patient / Event / Result interpretation is out of scope.
- Unit 1's accepted contract, fixtures, verifier and tests remain unchanged.
- Unit 2 permits schema/bootstrap/contracts and temporary schema tests, not a production importer/exporter or populated source database.
- The later, separate Unit 3 authorization permits the exact pinned Matthew pipeline only.
  Unit 1, the amended schema-v2 Unit 2 baseline and historical independent audits
  are preserved; this checkpoint does not change them.
- The separate Unit 4 authorization adds only read-only verse/token queries over an
  existing schema-v2 store. It does not authorize another build, migration or Unit 5.

See `AGENTS.md`, `contracts/`, and `docs/governance/`.

## Unit 1 verification

Run from this repository with Python 3.10+ and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_unit1.py" -v
```

The verifier reads only the explicitly authorized upstream Matthew file, checks its Git root/revision and exact SHA-256, then checks the frozen fixtures. It does not acquire sources, normalize Greek, create databases, or update expectations. See [test instructions](tests/README.md), [fidelity constraints](docs/governance/FIDELITY-CONTRACT.md), and [phase status](docs/governance/PHASE-STATUS.md).

## Unit 2 schema verification

Python 3.10+ and SQLite 3.37+ with STRICT/JSON support, using only local standard-library dependencies:

```powershell
python -B -m scripts.source_schema
python -B -m unittest discover -s tests -p "test_unit2.py" -v
```

The first command creates and validates an empty **in-memory** database, then closes it.
That Unit 2 command does not run a production XML parser/importer or ingest data.

See the executable [DDL](schema/001-source-store.sql), [schema/identity documentation](docs/architecture/UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md),
[XmlReader profile](contracts/xmlreader-parser.unit2.json), and [locator contract](contracts/occurrence-locator.unit2.json).

## Unit 3 source fidelity pipeline

Python 3.10+, the locally installed .NET 9 SDK/runtime and Git; SQLite requirements
remain unchanged. There are no third-party package dependencies or downloads.
Use an existing temporary output directory; outputs must not already exist:

```powershell
python -B -m scripts.source_importer --output "$env:TEMP\matthew-source.sqlite3"
python -B -m scripts.source_fidelity --database "$env:TEMP\matthew-source.sqlite3" --archive-output "$env:TEMP\matthew-archive.xml" --normalized-output "$env:TEMP\matthew-normalized.xml"
python -B -m unittest discover -s tests -p "test_unit3.py" -v
```

The actual XmlReader importer stores the exact source-byte BLOB and complete generic/core
records. Publication requires schema-v2 validation, complete ancestry membership
set equality in both directions, and exhaustive independent Expat
source-versus-DB reconstruction equality. Byte export is distinct from normalized XML
serialization; normalized bytes need not reproduce the original lexical file.
Remove generated outputs when finished; no production database binary is a Git deliverable.
See the [Unit 3 contract](docs/architecture/UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md).
Default Unit 3 discovery shares one full Matthew build across the class. The
second-build determinism test remains an explicit slow gate; see [test instructions](tests/README.md).

## Unit 4 read-only source queries

The caller supplies an existing database path; no importer, network or .NET build
is run by these APIs:

```python
from scripts.source_query import get_token, get_verse

verse = get_verse(database_path, "MAT", 1, 1)
token = get_token(database_path, "MAT 1:1!3")
```

Results are immutable typed source facts. Missing verses/exact tokens return `None`;
invalid input, incompatible identity/schema and SQLite failures raise `QueryError`.
Verse tokens use canonical scripture order. Source text is not normalized or substituted.
Generated SQLite stays local and ignored; do not commit it or rebuild it for query tests.

```powershell
python -B -m unittest tests.test_unit4.Unit4FastTests -v
```

See the [Unit 4 query contract](docs/architecture/UNIT-4-MATTHEW-QUERY-SLICE.md)
for field mappings, read-only behavior and optional existing full-Matthew integration.
