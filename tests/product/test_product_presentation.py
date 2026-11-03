from contextlib import closing, redirect_stderr
from dataclasses import replace
from io import StringIO
from pathlib import Path
import re
import shutil
import socket
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from http.client import HTTPConnection

from scripts import projection_store as store
from product import adapter as boundary
from product import wording
from product.adapter import ExplorerAdapter
from product.config import ProductConfig
from product.errors import ErrorCategory
from product.models import ProductSelection, ProjectionState
from product.presentation import render_page
from product.server import create_server, handle_request
from tests.product.support.fixtures import GREEK, ParsedPage, file_state, temporary_fixture


class PresentationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = temporary_fixture(self)
        self.adapter = self.fixture.adapter()

    def response(self, target: str, method: str = "GET", host: str = "localhost:8765"):
        return handle_request(self.adapter, method, target, host, 8765)

    def clause_page(self, **values):
        return self.adapter.load_verse(ProductSelection("MAT", 1, 2, candidate_id=self.fixture.clause_id,
                                                       **values))

    def test_p1_eight_greek_tokens_verbless_and_no_fabricated_verb(self) -> None:
        target = "/verse?" + urlencode({"chapter": 1, "verse": 1, "candidate": self.fixture.apposition_ids[0]})
        response = self.response(target)
        self.assertEqual(response.status, 200)
        html = response.body.decode("utf-8")
        parsed = ParsedPage(html)
        self.assertEqual(tuple(parsed.tokens), tuple(f"MAT 1:1!{n}" for n in range(1, 9)))
        for surface in GREEK:
            self.assertIn(surface, html)
        self.assertIn("ClType: Verbless", parsed.visible_text)
        self.assertIn(wording.VERBLESS_NOTE, parsed.visible_text)
        self.assertIn("apposition", parsed.visible_text)
        self.assertNotRegex(parsed.visible_text.replace(wording.ORDER_NOTE, ""),
                            r"\b(is|Actor|Action|Patient|Event|Result|Identity|Property)\b")
        self.assertNotIn("S-V-O", parsed.visible_text)
        surfaces = [attrs for tag, attrs in parsed.elements if attrs.get("class") == "surface"]
        self.assertEqual(len(surfaces), 8)
        self.assertTrue(all(attrs.get("lang") == "grc" for attrs in surfaces))

    def test_p2_exact_membership_markup_components_and_selection(self) -> None:
        page = self.clause_page(token_ordinal=5)
        html = render_page(page)
        parsed = ParsedPage(html)
        self.assertEqual({ref: attrs["data-membership"] for ref, attrs in parsed.tokens.items()}, {
            "MAT 1:2!5": "member", "MAT 1:2!6": "non-member", "MAT 1:2!7": "member",
            "MAT 1:2!8": "member", "MAT 1:2!9": "member",
        })
        self.assertIn("selected-token", parsed.tokens["MAT 1:2!5"]["class"])
        self.assertNotIn("selected-token", parsed.tokens["MAT 1:2!6"]["class"])
        self.assertEqual(html.count("&#x25AE;"), 4)
        self.assertEqual(html.count(">member of selected candidate<"), 4)
        self.assertEqual(html.count(">not in selected candidate scope<"), 1)
        self.assertIn("subject-component", html)
        self.assertIn("verbal-component", html)
        self.assertIn("object-component", html)
        card = html.split("Exact member refs", 1)[1].split("</article>", 1)[0]
        self.assertNotIn("MAT 1:2!6", card)
        self.assertIn("Source rule: S-V-O", parsed.visible_text)

    def test_p12_token_six_filter_cannot_select_svo_or_its_evaluation(self) -> None:
        for extra in ({}, {"candidate": self.fixture.clause_id},
                      {"evaluation": self.fixture.evaluations[1].evaluation_id}):
            target = "/verse?" + urlencode({"chapter": 1, "verse": 2, "token": 6, **extra})
            response = self.response(target)
            self.assertEqual(response.status, 200)
            html = response.body.decode("utf-8")
            parsed = ParsedPage(html)
            self.assertTrue(all(t["data-membership"] == "non-member" for t in parsed.tokens.values()))
            self.assertIn("selected-token", parsed.tokens["MAT 1:2!6"]["class"])
            self.assertFalse(any("data-candidate" in attrs for _, attrs in parsed.elements))
            self.assertNotIn("Derived structural candidate: S-V-O", parsed.visible_text)
            self.assertIn(wording.NO_CANDIDATES, parsed.visible_text)
            self.assertNotIn(f'data-candidate="{self.fixture.clause_id}"', html)
            self.assertNotIn('class="component-label"', html)

    def test_p3_unevaluated_candidate_not_explicit_disposition(self) -> None:
        page = self.adapter.load_verse(ProductSelection(
            "MAT", 1, 1, candidate_id=self.fixture.apposition_ids[0],
        ))
        text = ParsedPage(render_page(page)).visible_text
        self.assertIn("Candidate status: candidate", text)
        self.assertIn(wording.NOT_EVALUATED, text)
        self.assertNotRegex(text.lower(), r"\b(undetermined|rejected|accepted)\b")

    def test_p4_p5_opposing_evaluations_fork_and_select_does_not_hide(self) -> None:
        for evaluation_id in (None, self.fixture.evaluations[1].evaluation_id):
            page = self.clause_page(evaluation_id=evaluation_id)
            html = render_page(page)
            parsed = ParsedPage(html)
            cards = [attrs for tag, attrs in parsed.elements if "data-evaluation" in attrs]
            self.assertEqual({a["data-evaluation"] for a in cards},
                             {e.evaluation_id for e in self.fixture.evaluations})
            self.assertEqual(html.count(">Not superseded<"), 3)
            self.assertIn("Evaluation: accepted under human-structural-adequacy/1 by", parsed.visible_text)
            self.assertIn("Evaluation: rejected under human-structural-adequacy/1 by", parsed.visible_text)
            self.assertIn("Superseded by " + self.fixture.evaluations[1].evaluation_id, parsed.visible_text)
            self.assertIn("Superseded by " + self.fixture.evaluations[2].evaluation_id, parsed.visible_text)
            self.assertIn(wording.ORDER_NOTE, parsed.visible_text)
            self.assertIn("Candidate status: candidate", parsed.visible_text)
            self.assertIn("Evaluation disposition", parsed.visible_text)
            self.assertNotIn("event_key", html)
            self.assertNotIn("product:root", html)
            if evaluation_id is not None:
                self.assertEqual([a["data-evaluation"] for a in cards if "selected-card" in a["class"]],
                                 [evaluation_id])

    def test_p6_valid_empty_store_and_p7_no_configuration(self) -> None:
        with TemporaryDirectory(prefix="macula-product-empty-") as directory:
            path = Path(directory) / "empty.sqlite3"
            store.initialize_projection_store(path)
            before = file_state(path)
            adapter = ExplorerAdapter(ProductConfig(self.fixture.source, path))
            response = handle_request(adapter, "GET", "/verse?chapter=1&verse=1", "localhost:8765", 8765)
            self.assertEqual(response.status, 200)
            self.assertIn(wording.NO_CANDIDATES.encode(), response.body)
            self.assertIn(b'VERIFIED_EMPTY', response.body)
            self.assertEqual(file_state(path), before)
        adapter = self.fixture.adapter(False)
        response = handle_request(adapter, "GET", "/verse?chapter=1&verse=1", "localhost:8765", 8765)
        self.assertIn(wording.NOT_CONFIGURED.encode(), response.body)
        self.assertNotIn(wording.NO_CANDIDATES.encode(), response.body)
        self.assertEqual(len(ParsedPage(response.body.decode()).tokens), 8)
        self.assertNotIn(b"No structural candidates exist", response.body)

    def test_p8_p11_errors_never_empty_and_keep_source(self) -> None:
        for effects, category in (
            ([ValueError("secret")], ErrorCategory.INTEGRITY_ERROR),
            ([None, boundary.QueryError("secret")], ErrorCategory.SOURCE_PROJECTION_MISMATCH),
        ):
            with patch.object(boundary, "verify_projection_store", side_effect=effects), redirect_stderr(StringIO()):
                adapter = self.fixture.adapter()
            response = handle_request(adapter, "GET", "/verse?chapter=1&verse=1", "localhost:8765", 8765)
            self.assertEqual(response.status, 200)
            self.assertIn(category.value.encode(), response.body)
            self.assertNotIn(b"secret", response.body)
            self.assertNotIn(wording.NO_CANDIDATES.encode(), response.body)
            self.assertEqual(len(ParsedPage(response.body.decode()).tokens), 8)

    def test_p9_absent_verse_and_absent_selections_statuses(self) -> None:
        response = self.response("/verse?chapter=99&verse=99")
        self.assertEqual(response.status, 404)
        self.assertIn(b"Verse not present in the source store: MAT 99:99", response.body)
        self.assertNotIn(b'data-error="SOURCE_STORE_ERROR"', response.body)
        for tail in ("token=999", "candidate=sha256:" + "0" * 64,
                     "evaluation=eval-sha256:" + "0" * 64):
            response = self.response("/verse?chapter=1&verse=1&" + tail)
            self.assertEqual(response.status, 200)
            self.assertIn(b'data-error="ABSENT"', response.body)
            self.assertEqual(len(ParsedPage(response.body.decode()).tokens), 8)

    def test_p10_ac15_16_all_selector_failures_before_core(self) -> None:
        invalid_values = ("", " ", "+1", "-1", "01", "0", "1.1", "\u0661", "\uff11",
                          str(2**63), "1" * 20, "9" * 4301)
        with patch.object(boundary, "get_verse") as verse, patch.object(
            boundary, "get_structural_interpretation_histories_for_selector",
        ) as history, patch.object(boundary, "get_ancestors_by_token") as ancestors:
            for name in ("chapter", "verse", "token"):
                for value in invalid_values:
                    with self.subTest(name=name, length=len(value)):
                        query = {"chapter": "1", "verse": "2", name: value}
                        response = self.response("/verse?" + urlencode(query))
                        self.assertEqual(response.status, 400)
                        self.assertIn(b"INVALID_INPUT", response.body)
            for target in (
                "/verse", "/verse?chapter=1", "/verse?verse=1",
                "/verse?chapter=1&verse=1&chapter=1", "/verse?chapter=1&verse=1&token=1&token=2",
                "/verse?chapter=1&verse=1&unknown=x", "/verse?chapter=1&verse=1&candidate=",
                "/verse?chapter=1&verse=1&evaluation=bad", "/verse?chapter=1&verse=1&book=MAT&book=MAT",
                "/verse?chapter=%ZZ&verse=1", "/verse?chapter=%FF&verse=1",
                "/verse?chapter=1&verse=1#fragment", "/" + "x" * 256, "/" + "\u03b1" * 128,
                "/verse?" + "x" * 2049, "/?unknown=x", "/static/explorer.css?unknown=x",
            ):
                with self.subTest(target=target[:100]):
                    self.assertEqual(self.response(target).status, 400)
            for book in ("JHN", "mat", " MAT", ""):
                response = self.response("/verse?" + urlencode({"chapter": 1, "verse": 1, "book": book}))
                self.assertEqual(response.status, 400)
                self.assertIn(b"UNSUPPORTED", response.body)
            verse.assert_not_called()
            history.assert_not_called()
            ancestors.assert_not_called()

    def test_ac35_all_dynamic_strings_escaped_and_human_controls_visible(self) -> None:
        page = self.clause_page()
        hostile = '<script>alert("x")</script><img src=x onerror="bad">&\''
        token = replace(page.verse.tokens[0], surface=hostile, lemma=hostile, referent=hostile)
        evaluation = replace(
            page.selected_history.evaluations[0], evaluator_label=hostile + "\u202e\u2066\x01\x85",
            rationale_note_text=hostile + "\n\t\r\u202a\u2069",
            rationale_note_language='en" onmouseover="x',
        )
        history = replace(page.selected_history, evaluations=(evaluation,))
        candidate = replace(page.selected_candidate, derivation_version=hostile,
                            source_snapshot=replace(page.selected_candidate.source_snapshot, revision=hostile))
        page = replace(page, verse=replace(page.verse, tokens=(token, *page.verse.tokens[1:])),
                       selected_token=token, selected_candidate=candidate, selected_history=history,
                       projection=replace(page.projection, candidates=(candidate,), histories=(history,)))
        html = render_page(page)
        parsed = ParsedPage(html)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&quot;x&quot;", html)
        self.assertIn("U+202E", html)
        self.assertIn("U+2066", html)
        self.assertIn("U+0001", html)
        self.assertIn("U+0085", html)
        self.assertIn("U+000D", html)
        self.assertIn("\n\t", html)
        self.assertTrue(any(tag == "bdi" for tag, _ in parsed.elements))
        self.assertFalse(any(tag in ("script", "img") or any(n.startswith("on") for n in attrs)
                             for tag, attrs in parsed.elements))
        note = next(attrs for _, attrs in parsed.elements if attrs.get("class") == "rationale-note")
        self.assertNotIn("lang", note)
        self.assertIn(hostile, parsed.visible_text)
        self.assertNotIn('href="http', html)

    def test_ac35_safe_language_and_no_rationale_link_or_markdown(self) -> None:
        page = self.clause_page()
        evaluation = replace(page.selected_history.evaluations[0],
                             rationale_note_text="[link](https://example.invalid) **note**",
                             rationale_note_language="en-Latn-GB")
        html = render_page(replace(page, selected_history=replace(
            page.selected_history, evaluations=(evaluation,),
        )))
        self.assertIn('class="rationale-note" lang="en-Latn-GB"', html)
        self.assertIn("[link](https://example.invalid) **note**", html)
        self.assertNotIn('href="https://example.invalid', html)

    def test_all_bidi_and_control_characters_are_visible_only_for_human_text(self) -> None:
        page = self.clause_page()
        codes = (*range(0x202A, 0x202F), *range(0x2066, 0x206A),
                 *(n for n in range(0x20) if n not in (9, 10)), *range(0x7F, 0xA0))
        controls = "".join(chr(n) for n in codes)
        evaluation = replace(page.selected_history.evaluations[0],
                             evaluator_label=controls, rationale_note_text=controls + "\n\t")
        html = render_page(replace(
            page, selected_history=replace(page.selected_history, evaluations=(evaluation,)),
        ))
        for n in codes:
            self.assertIn(f"U+{n:04X}", html)
            self.assertNotIn(chr(n), html)
        token = replace(page.verse.tokens[0], surface="\u03b1\u202e")
        source_html = render_page(replace(
            page, verse=replace(page.verse, tokens=(token, *page.verse.tokens[1:])),
        ))
        self.assertIn("\u03b1\u202e", source_html)

    def test_ac36_37_surface_and_optional_fields_not_conflated(self) -> None:
        page = self.clause_page(token_ordinal=5)
        token = replace(page.selected_token, surface="\u03b1\u0301.", normalized="different",
                        unicode="", lemma=None, functional_tag="", formal_tag="formal",
                        ref="MAT 1:2!5", referent="distinct Ref")
        verse = replace(page.verse, tokens=(token, *page.verse.tokens[1:]))
        html = render_page(replace(page, verse=verse, selected_token=token))
        self.assertIn("\u03b1\u0301.", html)
        self.assertIn("<dt>normalized</dt><dd>different</dd>", html)
        self.assertIn("<dt>unicode</dt><dd>(present, empty)</dd>", html)
        self.assertIn("<dt>lemma</dt><dd>(absent)</dd>", html)
        self.assertIn("<dt>FunctionalTag</dt><dd>(present, empty)</dd>", html)
        self.assertIn("<dt>FormalTag</dt><dd>formal</dd>", html)
        self.assertIn("distinct Ref", html)
        self.assertIn("Advanced token facts", html)
        self.assertNotIn("joined text", html)
        for label, rendered in ((None, "no label recorded"), ("", "(present, empty)")):
            e = replace(page.selected_history.evaluations[0], evaluator_label=label)
            self.assertIn(rendered, render_page(replace(
                page, selected_history=replace(page.selected_history, evaluations=(e,)),
            )))

    def test_ac20_32_33_34_38_49_landmarks_wording_diagnostics_and_links(self) -> None:
        html = render_page(self.clause_page(token_ordinal=5))
        parsed = ParsedPage(html)
        self.assertTrue(all(any(tag == name for tag, _ in parsed.elements) for name in ("header", "nav", "main")))
        sections = [attrs for tag, attrs in parsed.elements if tag == "section"]
        self.assertEqual({a["data-epistemic"] for a in sections}, {
            "source_fact", "derived_structural_candidate", "human_evaluation",
        })
        self.assertTrue(all("aria-labelledby" in a for a in sections))
        self.assertEqual({a["for"] for tag, a in parsed.elements if tag == "label"}, {"chapter", "verse"})
        self.assertIn("Diagnostics", html)
        self.assertIn("candidate_id", html)
        self.assertIn("evaluation_id", html)
        self.assertIn("source_snapshot", html)
        for name in ("source_family", "edition", "repository_uri", "revision",
                     "manifest_sha256", "relative_path", "source_sha256"):
            self.assertIn(name, html)
        self.assertNotIn(str(self.fixture.source), html)
        text = parsed.visible_text.replace(wording.ORDER_NOTE, "")
        self.assertNotRegex(text.lower(), r"\b(current|latest|final|canonical|preferred|winning|actor|action|patient|event|result|identity|property|confidence|probability|percentage|rank|weight|score|count|previous|next)\b")
        self.assertNotIn("%", text)
        for tag, attrs in parsed.elements:
            if tag == "a":
                href = attrs["href"]
                self.assertTrue(href.startswith("/verse?"))
                self.assertEqual(self.response(href).status, 200)
        self.assertNotRegex(html, r"(?:token_id|book_id|tree_id|element_id|rowid)")

    def test_ac46_routes_methods_host_headers_and_head(self) -> None:
        for target in ("/", "/verse?chapter=1&verse=1", "/static/explorer.css", "/unknown"):
            get = self.response(target)
            head = self.response(target, "HEAD")
            self.assertEqual((head.status, head.headers), (get.status, get.headers))
            self.assertEqual(head.body, b"")
            self.assertEqual(dict(get.headers)["Content-Length"], str(len(get.body)))
            self.assertEqual(dict(get.headers)["X-Content-Type-Options"], "nosniff")
            self.assertEqual(dict(get.headers)["Referrer-Policy"], "no-referrer")
            self.assertEqual(dict(get.headers)["Cache-Control"], "no-store")
            self.assertEqual(dict(get.headers)["Content-Security-Policy"],
                             "default-src 'none'; style-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")
            self.assertNotIn("Set-Cookie", dict(get.headers))
        self.assertEqual(self.response("/unknown").status, 404)
        self.assertEqual(dict(self.response("/static/explorer.css").headers)["Content-Type"],
                         "text/css; charset=utf-8")
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE", "CUSTOM"):
            self.assertEqual(self.response("/", method).status, 405)
        for host in ("evil.invalid:8765", "localhost", "127.0.0.1", "localhost:8766", "", "127.0.0.2:8765"):
            self.assertEqual(self.response("/", host=host).status, 400)
        for host in ("localhost:8765", "127.0.0.1:8765", "[::1]:8765"):
            self.assertEqual(self.response("/", host=host).status, 200)
        for target in ("/static/", "/static/../config.py", "/static/%2e%2e/config.py", "/product/config.py"):
            self.assertEqual(self.response(target).status, 404)

    def test_ac46_real_http_server_get_head_duplicate_host_and_body_unread(self) -> None:
        with create_server(ProductConfig(self.fixture.source, port=0), self.adapter) as server:
            for request in (
                "GET / HTTP/1.1\r\nHost: localhost:{port}\r\n\r\n",
                "HEAD / HTTP/1.1\r\nHost: localhost:{port}\r\n\r\n",
                "CUSTOM / HTTP/1.1\r\nHost: localhost:{port}\r\nContent-Length: 99999\r\n\r\n",
                "GET / HTTP/1.1\r\nHost: localhost:{port}\r\nHost: localhost:{port}\r\n\r\n",
            ):
                thread = Thread(target=server.handle_request)
                thread.start()
                with socket.create_connection(server.server_address, timeout=5) as client:
                    client.sendall(request.format(port=server.server_port).encode())
                    chunks = []
                    while chunk := client.recv(65536):
                        chunks.append(chunk)
                thread.join(timeout=5)
                self.assertFalse(thread.is_alive())
                response = b"".join(chunks)
                if request.startswith("CUSTOM"):
                    self.assertIn(b"405", response.split(b"\r\n", 1)[0])
                elif request.count("Host:") == 2:
                    self.assertIn(b"400", response.split(b"\r\n", 1)[0])
                else:
                    self.assertIn(b"200", response.split(b"\r\n", 1)[0])
                    if request.startswith("HEAD"):
                        self.assertEqual(response.split(b"\r\n\r\n", 1)[1], b"")

    def test_ac46_ipv6_loopback_server(self) -> None:
        with create_server(ProductConfig(self.fixture.source, host="::1", port=0), self.adapter) as server:
            thread = Thread(target=server.handle_request)
            thread.start()
            with closing(HTTPConnection("::1", server.server_port, timeout=5)) as connection:
                connection.request("GET", "/")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                response.read()
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
