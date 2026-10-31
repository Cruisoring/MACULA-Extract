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
Only Unit 1 is authorized: freeze the SBLGNT Matthew source contract and acceptance fixtures.

Unit 1 MUST NOT create:
- SQLite schema or database
- importer or exporter
- full Matthew database ingestion
- N1904 integration
- companion-source merges
- BRW semantic projection

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
