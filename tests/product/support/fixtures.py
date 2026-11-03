from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scripts import evaluated_interpretations as evaluated
from scripts import projection_store as store
from tests.support import unit8_amendment1_store as fixture_builder
from tests.test_unit2 import SchemaFixture
from tests.test_unit10 import derive, record_for

from product.adapter import ExplorerAdapter
from product.config import ProductConfig


GREEK = (
    "\u0392\u03af\u03b2\u03bb\u03bf\u03c2", "\u03b3\u03b5\u03bd\u03ad\u03c3\u03b5\u03c9\u03c2",
    "\u1f38\u03b7\u03c3\u03bf\u1fe6", "\u03a7\u03c1\u03b9\u03c3\u03c4\u03bf\u1fe6",
    "\u03c5\u1f31\u03bf\u1fe6", "\u0394\u03b1\u03c5\u1f76\u03b4",
    "\u03c5\u1f31\u03bf\u1fe6", "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.",
)
_SURFACES = {
    "surface-" + identity: GREEK[int(attrs["ref"].rsplit("!", 1)[1]) - 1]
    for identity, attrs in fixture_builder._ATTRS.items()
    if attrs.get("ref", "").startswith("MAT 1:1!")
}


class GreekSchemaFixture(SchemaFixture):
    def archive(self, raw: bytes = b"<r/>", number: int = 1) -> tuple[int, int]:
        for old, new in _SURFACES.items():
            raw = raw.replace(old.encode("utf-8"), new.encode("utf-8"))
        return super().archive(raw, number)

    def content(self, file_id: int, owner: int | None, kind: str, value: str | None = None,
                child: int | None = None, target: str | None = None) -> int:
        return super().content(file_id, owner, kind, _SURFACES.get(value, value), child, target)

    def token(self, tree: int, book: int, node: int, text: str, attributes: dict[str, str],
              traversal: int = 0, canonical: int = 0, verse: int = 1, word: int = 1,
              overrides: dict[str, object] | None = None) -> int:
        return super().token(tree, book, node, _SURFACES.get(text, text), attributes,
                             traversal, canonical, verse, word, overrides)


def build_source(path: Path, pk_offset: int = 0) -> None:
    with patch.object(fixture_builder, "SchemaFixture", GreekSchemaFixture):
        fixture_builder.build_amendment1_store(path, pk_offset=pk_offset)


def file_state(path: Path) -> tuple[int, int, str, tuple[str, ...]]:
    stat = path.stat()
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(
            hashlib, "file_digest"
        ) else hashlib.sha256(stream.read()).hexdigest()
    sidecars = tuple(suffix for suffix in ("-wal", "-shm", "-journal")
                     if Path(str(path) + suffix).exists())
    return stat.st_size, stat.st_mtime_ns, digest, sidecars


class ParsedPage(HTMLParser):
    def __init__(self, html: str) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []
        self.text: list[str] = []
        self.feed(html)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.elements.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(self.text)

    @property
    def tokens(self) -> dict[str, dict[str, str | None]]:
        return {attrs["data-ref"]: attrs for _, attrs in self.elements if "data-ref" in attrs}


@dataclass
class Fixture:
    source: Path
    projection: Path
    clause_id: str
    apposition_ids: tuple[str, ...]
    evaluations: tuple[evaluated.EvaluatedStructuralInterpretation, ...]

    def adapter(self, configured: bool = True) -> ExplorerAdapter:
        return ExplorerAdapter(ProductConfig(self.source, self.projection if configured else None))


def populate_projection(source: Path, projection: Path) -> Fixture:
    store.initialize_projection_store(projection)
    appositions = derive(source, "MAT 1:1!3")
    clause = derive(source, "MAT 1:2!5")[0]
    for candidate in (*appositions, clause):
        store.store_candidate(projection, candidate, source_db_path=source)
    root = record_for(source, clause, event="product:root", label="reader")
    accepted = record_for(source, clause, event="product:accepted", label="reader",
                          disposition="accepted", predecessor=root, prior=(root,))
    rejected = record_for(source, clause, event="product:rejected", label="reader",
                          disposition="rejected", predecessor=root, prior=(root, accepted))
    opposing = record_for(source, clause, event="product:opposing", label="another reader",
                          disposition="rejected")
    records = (root, accepted, rejected, opposing)
    for record in records:
        store.store_evaluation(projection, record, source_db_path=source)
    return Fixture(source, projection, clause.candidate_id,
                   tuple(c.candidate_id for c in appositions), records)


def temporary_fixture(testcase) -> Fixture:
    directory = TemporaryDirectory(prefix="macula-product1-")
    testcase.addCleanup(directory.cleanup)
    source = Path(directory.name) / "source.sqlite3"
    projection = Path(directory.name) / "projection.sqlite3"
    build_source(source)
    fixture = populate_projection(source, projection)
    before = file_state(source), file_state(projection)

    def check_preservation() -> None:
        testcase.assertEqual((file_state(source), file_state(projection)), before)
        testcase.assertEqual(before[0][3], ())
        testcase.assertEqual(before[1][3], ())

    testcase.addCleanup(check_preservation)
    return fixture
