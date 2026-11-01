from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

from scripts import source_schema as schema
from scripts import verify_unit1 as unit1
from scripts.occurrence_locator import SCHEME, SCHEME_VERSION, encode_locator


XML_NS = "http://www.w3.org/XML/1998/namespace"
NODE_FIELDS = {
    "nodeId": "upstream_node_id", "Id": "id_raw", "Cat": "cat", "Rule": "rule",
    "ClType": "cl_type", "Start": "start_raw", "End": "end_raw", "Head": "head_raw", "Length": "length_raw",
}
TOKEN_FIELDS = {
    "xml:id": "xml_id", "morphId": "morph_id", "ref": "ref_raw", "Unicode": "unicode_raw",
    "NormalizedForm": "normalized_form", "UnicodeLemma": "unicode_lemma", "Language": "language_raw",
    "Case": "case_raw", "Gender": "gender_raw", "Number": "number_raw", "Person": "person_raw",
    "Tense": "tense_raw", "Voice": "voice_raw", "Mood": "mood_raw", "Type": "type_raw",
    "Degree": "degree_raw", "HasDet": "has_det_raw", "FunctionalTag": "functional_tag",
    "FormalTag": "formal_tag", "StrongNumber": "strong_number", "English": "english",
    "Mandarin": "mandarin", "Gloss": "gloss", "LexDomain": "lex_domain_raw", "LN": "ln_raw",
    "Frame": "frame_raw", "Ref": "referent_raw", "SubjRef": "subject_referent_raw",
    "Notes": "notes_raw", "LowfatException": "lowfat_exception_raw", "status": "status_raw",
}


def tag(name: str, attributes: dict[str, str], content: str) -> str:
    return "<" + name + "".join(f" {key}={quoteattr(value)}" for key, value in attributes.items()) + ">" + content + f"</{name}>"


class SchemaFixture:
    """Manual SQL fixtures, not an XML-to-store processor."""

    def __init__(self, connection: sqlite3.Connection, offset: int = 0) -> None:
        self.db = connection
        self.offset = offset
        self.next_element = offset + 1

    def insert(self, table: str, values: dict[str, object]) -> int:
        columns = ", ".join(values)
        parameters = ", ".join("?" for _ in values)
        cursor = self.db.execute(f"INSERT INTO {table} ({columns}) VALUES ({parameters})", tuple(values.values()))
        if cursor.lastrowid is None:
            raise AssertionError("fixture insert requires an integer row ID")
        return cursor.lastrowid

    def archive(self, raw: bytes = b"<r/>", number: int = 1) -> tuple[int, int]:
        snapshot = self.offset + number
        self.insert("dataset_snapshot", {
            "snapshot_id": snapshot, "source_family": "MACULA Greek", "edition": "SBLGNT",
            "repository_uri": "urn:unit2-synthetic-schema-test", "revision": f"{number:x}" * 40,
            "manifest_sha256": hashlib.sha256(raw).hexdigest().upper(),
        })
        self.insert("book", {"book_id": snapshot, "snapshot_id": snapshot, "source_book_code": "MAT", "book_ordinal": 1})
        self.insert("source_file", {
            "file_id": snapshot, "snapshot_id": snapshot, "book_id": snapshot,
            "relative_path": "fixtures/synthetic.xml", "source_format": "schema-test-xml",
            "original_bytes": raw, "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "byte_size": len(raw), "encoding_evidence": "Synthetic fixture encoded as UTF-8.",
        })
        return snapshot, snapshot

    def element(
        self, file_id: int, parent: int | None, name: str,
        namespace: str = "", prefix: str = "",
    ) -> int:
        siblings = self.db.execute(
            "SELECT namespace_uri, local_name FROM xml_element WHERE file_id=? AND parent_element_id IS ?",
            (file_id, parent),
        ).fetchall()
        path: list[tuple[str, str, int]] = []
        if parent is not None:
            raw_path = self.db.execute("SELECT locator FROM xml_element WHERE element_id=?", (parent,)).fetchone()[0]
            path = [tuple(segment) for segment in json.loads(raw_path)]
        ordinal = 1 + sum((namespace, name) == sibling for sibling in siblings)
        path.append((namespace, name, ordinal))
        element_id = self.next_element
        self.next_element += 1
        self.insert("xml_element", {
            "element_id": element_id, "file_id": file_id, "parent_element_id": parent,
            "namespace_uri": namespace, "local_name": name, "qualified_name": (prefix + ":" if prefix else "") + name,
            "prefix": prefix, "sibling_ordinal": len(siblings), "locator_scheme": SCHEME,
            "locator_version": SCHEME_VERSION, "locator": encode_locator(path),
        })
        self.content(file_id, parent, "element", child=element_id)
        return element_id

    def content(
        self, file_id: int, owner: int | None, kind: str, value: str | None = None,
        child: int | None = None, target: str | None = None,
    ) -> int:
        ordinal = self.db.execute(
            "SELECT count(*) FROM xml_content WHERE file_id=? AND owner_element_id IS ?", (file_id, owner),
        ).fetchone()[0]
        return self.insert("xml_content", {
            "file_id": file_id, "owner_element_id": owner, "ordinal": ordinal, "kind": kind,
            "child_element_id": child, "value": value, "pi_target": target,
        })

    def attribute(self, element: int, name: str, value: str, namespace: str = "", prefix: str = "") -> int:
        ordinal = self.db.execute("SELECT count(*) FROM xml_attribute WHERE element_id=?", (element,)).fetchone()[0]
        return self.insert("xml_attribute", {
            "element_id": element, "ordinal": ordinal, "namespace_uri": namespace, "local_name": name,
            "qualified_name": (prefix + ":" if prefix else "") + name, "prefix": prefix, "value": value,
        })

    def attributes(self, element: int, attributes: dict[str, str]) -> None:
        for name, value in attributes.items():
            if name == "xml:id":
                self.attribute(element, "id", value, XML_NS, "xml")
            else:
                self.attribute(element, name, value)

    def node(self, tree: int, element: int, parent: int | None, ordinal: int, attributes: dict[str, str],
             overrides: dict[str, object] | None = None) -> int:
        values: dict[str, object] = {
            "tree_id": tree, "element_id": element, "parent_node_id": parent, "sibling_ordinal": ordinal,
            **{column: attributes.get(name) for name, column in NODE_FIELDS.items()},
        }
        values.update(overrides or {})
        return self.insert("syntax_node", values)

    def token(self, tree: int, book: int, node: int, text: str, attributes: dict[str, str],
              traversal: int = 0, canonical: int = 0, verse: int = 1, word: int = 1,
              overrides: dict[str, object] | None = None) -> int:
        values: dict[str, object] = {
            "tree_id": tree, "book_id": book, "node_id": node, "source_direct_text": text,
            "tree_leaf_ordinal": traversal, "canonical_ordinal": canonical, "chapter": 1,
            "verse": verse, "verse_token_ordinal": word,
            **{column: attributes.get(name) for name, column in TOKEN_FIELDS.items()},
        }
        values.update(overrides or {})
        return self.insert("token", values)

    def memberships(self) -> None:
        self.db.execute(
            "INSERT INTO node_token_membership SELECT e.* FROM expected_node_token_membership e "
            "WHERE NOT EXISTS(SELECT 1 FROM node_token_membership m WHERE m.node_id=e.node_id AND m.token_id=e.token_id)",
        )

    def model(self, text: str = "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.",
              extras: dict[str, str] | None = None, node_overrides: dict[str, object] | None = None,
              token_overrides: dict[str, object] | None = None, archive_number: int = 1) -> dict[str, int]:
        root_attributes = {"Cat": "S", "Head": "0", "nodeId": "root:0001", "Length": "1"}
        clause_attributes = {"Cat": "CL", "Rule": "P2CL", "ClType": "Verbless", "Start": "0", "End": "0"}
        attributes = {
            "Id": "leaf.001", "Cat": "noun", "nodeId": "00000001", "xml:id": "n00000001",
            "morphId": "00000001", "ref": "MAT 1:1!1", "Unicode": text, "NormalizedForm": text.rstrip("."),
            "UnicodeLemma": "source-lemma", "FunctionalTag": "N-GSM", "FormalTag": "N-PRI",
        }
        attributes.update(extras or {})
        leaf_xml = tag("Node", attributes, escape(text))
        raw = tag("Sentences", {}, tag("Sentence", {"ref": "MAT 1:1!1-1:1!1"},
              tag("Trees", {}, tag("Tree", {}, tag("Node", root_attributes,
                  tag("Node", clause_attributes, leaf_xml)))))).encode("utf-8")
        file_id, book_id = self.archive(raw, archive_number)
        document = self.element(file_id, None, "Sentences")
        sentence_element = self.element(file_id, document, "Sentence")
        self.attribute(sentence_element, "ref", "MAT 1:1!1-1:1!1")
        sentence = self.insert("sentence", {"file_id": file_id, "book_id": book_id, "element_id": sentence_element,
                                          "ordinal": 0, "ref_raw": "MAT 1:1!1-1:1!1"})
        wrapper = self.element(file_id, sentence_element, "Trees")
        tree_element = self.element(file_id, wrapper, "Tree")
        tree = self.insert("tree", {"sentence_id": sentence, "element_id": tree_element, "ordinal": 0})
        root_element = self.element(file_id, tree_element, "Node")
        self.attributes(root_element, root_attributes)
        root_node = self.node(tree, root_element, None, 0, root_attributes)
        clause_element = self.element(file_id, root_element, "Node")
        self.attributes(clause_element, clause_attributes)
        clause_node = self.node(tree, clause_element, root_node, 0, clause_attributes, node_overrides)
        leaf = self.element(file_id, clause_element, "Node")
        self.attributes(leaf, attributes)
        self.content(file_id, leaf, "text", text)
        leaf_node = self.node(tree, leaf, clause_node, 0, attributes)
        token = self.token(tree, book_id, leaf_node, text, attributes, overrides=token_overrides)
        self.memberships()
        return {"file": file_id, "book": book_id, "document": document, "sentence": sentence, "tree": tree,
                "root": root_node, "clause": clause_node, "leaf": leaf, "leaf_node": leaf_node, "token": token}


class Unit2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH))
        cls.document = ET.fromstring(cls.raw)

    def setUp(self) -> None:
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        schema.bootstrap(self.db)
        self.fixture = SchemaFixture(self.db)

    def test_empty_bootstrap_version_tables_and_foreign_keys(self) -> None:
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone(), (1,))
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (1,))
        actual = {r[0] for r in self.db.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
        self.assertEqual(actual, schema.TABLES)
        for table in actual:
            with self.subTest(table=table):
                info = self.db.execute(f"PRAGMA table_info({table})").fetchall()
                self.assertTrue(any(column[5] > 0 for column in info))
                if table not in ("dataset_snapshot", "schema_version"):
                    self.assertTrue(self.db.execute(f"PRAGMA foreign_key_list({table})").fetchall())

    def test_ddl_is_executable_without_python_functions(self) -> None:
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.executescript(schema.DDL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone(), (1,))
        self.assertEqual(len(db.execute("SELECT name FROM sqlite_schema WHERE type='table'").fetchall()), 12)

    def test_repeat_bootstrap_fails_without_mutation(self) -> None:
        before = list(self.db.iterdump())
        self.db.commit()
        with self.assertRaisesRegex(schema.SchemaError, "already initialized"):
            schema.bootstrap(self.db)
        self.assertEqual(before, list(self.db.iterdump()))

    def test_unknown_database_and_unknown_version_fail_closed(self) -> None:
        for setup in ("CREATE TABLE unrelated(v TEXT)", "CREATE TABLE sqliteXuser(v TEXT)", "PRAGMA user_version=42"):
            with self.subTest(setup=setup):
                db = sqlite3.connect(":memory:")
                try:
                    db.execute(setup)
                    before = list(db.iterdump())
                    with self.assertRaisesRegex(schema.SchemaError, "version mismatch"):
                        schema.bootstrap(db)
                    self.assertEqual(before, list(db.iterdump()))
                finally:
                    db.close()

    def test_active_transaction_rejected(self) -> None:
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.execute("BEGIN")
        with self.assertRaisesRegex(schema.SchemaError, "active transaction"):
            schema.bootstrap(db)
        self.assertTrue(db.in_transaction)
        self.assertFalse(db.execute("SELECT name FROM sqlite_schema").fetchall())

    def test_failed_ddl_rolls_back_all_schema_objects(self) -> None:
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        bad = "CREATE TABLE partial(v TEXT); INVALID SQL;"
        with patch.object(schema, "DDL_PATH") as path:
            path.read_text.return_value = bad
            with self.assertRaisesRegex(schema.SchemaError, "rolled back"):
                schema.bootstrap(db)
        self.assertFalse(db.in_transaction)
        self.assertFalse(db.execute("SELECT name FROM sqlite_schema").fetchall())
        self.assertEqual(db.execute("PRAGMA user_version").fetchone(), (0,))

    def test_version_persists_in_temporary_empty_database(self) -> None:
        with TemporaryDirectory(prefix="unit2-schema-test-", dir=schema.PROJECT_ROOT) as temporary:
            path = Path(temporary) / "schema-test.sqlite3"
            db = sqlite3.connect(path)
            schema.bootstrap(db)
            db.close()
            db = sqlite3.connect(path)
            try:
                with self.assertRaisesRegex(schema.SchemaError, "foreign keys must be ON"):
                    schema.validate_store(db)
                db.execute("PRAGMA foreign_keys=ON")
                db.execute("PRAGMA recursive_triggers=ON")
                schema.validate_store(db)
                self.assertEqual(db.execute("PRAGMA user_version").fetchone(), (1,))
            finally:
                db.close()

    def test_schema_identity_drift_rejected(self) -> None:
        self.db.execute("PRAGMA user_version=2")
        with self.assertRaisesRegex(schema.SchemaError, "version mismatch"):
            schema.validate_store(self.db)

    def test_source_archive_blob_checksum_and_immutability(self) -> None:
        raw = b"\xef\xbb\xbf<r>\xce\xb1\xf0\x9f\x98\x80</r>\r\n"
        file_id, _ = self.fixture.archive(raw)
        row = self.db.execute("SELECT original_bytes, sha256, byte_size, typeof(original_bytes) FROM source_file").fetchone()
        self.assertEqual(row, (raw, hashlib.sha256(raw).hexdigest().upper(), len(raw), "blob"))
        schema.validate_store(self.db)
        for sql in ("UPDATE source_file SET encoding_evidence='changed'", "DELETE FROM source_file",
                    "UPDATE dataset_snapshot SET edition='other'", "DELETE FROM dataset_snapshot"):
            with self.subTest(sql=sql):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
                    self.db.execute(sql)
        self.assertEqual(file_id, 1)

    def test_wrong_byte_size_blob_type_and_checksum_rejected(self) -> None:
        for change in ({"byte_size": 999}, {"original_bytes": "not bytes"}, {"sha256": "not-a-hash"}):
            with self.subTest(change=change):
                self.fixture.archive()
                source = dict(zip(
                    [d[0] for d in self.db.execute("SELECT * FROM source_file").description],
                    self.db.execute("SELECT * FROM source_file").fetchone(),
                ))
                source.update({"file_id": 2, "relative_path": "fixtures/other.xml", **change})
                with self.assertRaises(sqlite3.IntegrityError):
                    self.fixture.insert("source_file", source)
                self.db.rollback()

    def test_valid_shaped_but_incorrect_checksum_fails_validation(self) -> None:
        self.fixture.archive()
        self.db.execute(
            "INSERT INTO source_file(file_id,snapshot_id,relative_path,source_format,original_bytes,sha256,byte_size) "
            "VALUES(2,1,'other.xml','xml',?, ?,4)", (b"<x/>", "0" * 64),
        )
        with self.assertRaisesRegex(schema.SchemaError, "BLOB checksum mismatch"):
            schema.validate_store(self.db)

    def test_complete_manual_core_validates(self) -> None:
        self.fixture.model()
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT count(*) FROM syntax_node").fetchone(), (3,))
        self.assertEqual(self.db.execute("SELECT count(*) FROM node_token_membership").fetchone(), (3,))

    def test_absent_empty_ref_ref_ids_and_dual_tags(self) -> None:
        ids = self.fixture.model(extras={"English": "", "Ref": "n00000000000", "SubjRef": "not-loaded-target"})
        schema.validate_store(self.db)
        attributes = dict(self.db.execute(
            "SELECT local_name,value FROM xml_attribute WHERE element_id=? AND namespace_uri=''", (ids["leaf"],),
        ))
        self.assertEqual(attributes["English"], "")
        self.assertNotIn("Notes", attributes)
        self.assertEqual(attributes["ref"], "MAT 1:1!1")
        self.assertEqual(attributes["Ref"], "n00000000000")
        self.assertNotEqual(attributes["Id"], attributes["nodeId"])
        token = self.db.execute(
            "SELECT xml_id,morph_id,functional_tag,formal_tag,english,notes_raw,referent_raw,subject_referent_raw FROM token",
        ).fetchone()
        self.assertEqual(token, ("n00000001", "00000001", "N-GSM", "N-PRI", "", None, "n00000000000", "not-loaded-target"))
        self.assertEqual(self.db.execute(
            "SELECT namespace_uri,local_name,qualified_name,prefix FROM xml_attribute WHERE namespace_uri=?", (XML_NS,),
        ).fetchone(), (XML_NS, "id", "xml:id", "xml"))
        self.assertEqual(self.db.execute("SELECT typeof(upstream_node_id),typeof(id_raw) FROM syntax_node WHERE node_id=?",
                                        (ids["leaf_node"],)).fetchone(), ("text", "text"))

    def test_all_source_enrichment_mirrors_remain_raw(self) -> None:
        extras = {name: "raw:" + name for name in TOKEN_FIELDS if name not in (
            "xml:id", "morphId", "ref", "Unicode", "NormalizedForm", "UnicodeLemma", "FunctionalTag", "FormalTag",
        )}
        extras.update({"Frame": "A1:not-loaded;A1:n00000000000;AA2:other", "Mandarin": "\u8c31",
                       "LexDomain": "010002 033003", "LN": "93.169a"})
        self.fixture.model(extras=extras)
        schema.validate_store(self.db)
        for name, column in TOKEN_FIELDS.items():
            with self.subTest(name=name):
                mirror = self.db.execute(f"SELECT {column} FROM token").fetchone()[0]
                if name in extras:
                    self.assertEqual(mirror, extras[name])

    def test_nullable_head_start_end_length_no_inferred_defaults(self) -> None:
        ids = self.fixture.model()
        schema.validate_store(self.db)
        root = self.db.execute("SELECT start_raw,end_raw,head_raw,length_raw,id_raw,rule FROM syntax_node WHERE node_id=?",
                               (ids["root"],)).fetchone()
        leaf = self.db.execute("SELECT head_raw,length_raw FROM syntax_node WHERE node_id=?", (ids["leaf_node"],)).fetchone()
        self.assertEqual(root, (None, None, "0", "1", None, None))
        self.assertEqual(leaf, (None, None))

    def test_typed_attribute_wrong_value_and_absent_placeholder_rejected(self) -> None:
        self.fixture.model(node_overrides={"cl_type": "VerbElided"})
        with self.assertRaisesRegex(schema.SchemaError, "typed/source attribute mismatch"):
            schema.validate_store(self.db)

    def test_missing_typed_value_for_present_empty_attribute_rejected(self) -> None:
        self.fixture.model(extras={"English": ""}, token_overrides={"english": None})
        with self.assertRaisesRegex(schema.SchemaError, "typed/source attribute mismatch"):
            schema.validate_store(self.db)

    def test_invented_absent_typed_attribute_rejected(self) -> None:
        self.fixture.model(token_overrides={"notes_raw": ""})
        with self.assertRaisesRegex(schema.SchemaError, "typed/source attribute mismatch"):
            schema.validate_store(self.db)

    def test_direct_text_unicode_normalized_and_combining_forms_distinct(self) -> None:
        text = "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc."
        self.fixture.model(text=text, extras={"Unicode": "independent surface", "NormalizedForm": text[:-1],
                                            "UnicodeLemma": "\u03b1\u0301"})
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT source_direct_text,unicode_raw,normalized_form,unicode_lemma FROM token").fetchone(),
                         (text, "independent surface", text[:-1], "\u03b1\u0301"))
        self.assertNotEqual("\u03b1\u0301", "\u03ac")

    def test_text_substitution_is_rejected(self) -> None:
        self.fixture.model(token_overrides={"source_direct_text": "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc"})
        with self.assertRaisesRegex(schema.SchemaError, "typed direct text mismatch"):
            schema.validate_store(self.db)

    def test_genuine_single_character_greek_from_live_fixed_matthew(self) -> None:
        leaf = next(n for n in self.document.iter("Node") if n.attrib.get("ref") == "MAT 1:16!13")
        self.assertEqual(leaf.attrib[unit1.XML_ID], "n40001016013")
        self.assertEqual(leaf.text, "\u1f41")
        if leaf.text is None:
            self.fail("real single-character token text is missing")
        self.assertEqual(len(leaf.text), 1)
        self.fixture.model(text=leaf.text, extras={"Unicode": leaf.attrib["Unicode"]})
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT source_direct_text,unicode_raw,length(source_direct_text) FROM token").fetchone(),
                         ("\u1f41", "\u1f41", 1))

    def test_namespace_alias_duplicates_and_binary_case(self) -> None:
        file_id, _ = self.fixture.archive()
        element = self.fixture.element(file_id, None, "r", "urn:root", "p")
        self.fixture.attribute(element, "ref", "a")
        self.fixture.attribute(element, "Ref", "b")
        self.fixture.attribute(element, "x", "1", "urn:u", "p")
        self.fixture.attribute(element, "x", "2", "urn:v", "q")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.attribute(element, "x", "duplicate", "urn:u", "q")
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT value FROM xml_attribute WHERE local_name='ref'").fetchall(), [("a",)])
        self.assertEqual(self.db.execute("SELECT value FROM xml_attribute WHERE local_name='Ref'").fetchall(), [("b",)])

    def test_namespace_ordinal_locator_prefix_independence_and_repeated_siblings(self) -> None:
        file_id, _ = self.fixture.archive()
        root = self.fixture.element(file_id, None, "r")
        a = self.fixture.element(file_id, root, "x", "urn:u", "p")
        b = self.fixture.element(file_id, root, "other")
        c = self.fixture.element(file_id, root, "x", "urn:u", "q")
        d = self.fixture.element(file_id, root, "x", "urn:v", "p")
        schema.validate_store(self.db)
        locators = dict(self.db.execute("SELECT element_id,locator FROM xml_element"))
        self.assertEqual(locators[a], '[["","r",1],["urn:u","x",1]]')
        self.assertEqual(locators[c], '[["","r",1],["urn:u","x",2]]')
        self.assertEqual(locators[d], '[["","r",1],["urn:v","x",1]]')
        self.assertNotEqual(locators[a], locators[b])

    def test_locator_handles_delimiters_and_unicode_without_normalizing(self) -> None:
        segments = [("urn:x/{[1]}:\u03b1", "\u03b1\u0301", 1)]
        locator = encode_locator(segments)
        self.assertTrue(locator.isascii())
        self.assertEqual(json.loads(locator), [["urn:x/{[1]}:\u03b1", "\u03b1\u0301", 1]])
        self.assertNotEqual(locator, encode_locator([("urn:x/{[1]}:\u03b1", "\u03ac", 1)]))
        for bad in ([], [("", "", 1)], [("", "x", 0)], [("", "x", True)], [("", "x", 2)]):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    encode_locator(bad)

    def test_duplicate_locator_and_sibling_ordinal_rejected(self) -> None:
        file_id, _ = self.fixture.archive()
        root = self.fixture.element(file_id, None, "r")
        child = self.fixture.element(file_id, root, "x")
        columns = [d[0] for d in self.db.execute("SELECT * FROM xml_element").description]
        values = dict(zip(columns, self.db.execute("SELECT * FROM xml_element WHERE element_id=?", (child,)).fetchone()))
        for change in ({"element_id": 100, "sibling_ordinal": 1}, {"element_id": 101, "locator": '[["","r",1],["","x",2]]'}):
            with self.subTest(change=change):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.fixture.insert("xml_element", {**values, **change})

    def test_noncanonical_locator_rejected_by_completed_store_validation(self) -> None:
        file_id, _ = self.fixture.archive()
        self.fixture.insert("xml_element", {
            "file_id": file_id, "namespace_uri": "", "local_name": "r", "sibling_ordinal": 0,
            "locator_scheme": SCHEME, "locator_version": 1, "locator": '[ ["", "r", 1] ]',
        })
        with self.assertRaisesRegex(schema.SchemaError, "non-canonical"):
            schema.validate_store(self.db)

    def test_source_scoped_key_independent_of_database_pk_and_snapshot_ids_not_collapsed(self) -> None:
        ids = self.fixture.model()
        other = sqlite3.connect(":memory:")
        self.addCleanup(other.close)
        schema.bootstrap(other)
        other_ids = SchemaFixture(other, 100).model()
        self.assertNotEqual(ids["leaf"], other_ids["leaf"])
        self.assertEqual(schema.source_occurrence_key(self.db, ids["leaf"]),
                         schema.source_occurrence_key(other, other_ids["leaf"]))
        schema.validate_store(other)
        second_file, second_book = self.fixture.archive(number=2)
        other_root = self.fixture.element(second_file, None, "Sentences")
        self.assertNotEqual(schema.source_occurrence_key(self.db, ids["document"]),
                            schema.source_occurrence_key(self.db, other_root))
        self.assertEqual(second_book, second_file)

    def test_cross_snapshot_upstream_identifiers_not_globally_unique(self) -> None:
        self.fixture.model()
        second = SchemaFixture(self.db, 100)
        second_ids = second.model(archive_number=2)
        self.assertEqual(self.db.execute("SELECT xml_id FROM token ORDER BY token_id").fetchall(),
                         [("n00000001",), ("n00000001",)])
        self.assertEqual(self.db.execute("SELECT morph_id FROM token ORDER BY token_id").fetchall(),
                         [("00000001",), ("00000001",)])
        self.assertEqual(self.db.execute("SELECT count(*) FROM syntax_node WHERE upstream_node_id='00000001'").fetchone(), (2,))
        self.assertEqual(second_ids["book"], 102)
        schema.validate_store(self.db)

    def test_matthew_boundary_dual_orders_and_discontinuous_exact_membership(self) -> None:
        source_leaves = {
            int(n.attrib["ref"].rsplit("!", 1)[1]): n for n in unit1.leaf_nodes(self.document)
            if n.attrib["ref"].startswith("MAT 1:2!")
        }
        target = next(n for n in self.document.iter("Node") if n.attrib.get("nodeId") == "400010020050040")
        self.assertEqual([n.attrib["ref"] for n in unit1.leaf_nodes(target)],
                         ["MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9"])
        leaf_attributes = {
            word: {("xml:id" if key == unit1.XML_ID else key): value for key, value in source_leaves[word].attrib.items()}
            for word in (6, 5, 7, 8, 9)
        }
        leaf_text: dict[int, str] = {}
        for word, node in source_leaves.items():
            if node.text is None:
                self.fail("real boundary leaf text missing")
            leaf_text[word] = node.text
        leaf_xml = {
            word: tag("Node", attrs, escape(leaf_text[word]))
            for word, attrs in leaf_attributes.items()
        }
        root_attributes = {"Cat": "S", "nodeId": "fixture:reduced-boundary-root"}
        raw = tag("Sentences", {}, tag("Sentence", {"ref": "MAT 1:2!1-1:6!7"}, tag("Trees", {}, tag("Tree", {},
              tag("Node", root_attributes, leaf_xml[6] + tag("Node", target.attrib,
                  "".join(leaf_xml[word] for word in (5, 7, 8, 9)))))))).encode("utf-8")
        file_id, book_id = self.fixture.archive(raw)
        document = self.fixture.element(file_id, None, "Sentences")
        sentence_element = self.fixture.element(file_id, document, "Sentence")
        self.fixture.attribute(sentence_element, "ref", "MAT 1:2!1-1:6!7")
        sentence = self.fixture.insert("sentence", {"file_id": file_id, "book_id": book_id, "element_id": sentence_element,
                                                  "ordinal": 0, "ref_raw": "MAT 1:2!1-1:6!7"})
        wrapper = self.fixture.element(file_id, sentence_element, "Trees")
        tree_element = self.fixture.element(file_id, wrapper, "Tree")
        tree = self.fixture.insert("tree", {"sentence_id": sentence, "element_id": tree_element, "ordinal": 0})
        root_element = self.fixture.element(file_id, tree_element, "Node")
        self.fixture.attributes(root_element, root_attributes)
        root = self.fixture.node(tree, root_element, None, 0, root_attributes)
        first_element = self.fixture.element(file_id, root_element, "Node")
        self.fixture.attributes(first_element, leaf_attributes[6])
        self.fixture.content(file_id, first_element, "text", leaf_text[6])
        first_node = self.fixture.node(tree, first_element, root, 0, leaf_attributes[6])
        first_token = self.fixture.token(tree, book_id, first_node, leaf_text[6],
                                         leaf_attributes[6], traversal=0, canonical=1, verse=2, word=6)
        target_element = self.fixture.element(file_id, root_element, "Node")
        self.fixture.attributes(target_element, target.attrib)
        target_node = self.fixture.node(tree, target_element, root, 1, target.attrib)
        for ordinal, word in enumerate((5, 7, 8, 9)):
            element = self.fixture.element(file_id, target_element, "Node")
            attributes = leaf_attributes[word]
            self.fixture.attributes(element, attributes)
            text = source_leaves[word].text
            if text is None:
                self.fail("real boundary leaf text missing")
            self.fixture.content(file_id, element, "text", text)
            node = self.fixture.node(tree, element, target_node, ordinal, attributes)
            self.fixture.token(tree, book_id, node, text, attributes, traversal=ordinal + 1,
                               canonical=word - 5, verse=2, word=word)
        self.fixture.memberships()
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT verse_token_ordinal FROM token ORDER BY tree_leaf_ordinal").fetchall(),
                         [(6,), (5,), (7,), (8,), (9,)])
        self.assertEqual(self.db.execute("SELECT verse_token_ordinal FROM token ORDER BY canonical_ordinal").fetchall(),
                         [(5,), (6,), (7,), (8,), (9,)])
        members = self.db.execute(
            "SELECT t.verse_token_ordinal FROM node_token_membership m JOIN token t USING(token_id) "
            "WHERE m.node_id=? ORDER BY t.canonical_ordinal", (target_node,),
        ).fetchall()
        self.assertEqual(members, [(5,), (7,), (8,), (9,)])
        self.assertEqual(self.db.execute("SELECT start_raw,end_raw FROM syntax_node WHERE node_id=?",
                                        (target_node,)).fetchone(), ("5", "8"))
        self.assertEqual(self.db.execute("SELECT start_raw FROM syntax_node WHERE node_id=?", (first_node,)).fetchone(), ("4",))
        with self.assertRaisesRegex(sqlite3.IntegrityError, "actual descendant"):
            self.db.execute("INSERT INTO node_token_membership VALUES(?,?,?)", (target_node, first_token, tree))

    def test_bootstrap_logical_identity_is_deterministic(self) -> None:
        other = sqlite3.connect(":memory:")
        self.addCleanup(other.close)
        schema.bootstrap(other)
        self.assertEqual(list(self.db.iterdump()), list(other.iterdump()))

    def test_attribute_ordinal_and_namespace_qname_evidence_constraints(self) -> None:
        file_id, _ = self.fixture.archive()
        root = self.fixture.element(file_id, None, "r")
        self.fixture.attribute(root, "a", "")
        for values in (
            {"ordinal": 0, "namespace_uri": "", "local_name": "b", "value": ""},
            {"ordinal": 1, "namespace_uri": "", "local_name": "c", "qualified_name": "wrong", "prefix": "", "value": ""},
        ):
            with self.subTest(values=values):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.fixture.insert("xml_attribute", {"element_id": root, **values})

    def test_membership_cross_tree_foreign_keys_rejected(self) -> None:
        first = self.fixture.model()
        second = SchemaFixture(self.db, 100).model(archive_number=2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO node_token_membership VALUES(?,?,?)",
                            (first["root"], second["token"], first["tree"]))

    def test_unknown_occurrence_key_fails_explicitly(self) -> None:
        with self.assertRaisesRegex(schema.SchemaError, "unknown source occurrence"):
            schema.source_occurrence_key(self.db, 9999)

    def test_ordered_mixed_content_document_pi_cdata_comments_whitespace(self) -> None:
        file_id, _ = self.fixture.archive(b'<?p x?><r> \n<![CDATA[\xce\xb1]]><!--c--><?q ?></r>')
        self.fixture.content(file_id, None, "pi", "x", target="p")
        root = self.fixture.element(file_id, None, "r")
        self.fixture.content(file_id, root, "text", " \n")
        self.fixture.content(file_id, root, "cdata", "\u03b1")
        self.fixture.content(file_id, root, "comment", "c")
        self.fixture.content(file_id, root, "pi", "", target="q")
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute(
            "SELECT ordinal,kind,value FROM xml_content WHERE owner_element_id=? ORDER BY ordinal", (root,),
        ).fetchall(), [(0, "text", " \n"), (1, "cdata", "\u03b1"), (2, "comment", "c"), (3, "pi", "")])

    def test_invalid_content_payloads_duplicate_ordinals_and_noncanonical_segmentation(self) -> None:
        file_id, _ = self.fixture.archive()
        root = self.fixture.element(file_id, None, "r")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.content(file_id, root, "pi", "data")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.content(file_id, None, "cdata", "outside root")
        self.fixture.content(file_id, root, "text", "a")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.insert("xml_content", {"file_id": file_id, "owner_element_id": root, "ordinal": 0, "kind": "text", "value": "b"})
        self.fixture.content(file_id, root, "text", "b")
        with self.assertRaisesRegex(schema.SchemaError, "segmentation"):
            schema.validate_store(self.db)

    def test_invalid_foreign_keys_and_cross_file_parent_rejected(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.insert("book", {"snapshot_id": 9999, "source_book_code": "MAT", "book_ordinal": 1})
        first_file, _ = self.fixture.archive()
        root = self.fixture.element(first_file, None, "r")
        second_file, _ = self.fixture.archive(number=2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.element(second_file, root, "x")

    def test_typed_parent_scope_mismatch_is_diagnosed(self) -> None:
        self.fixture.model(node_overrides={"parent_node_id": None, "sibling_ordinal": 1})
        with self.assertRaisesRegex(schema.SchemaError, "syntax parent mismatch"):
            schema.validate_store(self.db)

    def test_scripture_coordinate_mismatch_is_diagnosed(self) -> None:
        self.fixture.model(token_overrides={"verse_token_ordinal": 2})
        with self.assertRaisesRegex(schema.SchemaError, "coordinates differ"):
            schema.validate_store(self.db)

    def test_membership_missing_row_and_wrong_ancestry_rejected(self) -> None:
        ids = self.fixture.model()
        self.db.execute("DELETE FROM node_token_membership WHERE node_id=?", (ids["clause"],))
        with self.assertRaisesRegex(schema.SchemaError, "incomplete/incorrect"):
            schema.validate_store(self.db)
        with self.assertRaisesRegex(sqlite3.IntegrityError, "descendant leaf"):
            self.db.execute("INSERT INTO node_token_membership VALUES(9999,?,?)", (ids["token"], ids["tree"]))
        self.db.execute("INSERT INTO node_token_membership SELECT * FROM expected_node_token_membership WHERE node_id=?",
                        (ids["clause"],))
        schema.validate_store(self.db)

    def test_no_physical_mapper_or_semantic_entities(self) -> None:
        fields = {r[1] for r in self.db.execute("PRAGMA table_info(xml_element)")}
        self.assertIn("diagnostic_line", fields)
        self.assertNotIn("byte_offset", fields)
        self.assertNotIn("utf16_offset", fields)
        self.assertFalse(schema.TABLES.intersection({"actor", "action", "patient", "event", "result", "projection"}))
        parser = unit1.load_json(schema.PARSER_PATH)
        self.assertFalse(parser["production_parser_implemented"])
        self.assertFalse(parser["xmlpro_dependency"])

    def test_unsafe_parser_contract_is_rejected_before_schema_writes(self) -> None:
        original = unit1.load_json(schema.PARSER_PATH)
        locator = unit1.load_json(schema.LOCATOR_PATH)
        mutations = [("settings", "DtdProcessing", "Parse"), ("settings", "XmlResolver", "resolver"),
                     ("input", "external_acquisition", True), ("input", "implicit_xinclude", True),
                     ("values", "application_trim", True), ("values", "text_substitution", True)]
        for section, key, value in mutations:
            with self.subTest(section=section, key=key):
                parser = deepcopy(original)
                unit1.object_value(parser[section], section)[key] = value
                db = sqlite3.connect(":memory:")
                try:
                    with patch.object(schema, "load_json", side_effect=[parser, locator]):
                        with self.assertRaises(schema.SchemaError):
                            schema.bootstrap(db)
                    self.assertFalse(db.execute("SELECT name FROM sqlite_schema").fetchall())
                finally:
                    db.close()

    def test_temp_shadow_and_attached_databases_fail_closed(self) -> None:
        for setup in ("CREATE TEMP TABLE schema_version(v TEXT)", "ATTACH ':memory:' AS other"):
            with self.subTest(setup=setup):
                db = sqlite3.connect(":memory:")
                try:
                    db.execute(setup)
                    with self.assertRaises(schema.SchemaError):
                        schema.bootstrap(db)
                    self.assertFalse(db.execute("SELECT name FROM main.sqlite_schema").fetchall())
                finally:
                    db.close()

    def test_dropped_immutability_trigger_is_detected(self) -> None:
        self.db.execute("DROP TRIGGER attribute_no_update")
        with self.assertRaisesRegex(schema.SchemaError, "actual SQL schema objects"):
            schema.validate_store(self.db)

    def test_adjacent_cdata_sections_remain_separate_content_occurrences(self) -> None:
        file_id, _ = self.fixture.archive(b"<r><![CDATA[a]]><![CDATA[b]]></r>")
        root = self.fixture.element(file_id, None, "r")
        self.fixture.content(file_id, root, "cdata", "a")
        self.fixture.content(file_id, root, "cdata", "b")
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT ordinal,value FROM xml_content WHERE kind='cdata' ORDER BY ordinal").fetchall(),
                         [(0, "a"), (1, "b")])

    def test_missing_typed_node_occurrence_cannot_pass_completed_validation(self) -> None:
        ids = self.fixture.model()
        root_element = self.db.execute("SELECT element_id FROM syntax_node WHERE node_id=?", (ids["root"],)).fetchone()[0]
        self.fixture.element(ids["file"], root_element, "Node")
        with self.assertRaisesRegex(schema.SchemaError, "typed syntax node occurrence"):
            schema.validate_store(self.db)

    def test_typed_token_book_scope_mismatch_is_diagnosed(self) -> None:
        self.fixture.archive(number=2)
        self.fixture.model(token_overrides={"book_id": 2})
        with self.assertRaisesRegex(schema.SchemaError, "book/snapshot scope"):
            schema.validate_store(self.db)

    def test_replace_cannot_bypass_source_immutability(self) -> None:
        ids = self.fixture.model()
        old = self.db.execute("SELECT original_bytes FROM source_file").fetchone()[0]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
            self.db.execute(
                "INSERT OR REPLACE INTO source_file "
                "SELECT file_id,snapshot_id,book_id,relative_path,source_format,original_bytes,sha256,byte_size,'changed' FROM source_file",
            )
        with self.assertRaisesRegex(sqlite3.IntegrityError, "immutable"):
            self.db.execute(
                "INSERT OR REPLACE INTO xml_attribute "
                "SELECT attribute_id,element_id,ordinal,namespace_uri,local_name,qualified_name,prefix,'changed' "
                "FROM xml_attribute WHERE element_id=?", (ids["leaf"],),
            )
        self.assertEqual(self.db.execute("SELECT original_bytes FROM source_file").fetchone()[0], old)
        schema.validate_store(self.db)

    def test_recursive_trigger_profile_is_required_on_each_connection(self) -> None:
        self.db.execute("PRAGMA recursive_triggers=OFF")
        with self.assertRaisesRegex(schema.SchemaError, "recursive triggers must be ON"):
            schema.validate_store(self.db)

    def test_non_bmp_text_is_preserved_without_physical_offset_claims(self) -> None:
        text = "\u03b1\U0001f600\u03b2"
        self.fixture.model(text)
        schema.validate_store(self.db)
        self.assertEqual(self.db.execute("SELECT source_direct_text,length(source_direct_text) FROM token").fetchone(), (text, 3))

    def test_cli_failure_is_explicit_and_nonzero(self) -> None:
        errors = io.StringIO()
        with patch.object(schema, "bootstrap", side_effect=schema.SchemaError("schema conflict")):
            with redirect_stderr(errors):
                self.assertEqual(schema.main(), 1)
        self.assertIn("FAILED", errors.getvalue())
        self.assertIn("schema conflict", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
