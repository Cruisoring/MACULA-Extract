from dataclasses import FrozenInstanceError
import hashlib
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

from scripts import source_query as query
from scripts import source_schema as schema
from tests.test_unit2 import SchemaFixture, tag


class Unit4FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit4-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "fixture # query.sqlite3"
        self.db = sqlite3.connect(self.path)
        self.addCleanup(self.db.close)
        schema.bootstrap(self.db)
        self._fixture()
        schema.validate_store(self.db)
        self.db.commit()

    def _fixture(self) -> None:
        facts = [
            (1, 3, "\u1f38\u03b7\u03c3\u03bf\u1fe6", {
                "UnicodeLemma": "\u1f38\u03b7\u03c3\u03bf\u1fe6\u03c2", "Case": "Genitive",
                "Gender": "Masculine", "Number": "Singular", "Type": "Proper",
                "StrongNumber": "2424", "English": "", "Mandarin": "mandarin-source",
                "Gloss": "gloss-source", "FunctionalTag": "N-GSM", "FormalTag": "N-PRI",
                "Ref": "distinct-referent", "Person": "Third", "Tense": "Present",
                "Voice": "Active", "Mood": "Indicative", "Degree": "Positive",
            }),
            (2, 6, "source-six", {}),
            (2, 5, "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.", {
                "NormalizedForm": "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc",
                "Unicode": "separate-unicode-mirror", "UnicodeLemma": "",
            }),
        ]
        attributes = [
            {"Cat": "noun", "nodeId": f"leaf-{i}", "ref": f"MAT 1:{verse}!{word}", **extras}
            for i, (verse, word, _, extras) in enumerate(facts)
        ]
        raw = tag("Sentences", {}, tag("Sentence", {"ref": "MAT 1:1!3-1:2!6"},
              tag("Trees", {}, tag("Tree", {}, tag("Node", {"Cat": "S"}, "".join(
                  tag("Node", attrs, escape(text))
                  for attrs, (_, _, text, _) in zip(attributes, facts)
              )))))).encode("utf-8")
        fixture = SchemaFixture(self.db)
        file_id, book_id = fixture.archive(raw)
        document = fixture.element(file_id, None, "Sentences")
        sentence_element = fixture.element(file_id, document, "Sentence")
        fixture.attribute(sentence_element, "ref", "MAT 1:1!3-1:2!6")
        sentence = fixture.insert("sentence", {
            "file_id": file_id, "book_id": book_id, "element_id": sentence_element,
            "ordinal": 0, "ref_raw": "MAT 1:1!3-1:2!6",
        })
        wrapper = fixture.element(file_id, sentence_element, "Trees")
        tree_element = fixture.element(file_id, wrapper, "Tree")
        tree = fixture.insert("tree", {"sentence_id": sentence, "element_id": tree_element, "ordinal": 0})
        root_element = fixture.element(file_id, tree_element, "Node")
        fixture.attributes(root_element, {"Cat": "S"})
        root = fixture.node(tree, root_element, None, 0, {"Cat": "S"})
        for traversal, ((verse, word, text, _), attrs) in enumerate(zip(facts, attributes)):
            element = fixture.element(file_id, root_element, "Node")
            fixture.attributes(element, attrs)
            fixture.content(file_id, element, "text", text)
            node = fixture.node(tree, element, root, traversal, attrs)
            fixture.token(tree, book_id, node, text, attrs, traversal=traversal,
                          canonical=(0, 2, 1)[traversal], verse=verse, word=word)
        fixture.memberships()

    def test_canonical_order_not_tree_or_row_order(self) -> None:
        verse = query.get_verse(self.path, "MAT", 1, 2)
        self.assertIsNotNone(verse)
        assert verse is not None
        self.assertEqual((verse.book_code, verse.chapter, verse.verse), ("MAT", 1, 2))
        self.assertEqual([t.ref for t in verse.tokens], ["MAT 1:2!5", "MAT 1:2!6"])
        self.assertEqual([t.verse_token_ordinal for t in verse.tokens], [5, 6])
        self.assertGreater(verse.tokens[0].token_id, verse.tokens[1].token_id)

    def test_exact_token_and_verse_use_same_model(self) -> None:
        token = query.get_token(self.path, "MAT 1:1!3")
        verse = query.get_verse(str(self.path), "MAT", 1, 1)
        assert token is not None and verse is not None
        self.assertEqual(token, verse.tokens[0])
        self.assertEqual((token.surface, token.lemma, token.case, token.gender, token.type, token.strong_number),
                         ("\u1f38\u03b7\u03c3\u03bf\u1fe6", "\u1f38\u03b7\u03c3\u03bf\u1fe6\u03c2",
                          "Genitive", "Masculine", "Proper", "2424"))
        self.assertEqual((token.number, token.person, token.tense, token.voice, token.mood, token.degree),
                         ("Singular", "Third", "Present", "Active", "Indicative", "Positive"))
        self.assertEqual((token.upstream_node_id, token.cat), ("leaf-0", "noun"))
        self.assertTrue(all(value > 0 for value in
                            (token.token_id, token.node_id, token.tree_id, token.element_id, token.book_id)))
        with self.assertRaises(FrozenInstanceError):
            setattr(token, "surface", "changed")

    def test_source_distinctions_and_absence_survive(self) -> None:
        token = query.get_token(self.path, "MAT 1:2!5")
        jesus = query.get_token(self.path, "MAT 1:1!3")
        assert token is not None and jesus is not None
        self.assertEqual(token.surface, "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.")
        self.assertEqual(token.normalized, "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc")
        self.assertEqual(token.unicode, "separate-unicode-mirror")
        self.assertEqual(token.lemma, "")
        self.assertEqual((jesus.unicode, jesus.normalized, jesus.xml_id, jesus.morph_id), (None,) * 4)
        self.assertEqual((jesus.english, jesus.mandarin, jesus.gloss), ("", "mandarin-source", "gloss-source"))
        self.assertEqual((jesus.functional_tag, jesus.formal_tag), ("N-GSM", "N-PRI"))
        self.assertEqual((jesus.ref, jesus.referent), ("MAT 1:1!3", "distinct-referent"))
        self.assertIsNone(token.case)

    def test_not_found_has_no_fallback_or_case_guessing(self) -> None:
        for book, chapter, verse in (("MAT", 99, 99), ("mat", 1, 1), ("MRK", 1, 1)):
            with self.subTest(book=book, chapter=chapter, verse=verse):
                self.assertIsNone(query.get_verse(self.path, book, chapter, verse))
        for ref in ("MAT 1:1!999", "mat 1:1!3", "MRK 1:1!3", "MAT 1:1!1"):
            with self.subTest(ref=ref):
                self.assertIsNone(query.get_token(self.path, ref))

    def test_invalid_arguments_fail_explicitly(self) -> None:
        for ref in ("", "MAT 1:1", " MAT 1:1!3", "MAT 1:1!3 ", "MAT 01:1!3",
                    "MAT 0:1!3", "MAT 1:1!3' OR 1=1", f"MAT {2**63}:1!3"):
            with self.subTest(ref=ref), self.assertRaises(query.QueryError):
                query.get_token(self.path, ref)
        with self.assertRaises(query.QueryError):
            query.get_token(self.path, "MAT " + "9" * 5000 + ":1!3")
        for book, chapter, verse in (("", 1, 1), ("MAT ", 1, 1), ("MAT", 0, 1),
                                      ("MAT", 1, -1), ("MAT", True, 1), ("MAT", 2**63, 1)):
            with self.subTest(book=book, chapter=chapter, verse=verse), self.assertRaises(query.QueryError):
                query.get_verse(self.path, book, chapter, verse)

    def test_sqlite_rejects_insert_update_delete_even_without_query_only(self) -> None:
        before = hashlib.sha256(self.path.read_bytes()).digest()
        with query._open_readonly(self.path) as db:
            for pragma in ("query_only", "foreign_keys", "recursive_triggers"):
                self.assertEqual(db.execute(f"PRAGMA {pragma}").fetchone()[0], 1)
            for disable_query_only in (False, True):
                if disable_query_only:
                    db.execute("PRAGMA query_only=OFF")
                for sql in (
                    "INSERT INTO token DEFAULT VALUES",
                    "UPDATE token SET source_direct_text='changed'",
                    "DELETE FROM token",
                ):
                    with self.subTest(sql=sql, query_only=not disable_query_only):
                        with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                            db.execute(sql)
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).digest(), before)

    def test_missing_or_non_sqlite_database_is_not_not_found(self) -> None:
        missing = self.path.with_name("missing.sqlite3")
        with self.assertRaises(query.QueryError):
            query.get_verse(missing, "MAT", 99, 99)
        self.assertFalse(missing.exists())
        broken = self.path.with_name("broken.sqlite3")
        broken.write_bytes(b"not a SQLite database")
        with self.assertRaises(query.QueryError):
            query.get_token(broken, "MAT 1:1!999")

    def test_schema_version_identity_and_query_columns_are_required(self) -> None:
        mutations = (
            "PRAGMA user_version=1",
            "PRAGMA user_version=3",
            "DROP TRIGGER version_no_update; UPDATE schema_version SET ddl_sha256='" + "0" * 64 + "'",
            "DROP TRIGGER version_no_update; UPDATE schema_version SET parser_contract_sha256='" + "0" * 64 + "'",
            "DROP TABLE schema_version",
            "DROP TABLE token",
            "ALTER TABLE token RENAME COLUMN normalized_form TO missing_normalized",
            "ALTER TABLE syntax_node RENAME COLUMN cat TO missing_cat",
            "ALTER TABLE book RENAME COLUMN source_book_code TO missing_book_code",
        )
        for sql in mutations:
            with self.subTest(sql=sql):
                path = self.path.with_name("invalid.sqlite3")
                invalid = sqlite3.connect(path)
                try:
                    self.db.backup(invalid)
                    invalid.executescript(sql)
                finally:
                    invalid.close()
                for operation in (
                    lambda: query.get_verse(path, "MAT", 99, 99),
                    lambda: query.get_token(path, "MAT 1:1!999"),
                ):
                    with self.assertRaises(query.QueryError):
                        operation()
                path.unlink()

    def test_empty_schema_v2_store_returns_none(self) -> None:
        path = self.path.with_name("empty.sqlite3")
        db = sqlite3.connect(path)
        try:
            schema.bootstrap(db)
        finally:
            db.close()
        self.assertIsNone(query.get_verse(path, "MAT", 1, 1))
        self.assertIsNone(query.get_token(path, "MAT 1:1!3"))

    def test_multiple_snapshot_book_identity_fails_closed(self) -> None:
        fixture = SchemaFixture(self.db)
        fixture.archive(number=2)
        self.db.commit()
        for operation in (
            lambda: query.get_verse(self.path, "MAT", 1, 1),
            lambda: query.get_token(self.path, "MAT 1:1!3"),
        ):
            with self.assertRaisesRegex(query.QueryError, "ambiguous book"):
                operation()

    def test_query_uses_scripture_index_and_no_membership(self) -> None:
        with query._open_readonly(self.path) as db:
            for sql, args in ((query._VERSE_SQL, (1, 1, 2)),
                              (query._EXACT_SQL, (1, 1, 1, 3, "MAT 1:1!3"))):
                plan = [row[3] for row in db.execute("EXPLAIN QUERY PLAN " + sql, args)]
                self.assertTrue(any("SEARCH t USING INDEX token_scripture" in detail for detail in plan), plan)
                self.assertFalse(any("SCAN t" in detail for detail in plan), plan)
        statements: list[str] = []
        original_connect = query._connect_readonly

        def traced_connect(path: Path) -> sqlite3.Connection:
            db = original_connect(path)
            db.set_trace_callback(statements.append)
            return db

        with patch.object(query, "_connect_readonly", side_effect=traced_connect):
            self.assertIsNotNone(query.get_verse(self.path, "MAT", 1, 2))
        self.assertFalse(any("membership" in sql.lower() for sql in statements), statements)
        self.assertFalse(any(sql.lstrip().split()[0].upper() in
                             ("INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER", "VACUUM")
                             for sql in statements), statements)


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT4_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT4_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only local full-Matthew integration")
class Unit4MatthewIntegrationTests(unittest.TestCase):
    def test_matthew_1_1_exact_surfaces_and_refs(self) -> None:
        verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 1)
        assert verse is not None
        self.assertEqual(len(verse.tokens), 8)
        self.assertEqual([t.ref for t in verse.tokens], [f"MAT 1:1!{i}" for i in range(1, 9)])
        self.assertEqual([t.verse_token_ordinal for t in verse.tokens], list(range(1, 9)))
        self.assertEqual([t.surface for t in verse.tokens], [
            "\u0392\u03af\u03b2\u03bb\u03bf\u03c2", "\u03b3\u03b5\u03bd\u03ad\u03c3\u03b5\u03c9\u03c2",
            "\u1f38\u03b7\u03c3\u03bf\u1fe6", "\u03c7\u03c1\u03b9\u03c3\u03c4\u03bf\u1fe6",
            "\u03c5\u1f31\u03bf\u1fe6", "\u0394\u03b1\u03c5\u1f76\u03b4",
            "\u03c5\u1f31\u03bf\u1fe6", "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.",
        ])
        self.assertEqual(verse.tokens[0].lemma, "\u03b2\u03af\u03b2\u03bb\u03bf\u03c2")
        self.assertEqual(verse.tokens[2].lemma, "\u1f38\u03b7\u03c3\u03bf\u1fe6\u03c2")
        self.assertEqual(verse.tokens[2].strong_number, "2424")
        self.assertEqual(verse.tokens[-1].normalized, "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc")
        self.assertNotEqual(verse.tokens[-1].surface, verse.tokens[-1].normalized)

    def test_matthew_1_2_canonical_order(self) -> None:
        verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 2)
        assert verse is not None
        ordinals = [t.verse_token_ordinal for t in verse.tokens]
        refs = [t.ref for t in verse.tokens]
        self.assertEqual(ordinals, sorted(set(ordinals)))
        self.assertLess(refs.index("MAT 1:2!5"), refs.index("MAT 1:2!6"))
        with query._open_readonly(_LOCAL_DATABASE) as db:
            traversal = [row[0] for row in db.execute(
                "SELECT ref_raw FROM token WHERE book_id=1 AND chapter=1 AND verse=2 "
                "ORDER BY tree_leaf_ordinal",
            )]
        self.assertLess(traversal.index("MAT 1:2!6"), traversal.index("MAT 1:2!5"))

    def test_exact_jesus_occurrence(self) -> None:
        token = query.get_token(_LOCAL_DATABASE, "MAT 1:1!3")
        assert token is not None
        self.assertEqual((token.ref, token.surface, token.lemma, token.case, token.gender, token.type,
                          token.strong_number),
                         ("MAT 1:1!3", "\u1f38\u03b7\u03c3\u03bf\u1fe6", "\u1f38\u03b7\u03c3\u03bf\u1fe6\u03c2",
                          "Genitive", "Masculine", "Proper", "2424"))
        verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 1)
        assert verse is not None
        self.assertEqual(token, verse.tokens[2])

    def test_not_found(self) -> None:
        self.assertIsNone(query.get_verse(_LOCAL_DATABASE, "MAT", 99, 99))
        self.assertIsNone(query.get_token(_LOCAL_DATABASE, "MAT 1:1!999"))


if __name__ == "__main__":
    unittest.main()
