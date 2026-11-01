# Post-Unit-4 Product Readiness Conclusion

> **Document purpose:** Preserve the conclusions from the post-Unit-4 read-only SQLite product-readiness exploration.
>
> **Evidence boundary:** This note combines (1) previously documented/independently verified source facts and architecture constraints, and (2) manual read-only SQLite observations performed after Unit 4. Manual SQLite observations are product-readiness evidence, not independent acceptance.
>
> **Encoding:** UTF-8 (with BOM) is recommended when this file is consumed by Windows tools. Greek and Chinese text must be preserved exactly and must not be converted through a legacy code page.

## 1. Readiness decision

**Decision: READY FOR PRODUCT-ORIENTED DESIGN. Unit 5 remains NOT STARTED.**

The important post-Unit-4 discovery is that the first product-facing linguistic experience does **not** require a separate, large MACULA syntax-mapping engine.

The emerging product path should be:

```text
SQLite Source Store
        ↓
Thin Read-Only Navigation
        ↓
Localization
        ↓
Presentation
```

rather than:

```text
SQLite
   ↓
Large Syntax Mapping Engine
   ↓
Reconstructed Linguistic Model
   ↓
Presentation
```

The source architecture already treats the database as an immutable linguistic store, with downstream localization/explanation/interpretation kept separate from source facts.

---

## 2. Evidence boundary

This conclusion deliberately distinguishes three evidence classes.

### A. Independently verified upstream facts

The accepted Matthew fixtures establish, among other things:

- Matthew 1:1 contains 26 source nodes, 25 node-to-node relations, and 8 noun-token leaves.
- The clause is explicitly `ClType=Verbless` and contains no verb leaf.
- The final Matthew 1:1 surface is `Ἀβραάμ.` while its normalized form is `Ἀβραάμ`.
- Matthew 1:2 contains a real tree-order/canonical-order counterexample.
- The `S-V-O` subtree with source `Start=5`, `End=8` has exact descendant membership `[5, 7, 8, 9]`, with token 6 excluded because it is a sibling, not a descendant.

### B. Architecture constraints already established

The source-store architecture establishes that:

- `parent_node_id + sibling_ordinal` is sufficient to restore the current ordered rooted syntax tree.
- `node_token_membership` represents exact descendant-token membership and must not be reconstructed from `Start/End` arithmetic.
- source `Head` is the zero-based index of a direct child.
- following head-child links downward may produce a recomputable lexical head, but does not produce semantic roles such as Actor or Action.
- original linguistic facts, deterministic localization labels, and human-readable explanation belong to separate layers.

### C. Post-Unit-4 manual SQLite observations

The following observations were made manually with read-only SQL against the actual SQLite produced by the current vertical slice. They are not independent acceptance claims.

They demonstrated that the relational store can directly expose:

```text
verse → ordered tokens

token → linguistic attributes
token → syntax leaf
token → ancestor chain

node → parent
node → ordered direct children
node → exact member tokens
node → source Head child
node → lexical-head path
```

---

## 3. Token product readiness

The actual `token` schema observed in SQLite contains the fields needed for an initial token-oriented study experience, including:

```text
ref_raw
chapter
verse
verse_token_ordinal

source_direct_text
unicode_raw
normalized_form
unicode_lemma

case_raw
gender_raw
number_raw
person_raw
tense_raw
voice_raw
mood_raw
type_raw
degree_raw

functional_tag
formal_tag
strong_number

english
mandarin
gloss
lex_domain_raw
```

The Matthew 1:1 token query demonstrated that these can be consumed together as an occurrence-level research record.

Example source facts for `MAT 1:1!3` include:

```text
surface:  Ἰησοῦ
lemma:    Ἰησοῦς
case:     Genitive
gender:   Masculine
number:   Singular
type:     Proper
Strong:   2424
English:  Jesus
Mandarin: 耶稣
Gloss:    of Jesus
```

This means an initial **Token Card** does not require another linguistic mapping database.

---

## 4. Syntax topology product readiness

The actual `syntax_node` schema observed in SQLite includes:

```text
node_id
tree_id
element_id
parent_node_id
sibling_ordinal
upstream_node_id
id_raw
cat
rule
cl_type
start_raw
end_raw
head_raw
length_raw
```

This is enough to navigate the existing source topology without reparsing XML or constructing a second authoritative tree.

The Product Readiness conclusion therefore treats syntax navigation as primarily a relational-navigation problem, not a syntax-reconstruction problem.

---

## 5. Matthew 1:1: ancestor navigation

A recursive SQLite query starting from `MAT 1:1!3` (`Ἰησοῦ`) returned this actual ancestor chain:

```text
depth 0  noun  Ἰησοῦ
   ↑
depth 1  np    N2NP
   ↑
depth 2  np    Np-Appos
   ↑
depth 3  np    Np-Appos
   ↑
depth 4  np    Np-Appos
   ↑
depth 5  np    NPofNP
   ↑
depth 6  np    NPofNP
   ↑
depth 7  P     Np2P
   ↑
depth 8  CL    P2CL / Verbless
   ↑
depth 9  S
```

This demonstrates the feasibility of a simple product interaction:

```text
click Greek token
        ↓
show token details
        ↓
show structural ancestor breadcrumb
```

A first version does not require a large tree-visualization framework.

---

## 6. Matthew 1:1: exact constituent membership

Manual `node_token_membership` queries returned actual member tokens for nested nodes:

```text
node 10  np / Np-Appos
  Ἰησοῦ χριστοῦ υἱοῦ Δαυὶδ υἱοῦ Ἀβραάμ.

node 11  np / Np-Appos
  Ἰησοῦ χριστοῦ υἱοῦ Δαυὶδ

node 12  np / Np-Appos
  Ἰησοῦ χριστοῦ

node 17  np / NPofNP
  υἱοῦ Δαυὶδ

node 22  np / NPofNP
  υἱοῦ Ἀβραάμ.
```

This turns a syntax node directly into a highlightable Greek constituent.

The product operation can therefore be:

```text
node_id
   ↓
node_token_membership
   ↓
canonical token ordering
   ↓
highlight exact Greek token occurrences
```

No phrase-boundary inference is required.

---

## 7. Start/End must not drive phrase highlighting

The independently verified Matthew 1:2 boundary remains the decisive invariant:

```text
source subtree:
Rule = S-V-O
Start = 5
End   = 8

exact member scripture ordinals:
[5, 7, 8, 9]
```

Token 6 lies inside the apparent numeric envelope but is not a descendant.

Therefore:

```text
Start/End
≠ exact constituent membership
```

Product phrase highlighting must use exact membership, not a continuous scripture range inferred from `Start/End`.

---

## 8. Source Head is directly usable for navigation

A representative `DetNP` observation produced:

```text
node 37
np / DetNP
Head = 1

├── [0] node 38
│       det
│       τὸν
│
└── [1] node 39        ← source Head
        np / N2NP
        Head = 0
        │
        └── [0] node 40
                noun
                Ἰσαάκ,
                lemma = Ἰσαάκ
```

This provides a concrete navigation path:

```text
DetNP
  ↓ Head=1
np / N2NP
  ↓ Head=0
lexical leaf: Ἰσαάκ
```

The architecture already treats lexical-head resolution as recomputable from source Head relationships. It should remain a deterministic query/helper, not a new source fact written back into the store.

---

## 9. Matthew 1:2: ordinary S-V-O clause

The manual exploration also exposed a source clause directly as:

```text
CL / S-V-O
Head = 1

├── [0] S / Np2S
│       Ἰσαὰκ
│
├── [1] V / Vp2V      ← source Head
│       ἐγέννησεν
│
└── [2] O / Np2O
        τὸν Ἰακώβ,
```

The exact clause membership query returned:

```text
MAT 1:2!5  Ἰσαὰκ
MAT 1:2!7  ἐγέννησεν
MAT 1:2!8  τὸν
MAT 1:2!9  Ἰακώβ,
```

The direct child membership query returned:

```text
S → Ἰσαὰκ
V → ἐγέννησεν
O → τὸν Ἰακώβ,
```

This is a major reduction in anticipated presentation work. The product does not need to infer an S/V/O grouping in this case. It can present the source syntax structure already stored in SQLite.

---

## 10. Product architecture consequence

The preferred product-facing architecture after Unit 4 is:

```text
Immutable SQLite Source Store
        │
        ├── existing verse query
        ├── existing exact-token query
        │
        └── future thin syntax navigation
                │
                ├── node
                ├── children
                ├── ancestors
                ├── exact members
                └── lexical head
                        ↓
                 Localization
                        ↓
                 Presentation
```

The application should not construct and maintain a second authoritative syntax model unless an actual future requirement proves one necessary.

---

## 11. Remaining deterministic mapping work is mainly localization

The Product Readiness exploration changes the expected nature of the remaining mapping work.

The primary deterministic mapping task is now presentation vocabulary, for example:

```text
Nominative → 主格
Genitive   → 属格
Accusative → 宾格

Masculine → 阳性
Feminine  → 阴性
Neuter    → 中性

np        → 名词短语
Np-Appos  → 同位结构
CL + Verbless → 无动词子句
```

Important contextual distinction:

```text
S as sentence root
≠
S as clause-level subject function
```

Localization must therefore be context-aware where the same source code appears at different structural levels.

Localization is not source mutation.

---

## 12. Recommended first product presentation

### 12.1 Token Card

A first Token Card can be based directly on existing source fields:

```text
Ἰησοῦ

Lemma
Ἰησοῦς

Strong
2424

Morphology
属格 · 阳性 · 单数 · 专有名词

English
Jesus

Mandarin
耶稣

Gloss
of Jesus
```

The exact user-facing typography and terminology remain presentation decisions.

### 12.2 Syntax Inspector

A first Syntax Inspector can begin with a breadcrumb rather than a large graphical tree:

```text
Ἰησοῦ
↑ noun
↑ N2NP
↑ Np-Appos
↑ Np-Appos
↑ Np-Appos
↑ NPofNP
↑ NPofNP
↑ P
↑ CL · Verbless
↑ S
```

### 12.3 Phrase Highlight

When a user selects a constituent:

```text
selected node
    ↓
exact member tokens
    ↓
highlight those token occurrences
```

This works for both contiguous and non-contiguous constituents because it is membership-based rather than envelope-based.

---

## 13. Candidate future thin-navigation requirements

These are **future requirement candidates**, not current Unit 4 API claims and not Unit 5 authorization:

```text
get_node(node_id)

get_children(node_id)

get_ancestors(token_ref or node_id)

get_members(node_id)

resolve_lexical_head(node_id)   # optional deterministic helper
```

The first four represent the smallest navigation surface suggested by the manual SQLite product exploration.

The lexical-head helper should be included only if product interaction demonstrates a need for it.

---

## 14. Semantic boundary remains unchanged

A source structure such as:

```text
S → Ἰσαὰκ
V → ἐγέννησεν
O → τὸν Ἰακώβ
```

must **not** automatically be rewritten as:

```text
Actor   → Isaac
Action  → begat
Patient → Jacob
```

The source architecture explicitly distinguishes syntax from evaluated semantic interpretation.

Reasons include:

- source `S` does not guarantee semantic agent;
- passive constructions can separate grammatical subject from agent;
- source `V` does not universally mean an Action or Event;
- source `O` does not universally mean Patient;
- verbless, predicate, complement, ellipsis, speech, PP, and multi-clause structures require separate treatment.

The required boundary remains:

```text
Linguistic Source Fact
        ↓
Derived Structural Candidate
        ↓
Evaluated Interpretation
```

No interpretive role should be written into the immutable source store merely because it is convenient for presentation.

---

## 15. Importer/parser boundary should remain closed

The Product Readiness discovery does not justify reopening importer or parser design.

The parser investigation already established that the inspected XmlPro parser loses 733 actual Matthew token direct-text occurrences consisting of single UTF-16 code units, whereas the explicitly configured standard XML routes observe zero empty token texts in that diagnostic. The authoritative direction remains the configured standard XML reader plus archived original bytes and deterministic source identity.

Therefore the current Product Readiness work should **not** trigger:

```text
importer rewrite
parser replacement
schema redesign
source-data normalization
```

The product layer should consume the store instead of changing the store to fit the UI.

---

## 16. Readiness matrix

| Capability | Product readiness conclusion |
|---|---|
| Canonical verse tokens | READY |
| Exact token lookup | READY |
| Token morphology / lemma / Strong / gloss data | READY |
| Token → syntax leaf | READY for design based on observed relational shape |
| Token → ancestors | READY for design based on manual SQLite exploration |
| Node → ordered children | READY for design based on stored topology |
| Node → exact member tokens | READY for design based on `node_token_membership` |
| Phrase highlighting basis | READY |
| Source Head navigation | READY for design |
| Lexical-head resolution | FEASIBLE as a deterministic helper; not yet a required public API |
| Chinese linguistic localization | DESIGN WORK REMAINS |
| Human-readable structural explanation | LATER PRESENTATION/EXPLANATION LAYER |
| Actor/Action/Patient/Event projection | NOT READY / OUTSIDE SOURCE NAVIGATION |

Here `READY` means that no source-store redesign blocker was found for the stated product-facing use. It does **not** mean independent acceptance, production release certification, full-NT readiness, or semantic-interpretation readiness.

---

## 17. Recommended work before Unit 5

The following may proceed as **Post-Unit-4 Product Readiness / hardening**, without starting Unit 5:

1. **Freeze the Unit 4 query contract**
   - `get_verse()`
   - `get_token()`
   - exact-match and not-found behavior
   - read-only expectations

2. **Preserve this Product Readiness conclusion**
   - keep manual SQLite observations clearly marked as manual exploration
   - do not relabel them as independent acceptance

3. **Draft a versioned localization catalog**
   - morphology labels
   - `Cat`
   - `Rule`
   - `ClType`
   - context-sensitive labels where required

4. **Design the Token Card**
   - decide which existing source fields are useful in the first view

5. **Design the Syntax Inspector**
   - ancestor breadcrumb
   - exact phrase highlight
   - clause child display
   - optional head indication

6. **Freeze candidate navigation requirements**
   - `get_node`
   - `get_children`
   - `get_ancestors`
   - `get_members`
   - optional lexical-head resolution

7. **Only after real product interaction confirms the minimum required capability, authorize Unit 5.**

---

## 18. Explicitly not authorized by this conclusion

This Product Readiness conclusion does **not** authorize:

```text
Unit 5 implementation
full New Testament import
N1904 integration
HTTP / REST / GraphQL API
UI implementation
large syntax-graph framework
Actor / Action / Patient automatic mapping
Event / Result automatic generation
implicit copula generation
theological interpretation
semantic projection
source schema redesign
importer rewrite
parser replacement
SQLite size/performance optimization
```

---

## 19. Final conclusion

**Post-Unit-4 Product Readiness: POSITIVE.**

The current relational linguistic store already exposes the structural facts required for a useful first Bible Research presentation layer: occurrence-level token facts, canonical ordering, ordered syntax topology, exact constituent membership, ancestor navigation, and source Head relationships.

The principal product challenge has therefore shifted.

It is no longer primarily:

> How do we reconstruct MACULA structure for the product?

It is now:

> Which source facts are worth showing, how should they be localized, and how can they be presented clearly without crossing from linguistic source facts into unreviewed interpretation?

**Recommended architectural direction:**

```text
SQLite Source Store
        ↓
Thin Read-Only Navigation
        ↓
Localization
        ↓
Presentation
```

**Governance direction:** Keep Unit 5 **NOT STARTED** until actual Bible Research interaction requirements define the smallest necessary syntax-navigation capability.

---

## 20. Source references

This note was prepared from the following preserved project evidence plus the manual SQL observations recorded in the working discussion:

- `MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md`
- `UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md`
- `XMLPRO-MACULA-PARSER-REUSE-ARCHITECTURE-SPIKE.md`
- `PHASE-STATUS.md`
- screenshots of the actual SQLite `token` and `syntax_node` schemas and Matthew 1:1 query output

The manual SQL result sets themselves should be retained separately if a formal reproducibility package is later desired.
