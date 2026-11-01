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
LOCAL_IDS = {"token_id", "node_id", "tree_id", "element_id", "book_id"}


class Unit6FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit6-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "evidence # fixture.sqlite3"
        self.db = self.make_store(self.path)

    def make_store(self, path: Path, offset: int = 0, root_leaf: bool = False) -> sqlite3.Connection:
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        schema.bootstrap(db)
        fixture = SchemaFixture(db, offset)
        attrs = {
            "root:opaque": {"Cat": "S"},
            "cl:opaque": {"Cat": "CL", "Rule": "P2CL", "ClType": "Verbless"},
            "np:opaque": {"Cat": "np", "Rule": "N2NP", "Id": ""},
            JESUS: {"Cat": "noun", "ref": "MAT 1:1!3", "xml:id": "xml-source",
                    "morphId": "morph-source", "UnicodeLemma": "source-lemma",
                    "English": "", "Ref": "separate-referent", "Case": "Genitive"},
            "connector": {"Cat": "conj", "ref": "MAT 1:2!6"},
            BOUNDARY: {"Cat": "CL", "Rule": "S-V-O", "Start": "5", "End": "8", "Head": "1"},
            "z-five": {"Cat": "S", "ref": "MAT 1:2!5"},
            "a-seven": {"Cat": "V", "ref": "MAT 1:2!7"},
            "m-object": {"Cat": "O"},
            "leaf-eight": {"Cat": "noun", "ref": "MAT 1:2!8"},
            "leaf-nine": {"Cat": "noun", "ref": "MAT 1:2!9"},
        }
        children = {
            "root:opaque": ["cl:opaque", "connector", BOUNDARY],
            "cl:opaque": ["np:opaque"],
            "np:opaque": [JESUS],
            BOUNDARY: ["z-five", "a-seven", "m-object"],
            "m-object": ["leaf-eight", "leaf-nine"],
        }
        root = "root:opaque"
        if root_leaf:
            attrs = {JESUS: attrs[JESUS]}
            children = {}
            root = JESUS
        for identity, values in attrs.items():
            values["nodeId"] = identity
        leaves = [identity for identity, values in attrs.items() if "ref" in values]
        coordinates = {
            identity: tuple(int(value) for value in attrs[identity]["ref"].split(":")[1].split("!"))
            for identity in leaves
        }
        canonical = sorted(leaves, key=coordinates.__getitem__)
        texts = {identity: "surface-" + attrs[identity]["ref"] for identity in leaves}
        node_ids = {identity: offset + 1000 - i * 10 for i, identity in enumerate(attrs)}

        def node_xml(identity: str) -> str:
            content = "".join(node_xml(child) for child in children.get(identity, []))
            return tag("Node", attrs[identity], content or escape(texts[identity]))

        ref = "MAT 1:1!3-1:2!9" if not root_leaf else "MAT 1:1!3-1:1!3"
        raw = tag("Sentences", {}, tag("Sentence", {"ref": ref},
                  tag("Trees", {}, tag("Tree", {}, node_xml(root))))).encode()
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
            "tree_id": offset + 1, "sentence_id": sentence, "element_id": tree_element, "ordinal": 0,
        })

        def add_node(identity: str, parent_element: int, parent: int | None, ordinal: int) -> None:
            element = fixture.element(file_id, parent_element, "Node")
            fixture.attributes(element, attrs[identity])
            node = fixture.node(tree, element, parent, ordinal, attrs[identity],
                                {"node_id": node_ids[identity]})
            if identity in texts:
                traversal = leaves.index(identity)
                verse, word = coordinates[identity]
                fixture.content(file_id, element, "text", texts[identity])
                fixture.token(
                    tree, book_id, node, texts[identity], attrs[identity],
                    traversal=traversal, canonical=canonical.index(identity), verse=verse, word=word,
                    overrides={"token_id": offset + 10000 - traversal},
                )
            for sibling, child in enumerate(children.get(identity, [])):
                add_node(child, element, node, sibling)

        add_node(root, tree_element, None, 0)
        fixture.memberships()
        schema.validate_store(db)
        db.commit()
        return db

    def test_exact_known_token_composes_frozen_source_facts(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:1!3")
        assert evidence is not None
        self.assertIsInstance(evidence, query.SourceEvidence)
        self.assertEqual((evidence.token.ref, evidence.token.upstream_node_id,
                          evidence.token.xml_id, evidence.token.morph_id),
                         ("MAT 1:1!3", JESUS, "xml-source", "morph-source"))
        self.assertEqual((evidence.token.surface, evidence.token.lemma, evidence.token.case,
                          evidence.token.english, evidence.token.referent),
                         ("surface-MAT 1:1!3", "source-lemma", "Genitive", "", "separate-referent"))
        self.assertIsNone(evidence.token.normalized)
        self.assertEqual((evidence.node.source_node_id, evidence.node.parent_source_node_id), (JESUS, "np:opaque"))
        self.assertEqual(evidence.membership_node.source_node_id, "np:opaque")
        self.assertEqual(evidence.membership_node.id_raw, "")
        self.assertIsNone(evidence.membership_node.head_raw)
        self.assertEqual([token.ref for token in evidence.contextual_members], ["MAT 1:1!3"])
        for result, field in ((evidence, "node"), (evidence.node, "cat"), (evidence.token, "surface")):
            with self.assertRaises(FrozenInstanceError):
                setattr(result, field, "changed")
        for collection in (evidence.ancestors, evidence.parent_children, evidence.contextual_members):
            self.assertIsInstance(collection, tuple)
        self.assertTrue(LOCAL_IDS.isdisjoint(field.name for field in fields(evidence.node)))

    def test_composition_equivalence_with_existing_public_queries(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:1!3")
        assert evidence is not None
        self.assertEqual(evidence.token, query.get_token(self.path, "MAT 1:1!3"))
        self.assertEqual(evidence.node, query.get_node(self.path, JESUS))
        self.assertEqual(evidence.ancestors, query.get_ancestors_by_token(self.path, "MAT 1:1!3"))
        self.assertEqual(evidence.parent_children, query.get_children(self.path, "np:opaque"))
        self.assertEqual(evidence.contextual_members, query.get_members(self.path, "np:opaque"))

    def test_unknown_exact_refs_have_no_identity_or_case_fallback(self) -> None:
        for ref in ("MAT 1:1!999", "MAT 1:1!1", "mat 1:1!3", "MRK 1:1!3", "MAT 99:99!3"):
            with self.subTest(ref=ref):
                self.assertIsNone(query.get_source_evidence(self.path, ref))
        self.db.execute("DROP TRIGGER token_no_update")
        self.db.execute("UPDATE token SET ref_raw='MAT 1:1!30' WHERE ref_raw='MAT 1:1!3'")
        self.db.commit()
        self.assertIsNone(query.get_source_evidence(self.path, "MAT 1:1!3"))

    def test_invalid_refs_fail_explicitly(self) -> None:
        for ref in ("", None, 1000, True, "MAT 1:1", " MAT 1:1!3", "MAT 1:1!3 ",
                    "MAT 01:1!3", "MAT 1:1!3' OR 1=1", JESUS, "xml-source", "morph-source",
                    f"MAT {2**63}:1!3", "MAT " + "9" * 5000 + ":1!3"):
            with self.subTest(ref=ref), self.assertRaises(query.QueryError):
                query.get_source_evidence(self.path, ref)

    def test_leaf_ancestry_nearest_first_excludes_self_and_reaches_root(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:1!3")
        assert evidence is not None
        self.assertEqual([node.source_node_id for node in evidence.ancestors],
                         ["np:opaque", "cl:opaque", "root:opaque"])
        self.assertNotIn(JESUS, [node.source_node_id for node in evidence.ancestors])
        self.assertEqual((evidence.ancestors[1].rule, evidence.ancestors[1].cl_type), ("P2CL", "Verbless"))
        self.assertIsNone(evidence.ancestors[-1].parent_source_node_id)
        self.assertEqual(query.get_children(self.path, JESUS), ())

    def test_direct_parent_children_are_sibling_order_not_pk_order(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:2!5")
        assert evidence is not None
        self.assertEqual(evidence.membership_node.source_node_id, BOUNDARY)
        self.assertEqual([node.source_node_id for node in evidence.parent_children], ["z-five", "a-seven", "m-object"])
        self.assertEqual([node.cat for node in evidence.parent_children], ["S", "V", "O"])
        self.assertEqual([node.sibling_ordinal for node in evidence.parent_children], [0, 1, 2])
        self.assertTrue(all(node.parent_source_node_id == BOUNDARY for node in evidence.parent_children))
        self.assertNotIn("leaf-eight", [node.source_node_id for node in evidence.parent_children])
        pk_order = self.db.execute(
            "SELECT upstream_node_id FROM syntax_node WHERE parent_node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id=?) ORDER BY node_id", (BOUNDARY,),
        ).fetchall()
        self.assertEqual([row[0] for row in pk_order], ["m-object", "a-seven", "z-five"])

    def test_exact_discontinuous_context_membership_excludes_six(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:2!5")
        assert evidence is not None
        self.assertEqual((evidence.membership_node.rule, evidence.membership_node.start_raw,
                          evidence.membership_node.end_raw, evidence.membership_node.head_raw),
                         ("S-V-O", "5", "8", "1"))
        self.assertEqual([token.verse_token_ordinal for token in evidence.contextual_members], [5, 7, 8, 9])
        self.assertNotIn("MAT 1:2!6", [token.ref for token in evidence.contextual_members])
        self.assertEqual([token.ref for token in evidence.contextual_members],
                         [f"MAT 1:2!{word}" for word in (5, 7, 8, 9)])
        assert evidence.membership_node.head_raw is not None
        self.assertEqual(evidence.parent_children[int(evidence.membership_node.head_raw)].cat, "V")

    def test_membership_is_not_promoted_to_higher_ancestor(self) -> None:
        evidence = query.get_source_evidence(self.path, "MAT 1:2!8")
        assert evidence is not None
        self.assertEqual([node.source_node_id for node in evidence.ancestors], ["m-object", BOUNDARY, "root:opaque"])
        self.assertEqual(evidence.membership_node.source_node_id, "m-object")
        self.assertEqual([token.verse_token_ordinal for token in evidence.contextual_members], [8, 9])

    def test_membership_uses_stored_relation_even_when_empty(self) -> None:
        self.db.execute(
            "DELETE FROM node_token_membership WHERE node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id=?)", (BOUNDARY,),
        )
        self.db.commit()
        evidence = query.get_source_evidence(self.path, "MAT 1:2!5")
        assert evidence is not None
        self.assertEqual(evidence.contextual_members, ())
        self.assertEqual(evidence.membership_node.source_node_id, BOUNDARY)

    def test_root_leaf_uses_own_membership_without_parent_context(self) -> None:
        path = self.path.with_name("root-leaf.sqlite3")
        self.make_store(path, root_leaf=True)
        evidence = query.get_source_evidence(path, "MAT 1:1!3")
        assert evidence is not None
        self.assertIsNone(evidence.node.parent_source_node_id)
        self.assertEqual(evidence.ancestors, ())
        self.assertEqual(evidence.parent_children, ())
        self.assertEqual(evidence.membership_node, evidence.node)
        self.assertEqual(evidence.contextual_members, (evidence.token,))

    def test_empty_initialized_store_is_explicit_not_found(self) -> None:
        path = self.path.with_name("empty.sqlite3")
        with sqlite3.connect(path) as db:
            schema.bootstrap(db)
        db.close()
        self.assertIsNone(query.get_source_evidence(path, "MAT 1:1!3"))

    def test_wrong_database_schema_and_missing_columns_are_errors_not_not_found(self) -> None:
        missing = self.path.with_name("missing.sqlite3")
        with self.assertRaises(query.QueryError):
            query.get_source_evidence(missing, "MAT 1:1!999")
        self.assertFalse(missing.exists())
        broken = self.path.with_name("broken.sqlite3")
        broken.write_bytes(b"not SQLite")
        with self.assertRaises(query.QueryError):
            query.get_source_evidence(broken, "MAT 1:1!999")
        mutations = (
            "PRAGMA user_version=3",
            "DROP TRIGGER version_no_update; UPDATE schema_version SET ddl_sha256='" + "0" * 64 + "'",
            "ALTER TABLE token RENAME COLUMN normalized_form TO missing_normalized",
            "ALTER TABLE syntax_node RENAME COLUMN parent_node_id TO missing_parent",
            "ALTER TABLE syntax_node RENAME COLUMN head_raw TO missing_head",
            "DROP TABLE node_token_membership",
            "DROP TABLE schema_version",
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
                for ref in ("MAT 1:1!3", "MAT 1:1!999"):
                    with self.assertRaises(query.QueryError):
                        query.get_source_evidence(path, ref)
                path.unlink()

    def test_duplicate_source_identity_propagates_for_leaf_ancestor_and_sibling(self) -> None:
        for identity in (JESUS, BOUNDARY, "root:opaque", "m-object"):
            with self.subTest(identity=identity):
                path = self.path.with_name("duplicate.sqlite3")
                db = sqlite3.connect(path)
                try:
                    self.db.backup(db)
                    db.execute("DROP TRIGGER node_no_update")
                    db.execute("UPDATE syntax_node SET upstream_node_id=? WHERE upstream_node_id='connector'", (identity,))
                    db.commit()
                finally:
                    db.close()
                ref = "MAT 1:1!3" if identity == JESUS else "MAT 1:2!5"
                with self.assertRaisesRegex(query.QueryError, "ambiguous source_node_id"):
                    query.get_source_evidence(path, ref)
                path.unlink()

    def test_multiple_matthew_snapshots_fail_closed(self) -> None:
        SchemaFixture(self.db).archive(number=2)
        self.db.commit()
        with self.assertRaisesRegex(query.QueryError, "ambiguous book"):
            query.get_source_evidence(self.path, "MAT 1:1!3")

    def test_cycle_failure_propagates_without_empty_bundle(self) -> None:
        self.db.execute("DROP TRIGGER node_no_update")
        self.db.execute(
            "UPDATE syntax_node SET parent_node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id='np:opaque'),sibling_ordinal=1 "
            "WHERE upstream_node_id='root:opaque'",
        )
        self.db.commit()
        with self.assertRaisesRegex(query.QueryError, "cyclic syntax ancestry"):
            query.get_source_evidence(self.path, "MAT 1:1!3")

    def test_missing_parent_or_source_identity_is_explicit_failure(self) -> None:
        for sql, message in (
            ("UPDATE syntax_node SET parent_node_id=999999 WHERE upstream_node_id='np:opaque'",
             "missing or cross-Tree syntax parent"),
            ("UPDATE syntax_node SET upstream_node_id=NULL WHERE upstream_node_id='" + JESUS + "'",
             "no source_node_id"),
        ):
            with self.subTest(sql=sql):
                path = self.path.with_name("missing-link.sqlite3")
                db = sqlite3.connect(path)
                try:
                    self.db.backup(db)
                    db.execute("PRAGMA foreign_keys=OFF")
                    db.execute("DROP TRIGGER node_no_update")
                    db.execute(sql)
                    db.commit()
                finally:
                    db.close()
                with self.assertRaisesRegex(query.QueryError, message):
                    query.get_source_evidence(path, "MAT 1:1!3")
                path.unlink()

    def test_surrogate_pk_reallocation_preserves_all_source_level_evidence(self) -> None:
        path = self.path.with_name("shifted.sqlite3")
        self.make_store(path, 20000)
        for ref in ("MAT 1:1!3", "MAT 1:2!5", "MAT 1:2!6", "MAT 1:2!8"):
            with self.subTest(ref=ref):
                left = query.get_source_evidence(self.path, ref)
                right = query.get_source_evidence(path, ref)
                assert left is not None and right is not None
                for l_token, r_token in ((left.token, right.token),
                                         *zip(left.contextual_members, right.contextual_members)):
                    l_facts, r_facts = asdict(l_token), asdict(r_token)
                    for key in LOCAL_IDS:
                        self.assertNotEqual(l_facts[key], r_facts[key], key)
                    self.assertEqual({key: value for key, value in l_facts.items() if key not in LOCAL_IDS},
                                     {key: value for key, value in r_facts.items() if key not in LOCAL_IDS})
                self.assertEqual(len(left.contextual_members), len(right.contextual_members))
                self.assertEqual(left.node, right.node)
                self.assertEqual(left.ancestors, right.ancestors)
                self.assertEqual(left.parent_children, right.parent_children)
                self.assertEqual(left.membership_node, right.membership_node)

    def test_public_composition_uses_one_sqlite_enforced_readonly_connection(self) -> None:
        before = self.path.read_bytes()
        catalog = self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall()
        statements: list[str] = []
        opened: list[sqlite3.Connection] = []
        connect = query._connect_readonly

        def checked_connect(path: Path) -> sqlite3.Connection:
            db = connect(path)
            opened.append(db)
            for pragma in ("query_only", "foreign_keys", "recursive_triggers"):
                self.assertEqual(db.execute(f"PRAGMA {pragma}").fetchone()[0], 1)
            for disable in (False, True):
                if disable:
                    db.execute("PRAGMA query_only=OFF")
                for sql in ("INSERT INTO token DEFAULT VALUES", "UPDATE token SET english='changed'",
                            "DELETE FROM node_token_membership", "CREATE TABLE forbidden(x)"):
                    with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                        db.execute(sql)
            db.execute("PRAGMA query_only=ON")
            db.set_trace_callback(statements.append)
            return db

        with patch.object(query, "_connect_readonly", side_effect=checked_connect), \
                patch.object(ET, "fromstring", side_effect=AssertionError("runtime XML prohibited")), \
                patch.object(unit1, "verify_source", side_effect=AssertionError("runtime source access prohibited")):
            self.assertIsNotNone(query.get_source_evidence(self.path, "MAT 1:2!5"))
        self.assertEqual(len(opened), 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute("SELECT 1")
        self.assertTrue(any("main.node_token_membership" in sql for sql in statements))
        self.assertFalse(any("expected_node_token_membership" in sql for sql in statements))
        self.assertFalse(any(sql.lstrip().split()[0].upper() in (
            "INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER", "ATTACH", "VACUUM",
        ) for sql in statements))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall(), catalog)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (2,))

    def test_connection_closes_on_not_found_and_query_failure(self) -> None:
        connect = query._connect_readonly
        opened: list[sqlite3.Connection] = []

        def tracked_connect(path: Path) -> sqlite3.Connection:
            db = connect(path)
            opened.append(db)
            return db

        with patch.object(query, "_connect_readonly", side_effect=tracked_connect):
            self.assertIsNone(query.get_source_evidence(self.path, "MAT 1:1!999"))
            with patch.object(query, "_ancestors", side_effect=query.QueryError("explicit topology failure")):
                with self.assertRaisesRegex(query.QueryError, "explicit topology failure"):
                    query.get_source_evidence(self.path, "MAT 1:1!3")
        self.assertEqual(len(opened), 2)
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT6_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT6_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit6MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_size = _LOCAL_DATABASE.stat().st_size
        cls.before_hash = hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper()
        with query._open_syntax_readonly(_LOCAL_DATABASE) as db:
            cls.before_version = db.execute("PRAGMA user_version").fetchone()[0]
            cls.before_catalog = tuple(db.execute("SELECT * FROM sqlite_schema ORDER BY type,name"))
        cls.document = ET.fromstring(unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH)))

    @classmethod
    def tearDownClass(cls) -> None:
        if _LOCAL_DATABASE.stat().st_size != cls.before_size:
            raise AssertionError("integration database byte size changed")
        if hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper() != cls.before_hash:
            raise AssertionError("integration database SHA-256 changed")
        with query._open_syntax_readonly(_LOCAL_DATABASE) as db:
            if db.execute("PRAGMA user_version").fetchone()[0] != cls.before_version:
                raise AssertionError("integration schema version changed")
            if tuple(db.execute("SELECT * FROM sqlite_schema ORDER BY type,name")) != cls.before_catalog:
                raise AssertionError("integration schema/index inventory changed")
        print(f"Unit 6 read-only store unchanged: {_LOCAL_DATABASE}; {cls.before_size} bytes; "
              f"SHA-256 {cls.before_hash}; user_version {cls.before_version}", flush=True)

    def test_matthew_1_1_exact_composition_and_verbless_source_ancestry(self) -> None:
        evidence = query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3")
        assert evidence is not None
        self.assertEqual((evidence.token.ref, evidence.token.upstream_node_id, evidence.node.source_node_id),
                         ("MAT 1:1!3", JESUS, JESUS))
        self.assertEqual((evidence.token.surface, evidence.token.lemma, evidence.token.case, evidence.token.strong_number),
                         ("\u1f38\u03b7\u03c3\u03bf\u1fe6", "\u1f38\u03b7\u03c3\u03bf\u1fe6\u03c2", "Genitive", "2424"))
        self.assertEqual([node.source_node_id for node in evidence.ancestors], [
            "400010010030011", "400010010030020", "400010010030040", "400010010030060",
            "400010010020070", "400010010010080", "400010010010081", "400010010010082", "400010010010083",
        ])
        self.assertEqual([node.rule for node in evidence.ancestors],
                         ["N2NP", "Np-Appos", "Np-Appos", "Np-Appos", "NPofNP", "NPofNP", "Np2P", "P2CL", None])
        self.assertEqual([node.cat for node in evidence.ancestors], ["np"] * 6 + ["P", "CL", "S"])
        self.assertEqual(evidence.ancestors[-2].cl_type, "Verbless")
        self.assertIsNone(evidence.ancestors[-1].parent_source_node_id)
        self.assertNotIn(JESUS, [node.source_node_id for node in evidence.ancestors])
        self.assertEqual(evidence.membership_node.source_node_id, "400010010030011")
        self.assertEqual([node.source_node_id for node in evidence.parent_children], [JESUS])
        self.assertEqual([token.ref for token in evidence.contextual_members], ["MAT 1:1!3"])

    def test_matthew_1_2_composition_reaches_exact_discontinuous_boundary(self) -> None:
        evidence = query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:2!5")
        assert evidence is not None
        self.assertEqual(evidence.node.source_node_id, "400010020050010")
        self.assertEqual([node.source_node_id for node in evidence.ancestors], [
            "400010020050011", "400010020050012", BOUNDARY, "400010020010820", "400010020010821",
        ])
        boundary = evidence.ancestors[2]
        self.assertEqual((boundary.rule, boundary.start_raw, boundary.end_raw, boundary.head_raw),
                         ("S-V-O", "5", "8", "1"))
        children = query.get_children(_LOCAL_DATABASE, boundary.source_node_id)
        members = query.get_members(_LOCAL_DATABASE, boundary.source_node_id)
        assert children is not None and members is not None
        self.assertEqual([node.source_node_id for node in children],
                         ["400010020050012", "400010020070012", "400010020080021"])
        self.assertEqual([node.cat for node in children], ["S", "V", "O"])
        self.assertEqual([node.sibling_ordinal for node in children], [0, 1, 2])
        self.assertEqual([token.verse_token_ordinal for token in members], [5, 7, 8, 9])
        self.assertNotIn("MAT 1:2!6", [token.ref for token in members])
        source = self.document.find(f".//Node[@nodeId='{BOUNDARY}']")
        assert source is not None
        self.assertEqual({token.ref for token in members},
                         {node.attrib["ref"] for node in source.iter("Node") if "ref" in node.attrib})
        self.assertEqual(evidence.membership_node.source_node_id, "400010020050011")
        self.assertEqual([node.source_node_id for node in evidence.parent_children], ["400010020050010"])
        self.assertEqual([token.ref for token in evidence.contextual_members], ["MAT 1:2!5"])

    def test_matthew_unknown_and_repeated_queries_are_deterministic(self) -> None:
        self.assertIsNone(query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!999"))
        self.assertIsNone(query.get_source_evidence(_LOCAL_DATABASE, "mat 1:1!3"))
        self.assertEqual(query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3"),
                         query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3"))


if __name__ == "__main__":
    unittest.main()
