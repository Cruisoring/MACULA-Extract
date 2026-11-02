from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Final, Literal
import unicodedata

from scripts import structural_candidates as structural
from scripts.source_query import QueryError


RECORD_PROTOCOL: Final = "macula.evaluated-structural-interpretation.v1"
EVALUATION_PROTOCOL_ID: Final = "human-structural-adequacy"
EVALUATION_PROTOCOL_VERSION: Final = "1"

_CANDIDATE_ID = re.compile(r"sha256:[0-9a-f]{64}")
_EVALUATION_ID = re.compile(r"eval-sha256:[0-9a-f]{64}")
_EVENT_KEY = re.compile(r"[A-Za-z0-9._:-]{1,128}")
_TOKEN_REF = re.compile(r"([^\s]+) ([1-9][0-9]*):([1-9][0-9]*)!([1-9][0-9]*)")
_LANGUAGE = re.compile(
    r"(?:(?:[a-z]{2,3}(?:-[a-z]{3}){0,3}|[a-z]{4}|[a-z]{5,8})"
    r"(?:-[a-z]{4})?(?:-(?:[a-z]{2}|[0-9]{3}))?"
    r"(?:-(?:[a-z0-9]{5,8}|[0-9][a-z0-9]{3}))*"
    r"(?:-[0-9a-wy-z](?:-[a-z0-9]{2,8})+)*(?:-x(?:-[a-z0-9]{1,8})+)?"
    r"|x(?:-[a-z0-9]{1,8})+)", re.IGNORECASE | re.ASCII,
)
_GRANDFATHERED: Final = frozenset((
    "en-gb-oed", "i-ami", "i-bnn", "i-default", "i-enochian", "i-hak",
    "i-klingon", "i-lux", "i-mingo", "i-navajo", "i-pwn", "i-tao", "i-tay",
    "i-tsu", "sgn-be-fr", "sgn-be-nl", "sgn-ch-de", "art-lojban", "cel-gaulish",
    "no-bok", "no-nyn", "zh-guoyu", "zh-hakka", "zh-min", "zh-min-nan", "zh-xiang",
))


def _text(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QueryError(f"{label} must be a nonempty string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        raise QueryError(f"{label} must be valid UTF-8 text") from error


def _language(value: str) -> None:
    _text(value, "rationale note language")
    lowered = value.lower()
    if lowered in _GRANDFATHERED or lowered.startswith("x-") and _LANGUAGE.fullmatch(value):
        return
    if not _LANGUAGE.fullmatch(value):
        raise QueryError("rationale note language must be a BCP 47 tag")
    parts = lowered.split("-")
    variants: set[str] = set()
    extensions: set[str] = set()
    in_extension = False
    for part in parts[1:]:
        if part == "x":
            break
        if len(part) == 1:
            if part in extensions:
                raise QueryError("duplicate BCP 47 extension")
            extensions.add(part)
            in_extension = True
        elif not in_extension and (len(part) >= 5 or len(part) == 4 and part[0].isdigit()):
            if part in variants:
                raise QueryError("duplicate BCP 47 variant")
            variants.add(part)


@dataclass(frozen=True, slots=True)
class RationaleCitation:
    kind: Literal["syntax_node", "token"]
    citation_id: str

    def __post_init__(self) -> None:
        if self.kind not in ("syntax_node", "token"):
            raise QueryError("unsupported rationale citation kind")
        _text(self.citation_id, "rationale citation id")


@dataclass(frozen=True, slots=True)
class RationaleNote:
    text: str
    language: str

    def __post_init__(self) -> None:
        _text(self.text, "rationale note text")
        _language(self.language)


def _verify_candidate(candidate: structural.StructuralCandidate) -> None:
    if type(candidate) is not structural.StructuralCandidate:
        raise QueryError("candidate must be a Unit 7 StructuralCandidate, not a local PK")
    if not isinstance(candidate.candidate_id, str) or not _CANDIDATE_ID.fullmatch(candidate.candidate_id):
        raise QueryError("malformed candidate_id")
    if candidate.candidate_kind != "apposition":
        raise QueryError("unsupported candidate kind")
    if candidate.derivation_kind != "source-np-appos" or candidate.derivation_version != "1":
        raise QueryError("unsupported candidate derivation kind or version")
    if candidate.status != "candidate":
        raise QueryError("candidate status must remain candidate")
    snapshot = candidate.source_snapshot
    if type(snapshot) is not structural.SourceSnapshot:
        raise QueryError("candidate requires all seven source snapshot fields")
    snapshot_values = [
        snapshot.source_family, snapshot.edition, snapshot.repository_uri,
        snapshot.revision, snapshot.manifest_sha256, snapshot.relative_path,
        snapshot.source_sha256,
    ]
    for value in snapshot_values:
        _text(value, "source snapshot field")
    scope = candidate.scope
    if type(scope) is not structural.CandidateScope:
        raise QueryError("candidate requires an exact scope")
    _text(scope.source_node_id, "scope source node id")
    if type(scope.member_token_refs) is not tuple or not scope.member_token_refs:
        raise QueryError("candidate requires nonempty tuple scope members")
    keys: list[tuple[str, int, int, int]] = []
    for ref in scope.member_token_refs:
        _text(ref, "scope token ref")
        match = _TOKEN_REF.fullmatch(ref)
        if match is None:
            raise QueryError("scope token ref must have exact source coordinate form")
        book, chapter, verse, word = match.groups()
        numbers = (chapter, verse, word)
        if any(len(number) > 19 or int(number) > 2**63 - 1 for number in numbers):
            raise QueryError("scope coordinates must be positive SQLite integers")
        keys.append((book, int(chapter), int(verse), int(word)))
    if len({key[0] for key in keys}) != 1 or any(a >= b for a, b in zip(keys, keys[1:])):
        raise QueryError("scope tokens must be unique and in canonical scripture order")
    if type(candidate.evidence) is not tuple or not candidate.evidence:
        raise QueryError("candidate requires nonempty tuple evidence")
    evidence_values: list[list[str]] = []
    for index, ref in enumerate(candidate.evidence):
        if type(ref) is not structural.EvidenceRef:
            raise QueryError("candidate evidence must contain Unit 7 EvidenceRef values")
        if ref.role != ("anchor" if index == 0 else "child") or ref.kind != "syntax_node":
            raise QueryError("candidate evidence must be anchor then syntax_node children")
        _text(ref.source_node_id, "evidence source node id")
        evidence_values.append([ref.role, ref.kind, ref.source_node_id])
    node_ids = tuple(ref.source_node_id for ref in candidate.evidence)
    if len(set(node_ids)) != len(node_ids):
        raise QueryError("duplicate candidate evidence")
    payload = candidate.payload
    if type(payload) is not structural.AppositionCandidatePayload:
        raise QueryError("candidate requires an Apposition payload")
    if (type(payload.child_source_node_ids) is not tuple
            or payload.anchor_source_node_id != scope.source_node_id
            or payload.anchor_source_node_id != node_ids[0]
            or payload.child_source_node_ids != node_ids[1:]):
        raise QueryError("candidate payload must match scope and ordered evidence")
    # Frozen Unit 7 wire protocol, independent of its private identity helpers.
    value = [
        "macula.structural-candidate.v1", snapshot_values, candidate.candidate_kind,
        candidate.derivation_kind, candidate.derivation_version,
        [scope.source_node_id, list(scope.member_token_refs)], evidence_values,
        [payload.anchor_source_node_id, list(payload.child_source_node_ids)],
    ]
    expected = "sha256:" + hashlib.sha256(_identity_bytes(value)).hexdigest()
    if candidate.candidate_id != expected:
        raise QueryError("candidate_id does not recompute from candidate echo")


def _identity_bytes(value: list[object]) -> bytes:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def compute_evaluation_id(
    candidate: structural.StructuralCandidate, *,
    evaluator_class: str, evaluator_label: str,
    evaluation_protocol_id: str, evaluation_protocol_version: str,
    disposition: str, rationale_evidence: tuple[RationaleCitation, ...],
    rationale_note: RationaleNote, event_key: str, supersedes: str | None = None,
) -> str:
    """Validate V1 content and compute the frozen identity; no source or history access."""
    _verify_candidate(candidate)
    if (evaluation_protocol_id != EVALUATION_PROTOCOL_ID
            or evaluation_protocol_version != EVALUATION_PROTOCOL_VERSION):
        raise QueryError("unsupported evaluation protocol id or version")
    if evaluator_class != "human":
        raise QueryError("unsupported evaluator class; only human has a registered protocol")
    _text(evaluator_label, "human evaluator_label")
    if len(evaluator_label) > 128 or any(unicodedata.category(char) == "Cc" for char in evaluator_label):
        raise QueryError("human evaluator_label must be 1-128 characters without control characters")
    if not isinstance(event_key, str) or not _EVENT_KEY.fullmatch(event_key):
        raise QueryError("human event_key must be 1-128 characters from A-Za-z0-9._:-")
    if disposition not in ("accepted", "rejected", "undetermined"):
        raise QueryError("unsupported disposition")
    if type(rationale_note) is not RationaleNote:
        raise QueryError("human rationale note is required")
    rationale_note.__post_init__()
    if type(rationale_evidence) is not tuple:
        raise QueryError("rationale evidence must be a tuple")
    canonical = (
        *(("syntax_node", ref.source_node_id) for ref in candidate.evidence),
        *(("token", ref) for ref in candidate.scope.member_token_refs),
    )
    positions: list[int] = []
    for citation in rationale_evidence:
        if type(citation) is not RationaleCitation:
            raise QueryError("rationale evidence must contain RationaleCitation values")
        citation.__post_init__()
        key = (citation.kind, citation.citation_id)
        if key not in canonical:
            raise QueryError("rationale citation is outside candidate evidence or exact scope")
        positions.append(canonical.index(key))
    if any(a >= b for a, b in zip(positions, positions[1:])):
        raise QueryError("duplicate or incorrectly ordered rationale citations")
    if disposition in ("accepted", "rejected") and not rationale_evidence:
        raise QueryError("accepted/rejected requires at least one rationale citation")
    if supersedes is not None and (
        not isinstance(supersedes, str) or not _EVALUATION_ID.fullmatch(supersedes)
    ):
        raise QueryError("supersedes must be one evaluation_id or None")
    value = [
        RECORD_PROTOCOL, candidate.candidate_id, evaluator_class, evaluator_label,
        evaluation_protocol_id, evaluation_protocol_version, disposition,
        [[citation.kind, citation.citation_id] for citation in rationale_evidence],
        [rationale_note.text, rationale_note.language], event_key, supersedes,
    ]
    return "eval-sha256:" + hashlib.sha256(_identity_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class EvaluatedStructuralInterpretation:
    record_protocol: str
    evaluation_id: str
    candidate: structural.StructuralCandidate
    evaluator_class: Literal["human"]
    evaluator_label: str
    evaluation_protocol_id: str
    evaluation_protocol_version: str
    disposition: Literal["accepted", "rejected", "undetermined"]
    rationale_evidence: tuple[RationaleCitation, ...]
    rationale_note: RationaleNote
    event_key: str
    supersedes: str | None = None

    def __post_init__(self) -> None:
        if self.record_protocol != RECORD_PROTOCOL:
            raise QueryError("unsupported record_protocol")
        if not isinstance(self.evaluation_id, str) or not _EVALUATION_ID.fullmatch(self.evaluation_id):
            raise QueryError("malformed evaluation_id")
        if self.supersedes == self.evaluation_id:
            raise QueryError("evaluation cannot supersede itself")
        expected = compute_evaluation_id(
            self.candidate, evaluator_class=self.evaluator_class,
            evaluator_label=self.evaluator_label, evaluation_protocol_id=self.evaluation_protocol_id,
            evaluation_protocol_version=self.evaluation_protocol_version, disposition=self.disposition,
            rationale_evidence=self.rationale_evidence, rationale_note=self.rationale_note,
            event_key=self.event_key, supersedes=self.supersedes,
        )
        if self.evaluation_id != expected:
            raise QueryError("evaluation_id does not recompute from record content")


def _verify_history(
    record: EvaluatedStructuralInterpretation,
    prior_records: tuple[EvaluatedStructuralInterpretation, ...],
) -> None:
    if type(prior_records) is not tuple:
        raise QueryError("prior_records must be a tuple")
    records: dict[str, EvaluatedStructuralInterpretation] = {}
    events: dict[tuple[str, str], str] = {}
    for item in (*prior_records, record):
        if type(item) is not EvaluatedStructuralInterpretation:
            raise QueryError("prior_records must contain evaluation records")
        item.__post_init__()
        previous = records.get(item.evaluation_id)
        if previous is not None and previous != item:
            raise QueryError("inconsistent duplicate evaluation identity")
        records[item.evaluation_id] = item
        event = (item.evaluator_label, item.event_key)
        if event in events and events[event] != item.evaluation_id:
            raise QueryError("human event_key reuse conflict")
        events[event] = item.evaluation_id
    for item in records.values():
        if item.supersedes is None:
            continue
        predecessor = records.get(item.supersedes)
        if predecessor is None:
            raise QueryError("supersedes predecessor not found in prior_records")
        if predecessor.candidate.candidate_id != item.candidate.candidate_id:
            raise QueryError("supersedes predecessor must concern the same candidate")
        if (predecessor.evaluator_class, predecessor.evaluator_label) != (
            item.evaluator_class, item.evaluator_label,
        ):
            raise QueryError("supersedes predecessor must have the same evaluator")
    completed: set[str] = set()
    for item in records.values():
        lineage: set[str] = set()
        current: EvaluatedStructuralInterpretation | None = item
        while current is not None and current.evaluation_id not in completed:
            if current.evaluation_id in lineage:
                raise QueryError("cyclic evaluation supersession")
            lineage.add(current.evaluation_id)
            current = records[current.supersedes] if current.supersedes is not None else None
        completed.update(lineage)


def verify_evaluated_interpretation(
    record: EvaluatedStructuralInterpretation, *, db_path: str | Path | None = None,
    prior_records: tuple[EvaluatedStructuralInterpretation, ...] = (),
) -> None:
    """Verify V1/history offline, and V2 when the bound source store is supplied."""
    if type(record) is not EvaluatedStructuralInterpretation:
        raise QueryError("record must be an EvaluatedStructuralInterpretation")
    _verify_history(record, prior_records)
    if db_path is None:
        return
    candidate = record.candidate
    derived = structural.derive_structural_candidates(db_path, candidate.scope.member_token_refs[0])
    if not derived:
        raise QueryError("candidate not found in bound source store")
    if candidate in derived:
        return
    if not any(item.source_snapshot == candidate.source_snapshot for item in derived):
        raise QueryError("candidate source snapshot mismatch")
    if any(item.scope.source_node_id == candidate.scope.source_node_id for item in derived):
        raise QueryError("candidate echo does not match source-grounded re-derivation")
    raise QueryError("candidate not found in bound source store")


def create_evaluated_interpretation(
    db_path: str | Path, candidate: structural.StructuralCandidate, *,
    evaluator_class: Literal["human"], evaluator_label: str,
    evaluation_protocol_id: str, evaluation_protocol_version: str,
    disposition: Literal["accepted", "rejected", "undetermined"],
    rationale_evidence: tuple[RationaleCitation, ...], rationale_note: RationaleNote,
    event_key: str, supersedes: str | None = None,
    prior_records: tuple[EvaluatedStructuralInterpretation, ...] = (),
) -> EvaluatedStructuralInterpretation:
    """Create an immutable record only after V1, V2 and supplied-history validation."""
    if db_path is None:
        raise QueryError("creation requires a source database for V2")
    evaluation_id = compute_evaluation_id(
        candidate, evaluator_class=evaluator_class, evaluator_label=evaluator_label,
        evaluation_protocol_id=evaluation_protocol_id,
        evaluation_protocol_version=evaluation_protocol_version, disposition=disposition,
        rationale_evidence=rationale_evidence, rationale_note=rationale_note,
        event_key=event_key, supersedes=supersedes,
    )
    record = EvaluatedStructuralInterpretation(
        RECORD_PROTOCOL, evaluation_id, candidate, evaluator_class, evaluator_label,
        evaluation_protocol_id, evaluation_protocol_version, disposition,
        rationale_evidence, rationale_note, event_key, supersedes,
    )
    verify_evaluated_interpretation(record, db_path=db_path, prior_records=prior_records)
    return record
