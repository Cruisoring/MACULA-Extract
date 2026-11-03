from dataclasses import replace
from pathlib import Path
import sys
from typing import Literal, Protocol

from scripts.source_query import get_verse, get_ancestors_by_token, get_node, QueryError
from scripts.projection_query import (
    ScriptureSelector, get_structural_interpretation_histories_for_selector, ProjectionQueryError,
)
from scripts.projection_store import verify_projection_store

from product.config import ProductConfig
from product.errors import ErrorCategory, ProductError
from product.models import (
    ProductAppositionPayload, ProductCandidate, ProductClauseComponent, ProductClausePayload,
    ProductEvaluation, ProductHistory, ProductPage, ProductSelection, ProductSnapshot,
    ProductSourceNode, ProductStatus, ProductToken, ProductVerse, ProjectionBinding,
    ProjectionPanel, ProjectionState, SourceStatus,
)
from product.validation import validate_selection
from product.wording import NOT_CONFIGURED, STALE_BINDING


class _SourceNode(Protocol):
    @property
    def source_node_id(self) -> str: ...
    @property
    def parent_source_node_id(self) -> str | None: ...
    @property
    def sibling_ordinal(self) -> int: ...
    @property
    def cat(self) -> str | None: ...
    @property
    def rule(self) -> str | None: ...
    @property
    def cl_type(self) -> str | None: ...
    @property
    def id_raw(self) -> str | None: ...
    @property
    def head_raw(self) -> str | None: ...


def _node(node: _SourceNode) -> ProductSourceNode:
    return ProductSourceNode(node.source_node_id, node.parent_source_node_id,
                             node.sibling_ordinal, node.cat, node.rule, node.cl_type,
                             node.id_raw, node.head_raw)


def _fingerprint(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def _failure(
    error: Exception, category: ErrorCategory, scope: Literal["source", "projection"], message: str,
    expected: tuple[type[Exception], ...] = (QueryError,),
) -> ProductError:
    print(type(error).__name__, file=sys.stderr)
    if not isinstance(error, expected):
        category = ErrorCategory.INTEGRITY_ERROR
        message = "Store evidence could not be safely displayed."
    if scope == "source":
        return ProductError(category, "source", message)
    return ProductError(category, "projection", message)


def _contradiction(scope: str) -> ProductError:
    print("IntegrityContradiction", file=sys.stderr)
    return ProductError(ErrorCategory.INTEGRITY_ERROR,
                        "source" if scope == "source" else "projection",
                        "Store evidence contradicts the configured source.")


class ExplorerAdapter:
    def __init__(self, config: ProductConfig) -> None:
        self.config = config
        self.source_status = SourceStatus.ERROR
        self.source_error: ProductError | None = None
        self.binding = ProjectionBinding(
            ProjectionState.NOT_CONFIGURED if config.projection_db_path is None
            else ProjectionState.CONFIGURED_ERROR,
            ProductError(ErrorCategory.PROJECTION_STORE_NOT_CONFIGURED, "projection", NOT_CONFIGURED)
            if config.projection_db_path is None else
            ProductError(ErrorCategory.PROJECTION_STORE_ERROR, "projection",
                         "Projection verification unavailable while the source store is unavailable."),
        )
        try:
            verse = get_verse(config.source_db_path, "MAT", 1, 1)
        except Exception as error:
            self.source_error = _failure(error, ErrorCategory.SOURCE_STORE_ERROR, "source",
                                         "Source store unavailable.")
            return
        if verse is None:
            self.source_error = ProductError(ErrorCategory.SOURCE_STORE_ERROR, "source",
                                             "Source store does not contain Matthew 1:1.")
            return
        self.source_status = SourceStatus.READY
        projection = config.projection_db_path
        if projection is None:
            return
        try:
            verify_projection_store(projection)
            before_source = _fingerprint(config.source_db_path)
            before_projection = _fingerprint(projection)
        except Exception as error:
            self.binding = ProjectionBinding(
                ProjectionState.CONFIGURED_ERROR,
                _failure(error, ErrorCategory.PROJECTION_STORE_ERROR, "projection",
                         "Structural interpretation store unavailable or invalid.", (QueryError, OSError)),
            )
            return
        try:
            verify_projection_store(projection, config.source_db_path)
            if (before_source != _fingerprint(config.source_db_path)
                    or before_projection != _fingerprint(projection)):
                self.binding = ProjectionBinding(
                    ProjectionState.BINDING_FAILED,
                    ProductError(ErrorCategory.SOURCE_PROJECTION_MISMATCH, "projection",
                                 STALE_BINDING),
                )
                return
        except Exception as error:
            self.binding = ProjectionBinding(
                ProjectionState.BINDING_FAILED,
                _failure(error, ErrorCategory.SOURCE_PROJECTION_MISMATCH, "projection",
                         "Source and structural interpretation store binding failed.", (QueryError, OSError)),
            )
            return
        self.binding = ProjectionBinding(ProjectionState.VERIFIED_EMPTY, None,
                                         before_source, before_projection)

    def status(self) -> ProductStatus:
        projection = self.config.projection_db_path
        if self.binding.state in (ProjectionState.VERIFIED_EMPTY, ProjectionState.VERIFIED_POPULATED):
            try:
                stale = (projection is None
                         or _fingerprint(self.config.source_db_path) != self.binding.source_fingerprint
                         or _fingerprint(projection) != self.binding.projection_fingerprint)
            except OSError as error:
                print(type(error).__name__, file=sys.stderr)
                stale = True
            if stale:
                self.binding = replace(
                    self.binding, state=ProjectionState.BINDING_FAILED,
                    error=ProductError(ErrorCategory.SOURCE_PROJECTION_MISMATCH, "projection",
                                       STALE_BINDING),
                )
        return ProductStatus(self.source_status, self.binding.state,
                             self.source_error or self.binding.error,
                             self.config.source_db_path.name,
                             None if projection is None else projection.name)

    def home(self, error: ProductError | None = None) -> ProductPage:
        return ProductPage(self.status(), None,
                           ProjectionPanel(self.binding.state, error=self.binding.error),
                           error=error or self.source_error)

    def load_verse(self, selection: ProductSelection) -> ProductPage:
        error = validate_selection(selection)
        if error is not None:
            return self.home(error)
        status = self.status()
        panel = ProjectionPanel(self.binding.state, error=self.binding.error)
        if self.source_status != SourceStatus.READY:
            return ProductPage(status, selection, panel, error=self.source_error)
        try:
            core_verse = get_verse(self.config.source_db_path, "MAT",
                                   selection.chapter, selection.verse)
            if core_verse is None:
                return ProductPage(
                    status, selection, panel,
                    error=ProductError(ErrorCategory.ABSENT, "selection",
                                       f"Verse not present in the source store: "
                                       f"MAT {selection.chapter}:{selection.verse}"),
                )
            tokens: list[ProductToken] = []
            nodes: dict[str, ProductSourceNode] = {}
            for token in core_verse.tokens:
                ref = f"MAT {selection.chapter}:{selection.verse}!{token.verse_token_ordinal}"
                if token.ref != ref:
                    return ProductPage(status, selection, panel, error=_contradiction("source"))
                tokens.append(ProductToken(
                    ref, token.chapter, token.verse, token.verse_token_ordinal,
                    token.surface, token.unicode, token.normalized, token.lemma, token.cat,
                    token.language, token.case, token.gender, token.number, token.person,
                    token.tense, token.voice, token.mood, token.degree, token.type,
                    token.functional_tag, token.formal_tag, token.strong_number,
                    token.english, token.mandarin, token.gloss, token.referent,
                    token.upstream_node_id, token.xml_id, token.morph_id,
                ))
                ancestors = get_ancestors_by_token(self.config.source_db_path, ref)
                if ancestors is None:
                    return ProductPage(status, selection, panel, error=_contradiction("source"))
                for ancestor in ancestors:
                    mapped = _node(ancestor)
                    if mapped.key in nodes and nodes[mapped.key] != mapped:
                        return ProductPage(status, selection, panel, error=_contradiction("source"))
                    nodes.setdefault(mapped.key, mapped)
            verse = ProductVerse(core_verse.book_code, core_verse.chapter, core_verse.verse,
                                 tuple(tokens), tuple(nodes.values()))
        except Exception as error:
            failure = _failure(error, ErrorCategory.SOURCE_STORE_ERROR, "source",
                               "Source store unavailable.")
            return ProductPage(
                replace(status, source_status=SourceStatus.ERROR, error=failure),
                selection, panel, error=failure,
            )
        notices: list[ProductError] = []
        selected_token = None
        if selection.token_ordinal is not None:
            selected_token = next((t for t in verse.tokens
                                   if t.ordinal == selection.token_ordinal), None)
            if selected_token is None:
                notices.append(ProductError(ErrorCategory.ABSENT, "selection",
                                            "Selected token not present in this verse."))
        projection = self.config.projection_db_path
        if self.binding.state != ProjectionState.VERIFIED_EMPTY or projection is None:
            return ProductPage(status, selection, panel, verse, selected_token,
                               notices=tuple(notices))
        try:
            core_histories = get_structural_interpretation_histories_for_selector(
                projection, ScriptureSelector("MAT", selection.chapter, selection.verse),
            )
            candidates: list[ProductCandidate] = []
            histories: list[ProductHistory] = []
            for history in core_histories:
                candidate = history.candidate
                if selection.token_ordinal is not None:
                    ref = f"MAT {selection.chapter}:{selection.verse}!{selection.token_ordinal}"
                    if ref not in candidate.scope.member_token_refs:
                        continue
                if candidate.candidate_kind == "apposition":
                    payload = ProductAppositionPayload(
                        candidate.payload.anchor_source_node_id,
                        candidate.payload.child_source_node_ids,
                    )
                else:
                    payload = ProductClausePayload(
                        candidate.payload.anchor_source_node_id, candidate.payload.source_rule,
                        candidate.payload.source_head_raw,
                        tuple(ProductClauseComponent(
                            c.source_node_id, c.source_cat, c.sibling_ordinal,
                            c.component_role, c.member_token_refs,
                        ) for c in candidate.payload.components),
                    )
                snapshot = candidate.source_snapshot
                candidates.append(ProductCandidate(
                    candidate.candidate_id, candidate.candidate_kind, candidate.derivation_kind,
                    candidate.derivation_version, candidate.status,
                    ProductSnapshot(snapshot.source_family, snapshot.edition,
                                    snapshot.repository_uri, snapshot.revision,
                                    snapshot.manifest_sha256, snapshot.relative_path,
                                    snapshot.source_sha256),
                    candidate.scope.source_node_id, candidate.scope.member_token_refs,
                    tuple((e.role, e.kind, e.source_node_id) for e in candidate.evidence),
                    payload, bool(history.evaluations),
                ))
                edges = tuple((e.predecessor_evaluation_id, e.successor_evaluation_id)
                              for e in history.supersession_edges)
                evaluations = tuple(ProductEvaluation(
                    e.evaluation_id, candidate.candidate_id, e.evaluator_class, e.evaluator_label,
                    e.evaluation_protocol_id, e.evaluation_protocol_version, e.disposition,
                    tuple((c.kind, c.citation_id) for c in e.rationale_evidence),
                    e.rationale_note.text, e.rationale_note.language, e.supersedes,
                    tuple(successor for predecessor, successor in edges
                          if predecessor == e.evaluation_id),
                    e.evaluation_id in history.unsuperseded_evaluation_ids,
                ) for e in history.evaluations)
                histories.append(ProductHistory(candidate.candidate_id, evaluations, edges,
                                                history.unsuperseded_evaluation_ids))
        except Exception as error:
            panel = ProjectionPanel(
                ProjectionState.CONFIGURED_ERROR,
                error=_failure(error, ErrorCategory.PROJECTION_STORE_ERROR, "projection",
                               "Structural interpretation store unavailable or invalid.", (ProjectionQueryError,)),
            )
            return ProductPage(replace(status, projection_state=panel.state, error=panel.error),
                               selection, panel, verse, selected_token, notices=tuple(notices))
        # A change during the reads invalidates their binding as well.
        status = self.status()
        if self.binding.state == ProjectionState.BINDING_FAILED:
            return ProductPage(status, selection,
                               ProjectionPanel(self.binding.state, error=self.binding.error),
                               verse, selected_token, notices=tuple(notices))
        panel = ProjectionPanel(
            ProjectionState.VERIFIED_POPULATED if candidates else ProjectionState.VERIFIED_EMPTY,
            tuple(candidates), tuple(histories),
        )
        status = replace(status, projection_state=panel.state)
        selected_candidate = next((c for c in candidates
                                   if c.key == selection.candidate_id), None)
        if selection.candidate_id is not None and selected_candidate is None:
            notices.append(ProductError(ErrorCategory.ABSENT, "selection",
                                        "Selected candidate not present for this selection."))
        if selection.candidate_id is None and selection.evaluation_id is not None:
            selected_history = next((h for h in histories if any(
                e.key == selection.evaluation_id for e in h.evaluations)), None)
            if selected_history is not None:
                selected_candidate = next(c for c in candidates if c.key == selected_history.key)
        selected_history = next((h for h in histories
                                 if selected_candidate is not None
                                 and h.key == selected_candidate.key), None)
        if selection.evaluation_id is not None and (
            selected_history is None
            or not any(e.key == selection.evaluation_id for e in selected_history.evaluations)
        ):
            notices.append(ProductError(ErrorCategory.ABSENT, "selection",
                                        "Selected evaluation not present for this selection."))
        evidence_nodes: dict[str, ProductSourceNode] = {}
        if selected_candidate is not None:
            try:
                for _, _, source_id in selected_candidate.evidence:
                    if source_id in evidence_nodes:
                        continue
                    node = get_node(self.config.source_db_path, source_id)
                    if node is None:
                        panel = replace(panel, candidate_error=_contradiction("source"))
                        break
                    evidence_nodes[source_id] = _node(node)
            except Exception as error:
                panel = replace(panel, candidate_error=_failure(
                    error, ErrorCategory.SOURCE_STORE_ERROR, "source", "Source evidence unavailable.",
                ))
            if panel.candidate_error is not None:
                selected_candidate = None
                selected_history = None
            else:
                panel = replace(panel, evidence_nodes=tuple(evidence_nodes.values()))
        ending_status = self.status()
        if ending_status.projection_state == ProjectionState.BINDING_FAILED:
            return ProductPage(ending_status, selection,
                               ProjectionPanel(self.binding.state, error=self.binding.error),
                               verse, selected_token, notices=tuple(notices))
        return ProductPage(status, selection, panel, verse, selected_token,
                           selected_candidate, selected_history, notices=tuple(notices))
