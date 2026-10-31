# Source Fidelity Contract

The machine-readable authority is [the Unit 1 contract](../../contracts/macula-sblgnt-matthew.unit1.json). Revision and exact artifact checksum jointly define the input; its allowlist contains only SBLGNT Matthew nodes. Changing either requires separate source-drift authorization, not automatic refresh.

| Invariant | Required boundary |
|---|---|
| F-01 | Raw source is source authority. |
| F-02 | Future typed/normalized fields are deterministic mirrors and must not overwrite raw source. |
| F-03 | Missing and present-empty must remain distinguishable. |
| F-04 | XML attribute identity preserves namespace, name, and case. |
| F-05 | Greek surface text must not undergo destructive normalization. |
| F-06 | Lemma must not replace token occurrence. |
| F-07 | Exact canonical membership comes from tree ancestry, not Start/End or an envelope. |
| F-08 | Upstream identifiers require source, edition, and version scope. |
| F-09 | Unknown/unresolved information is retained or explicitly diagnosed, never silently discarded. |
| F-10 | MACULA annotations are not automatically BRW evaluated interpretations. |

## Independent source identities

`ref` (scripture coordinate) and `Ref` (referent annotation) remain distinct. `Id`, `xml:id`, `nodeId`, and `morphId` are not one generic ID. `xml:id` uses the XML namespace `http://www.w3.org/XML/1998/namespace`; `FunctionalTag` and `FormalTag` remain two fields even when their values agree in the primary fixture.

## Ordering and membership

Keep these seven concepts separate: source child/sibling order, tree leaf traversal order, source Start, source End, scripture coordinate, canonical scripture order, and exact node-token membership.

The [boundary fixture](../../fixtures/matthew-1-2-boundary.expected.json) freezes tree order `MAT 1:2!6` before `MAT 1:2!5`. The designated subtree's source span is `5..8`, but ancestry yields scripture members `5,7,8,9`; token `6` is an interior envelope non-member. No membership persistence is implemented here.

The [primary fixture](../../fixtures/matthew-1-1.expected.json) preserves eight token occurrences, missing attributes, and source text/Unicode `Ἀβραάμ.` separately from NormalizedForm `Ἀβραάμ`. No normalization is applied to source text.

## Semantic non-authorization
The contract prohibits `S→Actor`, `V→Action`, `V→Event`, `O→Patient`, `P→Identity`, `P→Attribute`, `A0→Actor`, `A1→Patient`, and `A2→Recipient`. These pairs are prohibitions, not executable mappings. No fixture/verifier/test helper applies them.

`ClType=Verbless` is a source fact. Do not invent a copula, implicit verb, Action, or Event. No SQLite schema/database, importer/exporter, annotation/reference parser, companion integration, N1904 work, or BRW projection is authorized by this contract freeze. Unit 2 requires separate authorization.
