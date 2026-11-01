from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Final, Literal

from scripts import source_query as query


CANDIDATE_KIND: Final = "apposition"
DERIVATION_KIND: Final = "source-np-appos"
DERIVATION_VERSION: Final = "1"
IDENTITY_PROTOCOL: Final = "macula.structural-candidate.v1"


@dataclass(frozen=True)
class SourceSnapshot:
    source_family: str
    edition: str
    repository_uri: str
    revision: str
    manifest_sha256: str
    relative_path: str
    source_sha256: str


@dataclass(frozen=True)
class EvidenceRef:
    role: Literal["anchor", "child"]
    kind: Literal["syntax_node"]
    source_node_id: str


@dataclass(frozen=True)
class CandidateScope:
    source_node_id: str
    member_token_refs: tuple[str, ...]


@dataclass(frozen=True)
class AppositionCandidatePayload:
    anchor_source_node_id: str
    child_source_node_ids: tuple[str, ...]


@dataclass(frozen=True)
class StructuralCandidate:
    candidate_id: str
    candidate_kind: Literal["apposition"]
    derivation_kind: str
    derivation_version: str
    source_snapshot: SourceSnapshot
    scope: CandidateScope
    evidence: tuple[EvidenceRef, ...]
    payload: AppositionCandidatePayload
    status: Literal["candidate"] = "candidate"

    def __post_init__(self) -> None:
        if self.candidate_kind != CANDIDATE_KIND:
            raise query.QueryError("unknown structural candidate kind")
        if self.status != "candidate":
            raise query.QueryError("structural candidates cannot have evaluation status")


_SNAPSHOT_SQL = """
SELECT d.source_family, d.edition, d.repository_uri, d.revision,
       d.manifest_sha256, f.relative_path, f.sha256 AS source_sha256
FROM main.token t
JOIN main.syntax_node n ON n.node_id = t.node_id AND n.tree_id = t.tree_id
JOIN main.tree tr ON tr.tree_id = n.tree_id
JOIN main.sentence s ON s.sentence_id = tr.sentence_id AND s.book_id = t.book_id
JOIN main.book b ON b.book_id = s.book_id
JOIN main.source_file f
  ON f.file_id = s.file_id AND f.book_id = b.book_id AND f.snapshot_id = b.snapshot_id
JOIN main.dataset_snapshot d ON d.snapshot_id = b.snapshot_id
WHERE t.token_id = ?
"""


def _source_snapshot(db: sqlite3.Connection, token: query.TokenResult) -> SourceSnapshot:
    rows = db.execute(_SNAPSHOT_SQL, (token.token_id,)).fetchall()
    if len(rows) != 1 or any(not isinstance(value, str) or not value for value in rows[0]):
        raise query.QueryError("missing or inconsistent linked source snapshot")
    return SourceSnapshot(**dict(rows[0]))


def _resolve_node(db: sqlite3.Connection, source_node_id: str) -> int:
    sqlite_node_id = query._resolve_source_node_id(db, source_node_id)
    if sqlite_node_id is None:
        raise query.QueryError("unresolved candidate source evidence")
    return sqlite_node_id


def _scope(db: sqlite3.Connection, source_node_id: str) -> CandidateScope:
    """Project exact stored membership, never a source Start/End envelope."""
    members = query._members(db, _resolve_node(db, source_node_id))
    if not members:
        raise query.QueryError("candidate scope has no source token evidence")
    refs: list[str] = []
    for token in members:
        if token.ref is None:
            raise query.QueryError("candidate scope member has no source token ref")
        if query._token_key(token.ref) != (
            token.book_code, token.chapter, token.verse, token.verse_token_ordinal,
        ):
            raise query.QueryError("candidate scope member ref disagrees with source coordinates")
        refs.append(token.ref)
    return CandidateScope(source_node_id, tuple(refs))


def _identity_bytes(
    source_snapshot: SourceSnapshot, candidate_kind: str,
    derivation_kind: str, derivation_version: str, scope: CandidateScope,
    evidence: tuple[EvidenceRef, ...], payload: AppositionCandidatePayload,
) -> bytes:
    if candidate_kind != CANDIDATE_KIND:
        raise query.QueryError("unknown structural candidate kind")
    value = [
        IDENTITY_PROTOCOL,
        [
            source_snapshot.source_family, source_snapshot.edition,
            source_snapshot.repository_uri, source_snapshot.revision,
            source_snapshot.manifest_sha256, source_snapshot.relative_path,
            source_snapshot.source_sha256,
        ],
        candidate_kind, derivation_kind, derivation_version,
        [scope.source_node_id, list(scope.member_token_refs)],
        [[ref.role, ref.kind, ref.source_node_id] for ref in evidence],
        [payload.anchor_source_node_id, list(payload.child_source_node_ids)],
    ]
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _candidate_id(
    source_snapshot: SourceSnapshot, candidate_kind: str,
    derivation_kind: str, derivation_version: str, scope: CandidateScope,
    evidence: tuple[EvidenceRef, ...], payload: AppositionCandidatePayload,
) -> str:
    return "sha256:" + hashlib.sha256(_identity_bytes(
        source_snapshot, candidate_kind, derivation_kind, derivation_version,
        scope, evidence, payload,
    )).hexdigest()


def derive_structural_candidates(
    db_path: str | Path, token_ref: str,
) -> tuple[StructuralCandidate, ...] | None:
    """Derive only explicit Np-Appos on self/nearest-first ancestry; None if unknown."""
    source = query.get_source_evidence(db_path, token_ref)
    candidates: list[StructuralCandidate] = []
    with query._open_syntax_readonly(db_path) as db:
        db.execute(_SNAPSHOT_SQL + " LIMIT 0", (None,))
        if source is None:
            return None
        snapshot = _source_snapshot(db, source.token)
        for node in (source.node, *source.ancestors):
            if node.rule != "Np-Appos":
                continue
            children = query._children(db, _resolve_node(db, node.source_node_id))
            for child in children:
                _resolve_node(db, child.source_node_id)
            scope = _scope(db, node.source_node_id)
            if token_ref not in scope.member_token_refs:
                raise query.QueryError("candidate anchor membership omits selected token")
            evidence = (
                EvidenceRef("anchor", "syntax_node", node.source_node_id),
                *(EvidenceRef("child", "syntax_node", child.source_node_id) for child in children),
            )
            payload = AppositionCandidatePayload(
                node.source_node_id, tuple(child.source_node_id for child in children),
            )
            candidates.append(StructuralCandidate(
                candidate_id=_candidate_id(
                    snapshot, CANDIDATE_KIND, DERIVATION_KIND, DERIVATION_VERSION,
                    scope, evidence, payload,
                ),
                candidate_kind=CANDIDATE_KIND, derivation_kind=DERIVATION_KIND,
                derivation_version=DERIVATION_VERSION, source_snapshot=snapshot,
                scope=scope, evidence=evidence, payload=payload,
            ))
    return tuple(candidates)
