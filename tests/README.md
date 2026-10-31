# Unit 1 Tests

Unit 1 tests should verify the frozen source contract against the read-only upstream checkout at `C:\Works\macula-greek`.

Required checks:
- revision/path/SHA-256
- Matthew 1:1 shape and attribute accounting
- verbless and surface/normalized invariants
- Matthew 1:2 ordering and discontinuous-membership counterexamples
- source field identity distinctions

Tests must not fetch or modify upstream data and must not create SQLite databases.

## Run

From `C:\Projects\MACULA-Extract`, using Python 3.10 or later and Git:

```powershell
python -B -m scripts.verify_unit1
python -B -m unittest discover -s tests -p "test_*.py" -v
```

No third-party dependencies or downloads are required. `-B` avoids Python bytecode files. The first command returns a JSON verification summary only on success; errors are explicit on stderr with a nonzero exit code. It never writes a report or regenerates expected values.

Tests T1–T8 cover the actual pinned source and both frozen fixtures. Negative regressions reject revision/root/path/checksum/allowlist/policy drift, fixture mutation, placeholders, changed head/verbless/surface, incorrect ordering/membership, duplicate JSON keys, and unauthorized XML expansion. Mutations use in-memory XML/bytes or mocks, never the upstream file.

The fixture assertions are independently anchored to the authorized counts, identities, surfaces, and boundary members in tests; editing expectations to accommodate a future implementation does not make those tests pass. Machine-readable F-01–F-10, field identity, seven ordering concepts, and the forbidden semantic mappings are also verified.

This is source-contract verification, not ingestion or normalized reconstruction. The architecture spike remains historical evidence and is not rewritten by these tests.
