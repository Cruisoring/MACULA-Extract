from dataclasses import FrozenInstanceError, asdict, fields, replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from xml.sax.saxutils import escape

from scripts import evaluated_interpretations as evaluation
from scripts import source_query as query
from scripts import source_schema as schema
from scripts import structural_candidates as candidate
from tests.test_unit2 import SchemaFixture, tag
from tests import test_unit7 as unit7
from tests import test_unit8 as unit8


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "matthew-1-2-svo-candidate.expected.json"
EXPECTED = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
ANCHOR = "400010020050040"
SUBJECT = "400010020050012"
VERBAL = "400010020070012"
OBJECT = "400010020080021"
REFS = ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
APPOSITION_IDS = (
    "sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c",
    "sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f",
    "sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220",
)


def frozen_payload() -> candidate.ClauseStructurePayload:
    payload = EXPECTED["payload"]
    return candidate.ClauseStructurePayload(
        payload["anchor_source_node_id"], payload["source_rule"], payload["source_head_raw"],
        tuple(candidate.ClauseComponent(
            item["source_node_id"], item["source_cat"], item["sibling_ordinal"],
            item["component_role"], tuple(item["member_token_refs"]),
        ) for item in payload["components"]),
    )


class Unit9FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit9-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "clause # fixture.sqlite3"
        self.db = self.make_store(self.path)

    def make_store(self, path: Path, offset: int = 0) -> sqlite3.Connection:
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        schema.bootstrap(db)
        fixture = SchemaFixture(db, offset)
        attrs = {
            "root:opaque": {"Cat": "S"},
            "connector": {"Cat": "conj", "ref": "MAT 1:2!6"},
            ANCHOR: {"Cat": "CL", "Rule": "S-V-O", "Head": "1", "Start": "5", "End": "8"},
            SUBJECT: {"Cat": "S", "ref": "MAT 1:2!5"},
            VERBAL: {"Cat": "V", "ref": "MAT 1:2!7", "Voice": "Passive", "Frame": "A1 A2"},
            OBJECT: {"Cat": "O"},
            "z-eight": {"Cat": "OC", "ref": "MAT 1:2!8"},
            "a-nine": {"Cat": "O2", "ref": "MAT 1:2!9"},
            "off-ten": {"Cat": "noun", "ref": "MAT 1:2!10"},
        }
        children = {
            "root:opaque": ["connector", ANCHOR, "off-ten"],
            ANCHOR: [SUBJECT, VERBAL, OBJECT],
            OBJECT: ["z-eight", "a-nine"],
        }
        for identity, values in attrs.items():
            values["nodeId"] = identity

        def node_xml(identity: str) -> str:
            content = "".join(node_xml(child) for child in children.get(identity, []))
            return tag("Node", attrs[identity], content or escape(identity))

        sentence_ref = "MAT 1:2!5-1:2!10"
        raw = tag("Sentences", {}, tag("Sentence", {"ref": sentence_ref},
                  tag("Trees", {}, tag("Tree", {}, node_xml("root:opaque"))))).encode("utf-8")
        file_id, book_id = fixture.archive(raw)
        document = fixture.element(file_id, None, "Sentences")
        sentence_element = fixture.element(file_id, document, "Sentence")
        fixture.attribute(sentence_element, "ref", sentence_ref)
        sentence = fixture.insert("sentence", {
            "sentence_id": offset + 1,
            "file_id": file_id, "book_id": book_id, "element_id": sentence_element,
            "ordinal": 0, "ref_raw": sentence_ref,
        })
        wrapper = fixture.element(file_id, sentence_element, "Trees")
        tree_element = fixture.element(file_id, wrapper, "Tree")
        tree = fixture.insert("tree", {
            "tree_id": offset + 1, "sentence_id": sentence, "element_id": tree_element, "ordinal": 0,
        })
        identities = list(attrs)
        traversal = []

        def add_node(identity: str, parent_element: int, parent: int | None, ordinal: int) -> None:
            element = fixture.element(file_id, parent_element, "Node")
            fixture.attributes(element, attrs[identity])
            index = identities.index(identity)
            node = fixture.node(tree, element, parent, ordinal, attrs[identity],
                                {"node_id": offset + 1000 + (index if offset else -index)})
            if "ref" in attrs[identity]:
                word = int(attrs[identity]["ref"].split("!")[1])
                fixture.content(file_id, element, "text", identity)
                fixture.token(
                    tree, book_id, node, identity, attrs[identity],
                    traversal=len(traversal), canonical=word - 5, verse=2, word=word,
                    overrides={"token_id": offset + 10000 + (word if offset else -word)},
                )
                traversal.append(identity)
            for sibling, child in enumerate(children.get(identity, [])):
                add_node(child, element, node, sibling)

        add_node("root:opaque", tree_element, None, 0)
        fixture.memberships()
        schema.validate_store(db)
        db.commit()
        return db

    def derive(self, path: Path | None = None, ref: str = REFS[0]) -> candidate.ClauseStructureCandidate:
        result = candidate.derive_structural_candidates(self.path if path is None else path, ref)
        assert result is not None
        clauses = [item for item in result if isinstance(item, candidate.ClauseStructureCandidate)]
        self.assertEqual(len(clauses), 1)
        return clauses[0]

    def mutate(self, sql: str) -> None:
        self.db.executescript(sql)

    def node_update(self, assignment: str, identity: str = ANCHOR) -> None:
        self.mutate("DROP TRIGGER IF EXISTS node_no_update; UPDATE syntax_node SET "
                    + assignment + " WHERE upstream_node_id='" + identity + "';")

    def member_sql(self, identity: str, ref: str) -> str:
        return ("SELECT n.node_id,t.token_id,n.tree_id FROM syntax_node n CROSS JOIN token t "
                f"WHERE n.upstream_node_id='{identity}' AND t.ref_raw='{ref}'")

    def test_u9_01_frozen_dtos_and_closed_constants(self) -> None:
        item = self.derive()
        for obj in (item, item.payload, *item.payload.components, item.scope,
                    item.source_snapshot, *item.evidence):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, fields(obj)[0].name, "changed")
        for change in ({"candidate_kind": "apposition"}, {"status": "accepted"},
                       {"derivation_kind": "other"}, {"derivation_version": "2"}):
            with self.subTest(change=change), self.assertRaises(query.QueryError):
                replace(item, **change)
        self.assertEqual((item.candidate_kind, item.derivation_kind, item.derivation_version, item.status),
                         ("clause-structure", "source-rule-s-v-o", "1", "candidate"))

    def test_u9_02_rule_is_source_exact(self) -> None:
        for rule in ("s-v-o", "S-V-O ", "Np-Appos", ""):
            self.node_update("rule='" + rule + "'")
            result = candidate.derive_structural_candidates(self.path, REFS[0])
            assert result is not None
            self.assertFalse(any(isinstance(c, candidate.ClauseStructureCandidate) for c in result))

    def test_u9_03_exact_child_sequence_and_ordinals(self) -> None:
        self.assertEqual([(c.source_cat, c.sibling_ordinal) for c in self.derive().payload.components],
                         [("S", 0), ("V", 1), ("O", 2)])
        self.node_update("cat='O2'", OBJECT)
        self.assertEqual(candidate.derive_structural_candidates(self.path, REFS[0]), ())

    def test_u9_04_head_one_selects_verbal_child(self) -> None:
        item = self.derive()
        self.assertEqual(item.payload.source_head_raw, "1")
        self.assertEqual(item.payload.components[int(item.payload.source_head_raw)].source_node_id, VERBAL)
        for head in ("NULL", "'0'", "'2'"):
            self.node_update("head_raw=" + head)
            self.assertEqual(candidate.derive_structural_candidates(self.path, REFS[0]), ())

    def test_u9_05_anchor_exact_scope(self) -> None:
        self.assertEqual(self.derive().scope, candidate.CandidateScope(ANCHOR, REFS))

    def test_u9_06_frozen_subject_membership(self) -> None:
        self.assertEqual(self.derive().payload.components[0].member_token_refs, ("MAT 1:2!5",))

    def test_u9_07_frozen_verbal_membership(self) -> None:
        self.assertEqual(self.derive().payload.components[1].member_token_refs, ("MAT 1:2!7",))

    def test_u9_08_frozen_object_membership(self) -> None:
        self.assertEqual(self.derive().payload.components[2].member_token_refs, ("MAT 1:2!8", "MAT 1:2!9"))

    def test_u9_09_pairwise_disjoint(self) -> None:
        components = self.derive().payload.components
        for left in range(3):
            for right in range(left + 1, 3):
                self.assertTrue(set(components[left].member_token_refs).isdisjoint(
                    components[right].member_token_refs))

    def test_u9_10_union_equals_anchor(self) -> None:
        item = self.derive()
        self.assertEqual(set(item.scope.member_token_refs),
                         {ref for c in item.payload.components for ref in c.member_token_refs})

    def test_u9_11_token_six_excluded_everywhere(self) -> None:
        item = self.derive()
        for refs in (item.scope.member_token_refs, *(c.member_token_refs for c in item.payload.components)):
            self.assertNotIn("MAT 1:2!6", refs)

    def test_u9_12_frozen_evidence_order(self) -> None:
        self.assertEqual([asdict(ref) for ref in self.derive().evidence], EXPECTED["evidence"])

    def test_u9_13_frozen_payload(self) -> None:
        self.assertEqual(self.derive().payload, frozen_payload())
        self.assertIsInstance(self.derive().payload.components, tuple)

    def test_u9_14_independent_canonical_serialization(self) -> None:
        item = self.derive()
        p = EXPECTED["payload"]
        expected = [
            "macula.structural-candidate.v1", list(asdict(item.source_snapshot).values()),
            "clause-structure", "source-rule-s-v-o", "1", [ANCHOR, list(REFS)],
            [[e["role"], e["kind"], e["source_node_id"]] for e in EXPECTED["evidence"]],
            [ANCHOR, "S-V-O", "1",
             [[c["component_role"], c["source_cat"], c["sibling_ordinal"],
               c["source_node_id"], c["member_token_refs"]] for c in p["components"]]],
        ]
        encoded = json.dumps(expected, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.assertEqual(candidate._identity_bytes(
            item.source_snapshot, item.candidate_kind, item.derivation_kind,
            item.derivation_version, item.scope, item.evidence, item.payload,
        ), encoded)
        self.assertEqual(item.candidate_id, "sha256:" + hashlib.sha256(encoded).hexdigest())

    def test_u9_15_frozen_identity_with_frozen_snapshot(self) -> None:
        item = self.derive()
        self.assertEqual(candidate._candidate_id(
            candidate.SourceSnapshot(**EXPECTED["source_snapshot"]), item.candidate_kind,
            item.derivation_kind, item.derivation_version, item.scope, item.evidence, item.payload,
        ), EXPECTED["candidate_id"])

    def test_u9_16_identity_sensitive_to_all_protocol_inputs(self) -> None:
        item = self.derive()
        inputs = {name: getattr(item, name) for name in (
            "source_snapshot", "candidate_kind", "derivation_kind", "derivation_version",
            "scope", "evidence", "payload",
        )}
        component = item.payload.components[0]
        mutations = [
            {"derivation_version": "2"}, {"derivation_kind": "changed"},
            {"scope": replace(item.scope, source_node_id="different")},
            {"scope": replace(item.scope, member_token_refs=REFS[:-1])},
            {"evidence": tuple(reversed(item.evidence))},
            {"evidence": (replace(item.evidence[0], role="child"), *item.evidence[1:])},
            {"payload": replace(item.payload, source_head_raw="0")},
            {"payload": replace(item.payload, source_rule="changed")},
            {"payload": replace(item.payload, anchor_source_node_id="different")},
            {"payload": replace(item.payload, components=tuple(reversed(item.payload.components)))},
        ]
        for field in fields(item.source_snapshot):
            mutations.append({"source_snapshot": replace(item.source_snapshot, **{field.name: "changed"})})
        for name, value in (("source_node_id", "changed"), ("source_cat", "V"),
                            ("sibling_ordinal", 2), ("component_role", "verbal-component"),
                            ("member_token_refs", ("MAT 1:2!6",))):
            mutations.append({"payload": replace(item.payload, components=(
                replace(component, **{name: value}), *item.payload.components[1:],
            ))})
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assertNotEqual(item.candidate_id, candidate._candidate_id(**{**inputs, **mutation}))

    def test_u9_17_surrogate_pk_reallocation(self) -> None:
        moved = self.path.with_name("reallocated.sqlite3")
        other = self.make_store(moved, 20000)
        self.assertEqual(self.derive(), self.derive(moved))
        for table, column in (("dataset_snapshot", "snapshot_id"), ("book", "book_id"),
                              ("source_file", "file_id"), ("xml_element", "element_id"),
                              ("sentence", "sentence_id"), ("tree", "tree_id"),
                              ("syntax_node", "node_id"), ("token", "token_id")):
            self.assertNotEqual(self.db.execute(f"SELECT min({column}) FROM {table}").fetchone(),
                                other.execute(f"SELECT min({column}) FROM {table}").fetchone())

    def test_u9_18_pk_and_numeric_order_not_lexical(self) -> None:
        before = self.derive()
        self.assertEqual(self.db.execute(
            "SELECT ref_raw FROM token WHERE ref_raw IN ('MAT 1:2!8','MAT 1:2!9') ORDER BY token_id",
        ).fetchall(), [("MAT 1:2!9",), ("MAT 1:2!8",)])
        self.assertNotEqual([r[0] for r in self.db.execute(
            "SELECT upstream_node_id FROM syntax_node WHERE parent_node_id="
            f"(SELECT node_id FROM syntax_node WHERE upstream_node_id='{ANCHOR}') ORDER BY node_id",
        )], [SUBJECT, VERBAL, OBJECT])
        for identity in (ANCHOR, OBJECT):
            self.mutate("INSERT INTO node_token_membership " + self.member_sql(identity, "MAT 1:2!10"))
        self.assertEqual(self.derive().payload.components[2].member_token_refs,
                         ("MAT 1:2!8", "MAT 1:2!9", "MAT 1:2!10"))
        self.assertNotEqual(before.candidate_id, self.derive().candidate_id)

    def test_u9_19_start_end_are_not_membership(self) -> None:
        before = self.derive()
        for start, end in (("999", "1"), ("5", "9"), ("", "")):
            self.node_update(f"start_raw='{start}',end_raw='{end}'")
            self.assertEqual(before, self.derive())

    def test_u9_20_missing_child_membership_errors(self) -> None:
        self.mutate("DELETE FROM node_token_membership WHERE node_id="
                    f"(SELECT node_id FROM syntax_node WHERE upstream_node_id='{SUBJECT}')")
        with self.assertRaisesRegex(query.QueryError, "empty required membership"):
            self.derive()

    def test_u9_21_overlapping_components_error(self) -> None:
        self.mutate("INSERT INTO node_token_membership " + self.member_sql(OBJECT, REFS[0]))
        with self.assertRaisesRegex(query.QueryError, "overlapping"):
            self.derive()

    def test_u9_22_child_outside_anchor_errors(self) -> None:
        self.mutate("INSERT INTO node_token_membership " + self.member_sql(OBJECT, "MAT 1:2!10"))
        with self.assertRaisesRegex(query.QueryError, "union differs"):
            self.derive()

    def test_u9_23_unassigned_anchor_member_errors(self) -> None:
        self.mutate("DELETE FROM node_token_membership WHERE node_id="
                    f"(SELECT node_id FROM syntax_node WHERE upstream_node_id='{OBJECT}') "
                    "AND token_id=(SELECT token_id FROM token WHERE ref_raw='MAT 1:2!9')")
        with self.assertRaisesRegex(query.QueryError, "union differs"):
            self.derive()

    def test_u9_24_all_member_lookups_equal(self) -> None:
        expected = self.derive()
        for ref in REFS:
            self.assertEqual(self.derive(ref=ref), expected)

    def test_u9_25_connector_lookup_is_negative(self) -> None:
        self.assertEqual(candidate.derive_structural_candidates(self.path, "MAT 1:2!6"), ())
        self.assertIsNone(candidate.derive_structural_candidates(self.path, "MAT 1:2!999"))

    def test_u9_26_verbless_is_not_svo(self) -> None:
        self.node_update("rule='P2CL',cl_type='Verbless'")
        self.assertEqual(candidate.derive_structural_candidates(self.path, REFS[0]), ())

    def test_u9_27_apposition_regression_and_mixed_nearest_first(self) -> None:
        fixture = unit7.Unit7FastTests(methodName="runTest")
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        before = candidate.derive_structural_candidates(fixture.path, "MAT 1:1!3")
        fixture.test_exact_apposition_path_payload_evidence_and_scope()
        fixture.mutate("DROP TRIGGER node_no_update; UPDATE syntax_node SET "
                       "start_raw='999',end_raw='1',head_raw='0' WHERE rule='Np-Appos'")
        self.assertEqual(before, candidate.derive_structural_candidates(fixture.path, "MAT 1:1!3"))
        self.node_update("rule='Np-Appos'", "root:opaque")
        result = candidate.derive_structural_candidates(self.path, REFS[0])
        assert result is not None
        self.assertEqual([c.candidate_kind for c in result], ["clause-structure", "apposition"])
        self.node_update("rule='Np-Appos'", OBJECT)
        result = candidate.derive_structural_candidates(self.path, REFS[2])
        assert result is not None
        self.assertEqual([c.candidate_kind for c in result], ["apposition", "clause-structure", "apposition"])

    def test_u9_28_closed_source_facing_shape(self) -> None:
        item = self.derive()
        self.assertEqual(set(asdict(item)), {
            "candidate_id", "candidate_kind", "derivation_kind", "derivation_version", "status",
            "source_snapshot", "scope", "evidence", "payload",
        })
        self.assertEqual(set(asdict(item.payload)), {
            "anchor_source_node_id", "source_rule", "source_head_raw", "components",
        })
        self.assertEqual(set(asdict(item.payload.components[0])), {
            "source_node_id", "source_cat", "sibling_ordinal", "component_role", "member_token_refs",
        })
        self.assertEqual(set(asdict(item.source_snapshot)), set(EXPECTED["source_snapshot"]))
        for obj in (item, item.payload, item.scope, *item.payload.components, *item.evidence):
            self.assertTrue(unit7.LOCAL_IDS.isdisjoint(field.name for field in fields(obj)))

    def test_u9_29_readonly_rejection_closure_and_no_sidecars(self) -> None:
        before = self.path.read_bytes()
        catalog = self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall()
        connect = query._connect_readonly
        opened = []

        def checked_connect(path: Path) -> sqlite3.Connection:
            db = connect(path)
            opened.append(db)
            for mode in (1, 0):
                db.execute(f"PRAGMA query_only={mode}")
                for sql in ("INSERT INTO token DEFAULT VALUES", "UPDATE token SET english='changed'",
                            "DELETE FROM node_token_membership", "CREATE TABLE forbidden(x)"):
                    with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                        db.execute(sql)
            db.execute("PRAGMA query_only=ON")
            return db

        with patch.object(query, "_connect_readonly", side_effect=checked_connect):
            self.derive()
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(catalog, self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall())
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (2,))
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_u9_30_malformed_topology_and_unknown_input(self) -> None:
        for ref in ("", "MAT 01:2!5", "MAT 1:2!5 "):
            with self.assertRaises(query.QueryError):
                candidate.derive_structural_candidates(self.path, ref)
        self.node_update("sibling_ordinal=5", OBJECT)
        with self.assertRaisesRegex(query.QueryError, "sibling ordinal"):
            self.derive()

    def test_malformed_and_out_of_range_head_errors(self) -> None:
        for head in ("", "01", "-1", "1.0", " 1", "3", "9" * 20):
            self.node_update("head_raw='" + head + "'")
            with self.subTest(head=head), self.assertRaisesRegex(query.QueryError, "Head"):
                self.derive()

    def test_missing_and_ambiguous_source_identity_errors(self) -> None:
        self.node_update("upstream_node_id=NULL", OBJECT)
        with self.assertRaisesRegex(query.QueryError, "no source_node_id"):
            self.derive()
        self.mutate(f"UPDATE syntax_node SET upstream_node_id='{OBJECT}' WHERE upstream_node_id IS NULL; "
                    f"UPDATE syntax_node SET upstream_node_id='{SUBJECT}' WHERE upstream_node_id='off-ten'")
        with self.assertRaisesRegex(query.QueryError, "ambiguous source_node_id"):
            self.derive()

    def test_incomplete_coordinates_and_snapshot_error(self) -> None:
        cases = (
            ("ALTER TABLE token RENAME TO original_tokens; CREATE TABLE token AS SELECT * FROM original_tokens; "
             "UPDATE token SET chapter=NULL WHERE ref_raw='MAT 1:2!9'",
             "canonical scripture coordinates"),
            ("DROP TRIGGER token_no_update; UPDATE token SET ref_raw='MAT 1:2!90' WHERE ref_raw='MAT 1:2!9'",
             "canonical scripture coordinates"),
            ("ALTER TABLE dataset_snapshot RENAME TO original_snapshots; "
             "CREATE TABLE dataset_snapshot AS SELECT * FROM original_snapshots; "
             "UPDATE dataset_snapshot SET revision=''",
             "linked source snapshot"),
            ("PRAGMA foreign_keys=OFF; DROP TRIGGER file_no_update; UPDATE source_file SET snapshot_id=99999",
             "linked source snapshot"),
        )
        for index, (sql, message) in enumerate(cases):
            path = self.path.with_name(f"corrupt-{index}.sqlite3")
            db = sqlite3.connect(path)
            try:
                self.db.backup(db)
                db.executescript(sql)
            finally:
                db.close()
            with self.subTest(sql=sql), self.assertRaisesRegex(query.QueryError, message):
                self.derive(path)

    def test_duplicate_membership_and_sibling_ordinal_error(self) -> None:
        self.mutate(
            "ALTER TABLE node_token_membership RENAME TO original_memberships; "
            "CREATE TABLE node_token_membership AS SELECT * FROM original_memberships; "
            "INSERT INTO node_token_membership SELECT * FROM original_memberships WHERE node_id="
            f"(SELECT node_id FROM syntax_node WHERE upstream_node_id='{OBJECT}')"
        )
        with self.assertRaises(query.QueryError):
            self.derive()
        self.mutate("DELETE FROM node_token_membership WHERE rowid NOT IN "
                    "(SELECT min(rowid) FROM node_token_membership GROUP BY node_id,token_id)")
        self.mutate("ALTER TABLE syntax_node RENAME TO original_nodes; "
                    "CREATE TABLE syntax_node AS SELECT * FROM original_nodes; "
                    f"UPDATE syntax_node SET sibling_ordinal=1 WHERE upstream_node_id='{OBJECT}'")
        with self.assertRaisesRegex(query.QueryError, "sibling ordinal"):
            self.derive()

    def test_missing_anchor_membership_error(self) -> None:
        self.mutate("DELETE FROM node_token_membership WHERE node_id="
                    f"(SELECT node_id FROM syntax_node WHERE upstream_node_id='{ANCHOR}')")
        with self.assertRaisesRegex(query.QueryError, "empty required membership"):
            self.derive()

    def test_semantic_annotations_do_not_change_derivation(self) -> None:
        before = self.derive()
        for cat in ("S", "V", "O", "P", "OC", "O2"):
            self.node_update(f"cat='{cat}',cl_type='Ellipsis'")
            self.assertEqual(before, self.derive())
        self.assertEqual(self.db.execute("SELECT voice_raw,frame_raw FROM token WHERE ref_raw='MAT 1:2!7'").fetchone(),
                         ("Passive", "A1 A2"))

    def test_unit8_amendment_accepts_registered_svo_candidate(self) -> None:
        item = self.derive()
        before_id = item.candidate_id
        record = evaluation.create_evaluated_interpretation(
            self.path, item, evaluator_class="human", evaluator_label="reviewer",
            evaluation_protocol_id="human-structural-adequacy", evaluation_protocol_version="1",
            disposition="accepted", rationale_evidence=(
                evaluation.RationaleCitation("syntax_node", ANCHOR),
            ), rationale_note=evaluation.RationaleNote("Structural evidence inspected.", "en"),
            event_key="unit9-amendment-compatibility",
        )
        self.assertEqual(record.record_protocol, "macula.evaluated-structural-interpretation.v1")
        self.assertEqual(record.evaluation_protocol_id, "human-structural-adequacy")
        self.assertEqual(record.evaluation_protocol_version, "1")
        self.assertEqual(record.evaluator_class, "human")
        self.assertEqual(record.candidate, item)
        self.assertEqual(record.candidate.status, "candidate")
        self.assertEqual(record.candidate.candidate_id, before_id)
        self.assertEqual(item.candidate_id, before_id)
        evaluation.verify_evaluated_interpretation(record)
        evaluation.verify_evaluated_interpretation(record, db_path=self.path)

    def test_unit8_envelope_forgery_remains_rejected(self) -> None:
        fixture = unit8.Unit8FastTests(methodName="runTest")
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        members = query.get_members(fixture.path, ANCHOR)
        assert members is not None
        self.assertEqual(tuple(token.ref for token in members), REFS)
        forged = replace(
            fixture.candidate,
            scope=candidate.CandidateScope(ANCHOR, tuple(f"MAT 1:2!{n}" for n in (5, 6, 7, 8, 9))),
            evidence=(candidate.EvidenceRef("anchor", "syntax_node", ANCHOR),),
            payload=candidate.AppositionCandidatePayload(ANCHOR, ()),
        )
        citations = (evaluation.RationaleCitation("token", "MAT 1:2!6"),)
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            fixture.create(forged, rationale_evidence=citations)
        with self.assertRaisesRegex(query.QueryError, "does not match source-grounded re-derivation"):
            fixture.create(unit8.reidentify(forged), rationale_evidence=citations)

    def test_hash_seed_and_database_location_invariance(self) -> None:
        moved = self.path.with_name("different location.sqlite3")
        moved.write_bytes(self.path.read_bytes())
        code = ("from scripts.structural_candidates import derive_structural_candidates; import sys; "
                "print(derive_structural_candidates(sys.argv[1], 'MAT 1:2!5')[0].candidate_id)")
        for seed, path in (("1", self.path), ("42", moved)):
            actual = subprocess.run(
                [sys.executable, "-B", "-c", code, str(path)],
                cwd=Path(__file__).resolve().parents[1], env={**os.environ, "PYTHONHASHSEED": seed},
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(actual.stdout.strip(), self.derive().candidate_id)


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT9_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT9_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit9MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before_bytes = (_LOCAL_DATABASE.stat().st_size,
                            hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest())
        cls.before_catalog = unit7.sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name")
        cls.before_version = unit7.sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version")

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.before_bytes != (_LOCAL_DATABASE.stat().st_size,
                                hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest()):
            raise AssertionError("Unit 9 integration database bytes changed")
        if cls.before_catalog != unit7.sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name"):
            raise AssertionError("Unit 9 integration catalog/index inventory changed")
        if cls.before_version != unit7.sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version"):
            raise AssertionError("Unit 9 integration user_version changed")
        print(f"Unit 9 read-only store unchanged: {cls.before_bytes}; user_version={cls.before_version}", flush=True)

    def test_frozen_complete_production_dto_and_all_lookups(self) -> None:
        expected = {key: value for key, value in EXPECTED.items()
                    if key not in ("identity_protocol", "source_annotations", "excluded_token_refs")}
        for ref in REFS:
            result = candidate.derive_structural_candidates(_LOCAL_DATABASE, ref)
            assert result is not None
            matched = [item for item in result if item.scope.source_node_id == ANCHOR]
            self.assertEqual(len(matched), 1)
            self.assertEqual(json.loads(json.dumps(asdict(matched[0]))), expected)
        excluded = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:2!6")
        assert excluded is not None
        self.assertNotIn(ANCHOR, [item.scope.source_node_id for item in excluded])
        node = query.get_node(_LOCAL_DATABASE, ANCHOR)
        assert node is not None
        self.assertEqual((node.rule, node.head_raw, node.start_raw, node.end_raw), ("S-V-O", "1", "5", "8"))
        children = query.get_children(_LOCAL_DATABASE, ANCHOR)
        assert children is not None
        self.assertEqual([(n.source_node_id, n.cat, n.sibling_ordinal) for n in children],
                         [(SUBJECT, "S", 0), (VERBAL, "V", 1), (OBJECT, "O", 2)])

    def test_matthew_1_1_verbless_and_frozen_apposition_identities(self) -> None:
        evidence = query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3")
        verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 1)
        result = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3")
        assert evidence is not None and verse is not None and result is not None
        self.assertEqual([(n.rule, n.cl_type) for n in evidence.ancestors if n.cat == "CL"],
                         [("P2CL", "Verbless")])
        self.assertEqual([token.cat for token in verse.tokens], ["noun"] * 8)
        self.assertTrue(all(type(item) is candidate.StructuralCandidate for item in result))
        self.assertEqual(tuple(item.candidate_id for item in result), APPOSITION_IDS)
        for item, (anchor, children, words) in zip(result, unit7.MATTHEW_APPOSITIONS):
            self.assertEqual(item.payload, candidate.AppositionCandidatePayload(anchor, children))
            self.assertEqual(item.scope, candidate.CandidateScope(
                anchor, tuple(f"MAT 1:1!{word}" for word in words),
            ))
            self.assertEqual(item.evidence, (
                candidate.EvidenceRef("anchor", "syntax_node", anchor),
                *(candidate.EvidenceRef("child", "syntax_node", child) for child in children),
            ))
            self.assertEqual(asdict(item.source_snapshot), EXPECTED["source_snapshot"])

    def test_unit8_existing_apposition_evaluation_remains_unchanged(self) -> None:
        result = candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3")
        assert result is not None
        self.assertEqual(len(result), 3)
        for item in result:
            assert isinstance(item, candidate.StructuralCandidate)
            record = evaluation.create_evaluated_interpretation(
                _LOCAL_DATABASE, item, evaluator_class="human", evaluator_label="test-only-reviewer",
                evaluation_protocol_id="human-structural-adequacy", evaluation_protocol_version="1",
                disposition="undetermined",
                rationale_evidence=(evaluation.RationaleCitation("syntax_node", item.scope.source_node_id),),
                rationale_note=evaluation.RationaleNote("Test-only record, not a recorded source judgment.", "en"),
                event_key="test:" + item.scope.source_node_id,
            )
            evaluation.verify_evaluated_interpretation(record)
            evaluation.verify_evaluated_interpretation(record, db_path=_LOCAL_DATABASE)
            self.assertIs(record.candidate, item)
        self.assertEqual(result, candidate.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3"))


if __name__ == "__main__":
    unittest.main()
