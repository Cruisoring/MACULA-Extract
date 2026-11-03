import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from product.adapter import ExplorerAdapter
from product.config import ProductConfig
from product.models import ProductSelection
from product.server import handle_request
from product.wording import ORDER_NOTE
from tests.product.support.fixtures import ParsedPage, file_state, populate_projection


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(os.environ.get("MACULA_MATTHEW_DB", str(ROOT / "sblgnt-matthew.sqlite3")))


@unittest.skipUnless(os.environ.get("MACULA_PRODUCT1_INTEGRATION") == "1",
                     "opt-in read-only real Matthew: set MACULA_PRODUCT1_INTEGRATION=1")
class RealMatthewTests(unittest.TestCase):
    def test_p1_p2_p3_p4_p5_p12_real_store_preservation(self) -> None:
        self.assertTrue(SOURCE.is_file(), "configured integration source must exist")
        before_source = file_state(SOURCE)
        self.addCleanup(lambda: self.assertEqual(file_state(SOURCE), before_source))
        self.assertEqual(before_source[3], ())
        with TemporaryDirectory(prefix="macula-product1-matthew-") as directory:
            projection = Path(directory) / "projection.sqlite3"
            fixture = populate_projection(SOURCE, projection)
            before_projection = file_state(projection)
            try:
                adapter = ExplorerAdapter(ProductConfig(SOURCE, projection))
                frozen = json.loads((ROOT / "fixtures" / "matthew-1-2-svo-candidate.expected.json").read_text(encoding="utf-8"))
                self.assertEqual(fixture.clause_id, frozen["candidate_id"])
                selection = ProductSelection("MAT", 1, 2, 5, fixture.clause_id)
                page = adapter.load_verse(selection)
                self.assertEqual(page.selected_candidate.member_token_refs,
                                 ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9"))
                from product.presentation import render_page
                parsed = ParsedPage(render_page(page))
                for ref, attrs in parsed.tokens.items():
                    self.assertEqual(attrs["data-membership"],
                                     "member" if ref in page.selected_candidate.member_token_refs else "non-member")
                self.assertEqual(parsed.tokens["MAT 1:2!6"]["data-membership"], "non-member")
                token_six = adapter.load_verse(ProductSelection("MAT", 1, 2, 6, fixture.clause_id))
                self.assertFalse(token_six.projection.candidates)
                verse_one = adapter.load_verse(ProductSelection("MAT", 1, 1,
                                                               candidate_id=fixture.apposition_ids[0]))
                self.assertEqual(len(verse_one.verse.tokens), 8)
                self.assertTrue(all(t.cat == "noun" for t in verse_one.verse.tokens))
                self.assertTrue(any(n.cl_type == "Verbless" for n in verse_one.verse.source_nodes))
                self.assertEqual(verse_one.selected_history.evaluations, ())
                text = ParsedPage(render_page(verse_one)).visible_text
                self.assertIn("ClType: Verbless", text)
                self.assertNotRegex(text.replace(ORDER_NOTE, ""),
                                    r"\b(is|Actor|Action|Patient|Event|Result|Identity|Property)\b")
                self.assertEqual(len(page.selected_history.evaluations), 4)
                self.assertEqual(sum(e.not_superseded for e in page.selected_history.evaluations), 3)
                response = handle_request(adapter, "GET", "/verse?chapter=1&verse=2&token=6",
                                          "localhost:8765", 8765)
                self.assertEqual(response.status, 200)
                parsed = ParsedPage(response.body.decode("utf-8"))
                self.assertFalse(any("data-candidate" in attrs for _, attrs in parsed.elements))
            finally:
                self.assertEqual(file_state(projection), before_projection)
                self.assertEqual(before_projection[3], ())
