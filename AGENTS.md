# MACULA-Extract Agent Instructions

## Project boundary
This repository is an independent MACULA linguistic source extraction and verification project.

### Upstream evidence
- Local checkout: `C:\Works\macula-greek`
- Treat upstream as read-only.
- Do not fetch, pull, checkout, reset, clean, or modify upstream to make tests pass.

### Downstream consumer
`bible-research-merged` is downstream. Do not modify it from this repository unless a later task explicitly authorizes cross-repository integration.

## Current Governance Status
This is a summary ledger. [docs/governance/PHASE-STATUS.md](docs/governance/PHASE-STATUS.md)
is the authoritative lifecycle record; historical audits are evidence about their own
checkpoints and are not rewritten by later governance.

| Unit | Current status | Decision / note |
|---|---|---|
| Unit 1 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT; contract, fixtures, verifier, tests and findings frozen |
| Unit 2 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT WITH MINOR FINDINGS (existing findings unchanged; [audit](docs/audits/UNIT-2-SQLITE-SOURCE-SCHEMA-INDEPENDENT-ACCEPTANCE-AUDIT.md)) |
| Unit 2 Amendment 1 | IMPLEMENTED | Not separately independently accepted; schema version 2 (`087865e3d822c7baa1f9d7e5313d46b5168bc670`) |
| Unit 3 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT ([audit](docs/audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)) |
| Unit 4 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT (same audit) |
| Unit 5 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT WITH MINOR FINDINGS; **Unit 5 M1 unresolved** |
| Unit 6 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT (same audit as Units 3 and 4) |
| Unit 7 | IMPLEMENTED / INDEPENDENTLY ACCEPTED | ACCEPT WITH MINOR FINDINGS; **Unit 7 audit M1 unresolved**; I1-I6 informational, not remediated ([audit](docs/audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md)) |
| Unit 8 | IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE | Separately authorized in-memory boundary only; no persistence; no independent acceptance audit exists |
| Unit 9 | DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED | Production implementation NOT YET PERFORMED; independently frozen S/V/O memberships and expected identity only |
| Phase | AUTHORIZED | Not COMPLETE, not CLOSED |

Unit 5 M1 and the Unit 7 audit M1 are different findings; keep them distinct and do not
remediate either without separate explicit authorization. Acceptance of Units 3, 4 and 6
is not independent acceptance of Unit 2 Amendment 1.

## Authorization boundary
Each Unit is authorized only by a separate explicit user instruction; the Phase being
AUTHORIZED, a Unit being accepted, or a contract existing does not authorize the next Unit.
Standing prohibitions unless a later user task explicitly authorizes them:
- other books, N1904/full-NT ingestion, or companion-source merges
- XmlPro dependency or physical byte/UTF-16 range mapper
- network acquisition
- BRW integration, semantic projection, localization or UI
- automatic independent acceptance of any Unit

Unit 1 and the amended Unit 2 technical baseline, plus their historical audits, remain frozen.
See the [Unit 3 pipeline contract](docs/architecture/UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md).

Historical scope notes (superseded by later separate authorizations, kept for context):
Unit 2 originally permitted only the SQLite source schema, empty-database bootstrap/version
verification, XmlReader and occurrence-identity contracts and temporary schema tests; Unit 3
later added the pinned SBLGNT Matthew XmlReader importer, exact archived-byte export, DB-only
reconstruction and independent source-fidelity verification; Unit 4 added read-only
verse/token queries; Units 5-7 added read-only syntax navigation, source evidence
composition and in-memory Apposition structural candidates. Unit 2 Amendment 1 removed the
per-row membership ancestry INSERT trigger and retains transactional post-load
complete-set validation.

## Unit 8 implementation and stop boundary
Unit 8 is **IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE** under the separate user
authorization starting at `8f8b2e7642204378eb0e56e20d096b6233e409b2`.
The [contract implementation section](docs/architecture/UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md#34-authorized-initial-implementation)
supersedes its preserved historical design-only authorization/status text.
`scripts/evaluated_interpretations.py` exposes `create_evaluated_interpretation`,
`verify_evaluated_interpretation`, `compute_evaluation_id` and frozen
`EvaluatedStructuralInterpretation`, `RationaleCitation`, `RationaleNote` DTOs.
Creation requires independent frozen-protocol candidate V1 and public Unit 7 V2;
verification without a database is V1/history only, with a database also V2.
Only `human-structural-adequacy` / `1`, class `human`, is registered.
The checkpoint validated 50 Unit 8 fast tests, 1 opt-in existing-Matthew integration
test, 62 Unit 4-7 fast regressions and both required verifiers (all PASS).
This is implementation validation, not an independent acceptance audit.
Without separate explicit user authorization, do NOT:
- conduct independent Unit 8 acceptance in the implementation task
- create evaluation persistence or a projection database
- modify the source schema
- integrate Bible Research / BRW
- implement semantic roles or create Actor/Action/Patient/Event/Result/Identity/Property entities
- begin Unit 9 production implementation

Implemented invariants (details in the contract):
- Source fact, Unit 7 `StructuralCandidate` and Unit 8 evaluated interpretation are distinct
  epistemic object classes; do not collapse them.
- Evaluating a candidate must not mutate source facts or the candidate.
- The authoritative source store stays read-only to downstream interpretation.
- No synthetic confidence, probability or scoring.
- No semantic-role or theological interpretation.
- Persistence is not part of the current Unit 8 design/implementation boundary.
- Unit 5 M1 and Unit 7 audit M1 remain unresolved; Phase remains AUTHORIZED.

## Unit 9 design/fixture freeze and stop boundary
The separately authorized [Unit 9 freeze](docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md#27-authorized-component-membership-freeze-evidence)
adds only a design contract and
[source-facing expected fixture](fixtures/matthew-1-2-svo-candidate.expected.json).
Status: **DESIGN + FIXTURE FROZEN / NOT IMPLEMENTED**.
Production implementation: **NOT YET PERFORMED**.
Raw XML and independent read-only SQLite agree on Matthew 1:2 anchor exact scope
`!5,!7,!8,!9`, S=`!5`, V=`!7`, O=`!8,!9`; token 6 is excluded everywhere.
The expected candidate identity was independently computed only after membership
freeze. Eight reduced-store audit controls are not production Unit 9 tests.
Do not extend `scripts/structural_candidates.py`, create `tests/test_unit9.py`,
amend Unit 8's contract/registry, add persistence, semantic roles/projection, BRW
integration or Unit 10 without separate authorization.
Unit 8 remains IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.
Unit 5 M1 and Unit 7 audit M1 remain unresolved; Phase remains AUTHORIZED.

## Fidelity principles
1. Raw source is source authority.
2. Missing and present-empty are distinct.
3. Greek surface text must not be destructively normalized.
4. `ref` and `Ref` are distinct source fields.
5. `Id`, `xml:id`, `nodeId`, and `morphId` are distinct identities.
6. `FunctionalTag` and `FormalTag` remain distinct.
7. Tree traversal order, canonical scripture order, source Start/End, and exact node-token membership are distinct concepts.
8. MACULA linguistic annotations are not BRW evaluated interpretations.
9. Do not mechanically map S/V/O/P or A0/A1/A2 to BRW semantic roles.
10. Fail closed on source revision, path, checksum, or fixture mismatch.

## Git safety
Before editing, record branch, HEAD, staged/unstaged/untracked state. Do not destroy pre-existing user work. Only create a Unit checkpoint after all authorized tests and acceptance criteria pass.

## Unit 2 verification boundary
- SQLite 3.37+ with STRICT and JSON support; Python standard library, no downloads.
- Use a dedicated main connection with `foreign_keys=ON` and `recursive_triggers=ON`.
- Bootstrap only an empty, unversioned database; repeated/unknown initialization fails closed.
- Original source bytes are exact BLOB authority. LF normalization of schema/config text hashes is not source normalization.
- `validate_store` is a mandatory schema/model consistency gate, not an XML parser or production round-trip certification.
- Source attributes/content are the presence/value ledger; typed mirrors must agree.
- Preserve zero-based sibling/traversal orders separately from one-based locator name ordinals and scripture coordinates.
- Membership is complete descendant-leaf ancestry (including leaf self), never a Start/End interval.

## Unit 3 verification boundary
- The production parser must actually run System.Xml.XmlReader with the explicit safe profile.
- The public importer accepts no input path; it rechecks the frozen source root/revision/path/hash.
- Build .NET offline with cleared package sources; keep build outputs outside this repository.
- Publication requires the schema-v2 Unit 2 consistency validator, including both
  directions of complete ancestry membership equality, plus independent Expat
  source-versus-DB XML/core equality. Do not treat BLOB equality as normalized certification.
- Publish without overwriting; consumers use read-only/query-only connections with both PRAGMAs ON.
- Do not commit generated production database binaries. Keep all tests/builds temporary and clean up.
- Preserve historical F-1 through F-4; Unit 3's source-fidelity control does not erase F-2.

## Unit 4 query boundary
- Only `get_verse` and `get_token`; caller supplies the existing schema-v2 database path.
- Use SQLite URI `mode=ro`, `query_only=ON` and the existing consumer PRAGMA profile.
- Check version/contract identity and required query columns before lookup; errors are not not-found.
- Order verse tokens by stored scripture coordinates, never tree/row/Start order.
- Preserve raw mirrors, absence versus empty, and surface versus normalized; do not derive semantics.
- Keep local SQLite ignored and byte-for-byte unchanged; no migration or full Matthew rebuild.
- Fast tests use temporary minimal stores. Full-Matthew integration is opt-in and read-only.
- Default Unit 3 discovery builds Matthew; do not run it for a zero-build query task without
  an external read-only reuse fixture. See the [Unit 4 contract](docs/architecture/UNIT-4-MATTHEW-QUERY-SLICE.md).
