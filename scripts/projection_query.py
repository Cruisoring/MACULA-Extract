"""Read-only discovery and history queries over the Unit 10 projection store.

Unit 11 adds no epistemic object: it reconstructs and validates records that Units 7-10
already define, and it never derives, ranks, resolves or writes them.
"""

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from scripts import evaluated_interpretations as evaluated
from scripts import projection_store as store
from scripts import structural_candidates as structural
from scripts.source_query import QueryError


Candidate = store.Candidate
Evaluation = evaluated.EvaluatedStructuralInterpretation
SUPPORTED_BOOK = "MAT"
_MAX_INTEGER = 2**63 - 1
_VERSE_REF = re.compile(r"MAT ([1-9][0-9]*):([1-9][0-9]*)")
_TOKEN_REF = re.compile(r"MAT ([1-9][0-9]*):([1-9][0-9]*)!([1-9][0-9]*)")


class ProjectionQueryError(Exception):
    """The request or the supplied projection store cannot be trusted."""


def _positive(value: object, label: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 1 <= value <= _MAX_INTEGER:
        raise ProjectionQueryError(f"{label} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class ScriptureSelector:
    book: str
    chapter: int | None = None
    verse: int | None = None
    token: int | None = None

    def __post_init__(self) -> None:
        if type(self.book) is not str:
            raise ProjectionQueryError("book is required")
        if self.book != SUPPORTED_BOOK:
            raise ProjectionQueryError(f"unsupported book: {self.book!r}")
        _positive(self.chapter, "chapter")
        _positive(self.verse, "verse")
        _positive(self.token, "token")
        if self.verse is not None and self.chapter is None:
            raise ProjectionQueryError("verse requires chapter")
        if self.token is not None and (self.chapter is None or self.verse is None):
            raise ProjectionQueryError("token requires chapter and verse")


@dataclass(frozen=True, slots=True)
class SupersessionEdge:
    predecessor_evaluation_id: str
    successor_evaluation_id: str


@dataclass(frozen=True, slots=True)
class StructuralInterpretationHistory:
    candidate: structural.StructuralCandidate | structural.ClauseStructureCandidate
    evaluations: tuple[Evaluation, ...]
    supersession_edges: tuple[SupersessionEdge, ...]
    unsuperseded_evaluation_ids: tuple[str, ...]


def _parse_ref(text: object, pattern: re.Pattern[str], label: str) -> tuple[int, ...]:
    if type(text) is not str:
        raise ProjectionQueryError(f"{label} must be a string")
    match = pattern.fullmatch(text)
    if match is None:
        raise ProjectionQueryError(f"malformed {label}")
    return tuple(int(part) for part in match.groups())


def _selector(value: object) -> ScriptureSelector:
    if type(value) is not ScriptureSelector:
        raise ProjectionQueryError("selector must be a ScriptureSelector")
    # Re-validate: a frozen instance can still be built without running __post_init__.
    return ScriptureSelector(value.book, value.chapter, value.verse, value.token)


def _identity(value: object, *, evaluation: bool = False) -> str:
    try:
        store._identity(value, evaluation=evaluation)
    except QueryError as error:
        raise ProjectionQueryError(str(error)) from error
    return value  # type: ignore[return-value]


def _load(projection_db_path: str | Path) -> tuple[tuple[Candidate, ...], tuple[Evaluation, ...]]:
    """Open read-only and return fully validated candidates and evaluations."""
    try:
        with store._open(projection_db_path) as db:
            candidates, records = store._contents(db)
    except (QueryError, sqlite3.Error, OSError, ValueError, RecursionError) as error:
        raise ProjectionQueryError(str(error)) from error
    _check_graph(records)
    return candidates, records


def _check_graph(records: tuple[Evaluation, ...]) -> None:
    by_id = {record.evaluation_id: record for record in records}
    for record in records:
        if record.supersedes is None:
            continue
        if record.supersedes == record.evaluation_id:
            raise ProjectionQueryError("evaluation cannot supersede itself")
        predecessor = by_id.get(record.supersedes)
        if predecessor is None:
            raise ProjectionQueryError("supersedes predecessor not found")
        if predecessor.candidate.candidate_id != record.candidate.candidate_id:
            raise ProjectionQueryError("supersedes predecessor concerns another candidate")
        if (predecessor.evaluator_class, predecessor.evaluator_label) != (
                record.evaluator_class, record.evaluator_label):
            raise ProjectionQueryError("supersedes predecessor has another evaluator")
    done: set[str] = set()
    for record in records:
        path: set[str] = set()
        current: Evaluation | None = record
        while current is not None and current.evaluation_id not in done:
            if current.evaluation_id in path:
                raise ProjectionQueryError("cyclic evaluation supersession")
            path.add(current.evaluation_id)
            current = None if current.supersedes is None else by_id[current.supersedes]
        done |= path


def _candidate_key(candidate: Candidate) -> tuple[object, ...]:
    first = evaluated._scope_keys(candidate.scope.member_token_refs, "candidate")[0]
    return (first, candidate.candidate_kind, candidate.derivation_kind,
            candidate.derivation_version, candidate.candidate_id)


def _evaluation_key(record: Evaluation) -> tuple[object, ...]:
    label = record.evaluator_label
    return (record.candidate.candidate_id, record.evaluator_class,
            (label is not None, label or ""), record.evaluation_protocol_id,
            record.evaluation_protocol_version, record.evaluation_id)


def _matches(candidate: Candidate, selector: ScriptureSelector) -> bool:
    wanted = (selector.book, selector.chapter, selector.verse, selector.token)
    for key in evaluated._scope_keys(candidate.scope.member_token_refs, "candidate"):
        if all(want is None or want == part for want, part in zip(wanted, key)):
            return True
    return False


def _discover(candidates: tuple[Candidate, ...], selector: ScriptureSelector) -> tuple[Candidate, ...]:
    # Every row was validated by _load; no row is skipped before its scope is known.
    return tuple(sorted((c for c in candidates if _matches(c, selector)), key=_candidate_key))


def _history(candidate: Candidate, records: tuple[Evaluation, ...]) -> StructuralInterpretationHistory:
    own = tuple(sorted((r for r in records if r.candidate.candidate_id == candidate.candidate_id),
                       key=_evaluation_key))
    edges = tuple(sorted(
        (SupersessionEdge(r.supersedes, r.evaluation_id) for r in own if r.supersedes is not None),
        key=lambda e: (e.predecessor_evaluation_id, e.successor_evaluation_id),
    ))
    superseded = {edge.predecessor_evaluation_id for edge in edges}
    leaves = tuple(sorted(r.evaluation_id for r in own if r.evaluation_id not in superseded))
    return StructuralInterpretationHistory(candidate, own, edges, leaves)


def _find_candidate(candidates: tuple[Candidate, ...], candidate_id: str) -> Candidate | None:
    return next((c for c in candidates if c.candidate_id == candidate_id), None)


def list_persisted_candidates_for_selector(
    projection_db_path: str | Path, selector: ScriptureSelector,
) -> tuple[Candidate, ...]:
    checked = _selector(selector)
    candidates, _ = _load(projection_db_path)
    return _discover(candidates, checked)


def list_persisted_candidates_for_chapter(
    projection_db_path: str | Path, book: str, chapter: int,
) -> tuple[Candidate, ...]:
    if chapter is None:
        raise ProjectionQueryError("chapter is required")
    return list_persisted_candidates_for_selector(projection_db_path, ScriptureSelector(book, chapter))


def list_persisted_candidates_for_verse(
    projection_db_path: str | Path, verse_ref: str,
) -> tuple[Candidate, ...]:
    chapter, verse = _parse_ref(verse_ref, _VERSE_REF, "verse_ref")
    return list_persisted_candidates_for_selector(
        projection_db_path, ScriptureSelector(SUPPORTED_BOOK, chapter, verse))


def list_persisted_candidates_for_token(
    projection_db_path: str | Path, token_ref: str,
) -> tuple[Candidate, ...]:
    chapter, verse, token = _parse_ref(token_ref, _TOKEN_REF, "token_ref")
    return list_persisted_candidates_for_selector(
        projection_db_path, ScriptureSelector(SUPPORTED_BOOK, chapter, verse, token))


def get_persisted_candidate(projection_db_path: str | Path, candidate_id: str) -> Candidate | None:
    _identity(candidate_id)
    candidates, _ = _load(projection_db_path)
    return _find_candidate(candidates, candidate_id)


def get_persisted_evaluation(projection_db_path: str | Path, evaluation_id: str) -> Evaluation | None:
    _identity(evaluation_id, evaluation=True)
    _, records = _load(projection_db_path)
    return next((r for r in records if r.evaluation_id == evaluation_id), None)


def list_candidate_evaluations(
    projection_db_path: str | Path, candidate_id: str,
) -> tuple[Evaluation, ...] | None:
    """Every evaluation of a known candidate; None only when the candidate itself is absent."""
    _identity(candidate_id)
    candidates, records = _load(projection_db_path)
    candidate = _find_candidate(candidates, candidate_id)
    return None if candidate is None else _history(candidate, records).evaluations


def get_evaluation_history(
    projection_db_path: str | Path, evaluation_id: str,
) -> tuple[Evaluation, ...] | None:
    """The connected supersession component of one evaluation, in presentation order only."""
    _identity(evaluation_id, evaluation=True)
    _, records = _load(projection_db_path)
    by_id = {r.evaluation_id: r for r in records}
    if evaluation_id not in by_id:
        return None
    neighbours: dict[str, set[str]] = {r.evaluation_id: set() for r in records}
    for record in records:
        if record.supersedes is not None:
            neighbours[record.evaluation_id].add(record.supersedes)
            neighbours[record.supersedes].add(record.evaluation_id)
    seen = {evaluation_id}
    queue = deque((evaluation_id,))
    while queue:
        for other in neighbours[queue.popleft()] - seen:
            seen.add(other)
            queue.append(other)
    return tuple(sorted((by_id[i] for i in seen), key=_evaluation_key))


def list_unsuperseded_evaluations(
    projection_db_path: str | Path, candidate_id: str,
) -> tuple[Evaluation, ...] | None:
    """Graph leaves only; being unsuperseded carries no authority."""
    _identity(candidate_id)
    candidates, records = _load(projection_db_path)
    candidate = _find_candidate(candidates, candidate_id)
    if candidate is None:
        return None
    history = _history(candidate, records)
    leaves = set(history.unsuperseded_evaluation_ids)
    return tuple(r for r in history.evaluations if r.evaluation_id in leaves)


def get_structural_interpretation_history(
    projection_db_path: str | Path, candidate_id: str,
) -> StructuralInterpretationHistory | None:
    _identity(candidate_id)
    candidates, records = _load(projection_db_path)
    candidate = _find_candidate(candidates, candidate_id)
    return None if candidate is None else _history(candidate, records)


def get_structural_interpretation_histories_for_selector(
    projection_db_path: str | Path, selector: ScriptureSelector,
) -> tuple[StructuralInterpretationHistory, ...]:
    checked = _selector(selector)
    candidates, records = _load(projection_db_path)
    return tuple(_history(c, records) for c in _discover(candidates, checked))
