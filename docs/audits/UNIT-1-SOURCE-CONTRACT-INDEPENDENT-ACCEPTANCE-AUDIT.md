# Unit 1 Independent Acceptance Audit

This is an independent acceptance audit of the Unit 1 checkpoint. It was performed as a separate reviewer, not as the implementer, and did not accept the implementer's PASS claims as fact. All critical findings below were independently re-derived from the actual repository, the actual upstream checkout, and actual test execution.

## Decision

ACCEPT

## Audited checkpoint

Repository: C:\Projects\MACULA-Extract
Branch: master
Checkpoint: a0327c93db4f555443683f5ea2d2b447f2e52704
Root commit status: sole commit, no parent (`git rev-list --count HEAD` = 1; `git log -1 --pretty=%P HEAD` = empty)
Commit count: 1

Tracked file set matched the expected 13 Unit 1 files exactly:
`.gitignore`, `AGENTS.md`, `README.md`, `contracts/macula-sblgnt-matthew.unit1.json`,
`docs/architecture/MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md`,
`docs/architecture/README.md`, `docs/governance/FIDELITY-CONTRACT.md`,
`docs/governance/PHASE-STATUS.md`, `fixtures/matthew-1-1.expected.json`,
`fixtures/matthew-1-2-boundary.expected.json`, `scripts/verify_unit1.py`,
`tests/README.md`, `tests/test_unit1.py`.

Worktree and index were clean, no untracked files, no ignored-matching generated artifacts, and
`git diff-tree --check --root HEAD` reported no diff hygiene problems.

## Independent source verification

MACULA revision: `8423afe47b9e8f24b7772e808af45c7159a6fe7e` — confirmed as the actual
`git rev-parse HEAD` of `C:\Works\macula-greek`, with a clean worktree, independently of the
Unit 1 contract or verifier.

Matthew path: `SBLGNT/nodes/01-matthew.xml`

Expected SHA-256: `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`

Actual SHA-256 (computed independently via `Get-FileHash -Algorithm SHA256`, outside the
verifier and outside the fixtures): identical value.

Result: PASS

## Matthew 1:1 independent verification

Facts below were read directly from the raw upstream XML (`SBLGNT/nodes/01-matthew.xml`),
not from the fixture or verifier output, then compared against the fixture.

- Sentence: `MAT 1:1!1-1:1!8`
- Tree: 1
- Nodes: 26 (manually recounted `Node` elements under the tree)
- Node→Node relations: 25 (manually recounted parent→child edges)
- Tokens: 8 leaf `Node` elements
- Source attributes: 342 (sum of attribute counts over every element in the sentence)
- Leaf attributes: 200 total (25 per token, confirmed on the first and last leaf nodes)
- ClType=Verbless: confirmed verbatim on the clause node
  (`Id="2.1" Cat="CL" Rule="P2CL" Start="0" End="7" Head="0" ClType="Verbless" nodeId="400010010010082" Length="8"`)
- Verb leaves: 0 (all 8 leaves have `Cat="noun"`)
- Surface/Normalized distinction: the final leaf's text content and `Unicode` attribute are both
  `Ἀβραάμ.` (with trailing period), while `NormalizedForm` is `Ἀβραάμ` (no period) — confirmed
  distinct directly in the raw XML.
- Root node attributes (`Cat="S" Head="0" nodeId="400010010010083" Length="8"`) match the fixture
  exactly, and `Start`/`End`/`Id`/`Rule` are genuinely absent from the XML element (not
  present-with-empty-value).

Result: PASS — all counts, topology, and token facts were independently re-derived from upstream
and matched the frozen fixture exactly.

## Matthew 1:2 ancestry/membership independent verification

- Tree-order counterexample: node `MAT 1:2!6` (`δὲ`, `Start="4"`) appears in document/tree
  traversal order **before** node `MAT 1:2!5` (`Ἰσαὰκ`, `Start="5"`) — confirmed by direct reading
  of the raw XML, not by reading the fixture first.
- Canonical-order comparison: scripture ordinal 5 is less than ordinal 6, so canonical scripture
  order reverses the tree-traversal order of this pair.
- Subtree: `nodeId="400010020050040"`, `Rule="S-V-O"`, `Start="5"`, `End="8"`.
- Ancestry-derived members: manually walked the actual parent→descendant `Node` structure of that
  subtree in the raw XML (not using `Start`/`End` arithmetic, and not reading the fixture's
  membership array first). The real leaf descendants are `MAT 1:2!5`, `MAT 1:2!7`, `MAT 1:2!8`,
  `MAT 1:2!9`, giving ordinals `[5, 7, 8, 9]`.
- Envelope non-member token 6: token `MAT 1:2!6` (`δὲ`) is a **sibling** of the subtree in the
  parse tree, not a descendant of it, even though its scripture ordinal (6) falls inside the
  numeric `Start=5`/`End=8` envelope. This was confirmed by direct ancestry inspection, proving
  the exact membership is genuinely tree-derived rather than an envelope/interval shortcut.

Result: PASS

## Test independence assessment

`scripts/verify_unit1.py::verify_fixtures` parses the live upstream XML via `ET.fromstring(raw)`
at call time and recomputes all critical facts from the actual element tree on every invocation.
It uses the fixture only as the *expected* value to compare the live computation against, never
as the source of the computation itself. Specifically:

- Node/leaf/relation counts are computed via `tree.iter("Node")` and a `leaf_nodes()` helper that
  walks real children, not read from the fixture.
- Attribute absence is checked via `name in element.attrib` (a true XML attribute-presence check),
  not `element.attrib.get(name) is None`, which would conflate "missing" with "present but
  normalized/empty." A dedicated negative test
  (`test_fixture_rejects_placeholder_attribute`) proves the distinction is real: it mutates a live
  in-memory document to make `Frame` present-with-empty-value and confirms the verifier correctly
  rejects it as a violation of the frozen absence expectation.
- Discontinuous membership is computed by finding the subtree node by `nodeId` in the live parsed
  tree and then calling `leaf_nodes(subtree)`, which walks actual descendant `Node` elements. It
  never derives membership from `Start`/`End` arithmetic or an interval/envelope.

I independently re-derived the same facts (node counts, Verbless, token surfaces, ordering
counterexample, exact membership) directly from the XML myself, without consulting the verifier
code or fixture values as my source of derivation, and they matched exactly.

No TYPE-C (fixture-compared-only-to-fixture) circularity exists in any of the critical acceptance
paths (source identity, node/attribute counts, Verbless, token identity/surface, ordering,
membership). The `validate_contract` self-consistency checks are legitimately TYPE B
(contract-drift detection against a hardcoded expected contract in the verifier module) and are
never used to prove source fidelity; TYPE A (upstream → independently computed actual → frozen
expected) coverage exists for every critical acceptance fact listed above.

## Negative tests

All 26 tests in `tests/test_unit1.py` were run directly by this audit
(`python -B -m unittest tests.test_unit1 -v`): 26 passed, 0 failed, 0 skipped, 0 errors.

Meaningful fail-closed coverage confirmed present and exercised:

- `test_source_rejects_wrong_git_root` — wrong upstream git root → FAIL
- `test_source_rejects_revision_mismatch` — wrong revision → FAIL
- `test_source_rejects_missing_file` — missing source file → FAIL (propagates `FileNotFoundError`)
- `test_source_rejects_same_length_byte_mutation` — single-bit byte mutation, same length → SHA-256 mismatch → FAIL
- `test_contract_rejects_identity_or_policy_drift` — 9 separate contract-field drifts (revision, edition, source_format, authorized_book, upstream path, network_fetch, implicit_xinclude, directory_wildcard_expansion, contract_version) → FAIL
- `test_contract_rejects_path_checksum_and_allowlist_drift` — empty allowlist, wrong path, wrong path traversal (`../01-matthew.xml`), wrong checksum, duplicated allowlist entries → FAIL
- `test_contract_rejects_removed_fidelity_or_field_distinctions` — field_identity/ordering_concepts/fidelity_invariants/prohibited_semantic_mappings stripped → FAIL
- `test_fixture_rejects_shape_and_attribute_mutation` — wrong node_count/token_count/source_attribute_count/leaf_attribute_count_per_token → FAIL
- `test_fixture_rejects_placeholder_attribute` — present-but-empty attribute substituted for genuinely absent attribute → FAIL
- `test_fixture_rejects_changed_head` — mutated `Head` attribute on live in-memory tree → FAIL
- `test_fixture_rejects_changed_verbless` — `ClType` changed away from `Verbless` → FAIL
- `test_fixture_rejects_normalized_surface` — raw token text replaced with its `NormalizedForm` → FAIL
- `test_fixture_rejects_incorrect_order_and_membership_expectations` — wrong ordering fixture and wrong membership fixture, each independently → FAIL
- `test_doctype_and_xinclude_are_rejected` — DOCTYPE and XInclude in source bytes → FAIL
- `test_json_field_keys_preserve_case` — duplicate JSON keys → FAIL
- `test_verification_only_uses_read_only_git_commands` — confirms only `git rev-parse --show-toplevel` / `git rev-parse --verify HEAD` are invoked, no mutating git commands

All mutation-based negative tests use in-memory XML/bytes or mocked subprocess/`Path.read_bytes`
calls; none of them modify the tracked upstream file or fixtures on disk.

In addition to the suite, this audit ran one ad-hoc negative check outside the test file (forged
all-zero revision passed through `verify_source` against the real contract) and confirmed it
raised `VerificationError` referencing the revision mismatch, consistent with the suite's coverage.

## Findings

### BLOCKER

None.

### MAJOR

None.

### MINOR

None.

### INFORMATIONAL

- The candidate SQLite tables sketched in the Architecture Spike document remain clearly labeled
  as non-authoritative design candidates, not frozen production DDL. This is appropriate for the
  current phase and is not a Unit 1 defect; it is noted here only as a forward-looking design
  consideration for a future, separately authorized Unit.

## Acceptance criteria

AC-IA-01 PASS — Repository root, branch (`master`), and root commit (`a0327c93db4f555443683f5ea2d2b447f2e52704`) independently verified via `git rev-parse`.
AC-IA-02 PASS — `git rev-list --count HEAD` = 1 and the commit has no parent.
AC-IA-03 PASS — `git ls-tree -r --name-only HEAD` matched the expected 13-file set exactly.
AC-IA-04 PASS — Upstream `C:\Works\macula-greek` HEAD independently confirmed as `8423afe47b9e8f24b7772e808af45c7159a6fe7e` with a clean worktree.
AC-IA-05 PASS — Matthew source SHA-256 independently computed via `Get-FileHash`, matching the contract/fixture value.
AC-IA-06 PASS — Allowlist is a single explicit entry; contract declares `network_fetch`, `implicit_xinclude`, and `directory_wildcard_expansion` all false; drift in any of these fields is proven to raise via negative tests.
AC-IA-07 PASS — `verify_fixtures` recomputes counts/topology/membership from the live parsed XML tree on every call; fixtures supply only expected values for comparison.
AC-IA-08 PASS — Matthew 1:1 sentence/tree/node/relation/token counts independently recounted from raw XML and matched.
AC-IA-09 PASS — `ClType=Verbless` and zero verb leaves confirmed directly in the raw XML.
AC-IA-10 PASS — All eight token `ref`/`xml:id`/`morphId`/surface values independently confirmed against the raw XML.
AC-IA-11 PASS — Final token's raw text/`Unicode` (`Ἀβραάμ.`) and `NormalizedForm` (`Ἀβραάμ`) confirmed distinct in the raw XML.
AC-IA-12 PASS — Absence is checked via `name in element.attrib`, and `test_fixture_rejects_placeholder_attribute` proves present-empty is distinguished from genuinely absent.
AC-IA-13 PASS — `ref` (scripture coordinate) and `Ref` (referent annotation) are distinct fields in the contract, fixtures, and verifier; confirmed `Ref` is absent from Matthew 1:1 leaves while `ref` is present.
AC-IA-14 PASS — `FunctionalTag` and `FormalTag` are tracked and asserted as separate fields throughout contract, fixtures, and tests.
AC-IA-15 PASS — Matthew 1:2 tree-order-before-canonical-order counterexample independently confirmed from raw XML (token 6 precedes token 5 in tree order; canonical order reverses this).
AC-IA-16 PASS — Discontinuous membership `[5, 7, 8, 9]` independently derived by walking real descendant `Node` elements of subtree `nodeId=400010020050040`, not from `Start`/`End` arithmetic.
AC-IA-17 PASS — Token 6 independently confirmed to be a sibling, not a descendant, of the subtree, despite falling inside the `Start`/`End` numeric envelope.
AC-IA-18 PASS — No critical acceptance fact relies solely on fixture-to-fixture comparison; all critical facts have a live-source-derived (TYPE A) verification path.
AC-IA-19 PASS — 26 tests include substantive fail-closed negative coverage (revision, root, checksum, path, allowlist, contract-field drift, fixture-count drift, placeholder-attribute, changed Head/ClType/surface, wrong ordering/membership, DOCTYPE/XInclude, duplicate JSON keys); all independently rerun and confirmed to fail-closed as expected.
AC-IA-20 PASS — Byte-level diff performed by this audit between the originally supplied Architecture Spike attachment and the repository copy showed only 3 trailing-whitespace removals at lines 29-31; no other textual differences.
AC-IA-21 PASS — `docs/governance/PHASE-STATUS.md` (pre-audit) declared Phase `AUTHORIZED` and Unit 1 `IMPLEMENTED`, explicitly stating the Phase is not COMPLETE/CLOSED and Unit 1 does not authorize Unit 2.
AC-IA-22 PASS — No SQLite schema/database, importer/exporter, N1904 integration, companion-source merge, or BRW semantic-projection code exists anywhere in the tracked file set; `git grep` hits for prohibited-mapping terms are confined to documentation/prohibition declarations (contract's `prohibited_semantic_mappings`, governance prose, architecture-spike prose), never executable logic.
AC-IA-23 PASS — `C:\Works\macula-greek` HEAD and clean status confirmed unchanged before and after this audit.
AC-IA-24 PASS — `C:\Projects\bible-research-merged` HEAD (`0e4c9baad299f7149cc71b35bcd5208297d4f8c0`) and clean status confirmed unchanged before and after this audit.
AC-IA-25 PASS — `python -B -m scripts.verify_unit1` and `python -B -m unittest tests.test_unit1 -v` were both independently rerun by this audit (Python 3.13.7); verifier printed matching JSON, test suite reported 26 passed / 0 failed.
AC-IA-26 PASS — All three repositories confirmed clean at the end of the audit. (This audit's own ad-hoc commands generated a `scripts/__pycache__` directory during testing; it was identified and removed before concluding the audit, restoring `MACULA-Extract` to a clean state.)

## Tests actually run

```powershell
cd C:\Projects\MACULA-Extract
python -B -m scripts.verify_unit1
python -B -m unittest tests.test_unit1 -v
```

Python version: 3.13.7

Results:
- `scripts.verify_unit1`: exit 0, JSON summary matched both frozen fixtures exactly (revision, SHA-256, primary counts/`ClType`, boundary `tree_pair`/`exact_members`/`excluded`).
- `unittest tests.test_unit1 -v`: `Ran 26 tests in 18.507s` — `OK` (0 failures, 0 errors, 0 skips).

## Repository safety

MACULA-Extract final status: clean at the time of this finding (a self-generated `scripts/__pycache__` artifact from ad-hoc audit commands was identified and removed before concluding the technical audit).
macula-greek final status: clean; HEAD unchanged at `8423afe47b9e8f24b7772e808af45c7159a6fe7e`.
bible-research-merged final status: clean; HEAD unchanged at `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`.

## Scope confirmation

SQLite schema/database: NO
Importer/exporter: NO
N1904/full NT: NO
Semantic projection: NO
Unit 2 started: NO

## Final statement

The Unit 1 checkpoint (`a0327c93db4f555443683f5ea2d2b447f2e52704`) is ACCEPTED. Every critical
fidelity claim — source identity/checksum, Matthew 1:1 topology and Verbless/zero-verb facts,
token surface/NormalizedForm distinction, the Matthew 1:2 tree-vs-canonical ordering
counterexample, and the exact-ancestry discontinuous membership excluding token 6 — was
independently re-derived by this audit directly from the raw upstream XML, not merely replayed
from the fixtures or the implementer's report, and matched exactly. The verifier and tests
demonstrably read live source and reject drift (contract, checksum, revision, root, fixture,
ordering, membership) in genuine negative tests rerun independently by this audit. No scope
leakage, no overclaimed governance status, and all three repositories were confirmed unmodified
and clean at the conclusion of this audit.
