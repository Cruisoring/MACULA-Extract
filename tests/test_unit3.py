from contextlib import redirect_stderr
import hashlib
import io
from itertools import count, zip_longest
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import source_importer as importer
from scripts import source_fidelity as fidelity
from scripts import source_schema as schema
from scripts import verify_unit1 as unit1
from scripts.xmlreader_bridge import ImportFailure, reader_bridge, reader_events
from test_unit2 import SchemaFixture


SAMPLE = (
    '<Sentences><Sentence ref="MAT 1:1!1-1:1!1"><Trees><Tree>'
    '<Node Cat="S"><Node Cat="noun" ref="MAT 1:1!1" English="" xml:id="n0001">'
    '\u1f41</Node></Node></Tree></Trees></Sentence></Sentences>'
).encode("utf-8")


class Unit3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = TemporaryDirectory(prefix="macula-unit3-acceptance-")
        cls.addClassCleanup(cls.directory.cleanup)
        cls.temporary = Path(cls.directory.name)
        cls.bridge_context = reader_bridge()
        cls.bridge = cls.bridge_context.__enter__()
        cls.addClassCleanup(cls.bridge_context.__exit__, None, None, None)
        cls.raw = unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH))
        cls.first = cls.temporary / "first.sqlite3"
        cls.second = cls.temporary / "second.sqlite3"
        cls.reports = []
        for path in (cls.first,):
            print(f"Unit 3 independent full production-style build: {path.name}", flush=True)
            cls.reports.append(importer.build_matthew(path, cls.bridge))
            print(json.dumps(cls.reports[-1], ensure_ascii=True), flush=True)
        cls.db = fidelity.open_readonly(cls.first)
        cls.addClassCleanup(cls.db.close)

    def synthetic(self, raw: bytes = SAMPLE) -> sqlite3.Connection:
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        schema.bootstrap(db)
        db.execute("BEGIN")
        importer._populate(db, raw, self.bridge)
        fidelity.verify_fidelity(db, raw)
        return db

    @unittest.skipUnless(os.environ.get("MACULA_UNIT3_SECOND_BUILD") == "1",
                         "explicit slow gate: set MACULA_UNIT3_SECOND_BUILD=1 for a second full build")
    def test_u3_01_two_full_builds_and_logical_digests(self) -> None:
        self.reports.append(importer.build_matthew(self.second, self.bridge))
        self.assertEqual(self.reports[0]["logical_digest"], self.reports[1]["logical_digest"])
        self.assertEqual(self.reports[0]["logical_digest_version"], fidelity.DIGEST_VERSION)
        self.assertEqual(self.reports[0]["parser"], "System.Xml.XmlReader")
        self.assertEqual(self.reports[0]["status"], "COMPLETE")

    def test_u3_02_independently_derived_full_source_counts(self) -> None:
        counts = unit1.object_value(self.reports[0]["counts"], "actual counts")
        self.assertEqual(counts, {
            "elements": 59891, "attributes": 767429, "content": 179675,
            "sentences": 1134, "trees": 1134, "nodes": 56488, "tokens": 18329,
            "memberships": self.db.execute("SELECT count(*) FROM node_token_membership").fetchone()[0],
            "single_character_tokens": 733,
        })

    def test_u3_03_actual_archived_byte_export(self) -> None:
        exported = self.temporary / "archived-matthew.xml"
        exported.write_bytes(fidelity.archive_bytes(self.db))
        self.assertEqual(exported.read_bytes(), self.raw)
        self.assertEqual(exported.stat().st_size, 14115918)
        self.assertEqual(hashlib.sha256(exported.read_bytes()).hexdigest().upper(), unit1.SHA256)

    def test_u3_04_full_db_only_serialized_reconstruction(self) -> None:
        exported = self.temporary / "normalized-matthew.xml"
        exported.write_bytes(fidelity.normalized_xml(self.db))
        expected = fidelity.Reference()
        actual = fidelity.Reference()
        for source_event, reconstructed_event in zip_longest(
                fidelity.reference_events(self.raw, expected),
                fidelity.reference_events(exported.read_bytes(), actual)):
            self.assertEqual(source_event, reconstructed_event)
        self.assertEqual(expected.tokens, actual.tokens)
        self.assertEqual(expected.nodes, actual.nodes)
        self.assertEqual(expected.memberships, actual.memberships)

    def test_u3_05_db_reconstruction_never_reads_original_blob(self) -> None:
        db = fidelity.open_readonly(self.first)
        self.addCleanup(db.close)

        def forbid_blob(action: int, table: str, column: str, database: str, trigger: str) -> int:
            if action == sqlite3.SQLITE_READ and table == "source_file" and column == "original_bytes":
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        db.set_authorizer(forbid_blob)
        self.assertEqual(sum(event[0] == "start" for event in fidelity.db_xml_events(db)), 59891)

    def test_u3_06_consumer_is_explicitly_readonly(self) -> None:
        self.assertEqual(self.db.execute("PRAGMA query_only").fetchone(), (1,))
        self.assertEqual(self.db.execute("PRAGMA foreign_keys").fetchone(), (1,))
        self.assertEqual(self.db.execute("PRAGMA recursive_triggers").fetchone(), (1,))
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute("DELETE FROM node_token_membership")

    def test_u3_07_genuine_one_character_text_exhaustive_and_samples(self) -> None:
        rows = self.db.execute(
            "SELECT ref_raw,xml_id,source_direct_text FROM token WHERE length(source_direct_text)=1"
        ).fetchall()
        self.assertEqual(len(rows), 733)
        self.assertIn(("MAT 1:16!13", "n40001016013", "\u1f41"), rows)
        self.assertIn(("MAT 1:18!5", "n40001018005", "\u1f21"), rows)
        self.assertTrue(all(len(text) == 1 for _, _, text in rows))
        self.assertEqual(self.reports[0]["normalized_fidelity"], "PASS")

    def test_u3_08_actual_matthew_1_1_shape_attributes_and_text(self) -> None:
        tree = self.db.execute(
            "SELECT tree_id FROM tree JOIN sentence USING(sentence_id) WHERE ref_raw='MAT 1:1!1-1:1!8'"
        ).fetchone()[0]
        self.assertEqual(self.db.execute("SELECT count(*) FROM syntax_node WHERE tree_id=?", (tree,)).fetchone(), (26,))
        self.assertEqual(self.db.execute("SELECT count(*) FROM syntax_node WHERE tree_id=? AND parent_node_id IS NOT NULL",
                                        (tree,)).fetchone(), (25,))
        rows = self.db.execute(
            "SELECT ref_raw,xml_id,morph_id,source_direct_text,unicode_raw,normalized_form "
            "FROM token WHERE tree_id=? ORDER BY canonical_ordinal", (tree,),
        ).fetchall()
        self.assertEqual(len(rows), 8)
        fixture = unit1.load_json(unit1.PROJECT_ROOT / "fixtures" / "matthew-1-1.expected.json")
        for row, expected in zip(rows, unit1.list_value(fixture["tokens"], "frozen tokens")):
            token = unit1.object_value(expected, "frozen token")
            self.assertEqual(row[:4], (token["ref"], token["xml:id"], token["morphId"], token["text"]))
        self.assertEqual(rows[-1][3:], ("\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.", "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.",
                                      "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc"))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM xml_attribute a JOIN xml_element e USING(element_id) "
            "WHERE json_extract(e.locator,'$[1][2]')=1").fetchone(), (342,))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM xml_attribute JOIN syntax_node USING(element_id) JOIN token USING(node_id) "
            "WHERE token.tree_id=?", (tree,)).fetchone(), (200,))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM node_token_membership WHERE tree_id=?", (tree,)).fetchone(), (71,))
        self.assertEqual(self.db.execute(
            "SELECT start_raw,end_raw,id_raw,rule,head_raw,length_raw FROM syntax_node "
            "WHERE tree_id=? AND parent_node_id IS NULL", (tree,)).fetchone(), (None, None, None, None, "0", "8"))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM syntax_node WHERE tree_id=? AND cl_type='Verbless'", (tree,)).fetchone(), (1,))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM token JOIN syntax_node USING(node_id) WHERE token.tree_id=? AND cat='verb'",
            (tree,)).fetchone(), (0,))

    def test_u3_09_actual_matthew_1_2_dual_order(self) -> None:
        rows = self.db.execute(
            "SELECT ref_raw,source_direct_text,tree_leaf_ordinal,canonical_ordinal,start_raw FROM token "
            "JOIN syntax_node USING(node_id) WHERE ref_raw IN ('MAT 1:2!6','MAT 1:2!5')"
        ).fetchall()
        by_ref = {row[0]: row for row in rows}
        six, five = by_ref["MAT 1:2!6"], by_ref["MAT 1:2!5"]
        self.assertEqual((six[1], five[1], six[4], five[4]), ("\u03b4\u1f72", "\u1f38\u03c3\u03b1\u1f70\u03ba", "4", "5"))
        self.assertLess(six[2], five[2])
        self.assertGreater(six[3], five[3])

    def test_u3_10_actual_discontinuous_ancestry_not_numeric_span(self) -> None:
        node, start, end = self.db.execute(
            "SELECT node_id,start_raw,end_raw FROM syntax_node WHERE upstream_node_id='400010020050040'"
        ).fetchone()
        self.assertEqual((start, end), ("5", "8"))
        members = self.db.execute(
            "SELECT verse_token_ordinal FROM node_token_membership JOIN token USING(token_id) "
            "WHERE node_token_membership.node_id=? ORDER BY canonical_ordinal", (node,),
        ).fetchall()
        self.assertEqual(members, [(5,), (7,), (8,), (9,)])
        self.assertNotIn((6,), members)

    def test_u3_11_full_dual_tags_and_present_empty(self) -> None:
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM token WHERE functional_tag IS NOT formal_tag").fetchone(), (215,))
        self.assertEqual(self.db.execute(
            "SELECT english,notes_raw FROM token WHERE ref_raw='MAT 1:2!8'").fetchone(), ("", None))

    def test_u3_12_mixed_namespaces_prefix_aliases_and_empty_cdata(self) -> None:
        raw = (
            '<?p x?>\r\n<r xmlns="urn:r" a="" xmlns:p="urn:p" p:a="1" xmlns:q="urn:p">'
            ' \r\n<![CDATA[\u03b1]]><![CDATA[]]><!--c--><?q ?><p:x/><q:x/></r>\r\n'
        ).encode()
        db = self.synthetic(raw)
        self.assertEqual(db.execute(
            "SELECT locator FROM xml_element WHERE namespace_uri='urn:p' ORDER BY sibling_ordinal"
        ).fetchall(), [('[["urn:r","r",1],["urn:p","x",1]]',), ('[["urn:r","r",1],["urn:p","x",2]]',)])
        self.assertEqual(db.execute(
            "SELECT value FROM xml_content WHERE kind='cdata' ORDER BY content_id").fetchall(), [("\u03b1",), ("",)])
        self.assertEqual(list(fidelity.reference_events(fidelity.normalized_xml(db), fidelity.Reference())),
                         list(fidelity.db_xml_events(db)))

    def test_u3_13_bom_encoding_combining_non_bmp_and_no_substitution(self) -> None:
        for encoding in ("utf-8-sig", "utf-16"):
            with self.subTest(encoding=encoding):
                raw = ('<?xml version="1.0" encoding="' + ("utf-8" if encoding == "utf-8-sig" else "utf-16") +
                       '"?><r a="&#13;&#10;&#9;">\u03b1\u0301\U0001f600&#13;</r>').encode(encoding)
                db = self.synthetic(raw)
                self.assertEqual(fidelity.archive_bytes(db), raw)
                self.assertIn(["text", "\u03b1\u0301\U0001f600\r"], list(fidelity.db_xml_events(db)))
                self.assertEqual(list(fidelity.reference_events(fidelity.normalized_xml(db), fidelity.Reference())),
                                 list(fidelity.db_xml_events(db)))

    def test_u3_14_authoritative_parser_failures_are_atomic(self) -> None:
        bad = [
            b'<!DOCTYPE r><r/>',
            b'<!DOCTYPE r SYSTEM "file:///not-authorized"><r/>',
            b'<r xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="not-authorized"/></r>',
            b'<r>',
            b'<r/><r/>',
            b'<p:r/>',
            b'<r a="1" a="2"/>',
            b'<r xmlns:p="urn:u" xmlns:q="urn:u" p:a="1" q:a="2"/>',
            b'<r>\x01</r>',
            b'<r>\xff</r>',
        ]
        for raw in bad:
            with self.subTest(raw=raw):
                output = self.temporary / "failed.sqlite3"
                before = set(self.temporary.iterdir())
                with patch.object(unit1, "verify_source", return_value=raw):
                    with self.assertRaises(ImportFailure):
                        importer.build_matthew(output, self.bridge)
                self.assertFalse(output.exists())
                self.assertEqual(set(self.temporary.iterdir()), before)

    def test_u3_15_failed_schema_and_fidelity_validation_do_not_publish(self) -> None:
        for error in (schema.SchemaError("schema failure"), ImportFailure("typed/source mismatch")):
            with self.subTest(error=error):
                output = self.temporary / "failed-validation.sqlite3"
                before = set(self.temporary.iterdir())
                with patch.object(unit1, "verify_source", return_value=SAMPLE):
                    with patch.object(fidelity, "verify_fidelity", side_effect=error):
                        with self.assertRaises(type(error)):
                            importer.build_matthew(output, self.bridge)
                self.assertFalse(output.exists())
                self.assertEqual(set(self.temporary.iterdir()), before)

    def test_u3_16_source_revision_and_checksum_failure_do_not_publish(self) -> None:
        for message in ("upstream revision mismatch", "source SHA-256 mismatch"):
            with self.subTest(message=message):
                output = self.temporary / "failed-source.sqlite3"
                with patch.object(unit1, "verify_source", side_effect=unit1.VerificationError(message)):
                    with self.assertRaises(unit1.VerificationError):
                        importer.build_matthew(output, self.bridge)
                self.assertFalse(output.exists())

    def test_u3_17_protected_outputs_and_overwrite_fail_closed(self) -> None:
        before = hashlib.sha256(self.first.read_bytes()).hexdigest()
        with self.assertRaises(ImportFailure):
            importer.build_matthew(self.first, self.bridge)
        self.assertEqual(hashlib.sha256(self.first.read_bytes()).hexdigest(), before)
        for root in importer.PROTECTED_ROOTS:
            with self.subTest(root=root):
                with self.assertRaises(ImportFailure):
                    importer.safe_output(root / "forbidden.sqlite3")

    def test_u3_18_f2_consistent_generic_typed_tamper(self) -> None:
        path = self.temporary / "tampered.sqlite3"
        db = sqlite3.connect(path)
        schema.bootstrap(db)
        importer._populate(db, SAMPLE, self.bridge)
        fidelity.verify_fidelity(db, SAMPLE)
        db.commit()
        db.close()
        db = sqlite3.connect(path)
        self.addCleanup(db.close)
        self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone(), (0,))
        for table, value_column, where in (
            ("xml_attribute", "value", "local_name='English'"),
            ("token", "english", "1=1"),
        ):
            columns = [row[1] for row in db.execute(f"PRAGMA table_info({table})")]
            values = ["'tampered'" if column == value_column else column for column in columns]
            db.execute(f"INSERT OR REPLACE INTO {table} SELECT {','.join(values)} FROM {table} WHERE {where}")
        db.commit()
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA recursive_triggers=ON")
        schema.validate_store(db)
        self.assertEqual(fidelity.archive_bytes(db), SAMPLE)
        with self.assertRaisesRegex(ImportFailure, "NORMALIZED source fidelity failed"):
            fidelity.verify_fidelity(db, SAMPLE)

    def test_u3_19_logical_digest_excludes_surrogate_pk(self) -> None:
        stores = []
        for offset in (0, 100):
            db = sqlite3.connect(":memory:")
            self.addCleanup(db.close)
            schema.bootstrap(db)
            fixture = SchemaFixture(db, offset)
            node_ids = count(offset + 1)
            original_insert = fixture.insert

            def shifted_insert(table: str, values: dict[str, object]) -> int:
                if table == "syntax_node":
                    values = {"node_id": next(node_ids), **values}
                return original_insert(table, values)

            with patch.object(fixture, "insert", side_effect=shifted_insert):
                fixture.model()
            schema.validate_store(db)
            stores.append(db)
        self.assertNotEqual(stores[0].execute("SELECT node_id FROM token").fetchone(),
                            stores[1].execute("SELECT node_id FROM token").fetchone())
        self.assertEqual(fidelity.logical_digest(stores[0]), fidelity.logical_digest(stores[1]))

    def test_u3_20_logical_digest_excludes_physical_page_layout(self) -> None:
        digests = []
        sizes = []
        for page_size in (4096, 16384):
            db = sqlite3.connect(":memory:")
            self.addCleanup(db.close)
            db.execute(f"PRAGMA page_size={page_size}")
            schema.bootstrap(db)
            importer._populate(db, SAMPLE, self.bridge)
            digests.append(fidelity.logical_digest(db))
            sizes.append(db.execute("PRAGMA page_size").fetchone()[0])
        self.assertNotEqual(*sizes)
        self.assertEqual(*digests)

    def test_u3_21_complete_occurrence_identity_and_typed_links(self) -> None:
        self.assertEqual(self.db.execute("SELECT count(*),count(DISTINCT locator) FROM xml_element").fetchone(), (59891, 59891))
        for table in ("sentence", "tree", "syntax_node"):
            with self.subTest(table=table):
                self.assertEqual(self.db.execute(
                    f"SELECT count(*) FROM {table} t LEFT JOIN xml_element e USING(element_id) WHERE e.element_id IS NULL"
                ).fetchone(), (0,))
        self.assertEqual(self.db.execute(
            "SELECT count(*) FROM token t LEFT JOIN syntax_node n USING(node_id) WHERE n.node_id IS NULL"
        ).fetchone(), (0,))

    def test_u3_22_import_cli_failure_is_explicit(self) -> None:
        errors = io.StringIO()
        with patch("sys.argv", ["source_importer", "--output", str(self.first)]):
            with patch.object(importer, "reader_bridge", side_effect=ImportFailure("offline build failed")):
                with redirect_stderr(errors):
                    self.assertEqual(importer.main(), 1)
        self.assertIn("FAILED", errors.getvalue())
        self.assertIn("offline build failed", errors.getvalue())

    def test_u3_23_fidelity_cli_failure_is_explicit(self) -> None:
        errors = io.StringIO()
        with patch("sys.argv", ["source_fidelity", "--database", str(self.first)]):
            with patch.object(fidelity, "verify_fidelity", side_effect=ImportFailure("source-consistent tamper")):
                with redirect_stderr(errors):
                    self.assertEqual(fidelity.main(), 1)
        self.assertIn("FAILED", errors.getvalue())
        self.assertIn("source-consistent tamper", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
