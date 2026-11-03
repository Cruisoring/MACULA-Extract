# MACULA Consumer Baseline v0

## 1. Status

**Baseline identifier:** `MACULA Consumer Baseline v0` (short form **CB0**).

**Status:** FROZEN as a documentation/contract checkpoint. Product implementation may be
separately authorized against it; this checkpoint implements nothing.

CB0 is a documentation contract version. It is **not** a Unit, not "Unit 12", not an API
version, not a source-schema or projection-schema version and not a semantic model version.

| Item | State at this checkpoint |
|---|---|
| Starting commit (sole parent of this checkpoint) | `679ff2f61b255680d209bfd5e759af619fe6cbcc` (`independently accept Unit 11 discovery and history queries`), verified from Git |
| Units 1-11 | as recorded in [PHASE-STATUS](../governance/PHASE-STATUS.md); unchanged |
| Unit 11 | IMPLEMENTED / INDEPENDENTLY ACCEPTED (ACCEPT WITH MINOR FINDINGS) |
| Unit 12 | **NOT AUTHORIZED** |
| Phase | **AUTHORIZED**; not COMPLETE, not CLOSED |
| Semantic projection, BRW integration, localization, UI, product | **NOT AUTHORIZED** |

Current governance authority is [PHASE-STATUS.md](../governance/PHASE-STATUS.md). This document
creates no finding, remediates no finding, changes no historical audit and changes no frozen
contract. Where it quotes a finding it points to the audit that owns it.

## 2. Purpose

Answer one question:

> What may a consumer application now safely depend on from Units 1-11, and what must remain
> outside the consumer contract?

```text
RESEARCH CORE -> ACCEPTED CONSUMER-FACING CAPABILITIES -> FROZEN CONSUMER BASELINE
              -> future Product / UI implementation
```

CB0 is deliberately narrow. It freezes the accepted, observable behavior a Scripture
Structural Explorer may rely on, names the behavior it must not rely on, and records the
capabilities the accepted core does not provide. It does not invent a research Unit because
Unit 11 exists, and a missing capability is not automatically a Unit.

## 3. Audited / accepted research-core prerequisites

CB0 depends only on behavior that each owning Unit's current governance status accepts and that
this checkpoint re-verified against production code and tests (section 21).

| Unit | Consumer-relevant accepted behavior | Owner |
|---|---|---|
| 3 | Pinned SBLGNT Matthew source store (schema v2), read-only at consumption | [Unit 3](UNIT-3-SBLGNT-MATTHEW-SOURCE-FIDELITY-PIPELINE.md) |
| 4 | `get_verse`, `get_token` | [Unit 4](UNIT-4-MATTHEW-QUERY-SLICE.md) |
| 5 | `get_node`, `get_children`, `get_ancestors_by_node`, `get_ancestors_by_token`, `get_members` | [Unit 5](UNIT-5-READ-ONLY-SYNTAX-NAVIGATION-CONTRACT.md) |
| 6 | `get_source_evidence` | [Unit 6](UNIT-6-READ-ONLY-SOURCE-EVIDENCE-COMPOSITION.md) |
| 7 | Apposition `StructuralCandidate` DTO and identity | [Unit 7](UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md) |
| 8 + Amendment 1 | `EvaluatedStructuralInterpretation` DTO; `human-structural-adequacy`/`1` | [Unit 8](UNIT-8-EVALUATED-STRUCTURAL-INTERPRETATION-CONTRACT.md), [Amendment 1](UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md) |
| 9 | S-V-O `ClauseStructureCandidate` DTO and identity | [Unit 9](UNIT-9-SVO-CLAUSE-STRUCTURAL-CANDIDATE-CONTRACT.md) |
| 10 | Separate append-only projection store holding candidates and human evaluations | [Unit 10](UNIT-10-STRUCTURAL-INTERPRETATION-PERSISTENCE-CONTRACT.md) |
| 11 | Read-only discovery and history queries over the projection store | [Unit 11](UNIT-11-READ-ONLY-STRUCTURAL-INTERPRETATION-DISCOVERY-HISTORY-QUERY-CONTRACT.md) |

Unit 2 Amendment 1 is IMPLEMENTED but not separately independently accepted; CB0 relies on
the schema-v2 store only through the independently accepted Units 3, 4 and 6 and their audit.

## 4. Epistemic model

```text
SOURCE FACT  ->  DERIVED STRUCTURAL CANDIDATE  ->  EVALUATION / HISTORY  ->  PRESENTATION
```

| Class | What it is | Produced by | Identity |
|---|---|---|---|
| **Source fact** | A value recorded by the pinned MACULA/SBLGNT source and mirrored exactly | Units 3-6 | token ref; `source_node_id` |
| **Derived structural candidate** | "The registered derivation proposed this structural description" | Units 7, 9 | `candidate_id` |
| **Evaluation** | "This named human evaluator, under this protocol/version, recorded this disposition for this candidate" | Units 8, 10 | `evaluation_id` |
| **Presentation** | How the application chooses to show the above | the consumer | none |

A presentation layer may show all three. It MUST NOT collapse them. In particular:

- a candidate is not a source fact and MUST NOT be worded as though MACULA/SBLGNT asserted it;
- a candidate does **not** mean "objectively true", "the semantic meaning", "the accepted
  interpretation" or "a theological conclusion";
- an evaluation is a recorded human judgment about structural adequacy only; it is not source
  data, not a truth value and not a semantic or theological claim;
- MACULA linguistic annotations are not BRW evaluated interpretations (fidelity principle 8).

Required presentation separation (not styling): a consumer MUST be able to render three clearly
labelled, separately addressable sections, e.g. **Source**, **Structural candidate**,
**Evaluation history**. Permitted structural wording: `Source rule: S-V-O`,
`Derived structural candidate`, `Evaluation: accepted under human-structural-adequacy/1`.
Forbidden wording patterns: `MACULA says this is the accepted S-V-O meaning`,
`Correct interpretation: ...`, or any text presenting a derived/evaluated object as raw source.
Exact UI wording is not frozen; the distinctions are.

## 5. Consumer journey

Minimum journey and what the accepted public behavior supports (all verified, section 21):

| # | Step | Supported by | Verdict |
|---|---|---|---|
| 1 | select book | constant `MAT` (Matthew-only) | SUPPORTED (single book; no book enumeration API, none needed for v0) |
| 2 | select chapter | typed/stepped coordinate; `get_verse` returns `None` when absent | SUPPORTED by direct selection; **no enumeration API** (GAP-1) |
| 3 | select verse | `get_verse` | SUPPORTED by direct selection; **no enumeration API** (GAP-1) |
| 4 | optionally select token | `get_token`, `get_verse` tokens | SUPPORTED |
| 5 | display scripture/token facts | `get_verse`, `get_token` | SUPPORTED |
| 6 | candidates intersecting selection | `list_persisted_candidates_for_*`, `get_structural_interpretation_histories_for_selector` (no `candidate_id` needed) | SUPPORTED over a provisioned projection store (GAP-2) |
| 7 | inspect one candidate | `get_persisted_candidate`, selector-history DTO | SUPPORTED |
| 8 | exact member scope / structural evidence | `candidate.scope`, `candidate.evidence`, `get_node`, `get_children`, `get_members` | SUPPORTED |
| 9 | all persisted evaluations | `list_candidate_evaluations`, history DTO | SUPPORTED |
| 10 | supersession / history | `SupersessionEdge`, `get_evaluation_history`, `get_structural_interpretation_history` | SUPPORTED |
| 11 | unsuperseded graph leaves vs "current truth" | `list_unsuperseded_evaluations`, `unsuperseded_evaluation_ids` (graph leaves only) | SUPPORTED, with the leaf-only rule frozen below |

The journey is supported without a `candidate_id` before initial discovery. Two limits are
recorded as gaps, not defects and not Unit proposals (section 18): GAP-1 navigation
enumeration and GAP-2 projection-store provisioning. Neither requires changing the accepted
core to start a Matthew-only, coordinate-driven product slice (sections 17-18).

## 6. Scripture navigation boundary

Frozen, Matthew-only:

- **Book.** The only supported book code is `MAT`. `ScriptureSelector("MAT", ...)` is the only
  accepted projection selector book; any other book raises `ProjectionQueryError("unsupported
  book ...")`. Source-layer syntax functions hard-code `MAT`. Matthew-only is a boundary of
  v0, not a defect. No multi-book, full-NT, N1904 or multi-snapshot behavior is frozen.
- **Canonical order.** `get_verse(...).tokens` is ordered by stored scripture coordinates
  (`verse_token_ordinal`), never by tree, row, XML, `Start` or ancestry order. Within
  Matthew 1:2 token 5 precedes token 6 although tree traversal differs.
- **Exact token lookup.** `get_token(db, "MAT 1:2!5")` requires the exact coordinate form
  `<book> <chapter>:<verse>!<ordinal>` with positive decimal integers without leading zeroes,
  and an exact binary match of the stored source `ref`. Lookup is case-sensitive; a lower-case
  `mat 1:1!1` is well formed and returns `None`, it is not normalized.
- **Absent.** A missing verse, chapter or token returns `None` (for example `MAT 1:1!999`,
  `MAT 99:99`, a non-`MAT` book code at the source layer). No nearest/partial/fuzzy fallback.
- **Gaps in numbering are real.** The Matthew store has 28 chapters and 18,329 tokens, and
  verse numbering is **not contiguous**: chapters 17, 18 and 23 have verse sets with gaps
  (max verse 27, 35, 39; 26, 34, 38 verses present). A consumer MUST treat `get_verse` returning
  `None` as the authority on absence, MUST NOT infer "end of chapter" from the first missing
  verse, and MUST NOT hard-code versification as a source fact.
- **Malformed.** A malformed ref, non-positive/non-integer/boolean coordinate or empty/whitespace
  book code raises `QueryError` (source layer) or `ProjectionQueryError` (projection layer).

## 7. Source-fact boundary

Classification of consumer-visible source fields (from the accepted DTOs
`TokenResult`, `NodeResult`, `SourceEvidence`):

| Field(s) | Class | Notes |
|---|---|---|
| `book_code`, `chapter`, `verse`, `verse_token_ordinal`, `ref` | **BASELINE** | scripture coordinate / token identity (section 12) |
| `surface`, `unicode`, `normalized`, `lemma` | **BASELINE** | exact, never destructively normalized; `surface` vs `normalized` stay distinct; `None` (absent) vs `""` (present-empty) preserved |
| `cat`, `language`, `case`, `gender`, `number`, `person`, `tense`, `voice`, `mood`, `degree`, `type` | **BASELINE** | raw source morphology; no inference; `Cat` is a source category, not a semantic role |
| `functional_tag`, `formal_tag`, `strong_number` | **BASELINE** | `FunctionalTag` and `FormalTag` remain distinct |
| `english`, `mandarin`, `gloss` | ADVANCED/OPTIONAL | source glosses; separate fields, never merged into surface |
| `referent` (source `Ref`) | ADVANCED/OPTIONAL | distinct from scripture `ref` (principle 4) |
| `upstream_node_id`; `NodeResult.source_node_id`, `parent_source_node_id` | **BASELINE** | source node identity |
| `NodeResult.cat`, `rule`, `cl_type`, `sibling_ordinal` | **BASELINE** | source syntax facts; `Rule`/`ClType` carried verbatim |
| `get_children` (sibling order), `get_ancestors_*` (nearest parent first, self excluded, root last) | **BASELINE** | relational syntax navigation |
| `get_members(...)` / `contextual_members` | **BASELINE** | exact stored membership, scripture order (section 8) |
| `NodeResult.id_raw` (`Id`), `xml_id`, `morph_id` | ADVANCED/OPTIONAL | distinct identities (principle 5); display/debug only |
| `NodeResult.head_raw` | ADVANCED/OPTIONAL | raw source `Head`; a raw value, never a token ordinal |
| `NodeResult.start_raw`, `end_raw`, `length_raw` | ADVANCED/OPTIONAL (debug) | raw sentence word positions, **not** scripture ordinals and **not** membership; MUST NOT be used to compute membership or ranges |
| `token_id`, `book_id`, `node_id`, `tree_id`, `element_id` | **NOT CONSUMER CONTRACT** | see below |

### Local surrogate IDs (Unit 5 M1)

`TokenResult` still exposes `token_id`, `book_id`, `node_id`, `tree_id` and `element_id`
(Unit 5 M1, unresolved, MINOR; inherited by `get_members` and `SourceEvidence`). They are:

> **NON-PORTABLE IMPLEMENTATION DETAIL - MUST NOT BE USED AS CONSUMER IDENTITY.**

They vary across equivalent builds while source identities, facts, exact membership and
canonical order do not. CB0 does not normalize this leakage into a legitimate identifier: no
consumer key, URL, cache key, selection state, evaluation reference or comparison may use them.
This checkpoint does not remediate Unit 5 M1.

## 8. Exact-membership invariant

This invariant is non-negotiable and applies to every consumer feature:

> **Constituent and candidate membership is exact membership, never a scripture envelope.**

The membership of a node, candidate scope or clause component is the stored/derived **exact
set** of member tokens. A consumer MUST NOT compute or imply membership from:

- `min(member)..max(member)` or any bounding box;
- source `Start..End` (these are sentence word positions, not scripture ordinals);
- lexical, row, primary-key or index ranges;
- "all tokens between the first and last member";
- any hidden interval expansion.

A UI MAY draw a visual span over a region only if the convention cannot imply that interior
non-members are structural members (for example by marking each member and visibly excluding
non-members). Display of non-members as members is a violation.

**Frozen Matthew 1:2 case** (verified against the source store and by Unit 11 tests):

```text
S-V-O clause candidate exact scope:   MAT 1:2!5, MAT 1:2!7, MAT 1:2!8, MAT 1:2!9
  subject-component  : MAT 1:2!5
  verbal-component   : MAT 1:2!7
  object-component   : MAT 1:2!8, MAT 1:2!9
MAT 1:2!6            : NOT A MEMBER (a tree sibling under a conjunction clause; never in scope)
```

`MAT 1:2`, `!5`, `!7`, `!8` and `!9` discover the candidate; `MAT 1:2!6` does not. Scripture
ordinal envelope `!5..!9` contains token 6, and that envelope is precisely what a consumer
must not use.

## 9. Candidate boundary

Only already-accepted candidate families are baseline. Both share the DTO fields
`candidate_id`, `candidate_kind`, `derivation_kind`, `derivation_version`, `source_snapshot`,
`scope` (`source_node_id`, ordered exact `member_token_refs`), `evidence` and `status`.

| Field | Stable consumer interpretation |
|---|---|
| `candidate_id` | `sha256:<64 hex>`. The logical identity of the candidate. It is a content hash over snapshot, kind, derivation, scope, evidence and payload; it is the only candidate key. |
| `candidate_kind` | `apposition` or `clause-structure`. Closed set for v0. |
| `derivation_kind` / `derivation_version` | The registered derivation (`source-np-appos`/`1`, `source-rule-s-v-o`/`1`). Part of identity. A different version is a different logical candidate. |
| `source_snapshot` | `source_family`, `edition`, `repository_uri`, `revision`, `manifest_sha256`, `relative_path`, `source_sha256`. Part of identity (section 12). |
| `scope` | `source_node_id` of the anchor plus the **exact** member refs (section 8). |
| `evidence` | Ordered `EvidenceRef(role, "syntax_node", source_node_id)`; the source nodes the derivation used. Resolve with `get_node` / `get_children` / `get_members`. |
| payload | Typed, kind-specific, below. |
| `status` | Always `"candidate"`. A candidate never carries an evaluation status. |

**Apposition** (`apposition` / `source-np-appos` / `1`): payload is the anchor
`source_node_id` and ordered child `source_node_id`s of an explicit source `Np-Appos` node;
evidence roles `anchor` and `child`.

**S-V-O clause structure** (`clause-structure` / `source-rule-s-v-o` / `1`): payload is
`anchor_source_node_id`, `source_rule` (`S-V-O`), `source_head_raw` and three ordered
`ClauseComponent`s, each with `source_node_id`, `source_cat`, `sibling_ordinal`,
`component_role` (`subject-component`, `verbal-component`, `object-component`) and exact
`member_token_refs`; evidence roles `anchor`, `subject-child`, `verbal-child`, `object-child`.
`component_role` values are derivation-assigned **structural** labels carried through verbatim.

A candidate means only: *the registered derivation proposed this structural description over
this exact scope in this source snapshot.* It is not truth, meaning, accepted interpretation or
theology. A UI MAY format or localize labels; it MUST NOT reinterpret payload as semantic
ontology (section 14).

**Persisted discovery is not existence.** A verse with zero **persisted** candidates does not
prove that no derivable candidate exists; it means none was persisted in the supplied store.
Live derivation (`derive_structural_candidates`, Units 7/9) is ADVANCED/OPTIONAL: it is
in-memory, per token, unpersisted and unevaluated, and if shown it MUST be labelled as such.
Derived and persisted candidates with the same `candidate_id` are the same logical candidate.

## 10. Evaluation boundary

An evaluation (`EvaluatedStructuralInterpretation`) exposes, and a consumer MUST preserve and
be able to show:

| Field | Meaning |
|---|---|
| `evaluation_id` | `eval-sha256:<64 hex>`; logical identity (includes `event_key` and `supersedes`) |
| `evaluator_class` | `human` (the only registered class; no AI evaluator class exists) |
| `evaluator_label` | the human evaluator's recorded label, verbatim |
| `evaluation_protocol_id` / `evaluation_protocol_version` | `human-structural-adequacy` / `1` |
| `disposition` | `accepted`, `rejected` or `undetermined` |
| `rationale_evidence` | ordered citations of `syntax_node` or `token` ids |
| `rationale_note` | human text plus BCP 47 language tag, verbatim; never translated, merged or summarized |
| `supersedes` | the predecessor `evaluation_id`, or `None` |
| `candidate` | the evaluated candidate (echo; must match the stored candidate) |

`event_key` is an idempotency key, not a semantic Event, and need not be displayed.

Frozen distinctions:

```text
no evaluation  !=  undetermined  !=  rejected  !=  accepted
```

- **No evaluation** (a candidate with zero records) means *not evaluated*. It is visible,
  discoverable and distinct from "missing candidate". `list_candidate_evaluations` returns `()`
  for a known unevaluated candidate and `None` only when the candidate itself is absent.
- **`undetermined`** is an explicit recorded disposition.
- **`rejected`** means the evaluator judged the proposal not to satisfy the protocol's adequacy
  criterion for that evidence. It is not "no candidate" and not "the source is wrong".
- **`accepted`** means the evaluator judged the proposal to satisfy that criterion. It is a
  structural-adequacy judgment under a named protocol, not truth or meaning.
- A consumer MUST preserve **all** persisted valid evaluations and MUST NOT hide opposing
  evaluations because one is accepted. Opposing evaluations coexist.
- The criterion of `human-structural-adequacy`/`1` concerns structure only.
- **No synthetic fields.** `confidence`, `probability`, `percentage`, `certainty`, rank,
  weight, vote count or any score derived from the number or mix of evaluations is PROHIBITED.

## 11. History / supersession boundary

Supersession is **explicit reconsideration history** recorded by `supersedes`. It does **not**
mean latest wins, newer is correct, current truth or a final answer.

- `SupersessionEdge(predecessor_evaluation_id, successor_evaluation_id)` is built only from
  the logical `supersedes` field. Every returned record, including superseded ones, remains
  returnable by id and in candidate listings.
- **Unsuperseded evaluations are graph leaves.** They are NOT automatically current, canonical,
  preferred, winning or consensus evaluations. Forks remain forks; several leaves coexist.
- A presentation label for a leaf MUST communicate graph structure, for example
  `not superseded`. It MUST NOT be shortened to `current`, `latest`, `final` or any label
  implying epistemic authority unless a later, separately authorized contract creates that
  meaning.
- **Ordering is presentation order only.** Result order is a deterministic function of logical
  fields (candidate id, evaluator class/label, protocol, evaluation id). It is not time order,
  insertion order, rank or precedence. DTOs carry no timestamp or row identity. A consumer
  MUST NOT infer recency, priority or authority from position, list index or id ordering.
- `get_evaluation_history(evaluation_id)` returns the weakly connected supersession component
  of one evaluation (presentation order only).
- Predecessors always concern the same candidate and the same evaluator (class and label);
  graph defects (dangling, self, cross-candidate, cross-evaluator, cyclic) fail closed and are
  never silently dropped.

## 12. Provenance and stable identity

Stable consumer identities:

| Object | Consumer identity | Notes |
|---|---|---|
| Token | exact ref string `MAT c:v!n` (= `book_code`, `chapter`, `verse`, `verse_token_ordinal`) | the form accepted by `get_token`; used in candidate scopes and rationale citations |
| Source syntax node | `source_node_id` (the upstream node identity) | scoped to the active Matthew snapshot; distinct from `id_raw` (`Id`), `xml_id`, `morph_id` |
| Candidate | `candidate_id` | whole string; includes snapshot, kind, derivation kind/version, scope, evidence, payload |
| Evaluation | `evaluation_id` | whole string |

**Never** consumer identity: `token_id`, `book_id`, `node_id`, `tree_id`, `element_id`, SQLite
rowids or primary keys, database file paths, insertion order, list index, timestamps.

Provenance rule (frozen):

> **Display convenience may hide provenance; consumer identity may not discard it.**

A normal UI need not show checksums constantly, but it MUST remain possible (for example in a
details/diagnostic surface) to identify the `source_snapshot` a candidate derives from and the
`candidate_id` an evaluation targets. No consumer may treat an identical-looking structure from
a different source snapshot or derivation version as automatically the same logical candidate.
Cross-snapshot migration/equivalence is outside CB0.

Snapshot binding between a source store and a projection store: Unit 11 queries do not open the
source database. A consumer that displays persisted candidates beside source tokens SHOULD
establish binding once, read-only, with `verify_projection_store(projection_path, source_path)`
(Unit 10; source-grounded V2 re-derivation of every candidate and evaluation). That call is
O(store), is a startup/diagnostic gate and not a per-query step, and a store holding more than
one snapshot cannot pass it against a single source (Unit 10 I-5; not a v0 case).

## 13. Read-only data boundaries

Two accepted authorities, both read-only to the consumer:

| Authority | Content | Consumer access |
|---|---|---|
| **Source store** | read-only linguistic facts (schema v2) | Units 4-6 query functions over `mode=ro`, `query_only=ON` connections |
| **Projection store** | persisted candidates, evaluations, history | Unit 11 query functions over `mode=ro` connections |

Frozen rules:

- Consumer read paths MUST NOT write to the source database.
- Consumer query paths MUST NOT write, append, update or delete persisted candidates,
  evaluations or history, and MUST NOT call Unit 10 write APIs (`initialize_projection_store`,
  `store_candidate`, `store_evaluation`) or Unit 8 `create_evaluated_interpretation`.
- Display preferences, selection state, caches or bookmarks MUST NOT be stored by modifying
  either authoritative store. No mechanism for such state is provided or designed here.
- No consumer may add tables, indexes or columns to either store.
- Source and projection stores are physically separate files; the consumer supplies both paths.

Consumer projection reads MUST use the Unit 11 functions. They MUST NOT use
`projection_store.get_candidate` (non-verifying by contract, Unit 10 I-2),
`projection_store.get_evaluation`, `list_evaluations_for_candidate` (unordered `frozenset`),
private (`_`-prefixed) helpers, or the incidental module attributes `store`, `structural` and
`evaluated` exposed by `projection_query` (Unit 11 I-5).

## 14. Semantic and Verbless firewalls

### Semantic firewall

CB0 PROHIBITS any unconditional mapping equivalent to:

```text
S  -> Actor      V -> Action      V -> Event
O  -> Patient    O -> Result
P  -> Identity   P -> Property
A0 -> Actor      A1 -> Patient    A2 -> Recipient   A2 -> Result
```

Source and derived structural labels (`S`, `V`, `O`, `P`, `A0`..`A2`, `subject-component`,
`verbal-component`, `object-component`, `Cat`, `Rule`, `ClType`) remain structural labels. A
consumer may explain them linguistically in neutral wording; it must not turn them into a
semantic ontology and MUST NOT create Actor/Action/Patient/Event/Result/Identity/Property
entities. Semantic projection requires separate future authorization and is outside CB0.

### Verbless negative fixture: Matthew 1:1

Matthew 1:1 is a mandatory consumer negative fixture (verified against the source store):

```text
Clause node:   Cat=CL   Rule=P2CL   ClType=Verbless
Leaves:        eight tokens, all Cat=noun   (MAT 1:1!1 .. MAT 1:1!8)
Verb leaves:   zero
```

A consumer MUST NOT fabricate or imply a source Greek verb or copula: no synthetic "is", no
verb token, no Action, Event, Actor, Patient, Identity or Property. Human-readable presentation
may state that the source marks the clause `Verbless`; it must not rewrite the source as though
an omitted Greek verb were present. Matthew 1:1 yields Apposition candidates only and no S-V-O
candidate.

## 15. Consumer error model

The failure distinctions a consumer MUST preserve, with where they exist today:

| Distinction | Existing mechanism | Adaptation needed |
|---|---|---|
| **NOT FOUND / ABSENT** | source `get_*` return `None`; `get_children`/`get_members`/`get_node` `None` = unknown node; projection `get_*` return `None`; discovery lists return `()`; `list_candidate_evaluations` `()` = known candidate with no evaluations, `None` = candidate absent | none; consumers MUST NOT turn absence into an error or an error into absence |
| **INVALID SELECTOR** | source layer `QueryError(ValueError)`; projection layer `ProjectionQueryError` | types do **not** separate selector errors from store errors (see below) |
| **INVALID / CORRUPT STORE** | source `QueryError` (identity/version/SQLite failure); projection `ProjectionQueryError` (identity, catalog, any invalid row, graph defects, missing/non-database file) | same exception type as selector errors |
| **UNSUPPORTED** | projection `ProjectionQueryError("unsupported book")`; source layer returns `None` for a non-`MAT` book, indistinguishable from absence | consumer-level classification required |
| **INTERNAL / INTEGRITY FAILURE** | wrapped store/integrity failures above; plus the Unit 11 M-1 `ValueError` and I-2 `AttributeError` leaks | consumer-level classification required |

Rules:

1. A candidate with zero evaluations MUST NOT look like a missing candidate.
2. A verse with zero discovered candidates is not a database failure.
3. Corruption, identity mismatch and unreadable stores MUST NOT be flattened into
   "nothing found".
4. `QueryError` (source) and `ProjectionQueryError` (projection) are distinct classes; the
   projection one is not a `QueryError`. Neither distinguishes bad input from bad store by type.
   The consumer adapter (section 16) MUST classify selector problems itself, **before**
   calling the core, using the accepted grammars (section 6; positive integers, at most 19
   digits / at most 2^63-1, supported book `MAT`); an exception from a call whose input it already
   validated is then a store/integrity failure. This pre-validation also avoids Unit 11 M-1.
5. Whole-store validation (section 19) means any corrupt record makes every projection query
   fail closed; the consumer reports a store failure, never an empty result.

**Unit 11 audit M-1** (known baseline limitation): string-form verse/token selectors with more
than 4300 digits (for example `"MAT 1:" + "9"*5000`) raise `ValueError` rather than
`ProjectionQueryError`. It fails closed (no result, no connection opened). It does not block
product implementation because the adapter's input pre-validation makes it unreachable. It is
not remediated here.

## 16. Consumer DTO / adaptation recommendation

**Decision (design only): a thin consumer adapter / view-model boundary is advisable, and a
UI SHOULD NOT consume research-core DTOs directly.** Reasons: `TokenResult` carries local
surrogate IDs (section 7); core exceptions do not separate selector errors from store errors
(section 15); selector discovery plus history is best done once per request because every
projection call validates the whole store (section 19); and epistemic labels belong at the
boundary so the UI cannot confuse source, candidate and evaluation.

Permitted adapter responsibilities:

- drop/hide local SQLite PK fields from consumer-facing models;
- combine already-public read outputs for presentation (for example one
  `get_structural_interpretation_histories_for_selector` call per verse selection);
- attach explicit epistemic type labels (`source_fact`, `derived_structural_candidate`,
  `human_evaluation`) to every model;
- expose the stable logical identities of section 12;
- pre-validate selectors and normalize consumer error categories (section 15) without
  changing the underlying meaning;
- preserve provenance (`source_snapshot`, `candidate_id`) for a diagnostic surface.

The adapter MUST NOT: re-derive candidate existence; change or widen exact scope; choose,
order-by-authority or merge evaluations; label a graph leaf `current`; synthesize
confidence/probability/consensus; generate semantic roles; translate rationale notes; or
mutate source or projection data. The adapter is **not implemented** by this checkpoint.

## 17. Capability matrix

Values: **BASELINE**, **ADVANCED/OPTIONAL**, **DEFERRED**, **PROHIBITED**. A database column
existing does not make a capability BASELINE.

| Capability | Source Unit | Consumer status | Stable identity | Read-only? | Known limitation | Baseline decision |
|---|---|---|---|---|---|---|
| Book/chapter/verse navigation (by coordinate) | 4 | **BASELINE** | `MAT c:v` | yes | Matthew-only; no enumeration API (GAP-1); non-contiguous verse numbering | BASELINE |
| Book/chapter/verse enumeration | - | **DEFERRED** | - | - | not provided by accepted core | DEFERRED (GAP-1) |
| Token lookup | 4 | **BASELINE** | token ref | yes | case-sensitive exact ref; `None` when absent | BASELINE |
| Morphology display | 4 | **BASELINE** | token ref | yes | raw source values; no inference | BASELINE |
| Syntax ancestry | 5, 6 | **BASELINE** | `source_node_id` | yes | nearest-first, self excluded | BASELINE |
| Direct children | 5, 6 | **BASELINE** | `source_node_id` | yes | sibling order | BASELINE |
| Exact membership | 5 | **BASELINE** | token refs | yes | `TokenResult` local IDs (Unit 5 M1) MUST be hidden | BASELINE |
| SourceEvidence | 6 | **ADVANCED/OPTIONAL** | token ref | yes | convenience composition; local IDs inside | ADVANCED/OPTIONAL |
| Raw Start / End / Length | 5 | **ADVANCED/OPTIONAL** (debug) | - | yes | not scripture ordinals; never membership | ADVANCED/OPTIONAL |
| Source surrogate IDs | 4, 5 | **PROHIBITED** as identity | - | - | Unit 5 M1 | PROHIBITED |
| Apposition candidate (persisted) | 7, 10, 11 | **BASELINE** | `candidate_id` | yes | present only if persisted (GAP-2) | BASELINE |
| S-V-O candidate (persisted) | 9, 10, 11 | **BASELINE** | `candidate_id` | yes | Unit 9 audit M-1; present only if persisted | BASELINE |
| Live candidate derivation | 7, 9 | **ADVANCED/OPTIONAL** | `candidate_id` | yes | in-memory, unpersisted, unevaluated; must be labelled | ADVANCED/OPTIONAL |
| Persisted candidate discovery (selector) | 11 | **BASELINE** | `candidate_id` | yes | whole-store validation per call | BASELINE |
| Candidate lookup by id | 11 | **BASELINE** | `candidate_id` | yes | - | BASELINE |
| Evaluation lookup by id | 11 | **BASELINE** | `evaluation_id` | yes | - | BASELINE |
| All evaluations of a candidate | 11 | **BASELINE** | `evaluation_id` | yes | presentation order only | BASELINE |
| Supersession edges | 11 | **BASELINE** | evaluation id pair | yes | - | BASELINE |
| Evaluation history (component / full) | 11 | **BASELINE** | `evaluation_id` | yes | presentation order only | BASELINE |
| Unsuperseded graph leaves | 11 | **BASELINE** (as graph structure) | `evaluation_id` | yes | never "current"; forks remain | BASELINE |
| Source-grounded snapshot verification | 10 | **ADVANCED/OPTIONAL** | - | yes | O(store); single-snapshot stores | ADVANCED/OPTIONAL |
| Projection-store write APIs / evaluation creation | 8, 10 | **DEFERRED** | - | writes | operator/offline only; not a consumer path | DEFERRED (write UI) |
| Projection-store provisioning | - | **DEFERRED** | - | writes | no accepted bulk procedure (GAP-2) | DEFERRED |
| Semantic roles / Actor-Action-Patient-Event-Result | - | **PROHIBITED** | - | - | semantic firewall | PROHIBITED |
| Confidence / probability / scoring / ranking | - | **PROHIBITED** | - | - | no accepted semantics | PROHIBITED |
| Consensus / "current" / "canonical" / "latest" answer | - | **PROHIBITED** | - | - | leaf-only rule | PROHIBITED |
| AI evaluator class / AI-generated interpretation | - | **PROHIBITED** | - | - | only `human` is registered | PROHIBITED |
| Localization | - | **DEFERRED** | - | - | no runtime; display wording only | DEFERRED |
| Theological interpretation | - | **PROHIBITED** | - | - | out of scope | PROHIBITED |
| Other books / full NT / N1904 / cross-edition | - | **DEFERRED** | - | - | Matthew-only core | DEFERRED |

## 18. Consumer gaps (missing capabilities, not Units)

Identified exactly; none is implemented, scheduled or named "Unit 12" here.

- **GAP-1 - Navigation enumeration.** No accepted API lists the available chapters or verses
  (or books). Direct selection is fully supported; list-driven pickers are not. Verse numbering
  is non-contiguous (section 6), so "first `None` ends the chapter" is wrong, and probing
  `get_verse` over a consumer-chosen ceiling can never prove completeness. Hard-coded
  versification would invent source facts. **Does not block** a coordinate-driven first slice
  (typed/stepped selection with absence handled); it **would block** a claim that a chapter/verse
  list is source-complete unless a future separately authorized contract provides one. Not
  a product defect and not an automatic Unit.
- **GAP-2 - Projection-store provisioning.** Unit 11 reads a store that must already hold
  candidates. Public pieces to produce one exist (Unit 7/9 derivation, Unit 10 writers with
  source-grounded V2), but no accepted bulk/provisioning procedure or production projection
  store exists in the repository. **Does not block** product implementation: the slice must
  work, and be tested, against empty, partial and fixture stores; "no persisted candidates" is a
  normal state (section 9). Provisioning and any evaluation authoring are operator/offline work
  needing their own authorization and are not a consumer read path.
- **GAP-3 - Error typing.** Selector, unsupported-book and store failures share exception
  types (section 15). Closed by adapter-side pre-validation; no core change needed for v0.
- **GAP-4 - Whole-store validation per call** (section 19). Handled by batching in the adapter.

## 19. Performance / loading characteristics

Not optimized here; recorded so a product does not discover it late. Confirmed from
`projection_query._load` and the Unit 11 audit (I-3): **every** Unit 11 call opens the store and
validates **every** persisted candidate and evaluation (V1 re-validation, id recomputation,
graph checks) before answering, so cost is O(store) per call, and one corrupt row anywhere
fails every query. This is a deliberate fail-closed choice. Consequences for a consumer: batch
(one selector-history call returns candidates, evaluations, edges and leaf ids together),
avoid per-candidate call fan-out, and do not cache results in either authoritative store. Source
queries are indexed and cheap by comparison (Unit 4 recorded low-millisecond calls). Correctness
and fail-closed semantics take precedence over speed in CB0.

## 20. Minimum product vertical slice (defined, not implemented)

"What could Product Implementation #1 build without any Unit 12?" A **Matthew-only, read-only
Scripture Structural Explorer**:

1. Book: `Matthew` (single fixed source code `MAT`).
2. Chapter and verse selection by coordinate with absence handled (GAP-1); no hard-coded
   versification claimed as source fact.
3. Greek verse/token display in canonical scripture order.
4. Token linguistic details (BASELINE source fields; ADVANCED fields behind a detail toggle).
5. Structural candidates intersecting the selection (persisted discovery, no `candidate_id`
   needed), including candidates with zero evaluations.
6. Candidate exact scope and evidence (members marked individually; non-members never shown as
   members; Matthew 1:2 token 6 and Matthew 1:1 Verbless as acceptance fixtures).
7. Evaluation/history panel: all evaluations, disposition, evaluator class/label,
   protocol/version, rationale evidence and note, supersession edges, and graph leaves labelled
   as `not superseded`.
8. Three visibly separate sections: Source / Structural candidate / Evaluation history.
9. Diagnostic surface exposing `source_snapshot`, `candidate_id`, `evaluation_id`.
10. Distinct empty/absent/invalid/unsupported/corrupt-store states (section 15).

Frontend framework, hosting, API server, routes, mockups and localization are **not** chosen or
created here; no repository constraint resolves them. The slice needs a provisioned or fixture
projection store (GAP-2) and writes nothing.

## 21. Known limitations / findings register

Only consumer-relevant items; the complete ledger lives in governance and the owning audits.
"Blocks" asks: does the item block product implementation against CB0?

| Finding | Owner | Class | Blocks? | Why / consumer rule |
|---|---|---|---|---|
| Unit 5 M1: `TokenResult` exposes local SQLite PK fields | Unit 5 | MINOR, unresolved | **NO** | no lookup needs a PK; adapter hides them; section 7 marks them non-portable and never identity |
| Unit 7 audit M1: pre-implementation contract bytes not independently reconstructable | Unit 7 audit | MINOR, unresolved | **NO** | provenance of the original contract text; every behavior was independently tested as committed; no consumer-visible effect |
| Unit 8 audit M-1: stale "fails by design/filtered" prose | Unit 8 audit | MINOR, unresolved | **NO** | documentation staleness; behavior correct (S-V-O evaluation accepted); consumers rely on behavior in section 10 |
| Unit 9 audit M-1: no dedicated production check for token 6 in anchor/component | Unit 9 audit | MINOR, unresolved | **NO** | genuine store yields the correct exclusion (verified: `!5,!7,!8,!9`); a self-consistent corrupted source store could mislead derivation; source store is read-only and gated at build/publication; consumers must not repair or widen scope; `verify_projection_store` with source rejects forged candidate echoes |
| Unit 10 I-1, I-2, I-3, I-5 (self-consistent forgery passes V1; `get_candidate` non-verifying; V2 only for new candidate on write; single-snapshot V2) | Unit 10 audit | informational | **NO** | consumers use only Unit 11 reads (validating) and optionally the source-grounded verify gate; section 13 |
| Unit 11 audit M-1: oversized string selector raises `ValueError` | Unit 11 audit | MINOR, unresolved | **NO** | fails closed; unreachable after adapter pre-validation; section 15 |
| Unit 11 I-1: self-consistent forged persisted candidate accepted by the projection-only path | Unit 11 audit | informational | **NO** | trust-boundary limit; mitigated by source-grounded verification and by treating the projection file as operator-provisioned; consumer must not present an unverified file as source-attested |
| Unit 11 I-2 / I-5: `AttributeError` on misuse of a frozen selector; incidental module attributes | Unit 11 audit | informational | **NO** | programmer misuse only; use public constructors and listed functions |
| Unit 11 I-3: whole-store validation per call | Unit 11 audit | informational | **NO** | section 19; batch calls |
| Unit 9 I-1: raw `Start`/`End` are sentence word positions | Unit 9 audit | informational | **NO** | section 7/8: never membership |
| GAP-1, GAP-2 | this document | missing capabilities | **NO** | sections 18 and 20 |

**No blocker prevents Product Implementation #1 as defined in section 20.**

Verification performed for this checkpoint (this document's claims were checked against
production and tests, not copied from prose); see the final report for exact commands and counts:
read-only source-store probes of Matthew 1:1/1:2 membership, derivation output, absence,
malformed and unopenable-store behavior, verse-numbering gaps; both required verifiers; the
Unit 11 tests and read-only integration test; Units 4-10 fast tests. The source database was
hashed before and after.

## 22. Explicit non-goals / deferred work

Not part of CB0 and not defects: Unit 12; full New Testament ingestion; other books; N1904;
cross-edition alignment; cross-snapshot candidate migration/equivalence; semantic
Actor/Action/Patient/Event/Result projection; theological interpretation; AI-generated
interpretation or an AI evaluator class; confidence, ranking or recommendation; consensus or a
universal current answer; localization runtime; Chinese Bible translation; user accounts or
authentication; collaborative review; write UI for evaluation creation; editing source data;
editing persisted historical evaluations; cloud deployment; sync; multi-user conflict
resolution; user-preference persistence; remediation of any prior finding; BRW integration;
frontend framework, API server, routes or any UI file.

## 23. Baseline versioning rule

CB0 changes (a new baseline, e.g. v1, is required) when any of these change in a way a consumer
must understand:

- a consumer-visible semantic of section 4-14 is removed or altered;
- an identity meaning changes (token ref, `source_node_id`, `candidate_id`, `evaluation_id`);
- exact-membership semantics change;
- evaluation, disposition or supersession/graph-leaf meanings change;
- a new candidate kind, evaluator class or protocol becomes consumer-visible;
- a semantic interpretation layer is added, or "current/canonical" evaluation meaning is created;
- Matthew-only scope is widened.

Pure internal refactoring, performance work, new tests, documentation clarification and remediation of a
finding that preserves the frozen behavior do **not** require a new baseline. CB0 is not bumped by
the existence of Unit 12 or later Units unless they change one of the items above.

## 24. Acceptance criteria

Independently reviewable; each is satisfied by this document and verified against production and
tests at this checkpoint, except product-behavior criteria, which bind the future product.

| ID | Criterion |
|---|---|
| AC-CB0-01 | No consumer identity, key, URL, cache key or comparison uses `token_id`, `book_id`, `node_id`, `tree_id`, `element_id`, rowids, paths, insertion order or list index (section 12). |
| AC-CB0-02 | Local surrogate IDs in existing DTOs are marked "NON-PORTABLE IMPLEMENTATION DETAIL - MUST NOT BE USED AS CONSUMER IDENTITY"; Unit 5 M1 is recorded and not remediated (section 7). |
| AC-CB0-03 | Constituent and candidate membership is exact membership; `min..max`, `Start..End`, lexical/PK ranges, bounding boxes and hidden interval expansion are forbidden (section 8). |
| AC-CB0-04 | Matthew 1:2 S-V-O exact scope is `!5,!7,!8,!9` with components `!5` / `!7` / `!8,!9`, and `MAT 1:2!6` is not a member and is not discovered. |
| AC-CB0-05 | Matthew 1:1 is preserved as `Rule=P2CL`, `ClType=Verbless`, eight noun leaves, zero verb leaves; no verb, copula, Action, Event, Actor, Patient, Identity or Property is fabricated (section 14). |
| AC-CB0-06 | Source fact, derived structural candidate and evaluation are distinct, separately labelled and separately addressable sections; no derived/evaluated object is worded as raw source (section 4). |
| AC-CB0-07 | Candidates are discoverable from a scripture selector without a prior `candidate_id` (sections 5, 9). |
| AC-CB0-08 | A candidate with zero evaluations is visible and distinct from a missing candidate (sections 10, 15). |
| AC-CB0-09 | `no evaluation`, `undetermined`, `rejected` and `accepted` are four distinct states (section 10). |
| AC-CB0-10 | All persisted valid evaluations are preserved and shown; opposing evaluations coexist and none is hidden because another is accepted (section 10). |
| AC-CB0-11 | No `current`, `latest`, `final`, `canonical`, `preferred`, `winning` or `consensus` inference from recency, order, id, supersession or evaluation count (section 11). |
| AC-CB0-12 | Unsuperseded means graph leaf only; forks remain forks; any leaf label communicates graph structure (e.g. `not superseded`), not authority (section 11). |
| AC-CB0-13 | No confidence, probability, percentage, certainty, ranking weight or score is displayed or derived (section 10). |
| AC-CB0-14 | S/V/O/P and A0/A1/A2 are not unconditionally mapped to Actor/Action/Patient/Event/Result/Identity/Property/Recipient (section 14). |
| AC-CB0-15 | Candidate identity retains `source_snapshot`, `derivation_kind` and `derivation_version`; identical-looking structures from different snapshots or versions are not assumed equal; `source_snapshot` and `candidate_id` remain obtainable (section 12). |
| AC-CB0-16 | The consumer never writes to the source store (section 13). |
| AC-CB0-17 | Consumer query paths never write, rewrite or delete persisted candidates, evaluations or history, and use only Unit 11 reads for projection data (section 13). |
| AC-CB0-18 | Display preferences, state and caches are not stored by modifying either authoritative store (section 13). |
| AC-CB0-19 | Corruption, identity mismatch and unreadable stores are not reported as "not found"/"nothing found"; a verse with zero persisted candidates is not a store failure (section 15). |
| AC-CB0-20 | Absent, invalid selector, invalid/corrupt store, unsupported and internal/integrity failures are distinguishable to the user (section 15). |
| AC-CB0-21 | Unit 11 audit M-1 is recorded as a known baseline limitation, not remediated, with adapter pre-validation as the consumer control (section 15). |
| AC-CB0-22 | v0 scope is Matthew-only; no other book, full-NT, N1904 or multi-snapshot behavior is claimed (section 6). |
| AC-CB0-23 | Verse numbering is not assumed contiguous and versification is not hard-coded as a source fact (sections 6, 18). |
| AC-CB0-24 | A zero-persisted-candidate result is not presented as proof that no structural candidate is derivable (section 9). |
| AC-CB0-25 | Raw `Start`/`End`/`Length` are never used as scripture ordinals or membership (sections 7, 8). |
| AC-CB0-26 | Every consumer-visible capability is classified BASELINE / ADVANCED-OPTIONAL / DEFERRED / PROHIBITED in the matrix, not by column existence (section 17). |
| AC-CB0-27 | A thin adapter is recommended with defined responsibilities and prohibitions, and is not implemented (section 16). |
| AC-CB0-28 | Whole-store validation per Unit 11 call is recorded as a known characteristic and not optimized (section 19). |
| AC-CB0-29 | Every consumer-relevant prior finding is classified with a "blocks product implementation" decision (section 21). |
| AC-CB0-30 | Unit 12 is not authorized, not implied and not named as the vehicle for any gap (sections 1, 18). |
| AC-CB0-31 | Semantic projection, BRW integration, localization, AI interpretation and theological interpretation are not authorized (sections 14, 22). |
| AC-CB0-32 | This checkpoint adds no UI, framework choice, API server, route, HTML/CSS/JS, production code, test, schema, fixture or database, and changes no historical contract or audit. |
| AC-CB0-33 | Source and projection stores and protected repositories are unchanged by this checkpoint. |

## 25. Product-implementation authorization status

**Product implementation is NOT authorized by this checkpoint.** CB0 records that product
implementation *may be separately authorized against this baseline*. The proper next step is a
separately authorized **Product Implementation #1 design / authorization** against
"MACULA Consumer Baseline v0". Unit 12, semantic projection, BRW integration, localization and
remediation of any finding are each NOT AUTHORIZED. Phase remains **AUTHORIZED**, not COMPLETE
and not CLOSED. Product Implementation #1 would need its own explicit authorization before any
UI, API, framework or provisioning work begins.
