from dataclasses import dataclass, field
from enum import Enum

from product.errors import ProductError


class EpistemicClass(str, Enum):
    SOURCE = "source_fact"
    CANDIDATE = "derived_structural_candidate"
    EVALUATION = "human_evaluation"


class SourceStatus(str, Enum):
    READY = "READY"
    ERROR = "SOURCE_STORE_ERROR"


class ProjectionState(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CONFIGURED_ERROR = "CONFIGURED_ERROR"
    BINDING_FAILED = "BINDING_FAILED"
    VERIFIED_EMPTY = "VERIFIED_EMPTY"
    VERIFIED_POPULATED = "VERIFIED_POPULATED"


@dataclass(frozen=True, slots=True)
class ProductToken:
    ref: str
    chapter: int
    verse: int
    ordinal: int
    surface: str | None
    unicode: str | None
    normalized: str | None
    lemma: str | None
    cat: str | None
    language: str | None
    case: str | None
    gender: str | None
    number: str | None
    person: str | None
    tense: str | None
    voice: str | None
    mood: str | None
    degree: str | None
    type: str | None
    functional_tag: str | None
    formal_tag: str | None
    strong_number: str | None
    english: str | None
    mandarin: str | None
    gloss: str | None
    referent: str | None
    upstream_node_id: str | None
    xml_id: str | None
    morph_id: str | None
    epistemic_class: EpistemicClass = field(default=EpistemicClass.SOURCE, init=False)

    @property
    def key(self) -> str:
        return self.ref


@dataclass(frozen=True, slots=True)
class ProductSourceNode:
    source_node_id: str
    parent_source_node_id: str | None
    sibling_ordinal: int
    cat: str | None
    rule: str | None
    cl_type: str | None
    id_raw: str | None
    head_raw: str | None
    epistemic_class: EpistemicClass = field(default=EpistemicClass.SOURCE, init=False)

    @property
    def key(self) -> str:
        return self.source_node_id


@dataclass(frozen=True, slots=True)
class ProductVerse:
    book_code: str
    chapter: int
    verse: int
    tokens: tuple[ProductToken, ...]
    source_nodes: tuple[ProductSourceNode, ...]
    epistemic_class: EpistemicClass = field(default=EpistemicClass.SOURCE, init=False)

    @property
    def key(self) -> str:
        return f"{self.book_code} {self.chapter}:{self.verse}"


@dataclass(frozen=True, slots=True)
class ProductSnapshot:
    source_family: str
    edition: str
    repository_uri: str
    revision: str
    manifest_sha256: str
    relative_path: str
    source_sha256: str


@dataclass(frozen=True, slots=True)
class ProductAppositionPayload:
    anchor_source_node_id: str
    child_source_node_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductClauseComponent:
    source_node_id: str
    source_cat: str
    sibling_ordinal: int
    component_role: str
    member_token_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProductClausePayload:
    anchor_source_node_id: str
    source_rule: str
    source_head_raw: str
    components: tuple[ProductClauseComponent, ...]


@dataclass(frozen=True, slots=True)
class ProductCandidate:
    candidate_id: str
    candidate_kind: str
    derivation_kind: str
    derivation_version: str
    status: str
    source_snapshot: ProductSnapshot
    scope_source_node_id: str
    member_token_refs: tuple[str, ...]
    evidence: tuple[tuple[str, str, str], ...]
    payload: ProductAppositionPayload | ProductClausePayload
    is_evaluated: bool
    epistemic_class: EpistemicClass = field(default=EpistemicClass.CANDIDATE, init=False)

    @property
    def key(self) -> str:
        return self.candidate_id


@dataclass(frozen=True, slots=True)
class ProductEvaluation:
    evaluation_id: str
    candidate_id: str
    evaluator_class: str
    evaluator_label: str | None
    protocol_id: str
    protocol_version: str
    disposition: str
    rationale_evidence: tuple[tuple[str, str], ...]
    rationale_note_text: str
    rationale_note_language: str
    supersedes: str | None
    superseded_by: tuple[str, ...]
    not_superseded: bool
    epistemic_class: EpistemicClass = field(default=EpistemicClass.EVALUATION, init=False)

    @property
    def key(self) -> str:
        return self.evaluation_id


@dataclass(frozen=True, slots=True)
class ProductHistory:
    candidate_id: str
    evaluations: tuple[ProductEvaluation, ...]
    edges: tuple[tuple[str, str], ...]
    not_superseded_ids: tuple[str, ...]
    epistemic_class: EpistemicClass = field(default=EpistemicClass.EVALUATION, init=False)

    @property
    def key(self) -> str:
        return self.candidate_id


@dataclass(frozen=True, slots=True)
class ProductSelection:
    book: str
    chapter: int
    verse: int
    token_ordinal: int | None = None
    candidate_id: str | None = None
    evaluation_id: str | None = None

    @property
    def key(self) -> tuple[str, int, int, int | None, str | None, str | None]:
        return (self.book, self.chapter, self.verse, self.token_ordinal,
                self.candidate_id, self.evaluation_id)


@dataclass(frozen=True, slots=True)
class ProjectionBinding:
    state: ProjectionState
    error: ProductError | None = None
    source_fingerprint: tuple[int, int] | None = None
    projection_fingerprint: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class ProductStatus:
    source_status: SourceStatus
    projection_state: ProjectionState
    error: ProductError | None
    source_file_name: str
    projection_file_name: str | None


@dataclass(frozen=True, slots=True)
class ProjectionPanel:
    state: ProjectionState
    candidates: tuple[ProductCandidate, ...] = ()
    histories: tuple[ProductHistory, ...] = ()
    error: ProductError | None = None
    evidence_nodes: tuple[ProductSourceNode, ...] = ()
    candidate_error: ProductError | None = None


@dataclass(frozen=True, slots=True)
class ProductPage:
    status: ProductStatus
    selection: ProductSelection | None
    projection: ProjectionPanel
    verse: ProductVerse | None = None
    selected_token: ProductToken | None = None
    selected_candidate: ProductCandidate | None = None
    selected_history: ProductHistory | None = None
    error: ProductError | None = None
    notices: tuple[ProductError, ...] = ()
