# Product Implementation #1 Independent Acceptance Audit

Matthew Scripture Structural Explorer

## 1. Decision

**ACCEPT WITH MINOR FINDINGS.**

- Findings: **0 BLOCKER, 0 MAJOR, 1 MINOR (P1-M-1), 4 INFORMATIONAL (P1-I-1..P1-I-4).**
- AC-P1-01 through AC-P1-56: **55 PASS, 1 QUALIFIED (AC-P1-01), 0 observed FAIL**.
  The qualification is a historical-evidence limitation, not evidence of a dirty start.
- P1 through P12: **12 PASS** in independently executed checks.
- Product lifecycle: **IMPLEMENTED / INDEPENDENTLY ACCEPTED
  (ACCEPT WITH MINOR FINDINGS)**. This is product acceptance, not a research Unit.
- P1-M-1 is not remediated. Existing Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1,
  Unit 9 audit M-1 and Unit 11 audit M-1 remain unresolved and distinct.
- Unit 12 remains **NOT AUTHORIZED**. Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.

The minor finding concerns the home-page population-state label. It does not change
source data, membership, candidate identity, evaluations, supersession, or store access.
Acceptance does not certify the home label as correct or waive the finding.

## 2. Checkpoint, frozen contract and Git evidence

Audit date: 2026-11-03. Repository: `C:\Projects\MACULA-Extract`.

| Item | Independently observed value |
|---|---|
| Starting branch | `master` |
| Starting HEAD / audited implementation | `4f939462b1dc2ca84cdf87a9f6cc94fd2b43b790` |
| Implementation subject | `implement Product Implementation #1 Matthew Structural Explorer` |
| Implementation sole parent / required design freeze | `0a10c810b55da46d2358e3cd894ad59121d616bf` |
| Design-freeze sole parent | `7f46b1208e5b3dcbc9587a9cb6d4a4fb4d3a1a11` |
| Audit-start staged / unstaged / untracked state | none; `git status --porcelain=v1` was empty |
| Ignored repository artifact | existing `sblgnt-matthew.sqlite3` only |
| Implementation diff | 22 paths; 2,613 insertions, 19 deletions |
| Implementation whitespace gate | `git diff --check <freeze> <implementation>` passed |
| Frozen normative contract | sections 2-25 equal between freeze and implementation |
| Protected implementation paths | no changes in research code, schemas, fixtures, parser/contracts, old Unit tests/support, CB0, Unit contracts or historical audits |

The [frozen product contract](../product/PRODUCT-IMPLEMENTATION-1-MATTHEW-STRUCTURAL-EXPLORER.md)
was read in full. Its status changes and appended implementation section were treated
as claims, not proof. Normative sections 2-25 were compared with `git show` from the
design freeze, not merely with their current text.

The implementation changed exactly:

- Eleven production files: `product/__init__.py`, `__main__.py`, `config.py`,
  `errors.py`, `models.py`, `validation.py`, `adapter.py`, `wording.py`,
  `presentation.py`, `server.py`, `static/explorer.css`.
- Five new test files: the four `tests/product/test_product_*.py` modules and
  `tests/product/support/fixtures.py`.
- Six documentation paths: `README.md`, `AGENTS.md`, `tests/README.md`,
  `docs/architecture/README.md`, `docs/governance/PHASE-STATUS.md`, and the product contract.

No path outside the section 25 allowlist was present. Documentation changes update
product status/evidence; no research Unit decision changed. The audit did not rewrite
any implementation evidence, frozen contract, historical audit, or existing finding.

Current and checkpoint Git properties are independently observable. Git cannot
reconstruct the implementer's pre-edit untracked/index state or historical branch
name. No independently accessible implementation-session record was located.
Consequently that part of AC-P1-01 is qualified, rather than falsely certified.

## 3. Independent methodology and evidence identifiers

All audit executable code and structured intermediate observations lived in the
session workspace, outside Git. No product test helper was used to construct the
independent product fixture or its expected presentation/history.

| Evidence | Method |
|---|---|
| E1 | Git graph, exact changed-path inventory, frozen-body comparison, protected-path comparison, clean-start and preservation gates |
| E2 | Independent stdlib ElementTree parsing of pinned raw XML; independent `sqlite3` read-only queries; all 18,329 token surfaces and 22 optional fields compared |
| E3 | Independently authored adapter/rendering audit: 60 real verses, 1,008 product tokens, all 28 chapters, actual numbering gaps, all 18 Matthew 1:2 token selections |
| E4 | Independently seeded disposable projection: three real Apposition candidates, the frozen S-V-O candidate, six adversarial human evaluations; independently computed history edges/leaves |
| E5 | Invalid-input spies, ordered startup spies, one-query fan-out measurements, read-only connection/SQL traces, injected exception classes, mismatch and mid-read staleness checks |
| E6 | Route and real-socket adversarial checks: Host, duplicate Host, methods, HEAD, headers, fixed CSS, path traversal, CLI/configuration, absence and error states |
| E7 | New independent loopback browser server/fixture: rendered styles, keyboard navigation, token 6, Verbless, evaluation selection, controls/escaping, diagnostics, local resource requests |
| E8 | Independently executed existing product tests, required frozen verifiers, required core regressions, and all 25 opted-in core integration tests |

### 3.1 Independent source oracle

The source oracle traversed raw `Node` descendants and selected actual leaves with
`ref`. It sorted token references by parsed integer `(chapter, verse, ordinal)`.
It did not use a repository parser, source-query SQL, membership helper, candidate
deriver, or expected product output as its oracle.

Separately, read-only SQL joined `node_token_membership`, `syntax_node` and `token`.
It selected the exact anchor identity and ordered scripture coordinates. Both
oracles returned:

```text
anchor: 400010020050040
raw Rule: S-V-O; Cat: CL; Head: 1
exact scope: MAT 1:2!5, MAT 1:2!7, MAT 1:2!8, MAT 1:2!9
S component: MAT 1:2!5
V component: MAT 1:2!7
O component: MAT 1:2!8, MAT 1:2!9
excluded interior token: MAT 1:2!6
```

All 18,329 raw leaf refs equal the SQLite token-ref set. Every surface and 22
optional fields agreed, including `Unicode`, `NormalizedForm`, `UnicodeLemma`,
`FunctionalTag`, `FormalTag`, source `Ref`, `xml:id`, `morphId`, morphology and
source gloss/enrichment fields. This is independent targeted source-mirror
evidence, not a new full Unit 3 round-trip certification.

The product comparison sampled the first and last existing verse of every chapter
plus targeted verses. It independently checked 60 verses / 1,008 tokens against raw
XML, including order, surfaces and separate fields. Actual gaps Matthew 17:21,
18:11 and 23:14, and Matthew 99:99, were independently absent; nearby real verses
continued to work. No enumeration behavior was added to production.

### 3.2 Disposable histories and adversarial inputs

The independent fixture was populated only in a system temporary directory through
accepted public Unit 10 writers. Real source candidates were fixture inputs, not
product live derivation. Synthetic evaluation labels/notes were audit data only:
no existing projection was provisioned and no production evaluation was authored.

History specification: two opposing independent evaluations, a two-successor fork,
a further successor on one branch, and another independent evaluation. Expected
edges and leaves were calculated from the declared predecessor pairs, without
Unit 11's graph helpers. Results: **six evaluations, three edges, four leaves**.
All six evaluation selections preserved all six cards and all four leaf labels.
An evaluation-only URL also resolved its candidate without hiding other records.

Human notes included HTML-shaped text, Markdown-shaped links, every C0/C1 character,
all U+202A-U+202E and U+2066-U+2069 controls, LF and TAB. Valid human labels included
HTML-shaped text and bidi controls. The accepted core rejects C0/C1 evaluator labels;
that existing boundary was respected, not bypassed.

In-memory adversarial view models additionally checked absent versus present-empty,
escaped source fields, an unchanged combining-mark surface, and a member ref in
another verse. The latter remained card text and never became a displayed verse
token. No claim is made that this artificial cross-verse model was a persisted,
source-verified candidate.

### 3.3 Runtime and transport checks

- Forty-one malformed/unsupported route cases and three invalid direct selections
  were rejected before any permitted core call. Tests included 20/4,301-digit
  selectors, overflow, signs, leading zeros, non-ASCII digits, repeats, unknown
  parameters, malformed UTF-8/percent escapes and invalid ids.
- Startup sequence was exactly source gate, offline projection verification,
  source-grounded verification. A selected Matthew 1:2 page made one source verse
  read, 18 ancestry reads, one combined Unit 11 history query, and four distinct
  evidence-node reads; no repeated startup verification.
- Traced disk connections used URI `mode=ro`; trace evidence contained
  `query_only=ON`, `foreign_keys=ON`, `recursive_triggers=ON`, and no disk DML/DDL.
  Accepted-core internal in-memory schema verification was not misclassified as
  a product database.
- Independently configured missing/invalid/empty/unconfigured stores remained
  distinct. A real-snapshot projection paired with a reduced temporary source
  failed source binding and suppressed projection data, while source display worked.
- Changes to a temporary projection's mtime latched binding failure; restoring its
  original fingerprint did not automatically re-verify. A change during evidence
  reads also suppressed all projection data.
- QueryError/ProjectionQueryError, ValueError, AttributeError and RecursionError
  injections verified class/stage classification, visible errors, sanitized
  logging, source/projection independence, and no success-shaped empty fallback.
  An unresolved candidate evidence node produced an integrity notice and withheld
  selected candidate/history details.
- Invalid Host values and duplicate Host headers were rejected; eight non-read
  methods returned 405. HEAD preserved GET headers/status/content length with no
  body. Traversal did not expose a file; only the fixed stylesheet was served.
- Configuration checks rejected non-loopback hosts and identical store paths with
  usage exit 2; CLI/environment precedence and disabled projection configuration
  were exercised. Missing store paths were not created.
- Independent AST inspection found exactly the eight permitted imported core names,
  only in `adapter.py`; no product SQL, private/write/derive API, third-party
  framework, JavaScript, file write, or evaluation-authoring control.

## 4. Independent browser evidence

The previously shared browser snapshot was not accepted as evidence. No listener
was found on its advertised port. A fresh, bounded audit helper bound to
`127.0.0.1:58058`, returned HTTP 200, and used a new disposable projection.
No unrelated service was stopped or modified.

Independently observed in the browser:

- Eighteen Matthew 1:2 Greek token elements, only `!5,!7,!8,!9` with member markers,
  component labels, tinted backgrounds and solid underline bars.
- Token 6 had no member marker/component label, a transparent background and no
  member bar. Keyboard Tab gave it a visible solid focus outline; Enter selected
  it, left zero candidate cards and zero members, and showed an ABSENT selection
  notice for the previously selected S-V-O candidate.
- Three labelled epistemic regions, six simultaneous evaluation cards, four
  simultaneous `Not superseded` labels. Selecting an evaluation emphasized only
  that card but retained the others.
- Zero script/image/iframe elements despite adversarial notes/labels. Six rationale
  `bdi` blocks displayed literal HTML/Markdown-shaped text and visible `U+XXXX`
  controls. Greek source surfaces remained untouched.
- Direct form navigation to Matthew 1:1 showed exactly eight Greek surfaces,
  `ClType: Verbless`, its neutral source explanation, and three persisted
  Apposition cards. No synthetic copula/verb or semantic-role terms appeared in
  the source region. Selecting an unevaluated Apposition showed `Not evaluated`.
- Diagnostics opened and exposed candidate identities and all seven snapshot
  fields. Browser resource timing listed only the loopback stylesheet.
- Returning home independently reproduced P1-M-1.

Computed-style observations, keyboard interaction and screenshots supplemented
DOM/accessibility evidence; an implementation browser claim was never substituted.
The helper exited normally after a stop signal, verified both stores unchanged,
closed the server, and removed its temporary fixture directory.

## 5. Mandatory product scenarios

| Scenario | Result | Independent evidence |
|---|---|---|
| P1 | PASS | Raw-backed eight-token Matthew 1:1; source Verbless; no fabricated verb/copula/semantic entity; persisted Apposition |
| P2 | PASS | Raw XML, SQL, adapter, every token's markup and actual browser styles agree on `!5,!7,!8,!9`; `!6` plain |
| P3 | PASS | Unevaluated real Apposition retains its card; history is `Not evaluated`, not undetermined/rejected |
| P4 | PASS | Opposed accepted/rejected records coexist with no winner or count |
| P5 | PASS | Independent fork/chain graph has four simultaneous leaves, all `Not superseded` |
| P6 | PASS | New valid empty temporary projection preserves source UI and exact empty-selection wording |
| P7 | PASS | No configured projection preserves source UI and neutral not-configured wording |
| P8 | PASS | Invalid and missing projections produce store errors, never no-candidate success |
| P9 | PASS | Actual source gaps and MAT 99:99 return ABSENT, not corruption |
| P10 | PASS | Malformed route/direct selectors reach zero core calls |
| P11 | PASS | Real snapshot mismatch and stale/mid-read fingerprints suppress projection data; source UI remains |
| P12 | PASS | Sweep of all 18 token selections plus browser keyboard selection excludes token 6 from candidate/component membership |

## 6. AC-P1-01 through AC-P1-56

PASS means the criterion's product behavior/boundary was independently verified.
It does not assert perfection of every neighboring surface. P1-M-1 is a separate
section 11.1 population-state presentation defect, not a false PASS for the
failed/stale-store suppression required by AC-P1-19.

| Criterion | Result | Evidence / assessment |
|---|---|---|
| AC-P1-01 | QUALIFIED | E1: exact required sole parent, current master/clean tree; historical branch/index/untracked start cannot be reconstructed (P1-I-1) |
| AC-P1-02 | PASS | E1/E6: no new Unit 12 paths, lifecycle row, code or tests; existing NOT AUTHORIZED wording is not implementation |
| AC-P1-03 | PASS | E1/E6/E7: stdlib HTTP server and server-rendered HTML/CSS |
| AC-P1-04 | PASS | E1/E6: no dependency/config/JS/build-system additions or installed packages |
| AC-P1-05 | PASS | E5/E6: AST confirms adapter alone imports scripts |
| AC-P1-06 | PASS | E5/E6: exact closed core imports/calls; no private/write/derive API |
| AC-P1-07 | PASS | E3/E5: recursively inspected returned trees contain product models, never core DTOs/exceptions |
| AC-P1-08 | PASS | E3/E5/E7: stable keys; no local PK fields or full paths in models-as-identity, URLs, rendered text or class-only logs |
| AC-P1-09 | PASS | E5/E6: exact MAT validation, non-MAT unsupported before core |
| AC-P1-10 | PASS | E5/E8: independent AST and executed implementation structural tests |
| AC-P1-11 | PASS | E1/E2/E8: source size/mtime/hash and no sidecars preserved |
| AC-P1-12 | PASS | E4/E7/E8: independent and implementation fixture projections preserved byte-for-byte |
| AC-P1-13 | PASS | E1/E5: no product database, preference, cache or config write |
| AC-P1-14 | PASS | E1/E5/E7: no provisioning, initialization, persistence or authoring control in product |
| AC-P1-15 | PASS | E5: route/direct grammar rejection and zero-core-call spies |
| AC-P1-16 | PASS | E5: oversized and 4,301-digit forms blocked; accepted inputs passed as bounded integers |
| AC-P1-17 | PASS | E5: startup gate order and once-only verification; home-state caveat P1-M-1 does not alter verification |
| AC-P1-18 | PASS | E5: immutable process-only binding; latched changed fingerprints |
| AC-P1-19 | PASS | E5/E6: failed/stale bindings and invalid stores never become no-candidate success; separate home-label defect P1-M-1 |
| AC-P1-20 | PASS | E3/E7: three labelled, independently addressable epistemic sections/badges |
| AC-P1-21 | PASS | E3/E7: source rule, derived candidate and human disposition not conflated |
| AC-P1-22 | PASS | E3/E4/E7: Candidate status separate from Evaluation disposition |
| AC-P1-23 | PASS | E2/E3/E7: every displayed token classified by exact ref |
| AC-P1-24 | PASS | E3/E5/E7: no envelope/wrapper/range propagation; CSS and renderer inspected |
| AC-P1-25 | PASS | E2/E3/E7: mandatory raw/SQL membership and actual visual states |
| AC-P1-26 | PASS | E3/E7: all 18 selections; token 6 absent from S-V-O cards/components/member styles |
| AC-P1-27 | PASS | E2/E3/E7: eight real Matthew 1:1 tokens and exact Verbless explanation |
| AC-P1-28 | PASS | E2/E3/E7: no fabricated source copula/verb/semantic entity; mandatory order-note wording is not one (P1-I-4) |
| AC-P1-29 | PASS | E3/E7: zero evaluations displays Not evaluated |
| AC-P1-30 | PASS | E4/E7: opposing evaluations coexist without summary/winner |
| AC-P1-31 | PASS | E4/E7: graph independently computed, all four leaves labelled |
| AC-P1-32 | PASS | E3/E7: no authored Current/Latest/Final/Canonical/Preferred/Winning wording |
| AC-P1-33 | PASS | E3/E5/E7: no authored semantic-entity labels/mapping |
| AC-P1-34 | PASS | E3/E5/E7: no scoring/ranking/count presentation; mandatory anti-rank note treated literally (P1-I-4) |
| AC-P1-35 | PASS | E4/E7: escaped source/human text, all specified controls, bdi, no generated links/translation |
| AC-P1-36 | PASS | E2/E3/E7: all source mirrors; 1,008 product surfaces; combining-mark render; distinct normalized/unicode/lemma |
| AC-P1-37 | PASS | E2/E3: optional raw equality plus explicit absent/present-empty model/render cases |
| AC-P1-38 | PASS | E3/E5/E7: coordinate-only form; actual gaps; no production enumeration or Previous/Next |
| AC-P1-39 | PASS | E3/E6: real source with no projection |
| AC-P1-40 | PASS | E4/E6: valid empty projection and exact persisted-selection wording |
| AC-P1-41 | PASS | E4/E5/E6: missing/invalid/corrupt projection is an error |
| AC-P1-42 | PASS | E2/E3/E6: absent coordinates/actual gaps are ABSENT |
| AC-P1-43 | PASS | E5: all malformed cases blocked before core |
| AC-P1-44 | PASS | E5: closed error enum; class/stage-only mapping; sanitized errors/logs |
| AC-P1-45 | PASS | E5: one Unit 11 query with token/candidate/evaluation selected; in-memory selection and all-token sweep |
| AC-P1-46 | PASS | E6/E7/E8: loopback config/live socket, Host/duplicate Host, methods, HEAD, fixed CSS, security headers; existing IPv6 test executed |
| AC-P1-47 | PASS | E5/E6/E7: stdlib/local resources; no external-service/session/auth/telemetry code |
| AC-P1-48 | PASS | E1/E6: CLI/env-only configuration, precedence and identical-path usage rejection |
| AC-P1-49 | PASS | E3/E4/E7: event keys absent; full logical ids and seven snapshot fields available |
| AC-P1-50 | PASS | E8: four test-layer files and repository-root stdlib discovery work |
| AC-P1-51 | PASS | E1/E8: opted-in integration only; zero full builds; no Unit 3 discovery or second-build enablement |
| AC-P1-52 | PASS | E1: every protected path byte-identical to freeze |
| AC-P1-53 | PASS | E8: both required verifiers, 376-test default regression and all 25 skipped integrations independently executed |
| AC-P1-54 | PASS | E1: old finding/audit/code bytes untouched; unresolved statuses retained |
| AC-P1-55 | PASS | E1: product-only lifecycle update, no research Unit change; Phase AUTHORIZED |
| AC-P1-56 | PASS | E1/E7/E8: no generated artifacts committed, no repository sidecars/bytecode, protected repositories unchanged |

## 7. Independent test executions

Environment actually executed: CPython **3.13.7**, SQLite **3.50.4**, Windows.
No installation, restore, download, upstream fetch, full Matthew build or second-build
gate was performed. Commands used `python -B`.

| Execution | Independently observed result |
|---|---|
| `python -B -m scripts.verify_unit1` | exit 0; pinned revision/path/hash, raw fixture and exclusion controls PASS |
| `python -B -m scripts.source_schema` | exit 0; schema version 2, SQLite 3.50.4, empty-only verifier PASS |
| `python -B -m unittest tests.test_unit1 tests.test_unit2 tests.test_unit4 tests.test_unit5 tests.test_unit6 tests.test_unit7 tests.test_unit8 tests.test_unit8_amendment1 tests.test_unit9 tests.test_unit10 tests.test_unit11` | 376 ran in 112.087s; 351 passed, 25 explicit integration skips; no failures/errors |
| `python -B -m unittest discover -s tests\product -p "test_product_*.py"` | 43 ran in 52.691s; 42 passed, 1 explicit integration skip; no failures/errors |
| Same discovery for `test_product_integration.py`, with `MACULA_PRODUCT1_INTEGRATION=1` | 1 passed in 5.383s; no skips/failures/errors |
| Selected Unit 4-11 real-Matthew integration classes, all owning opt-in flags enabled | 25 passed in 13.873s; no skips/failures/errors |
| Independently authored audit harness, final execution | 16 checks ran in 50.686s; no skips/failures/errors or ResourceWarning; includes successful reproduction of P1-M-1, not 16 assertions of defect-free behavior |
| Fresh bounded browser helper | startup/readiness, independent interactions and post-use preservation PASS; normal exit and fixture cleanup |

The core integration command selected `Unit4MatthewIntegrationTests` through
`Unit11MatthewIntegrationTests` in their respective modules, plus
`Unit8Amendment1MatthewIntegrationTests`. Environment opt-ins were
`MACULA_UNIT4_INTEGRATION` through `MACULA_UNIT11_INTEGRATION`, and
`MACULA_UNIT8_AMENDMENT1_INTEGRATION`, all `1`. Source was the existing local Matthew
store; no rebuild or active-test filtering.

Default core skips by owning suite: Unit 4 (4), Unit 5 (4), Unit 6 (3), Unit 7 (3),
Unit 8 (1), Unit 8 Amendment 1 (3), Unit 9 (3), Unit 10 (3), Unit 11 (1).
Those exact 25 integration cases subsequently passed in the selected integration
execution. These are separate executions, not a fabricated combined test-run count.

Two initial independent-harness setup attempts ran zero tests: unchanged Unit 8
validation rejected control-bearing evaluator labels, then a cross-evaluator
supersession fixture. Only the audit fixture was corrected. An intermediate
14-check execution passed in 15.419s but exposed a ResourceWarning in the auditor's
own read-only SQLite oracle connection. Explicit connection closing corrected it.
The final 16-check execution above supersedes that intermediate result. Production,
core and existing tests were never altered to make the audit pass.

## 8. Findings

### P1-M-1 - MINOR: home header reports VERIFIED_EMPTY for a populated store

**Confidence: 10/10. Unresolved; no remediation performed.**

Locations: [adapter.py](../../product/adapter.py), lines 129-156 and 282-289;
[presentation.py](../../product/presentation.py), lines 283-286.
Contract reference: sections 11.1, 11.3 and 12.

After successful startup, the retained binding state is always `VERIFIED_EMPTY`.
A populated verse response replaces only its local status with
`VERIFIED_POPULATED`; the retained state stays empty. `home()` reports the retained
state without any verse query.

Independent reproduction with a valid four-candidate/six-evaluation temporary store:

```text
adapter.home().status.projection_state                 VERIFIED_EMPTY
adapter.load_verse(ProductSelection("MAT", 1, 2))
    .projection.state                                 VERIFIED_POPULATED
adapter.home().status.projection_state                 VERIFIED_EMPTY
GET / header: Source: READY | Structural interpretation store: VERIFIED_EMPTY
```

The fresh browser reproduced the same home header and then showed three Apposition
cards / `VERIFIED_POPULATED` after direct form navigation to Matthew 1:1.

`VERIFIED_EMPTY` is defined as a verified store whose verse query returned zero
candidates, not as a generic successful/unqueried binding. This header can mislead a
user about population, including after viewing existing candidates. It does not
hide candidates from a loaded verse, turn a store failure into emptiness, claim
derivability completeness, or weaken source binding. Therefore MINOR, not MAJOR.
Any correction or design clarification requires separate authorization.

### P1-I-1 - INFORMATIONAL: historical clean-start evidence is limited

Git independently proves the exact sole parent, tracked-path boundary and current
clean master state, but not historical untracked/index cleanliness or the branch
name when implementation began. Implementation prose is not independent evidence.
AC-P1-01 is explicitly QUALIFIED for that component; no dirty-start violation was
observed. Acceptance does not invent historical evidence.

### P1-I-2 - INFORMATIONAL: runtime/platform coverage is bounded

Actual execution was Windows / Python 3.13.7 / SQLite 3.50.4. Product Python files
also parsed under Python 3.10 grammar. This is not actual execution on Python 3.10,
Linux or macOS, and no claim of independent cross-platform certification is made.
No unsupported-runtime defect was observed.

### P1-I-3 - INFORMATIONAL: binding fingerprints are not tamper-proof

The frozen `(size, mtime_ns)` policy was implemented and tested, including latching
and mid-read changes. Equal-size content replacement with deliberately restored
mtime is outside that invalidation guarantee; fingerprints are not cryptographic
continuous source certification. The accepted startup/core verification boundary
and frozen local-use design remain unchanged. This is a documented design limit,
not authorization to modify stores or introduce a new verification algorithm.

### P1-I-4 - INFORMATIONAL: required note takes precedence over literal term scans

Section 17 mandates:
`Listing order carries no meaning; it is not time, rank, quality or authority.`
It necessarily contains both `is` and `rank`. AC-P1-28/34 cannot consistently be
read as banning those substrings in that exact required note. The audit required
the note unchanged and checked that no source copula/verb, ranking, metric or score
was fabricated. Data-authored strings were likewise not treated as application
claims. No contract text was changed or semantic/scoring prohibition weakened.

## 9. Preservation and acceptance checkpoint boundary

| Protected resource | Before/after independent evidence |
|---|---|
| Source store | 160,968,704 bytes; mtime_ns `1793509059488056500`; SHA-256 `e52db7e2abdb1c2b9b4f93060312587a1363066378b7a0c9b8fb72475c25ce7e`; no WAL/SHM/journal |
| Raw upstream XML | 14,115,918 bytes; mtime_ns `1793460807178931500`; SHA-256 `fe1a8fed24dec268a0d04160ec15babdbe90105fffdb915fd041b572c1fc40f4`; unchanged |
| Independent projection fixture | 61,440 bytes; mtime_ns `1793673873505895700`; SHA-256 `95855e50952243467782de68fd1e479ff30063fa732303c2483435591f3586f9`; unchanged after all independent reads, then removed |
| Independent browser projection | before/after size, mtime, SHA-256 and sidecars equal; fixture directory removed |
| Upstream repository | HEAD `8423afe47b9e8f24b7772e808af45c7159a6fe7e`; clean before/after; no modification/acquisition |
| Downstream repository | HEAD `0e4c9baad299f7149cc71b35bcd5208297d4f8c0`; clean before/after; no integration/modification |
| Repository generated artifacts | no WAL/SHM/journal/bytecode found; existing source binary remains ignored and uncommitted |

The independent acceptance checkpoint changes only this new audit and
[PHASE-STATUS.md](../governance/PHASE-STATUS.md)'s product acceptance status/evidence.
Implementation documentation remains historical checkpoint evidence; its pending
acceptance text is superseded by the current lifecycle record, not rewritten.
No research Unit status or old finding changes.

Required acceptance sole parent: `4f939462b1dc2ca84cdf87a9f6cc94fd2b43b790`.
The actual resulting SHA is reported only after commit. Post-checkpoint gates must
verify that parent, exact two-path delta, clean staged/unstaged/untracked state,
whitespace, protected bytes, source hash/mtime/size/sidecars, protected repository
HEAD/status and helper/fixture cleanup.

**Stop:** after this independent product acceptance checkpoint and its verification.
No finding remediation, Unit 12, semantic projection, BRW integration, localization,
provisioning, evaluation authoring, or other downstream implementation is authorized
or performed by this audit.
