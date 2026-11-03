import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from enum import Enum
from pathlib import Path
import re
import unittest

from product import models
from product.errors import ErrorCategory, ProductError
from product.models import ProductSelection
from tests.product.support.fixtures import temporary_fixture


ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "product"
PRODUCTION_FILES = {
    "__init__.py", "__main__.py", "config.py", "errors.py", "models.py",
    "validation.py", "adapter.py", "wording.py", "presentation.py", "server.py",
    "static/explorer.css",
}
PERMITTED = {
    "scripts.source_query": {"get_verse", "get_ancestors_by_token", "get_node", "QueryError"},
    "scripts.projection_query": {
        "ScriptureSelector", "get_structural_interpretation_histories_for_selector", "ProjectionQueryError",
    },
    "scripts.projection_store": {"verify_projection_store"},
}
FORBIDDEN_FIELDS = {
    "token_id", "book_id", "node_id", "tree_id", "element_id", "rowid", "event_key",
    "timestamp", "insertion_order", "confidence", "probability", "percentage", "score",
    "rank", "weight", "count", "source_db_path", "projection_db_path",
    "start_raw", "end_raw", "length_raw", "record_protocol",
}


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = temporary_fixture(self)
        self.page = self.fixture.adapter().load_verse(
            ProductSelection("MAT", 1, 2, 5, self.fixture.clause_id),
        )

    def test_ac07_immutable_model_tree_no_research_dtos(self) -> None:
        def check(value) -> None:
            if is_dataclass(value):
                self.assertTrue(type(value).__module__.startswith("product."))
                self.assertTrue(type(value).__dataclass_params__.frozen)
                self.assertTrue(hasattr(type(value), "__slots__"))
                self.assertFalse(FORBIDDEN_FIELDS & {f.name for f in fields(value)})
                for f in fields(value):
                    check(getattr(value, f.name))
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    value.unexpected = "mutation"
            elif isinstance(value, tuple):
                for item in value:
                    check(item)
            else:
                self.assertIsInstance(value, (str, int, bool, Enum, type(None)))
        check(self.page)
        for value in (self.page.verse, self.page.selected_candidate, self.page.selected_history,
                      self.page.selected_token, self.page.verse.source_nodes[0]):
            with self.assertRaises(FrozenInstanceError):
                value.epistemic_class = models.EpistemicClass.EVALUATION

    def test_ac08_stable_keys_and_snapshot_fields(self) -> None:
        self.assertEqual(self.page.verse.key, "MAT 1:2")
        self.assertEqual(self.page.selected_token.key, "MAT 1:2!5")
        self.assertEqual(self.page.selected_candidate.key, self.fixture.clause_id)
        self.assertEqual(self.page.selected_history.key, self.fixture.clause_id)
        self.assertEqual(self.page.selected_history.evaluations[0].key,
                         self.page.selected_history.evaluations[0].evaluation_id)
        self.assertEqual(self.page.selection.key, ("MAT", 1, 2, 5, self.fixture.clause_id, None))
        self.assertEqual({f.name for f in fields(self.page.selected_candidate.source_snapshot)}, {
            "source_family", "edition", "repository_uri", "revision",
            "manifest_sha256", "relative_path", "source_sha256",
        })
        self.assertNotIn(str(self.fixture.source), repr(self.page))

    def test_ac37_absent_and_present_empty_remain_distinct(self) -> None:
        token = self.page.selected_token
        absent = replace(token, normalized=None, functional_tag=None)
        empty = replace(token, normalized="", functional_tag="")
        self.assertIsNone(absent.normalized)
        self.assertEqual(empty.normalized, "")
        self.assertNotEqual(absent, empty)
        evaluation = self.page.selected_history.evaluations[0]
        self.assertNotEqual(replace(evaluation, evaluator_label=None),
                            replace(evaluation, evaluator_label=""))

    def test_ac20_epistemic_and_error_categories_are_closed(self) -> None:
        self.assertEqual({v.value for v in models.EpistemicClass}, {
            "source_fact", "derived_structural_candidate", "human_evaluation",
        })
        self.assertEqual({v.value for v in models.ProjectionState}, {
            "NOT_CONFIGURED", "CONFIGURED_ERROR", "BINDING_FAILED",
            "VERIFIED_EMPTY", "VERIFIED_POPULATED",
        })
        self.assertEqual({v.value for v in ErrorCategory}, {
            "ABSENT", "INVALID_INPUT", "UNSUPPORTED", "SOURCE_STORE_ERROR",
            "PROJECTION_STORE_NOT_CONFIGURED", "PROJECTION_STORE_ERROR",
            "SOURCE_PROJECTION_MISMATCH", "INTEGRITY_ERROR",
        })
        with self.assertRaises(ValueError):
            ErrorCategory("unknown")
        error = ProductError(ErrorCategory.ABSENT, "selection", "Absent.")
        with self.assertRaises(FrozenInstanceError):
            error.message = "changed"


class ArchitectureTests(unittest.TestCase):
    def test_ac03_to_10_exact_paths_stdlib_and_closed_core_imports(self) -> None:
        self.assertEqual({p.relative_to(PRODUCT).as_posix() for p in PRODUCT.rglob("*") if p.is_file()},
                         PRODUCTION_FILES)
        imported_core = set()
        for path in PRODUCT.rglob("*.py"):
            with self.subTest(path=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 10))
                core_names = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        self.assertFalse(any(n.name == "sqlite3" or n.name.startswith("scripts")
                                             for n in node.names))
                        self.assertTrue(all(n.name.split(".")[0] in {
                            "argparse", "os", "sys", "re", "socket",
                        } for n in node.names))
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        self.assertNotEqual(module, "sqlite3")
                        if module.startswith("scripts"):
                            self.assertEqual(path.name, "adapter.py")
                            self.assertIn(module, PERMITTED)
                            self.assertEqual({n.name for n in node.names}, PERMITTED[module])
                            self.assertTrue(all(n.asname is None for n in node.names))
                            imported_core.add(module)
                            core_names.update(n.name for n in node.names)
                        else:
                            self.assertIn(module.split(".")[0], {
                                "product", "dataclasses", "enum", "typing", "collections",
                                "pathlib", "html", "http", "urllib",
                            })
                        if path.name == "presentation.py" and module.startswith("product"):
                            self.assertIn(module, {"product.models", "product.errors", "product"})
                            if module == "product":
                                self.assertEqual([n.name for n in node.names], ["wording"])
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        self.assertNotIn(node.func.id, {"open", "eval", "exec", "__import__"})
                        if node.func.id in core_names:
                            self.assertIn(node.func.id, set().union(*PERMITTED.values()))
                    if isinstance(node, ast.Attribute):
                        self.assertNotIn(node.attr, {
                            "store_candidate", "store_evaluation", "initialize_projection_store",
                            "create_evaluated_interpretation", "derive_structural_candidates",
                            "execute", "executemany", "executescript", "write_text", "write_bytes",
                        })
        self.assertEqual(imported_core, set(PERMITTED))

    def test_ac13_14_24_38_47_no_extra_state_network_or_scope_algorithm(self) -> None:
        code = "\n".join(p.read_text(encoding="utf-8") for p in PRODUCT.rglob("*.py"))
        for word in ("sqlite3", "min(", "max(", "start_raw", "end_raw", "rowid",
                     "urlopen", "requests", "set_cookie", "Previous", "Next"):
            self.assertNotIn(word, code)
        self.assertIsNone(re.search(r"\bsession\b", code))
        css = (PRODUCT / "static" / "explorer.css").read_text(encoding="utf-8")
        for forbidden in ("~", "+", ":has", "@import", "url(", "javascript"):
            self.assertNotIn(forbidden, css.lower())
        for pattern in ("*.js", "*.ts", "*requirements*.txt", "*package*.json", "*lock*",
                        "pyproject.toml", "*.sqlite*", "*.db", "*.pyc"):
            self.assertFalse(list(PRODUCT.rglob(pattern)))
