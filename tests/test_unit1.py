from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from scripts import verify_unit1 as verifier


class Unit1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = verifier.load_json(verifier.CONTRACT_PATH)
        cls.primary = verifier.load_json(verifier.PROJECT_ROOT / "fixtures" / "matthew-1-1.expected.json")
        cls.boundary = verifier.load_json(verifier.PROJECT_ROOT / "fixtures" / "matthew-1-2-boundary.expected.json")
        cls.raw = verifier.verify_source(cls.contract)

    def verify(self, raw: bytes | None = None) -> dict[str, object]:
        return verifier.verify_fixtures(
            self.raw if raw is None else raw, self.primary, self.boundary,
        )

    def document(self) -> ET.Element:
        return ET.fromstring(self.raw)

    def primary_sentence(self, document: ET.Element) -> ET.Element:
        return next(s for s in document.findall("Sentence") if s.attrib["ref"] == self.primary["sentence_ref"])

    def test_t1_live_source_identity(self) -> None:
        self.assertEqual(self.contract["revision"], "8423afe47b9e8f24b7772e808af45c7159a6fe7e")
        self.assertEqual(self.contract["allowlist"], [{
            "relative_path": "SBLGNT/nodes/01-matthew.xml",
            "sha256": "FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4",
        }])
        self.assertEqual(hashlib.sha256(self.raw).hexdigest().upper(), verifier.SHA256)

    def test_t2_primary_shape_and_relations(self) -> None:
        primary = verifier.object_value(self.verify()["primary"], "primary result")
        self.assertEqual(primary["sentence_count"], 1)
        self.assertEqual(primary["tree_count"], 1)
        self.assertEqual(primary["node_count"], 26)
        self.assertEqual(primary["node_to_node_relations"], 25)
        self.assertEqual(primary["token_count"], 8)
        self.assertEqual(self.primary["root"], {
            "Cat": "S", "Head": "0", "nodeId": "400010010010083", "Length": "8",
        })

    def test_t3_attribute_accounting_and_absence(self) -> None:
        primary = verifier.object_value(self.verify()["primary"], "primary result")
        self.assertEqual(primary["source_attribute_count"], 342)
        self.assertEqual(primary["leaf_attribute_count"], 200)
        self.assertEqual(self.primary["leaf_attribute_count_per_token"], 25)
        leaves = verifier.leaf_nodes(self.primary_sentence(self.document()))
        for leaf in leaves:
            self.assertEqual(len(leaf.attrib), 25)
            for field in (
                "Frame", "Ref", "SubjRef", "Person", "Tense", "Voice", "Mood",
                "Degree", "HasDet", "Notes", "LowfatException", "Head", "Length",
            ):
                self.assertNotIn(field, leaf.attrib)
        self.assertEqual(self.primary["root_fields_expected_absent"], ["Start", "End", "Id", "Rule"])

    def test_t4_verbless_and_no_created_verb(self) -> None:
        primary = verifier.object_value(self.verify()["primary"], "primary result")
        self.assertEqual(primary["ClType"], "Verbless")
        self.assertEqual(primary["verb_leaf_count"], 0)
        self.assertEqual(self.primary["leaf_category"], "noun")
        self.assertEqual(self.primary["clause"], {
            "Id": "2.1", "Cat": "CL", "Rule": "P2CL", "ClType": "Verbless",
            "Start": "0", "End": "7", "Head": "0", "nodeId": "400010010010082", "Length": "8",
        })

    def test_t5_all_token_identities_and_surface_distinction(self) -> None:
        self.verify()
        expected_surfaces = [
            "\u0392\u03af\u03b2\u03bb\u03bf\u03c2",
            "\u03b3\u03b5\u03bd\u03ad\u03c3\u03b5\u03c9\u03c2",
            "\u1f38\u03b7\u03c3\u03bf\u1fe6",
            "\u03c7\u03c1\u03b9\u03c3\u03c4\u03bf\u1fe6",
            "\u03c5\u1f31\u03bf\u1fe6",
            "\u0394\u03b1\u03c5\u1f76\u03b4",
            "\u03c5\u1f31\u03bf\u1fe6",
            "\u1f08\u03b2\u03c1\u03b1\u03ac\u03bc.",
        ]
        tokens = verifier.list_value(self.primary["tokens"], "primary tokens")
        for ordinal, value in enumerate(tokens, 1):
            token = verifier.object_value(value, "token")
            self.assertEqual(token["ref"], f"MAT 1:1!{ordinal}")
            self.assertEqual(token["xml:id"], f"n40001001{ordinal:03}")
            self.assertEqual(token["morphId"], f"40001001{ordinal:03}")
            self.assertEqual(token["text"], expected_surfaces[ordinal - 1])
        last = verifier.object_value(tokens[-1], "last token")
        self.assertEqual(last["Unicode"], expected_surfaces[-1])
        self.assertEqual(last["NormalizedForm"], expected_surfaces[-1][:-1])
        self.assertNotEqual(last["text"], last["NormalizedForm"])

    def test_t6_boundary_ordering(self) -> None:
        boundary = verifier.object_value(self.verify()["boundary"], "boundary result")
        self.assertEqual(boundary["tree_pair"], [6, 5])
        self.assertEqual(self.boundary["ordering_counterexample"], {
            "first_tree_item": {"ref": "MAT 1:2!6", "text": "\u03b4\u1f72", "Start": "4"},
            "later_tree_item": {"ref": "MAT 1:2!5", "text": "\u1f38\u03c3\u03b1\u1f70\u03ba", "Start": "5"},
        })

    def test_t7_exact_ancestry_membership_not_envelope(self) -> None:
        boundary = verifier.object_value(self.verify()["boundary"], "boundary result")
        self.assertEqual(boundary["exact_members"], [5, 7, 8, 9])
        self.assertEqual(boundary["excluded"], 6)
        self.assertNotIn(6, verifier.list_value(boundary["exact_members"], "members"))
        self.assertNotEqual(boundary["exact_members"], list(range(5, 9)))
        self.assertEqual(self.boundary["discontinuous_membership"], {
            "scripture_coordinate": "MAT 1:2", "nodeId": "400010020050040",
            "Rule": "S-V-O", "Start": "5", "End": "8",
            "scripture_token_members": [5, 7, 8, 9], "canonical_envelope_non_member": 6,
        })

    def test_t8_field_identity_and_fidelity_contract(self) -> None:
        verifier.validate_contract(self.contract)
        self.assertEqual(self.contract["field_identity"], {
            "scripture_and_referent": ["ref", "Ref"],
            "identifiers": ["Id", "xml:id", "nodeId", "morphId"],
            "morphology_tags": ["FunctionalTag", "FormalTag"],
            "xml_id_expanded_name": "{http://www.w3.org/XML/1998/namespace}id",
        })
        self.assertEqual(len(verifier.list_value(self.contract["ordering_concepts"], "ordering concepts")), 7)
        self.assertEqual(set(verifier.object_value(self.contract["fidelity_invariants"], "invariants")), {f"F-{n:02}" for n in range(1, 11)})
        self.assertEqual(len(verifier.list_value(self.contract["prohibited_semantic_mappings"], "prohibitions")), 9)
        leaf = verifier.leaf_nodes(self.primary_sentence(self.document()))[0]
        self.assertIn("ref", leaf.attrib)
        self.assertNotIn("Ref", leaf.attrib)
        self.assertIn("Id", leaf.attrib)
        self.assertIn(verifier.XML_ID, leaf.attrib)
        self.assertIn("nodeId", leaf.attrib)
        self.assertIn("morphId", leaf.attrib)
        self.assertIn("FunctionalTag", leaf.attrib)
        self.assertIn("FormalTag", leaf.attrib)

    def test_contract_rejects_identity_or_policy_drift(self) -> None:
        for key, value in (
            ("revision", "0" * 40), ("edition", "Nestle1904"),
            ("source_format", "lowfat"), ("authorized_book", "Mark"),
            ("upstream_local_checkout", r"C:\Projects\MACULA Extract"),
            ("network_fetch", True), ("implicit_xinclude", True),
            ("directory_wildcard_expansion", True), ("contract_version", True),
        ):
            with self.subTest(key=key):
                contract = deepcopy(self.contract)
                contract[key] = value
                with self.assertRaises(verifier.VerificationError):
                    verifier.validate_contract(contract)

    def test_contract_rejects_path_checksum_and_allowlist_drift(self) -> None:
        for allowlist in (
            [], [{"relative_path": "SBLGNT/nodes/02-mark.xml", "sha256": verifier.SHA256}],
            [{"relative_path": "../01-matthew.xml", "sha256": verifier.SHA256}],
            [{"relative_path": verifier.RELATIVE_PATH, "sha256": "0" * 64}],
            verifier.list_value(self.contract["allowlist"], "allowlist") * 2,
        ):
            with self.subTest(allowlist=allowlist):
                contract = deepcopy(self.contract)
                contract["allowlist"] = allowlist
                with self.assertRaises(verifier.VerificationError):
                    verifier.validate_contract(contract)

    def test_contract_rejects_removed_fidelity_or_field_distinctions(self) -> None:
        for key in ("field_identity", "ordering_concepts", "fidelity_invariants", "prohibited_semantic_mappings"):
            with self.subTest(key=key):
                contract = deepcopy(self.contract)
                contract[key] = {}
                with self.assertRaises(verifier.VerificationError):
                    verifier.validate_contract(contract)

    def git_results(self, revision: str = verifier.REVISION) -> list[subprocess.CompletedProcess[str]]:
        return [
            subprocess.CompletedProcess([], 0, "C:/Works/macula-greek\n"),
            subprocess.CompletedProcess([], 0, revision + "\n"),
        ]

    def test_source_rejects_wrong_git_root(self) -> None:
        with patch.object(verifier.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "C:/wrong\n")):
            with self.assertRaisesRegex(verifier.VerificationError, "upstream root"):
                verifier.verify_source(self.contract)

    def test_source_rejects_revision_mismatch(self) -> None:
        with patch.object(verifier.subprocess, "run", side_effect=self.git_results("0" * 40)):
            with self.assertRaisesRegex(verifier.VerificationError, "upstream revision"):
                verifier.verify_source(self.contract)

    def test_source_rejects_missing_file(self) -> None:
        with patch.object(verifier.subprocess, "run", side_effect=self.git_results()):
            with patch.object(Path, "read_bytes", side_effect=FileNotFoundError("missing Matthew")):
                with self.assertRaises(FileNotFoundError):
                    verifier.verify_source(self.contract)

    def test_source_rejects_same_length_byte_mutation(self) -> None:
        changed = bytes([self.raw[0] ^ 1]) + self.raw[1:]
        self.assertEqual(len(changed), len(self.raw))
        with patch.object(verifier.subprocess, "run", side_effect=self.git_results()):
            with patch.object(Path, "read_bytes", return_value=changed):
                with self.assertRaisesRegex(verifier.VerificationError, "SHA-256"):
                    verifier.verify_source(self.contract)

    def test_verification_only_uses_read_only_git_commands(self) -> None:
        with patch.object(verifier.subprocess, "run", side_effect=self.git_results()) as run:
            with patch.object(Path, "read_bytes", return_value=self.raw) as read:
                verifier.verify_source(self.contract)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands, [
            ["git", "-C", r"C:\Works\macula-greek", "rev-parse", "--show-toplevel"],
            ["git", "-C", r"C:\Works\macula-greek", "rev-parse", "--verify", "HEAD"],
        ])
        read.assert_called_once_with()

    def test_fixture_rejects_shape_and_attribute_mutation(self) -> None:
        for field in ("node_count", "token_count", "source_attribute_count", "leaf_attribute_count_per_token"):
            with self.subTest(field=field):
                expected = deepcopy(self.primary)
                count = expected[field]
                if not isinstance(count, int):
                    self.fail("expected count must be an integer")
                expected[field] = count + 1
                with self.assertRaises(verifier.VerificationError):
                    verifier.verify_fixtures(self.raw, expected, self.boundary)

    def test_fixture_rejects_placeholder_attribute(self) -> None:
        document = self.document()
        leaf = verifier.leaf_nodes(self.primary_sentence(document))[0]
        leaf.attrib.pop("LN")
        leaf.set("Frame", "")
        self.assertEqual(len(leaf.attrib), 25)
        with self.assertRaisesRegex(verifier.VerificationError, "absence Frame"):
            self.verify(ET.tostring(document, encoding="utf-8"))

    def test_fixture_rejects_changed_head(self) -> None:
        document = self.document()
        verifier.one(self.primary_sentence(document).findall("Trees/Tree/Node"), "root").set("Head", "1")
        with self.assertRaises(verifier.VerificationError):
            self.verify(ET.tostring(document, encoding="utf-8"))

    def test_fixture_rejects_changed_verbless(self) -> None:
        document = self.document()
        verifier.one(self.primary_sentence(document).findall("Trees/Tree/Node/Node"), "clause").set("ClType", "Minor")
        with self.assertRaises(verifier.VerificationError):
            self.verify(ET.tostring(document, encoding="utf-8"))

    def test_fixture_rejects_normalized_surface(self) -> None:
        document = self.document()
        last = verifier.leaf_nodes(self.primary_sentence(document))[-1]
        last.text = last.attrib["NormalizedForm"]
        with self.assertRaises(verifier.VerificationError):
            self.verify(ET.tostring(document, encoding="utf-8"))

    def test_fixture_rejects_incorrect_order_and_membership_expectations(self) -> None:
        boundary = deepcopy(self.boundary)
        order = verifier.object_value(boundary["ordering_counterexample"], "ordering")
        verifier.object_value(order["first_tree_item"], "first item")["Start"] = "5"
        with self.assertRaises(verifier.VerificationError):
            verifier.verify_fixtures(self.raw, self.primary, boundary)
        boundary = deepcopy(self.boundary)
        verifier.object_value(boundary["discontinuous_membership"], "membership")["scripture_token_members"] = [5, 6, 7, 8]
        with self.assertRaises(verifier.VerificationError):
            verifier.verify_fixtures(self.raw, self.primary, boundary)

    def test_present_empty_remains_distinct_from_missing(self) -> None:
        document = self.document()
        leaf = next(n for n in document.iter("Node") if n.attrib.get("ref") == "MAT 1:2!8")
        self.assertIn("English", leaf.attrib)
        self.assertEqual(leaf.attrib["English"], "")
        self.assertNotIn("Notes", leaf.attrib)
        self.assertIsNone(leaf.attrib.get("Notes"))

    def test_json_field_keys_preserve_case(self) -> None:
        with patch.object(Path, "read_text", return_value='{"ref": "address", "Ref": "referent"}'):
            self.assertEqual(verifier.load_json(Path("unused")), {"ref": "address", "Ref": "referent"})
        with patch.object(Path, "read_text", return_value='{"ref": "a", "ref": "b"}'):
            with self.assertRaisesRegex(verifier.VerificationError, "duplicate JSON key"):
                verifier.load_json(Path("unused"))

    def test_doctype_and_xinclude_are_rejected(self) -> None:
        with self.assertRaisesRegex(verifier.VerificationError, "DOCTYPE"):
            self.verify(b"<!DOCTYPE Sentences><Sentences/>")
        with self.assertRaisesRegex(verifier.VerificationError, "XInclude"):
            self.verify(b'<Sentences xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="other.xml"/></Sentences>')

    def test_cli_failure_is_explicit_and_nonzero(self) -> None:
        errors = io.StringIO()
        with patch.object(verifier, "run_unit1", side_effect=verifier.VerificationError("source drift")):
            with redirect_stderr(errors):
                self.assertEqual(verifier.main(), 1)
        self.assertIn("FAILED", errors.getvalue())
        self.assertIn("source drift", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
