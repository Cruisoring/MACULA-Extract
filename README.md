# MACULA-Extract

Independent project for building a versioned, fidelity-preserving linguistic source store from fixed MACULA Greek source artifacts.

## Current phase
MACULA Greek Linguistic Source Store Phase

Current authorized implementation scope: **Unit 1 only: Source Contract & Fixture Freeze**.

## Boundaries
- Upstream MACULA checkout is read-only evidence.
- SBLGNT `nodes` is the primary linguistic source for the authorized Matthew vertical slice.
- This project does not perform BRW semantic projection.
- Actor / Action / Patient / Event / Result interpretation is out of scope.
- No SQLite schema, importer, or exporter is authorized in Unit 1.

See `AGENTS.md`, `contracts/`, and `docs/governance/`.

## Unit 1 verification

Run from this repository with Python 3.10+ and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_*.py" -v
```

The verifier reads only the explicitly authorized upstream Matthew file, checks its Git root/revision and exact SHA-256, then checks the frozen fixtures. It does not acquire sources, normalize Greek, create databases, or update expectations. See [test instructions](tests/README.md), [fidelity constraints](docs/governance/FIDELITY-CONTRACT.md), and [phase status](docs/governance/PHASE-STATUS.md).
