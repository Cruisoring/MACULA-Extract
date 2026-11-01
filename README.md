# MACULA-Extract

Independent project for building a versioned, fidelity-preserving linguistic source store from fixed MACULA Greek source artifacts.

## Current phase
MACULA Greek Linguistic Source Store Phase

Unit 1: **IMPLEMENTED / INDEPENDENTLY ACCEPTED**.

Unit 2: **IMPLEMENTED / INDEPENDENTLY ACCEPTED WITH MINOR FINDINGS** - SQLite Source Schema & Parser Contract.
Independent decision: **ACCEPT WITH MINOR FINDINGS** ([audit](docs/audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
Phase remains **AUTHORIZED**; Unit 3 is not authorized or started.

## Boundaries
- Upstream MACULA checkout is read-only evidence.
- SBLGNT `nodes` is the primary linguistic source for the authorized Matthew vertical slice.
- This project does not perform BRW semantic projection.
- Actor / Action / Patient / Event / Result interpretation is out of scope.
- Unit 1's accepted contract, fixtures, verifier and tests remain unchanged.
- Unit 2 permits schema/bootstrap/contracts and temporary schema tests, not a production importer/exporter or populated source database.

See `AGENTS.md`, `contracts/`, and `docs/governance/`.

## Unit 1 verification

Run from this repository with Python 3.10+ and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_*.py" -v
```

The verifier reads only the explicitly authorized upstream Matthew file, checks its Git root/revision and exact SHA-256, then checks the frozen fixtures. It does not acquire sources, normalize Greek, create databases, or update expectations. See [test instructions](tests/README.md), [fidelity constraints](docs/governance/FIDELITY-CONTRACT.md), and [phase status](docs/governance/PHASE-STATUS.md).

## Unit 2 schema verification

Python 3.10+ and SQLite 3.37+ with STRICT/JSON support, using only local standard-library dependencies:

```powershell
python -B -m scripts.source_schema
python -B -m unittest discover -s tests -p "test_unit2.py" -v
```

The first command creates and validates an empty **in-memory** database, then closes it.
There is no production XML parser/importer, ingestion command, or database deliverable.

See the executable [DDL](schema/001-source-store.sql), [schema/identity documentation](docs/architecture/UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md),
[XmlReader profile](contracts/xmlreader-parser.unit2.json), and [locator contract](contracts/occurrence-locator.unit2.json).
