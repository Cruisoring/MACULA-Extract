from dataclasses import FrozenInstanceError, asdict, fields
import hashlib
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from scripts import source_query as query
from scripts import source_schema as schema
from scripts import verify_unit1 as unit1
from tests.test_unit2 import SchemaFixture, tag


BOUNDARY = "400010020050040"
JESUS = "400010010030010"
NODE_OPERATIONS = (
    query.get_node, query.get_children, query.get_ancestors_by_node, query.get_members,
)
LOCAL_IDS = {"token_id", "book_id", "node_id", "tree_id", "element_id"}


class Unit5FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit5-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "syntax # fixture.sqlite3"
        self.db = self.make_store(self.path)

    def make_store(self, path: Path, offset: int = 0) -> sqlite3.Connection:
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        schema.bootstrap(db)
        fixture = SchemaFixture(db, offset)
        attrs = {
            "root:zz": {"Cat": "S"},
            "np:zz": {"Cat": "np", "Rule": "N2NP", "Id": ""},
            JESUS: {"Cat": "noun", "ref": "MAT 1:1!3", "xml:id": "n-synthetic",
                    "morphId": "m-synthetic", "UnicodeLemma": "source-lemma"},
            "connector": {"Cat": "conj", "ref": "MAT 1:2!6"},
            BOUNDARY: {"Cat": "CL", "Rule": "S-V-O", "Head": "1",
                       "Start": "5", "End": "8", "Length": "4"},
            "z-subject": {"Cat": "S"},
            "leaf-five": {"Cat": "noun", "ref": "MAT 1:2!5"},
            "a-verb": {"Cat": "V"},
            "leaf-seven": {"Cat": "verb", "ref": "MAT 1:2!7"},
            "m-object": {"Cat": "O"},
            "leaf-eight": {"Cat": "noun", "ref": "MAT 1:2!8"},
            "leaf-nine": {"Cat": "noun", "ref": "MAT 1:2!9"},
        }
        children = {
            "root:zz": ["np:zz", "connector", BOUNDARY],
            "np:zz": [JESUS],
            BOUNDARY: ["z-subject", "a-verb", "m-object"],
            "z-subject": ["leaf-five"],
            "a-verb": ["leaf-seven"],
            "m-object": ["leaf-eight", "leaf-nine"],
        }
        for identity, values in attrs.items():
            values["nodeId"] = identity
        node_ids = {identity: offset + 1000 - i * 10 for i, identity in enumerate(attrs)}
        texts = {identity: "source-" + values["ref"] for identity, values in attrs.items() if "ref" in values}

        def node_xml(identity: str) -> str:
            content = "".join(node_xml(child) for child in children.get(identity, []))
            return tag("Node", attrs[identity], content or escape(texts[identity]))

        ref = "MAT 1:1!3-1:2!9"
        raw = tag("Sentences", {}, tag("Sentence", {"ref": ref}, tag("Trees", {},
                  tag("Tree", {}, node_xml("root:zz"))))).encode()
        file_id, book_id = fixture.archive(raw)
        document = fixture.element(file_id, None, "Sentences")
        sentence_element = fixture.element(file_id, document, "Sentence")
        fixture.attribute(sentence_element, "ref", ref)
        sentence = fixture.insert("sentence", {
            "file_id": file_id, "book_id": book_id, "element_id": sentence_element,
            "ordinal": 0, "ref_raw": ref,
        })
        wrapper = fixture.element(file_id, sentence_element, "Trees")
        tree_element = fixture.element(file_id, wrapper, "Tree")
        tree = fixture.insert("tree", {
            "sentence_id": sentence, "element_id": tree_element, "ordinal": 0,
        })
        leaves = list(texts)
        canonical = sorted(leaves, key=lambda identity: (
            int(attrs[identity]["ref"].split(":")[1].split("!")[0]),
            int(attrs[identity]["ref"].split("!")[1]),
        ))

        def add_node(identity: str, parent_element: int, parent: int | None, ordinal: int) -> None:
            element = fixture.element(file_id, parent_element, "Node")
            fixture.attributes(element, attrs[identity])
            node = fixture.node(tree, element, parent, ordinal, attrs[identity],
                                {"node_id": node_ids[identity]})
            if identity in texts:
                traversal = leaves.index(identity)
                token_ref = attrs[identity]["ref"]
                verse, word = (int(value) for value in token_ref.split(":")[1].split("!"))
                fixture.content(file_id, element, "text", texts[identity])
                fixture.token(
                    tree, book_id, node, texts[identity], attrs[identity],
                    traversal=traversal, canonical=canonical.index(identity), verse=verse, word=word,
                    overrides={"token_id": offset + 10000 - traversal},
                )
            for sibling, child in enumerate(children.get(identity, [])):
                add_node(child, element, node, sibling)

        add_node("root:zz", tree_element, None, 0)
        fixture.memberships()
        schema.validate_store(db)
        db.commit()
        return db

    def test_source_resolver_exact_zero_one_and_no_identity_fallback(self) -> None:
        with query._open_syntax_readonly(self.path) as db:
            sqlite_node_id = query._resolve_source_node_id(db, BOUNDARY)
            self.assertIsInstance(sqlite_node_id, int)
            self.assertEqual(db.execute("SELECT upstream_node_id FROM syntax_node WHERE node_id=?",
                                        (sqlite_node_id,)).fetchone()[0], BOUNDARY)
            self.assertIsNone(query._resolve_source_node_id(db, "unknown"))
        for identity in ("unknown", "ROOT:ZZ", "root:zz ", "root", "n-synthetic",
                         "m-synthetic", str(sqlite_node_id), BOUNDARY[:-1],
                         "' OR 1=1 --"):
            for operation in NODE_OPERATIONS:
                with self.subTest(identity=identity, operation=operation.__name__):
                    self.assertIsNone(operation(self.path, identity))

    def test_duplicate_source_node_id_fails_closed_without_limit_one(self) -> None:
        root, root_element, tree = self.db.execute(
            "SELECT node_id,element_id,tree_id FROM syntax_node WHERE upstream_node_id='root:zz'",
        ).fetchone()
        fixture = SchemaFixture(self.db)
        fixture.next_element = self.db.execute("SELECT max(element_id)+1 FROM xml_element").fetchone()[0]
        file_id = self.db.execute("SELECT file_id FROM xml_element WHERE element_id=?", (root_element,)).fetchone()[0]
        element = fixture.element(file_id, root_element, "Node")
        attributes = {"nodeId": BOUNDARY}
        fixture.attributes(element, attributes)
        fixture.node(tree, element, root, 3, attributes)
        self.db.commit()
        statements: list[str] = []
        with query._open_syntax_readonly(self.path) as db:
            db.set_trace_callback(statements.append)
            with self.assertRaisesRegex(query.QueryError, "ambiguous source_node_id"):
                query._resolve_source_node_id(db, BOUNDARY)
        resolver_sql = [sql for sql in statements if "n.upstream_node_id =" in sql]
        self.assertEqual(len(resolver_sql), 1)
        self.assertNotIn("LIMIT", resolver_sql[0].upper())
        for operation in NODE_OPERATIONS:
            with self.assertRaisesRegex(query.QueryError, "ambiguous source_node_id"):
                operation(self.path, BOUNDARY)

    def test_invalid_source_arguments_are_not_numeric_keys(self) -> None:
        for identity in ("", 1000, True, None):
            for operation in NODE_OPERATIONS:
                with self.subTest(identity=identity, operation=operation.__name__):
                    with self.assertRaisesRegex(query.QueryError, "source_node_id"):
                        operation(self.path, identity)

    def test_node_projection_raw_absence_empty_and_root_parent(self) -> None:
        root = query.get_node(self.path, "root:zz")
        np = query.get_node(self.path, "np:zz")
        node = query.get_node(self.path, BOUNDARY)
        assert root is not None and np is not None and node is not None
        self.assertEqual(node.source_node_id, BOUNDARY)
        self.assertEqual(node.parent_source_node_id, "root:zz")
        self.assertEqual((node.rule, node.start_raw, node.end_raw, node.head_raw, node.length_raw),
                         ("S-V-O", "5", "8", "1", "4"))
        self.assertIsNone(root.parent_source_node_id)
        self.assertEqual((root.id_raw, root.rule, root.cl_type, root.start_raw,
                          root.end_raw, root.head_raw, root.length_raw), (None,) * 7)
        self.assertEqual(np.id_raw, "")
        self.assertIsNone(np.head_raw)
        self.assertTrue(LOCAL_IDS.isdisjoint(field.name for field in fields(node)))
        with self.assertRaises(FrozenInstanceError):
            setattr(node, "source_node_id", "changed")

    def test_children_direct_sibling_order_not_pk_or_source_id(self) -> None:
        children = query.get_children(self.path, BOUNDARY)
        assert children is not None
        self.assertEqual([node.source_node_id for node in children], ["z-subject", "a-verb", "m-object"])
        self.assertEqual([node.cat for node in children], ["S", "V", "O"])
        self.assertEqual([node.sibling_ordinal for node in children], [0, 1, 2])
        self.assertTrue(all(node.parent_source_node_id == BOUNDARY for node in children))
        pk_order = [row[0] for row in self.db.execute(
            "SELECT upstream_node_id FROM syntax_node WHERE parent_node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id=?) ORDER BY node_id", (BOUNDARY,),
        )]
        self.assertNotEqual(pk_order, [node.source_node_id for node in children])
        self.assertEqual(query.get_children(self.path, JESUS), ())

    def test_ancestors_nearest_first_exclude_self_and_share_exact_token_boundary(self) -> None:
        ancestors = query.get_ancestors_by_node(self.path, JESUS)
        assert ancestors is not None
        self.assertEqual([node.source_node_id for node in ancestors], ["np:zz", "root:zz"])
        self.assertEqual(query.get_ancestors_by_token(self.path, "MAT 1:1!3"), ancestors)
        self.assertEqual(query.get_ancestors_by_node(self.path, "root:zz"), ())
        for ref in ("MAT 1:1!999", "mat 1:1!3", "MAT 1:1!1", "MAT 99:99!3"):
            with self.subTest(ref=ref):
                self.assertIsNone(query.get_ancestors_by_token(self.path, ref))
        for ref in ("MAT 1:1", "MAT 01:1!3", "MAT 1:1!3 ", "MAT 1:1!3' OR 1=1"):
            with self.subTest(ref=ref), self.assertRaises(query.QueryError):
                query.get_ancestors_by_token(self.path, ref)

    def test_cycle_is_integrity_error_not_truncated_ancestry(self) -> None:
        self.db.execute("DROP TRIGGER node_no_update")
        self.db.execute(
            "UPDATE syntax_node SET parent_node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id='np:zz'),sibling_ordinal=1 "
            "WHERE upstream_node_id='root:zz'",
        )
        self.db.commit()
        for operation in (
            lambda: query.get_ancestors_by_node(self.path, JESUS),
            lambda: query.get_ancestors_by_token(self.path, "MAT 1:1!3"),
        ):
            with self.assertRaisesRegex(query.QueryError, "cyclic syntax ancestry"):
                operation()

    def test_missing_linked_parent_is_integrity_error(self) -> None:
        self.db.execute("PRAGMA foreign_keys=OFF")
        self.db.execute("DROP TRIGGER node_no_update")
        self.db.execute("UPDATE syntax_node SET parent_node_id=999999 WHERE upstream_node_id='np:zz'")
        self.db.commit()
        for operation in (
            lambda: query.get_node(self.path, "np:zz"),
            lambda: query.get_ancestors_by_node(self.path, JESUS),
            lambda: query.get_ancestors_by_token(self.path, "MAT 1:1!3"),
        ):
            with self.assertRaisesRegex(query.QueryError, "missing or cross-Tree syntax parent"):
                operation()

    def test_exact_members_exclude_six_and_wrong_envelopes(self) -> None:
        members = query.get_members(self.path, BOUNDARY)
        assert members is not None
        ordinals = [token.verse_token_ordinal for token in members]
        self.assertEqual(ordinals, [5, 7, 8, 9])
        self.assertNotIn(6, ordinals)
        self.assertNotEqual(ordinals, [5, 6, 7, 8])
        self.assertNotEqual(ordinals, [5, 6, 7, 8, 9])
        self.assertEqual(query.get_members(self.path, JESUS),
                         (query.get_token(self.path, "MAT 1:1!3"),))
        root_members = query.get_members(self.path, "root:zz")
        assert root_members is not None
        self.assertEqual([token.ref for token in root_members],
                         ["MAT 1:1!3"] + [f"MAT 1:2!{i}" for i in (5, 6, 7, 8, 9)])

    def test_members_use_materialized_relation_not_span_or_recomputed_ancestry(self) -> None:
        self.db.execute(
            "DELETE FROM node_token_membership WHERE node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id=?)", (BOUNDARY,),
        )
        self.db.commit()
        self.assertEqual(query.get_members(self.path, BOUNDARY), ())

    def test_head_raw_is_direct_child_index_and_missing_stays_missing(self) -> None:
        node = query.get_node(self.path, BOUNDARY)
        children = query.get_children(self.path, BOUNDARY)
        assert node is not None and children is not None and node.head_raw is not None
        self.assertEqual(children[int(node.head_raw)].cat, "V")
        self.assertEqual(children[int(node.head_raw)].source_node_id, "a-verb")
        leaf = query.get_node(self.path, JESUS)
        assert leaf is not None
        self.assertIsNone(leaf.head_raw)

    def test_surrogate_pk_invariance_for_all_public_navigation(self) -> None:
        second = self.path.with_name("shifted.sqlite3")
        shifted = self.make_store(second, 20000)
        self.assertNotEqual(self.db.execute("SELECT node_id FROM token ORDER BY ref_raw").fetchall(),
                            shifted.execute("SELECT node_id FROM token ORDER BY ref_raw").fetchall())
        for identity in ("root:zz", "np:zz", JESUS, BOUNDARY):
            for operation in NODE_OPERATIONS[:-1]:
                with self.subTest(identity=identity, operation=operation.__name__):
                    self.assertEqual(operation(self.path, identity), operation(second, identity))
            left = query.get_members(self.path, identity)
            right = query.get_members(second, identity)
            assert left is not None and right is not None
            self.assertEqual(
                [{key: value for key, value in asdict(token).items() if key not in LOCAL_IDS} for token in left],
                [{key: value for key, value in asdict(token).items() if key not in LOCAL_IDS} for token in right],
            )
        self.assertEqual(query.get_ancestors_by_token(self.path, "MAT 1:1!3"),
                         query.get_ancestors_by_token(second, "MAT 1:1!3"))

    def test_public_queries_readonly_without_xml_or_source_mutation(self) -> None:
        before = self.path.read_bytes()
        catalog = self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall()
        statements: list[str] = []
        connect = query._connect_readonly

        def traced_connect(path: Path) -> sqlite3.Connection:
            db = connect(path)
            db.set_trace_callback(statements.append)
            return db

        with patch.object(query, "_connect_readonly", side_effect=traced_connect), \
                patch.object(ET, "fromstring", side_effect=AssertionError("runtime XML parsing prohibited")), \
                patch.object(unit1, "verify_source", side_effect=AssertionError("runtime source access prohibited")):
            for operation in NODE_OPERATIONS:
                self.assertIsNotNone(operation(self.path, BOUNDARY))
            self.assertIsNotNone(query.get_ancestors_by_token(self.path, "MAT 1:1!3"))
        self.assertFalse(any("expected_node_token_membership" in sql for sql in statements))
        self.assertTrue(any("node_token_membership" in sql for sql in statements))
        self.assertFalse(any(sql.lstrip().split()[0].upper() in (
            "INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER",
            "VACUUM", "REINDEX", "ATTACH",
        ) for sql in statements))
        with query._open_syntax_readonly(self.path) as db:
            for pragma in ("query_only", "foreign_keys", "recursive_triggers"):
                self.assertEqual(db.execute(f"PRAGMA {pragma}").fetchone()[0], 1)
            for disable in (False, True):
                if disable:
                    db.execute("PRAGMA query_only=OFF")
                for sql in (
                    "INSERT INTO syntax_node DEFAULT VALUES",
                    "UPDATE syntax_node SET head_raw='0'",
                    "DELETE FROM syntax_node",
                    "DELETE FROM node_token_membership",
                    "CREATE TABLE forbidden(x)",
                ):
                    with self.subTest(sql=sql, query_only=not disable):
                        with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                            db.execute(sql)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall(), catalog)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (2,))

    def test_incompatible_store_or_missing_syntax_columns_are_not_not_found(self) -> None:
        mutations = (
            "PRAGMA user_version=3",
            "ALTER TABLE syntax_node RENAME COLUMN head_raw TO missing_head",
            "ALTER TABLE syntax_node RENAME COLUMN parent_node_id TO missing_parent",
            "ALTER TABLE syntax_node RENAME COLUMN sibling_ordinal TO missing_ordinal",
            "ALTER TABLE tree RENAME COLUMN sentence_id TO missing_sentence",
            "ALTER TABLE sentence RENAME COLUMN book_id TO missing_book",
            "DROP TABLE node_token_membership",
        )
        for sql in mutations:
            with self.subTest(sql=sql):
                path = self.path.with_name("invalid.sqlite3")
                db = sqlite3.connect(path)
                try:
                    self.db.backup(db)
                    db.executescript(sql)
                finally:
                    db.close()
                for operation in NODE_OPERATIONS:
                    with self.assertRaises(query.QueryError):
                        operation(path, "unknown")
                with self.assertRaises(query.QueryError):
                    query.get_ancestors_by_token(path, "MAT 1:1!999")
                path.unlink()
        missing = self.path.with_name("missing.sqlite3")
        with self.assertRaises(query.QueryError):
            query.get_node(missing, "unknown")
        self.assertFalse(missing.exists())

    def test_multiple_matthew_snapshots_are_not_guessed(self) -> None:
        SchemaFixture(self.db).archive(number=2)
        self.db.commit()
        for operation in NODE_OPERATIONS:
            with self.assertRaisesRegex(query.QueryError, "ambiguous book"):
                operation(self.path, BOUNDARY)
        with self.assertRaisesRegex(query.QueryError, "ambiguous book"):
            query.get_ancestors_by_token(self.path, "MAT 1:1!3")

    def test_empty_schema_v2_store_has_explicit_not_found(self) -> None:
        path = self.path.with_name("empty.sqlite3")
        db = sqlite3.connect(path)
        try:
            schema.bootstrap(db)
        finally:
            db.close()
        for operation in NODE_OPERATIONS:
            self.assertIsNone(operation(path, BOUNDARY))
        self.assertIsNone(query.get_ancestors_by_token(path, "MAT 1:1!3"))


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT5_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT5_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit5MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_size = _LOCAL_DATABASE.stat().st_size
        cls.before_hash = hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper()
        with query._open_syntax_readonly(_LOCAL_DATABASE) as db:
            cls.before_catalog = tuple(db.execute("SELECT * FROM sqlite_schema ORDER BY type,name"))
        raw = unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH))
        cls.document = ET.fromstring(raw)

    @classmethod
    def tearDownClass(cls) -> None:
        if _LOCAL_DATABASE.stat().st_size != cls.before_size:
            raise AssertionError("integration database byte size changed")
        if hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper() != cls.before_hash:
            raise AssertionError("integration database SHA-256 changed")
        with query._open_syntax_readonly(_LOCAL_DATABASE) as db:
            if tuple(db.execute("SELECT * FROM sqlite_schema ORDER BY type,name")) != cls.before_catalog:
                raise AssertionError("integration schema/index inventory changed")
            if db.execute("PRAGMA user_version").fetchone()[0] != 2:
                raise AssertionError("integration schema version changed")
        print(f"Unit 5 read-only store unchanged: {cls.before_size} bytes; SHA-256 {cls.before_hash}", flush=True)

    def test_matthew_1_1_exact_token_ancestry_matches_independent_source(self) -> None:
        leaf = self.document.find(".//Node[@ref='MAT 1:1!3']")
        assert leaf is not None
        parents = {child: parent for parent in self.document.iter() for child in parent}
        expected = []
        current = leaf
        while parents[current].tag == "Node":
            current = parents[current]
            expected.append(current)
        ancestors = query.get_ancestors_by_token(_LOCAL_DATABASE, "MAT 1:1!3")
        assert ancestors is not None
        self.assertEqual([node.source_node_id for node in ancestors],
                         [node.attrib["nodeId"] for node in expected])
        self.assertEqual([node.rule for node in ancestors],
                         ["N2NP", "Np-Appos", "Np-Appos", "Np-Appos", "NPofNP", "NPofNP", "Np2P", "P2CL", None])
        self.assertEqual([node.cat for node in ancestors], ["np"] * 6 + ["P", "CL", "S"])
        self.assertEqual(ancestors[-2].cl_type, "Verbless")
        self.assertEqual(query.get_ancestors_by_node(_LOCAL_DATABASE, leaf.attrib["nodeId"]), ancestors)
        self.assertEqual(query.get_children(_LOCAL_DATABASE, leaf.attrib["nodeId"]), ())
        self.assertEqual(query.get_members(_LOCAL_DATABASE, leaf.attrib["nodeId"]),
                         (query.get_token(_LOCAL_DATABASE, "MAT 1:1!3"),))

    def test_matthew_1_2_direct_children_and_head_match_source(self) -> None:
        source = self.document.find(f".//Node[@nodeId='{BOUNDARY}']")
        assert source is not None
        node = query.get_node(_LOCAL_DATABASE, BOUNDARY)
        children = query.get_children(_LOCAL_DATABASE, BOUNDARY)
        assert node is not None and children is not None and node.head_raw is not None
        self.assertEqual((node.rule, node.start_raw, node.end_raw, node.head_raw), ("S-V-O", "5", "8", "1"))
        self.assertEqual([child.source_node_id for child in children],
                         [child.attrib["nodeId"] for child in source.findall("Node")])
        self.assertEqual([child.cat for child in children], ["S", "V", "O"])
        self.assertEqual([child.sibling_ordinal for child in children], [0, 1, 2])
        self.assertEqual(children[int(node.head_raw)].cat, "V")
        self.assertTrue(all(child.parent_source_node_id == BOUNDARY for child in children))

    def test_matthew_1_2_exact_membership_excludes_envelope_token_six(self) -> None:
        source = self.document.find(f".//Node[@nodeId='{BOUNDARY}']")
        assert source is not None
        members = query.get_members(_LOCAL_DATABASE, BOUNDARY)
        assert members is not None
        self.assertEqual([token.verse_token_ordinal for token in members], [5, 7, 8, 9])
        self.assertNotIn(6, [token.verse_token_ordinal for token in members])
        self.assertEqual({token.ref for token in members},
                         {node.attrib["ref"] for node in source.iter("Node") if "ref" in node.attrib})
        for token in members:
            assert token.ref is not None
            self.assertEqual(token, query.get_token(_LOCAL_DATABASE, token.ref))

    def test_matthew_root_absence_and_unknown_identities(self) -> None:
        root = query.get_node(_LOCAL_DATABASE, "400010010010083")
        assert root is not None
        self.assertIsNone(root.parent_source_node_id)
        self.assertEqual((root.start_raw, root.end_raw, root.id_raw, root.rule), (None,) * 4)
        leaf = query.get_node(_LOCAL_DATABASE, JESUS)
        assert leaf is not None
        self.assertIsNone(leaf.head_raw)
        for operation in NODE_OPERATIONS:
            self.assertIsNone(operation(_LOCAL_DATABASE, "unknown"))
        self.assertIsNone(query.get_ancestors_by_token(_LOCAL_DATABASE, "MAT 1:1!999"))


if __name__ == "__main__":
    unittest.main()
