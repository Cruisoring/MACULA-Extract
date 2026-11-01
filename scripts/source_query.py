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


def get_token(db_path: str | Path, ref: str) -> TokenResult | None:
    """Return the exact source ref occurrence, or None when it does not exist."""
    match = _REF.fullmatch(ref) if isinstance(ref, str) else None
    if match is None:
        raise QueryError("ref must have exact source coordinate form, e.g. MAT 1:1!3")
    book_code = match[1]
    if any(len(match[i]) > 19 for i in (2, 3, 4)):
        raise QueryError("ref coordinates must be positive SQLite integers")
    chapter, verse, ordinal = (int(match[i]) for i in (2, 3, 4))
    for value, label in ((chapter, "chapter"), (verse, "verse"), (ordinal, "token ordinal")):
        _positive_integer(value, label)
    with _open_readonly(db_path) as db:
        book_id = _book_id(db, book_code)
        if book_id is None:
            return None
        rows = db.execute(_EXACT_SQL, (book_id, chapter, verse, ordinal, ref)).fetchall()
        if len(rows) > 1:
            raise QueryError("ambiguous exact token occurrence")
        return TokenResult(**dict(rows[0])) if rows else None
