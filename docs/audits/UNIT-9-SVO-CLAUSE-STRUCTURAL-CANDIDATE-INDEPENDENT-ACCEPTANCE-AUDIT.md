# Unit 9 S-V-O Clause Structural Candidate Independent Acceptance Audit

## Decision

**ACCEPT WITH MINOR FINDINGS.**

- Unit 9 implementation checkpoint: `ddd23c4bc51c651aea82722d747c44671f15832a`.
- Audit starting HEAD: `35337d87bb93e9c19099ff3298afe6e3f36ea76c`.
- AC-U9-01..26: **25 PASS, 1 SUPERSEDED by an accepted amendment (AC-U9-24), 0 FAIL.**
- Findings: 0 BLOCKER, 0 MAJOR, **1 MINOR (M-1)**, 5 INFORMATIONAL (I-1..I-5).
- No production, test, fixture, schema or contract file was changed by this audit.
  Unit 5 M1 and Unit 7 audit M1 remain unresolved and distinct. Phase remains
  **AUTHORIZED**. No next Unit is authorized.

The decision was derived last, from the evidence below.

## Audited checkpoint

| Item | Value |
|---|---|
| Implementation checkpoint | `ddd23c4bc51c651aea82722d747c44671f15832a` (sole parent `22595753477d6ed36317bb685347d77ed1c0a567`, the freeze) |
| Audit starting / ending code HEAD | `35337d87bb93e9c19099ff3298afe6e3f36ea76c` |
| Production under audit | `scripts/structural_candidates.py` (unchanged since `ddd23c4`; `git diff ddd23c4 HEAD` of `scripts/` touches only `scripts/evaluated_interpretations.py`, Unit 8 Amendment 1) |
| Contract | `docs/architecture/UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md` (unchanged between `ddd23c4` and HEAD) |
| Fixture | `fixtures/matthew-1-2-svo-candidate.expected.json`, 2,368 bytes, SHA-256 `6986B8A03465A4AD05533D12A714CE87CADE9ABD760555D4586F1758EEF9764C` |

## Starting state

Repository `C:\Projects\MACULA-Extract`: branch `master`, HEAD `35337d8…`, no staged,
unstaged or untracked files, `git diff --check` clean. The only ignored file is
`sblgnt-matthew.sqlite3`. Upstream `C:\Works\macula-greek` (`main`,
`8423afe47b9e8f24b7772e808af45c7159a6fe7e`) and downstream
`C:\Projects\bible-research-merged` (`master`, `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`)
were clean before and after. Upstream was read-only (no fetch/pull/checkout/reset/clean).
Downstream was not touched.

## Independence

Evidence was ordered A raw XML, B synthetic/mutated stores, C production inspection,
D existing tests last. Audit-owned scripts lived outside the repository (temp directory,
deleted at the end) and used only the Python standard library:

- **A:** a stdlib `ElementTree` oracle over the pinned raw XML with its own membership,
  topology, eligibility and identity serializer (written from the contract text, not
  importing production code).
- **B:** reduced stores with remapped surrogate keys; 37 mutation stores (triggers dropped
  and FKs relaxed in disposable copies only); forged-candidate attacks through the public
  Unit 8 Amendment 1 API.
- **C:** static review, SQLite authorizer tracing, connection-close tracking.
- **D:** the existing test suites, run last and unfiltered.

Existing tests, the frozen fixture and the Unit 8 audit were not used as primary
evidence. The fixture was compared only after the independent derivation.

## Git lineage

Each commit has a sole parent: `8f8b2e7` -> `5bfd1d4` (Unit 8) -> `22595753` (Unit 9
freeze) -> `ddd23c4` (Unit 9 implementation) -> `ac215cb` (Unit 8 Amendment 1) ->
`86c1aad` (test reconciliation) -> `35337d8` (Unit 8/Amendment 1 acceptance, HEAD).
Between `ddd23c4` and HEAD, `scripts/structural_candidates.py`, `source_query.py`,
`source_schema.py`, `source_fidelity.py`, the fixtures, schema and contracts did not change.

## Contract integrity

`git log` shows the Unit 9 contract changed only in `22595753` (freeze) and `ddd23c4`
(+144/-1, the section 28 implementation evidence); no change afterwards. The frozen
identity ordering, section 6 eligibility and AC-U9-01..26 were not weakened by the
implementation diff (`22595753..ddd23c4`).

## Raw-source derivation (type A)

Pinned source: revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`, path
`SBLGNT/nodes/01-matthew.xml`, 14,115,918 bytes, SHA-256
`FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4` (measured);
manifest SHA-256 `894CD81CFFE0DEB3FD5A6D29A81CB0694A6A82E547542014191C0E1DAC31731F`
(equals the hash of `contracts/macula-sblgnt-matthew.unit1.json`). 56,488 nodes, no
duplicate `nodeId`, no leaf without `ref`.

Matthew 1:2 anchor `400010020050040`: `Rule=S-V-O`, `Cat=CL`, `Head="1"`, parent
`400010020010820` (Conj13CL). Direct children by ordinal: 0 `400010020050012` (S),
1 `400010020070012` (V), 2 `400010020080021` (O). The corpus holds 97 S-V-O nodes; all
have exactly the shape S,V,O and `Head="1"` and are eligible; 175 `Np-Appos` nodes.

## Exact membership

Independent leaf-descendant sets: anchor `!5,!7,!8,!9`; S `!5`; V `!7`; O `!8,!9`.
Components are non-empty, unique, pairwise disjoint, and the union equals the anchor in
both set-difference directions. Token `!6` (`δὲ`, `400010020060010`) is a leaf of
Conj13CL, not of the anchor; its expected output is the empty tuple. The ordinal envelope
`!5..!9` has `!6` as its only non-member.

## Component / Head

Head `"1"` selects the V child (ordinal 1). Production preserves raw Head text
(`"1"`), Rule and Cats. Mutations M11-M17 (Head `0`, `2`, `3`, `x`, absent, empty, `01`)
behave as: `0`, `2`, absent -> `()`; `3` (outside range), `x`, empty, `01` ->
`QueryError`. M18-M24 (rule case/trailing space/NULL/neighbour rule; swapped, altered or
NULL child Cats) -> `()`. M25-M28 (child count or ordinal damage) -> `()` or
`QueryError` explicitly (see I-2 for precedence).

## Identity reconstruction

Independently serialized identity (JSON array, `ensure_ascii=True`, compact separators,
UTF-8, SHA-256, `sha256:` prefix):
`sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087`, equal to the
production ID and the frozen fixture ID (computed before reading the fixture ID back).
Matthew 1:1!3 Apposition IDs reproduced from raw XML, nearest-first:
`400010010030020` = `sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c`;
`400010010030040` = `sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f`;
`400010010030060` = `sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220`.

Full-corpus production-versus-oracle comparison (all 18,329 Matthew tokens): 16,951 tokens
expected and returned `()`; 1,378 tokens with candidates produced 1,474 candidate
instances (523 S-V-O, 951 Apposition); **all 1,474 equal on every DTO field and on
`candidate_id`; 0 mismatches, 0 errors.**

## Sensitivity and invariance

With the audit-owned serializer, 28 single-field variants (all seven snapshot fields,
candidate kind, derivation kind and version, scope node, scope membership drop/add/order,
evidence id/order/role/kind, payload anchor/rule/Head, component role/Cat/ordinal/id/
members/order/count) all change the ID, and all 28 are pairwise distinct. A production
store whose `source_file.sha256` differs yields a different ID (M36). The ID is identical
across `PYTHONHASHSEED` 0, 1, 12345 and random, a different working directory, a
different process and repeated calls; every anchor member lookup returns an equal DTO
tuple. Start/End mutations (below) and semantic-annotation mutations do not change it.

## PK reallocation

Reduced stores (Matthew sentences 1-2) in modes identity, affine, descending, shuffle and
mixed remapped snapshot/book/file/sentence/tree/node/token/element keys with shuffled
insertion order; sibling order differs from child PK order, and token PK order differs
from `ref` order in affine/shuffle/mixed. Complete production results for 27 refs equal
the real-store results in every mode. The real store itself has negative, reverse-ordered
token PKs. Node IDs are only compared and serialized, never parsed (static review).

## Envelope forgery

Through the public Unit 8 Amendment 1 path (`create_evaluated_interpretation`):

| Attack | Result |
|---|---|
| A1 stale ID, `!6` added to anchor and O | `QueryError: candidate_id does not recompute from candidate echo` |
| A2 stale ID, scope gains `!6` only | `QueryError: clause component union must equal the exact scope` |
| A3 stale ID, Start/End-as-ordinal envelope `!5..!8` | `QueryError: candidate_id does not recompute ...` |
| B1 self-consistent ID, `!6` in anchor and O | `QueryError: candidate echo does not match source-grounded re-derivation` |
| B2 self-consistent ID, envelope `!5..!8` | same V2 rejection |
| B3 self-consistent ID, `!6` in anchor and V | same V2 rejection |
| B4 self-consistent ID, union != scope | `QueryError: clause component union must equal the exact scope` (V1) |

The genuine candidate is accepted by all four member-token lookups, the echo is
byte-for-byte unchanged, and `verify_evaluated_interpretation` passes offline and against
the source store. Unit 9 itself has no candidate-verify API (not a contract requirement).

## Public API behaviour

`MAT 1:2!99` -> `None`; `MAT 1:2!6` -> `()`; `MAT 1:1!3` -> 3 Apposition candidates;
malformed ref and missing database -> `QueryError` with no connection opened. Each call
that opens the store opens two read-only connections (query layer and structural layer);
all were closed on success, no-match and error paths. Inconsistent stores (M01-M04, M06,
M26, M28-M35) raise explicit `QueryError` (empty/missing/overlapping/union-mismatched
memberships, ambiguous or duplicate node IDs, dangling parent, wrong-tree membership,
incomplete or NULL coordinates; the token whose own coordinate was damaged, M34/M35, is
not found and returns `None`) and never yield a partial candidate. M05 (a consistently
smaller anchor and O) and M07 (see M-1) are self-consistent store edits and return a
candidate for the edited store; M05's removed token `!9` raises
`candidate anchor membership omits selected token`.

## Start/End firewall

M08 (Start/End `999`/`1`), M09 (`5`/`9`, an envelope containing `!6`) and M10 (NULL on
anchor and children) all return the identical candidate and ID
(`sha256:129c3970…ff087`). Production never reads `start_raw`/`end_raw` (static review).
Observation (I-1): raw Start/End are 0-based sentence word positions, not verse ordinals.

## Apposition regression

The 951 Apposition instances in the full corpus equal the independent oracle, including
the three frozen Matthew 1:1!3 IDs. The implementation diff did delete/generalise
Apposition-adjacent lines (evidence role literal, identity builder, ancestor scan), but
the Apposition DTO content and IDs are unchanged per the oracle.

## Matthew 1:1 Verbless firewall

Sentence `MAT 1:1!1-1:1!8`: `Rule=P2CL`, `ClType=Verbless`, 8 noun leaves, 0 verb leaves, no
S-V-O node. Production returns Apposition candidates only; no clause candidate and no
fabricated verb or copula.

## Semantic firewall

Static: no semantic-role, Actor/Action/Patient/Event/Result, confidence/probability/score
or theological identifiers; component roles are the closed `subject-component` /
`verbal-component` / `object-component` vocabulary; no Frame/SubjRef/Notes/Gloss/lemma
reads. Dynamic: 81 `xml_attribute` values on the anchor subtree (Frame, Gloss,
LexDomain, Mood, Tense, StrongNumber, UnicodeLemma, FunctionalTag, FormalTag, …) and
token mirrors (lemma, tense, case, gender, number, person, normalized form) were rewritten
in a store copy; the candidate DTO and ID are unchanged for all members.

## Read-only and persistence

An SQLite authorizer on every production connection observed only PRAGMA (`user_version`,
`query_only`, `foreign_keys`, `recursive_triggers`), SELECT and READ actions, 0 denied
actions (no write, DDL, ATTACH or transaction control). No `INSERT/UPDATE/DELETE/CREATE/
ATTACH`, file write or JSON dump exists in `structural_candidates.py`. The existing DB
and the repository tree were unchanged after every run; no sidecar files.

## Unit 8 compatibility

At `ddd23c4`, Unit 8 hard-coded `candidate_kind != "apposition"` and rejected the new kind
(AC-U9-24 as written). At HEAD the accepted Unit 8 Amendment 1 registry evaluates
`clause-structure/source-rule-s-v-o/1`; real candidate evaluation, V1/V2 and forgery
rejection were reproduced above. Existing Apposition evaluation behaviour is unchanged.

## Fixture provenance

Blob `adb1783d3527168c5dfa9c4d05abb539d9b05611`, SHA-256
`6986B8A0…9764C`; first and only commit `22595753` (freeze, before the implementation);
identical at `ddd23c4`, `ac215cb`, `86c1aad` and HEAD. The fixture is expected-only (no
production-generated content); the independently derived values equal it.

## Acceptance matrix

| AC | Result | Evidence |
|---|---|---|
| 01 one family `source-rule-s-v-o/1` | PASS | A, C, D |
| 02 status only `candidate` | PASS | C, A |
| 03 relational topology, not node-ID encoding | PASS | C (IDs never parsed), B (PK/ID mutations) |
| 04 children exactly S/V/O at 0/1/2 | PASS | A, B M22-M28 |
| 05 raw Head, `"1"` selects V | PASS | A, B M11-M17 |
| 06 exact materialized membership only | PASS | A, B M01-M10, C |
| 07 non-empty, unique, canonical order | PASS | A, B, full corpus |
| 08 pairwise disjoint | PASS | A, B M03 |
| 09 union equals anchor, both directions | PASS | A, B M02, M04 |
| 10 Matthew 1:2 scope `[5,7,8,9]`, excludes `!6` | PASS | A, full corpus |
| 11 `!6` cannot enter via Start/End/envelope | PASS | B M08-M10, A1-B3 |
| 12 independent raw-XML freeze compared | PASS | A (oracle equals fixture) |
| 13 evidence order anchor, S, V, O | PASS | A, full corpus |
| 14 payload preserves rule, Head, components | PASS | A, full corpus |
| 15 identity sensitivity | PASS | B (28 variants, M36) |
| 16 independence of PK, path, seed, time, order | PASS | B (5 PK modes), hash seeds |
| 17 every member lookup equal; `!6` not | PASS | A, B, full corpus |
| 18 Apposition unchanged | PASS | A, full corpus (951) |
| 19 read-only, schema version unchanged | PASS | C (authorizer), DB hash |
| 20 no persistence/DDL/sidecar | PASS | C |
| 21 no Actor/Action/semantic mapping | PASS | C, B (semantic mutation) |
| 22 no confidence/probability/score | PASS | C |
| 23 Matthew 1:1 Verbless negative | PASS | A, full corpus |
| 24 Unit 8 rejects until amendment | SUPERSEDED | C at `ddd23c4` true; later accepted Amendment 1 (see I-3) |
| 25 Unit 5 M1 / Unit 7 M1 unchanged | PASS | governance and diff review |
| 26 Phase not COMPLETE/CLOSED | PASS | governance review |

## Tests run (type D, last)

Unfiltered, current HEAD, existing DB read-only, all opt-in integration flags on
(`MACULA_UNIT{4..9}_INTEGRATION`, `MACULA_UNIT8_AMENDMENT1_INTEGRATION`, `MACULA_MATTHEW_DB`):
`python -B -m unittest` of Units 1, 2, 4, 5, 6, 7, 8, Unit 8 Amendment 1 and 9.

**Ran 295; 295 passed; 0 failures, 0 errors, 0 skipped.** By module: Unit 1 26, Unit 2
56, Unit 4 15, Unit 5 20, Unit 6 22, Unit 7 19, Unit 8 51, Unit 8 Amendment 1 44, Unit 9
42 (39 fast + 3 read-only integration). No obsolete-test filter was applied.
`python -B -m scripts.verify_unit1` and `python -B -m scripts.source_schema` exited 0.
**Unit 3 tests were NOT re-run** because default discovery performs a full Matthew build;
zero Matthew builds were performed by this audit. Unit 3 is not an input to Unit 9 beyond
the existing store (NOT INDEPENDENTLY VERIFIED in this audit).

## Findings

### BLOCKER

None.

### MAJOR

None.

### MINOR

- **M-1: contract section 16 token-6 fail-closed rule is not implemented.** Section 16
  lists "Matthew fixture token 6 appears in the anchor or a component membership" as a
  `QueryError`. Mutation M07 (a self-consistent store in which `!6` is added to both the
  anchor and the O child memberships) returns a candidate containing `!6` rather than
  raising. Production does not check per query that membership equals leaf-descendant
  ancestry, and has no token-specific rule; it relies on build/publication gates (Unit
  2/3 `validate_store`, the `expected_node_token_membership` view). Mitigations: the
  authoritative store is read-only;   non-self-consistent corruption (M01-M04, M06) is
    rejected, and V2 rejects forged candidate echoes (B1-B3); the genuine production store yields the correct result. Not remediated.

### INFORMATIONAL

- **I-1:** Raw Start/End are 0-based sentence word positions. For the anchor, Start 5 and
  End 8 are the positions of exactly `!5,!7,!8,!9`; reading them as verse ordinals would
  wrongly include `!6` and omit `!9`. The contract's "`!6` is inside the envelope" holds
  for the ordinal envelope `!5..!9`. The firewall conclusion is unaffected.
- **I-2:** A node whose child count is not three but whose Head is outside the child range
  raises `QueryError` (Head-range check precedes the shape check) instead of no match.
  Section 16 does not fix this precedence; the real corpus has no such node.
- **I-3:** AC-U9-24 and contract section 17 describe the pre-amendment state and are
  superseded by the accepted Unit 8 Amendment 1; the contract header and historical
  prose still say "pending independent acceptance"/"rejects". Frozen contract text was
  not rewritten.
- **I-4:** Each public call opens two read-only connections (query and structural layer);
  both are closed on every path.
- **I-5:** Production does not re-verify the stored snapshot against the pinned contract
  at query time (a different stored source hash yields a different, self-consistent
  candidate ID); source-revision pinning is an import/publication gate.

## Existing database preservation

Before and after the audit, all values were identical: size 160,968,704 bytes; SHA-256
`E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`; mtime_ns
`1793509059488056500`; `user_version` 2; schema cookie 51; 75 catalog rows (catalog hash
`e3a2d02c…b30`); 38 indexes (hash `0bdc6a55…3dfd7`); 23 triggers; row counts (book 1,
dataset_snapshot 1, node_token_membership 159,391, schema_version 1, sentence 1,134,
source_file 1, syntax_node 56,488, token 18,329, tree 1,134, xml_attribute 767,429,
xml_content 179,675, xml_element 59,891); no sidecar files. All mutation work used
disposable copies outside the repository.

## Protected repositories

`C:\Works\macula-greek` stayed at `main` `8423afe4…`, clean. `C:\Projects\bible-research-merged`
stayed at `master` `0e4c9baa…`, clean.

## Scope confirmation

This audit performed no remediation and no persistence, projection, source-schema change,
other-book/N1904/companion-source work, network acquisition, XmlPro/byte-range mapper,
BRW integration, semantic role/localization/UI work, or Unit 10. Unit 5 M1 and Unit 7
audit M1 were not changed. Unit 2 Amendment 1 independent acceptance, Unit 3 re-run and
any new Unit are not claimed.

## Final statements

Unit 9 is **IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS)**. The
Phase remains **AUTHORIZED**, not COMPLETE and not CLOSED. No further Unit is authorized
by this audit.
