# Product Implementation #1 - Matthew Scripture Structural Explorer

## 1. Status

**DESIGN FROZEN / NOT IMPLEMENTED.** Implementation requires a separate explicit user
authorization (section 25).

This is a **product design + implementation-authorization contract**. It is a consumer
track document governed by [Consumer Baseline v0](../architecture/CONSUMER-BASELINE-V0.md)
(CB0). It is not a research Unit, not "Unit 12", not an API/schema/semantic version and not
a change to CB0. Where this contract quotes CB0 behavior, CB0 remains the authority.

| Item | State at this checkpoint |
|---|---|
| Product Implementation #1 | **DESIGN FROZEN / NOT IMPLEMENTED** |
| Consumer Baseline v0 | FROZEN, unchanged (byte-identical to the starting checkpoint) |
| Units 1-11 | statuses unchanged ([PHASE-STATUS](../governance/PHASE-STATUS.md)) |
| Unit 11 | IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS) |
| Unit 12 | **NOT AUTHORIZED** |
| Phase | **AUTHORIZED**; not COMPLETE, not CLOSED |

This contract creates no finding, remediates no finding and changes no frozen contract or
audit. Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1, Unit 9 audit M-1 and Unit 11 audit M-1
remain unresolved and distinct.

## 2. Purpose

Turn the independently accepted research core into the smallest genuinely useful personal
application: a **local, single-user, read-only, Matthew-only** explorer in which one user can

1. choose a Matthew chapter and verse by coordinate;
2. read the Greek verse in canonical scripture order;
3. inspect individual token linguistic facts;
4. discover **persisted** structural candidates associated with the selection;
5. inspect candidate exact membership and structural evidence;
6. inspect **all** persisted human evaluations of a candidate;
7. inspect supersession history and unsuperseded graph leaves;
8. always see whether information is **SOURCE FACT**, **DERIVED STRUCTURAL CANDIDATE** or
   **HUMAN EVALUATION**;
9. inspect stable logical identities and provenance on demand;
10. distinguish empty, absent, unsupported, unconfigured and corrupt-store states.

The product stays useful with no projection store, an empty one or a partially populated one.

## 3. Starting baseline

Verified from Git and the working tree before design (not trusted from the task text):

| Check | Result |
|---|---|
| Repository root / branch | `C:/Projects/MACULA-Extract` / `master` |
| HEAD | `7f46b1208e5b3dcbc9587a9cb6d4a4fb4d3a1a11` (`freeze consumer baseline v0`) |
| HEAD sole parent | `679ff2f61b255680d209bfd5e759af619fe6cbcc` (`independently accept Unit 11 discovery and history queries`) |
| Staged / unstaged changes | none |
| Untracked | one pre-existing malformed-name file (`MACULA-Extractdocsgovernance...PHASE-STATUS.md...`); user content, not touched, not part of any checkpoint |
| Ignored artifacts | `sblgnt-matthew.sqlite3` (source store, 160,968,704 bytes, SHA-256 `E52DB7E2...25CE7E`) |
| Environment | Python 3.13.7, SQLite 3.50.4; **not installed**: Flask, FastAPI, Jinja2, pytest; installed but irrelevant: numpy, pandas, scikit-learn; Node 22.16 exists but is not used; stdlib `tkinter` 8.6 present |
| Packaging | no `pyproject.toml`, `requirements.txt` or `package.json` in the repository |

Lifecycle at the starting checkpoint: Units 1-11 as recorded in PHASE-STATUS; CB0 FROZEN;
Product Implementation #1 not implemented; Unit 12 NOT AUTHORIZED; Phase AUTHORIZED.

## 4. Product scope

In scope (all read-only, Matthew-only, local):

- coordinate-driven verse selection (GAP-1 handled by direct entry, section 13);
- Greek token display from source `surface`, in canonical scripture order;
- token detail: BASELINE source fields; ADVANCED fields behind a native `<details>` toggle;
- source clause nodes for the displayed verse (Matthew 1:1 `ClType: Verbless`);
- **persisted** candidate discovery for the verse and for a selected token;
- candidate exact scope, evidence, kind-specific payload and provenance;
- all persisted evaluations, graph-leaf labelling and supersession edges;
- a diagnostics surface (`candidate_id`, `evaluation_id`, `source_snapshot`);
- the closed error/empty-state set of section 18.

Out of scope: section 24.

## 5. Chosen execution architecture

**Decision: Option A - a local, server-rendered Python web application with no
browser-side code**, using only the Python standard library. One process, one language, one
entry point; the browser is a plain document viewer.

| Option | Dependencies | Direct reuse of Python core | Serialization boundary | UI complexity | Testability | Startup / install | DTO-coupling risk | Verdict |
|---|---|---|---|---|---|---|---|---|
| **A. Local Python-rendered web app (stdlib)** | none | direct | none (view models only) | low: HTML + one CSS file, no JS | high: pure `handle_request` function, no sockets/browser needed | `python -B -m product ...` | contained by adapter | **CHOSEN** |
| B. Local Python JSON API + browser frontend | needs a JS frontend, realistically Node/npm or hand-written JS | direct | JSON wire format to design, freeze and test | high (client state, escaping on a second boundary) | medium: two runtimes | two moving parts | high (DTOs leak into wire format) | rejected: more parts, a second boundary, no capability gain |
| C. Desktop/native (e.g. `tkinter`) | stdlib, no new package | direct | none | medium-high: per-token styled marking and a three-panel layout in Tk widgets | low: needs a display; no headless route-level tests | `python -m ...` | contained | rejected: exact-membership visuals and state tests are costlier than HTML; no headless presentation tests |
| D. Static frontend + separate local data service | JS frontend, a service process | via the service | JSON API | high | medium | two processes | high | rejected: strictly more parts than B for no benefit |
| E. Terminal/CLI explorer | none | direct | none | low | high | trivial | contained | rejected as primary: poor fit for the three-panel and per-token membership contract; the Windows console already raised `UnicodeEncodeError` on Greek surfaces under the default `cp1252` code page during design probing |

Why A satisfies the rules: fewest new moving parts; the SQLite paths stay on the local
process; read-only is enforced by the accepted core (`mode=ro`, `query_only`) plus an
adapter that owns no SQL; the thin-adapter / UI boundary is a Python package boundary;
no JavaScript build system is required; all interaction state (verse, token, candidate,
evaluation) lives in the URL query string, so there are no cookies, sessions or client
state.

A future change of presentation technology (for example a JSON API for another client)
would reuse the adapter and view models unchanged and would not touch CB0.

## 6. Chosen runtime / framework / dependency boundary

| Item | Frozen decision |
|---|---|
| Runtime | CPython >= 3.10 (verified 3.13.7), SQLite >= 3.37 (verified 3.50.4), Windows/Linux/macOS portable |
| HTTP | stdlib `http.server.HTTPServer` (single-threaded) wrapping a transport-independent `handle_request(...)` |
| Rendering | server-side string rendering with stdlib `html.escape`; no template engine |
| Styling | one static stylesheet served by the app itself; no CDN, remote fonts, scripts or images |
| Client code | **none**: no JavaScript, no inline event handlers, no build step |
| Third-party packages | **none**. No ORM, no web framework, no second database, no Node/npm |
| New dependency/config files | **none authorized**: no `pyproject.toml`, `requirements*.txt`, `package.json`, lock file or config file |
| Implementation prerequisites | none: every required runtime facility is already present offline |

No package was installed, downloaded or enabled by this design task.

## 7. Product layering

```text
ACCEPTED RESEARCH CORE   scripts/source_query.py, scripts/projection_query.py,
        |                scripts/projection_store.py (verify_projection_store only)
        v
PRODUCT ADAPTER          product/adapter.py   (the only module that imports scripts.*)
        |
        v
PRODUCT VIEW MODELS      product/models.py    (frozen, immutable, no core DTOs, no surrogate IDs)
        |
        v
PRESENTATION / UI        product/presentation.py, product/server.py, product/static/
```

Rules:

- The UI/presentation code imports only `product.models`, `product.errors` and
  `product.wording`. It never imports `scripts` and never calls a research-core function.
- The adapter is not an interpretation layer: it translates, classifies, batches and labels.
- A structural test enforces the import boundary (AC-P1-10).

## 8. Adapter contract

`product/adapter.py` exposes a small class (for example `ExplorerAdapter`) constructed from
a `ProductConfig` and returns **only** view models or `ProductError` values; it never lets a
core DTO or core exception escape.

### 8.1 Permitted core surface (closed list)

| Core call | Used for |
|---|---|
| `source_query.get_verse` | verse + tokens (canonical order); startup source gate (MAT 1:1) |
| `source_query.get_ancestors_by_token` | distinct source syntax nodes of the verse (clause nodes) |
| `source_query.get_node` | resolving candidate evidence `source_node_id`s |
| `projection_query.get_structural_interpretation_histories_for_selector` with `ScriptureSelector("MAT", chapter, verse)` | **the single projection query per verse page** |
| `projection_store.verify_projection_store` | the one-time startup binding gate (section 11.3); no other `projection_store` name |
| `source_query.QueryError`, `projection_query.ProjectionQueryError` | exception classification only |

Everything else - `get_token`, `get_source_evidence`, `get_children`, `get_members`,
`get_persisted_*`, `list_*`, `derive_structural_candidates`, all Unit 10 write APIs, Unit 8
`create_evaluated_interpretation`, `projection_store.get_candidate/get_evaluation/
list_evaluations_for_candidate`, `source_fidelity`, private (`_`-prefixed) names and the
incidental `projection_query` attributes `store`, `structural`, `evaluated` - is **not
permitted** in Product #1. Adding a permitted call requires a contract amendment.

### 8.2 Responsibilities (MAY)

Pre-validate selectors (section 13.2); call the permitted core surface; combine source and
projection reads; classify errors into section 18 categories; hide local SQLite surrogate
IDs; map DTOs into immutable view models; attach the epistemic class; preserve stable
logical identities and provenance; filter an already-discovered result in memory by **exact
set membership of a token ref** (this is selection filtering, not candidate derivation);
batch queries.

### 8.3 Prohibitions (MUST NOT)

Query tables with SQL (no `sqlite3` import anywhere under `product/`); call private
helpers; call any write API; derive candidate existence when presenting persisted discovery;
modify, widen, narrow or "fill" membership; decide which evaluation is correct; derive
confidence, counts-as-scores, consensus or rank; generate semantic roles; translate,
summarize or reinterpret rationale notes; invent source facts; mutate either store; open a
database other than the two configured stores; write any file.

### 8.4 Request flow for one verse (fan-out budget)

1. Pre-validate coordinates (no core call on failure).
2. Source: one `get_verse` (absent -> ABSENT, stop; no projection call), then one
   `get_ancestors_by_token` per verse token (indexed, low-millisecond source queries; the
   per-token calls are bounded by the verse token count).
3. Projection (only if the binding is VERIFIED, section 11.3): **exactly one** Unit 11 call,
   `get_structural_interpretation_histories_for_selector`, returning candidates,
   evaluations, supersession edges and graph-leaf ids together.
4. Token / candidate / evaluation selection is **filtered in memory from that single result**.
   Selecting a token, candidate or evaluation causes **no additional Unit 11 call**.
   Selecting a candidate adds only `get_node` source calls for its evidence nodes.

Fan-out of `discover -> N candidate lookups -> N evaluation lookups -> N history lookups` is
prohibited (CB0 GAP-4). No result cache is part of v1; if later added it must be
process-memory only, keyed to the configured paths and discarded when they change, never an
authority and never required for correctness.

## 9. Application configuration

Frozen decision: **command-line arguments, with environment-variable fallback; no
configuration file.** This is the simplest auditable option: nothing machine-specific is
tracked, no gitignored file must be managed and nothing is stored in either database.

| Setting | CLI argument | Environment fallback | Rule |
|---|---|---|---|
| `source_db_path` | `--source-db PATH` | `MACULA_EXPLORER_SOURCE_DB` | required |
| `projection_db_path` | `--projection-db PATH` | `MACULA_EXPLORER_PROJECTION_DB` | optional; absent = "not configured" |
| `host` | `--host ADDR` (default `127.0.0.1`) | none | loopback literals only (`127.0.0.1`, `::1`); anything else refuses to start |
| `port` | `--port N` (default `8765`; `0` = OS-assigned, for tests) | none | integer 0-65535 |

- CLI overrides environment; an empty or whitespace-only value counts as not set.
- Paths are resolved to absolute paths once at startup and held in memory only.
- Missing `--source-db` -> usage error, exit code 2. Identical resolved source and projection
  paths -> usage error, exit code 2 (they are physically separate stores).
- A configured path that is missing, unreadable or invalid is **not** a startup crash: the
  application starts and presents the corresponding store state (section 11 / 18), so the
  failure is visible in the UI and testable without a process.
- Never rendered as object identity. The UI shows at most the file **base name** in the
  diagnostics surface; full paths are never put in URLs, models keys or page chrome.
- No project-relative default DB path, no DB copied into the source tree, no database or
  WAL/SHM/journal committed, no product-specific database, no stored preferences.

## 10. Source-store consumption

- Source DB is required and read-only; consumed only through the permitted calls (8.1).
- **Source gate (startup, once):** `get_verse(source, "MAT", 1, 1)` is called. The accepted
  Unit 4 identity/version checks run inside it. Success with a non-`None` verse =>
  `SourceStatus.READY`. `QueryError` or `None` => `SOURCE_STORE_ERROR` state (a configured
  source in which Matthew 1:1 is missing is not a usable Matthew store; at startup this is not
  an ABSENT verse). All later pages then show `SOURCE_STORE_ERROR` and make no projection call.
- Absent verse at request time -> `ABSENT` (section 18); never an error, never corruption.
- A `QueryError` from a call whose input the adapter already validated -> `SOURCE_STORE_ERROR`.
- Token `surface` is used for display; `normalized`, `unicode` and `lemma` are separate
  fields and are never substituted for `surface`. Missing (`None`) vs present-empty (`""`) is
  preserved through the view model and shown distinctly.
- The source database is opened by the core only (`mode=ro`, `query_only=ON`); the product
  never writes, migrates or normalizes it, and no WAL/journal/temporary file may appear next to it.

## 11. Projection-store consumption

### 11.1 Operating states (closed set)

| State | Meaning | Candidate area shows |
|---|---|---|
| `NOT_CONFIGURED` | no projection path supplied | `Structural interpretation store not configured.` |
| `CONFIGURED_ERROR` | configured, but unopenable / not a Unit 10 store / failed validation | a `PROJECTION_STORE_ERROR` (or `INTEGRITY_ERROR`) panel, never "no candidates" |
| `BINDING_FAILED` | store is valid by itself but does not verify against the configured source, or the binding is stale | a `SOURCE_PROJECTION_MISMATCH` panel; no projection data shown |
| `VERIFIED_EMPTY` | verified store; the verse query returns zero candidates | `No persisted structural candidates for this selection.` |
| `VERIFIED_POPULATED` | verified store; the verse query returns candidates | candidate cards; no completeness claim |

"Partially populated" is `VERIFIED_POPULATED`: only the persisted candidates are shown and
**no completeness claim** is made. Live derivation is never run to fill a gap (it is
ADVANCED/OPTIONAL in CB0 and is not part of Product #1). The product never says "No structural
candidates exist" (persisted discovery absence is not derivability). There is no
provisioning button, no automatic candidate persistence and no write control (GAP-2 is not
solved here).

### 11.2 Supplying an existing projection path

The user supplies an existing store with `--projection-db` or `MACULA_EXPLORER_PROJECTION_DB`
(section 9). Omitting it is a supported operating state (`NOT_CONFIGURED`). The product never
creates, initializes, populates or modifies a projection store.

### 11.3 Source / projection binding gate

CB0 section 12: a consumer that shows persisted candidates beside source tokens SHOULD
establish binding once with `verify_projection_store`. Product #1 adopts this as **MUST**
before any projection data is shown, using only the accepted verification boundary (no new
algorithm).

- **When:** once, at startup, only after the source gate succeeded and only if a projection
  path is configured. Never per page/view (it is O(store); every Unit 11 call is already
  O(store), CB0 section 19).
- **Stage 1** `verify_projection_store(projection)` (offline). Failure -> `CONFIGURED_ERROR`
  (`PROJECTION_STORE_ERROR`).
- **Stage 2** `verify_projection_store(projection, source)` (source-grounded). Because stage 1
  just established the store's internal validity, a stage-2 failure -> `BINDING_FAILED`
  (`SOURCE_PROJECTION_MISMATCH`). Success -> `VERIFIED_*`.
- **Retained in memory only:** an immutable `ProjectionBinding` (state, error category if any,
  and a `(size, mtime_ns)` fingerprint of each of the two files). Nothing is written to either
  database or anywhere on disk.
- **Staleness:** every request compares the two fingerprints with the retained ones; a change
  makes the state `BINDING_FAILED` ("binding no longer established; restart to re-verify") and no
  projection data is shown. No automatic re-verification.
- **User-visible result:** header status line plus the projection panel; the source UI keeps
  working in every state. **A failed or stale verification is never rendered as zero
  candidates.**
- A store holding more than one snapshot cannot pass against a single source (Unit 10 I-5);
  that is `BINDING_FAILED`, correctly.
- Per-request Unit 11 errors on an already verified store (the file became corrupt after
  startup) -> `PROJECTION_STORE_ERROR`, or `INTEGRITY_ERROR` for an unexpected exception type
  (section 18); never an empty result.

## 12. Product view models

All models are frozen, slotted, immutable dataclasses of primitives and tuples in
`product/models.py`. Each carries a stable `key` and an `epistemic_class` where applicable.
**No model exposes** `token_id`, `book_id`, `node_id`, `tree_id`, `element_id`, a SQLite rowid
or primary key, a database path, a timestamp, insertion order or a list index as identity.
Core DTOs (`TokenResult`, `NodeResult`, `SourceEvidence`, `StructuralCandidate`,
`ClauseStructureCandidate`, `EvaluatedStructuralInterpretation`, `StructuralInterpretationHistory`)
are never exposed to presentation code.

`epistemic_class` is a closed set: `source_fact`, `derived_structural_candidate`,
`human_evaluation`. (CB0 section 16 spells the middle label
`derived_structural_candidate`; the shorthand `structural_candidate` used in the design
request is treated as the same class and CB0's spelling is frozen here.)

| Model | `key` | Origin identity | Consumer-visible fields | Deliberately omitted | Absence / error behavior |
|---|---|---|---|---|---|
| `ProductVerse` | `"MAT c:v"` | `(book_code, chapter, verse)` | `book_code`, `chapter`, `verse`, `tokens: tuple[ProductToken]` (canonical scripture order), `source_nodes: tuple[ProductSourceNode]`, class `source_fact` | the core `VerseResult`; any joined verse "text" field | verse absent -> `ProductError(ABSENT)`, never an empty verse |
| `ProductToken` | token `ref` (`MAT c:v!n`) | `ref` | **BASELINE:** `ref`, `chapter`, `verse`, `ordinal`, `surface`, `unicode`, `normalized`, `lemma`, `cat`, `language`, `case`, `gender`, `number`, `person`, `tense`, `voice`, `mood`, `degree`, `type`, `functional_tag`, `formal_tag`, `strong_number`; **ADVANCED:** `english`, `mandarin`, `gloss`, `referent` (source `Ref`, distinct from scripture `ref`), `upstream_node_id`, `xml_id`, `morph_id`; class `source_fact` | `token_id`, `book_id`, `node_id`, `tree_id`, `element_id` | every optional field keeps `None` (absent) vs `""` (present-empty) distinct; no semantic role field |
| `ProductSourceNode` | `source_node_id` | `source_node_id` | `source_node_id`, `parent_source_node_id`, `sibling_ordinal`, `cat`, `rule`, `cl_type`; ADVANCED: `id_raw`, `head_raw`; class `source_fact` | `start_raw`, `end_raw`, `length_raw` (raw sentence word positions; omitted so they cannot be mistaken for ordinals or membership), `node_id` | unknown evidence node -> `INTEGRITY_ERROR` on that candidate card |
| `ProductCandidate` | `candidate_id` | `candidate_id` | `candidate_id`, `candidate_kind`, `derivation_kind`, `derivation_version`, `status` (always `candidate`), `source_snapshot` (7 fields), `scope_source_node_id`, `member_token_refs` (exact, ordered), `evidence: tuple[(role, kind, source_node_id)]`, kind-specific `payload`, `is_evaluated: bool`; class `derived_structural_candidate` | an evaluation status on the candidate; any count, score or rank | zero persisted candidates is a valid state, not an error; `is_evaluated=False` when no evaluation exists |
| `ProductAppositionPayload` | n/a | candidate | `anchor_source_node_id`, ordered `child_source_node_ids` | semantic properties | - |
| `ProductClausePayload` | n/a | candidate | `anchor_source_node_id`, `source_rule`, `source_head_raw`, ordered `components: tuple[ProductClauseComponent(source_node_id, source_cat, sibling_ordinal, component_role, member_token_refs)]` | Actor/Action/Patient/Event/Result/Identity/Property, any role translation (`component_role` is shown verbatim as a structural label) | - |
| `ProductEvaluation` | `evaluation_id` | `evaluation_id` | `evaluation_id`, `candidate_id`, `evaluator_class`, `evaluator_label` (`None` vs `""` preserved), `protocol_id`, `protocol_version`, `disposition`, `rationale_evidence: tuple[(kind, citation_id)]`, `rationale_note_text`, `rationale_note_language`, `supersedes` (id or `None`), `superseded_by: tuple[id]`, `not_superseded: bool` (graph leaf); class `human_evaluation` | `event_key` (idempotency key; not shown), `record_protocol`, the echoed candidate, confidence/score/rank/count fields | text is data only (section 17) |
| `ProductHistory` | `candidate_id` | `candidate_id` | `candidate_id`, `evaluations: tuple[ProductEvaluation]`, `edges: tuple[(predecessor_id, successor_id)]`, `not_superseded_ids` | timestamps, insertion order, "current"/"latest" flags | zero evaluations -> empty tuple = valid **Not evaluated** state |
| `ProductSelection` | `(book, chapter, verse, token_ordinal, candidate_id, evaluation_id)` | URL query | the six validated values (`token_ordinal`, `candidate_id`, `evaluation_id` optional) | paths, DB handles | invalid -> `INVALID_INPUT` before any core call |
| `ProjectionPanel` | n/a | binding + one Unit 11 result | `state` (section 11.1), `candidates: tuple[ProductCandidate]`, `histories: tuple[ProductHistory]`, `error: ProductError | None` | - | state is never inferred; failure states carry the error |
| `ProductStatus` | n/a | startup gates | `source_status`, `projection_state`, `error: ProductError | None`, base file names for diagnostics | full paths | - |
| `ProductError` | n/a | adapter classification | `category` (section 18), `scope` (`input`/`source`/`projection`/`selection`), fixed adapter-authored `message`, optional `detail_code` | raw exception messages (may contain filesystem paths; allowed only on the local stderr log) | closed category set |

Ordering: tokens are in scripture order; candidates and evaluations keep the Unit 11
presentation order, which is **presentation order only** (no recency, rank or authority); the
UI says so once in the evaluation panel.

## 13. Navigation design

### 13.1 GAP-1 handling

The accepted core has no chapter/verse enumeration API and Matthew numbering is non-contiguous
(chapters 17, 18 and 23 have gaps). Product #1 therefore:

- offers **direct coordinate entry only**: `Matthew`, `Chapter [ ]`, `Verse [ ]`, `Go / Load`
  (a GET form; text inputs with `inputmode="numeric"`);
- does **not** hard-code chapter or verse counts, does not step until the first missing
  verse, does not infer that a gap ends a chapter and does not scan to a ceiling;
- treats `get_verse` returning `None` as the sole authority on absence;
- **defers Previous/Next**: previous/next *existing* verse cannot be correct without
  enumeration, and coordinate-arithmetic buttons would add noise for no capability. They may
  be added only by a later authorization that states coordinate-arithmetic semantics;
- shows, for an absent verse, `Verse not present in the source store: MAT c:v` and nothing about
  neighbouring verses or the chapter.

### 13.2 Selector pre-validation (before any core call)

Grammar for every numeric parameter (`chapter`, `verse`, `token`): ASCII `[1-9][0-9]*`, at
most 19 digits and value <= 2^63-1 (the accepted core limits). Rejected as `INVALID_INPUT`:
empty, whitespace, sign, leading zero, non-ASCII digits, fractions, repeated parameters and
parameters longer than the cap. The raw query string is capped at 2048 bytes and the path at
256 bytes. `book`, when present, must equal `MAT` exactly, otherwise `UNSUPPORTED`.
`candidate` must match `sha256:[0-9a-f]{64}` and `evaluation` `eval-sha256:[0-9a-f]{64}`.
Unknown query parameters are `INVALID_INPUT`. Validated values are passed to the core as
**integers**, never as long strings, so **Unit 11 audit M-1 is unreachable** from product input.
Token refs are constructed by the adapter as `MAT c:v!n` only after validation.

### 13.3 Routes

| Route | Purpose |
|---|---|
| `GET /` | header, status, navigation form, no verse loaded |
| `GET /verse?chapter=&verse=[&token=][&candidate=][&evaluation=]` | the primary screen for one verse with optional selection |
| `GET /static/explorer.css` | the single fixed static asset |
| anything else | 404 page (`ABSENT`), `HEAD` mirrors `GET`, any other method -> 405 |

Interaction state is entirely in the URL; selection is built by server-generated links.

## 14. Scripture / token presentation

- Each token is its own element showing `surface` verbatim (Greek Unicode untouched; no
  normalization, case folding or stripping of punctuation). Tokens appear in `ProductVerse.tokens`
  order, i.e. canonical scripture order.
- Spacing between tokens is presentation (CSS), not inserted text. An optional "joined text"
  line (token surfaces separated by one U+0020) may appear **only** inside the diagnostics
  `<details>` and must be labelled "presentation composition of source token surfaces; not a
  source fact".
- Token detail panel: BASELINE fields always; ADVANCED fields inside `<details>`. Absent shows
  `(absent)`; present-empty shows `(present, empty)`. `FunctionalTag` and `FormalTag` are shown
  as separate rows; `ref` and `referent` are separate rows; `surface` and `normalized` are
  separate rows. No semantic role or gloss-as-meaning claim.
- Source clause panel (BASELINE): the displayed verse's `ProductSourceNode`s whose raw `cat`
  equals `CL`, with `rule` and `cl_type` verbatim; all other ancestor nodes are listed in an
  ADVANCED `<details>`. Order is first-encounter order over the tokens' ancestors and is
  presentation only.
- **Matthew 1:1 (Verbless):** when a displayed clause node has `cl_type == "Verbless"` the
  panel states `ClType: Verbless` and `The source marks this clause as Verbless.` Nothing is
  rendered for a missing verb: no Greek copula, no "is", no synthetic verb token, no Action,
  Event, Actor, Patient, Identity or Property.

### 14.1 Screen structure (one primary screen)

```text
HEADER       product name | source status | projection-store state (+ binding result)
NAVIGATION   Matthew  Chapter [ ]  Verse [ ]  [Go / Load]
SOURCE                                   (badge: SOURCE FACT)
  scripture panel   Greek tokens, canonical order, individually addressable
  token details     BASELINE + <details> ADVANCED
  source clauses    cat=CL nodes: Rule / ClType (e.g. Verbless) ; <details> all nodes
DERIVED STRUCTURAL CANDIDATES            (badge: DERIVED STRUCTURAL CANDIDATE)
  candidate cards   (persisted only; states of section 11.1)
  candidate details kind, derivation, exact scope, evidence, payload
HUMAN EVALUATION HISTORY                 (badge: HUMAN EVALUATION)
  all evaluations, rationale, supersession, "Not superseded"
DIAGNOSTICS  <details>: candidate_id, evaluation_id, source_snapshot, base file names
```

Frozen presentation scope: information hierarchy, the selected/unselected/member/non-member
states, the empty/error states and accessible semantics (landmark `<header>/<nav>/<main>`,
three `<section>`s with `aria-labelledby` headings and `data-epistemic` attributes, form
`<label>`s, `lang="grc"` on Greek surfaces, visible focus). Desktop-first, readable at a
single column. Pixel styling, branding, animation and mobile optimization are out of scope.

### 14.2 Interactions

- **Select a verse** (Go / Load): loads the source verse and the persisted candidates
  intersecting the verse (one Unit 11 call).
- **Select a token** (`token=`): emphasizes exactly that token, shows its details and lists
  the persisted candidates whose exact member set contains its ref (in-memory filter of the
  verse result).
- **Select a candidate** (`candidate=`): marks exactly its member refs (section 16), shows its
  details/evidence and its evaluation history.
- **Select an evaluation** (`evaluation=`): shows that evaluation's own details and does not
  hide the others.
- No interaction infers candidate membership from screen position or DOM order.

## 15. Structural-candidate presentation

- The candidate area is headed **Derived structural candidates** and every card carries the
  badge `DERIVED STRUCTURAL CANDIDATE` and the status `candidate`. It is visually separate
  from the Source and Evaluation areas.
- Card summary: `candidate_kind` / `derivation_kind` / `derivation_version`, exact member
  refs. Details: scope anchor node, ordered evidence (role, kind, `source_node_id`, with the
  resolved `ProductSourceNode` facts) and a snapshot summary; the full `candidate_id` and
  all seven `source_snapshot` fields live in the diagnostics `<details>`.
- **Apposition:** anchor node and ordered child nodes; evidence roles `anchor`, `child`.
- **S-V-O clause structure:** `Source rule: S-V-O` (from `payload.source_rule`, verbatim),
  `source_head_raw` verbatim and three ordered components, each showing its verbatim
  `component_role` (`subject-component`, `verbal-component`, `object-component`) and its
  exact member refs. `component_role` is a derivation-assigned **structural** label and is
  never mapped to a semantic role.
- Permitted wording: `Source rule: S-V-O`, `Derived structural candidate: S-V-O`. Forbidden:
  any sentence implying MACULA/SBLGNT accepted the candidate, "correct/true interpretation",
  or presenting a candidate as source data.
- Candidate **status** (`candidate`) and evaluation **disposition**
  (`accepted`/`rejected`/`undetermined`) are rendered in different places with different
  labels and are never combined into one badge.
- No confidence, probability, rank, score, vote count or evaluation count anywhere.

## 16. Exact-membership visual contract

**Frozen visual rule (single rule):** when a candidate is selected, *every token of the
displayed verse is rendered in exactly one of two states, decided only by whether its exact
`ref` string is an element of that candidate's `member_token_refs` set.* A member token gets
the member style (solid underline bar + tinted background) **and** a non-color signal (a
visible `▮` marker and the visually-hidden text `member of selected candidate`); a non-member
gets the plain style and the visually-hidden text `not in selected candidate scope`. The
rendered element for each token carries `data-membership="member"` or
`data-membership="non-member"`.

Prohibited (and covered by tests): `first..last` highlighting, `min..max`, `Start..End`,
a wrapper element spanning several tokens to represent scope, CSS sibling/range selectors
(`~`, `+`, `:has`) to propagate membership, and any inference of membership from screen
position or DOM order. A connector, bracket or line may be drawn only **per member token**
(for example connecting listed members) and must never be drawn across a non-member token in a
way that implies membership. S-V-O component labels are attached to the individual member
tokens of that component.

Selection and membership are different states and are visually distinct: *selected token*
(outline) vs *member token* (underline + tint); a token may be both. Members of a candidate that
lie in a **different** verse are listed as refs in the card (text) and are not rendered as
verse tokens.

**Mandatory fixture (Matthew 1:2 S-V-O):** `!5` member, `!6` **non-member**, `!7` member, `!8`
member, `!9` member. Token 6 must not appear as a member anywhere (verse strip, candidate card
or component list).

## 17. Evaluation / history presentation

Headed **Human evaluation history**, badge `HUMAN EVALUATION`, with the standing note
`Listing order carries no meaning; it is not time, rank, quality or authority.`

For every persisted evaluation of the selected candidate (all of them, always):

- details: `evaluation_id` (in diagnostics `<details>`), evaluator class, evaluator label
  (verbatim; `no label recorded` for `None`, `(present, empty)` for `""`), protocol
  `human-structural-adequacy` / version, **disposition**, rationale evidence citations (kind
  + id as plain text), rationale note (text + language tag), `supersedes` relation and
  whether it is a graph leaf;
- wording: `Evaluation: accepted under human-structural-adequacy/1 by <evaluator label>`;
- a candidate with **zero** evaluations shows `Not evaluated` and never `Undetermined` or
  `Rejected`; `no evaluation != undetermined != rejected != accepted`;
- opposing evaluations (for example `accepted` and `rejected`) are listed together, equal in
  weight; the product never chooses a summary or winner;
- **graph-leaf wording is frozen:** an unsuperseded evaluation is labelled
  **`Not superseded`**; a superseded one `Superseded by <evaluation_id>`. The words *Current,
  Latest, Final, Canonical, Preferred, Winning* are prohibited. In a fork, **every** leaf shows
  `Not superseded` simultaneously (expected, not an error);
- selecting an evaluation shows its own details and **does not hide the others**;
- `event_key` is never shown.

**Rationale notes are untrusted plain text** (section 19): shown as escaped text in a
`white-space: pre-wrap` block, never rendered as HTML/Markdown/links, never translated,
summarized or promoted to a source fact; the BCP 47 language tag is displayed as metadata and
may be used for the `lang` attribute only if it matches `[A-Za-z0-9-]{1,35}`.

## 18. Error / empty states

Closed error category set (adapter-owned mapping, independent of core exception classes):

| Category | When | HTTP |
|---|---|---|
| `ABSENT` | valid verse/token/candidate/evaluation reference that does not exist; unknown route | 404 (verse/route); 200 with a selection notice (token/candidate/evaluation absent within an otherwise loaded verse) |
| `INVALID_INPUT` | any pre-validation failure (13.2) | 400 |
| `UNSUPPORTED` | `book` other than `MAT` | 400 |
| `SOURCE_STORE_ERROR` | source gate failure; `QueryError` from a validated source call | 500 page (source panel unavailable) |
| `PROJECTION_STORE_NOT_CONFIGURED` | no projection path (a state, not a failure) | 200 (neutral panel) |
| `PROJECTION_STORE_ERROR` | configured projection missing/unopenable/not a Unit 10 store/failed validation, at the gate or on a later Unit 11 call | 200 with a projection-panel error |
| `SOURCE_PROJECTION_MISMATCH` | source-grounded verification failed, or the binding is stale | 200 with a projection-panel error |
| `INTEGRITY_ERROR` | an exception of an unexpected class from a call whose input was already validated (for example `ValueError`/`AttributeError`/`RecursionError`), or a verified store contradicted (a candidate's evidence node unknown to the source) | 200 with a panel/card error |

Rules:

- valid missing verse/token -> `ABSENT`, not corruption; zero persisted candidates -> a valid
  empty state, not an error; candidate with zero evaluations -> valid `Not evaluated`; non-Matthew
  -> `UNSUPPORTED`; **no store error is ever flattened into ABSENT or an empty state**;
- the adapter never inspects exception **messages** to classify; classification uses the
  exception **class** and the **stage** (gate / request) in which it occurred;
- the source and projection panels are independent: a projection error never hides the source UI,
  a source error never triggers a projection call;
- raw exception messages are never rendered (they may contain local paths); the local stderr
  log may carry the exception class name only.

## 19. Security / locality model

Local, single user, single machine.

- Bind only to loopback (`127.0.0.1` default; `::1` permitted). A non-loopback `--host` refuses
  to start. There is no LAN opt-in flag.
- No accounts, authentication, authorization roles, cookies, sessions, remote calls, CDN,
  remote fonts/scripts, telemetry or analytics. Normal use needs no network beyond loopback.
- Only `GET`/`HEAD`; the `Host` header must be `127.0.0.1:<port>`, `localhost:<port>` or
  `[::1]:<port>` (DNS-rebinding guard), otherwise 400. No request body is read.
- The only served file is the fixed `/static/explorer.css` (no path-derived file access, no
  directory listing).
- Response headers: `Content-Type: text/html; charset=utf-8` (CSS: `text/css; charset=utf-8`),
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`,
  `Content-Security-Policy: default-src 'none'; style-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'`.
- **All dynamic text is data and is escaped** (`html.escape(..., quote=True)`): source strings,
  glosses, evaluator labels, rationale notes, error text. No raw/trusted HTML is ever
  emitted from source or evaluation text; no Markdown rendering; no `innerHTML`; no inline
  scripts or event handlers; no links built from untrusted text (citation ids are plain text).
  Links are built only from validated integers and validated `sha256:`/`eval-sha256:` ids and
  percent-encoded.
- In human-authored strings (`evaluator_label`, rationale notes) Unicode bidirectional
  override/embedding/isolate controls (U+202A-U+202E, U+2066-U+2069) and C0/C1 control characters
  other than LF/TAB are displayed as visible `U+XXXX` text, and the string is isolated
  (`<bdi>`); Greek source surfaces are never altered.
- The product writes no file. Default request logging to local stderr is allowed; no file logs.

## 20. Performance / loading strategy

Per verse page: `1 x get_verse` + `N_tokens x get_ancestors_by_token` (source, cheap) +
`<= 1 x` Unit 11 call + `<= K x get_node` for the selected candidate's evidence (source). The
whole-store validation cost of Unit 11 (CB0 GAP-4) is paid once per page, not per
candidate/evaluation. Token, candidate and evaluation selection never add a Unit 11 call.
The O(store) verification runs once at startup. Validation is never weakened; nothing is
cached in an authoritative store. No optimization work is part of this design.

## 21. Product fixtures (mandatory acceptance scenarios)

| ID | Scenario | Required outcome |
|---|---|---|
| P1 | Matthew 1:1 | eight Greek tokens; `ClType: Verbless` shown; **zero** fabricated verb/copula; Apposition candidates shown if persisted; **no** Action/Event/Actor/Patient/Identity/Property text |
| P2 | Matthew 1:2 exact membership (S-V-O) | `!5` MEMBER, `!6` NON-MEMBER, `!7` MEMBER, `!8` MEMBER, `!9` MEMBER, visibly distinguishable |
| P3 | candidate with zero evaluations | candidate card shown; evaluation area `Not evaluated`; not `Undetermined`/`Rejected` |
| P4 | opposing evaluations | `accepted` and `rejected` both visible, no winner/summary |
| P5 | supersession fork | both graph leaves `Not superseded`; no current answer |
| P6 | valid empty projection store | source UI works; `No persisted structural candidates for this selection.`; no completeness claim |
| P7 | projection not configured | source UI works; `Structural interpretation store not configured.` |
| P8 | corrupt projection store | `PROJECTION_STORE_ERROR`/`INTEGRITY_ERROR` panel; never "no candidates" |
| P9 | absent verse (e.g. MAT 99:99) | `ABSENT` / verse not present; not corruption |
| P10 | malformed coordinate | `INVALID_INPUT` rejected **before** any research-core call |
| P11 | source/projection binding failure | `SOURCE_PROJECTION_MISMATCH`; projection data not shown; source UI works |
| P12 | selecting `MAT 1:2!6` | no S-V-O candidate lists token 6; `!6` is never a member |

Fixture stores are temporary (system temp directory, outside the repository), built with the
accepted Unit 10 writers by the test code only (for example via `tests/support`), and removed
afterwards; product production code never builds one.

## 22. Test strategy

| Layer | Scope | Needs |
|---|---|---|
| A. Adapter unit tests | selector pre-validation; error classification (class/stage, never message); permitted-core-surface call counts (`<= 1` Unit 11 call per verse); model mapping; gate states | minimal accepted temp stores; mocks only to count/redirect calls |
| B. View-model tests | immutability; no surrogate-ID fields; `None` vs `""`; closed enums; no prohibited fields (confidence/score/rank/count) | none (no browser, no server) |
| C. Presentation / route tests | `handle_request(...)` rendered states P1-P12; escaping; membership markup; wording; headers; routes/methods/Host guard; no-JS, no external URLs; prohibited-term scan of application-authored visible text | temp stores; no sockets, no browser |
| D. Real-Matthew read-only integration | **opt-in only** (`MACULA_PRODUCT1_INTEGRATION=1`, source DB from `MACULA_MATTHEW_DB` or the repository default as Unit 11 does) against the existing source store plus a temporary projection store | no full Matthew rebuild |

Structural tests: only `product/adapter.py` imports `scripts`; no module under `product/`
imports `sqlite3`; the adapter imports only the names of section 8.1; no underscore-prefixed
core name is referenced; no write API names appear (AST scan).

Preservation: every layer proves the source store and fixture projection stores are byte-for-byte
unchanged (size/mtime/SHA-256) and that no `-wal`, `-shm` or `-journal` file appears. Product tests
must not require or trigger a full Matthew rebuild and must not enable Unit 3's second-build gate.

## 23. Product acceptance criteria

Criteria for the later implementation and its independent review (56 criteria,
AC-P1-01..AC-P1-56).

| ID | Criterion |
|---|---|
| AC-P1-01 | The implementation starts from a clean `master` at the design-freeze checkpoint (or its recorded descendant) with the baseline recorded before editing. |
| AC-P1-02 | No Unit 12 contract, code, test, status or naming exists; Unit 12 remains NOT AUTHORIZED. |
| AC-P1-03 | Execution model is the stdlib server-rendered local web app of section 5; no other framework is introduced. |
| AC-P1-04 | The dependency boundary of section 6 holds: no third-party package, no JS, no build step, no dependency/config file. |
| AC-P1-05 | `product/adapter.py` exists as the thin product boundary and is the only module importing `scripts.*`. |
| AC-P1-06 | The adapter calls only the permitted core surface of 8.1; no private, write, derive or non-verifying API is used. |
| AC-P1-07 | UI/presentation code consumes only view models; no core DTO or core exception reaches it. |
| AC-P1-08 | No view model, URL, key, template or log exposes `token_id`, `book_id`, `node_id`, `tree_id`, `element_id`, rowids or DB paths as identity. |
| AC-P1-09 | The product is Matthew-only: a non-`MAT` `book` is `UNSUPPORTED`; no other book/edition appears. |
| AC-P1-10 | A structural (AST) test proves no `sqlite3` import under `product/` and the import boundary of AC-P1-05/06. |
| AC-P1-11 | The source store is never written; size/mtime/SHA-256 and absence of WAL/SHM/journal are verified after use. |
| AC-P1-12 | The projection store is never written; fixture stores are byte-identical after use. |
| AC-P1-13 | No product database, cache file, preference file or config file is created or committed. |
| AC-P1-14 | No provisioning, store-initialization, candidate-persistence, evaluation-authoring or write control exists in code or UI. |
| AC-P1-15 | Chapter, verse and token inputs follow the 13.2 grammar and are rejected as `INVALID_INPUT` **before** any core call (verified by call spies). |
| AC-P1-16 | Oversized (>19 digit) and 4300+-digit selectors never reach Unit 11; Unit 11 audit M-1 is unreachable and unremediated. |
| AC-P1-17 | The startup binding gate runs once, in order (source gate, stage 1, stage 2), only with a configured projection, and never per request. |
| AC-P1-18 | Binding state lives only in process memory; nothing is persisted to either store; fingerprint staleness yields `SOURCE_PROJECTION_MISMATCH`. |
| AC-P1-19 | A failed or stale binding or a failed store never renders as zero candidates (P8, P11). |
| AC-P1-20 | Source, candidate and evaluation are three visibly separate, labelled sections with `data-epistemic` attributes and badges. |
| AC-P1-21 | No wording implies MACULA/SBLGNT accepted a candidate or presents a candidate/evaluation as source data. |
| AC-P1-22 | Candidate `status` and evaluation `disposition` are displayed separately and never merged. |
| AC-P1-23 | Membership is the exact set of section 16: every token has `data-membership` of `member` or `non-member` decided by exact-ref set membership. |
| AC-P1-24 | No envelope/min-max/Start-End/wrapper-span/CSS-sibling membership logic exists (code and CSS scan). |
| AC-P1-25 | P2: MAT 1:2 S-V-O shows `!5,!7,!8,!9` as members and `!6` as a non-member. |
| AC-P1-26 | `MAT 1:2!6` is never shown as a member in any view (P12). |
| AC-P1-27 | P1: MAT 1:1 shows eight tokens and `ClType: Verbless` with the neutral explanatory sentence. |
| AC-P1-28 | MAT 1:1 contains no fabricated verb, copula, "is", or Action/Event/Actor/Patient/Identity/Property text. |
| AC-P1-29 | P3: a candidate with zero evaluations shows `Not evaluated`, not `Undetermined`/`Rejected`. |
| AC-P1-30 | P4: opposing evaluations coexist visibly; no summary, winner, vote or count. |
| AC-P1-31 | P5: every graph leaf shows `Not superseded`; no current answer. |
| AC-P1-32 | The words Current/Latest/Final/Canonical/Preferred/Winning never appear in application-authored visible text. |
| AC-P1-33 | The words Actor/Action/Patient/Event/Result/Identity/Property never appear in application-authored visible text; no semantic-role mapping exists. |
| AC-P1-34 | No confidence, probability, percentage, rank, weight, score or evaluation count appears anywhere. |
| AC-P1-35 | Rationale notes and all source/evaluation strings are escaped plain text; no HTML/Markdown/link rendering; bidi/control characters are made visible; no translation or AI processing. |
| AC-P1-36 | Greek `surface` is shown unchanged; `normalized`/`unicode`/`lemma` are separate fields; no destructive normalization. |
| AC-P1-37 | `None` (absent) and `""` (present-empty) are distinct in models and display. |
| AC-P1-38 | GAP-1: navigation is coordinate entry only; no hard-coded verse counts, no "until first missing", no ceiling scan, no Previous/Next. |
| AC-P1-39 | P7: with no projection path the source UI works and the neutral `not configured` text shows. |
| AC-P1-40 | P6: an empty valid projection store shows `No persisted structural candidates for this selection.` and never "No structural candidates exist". |
| AC-P1-41 | P8: a corrupt/invalid projection store shows a store/integrity error, not an empty state. |
| AC-P1-42 | P9: an absent verse shows `ABSENT` and is not reported as corruption. |
| AC-P1-43 | P10: a malformed coordinate is rejected before the research core is called. |
| AC-P1-44 | The error categories form the closed set of section 18; classification uses exception class and stage, never message text; raw core messages are not rendered. |
| AC-P1-45 | A verse page makes at most one Unit 11 call; token/candidate/evaluation selection adds none; no per-candidate fan-out. |
| AC-P1-46 | The server binds loopback only, rejects non-loopback `--host`, enforces the Host header, serves only GET/HEAD and the one static file, and sets the section 19 headers. |
| AC-P1-47 | No external network, CDN, remote font/script, cookie, session, authentication or telemetry is used or required. |
| AC-P1-48 | Configuration is CLI/environment only with no config file and no tracked machine-specific path; identical source/projection paths are a usage error. |
| AC-P1-49 | `event_key` is not displayed; `evaluation_id`, `candidate_id` and `source_snapshot` remain available in diagnostics. |
| AC-P1-50 | Tests are separated into the four layers of section 22; the unittest discovery command works from the repository root without installs. |
| AC-P1-51 | No test requires or performs a full Matthew rebuild; Unit 3's second-build gate stays disabled; the real-Matthew test is opt-in and read-only. |
| AC-P1-52 | CB0, all Unit contracts and audits, schemas, fixtures, contracts, research code and existing tests are byte-identical to the starting checkpoint. |
| AC-P1-53 | Units 1, 2 and 4-11 regression suites, `python -B -m scripts.verify_unit1` and `python -B -m scripts.source_schema` still pass unchanged. |
| AC-P1-54 | Existing findings (Unit 5 M1, Unit 7 M1, Unit 8 M-1, Unit 9 M-1, Unit 11 M-1) are neither remediated nor re-described as resolved. |
| AC-P1-55 | Product #1 remains a product track: no Unit lifecycle row is added or changed, and Phase remains AUTHORIZED. |
| AC-P1-56 | No database, WAL/SHM/journal, `__pycache__` or generated artifact is committed; protected repositories are untouched. |

## 24. Explicit non-goals

Unit 12 of any kind; research-core, source-schema, projection-schema, candidate or evaluation
changes; projection provisioning or any "initialize/populate/evaluate/store/generate" control;
evaluation authoring; live candidate derivation in the normal flow; semantic projection or
Actor/Action/Patient/Event/Result/Identity/Property; semantic-role mapping of S/V/O/P or A0-A2;
confidence, probability, ranking, consensus or "current/latest/canonical" answers; BRW /
`bible-research-merged` integration; localization runtime; AI interpretation or AI evaluators;
theological interpretation; other books, full NT, N1904, companion sources; chapter/verse
enumeration or previous/next-existing-verse navigation; cloud deployment, accounts,
multi-user, telemetry; JavaScript, Node/npm, packaging or installers; any new database or
persisted preference; remediation of Unit 5 M1, Unit 7 audit M1, Unit 8 audit M-1, Unit 9 audit
M-1 or Unit 11 audit M-1.

## 25. Implementation authorization boundary

### 25.1 Authorized scope of a later implementation (frozen, not yet authorized)

A later, separately authorized implementation checkpoint may create or change **only**:

| Kind | Paths |
|---|---|
| Production | `product/__init__.py`, `product/__main__.py`, `product/config.py`, `product/errors.py`, `product/models.py`, `product/validation.py`, `product/adapter.py`, `product/wording.py`, `product/presentation.py`, `product/server.py`, `product/static/explorer.css` |
| Tests | `tests/product/test_product_*.py` (layers A-D), optional `tests/product/support/*.py`; reuse of `tests/support/*` read-only |
| Documentation | a new `## Product Implementation #1` section in `tests/README.md`, `README.md`, `AGENTS.md`, `docs/governance/PHASE-STATUS.md`, `docs/architecture/README.md`, and this contract's status block |
| Dependency/config | **none** |

**Forbidden:** `scripts/`, `schema/`, `fixtures/`, `contracts/`, `parsers/`, existing
`tests/test_unit*.py` and `tests/support/*`, CB0, every Unit contract and audit, any
database/WAL/SHM/journal, `pyproject.toml`, `requirements*.txt`, `package.json`, lock files,
any JavaScript, `C:\Works\macula-greek` and `C:\Projects\bible-research-merged`.

Suggested discovery command (frozen at implementation, flat-test convention without installs):

```powershell
python -B -m unittest discover -s tests/product -p "test_product_*.py" -v
```

Suggested launch (documented, not run by tests):

```powershell
python -B -m product --source-db <path-to-sblgnt-matthew.sqlite3> [--projection-db <path>]
```

Suggested implementation checkpoint subject: `implement Product Implementation #1 Matthew Structural Explorer`
(never "Unit 12").

**Stop line for the implementation:** after the single implementation checkpoint and its
post-checkpoint gate, stop. No independent acceptance, semantic projection, BRW integration,
provisioning, evaluation authoring, localization, previous/next navigation, finding
remediation or Unit 12 without a separate explicit authorization.

### 25.2 Decision

```text
PRODUCT IMPLEMENTATION #1:
READY FOR IMPLEMENTATION AUTHORIZATION
```

Product Implementation #1 is **DESIGN FROZEN / NOT IMPLEMENTED**. Implementation is **not**
authorized by this contract; the next action must be a new explicit user authorization
`IMPLEMENT PRODUCT IMPLEMENTATION #1` against this frozen contract.
