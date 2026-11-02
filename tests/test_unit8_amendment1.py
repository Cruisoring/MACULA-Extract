"""Unit 8 Amendment 1 tests: S-V-O evaluation-registry extension.

This module is written against the public Unit 8 API and the public Unit 7/9
derivation entry point. It must not import Unit 8 or Unit 9 private helpers.

Fast tests use the disposable store built by
``tests.support.unit8_amendment1_store.build_amendment1_store``. That store carries the
synthetic Unit 2 snapshot, because ``source_file.sha256`` must equal the SHA-256 of the
stored bytes, so its candidate IDs differ from the frozen real-snapshot IDs only through
``source_snapshot``. The fast tests therefore pin the frozen IDs by independently
re-encoding the derived candidate under the frozen snapshot; the real-Matthew integration
tests assert the frozen IDs directly.

Real-Matthew tests are opt-in:

    set MACULA_UNIT8_AMENDMENT1_INTEGRATION=1
    set MACULA_MATTHEW_DB=C:\\Projects\\MACULA-Extract\\sblgnt-matthew.sqlite3
    python -B -m unittest tests.test_unit8_amendment1 -v
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any, Iterable
from unittest import mock

from scripts import evaluated_interpretations as evaluation
from scripts import structural_candidates as candidates
from scripts.source_query import QueryError


ROOT = Path(__file__).resolve().parents[1]
UNIT9_FIXTURE = ROOT / "fixtures" / "matthew-1-2-svo-candidate.expected.json"
DEFAULT_MATTHEW_DB = ROOT / "sblgnt-matthew.sqlite3"

PROTOCOL_ID = "human-structural-adequacy"
PROTOCOL_VERSION = "1"
RECORD_PROTOCOL = "macula.evaluated-structural-interpretation.v1"

CLAUSE_KIND = "clause-structure"
CLAUSE_DERIVATION = "source-rule-s-v-o"
CLAUSE_DERIVATION_VERSION = "1"

APPOSITION_KIND = "apposition"
APPOSITION_DERIVATION = "source-np-appos"
APPOSITION_DERIVATION_VERSION = "1"
APPOSITION_CANDIDATE_ID = (
    "sha256:ca5dc5188ebf612545856de8bbf2a407"
    "783bb6afffbb892bec8d6326d4c05c3c"
)

SVO_CANDIDATE_ID = (
    "sha256:129c397055985ed0156e320bc543d551"
    "be0cf8d3ecfa192e60914540646ff087"
)
SVO_ANCHOR = "400010020050040"
SVO_CHILDREN = (
    "400010020050012",
    "400010020070012",
    "400010020080021",
)
SVO_SCOPE = (
    "MAT 1:2!5",
    "MAT 1:2!7",
    "MAT 1:2!8",
    "MAT 1:2!9",
)
EXCLUDED_TOKEN = "MAT 1:2!6"

SEMANTIC_FIELDS = {
    "actor",
    "action",
    "patient",
    "event",
    "result",
    "identity",
    "property",
    "semantic_role",
    "semantic_roles",
}
CONFIDENCE_FIELDS = {
    "confidence",
    "probability",
    "certainty",
    "score",
    "percentage",
    "weight",
    "rank",
}
LOCAL_PK_FIELDS = {
    "token_id",
    "node_id",
    "tree_id",
    "element_id",
    "book_id",
    "snapshot_id",
    "file_id",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _catalog(connection: sqlite3.Connection) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        connection.execute(
            "SELECT type,name,tbl_name,rootpage,sql "
            "FROM sqlite_schema ORDER BY type,name,tbl_name"
        )
    )


def _database_state(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        connection.execute("PRAGMA query_only=ON")
        return {
            "size": path.stat().st_size,
            "sha256": _sha256(path),
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "catalog": _catalog(connection),
        }
    finally:
        connection.close()


def _field_names(value_or_type: object) -> set[str]:
    return {field.name for field in dataclasses.fields(value_or_type)}


def _walk_keys(value: object) -> Iterable[str]:
    if dataclasses.is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (tuple, list)):
        for child in value:
            yield from _walk_keys(child)


def _load_unit9_fixture() -> dict[str, Any]:
    return json.loads(UNIT9_FIXTURE.read_text(encoding="utf-8"))


def _find_candidate(
    values: tuple[object, ...] | None,
    *,
    candidate_kind: str,
    candidate_id: str | None = None,
) -> object:
    for value in values or ():
        if getattr(value, "candidate_kind") != candidate_kind:
            continue
        if candidate_id is not None and getattr(value, "candidate_id") != candidate_id:
            continue
        return value
    raise AssertionError(
        f"candidate not found: kind={candidate_kind!r}, id={candidate_id!r}"
    )


def _citation(kind: str, identifier: str) -> object:
    return evaluation.RationaleCitation(kind=kind, citation_id=identifier)


def _note(text: str = "The candidate adequately describes the cited structure.") -> object:
    return evaluation.RationaleNote(text=text, language="en")


@dataclasses.dataclass(frozen=True)
class _HumanInput:
    """Test-local bundle of the public keyword arguments of the Unit 8 creation API."""

    candidate: object
    evaluator_label: str
    evaluation_protocol_id: str
    evaluation_protocol_version: str
    disposition: str
    rationale_evidence: tuple[object, ...]
    rationale_note: object
    event_key: str
    supersedes: str | None

    def kwargs(self) -> dict[str, Any]:
        return {
            "evaluator_class": "human",
            "evaluator_label": self.evaluator_label,
            "evaluation_protocol_id": self.evaluation_protocol_id,
            "evaluation_protocol_version": self.evaluation_protocol_version,
            "disposition": self.disposition,
            "rationale_evidence": self.rationale_evidence,
            "rationale_note": self.rationale_note,
            "event_key": self.event_key,
            "supersedes": self.supersedes,
        }


def _tampered(value: object, **fields: object) -> object:
    """Copy a frozen candidate and overwrite fields without running validation."""
    clone = copy.copy(value)
    for name, field_value in fields.items():
        object.__setattr__(clone, name, field_value)
    return clone


def _human_input(
    candidate_value: object,
    *,
    disposition: str = "accepted",
    citations: tuple[object, ...] | None = None,
    note: object | None = None,
    event_key: str = "unit8-amendment1-event-001",
    evaluator_label: str = "unit8-amendment1-reviewer",
    supersedes: str | None = None,
) -> object:
    if citations is None:
        citations = (
            _citation(
                "syntax_node",
                candidate_value.evidence[0].source_node_id,
            ),
        )
    if note is None:
        note = _note()
    return _HumanInput(
        candidate=candidate_value,
        evaluator_label=evaluator_label,
        evaluation_protocol_id=PROTOCOL_ID,
        evaluation_protocol_version=PROTOCOL_VERSION,
        disposition=disposition,
        rationale_evidence=citations,
        rationale_note=note,
        event_key=event_key,
        supersedes=supersedes,
    )


def _create(db_path: Path, input_value: _HumanInput, **extra: Any) -> object:
    return evaluation.create_evaluated_interpretation(
        db_path, input_value.candidate, **input_value.kwargs(), **extra
    )


def _v1(candidate_value: object) -> object:
    """Run the offline V1 candidate validation through the public identity function."""
    evaluation.compute_evaluation_id(
        candidate_value,
        evaluator_class="human",
        evaluator_label="unit8-amendment1-reviewer",
        evaluation_protocol_id=PROTOCOL_ID,
        evaluation_protocol_version=PROTOCOL_VERSION,
        disposition="undetermined",
        rationale_evidence=(),
        rationale_note=_note("Offline V1 validation only."),
        event_key="unit8-amendment1-v1",
    )
    return candidate_value


def _v2(db_path: Path, candidate_value: object, token_ref: str) -> object:
    """Re-derive ``token_ref`` publicly, then verify the candidate against the store.

    Production V2 always derives from the candidate's first scope token; the explicit
    lookup here additionally requires that ``token_ref`` itself exposes the candidate.
    """
    derived = candidates.derive_structural_candidates(db_path, token_ref)
    if not derived or candidate_value not in derived:
        raise QueryError(f"candidate not exposed by {token_ref}")
    input_value = _human_input(candidate_value, event_key="unit8-amendment1-v2")
    record = evaluation.EvaluatedStructuralInterpretation(
        evaluation.RECORD_PROTOCOL,
        evaluation.compute_evaluation_id(candidate_value, **input_value.kwargs()),
        candidate_value,
        "human",
        input_value.evaluator_label,
        PROTOCOL_ID,
        PROTOCOL_VERSION,
        input_value.disposition,
        input_value.rationale_evidence,
        input_value.rationale_note,
        input_value.event_key,
        None,
    )
    evaluation.verify_evaluated_interpretation(record, db_path=db_path)
    return record.candidate


class Unit8Amendment1FastTests(unittest.TestCase):
    """Amendment-delta tests using a disposable Unit 9-compatible source store."""

    @classmethod
    def setUpClass(cls) -> None:
        # The implementation task should expose a stable test-support builder here.
        # It is test code, not production API, and must create both an Apposition
        # fixture and the frozen Matthew 1:2 S-V-O fixture.
        from tests.support.unit8_amendment1_store import (
            APPOSITION_FROZEN_IDS,
            build_amendment1_store,
            frozen_candidate_id,
        )

        cls.frozen_candidate_id = staticmethod(frozen_candidate_id)
        cls._temporary_directory = tempfile.TemporaryDirectory(
            prefix="macula-unit8-amendment1-"
        )
        cls.db_path = Path(cls._temporary_directory.name) / "source.sqlite3"
        build_amendment1_store(cls.db_path)

        clause_values = candidates.derive_structural_candidates(
            cls.db_path, "MAT 1:2!5"
        )
        cls.clause_candidate = _find_candidate(
            clause_values, candidate_kind=CLAUSE_KIND
        )
        assert frozen_candidate_id(cls.clause_candidate) == SVO_CANDIDATE_ID

        apposition_values = candidates.derive_structural_candidates(
            cls.db_path, "MAT 1:1!3"
        )
        assert APPOSITION_CANDIDATE_ID in APPOSITION_FROZEN_IDS
        cls.apposition_candidate = next(
            value
            for value in apposition_values
            if value.candidate_kind == APPOSITION_KIND
            and frozen_candidate_id(value) == APPOSITION_CANDIDATE_ID
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    # Registry -------------------------------------------------------------

    def test_a1_01_apposition_registry_entry_remains_supported(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.apposition_candidate,
                event_key="a1-01-apposition",
            ),
        )
        self.assertEqual(APPOSITION_KIND, record.candidate.candidate_kind)

    def test_a1_02_clause_structure_registry_entry_is_supported(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                event_key="a1-02-clause",
            ),
        )
        self.assertEqual(CLAUSE_KIND, record.candidate.candidate_kind)
        self.assertEqual(PROTOCOL_ID, record.evaluation_protocol_id)
        self.assertEqual(PROTOCOL_VERSION, record.evaluation_protocol_version)

    def test_a1_03_clause_structure_wrong_derivation_is_rejected(self) -> None:
        forged = _tampered(
            self.clause_candidate, derivation_kind=APPOSITION_DERIVATION
        )
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_04_clause_structure_derivation_version_two_is_rejected(self) -> None:
        forged = _tampered(self.clause_candidate, derivation_version="2")
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_05_unknown_candidate_kind_remains_rejected(self) -> None:
        forged = _tampered(self.clause_candidate, candidate_kind="semantic-event")
        with self.assertRaises(QueryError):
            _v1(forged)

    # V1 -------------------------------------------------------------------

    def test_a1_06_frozen_clause_candidate_passes_v1(self) -> None:
        self.assertEqual(self.clause_candidate, _v1(self.clause_candidate))
        fixture = _load_unit9_fixture()
        # The disposable store has a synthetic snapshot, so the frozen identity is
        # pinned by re-encoding the derived candidate under the frozen snapshot.
        self.assertEqual(
            fixture["candidate_id"],
            self.frozen_candidate_id(self.clause_candidate),
        )

    def test_a1_07_scope_mutation_is_rejected_by_v1(self) -> None:
        forged_scope = replace(
            self.clause_candidate.scope,
            member_token_refs=(
                "MAT 1:2!5",
                EXCLUDED_TOKEN,
                "MAT 1:2!7",
                "MAT 1:2!8",
                "MAT 1:2!9",
            ),
        )
        forged = replace(self.clause_candidate, scope=forged_scope)
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_08_evidence_order_mutation_is_rejected_by_v1(self) -> None:
        anchor, subject, verbal, obj = self.clause_candidate.evidence
        forged = replace(
            self.clause_candidate,
            evidence=(anchor, verbal, subject, obj),
        )
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_09_component_membership_mutation_is_rejected_by_v1(self) -> None:
        subject, verbal, obj = self.clause_candidate.payload.components
        forged_object = replace(obj, member_token_refs=("MAT 1:2!8",))
        forged_payload = replace(
            self.clause_candidate.payload,
            components=(subject, verbal, forged_object),
        )
        forged = replace(self.clause_candidate, payload=forged_payload)
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_10_component_order_mutation_is_rejected_by_v1(self) -> None:
        subject, verbal, obj = self.clause_candidate.payload.components
        forged_payload = replace(
            self.clause_candidate.payload,
            components=(verbal, subject, obj),
        )
        forged = replace(self.clause_candidate, payload=forged_payload)
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_11_head_mutation_is_rejected_by_v1(self) -> None:
        forged_payload = replace(
            self.clause_candidate.payload,
            source_head_raw="0",
        )
        forged = replace(self.clause_candidate, payload=forged_payload)
        with self.assertRaises(QueryError):
            _v1(forged)

    def test_a1_12_forged_candidate_id_is_rejected_by_v1(self) -> None:
        forged = replace(
            self.clause_candidate,
            candidate_id="sha256:" + "0" * 64,
        )
        with self.assertRaises(QueryError):
            _v1(forged)

    # Evaluation -----------------------------------------------------------

    def test_a1_13_human_can_accept_clause_candidate(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                disposition="accepted",
                event_key="a1-13-accepted",
            ),
        )
        self.assertEqual("accepted", record.disposition)
        self.assertEqual(self.clause_candidate, record.candidate)
        self.assertEqual("candidate", record.candidate.status)
        self.assertTrue(record.evaluation_id.startswith("eval-sha256:"))

    def test_a1_14_human_can_reject_clause_candidate(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                disposition="rejected",
                note=_note(
                    "The candidate does not satisfy the protocol criterion."
                ),
                event_key="a1-14-rejected",
            ),
        )
        self.assertEqual("rejected", record.disposition)

    def test_a1_15_human_can_record_undetermined_without_citations(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                disposition="undetermined",
                citations=(),
                note=_note("The criterion could not be conclusively applied."),
                event_key="a1-15-undetermined",
            ),
        )
        self.assertEqual("undetermined", record.disposition)
        self.assertEqual((), record.rationale_evidence)

    def test_a1_16_identical_human_input_is_idempotent(self) -> None:
        input_value = _human_input(
            self.clause_candidate,
            event_key="a1-16-same-event",
        )
        first = _create(self.db_path, input_value)
        second = _create(self.db_path, input_value)
        self.assertEqual(first, second)
        self.assertEqual(first.evaluation_id, second.evaluation_id)

    def test_a1_17_different_event_keys_create_distinct_records(self) -> None:
        first = _create(
            self.db_path,
            _human_input(self.clause_candidate, event_key="a1-17-a"),
        )
        second = _create(
            self.db_path,
            _human_input(self.clause_candidate, event_key="a1-17-b"),
        )
        self.assertNotEqual(first.evaluation_id, second.evaluation_id)
        self.assertEqual(first.candidate.candidate_id, second.candidate.candidate_id)

    def test_a1_18_evaluation_does_not_change_candidate_identity(self) -> None:
        before = self.clause_candidate
        record = _create(
            self.db_path,
            _human_input(before, event_key="a1-18-candidate-unchanged"),
        )
        self.assertEqual(before, record.candidate)
        self.assertEqual(before.candidate_id, record.candidate.candidate_id)

    def test_a1_19_existing_record_protocol_is_retained(self) -> None:
        record = _create(
            self.db_path,
            _human_input(self.clause_candidate, event_key="a1-19-protocol"),
        )
        self.assertEqual(RECORD_PROTOCOL, record.record_protocol)
        self.assertTrue(record.evaluation_id.startswith("eval-sha256:"))

    # Rationale ------------------------------------------------------------

    def test_a1_20_anchor_syntax_node_citation_is_valid(self) -> None:
        citation = _citation("syntax_node", SVO_ANCHOR)
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                citations=(citation,),
                event_key="a1-20-anchor",
            ),
        )
        self.assertEqual((citation,), record.rationale_evidence)

    def test_a1_21_component_child_citations_are_valid(self) -> None:
        for ordinal, source_node_id in enumerate(SVO_CHILDREN):
            with self.subTest(source_node_id=source_node_id):
                citation = _citation("syntax_node", source_node_id)
                record = _create(
                    self.db_path,
                    _human_input(
                        self.clause_candidate,
                        citations=(citation,),
                        event_key=f"a1-21-child-{ordinal}",
                    ),
                )
                self.assertEqual((citation,), record.rationale_evidence)

    def test_a1_22_exact_scope_token_citations_are_valid(self) -> None:
        for ordinal, token_ref in enumerate(SVO_SCOPE):
            with self.subTest(token_ref=token_ref):
                citation = _citation("token", token_ref)
                record = _create(
                    self.db_path,
                    _human_input(
                        self.clause_candidate,
                        citations=(citation,),
                        event_key=f"a1-22-token-{ordinal}",
                    ),
                )
                self.assertEqual((citation,), record.rationale_evidence)

    def test_a1_23_token_six_citation_is_rejected(self) -> None:
        with self.assertRaises(QueryError):
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    citations=(_citation("token", EXCLUDED_TOKEN),),
                    event_key="a1-23-token-six",
                ),
            )

    def test_a1_24_unrelated_syntax_node_citation_is_rejected(self) -> None:
        unrelated = "400010010010083"
        self.assertNotIn(
            unrelated,
            tuple(item.source_node_id for item in self.clause_candidate.evidence),
        )
        with self.assertRaises(QueryError):
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    citations=(_citation("syntax_node", unrelated),),
                    event_key="a1-24-unrelated-node",
                ),
            )

    def test_a1_25_duplicate_citations_are_rejected(self) -> None:
        citation = _citation("syntax_node", SVO_ANCHOR)
        with self.assertRaises(QueryError):
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    citations=(citation, citation),
                    event_key="a1-25-duplicate",
                ),
            )

    def test_a1_26_citations_use_candidate_order(self) -> None:
        # Frozen Unit 8 behavior: canonical order is required of the caller, not
        # normalized by the API; incorrectly ordered citations are rejected.
        unordered = (
            _citation("token", "MAT 1:2!9"),
            _citation("syntax_node", SVO_CHILDREN[2]),
            _citation("token", "MAT 1:2!5"),
            _citation("syntax_node", SVO_ANCHOR),
            _citation("syntax_node", SVO_CHILDREN[1]),
            _citation("syntax_node", SVO_CHILDREN[0]),
        )
        expected = (
            _citation("syntax_node", SVO_ANCHOR),
            _citation("syntax_node", SVO_CHILDREN[0]),
            _citation("syntax_node", SVO_CHILDREN[1]),
            _citation("syntax_node", SVO_CHILDREN[2]),
            _citation("token", "MAT 1:2!5"),
            _citation("token", "MAT 1:2!9"),
        )
        with self.assertRaisesRegex(QueryError, "ordered"):
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    citations=unordered,
                    event_key="a1-26-order",
                ),
            )
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                citations=expected,
                event_key="a1-26-order",
            ),
        )
        self.assertEqual(expected, record.rationale_evidence)

    # V2 -------------------------------------------------------------------

    def test_a1_27_each_scope_member_rederives_the_same_candidate(self) -> None:
        for token_ref in SVO_SCOPE:
            with self.subTest(token_ref=token_ref):
                self.assertEqual(
                    self.clause_candidate,
                    _v2(self.db_path, self.clause_candidate, token_ref),
                )

    def test_a1_28_v2_uses_public_candidate_derivation_api(self) -> None:
        with mock.patch.object(
            candidates,
            "derive_structural_candidates",
            wraps=candidates.derive_structural_candidates,
        ) as derive:
            _v2(self.db_path, self.clause_candidate, SVO_SCOPE[0])
        derive.assert_called()

    def test_a1_29_token_six_is_not_a_valid_lookup_hint(self) -> None:
        with self.assertRaises(QueryError):
            _v2(self.db_path, self.clause_candidate, EXCLUDED_TOKEN)

    def test_a1_30_v2_requires_field_for_field_candidate_equality(self) -> None:
        subject, verbal, obj = self.clause_candidate.payload.components
        forged_payload = replace(
            self.clause_candidate.payload,
            components=(
                subject,
                verbal,
                replace(obj, member_token_refs=("MAT 1:2!8",)),
            ),
        )
        forged = replace(self.clause_candidate, payload=forged_payload)
        with mock.patch.object(
            candidates,
            "derive_structural_candidates",
            return_value=(self.clause_candidate,),
        ):
            with self.assertRaises(QueryError):
                _v2(self.db_path, forged, SVO_SCOPE[0])

    # Regression -----------------------------------------------------------

    def test_a1_31_existing_apposition_evaluation_vector_is_stable(self) -> None:
        first = _create(
            self.db_path,
            _human_input(
                self.apposition_candidate,
                event_key="a1-31-apposition-vector",
            ),
        )
        second = _create(
            self.db_path,
            _human_input(
                self.apposition_candidate,
                event_key="a1-31-apposition-vector",
            ),
        )
        self.assertEqual(first, second)
        self.assertEqual(
            APPOSITION_CANDIDATE_ID,
            self.frozen_candidate_id(first.candidate),
        )

    def test_a1_32_apposition_candidate_is_unchanged(self) -> None:
        self.assertEqual(
            APPOSITION_CANDIDATE_ID,
            self.frozen_candidate_id(self.apposition_candidate),
        )
        self.assertEqual(APPOSITION_KIND, self.apposition_candidate.candidate_kind)
        self.assertEqual(
            APPOSITION_DERIVATION,
            self.apposition_candidate.derivation_kind,
        )
        self.assertEqual(
            APPOSITION_DERIVATION_VERSION,
            self.apposition_candidate.derivation_version,
        )

    def test_a1_33_one_api_evaluates_both_candidate_families(self) -> None:
        records = (
            _create(
                self.db_path,
                _human_input(
                    self.apposition_candidate,
                    event_key="a1-33-apposition",
                ),
            ),
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    event_key="a1-33-clause",
                ),
            ),
        )
        self.assertEqual(
            {APPOSITION_KIND, CLAUSE_KIND},
            {record.candidate.candidate_kind for record in records},
        )
        for record in records:
            self.assertEqual(PROTOCOL_ID, record.evaluation_protocol_id)
            self.assertEqual(PROTOCOL_VERSION, record.evaluation_protocol_version)
            self.assertEqual("human", record.evaluator_class)
            self.assertEqual("candidate", record.candidate.status)

    # Firewalls ------------------------------------------------------------

    def test_a1_34_evaluation_record_has_no_semantic_entity_fields(self) -> None:
        fields = _field_names(evaluation.EvaluatedStructuralInterpretation)
        self.assertTrue(SEMANTIC_FIELDS.isdisjoint(fields))

    def test_a1_35_evaluation_record_has_no_confidence_fields(self) -> None:
        fields = _field_names(evaluation.EvaluatedStructuralInterpretation)
        self.assertTrue(CONFIDENCE_FIELDS.isdisjoint(fields))

    def test_a1_36_svo_codes_remain_only_in_candidate_echo(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                event_key="a1-36-structural-only",
            ),
        )
        value = asdict(record)
        self.assertEqual(
            ["S", "V", "O"],
            [
                component["source_cat"]
                for component in value["candidate"]["payload"]["components"]
            ],
        )
        top_level_keys = set(value)
        self.assertTrue(SEMANTIC_FIELDS.isdisjoint(top_level_keys))
        self.assertTrue(CONFIDENCE_FIELDS.isdisjoint(top_level_keys))

    def test_a1_37_semantic_shortcut_arguments_are_not_accepted(self) -> None:
        with self.assertRaises(TypeError):
            _create(
                self.db_path,
                _human_input(
                    self.clause_candidate,
                    event_key="a1-37-no-shortcut",
                ),
                actor=SVO_CHILDREN[0],
            )

    # Persistence and local identity --------------------------------------

    def test_a1_38_amendment_exposes_no_persistence_api(self) -> None:
        forbidden = {
            "save_evaluation",
            "insert_evaluation",
            "delete_evaluation",
            "update_evaluation",
            "create_evaluation_database",
            "persist_candidate",
        }
        self.assertTrue(forbidden.isdisjoint(dir(evaluation)))

    def test_a1_39_source_database_is_not_modified(self) -> None:
        before = _database_state(self.db_path)
        _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                event_key="a1-39-read-only",
            ),
        )
        self.assertEqual(before, _database_state(self.db_path))

    def test_a1_40_no_local_pk_enters_record_or_identity(self) -> None:
        record = _create(
            self.db_path,
            _human_input(
                self.clause_candidate,
                event_key="a1-40-no-local-pk",
            ),
        )
        keys = set(_walk_keys(record))
        self.assertTrue(LOCAL_PK_FIELDS.isdisjoint(keys))
        self.assertFalse(hasattr(record, "database_path"))

    def test_a1_41_surrogate_key_values_do_not_change_candidate_or_evaluation(self) -> None:
        from tests.support.unit8_amendment1_store import build_amendment1_store

        with tempfile.TemporaryDirectory(prefix="macula-unit8-amendment1-pk-") as directory:
            other = Path(directory) / "source.sqlite3"
            build_amendment1_store(other, pk_offset=20000)
            other_clause = _find_candidate(
                candidates.derive_structural_candidates(other, SVO_SCOPE[0]),
                candidate_kind=CLAUSE_KIND,
            )
            self.assertEqual(self.clause_candidate, other_clause)
            first = _create(
                self.db_path, _human_input(self.clause_candidate, event_key="a1-41-pk")
            )
            second = _create(other, _human_input(other_clause, event_key="a1-41-pk"))
            self.assertEqual(first, second)


@unittest.skipUnless(
    os.environ.get("MACULA_UNIT8_AMENDMENT1_INTEGRATION") == "1",
    "set MACULA_UNIT8_AMENDMENT1_INTEGRATION=1",
)
class Unit8Amendment1MatthewIntegrationTests(unittest.TestCase):
    """Opt-in read-only checks against the existing verified Matthew database."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.db_path = Path(
            os.environ.get("MACULA_MATTHEW_DB", str(DEFAULT_MATTHEW_DB))
        ).resolve()
        if not cls.db_path.is_file():
            raise unittest.SkipTest(f"Matthew database not found: {cls.db_path}")
        cls.before = _database_state(cls.db_path)

    @classmethod
    def tearDownClass(cls) -> None:
        assert cls.before == _database_state(cls.db_path), (
            "real Matthew database changed during Unit 8 Amendment 1 integration"
        )

    def test_int_a1_01_real_matthew_clause_candidate_can_be_evaluated(self) -> None:
        clause = _find_candidate(
            candidates.derive_structural_candidates(self.db_path, SVO_SCOPE[0]),
            candidate_kind=CLAUSE_KIND,
            candidate_id=SVO_CANDIDATE_ID,
        )
        record = _create(
            self.db_path,
            _human_input(clause, event_key="int-a1-01-real-clause"),
        )
        self.assertEqual(SVO_CANDIDATE_ID, clause.candidate_id)
        self.assertEqual(clause, record.candidate)
        self.assertEqual(SVO_SCOPE, clause.scope.member_token_refs)

    def test_int_a1_02_all_four_scope_members_produce_the_same_evaluable_candidate(self) -> None:
        observed_ids: set[str] = set()
        for ordinal, token_ref in enumerate(SVO_SCOPE):
            with self.subTest(token_ref=token_ref):
                clause = _find_candidate(
                    candidates.derive_structural_candidates(self.db_path, token_ref),
                    candidate_kind=CLAUSE_KIND,
                    candidate_id=SVO_CANDIDATE_ID,
                )
                observed_ids.add(clause.candidate_id)
                record = _create(
                    self.db_path,
                    _human_input(
                        clause,
                        event_key=f"int-a1-02-{ordinal}",
                    ),
                )
                self.assertEqual(clause, record.candidate)
        self.assertEqual({SVO_CANDIDATE_ID}, observed_ids)

    def test_int_a1_03_token_six_is_excluded_and_database_is_unchanged(self) -> None:
        before = _database_state(self.db_path)
        values = candidates.derive_structural_candidates(
            self.db_path,
            EXCLUDED_TOKEN,
        )
        clause_ids = {
            value.candidate_id
            for value in values or ()
            if value.candidate_kind == CLAUSE_KIND
        }
        self.assertNotIn(SVO_CANDIDATE_ID, clause_ids)
        self.assertEqual(before, _database_state(self.db_path))


if __name__ == "__main__":
    unittest.main()
