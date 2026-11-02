from dataclasses import FrozenInstanceError, asdict, fields, replace
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

from scripts import source_query as query
from scripts import source_schema as schema
from scripts import structural_candidates as candidate
from scripts import verify_unit1 as unit1
from tests.test_unit2 import SchemaFixture, tag


BOUNDARY = "400010020050040"
LOCAL_IDS = {"token_id", "node_id", "tree_id", "element_id", "book_id"}
MATTHEW_APPOSITIONS = (
    ("400010010030020", ("400010010030011", "400010010040011"), (3, 4)),
    ("400010010030040", ("400010010030020", "400010010050020"), (3, 4, 5, 6)),
    ("400010010030060", ("400010010030040", "400010010070020"), (3, 4, 5, 6, 7, 8)),
)


SVO_TUPLE = ("clause-structure", "source-rule-s-v-o", "1")
SVO_SCOPE = tuple(f"MAT 1:2!{word}" for word in (5, 7, 8, 9))


def svo_candidates(result: tuple) -> list:
    return [item for item in result
            if (item.candidate_kind, item.derivation_kind, item.derivation_version) == SVO_TUPLE]


class Unit7FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit7-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "candidate # fixture.sqlite3"
        self.db = self.make_store(self.path)

    def make_store(self, path: Path, offset: int = 0) -> sqlite3.Connection:
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        schema.bootstrap(db)
        fixture = SchemaFixture(db, offset)
        attrs = {
            "root:opaque": {"Cat": "S"},
            "cl:opaque": {"Cat": "CL", "Rule": "P2CL", "ClType": "Verbless"},
            "a-outer": {"Cat": "np", "Rule": "Np-Appos", "Start": "3", "End": "4"},
            "z-inner": {"Cat": "np", "Rule": "Np-Appos"},
            "z-leaf": {"Cat": "noun", "ref": "MAT 1:1!3"},
            "a-leaf": {"Cat": "noun", "ref": "MAT 1:1!4"},
            "m-leaf": {"Cat": "noun", "ref": "MAT 1:1!8"},
            "unrelated-appos": {"Cat": "np", "Rule": "Np-Appos"},
            "off-one": {"Cat": "noun", "ref": "MAT 1:1!1"},
            "off-two": {"Cat": "noun", "ref": "MAT 1:1!2"},
            "connector": {"Cat": "conj", "ref": "MAT 1:2!6"},
            BOUNDARY: {"Cat": "CL", "Rule": "S-V-O", "Start": "5", "End": "8", "Head": "1"},
            "z-five": {"Cat": "S", "ref": "MAT 1:2!5", "Frame": "A0"},
            "a-seven": {"Cat": "V", "ref": "MAT 1:2!7", "Voice": "Passive",
                        "Frame": "A1 A2 AA2", "Notes": "Event Result"},
            "m-object": {"Cat": "O"},
            "leaf-eight": {"Cat": "OC", "ref": "MAT 1:2!8"},
            "leaf-nine": {"Cat": "O2", "ref": "MAT 1:2!9"},
        }
        children = {
            "root:opaque": ["cl:opaque", "unrelated-appos", "connector", BOUNDARY],
            "cl:opaque": ["a-outer"],
            "a-outer": ["z-inner", "m-leaf"],
            "z-inner": ["z-leaf", "a-leaf"],
            "unrelated-appos": ["off-one", "off-two"],
            BOUNDARY: ["z-five", "a-seven", "m-object"],
            "m-object": ["leaf-eight", "leaf-nine"],
        }
        for identity, values in attrs.items():
            values["nodeId"] = identity
        leaves = [identity for identity, values in attrs.items() if "ref" in values]
        coordinates = {
            identity: tuple(int(value) for value in attrs[identity]["ref"].split(":")[1].split("!"))
            for identity in leaves
        }
        canonical = sorted(leaves, key=coordinates.__getitem__)
        node_ids = {
            identity: offset + 1000 + (i * 10 if offset else -i * 10)
            for i, identity in enumerate(attrs)
        }

        def node_xml(identity: str) -> str:
            content = "".join(node_xml(child) for child in children.get(identity, []))
            return tag("Node", attrs[identity], content or escape("surface-" + identity))

        sentence_ref = "MAT 1:1!1-1:2!9"
        raw = tag("Sentences", {}, tag("Sentence", {"ref": sentence_ref},
                  tag("Trees", {}, tag("Tree", {}, node_xml("root:opaque"))))).encode("utf-8")
        file_id, book_id = fixture.archive(raw)
        document = fixture.element(file_id, None, "Sentences")
        sentence_element = fixture.element(file_id, document, "Sentence")
        fixture.attribute(sentence_element, "ref", sentence_ref)
        sentence = fixture.insert("sentence", {
            "file_id": file_id, "book_id": book_id, "element_id": sentence_element,
            "ordinal": 0, "ref_raw": sentence_ref,
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
            if identity in leaves:
                traversal = leaves.index(identity)
                verse, word = coordinates[identity]
                text = "surface-" + identity
                fixture.content(file_id, element, "text", text)
                fixture.token(
                    tree, book_id, node, text, attrs[identity],
                    traversal=traversal, canonical=canonical.index(identity), verse=verse, word=word,
                    overrides={"token_id": offset + 10000 + (traversal if offset else -traversal)},
                )
            for sibling, child in enumerate(children.get(identity, [])):
                add_node(child, element, node, sibling)

        add_node("root:opaque", tree_element, None, 0)
        fixture.memberships()
        schema.validate_store(db)
        db.commit()
        return db

    def mutate(self, sql: str) -> None:
        self.db.executescript(sql)

    def test_exact_apposition_path_payload_evidence_and_scope(self) -> None:
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        self.assertEqual(len(result), 2)
        for actual, anchor, children, words in zip(
            result, ("z-inner", "a-outer"),
            (("z-leaf", "a-leaf"), ("z-inner", "m-leaf")), ((3, 4), (3, 4, 8)),
        ):
            self.assertEqual(actual.candidate_kind, "apposition")
            self.assertEqual(actual.derivation_kind, "source-np-appos")
            self.assertEqual(actual.derivation_version, "1")
            self.assertEqual(actual.status, "candidate")
            self.assertEqual(actual.payload, candidate.AppositionCandidatePayload(anchor, children))
            self.assertEqual(actual.scope, candidate.CandidateScope(
                anchor, tuple(f"MAT 1:1!{word}" for word in words),
            ))
            self.assertEqual(actual.evidence, (
                candidate.EvidenceRef("anchor", "syntax_node", anchor),
                *(candidate.EvidenceRef("child", "syntax_node", child) for child in children),
            ))
            self.assertRegex(actual.candidate_id, r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(result, candidate.derive_structural_candidates(self.path, "MAT 1:1!3"))
        self.assertEqual(result, candidate.derive_structural_candidates(self.path, "MAT 1:1!4"))
        self.assertNotIn("unrelated-appos", [item.scope.source_node_id for item in result])
        self.assertEqual([row[0] for row in self.db.execute(
            "SELECT upstream_node_id FROM syntax_node WHERE parent_node_id=("
            "SELECT node_id FROM syntax_node WHERE upstream_node_id='z-inner') ORDER BY node_id",
        )], ["a-leaf", "z-leaf"])

    def test_dtos_are_frozen_typed_source_oriented_not_source_facts(self) -> None:
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        item = result[0]
        self.assertNotIsInstance(item, query.SourceEvidence)
        self.assertNotIsInstance(item, query.NodeResult)
        for obj in (item, item.source_snapshot, item.scope, item.evidence[0], item.payload):
            name = fields(obj)[0].name
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, name, "changed")
            self.assertTrue(LOCAL_IDS.isdisjoint(field.name for field in fields(obj)))
        for collection in (result, item.evidence, item.scope.member_token_refs, item.payload.child_source_node_ids):
            self.assertIsInstance(collection, tuple)
        self.assertEqual({field.name for field in fields(item)}, {
            "candidate_id", "candidate_kind", "derivation_kind", "derivation_version",
            "source_snapshot", "scope", "evidence", "payload", "status",
        })
        with self.assertRaisesRegex(query.QueryError, "evaluation status"):
            replace(item, **{"status": "accepted"})
        with self.assertRaisesRegex(query.QueryError, "unknown structural candidate kind"):
            replace(item, **{"candidate_kind": "predicate"})

    def test_valid_no_match_is_empty_unknown_is_none_invalid_is_error(self) -> None:
        self.assertEqual(candidate.derive_structural_candidates(self.path, "MAT 1:2!6"), ())
        for ref in ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9"):
            result = candidate.derive_structural_candidates(self.path, ref)
            assert result is not None
            self.assertEqual([item.candidate_kind for item in result], ["clause-structure"])
            self.assertEqual(len(svo_candidates(result)), 1)
        for ref in ("MAT 1:1!999", "mat 1:1!3", "MRK 1:1!3", "MAT 1:1!30"):
            self.assertIsNone(candidate.derive_structural_candidates(self.path, ref))
        for ref in ("", "MAT 1:1", "MAT 01:1!3", " MAT 1:1!3", "MAT 1:1!3 ", "z-leaf"):
            with self.assertRaises(query.QueryError):
                candidate.derive_structural_candidates(self.path, ref)

    def test_only_exact_rule_matches_and_linked_node_is_in_search_region(self) -> None:
        self.mutate("DROP TRIGGER node_no_update; UPDATE syntax_node SET rule='np-appos' "
                    "WHERE upstream_node_id='z-inner';")
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        self.assertEqual([item.scope.source_node_id for item in result], ["a-outer"])
        self.mutate("UPDATE syntax_node SET rule='Np-Appos' WHERE upstream_node_id='z-leaf';")
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        self.assertEqual([item.scope.source_node_id for item in result], ["z-leaf", "a-outer"])
        self.assertEqual(result[0].payload.child_source_node_ids, ())
        self.assertEqual(result[0].scope.member_token_refs, ("MAT 1:1!3",))

    def test_semantic_annotations_categories_ellipsis_and_head_do_not_create_candidates(self) -> None:
        self.mutate("DROP TRIGGER node_no_update;")
        before = candidate.derive_structural_candidates(self.path, "MAT 1:2!7")
        for cat in ("S", "V", "O", "P", "OC", "O2"):
            self.db.execute("UPDATE syntax_node SET cat=?,cl_type='Ellipsis',head_raw='1' "
                            "WHERE upstream_node_id=?", (cat, BOUNDARY))
            self.db.commit()
            result = candidate.derive_structural_candidates(self.path, "MAT 1:2!7")
            assert result is not None
            self.assertEqual([item.candidate_kind for item in result], ["clause-structure"])
            self.assertEqual(result, before)
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        self.db.execute("UPDATE syntax_node SET head_raw='0' WHERE rule='Np-Appos'")
        self.db.commit()
        self.assertEqual(result, candidate.derive_structural_candidates(self.path, "MAT 1:1!3"))
        token = query.get_token(self.path, "MAT 1:2!7")
        assert token is not None
        self.assertEqual((token.cat, token.voice), ("V", "Passive"))
        self.assertEqual(self.db.execute("SELECT frame_raw,notes_raw FROM token WHERE ref_raw='MAT 1:2!7'").fetchone(),
                         ("A1 A2 AA2", "Event Result"))

    def test_exact_discontinuous_scope_and_span_mutation(self) -> None:
        with query._open_syntax_readonly(self.path) as db:
            scope = candidate._scope(db, BOUNDARY)
        self.assertEqual(scope, candidate.CandidateScope(
            BOUNDARY, tuple(f"MAT 1:2!{word}" for word in (5, 7, 8, 9)),
        ))
        self.assertNotIn("MAT 1:2!6", scope.member_token_refs)
        before = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        svo_before = candidate.derive_structural_candidates(self.path, "MAT 1:2!5")
        assert svo_before is not None
        self.assertEqual(len(svo_candidates(svo_before)), 1)
        self.mutate("DROP TRIGGER node_no_update; UPDATE syntax_node SET start_raw='999',end_raw='1';")
        self.assertEqual(before, candidate.derive_structural_candidates(self.path, "MAT 1:1!3"))
        with query._open_syntax_readonly(self.path) as db:
            self.assertEqual(scope, candidate._scope(db, BOUNDARY))
        self.assertEqual(svo_before, candidate.derive_structural_candidates(self.path, "MAT 1:2!5"))

    def test_scope_uses_materialized_membership_not_reconstructed_topology(self) -> None:
        self.mutate("DELETE FROM node_token_membership WHERE node_id=("
                    "SELECT node_id FROM syntax_node WHERE upstream_node_id='a-outer') "
                    "AND token_id=(SELECT token_id FROM token WHERE ref_raw='MAT 1:1!8');")
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        self.assertEqual(result[1].scope.member_token_refs, ("MAT 1:1!3", "MAT 1:1!4"))

    def test_missing_evidence_and_inconsistent_refs_fail_closed(self) -> None:
        mutations = (
            ("DELETE FROM node_token_membership WHERE node_id=(SELECT node_id FROM syntax_node "
             "WHERE upstream_node_id='z-inner')", "no source token evidence"),
            ("DELETE FROM node_token_membership WHERE node_id=(SELECT node_id FROM syntax_node "
             "WHERE upstream_node_id='z-inner') AND token_id=(SELECT token_id FROM token WHERE ref_raw='MAT 1:1!3')",
             "omits selected token"),
            ("DROP TRIGGER token_no_update; UPDATE token SET ref_raw=NULL WHERE ref_raw='MAT 1:1!4'",
             "no source token ref"),
            ("DROP TRIGGER token_no_update; UPDATE token SET ref_raw='MAT 1:1!40' WHERE ref_raw='MAT 1:1!4'",
             "disagrees with source coordinates"),
            ("DROP TRIGGER node_no_update; UPDATE syntax_node SET upstream_node_id=NULL WHERE upstream_node_id='a-leaf'",
             "no source_node_id"),
        )
        for sql, message in mutations:
            with self.subTest(sql=sql):
                path = self.path.with_name("missing-evidence.sqlite3")
                db = sqlite3.connect(path)
                try:
                    self.db.backup(db)
                    db.executescript(sql)
                finally:
                    db.close()
                with self.assertRaisesRegex(query.QueryError, message):
                    candidate.derive_structural_candidates(path, "MAT 1:1!3")
                path.unlink()
        with query._open_syntax_readonly(self.path) as db:
            with self.assertRaisesRegex(query.QueryError, "unresolved"):
                candidate._scope(db, "missing")

    def test_ambiguity_cycles_and_missing_links_are_not_empty_success(self) -> None:
        cases = (
            ("UPDATE syntax_node SET upstream_node_id='z-inner' WHERE upstream_node_id='connector'",
             "ambiguous source_node_id"),
            ("UPDATE syntax_node SET upstream_node_id='m-leaf' WHERE upstream_node_id='connector'",
             "ambiguous source_node_id"),
            ("UPDATE syntax_node SET parent_node_id=(SELECT node_id FROM syntax_node WHERE upstream_node_id='z-inner'),"
             "sibling_ordinal=2 WHERE upstream_node_id='root:opaque'", "cyclic syntax ancestry"),
            ("UPDATE syntax_node SET parent_node_id=999999 WHERE upstream_node_id='z-inner'",
             "missing or cross-Tree syntax parent"),
        )
        for sql, message in cases:
            with self.subTest(sql=sql):
                path = self.path.with_name("corrupt.sqlite3")
                db = sqlite3.connect(path)
                try:
                    self.db.backup(db)
                    db.executescript("DROP TRIGGER node_no_update; " + sql)
                finally:
                    db.close()
                with self.assertRaisesRegex(query.QueryError, message):
                    candidate.derive_structural_candidates(path, "MAT 1:1!3")
                path.unlink()
        SchemaFixture(self.db).archive(number=2)
        self.db.commit()
        with self.assertRaisesRegex(query.QueryError, "ambiguous book"):
            candidate.derive_structural_candidates(self.path, "MAT 1:1!3")

    def test_wrong_database_and_missing_snapshot_are_explicit_errors(self) -> None:
        missing = self.path.with_name("missing.sqlite3")
        with self.assertRaises(query.QueryError):
            candidate.derive_structural_candidates(missing, "MAT 1:1!999")
        self.assertFalse(missing.exists())
        broken = self.path.with_name("broken.sqlite3")
        broken.write_bytes(b"not SQLite")
        with self.assertRaises(query.QueryError):
            candidate.derive_structural_candidates(broken, "MAT 1:1!999")
        for sql in ("PRAGMA user_version=3", "DROP TABLE node_token_membership",
                    "ALTER TABLE dataset_snapshot RENAME COLUMN revision TO missing_revision"):
            path = self.path.with_name("wrong-schema.sqlite3")
            db = sqlite3.connect(path)
            try:
                self.db.backup(db)
                db.executescript(sql)
            finally:
                db.close()
            for ref in ("MAT 1:1!3", "MAT 1:1!999"):
                with self.assertRaises(query.QueryError):
                    candidate.derive_structural_candidates(path, ref)
            path.unlink()
        self.mutate("PRAGMA foreign_keys=OFF; DROP TRIGGER book_no_update; UPDATE book SET snapshot_id=999999;")
        with self.assertRaisesRegex(query.QueryError, "linked source snapshot"):
            candidate.derive_structural_candidates(self.path, "MAT 1:1!3")

    def test_all_surrogate_ids_and_all_candidate_fields_are_invariant(self) -> None:
        path = self.path.with_name("reallocated.sqlite3")
        self.make_store(path, 20000)
        for ref in ("MAT 1:1!3", "MAT 1:1!4", "MAT 1:1!8", "MAT 1:1!1"):
            left = query.get_token(self.path, ref)
            right = query.get_token(path, ref)
            assert left is not None and right is not None
            for key in LOCAL_IDS:
                self.assertNotEqual(getattr(left, key), getattr(right, key), key)
            self.assertEqual(candidate.derive_structural_candidates(self.path, ref),
                             candidate.derive_structural_candidates(path, ref))
        self.assertNotEqual(
            self.db.execute("SELECT upstream_node_id FROM syntax_node ORDER BY node_id").fetchall(),
            sqlite_rows(path, "SELECT upstream_node_id FROM syntax_node ORDER BY node_id"),
        )

    def test_snapshot_binding_reads_actual_provenance_and_changes_identity(self) -> None:
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        item = result[0]
        raw = self.db.execute("SELECT original_bytes FROM source_file").fetchone()[0]
        digest = hashlib.sha256(raw).hexdigest().upper()
        self.assertEqual(item.source_snapshot, candidate.SourceSnapshot(
            "MACULA Greek", "SBLGNT", "urn:unit2-synthetic-schema-test", "1" * 40,
            digest, "fixtures/synthetic.xml", digest,
        ))
        for column, value in (("revision", "2" * 40), ("manifest_sha256", "A" * 64)):
            path = self.path.with_name("snapshot.sqlite3")
            db = sqlite3.connect(path)
            try:
                self.db.backup(db)
                db.execute("DROP TRIGGER snapshot_no_update")
                db.execute(f"UPDATE dataset_snapshot SET {column}=?", (value,))
                db.commit()
            finally:
                db.close()
            changed = candidate.derive_structural_candidates(path, "MAT 1:1!3")
            assert changed is not None
            self.assertNotEqual(item.source_snapshot, changed[0].source_snapshot)
            self.assertNotEqual(item.candidate_id, changed[0].candidate_id)
            self.assertEqual(item.scope, changed[0].scope)
            path.unlink()
        self.assertEqual(item.source_snapshot.revision, "1" * 40)

    def test_identity_serialization_is_explicit_utf8_and_sha256(self) -> None:
        snapshot = candidate.SourceSnapshot("family", "edition", "urn:source", "revision",
                                            "manifest", "source.xml", "digest")
        scope = candidate.CandidateScope("n:\u03b1", ("MAT 1:1!3",))
        evidence = (candidate.EvidenceRef("anchor", "syntax_node", "n:\u03b1"),)
        payload = candidate.AppositionCandidatePayload("n:\u03b1", ())
        expected = (
            '["macula.structural-candidate.v1",["family","edition","urn:source","revision",'
            '"manifest","source.xml","digest"],"apposition","source-np-appos","1",'
            '["n:\\u03b1",["MAT 1:1!3"]],[["anchor","syntax_node","n:\\u03b1"]],["n:\\u03b1",[]]]'
        ).encode("utf-8")
        self.assertEqual(candidate._identity_bytes(
            snapshot, "apposition", "source-np-appos", "1", scope, evidence, payload,
        ), expected)
        self.assertEqual(candidate._candidate_id(
            snapshot, "apposition", "source-np-appos", "1", scope, evidence, payload,
        ), "sha256:" + hashlib.sha256(expected).hexdigest())
        with self.assertRaisesRegex(query.QueryError, "unknown structural candidate kind"):
            candidate._candidate_id(snapshot, "NPofNP", "source-np-appos", "1", scope, evidence, payload)

    def test_identity_changes_with_version_scope_evidence_order_payload_and_source_bytes(self) -> None:
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        item = result[0]
        inputs = {
            "source_snapshot": item.source_snapshot, "candidate_kind": item.candidate_kind,
            "derivation_kind": item.derivation_kind, "derivation_version": item.derivation_version,
            "scope": item.scope, "evidence": item.evidence, "payload": item.payload,
        }
        mutations = (
            {"derivation_version": "2"},
            {"derivation_kind": "changed-derivation"},
            {"scope": replace(item.scope, source_node_id="different-anchor")},
            {"scope": replace(item.scope, member_token_refs=("MAT 1:1!3",))},
            {"evidence": (replace(item.evidence[0], source_node_id="different-evidence"), *item.evidence[1:])},
            {"evidence": tuple(reversed(item.evidence))},
            {"payload": replace(item.payload, child_source_node_ids=tuple(reversed(item.payload.child_source_node_ids)))},
            {"source_snapshot": replace(item.source_snapshot, source_sha256="A" * 64)},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertNotEqual(item.candidate_id, candidate._candidate_id(**{**inputs, **mutation}))

    def test_process_hashseed_and_database_location_do_not_enter_identity(self) -> None:
        result = candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert result is not None
        expected = "\n".join(item.candidate_id for item in result)
        code = ("from scripts.structural_candidates import derive_structural_candidates; import sys; "
                "print('\\n'.join(c.candidate_id for c in derive_structural_candidates(sys.argv[1], 'MAT 1:1!3')))")
        moved = self.path.with_name("different location.sqlite3")
        moved.write_bytes(self.path.read_bytes())
        for seed, path in (("1", self.path), ("42", moved)):
            actual = subprocess.run(
                [sys.executable, "-B", "-c", code, str(path)],
                cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONHASHSEED": seed},
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(actual.stdout.strip(), expected)

    def test_production_is_readonly_no_xml_no_persistence_and_closes_connections(self) -> None:
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
            self.assertIsNotNone(candidate.derive_structural_candidates(self.path, "MAT 1:1!3"))
            self.assertIsNone(candidate.derive_structural_candidates(self.path, "MAT 1:1!999"))
            with patch.object(candidate, "_scope", side_effect=query.QueryError("explicit scope failure")):
                with self.assertRaisesRegex(query.QueryError, "explicit scope failure"):
                    candidate.derive_structural_candidates(self.path, "MAT 1:1!3")
        self.assertEqual(len(opened), 6)
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")
        self.assertFalse(any(sql.lstrip().split()[0].upper() in (
            "INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER", "ATTACH", "VACUUM",
        ) for sql in statements))
        self.assertTrue(any("main.node_token_membership" in sql for sql in statements))
        self.assertFalse(any("expected_node_token_membership" in sql for sql in statements))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall(), catalog)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (2,))


def sqlite_rows(path: Path, sql: str) -> list[tuple[object, ...]]:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        return db.execute(sql).fetchall()
    finally:
        db.close()


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT7_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT7_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit7MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_size = _LOCAL_DATABASE.stat().st_size
        cls.before_hash = hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper()
        cls.before_catalog = sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name")
        cls.before_version = sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version")

    @classmethod
    def tearDownClass(cls) -> None:
        if (_LOCAL_DATABASE.stat().st_size != cls.before_size
                or hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest().upper() != cls.before_hash):
            raise AssertionError("Unit 7 integration database bytes changed")
        if sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name") != cls.before_catalog:
            raise AssertionError("Unit 7 integration schema/index inventory changed")
        if sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version") != cls.before_version:
            raise AssertionError("Unit 7 integration schema version changed")
        print(f"Unit 7 read-only store unchanged: {_LOCAL_DATABASE}; {cls.before_size} bytes; "
              f"SHA-256 {cls.before_hash}; user_version {cls.before_version[0][0]}", flush=True)

    def test_matthew_1_1_fixed_nested_apposition_path(self) -> None:
        result = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3")
        assert result is not None
        self.assertEqual(len(result), 3)
        for actual, (anchor, children, words) in zip(result, MATTHEW_APPOSITIONS):
            self.assertEqual((actual.candidate_kind, actual.derivation_kind, actual.derivation_version, actual.status),
                             ("apposition", "source-np-appos", "1", "candidate"))
            self.assertEqual(actual.payload, candidate.AppositionCandidatePayload(anchor, children))
            self.assertEqual(actual.scope, candidate.CandidateScope(
                anchor, tuple(f"MAT 1:1!{word}" for word in words),
            ))
            self.assertEqual(actual.evidence, (
                candidate.EvidenceRef("anchor", "syntax_node", anchor),
                *(candidate.EvidenceRef("child", "syntax_node", child) for child in children),
            ))
            node = query.get_node(_LOCAL_DATABASE, anchor)
            children_result = query.get_children(_LOCAL_DATABASE, anchor)
            members_result = query.get_members(_LOCAL_DATABASE, anchor)
            assert node is not None and children_result is not None and members_result is not None
            self.assertEqual(node.rule, "Np-Appos")
            self.assertEqual(tuple(n.source_node_id for n in children_result), children)
            self.assertEqual(tuple(t.ref for t in members_result), actual.scope.member_token_refs)
            self.assertEqual(actual.source_snapshot.revision, unit1.REVISION)
            self.assertEqual(actual.source_snapshot.source_sha256, unit1.SHA256)
            print(f"Unit 7 apposition: {actual.candidate_id}; anchor={anchor}; "
                  f"children={children}; scope={actual.scope.member_token_refs}", flush=True)
        self.assertEqual(result, candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3"))
        self.assertEqual(len({item.candidate_id for item in result}), 3)

    def test_matthew_1_1_verbless_and_no_semantic_or_fabricated_material(self) -> None:
        evidence = query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3")
        verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 1)
        result = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3")
        assert evidence is not None and verse is not None and result is not None
        self.assertEqual([(node.rule, node.cl_type) for node in evidence.ancestors if node.cat == "CL"],
                         [("P2CL", "Verbless")])
        self.assertEqual([token.cat for token in verse.tokens], ["noun"] * 8)
        for item in result:
            self.assertEqual(item.candidate_kind, "apposition")
            self.assertEqual(set(asdict(item.payload)), {"anchor_source_node_id", "child_source_node_ids"})
            self.assertEqual(set(asdict(item.scope)), {"source_node_id", "member_token_refs"})
            self.assertTrue(set(item.scope.member_token_refs).issubset({token.ref for token in verse.tokens}))
        self.assertEqual(evidence, query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3"))

    def test_post_unit9_svo_preserves_unit7_exact_scope_invariants(self) -> None:
        node = query.get_node(_LOCAL_DATABASE, BOUNDARY)
        assert node is not None
        self.assertEqual((node.rule, node.start_raw, node.end_raw), ("S-V-O", "5", "8"))
        with query._open_syntax_readonly(_LOCAL_DATABASE) as db:
            scope = candidate._scope(db, BOUNDARY)
        self.assertEqual(scope.member_token_refs, SVO_SCOPE)
        self.assertNotIn("MAT 1:2!6", scope.member_token_refs)
        result = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:2!5")
        assert result is not None
        self.assertTrue(result)
        matched = svo_candidates(result)
        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0].scope, candidate.CandidateScope(BOUNDARY, SVO_SCOPE))
        self.assertNotIn("MAT 1:2!6", matched[0].scope.member_token_refs)


if __name__ == "__main__":
    unittest.main()
