# Unit 2 — SQLite Source Schema & Parser Contract: Independent Acceptance Audit

Decision: **ACCEPT WITH MINOR FINDINGS** (no BLOCKER, no MAJOR)

## 1. Audited checkpoint
- Repo: C:\Projects\MACULA-Extract, branch master
- Checkpoint: 9c39f832e215023becb366cc8f59af004c43407d
- Parent: 4cd957d7158cfbe0ea29a1afa56f09572fc877fa
- macula-greek: main 8423afe47b9e8f24b7772e808af45c7159a6fe7e (clean)
- bible-research-merged: master 0e4c9baad299f7149cc71b35bcd5208297d4f8c0 (only pre-existing ignored dist/, node_modules/, tsconfig.tsbuildinfo)

## 2. Environment
Python 3.13.7, SQLite 3.50.4, Windows (worktree CRLF via autocrlf, blobs LF).

## 3. Method
Independent re-derivation from raw XML (ElementTree, no repo code), independent DDL/catalog inspection, negative mutation tests
on scratch in-memory/temp databases, independent loader on real Matthew sentences. Scripts in this directory:
derive.py, audit_a.py (91/91 PASS), audit_b.py (127/127 PASS), audit_d.py, audit_e.py (2/2 PASS).
Evidence types: A = independent source/DDL/SQLite; B = negative mutation; C = repo-supplied tests (not relied upon alone).

## 4. Repo/history/path-set
Changed paths: M AGENTS.md, README.md, docs/architecture/README.md, docs/governance/FIDELITY-CONTRACT.md, docs/governance/PHASE-STATUS.md,
tests/README.md; A contracts/occurrence-locator.unit2.json, contracts/xmlreader-parser.unit2.json,
docs/architecture/UNIT-2-SQLITE-SOURCE-SCHEMA-CONTRACT.md, docs/architecture/XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md,
schema/001-source-store.sql, scripts/occurrence_locator.py, scripts/source_schema.py, tests/test_unit2.py. `git diff-tree --check` rc=0.

## 5. Unit 1 freeze
No Unit 1 frozen artifact modified (diff 4cd957d..9c39f83 on frozen paths empty). verify_unit1 rc=0; tests.test_unit1 26 OK.

## 6. Source authority
01-matthew.xml SHA-256 FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4 (14,115,918 bytes), unchanged vs HEAD; Unit 1 contract revision 8423afe.

## 7. Tests actually run
Full discovery 76 tests OK (26 Unit1 + 50 Unit2), 0 fail/error/skip; `python -B -m scripts.source_schema` rc=0 (schema_version 1, 12 tables).
Repo clean afterwards (verified at start and end).

## 8. SQLite schema — PASS
12 required tables, all STRICT, every TEXT column COLLATE BINARY; PK/FK/UNIQUE/CHECK enforced by real violating inserts.
## 9. Bootstrap/version — PASS
Empty->ok; user_version=1; singleton schema_version with DDL/parser/locator hashes equal to independently computed (LF-normalised) hashes; repeat, user_version 2/99, non-empty, active transaction, attached/temp shadow all fail closed; failed DDL rolls back to zero objects.
## 10. Source fidelity — PASS
Full 14 MB Matthew BLOB round-trips byte-exact; checksum/size/type CHECKs; valid-shaped wrong SHA caught by validate_store.
## 11. Attribute identity — PASS
ref vs Ref, Id, xml:id (XML namespace), nodeId, morphId distinct; present-empty = row with ''; absent = no row; NULL rejected; typed NULL for present-empty `Start=""` rejected, typed '' preserved (audit_e).
## 12. Mixed content / document level — PASS
aa,<b/>,bb,<c/>,cc + CDATA/comment/PI recoverable in order; document-level non-whitespace text rejected.
## 13. Namespaces — PASS
none/default/prefixed/same-local-different-URI/same-URI-different-prefix representable; identity = expanded name; duplicate expanded name via different prefix rejected.
## 14. Locator — PASS
Scheme macula.xml-expanded-ordinal-path v1; independently walked real-file paths equal encode_locator; independent of DB PK and prefix; 15 malformed inputs raise; SQLite CHECKs reject non-JSON/shape/scheme/version; semantic-wrong locators rejected by validate_store.
## 15. Matthew 1:1 — PASS
Sentence ref "MAT 1:1!1-1:1!8"; 1 Tree; 26 Node; 25 Node->Node edges; 8 leaves; 342 attributes (incl. Sentence@ref); 200 leaf attrs; ClType Verbless; root Start/End/Id/Rule absent (not defaulted); last token direct text 'Ἀβραάμ.' ≠ NormalizedForm 'Ἀβραάμ'.
## 16. Single-char Greek — PASS
733 single-code-point leaves in Matthew; MAT 1:16!13 (ὁ U+1F41) and MAT 1:18!5 (ἡ U+1F21) stored exactly, found in BLOB bytes; all 733 round-trip.
## 17. Matthew 1:2 ordering — PASS
Tree-leaf order puts 1:2!6 (Start=4) before 1:2!5 (Start=5); canonical ordinal stored separately from tree_leaf_ordinal.
## 18. Matthew 1:2 membership — PASS
nodeId 400010020050040 (Id 1.15, CL, S-V-O) descendant leaves = verse ordinals [5,7,8,9]; token 6 excluded; discontinuous membership; no dense interval assumed; leaf self-membership present.
## 19. Topology/membership constraints — PASS
Composite FKs block cross-tree/cross-file parents and cross-tree membership; non-descendant membership rejected by membership_ancestry trigger; duplicate rejected; UPDATE blocked; deleted membership detected by validate_store.
## 20. Immutability — PASS (see F-2)
BEFORE UPDATE/DELETE triggers on all source tables except membership (delete allowed by design); REPLACE blocked when recursive_triggers=ON; dropped trigger detected by catalog check.
## 21. Typed mirror — PASS
FunctionalTag ≠ FormalTag stored independently (215 in Matthew; e.g. MAT 1:16!14); typed/generic mismatch, invented typed value, missing typed value all rejected by validate_store.
## 22. Cross-snapshot — PASS
Identical nodeId/xml:id/morphId coexist across snapshots; external occurrence key (9 parts) differs.
## 23. Parser contract — CONTRACT VERIFIED; PRODUCTION PARSER NOT YET IMPLEMENTED
23 parser + 5 locator mutations (DtdProcessing Parse/Ignore, XmlResolver, Fragment, CheckCharacters false, Ignore* true, xmlpro_dependency, implicit XInclude, external acquisition, XInclude reject removed, HTML entities, trim/Greek normalisation, etc.) all fail closed; unmutated accepted.
## 24. Hygiene of archived XmlPro spike report — PASS
Only lines 653,656,659,662,665,668,671,674,677,680 differ from TEMP original (20 trailing-space bytes removed after EOL normalisation); otherwise byte-identical.
## 25. Scope — PASS
No importer/exporter/ingestion/populated DB/N1904/XmlPro dependency/semantic projection/Unit 3 in executables; only in-memory sqlite.
## 26. Governance — PASS
PHASE-STATUS: Unit 2 IMPLEMENTED (not accepted); Unit 3 NOT STARTED / NOT AUTHORIZED. Docs do not claim acceptance or production parsing.
## 27. Test-suite independence
test_unit2.py (50 tests) is partly circular (uses encode_locator and bootstrap/validate_store); mitigated because the audit scripts independently re-verified every behaviour with TYPE A/B evidence. 3 `patch.object` uses did not mask any verified behaviour.

## 28. Findings

| ID | Severity | Finding |
|----|----------|---------|
| F-1 | MINOR | Several scope invariants (tree/syntax_node element file scope, token.book_id snapshot scope, token-on-leaf-only, locator correctness, SHA vs bytes) are enforced by `validate_store`, not by SQLite constraints; all verified to fail closed under validation. Documented in the contract. |
| F-2 | MINOR / INFO | `foreign_keys` and `recursive_triggers` are per-connection pragmas. A default connection can INSERT OR REPLACE into immutable tables. Naive tamper is detected by validate_store; a consistent generic+typed tamper by an unguarded writer passes it because validate_store does not re-parse original_bytes (audit_d). Explicitly documented (“does not parse original BLOBs”); byte-to-occurrence coverage deferred to future importer. Recommend read-only connections for published stores. |
| F-3 | INFO | `external_identity` / `excluded_identity_inputs` in the locator contract are documentation only (not machine-validated by `_contracts()`); behaviour verified independently. |
| F-4 | INFO | membership_ancestry trigger recomputes a recursive view per insert; slow on larger loads (performance only). |

## 29. Acceptance matrix (AC-IA-U2-01..44)
All 44 criteria: PASS (evidence sections 4–27). AC rows touching F-1/F-2 (immutability, scope enforcement) PASS with the minor notes above. No FAIL, no NOT VERIFIED.

## 30. Scope confirmation
No Unit 3 work, no governance change, no commit, no repo modification.

## 31. Repository safety
Final `git status --porcelain=v1 --ignored`: MACULA-Extract clean (no __pycache__/db residue); macula-greek clean; bible-research-merged only pre-existing ignored paths. Scratch DB temp dirs removed.

## 32. Artifact location
C:\Users\cruis\AppData\Local\Temp\u2audit\ (outside all repos)

## 33. Final statement
Commit 9c39f832e215023becb366cc8f59af004c43407d is independently accepted (with minor findings F-1..F-4). Ready for a separate archival/governance checkpoint. Unit 3 is not started and not authorized by this audit.
