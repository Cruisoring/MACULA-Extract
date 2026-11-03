from contextlib import redirect_stderr
from dataclasses import replace
from io import StringIO
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import projection_store as store
from scripts import source_query as source
from scripts import projection_query as projection
from product import adapter as boundary
from product.adapter import ExplorerAdapter
from product.config import ProductConfig, parse_config
from product.errors import ErrorCategory
from product.models import ProductSelection, ProjectionState, SourceStatus
from product.server import handle_request
from tests.product.support.fixtures import build_source, file_state, temporary_fixture
from tests.support.unit8_amendment1_store import build_amendment1_store


class AdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = temporary_fixture(self)

    def test_ac17_startup_gates_order_and_once(self) -> None:
        with patch.object(boundary, "get_verse", wraps=source.get_verse) as verse, patch.object(
            boundary, "verify_projection_store", wraps=store.verify_projection_store,
        ) as verify:
            events = []
            verse.side_effect = lambda *args: (events.append("source"), source.get_verse(*args))[1]
            verify.side_effect = lambda *args: (events.append("offline" if len(args) == 1 else "bound"),
                                                store.verify_projection_store(*args))[1]
            adapter = self.fixture.adapter()
            self.assertEqual(events, ["source", "offline", "bound"])
            self.assertEqual(adapter.source_status, SourceStatus.READY)
            self.assertEqual(verify.call_args_list[0].args, (self.fixture.projection,))
            self.assertEqual(verify.call_args_list[1].args,
                             (self.fixture.projection, self.fixture.source))
            for selection in (ProductSelection("MAT", 1, 1), ProductSelection("MAT", 1, 2)):
                adapter.load_verse(selection)
            self.assertEqual(verify.call_count, 2)
            self.assertEqual(verse.call_count, 3)

    def test_ac45_one_history_call_with_every_selection(self) -> None:
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_structural_interpretation_histories_for_selector",
                          wraps=projection.get_structural_interpretation_histories_for_selector) as histories:
            for selection in (
                ProductSelection("MAT", 1, 2),
                ProductSelection("MAT", 1, 2, 5),
                ProductSelection("MAT", 1, 2, 5, self.fixture.clause_id),
                ProductSelection("MAT", 1, 2, 5, self.fixture.clause_id,
                                 self.fixture.evaluations[1].evaluation_id),
            ):
                histories.reset_mock()
                page = adapter.load_verse(selection)
                self.assertIsNotNone(page.verse)
                self.assertEqual(histories.call_count, 1)
                selector = histories.call_args.args[1]
                self.assertEqual((selector.book, selector.chapter, selector.verse, selector.token),
                                 ("MAT", 1, 2, None))
                self.assertIs(type(selector.chapter), int)

    def test_ac20_source_ancestry_budget_and_first_encounter_order(self) -> None:
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_ancestors_by_token", wraps=source.get_ancestors_by_token) as ancestors:
            page = adapter.load_verse(ProductSelection("MAT", 1, 1))
            self.assertEqual(ancestors.call_count, 8)
            expected = {}
            for token in page.verse.tokens:
                for node in source.get_ancestors_by_token(self.fixture.source, token.ref):
                    expected.setdefault(node.source_node_id, node)
            self.assertEqual(tuple(n.key for n in page.verse.source_nodes), tuple(expected))
            self.assertEqual([t.ordinal for t in page.verse.tokens], list(range(1, 9)))

    def test_ac15_invalid_direct_selections_never_reach_core(self) -> None:
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_verse") as verse, patch.object(
            boundary, "get_structural_interpretation_histories_for_selector",
        ) as history, patch.object(boundary, "get_ancestors_by_token") as ancestors:
            for selection in (
                ProductSelection("MAT", 0, 1), ProductSelection("MAT", True, 1),
                ProductSelection("MAT", 2**63, 1), ProductSelection("MAT", 1, 1, -1),
                ProductSelection("MAT", 1, 1, candidate_id="bad"),
                ProductSelection("MAT", 1, 1, evaluation_id="bad"),
            ):
                self.assertEqual(adapter.load_verse(selection).error.category, ErrorCategory.INVALID_INPUT)
            self.assertEqual(adapter.load_verse(ProductSelection("JHN", 1, 1)).error.category,
                             ErrorCategory.UNSUPPORTED)
            verse.assert_not_called()
            history.assert_not_called()
            ancestors.assert_not_called()

    def test_p9_absent_verse_stops_before_projection(self) -> None:
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_structural_interpretation_histories_for_selector") as query:
            page = adapter.load_verse(ProductSelection("MAT", 99, 99))
            self.assertEqual(page.error.category, ErrorCategory.ABSENT)
            self.assertIn("MAT 99:99", page.error.message)
            query.assert_not_called()

    def test_ac18_stale_source_and_projection_are_latched(self) -> None:
        for name in ("source", "projection"):
            with self.subTest(store=name), TemporaryDirectory(prefix="macula-stale-") as directory:
                source_path = Path(directory) / "source.sqlite3"
                projection_path = Path(directory) / "projection.sqlite3"
                shutil.copyfile(self.fixture.source, source_path)
                shutil.copyfile(self.fixture.projection, projection_path)
                adapter = ExplorerAdapter(ProductConfig(source_path, projection_path))
                target = source_path if name == "source" else projection_path
                stat = target.stat()
                os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000))
                before = file_state(source_path), file_state(projection_path)
                with patch.object(boundary, "verify_projection_store") as verify, patch.object(
                    boundary, "get_structural_interpretation_histories_for_selector",
                ) as query:
                    page = adapter.load_verse(ProductSelection("MAT", 1, 2))
                    self.assertIsNotNone(page.verse)
                    self.assertEqual(page.projection.state, ProjectionState.BINDING_FAILED)
                    self.assertEqual(page.projection.error.category, ErrorCategory.SOURCE_PROJECTION_MISMATCH)
                    self.assertFalse(page.projection.candidates)
                    os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
                    self.assertEqual(adapter.status().projection_state, ProjectionState.BINDING_FAILED)
                    query.assert_not_called()
                    verify.assert_not_called()
                os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000))
                self.assertEqual((file_state(source_path), file_state(projection_path)), before)

    def test_ac44_stage_and_exception_class_not_messages(self) -> None:
        for exception in (source.QueryError("private-path"), ValueError("private-path"),
                          AttributeError("private-path"), RecursionError("private-path")):
            with self.subTest(exception=type(exception)), redirect_stderr(StringIO()) as log:
                with patch.object(boundary, "get_verse", side_effect=exception), patch.object(
                    boundary, "verify_projection_store",
                ) as verify:
                    adapter = self.fixture.adapter()
                    expected = (ErrorCategory.SOURCE_STORE_ERROR if type(exception) is source.QueryError
                                else ErrorCategory.INTEGRITY_ERROR)
                    self.assertEqual(adapter.source_error.category, expected)
                    verify.assert_not_called()
                    self.assertNotIn("private-path", adapter.source_error.message)
                    self.assertEqual(log.getvalue().strip(), type(exception).__name__)
        for stage in (1, 2):
            for exception in (source.QueryError("same message"), ValueError("same message")):
                with self.subTest(stage=stage, exception=type(exception)), redirect_stderr(StringIO()):
                    with patch.object(boundary, "verify_projection_store",
                                      side_effect=exception if stage == 1 else [None, exception]):
                        adapter = self.fixture.adapter()
                        expected = (ErrorCategory.INTEGRITY_ERROR if type(exception) is ValueError else
                                    ErrorCategory.PROJECTION_STORE_ERROR if stage == 1 else
                                    ErrorCategory.SOURCE_PROJECTION_MISMATCH)
                        self.assertEqual(adapter.binding.error.category, expected)

    def test_p7_unconfigured_has_no_verification_or_projection_calls(self) -> None:
        with patch.object(boundary, "verify_projection_store") as verify, patch.object(
            boundary, "get_structural_interpretation_histories_for_selector",
        ) as query:
            page = self.fixture.adapter(False).load_verse(ProductSelection("MAT", 1, 1))
            self.assertEqual(page.projection.state, ProjectionState.NOT_CONFIGURED)
            self.assertEqual(page.projection.error.category, ErrorCategory.PROJECTION_STORE_NOT_CONFIGURED)
            self.assertIsNotNone(page.verse)
            verify.assert_not_called()
            query.assert_not_called()

    def test_p8_missing_invalid_and_non_unit10_projection(self) -> None:
        for kind in ("missing", "garbage", "source"):
            with self.subTest(kind=kind), TemporaryDirectory(prefix="macula-invalid-") as directory:
                path = Path(directory) / "projection.sqlite3"
                if kind == "garbage":
                    path.write_bytes(b"not a SQLite database")
                elif kind == "source":
                    shutil.copyfile(self.fixture.source, path)
                before = file_state(path) if path.exists() else None
                with redirect_stderr(StringIO()):
                    adapter = ExplorerAdapter(ProductConfig(self.fixture.source, path))
                    page = adapter.load_verse(ProductSelection("MAT", 1, 1))
                self.assertIsNotNone(page.verse)
                self.assertEqual(page.projection.state, ProjectionState.CONFIGURED_ERROR)
                self.assertEqual(page.projection.error.category, ErrorCategory.PROJECTION_STORE_ERROR)
                self.assertEqual(file_state(path) if path.exists() else None, before)

    def test_p11_real_source_snapshot_mismatch(self) -> None:
        with TemporaryDirectory(prefix="macula-binding-") as directory:
            incompatible = Path(directory) / "source.sqlite3"
            build_amendment1_store(incompatible)
            before = file_state(incompatible)
            with redirect_stderr(StringIO()):
                adapter = ExplorerAdapter(ProductConfig(incompatible, self.fixture.projection))
            page = adapter.load_verse(ProductSelection("MAT", 1, 1))
            self.assertEqual(page.projection.state, ProjectionState.BINDING_FAILED)
            self.assertEqual(page.projection.error.category, ErrorCategory.SOURCE_PROJECTION_MISMATCH)
            self.assertIsNotNone(page.verse)
            self.assertFalse(page.projection.candidates)
            self.assertEqual(file_state(incompatible), before)

    def test_source_gate_absent_or_unopenable_and_request_error(self) -> None:
        with patch.object(boundary, "get_verse", return_value=None), patch.object(
            boundary, "verify_projection_store",
        ) as verify:
            adapter = self.fixture.adapter()
            self.assertEqual(adapter.source_error.category, ErrorCategory.SOURCE_STORE_ERROR)
            verify.assert_not_called()
        with TemporaryDirectory(prefix="macula-missing-source-") as directory, redirect_stderr(StringIO()):
            adapter = ExplorerAdapter(ProductConfig(Path(directory) / "missing.sqlite3"))
            response = handle_request(adapter, "GET", "/", "localhost:8765", 8765)
            self.assertEqual(response.status, 500)
            self.assertFalse(adapter.config.source_db_path.exists())
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_ancestors_by_token", side_effect=source.QueryError("secret")), patch.object(
            boundary, "get_structural_interpretation_histories_for_selector",
        ) as query, redirect_stderr(StringIO()):
            page = adapter.load_verse(ProductSelection("MAT", 1, 1))
            self.assertEqual(page.error.category, ErrorCategory.SOURCE_STORE_ERROR)
            query.assert_not_called()

    def test_request_projection_errors_preserve_source(self) -> None:
        adapter = self.fixture.adapter()
        for exception in (projection.ProjectionQueryError("secret"), ValueError("secret")):
            with self.subTest(exception=type(exception)), redirect_stderr(StringIO()), patch.object(
                boundary, "get_structural_interpretation_histories_for_selector", side_effect=exception,
            ):
                page = adapter.load_verse(ProductSelection("MAT", 1, 2))
                self.assertIsNotNone(page.verse)
                self.assertFalse(page.projection.candidates)
                self.assertEqual(page.projection.error.category,
                                 ErrorCategory.PROJECTION_STORE_ERROR if type(exception) is projection.ProjectionQueryError
                                 else ErrorCategory.INTEGRITY_ERROR)

    def test_candidate_evidence_budget_and_contradiction(self) -> None:
        adapter = self.fixture.adapter()
        with patch.object(boundary, "get_node", wraps=source.get_node) as node:
            page = adapter.load_verse(ProductSelection("MAT", 1, 2, candidate_id=self.fixture.clause_id))
            self.assertEqual(node.call_count, len(page.selected_candidate.evidence))
            self.assertEqual(tuple(n.key for n in page.projection.evidence_nodes),
                             tuple(e[2] for e in page.selected_candidate.evidence))
        with patch.object(boundary, "get_node", return_value=None), redirect_stderr(StringIO()):
            page = adapter.load_verse(ProductSelection("MAT", 1, 2, candidate_id=self.fixture.clause_id))
            self.assertEqual(page.projection.candidate_error.category, ErrorCategory.INTEGRITY_ERROR)
            self.assertIsNone(page.selected_candidate)
            self.assertIsNotNone(page.verse)

    def test_binding_change_during_evidence_read_suppresses_projection(self) -> None:
        with TemporaryDirectory(prefix="macula-binding-race-") as directory:
            source_path = Path(directory) / "source.sqlite3"
            projection_path = Path(directory) / "projection.sqlite3"
            shutil.copyfile(self.fixture.source, source_path)
            shutil.copyfile(self.fixture.projection, projection_path)
            adapter = ExplorerAdapter(ProductConfig(source_path, projection_path))
            before = file_state(source_path), file_state(projection_path)
            stat = projection_path.stat()

            def read_node(*args):
                node = source.get_node(*args)
                os.utime(projection_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000))
                return node

            try:
                with patch.object(boundary, "get_node", side_effect=read_node):
                    page = adapter.load_verse(ProductSelection(
                        "MAT", 1, 2, candidate_id=self.fixture.clause_id,
                    ))
                self.assertEqual(page.projection.state, ProjectionState.BINDING_FAILED)
                self.assertFalse(page.projection.candidates)
                self.assertIsNone(page.selected_candidate)
                self.assertIsNotNone(page.verse)
            finally:
                os.utime(projection_path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            self.assertEqual((file_state(source_path), file_state(projection_path)), before)

    def test_ac08_pk_and_path_invariance(self) -> None:
        with TemporaryDirectory(prefix="macula-product-pk-") as directory:
            alternative = Path(directory) / "elsewhere.sqlite3"
            build_source(alternative, pk_offset=10000)
            before = file_state(alternative)
            left = self.fixture.adapter(False).load_verse(ProductSelection("MAT", 1, 1))
            right = ExplorerAdapter(ProductConfig(alternative)).load_verse(ProductSelection("MAT", 1, 1))
            self.assertEqual(left.verse, right.verse)
            self.assertEqual(file_state(alternative), before)

    def test_selection_absence_and_evaluation_only_selection(self) -> None:
        adapter = self.fixture.adapter()
        for selection in (
            ProductSelection("MAT", 1, 2, 999),
            ProductSelection("MAT", 1, 2, candidate_id="sha256:" + "0" * 64),
            ProductSelection("MAT", 1, 2, evaluation_id="eval-sha256:" + "0" * 64),
        ):
            page = adapter.load_verse(selection)
            self.assertIsNotNone(page.verse)
            self.assertEqual(page.notices[0].category, ErrorCategory.ABSENT)
        page = adapter.load_verse(ProductSelection(
            "MAT", 1, 2, evaluation_id=self.fixture.evaluations[1].evaluation_id,
        ))
        self.assertEqual(page.selected_candidate.key, self.fixture.clause_id)
        self.assertEqual(len(page.selected_history.evaluations), 4)


class ConfigTests(unittest.TestCase):
    def test_ac48_cli_environment_precedence_and_empty_values(self) -> None:
        with TemporaryDirectory(prefix="macula-config-") as directory:
            source_path = Path(directory) / "source.sqlite3"
            projection_path = Path(directory) / "projection.sqlite3"
            env = {"MACULA_EXPLORER_SOURCE_DB": str(source_path),
                   "MACULA_EXPLORER_PROJECTION_DB": str(projection_path)}
            config = parse_config([], env)
            self.assertEqual(config.source_db_path, source_path.resolve())
            self.assertEqual(config.projection_db_path, projection_path.resolve())
            config = parse_config(["--source-db", str(projection_path), "--projection-db", " "], env)
            self.assertEqual(config.source_db_path, projection_path.resolve())
            self.assertIsNone(config.projection_db_path)
            self.assertEqual((config.host, config.port), ("127.0.0.1", 8765))
            self.assertEqual(parse_config(["--source-db", str(source_path), "--port", "0"], {}).port, 0)
            self.assertFalse(source_path.exists())
            self.assertFalse(projection_path.exists())

    def test_ac48_usage_errors_exit_two(self) -> None:
        for args, env in (
            ([], {}), (["--source-db", " "], {"MACULA_EXPLORER_SOURCE_DB": "present"}),
            (["--source-db", "x", "--projection-db", "x"], {}),
            (["--source-db", "x", "--host", "0.0.0.0"], {}),
            (["--source-db", "x", "--host", "localhost"], {}),
            (["--source-db", "x", "--port", "-1"], {}),
            (["--source-db", "x", "--port", "65536"], {}),
            (["--source-db", "x", "--port", "1.2"], {}),
        ):
            with self.subTest(args=args), redirect_stderr(StringIO()), self.assertRaises(SystemExit) as exit:
                parse_config(args, env)
            self.assertEqual(exit.exception.code, 2)

    def test_same_physical_file_and_invalid_programmatic_config(self) -> None:
        with TemporaryDirectory(prefix="macula-samefile-") as directory:
            source_path = Path(directory) / "source"
            source_path.write_bytes(b"fixture")
            alias = Path(directory) / "alias"
            os.link(source_path, alias)
            with self.assertRaises(ValueError):
                ProductConfig(source_path, alias)
        for port in (True, -1, 65536):
            with self.assertRaises(ValueError):
                ProductConfig(Path("source"), port=port)
