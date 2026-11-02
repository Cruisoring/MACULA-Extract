from contextlib import closing
from dataclasses import FrozenInstanceError, fields, replace
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import evaluated_interpretations as evaluated
from scripts import projection_query as pq
from scripts import projection_store as store
from scripts import source_query as query
from scripts import structural_candidates as structural
from tests.support.unit8_amendment1_store import build_amendment1_store
from tests.test_unit10 import (
    ABSENT_CANDIDATE, ABSENT_EVALUATION, REFS, ROOT, SVO_ID, alter_record, derive,
    independent_candidate_id, record_for, state,
)


DDL_SHA256 = "93be60ede8751c8fa48f74495f8140e8eb7832d583449be06a51b03b2773347b"
PUBLIC_FUNCTIONS = {
    "list_persisted_candidates_for_selector", "list_persisted_candidates_for_chapter",
    "list_persisted_candidates_for_verse", "list_persisted_candidates_for_token",
    "get_persisted_candidate", "get_persisted_evaluation", "list_candidate_evaluations",
    "get_evaluation_history", "list_unsuperseded_evaluations",
    "get_structural_interpretation_history", "get_structural_interpretation_histories_for_selector",
}
FORBIDDEN_CALLS = {
    sqlite3.SQLITE_INSERT, sqlite3.SQLITE_UPDATE, sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_CREATE_TABLE, sqlite3.SQLITE_CREATE_INDEX, sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_CREATE_VIEW, sqlite3.SQLITE_DROP_TABLE, sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_DROP_TRIGGER, sqlite3.SQLITE_DROP_VIEW, sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH,
}
_REAL_CONNECT = sqlite3.connect
_REF = re.compile(r"MAT (\d+):(\d+)!(\d+)")


def coordinate(ref: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in _REF.fullmatch(ref).groups())  # type: ignore[return-value]


def ids(candidates: tuple[store.Candidate, ...]) -> tuple[str, ...]:
    return tuple(candidate.candidate_id for candidate in candidates)


def raw_candidate(path: Path, candidate: store.Candidate) -> None:
    with closing(sqlite3.connect(path)) as db:
        db.execute("INSERT INTO candidate VALUES (?,?)",
                   (candidate.candidate_id, store._candidate_json(candidate)))
        db.commit()


def variant(base: store.Candidate, s: tuple[str, ...], v: tuple[str, ...],
            o: tuple[str, ...]) -> store.Candidate:
    components = tuple(replace(component, member_token_refs=refs)
                       for component, refs in zip(base.payload.components, (s, v, o)))
    scope = replace(base.scope, member_token_refs=tuple(sorted(set(s + v + o), key=coordinate)))
    draft = replace(base, payload=replace(base.payload, components=components), scope=scope)
    return replace(draft, candidate_id=independent_candidate_id(draft))


class TrackedConnection(sqlite3.Connection):
    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.closed = False
        self.forbidden: list[int] = []
        self.set_authorizer(self._authorize)

    def _authorize(self, action: int, *_: object) -> int:
        if action in FORBIDDEN_CALLS:
            self.forbidden.append(action)
        return sqlite3.SQLITE_OK

    def close(self) -> None:
        self.closed = True
        super().close()


class Unit11Base(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit11-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "source.sqlite3"
        self.path = self.directory / "projection.sqlite3"
        build_amendment1_store(self.source)
        store.initialize_projection_store(self.path)
        self.appositions = derive(self.source, "MAT 1:1!3")
        self.clause = derive(self.source, REFS[0])[0]
        for candidate in (*self.appositions, self.clause):
            store.store_candidate(self.path, candidate, source_db_path=self.source)
        self.r0 = record_for(self.source, self.clause)
        self.r1 = record_for(self.source, self.clause, event="unit10:2", disposition="accepted",
                             predecessor=self.r0, prior=(self.r0,))
        self.r2 = record_for(self.source, self.clause, event="unit10:3", disposition="rejected",
                             predecessor=self.r0, prior=(self.r0, self.r1))
        self.other = record_for(self.source, self.clause, event="other:1", label="other-evaluator",
                                disposition="rejected")
        for record in (self.r0, self.r1, self.r2, self.other):
            store.store_evaluation(self.path, record, source_db_path=self.source)

    def clause_selector_hits(self, ref: str) -> tuple[str, ...]:
        return ids(pq.list_persisted_candidates_for_token(self.path, ref))


class SelectorAndDiscoveryTests(Unit11Base):
    def test_01_public_surface_is_exact_and_read_only(self) -> None:
        public = {name for name, value in vars(pq).items()
                  if inspect.isfunction(value) and not name.startswith("_")
                  and value.__module__ == pq.__name__}
        self.assertEqual(public, PUBLIC_FUNCTIONS)
        for name in PUBLIC_FUNCTIONS:
            self.assertEqual(next(iter(inspect.signature(getattr(pq, name)).parameters)),
                             "projection_db_path")
        source = inspect.getsource(pq)
        for word in ("store_candidate", "store_evaluation", "initialize_projection_store",
                     "derive_structural_candidates", "create_evaluated_interpretation",
                     "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ATTACH", "DETACH",
                     "GLOB", "LIKE", "rowid", "ORDER BY", "startswith"):
            self.assertNotIn(word, source)
        names = " ".join([*PUBLIC_FUNCTIONS, *(field.name for dto in (
            pq.ScriptureSelector, pq.SupersessionEdge, pq.StructuralInterpretationHistory)
            for field in fields(dto))]).lower()
        for word in ("current", "latest", "best", "canonical", "consensus", "winner", "score",
                     "rank", "confidence", "preferred", "majority", "probab", "actor", "event",
                     "patient", "identity"):
            self.assertNotIn(word, names)

    def test_02_selector_validation(self) -> None:
        pq.ScriptureSelector("MAT")
        pq.ScriptureSelector("MAT", 1, 2, 5)
        for args in (("mat",), ("JHN",), (None,), ("MAT", 0), ("MAT", -1), ("MAT", True),
                     ("MAT", "1"), ("MAT", 1.0), ("MAT", None, 2), ("MAT", 1, None, 5),
                     ("MAT", 1, 0), ("MAT", 1, 2, 0), ("MAT", 2**63), ("MAT", 1, 2, False)):
            with self.subTest(args=args), self.assertRaises(pq.ProjectionQueryError):
                pq.ScriptureSelector(*args)
        selector = pq.ScriptureSelector("MAT", 1)
        with self.assertRaises(FrozenInstanceError):
            selector.chapter = 2  # type: ignore[misc]

    def test_03_selector_revalidated_on_use_before_database_access(self) -> None:
        bad = object.__new__(pq.ScriptureSelector)
        for name, value in (("book", "MAT"), ("chapter", 0), ("verse", None), ("token", None)):
            object.__setattr__(bad, name, value)
        missing = self.directory / "never-created.sqlite3"
        for call in (pq.list_persisted_candidates_for_selector,
                     pq.get_structural_interpretation_histories_for_selector):
            with self.assertRaisesRegex(pq.ProjectionQueryError, "positive integer"):
                call(missing, bad)
            with self.assertRaisesRegex(pq.ProjectionQueryError, "ScriptureSelector"):
                call(missing, ("MAT", 1))  # type: ignore[arg-type]
        self.assertFalse(missing.exists())

    def test_04_string_forms_are_strict(self) -> None:
        missing = self.directory / "never-created.sqlite3"
        for ref in ("MAT 1:2 trailing", "mat 1:2", "MAT 0:2", "MAT 1:0", "MAT 1:02", "MAT 01:2",
                    " MAT 1:2", "MAT 1:2 ", "MAT 1:2!5", "MAT  1:2", "MAT 1:2:3", "", None, 12):
            with self.subTest(ref=ref), self.assertRaisesRegex(pq.ProjectionQueryError, "verse_ref"):
                pq.list_persisted_candidates_for_verse(missing, ref)  # type: ignore[arg-type]
        for ref in ("MAT 1:2", "MAT 1:2!5x", "MAT 1:2!5-7", "mat 1:2!5", "MAT 1:2!0", "MAT 1:2!05",
                    "MAT 1:2!5 ", " MAT 1:2!5", "MAT 1:2!5/anything", "MAT 1:2!", "MAT 1:2!5\n",
                    "MAT 1:2!\u0665", None):
            with self.subTest(ref=ref), self.assertRaisesRegex(pq.ProjectionQueryError, "token_ref"):
                pq.list_persisted_candidates_for_token(missing, ref)  # type: ignore[arg-type]
        for call, ref in ((pq.list_persisted_candidates_for_verse, "MAT 1:" + str(2**63)),
                          (pq.list_persisted_candidates_for_token, "MAT 1:2!" + "9" * 20)):
            with self.assertRaises(pq.ProjectionQueryError):
                call(missing, ref)
        for chapter in (None, 0, True, "1"):
            with self.subTest(chapter=chapter), self.assertRaises(pq.ProjectionQueryError):
                pq.list_persisted_candidates_for_chapter(missing, "MAT", chapter)  # type: ignore[arg-type]
        with self.assertRaises(pq.ProjectionQueryError):
            pq.list_persisted_candidates_for_chapter(missing, "JHN", 1)
        self.assertFalse(missing.exists())

    def test_05_discovery_without_candidate_id_and_matthew_1_2_negative_case(self) -> None:
        clause_id = self.clause.candidate_id
        self.assertEqual(ids(pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2")), (clause_id,))
        for ref in ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9"):
            with self.subTest(ref=ref):
                self.assertEqual(self.clause_selector_hits(ref), (clause_id,))
        self.assertEqual(self.clause_selector_hits("MAT 1:2!6"), ())
        for ref in ("MAT 1:2!4", "MAT 1:2!10", "MAT 1:3!5", "MAT 2:2!5"):
            self.assertEqual(self.clause_selector_hits(ref), ())
        found = pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!5")[0]
        self.assertEqual(found.scope.member_token_refs, REFS)
        self.assertNotIn("MAT 1:2!6", found.scope.member_token_refs)
        self.assertEqual(found, self.clause)

    def test_06_scope_is_never_expanded_by_broader_selectors(self) -> None:
        for call in (lambda: pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2"),
                     lambda: pq.list_persisted_candidates_for_chapter(self.path, "MAT", 1),
                     lambda: pq.list_persisted_candidates_for_selector(self.path, pq.ScriptureSelector("MAT")),
                     lambda: pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!9")):
            clause = [c for c in call() if c.candidate_id == self.clause.candidate_id][0]
            self.assertEqual(clause, self.clause)
            self.assertEqual(clause.scope.member_token_refs, REFS)
            self.assertEqual(tuple(ref for part in clause.payload.components
                                   for ref in part.member_token_refs), REFS)

    def test_07_exact_membership_oracle_for_every_apposition_token(self) -> None:
        for token in range(1, 12):
            ref = f"MAT 1:1!{token}"
            expected = {c.candidate_id for c in self.appositions if ref in c.scope.member_token_refs}
            self.assertEqual(set(self.clause_selector_hits(ref)), expected, ref)

    def test_08_candidates_without_evaluations_are_discoverable(self) -> None:
        self.assertEqual({c.candidate_id for c in pq.list_persisted_candidates_for_verse(self.path, "MAT 1:1")},
                         {c.candidate_id for c in self.appositions})
        for candidate in self.appositions:
            self.assertEqual(pq.list_candidate_evaluations(self.path, candidate.candidate_id), ())
            history = pq.get_structural_interpretation_history(self.path, candidate.candidate_id)
            self.assertEqual(history, pq.StructuralInterpretationHistory(candidate, (), (), ()))

    def test_09_matthew_1_1_stays_verbless_apposition_only(self) -> None:
        found = pq.list_persisted_candidates_for_verse(self.path, "MAT 1:1")
        self.assertEqual({c.candidate_kind for c in found}, {"apposition"})
        self.assertTrue(all(type(c) is structural.StructuralCandidate for c in found))
        self.assertTrue(any(node.cl_type == "Verbless"
                            for node in query.get_ancestors_by_token(self.source, "MAT 1:1!3")))
        for history in pq.get_structural_interpretation_histories_for_selector(
                self.path, pq.ScriptureSelector("MAT", 1, 1)):
            self.assertEqual(history.evaluations, ())

    def test_10_no_match_is_empty_not_error_and_book_level_selector(self) -> None:
        self.assertEqual(pq.list_persisted_candidates_for_verse(self.path, "MAT 1:99"), ())
        self.assertEqual(pq.list_persisted_candidates_for_chapter(self.path, "MAT", 28), ())
        self.assertEqual(pq.get_structural_interpretation_histories_for_selector(
            self.path, pq.ScriptureSelector("MAT", 1, 2, 6)), ())
        everything = pq.list_persisted_candidates_for_selector(self.path, pq.ScriptureSelector("MAT"))
        self.assertEqual({c.candidate_id for c in everything},
                         {*(c.candidate_id for c in self.appositions), self.clause.candidate_id})

    def test_11_deterministic_presentation_order_is_scripture_then_logical_keys(self) -> None:
        found = pq.list_persisted_candidates_for_selector(self.path, pq.ScriptureSelector("MAT"))
        keys = [(coordinate(c.scope.member_token_refs[0]), c.candidate_kind, c.derivation_kind,
                 c.derivation_version, c.candidate_id) for c in found]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(found[-1], self.clause)

    def test_12_lookup_by_logical_identity(self) -> None:
        self.assertEqual(pq.get_persisted_candidate(self.path, self.clause.candidate_id), self.clause)
        self.assertEqual(pq.get_persisted_evaluation(self.path, self.r1.evaluation_id), self.r1)
        self.assertIsNone(pq.get_persisted_candidate(self.path, ABSENT_CANDIDATE))
        self.assertIsNone(pq.get_persisted_evaluation(self.path, ABSENT_EVALUATION))
        self.assertIsNone(pq.list_candidate_evaluations(self.path, ABSENT_CANDIDATE))
        self.assertIsNone(pq.list_unsuperseded_evaluations(self.path, ABSENT_CANDIDATE))
        self.assertIsNone(pq.get_structural_interpretation_history(self.path, ABSENT_CANDIDATE))
        self.assertIsNone(pq.get_evaluation_history(self.path, ABSENT_EVALUATION))
        missing = self.directory / "never-created.sqlite3"
        for value in ("", "sha256:xyz", "sha256:" + "A" * 64, ABSENT_EVALUATION, None, 5):
            with self.subTest(value=value):
                for call in (pq.get_persisted_candidate, pq.list_candidate_evaluations,
                             pq.list_unsuperseded_evaluations, pq.get_structural_interpretation_history):
                    with self.assertRaisesRegex(pq.ProjectionQueryError, "malformed candidate_id"):
                        call(missing, value)  # type: ignore[arg-type]
        for value in ("", "eval-sha256:xyz", ABSENT_CANDIDATE, None):
            for call in (pq.get_persisted_evaluation, pq.get_evaluation_history):
                with self.assertRaisesRegex(pq.ProjectionQueryError, "malformed evaluation_id"):
                    call(missing, value)  # type: ignore[arg-type]
        self.assertFalse(missing.exists())


class HistoryTests(Unit11Base):
    def test_20_all_dispositions_coexist_without_resolution(self) -> None:
        listed = pq.list_candidate_evaluations(self.path, self.clause.candidate_id)
        self.assertEqual({r.evaluation_id for r in listed},
                         {self.r0.evaluation_id, self.r1.evaluation_id,
                          self.r2.evaluation_id, self.other.evaluation_id})
        self.assertEqual({r.disposition for r in listed}, {"accepted", "rejected", "undetermined"})
        self.assertIn(self.other, listed)
        history = pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        self.assertEqual(history.candidate, self.clause)
        self.assertEqual(history.evaluations, listed)

    def test_21_superseded_records_remain_valid_and_queryable(self) -> None:
        self.assertEqual(pq.get_persisted_evaluation(self.path, self.r0.evaluation_id), self.r0)
        self.assertIn(self.r0, pq.list_candidate_evaluations(self.path, self.clause.candidate_id))
        self.assertNotIn(self.r0, pq.list_unsuperseded_evaluations(self.path, self.clause.candidate_id))

    def test_22_edges_come_from_logical_fields_and_forks_stay_unresolved(self) -> None:
        history = pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        self.assertEqual(history.supersession_edges, tuple(sorted(
            (pq.SupersessionEdge(self.r0.evaluation_id, self.r1.evaluation_id),
             pq.SupersessionEdge(self.r0.evaluation_id, self.r2.evaluation_id)),
            key=lambda e: (e.predecessor_evaluation_id, e.successor_evaluation_id))))
        self.assertEqual(history.unsuperseded_evaluation_ids, tuple(sorted(
            (self.r1.evaluation_id, self.r2.evaluation_id, self.other.evaluation_id))))
        leaves = pq.list_unsuperseded_evaluations(self.path, self.clause.candidate_id)
        self.assertEqual({r.evaluation_id for r in leaves}, set(history.unsuperseded_evaluation_ids))
        self.assertEqual({r.disposition for r in leaves}, {"accepted", "rejected"})

    def test_23_evaluation_history_is_the_same_evaluator_component(self) -> None:
        expected = {self.r0.evaluation_id, self.r1.evaluation_id, self.r2.evaluation_id}
        for start in expected:
            component = pq.get_evaluation_history(self.path, start)
            self.assertEqual({r.evaluation_id for r in component}, expected)
            self.assertEqual(component, pq.get_evaluation_history(self.path, self.r0.evaluation_id))
        self.assertEqual(pq.get_evaluation_history(self.path, self.other.evaluation_id), (self.other,))
        self.assertEqual(pq.get_evaluation_history(self.path, self.other.evaluation_id)[0].supersedes, None)

    def test_24_evaluation_presentation_order_carries_no_precedence(self) -> None:
        listed = pq.list_candidate_evaluations(self.path, self.clause.candidate_id)
        keys = [(r.evaluator_class, r.evaluator_label, r.evaluation_protocol_id,
                 r.evaluation_protocol_version, r.evaluation_id) for r in listed]
        self.assertEqual(keys, sorted(keys))

    def test_25_histories_for_selector_pair_each_discovered_candidate(self) -> None:
        histories = pq.get_structural_interpretation_histories_for_selector(
            self.path, pq.ScriptureSelector("MAT", 1, 2, 7))
        self.assertEqual(len(histories), 1)
        self.assertEqual(histories[0], pq.get_structural_interpretation_history(
            self.path, self.clause.candidate_id))
        self.assertEqual(pq.get_structural_interpretation_histories_for_selector(
            self.path, pq.ScriptureSelector("MAT", 1, 2, 6)), ())

    def test_26_dto_are_frozen_and_plain(self) -> None:
        history = pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        with self.assertRaises(FrozenInstanceError):
            history.candidate = None  # type: ignore[misc]
        self.assertEqual([f.name for f in fields(history)],
                         ["candidate", "evaluations", "supersession_edges", "unsuperseded_evaluation_ids"])
        self.assertIsInstance(history.evaluations, tuple)

    def test_27_graph_defects_fail_closed(self) -> None:
        with patch.object(evaluated.EvaluatedStructuralInterpretation, "__post_init__", lambda self: None):
            def make(identity: str, **changes: object) -> evaluated.EvaluatedStructuralInterpretation:
                return replace(self.r0, evaluation_id="eval-sha256:" + identity * 64, **changes)

            a, b = "a", "b"
            ida, idb = "eval-sha256:" + a * 64, "eval-sha256:" + b * 64
            cases = {
                "self": (make(a, supersedes=ida),),
                "dangling": (self.r0, make(a, supersedes=ABSENT_EVALUATION)),
                "cross-candidate": (self.r0, make(a, supersedes=self.r0.evaluation_id,
                                                   candidate=self.appositions[0])),
                "cross-evaluator": (self.r0, make(a, supersedes=self.r0.evaluation_id,
                                                   evaluator_label="someone-else")),
                "cycle": (make(a, supersedes=idb), make(b, supersedes=ida)),
            }
            for name, records in cases.items():
                with self.subTest(name=name):
                    with self.assertRaises(pq.ProjectionQueryError):
                        pq._check_graph(records)
                    with patch.object(store, "_contents", return_value=((self.clause,), records)):
                        for call in (lambda: pq.get_evaluation_history(self.path, self.r0.evaluation_id),
                                     lambda: pq.list_unsuperseded_evaluations(self.path, self.clause.candidate_id),
                                     lambda: pq.get_structural_interpretation_history(
                                         self.path, self.clause.candidate_id),
                                     lambda: pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2")):
                            with self.assertRaises(pq.ProjectionQueryError):
                                call()


class VariantScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit11-variants-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        source = self.directory / "source.sqlite3"
        self.path = self.directory / "projection.sqlite3"
        build_amendment1_store(source)
        store.initialize_projection_store(self.path)
        self.base = derive(source, REFS[0])[0]
        store.store_candidate(self.path, self.base, source_db_path=source)
        self.v20 = variant(self.base, ("MAT 1:20!5",), ("MAT 1:20!7",), ("MAT 1:20!8", "MAT 1:20!9"))
        self.v50 = variant(self.base, ("MAT 1:2!50",), ("MAT 1:2!51",), ("MAT 1:2!52",))
        self.v11 = variant(self.base, ("MAT 11:2!5",), ("MAT 11:2!7",), ("MAT 11:2!8",))
        self.cross = variant(self.base, ("MAT 1:2!8",), ("MAT 1:2!9",), ("MAT 1:3!1",))
        for candidate in (self.v20, self.v50, self.v11, self.cross):
            raw_candidate(self.path, candidate)

    def tokens(self, ref: str) -> set[str]:
        return {c.candidate_id for c in pq.list_persisted_candidates_for_token(self.path, ref)}

    def verse(self, ref: str) -> set[str]:
        return {c.candidate_id for c in pq.list_persisted_candidates_for_verse(self.path, ref)}

    def test_30_integer_coordinates_not_string_prefixes(self) -> None:
        self.assertEqual(self.verse("MAT 1:2"), {self.base.candidate_id, self.v50.candidate_id,
                                                self.cross.candidate_id})
        self.assertEqual(self.verse("MAT 1:20"), {self.v20.candidate_id})
        self.assertEqual(self.tokens("MAT 1:2!5"), {self.base.candidate_id})
        self.assertEqual(self.tokens("MAT 1:2!50"), {self.v50.candidate_id})
        self.assertEqual(self.tokens("MAT 1:20!5"), {self.v20.candidate_id})
        self.assertEqual(self.tokens("MAT 11:2!5"), {self.v11.candidate_id})
        chapter_1 = {c.candidate_id for c in pq.list_persisted_candidates_for_chapter(self.path, "MAT", 1)}
        self.assertEqual(chapter_1, {self.base.candidate_id, self.v20.candidate_id, self.v50.candidate_id,
                                     self.cross.candidate_id})
        self.assertEqual({c.candidate_id for c in pq.list_persisted_candidates_for_chapter(self.path, "MAT", 11)},
                         {self.v11.candidate_id})
        self.assertEqual({c.candidate_id for c in pq.list_persisted_candidates_for_chapter(self.path, "MAT", 2)},
                         set())

    def test_31_no_envelope_or_range_expansion_across_verses(self) -> None:
        self.assertEqual(self.verse("MAT 1:3"), {self.cross.candidate_id})
        self.assertEqual(self.tokens("MAT 1:3!1"), {self.cross.candidate_id})
        self.assertEqual(self.tokens("MAT 1:2!7"), {self.base.candidate_id})
        self.assertEqual(self.tokens("MAT 1:2!10"), set())
        self.assertEqual(self.tokens("MAT 1:3!2"), set())
        found = [c for c in pq.list_persisted_candidates_for_verse(self.path, "MAT 1:3")][0]
        self.assertEqual(found.scope.member_token_refs, ("MAT 1:2!8", "MAT 1:2!9", "MAT 1:3!1"))

    def test_32_bad_validated_candidate_is_never_silently_skipped(self) -> None:
        for selector_call in (lambda: pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!5"),
                              lambda: pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!6")):
            self.assertIsNotNone(selector_call())
        alter_record(self.path, "candidate", self.v11.candidate_id, "{not json")
        for call in (lambda: pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!5"),
                     lambda: pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!6"),
                     lambda: pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2"),
                     lambda: pq.get_persisted_candidate(self.path, self.base.candidate_id),
                     lambda: pq.get_persisted_evaluation(self.path, ABSENT_EVALUATION)):
            with self.assertRaises(pq.ProjectionQueryError):
                call()


class IntegrityAndReadOnlyTests(Unit11Base):
    def snapshot(self) -> bytes:
        return self.path.read_bytes()

    def test_40_projection_store_is_unchanged_by_every_query(self) -> None:
        before = self.snapshot()
        selector = pq.ScriptureSelector("MAT", 1, 2, 5)
        pq.list_persisted_candidates_for_selector(self.path, selector)
        pq.list_persisted_candidates_for_chapter(self.path, "MAT", 1)
        pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2")
        pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!5")
        pq.get_persisted_candidate(self.path, self.clause.candidate_id)
        pq.get_persisted_evaluation(self.path, self.r0.evaluation_id)
        pq.list_candidate_evaluations(self.path, self.clause.candidate_id)
        pq.get_evaluation_history(self.path, self.r0.evaluation_id)
        pq.list_unsuperseded_evaluations(self.path, self.clause.candidate_id)
        pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        pq.get_structural_interpretation_histories_for_selector(self.path, selector)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(sorted(p.name for p in self.directory.iterdir()),
                         ["projection.sqlite3", "source.sqlite3"])
        store.verify_projection_store(self.path, self.source)

    def test_41_connection_is_read_only_and_authorizer_sees_no_write(self) -> None:
        tracked: list[TrackedConnection] = []

        def spy(database: object, *args: object, **kwargs: object) -> sqlite3.Connection:
            if isinstance(database, str) and "mode=ro" in database:
                kwargs["factory"] = TrackedConnection
            connection = _REAL_CONNECT(database, *args, **kwargs)
            if isinstance(connection, TrackedConnection):
                tracked.append(connection)
            return connection

        before = self.snapshot()
        with patch.object(sqlite3, "connect", spy):
            pq.list_persisted_candidates_for_token(self.path, "MAT 1:2!5")
            pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        self.assertTrue(tracked)
        self.assertTrue(all(c.closed and not c.forbidden for c in tracked))

        def attempt_write(db: sqlite3.Connection) -> None:
            db.execute("PRAGMA query_only=OFF")
            db.execute("INSERT INTO candidate VALUES ('sha256:" + "1" * 64 + "','{}')")

        with patch.object(store, "_contents", attempt_write):
            with self.assertRaises(pq.ProjectionQueryError):
                pq.list_persisted_candidates_for_verse(self.path, "MAT 1:2")
        self.assertEqual(self.snapshot(), before)

    def test_42_connections_close_on_success_not_found_empty_and_failure(self) -> None:
        tracked: list[TrackedConnection] = []

        def spy(database: object, *args: object, **kwargs: object) -> sqlite3.Connection:
            if isinstance(database, str) and "mode=ro" in database:
                kwargs["factory"] = TrackedConnection
            connection = _REAL_CONNECT(database, *args, **kwargs)
            if isinstance(connection, TrackedConnection):
                tracked.append(connection)
            return connection

        corrupt = self.directory / "corrupt.sqlite3"
        corrupt.write_bytes(self.snapshot())
        alter_record(corrupt, "candidate", self.clause.candidate_id, "{}")
        with patch.object(sqlite3, "connect", spy):
            pq.get_persisted_candidate(self.path, self.clause.candidate_id)
            pq.get_persisted_candidate(self.path, ABSENT_CANDIDATE)
            pq.list_persisted_candidates_for_verse(self.path, "MAT 1:99")
            for call in (lambda: pq.get_persisted_candidate(corrupt, self.clause.candidate_id),
                         lambda: pq.list_persisted_candidates_for_verse(self.source, "MAT 1:2"),
                         lambda: pq.list_persisted_candidates_for_verse(
                             self.directory / "absent.sqlite3", "MAT 1:2")):
                with self.assertRaises(pq.ProjectionQueryError):
                    call()
        self.assertGreaterEqual(len(tracked), 4)
        self.assertTrue(all(c.closed for c in tracked))
        self.assertFalse((self.directory / "absent.sqlite3").exists())

    def test_43_store_identity_failures_are_errors_not_empty(self) -> None:
        wrong_version = self.directory / "version.sqlite3"
        wrong_version.write_bytes(self.snapshot())
        with closing(sqlite3.connect(wrong_version)) as db:
            db.execute("PRAGMA user_version=2")
            db.commit()
        empty = self.directory / "empty.sqlite3"
        empty.write_bytes(b"")
        blank = self.directory / "blank.sqlite3"
        with closing(sqlite3.connect(blank)) as db:
            db.execute("CREATE TABLE t(x)")
            db.commit()
        drift = self.directory / "drift.sqlite3"
        drift.write_bytes(self.snapshot())
        with closing(sqlite3.connect(drift)) as db:
            db.execute("CREATE TABLE extra(x)")
            db.commit()
        for target in (wrong_version, empty, blank, drift, self.source, self.directory):
            with self.subTest(target=target.name):
                for call in (lambda: pq.list_persisted_candidates_for_verse(target, "MAT 1:2"),
                             lambda: pq.get_persisted_candidate(target, ABSENT_CANDIDATE),
                             lambda: pq.get_evaluation_history(target, ABSENT_EVALUATION)):
                    with self.assertRaises(pq.ProjectionQueryError):
                        call()
        with patch.object(store, "_ddl", return_value=store.DDL_PATH.read_text(encoding="utf-8") + "\n"):
            with self.assertRaisesRegex(pq.ProjectionQueryError, "hash drift"):
                pq.get_persisted_candidate(self.path, ABSENT_CANDIDATE)

    def test_44_record_corruption_and_identity_mismatch_fail_closed(self) -> None:
        def corrupted(table: str, identity: str, text: str) -> Path:
            target = self.directory / f"c-{table}-{abs(hash((identity, text)))}.sqlite3"
            target.write_bytes(self.snapshot())
            alter_record(target, table, identity, text)
            return target

        with closing(sqlite3.connect(self.path)) as db:
            candidate_json = db.execute("SELECT record_json FROM candidate WHERE candidate_id=?",
                                        (self.clause.candidate_id,)).fetchone()[0]
            evaluation_json = db.execute("SELECT record_json FROM evaluation WHERE evaluation_id=?",
                                         (self.r0.evaluation_id,)).fetchone()[0]
        targets = [
            corrupted("candidate", self.appositions[0].candidate_id, "not json"),
            corrupted("candidate", self.appositions[0].candidate_id, candidate_json),
            corrupted("candidate", self.clause.candidate_id,
                      candidate_json.replace("macula.structural-candidate.v1", "macula.structural-candidate.v9")),
            corrupted("candidate", self.clause.candidate_id,
                      candidate_json.replace('"MAT 1:2!9"', '"MAT 1:2!6"', 1)),
            corrupted("evaluation", self.r1.evaluation_id, "{}"),
            corrupted("evaluation", self.r0.evaluation_id, evaluation_json.replace('"undetermined"', '"accepted"')),
            corrupted("evaluation", self.other.evaluation_id, evaluation_json),
        ]
        for target in targets:
            with self.subTest(target=target.name):
                for call in (lambda: pq.get_persisted_evaluation(target, self.r0.evaluation_id),
                             lambda: pq.list_persisted_candidates_for_token(target, "MAT 1:2!6"),
                             lambda: pq.get_structural_interpretation_history(target, ABSENT_CANDIDATE)):
                    with self.assertRaises(pq.ProjectionQueryError):
                        call()

    def test_45_no_source_database_dependency(self) -> None:
        self.source.unlink()
        with patch.object(structural, "derive_structural_candidates", side_effect=AssertionError("source")):
            self.assertEqual(self.clause_selector_hits("MAT 1:2!5"), (self.clause.candidate_id,))
            self.assertEqual(self.clause_selector_hits("MAT 1:2!6"), ())
            self.assertEqual(len(pq.list_candidate_evaluations(self.path, self.clause.candidate_id)), 4)

    def test_46_logical_results_ignore_pk_insertion_order_and_path(self) -> None:
        other = self.directory / "nested-copy" / "different-name.db"
        other.parent.mkdir()
        store.initialize_projection_store(other)
        with closing(sqlite3.connect(self.path)) as src, closing(sqlite3.connect(other)) as dst:
            dst.execute("PRAGMA foreign_keys=OFF")
            for offset, table in ((9000, "evaluation"), (7000, "candidate")):
                for index, row in enumerate(src.execute(f"SELECT * FROM {table} ORDER BY rowid DESC")):
                    marks = ",".join("?" for _ in row)
                    dst.execute(f"INSERT INTO {table}(rowid,{','.join(c[1] for c in dst.execute(f'PRAGMA table_info({table})'))}) "
                                f"VALUES (?,{marks})", (offset + index * 3, *row))
            dst.commit()
        with closing(sqlite3.connect(self.path)) as a, closing(sqlite3.connect(other)) as b:
            order = lambda db: [r[0] for r in db.execute("SELECT candidate_id FROM candidate ORDER BY rowid")]
            self.assertNotEqual(order(a), order(b))
        selectors = [pq.ScriptureSelector("MAT"), pq.ScriptureSelector("MAT", 1, 2, 7),
                     pq.ScriptureSelector("MAT", 1, 1)]
        for selector in selectors:
            self.assertEqual(pq.list_persisted_candidates_for_selector(self.path, selector),
                             pq.list_persisted_candidates_for_selector(other, selector))
            self.assertEqual(pq.get_structural_interpretation_histories_for_selector(self.path, selector),
                             pq.get_structural_interpretation_histories_for_selector(other, selector))
        for identity in (self.r0.evaluation_id, self.other.evaluation_id):
            self.assertEqual(pq.get_evaluation_history(self.path, identity),
                             pq.get_evaluation_history(other, identity))
        self.assertEqual(pq.list_unsuperseded_evaluations(self.path, self.clause.candidate_id),
                         pq.list_unsuperseded_evaluations(other, self.clause.candidate_id))

    def test_47_unit10_schema_and_read_api_unchanged(self) -> None:
        digest = hashlib.sha256(store.DDL_PATH.read_text(encoding="utf-8").encode()).hexdigest()
        self.assertEqual(digest, DDL_SHA256)
        self.assertEqual(store.list_evaluations_for_candidate(self.path, self.clause.candidate_id),
                         frozenset((self.r0, self.r1, self.r2, self.other)))
        self.assertEqual(set(pq.list_candidate_evaluations(self.path, self.clause.candidate_id)),
                         set(store.list_evaluations_for_candidate(self.path, self.clause.candidate_id)))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
        self.assertFalse(any(name in {"store_candidate", "store_evaluation"} for name in PUBLIC_FUNCTIONS))

    def test_48_no_semantic_projection_in_results(self) -> None:
        history = pq.get_structural_interpretation_history(self.path, self.clause.candidate_id)
        blob = json.dumps(
            [f.name for f in fields(history)] + [f.name for f in fields(pq.SupersessionEdge)]).lower()
        for word in ("actor", "action", "patient", "result", "event", "identity", "property", "frame"):
            self.assertNotIn(word, blob)
        self.assertEqual([c.component_role for c in history.candidate.payload.components],
                         [c.component_role for c in self.clause.payload.components])


_MATTHEW = Path(os.environ.get("MACULA_MATTHEW_DB", str(ROOT / "sblgnt-matthew.sqlite3")))


@unittest.skipUnless(os.environ.get("MACULA_UNIT11_INTEGRATION") == "1" and _MATTHEW.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit11MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before = state(_MATTHEW)

    @classmethod
    def tearDownClass(cls) -> None:
        if state(_MATTHEW) != cls.before:
            raise AssertionError("Unit 11 changed authoritative Matthew database")

    def test_50_real_matthew_discovery_history_and_token_6_negative_case(self) -> None:
        with TemporaryDirectory(prefix="macula-unit11-matthew-") as directory:
            path = Path(directory) / "projection.sqlite3"
            store.initialize_projection_store(path)
            clause = derive(_MATTHEW, REFS[0])[0]
            self.assertEqual(clause.candidate_id, SVO_ID)
            store.store_candidate(path, clause, source_db_path=_MATTHEW)
            appositions = derive(_MATTHEW, "MAT 1:1!3")
            for candidate in appositions:
                store.store_candidate(path, candidate, source_db_path=_MATTHEW)
            first = record_for(_MATTHEW, clause)
            second = record_for(_MATTHEW, clause, event="unit10:2", disposition="accepted",
                                predecessor=first, prior=(first,))
            for record in (first, second):
                store.store_evaluation(path, record, source_db_path=_MATTHEW)
            self.assertEqual(ids(pq.list_persisted_candidates_for_verse(path, "MAT 1:2")), (SVO_ID,))
            for ref in REFS:
                found = pq.list_persisted_candidates_for_token(path, ref)
                self.assertEqual(ids(found), (SVO_ID,))
                self.assertEqual(found[0].scope.member_token_refs, REFS)
            self.assertEqual(pq.list_persisted_candidates_for_token(path, "MAT 1:2!6"), ())
            self.assertEqual(derive(_MATTHEW, "MAT 1:2!6"), ())
            history = pq.get_structural_interpretation_history(path, SVO_ID)
            self.assertEqual(history.supersession_edges,
                             (pq.SupersessionEdge(first.evaluation_id, second.evaluation_id),))
            self.assertEqual(history.unsuperseded_evaluation_ids, (second.evaluation_id,))
            verse_one = pq.list_persisted_candidates_for_verse(path, "MAT 1:1")
            self.assertEqual({c.candidate_id for c in verse_one}, {c.candidate_id for c in appositions})
            self.assertEqual({c.candidate_kind for c in verse_one}, {"apposition"})
            self.assertTrue(any(node.cl_type == "Verbless"
                                for node in query.get_ancestors_by_token(_MATTHEW, "MAT 1:1!3")))
            self.assertEqual(len(pq.list_persisted_candidates_for_selector(
                path, pq.ScriptureSelector("MAT"))), len(appositions) + 1)
            store.verify_projection_store(path, _MATTHEW)


if __name__ == "__main__":
    unittest.main()
