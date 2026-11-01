# MACULA-Extract Agent Instructions

## Project boundary
This repository is an independent MACULA linguistic source extraction and verification project.

### Upstream evidence
- Local checkout: `C:\Works\macula-greek`
- Treat upstream as read-only.
- Do not fetch, pull, checkout, reset, clean, or modify upstream to make tests pass.

### Downstream consumer
`bible-research-merged` is downstream. Do not modify it from this repository unless a later task explicitly authorizes cross-repository integration.

## Current authorization
Unit 1 is IMPLEMENTED / INDEPENDENTLY ACCEPTED. Its contract, fixtures, verifier,
tests and independent acceptance findings remain frozen.

The user's separate Unit 2 authorization permits only SQLite source schema,
empty-database bootstrap/version verification, XmlReader and occurrence-identity
contracts, temporary schema tests, and directly related documentation.

Unit 2 MUST NOT create:
- production XML importer or exporter
- populated production Matthew database or production ingestion
- full-NT or N1904 work
- companion-source merges
- BRW integration, semantic projection, localization or UI
- XmlPro dependency or physical byte/UTF-16 mapper

Phase remains AUTHORIZED. Unit 2 is IMPLEMENTED, not independently accepted by its own tests.
Unit 3 is not authorized or started. No network acquisition is permitted.

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
