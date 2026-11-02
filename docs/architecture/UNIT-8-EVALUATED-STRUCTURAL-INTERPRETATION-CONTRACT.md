# UNIT 8 — EVALUATED STRUCTURAL INTERPRETATION BOUNDARY

**Status:** CONTRACT DRAFT / NOT IMPLEMENTED

**Implementation authorization: NOT AUTHORIZED.**

## 1. Purpose

This is a design-only contract. It defines what an *evaluated structural
interpretation* means downstream of the independently accepted
[Unit 7 structural candidate boundary](UNIT-7-DERIVED-STRUCTURAL-CANDIDATE-CONTRACT.md),
without creating any production behavior.

Unit 7 froze the boundary between:

1. authoritative linguistic source facts;
2. deterministic source-evidence composition;
3. derived structural candidates; and
4. evaluated structural interpretation (left explicitly to a future unit).

Unit 8 is that future unit's *design*. It answers one question conservatively:

> What is the smallest auditable, epistemically honest object that records an
> explicit assessment of one Unit 7 candidate, without changing source facts,
> without changing the candidate, without fabricating certainty, without
> conflating deterministic derivation with judgment, without a semantic
> ontology and without theological interpretation?

The answer, in one sentence:

> An **EvaluatedStructuralInterpretation** is an immutable, content-identified
> record stating that *a named evaluator, under a named and versioned evaluation
> protocol, recorded a disposition (`accepted`, `rejected` or `undetermined`) for
> exactly one identified Unit 7 candidate bound to one fixed source snapshot,
> citing evidence drawn from that candidate*. It claims nothing else.

Evidence classes used in this document (also tabulated in section 29):

- **[EI]** EXISTING INVARIANT — already established by accepted prior units or the architecture.
- **[DD]** DESIGN DECISION — newly proposed and justified here.
- **[DEF]** DEFERRED — intentionally left to a future, separately authorized unit.
- **[RISK]** OPEN RISK — relevant but not resolvable in this design task.

## 2. Status and authorization boundary

- This document is a design contract only. It adds no production module, test,
  schema, database, dependency or integration.
- Unit 8 is **not implemented**, **not accepted** and **not authorized for
  implementation** (see section 32).
- Unit 7 remains `IMPLEMENTED / INDEPENDENTLY ACCEPTED`, decision
  `ACCEPT WITH MINOR FINDINGS`; Unit 7's audit M1 is unresolved and unchanged.
- Unit 5 remains `ACCEPT WITH MINOR FINDINGS`; Unit 5 M1 is unresolved and unchanged.
- Units 3, 4 and 6 remain `IMPLEMENTED / INDEPENDENTLY ACCEPTED` (ACCEPT).
- Unit 2 Amendment 1 remains `IMPLEMENTED` and is not separately independently accepted.
- The Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.
- Authorizing this design is not authorizing candidate persistence, evaluation
  persistence, BRW integration, any other candidate kind, or any later unit.

## 3. Preconditions

Established by the current repository, not assumed [EI]:

- Unit 7 candidate derivation is implemented in `scripts/structural_candidates.py`
  over the read-only `scripts/source_query.py` boundary and independently accepted
  (see the [Unit 7 audit](../audits/UNIT-7-STRUCTURAL-CANDIDATE-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
- Units 3, 4 and 6 are independently accepted (see the
  [historical audit](../audits/HISTORICAL-UNITS-3-4-6-INDEPENDENT-ACCEPTANCE-AUDIT.md)).
- The authoritative source store is an immutable, read-only linguistic evidence
  boundary; downstream interpretation lives in a separate projection store, never
  in source tables (architecture spike, sections 7.10 and 12.4; Unit 7 contract sections 24-25).
- The repository has **no identity, account or authentication system**. Unit 8
  must be designable without one (section 9).

## 4. Definitions

| Term | Meaning |
|---|---|
| Source fact | A statement that the fixed source snapshot contains a value or relationship. Owned by the source store. |
| Candidate | A Unit 7 `StructuralCandidate`: a deterministic proposal derived from source facts. |
| Candidate reference | The Unit 7 `candidate_id` string (`sha256:` plus 64 lowercase hex digits). |
| Evaluation record | The Unit 8 object defined here, a.k.a. EvaluatedStructuralInterpretation. |
| Evaluation protocol | A named, versioned, closed-registry rule set that gives a disposition its meaning. |
| Evaluator | The class and label of whoever or whatever applied the protocol. |
| Disposition | One of `accepted`, `rejected`, `undetermined`, with the frozen meanings of section 10. |
| Rationale | Machine-checkable evidence references plus optional/required human prose, kept separate. |
| Supersession | An explicit same-evaluator reconsideration edge between two records. Not "newer wins". |
| Echo | A verbatim copy of candidate content stored for offline verification; never authoritative. |
| Snapshot | The seven-field Unit 7 `SourceSnapshot` (family, edition, repository URI, revision, manifest SHA-256, relative path, source-file SHA-256). |

## 5. Three-layer epistemic model

| Layer | Object | Existence means | Authority |
|---|---|---|---|
| A | LinguisticSourceFact | "the selected MACULA snapshot contains source node X with Rule Y" | The immutable source store |
| B | StructuralCandidate (Unit 7) | "the derivation protocol `source-np-appos`/`1` proposed this structure from these source facts" | Deterministic derivation; reproducible |
| C | EvaluatedStructuralInterpretation (Unit 8) | "evaluator E under protocol P/V recorded disposition D for candidate C, citing evidence R" | The evaluator's recorded act; auditable, not reproducible from source bytes alone |

Rules:

1. Arrows are one-way: A may cause B; B may be the subject of C. C never mutates B; B never mutates A.
2. **Unit 8 stops at layer C** [DD]. No fourth layer (semantic entity, ontology, role
   assignment, BRW object) is introduced. Later BRW work may need one; that need
   does not place one inside this contract.
3. A candidate and an evaluation record are different object types with different
   identity namespaces. A record never reuses a `candidate_id`, never edits a
   candidate's `status` (which remains `candidate`), and never causes a candidate
   to be re-labelled as source fact or as interpretation.
4. The existence of a candidate does not imply an evaluation exists. The absence
   of an evaluation is meaningful: it means *not evaluated*, never *rejected*,
   and never *accepted by default*.
5. "No candidate was derived" (Unit 7) is different from `rejected` (Unit 8).
   Rejection can only be recorded about a candidate that exists.

## 6. Unit 7 input boundary

### 6.1 What Unit 7 guarantees [EI]

Verified from the implemented code and contract section 41:

- **candidate_id**: `sha256:` + lowercase SHA-256 of canonical JSON under protocol
  tag `macula.structural-candidate.v1`. Inputs: the seven-field snapshot, candidate
  kind, derivation kind, derivation version, scope (owning source node ID and
  ordered member token refs), ordered evidence (role, kind, source node ID) and
  payload (anchor and ordered child node IDs). No SQLite PK, path, timestamp,
  Python hash, process identity or random value participates.
- **candidate kind**: only `apposition`. **Derivation**: only `source-np-appos`,
  version `1`. Unknown kinds fail explicitly.
- **status**: only `candidate`. The DTO rejects any other status.
- **source snapshot binding**: read from the selected token's actual linked
  snapshot/file provenance; any change of source revision, manifest or file hash
  produces a distinct `candidate_id`.
- **scope**: exact materialized membership in canonical scripture order; never a
  Start/End envelope; discontinuous membership remains discontinuous.
- **evidence**: anchor first, then direct children in sibling order; source-oriented
  opaque node IDs only.
- **ordering**: candidates are returned nearest-first along self/ancestor order;
  no lexical node-ID order, PK order or insertion order.
- **surrogate-PK independence**: Unit 7 DTOs contain no local SQLite IDs.
- **read-only, in-memory**: no persistence, cache or sidecar; no write to the source.
- **absence of evaluation, confidence and semantic roles**: none is generated.
- **return convention**: unknown exact token ref -> `None`; valid token with no
  matching structure -> `()`; source/schema/ambiguity/topology failure -> explicit `QueryError`.

Unit 8 treats all of the above as **input**. It MUST NOT redefine, reinterpret or
extend any of them.

### 6.2 Unit 8 trust boundary [DD]

Unit 7 DTO construction validates only kind and status; it does not recompute
`candidate_id`, and `Literal` types are static-only (Unit 7 audit I2). A DTO
produced by `dataclasses.replace()` or by deserialization can therefore be
internally inconsistent. Unit 8 therefore adopts this rule:

> **Every candidate presented to Unit 8 is untrusted data until verified.**

Verification has two levels (precise definition in section 12.2):

- **V1 — offline self-consistency.** Recompute `candidate_id` from the candidate's
  own fields using the frozen `macula.structural-candidate.v1` protocol and require
  equality; validate closed vocabularies and non-empty scope and evidence.
- **V2 — source-grounded.** Re-derive through the *public* Unit 7 API
  `derive_structural_candidates(db_path, token_ref)` against the read-only source
  store and require field-for-field equality with a re-derived candidate.

Creating a new evaluation record requires V1 and V2. Auditing an existing record
requires V1, and V2 whenever the bound source store is available.

Unit 8 MUST NOT modify Unit 7, import Unit 7 private helpers as a trust shortcut,
or accept a "trusted DTO" exemption. A future implementation may reuse Unit 7
code, but may not weaken V1/V2.

## 7. Evaluation semantics

### 7.1 Logical record shape

This is a logical shape, not frozen Python or SQL.

```text
EvaluatedStructuralInterpretation(
    record_protocol,        # "macula.evaluated-structural-interpretation.v1"
    evaluation_id,          # "eval-sha256:" + 64 lowercase hex
    candidate,              # verbatim echo of ONE Unit 7 candidate (section 12.1)
    evaluator_class,        # "human" | "deterministic-policy"
    evaluator_label,        # human only; unauthenticated assertion
    evaluation_protocol_id,
    evaluation_protocol_version,
    disposition,            # "accepted" | "rejected" | "undetermined"
    rationale_evidence,     # ordered machine-checkable citations
    rationale_note,         # (text, language) | None  -- human prose
    event_key,              # human only; recording-event discriminator
    supersedes,             # None | one evaluation_id
)
```

An evaluation targets **exactly one candidate** [DD]. Comparative or batch
evaluations ("prefer C1 over C2") would require relational dispositions such as
*preferred*, whose semantics are not frozen; they are deferred. A caller may
create many single-candidate records.

An evaluation always applies to the candidate's **entire** exact scope [DD]. There
is no separate evaluated-scope field: partial evaluation would require new scope
arithmetic, which Unit 8 prohibits.

### 7.2 Field analysis

| Field | Why necessary | Class | In identity | Mutable | Omittable | Independently verifiable | False-confidence risk |
|---|---|---|---|---|---|---|---|
| `record_protocol` | Selects the identity/validation rules; allows future versions to coexist | metadata | yes | no | no | yes | none |
| `evaluation_id` | External identity of the record | derived | n/a (it is the digest) | no | no | yes (recompute) | none |
| `candidate.candidate_id` | The target; stable reference independent of PKs | derived (Unit 7) | yes | no | no | yes (V1; V2) | none |
| `candidate` echo (rest) | Offline audit: snapshot, scope, evidence, payload as evaluated | derived echo | transitively, via `candidate_id` | no | no | yes (recompute `candidate_id`) | echo could be read as source fact; it is labelled non-authoritative |
| `evaluator_class` | `human` and `deterministic-policy` must never be indistinguishable | provenance metadata | yes | no | no | partially (class rules) | low |
| `evaluator_label` | Distinguishes human evaluators without an account system | provenance metadata (asserted) | yes | no | omitted for deterministic | no (unauthenticated) | could imply authority; stated unauthenticated |
| `evaluation_protocol_id` / `_version` | Gives the disposition its meaning | metadata | yes | no | no | yes (closed registry) | none |
| `disposition` | The judgment | evaluator judgment | yes | no | no | no (judgment) | `accepted` could imply truth; semantics frozen in section 10 |
| `rationale_evidence` | Machine-checkable support, restricted to the candidate's own evidence/scope | derived citations | yes | no | only for `undetermined` | yes | none |
| `rationale_note` | Human reasoning | evaluator prose | yes (exact bytes) | no | deterministic: forbidden; human: required | no | prose could overclaim; cannot alter disposition meaning |
| `event_key` | Makes separately recorded identical human judgments distinct | metadata | yes | no | deterministic: forbidden; human: required | no | none |
| `supersedes` | Explicit same-evaluator reconsideration | metadata | yes | no | yes | yes (predecessor must exist and match) | "latest wins" is not implied |

### 7.3 Fields considered and rejected [DD]

| Candidate field | Decision | Reason |
|---|---|---|
| confidence / probability / certainty / score / percentage / weight / rank | **Prohibited** | No producer, calibration or comparison semantics exist (section 10.4) |
| wall-clock timestamp in the logical record | Excluded | Would make identity or ordering time-dependent; operational metadata may be stored separately by a future store, never in identity |
| separate evaluated-scope field | Omitted | Evaluation always covers the full candidate scope; a field would permit envelope/sub-scope shortcuts |
| multiple target candidates | Omitted | Needs comparative semantics that are not frozen |
| account / user id / signature | Omitted | No identity system exists; none is invented (section 9) |
| second candidate digest | Omitted | `candidate_id` is already a complete content digest; two competing fingerprints would invite divergence |
| separate logical "thread" id | Omitted | Single-level immutable identity plus explicit supersession edges is sufficient (section 11) |
| `preferred`, `canonical`, `confirmed`, `correct`, `human_verified` states | Prohibited | Imply truth/authority not defined here |
| semantic fields (actor, action, patient, event, result, identity, property, role) | Prohibited | Semantic-role firewall (section 20) |
| theological fields (meaning, doctrine, significance, canonical truth) | Prohibited | Theological firewall (section 20) |
| rationale translation stored as the rationale | Omitted | Localization is presentation; it cannot change evaluation semantics (section 16) |

## 8. Evaluation protocol and version

### 8.1 Rule [DD]

A disposition is meaningless without the rule it was made under. Every record
names an evaluation protocol `(evaluation_protocol_id, evaluation_protocol_version)`
drawn from a **closed Unit 8 registry**. An unknown id or version is rejected;
there is no nearest-match fallback.

A protocol version fully determines the evaluation criterion, the permitted
evaluator class and the permitted dispositions. Parameters, thresholds or
configuration variants are **not** a separate field: any behavioral change is a
new protocol version. This mirrors the Unit 7 derivation-version rule.

### 8.2 Registry at contract freeze [DD]

| Protocol id | Version | Evaluator class | Permitted dispositions | Candidate kinds |
|---|---|---|---|---|
| `human-structural-adequacy` | `1` | `human` | `accepted`, `rejected`, `undetermined` | `apposition` (derivation `source-np-appos`/`1`) |

Criterion of `human-structural-adequacy`/`1` (frozen with the version): the
evaluator inspected the candidate's cited source evidence in the bound snapshot
and judged whether the candidate's structural proposal — exactly as stated by its
candidate kind and payload, over exactly its scope — is an adequate *structural
description* of that evidence. The criterion concerns structure only. It does not
concern referents, semantic roles, discourse meaning, translation or theology.

No `deterministic-policy` protocol is registered by this contract [DEF]. The class
exists in the envelope so that determinism and judgment are never conflated
(section 17), but registering a deterministic protocol requires an amendment that
states its exact rule, inputs, permitted dispositions and independent criterion.
A deterministic protocol MUST NOT merely restate the Unit 7 derivation rule: a
policy that "accepts" every candidate because the derivation produced it adds no
independent judgment and would launder derivation output into acceptance.

New candidate kinds are likewise unsupported until an amendment adds them to the
registry (N4).

## 9. Evaluator provenance

The repository has no identity system [EI]. Unit 8 does not build one [DD].

| Aspect | `human` | `deterministic-policy` (reserved) |
|---|---|---|
| Provenance | `evaluator_label`: opaque, caller-asserted, unauthenticated text, 1-128 characters, no control characters, case-sensitive, stored exactly | The registered protocol id/version *is* the evaluator; no label |
| Reproducibility | Not reproducible from source bytes; auditable via the record | Reproducible from candidate + protocol/version |
| Versioning | Protocol version in record; label has no version | Protocol version fully determines behavior |
| Identity implication | Label and `event_key` participate in identity | No label, no `event_key`; identical inputs collapse |
| Rationale requirement | Non-empty note, and >= 1 evidence citation for `accepted`/`rejected` | >= 1 evidence citation for `accepted`/`rejected`; note forbidden |
| Repeated evaluations may coexist | Yes (distinct `event_key`s, distinct labels) | Only as distinct protocol versions; identical input is idempotent |

The label is a pseudonymous assertion. It is not an account, is not verified, and
is never evidence of authority. Evaluators using personal names are the caller's
choice; the contract requires none. An evaluator class for model-generated
evaluations (for example an LLM) is **not** defined [DEF]; Unit 7 already excluded
LLM interpretation, and no provenance semantics for it exist.

## 10. Disposition model

### 10.1 Vocabulary [DD]

Exactly three values. All others (including `confirmed`, `correct`, `preferred`,
`canonical`, `human_verified`, `refined`, `partial`) are unsupported (N6).

| Disposition | Exact meaning |
|---|---|
| `accepted` | The evaluator, under the named protocol/version, judged the candidate's structural proposal to satisfy that protocol's adequacy criterion for the cited evidence in the bound snapshot. |
| `rejected` | The evaluator, under the named protocol/version, judged the candidate's structural proposal **not** to satisfy that protocol's adequacy criterion for that evidence. It is not a claim that the source is wrong, and it is not "no candidate was derived". |
| `undetermined` | The evaluator considered the candidate and recorded neither judgment (insufficient evidence, or the criterion could not be applied). It differs from the absence of any record, which means *not evaluated*. |

### 10.2 What `accepted` is not [DD]

`accepted` MUST NOT mean, and no consumer may read it as:

- objectively true, linguistically infallible, or theologically true;
- accepted by MACULA, Clear Bible, or the source dataset;
- valid in any source revision other than the bound snapshot;
- valid for any derivation version other than the bound one;
- an upgrade of the candidate to a source fact;
- a semantic assertion (identity of referents, roles, events).

### 10.3 Mandatory reading rule [DD]

A record may be read only as:

> "Evaluator `<class>`/`<label>`, under protocol `<id>`@`<version>`, recorded
> `<disposition>` for candidate `<candidate_id>`, bound to snapshot `<snapshot>`,
> citing `<rationale_evidence>`."

WHO or WHAT: `evaluator_class` and `evaluator_label`. UNDER WHICH: protocol
id/version. AGAINST WHICH: `candidate_id`. BOUND TO WHICH: the echoed seven-field
snapshot. WITH WHAT: `rationale_evidence` and `rationale_note`.

### 10.4 No synthetic confidence [DD]

Unit 8 prohibits `confidence`, `probability`, `certainty`, `score`, `percentage`
and `ranking weight` (and any synonym). A numeric value requires a defined
producer, interpretation, calibration and comparison semantics; none exists. That
an evaluator can issue a disposition does not imply a probability. Absence of
confidence means *absent*, never `1.0`, never `0.5` (consistent with Unit 7
section 28 [EI]). Any record input carrying such a field is rejected (S1).

## 11. Identity model

### 11.1 Requirements [DD]

The external identity MUST NOT depend on: SQLite surrogate PKs, DB file path,
process ID, Python `hash()`, wall-clock-only uniqueness, insertion order, or any
mutable row ID. Unit 7's "derive identity purely from content" cannot simply be
copied: a candidate is a deterministic function of source bytes, whereas an
evaluation may contain judgment, and two separately made judgments with identical
content may be intentionally distinct.

### 11.2 Options considered

| Option | Result |
|---|---|
| Pure content-derived id | Deterministic and verifiable, but silently collapses separately recorded identical human judgments |
| Random UUID per record | Distinguishes judgments, but identity is then unverifiable and unreproducible; a hidden `uuid4()` inside constructors breaks determinism |
| Two-level (logical thread id + revision id) | Adds a mutable-looking "thread" notion and a second id family for no capability that supersession edges do not already give |

### 11.3 Recommendation [DD]

**A single-level, immutable, content-derived record identity, with distinctness for
human judgments supplied by an explicit `event_key` that is part of the content.**

- The recorder chooses `event_key` **once**, when the judgment is made (a UUID is
  recommended: opaque string of 1-128 characters from `A-Za-z0-9._:-`). The
  identity function never generates randomness; it only hashes the supplied value.
- `deterministic-policy` records have no `event_key`, so identical inputs yield
  the identical id (idempotent).
- Human records with identical content and **different** `event_key`s are distinct.
  Identical content with the **same** `event_key` is the same record (idempotent resubmission).

Identity input (ordered JSON array; field order explicit, no dictionary order):

```text
[
  "macula.evaluated-structural-interpretation.v1",
  candidate_id,
  evaluator_class,
  evaluator_label | null,
  evaluation_protocol_id, evaluation_protocol_version,
  disposition,
  [[citation_kind, citation_id], ...],        // canonical order, section 16.2
  [note_text, note_language] | null,
  event_key | null,
  supersedes | null
]
```

Serialization follows the Unit 7 convention: `json.dumps(ensure_ascii=True,
separators=(",", ":"), allow_nan=False).encode("utf-8")`, no trailing newline.
`evaluation_id = "eval-sha256:" + lowercase SHA-256 hex digest`.

Properties:

- The `eval-sha256:` prefix is distinct from Unit 7's `sha256:` so an evaluation id
  can never be mistaken for a candidate id (N2).
- The protocol tag is the first element (domain separation and versioning).
- The echoed candidate fields, being fully determined by `candidate_id`, are not
  hashed separately.
- No timestamp, path, PK, process id, hash seed or random value enters the id.
- A record cannot contain its own id, so supersession cycles are impossible by construction (section 15).

**Trade-off:** pure content identity (no `event_key`) is simpler but makes human
re-affirmations indistinguishable; the `event_key` costs one caller-supplied opaque
field but keeps identity verifiable, deterministic and explicit. A separate logical
thread id was rejected because the supersession edge already expresses lineage.

**Honest limit:** a content-derived id detects accidental alteration of a record;
it does **not** authenticate its origin. Anyone can compute a valid id for a
fabricated record (section 25).

## 12. Candidate and source snapshot binding

### 12.1 What a record stores about its candidate [DD]

`candidate` is a verbatim, non-authoritative echo of the evaluated Unit 7
candidate: `candidate_id`, `candidate_kind`, `derivation_kind`,
`derivation_version`, the seven-field `source_snapshot`, `scope`, `evidence` and
`payload`. Authority remains with Unit 7 derivation over the source snapshot.

The echo exists because `candidate_id` is a one-way hash: without the echoed
content an auditor could neither tell which snapshot to open nor recompute the
hash. Because `candidate_id` is already a complete content digest of the Unit 7
protocol, **no second digest is introduced** [DD]. The echo is small and does not
duplicate the source store. It carries `status = "candidate"` unchanged, and is
never presented as a source fact.

### 12.2 Verification levels [DD]

| Level | Needs | Checks |
|---|---|---|
| V1 offline | the record only | recompute `candidate_id` from the echo; recompute `evaluation_id`; closed vocabularies; protocol/class/disposition permissions; rationale citations drawn only from the echoed evidence/scope; field presence rules |
| V2 source-grounded | read-only source store | locate via the public Unit 7 API using any token ref in `scope.member_token_refs` as a lookup hint (the hint is not identity and is not stored), and require a re-derived candidate equal field-for-field to the echo |

Creation requires V1 + V2 against the current source store. V2 against a store with a
different snapshot **fails with an explicit snapshot mismatch**; it never
re-interprets the record as an evaluation of the other snapshot.

### 12.3 Changes over time [DD]

| Change | Effect on existing records | Effect on new work |
|---|---|---|
| Source revision / manifest / file SHA change | Records stay bound to the old snapshot; unchanged and valid as history | New derivation yields new `candidate_id`s; new records are required |
| Unit 7 derivation version change | Records stay bound to the old derivation version | New `candidate_id`; new evaluation required |
| `candidate_id` change for any reason | Records are **not** carried over | No cross-version equivalence, migration or inheritance |

Cross-version equivalence, migration or "same scope, new snapshot" linking is out
of scope and must not be implied by any query or field [DEF].

### 12.4 Two-connection observation (Unit 7 audit I1) [EI]

`derive_structural_candidates` reads through two separate read-only connections
and is not one atomic snapshot. For Unit 8 this is harmless in the intended
threat model: the source store is immutable and published without overwrite, and
V2 compares the entire re-derived candidate (including all seven snapshot fields)
to the echo, so any inconsistency produces a mismatch rather than a success. A
store replaced between the two connections is outside the model [RISK]. Unit 8
introduces no code to change this and does not treat I1 as fixed.

## 13. Exact scope and evidence binding

- Scope appears in a Unit 8 record **only** as the verbatim echo of the candidate's
  scope (owning source node ID and ordered member token refs). Unit 8 creates no
  scope field and no scope arithmetic.
- V1/V2 require the echoed scope to equal the candidate's own scope and the
  re-derived scope exactly. Never replaced by `min(ref)..max(ref)`, `Start..End`,
  a verse envelope, source-node-ID slicing or a PK range.
- A scope with members `[5,7,8,9]` is never `[5,6,7,8,9]` in any Unit 8 object or check.
- Canonical scripture order (scope members) and source sibling order (candidate
  evidence) remain distinct and are not conflated.

## 14. Multiple evaluations

One candidate may have any number of records [DD]. Reasons include a different
evaluator, a different protocol or protocol version, a changed mind, or a
repeated judgment.

- Multiple records are **not conflicts** and are never merged, averaged, voted or
  ranked. No consensus or majority mechanism is defined [DEF].
- Callers distinguish records by `evaluation_id`, and by `evaluator_class`,
  `evaluator_label`, protocol id/version, `event_key` and the supersession graph.
- Opposing dispositions (`accepted` and `rejected`) on one candidate coexist as
  distinct history. Consumers must not collapse them to a single "current" answer
  unless a future contract defines such a view.
- Ordering of a record set, where needed, is by explicit supersession edges only;
  never by insertion order or timestamp.

## 15. Supersession and history

Supersession is supported [DD] in a deliberately narrow form.

- A record may name **at most one** predecessor in `supersedes`.
- The predecessor must be a valid record for the **same candidate** (`candidate_id`)
  and the **same evaluator** (same `evaluator_class` and `evaluator_label`).
  The protocol id/version may differ (the same evaluator reconsidering under a newer
  protocol version).
- One evaluator cannot supersede another evaluator's record; those records coexist.
- Supersession means *"the same evaluator reconsidered"*. It is not "newer is
  better" and not "latest wins". Unit 8 defines no universal "current evaluation".
- The superseded record remains valid historical evidence, remains verifiable and
  remains queryable. Supersession never deletes or edits it.
- Cycles are impossible: a record's id is a hash that includes the predecessor id,
  so a record cannot reference itself or a descendant. A missing, mismatched or
  non-existent predecessor is rejected (S3).
- Several records may supersede the same predecessor (a fork). This is allowed as
  distinct history and is not resolved by Unit 8.
- Supersession scope is per candidate: a record never supersedes across candidates,
  snapshots or derivation versions.

## 16. Rationale model

### 16.1 Two separate parts [DD]

| Part | Nature | Role |
|---|---|---|
| `rationale_evidence` | Machine-checkable citations | Support; verifiable against the candidate |
| `rationale_note` | Human prose `(text, language)` | Explanation; never changes the meaning of the disposition |

Neither is a source fact. Neither becomes part of the candidate's identity;
`candidate_id` is unaffected by any rationale.

### 16.2 Machine-checkable citations

Each citation is `[kind, id]` with `kind` in `{"syntax_node", "token"}`:

- `syntax_node`: an `id` that appears in the candidate's `evidence` source node IDs;
- `token`: an `id` that appears in the candidate's `scope.member_token_refs`.

Citations may reference **only** the candidate's own evidence and scope [DD].
Anything else (including a source node that exists in the snapshot but is not part
of this candidate) is rejected; widening citations to other source context is
deferred [DEF] because it needs a context-selection contract.

Canonical order (identity-bearing): citations in candidate evidence order first
(anchor, then children), then tokens in scope order. Duplicates are rejected.
Lexical ID sorting is not used (Unit 7 section 29).

### 16.3 Human note

- `text` is stored and hashed as exact UTF-8: no Unicode normalization, no trimming,
  at least one non-whitespace character.
- `language` is a non-empty BCP 47 tag string, recorded verbatim.
- The note language does not alter semantics. A translation or localized rendering
  is a presentation artifact; if recorded as the evaluator's own note it is a
  different record. The localization system itself is not built here [DEF].
- The note MUST NOT contain, or be interpreted as, source facts or candidate fields.

### 16.4 Requirements by disposition

| Disposition | `rationale_evidence` | `rationale_note` (human) |
|---|---|---|
| `accepted` | >= 1 citation | required |
| `rejected` | >= 1 citation | required |
| `undetermined` | optional | required (states why) |

For `deterministic-policy` records the note is forbidden and the same citation
requirements apply.

## 17. Deterministic versus human evaluation

Both classes are supported by the envelope; **only `human` has a registered
protocol** at contract freeze (section 8.2) [DD]. They are never indistinguishable:
`evaluator_class` is identity-bearing and drives different field rules.

**Derivation reproducibility vs evaluation provenance [DD].**

- Unit 7 *derivation* is reproducible: same snapshot, evidence and derivation
  version yield the same candidate.
- A Unit 8 *evaluation* is reproducible only if its protocol is deterministic. A
  human evaluation cannot be regenerated from source bytes; instead its evaluator
  label, protocol/version, rationale, `event_key` and supersession history must
  remain auditable. Unit 8 never requires every evaluation to reproduce from source.

**Idempotence [DD].**

| Case | Behavior |
|---|---|
| Deterministic: same candidate + protocol/version | Same `evaluation_id`; repeating creates no new history entry |
| Human: identical content, same `event_key` | Same record; idempotent resubmission |
| Human: identical content, different `event_key` | Distinct records (two separately recorded judgments) |
| Human: same `(evaluator_label, event_key)`, different content, in one record set | Rejected as an `event_key` reuse conflict (S5) |

## 18. Persistence decision

Options:

- **A — in-memory evaluation DTO/API only.**
- **B — a separate projection/evaluation store.**
- **C — tables added to the authoritative MACULA source SQLite database.**

**Decision [DD]: Option C is rejected. Unit 8 does not include persistence; its first
implementation, if separately authorized, is Option A. Persistence, when later and
separately authorized, belongs in Option B.**

Reasoning:

- The source store is an immutable linguistic evidence boundary; the architecture
  places downstream interpretation in a separate projection store (spike sections 7.10 and 12.4;
  Unit 7 sections 24-25). Option C is incompatible with this and with the
  "no source schema/trigger/semantic column" prohibitions.
- Evaluation *semantics* (identity, vocabulary, validation, verification) are the
  hard-to-reverse decisions. They can be frozen and tested in memory without choosing DDL.
- Persistence design needs its own decisions (durability, backup, concurrency,
  append-only enforcement) that this task must not make.

**Consequence [RISK]:** an in-memory Unit 8 cannot retain a human judgment beyond a
process. Retention before a persistence unit exists is the caller's problem. Unlike
candidates, which are rebuildable from source, *human evaluations are not
regenerable*: a future store must treat them as primary records (durability and
backup are a persistence-unit concern).

### 18.1 Conceptual boundary for a later projection store [DEF]

Only the conceptual boundary; **no DDL, no indexes, no BRW design**:

- a physically separate file/database from the source store; the source is opened
  read-only (`mode=ro`, `query_only=ON`) and is never attached writably;
- primary logical key: `evaluation_id`; candidate reference: `candidate_id` plus the
  snapshot echo, with no foreign key into source tables and no surrogate PK as a reference;
- stored fields cover the record shape of section 7.1 (protocol/version, disposition,
  rationale, supersession, provenance);
- append-only: records are inserted, never updated or deleted by the evaluation
  workflow; insert by `evaluation_id` is idempotent;
- supersession stored as edges, never as in-place overwrites;
- the persisted form carries the `record_protocol` tag;
- deleting or rebuilding derived candidate data must not alter source or evaluation records.

## 19. Read-only source-store boundary

Regardless of persistence, the authoritative source database remains read-only to
Unit 8 [EI/DD]. Unit 8 MUST NOT:

- INSERT, UPDATE or DELETE source rows;
- add triggers, tables or columns to the source store (including semantic columns
  on `token` or `syntax_node`);
- change the source schema version (currently 2);
- persist an evaluation inside source facts;
- materialize `candidate_id` or `evaluation_id` into source rows.

Source access is only through the existing read-only Unit 4-7 query/derivation
boundary. Unit 8 adds no XML parser, XmlPro dependency, or second source of truth.

## 20. Firewalls

### 20.1 Semantic-role firewall [EI/DD]

Unit 8 evaluates **structural candidates only**. It defines no actor/action/event
ontology. The following are prohibited as unconditional rules, and the record has no
field in which they could be expressed:

```text
Cat=S  -> Actor        Cat=V -> Action/Event     Cat=O -> Patient/Result
Cat=P  -> Identity/Property
Frame A0 -> Actor      Frame A1 -> Patient       Frame A2 -> Recipient/Result
```

Source `Cat`, `Rule`, `Frame`, `Ref`, `SubjRef`, `Notes` and similar values are
evidence inputs, not BRW ontology commitments. Strings such as "Event" or "Result"
inside a source annotation do not create an evaluated Event or Result.
`accepted` on a candidate does not assign any semantic role.

Unit 8 MUST NOT create Actor, Action, Patient, Event, Result, Identity or Property
as executable or persistence entities.

### 20.2 Theological firewall [DD]

Structural evaluation is not theological evaluation. There are no fields such as
`theological_meaning`, `doctrine`, `christological_role`,
`soteriological_significance` or `canonical_truth`, and a note that asserts such
content does not change the record's reading rule (section 10.3). A structural
interpretation may later be useful to theological work; that does not place
theology in this contract.

### 20.3 Presentation firewall [EI]

Localization and UI vocabulary cannot change the semantics of any Unit 8 field.

## 21. Matthew 1:1 Verbless negative case

**Source facts [EI]:** Matthew 1:1 contains a `CL` with `Rule=P2CL` and
`ClType=Verbless`, eight noun leaves and **no verb leaf**.

**Unit 7 result [EI]:** exactly three nested Apposition candidates for `MAT 1:1!3`
(section 23), with no verb, copula, Action, Event or semantic Actor/Patient.

**Unit 8 rules [DD]:**

- Evaluation is not authorization to fabricate a Greek verb token, a source copula,
  a source node, a source ref, an `xml:id` or a `morphId`.
- Rationale citations may name only the candidate's own evidence nodes and scope
  tokens; a citation to a node or token that does not exist in the candidate is rejected (N12).
- The record has no field for an implicit relation. If a future evaluated
  interpretation wished to conceptualize an implicit relation, it would need an
  explicitly **non-source identity** and an explicitly later interpretive contract.
  That belongs to neither this unit nor an automatic extension of it. **Default:
  deferred** [DEF].
- `ClType=Verbless` remains source evidence; an evaluation cannot turn it into a verb.

## 22. Matthew 1:2 exact-membership negative case

**Source facts [EI]:** node `400010020050040` has `Rule=S-V-O`, `Start="5"`,
`End="8"` and exact membership `[5,7,8,9]`. Token 6 is not a member.

**Current Unit 7 behavior [EI]:** `derive_structural_candidates("MAT 1:2!5")` returns
`()`: S-V-O is not a candidate kind, so there is no candidate to evaluate. A
caller cannot create one through Unit 8.

**Unit 8 rules [DD]:**

- An evaluation referencing a candidate that purports to scope this node as
  `[5,6,7,8,9]`, `5..8`, or any envelope fails V1 (the recomputed `candidate_id`
  differs) or V2 (no such candidate is derived) and is rejected (N11). Token 6
  never enters because it lies inside a numeric envelope.
- Were a later candidate kind scoped to this node, its scope would carry exactly
  `[5,7,8,9]`, and any Unit 8 echo would preserve that verbatim.
- Unit 8 creates no scope arithmetic and no Start/End-derived scope.

## 23. Apposition worked example (illustrative)

Values below are the **actual** Unit 7 output of
`derive_structural_candidates("sblgnt-matthew.sqlite3", "MAT 1:1!3")` against the
existing read-only Matthew store at the time of this design. The evaluation record
that follows is **purely illustrative**: it is not a recorded evaluation, the
evaluator label is fictitious, and its disposition makes no claim about Matthew.

Snapshot (all three candidates):

```text
source_family:   MACULA Greek
edition:         SBLGNT
repository_uri:  https://github.com/Clear-Bible/macula-greek
revision:        8423afe47b9e8f24b7772e808af45c7159a6fe7e
manifest_sha256: 894CD81CFFE0DEB3FD5A6D29A81CB0694A6A82E547542014191C0E1DAC31731F
relative_path:   SBLGNT/nodes/01-matthew.xml
source_sha256:   FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4
```

The three nested Np-Appos candidates (nearest-first), kind `apposition`, derivation
`source-np-appos`/`1`, status `candidate`:

| # | candidate_id | anchor / scope node | exact scope members | evidence (anchor, then children) |
|---|---|---|---|---|
| 1 | `sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c` | `400010010030020` | `MAT 1:1!3`, `!4` | `400010010030020`; `400010010030011`, `400010010040011` |
| 2 | `sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f` | `400010010030040` | `MAT 1:1!3`..`!6` | `400010010030040`; `400010010030020`, `400010010050020` |
| 3 | `sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220` | `400010010030060` | `MAT 1:1!3`..`!8` | `400010010030060`; `400010010030040`, `400010010070020` |

Illustrative record over candidate 1:

```text
record_protocol:             macula.evaluated-structural-interpretation.v1
evaluation_id:               eval-sha256:<derived per section 11; not a recorded value>
candidate:                   verbatim echo of candidate 1 above (id, kind, derivation,
                             snapshot, scope, evidence, payload; status "candidate")
evaluator_class:             human
evaluator_label:             "example-reviewer"            (fictitious, unauthenticated)
evaluation_protocol_id:      human-structural-adequacy
evaluation_protocol_version: 1
disposition:                 accepted
rationale_evidence:          [["syntax_node","400010010030020"],
                              ["syntax_node","400010010030011"],
                              ["syntax_node","400010010040011"]]
rationale_note:              ("<illustrative text>", "en")
event_key:                   "<UUID chosen once by the recorder>"
supersedes:                  null
```

Reading (section 10.3): *"A human evaluator labelled `example-reviewer`, under
`human-structural-adequacy`@`1`, recorded `accepted` for candidate `sha256:ca5dc5…`,
bound to the SBLGNT snapshot above, citing these three source nodes."*

What this record does **not** do:

- it does not change candidate 1, its `candidate_id` or its `status`;
- it does not copy candidate fields into a new source fact;
- it does not say MACULA, Clear Bible or the dataset accepted the apposition, beyond
  what MACULA actually supplies (a source node with `Rule=Np-Appos` and these children);
- it asserts nothing about the referents being identical, and generates no meaning,
  semantic role or theological content;
- it does not evaluate candidates 2 or 3 (each needs its own record).

A second evaluator may record `rejected` for the same candidate, or the same
evaluator may later record a record with `supersedes` naming the first. Both coexist.

## 24. Error and fail-closed semantics

Behavior vocabulary: **REJECT** (explicit error; no record is created);
**NOT-FOUND** (absence is reported as absent, never as success); **ALLOW-DISTINCT**
(accepted as separate history); **DEFER-UNSUPPORTED** (explicit unsupported error;
future unit). Infrastructure/schema/provenance failures are errors, never
NOT-FOUND (Unit 4 convention [EI]).

| # | Case | Behavior |
|---|---|---|
| N1 | Candidate not found: well-formed `candidate_id` that V2 cannot re-derive | **REJECT** (not-found class); no record. A lookup of an unknown candidate reports **NOT-FOUND**, not an empty success |
| N2 | Candidate identity malformed (not `sha256:` + 64 lowercase hex; or an `eval-sha256:` id supplied as candidate id) | **REJECT** before any source access |
| N3 | Candidate present but candidate/snapshot evidence incomplete or inconsistent (missing/empty snapshot field, empty scope/evidence, recomputed id differs) | **REJECT**; never a success-shaped record |
| N4 | Unknown candidate kind (or derivation kind/version) | **DEFER-UNSUPPORTED** |
| N5 | Unknown evaluation protocol id or version | **DEFER-UNSUPPORTED** (closed registry; no fallback) |
| N6 | Unsupported disposition | **REJECT** |
| N7 | Record references candidate C but supplied evidence/citations belong to another candidate | **REJECT** (V1: citation outside C's evidence/scope, or echo does not recompute to C) |
| N8 | Attempt to bind only by a local surrogate PK | **REJECT**: no surrogate field exists; absent `candidate_id` is malformed (N2) |
| N9 | Source snapshot changes after a prior evaluation | Prior record stays valid, bound to the old snapshot (**ALLOW-DISTINCT** history); V2 against the new store fails with snapshot mismatch; no transfer |
| N10 | Candidate derivation version changes | New `candidate_id`; old records stay bound to the old one; new evaluation required (**ALLOW-DISTINCT**); no inheritance |
| N11 | Matthew 1:2 numeric envelope attempts to introduce token 6 | **REJECT** (V1/V2 scope mismatch) |
| N12 | Matthew 1:1 evaluation tries to invent a source copula/verb identity | **REJECT** (citation outside candidate evidence/scope; no field for it) |
| N13 | Semantic-role shortcut (S->Actor, V->Action/Event, O->Patient, P->Identity, A0/A1/A2) | **DEFER-UNSUPPORTED**: the record has a closed field set; unknown fields are rejected |
| N14 | Duplicate, logically identical evaluation | Deterministic: same id, **idempotent** (no new history). Human, same `event_key`: idempotent. Human, different `event_key`: **ALLOW-DISTINCT** |
| N15 | Conflicting or multiple evaluations of one candidate | **ALLOW-DISTINCT**; never merged, voted or ranked |

Supplemental cases:

| # | Case | Behavior |
|---|---|---|
| S1 | Confidence/probability/score/rank field present | **REJECT** (section 10.4) |
| S2 | Theological or semantic-entity field present | **DEFER-UNSUPPORTED** (section 20) |
| S3 | `supersedes` names a missing record, a record for another candidate, another evaluator, or the record itself | **REJECT** |
| S4 | Unknown `evaluator_class` (including any model/LLM class) | **DEFER-UNSUPPORTED** |
| S5 | Human `(evaluator_label, event_key)` reused with different content in one record set | **REJECT** |
| S6 | Record whose `evaluation_id` does not recompute, or whose echo `candidate_id` does not recompute | **REJECT** (self-inconsistent) |
| S7 | Deterministic-policy record carrying a note, label or `event_key`; human record lacking note, label or `event_key` | **REJECT** |
| S8 | `accepted`/`rejected` without the required citation(s) | **REJECT** |

## 25. Security and provenance implications

- There is no authentication, signing or authorization. The `evaluator_label` and
  `event_key` are unauthenticated assertions.
- The content-derived id gives **integrity against accidental change**, not
  **authenticity**: anyone can compute a valid id for a fabricated record. No
  consumer may treat a valid id as proof that a named person made the judgment.
- Free-text notes are untrusted data. Any future presentation must not assume they
  are safe to render or execute.
- `event_key` reuse detection depends on the record set the verifier can see
  (S5); a global guarantee needs a future store.
- Echoed candidate content is verifiable (V1/V2) but could be mistaken for source
  fact by a careless consumer; it is labelled non-authoritative.
- No network, secret, credential or personal-data handling is introduced.

## 26. Explicit non-goals

Unit 8 (design or any implementation under this contract) does not:

- authorize implementation, persistence, new schema or a new SQLite database;
- modify, remediate or re-audit Unit 7, Unit 5 M1 or Unit 7's audit M1;
- implement semantic roles, an ontology, or Actor/Action/Patient/Event/Result/Identity/Property entities;
- perform theological, discourse, translation or localization work;
- integrate with `bible-research-merged` or design any BRW schema/mapping;
- add confidence, scoring, ranking or consensus;
- define cross-snapshot or cross-derivation migration/equivalence;
- add candidate kinds, N1904, full-NT, other books, companion sources or XmlPro;
- build accounts, authentication, signing, a review UI or a human-review workflow;
- authorize another unit.

## 27. Deferred work

| Item | Disposition |
|---|---|
| Unit 8 implementation (in-memory API, DTOs, validators) | Deferred; needs separate authorization |
| Evaluation persistence / projection store DDL | Deferred; separate unit |
| Independent Unit 8 acceptance | Deferred; separate audit after any implementation |
| Deterministic-policy protocol registration | Deferred; amendment required |
| AI/model evaluator class | Deferred; no provenance semantics exist |
| Comparative/multi-candidate evaluation; `preferred` | Deferred |
| Wider rationale context citations | Deferred |
| Consensus / "current evaluation" view | Deferred |
| Implicit/elliptical relation interpretation (non-source identity) | Deferred; later interpretive contract |
| Actor/Action/Patient/Event/Result semantic projection | Deferred |
| BRW integration | Deferred |
| Theological interpretation | Deferred |
| Cross-snapshot migration / equivalence | Deferred |
| Full-NT / N1904 / other candidate kinds | Deferred |
| Record serialization beyond the frozen identity input; test vectors | Deferred to the implementation unit |
| Remediation of Unit 5 M1 and Unit 7 audit M1 | Deferred; not done here |

## 28. Open findings and risks

| Finding / risk | Status here | Relevance to Unit 8 |
|---|---|---|
| **Unit 5 M1** (inherited `TokenResult` exposes build-local PKs) | **Unresolved; unchanged** | Not a prerequisite. Unit 8 consumes only Unit 7 candidates, which contain no local IDs, and MUST NOT consume `TokenResult`/`SourceEvidence` local PK fields. Risk: an implementation that reads them could leak PK identity; AC-U8-22 forbids this |
| **Unit 7 audit M1** (original contract bytes unrecoverable) | **Unresolved; unchanged** | Not a prerequisite. Unit 8 relies on the contract section 41 identity protocol, the implemented code and the audit's independent testing of the committed state, not on provenance of sections 1-39 |
| Unit 7 I1 (two read-only connections) | Unchanged | Section 12.4; harmless under immutability; not treated as fixed |
| Unit 7 I2 (DTO does not recompute `candidate_id`; `Literal` static-only) | Unchanged | Design response: untrusted-input boundary, V1/V2 (section 6.2); Unit 7 not modified |
| Unit 7 I3 (integration tests opt-in; literal expectations) | Unchanged | A future Unit 8 implementation must not rely on opt-in-only evidence for its own gates |
| Unit 7 I4 (membership agreement verified for sampled anchors; broad membership relied on Unit 3 acceptance) | Unchanged | The recorded dependency on Unit 3 has since been independently accepted by a separate audit; I4 is not treated as fixed |
| Unit 7 I5 (`MAT` hard-coded in node resolution) | Unchanged | Unit 8 is Matthew-only through inherited behavior |
| Unit 7 I6 (Unit 5 M1 persists in `TokenResult`) | Unchanged | As Unit 5 M1 |
| In-memory evaluations are not retained | **Open risk** | Section 18 |
| Human evaluations are not regenerable | **Open risk** | Future store must treat them as primary records |
| Unauthenticated provenance | **Open risk** | Section 25 |
| `AGENTS.md` still carries pre-reconciliation status text for Units 3-5 | Observation only; not changed here | This design does not update agent instructions; a separately authorized governance task may |

## 29. Design decision register

| ID | Decision | Class |
|---|---|---|
| D-01 | Source/candidate/evaluation are three distinct object classes; one-way arrows | EI (Unit 7 sec 3, 39; spike sec 12) |
| D-02 | Unit 8 stops at layer C; no fourth semantic layer | DD |
| D-03 | Record targets exactly one candidate, whole scope | DD |
| D-04 | Disposition vocabulary `accepted`/`rejected`/`undetermined` with frozen meanings | DD |
| D-05 | No confidence/probability/score | EI (Unit 7 sec 28) + DD |
| D-06 | Closed protocol registry; version fully determines behavior | DD |
| D-07 | Evaluator classes `human` and `deterministic-policy`; no registered deterministic protocol; no AI class | DD / DEF |
| D-08 | No identity/account system; unauthenticated label | EI (none exists) + DD |
| D-09 | Single-level content-derived id with human `event_key` | DD |
| D-10 | Records immutable; reconsideration by new record | DD |
| D-11 | Supersession: one predecessor, same candidate and evaluator, not "latest wins" | DD |
| D-12 | Multiple evaluations coexist; no consensus | DD / DEF |
| D-13 | Candidate echo + `candidate_id` as sole digest; V1/V2 verification | DD |
| D-14 | Old evaluations stay bound to old snapshot/derivation; no migration | EI (spike sec 12.4; Unit 7 sec 6) + DD |
| D-15 | Exact scope only as echo; no scope arithmetic | EI (Unit 7 sec 9, 16) |
| D-16 | Rationale = machine citations + prose, citations limited to candidate | DD |
| D-17 | Persistence not in Unit 8; Option A first, Option B later; Option C rejected | DD / DEF |
| D-18 | Source store read-only | EI |
| D-19 | Verbless: no copula/verb; implicit relations deferred | EI + DEF |
| D-20 | Semantic-role and theological firewalls | EI + DD |
| D-21 | Unit 7 DTOs untrusted until V1/V2 | DD (responds to I2) |
| D-22 | Two-connection derivation harmless under immutability | EI (I1) + RISK |
| D-23 | Unit 5 M1 and Unit 7 M1 not remediated | EI |

## 30. Design questions answered

| Q | Answer |
|---|---|
| Q1 What is an evaluated structural interpretation? | An immutable, content-identified record of one evaluator's disposition for one Unit 7 candidate under a named protocol/version (section 1) |
| Q2 How does it differ epistemically from a candidate? | A candidate says "the derivation proposed this"; the record says "this evaluator, under this protocol, judged this proposal" (section 5) |
| Q3 Does evaluation imply truth? | No (section 10.2) |
| Q4 Dispositions and meanings | `accepted`, `rejected`, `undetermined`, as defined in section 10.1 |
| Q5 Confidence/probability? | Prohibited (section 10.4) |
| Q6 Multiple evaluations of one candidate? | Yes; distinct history, no consensus (section 14) |
| Q7 Evaluator and protocol representation | Class + unauthenticated label; closed protocol registry id/version (sections 8-9) |
| Q8 Binding to candidate/snapshot | `candidate_id` plus verbatim echo with seven-field snapshot; V1/V2 (section 12) |
| Q9 Derivation version changes | New `candidate_id`; old records stay bound; new evaluation needed (section 12.3) |
| Q10 Source snapshot changes | Same as Q9; no migration or equivalence (section 12.3) |
| Q11 Deterministic, human or both? | Envelope supports both, distinguishable; only human protocol registered now (sections 8, 17) |
| Q12 Identity model | `eval-sha256:` content id with human `event_key` (section 11) |
| Q13 Immutable? | Yes; reconsideration is a new record (sections 11, 15) |
| Q14 Supersession? | Yes, narrow: same candidate and evaluator, one predecessor, not "latest wins" (section 15) |
| Q15 Persistence part of Unit 8? | No (section 18) |
| Q16 Where should persistence live? | A separate projection store, never the source database (section 18.1) |
| Q17 May Unit 8 create Actor/Action/Patient/Event/Result? | No (section 20.1) |
| Q18 Implicit/copular entities for Matthew 1:1? | No; deferred (section 21) |
| Q19 How is discontinuous scope kept? | Verbatim echo of exact member refs; verified by V1/V2 (sections 13, 22) |
| Q20 Evidence needed to audit later | The record, V1 offline, and V2 with the read-only source store of the bound snapshot (section 12.2) |
| Q21 Which open findings matter? | Unit 5 M1 and Unit 7 I2/I1 are relevant; none is a prerequisite or fixed here (section 28) |
| Q22 What remains deferred? | Section 27 |

Quality gate — from this contract alone: the fact in MACULA is the source node/rule
(section 5, layer A); the proposal Unit 7 derived is the candidate (section 23);
Unit 8 evaluated exactly one whole candidate (section 7.1); the evaluator is the
class and unauthenticated label (section 9); under the named protocol/version
(section 8); against the echoed candidate and seven-field snapshot (section 12);
with citations and a note (section 16); the decision claims no objective truth
(section 10.2); no source fact changes (section 19); other evaluations may coexist
(section 14); and the record stays distinguishable after source or derivation
changes because the `candidate_id` differs (section 12.3).

## 31. Acceptance criteria

Each is independently reviewable as a design invariant or testable in a future
implementation.

- **AC-U8-01** An evaluation record is a distinct object type from a Unit 7 `StructuralCandidate`; the candidate `status` remains `candidate` and no candidate is mutated, replaced or relabelled.
- **AC-U8-02** Source facts are never changed by evaluation; no source row, schema or trigger is touched.
- **AC-U8-03** The evaluated candidate's `candidate_id` and content are unchanged by evaluation; the echo is non-authoritative.
- **AC-U8-04** The stable candidate reference is the Unit 7 `candidate_id`; no local PK is accepted or stored as a reference.
- **AC-U8-05** Every record carries the seven-field source snapshot (via the echo); verification against a different snapshot fails explicitly and never re-interprets the record.
- **AC-U8-06** Scope appears only as the verbatim candidate scope; V1 and V2 require exact equality.
- **AC-U8-07** No envelope shortcut: `[5,7,8,9]` is never `[5,6,7,8,9]`, and Matthew 1:2 token 6 never enters.
- **AC-U8-08** Evaluation protocol id and version are mandatory and drawn from a closed registry; unknown values are rejected.
- **AC-U8-09** The disposition vocabulary is closed (`accepted`, `rejected`, `undetermined`) with frozen meanings; none implies truth, authority or cross-version validity.
- **AC-U8-10** Evaluator class is closed (`human`, `deterministic-policy`), identity-bearing, and drives distinct field rules; no model/LLM class exists.
- **AC-U8-11** Evaluator labels are unauthenticated and no identity/account system is created or implied.
- **AC-U8-12** Deterministic-policy records have no label, note or `event_key`; identical inputs yield identical ids; no registered policy merely restates the derivation.
- **AC-U8-13** Human records require label, note and `event_key`; identical content with different `event_key`s yields distinct records.
- **AC-U8-14** Multiple evaluations of one candidate coexist; no merge, vote, ranking, "latest wins" or timestamp ordering exists.
- **AC-U8-15** Supersession requires one predecessor with the same candidate and evaluator; cycles are impossible; the superseded record remains valid and queryable.
- **AC-U8-16** Records are immutable; reconsideration creates a new record.
- **AC-U8-17** No confidence, probability, score, percentage or ranking weight exists in any record or input.
- **AC-U8-18** No unconditional S/V/O/P or Frame A0/A1/A2 mapping exists; the closed field set rejects semantic-role fields.
- **AC-U8-19** Matthew 1:1 remains Verbless: no verb, copula, Action or Event is created, and the implicit-relation question stays deferred.
- **AC-U8-20** No Greek token, source node, ref, `xml:id` or `morphId` is invented; rationale citations are limited to the candidate's own evidence and scope.
- **AC-U8-21** No theological field or interpretation exists in any record.
- **AC-U8-22** Surrogate-PK independence: no record or identity depends on `token_id`, `node_id`, `tree_id`, `element_id`, `book_id` or any local PK, and Unit 5 M1 fields are never consumed.
- **AC-U8-23** The source database is read-only to Unit 8 and its schema version is unchanged.
- **AC-U8-24** Persistence is not part of Unit 8; Option C (source-store tables) is prohibited; any persistence uses a separate store under a separate authorization.
- **AC-U8-25** Identity is deterministic: the frozen protocol and serialization produce equal ids across processes, hash seeds, paths and PK reallocation, with no timestamp, path, PK, `hash()` or hidden randomness.
- **AC-U8-26** Records are self-validating: a record whose `evaluation_id` or echo `candidate_id` does not recompute cannot be constructed or verified.
- **AC-U8-27** Incoming candidates are untrusted; creation requires V1 and V2, and Unit 7 is not modified to grant a trusted path.
- **AC-U8-28** Unknown or malformed input fails closed per section 24 (N1-N15, S1-S8); no failure is success-shaped, and infrastructure errors are never NOT-FOUND.
- **AC-U8-29** Rationale citations and human prose are kept separate; neither alters candidate identity or the meaning of the disposition; localization cannot change semantics.
- **AC-U8-30** A source snapshot or derivation-version change never carries an evaluation forward; no cross-version equivalence or migration exists.
- **AC-U8-31** Unknown candidate kinds, derivations and versions fail; each new kind requires an explicit amendment.
- **AC-U8-32** Existing Unit 1-7 behavior and regressions are unchanged by any Unit 8 implementation.
- **AC-U8-33** No BRW integration, semantic entity (Actor/Action/Patient/Event/Result/Identity/Property) or later-unit behavior is introduced.
- **AC-U8-34** Unit 8 status, acceptance and Phase status are changed only by separate governance records; the Phase remains AUTHORIZED.

## 32. Implementation authorization

**Unit 8 implementation: NOT AUTHORIZED.**

This design checkpoint does **not** authorize:

- `scripts/evaluated_interpretations.py` or any production module;
- any test, schema or schema-version change;
- any new SQLite database or projection store;
- candidate persistence or evaluation persistence;
- BRW integration;
- independent Unit 8 acceptance.

A future, separate user instruction must authorize implementation and must name at
least: the actual starting checkpoint, the module location, the exact public API
and DTOs, the persistence policy, the initial protocol registry entries, the test
scope, the authorized changed paths and the governance checkpoint boundary.

Current status: `CONTRACT DRAFT / NOT IMPLEMENTED`. Not `IMPLEMENTED`. Not
`INDEPENDENTLY ACCEPTED`. Phase remains **AUTHORIZED**.

## 33. Architectural stop line

```text
AUTHORITATIVE SOURCE
    immutable linguistic facts                    (Units 1-4)
              |
              v
    read-only SourceEvidence                      (Units 5-6)
              |
              v
--------------------------------------------------
DERIVED / REBUILDABLE BOUNDARY
--------------------------------------------------
              |
              v
      StructuralCandidate                         (Unit 7, accepted)
              |
              v
--------------------------------------------------
EVALUATION BOUNDARY                               (Unit 8 — DESIGN ONLY)
--------------------------------------------------
              |
              v
 EvaluatedStructuralInterpretation                (record of one evaluator's disposition)
              |
              X   <- STOP. Nothing below is defined, authorized or implied:
                      semantic roles, ontology, BRW entities, theology,
                      persistence implementation, cross-snapshot migration.
```

Source facts may cause candidates. Candidates never become source facts.
Candidates never become evaluated interpretations merely by being generated.
An evaluation never rewrites either.

**STOP.** Unit 8 implementation requires a separate, explicit user authorization.

## 34. Authorized initial implementation

**Current Unit 8 status: IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.**

The user separately authorized this bounded in-memory implementation from
`master` at `8f8b2e7642204378eb0e56e20d096b6233e409b2`.
That authorization supersedes the historical design-only status and implementation
stop lines above for this implementation only. Sections 1-33, including
AC-U8-01 through AC-U8-34, remain byte-for-byte unchanged as design-checkpoint
evidence. This section does not weaken any technical invariant or authorize an
independent acceptance audit.

### 34.1 Actual public boundary

Implementation: `scripts/evaluated_interpretations.py`.
Focused tests: `tests/test_unit8.py`. No existing production module is changed.

Frozen, slotted DTOs:

- `RationaleCitation(kind, citation_id)`: `syntax_node` or `token`.
- `RationaleNote(text, language)`: nonblank exact UTF-8 text and verbatim,
  syntactically well-formed BCP 47 tag (including private-use/grandfathered tags).
- `EvaluatedStructuralInterpretation`: exactly the section 7.1 fields,
  with tuple citations and the unchanged Unit 7 candidate echo. Its constructor
  validates V1 content and both identities. Source/history checks use the API.

```python
create_evaluated_interpretation(
    db_path, candidate, *,
    evaluator_class, evaluator_label,
    evaluation_protocol_id, evaluation_protocol_version,
    disposition, rationale_evidence, rationale_note, event_key,
    supersedes=None, prior_records=(),
) -> EvaluatedStructuralInterpretation

verify_evaluated_interpretation(
    record, *, db_path=None, prior_records=(),
) -> None

compute_evaluation_id(
    candidate, *,
    evaluator_class, evaluator_label,
    evaluation_protocol_id, evaluation_protocol_version,
    disposition, rationale_evidence, rationale_note, event_key,
    supersedes=None,
) -> str
```

Creation requires V1 and V2; `db_path=None` is not a creation exemption.
Offline verification validates V1 and supplied history; supplying `db_path` also
requires V2. The identity function validates V1 content only and does not access
the source store or history, nor generate event keys. Errors use existing
`source_query.QueryError`; closed Python signatures reject unsupported fields.

V1 independently encodes the frozen `macula.structural-candidate.v1` array,
without importing private Unit 7 identity helpers. It validates candidate-id
syntax/equality, kind/derivation/version/status, all seven nonempty snapshot
fields, nonempty immutable exact canonical scope, ordered anchor/child syntax-node
evidence, matching Apposition payload and no local-PK identity.

V2 calls only public `derive_structural_candidates`, using the first exact scope
token ref as a lookup hint, then requires field-for-field candidate equality.
Source access remains through Unit 7's existing read-only boundary.
Unknown exact candidates raise `candidate not found in bound source store`;
different source snapshots raise `candidate source snapshot mismatch`; altered
echoes for a re-derived anchor raise an explicit source-grounded mismatch.
Infrastructure/schema errors propagate, never becoming not-found or empty success.

Exactly section 8.2's initial registry is implemented:
`human-structural-adequacy` / `1`, class `human`, kind `apposition`,
derivation `source-np-appos` / `1`, dispositions accepted/rejected/undetermined.
There is no registered deterministic-policy protocol or AI/model evaluator.

Rationale cites only the candidate's own evidence/scope, in evidence-then-token
order. It is not sorted or normalized. Human labels, explicit bounded event keys
and notes are mandatory; accepted/rejected require at least one citation.
`prior_records` is a tuple of V1-valid records including complete supersession
ancestry. Verification checks the whole supplied set for event reuse conflicts
and invalid edges, without requiring insertion order. Same-evaluator/candidate
supersession preserves predecessors, permits forks and introduces no "latest wins".
Event uniqueness cannot be guaranteed outside caller-supplied history.

### 34.2 Frozen literal identity vector

The frozen candidate vector has candidate id:

```text
sha256:7f5ec0e7ad1a70565f1ef852f0b466213b03600214505408e61b809d9fae7a7c
```

Its snapshot fields, in order, are `family`, `edition`, `urn:source`, `revision`,
`manifest`, `source.xml`, `digest`. Scope is node `n:\u03b1` with sole token
`MAT 1:1!3`; evidence is that anchor only, with an empty child payload.
These synthetic strings are test data, not a source snapshot claim.

Literal evaluation identity input (one UTF-8 line; backslash escapes shown are
the actual ASCII JSON bytes; no trailing newline):

```json
["macula.evaluated-structural-interpretation.v1","sha256:7f5ec0e7ad1a70565f1ef852f0b466213b03600214505408e61b809d9fae7a7c","human","example-reviewer","human-structural-adequacy","1","accepted",[["syntax_node","n:\u03b1"],["token","MAT 1:1!3"]],["  \u03b1\r\n","el"],"event:1",null]
```

Expected literal identity:

```text
eval-sha256:b13074925b58de0b3595d088e7f6c505906d1f34500e1af78bb017aa6eaf83b0
```

The test fixes both the input bytes and digest; it does not derive its expected
digest from the production identity function. Serialization remains exactly
`json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")`.

### 34.3 Implementation validation and checkpoint

Commands actually run successfully:

```powershell
$env:MACULA_UNIT8_INTEGRATION = "1"
$env:MACULA_UNIT8_DATABASE = "C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3"
python -B -m unittest tests.test_unit8
python -B -m unittest tests.test_unit4.Unit4FastTests tests.test_unit5.Unit5FastTests tests.test_unit6.Unit6FastTests tests.test_unit7.Unit7FastTests
python -B -m scripts.verify_unit1
python -B -m scripts.source_schema
```

- Unit 8: **51 passed, 0 failures/errors, 0 skipped** (50 synthetic fast tests,
  1 opt-in read-only existing-Matthew integration test).
- Unit 4-7 fast regressions: **62 passed, 0 failures/errors, 0 skipped**
  (Unit 4: 11; Unit 5: 16; Unit 6: 19; Unit 7: 16).
- Unit 1 verifier: PASS. In-memory source-schema verifier: PASS (version 2).
- Python 3.10 syntax parsing and current-runtime compilation: PASS.
- Matthew integration re-derived all three actual Matthew 1:1 candidates and
  verified test-only undetermined records, preserved Verbless/eight-noun facts,
  and confirmed Matthew 1:2 `[5,7,8,9]` membership excluding token 6.
- Source DB before/after: **160,968,704 bytes**, SHA-256
  `E52DB7E2ABDB1C2B9B4F93060312587A1363066378B7A0C9B8FB72475C25CE7E`,
  `user_version=2`, unchanged schema/catalog/index inventory.
- No Unit 3 discovery, second-full-build gate or Matthew rebuild was run.
  The existing ignored database is not a deliverable.
- Protected `C:\Works\macula-greek` and `C:\Projects\bible-research-merged`
  remain untouched.

Checkpoint boundary: one implementation commit with sole parent
`8f8b2e7642204378eb0e56e20d096b6233e409b2`. Its actual SHA, sole parent and final
worktree state are reported after Git creates it; they are not fabricated inside
the commit or added by amending it.

### 34.4 Effective stop line

**UNIT 8 IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.**
Implementation validation is not an independent acceptance audit.
The Phase remains **AUTHORIZED**, not COMPLETE or CLOSED.
Unit 5 M1 and Unit 7 audit M1 remain unresolved; prior acceptance decisions and
informational findings are unchanged.

No persistence, semantic roles, confidence, BRW integration, source-schema
changes or Unit 9. No deterministic-policy registration, AI evaluator,
cross-snapshot migration or new candidate kind. Stop after this implementation
checkpoint; independent acceptance requires a separately authorized task.

## 35. Amendment 1 reference

Unit 8 Amendment 1 extends the closed `human-structural-adequacy/1` registry to the
Unit 9 candidate tuple `clause-structure / source-rule-s-v-o / 1` while preserving the
`apposition / source-np-appos / 1` tuple. Sections 1-34 above are historical and are not
rewritten: statements in them that Unit 7 `StructuralCandidate` is the only supported
candidate type, or that new clause DTOs are unsupported for evaluation, are superseded
for that tuple only by
[UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md](UNIT-8-AMENDMENT-1-SVO-EVALUATION-REGISTRY.md).
The protocol version, identity serialization, V1/V2 semantics, rationale and
citation-order rules, firewalls and the no-persistence decision are unchanged.

**UNIT 8 AMENDMENT 1 IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.**
