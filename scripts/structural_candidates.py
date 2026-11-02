from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Final, Literal

from scripts import source_query as query


CANDIDATE_KIND: Final = "apposition"
DERIVATION_KIND: Final = "source-np-appos"
DERIVATION_VERSION: Final = "1"
IDENTITY_PROTOCOL: Final = "macula.structural-candidate.v1"
CLAUSE_CANDIDATE_KIND: Final = "clause-structure"
CLAUSE_DERIVATION_KIND: Final = "source-rule-s-v-o"
CLAUSE_DERIVATION_VERSION: Final = "1"
_CLAUSE_EVIDENCE_ROLES: Final[tuple[Literal["subject-child", "verbal-child", "object-child"], ...]] = (
    "subject-child", "verbal-child", "object-child",
)


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
    role: Literal["anchor", "child", "subject-child", "verbal-child", "object-child"]
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


@dataclass(frozen=True)
class ClauseComponent:
    source_node_id: str
    source_cat: str
    sibling_ordinal: int
    component_role: str
    member_token_refs: tuple[str, ...]


@dataclass(frozen=True)
class ClauseStructurePayload:
    anchor_source_node_id: str
    source_rule: str
    source_head_raw: str
    components: tuple[ClauseComponent, ...]


@dataclass(frozen=True)
class ClauseStructureCandidate:
    candidate_id: str
    candidate_kind: Literal["clause-structure"]
    derivation_kind: Literal["source-rule-s-v-o"]
    derivation_version: Literal["1"]
    source_snapshot: SourceSnapshot
    scope: CandidateScope
    evidence: tuple[EvidenceRef, ...]
    payload: ClauseStructurePayload
    status: Literal["candidate"] = "candidate"

    def __post_init__(self) -> None:
        if self.candidate_kind != CLAUSE_CANDIDATE_KIND:
            raise query.QueryError("unknown structural candidate kind")
        if (self.derivation_kind, self.derivation_version) != (
            CLAUSE_DERIVATION_KIND, CLAUSE_DERIVATION_VERSION,
        ):
            raise query.QueryError("unsupported clause derivation kind or version")
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


def _get_exact_memberships(
    db: sqlite3.Connection, source_node_ids: tuple[str, ...], snapshot: SourceSnapshot,
) -> tuple[tuple[str, ...], ...]:
    """Keep local join keys inside this boundary and retain every stored membership."""
    requested = tuple((ordinal, _resolve_node(db, identity))
                      for ordinal, identity in enumerate(source_node_ids))
    values = ",".join("(?,?)" for _ in requested)
    rows = db.execute(f"""
        WITH requested(owner_ordinal, local_node_id) AS (VALUES {values})
        SELECT r.owner_ordinal, n.tree_id AS owner_tree_id, os.book_id AS owner_book_id,
               m.tree_id AS membership_tree_id, t.tree_id AS token_tree_id,
               t.book_id AS token_book_id, nt.tree_id AS leaf_tree_id,
               t.ref_raw, b.source_book_code, b.book_ordinal,
               t.chapter, t.verse, t.verse_token_ordinal,
               d.source_family, d.edition, d.repository_uri, d.revision,
               d.manifest_sha256, f.relative_path, f.sha256 AS source_sha256
        FROM requested r
        JOIN main.syntax_node n ON n.node_id = r.local_node_id
        JOIN main.tree ot ON ot.tree_id = n.tree_id
        JOIN main.sentence os ON os.sentence_id = ot.sentence_id
        LEFT JOIN main.node_token_membership m ON m.node_id = n.node_id
        LEFT JOIN main.token t ON t.token_id = m.token_id
        LEFT JOIN main.syntax_node nt ON nt.node_id = t.node_id
        LEFT JOIN main.tree tr ON tr.tree_id = t.tree_id
        LEFT JOIN main.sentence s ON s.sentence_id = tr.sentence_id AND s.book_id = t.book_id
        LEFT JOIN main.book b ON b.book_id = s.book_id
        LEFT JOIN main.source_file f
          ON f.file_id = s.file_id AND f.book_id = b.book_id AND f.snapshot_id = b.snapshot_id
        LEFT JOIN main.dataset_snapshot d ON d.snapshot_id = b.snapshot_id
        ORDER BY r.owner_ordinal, b.book_ordinal, t.chapter, t.verse, t.verse_token_ordinal
    """, tuple(value for pair in requested for value in pair))
    memberships: list[list[str]] = [[] for _ in requested]
    coordinates: list[set[tuple[str, int, int, int]]] = [set() for _ in requested]
    for row in rows:
        ordinal = row["owner_ordinal"]
        if row["ref_raw"] is None:
            raise query.QueryError("empty required membership or member missing source token ref")
        if (row["owner_tree_id"] != row["membership_tree_id"]
                or row["owner_tree_id"] != row["token_tree_id"]
                or row["owner_tree_id"] != row["leaf_tree_id"]
                or row["owner_book_id"] != row["token_book_id"]):
            raise query.QueryError("inconsistent membership source/tree context")
        key = query._token_key(row["ref_raw"])
        if (key != (row["source_book_code"], row["chapter"], row["verse"],
                    row["verse_token_ordinal"])
                or not isinstance(row["book_ordinal"], int) or row["book_ordinal"] < 1):
            raise query.QueryError("membership missing or inconsistent canonical scripture coordinates")
        if key in coordinates[ordinal]:
            raise query.QueryError("duplicate membership ref or canonical scripture coordinate")
        coordinates[ordinal].add(key)
        linked_snapshot = SourceSnapshot(**{name: row[name] for name in SourceSnapshot.__annotations__})
        if linked_snapshot != snapshot:
            raise query.QueryError("membership source snapshot inconsistency")
        memberships[ordinal].append(row["ref_raw"])
    if any(not members for members in memberships):
        raise query.QueryError("empty required membership")
    return tuple(tuple(members) for members in memberships)


def _get_clause_membership_partition(
    db: sqlite3.Connection, node: query.NodeResult, snapshot: SourceSnapshot,
) -> tuple[CandidateScope, ClauseStructurePayload] | None:
    if node.rule != "S-V-O":
        return None
    children = query._children(db, _resolve_node(db, node.source_node_id))
    for child in children:
        _resolve_node(db, child.source_node_id)
    ordinals = tuple(child.sibling_ordinal for child in children)
    if ordinals != tuple(range(len(children))):
        raise query.QueryError("duplicate or missing sibling ordinal in clause topology")
    head = node.head_raw
    if head is not None:
        if not re.fullmatch(r"0|[1-9][0-9]*", head) or len(head) > 19:
            raise query.QueryError("malformed clause Head")
        if int(head) >= len(children):
            raise query.QueryError("clause Head outside direct-child range")
    if tuple(child.cat for child in children) != ("S", "V", "O") or head != "1":
        return None
    anchor_refs, *component_refs = _get_exact_memberships(
        db, (node.source_node_id, *(child.source_node_id for child in children)), snapshot,
    )
    assigned: set[str] = set()
    components: list[ClauseComponent] = []
    for child, refs, cat, role in zip(
        children, component_refs, ("S", "V", "O"),
        ("subject-component", "verbal-component", "object-component"),
    ):
        if assigned.intersection(refs):
            raise query.QueryError("overlapping clause component memberships")
        assigned.update(refs)
        components.append(ClauseComponent(
            child.source_node_id, cat, child.sibling_ordinal, role, refs,
        ))
    if assigned != set(anchor_refs):
        raise query.QueryError("clause component union differs from anchor membership")
    return (
        CandidateScope(node.source_node_id, anchor_refs),
        ClauseStructurePayload(node.source_node_id, node.rule, head, tuple(components)),
    )


def _identity_bytes(
    source_snapshot: SourceSnapshot, candidate_kind: str,
    derivation_kind: str, derivation_version: str, scope: CandidateScope,
    evidence: tuple[EvidenceRef, ...], payload: AppositionCandidatePayload | ClauseStructurePayload,
) -> bytes:
    payload_value: list[object]
    if candidate_kind == CANDIDATE_KIND and isinstance(payload, AppositionCandidatePayload):
        payload_value = [payload.anchor_source_node_id, list(payload.child_source_node_ids)]
    elif candidate_kind == CLAUSE_CANDIDATE_KIND and isinstance(payload, ClauseStructurePayload):
        payload_value = [
            payload.anchor_source_node_id, payload.source_rule, payload.source_head_raw,
            [[component.component_role, component.source_cat, component.sibling_ordinal,
              component.source_node_id, list(component.member_token_refs)]
             for component in payload.components],
        ]
    else:
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
        payload_value,
    ]
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _candidate_id(
    source_snapshot: SourceSnapshot, candidate_kind: str,
    derivation_kind: str, derivation_version: str, scope: CandidateScope,
    evidence: tuple[EvidenceRef, ...], payload: AppositionCandidatePayload | ClauseStructurePayload,
) -> str:
    return "sha256:" + hashlib.sha256(_identity_bytes(
        source_snapshot, candidate_kind, derivation_kind, derivation_version,
        scope, evidence, payload,
    )).hexdigest()


def derive_structural_candidates(
    db_path: str | Path, token_ref: str,
) -> tuple[StructuralCandidate | ClauseStructureCandidate, ...] | None:
    """Derive explicit Apposition/S-V-O on self/nearest-first ancestry; None if unknown."""
    source = query.get_source_evidence(db_path, token_ref)
    candidates: list[StructuralCandidate | ClauseStructureCandidate] = []
    with query._open_syntax_readonly(db_path) as db:
        db.execute(_SNAPSHOT_SQL + " LIMIT 0", (None,))
        if source is None:
            return None
        snapshot = _source_snapshot(db, source.token)
        for node in (source.node, *source.ancestors):
            if node.rule == "S-V-O":
                partition = _get_clause_membership_partition(db, node, snapshot)
                if partition is None:
                    continue
                clause_scope, clause_payload = partition
                if token_ref not in clause_scope.member_token_refs:
                    raise query.QueryError("candidate anchor membership omits selected token")
                clause_evidence = (
                    EvidenceRef("anchor", "syntax_node", node.source_node_id),
                    *(EvidenceRef(role, "syntax_node", component.source_node_id)
                      for role, component in zip(
                          _CLAUSE_EVIDENCE_ROLES,
                          clause_payload.components,
                      )),
                )
                candidates.append(ClauseStructureCandidate(
                    candidate_id=_candidate_id(
                        snapshot, CLAUSE_CANDIDATE_KIND, CLAUSE_DERIVATION_KIND,
                        CLAUSE_DERIVATION_VERSION, clause_scope, clause_evidence, clause_payload,
                    ),
                    candidate_kind=CLAUSE_CANDIDATE_KIND, derivation_kind=CLAUSE_DERIVATION_KIND,
                    derivation_version=CLAUSE_DERIVATION_VERSION, source_snapshot=snapshot,
                    scope=clause_scope, evidence=clause_evidence, payload=clause_payload,
                ))
                continue
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
