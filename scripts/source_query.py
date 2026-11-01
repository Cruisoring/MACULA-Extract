from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3

from scripts import source_schema as schema
from scripts.source_fidelity import open_readonly as _connect_readonly


class QueryError(ValueError):
    """Invalid query, incompatible store, or SQLite access failure."""


@dataclass(frozen=True)
class TokenResult:
    token_id: int
    book_id: int
    book_code: str
    chapter: int
    verse: int
    verse_token_ordinal: int
    node_id: int
    tree_id: int
    element_id: int
    upstream_node_id: str | None
    xml_id: str | None
    morph_id: str | None
    ref: str | None
    surface: str
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


@dataclass(frozen=True)
class VerseResult:
    book_code: str
    chapter: int
    verse: int
    tokens: tuple[TokenResult, ...]


@dataclass(frozen=True)
class NodeResult:
    source_node_id: str
    parent_source_node_id: str | None
    sibling_ordinal: int
    id_raw: str | None
    cat: str | None
    rule: str | None
    cl_type: str | None
    start_raw: str | None
    end_raw: str | None
    head_raw: str | None
    length_raw: str | None


@dataclass(frozen=True)
class SourceEvidence:
    token: TokenResult
    node: NodeResult
    ancestors: tuple[NodeResult, ...]
    parent_children: tuple[NodeResult, ...]
    membership_node: NodeResult
    contextual_members: tuple[TokenResult, ...]


_TOKEN_SQL = """
SELECT t.token_id, t.book_id, b.source_book_code AS book_code,
       t.chapter, t.verse, t.verse_token_ordinal,
       t.node_id, t.tree_id, n.element_id, n.upstream_node_id,
       t.xml_id, t.morph_id, t.ref_raw AS ref,
       t.source_direct_text AS surface, t.unicode_raw AS unicode,
       t.normalized_form AS normalized, t.unicode_lemma AS lemma, n.cat,
       t.language_raw AS language, t.case_raw AS "case", t.gender_raw AS gender,
       t.number_raw AS number, t.person_raw AS person, t.tense_raw AS tense,
       t.voice_raw AS voice, t.mood_raw AS mood, t.degree_raw AS degree,
       t.type_raw AS type, t.functional_tag, t.formal_tag, t.strong_number,
       t.english, t.mandarin, t.gloss, t.referent_raw AS referent
FROM main.token t
JOIN main.book b ON b.book_id = t.book_id
JOIN main.syntax_node n ON n.node_id = t.node_id
"""
_VERSE_SQL = _TOKEN_SQL + """
WHERE t.book_id = ? AND t.chapter = ? AND t.verse = ?
ORDER BY t.verse_token_ordinal
"""
_EXACT_SQL = _TOKEN_SQL + """
WHERE t.book_id = ? AND t.chapter = ? AND t.verse = ?
  AND t.verse_token_ordinal = ? AND t.ref_raw = ? COLLATE BINARY
"""
_REF = re.compile(r"([^\s]+) ([1-9][0-9]*):([1-9][0-9]*)!([1-9][0-9]*)")
_NODE_SQL = """
SELECT n.node_id, n.tree_id, n.parent_node_id,
       p.node_id AS resolved_parent_node_id,
       n.upstream_node_id AS source_node_id,
       p.upstream_node_id AS parent_source_node_id,
       n.sibling_ordinal, n.id_raw, n.cat, n.rule, n.cl_type,
       n.start_raw, n.end_raw, n.head_raw, n.length_raw
FROM main.syntax_node n
JOIN main.tree tr ON tr.tree_id = n.tree_id
JOIN main.sentence s ON s.sentence_id = tr.sentence_id
JOIN main.book b ON b.book_id = s.book_id
LEFT JOIN main.syntax_node p
  ON p.node_id = n.parent_node_id AND p.tree_id = n.tree_id
"""
_MEMBERS_SQL = _TOKEN_SQL + """
JOIN main.node_token_membership m
  ON m.token_id = t.token_id AND m.tree_id = t.tree_id
WHERE m.node_id = ?
ORDER BY b.book_ordinal, t.chapter, t.verse, t.verse_token_ordinal
"""


@contextmanager
def _open_readonly(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    db = None
    try:
        db = _connect_readonly(Path(db_path))
        if db.execute("PRAGMA user_version").fetchone() != (schema.SCHEMA_VERSION,):
            raise QueryError("source query requires schema version 2")
        identity = db.execute(
            "SELECT singleton, version, ddl_sha256, parser_contract_sha256, "
            "locator_contract_sha256 FROM main.schema_version",
        ).fetchall()
        if identity != [(1, *schema._identity())]:
            raise QueryError("source schema/contract identity mismatch")
        db.execute(_TOKEN_SQL + " LIMIT 0")
        db.row_factory = sqlite3.Row
        yield db
    except sqlite3.Error as error:
        raise QueryError(f"source query failed: {error}") from error
    finally:
        if db is not None:
            db.close()


def _book_id(db: sqlite3.Connection, book_code: str) -> int | None:
    rows = db.execute(
        "SELECT book_id FROM main.book WHERE source_book_code = ? COLLATE BINARY",
        (book_code,),
    ).fetchall()
    if len(rows) > 1:
        raise QueryError("ambiguous book identity; multiple snapshots are not supported")
    return rows[0][0] if rows else None


def _positive_integer(value: int, label: str) -> None:
    if type(value) is not int or not 0 < value <= 9223372036854775807:
        raise QueryError(f"{label} must be a positive SQLite integer")


def get_verse(
    db_path: str | Path, book_code: str, chapter: int, verse: int,
) -> VerseResult | None:
    """Return scripture-ordered source tokens, or None for a missing verse."""
    if not isinstance(book_code, str) or not book_code or any(c.isspace() for c in book_code):
        raise QueryError("book_code must be a nonempty source code without whitespace")
    _positive_integer(chapter, "chapter")
    _positive_integer(verse, "verse")
    with _open_readonly(db_path) as db:
        book_id = _book_id(db, book_code)
        if book_id is None:
            return None
        tokens = tuple(TokenResult(**dict(row)) for row in db.execute(
            _VERSE_SQL, (book_id, chapter, verse),
        ))
        if not tokens:
            return None
        if any(left.verse_token_ordinal >= right.verse_token_ordinal
               for left, right in zip(tokens, tokens[1:])):
            raise QueryError("ambiguous scripture coordinates within verse")
        return VerseResult(book_code, chapter, verse, tokens)


def _token_key(ref: str) -> tuple[str, int, int, int]:
    match = _REF.fullmatch(ref) if isinstance(ref, str) else None
    if match is None:
        raise QueryError("ref must have exact source coordinate form, e.g. MAT 1:1!3")
    book_code = match[1]
    if any(len(match[i]) > 19 for i in (2, 3, 4)):
        raise QueryError("ref coordinates must be positive SQLite integers")
    chapter, verse, ordinal = (int(match[i]) for i in (2, 3, 4))
    for value, label in ((chapter, "chapter"), (verse, "verse"), (ordinal, "token ordinal")):
        _positive_integer(value, label)
    return book_code, chapter, verse, ordinal


def _get_token(
    db: sqlite3.Connection, ref: str, key: tuple[str, int, int, int],
) -> TokenResult | None:
    book_code, chapter, verse, ordinal = key
    book_id = _book_id(db, book_code)
    if book_id is None:
        return None
    rows = db.execute(_EXACT_SQL, (book_id, chapter, verse, ordinal, ref)).fetchall()
    if len(rows) > 1:
        raise QueryError("ambiguous exact token occurrence")
    return TokenResult(**dict(rows[0])) if rows else None


def get_token(db_path: str | Path, ref: str) -> TokenResult | None:
    """Return the exact source ref occurrence, or None when it does not exist."""
    key = _token_key(ref)
    with _open_readonly(db_path) as db:
        return _get_token(db, ref, key)


@contextmanager
def _open_syntax_readonly(db_path: str | Path) -> Iterator[sqlite3.Connection]:
    with _open_readonly(db_path) as db:
        db.execute(_NODE_SQL + " LIMIT 0")
        db.execute(_MEMBERS_SQL + " LIMIT 0", (None,))
        yield db


def _source_node_key(source_node_id: str) -> None:
    if not isinstance(source_node_id, str) or not source_node_id:
        raise QueryError("source_node_id must be a nonempty source string")


def _resolve_source_node_id(db: sqlite3.Connection, source_node_id: str) -> int | None:
    book_id = _book_id(db, "MAT")
    rows = db.execute(
        "SELECT n.node_id FROM main.syntax_node n "
        "JOIN main.tree tr ON tr.tree_id = n.tree_id "
        "JOIN main.sentence s ON s.sentence_id = tr.sentence_id "
        "WHERE s.book_id = ? AND n.upstream_node_id = ? COLLATE BINARY",
        (book_id, source_node_id),
    ).fetchall()
    if len(rows) > 1:
        raise QueryError("ambiguous source_node_id within active Matthew snapshot")
    return rows[0][0] if rows else None


def _node_row(db: sqlite3.Connection, sqlite_node_id: int) -> sqlite3.Row:
    row = db.execute(_NODE_SQL + " WHERE n.node_id = ?", (sqlite_node_id,)).fetchone()
    if row is None:
        raise QueryError("missing linked syntax node")
    return row


def _project_node(row: sqlite3.Row) -> NodeResult:
    if row["source_node_id"] is None or row["source_node_id"] == "":
        raise QueryError("linked syntax node has no source_node_id")
    if row["parent_node_id"] is not None and row["resolved_parent_node_id"] is None:
        raise QueryError("missing or cross-Tree syntax parent")
    return NodeResult(
        source_node_id=row["source_node_id"],
        parent_source_node_id=row["parent_source_node_id"],
        sibling_ordinal=row["sibling_ordinal"],
        id_raw=row["id_raw"], cat=row["cat"], rule=row["rule"], cl_type=row["cl_type"],
        start_raw=row["start_raw"], end_raw=row["end_raw"],
        head_raw=row["head_raw"], length_raw=row["length_raw"],
    )


def get_node(db_path: str | Path, source_node_id: str) -> NodeResult | None:
    """Return exact source node facts, or None for an unknown source identity."""
    _source_node_key(source_node_id)
    with _open_syntax_readonly(db_path) as db:
        sqlite_node_id = _resolve_source_node_id(db, source_node_id)
        return None if sqlite_node_id is None else _project_node(_node_row(db, sqlite_node_id))


def _children(db: sqlite3.Connection, sqlite_node_id: int) -> tuple[NodeResult, ...]:
    return tuple(_project_node(row) for row in db.execute(
        _NODE_SQL + " WHERE n.parent_node_id = ? ORDER BY n.sibling_ordinal",
        (sqlite_node_id,),
    ))


def get_children(db_path: str | Path, source_node_id: str) -> tuple[NodeResult, ...] | None:
    """Return direct children in sibling order; None means unknown source node."""
    _source_node_key(source_node_id)
    with _open_syntax_readonly(db_path) as db:
        sqlite_node_id = _resolve_source_node_id(db, source_node_id)
        if sqlite_node_id is None:
            return None
        return _children(db, sqlite_node_id)


def _ancestors(db: sqlite3.Connection, sqlite_node_id: int) -> tuple[NodeResult, ...]:
    row = _node_row(db, sqlite_node_id)
    _project_node(row)
    tree_id = row["tree_id"]
    seen = {sqlite_node_id}
    ancestors: list[NodeResult] = []
    while row["parent_node_id"] is not None:
        parent = row["parent_node_id"]
        if parent in seen:
            raise QueryError("cyclic syntax ancestry")
        seen.add(parent)
        row = _node_row(db, parent)
        if row["tree_id"] != tree_id:
            raise QueryError("cross-Tree syntax ancestry")
        ancestors.append(_project_node(row))
    return tuple(ancestors)


def get_ancestors_by_node(
    db_path: str | Path, source_node_id: str,
) -> tuple[NodeResult, ...] | None:
    """Return nearest parent first, root last, excluding self; None if unknown."""
    _source_node_key(source_node_id)
    with _open_syntax_readonly(db_path) as db:
        sqlite_node_id = _resolve_source_node_id(db, source_node_id)
        return None if sqlite_node_id is None else _ancestors(db, sqlite_node_id)


def get_ancestors_by_token(db_path: str | Path, ref: str) -> tuple[NodeResult, ...] | None:
    """Use Unit 4 exact token lookup; nearest parent first, excluding the leaf."""
    key = _token_key(ref)
    with _open_syntax_readonly(db_path) as db:
        token = _get_token(db, ref, key)
        return None if token is None else _ancestors(db, token.node_id)


def _members(db: sqlite3.Connection, sqlite_node_id: int) -> tuple[TokenResult, ...]:
    tokens = tuple(TokenResult(**dict(row)) for row in db.execute(_MEMBERS_SQL, (sqlite_node_id,)))
    coordinates = [(t.book_code, t.chapter, t.verse, t.verse_token_ordinal) for t in tokens]
    if len(set(coordinates)) != len(coordinates):
        raise QueryError("ambiguous scripture coordinates within node membership")
    return tokens


def get_members(db_path: str | Path, source_node_id: str) -> tuple[TokenResult, ...] | None:
    """Return exact stored members in scripture order; None if source node unknown."""
    _source_node_key(source_node_id)
    with _open_syntax_readonly(db_path) as db:
        sqlite_node_id = _resolve_source_node_id(db, source_node_id)
        if sqlite_node_id is None:
            return None
        return _members(db, sqlite_node_id)


def get_source_evidence(db_path: str | Path, token_ref: str) -> SourceEvidence | None:
    """Compose exact token/leaf facts, nearest-first ancestry and parent context."""
    key = _token_key(token_ref)
    with _open_syntax_readonly(db_path) as db:
        token = _get_token(db, token_ref, key)
        if token is None:
            return None
        row = _node_row(db, token.node_id)
        node = _project_node(row)
        ancestors = _ancestors(db, token.node_id)
        parent = row["parent_node_id"]
        parent_children = () if parent is None else _children(db, parent)
        for source_node in (node, *ancestors, *parent_children):
            if _resolve_source_node_id(db, source_node.source_node_id) is None:
                raise QueryError("linked syntax source identity is outside active Matthew snapshot")
        membership_node = ancestors[0] if ancestors else node
        contextual_members = _members(db, token.node_id if parent is None else parent)
        return SourceEvidence(
            token=token, node=node, ancestors=ancestors, parent_children=parent_children,
            membership_node=membership_node, contextual_members=contextual_members,
        )
