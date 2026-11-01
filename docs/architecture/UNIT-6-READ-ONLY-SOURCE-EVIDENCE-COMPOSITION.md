# Unit 6 - Read-Only Source Evidence Composition

**Status:** IMPLEMENTED / PENDING INDEPENDENT ACCEPTANCE.

## Authorization and scope

The user separately authorizes one composition slice over the existing schema-v2
SBLGNT Matthew store. This contract is recorded before production implementation.
The Phase remains AUTHORIZED. Unit 5 is independently accepted with minor findings;
M1 remains unresolved. Units 3 and 4 remain pending independent acceptance.
Unit 6 implementation validation is not independent acceptance and does not
authorize Unit 7. See [phase status](../governance/PHASE-STATUS.md).

## Public API and immutable result

[source_query.py](../../scripts/source_query.py) adds one primary API:

```python
get_source_evidence(db_path: str | Path, token_ref: str) -> SourceEvidence | None
```

`SourceEvidence` is a frozen composition of existing frozen DTOs:

| Field | Exact meaning and order |
|---|---|
| `token: TokenResult` | Unit 4 exact, BINARY source-ref occurrence; unchanged linguistic facts |
| `node: NodeResult` | Exact syntax leaf linked by `token.node_id`, projected to source identity |
| `ancestors: tuple[NodeResult, ...]` | Actual relational parent chain, nearest parent first, root last; excludes the leaf |
| `parent_children: tuple[NodeResult, ...]` | Only direct children of the immediate parent, ordered by `sibling_ordinal`; includes the selected leaf, not just siblings |
| `membership_node: NodeResult` | Immediate parent (`ancestors[0]`) if present; otherwise the selected root leaf |
| `contextual_members: tuple[TokenResult, ...]` | Exact stored membership of **`membership_node`**, ordered by book/chapter/verse/token coordinates |

A root token has `ancestors=()` and `parent_children=()` and uses its leaf's own
membership. A known empty membership is `()`, not not-found. No semantic clause
selection or ancestor-category selector is added. A higher constituent can be
inspected through the existing Unit 5 APIs using its ancestor source identity.

## Four distinct boundaries

1. **Source facts:** exact token ref, separate upstream node/xml/morph identities,
   text, linguistic mirrors, raw Cat/Rule/ClType/Start/End/Head/Length and source
   parent/child identities. Missing remains `None`; present-empty remains `""`.
   No source strings are normalized, substituted or decoded.
2. **Database-local coordinates:** `TokenResult` still exposes `token_id`,
   `node_id`, `tree_id`, `element_id` and `book_id`. This inherits unresolved Unit 5
   M1; these fields are build-local diagnostics, not persistent identities.
   `NodeResult` remains source-facing. Callers supply no surrogate PK.
3. **Deterministic composition:** reuse Unit 4/5 query primitives within one
   existing syntax read-only connection. Follow actual relational links, not
   source-ID digits. Every exposed node identity must pass the existing
   active-Matthew, exactly-one source-ID resolver; ambiguous identities fail
   closed. Membership comes only from `node_token_membership`, never spans,
   envelopes, `BETWEEN`, ordinal min/max or reconstructed ancestry.
4. **Prohibited interpretation:** the result is source evidence, not an
   interpretation. S/V/O remain labels; Verbless remains a source annotation.
   No inferred copula, verb, Actor/Action/Patient/Event/Result, semantic role,
   identity/property relation, translation or theological meaning is generated.

## Read-only and failure semantics

Reuse the Unit 3/4/5 SQLite URI `mode=ro`, `query_only=ON`, `foreign_keys=ON`,
`recursive_triggers=ON` boundary. The owned connection closes on success and failure.
No runtime XML parsing, network access, importer, cache, source-ID map persistence,
materialized bundle or source-store write is introduced. Schema/catalog/indexes
are unchanged and `PRAGMA user_version` remains 2. No migration is authorized.

Unknown exact refs return `None` only after required token/syntax/membership
schema checks. Empty initialized stores also return `None`. Invalid refs raise
`QueryError` under Unit 4's exact coordinate grammar; no prefix, normalized,
case-insensitive, morph/xml/source-node-ID or surrogate fallback exists.
SQLite/schema/contract failures, missing source identities/parents, duplicate
identities or cycles propagate as explicit `QueryError`, never empty evidence.
This is a query-access gate, not per-query exhaustive source-fidelity validation.

## Required verification

[test_unit6.py](../../tests/test_unit6.py) uses independent manual synthetic
construction and fixed source expectations for critical fields. Limited comparison
with existing APIs proves composition equivalence rather than supplying all expected
values. Cover exact/not-found/invalid refs, incompatible stores, leaf/root behavior,
ancestor/child order, stored and discontinuous membership, duplicate-source/cycle
errors, source-level invariance under reallocated surrogate PKs and SQLite-enforced
read-only access. Compare local PK variance separately; do not hide or repair M1.

Opt-in existing-Matthew integration follows `MACULA_UNIT6_INTEGRATION=1` and
`MACULA_UNIT6_DATABASE`, with no full rebuild:

- `MAT 1:1!3`: exact linked leaf `400010010030010`, nine nearest-first ancestors,
  N2NP / three Np-Appos / two NPofNP / Np2P / P2CL / source root;
  CL retains `ClType=Verbless`; selected leaf is absent from ancestry.
- Matthew 1:2 ancestor `400010020050040`: raw Rule/Start/End/Head are
  `S-V-O` / `"5"` / `"8"` / `"1"`; its direct children are S/V/O by sibling
  ordinal. Its exact Unit 5 membership is `[5,7,8,9]`, excluding token 6.
  Unit 6's own membership remains the specifically named immediate-parent context,
  not silently promoted to this higher constituent.

Run unchanged Unit 1/schema verifiers and Unit 1-6 regressions, retaining Unit 3's
documented second-build skip and using its external read-only reuse fixture with
fresh complete BYTE/NORMALIZED/schema/membership validation. Record real database
path/length/SHA-256/version before and after and require byte identity. Preserve
both protected repositories. No generated database/cache is a deliverable.

## Deferred work

M1 DTO cleanup, full audit archival, semantic projection, Bible Research
integration, UI/localization, alignment, other books/editions, XmlPro and physical
source-range mapping remain outside this authorization.
