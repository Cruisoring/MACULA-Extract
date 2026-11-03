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

The commands/evidence below describe the historical Unit 7 checkpoint. Unit 9
intentionally supersedes four no-S-V-O tests without editing this frozen test file;
use the filtered regression instructions in the Unit 9 section for current runs.

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

## Unit 8

The commands/evidence below describe the historical Unit 8 checkpoint. Unit 9
supersedes two no-S-V-O tests without editing Unit 8's tests or registry.
Current filtered regression instructions and replacement coverage appear below.

```powershell
python -B -m unittest tests.test_unit8.Unit8FastTests
python -B -m unittest tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests tests.test_unit6.Unit6FastTests tests.test_unit7.Unit7FastTests
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
```

The **50 fast tests** reuse Unit 7's small, validated synthetic-store fixture without
running its test class. They cover human accepted/rejected/undetermined records;
frozen literal candidate/evaluation identity vectors; independent V1 and public-API
V2; all seven snapshot fields; exact scope/evidence/payload shape and ordering;
malformed/altered identities; closed protocol/class/disposition/field vocabularies;
verbatim Unicode/whitespace and BCP 47 language tags; typed tuple rationale;
external/duplicate/misordered citations; explicit event keys, idempotence/reuse
conflicts, coexisting opposing evaluations, supersession chains/forks and invalid
predecessors; no PK identity; no source writes/sidecars; frozen DTOs; Verbless safety;
Matthew 1:2 envelope rejection; unknown exact candidate errors; error propagation;
process/hash-seed/path independence and complete output equality under PK reallocation.

Opt-in integration never builds or populates Matthew:

```powershell
$env:MACULA_UNIT8_INTEGRATION = "1"
$env:MACULA_UNIT8_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit8
Remove-Item Env:MACULA_UNIT8_INTEGRATION
Remove-Item Env:MACULA_UNIT8_DATABASE
```

The **1 read-only integration test** exercises actual Matthew 1:1 Apposition
candidates, the fixed nearest candidate id, all three nested source-grounded
records, Verbless/eight-noun safety and Matthew 1:2 exact membership. It checks
before/after DB hash, size, catalog and version, even if an assertion fails.
Without opt-in or an existing file it explicitly skips; a skip is not a pass.
Records are test-only `undetermined` evaluations, not historical human judgments.

Actual implementation validation from
`8f8b2e7642204378eb0e56e20d096b6233e409b2`: **51 Unit 8 PASS, 0 failures/errors,
0 skips** (50 fast + 1 opted-in integration); **62 Unit 4-7 fast PASS,
0 failures/errors/skips** (11/16/19/16); both verifiers PASS. Python 3.10 syntax and
current-runtime compilation checks PASS. No Unit 3/full-build gate was invoked.
The single implementation checkpoint has that sole parent; Git's resulting SHA is
reported after creation. Implementation validation is not independent acceptance.
The [Unit 8 API/DTOs and frozen vector](../docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation)
remain in-memory only, with no persistence, semantic roles, confidence, BRW,
source-schema changes or Unit 9. Unit 5 M1 and Unit 7 audit M1 remain unresolved.
Unit 8 is **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**; Phase remains AUTHORIZED.

## Historical Unit 9 design/fixture freeze

At the freeze checkpoint Unit 9 was **DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED**.
Production implementation was **NOT YET PERFORMED**; no `tests/test_unit9.py` or
Unit 9 implementation tests existed then. The following subsection supersedes
that status, without changing frozen expected data.

The [expected fixture](../fixtures/matthew-1-2-svo-candidate.expected.json) was
frozen only after separate raw-XML and read-only direct-SQLite oracles agreed on
Matthew 1:2 anchor `400010020050040`, Rule `S-V-O`, raw Head `1`,
source-ordered S/V/O children and all four exact membership tuples:
S=`("MAT 1:2!5",)`, V=`("MAT 1:2!7",)`, O=`("MAT 1:2!8", "MAT 1:2!9")`,
anchor=`("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")`.
Token 6 is excluded. No production helper computed the expected memberships or ID.
The [freeze evidence](../docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#27-authorized-component-membership-freeze-evidence)
records the final fixture SHA-256, canonical expected candidate identity and M1-M8.

**8 independent disposable-store controls PASS, 0 failures/skips**: raw-span
invariance, envelope exclusion, deleted/external/overlapping/unassigned memberships,
all local-PK reallocation, reversed node/token PK and insertion ordering, and a
numeric-versus-lexical `!8,!9,!10` ordering probe. These prove audit-only logical
input invariance, not production candidate-ID behavior.

Proportionate existing regression actually run:

```powershell
python -B -m scripts.verify_unit1
```

Result: **PASS**, exit 0. Unit 7/8 suites were not rerun because no production,
existing tests, accepted fixtures or Unit 8 registry interactions changed.
No Matthew rebuild, Unit 3 discovery or second-build gate ran.
The source DB's bytes/version/catalog/counts and protected repositories are
preserved. Future production tests must compare against this independent frozen
expectation rather than generate it through their own candidate implementation.
Unit 8 remains pending independent acceptance. No Unit 8 amendment, persistence,
semantic projection, BRW integration or Unit 10. Phase remains AUTHORIZED.

## Unit 9 production implementation

Unit 9 is **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE**. Fast tests use only
temporary synthetic stores; the real-Matthew tests are opt-in and never rebuild it.

```powershell
python -B -m unittest tests.test_unit9.Unit9FastTests -v
$env:MACULA_UNIT9_INTEGRATION = "1"
$env:MACULA_UNIT9_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit9 -v
Remove-Item Env:MACULA_UNIT9_INTEGRATION
Remove-Item Env:MACULA_UNIT9_DATABASE
```

There are **39 fast + 3 integration tests**. Without opt-in/existing DB the latter
three skip; do not report skips as passes. Production is compared to the committed
independently frozen fixture, never used to regenerate expected values.
Coverage includes U9-01..U9-30, malformed source/store states, PK/path/hash-seed
invariance, canonical numeric order, mixed nearest-first ancestry, immutable DTOs,
exact identity bytes, read-only rejection/closure, all real member lookups, unchanged
Matthew 1:1 Apposition IDs, unchanged Unit 8 Apposition evaluation and explicit
new-clause/forged-envelope rejection.

### Frozen historical assertions intentionally superseded

These six unchanged tests contain an obsolete expectation that S-V-O derivation
returns `()`. Filter them explicitly, not silently and not as claimed passes:

| Unit/class | Skipped test | Replacement coverage in Unit 9 |
|---|---|---|
| 7 Fast | `test_valid_no_match_is_empty_unknown_is_none_invalid_is_error` | U9-24/25/26/30 |
| 7 Fast | `test_semantic_annotations_categories_ellipsis_and_head_do_not_create_candidates` | semantic-annotation invariance, U9-27 |
| 7 Fast | `test_exact_discontinuous_scope_and_span_mutation` | U9-05/11/19/27 |
| 7 Integration | `test_matthew_1_2_discontinuous_scope_without_svo_candidate` | complete frozen DTO/all-lookups integration |
| 8 Fast | `test_matthew_1_2_envelope_cannot_introduce_token_six` | `test_unit8_envelope_forgery_remains_rejected` |
| 8 Integration | `test_actual_matthew_1_1_apposition_and_preservation` | all three Unit 9 integration tests |

The Unit 8 forged candidate still fails V1 identity verification; after reidentifying
it, V2 now reports a source-grounded echo mismatch rather than candidate-not-found,
because an actual clause candidate exists at that anchor. Both are explicit errors,
not evaluation authorization. Unit 8 code/registry/tests/contract remain untouched.

For reproducible current Unit 4-9 regression, enable all existing integration flags
and apply only these explicit skips in memory:

```powershell
4..9 | ForEach-Object {
    Set-Item "Env:MACULA_UNIT$($_)_INTEGRATION" "1"
    Set-Item "Env:MACULA_UNIT$($_)_DATABASE" "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
}
@'
import importlib, unittest
modules = [importlib.import_module(f"tests.test_unit{n}") for n in range(4, 10)]
obsolete = {
    "test_valid_no_match_is_empty_unknown_is_none_invalid_is_error",
    "test_semantic_annotations_categories_ellipsis_and_head_do_not_create_candidates",
    "test_exact_discontinuous_scope_and_span_mutation",
    "test_matthew_1_2_discontinuous_scope_without_svo_candidate",
    "test_matthew_1_2_envelope_cannot_introduce_token_six",
    "test_actual_matthew_1_1_apposition_and_preservation",
}
def filtered(suite):
    for test in suite:
        if isinstance(test, unittest.TestSuite):
            yield from filtered(test)
        else:
            if test._testMethodName in obsolete:
                cls = type(test)
                name = test._testMethodName
                setattr(cls, name, unittest.skip(
                    "frozen no-S-V-O expectation superseded by Unit 9; replacement in test_unit9"
                )(getattr(cls, name)))
            yield test
suite = unittest.TestSuite(filtered(unittest.TestSuite(
    unittest.defaultTestLoader.loadTestsFromModule(module) for module in modules
)))
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
'@ | python -B -
4..9 | ForEach-Object {
    Remove-Item "Env:MACULA_UNIT$($_)_INTEGRATION"
    Remove-Item "Env:MACULA_UNIT$($_)_DATABASE"
}
```

Unit 1/2 may be added normally. Unit 3 must use the existing external read-only
setup override, fresh full fidelity verification and a full-source-population
guard. Never use default Unit 3 discovery here or enable its second-build gate.

Actual final validation:

| Unit | Passed | Skipped | Failures/errors |
|---|---:|---:|---:|
| 1 | 26 | 0 | 0 |
| 2 | 56 | 0 | 0 |
| 3 (initial guarded run) | 22 | 1 | 0 |
| 4 | 15 | 0 | 0 |
| 5 | 20 | 0 | 0 |
| 6 | 22 | 0 | 0 |
| 7 | 15 | 4 | 0 |
| 8 | 49 | 2 | 0 |
| 9 | 42 | 0 | 0 |

The seventh skip is exactly Unit 3
`test_u3_01_two_full_builds_and_logical_digests`, reason:
`explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build`.
All six other skips are enumerated above. Every available Unit 4/5/6/7/9 integration
test except the one obsolete Unit 7 assertion executed read-only; Unit 8's obsolete
integration test was skipped and its valid evaluation assertions executed in Unit 9.

The initial guarded run executed **272 tests: 265 passed, 2 failures, 0 errors,
5 skips**; the two failures exposed the additional frozen Unit 8 no-S-V-O assertions.
After adding replacement coverage, the final follow-up executed **251 tests:
245 passed, 0 failures/errors, 6 skips**, including all 42 Unit 9 tests.
Unit 3's already successful 22 tests were not repeated. The table therefore records
**267 passes and 7 skips across two stages**, not a single 274-test run.
Intermediate synthetic-fixture/diagnostic assertions were corrected and rerun.
Both required source/schema verifiers and Python 3.10 syntax/current compilation
passed. No type-check pass is claimed for Pylance's out-of-workspace files.

Existing DB bytes/version/all 75 measured catalog entries, the frozen fixture,
complete pre-change Apposition DTOs, Matthew source SHA and both protected
repositories were preserved. No full Matthew population or second build occurred.
This is implementation validation only; Unit 8 remains pending independent acceptance,
Unit 9 is pending independent acceptance, and the Phase remains AUTHORIZED.

> **Superseded by Unit 8 Amendment 1 (below):** the two Unit 8 rows in the table above
> were later amended narrowly and are no longer skipped, and the filter now also needs
> the Unit 9 test that asserted the pre-amendment Unit 8 rejection.

## Unit 8 Amendment 1

```powershell
python -B -m unittest tests.test_unit8_amendment1.Unit8Amendment1FastTests -v
```

41 fast tests use the disposable schema-v2 store from
`tests/support/unit8_amendment1_store.py` (real Matthew node ids for the Matthew 1:1
Np-Appos chain and the Matthew 1:2 S-V-O clause with interior token 6). The store carries
a synthetic snapshot because `source_file.sha256` must match the stored bytes, so the
builder self-validates all non-snapshot fields against the frozen fixture and re-encodes
every candidate under the frozen snapshot with an independent encoder to prove the frozen
S-V-O and three Apposition ids; fast tests assert the frozen ids through that recompute.
Citation order is a caller requirement (misordered citations are rejected), matching
frozen Unit 8 behavior.

Opt-in real-Matthew tests (3, read-only; skip otherwise, a skip is not a pass):

```powershell
$env:MACULA_UNIT8_AMENDMENT1_INTEGRATION = "1"
$env:MACULA_MATTHEW_DB = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit8_amendment1 -v
Remove-Item Env:MACULA_UNIT8_AMENDMENT1_INTEGRATION
Remove-Item Env:MACULA_MATTHEW_DB
```

`tests/test_unit8.py` was amended narrowly: Matthew 1:2 now yields exactly one
`ClauseStructureCandidate` (refs `!5,!7,!8,!9`), no Apposition, and a reidentified forged
envelope reports `does not match source-grounded re-derivation`. The two Unit 8 tests
therefore pass and are no longer filtered.

Current superseded-test filter for the combined Units 4-9 and amendment regression
(replace the `obsolete` set and add `tests.test_unit8_amendment1` to the modules):

```python
obsolete = {
    "test_valid_no_match_is_empty_unknown_is_none_invalid_is_error",
    "test_semantic_annotations_categories_ellipsis_and_head_do_not_create_candidates",
    "test_exact_discontinuous_scope_and_span_mutation",
    "test_matthew_1_2_discontinuous_scope_without_svo_candidate",
    "test_unit8_rejects_new_candidate_without_registry_amendment",
}
```

`tests/test_unit9.py::test_unit8_rejects_new_candidate_without_registry_amendment`
asserts that Unit 8 rejects an S-V-O candidate, the exact behavior Amendment 1
replaces, so it fails by design when run unfiltered. Unit 9 tests were not edited;
replacement coverage is `test_a1_02_clause_structure_registry_entry_is_supported`. A
future authorized change should retire or rewrite it.

Guarded validation actually run (existing DB read-only, fresh source-fidelity
verification, full-population guard, Unit 3 second-build gate disabled):
Units 1, 2, 4-9 and the amendment: 295 tests, 0 failures/errors, 5 explicit skips;
Unit 3: 23 tests, 22 passed, 1 skip (the disabled second-build gate). Skips are not
passes. This is implementation validation only, not independent acceptance.

### Current post-Amendment regression rule

Historical validation records above describe test filtering that was necessary at
their respective pre-Unit-9 or pre-Unit-8-Amendment-1 checkpoints. Those records
remain checkpoint evidence.

At the current repository HEAD, active regression must not remove test methods
solely because they encode a pre-S-V-O lifecycle state. The superseded pre-S-V-O
assertions were replaced by current regressions:

- Unit 7 Fast `test_valid_no_match_is_empty_unknown_is_none_invalid_is_error`,
  `test_semantic_annotations_categories_ellipsis_and_head_do_not_create_candidates`
  and `test_exact_discontinuous_scope_and_span_mutation` now expect exactly one
  `clause-structure/source-rule-s-v-o/1` candidate for `MAT 1:2!5/7/8/9`, `()` for
  `MAT 1:2!6`, and no Apposition candidate;
- Unit 7 Integration `test_matthew_1_2_discontinuous_scope_without_svo_candidate` was
  renamed `test_post_unit9_svo_preserves_unit7_exact_scope_invariants`: the S-V-O
  candidate preserves exact scope [5,7,8,9] and excludes token 6;
- Unit 9 `test_unit8_rejects_new_candidate_without_registry_amendment` was renamed
  `test_unit8_amendment_accepts_registered_svo_candidate`: the exact
  `clause-structure/source-rule-s-v-o/1` tuple is accepted by Unit 8;
- `test_unit8_envelope_forgery_remains_rejected` is unchanged: a forged envelope
  remains rejected;
- unknown neighboring candidate tuples still fail closed (existing Unit 8 and
  Amendment 1 tests).

The guarded Unit 3 read-only reuse fixture may replace expensive full-build setup,
but the current runner must not remove active test methods. The `obsolete` filter
sets recorded above are historical and must not be applied at the current HEAD.

## Unit 10 separate persistence

The [frozen contract](../docs/architecture/UNIT-10-STRUCTURAL-INTERPRETATION-PERSISTENCE-CONTRACT.md)
precedes all production implementation in checkpoint
`d690209f7dce140b61d0056446cec370afce2edd`.
The [new tests](test_unit10.py) use standard-library unittest/SQLite only, with disposable
databases outside the repository. No production Matthew build, source migration,
network acquisition or third-party dependency is needed.

```powershell
python -B -m unittest tests.test_unit10.Unit10FastTests -v

# Freshly validate the existing source before real-Matthew persistence tests.
python -B -m scripts.source_fidelity --database "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
$env:MACULA_UNIT10_INTEGRATION = "1"
$env:MACULA_MATTHEW_DB = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit10 -v
Remove-Item Env:MACULA_UNIT10_INTEGRATION
Remove-Item Env:MACULA_MATTHEW_DB
```

Actual result: **45 fast + 3 opt-in integration PASS**, no failures/errors/skips
when opted in. Default module discovery skips the three integration tests explicitly.
Coverage includes separate STRICT schema/version/bootstrap, immutable triggers including
REPLACE with recursive triggers OFF, exact candidate/evaluation round-trips,
stale/reidentified forgery and corruption, missing/cross/self supersession, forks,
global event reuse, snapshot preservation, unregistered derivation versions, changed
source PK/insertion order and projection candidate/evaluation row allocation, separate
read/write profiles, handle closure/rollback, cross-process reload and forbidden fields.
Frozen real-Matthew literal identities are independently recomputed, not taken from the
persistence encoder. Matthew 1:1 stays Verbless/Apposition; Matthew 1:2 exact scope and
components exclude !6.

Combined validation: 366 unfiltered tests, **365 passed / 1 skipped**, no failures/errors.
Earlier Units 1-9: 318 tests, 317 passed / 1 skipped. The only skip is Unit 3's disabled
second-full-build gate. The external guarded runner reused a byte-identical private
copy with fresh complete schema/Expat fidelity, prohibited population above 1 MB,
and still executed offline XmlReader on synthetic Unit 3 inputs.
**Full Matthew builds performed: 0.** No obsolete-test filters or prior-test edits.
Source bytes/catalog/version/logical fidelity and protected repository Git states
were checked before/after. This is implementation validation, NOT independent acceptance.

## Unit 11 discovery and history queries

The [frozen contract](../docs/architecture/UNIT-11-READ-ONLY-STRUCTURAL-INTERPRETATION-DISCOVERY-HISTORY-QUERY-CONTRACT.md)
precedes [projection_query.py](../scripts/projection_query.py). The
[new tests](test_unit11.py) use standard-library unittest/SQLite only, with disposable
source and projection databases outside the repository; no Matthew build, network access
or third-party dependency is needed.

```powershell
python -B -m unittest tests.test_unit11 -v

# Opt-in read-only real-Matthew integration (temporary projection store outside the repo).
$env:MACULA_UNIT11_INTEGRATION = "1"
$env:MACULA_MATTHEW_DB = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit11.Unit11MatthewIntegrationTests -v
Remove-Item Env:MACULA_UNIT11_INTEGRATION
Remove-Item Env:MACULA_MATTHEW_DB
```

Actual result: **32 fast + 1 opt-in integration PASS**; default discovery skips the
integration test explicitly (a skip is not a pass). Coverage includes strict selector and
string-form validation before database access, exact integer-coordinate token/verse/chapter/
book discovery (no `1:2`/`1:20`, `!5`/`!50` or chapter 1/11 prefix collisions, no
cross-verse envelope), the Matthew 1:2 `!6` negative case, unevaluated-candidate
discoverability, multiple/opposing evaluations, superseded history, forks, graph-leaf
semantics, self/dangling/cross-candidate/cross-evaluator/cyclic supersession failures,
corrupt or unvalidatable non-matching candidate rows failing discovery, SQLite-enforced
read-only access with an authorizer trace and connection-closure spy, path/PK/insertion-order
invariance, no source-database dependency and an unchanged Unit 10 DDL hash.

Required regression (no Unit 3 discovery, no Matthew build, no obsolete-test filters):

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
python -B -m unittest tests.test_unit10 tests.test_unit11 -v
python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4 tests.test_unit5 tests.test_unit6 tests.test_unit7 tests.test_unit8 tests.test_unit8_amendment1 tests.test_unit9 tests.test_unit10 tests.test_unit11 -v
```

Actual results: both verifiers exit 0; Units 10+11: 81 tests, OK, 4 explicit opt-in skips;
Units 1, 2, 4-11: 376 tests, OK, 25 explicit opt-in integration skips. Unit 3 was not run
(its default discovery can rebuild Matthew, its code is untouched) and its second-build gate
stayed disabled. The separate opt-in Unit 11 integration run passed read-only against the
existing source database (unchanged) with **0 full Matthew builds**. This is implementation
validation, NOT independent acceptance.

## Product Implementation #1

The [frozen contract](../docs/product/PRODUCT-IMPLEMENTATION-1-MATTHEW-STRUCTURAL-EXPLORER.md)
is implemented by the [product package](../product/), separately from research Units.
Four visible layers use standard-library unittest only:

- A: [adapter/config tests](product/test_product_adapter.py): closed core calls, startup
  stages, error class/stage mapping, input-before-core checks, query budgets, actual snapshot
  mismatch, latched staleness, evidence-read race, absence and path/PK invariance.
- B: [model/AST tests](product/test_product_models.py): frozen slotted model trees, logical keys,
  omitted surrogate/scoring fields, closed enums, absence vs empty, exact authorized files,
  adapter-only core imports, no SQL/writes/network/dependencies.
- C: [presentation/routes](product/test_product_presentation.py): P1-P12, exact token markup,
  CSS prohibitions, separate epistemic sections, all/forked/opposing evaluations, escaping,
  all forbidden bidi/C0/C1 controls, accessible labels, GET/HEAD, loopback/Host guard,
  duplicate Host rejection and unread request bodies; real IPv4 and IPv6 socket checks.
- D: [real-Matthew integration](product/test_product_integration.py): opt-in only, existing
  source read-only, temporary projection using accepted Unit 10 writers, frozen S-V-O id,
  Verbless, exact scope, token 6 exclusion, evaluations and store preservation.

All fixtures live in system temporary directories and are removed. Test-only source fixture
construction redirects the existing SchemaFixture to preserve Greek text consistently in
archived bytes, content and token mirrors; it still runs the accepted schema validator.
Every consumer fixture checks size/mtime_ns/SHA-256 and absence of WAL/SHM/journal sidecars.
No production code builds a store and no test rebuilds Matthew.

```powershell
python -B -m unittest discover -s tests/product -p "test_product_*.py" -v

$env:MACULA_PRODUCT1_INTEGRATION = "1"
python -B -m unittest discover -s tests/product -p "test_product_integration.py" -v
Remove-Item Env:MACULA_PRODUCT1_INTEGRATION
```

Integration uses `MACULA_MATTHEW_DB`, or the existing repository source-store convention.
An opted-in missing database fails explicitly. The implementation executions were separate:
default product discovery **43 ran, 42 passed, 1 skipped** (the explicit integration opt-in);
opted-in integration **1 passed**, no skips. Browser/syntax validation is recorded in the
[implementation section](../docs/product/PRODUCT-IMPLEMENTATION-1-MATTHEW-STRUCTURAL-EXPLORER.md#26-authorized-production-implementation).

Unchanged research regression actually run:

```powershell
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4 tests.test_unit5 tests.test_unit6 tests.test_unit7 tests.test_unit8 tests.test_unit8_amendment1 tests.test_unit9 tests.test_unit10 tests.test_unit11 -v
```

Both verifiers exit 0. Regression **376 ran, 351 passed, 25 skipped**, no failures/errors.
All 25 skips are existing read-only integration opt-ins: Units 4 (4), 5 (4), 6 (3), 7 (3),
8 (1), 8 Amendment 1 (3), 9 (3), 10 (3), 11 (1).
Exact skipped test names, grouped by owning module (reason: the corresponding existing
real-Matthew integration opt-in was not enabled):

- Unit 4: `test_exact_jesus_occurrence`, `test_matthew_1_1_exact_surfaces_and_refs`,
  `test_matthew_1_2_canonical_order`, `test_not_found`.
- Unit 5: `test_matthew_1_1_exact_token_ancestry_matches_independent_source`,
  `test_matthew_1_2_direct_children_and_head_match_source`,
  `test_matthew_1_2_exact_membership_excludes_envelope_token_six`,
  `test_matthew_root_absence_and_unknown_identities`.
- Unit 6: `test_matthew_1_1_exact_composition_and_verbless_source_ancestry`,
  `test_matthew_1_2_composition_reaches_exact_discontinuous_boundary`,
  `test_matthew_unknown_and_repeated_queries_are_deterministic`.
- Unit 7: `test_matthew_1_1_fixed_nested_apposition_path`,
  `test_matthew_1_1_verbless_and_no_semantic_or_fabricated_material`,
  `test_post_unit9_svo_preserves_unit7_exact_scope_invariants`.
- Unit 8: `test_actual_matthew_1_1_apposition_and_preservation`.
- Unit 8 Amendment 1: `test_int_a1_01_real_matthew_clause_candidate_can_be_evaluated`,
  `test_int_a1_02_all_four_scope_members_produce_the_same_evaluable_candidate`,
  `test_int_a1_03_token_six_is_excluded_and_database_is_unchanged`.
- Unit 9: `test_frozen_complete_production_dto_and_all_lookups`,
  `test_matthew_1_1_verbless_and_frozen_apposition_identities`,
  `test_unit8_existing_apposition_evaluation_remains_unchanged`.
- Unit 10: `test_46_real_svo_candidate_fixture_and_independent_identity`,
  `test_47_real_human_and_supersession_literal_vectors`,
  `test_48_real_verbless_apposition_lossless`.
- Unit 11: `test_50_real_matthew_discovery_history_and_token_6_negative_case`.

The default product skip is `test_p1_p2_p3_p4_p5_p12_real_store_preservation`
(reason: `MACULA_PRODUCT1_INTEGRATION` not enabled); its separate opted-in execution passed.
No active-test filter, Unit 3 discovery, second-build gate or full Matthew build was used.
These are implementation checks, not independent acceptance; existing findings remain open.
