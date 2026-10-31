# MACULA Greek → SQLite Linguistic Store — Architecture Spike

## 分析范围与证据等级

- 日期：2026-11-01，用户时区 UTC+10。
- 唯一被检查的仓库：本地 `C:\Works\macula-greek`，remote 为 Clear-Bible/macula-greek。
- 固定 revision：`8423afe47b9e8f24b7772e808af45c7159a6fe7e`。
- HEAD 提交时间：2026-07-07T11:47:28-04:00。
- 开始和报告生成前的 Git porcelain status 均为空。
- 本次只读检查没有运行生成 pipeline、安装依赖、创建 SQLite 数据库、创建 importer、修改仓库或 commit；没有检查其他仓库。
- 唯一交付物是本报告，保存在会话 artifact 目录，而非 MACULA 或 BRW 仓库。
- 八个 Pass 的 checkpoint 已在聊天中依次输出。

本报告是架构分析，不是已验证的 implementation specification，不包含 production importer、DDL、implementation prompt 或完整 BRW projection 设计。

证据等级：

1. **实测**：本地 XML/TSV 的定向读取、计数、全 nodes 语料只读扫描和原始文件 SHA-256。
2. **代码证据**：已阅读的转换、测试和配置代码；未执行这些会写文件的流程。
3. **文档声明**：README、许可和来源说明；与实测不一致处明确保留差异。
4. **建议/待确认**：候选 SQLite 架构、术语语义和未来实现验收，不冒充已运行的数据库结果。

## 1. Executive conclusion

**可以安全开展 MACULA → normalized SQLite 的本地技术实现，但必须以固定版本的 nodes 为主要 linguistic import source，而不是 TSV 或 lowfat。**

推荐的持久化边界：

> 版本固定的 MACULA nodes 原始字节
> → 不可变、保留全部 XML 属性和 occurrence 的语言学源库
> → 可重建的关系型 sentence/tree/node/token、双重顺序及精确 membership
> → 独立的下游 structural candidate / evaluated interpretation。

“authoritative”在这里表示：**对指定 edition、指定 MACULA revision 的发布数据负责、可回溯的输入层**。它不表示上游句法、词义、referent、frame 或 Notes 都是未经分析的人类语言客观真值，也不表示它们已经成为 BRW 的解释结论。

本次最重要的实测结论：

- Matthew 1:1 是 8 个 noun token、26 个 Node 的完整树，原 XML 明确标注 `ClType="Verbless"`。
- lowfat 同句只有 7 个 `wg` 和 8 个 `w`；原 sentence/CL/P 包装及其他单子节点包装不能还原。
- 当前 lowfat 同句没有 `predication="verbless"`。不能从当前查询中存在这个输出字段，推断发布物已完整保留它。
- TSV 的 27 列没有 sentence/tree/node topology、head、span、source nodeId 或大部分节点属性，不能 round-trip。
- **树叶遍历顺序不等于经文原文顺序。** SBLGNT 全语料存在 6,038 次相邻树叶的 morphId 经文顺序回退。
- Matthew 中 1,869 个子树的成员在经文顺序中不连续；一个 min/max 区间不能表示准确成员。
- `FunctionalTag` 和 `FormalTag` 不能合并：Matthew 中有 215 处值不同。
- `ref` 与 `Ref` 是不同字段：前者是经文地址，后者是 participant referent annotation。
- 原文 text、`Unicode` 和 `NormalizedForm` 必须分别保存。例如最后一词 text/Unicode 为 `Ἀβραάμ.`，NormalizedForm 为 `Ἀβραάμ`。
- 同一个上游 ID 在不同 edition 中不意味着同一词形。例如 Matthew 1:1!6 的 SBLGNT 为 `Δαυὶδ`，N1904 为 `Δαυεὶδ`。

**最小推荐实现单元**：先完整导入一个固定 revision 的 SBLGNT Matthew nodes 文件，并将 Matthew 1:1 作为不可变验收 fixture；同时用 Matthew 1:2 的顺序反例检验 membership。不是只导入这一节、不是全新句法分析，也不是 BRW projection。

本地技术实现暂无必须先重新设计 MACULA 的硬阻塞。实际 SQLite 往返、术语细节和许可分发范围仍需在相应阶段核准，不能把本 Spike 当作 production-ready 认证。

## 2. Repository evidence inspected

下列链接相对于本报告的实际会话目录，指向此次读取的本地仓库。行号是证据定位，不是本报告重新生成的数据。

### 2.1 主要证据目录/文件

| 证据 | 已检查对象 | 重点定位 / 用途 |
|---|---|---|
| E01 | [README.md](../../../../../../Works/macula-greek/README.md) | 1–25：数据来源与四种发布格式 |
| E02 | [LICENSE.md](../../../../../../Works/macula-greek/LICENSE.md) | 3–23、37–47：组合许可、来源例外、署名 |
| E03 | [SBLGNT/README.md](../../../../../../Works/macula-greek/SBLGNT/README.md) | 5–55：迁移、保留/补充字段、status、未完成 enrichment |
| E04 | [SBLGNT nodes Matthew](../../../../../../Works/macula-greek/SBLGNT/nodes/01-matthew.xml) | 1–51：完整 fixture；76–94：经文顺序反例；全文件属性检查 |
| E05 | [SBLGNT lowfat Matthew](../../../../../../Works/macula-greek/SBLGNT/lowfat/01-matthew.xml) | 1–165：同一 fixture 的实际派生树 |
| E06 | [SBLGNT TEI Matthew](../../../../../../Works/macula-greek/SBLGNT/tei/01-matthew.xml) | 1–17：verse、word ID 与独立 `pc` 标点 |
| E07 | [SBLGNT TSV](../../../../../../Works/macula-greek/SBLGNT/tsv/macula-greek-SBLGNT.tsv) | 1–9：27 列和 fixture 8 行 |
| E08 | [SBLGNT TSV README](../../../../../../Works/macula-greek/SBLGNT/tsv/README.md) | 1–14：BaseX 生成命令 |
| E09 | [N1904 nodes Matthew](../../../../../../Works/macula-greek/Nestle1904/nodes/01-matthew.xml) | 1–50：同句结构、不同词形与字段 |
| E10 | [mappings](../../../../../../Works/macula-greek/mappings/) | 全部 8 个现有 XQuery/XSLT 文件 |
| E11 | [lowfat XQuery](../../../../../../Works/macula-greek/mappings/lowfat-macula-greek.xquery) | 282–443、535–635、808–840、1610–1745、1780–2035：head、属性映射、消解与重组 |
| E12 | [lowfat→TSV query](../../../../../../Works/macula-greek/mappings/greek-lowfat-to-tsv.xq) | 全文件：列白名单、空值处理、按 xml:id 排序 |
| E13 | [nodes reference XSLT](../../../../../../Works/macula-greek/mappings/add-usfm-refs-to-nodes.xsl) | 227–320：ID 切片、地址生成、旧属性删除 |
| E14 | [lowfat pipeline](../../../../../../Works/macula-greek/pipelines/lowfat-transform/) | README、main.py、pyproject.toml |
| E15 | [TEI pipeline](../../../../../../Works/macula-greek/pipelines/tei-transform/) | README、main.py、fixtures/sblgnt-tei.xsl、pyproject.toml |
| E16 | [SBLGNT XInclude manifest](../../../../../../Works/macula-greek/SBLGNT/lowfat/sblgntlowfat.xml) | 27 个分卷 include；并非第二份完整数据 |
| E17 | [Clear annotations XML](../../../../../../Works/macula-greek/sources/Clear/annotations/annotations.xml) | 1–65：Frame、Ref、SubjRef；多 target、重复 role、sentinel 示例 |
| E18 | [Clear edition mapping TSV](../../../../../../Works/macula-greek/sources/Clear/mappings/mappings-GNT-stripped.tsv) | 1–12：N1904、NA27、NA28、SBLGNT、MARBLE IDs/text |
| E19 | [Clear edition mapping XML](../../../../../../Works/macula-greek/sources/Clear/mappings/mappings-GNT-stripped.xml) | 1–35：同类映射；注意表头命名差异 |
| E20 | [Clear wordsense](../../../../../../Works/macula-greek/sources/Clear/wordsense/) | README 与 TSV 头部；clustering 来源、occurrence ID、sense number |
| E21 | [Clear adjunct JSON](../../../../../../Works/macula-greek/sources/Clear/adjunct-types/adjunct_type.json) | 1–70；实测总数、field_type 词表 |
| E22 | [Clear synonyms](../../../../../../Works/macula-greek/sources/Clear/synonyms/) | README 与 Proximity.tsv 头部；Strong 前缀及跨语言距离 |
| E23 | [MARBLE documentation](../../../../../../Works/macula-greek/sources/MARBLE/SDBG/README.md) | domain/LN、源文件、Used with permission |
| E24 | [MARBLE→MACULA mapping](../../../../../../Works/macula-greek/sources/MARBLE/SDBG/MARBLE-macula-domains-ln.xml) | 1–18：domain/LN 与 morph IDs |
| E25 | [richer MARBLE domain/sense source](../../../../../../Works/macula-greek/sources/MARBLE/SDBG/sdbg-domains-glosses.xml) | 1–20：labels、多 sense 与 raw gloss；不等同 nodes 缩写字段 |
| E26 | [bundled Logos SBLGNT](../../../../../../Works/macula-greek/sources/LogosBible/SBLGNT/) | README、LICENSE、实际 Matt.xml 原文片段 |
| E27 | [raw Logos Matthew](../../../../../../Works/macula-greek/sources/LogosBible/SBLGNT/data/sblgnt/xml/Matt.xml) | 1–52：word/suffix/paragraph、无 syntax tree |
| E28 | [door43 source](../../../../../../Works/macula-greek/sources/door43/) | README 与 fetch-UTN-data.py；网络抓取、figures-of-speech 派生数据 |
| E29 | [test helpers](../../../../../../Works/macula-greek/test/__init__.py) | 4–64：27 分卷清单、edition-specific 测试数据范围 |
| E30 | [N1904 nodes tests](../../../../../../Works/macula-greek/test/test_nestle1904_nodes.py) | required attrs、token count、referent parsing |
| E31 | [SBLGNT lowfat tests](../../../../../../Works/macula-greek/test/test_sblgnt_lowfat.py) | attrs、count、error markers、class exemptions、标点 regression |
| E32 | [SBLGNT TEI tests](../../../../../../Works/macula-greek/test/test_sblgnt_tei.py) | 章节、地址、token count |
| E33 | [TSV tests](../../../../../../Works/macula-greek/test/test_tsv.py) | 实际目标为 N1904 TSV；不是 SBLGNT nodes fidelity 验证 |
| E34 | [cross-corpus tests](../../../../../../Works/macula-greek/test/test_consistency.py) | 全 corpus referent 检查；不能只在 sentence 内做 FK resolution |
| E35 | [wordsense tests](../../../../../../Works/macula-greek/test/sources/Clear/test_wordsense.py) | 来源字段与 ID 格式验证 |
| E36 | [CI workflow](../../../../../../Works/macula-greek/.github/workflows/pr.yml) | pytest pipeline，而非完整数据生成链 |
| E37 | [testing documentation](../../../../../../Works/macula-greek/UNIT-TEST.md) | 既有测试机制与使用说明 |
| E38 | [treebank PDF](../../../../../../Works/macula-greek/doc/MACULA%20Greek%20Treebank%20for%20the%20Nestle%201904%20Greek%20New%20Testament.pdf) | 仅定位与文件结构检查：599,695 bytes、33 page objects；未成功提取可解释正文 |
| E39 | [N1904 OC/O2 analysis query](../../../../../../Works/macula-greek/Nestle1904/nodes/oc-o2-by-verb.xquery) | 已有 governing-verb/OC/O2 汇总；不是 importer |

### 2.2 目录结构实测

| edition / directory | 目录内文件数 | 说明 |
|---|---:|---|
| SBLGNT nodes | 27 | 27 个分卷 XML；本次全量读取 |
| SBLGNT lowfat | 30 | 27 分卷 + 2 CSS + 1 XInclude manifest |
| SBLGNT TEI | 27 | 27 分卷 XML |
| SBLGNT TSV | 2 | 数据 TSV + README |
| N1904 nodes | 28 | 27 分卷 + OC/O2 分析查询 |
| N1904 lowfat | 40 | 27 分卷 + CSS、manifest、其他辅助 XML |
| N1904 TEI | 29 | 27 分卷 + manifest + CSS |
| N1904 TSV | 2 | 数据 TSV + README |

目录内 XML 并不全是可独立导入的 book。必须以显式 book manifest/允许列表识别发布源，不得同时展开 XInclude 又导入分卷，或把辅助 XML 当 scripture 数据。

未找到 `.xsd`、`.rng`、`.rnc`、`.sch`、`.dtd` 文件。没有据此宣称外部项目也不存在 schema。

### 2.3 调查限制

- PDF 的现有文本提取工具/库不可用；标准库的简单 PDF string extraction 没有获得可解释正文。已标记 **NO FURTHER YIELD**，不引用未经读取的 PDF 术语。
- 先前 PowerShell 全 corpus 扫描长时间无输出，已终止；随后标准库 XML 流式扫描成功完成。没有把未完成扫描算成验证成功。
- 一次小型 Greek 输出遇到 Windows stdout 编码错误；仅补跑未显示的短样本，未重复已成功的全 corpus 统计。
- 未运行 pytest，因为这里没有代码变更，且默认执行会产生缓存等文件。报告中的“实测通过”仅指明确说明的只读数据检查，不冒称 pytest suite 通过。

## 3. MACULA data architecture

### 3.1 Published formats 与上游来源关系

E01 说明 MACULA 将 Greek text、morphology、Clear syntax、gloss、word sense、frames 和 participant referents 组合到 trees。

更准确的来源图是：

- Clear 的 syntax / morphology tree 与其他 enrichment → **published nodes**。
- published nodes → E11/E14 → **lowfat**。
- lowfat → E12/BaseX → **TSV**。
- 对 SBLGNT：bundled Logos 原文 XML → E15 → **TEI**。

TEI 不是由当前 nodes pipeline 生成的另一个语法全集，而是另一条原文展示来源链。bundled Logos 原文更接近文本编辑层的上游，但缺失 Clear tree 和 enrichment，不能代替 linguistic primary source。

E03 说明 SBLGNT 版曾从 N1904 映射迁入词级信息：SBLGNT 已有字段保留；缺失字段才补充。punctuation 曾从 `Punc` 迁成词节点 text 的形式。当前 nodes fixture 没有 `Punc` 属性，不能让 importer 重新运行这种迁移或假定该属性仍存在。

尚未发现一个能从全部 bundled sources 重新生成当前 nodes 的完整、可执行、版本固定发布链。因此：

> 可重建的首要承诺是“从固定 nodes artifact 重建 SQLite，并从 SQLite 恢复该 artifact 的语言学结构”；不是“已经能重新计算全部 MACULA 上游标注”。

### 3.2 全 nodes 语料实测

只读取两套 edition 的 27 个分卷 nodes XML，未混入其他文件。

| 指标 | SBLGNT | Nestle1904 |
|---|---:|---:|
| book files | 27 | 27 |
| sentences | 8,010 | 8,011 |
| trees | 8,010 | 8,011 |
| Node occurrences | 420,049 | 420,364 |
| leaf/token occurrences | 137,741 | 137,779 |
| distinct token xml:id | 137,741 | 137,779 |
| distinct nodeId | 420,049 | 420,364 |
| multi-tree sentences in this snapshot | 0 | 0 |
| adjacent tree-leaf scripture-order decreases | 6,038 | 6,034 |

检查中未发现：

- 此 revision 内同 edition 的重复 nodeId 或 token xml:id；
- present Head 超出直接子 Node 的零基范围；
- present Length 不等于后代叶节点数；
- source Start/End 与后代叶 Start 的 envelope 不一致；
- source Start 坐标中不连续的 subtree；
- 必需 token identity/text/lemma 字段缺失；
- 按已观察 Ref/SubjRef/Frame list 语法提取后无法在对应 edition 全 corpus 找到的非 sentinel target。

**这些是当前 release 的实测，不是永远成立的 schema 公理。**

E11 末尾明确讨论过 multiple interpretations / multiple Tree 并只导出第一个。数据库仍应支持多个 Tree，不能因当前统计为零而消除此结构。

实测 Frame role codes：

- SBLGNT：`A0`、`A1`、`A2`、`AA2`。
- N1904：相同四种。
- 按此扫描口径，两 edition 都有 1,897 个 `n00000000000` sentinel reference occurrences。
- 当前扫描没有找到跨 book 的实际 target；但 source/test 设计允许全 corpus resolution。schema 不应强制 reference 与 owner 在同 sentence 或同 book。

### 3.3 实际 Node 属性 taxonomy

完整 SBLGNT Node 属性名共 39 个。下面不将“已存在的 annotation”伪装成纯 syntax。

| 字段 | source 中的角色 / 保存原则 |
|---|---|
| `nodeId` | tree node 的上游结构 ID；TEXT、完整保存；不以其编码替代 topology |
| `Id` | 原始局部结构标签，如 `2.13`；不是全 corpus PK；Matthew 有 277 种值在不同位置重复 |
| `xml:id` | XML namespace 的 token ID；不同于没有 namespace 的 `Id` |
| `morphId` | 上游 morphology/token identifier；不要去零或换成数据库整数 |
| `ref` | token scripture coordinate，例如 `MAT 1:1!3` |
| sentence `ref` | scripture range，如 `MAT 1:2!1-1:6!7`；sentence 不等于 verse |
| parent/child XML nesting | tree topology 的主要事实；必须保存 sibling order |
| `Start`, `End` | 源树叶坐标的 inclusive span；不能冒充 scripture-token span |
| `Length` | present 时与 subtree 叶数一致；SBLGNT internal Node 有，叶无；N1904 无此属性 |
| `Head` | 直接 child Node 的零基 index；不是 scripture index、nodeId 或 semantic Actor |
| `Cat` | 同时出现 POS、phrase category、clause function 与根包装类别；需结合结构上下文 |
| `Rule` | 结构规则，如 `NPofNP`、`Np-Appos`、`N2NP`、`S-V-O`；原字符串不能丢 |
| `ClType` | 此版出现 `Verbless`、`VerbElided`、`Minor`；缺失不是显式“ordinary” |
| `HasDet` | determiner/articular 相关结构 annotation；不能把 absent 写成 False |
| `Case`, `Gender`, `Number`, `Person` | grammatical morphology；保留 source spelling 与缺失 |
| `Tense`, `Voice`, `Mood`, `Degree` | morphology/inflection annotation；不能由词尾再次猜测替换 |
| `Type` | POS-dependent 子类；含 Common/Proper/Personal/Relative 等及空字符串，不是单一领域 enum |
| `FunctionalTag`, `FormalTag` | 两套原始 morph tags；README 称形态信息，精确编码关系仍待术语文档核准 |
| `Unicode` | 上游提供的 surface 属性，含 source punctuation/标记可能性 |
| leaf text | XML 叶文本；应与 Unicode 分别保存，不预设永远相等 |
| `NormalizedForm` | 上游 normalized form；不是 importer 对 surface 执行 normalization 的授权 |
| `UnicodeLemma` | source lemma assignment；可查询但不可覆盖 |
| `Language` | 此 SBLGNT corpus 为 `G`；不是现代 locale，不能写回 `el` 替换原值 |
| `StrongNumber` | 外部 lexical mapping；TEXT，保留 raw 格式，单独标识其 scheme |
| `LexDomain`, `LN` | MARBLE/Louw-Nida sense/domain enrichment；支持多值和有后缀代码，不能转成数值 |
| `English`, `Mandarin` | Cherith 相关 occurrence gloss/presentation 数据；producer attribution 根据文档记录其证据等级 |
| `Gloss` | Berean 来源 gloss；与 `English` 是两个字段，不应合并 |
| `Frame` | semantic-role/reference annotation；保留原 role code 和串，不生成 BRW actor/action model |
| `Ref` | participant referent list；不是 `ref` 经文坐标 |
| `SubjRef` | subject referent annotation；不是新生成的 actor |
| `Notes` | 上游分析备注，含 State/Event、方向、被动等判断；不是纯 morphology |
| `status` | edition migration/mapping provenance-like 数据，不是 linguistic confidence |
| `LowfatException` | 上游转换例外提示；保留，不作为 BRW解释规则 |

类别不是互斥的：例如 `Cat` 在不同高度的功能不同；`HasDet` 同时涉及结构和语法特征；`LexDomain/LN` 有词汇与语义成分。schema 应记录来源字段，不依赖唯一分类才能保存。

Matthew 实际 `Cat` 值：

`S, CL, P, np, noun, V, vp, O, O2, OC, IO, VC, ADV, advp, pp, prep, conj, pron, det, adj, adjp, num, nump, ptcl, intj` 等。

特别注意：

- 树根 `Cat="S"` 与 clause 内的主语功能 `Cat="S"` 不能被同一个不带 context 的 label 解释。
- `Cat="CL"` 也包括 complex-clause/包装结构，不能简单推断所有 CL 都是单一谓词事件。
- `LN="93.169a"` 不是浮点数。
- `LexDomain="010002 033003"` 不是单值 integer。
- source annotation 与后续 BRW interpretation 不在同一可信度/评估边界。

### 3.4 当前 enrichment 与 provenance-like 覆盖

SBLGNT 实测：

| 字段/状态 | occurrences |
|---|---:|
| English / Mandarin / UnicodeLemma / FunctionalTag / FormalTag | 各 137,741 |
| Gloss | 137,063 |
| LexDomain / LN | 各 128,616 |
| Frame | 25,362 |
| Ref | 14,542 |
| SubjRef | 16,625 |
| Notes | 2,716 |
| LowfatException | 5 |
| status=mapped | 137,063 |
| status=unmapped | 482 |
| status=refs-mapped | 196 |

缺失的 678 Gloss 和 9,125 domain/LN 必须作为 source 缺失保存。不能补空白冒充已有 annotation，更不能以另一个 edition 的词级字段盲补。

N1904 没有当前 SBLGNT 的 `English`、`Mandarin`、`Language`、`Length`、`Id`、`status`、`Notes` 属性。其部分 internal Node 也没有 Head。schema 不能把 SBLGNT 的 present 属性集合当作整个 MACULA 的非空约束。

## 4. Format fidelity comparison

### 4.1 Matthew 1:1 同一 fixture

| 维度 | nodes | lowfat | TSV | TEI |
|---|---|---|---|---|
| 8 token identities/address | 有 | 有 | 有 | 有 |
| Greek surface | text/Unicode，末词带点 | w text 与 after 拆开；unicode 另存 | text/after；无 unicode 列 | w 与独立 pc |
| lemma / morphology | 原字段、双 tags | 改名/小写；单 morph tag | 同低脂词级子集 | 无 |
| full source Node topology | 26 Node | 7 wg + 8 w，已简化 | 无 | 无 |
| source S/CL/P 包装 | 有 | fixture 中移除 | 无 | 无 |
| ClType=Verbless | 显式有 | fixture 中没有 predication | 无 | 无 |
| NPofNP / Np-Appos | 原结构/规则 | 核心 7 个 wg 中仍有 | 无 | 无 |
| source nodeId / Id / morphId | 有 | 不保留全套 | 无 | 仅共享 token xml:id，不含 tree IDs |
| Start / End / Length / Head | 有，依节点而不同 | 不保留原约定 | 无 | 无 |
| FunctionalTag + FormalTag | 两者 | 只映射 FunctionalTag→morph | 单 morph | 无 |
| source status / Notes / LowfatException | 有时存在 | 属性白名单不完整保留 | 无 | 无 |
| text/paragraph presentation | 源树叶文本 | 衍生 p/milestone/after | 单词行 | chapter/p/title/pc |
| 可重建原 nodes 树 | 是，直接保留 | 否 | 否 | 否 |

lowfat 保留部分 NP hierarchy，**不是完全扁平化**；但“还有树”不等于 full-fidelity 原树。

fixture loss accounting：

- nodes：26 Node = 18 nonleaf + 8 leaf。
- lowfat：7 wg + 8 w = 15 linguistic elements。
- 消失的 11 Node：S/CL/P 三层和八个 `N2NP` 包装。
- source `Head/Start/End/Length/Id/nodeId` 及 `ClType` 的原始归属不能从 lowfat 猜回。

### 4.2 TSV 为什么不可能 round-trip

E12 固定输出 27 列：

`xml:id, ref, role, class, type, english, mandarin, gloss, text, after, lemma, normalized, strong, morph, person, number, gender, case, tense, voice, mood, degree, domain, ln, frame, subjref, referent`。

查询选择 `//w` 并按 `xml:id` 排序，不保存：

- sentence membership/range；
- alternative Tree identity；
- nonterminal nodes 与 wrapper nodes；
- parent IDs、child ordinal；
- source Head；
- source Start/End/Length；
- rules 和 clause types；
- source nodeId、局部 Id；
- 原 text/Unicode 双表示；
- 双 morph tags；
- absent 与 present-empty 区别。

fixture 8 行的 role 都为空。lowfat 上层 `wg role="p"` 没有投射到每行成为完整祖先信息。即使每个 token 都有 role，role 也不能唯一指定多个嵌套 NP 的括号方式。

同样八行词级值可以对应多种 NP/同位树。因此 TSV→tree 的逆问题不是格式转换，而是重新选择/猜测一个分析，违反无损原则。

### 4.3 Import source 决策

| 方案 | 决策 |
|---|---|
| A. 直接从 nodes 导入 | **推荐作为第一阶段主链** |
| B. 从 lowfat 导入 | 不适合 full-fidelity authoritative store；可作为展示/回归参考 |
| C. 多来源直接合并为一个“更完整 token” | 不推荐默认执行；edition/来源/字段优先级与链接存在歧义 |
| D. 使用更上游来源替代 nodes | bundled Logos XML 无句法；未找到完整 nodes 重建链，不能替代 |

**A 不意味着丢弃其他 sources。** 未嵌入 nodes 的 companion annotations、mapping、richer MARBLE records 应独立登记/归档，后续经版本化 mapping 建立链接；不是自动覆盖 nodes。

若未来要求精确恢复 TEI 的 paragraph/title/独立标点结构，需将 TEI 作为独立 source document 导入/归档并链接。不能声称 nodes 自己包含 TEI 的全部版面信息。

## 5. Existing pipelines

### 5.1 可复用组件清单

| 组件证据 | consumes → outputs | 依赖 | 对 importer 的价值 / 复用边界 | 信息变化 |
|---|---|---|---|---|
| E14 main.py + E11 | nodes book XML → lowfat book XML，并重排格式 | Python ≥3.10、saxonche/SaxonC | 参考已发布规则、做独立派生出口；不作为主 ingest 内核 | wrapper dissolution、clause normalization、首 Tree、属性白名单、punctuation |
| E12 + E08 | lowfat `//w` → TSV | BaseX/XQuery | 可复用作下游词级导出和比对 | 完全不输出 nonterminal/tree topology；missing→empty |
| E15 main.py + XSL fixture | bundled Logos SBLGNT XML → TEI | Python ≥3.10、lxml/libxslt | 参考 book/address/word counter、文本版面来源；可独立复用到非源层出口 | 重组 chapters/paragraphs、生成 IDs、suffix/prefix→pc、删除部分空元素/空格 |
| E13 | 旧 nodes IDs/morphId/Sentence ID → USFM refs、排序 n 等 | XSLT 2.0 engine | ID/address 约定的理解参考；当前 nodes 已有 refs，不能默认再跑 | 删除 osisId/ID/usfmRef/word/verse 等旧属性 |
| E10 add-usfm-refs-to-tei.xsl | OSIS-like attrs → ref | XSLT 2.0 | 理解历史书名和地址映射 | 属性重命名，旧 literal 不再保留 |
| E10 add-xmlid-to-tei.xsl | ref/n → xml:id | XSLT 2.0 | 参考 2+3+3+3 坐标约定；应优先保留已有 ID | 生成/替换 ID，不证明跨 edition identity |
| E10 shorten-domain-attributes.xsl | richer Domain/SDBG attrs → domain/ln | XSLT 2.0 | 了解上游缩写来源 | 抽取 domain digits/SDBG 项；labels、gloss 等 richer information 可能丢失 |
| E10 precis-nodes.xquery | nodes → simplified wf/wg/w | XQuery engine | 调试参考、展示简化 | 属性白名单、只取 Tree[1]，不是 archival source |
| E10 precis.xquery | lowfat → simplified wf | XQuery engine | 简化显示参考 | 再次丢属性；入口不代表所有 sentence 结构 |
| E39 OC/O2 query | N1904 nodes → governing-verb 分组统计 | BaseX/XQuery | 显示现有分析 prior art，未来查询可参考 | 是派生统计，不是源事实，也不是完整 reconstruction |
| E18/E19 | edition/MARBLE ID/text mapping records | TSV/XML reader | 可复用既有 mapping 数据，不能重做 fuzzy matching 后覆盖 | 多 edition links；同 ID 不同 text；join 完整性需检查 |
| E17 | morphId→Frame/Ref/SubjRef XML | XML reader | 来源证据、annotation 原样存储/核对 | 未找到其全套生成/迁移脚本 |
| E20 | clustering senses→word ID/sense number TSV | 历史 MDB/CSV extract 链，当前 TSV 可直接读取 | 作为独立 lexical/semantic source | 不应推断已完整嵌入 nodes 或已属于 SBLGNT edition |
| E21 | PP/node_head/words/AdjunctType JSON | JSON reader | 独立 source annotation，有结构语义价值 | source scope 与到具体 syntax_node 的唯一映射需核准 |
| E22 | Strong code pair/distance TSV | TSV reader | 独立 lexical proximity source | 含 G/H/A 等跨语言数据；不是 token syntax |
| E23–E25 | MARBLE domain/sense/macula mappings | XML/JSON reader | 保留 richer source 与已发布 domain/LN provenance | nodes 不包含所有 richer labels/gloss/mapping IDs |
| E28 fetch script | 网络 UTN TSV → figures-of-speech 汇总 TSV | requests、pandas、door43 网络服务 | 仅理解 companion source；本阶段不执行、不网络抓取 | filtering、verse mapping、输出写文件；不是 MACULA core importer |
| E29–E37 | published data → pytest assertions/CI report | pytest、lxml、Poetry | 复用清单、基本 UTF-8/XML/address/count 思路 | 不证明 nodes→SQLite 保真或所有源字段语义 |

### 5.2 lowfat 不只是机械 schema conversion

E11 存在：

- atomic rule 解包与 role 传播；
- apposition 标记后处理；
- complex-clause subordination/coordination disambiguation；
- projecting-verb 的 lexical domain 检查；
- ellipsis 处理；
- wrapper/single-constituent CL dissolution；
- Minor clause→aux 等判别；
- nodeId 级例外；
- 首个 Tree selection；
- word 的括号删除及 trailing punctuation/symbol→after。

这些逻辑对理解 MACULA 很有价值，但已经超过“保持原 XML”的机械 ingest，不能悄悄纳入 authoritative importer。

当前 E11 有生成 `predication` 的代码，然而 P2CL 被消解时未必经过保留 CL attributes 的分支。fixture 的实际产物没有 verbless 属性。因此不能将这个差异直接归因于发布物过期：**可能是转换路径损失，也可能同时涉及生成版本差异；未执行 pipeline，原因未完全证实。**

代码引用的重组策略、TODO 和例外，不应变成 BRW importer 的隐性解释规则。

### 5.3 Validation prior art 与缺口

既有测试覆盖 UTF-8/XML、required attributes、地址、词数、referent targets、部分 lowfat 错误标记和标点 regression。

但 inspected test manifest 中：

- nodes 清单/直接 nodes tests 目标是 N1904；
- SBLGNT 有 lowfat/TEI tests；
- TSV 默认测试目标为 N1904；
- 不存在本次发现的 SQLite exporter、normalized tree round-trip 或双重顺序测试。

因此“现有 CI 可以通过”不等于“建议 schema 已经无损验证”，更不能替代新增 SQLite fidelity acceptance。

## 6. Full-fidelity boundary

需要同时定义两种保真承诺：

### 6.1 Linguistic/structural fidelity

从 normalized records 可恢复：

- 每个 sentence、所有 Tree 和其 XML occurrence；
- 所有 source Node、parent/child 与 sibling ordinal；
- 每个叶 token 的 ID、原文 text、Unicode、normalized、lemma 与全部原属性；
- source head index、source Start/End/Length；
- tree traversal order 与 scripture order，两者不同；
- 精确 node-token membership；
- 多值 lexical annotations 与 semantic/reference 原串；
- absent、present-empty、不同 namespace、属性名大小写；
- source wrapper elements 与其属性。

不能仅依赖“把 XML BLOB 放入数据库”：BLOB 可以备份，但无法替代 normalized record 恢复与 query 的验证。

### 6.2 Byte/document fidelity

XML parser 的 infoset 通常不能保留原始引号、实体写法、属性顺序、XML declaration 或所有字节级空白。故 source_file 应保存原始 bytes BLOB 和 SHA-256。

- **字节级恢复**：从 SQLite source_file 原始 BLOB 导出，SHA-256 必须与源一致。
- **语言学树恢复**：从关系表重建并比较 QName/attributes/text/ordered topology，不以 serializer 输出字节必须相同为标准。
- 通用 XML element/attribute/content 层可保存 wrappers、direct text、comments/PI 等 document 信息；原始 BLOB 仍是 exact-byte 保障。

不要用解析后的 `InnerText` 代替完整 source document；内部 Node 的 InnerText 可能混入缩进、后代文本和 tree traversal 顺序。

### 6.3 nodes 与整个 repository 的区别

“nodes full-fidelity”是对发布 nodes 的承诺，不是所有 companion sources 都已嵌入 nodes：

- 独立 word sense number；
- adjunct-type JSON；
- synonyms/proximity；
- richer MARBLE labels/senses/gloss；
- edition/MARBLE mappings；
- UTN figures-of-speech；
- TEI 版面结构。

不能因为主 importer 选择 nodes，就删除/忽略这些上游 artifact 的存在。建议另存原始 companion source、类型化 source records 和可审计 links；未经证实的 joins 保持 pending，不把内容补到 nodes。

## 7. Proposed normalized SQLite architecture

### 7.1 Rationale

推荐三部分共存：

1. **Immutable source archive**：source snapshots、原始文件字节、源许可、完整 XML attribute/content。
2. **Relational linguistic core**：book/sentence/tree/syntax_node/token，频繁查询字段采用 wide typed mirror。
3. **Rebuildable auxiliary relations**：精确 membership、lexical items、upstream annotation references、查询索引。

不是把全部语义藏进 JSON，也不是每个 morphology 字段拆成一张表。常见 scripture/token/morph 查询不应遍历 generic EAV；通用属性层保障完整性及未知字段，typed mirror 保障可用性。

**单一事实来源**：原始文件与 XML attribute/content 是 source authority；typed columns 和拆分引用是同一来源的确定性镜像，不是允许互相覆盖的两套 truth。它们的变化需要新 build/version 与一致性验证。

### 7.2 Candidate tables 与 PK/FK

表名与字段均为候选，不是冻结 DDL。

| 候选表 | PK / 主要 FK | 内容与必要性 |
|---|---|---|
| `dataset_snapshot` | snapshot PK | edition、repository URI、revision、manifest hash、capture/build identity；SBLGNT/N1904/不同 revision 分开 |
| `source_component` | component PK | Clear trees、SBLGNT text、Cherith、Berean、MARBLE 等 producer/source registry；仅声明有证据的 lineage |
| `source_license` / component-license link | license PK；component/license FK | 原文或原始许可 artifact/checksum、URI、attribution、documented permission、scope/status；允许多 license |
| `book` | book PK；snapshot FK | 原 book code、edition/book ordinal；与物理 file 分开 |
| `source_file` | file PK；snapshot FK；book/component FK 可空 | repository-relative path、format、bytes BLOB、SHA-256、size、encoding；companion artifact 不强行归一个 book |
| `xml_element` | element PK；file FK；parent element FK | QName、namespace/prefix、element-sibling ordinal、稳定 occurrence locator；包括 Sentences/Sentence/Trees/Tree/Node |
| `xml_attribute` | attribute PK；element FK | namespace/local-name/qualified-name、prefix、ordinal、parsed source value；名称使用 BINARY 比较，保留 empty 与 absent |
| `xml_content` | content PK；file FK；owner element FK 可空；child element FK 可空 | direct text/child element/comment/PI 的内容序号；document-level declaration/PI 的 exact 写法另由 BLOB 保证 |
| `sentence` | sentence PK，关联对应 element；file/book FK | source ordinal、ref_raw、可解析 range endpoint 镜像；不是按 verse 自动拆句 |
| `tree` | tree PK，关联对应 element；sentence FK | tree ordinal、source root links；保留所有 Tree，不选 Tree[1] |
| `syntax_node` | node PK，关联对应 element；tree FK；parent node FK 可空 | source nodeId/Id、Cat/Rule/ClType、sibling ordinal、present source Start/End/Head/Length 镜像 |
| `token` | token PK，可与 leaf node PK 同键；node/tree/book FK | 一个 leaf occurrence；xml:id、morphId、ref、坐标、tree-leaf ordinal、scripture order、source text/Unicode/NormalizedForm/lemma/language |
| token 内的 wide morphology/lexical columns | 随 token 主键 | source Case/Gender/Number/Person/Tense/Voice/Mood/Type/Degree、双 tags、Strong 等；无需第一阶段额外 1:1 morphology 表 |
| `node_token_membership` | (node PK, token PK)；两端 FK | 该 source subtree 的准确后代 token 集，包含叶自身；可由树重算，物化便于 span 查询 |
| `lexical_annotation` | item PK；source attribute/record FK；owner element/node FK | scheme、item ordinal、raw code，如多 LexDomain/LN；不将 source lemma occurrence 合成唯一全局词义 |
| `semantic_annotation` | annotation PK；source attribute/record FK；owner element FK | Frame/Ref/SubjRef/Notes/独立 AdjunctType 等的 scheme、原值、来源；非 BRW semantic interpretation |
| `annotation_reference` | reference occurrence PK；annotation FK；target token FK 可空 | role_code_raw、group/target ordinal、target ID raw、resolution status；支持重复 role、多个 target、sentinel、未加载目标 |
| `source_gloss` | gloss PK；source attribute/record FK；owner element/token FK | locale/language annotation、producer、raw text；Mandarin/English/Gloss 三个 source 字段分开 |
| `localization_label` | catalog version + locale + scheme/code/context | 自有固定中文语言学标签；不写回 source_gloss 或 Greek facts；与 source snapshots 的生命周期独立 |
| `source_record` | record PK；file FK | companion TSV/XML/JSON 的原 row/record ordinal、raw payload 和 locator；避免未整合 sources 被丢弃 |
| `external_mapping_member` | mapping-record + member ordinal；source_record FK；resolved token FK 可空 | edition/ID scheme/raw ID/raw text；多方 mapping 可扩展，不能要求简单一对一 |
| `import_build` | build PK；snapshot FK | parser/importer/exporter versions、config/manifest hash、validation results、诊断、counts；记录处理来源，不改写上游数据 |

license/source-component links 可是小型联接表；无需将所有词的每个属性都重复挂一份 license text。常见情况通过 component association 继承，例外可挂到 source artifact/annotation。只有 document 声明时才建立精确字段 producer association。

### 7.3 Identity

不将 `nodeId`、`xml:id` 或 `morphId` 单独当跨 edition/version 主键。

可靠的外部 source occurrence identity 至少包含：

> snapshot identity + source_file identity/checksum + element locator。

locator 可以是包含 ordinal 的确定性 XML path，例如：

`/Sentences[1]/Sentence[1]/Trees[1]/Tree[1]/Node[1]/...`

数据库 integer PK 是高效 FK，不应成为跨重建唯一持久协议。下游引用需携带稳定 source occurrence key；可额外保留 upstream IDs 便于人工定位。新 revision 中 ID 相同也不自动等于旧 snapshot 记录。

当前 corpus upstream IDs 唯一，可作为 release validation；未来 alternative Tree 可能重复 token identity，必须允许不同 XML occurrences 各自存储。可建立 scoped 检索索引，而非不可撤销的 global unique constraint。

### 7.4 Topology 与 edge

对于当前 ordered rooted tree：

- `parent_node_id + sibling_ordinal` 足够恢复树；
- 不必另存权威 `tree_edge`，以免两个拓扑来源分歧；
- Tree 的 root Node 由 parent NULL 和 tree FK 标识，root ordinal 仍需保存；
- 通用 XML parent/content 层与专门 node parent 是同一来源的镜像，必须一致。

如果以后遇到真正非-tree 的 source edge，才增加对应 source relation；不能提前把整个 XML 强行变成泛用 semantic graph。

### 7.5 两套 order 与 span：本次发现导致的关键修订

必须分开：

1. source child/sibling ordinal；
2. tree leaf traversal ordinal；
3. source Start/End 原值；
4. scripture address 的 book/chapter/verse/token；
5. canonical scripture order；
6. 精确 node-token membership。

E04 Matthew 中实测每个 leaf Start 等于 tree traversal ordinal，但这不是经文词序。

反例：

- `MAT 1:2!6 δὲ` 的 Start=4，先于 `MAT 1:2!5 Ἰσαὰκ` 的 Start=5 出现在树中。
- `nodeId=400010020050040`，Rule=S-V-O，source span=5..8，成员是 verse tokens 5、7、8、9。
- 经文顺序的 token 6 不属于该 CL subtree，虽位于 scripture envelope 中。

因此：

- source Start/End 按原值保留；
- scripture min/max 只允许称为 envelope；
- 精确 span 采用 membership 或由 membership 生成的若干不相交连续区间；
- 不得将缺口填成 source subtree 的新成员；
- 缓存的 canonical intervals/head-token 可重算，不能作为 source attribute 写回。

所有 membership 行由真实 ancestry 导出，不能由 Start/End 重新猜 topology。

### 7.6 Head

E11 与实际 `DetNP Head=1`、children=(det,np) 共同确认：Head 指向直接 child 的零基序号。

保存：

- source Head 字面值/存在性；
- sibling ordinal；
- 可选 resolved head-child FK/视图作为确定性镜像。

进一步沿 head-child 下行得到 lexical head 可以作为可重算 linguistic index，但并不产生 Actor/Action。missing Head、无头 coordination、非词级 head 的处理不能用默认 0 填平。

### 7.7 Morphology、lexical 与 semantic relations

- morphology wide columns 按 source values 存储，双 tags 独立；不要每个性/数/格拆表。
- lemma 先作为 occurrence 的 source assignment；全局 lemma lexicon/dedup 不是无损导入的必要条件。
- LexDomain/LN 保存 raw 全串，另按 scheme/item ordinal 拆分供查询。
- 不对 domain list 与 LN list 自动逐位配对或做 Cartesian product；对应关系需 richer source record 证明。
- Frame 保存原串，再解析 source role/target occurrences；`AA2` 不能删除或强转为 A2。
- 重复 A1 是允许观察到的 raw pattern，不能用 `role→one target` dictionary 覆盖。
- sentinel `n00000000000` 保留原 ID 和明确 unknown/sentinel status，target FK 为 NULL；不创建假 token。
- 一卷导入时 target 不在加载范围，不等于上游错误；用明确 not-loaded 状态保留并后续 resolve。
- Ref/SubjRef 的 list 分隔与 frame group 分隔按 source 语法解析，失败保留 raw 并报告；不静默删 target。

### 7.8 JSON 的合理位置

可使用 JSON 的部分：

- heterogeneous companion record 的 archival payload；
- build configuration 与结构化 diagnostics；
- 尚未稳定且当前不用于主要查询的 ancillary source payload。

理由：这些 payload 结构异质、需要完整保留未知键、并非高频 scripture/tree 查询路径。原始 file bytes 仍保存，因为 JSON reserialization 不保证字节一致。

不建议仅以 JSON 保存：

- token morphology 主查询字段；
- parent/child edges；
- scripture coordinates；
- 精确 node membership；
- 已知 annotation target references。

XML 全属性采用 namespace-aware relation 比 opaque JSON map 更可靠，尤其是 `ref/Ref` 与空值存在性。

### 7.9 重要索引

至少评估：

- source_file(snapshot_id, relative_path)，以及 checksum；
- book(snapshot_id, source_book_code)；
- sentence(file_id, ordinal)、source ref；
- tree(sentence_id, ordinal)；
- syntax_node(tree_id, parent_node_id, sibling_ordinal)；
- upstream nodeId / token xml:id / morphId，带 snapshot/edition scope；
- token(book_id, chapter, verse, verse_token_ordinal)；
- token(tree_id, tree_leaf_ordinal) 与 tree/canonical order；
- token(lemma)，按 Greek binary/codepoint 保留源形式；
- node_token_membership(node_id, token_id) 与反向(token_id,node_id)；
- lexical_annotation(scheme, code)；
- annotation_reference(target_token_id)，raw target ID+snapshot；
- source attribute(namespace_uri, local_name, element_id)，名称 BINARY；
- localization_label(catalog_version,locale,scheme,source_code,context)。

不应在没有实际工作负载时给所有 morphology 组合建立索引。核心 token query 不必每次 join 数十张 lookup 表。

### 7.10 Immutable boundary 与错误处理

- source snapshots append-only；修正源内容要新 snapshot，不 UPDATE 原事实。
- importer 不从 missing field 自动推断“正常/主动/False/已映射”。
- raw XML 在未知 attribute/schema 扩展时仍完整保留；typed parser 不理解的值须显式诊断，不能丢弃。
- UTF-8/XML 解析、必要身份冲突、source topology 不一致必须明确失败/隔离，不能 replacement decode 或返回空成功库。
- 暂未加载 reference 不伪装成功 resolve，也不破坏原标注。
- 发布 source store 可采用只读连接/文件边界；BRW 写独立 projection store，不授予 source table 更新权限。
- 当前 XML 不需要网络解析；默认禁用外部实体、网络 fetch 和隐式 XInclude。所有输入来自固定本地 manifest。

尚不能冻结：精确 ID uniqueness constraints、source producer per-field lineage、所有 Frame 语法、全局 enum、independent adjunct→syntax_node join、new-release drift 策略、source_content 存储的性能粒度。

## 8. Provenance / version / license model

### 8.1 必须记录的 provenance

- MACULA repository URL 与完整 commit SHA；
- edition 名称，不能只有“Greek NT”；
- artifact 的 relative path、format、exact bytes checksum/size；
- 明确 book file allowlist，不从任意目录通配推断；
- 每个 source occurrence 的 file/element locator；
- 所有 source upstream IDs；
- 必要时记录 source line/column；**定位辅助，不当唯一 identity**；
- component/source revision 与 attribution：仅记录可验证信息；
- importer/parser/schema/exporter version、configuration 与 manifest hash；
- source validation 与 normalized/export validation 的结果和差异；
- SQLite/build 的 logical content digest 或等价一致性摘要；不要仅比较 SQLite 文件字节，物理布局可能不同。

稳定的 source manifest 应包括路径及对应 SHA-256，以确定性规则计算 manifest hash。Git commit 单独不足以应对本地 dirty files、换行变化或下载损坏。

### 8.2 本次关键 artifact SHA-256

| 来源 | SHA-256 |
|---|---|
| E04 nodes Matthew | `FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4` |
| E05 lowfat Matthew | `A6E59E9C2B69E162C2654F80E71E827DF34D27825DA51EC6C5D31DBAC9A65888` |
| E06 TEI Matthew | `8B0473472EE9C4594DDFB7C48E373871B1153A801C0B4BD8DA588CC6FA9F4E9E` |
| E07 SBLGNT TSV | `A9F6EE958F8C3E73337C3DB897637C61559AB80A39016249B7C59F3BF594567A` |
| E02 MACULA license | `82C4509EF263295DB8B2441A3F9607BA3E2A71DA6D2E40E0E8B4F32324474F11` |
| E11 lowfat query | `BB9E65F9A31F13BA3A17053334AD007C5CFBC0B0A154DCE1579E0261CC0F340B` |
| E12 TSV query | `5537BD741D418B65929B53C959526520F702CE593D266E7BDCC51D47FA4BA16B` |
| E18 mapping TSV | `FB528ECEC75464381DA9B6EE739A7823FD45AD326EAFE0B38315D193C227C878` |
| E17 annotations XML | `2EC80517485BCEBC1BB7DAF77EEF387F706568316C302C9D9844D969CF973254` |

### 8.3 License conclusions 与边界

文档证据：

- MACULA aggregate：CC BY 4.0，E02 要求署名：
  “MACULA Greek Linguistic Datasets, available at https://github.com/Clear-Bible/macula-greek/”。
- SBLGNT：bundled README/LICENSE 为 CC BY 4.0；README 标明 text v1.2 / 2023-07-10，MACULA 文档指向上游 commit `736fdc76158950c3d04b949b7e013ca14305145a`。
- Clear datasets：E02 包括 syntax、morphology、wordsense、frames、referents、synonyms、mappings、adjunct types。
- Cherith：Andi Wu/Cherith Analytics，2023，CC BY 4.0；文档称 English/Chinese，实际 nodes 用 English/Mandarin，需保留这个 metadata discrepancy。
- Berean gloss：文档称 2023-04-30 起 public domain。
- MARBLE/LN/domain：**Used with permission**，不是独立确认的无限制 CC BY 再分发声明。
- N1904 transcription/morphology/markup 的具体来源许可需保留相应 upstream evidence，不仅写“1904 文本公有领域”。
- pipeline pyproject 声明 MIT，不能由此推断所有 repository data 同为 MIT。
- UTN、proximity、其他 companion sources 的自身 scope/rights 不应由 aggregate header 一笔抹平。

**许可风险是分发 gate，不是技术上无法做 normalized SQLite 的理由。** 本报告不提供法律认证。对外发布含 MARBLE/richer companion data 的 SQLite artifact 前，要确认其 permission 的继承、商业/再分发适用范围与 attribution；不确定时明确标注，而不是把许可一律写为 CC BY。

可以在 BRW store 之外提供 attribution/license manifest，仍须能从具体 source annotation 找到对应 component/许可证据。

## 9. Matthew 1:1 worked example

### 9.1 Source sentence

E04：

- root document：`Sentences`；
- sentence ref：`MAT 1:1!1-1:1!8`；
- `Trees` 下一个 `Tree`，两者无 source attributes；
- Tree 下 root Node：
  `Cat=S, Head=0, nodeId=400010010010083, Length=8`；
- CL：`Rule=P2CL, ClType=Verbless, Start=0, End=7, Head=0, Length=8`；
- CL 下 P，下 np；并非八词独立列表。

本次实际验证：所有 8 leaf `Cat=noun`，无 `Cat=verb`；source 还显式标注 Verbless。结论不是由已知 fixture 提示代替 XML 检查。

### 9.2 8 token records

T1–T8 是本报告的 ledger labels，不是新造 upstream IDs。

| token | ref 后缀 / Start=End | xml:id | morphId | leaf nodeId | source text = Unicode | lemma |
|---|---|---|---|---|---|---|
| T1 | `1:1!1` / 0 | n40001001001 | 40001001001 | 400010010010010 | Βίβλος | βίβλος |
| T2 | `1:1!2` / 1 | n40001001002 | 40001001002 | 400010010020010 | γενέσεως | γένεσις |
| T3 | `1:1!3` / 2 | n40001001003 | 40001001003 | 400010010030010 | Ἰησοῦ | Ἰησοῦς |
| T4 | `1:1!4` / 3 | n40001001004 | 40001001004 | 400010010040010 | χριστοῦ | Χριστός |
| T5 | `1:1!5` / 4 | n40001001005 | 40001001005 | 400010010050010 | υἱοῦ | υἱός |
| T6 | `1:1!6` / 5 | n40001001006 | 40001001006 | 400010010060010 | Δαυὶδ | Δαυίδ |
| T7 | `1:1!7` / 6 | n40001001007 | 40001001007 | 400010010070010 | υἱοῦ | υἱός |
| T8 | `1:1!8` / 7 | n40001001008 | 40001001008 | 400010010080010 | Ἀβραάμ. | Ἀβραάμ |

全部 ref 的 book prefix 都为 `MAT`。全部 Language=G、Number=Singular、status=mapped。

NormalizedForm：T1–T7 与对应表中 surface 相同；T8 为 `Ἀβραάμ`，没有句点。

| token | Case | Gender | Type | FunctionalTag / FormalTag | StrongNumber | LexDomain | LN |
|---|---|---|---|---|---|---|---|
| T1 | Nominative | Feminine | Common | N-NSF / N-NSF | 976 | 033005 | 33.38 |
| T2 | Genitive | Feminine | Common | N-GSF / N-GSF | 1078 | 010002 033003 | 10.24 33.19 |
| T3 | Genitive | Masculine | Proper | N-GSM / N-GSM | 2424 | 093001 | 93.169a |
| T4 | Genitive | Masculine | Proper | N-GSM / N-GSM | 5547 | 093001 | 93.387 |
| T5 | Genitive | Masculine | Common | N-GSM / N-GSM | 5207 | 010002 | 10.30 |
| T6 | Genitive | Masculine | Proper | N-PRI / N-PRI | 1138 | 093001 | 93.91 |
| T7 | Genitive | Masculine | Common | N-GSM / N-GSM | 5207 | 010002 | 10.30 |
| T8 | Genitive | Masculine | Proper | N-PRI / N-PRI | 11 | 093001 | 93.7 |

不能由 N-PRI 反向覆盖 source Case/Gender/Number；即便 tags 简略，这些具体 source attributes 仍有值。

| token | English | Mandarin | Gloss |
|---|---|---|---|
| T1 | book | 谱 | [The] book |
| T2 | genealogy | 族 | of [the] genealogy |
| T3 | Jesus | 耶稣 | of Jesus |
| T4 | Christ | 基督 | Christ |
| T5 | son | 子孙 | son |
| T6 | David | 大卫 | of David |
| T7 | son | 后裔 | son |
| T8 | Abraham | 亚伯拉罕 | of Abraham |

fixture 的 leaf 每个恰有 25 个 source attributes，共 200。没有 Frame、Ref、SubjRef、Person、Tense、Voice、Mood、Degree、HasDet、Notes 或 LowfatException。

不存在的 verb morphology/semantic reference 不生成 placeholder records；语义属性的缺失必须在 export 中仍然缺失。

### 9.3 完整 26-node ledger

N0–N25 是报告用 PK 代号。`children` 列从左到右表示必须保存的 sibling order。破折号表示 source attribute 缺失，不是 0。

| PK label | source nodeId | source Id | parent | children | Cat / Rule | source Start..End | Head | Length |
|---|---|---|---|---|---|---|---|---|
| N0 | 400010010010083 | — | Tree | N1 | S / — | — | 0 | 8 |
| N1 | 400010010010082 | 2.1 | N0 | N2 | CL / P2CL | 0..7 | 0 | 8 |
| N2 | 400010010010081 | 2.2 | N1 | N3 | P / Np2P | 0..7 | 0 | 8 |
| N3 | 400010010010080 | 2.3 | N2 | N4,N6 | np / NPofNP | 0..7 | 0 | 8 |
| N4 | 400010010010011 | 2.4 | N3 | N5 | np / N2NP | 0..0 | 0 | 1 |
| N5 | 400010010010010 | 2.5 | N4 | — | noun / — | 0..0 | — | — |
| N6 | 400010010020070 | 2.6 | N3 | N7,N9 | np / NPofNP | 1..7 | 0 | 7 |
| N7 | 400010010020011 | 2.7 | N6 | N8 | np / N2NP | 1..1 | 0 | 1 |
| N8 | 400010010020010 | 2.8 | N7 | — | noun / — | 1..1 | — | — |
| N9 | 400010010030060 | 2.9 | N6 | N10,N21 | np / Np-Appos | 2..7 | 0 | 6 |
| N10 | 400010010030040 | 2.10 | N9 | N11,N16 | np / Np-Appos | 2..5 | 0 | 4 |
| N11 | 400010010030020 | 2.11 | N10 | N12,N14 | np / Np-Appos | 2..3 | 0 | 2 |
| N12 | 400010010030011 | 2.12 | N11 | N13 | np / N2NP | 2..2 | 0 | 1 |
| N13 | 400010010030010 | 2.13 | N12 | — | noun / — | 2..2 | — | — |
| N14 | 400010010040011 | 2.14 | N11 | N15 | np / N2NP | 3..3 | 0 | 1 |
| N15 | 400010010040010 | 2.15 | N14 | — | noun / — | 3..3 | — | — |
| N16 | 400010010050020 | 2.16 | N10 | N17,N19 | np / NPofNP | 4..5 | 0 | 2 |
| N17 | 400010010050011 | 2.17 | N16 | N18 | np / N2NP | 4..4 | 0 | 1 |
| N18 | 400010010050010 | 2.18 | N17 | — | noun / — | 4..4 | — | — |
| N19 | 400010010060011 | 2.19 | N16 | N20 | np / N2NP | 5..5 | 0 | 1 |
| N20 | 400010010060010 | 2.20 | N19 | — | noun / — | 5..5 | — | — |
| N21 | 400010010070020 | 2.21 | N9 | N22,N24 | np / NPofNP | 6..7 | 0 | 2 |
| N22 | 400010010070011 | 2.22 | N21 | N23 | np / N2NP | 6..6 | 0 | 1 |
| N23 | 400010010070010 | 2.23 | N22 | — | noun / — | 6..6 | — | — |
| N24 | 400010010080011 | 2.24 | N21 | N25 | np / N2NP | 7..7 | 0 | 1 |
| N25 | 400010010080010 | 2.25 | N24 | — | noun / — | 7..7 | — | — |

额外 source attribute：N1 上 `ClType=Verbless`。不能搬到一个新造的“事件类型”字段后删除原位置。

### 9.4 Conceptual record insertion accounting

不执行 importer；这里只验证记录形状：

1. 一个 snapshot，以及 source_file 的完整 Matthew bytes/checksum、book record。
2. fixture 对应一个 sentence、一个 Trees wrapper、一个 Tree。
3. sentence subtree 有 29 个 element occurrences：Sentence + Trees + Tree + 26 Node；document root Sentences 另有 1 个。
4. 26 个 syntax_node，其中 18 个 nonleaf、8 个 token leaf。
5. 25 条 Node→Node parent relations；另有 Tree→N0 link。
6. 8 个 token record，分别链接 N5/N8/N13/N15/N18/N20/N23/N25。
7. fixture 原 attributes 共 **342**：
   - sentence ref 1；
   - root N0 属性 4；
   - 其余 17 nonleaf 的基本属性 136 + N1 ClType 1；
   - 8 leaf × 25 = 200。
8. 如果 source_gloss 全分开：24 条 gloss rows，来源分别为 English/Mandarin/Gloss，并各自链接原 attribute。
9. 如果 LexDomain 与 LN 分别拆 code items：9 个 domain item + 9 个 LN item；raw 双列表另保留，不能推断所有跨表 pairing。
10. fixture Frame/Ref/SubjRef reference rows 为 0；Verbless 是 source clause attribute，不需要伪造 frame。
11. materialized node-token-membership 包含叶自身时为 **71 行**，其中叶自身 8 行，nonleaf descendant memberships 63 行。

例如 N3、N0、N1、N2 的 membership 都是 T1–T8；N6 是 T2–T8；N9 是 T3–T8；N10 是 T3–T6；N16 是 T5,T6；N21 是 T7,T8。相同 token span 的多个 wrapper node 仍各自保留。

## 10. Round-trip validation

### 10.1 XML → proposed records → reconstructed XML tree

重建 thought experiment：

1. 由 snapshot/file/locator 找到 sentence；恢复 source ref。
2. 恢复 Trees/Tree wrappers，按 tree ordinal 选择展示，但不删除其他 tree。
3. 找到 N0 root；按 parent/sibling ordinal 递归恢复完整 26-node nesting。
4. 各 element 从 xml_attribute 恢复 namespace-aware 原属性和值。
5. 从 token/source content 恢复八个 leaf text；不以 lemma/normalized/gloss 替换。
6. 恢复 source Head/Start/End/Length 的 present/absent 状态。
7. 查询 source tree memberships 验证 descendant token set；经文展示独立按 ref/morphId 的已核准坐标排序。
8. 若需要 exact original document bytes，直接导出 source_file BLOB 并验证 SHA-256。

fixture 两种顺序刚好都是 T1…T8；不能因为 fixture 一致就移除双序字段。

### 10.2 Required properties

| 需求 | thought experiment 结果 / 证据 |
|---|---|
| 8 token 完整 | ledger 明确八个 leaf occurrence；不以 lemma 去重重复 υἱοῦ |
| token order | tree-leaf ordinal 和 scripture coordinate 都保留；fixture 0..7 / !1..!8 |
| Greek surface | 保留大小写、重音、末词句点；text/Unicode 与 NormalizedForm 分开 |
| lemma/morphology | 每个 token 的 source lemma、形态属性、双 tags 原样保留 |
| syntax hierarchy | 26-node ledger 与 25 parent edges 可唯一重建 source ordered tree |
| verbless | N1 ClType=Verbless 原位置重建，且无 verb leaf；不新增动词 |
| NP/genitive/apposition | 四 NPofNP、三 Np-Appos、八 N2NP 包装全部保留 |
| head | nonleaf Head=0 指向第一个 source child；leaf 的 Head 仍缺失 |
| source node IDs | 26 个 nodeId、25 个 Id、8 xml:id/morphId 均保留 |
| verse address | sentence range 和八个 ref 均保留；parsed columns 不替代 raw |
| annotation/gloss | source 原属性/归属/存在性可重建；不生成 fixture 不存在的 semantic frame |
| byte fidelity | 通过源 BLOB/checksum 可保证；不是 XML serializer 复刻引号/缩进 |

### 10.3 已修订的候选模型

| 发现 | 必须修订 |
|---|---|
| 根无 Start/End；叶无 Head/Length | raw presence 为权威，typed NULL 不写回“计算值” |
| source text 中带标点，normalized 不带 | 分存 text、Unicode、NormalizedForm；display split 是另一层 |
| tags 在 Matthew 215 处不同 | FunctionalTag/FormalTag 两列及原 attribute 均保留 |
| 当前有顺序回退和 scripture 非连续 subtree | 双重 order + exact membership；source span 不当 scripture interval |
| nodes 未嵌入全部 companion annotations | source_record/archive 与显式 links，不静默补入 token |
| 多 Tree 仍是 upstream 模型的一部分 | tree table + occurrence identity，即使当前无 multi-tree fixture |

### 10.4 真实实现之后的验收 gate

本次**没有真实 SQLite importer/exporter**，因此不能宣称已通过数据库 round-trip。第一实现单元至少应验证：

- fixture：1 sentence、1 tree、26 Node、25 Node edges、8 token、342 source attributes；
- 8 source surfaces、lemmas、双 tags、全部 source IDs/refs 精确相等；
- 8 leaf × 25 属性，缺失字段仍不存在；
- source ordered topology/attribute ownership 的比较无差异；
- 可物化时 membership=71，exact descendant sets 无差异；
- 原始 source_file BLOB 导出 SHA-256 与 E04 一致；
- Matthew 全文件：1,134 sentences、56,488 Node、18,329 tokens；
- Matthew 1:2 顺序反例与非连续 membership 成员完全正确；
- 同 snapshot 再建库的 logical source digest 一致，不能通过重复导入制造重复 occurrences；
- source immutability/FK/完整性检查通过；
- 任何未知值、未加载 target、sentinel 都明确保留/诊断，而不是隐藏失败。

## 11. Chinese localization boundary

### 11.1 已存在的中文

- SBLGNT source Node 的 `Mandarin`，lowfat/TSV 改名为 `mandarin`。
- 当前全 SBLGNT corpus 每个 token 都有 Mandarin 属性，但 present 可以是空字符串；存在属性不等于有有效 gloss。
- fixture 八个值见 §9.2。
- N1904 nodes/lowfat 在 inspected corpus 没有相同 Mandarin/English enrichment。
- 文档称 `Chinese`，实际 source 用 `Mandarin`；不要创建覆盖列来假装上游字段名一致。

它是 word-occurrence gloss，不是完整 Bible translation，也不是结构解释。T5/T7 同 lemma 不同 gloss 是直接证据。

### 11.2 三层模型

| 层 | 数据 | 变更边界 |
|---|---|---|
| 1. Original linguistic/source layer | Greek text、lemma、morphology、Cat/Rule/ClType、source annotations、独立保存的 upstream gloss | immutable snapshot |
| 2. Deterministic Chinese labels | source grammar code→固定中文标签，带 catalog version/context | localization 独立版本；不改 source |
| 3. Human-readable structural explanation | 对特定 source nodes 的可读说明，带 evidence references 与生成/评估来源 | 后续 explanation/projection 层，不属于 importer |

上游 Mandarin 是第 1 层中保留的来源数据，但在展示上使用；它不替代第 2 层的术语字典。

### 11.3 固定标签建议

| source code | 候选中文 |
|---|---|
| Nominative | 主格 |
| Genitive | 属格 |
| Accusative | 宾格 |
| Dative | 与格 |
| Vocative | 呼格 |
| Singular / Plural | 单数 / 复数 |
| Feminine / Masculine / Neuter | 阴性 / 阳性 / 中性 |
| CL + Verbless | 无动词子句，保留原 code |
| VerbElided | 动词省略子句，保留原 code |
| np | 名词短语 |
| Np-Appos | 同位结构，保留规则名 |
| S，作为 clause 内功能 | 主语成分；不是“Actor” |
| S，作为 sentence root | 句子根包装；不能标签为“主体” |
| O | 宾语成分；不是“承受者”判定 |
| V | 谓语动词成分，精确定义仍需术语核准；不是“动作/事件”断言 |
| P | 述谓/表语成分候选标签；不能自动固定为身份或属性 |
| IO / OC / O2 / VC / ADV | 保留 source code 与上下文；专门术语确认后再给稳定中文 |

“S→主体、V→动作/事件、O→对象/承受者、P→身份/属性”可以成为未来某个解释性的 presentation vocabulary，但不是对 MACULA source codes 的无条件语言学翻译。

Unknown/unlocalized code：显示 source code 与明确“尚未本地化”，不能静默猜成最接近概念。

### 11.4 人类可读解释示例的边界

允许未来依据 fixture 生成纯结构说明，例如：

> 上游将此句标记为无动词子句；述谓成分下有嵌套名词短语，其中保留属格形式和同位规则。

该文字是 derived explanation，应引用 N1/N2/N3 等 source occurrences，不回写到 source。

禁止：

- Mandarin 替换 Greek token；
- 中文译文替换树；
- 拼接八个 Mandarin 自动称为 Matthew 1:1 中文译文；
- 以中文标签的便利性创造 Actor/Action/Patient/Event；
- importer 生成 theological interpretation。

## 12. Future BRW projection boundary

仅规定接口边界，不设计完整 projection system。

### 12.1 三种不同对象

1. **Linguistic source fact**
   - 例如某具体 Node 的 `Cat=O`、某 token 的 `Voice=Passive`、某上游 Frame raw string。
   - “source 有该标注”可验证；其分析是否合理是另一问题。

2. **Derived structural candidate**
   - 在后续独立层提出的关系/结构候选，引用具体 source node/token/annotation。
   - 需要 derivation version、证据和范围；不改变源记录。

3. **Evaluated structural interpretation**
   - 对 candidate 的进一步评估或人类确认。
   - 与 raw source annotation 不能混淆，也不能反向成为 importer default。

authoritative linguistic store 的职责止于第 1 类及确定性查询镜像。

### 12.2 为什么不能 S=Actor / V=Action / O=Patient

- S 是句法位置或根包装代码，不承诺 semantic agent。
- Passive 中语法主语可能对应被影响方，agent 可能在 PP 中或缺失。
- V 可能表达状态、关系、被动、名词性分词等，不等于行动或 BRW事件。
- O 可能是内容、言语、补足语、非典型对象；不必然是 Patient。
- 上游 `A0/A1/A2/AA2` 也不能未经词义/构式/context 评估改成 BRW actor roles。
- fixture 只有 CL/P/NP 与 noun，不能因为系统偏爱 SVO 而补建 S/V/O。

### 12.3 后续必须单独处理的场景

| 场景 | 当前证据 / 不能在 importer 完成的判断 |
|---|---|
| verbless clauses | fixture N1；不能补造 copula/Action/Event |
| passive voice | Matthew 1:16!11：source Frame 只有 A1 target；不能要求存在 Actor |
| indirect object | source Cat=IO 与 np/PP 等；不能按 O 默认转 Patient |
| predicate / identity | P、OC、O2 不等价；具体关系需后续判别 |
| speech | 上游 conversion 有 projecting-domain 判断；不能用词汇白名单直接在源库完成解释 |
| complement | VC、clausal complement、nominalized clause 等；需保留上下文/层级 |
| prepositional phrase | PP 可有不同语法/语义功能；不能全部当 modifier 丢弃 |
| ADV as semantic argument | source ADV/pp 与独立 AdjunctType 说明 category 不等于 semantic optionality |
| state-change constructions | Notes 出现 State/Event 等上游判断；不自动转成 BRW Event/Result |
| implicit / ellipsis | VerbElided 与 sentinel/subject ref；不能创造未写出的 source token |
| multi-clause constructions | sentence 可跨多个 verse；CL 可是 clause complex；不能按每 CL 一个事件扁平化 |

E21 的 field_type 实测包括：

`Accompaniment, Beneficiary, Comparison, Concession, Condition, Extent, Goal, Instrument, Manner, Modal, Negation, Place, Projection, Relation, Result, Source, Time`。

其中字面值 `Result` 可以作为**上游 annotation 原值**归档；它不授权 importer 创建 BRW Result entity。同理，source Notes 中的 Event 字样原样保留，不生成一个 evaluated Event object。

这正是“不可丢 upstream enrichment”和“不可在 importer 产生解释对象”必须同时满足的原因。

### 12.4 与后续 Scripture X-Ray 的最小边界

- 下游读固定 source snapshot；
- 引用可定位的 source node/token occurrence；
- 自己保存 candidate/evaluation/localized explanation；
- 不在 source tables 中新增解释角色；
- 新版 MACULA 不自动替换既有解释的来源；
- 未来跨版本重新链接另行处理，不隐式“升级”旧 evidence。

没有在本报告设计任何高层解释机制。

## 13. Known unknowns

| 未决项 | 状态 / 对阶段的影响 |
|---|---|
| PDF 术语和完整 rule/tag 定义 | 未成功读取正文；影响精细 UI labels/解释，不阻塞 raw-preserving ingest |
| FunctionalTag/FormalTag 精确语义 | 实测不同、文档称 morphology；必须双存，不冻结解码转换 |
| nodeId 后段编码完整约定 | 不需要解码才能保存；不能将 ID 切片用于重建树 |
| 全 nodes/enrichment 生成链 | 未找到完整 orchestration；阻塞“重新计算上游发布物”的承诺，不阻塞固定 artifact→SQLite |
| 当前 query 与 published lowfat 的生成版本一致性 | fixture 路径明确有损，具体版本差异未执行验证 |
| 全 Frame grammar、AA2 定义 | 已观察代码与有效 targets；先保留 raw/code，再确认 semantic definition |
| companion source edition scope | wordsense/adjunct/source annotation IDs 不能因同名直接认定已属于 SBLGNT |
| rich MARBLE 对应关系 | nodes lists 和 rich source records 非完全等价；拆 items 不自动构建 pairing |
| mapping cardinality/空值/特殊 record | fixture 对应关系已查；全 mapping relational join 尚未逐条认证 |
| source per-field producer lineage | 文档提供 component 级说明，不能伪造精确每词生成 history |
| license/permission 再分发边界 | MARBLE 与 companion materials 对外分发前需要确认 |
| 多 Tree future release 行为 | 当前为零，但 source model/pipeline 明确容纳；schema 要保留 |
| normalized core 性能与 SQLite target 版本 | 未基准测试/执行 SQLite；先验证 fidelity，按真实 workload 调索引 |
| 真实 round-trip | 只有有实测支撑的 thought experiment；必须在实现阶段运行 exporter 验收 |

这些 unknowns 不应成为主动删除字段或提前简化数据模型的理由。

## 14. Risks

| 风险 | 后果 | 推荐控制 |
|---|---|---|
| TSV-first | 不可逆 tree loss | nodes-first |
| lowfat-first | wrapper/Head/ClType/IDs/notes loss，加上已重组分析 | 将 lowfat 定位为派生出口/参考 |
| Start 当 scripture order/span | 非连续子树被加入错误 token；原文重排 | 双 order + exact membership |
| ID 跨 edition/version 合并 | 覆盖不同词形/标注 | snapshot-scoped occurrence identity |
| tags 合一 | 丢失 FormalTag/FunctionalTag 差异 | 双 raw tags + source attrs |
| missing 当 empty/default | 无法重建原属性状态，假造正常值 | raw presence + typed nullable mirror |
| XML attr case-insensitive map | ref 与 Ref 混淆 | namespace-aware BINARY 属性键 |
| Greek normalization/标点删除 | 无法还原 surface/source text | raw bytes + 分存 source strings |
| rule/source Notes 直接解释化 | 导入器变成 BRW interpretation engine | immutable annotation 与 projection store 分层 |
| rich sources 自动补并 | edition/许可/优先级错误 | companion archive + explicitly versioned links |
| XInclude 双导入 | 重复 book/token | manifest allowlist、禁隐式展开 |
| 成功检查词数即宣称保真 | 相同 count 掩盖结构/字段损失 | per-node topology/attributes/text/reference 比较 |
| 只存 XML BLOB | 不具备 normalized query/reconstruction 能力 | relational core + independent normalized round-trip |
| 只存选定 relational fields | 未知/稀疏 upstream attrs 丢失 | 完整 XML attribute/content/source archive |
| 全局 unique ID 约束过早冻结 | future alternative trees 无法导入 | occurrence PK、release-specific validation |
| license 一律标 CC BY | 分发违规风险 | component/license evidence 与 distribution gate |
| mutable source 表 | 下游解释污染原证据 | read-only source store / append-only versions |

## 15. Minimal recommended implementation unit

**一卷、一个固定 snapshot、一个纯 source importer/exporter 验证闭环。**

建议范围：

1. 输入只允许 E04 固定 checksum 的 SBLGNT Matthew nodes XML。
2. 持久化 dataset/book/file provenance、原始 bytes、完整 XML elements/attributes/content。
3. 映射 sentence/tree/node/token、source parent/sibling/Head/span、双 order 和精确 membership。
4. 保留 source lexical/semantic/gloss 全字段；reference 只做透明 parsing/resolution，不做角色推断。
5. source archive 与 normalized exporter 两条保真验证。
6. fixture 使用 Matthew 1:1；边界反例使用 Matthew 1:2 tree/canonical order、tags 差异、sentinel、passive 与缺失 enrichment。
7. Matthew 全文件计数及 reconstructed per-node equality。
8. 记录构建版本/诊断；相同 source snapshot 可确定性重建。

一卷比单 verse 更合适，因为：

- sentence 可跨 verse；
- 顺序/非连续结构在 fixture 之外立刻出现；
- referents 可能跨 sentence；
- source 的缺失/tag 差异不在全部八 noun fixture 中充分体现。

本单元不要求：

- 重建 Clear/MARBLE 的上游标注生成算法；
- 导入全部新约或 N1904；
- 自动整合所有 companion sources；
- 完成中文词典或人类解释；
- 提供 Scripture X-Ray 完整 UI/semantic projection。

扩展到两 edition/全 corpus 之前，先完成最小单元真实 SQLite 往返验收，再做 mapping、许可与性能 gate。

## 16. Explicitly deferred work

- production importer 实现及其 implementation prompt；
- 正式 DDL、migration 与 BRW 数据库接入；
- Actor / Action / Patient / Event / Result 等 BRW解释实体的产生；
- theological interpretation；
- 完整 structural projection/evaluation system；
- 中文 Bible translation、gloss 拼接或所有人类可读解释；
- 完整 localization dictionary；
- N1904→SBLGNT 重映射、跨版本解释迁移；
- richer MARBLE/wordsense/adjunct/proximity 的自动 semantic merge；
- 重新计算 upstream syntax/morphology/frames/referents；
- pipeline bug 修复、发布物重新生成；
- 网络获取最新 UTN、外部 enrichment、其他仓库调查；
- 全 corpus production performance benchmarking 与最终许可法律认证。

## 最终决策摘要

| 问题 | 结论 |
|---|---|
| MACULA→SQLite 技术上是否可安全实施？ | **是，作为固定版本、原样保留的 source import；不是已完成的 production 认证。** |
| 推荐 import source | **SBLGNT nodes 分卷 XML**；不用 TSV/lowfat 替代 |
| 其他来源如何处理？ | 独立 archive/source records/versioned links；不默认覆盖 primary nodes |
| 最小 implementation unit | **完整 SBLGNT Matthew** + Matthew 1:1 fixture + 1:2 顺序反例 + normalized exporter |
| 核心 schema 不可省略什么？ | 全 source attrs/IDs、sentence/tree、parent/sibling、双 order、exact membership、raw bytes/provenance |
| 本地技术硬 blocker | 当前无；实际 SQLite round-trip 尚未实施，作为实现验收 gate |
| 分发 blocker | MARBLE/companion permission 范围必须在对外发布前核准 |
| 非阻塞不确定性 | PDF/术语、tags 精确定义、full generation chain、mapping scope、future alternatives；先完整保存，不强解码 |
| 本次实际交付 | 唯一分析报告；仓库无修改、无 importer、无 SQLite 文件、无 commit |

**架构核心不是把 schema 设计得漂亮，而是确保以后任何结构解释都能指向未被覆盖、未被重排、未被扁平化或补造的 MACULA source occurrence。**
