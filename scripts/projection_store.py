"""Separate append-only persistence; source and evaluation semantics remain upstream."""

from collections.abc import Iterator
from contextlib import closing, contextmanager
from dataclasses import asdict, fields, is_dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from types import UnionType
from typing import Literal, TypeVar, Union, get_args, get_origin, get_type_hints

from scripts import evaluated_interpretations as evaluated
from scripts import structural_candidates as structural
from scripts.source_query import QueryError


STORE_PROTOCOL = "macula.structural-interpretation-store.v1"
APPLICATION_ID = 0x4D553130
SCHEMA_VERSION = 1
DDL_PATH = Path(__file__).resolve().parents[1] / "schema" / "001-projection-store.sql"
Candidate = structural.StructuralCandidate | structural.ClauseStructureCandidate
Evaluation = evaluated.EvaluatedStructuralInterpretation
T = TypeVar("T")


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _path(value: str | Path) -> Path:
    if not isinstance(value, (str, Path)) or isinstance(value, str) and not value.strip():
        raise QueryError("database path must be a nonempty string or Path")
    try:
        return Path(value).resolve()
    except (OSError, ValueError, RuntimeError) as error:
        raise QueryError(f"invalid database path: {error}") from error


def _separate(store_path: str | Path, source_path: str | Path) -> None:
    store, source = _path(store_path), _path(source_path)
    try:
        if store == source or store.exists() and source.exists() and store.samefile(source):
            raise QueryError("source and projection store must be physically separate")
    except OSError as error:
        raise QueryError(f"cannot establish separate database paths: {error}") from error


def _identity(value: str, *, evaluation: bool = False) -> None:
    prefix = "eval-sha256:" if evaluation else "sha256:"
    if not isinstance(value, str) or re.fullmatch(prefix + r"[0-9a-f]{64}", value) is None:
        raise QueryError("malformed evaluation_id" if evaluation else "malformed candidate_id")


def _ddl() -> str:
    try:
        return DDL_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise QueryError(f"cannot read projection DDL: {error}") from error


def _catalog(db: sqlite3.Connection) -> list[tuple[object, ...]]:
    return db.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name"
    ).fetchall()


@lru_cache(maxsize=1)
def _expected_catalog(ddl: str) -> list[tuple[object, ...]]:
    with closing(sqlite3.connect(":memory:")) as db:
        db.executescript(ddl)
        return _catalog(db)


def _check_schema(db: sqlite3.Connection) -> None:
    if (db.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION):
        raise QueryError("incompatible projection store identity or version")
    ddl = _ddl()
    if _catalog(db) != _expected_catalog(ddl):
        raise QueryError("projection store catalog drift")
    metadata = db.execute("SELECT * FROM projection_metadata").fetchall()
    if metadata != [(1, STORE_PROTOCOL, hashlib.sha256(ddl.encode("utf-8")).hexdigest())]:
        raise QueryError("projection store metadata or DDL hash drift")
    if db.execute("PRAGMA journal_mode").fetchone()[0] != "delete":
        raise QueryError("projection store requires DELETE journal mode")


@contextmanager
def _open(path: str | Path, *, write: bool = False) -> Iterator[sqlite3.Connection]:
    target = _path(path)
    db: sqlite3.Connection | None = None
    try:
        if write:
            # Unknown/source databases must fail before any writable connection.
            with _open(target) as preflight:
                _check_schema(preflight)
        db = sqlite3.connect(target.as_uri() + ("?mode=rw" if write else "?mode=ro"),
                             uri=True, timeout=5.0)
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA recursive_triggers=ON")
        if write:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("BEGIN IMMEDIATE")
        else:
            db.execute("PRAGMA query_only=ON")
        _check_schema(db)
        yield db
        if write:
            db.commit()
    except (sqlite3.Error, OSError) as error:
        raise QueryError(f"projection store access failed: {error}") from error
    finally:
        if db is not None:
            db.close()  # Closing an uncommitted connection rolls the transaction back.


def initialize_projection_store(path: str | Path) -> None:
    """Create exclusively; never initialize, migrate or overwrite an existing file."""
    target = _path(path)
    created = False
    complete = False
    try:
        with target.open("xb"):
            created = True
        with closing(sqlite3.connect(target.as_uri() + "?mode=rw", uri=True, timeout=5.0)) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA recursive_triggers=ON")
            db.execute("PRAGMA journal_mode=DELETE")
            db.execute("PRAGMA synchronous=FULL")
            ddl = _ddl()
            db.executescript("BEGIN IMMEDIATE;\n" + ddl)
            db.execute("INSERT INTO projection_metadata VALUES (1,?,?)",
                       (STORE_PROTOCOL, hashlib.sha256(ddl.encode("utf-8")).hexdigest()))
            _check_schema(db)
            db.commit()
            complete = True
    except (sqlite3.Error, OSError) as error:
        raise QueryError(f"projection store initialization failed: {error}") from error
    finally:
        if created and not complete:
            target.unlink()


def _object(value: object, names: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != names:
        raise QueryError("stored object has missing or unknown fields")
    return value


def _decode(cls: type[T], value: object) -> T:
    data = _object(value, {field.name for field in fields(cls)})
    hints = get_type_hints(cls)
    return cls(**{name: _decode_value(hints[name], item) for name, item in data.items()})


def _decode_value(annotation: object, value: object) -> object:
    origin, args = get_origin(annotation), get_args(annotation)
    if annotation is str or annotation is int:
        if type(value) is not annotation:
            raise QueryError("stored field has an invalid primitive type")
        return value
    if origin is Literal:
        if not any(type(value) is type(option) and value == option for option in args):
            raise QueryError("stored field has an unsupported literal")
        return value
    if origin is tuple:
        if type(value) is not list:
            raise QueryError("stored tuple field must be an array")
        return tuple(_decode_value(args[0], item) for item in value)
    if origin in (Union, UnionType):
        if annotation == Candidate:
            return _decode_candidate(value)
        if value is None and type(None) in args:
            return None
        return _decode_value(next(arg for arg in args if arg is not type(None)), value)
    if isinstance(annotation, type) and is_dataclass(annotation):
        return _decode(annotation, value)
    raise QueryError("unsupported stored field type")


def _decode_candidate(value: object) -> Candidate:
    if not isinstance(value, dict):
        raise QueryError("stored candidate must be an object")
    kind = value.get("candidate_kind")
    if kind == structural.CANDIDATE_KIND:
        return _decode(structural.StructuralCandidate, value)
    if kind == structural.CLAUSE_CANDIDATE_KIND:
        return _decode(structural.ClauseStructureCandidate, value)
    raise QueryError("unsupported stored candidate kind")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise QueryError("duplicate stored JSON key")
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise QueryError(f"non-finite stored JSON constant: {value}")


def _parse(text: str) -> object:
    try:
        value = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError) as error:
        raise QueryError(f"invalid stored JSON: {error}") from error
    if _json(value) != text:
        raise QueryError("noncanonical stored JSON")
    return value


def _candidate_json(candidate: Candidate) -> str:
    return _json({"candidate_protocol": structural.IDENTITY_PROTOCOL, "candidate": asdict(candidate)})


def _candidate_row(row: tuple[str, str]) -> Candidate:
    identity, text = row
    data = _object(_parse(text), {"candidate_protocol", "candidate"})
    if data["candidate_protocol"] != structural.IDENTITY_PROTOCOL:
        raise QueryError("unsupported stored candidate protocol")
    result = _decode_candidate(data["candidate"])
    if result.candidate_id != identity:
        raise QueryError("stored candidate key/echo conflict")
    return result


def _evaluation_row(db: sqlite3.Connection, row: tuple[str, str, str, str, str | None, str]) -> Evaluation:
    identity, candidate_id, label, event, supersedes, text = row
    result = _decode(Evaluation, _parse(text))
    if (result.evaluation_id, result.candidate.candidate_id, result.evaluator_label,
            result.event_key, result.supersedes) != (identity, candidate_id, label, event, supersedes):
        raise QueryError("stored evaluation key/echo conflict")
    candidate_row = db.execute("SELECT * FROM candidate WHERE candidate_id=?", (candidate_id,)).fetchone()
    if candidate_row is None or _candidate_row(candidate_row) != result.candidate:
        raise QueryError("stored evaluation candidate echo conflict")
    return result


def _contents(db: sqlite3.Connection) -> tuple[tuple[Candidate, ...], tuple[Evaluation, ...]]:
    candidates = tuple(_candidate_row(row) for row in db.execute("SELECT * FROM candidate"))
    for candidate in candidates:
        evaluated._verify_candidate(candidate)
    records = tuple(_evaluation_row(db, row) for row in db.execute("SELECT * FROM evaluation"))
    if records:
        evaluated.verify_evaluated_interpretation(records[0], prior_records=records)
    return candidates, records


def _ground(candidate: Candidate, source_db_path: str | Path) -> None:
    evaluated._verify_candidate(candidate)
    derived = structural.derive_structural_candidates(_path(source_db_path),
                                                      candidate.scope.member_token_refs[0])
    if derived is None or candidate not in derived:
        raise QueryError("candidate does not match source-grounded re-derivation or snapshot")


def _insert_candidate(db: sqlite3.Connection, candidate: Candidate) -> None:
    text = _candidate_json(candidate)
    old = db.execute("SELECT record_json FROM candidate WHERE candidate_id=?",
                     (candidate.candidate_id,)).fetchone()
    if old is not None:
        if old[0] != text:
            raise QueryError("conflicting stored candidate_id content")
        return
    db.execute("INSERT INTO candidate VALUES (?,?)", (candidate.candidate_id, text))


def store_candidate(store_path: str | Path, candidate: Candidate, *,
                    source_db_path: str | Path) -> None:
    """Append only after V1/V2; identical duplicates do not change logical records."""
    _separate(store_path, source_db_path)
    _ground(candidate, source_db_path)
    with _open(store_path, write=True) as db:
        _contents(db)
        _insert_candidate(db, candidate)


def get_candidate(store_path: str | Path, candidate_id: str) -> Candidate | None:
    """Load stored content without source access or replacement derivation."""
    _identity(candidate_id)
    with _open(store_path) as db:
        row = db.execute("SELECT * FROM candidate WHERE candidate_id=?", (candidate_id,)).fetchone()
        return None if row is None else _candidate_row(row)


def store_evaluation(store_path: str | Path, evaluation: Evaluation, *,
                     source_db_path: str | Path) -> None:
    """Atomically append the full candidate and human record with stored history."""
    _separate(store_path, source_db_path)
    if type(evaluation) is not Evaluation:
        raise QueryError("evaluation must be an EvaluatedStructuralInterpretation")
    with _open(store_path, write=True) as db:
        _, records = _contents(db)
        evaluated.verify_evaluated_interpretation(
            evaluation, db_path=_path(source_db_path), prior_records=records,
        )
        _insert_candidate(db, evaluation.candidate)
        text = _json(asdict(evaluation))
        old = db.execute("SELECT record_json FROM evaluation WHERE evaluation_id=?",
                         (evaluation.evaluation_id,)).fetchone()
        if old is not None:
            if old[0] != text:
                raise QueryError("conflicting stored evaluation_id content")
            return
        db.execute("INSERT INTO evaluation VALUES (?,?,?,?,?,?)", (
            evaluation.evaluation_id, evaluation.candidate.candidate_id,
            evaluation.evaluator_label, evaluation.event_key, evaluation.supersedes, text,
        ))


def get_evaluation(store_path: str | Path, evaluation_id: str) -> Evaluation | None:
    """Load the historical record; never regenerate human judgment."""
    _identity(evaluation_id, evaluation=True)
    with _open(store_path) as db:
        row = db.execute("SELECT * FROM evaluation WHERE evaluation_id=?", (evaluation_id,)).fetchone()
        return None if row is None else _evaluation_row(db, row)


def list_evaluations_for_candidate(store_path: str | Path, candidate_id: str) -> frozenset[Evaluation]:
    _identity(candidate_id)
    with _open(store_path) as db:
        return frozenset(_evaluation_row(db, row) for row in db.execute(
            "SELECT * FROM evaluation WHERE candidate_id=?", (candidate_id,),
        ))


def verify_projection_store(store_path: str | Path, source_db_path: str | Path | None = None) -> None:
    """Verify offline content/history, adding source-grounded checks only on request."""
    if source_db_path is not None:
        _separate(store_path, source_db_path)
    with _open(store_path) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise QueryError("projection store integrity check failed")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise QueryError("projection store foreign key check failed")
        candidates, records = _contents(db)
        if source_db_path is not None:
            for candidate in candidates:
                _ground(candidate, source_db_path)
            for record in records:
                evaluated.verify_evaluated_interpretation(
                    record, db_path=_path(source_db_path), prior_records=records,
                )
