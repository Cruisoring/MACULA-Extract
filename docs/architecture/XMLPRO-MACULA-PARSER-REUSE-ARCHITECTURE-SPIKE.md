# XmlPro → MACULA Parser Reuse Architecture Spike

Date: 2026-11-01. Investigation and controlled experiments only.

**Decision: use explicitly configured System.Xml.XmlReader for authoritative XML correctness; reuse XmlPro's source-range and ordered-occurrence ideas, not its parser, assembly, attribute lookup or serializer. Prefer Option D.**

Evidence labels throughout this report:

- **CODE EVIDENCE**: directly inspected local source; not necessarily executed.
- **EXPERIMENTALLY VERIFIED**: observations in the temporary experiment outputs.
- **BENCHMARKED**: the explicitly described measured workloads, not production ingestion.
- **DOCUMENTED**: local project/governance documentation.
- **RECOMMENDATION**: design input, not implementation or authorization.
- **NOT BENCHMARKED / NOT VERIFIED**: remaining limits.

## 1. Executive conclusion

**EXPERIMENTALLY VERIFIED:** XmlPro can reproduce the *specified narrow checks* of Matthew 1:1 and 1:2 when given its explicit XML parse profile and exact-name attribute access. This does not establish full source fidelity.

The decisive counterexample comes from the real, fixed Matthew file: XmlPro retains 56,488 Node occurrences and 18,329 token elements, but **733 token occurrences have empty parsed direct text where the standard parser observes a one-UTF-16-code-unit Greek word**. All 733 changed token texts are precisely single-code-unit-to-empty changes. Examples include `MAT 1:16!13` `ὁ`, `MAT 1:18!5` `ἡ`, and `MAT 1:18!17` `ἢ`.

**CODE EVIDENCE / EXPERIMENTALLY VERIFIED:** `XElement.Generate` checks `tag.Begin > tagEnd + 1`, rather than permitting a one-character gap. The raw source remains available through Context, but that does not repair the missing parsed text occurrence. Replacing missing text with Unicode/NormalizedForm would violate the authoritative source boundary.

Other disqualifying results include namespace identity absent from the object model, case-insensitive lookup fallback, acceptance of namespace-equivalent duplicate attributes, malformed quoted attributes silently losing data, HTML-only entities accepted as XML, generic PI failure, and incorrect serialization of mixed content.

**RECOMMENDATION:** retain original bytes and their checksum, record deterministic occurrence identities and diagnostic line/column positions, and make physical character/byte mapping an optional independent layer. Do not make an unvalidated lexical scanner responsible for XML correctness.

This report creates no production parser, importer/exporter, schema, database, project reference or Unit 2 authorization.

## 2. Evidence and source-directory state

### 2.1 Actual starting baselines

| Source location | Branch | Full HEAD | State |
|---|---|---|---|
| [MACULA-Extract](../../../../../../Projects/MACULA-Extract/) | master | `4cd957d7158cfbe0ea29a1afa56f09572fc877fa` | clean index/worktree; no untracked files |
| [macula-greek](../../../../../../Works/macula-greek/) | main | `8423afe47b9e8f24b7772e808af45c7159a6fe7e` | clean index/worktree; no untracked files |
| [bible-research-merged](../../../../../../Projects/bible-research-merged/) | master | `0e4c9baad299f7149cc71b35bcd5208297d4f8c0` | clean index/worktree; no untracked files |
| [XmlPro-main](../../../../../../Projects/XmlPro-main/) | NOT AVAILABLE | NOT AVAILABLE | source snapshot, **not a Git repository** |

XmlPro Git inspection returned “not a git repository.” No repository was initialized or repaired. Therefore this report cannot honestly describe XmlPro as Git-clean or provide a commit SHA. Its independent safety baseline is all **42 files, 6,393,126 bytes**, with relative paths, lengths and SHA-256 recorded in [xmlpro-start-files.json](xmlpro-start-files.json).

The MACULA-Extract checkpoint subject is exactly `record Unit 1 independent acceptance`, and its parent is `a0327c93db4f555443683f5ea2d2b447f2e52704`.

**DOCUMENTED:** [AGENTS.md](../../../../../../Projects/MACULA-Extract/AGENTS.md), [PHASE-STATUS.md](../../../../../../Projects/MACULA-Extract/docs/governance/PHASE-STATUS.md), [FIDELITY-CONTRACT.md](../../../../../../Projects/MACULA-Extract/docs/governance/FIDELITY-CONTRACT.md), the complete [independent acceptance audit](../../../../../../Projects/MACULA-Extract/docs/audits/UNIT-1-SOURCE-CONTRACT-INDEPENDENT-ACCEPTANCE-AUDIT.md), historical [Architecture Spike](../../../../../../Projects/MACULA-Extract/docs/architecture/MACULA-GREEK-TO-SQLITE-LINGUISTIC-STORE-ARCHITECTURE-SPIKE.md), [contract](../../../../../../Projects/MACULA-Extract/contracts/macula-sblgnt-matthew.unit1.json) and both [primary](../../../../../../Projects/MACULA-Extract/fixtures/matthew-1-1.expected.json)/[boundary](../../../../../../Projects/MACULA-Extract/fixtures/matthew-1-2-boundary.expected.json) fixtures were read from the actual repository.

Unit 1 is IMPLEMENTED / INDEPENDENTLY ACCEPTED. Phase remains AUTHORIZED, not COMPLETE/CLOSED. Unit 2 is NOT STARTED / NOT YET IMPLEMENTATION-AUTHORIZED. This investigation does not change any of those states. Downstream inspection was limited to Git safety metadata, not another phase authorization audit.

### 2.2 Runtime and build

- Windows x64; SDK `9.0.310`; experimental runtime **.NET 9.0.12**.
- XmlPro original library and MSTest project target **net5.0**.
- Original test package requirements: Microsoft.NET.Test.Sdk 16.7.1, MSTest.TestAdapter 2.1.1, MSTest.TestFramework 2.1.1, coverlet.collector 1.3.0.
- Original project also has a post-build `xcopy` of Data. It was not built in its source directory.
- Original solution restore was attempted only in a byte-identical TEMP copy, with all NuGet sources cleared and NuGet audit disabled. It failed with NU1100 for missing net5 reference packs and test packages.
- **BLOCKED BY NETWORK-DEPENDENT RESTORE** applies to the original net5 build/test route. No feed was enabled to overcome it. Original MSTest execution is **NOT VERIFIED**, not PASS.
- Alternative: a separate net9 Release experiment project compiled all 23 original library C# files verbatim. Original project files were neither edited nor imported as project references. Offline restore succeeded; final builds had zero warnings/errors.
- CLI telemetry was disabled for restore/build/experimental commands; CLI homes and package locations for restores were temporary. Shared compilation and MSBuild node reuse were disabled for builds.
- `DOTNET_TieredCompilation=0` for experimental processes.

No packaged README or LICENSE was found among the 42 snapshot files. Do not assume a redistribution license for copying this code into a future product. User-authorized local experimental copying is not a production redistribution decision.

### 2.3 Persistent experimental evidence

- [correctness.json](correctness.json): 49 synthetic cases × four implementations; real-source fixture observations; initial range checks.
- [diagnostics.json](diagnostics.json): seven additional cases, real lost-token samples, UTF-16/scalar/byte positioning and mutable-context evidence.
- [benchmark.json](benchmark.json): five iterations per workload, allocation measurements, approximate retained heap, output counts and staged-build timings.
- [original-offline-restore.log](original-offline-restore.log): actual original dependency blocker.
- [harness/Program.cs](harness/Program.cs), [harness/Spike.csproj](harness/Spike.csproj), [NuGet.Config](NuGet.Config): **experimental recipe only**, not production code or a parser implementation authorized for either project.

Temporary originals, copied library source, binaries, obj directories and CLI/package scratch directories are disposable; the small evidence and experiment recipe are retained to audit the report. All are outside the four source directories.

To reproduce the experiment, copy the unchanged original XmlPro library directory into `harness/source/XmlPro`, then restore the separate Spike.csproj with the supplied empty-source NuGet.Config and build Release using an already installed net9 SDK/reference pack. Run the resulting temporary assembly from this deliverable directory with mode `correctness`, `diagnostics` or `benchmark`, and TieredCompilation=0. The recipe uses the actual read-only source and accepted fixtures at the fixed paths; it is not a production implementation prompt.

## 3. XmlPro architecture summary

**CODE EVIDENCE:** the snapshot contains two projects and a solution: 23 library C# files, ten test C# files, five Data fixtures, and a gitignore. All library/test source, project files and solution were inspected; Data headers and small fixtures were read. The larger fixtures are a W3C XML specification with an external/internal DTD, XHTML, and Hebrew OSIS, not MACULA linguistic nodes.

The main flow is:

1. Caller decodes a whole file/string and obtains `char[]`.
2. `XTag.Generate` searches delimiters, constructs tag names and attribute objects.
3. `XElement.Generate` emits opening/closing tags, simple/declarative elements, and selected text blocks.
4. `XElement.Conclude` matches opening/closing tags and materializes parent/child lists.
5. Constructors materialize attribute dictionaries, combined child arrays and parent links.
6. `XDocument` selects one root element and exposes convenience search/printing APIs.

Range provenance and presentation are intertwined: StringScope simultaneously owns a Context reference, raw substring retrieval and HTML decoding; elements combine mutable parents, linguistic-agnostic tree contents, lookup fallback and serialization options.

Additional components inspected: ScopeExtensions, Indexer, all eight Interfaces, Chars, Cache, both enums, PrintConfig's static indent cache, and the unrelated Solution algorithm/test code.

## 4. Actual parser classification

**CODE EVIDENCE:** XmlPro is a **whole-document lexical scanner plus whole-document tree builder, retaining a DOM-like source-backed graph**.

It is not a true input-stream parser. Its public parsing entry points require a pre-existing char array, and inspected tests call `File.ReadAllText(...).ToCharArray()`. `yield return` makes enumeration lazy over that retained array, not streaming acquisition from a file or bounded lifetime of completed subtrees.

Conclude retains XElement/XTag/XAttribute/XTextBlock instances, Lists, arrays and Dictionaries. Scope-bearing objects share references to the same full Context array. This is not a separate char-array copy per object, but keeping one small object alive can retain the full array.

Tree construction is stack-based and mostly iterative. Searches, conversion/printing and child traversal have recursive paths. Synthetic depth 256 succeeded, but unbounded depth/stack behavior and full-NT scaling were **NOT BENCHMARKED**.

## 5. Component-by-component reuse classification

Categories: A REUSE AS-IS; B REUSE WITH LIMITED MODIFICATIONS; C REUSE CORE ABSTRACTION, REIMPLEMENT CODE; D REUSE TECHNIQUE / DESIGN IDEA ONLY; E BENCHMARK / REFERENCE ONLY; F DO NOT REUSE.

| Component | Category | Decision and evidence |
|---|---|---|
| Scope | **C** | Keep closed-open range idea; add explicit source identity, offset unit, bounds and total ordering. Current Begin-only comparison is unsafe as identity ordering. |
| StringScope | **D** | Raw substring idea is useful. Do not inherit its HTML decoding, mutable whole-array ownership or text/location coupling. |
| IScope | **C** | Retain inclusive Begin/exclusive End contract, but distinguish byte and UTF-16 units and source owner. |
| Source context ownership | **D** | Use one immutable archived source owner plus non-owning references/ranges; do not expose mutable char arrays. |
| XTag | **F** | Quote-insensitive delimiter search, no namespace resolution, incomplete grammar and wrong special-node serialization. |
| XAttribute | **C** | Reimplement an ordered namespace-aware attribute descriptor with presence and optional raw location. Do not reuse its grammar/HTML decoder. |
| XElement.Generate | **F** | Real 733-token text loss; trailing text omission; HTML-oriented defaults. |
| XElement.Conclude | **F** | Do not reuse this implementation as parser/build authority. Matching and document validity are incomplete; presentation-oriented structures are coupled in. |
| Stack-based tree construction technique | **D** | Standard parent stack and explicit ordered-child association are reusable ideas, implemented from validated reader events. |
| XElement object/search model | **D** | Parent/child/source occurrence concepts useful; existing search and text APIs must not govern ingest. |
| XTextBlock | **C** | Separate direct text occurrence/value from raw range and presentation; preserve kinds/order; remove decode/trim behavior. |
| XDocument | **D** | Document/root/source ownership concepts only. Existing object delegates printing to Root and drops document-level nodes. |
| ParseConfig | **C** | Replace mutable shared defaults/HTML flags with an explicit immutable XML safety/source-fidelity profile. |
| PrintConfig | **E** | Presentation reference only; defaults truncate/trim/insert indentation, caches are global. |
| Indexer | **E** | Generic search reference, not an XML grammar or location dependency. Prefer standard spans/search with tested bounds. |
| ScopeExtensions | **E** | Covers/range operations are useful requirements; current “intersection” and search bounds are wrong. |
| Interfaces | **C** | Reimplement narrow occurrence/range/content interfaces without case-insensitive lookup or serialization dependencies. |
| Attribute lookup/indexer | **F** | Never use best-match lookup for authoritative fields. |
| Serialization: XTag/XElement/XTextBlock/XDocument | **F** | Proven wrong names/repeated text/declarative placeholders/document-node loss. Use standard XML writing for future infoset reconstruction. |
| Original tests | **E** | Baseline examples/reference only; assertions sometimes certify deliberately illegal behavior. |
| Project/runtime configuration | **F** | Do not inherit net5 targets or old packages; future runtime selection is a separate authorized decision. |
| Chars | **E** | Character constants/reference, not a complete XML name/grammar definition. |
| Cache | **D** | Lazy retrieval idea only if profiling justifies it; no need to add it to authoritative ingest. |
| ElementType/TagType | **C** | Node-kind concept useful; current enum merges CDATA/comments/PI/DOCTYPE into declarative conveniences. |
| IGenerate and unrelated Solution code/tests | **F** | Empty marker and unrelated algorithms provide no MACULA value. |

No A/B recommendation is warranted for an authoritative ingest dependency. This does not imply every utility is unusable; it means direct code reuse brings more coupling/testing/license cost than the demonstrated benefit.

## 6. MACULA fidelity compatibility matrix

Standard columns refer to the tested explicit XmlReader profile; XDocument and XmlDocument are loaded through that same reader, not uncontrolled default overloads.

| Requirement | XmlPro current implementation | Standard route / architectural boundary |
|---|---|---|
| Ordered element hierarchy | Preserved on real Matthew's element shape | Preserve ordered events and wrappers |
| Parent/child and sibling occurrence | Element relationships available; incomplete content population | Explicit parent stack and ordinal policy |
| Complete element occurrence identity | Physical char scopes, but no source/snapshot-scoped identity | Add deterministic source-scoped occurrence path |
| Attribute presence | Dictionary/array can distinguish presence for ordinary XML cases | Enumerate ordered attributes; missing has no occurrence |
| Present-empty versus absent | Empty string supported; no-value HTML attributes add a null state | XML no-value is invalid; empty is a real value |
| Case-sensitive source identity | Storage usually exact; public lookup fallback violates it | Exact ordinal/expanded-name lookup only |
| Namespace-aware attribute identity | **Missing**; qualified strings are not URI/local-name identities | XmlReader LocalName/NamespaceURI/Prefix available |
| ref / Ref | Both retained when present; absent ref can falsely return Ref | Separate exact names and presence |
| Id / xml:id / nodeId / morphId | Literal names/values retained, but xml namespace absent | Preserve each scheme/name and xml:id URI |
| FunctionalTag / FormalTag | Separate literal entries on current source | Keep both; no tag merging |
| Direct text occurrences | **733 real token texts omitted** | Preserve direct event values, kind and sequence |
| Greek Unicode/punctuation | Longer fixture values preserved; single-code-unit Greek lost | Preserve source values; no Greek normalization |
| Surface versus NormalizedForm | Separate source attributes; no need to substitute | Never fill text from normalized/lemma/gloss |
| Source wrappers | Current Matthew elements retained | Preserve Sentences/Sentence/Trees/Tree/Node |
| Comments/PI/CDATA | Generic declarative model; PI failure and serializer loss | Preserve native node kinds; document content included |
| Deterministic locator | Scope lacks source and locator scheme identity | Snapshot/file hash + scheme + path |
| Unknown future attributes | Simple literal names retained, grammar/namespace exceptions unsafe | Enumerate without a field whitelist; retain unknown names |
| Malformed XML failure | Mixed: rejects some, silently accepts/repairs others | Fail with XmlException under explicit document profile |
| No implicit XInclude | Not expanded, but no namespace-aware guard | Native reader does not expand; explicit contract guard recommended |
| No external entity/network resolution | Scanner does not resolve; also does not prohibit DTD/entities | DTD Prohibit + resolver null; no validation/acquisition |
| No semantic normalization | No BRW roles generated, but HTML/XML conflation changes values | XML infoset processing only; interpretation separate |
| Start/End versus XML ancestry | They are just attribute strings | Membership from nesting, never span arithmetic |

**NOT VERIFIED:** this report is not a full-XML-specification certification or a production normalized round-trip test.

## 7. Scope and source-location analysis

**DOCUMENTED / CODE EVIDENCE:** [IScope.cs](../../../../../../Projects/XmlPro-main/XmlPro/Interfaces/IScope.cs), lines 11–26, defines `[Begin, End)`. [Scope.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/Scope.cs), lines 12–40, implements Length as End-Begin and rejects only Begin greater than End. Negative/context-out-of-bounds ranges remain possible.

**EXPERIMENTALLY VERIFIED:**

- Scope(5,6).CompareTo(Scope(5,9)) = 0; a SortedSet holds only one of those two ranges.
- `IntersectWith([1,3), [5,7))` returns `[1,7)`, an envelope, not an intersection. Source: [ScopeExtensions.cs](../../../../../../Projects/XmlPro-main/XmlPro/Extensions/ScopeExtensions.cs), lines 25–31.
- Searching scope `[0,3)` in `"abc"` for `"bc"` returns -1 because End==array.Length is wrongly rejected: lines 50–53.
- AllIndexesOf on `[0,2)` in `"zzabc"` yields index 2 for `"abc"`, outside the requested scope: lines 73–87 search the unbounded context with a mismatched stopping calculation.

`Covers` uses the expected inclusive/exclusive endpoints and is useful as a requirement. OfScope's negative indices are generic conveniences, not validated physical source offsets.

**CODE EVIDENCE:** Indexer/ScopeExtensions empty-pattern enumeration can fail to advance when partLength is zero. No unbounded empty-pattern enumeration was executed. Current Indexer complexity is generic naive search, not an XML lexer.

**EXPERIMENTALLY VERIFIED:** for text `α😀Z`, XTextBlock range `[3,7)` has Length **4 UTF-16 code units**, **3 Unicode scalars**, **7 UTF-8 bytes**. Current Scope is not a byte range.

For `<r>α😀<c/>Z</r>`:

| Position concept | Observed value |
|---|---:|
| `<c` opening's zero-based UTF-16 offset | 6 |
| zero-based Unicode scalar offset | 5 |
| zero-based UTF-8 byte offset | 9 |
| corresponding UTF-8 byte offset with three-byte BOM | 12 |
| XmlReader c element line/column | 1 / 8 |

The line/column points to the name position, not the opening `<` byte. It counts code units as observed in this sample, and cannot be used as a universal raw byte-index conversion formula.

**EXPERIMENTALLY VERIFIED:** mutating a temporary Context from `a='old'` to `a='Nld'` changes RawOuterText while cached attribute Value remains `"old"`. Record/init syntax does not make the underlying char array immutable.

**RECOMMENDATION:** a location descriptor must identify source owner/checksum, offset unit, bounds and mapping scheme. A total sort may use source identity, Begin, End and a tie-breaker; range order is not occurrence identity. Stable identity within fixed bytes is not stability across source revisions.

## 8. XML correctness analysis

**CODE EVIDENCE:** [XTag.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XTag.cs), lines 72–176, reads lookahead with `new Scope(i, i+9)` and finds the next closing delimiter through Indexer, without tracking quoted attribute value state.

**EXPERIMENTALLY VERIFIED:** `<n a="x>y">zz</n>` is accepted by XmlPro as an element with **no a attribute**, text `y">zz`, and serialization `<n>y&quot;&gt;zz</n>`. Standard implementations observe a=`x>y`, direct text=`zz`.

Malformed `<n a="bad/>` is accepted as an empty `<n />`; raw `<` inside a quoted attribute, invalid names, unbound prefixes and malformed comments are also accepted.

XmlPro does reject mismatched nesting, extra/missing closing tags, exact duplicate QName attributes (through ToDictionary), and multiple root elements (through XDocument.Single). The exception classes vary between FormatException, ArgumentException and InvalidOperationException; these checks are not a complete document grammar.

**EXPERIMENTALLY VERIFIED:** non-BMP text values work in all four implementations. The supplementary-name sample `<𐐀/>` is rejected by all tested implementations; XmlPro gives IndexOutOfRangeException and .NET gives XmlException. **NOT VERIFIED:** which XML-edition name repertoire the runtime claims; do not infer that this name is illegal in every XML specification version. A future source requiring expanded name-repertoire support needs its own compatibility gate. Current MACULA element/attribute names do not require that sample.

## 9. Namespace and attribute analysis

[XAttribute.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XAttribute.cs) stores decoded Name/Value and a raw character range. It does not store URI, local name, prefix binding or declaration scope. [XElement.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XElement.cs), lines 223–226 and 250–253, builds Dictionary<string,string>.

**EXPERIMENTALLY VERIFIED:**

- `<n xmlns="urn:u"><c/></n>` is accepted, but XmlPro provides no namespace identity for n or c.
- `p:x` and `q:x` with distinct namespace URIs remain different literal keys, but their expanded identities are unavailable.
- When p and q both bind `urn:u`, attributes `p:x="1"` and `q:x="2"` are invalid duplicates. Standard routes reject them; XmlPro accepts them.
- Namespace declarations are literal attrs in XmlPro, not namespace-aware declaration occurrences.
- In standard reader results xml:id has URI `http://www.w3.org/XML/1998/namespace`; XmlPro has no URI property. Experimental `null` represents **unavailable identity**, not a proven empty namespace.

**RECOMMENDATION:** prohibit Dictionary<string,string> as the authoritative attribute store. Use ordered occurrence descriptors containing namespace URI/local name, lexical QName/prefix where available, value and presence. An exact `(namespace URI, local name) → occurrence` lookup can be a convenience mirror. Original quote style/entity spelling/range comes from original bytes or an optional validated lexical mapper.

Attribute order in opening arrays/native enumeration was observed to follow source order in tested cases. XML infoset attributes are not a positional grammar; preserve an observed ordinal for provenance, but do not rely on Dictionary enumeration as the source-order contract.

XDocument stores expanded XNames, not a separate original-prefix field. The experiment's LINQ adapter infers a prefix from declarations; it does **not** prove exact original prefix selection when aliases share a URI. XmlReader and XmlDocument expose actual Prefix properties. Original bytes remain the lexical authority in all cases.

## 10. ref/Ref and source-ID identity

**CODE EVIDENCE:** [XElement.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XElement.cs):18 sets AttributeBestMatch=true. Lines 275–296 return an exact key if found, otherwise fall back to OrdinalIgnoreCase.

**EXPERIMENTALLY VERIFIED:** `<n ref="a" Ref="b"/>` returns exact ref=a and Ref=b. But `<n Ref="b"/>` makes the same `["ref"]` API return `"b"` despite ref being absent. This conflicts with the frozen source contract.

Existing [XElementTest.cs](../../../../../../Projects/XmlPro-main/XmlPro.MSTest/XElementTest.cs):95 explicitly queries `"Encoding"` against lowercase encoding, demonstrating reliance on the fallback.

**RECOMMENDATION:** remove this API from the authoritative path entirely, not merely advise careful calls. If retained in a future display/search-only helper, it must expose a clearly non-authoritative result with requested name, matched name and fallback status; it must never be used for presence checks, ingestion keys, provenance or joins. Global mutable switches are not a reliable boundary.

Id, xml:id, nodeId and morphId remain distinct source identifiers. xml:id's namespace is essential. Do not infer XML-ID/DTD typing, parse encoded IDs as ancestry, collapse schemes, or use a matching raw ID across editions/revisions as identity.

## 11. Whitespace, text and entities

**CODE EVIDENCE:** [StringScope.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/StringScope.cs):17–24 uses HttpUtility.HtmlDecode/HtmlEncode for both text and attributes.

**EXPERIMENTALLY VERIFIED:**

- Five predefined XML entities and numeric references, including a supplementary character, decode correctly in the tested ordinary cases.
- `&nbsp;` is accepted/decoded by XmlPro while standard XML rejects the undeclared HTML entity.
- `&madeup;` remains a literal string and is later escaped, silently turning invalid XML into ordinary text.
- `&#0;` becomes an actual NUL in XmlPro output; standard routes reject it.
- `&amp;lt;` is decoded once to literal `&lt;` by all four tested parse routes. **No automatic double-decoding in that route was demonstrated.** Explicitly calling Decode twice gives `<`, showing why decoded values must not be passed through another decoder.

HTML decode/encode must **not enter the authoritative XML path**. XML character-reference handling belongs to the standard parser; XML output escaping belongs to a standard writer. Lexical entity spelling is independently retained in original bytes.

**CODE EVIDENCE / EXPERIMENTALLY VERIFIED:** Conclude with no config uses DefaultHtmlParseConfig ([XElement.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XElement.cs):94). ParseConfig defaults trim text and drop whitespace. Explicit DefaultXmlParseConfig preserves whitespace and disables trim, but does not fix the one-character loss.

For `<n>  aa  </n>` under default Conclude, Content=`aa` while OuterText=`  aa  `. Content and raw-derived OuterText are different APIs, not interchangeable source facts.

Standard XML parsing normalizes line endings and literal attribute whitespace. Synthetic CRLF/CR text becomes LF in standard direct text; tabs/newlines inside literal attribute values become spaces. XmlPro keeps the raw CR/LF/tab in decoded values. The real file has 101,458 CRLF pairs; consequently its larger XmlPro text-character count is **not proof of better fidelity**, nor can raw total character counts alone establish semantic text equivalence.

GetText is a convenience concatenation of direct Texts, not a complete mixed-content sequence. **CODE EVIDENCE:** XElement.GetText ignores its connector argument; XDocument.InnerText searches an IElement-only indexer for ElementType.Text, which cannot supply ordinary XTextBlock entries. SearchText/recursive filtering also have null/recursion/pruning limitations. These helpers were not used to derive the source fixture facts.

Mandarin, lemma and NormalizedForm stay separate source fields. This investigation applies no semantic, grammatical, Greek Unicode or localization normalization.

## 12. Tree construction analysis

**CODE EVIDENCE:** Conclude pushes opening tags and saved parent/element/text lists, then pops/matches closing names. Constructors repair child Parent references and combine elements/texts by Begin. The ordinary element shape and the two target subtrees survive on Matthew.

**EXPERIMENTALLY VERIFIED:** mixed content `aa<b/>bb<c/>cc` has the correct parsed sequence of three text blocks and two elements when text segments exceed one code unit. Depth 256, self-closing and explicit empty elements were accepted.

However:

- one-character direct text is omitted;
- trailing text is never flushed after the final tag and is silently accepted;
- closing-stack underflow is an incidental exception, not structured XML diagnostics;
- declarative nodes do not have correct separate document node kinds;
- multiple roots are rejected by XDocument, but Conclude alone is not a document validator;
- opening/closing matches do not establish namespace correctness or name validity.

Tree order, canonical scripture order, source Start/End and exact membership remain separate. Experiments derive membership from descendants of the designated subtree. No Start/End interval generates a member.

**RECOMMENDATION:** a validated XmlReader event stream plus a depth/parent/ordinal stack can produce ordered source occurrences. Whether a complete tree, sentence-sized buffer or bounded output batches are materialized is a later design decision. No production sink was created.

## 13. Serializer analysis

**CODE EVIDENCE / EXPERIMENTALLY VERIFIED:**

1. [XTag.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XTag.cs):243 uses `Name` (tag name), not `a.Name`, when EncodeAttributeName=false. `<n a="1" b="2"/>` prints `<n n="1" n="2" />`.
2. [XElement.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XElement.cs):446 prints `Texts[0].Content` for each text node. Parsed `aa<b/>bb<c/>cc` serializes as `aa<b />aa<c />aa`.
3. Comments serialize as `<!--#comment-->`; CDATA becomes `<![CDATA[#cdata]]>`, losing original bodies even with explicit show-all flags.
4. [XDocument.cs](../../../../../../Projects/XmlPro-main/XmlPro/Entities/XDocument.cs):73 delegates AsStrings to Root. XML declaration and document-level stylesheet PI are lost.
5. Default PrintConfig/element profiles trim text, insert indentation/connectors, sort attrs, limit levels and often disable value/content encoding. They are display functions, not source reconstructions.

The mixed-content bug was verified with indentation/connectors disabled and TrimTextContent=false, so it is not explained away by display configuration.

[XTagTest.cs](../../../../../../Projects/XmlPro-main/XmlPro.MSTest/XTagTest.cs):55 actually asserts the wrong repeated tag-name attribute output. Passing those assertions would not establish XML correctness.

**RECOMMENDATION:** no XmlPro serializer in authoritative reconstruction. Use standard XML writing from namespace-aware ordered source facts; separately compare reconstructed infoset. Original byte fidelity is archive/checksum export, not serializer byte equality.

## 14. Security and deterministic input policy

**EXPERIMENTALLY VERIFIED:** all standard routes were created through a reader with DtdProcessing.Prohibit, XmlResolver=null, CheckCharacters=true, document conformance, preserved whitespace/comments/PI, MaxCharactersInDocument=64 Mi characters, and a finite entity-character setting.

DOCTYPE, internal entities, external entities and external DTD cases fail before entity resolution. External tests reference only inert `urn:blocked-by-spike:*` identifiers, not a network endpoint or a sensitive file. There is no resolution code in XmlPro's scanner.

**Important distinction:** XmlPro's lack of an external resolver does not make it standards-correct or contract-safe: it accepts DTD declarations/unresolved entities and turns their references into literal text. The standard route rejects DTD because of explicit policy, not because DTD is unsupported XML syntax.

**RECOMMENDATION:** future authoritative policy should explicitly require:

- fixed local allowlist, expected revision/checksum and size checks;
- DtdProcessing.Prohibit and XmlResolver=null, with no validation acquisition;
- ValidationType=None unless a separately authorized local validation policy exists;
- IgnoreWhitespace/Comments/ProcessingInstructions=false;
- CheckCharacters=true and ConformanceLevel.Document;
- bounded document size/character count and separately justified depth/resource limits;
- encoding detection from original bytes, strict malformed-input failure;
- no implicit XInclude; reject XInclude expanded names under this source contract rather than silently ignore them or open href;
- explicit diagnostics and failed-build handling; no partial-success-shaped authoritative output.

The synthetic XInclude element was accepted by all native routes **without expansion**. Application-level source-contract rejection is still needed; this experiment did not implement a production include guard.

MaxCharactersFromEntities is not a substitute for DTD prohibition. The 64-Mi-character limit is an experimental bound, not a frozen production limit or a full-NT certification. OS-level network tracing was **NOT VERIFIED**; no command enabled a package feed, XML resolver or external resource retrieval.

## 15. Original test quality

**CODE EVIDENCE:** 33 active TestMethod methods were counted, including three unrelated Solution tests. From inspected bodies, 19 methods contain direct/helper assertions; 14 are print/demo methods. Thus the suite is not “all demos,” but its many parse/print demonstrations provide no structural equality assertions.

Real assertions include range equality/Begin-only comparison, selected substring/index positions, common attribute decoding and convenient case-insensitive lookup. Some certify HTML-style no-value/illegal-name behavior or wrong default serializer output.

No inspected original assertion suite covers the accepted MACULA fixture, complete text occurrence fidelity, namespace URI/local-name identity, equivalent-prefix duplicates, malformed-document matrix, secure DTD policy, or source-vs-infoset round-trip.

The W3C Data file includes an external xmlspec.dtd reference not shipped in the snapshot. The native XmlDocument demo code does not establish an explicit safety profile. These tests were read, not executed through an improvised imitation of MSTest.

Original test execution remains **NOT VERIFIED / BLOCKED BY NETWORK-DEPENDENT RESTORE**. The temporary controlled experiments are a separate evidence set, not “33 original tests PASS.”

## 16. System.Xml.XmlReader comparison

**EXPERIMENTALLY VERIFIED:** the selected reader profile retains correct namespace identities, exact attribute names, present-empty values, direct text kinds, comment/CDATA/PI events, and ordered hierarchy for the tested source/cases. It rejects the tested malformed names/documents/entities and reports XmlException with line/position diagnostics.

XmlReader is a forward-only pull/event parser over a stream, not a retained DOM. Its bounded input buffering and current event values can be consumed without retaining a whole tree. It still allocates decoded strings: the measured event scan allocated 30.71 MiB.

It exposes line info, Depth, LocalName, NamespaceURI, Prefix, attribute enumeration and values. It does **not provide exact original byte/UTF-16 start/end ranges**. BaseStream.Position is buffered-read position, not the current XML occurrence boundary.

Original attribute lexical value, quote style, entity spelling, exact prefix spelling when reserialized and EOL bytes are archive/optional-mapper concerns. These limits are not reasons to replace a standard grammar with the inspected scanner.

**NOT VERIFIED:** universal XML specification/edition completeness, asynchronous behavior, all encodings and every future MACULA release.

## 17. XDocument / XmlDocument comparison

Both native whole-tree routes were tested through the configured reader, so DTD/security behavior is controlled rather than assumed from defaults.

| Dimension | XmlReader | XDocument | XmlDocument |
|---|---|---|---|
| Retained whole tree required | no | yes | yes |
| Expanded names | native event fields | XName | node namespace/local/prefix |
| Original prefix as distinct field | yes | not a separate XName field | yes |
| Direct ordered content | events | Nodes(), not only Value | ChildNodes, not only InnerText |
| CDATA/comment/PI | event types | dedicated nodes | dedicated nodes |
| Line info | native | SetLineInfo requested in experiment | not retained by the default object model |
| Byte/UTF-16 physical ranges | not native | not native | not native |
| Original bytes fidelity | separate archive | separate archive | separate archive |
| Unknown attrs | enumerate | enumerate | enumerate |
| Efficient local tree queries | external buffer/model | convenient | convenient |

**RECOMMENDATION:** XDocument is useful as a reference/oracle and perhaps for bounded subtree inspection. XmlDocument is a useful independent retained-tree comparison. Neither Value nor InnerText alone represents direct text occurrence order or mixed content.

The experiment's “lightweight” reader-built N model was not an optimized ingestion model and was not smaller than XDocument. Do not infer that custom records automatically reduce memory.

## 18. Actual MACULA fixture results

The raw source was read afresh in each experimental process and SHA-256 checked before parsing:

- source [SBLGNT/nodes/01-matthew.xml](../../../../../../Works/macula-greek/SBLGNT/nodes/01-matthew.xml)
- revision `8423afe47b9e8f24b7772e808af45c7159a6fe7e`
- **14,115,918 bytes**
- expected=actual `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4`

Actual records were derived by walking parsed XML. Fixtures were expected-value comparisons, not the source of the observed counts/text/membership.

| Implementation/profile | Matthew 1:1 specified checks | Matthew 1:2 specified checks | xml:id namespace identity |
|---|---|---|---|
| XmlPro, explicit XML profile/exact field access | PASS | PASS | unavailable; fidelity failure |
| XmlReader | PASS | PASS | correct XML URI |
| XDocument via reader | PASS | PASS | correct XML URI |
| XmlDocument via reader | PASS | PASS | correct XML URI |

### Primary

Sentence `MAT 1:1!1-1:1!8`; 1 sentence, 1 Tree, 26 Nodes, 25 Node→Node relations, eight noun token occurrences, 342 attributes, 200 leaf attributes, 25 per leaf, ClType=Verbless, no verb leaves.

All eight frozen ref/xml:id/morphId/text identities matched. Source direct text and Unicode=`Ἀβραάμ.`; NormalizedForm=`Ἀβραάμ`. Root attributes and missing Start/End/Id/Rule were checked. The frozen leaf absence list was checked using attribute occurrence presence, not null/default substitution.

### Boundary

Containing sentence `MAT 1:2!1-1:6!7`. Tree order token 6 `δὲ` Start=4 precedes token 5 `Ἰσαὰκ` Start=5; scripture order reverses them.

Subtree nodeId=`400010020050040`, Rule=`S-V-O`, source Start=`5`, End=`8`. Actual leaf descendants produce **[5,7,8,9]**; token 6 is excluded despite its position inside the canonical envelope.

### Complete-file diagnostic, not ingestion

| Metric | XmlPro | Each standard route |
|---|---:|---:|
| XML element occurrences | 59,891 | 59,891 |
| element attributes | 767,429 | 767,429 |
| Node occurrences | 56,488 | 56,488 |
| token elements | 18,329 | 18,329 |
| text nodes/events counted | 119,049 | 119,782 |
| parsed text UTF-16 characters | 1,469,888 | 1,369,168 |
| empty parsed token texts | **733** | **0** |

Text-character differences include XML line-ending normalization; the lost-token count was independently isolated by comparing leaves keyed by exact xml:id. All 733 mismatches are one code unit to empty. This is why counts alone cannot certify source fidelity. Full per-attribute/value equality across every Matthew node was **NOT VERIFIED**.

## 19. Synthetic correctness matrix

**EXPERIMENTALLY VERIFIED:** 49 main + seven supplemental = **56 cases**, each observed with XmlPro, XmlReader, XDocument and XmlDocument. Native accept/reject status agreed for these cases. Accepted native routes did not use uncontrolled DTD resolvers.

Legend: A=accepted; R=rejected. “Standard” below groups the three tested native profiles. A does not mean correct. Parsed structures, values, namespace fields, serialized XmlPro output and error details are in the JSON evidence.

| Case | XmlPro | Standard | Observed conclusion |
|---|---|---|---|
| ref and Ref | A | A | exact stored values survive; loose lookup assessed separately |
| only Ref | A | A | XmlPro ref lookup falsely returns b |
| Id/xml:id/nodeId/morphId | A | A | names retained; XmlPro namespace identity absent |
| absent attr | A | A | no occurrence |
| present-empty | A | A | actual empty string |
| namespace declarations | A | A | XmlPro only literal names |
| same local name/different URIs | A | A | native expanded identities distinct |
| prefixed element/attr | A | A | XmlPro cannot expose binding identity |
| default namespace | A | A | native descendants inherit URI |
| duplicate exact QName | R | R | XmlPro dictionary exception, native XmlException |
| duplicate expanded name/aliases | **A** | R | invalid XML accepted by XmlPro |
| mismatched nesting | R | R | explicit mismatch failure |
| extra closing tag | R | R | XmlPro stack-empty exception |
| missing closing tag | R | R | unpaired-tag failure |
| quoted > | **A, corrupt** | A | attribute disappears; tail becomes text |
| quoted / + single quotes | A | A | correct tested ordinary value |
| five XML entities | A | A | correct tested values |
| numeric/supplementary references | A | A | correct tested values |
| HTML-only nbsp | **A** | R | inappropriate HTML decode |
| unknown named entity | **A** | R | illegal XML becomes literal escaped text |
| invalid numeric zero | **A** | R | XmlPro NUL output |
| double-encoded amp/lt | A | A | one parse decode; explicit second decode unsafe |
| comment containing markup | A | A | XmlPro raw declarative retained, serializer body lost |
| CDATA containing > | A | A | XmlPro declarative, not proper CDATA content |
| generic PI | **R** | A | XmlPro IndexOutOfRangeException |
| xml-stylesheet PI | A, accidental model | A | matched by xml prefix; document serializer drops it |
| XML declaration | A | A | XmlPro document serializer drops declaration |
| simple DOCTYPE | A | R | native policy rejection |
| internal entity | A, unresolved | R | native policy rejection |
| external entity, inert URN | A, unresolved | R | no resolution enabled |
| external DTD, inert URN | A | R | native policy rejection |
| mixed content aa/b/bb/c/cc | A, parsed order correct | A | XmlPro serializer repeats aa |
| single-char text x | **A, lost** | A | parsed empty text |
| multiple roots | R | R | XmlPro document Single failure |
| trailing text | **A, lost** | R | no final text flush/document validation |
| non-BMP text | A | A | two UTF-16 units, not two scalars |
| source whitespace | A with explicit XML profile | A | default HTML profile remains lossy |
| Greek punctuation | A | A | target period preserved |
| self-closing | A | A | correct tested ordinary case |
| explicit empty pair | A | A | correct tested ordinary case |
| short comment | A | A | raw recognition; serializer placeholder |
| unterminated attr | **A, repaired** | R | becomes empty n |
| HTML no-value attr | **A** | R | outside XML grammar |
| unbound prefix | **A** | R | no namespace validation |
| illegal name n$ | **A** | R | no complete name validation |
| CRLF/CR and attr tab/newline | A, non-XML values | A, normalized XML values | archive must preserve lexical bytes separately |
| XInclude element | A, not expanded | A, not expanded | later explicit contract guard needed |
| depth 256 | A | A | measured acceptance, not arbitrary-depth certification |
| UTF-8 BOM + one-char alpha | A, text lost | A | BOM decoding is caller's; XmlPro text bug remains |
| ISO-8859-1 declaration/bytes | R in UTF-8 wrapper | A | XmlPro itself does not own XML encoding detection |
| invalid UTF-8 byte FF | R in strict wrapper | R | wrapper rejection is not a library parser feature |
| legal name punctuation n-a.b | A | A | tested ordinary name |
| supplementary name 𐐀 | R | R | runtime/name-repertoire caveat, not universal illegality |
| CDATA outside root | **A** | R | document grammar missing |
| malformed comment a--b | **A** | R | comment grammar missing |
| raw < inside attr | **A** | R | invalid XML accepted |

“Supported correctly” applies only to the particular successful cases. Namespace strings/stylesheet recognition are not standards-aware support; some are accidental support. Rejected valid PI is unsupported/fails rather than silent success. Quoted >, one-character/trailing text and malformed attributes are silent misparse/repair. Untested combinations remain **NOT VERIFIED**.

## 20. Performance and memory benchmark

**BENCHMARKED: five actual workloads. NOT BENCHMARKED: equivalent end-to-end authoritative ingestion, full NT, SQLite writing, production location mapping, original net5 runtime.**

### Method

- same fixed source bytes preloaded before timing; disk IO and SHA-256 calculation excluded;
- .NET 9.0.12 x64, net9 Release, original XmlPro library source unchanged;
- one full warmup per path, then five measured iterations per path;
- rotated path order each iteration;
- forced GC between measured paths; no concurrent benchmark workloads;
- Stopwatch around decode/parse/build; result observation/walking and serialization excluded;
- synchronous current-thread allocated bytes; no process-RSS or peak-memory claim;
- all workloads verify element/attribute/Node/token counts against the actual reader scan;
- retained heap is a separate one-sample approximate managed-heap delta with result kept alive;
- event scan reads attribute values but does not retain their occurrences/strings;
- XDocument requests PreserveWhitespace+SetLineInfo; XmlDocument preserves whitespace but has no retained line info;
- reader “light-tree” is the transparent experimental N/E model, not an optimized production store.

### Measured results

MiB = 1,048,576 bytes.

| Workload | Median ms | Min–max ms | Median allocated MiB | Approx. retained MiB |
|---|---:|---:|---:|---:|
| XmlPro decode + Conclude + XDocument | 1,070.09 | 965.17–1,085.83 | 293.77 | 192.68 |
| XmlReader event-only scan | 296.46 | 256.86–348.74 | 30.71 | ~0 (48-byte counts result) |
| XmlReader event-to-experimental retained tree | 811.34 | 755.07–996.02 | 151.98 | 109.75 |
| XDocument through configured reader | 639.72 | 571.46–652.93 | 106.17 | 106.10 |
| XmlDocument through configured reader | 753.42 | 624.16–772.62 | 116.60 | 108.80 |

**Critical comparability limit:** XmlPro does not execute an equivalent correct workload: it loses 733 token text occurrences and lacks native namespace/grammar work. Its row is **reference throughput only**, not a fair authoritative performance comparison. Equal element counts do not solve this.

Event-only scan and retained trees also have intentionally different output/lifetime work. The experimental custom tree stores line/name/namespace/kind metadata and empty lists differently from native trees. Therefore do not claim an inherent parser speed ranking, universal percentage advantage, or a complete importer throughput win.

### Separate scan/build diagnostic

A separate staged reader experiment captures all events, then links an N tree; one warmup and five measured runs:

| Phase | Median ms | Min–max ms |
|---|---:|---:|
| event parsing/capture | 710.04 | 593.77–787.08 |
| retained tree linking/build | 163.70 | 140.85–179.33 |

This double-retention staged diagnostic is **not** the direct streaming builder or event-only workload. Do not subtract its times from other rows or promote it as production architecture.

XmlPro and native DOM load calls fuse parsing/object building. Their individual scan versus build wall times are **NOT SEPARATELY MEASURED**; instrumenting internals would change the tested implementation. Total elapsed includes both.

Original tests have no fair MACULA benchmark; this report's measurements do not validate their “performance” Solution test.

## 21. Memory architecture analysis

**CODE EVIDENCE / BENCHMARKED:** XmlPro retains the decoded char array plus tags, attributes, source scopes, element dictionaries, text strings, parents and duplicated convenience lists/arrays. A full decoded string is transient before ToCharArray, affecting peak/allocation even if no longer retained.

Whole-array sharing prevents per-object array duplication, but is also a retention coupling. Lazy RawOuterText creates substrings on demand; Content/Name/Value are already decoded/materialized. Global indent caches and configuration have separate lifetimes. No profiler-based per-type allocation attribution was performed.

The event scan does not retain a graph and its returned counts object is 48 bytes. This does not mean zero parse allocations or zero peak working memory: preloaded input and parser buffering are excluded from the retained result delta.

The “lightweight” retained experiment is about 109.75 MiB, comparable to native retained trees. A different record model or bounded sentence/batch sink might change this, but is **NOT BENCHMARKED**. Whole-file retention remains linear in object occurrences by design; empirical full-NT scaling was not measured.

## 22. Hybrid architecture evaluation

| Option | Assessment |
|---|---|
| **A: XmlReader only** | Correct namespace/document events under explicit profile; good streaming capability and maintenance. Insufficient if “only” excludes original archive/source identity. No exact physical ranges. |
| **B: modified XmlPro as authoritative parser** | Rejected. Fixes require namespace binding, grammar/entity/encoding rules, document validity, text population and serializer separation, not limited modifications. Current benchmarks do not justify this maintenance burden. |
| **C: XmlReader + XmlPro-inspired mandatory Scope layer** | Can be correct if the location layer is independent and checked, not the present lexer. Adds mapping/alignment/encoding complexity and eager source retention. Benefit has not been benchmarked; avoid making it a Unit 2 dependency. |
| **D: XmlReader + original bytes + deterministic path + diagnostic line/column + optional separate lexical mapper** | **Recommended.** Correctness/provenance first; stable occurrence identity without mandatory byte mapper; optional locators can evolve independently and be recomputed from archived bytes. |

Full-NT scalability of every option is **NOT BENCHMARKED**. Option D offers a design route to bounded parsing/output, not a measured full-NT performance guarantee.

If a future UI requires immediate exact raw ranges for every attribute/text node, that is a separate measured requirement. It may justify an independently implemented lexical mapping layer, not reactivating XmlPro as authority.

## 23. Recommended authoritative parser boundary

**RECOMMENDATION:** standard XML reader owns well-formedness, namespace identity, entity/encoding semantics and event ordering under an explicit locked profile.

Source ingestion observes original source names, attributes and direct values; typed/query mirrors must not overwrite them. Unknown attributes are retained or explicitly diagnosed, never field-whitelisted away.

Keep raw archive fidelity separate from parsed XML infoset fidelity. XML-mandated line-ending/entity processing is not permission for Greek NFC normalization, punctuation removal, substituting NormalizedForm, or semantic interpretation.

Do not invoke XmlPro grammar, its attribute indexer, HTML decode/encode, convenience text helpers or printer in this boundary. No parser may infer membership from linguistic Start/End, or generate Actor/Action/Patient/Event/Result from source codes.

## 24. Recommended source-location boundary

| Locator/value | Decision | Rationale |
|---|---|---|
| Original fixed bytes + checksum/encoding evidence | **REQUIRED** | exact lexical/byte authority and reproducibility |
| Snapshot/file-scoped deterministic occurrence path | **REQUIRED** | stable rebuild reference independent of database PK |
| Locator scheme/version | **REQUIRED** | unambiguous ordinal/name/content segmentation contract |
| Source line/column | **OPTIONAL, RECOMMENDED diagnostics** | cheap native evidence; not unique or byte identity |
| UTF-16 bounds | **OPTIONAL** | only with a validated original-decoding map and explicit unit |
| Byte bounds | **OPTIONAL** | useful for exact raw excerpts; not required to recover archived source |
| Unicode scalar offsets | **NOT RECOMMENDED as core identity** | another display coordinate, not raw bytes/CLR indexing |
| Stream.Position as token offset | **NOT RECOMMENDED** | buffering defeats occurrence-boundary meaning |
| Position/range alone across revisions | **NOT RECOMMENDED** | insertions/encoding changes invalidate it |

A path scheme should distinguish namespace URI/local name and element occurrence ordinals, rather than rely on a prefix string. Preserve sibling/content order independently. Text/CDATA/comment/PI occurrence segmentation must be specified deterministically rather than assume arbitrary reader-event chunking remains invariant across parser builds.

At fixed bytes and a fixed scheme, source owner/hash + deterministic path can be stable across rebuilds. New bytes/revisions are new identities; matching upstream IDs does not silently relink them.

Byte mapping must account for encoding, BOM, UTF-8 multibyte sequences, UTF-16 surrogate boundaries, CRLF and lexical entity spellings. Mapping normalized parser Value back by string length alone is invalid. Invalid optional mapping must be explicitly marked unresolved, not guessed.

The Scope idea is worth reimplementing only behind this source-location boundary. Use a source owner/locator reference, not each object exposing a mutable char array. A physical mapper must be independently aligned against validated parser occurrences.

## 25. Unit 2 schema/design implications — inputs only

This investigation does **not** freeze a schema or authorize Unit 2 implementation.

Design inputs:

1. source bytes/checksum and scoped deterministic occurrence identity are core requirements;
2. line/column is diagnostic; physical range columns are optional, not a mandatory mapper prerequisite;
3. preserve namespace/local-name identity, prefix/QName evidence where available, and attribute presence;
4. preserve source wrappers and ordered direct content, not only concatenated token/InnerText;
5. separate source facts, deterministic mirrors and later interpretation;
6. keep Start/End, sibling order, traversal order, scripture order and exact ancestry membership distinct;
7. future tests must include actual single-code-unit Greek occurrences, alongside unchanged Unit 1 fixtures;
8. enforce explicit DTD/resolver/include/encoding/error policy;
9. native DOMs can serve as reference comparisons; custom record memory benefits require measurement;
10. optional mapper version/config/diagnostics must not alter source occurrence authority.

No modifications to accepted Unit 1 fixtures, governance, audit or historical Architecture Spike were made.

## 26. Changes needed if any XmlPro code were reused

**RECOMMENDATION:** production copying should first resolve snapshot provenance/license and target-runtime maintenance. Direct reuse is not the preferred route.

For a selected range/attribute abstraction, required redesign includes source owner identity, immutable source access, offset units, validated bounds, deterministic ordering, real intersection semantics, namespace-aware descriptors and source-vs-display separation.

For the current parser, required changes extend to quote-aware lexical state, complete legal-name/namespace/entity rules, encoding/document grammar, PI/CDATA/comments, duplicate expanded names, one-character/trailing text, resource policy and structured diagnostics. That is a parser rewrite/certification obligation, not a small reusable patch set.

Serializer and convenience APIs would need their own substantial correctness suite. There is no evidence that maintaining these rewrites has lower cost than standard XML correctness plus a narrow optional mapper.

## 27. Features prohibited from authoritative ingest

- AttributeBestMatch / OrdinalIgnoreCase fallback and global lookup switches.
- HttpUtility.HtmlDecode/HtmlEncode for source XML parsing/writing.
- Default HTML Conclude/ParseConfig and text trimming/whitespace dropping.
- tag delimiter search without XML quote/comment/CDATA/DOCTYPE grammar.
- QName-only dictionaries as attribute authority.
- null/no-value HTML attribute support masquerading as XML presence.
- one-character/trailing text omission or filling text from Unicode/NormalizedForm.
- declarative placeholder serialization, repeated first text, wrong attribute names.
- Root-only serialization as complete document reconstruction.
- convenience GetText/InnerText/search results as authoritative occurrence data.
- current Scope as byte offset, source identity, or cross-revision identity.
- implicit DTD/entities/XInclude/acquisition or success-shaped malformed-input repair.
- source Start/End arithmetic for ancestry/membership or BRW role generation.

## 28. Risks and unresolved questions

| Risk/unknown | Status and boundary |
|---|---|
| XmlPro source Git identity/license | unavailable in snapshot; no production reuse assumption |
| Original net5/MSTest behavior | blocked offline; net9 rehost is not original-runtime certification |
| XML name repertoire/version | supplementary-name rejection observed; exact specification support NOT VERIFIED |
| Combinatorial grammar cases | 56 finite examples, not full XML conformance suite |
| Full per-attribute/value source equality | NOT VERIFIED; namespace and text failures already disqualify XmlPro |
| Physical raw mapping | no production mapper and NOT BENCHMARKED |
| Stable text event segmentation | scheme must be defined and tested across builds |
| Native prefix alias round-trip | lexical prefix persistence NOT VERIFIED for LINQ; archive protects bytes |
| Resource thresholds | experimental 64 Mi characters/depth 256 not frozen limits |
| Whole-NT scalability / SQLite throughput | NOT BENCHMARKED |
| Heap/RSS fairness | approximate retained managed heap only; no profiler/RSS/peak conclusion |
| OS-level network tracing | NOT VERIFIED; feeds/resolvers disabled and inert URNs used |
| Initial harness wrapper/output problems | a PowerShell pipeline syntax error and deep JSON-output limit were corrected; neither was counted as successful evidence |

The evidence is already sufficient to reject the current XmlPro grammar/serializer as authority. Unresolved performance/locator details are not reasons to weaken source fidelity or delay the architectural boundary decision.

## 29. Required decisions Q1–Q10

**Q1 — Is XmlPro worth using for MACULA?**
**Yes as design inspiration/reference; no as the authoritative parser or assembly dependency.**

**Q2 — What is worth reusing?**
Closed-open scoped ranges, source ownership/occurrence concepts, raw excerpt retrieval and ordered-stack construction ideas. Reimplement narrow abstractions. Original examples and this rehost are benchmark/reference only. Do not reuse parser grammar or serializer.

**Q3 — Should XmlPro own authoritative XML parsing?**
**No.** Real 733-token text loss, namespace deficiency and malformed-input repair are sufficient blockers.

**Q4 — Should a standard parser own correctness?**
**Yes, with explicit safety and fidelity settings**, checked against fixed source/fixtures; not uncontrolled default overloads or a universal spec-certification claim.

**Q5 — Is Scope useful for source location?**
**Yes as an optional typed range technique**, not current byte/identity semantics.

**Q6 — Reimplement or reference existing assembly/source?**
**Reimplement independently.** No direct XmlPro dependency recommended.

**Q7 — What should be retained?**
Original bytes: REQUIRED. Deterministic source-scoped path/scheme: REQUIRED. Line/column: OPTIONAL, recommended diagnostics. UTF-16 and byte bounds: OPTIONAL after validated mapping. Bare line/column/ranges as identities: NOT RECOMMENDED.

**Q8 — Which hybrid should inform Unit 2 design?**
**Option D.** Correct standard parse, byte archive, deterministic occurrence identity, native diagnostics, optional independently validated mapper. This answer is not Unit 2 authorization.

**Q9 — What must be excluded?**
The functions/behaviors in §27, especially best-match lookup, HTML decoding, lossy defaults, current lexer, serializer and source-span/semantic shortcuts.

**Q10 — Which performance conclusions cannot be claimed?**
No fair authoritative-parser speed ranking involving defective XmlPro; no event-scan-vs-retained-tree importer victory; no inherent custom-record memory advantage; no original net5 performance, full-NT scaling, SQLite throughput, mapper costs, peak RSS or end-to-end ingest performance. The five exact temporary profiles were benchmarked; broader claims were not.

## 30. Final recommendation and safety closure

**Use XmlPro as source-location inspiration and reference/benchmark material, not as authoritative parser or serializer. Adopt Option D as design input for a separately authorized Unit 2.**

**Final safety verification:** the three actual Git repositories retain the full HEADs/branches in §2 with clean index/worktree/untracked state. XmlPro retains exactly the 42 original paths/lengths/SHA-256 values. No Git mutation, repository file creation/modification, Unit 2 status change, SQLite artifact or production parser/importer/exporter was performed.

The downstream project has 8,967 ignored dependency/build files, including node_modules/dist. Every inspected creation/modification timestamp predates this Spike. They were preserved, not cleaned. No initial hash baseline for those ignored files was captured, so byte-level before/after equality for them is not claimed. This task's commands did not write in the downstream directory. An overly strict temporary check requiring zero ignored files was corrected by distinguishing existing user artifacts from task-generated changes; ordinary Git cleanliness was unchanged throughout.

Report and evidence location:

`C:\Users\cruis\AppData\Local\Temp\XmlPro-Macula-Parser-Spike-20261101-074119`

The report is deliberately outside every Git/source repository. Retained C# is explicitly an experimental harness. Copied originals/library source, bin/obj and CLI scratch directories have been removed. Final hash/Git checks were performed after cleanup and report creation; no repository cleanup was performed.
