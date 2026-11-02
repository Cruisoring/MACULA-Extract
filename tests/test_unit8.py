from dataclasses import FrozenInstanceError, asdict, fields, replace
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import unittest
from unittest.mock import patch

from scripts import evaluated_interpretations as evaluation
from scripts import source_query as query
from scripts import structural_candidates as structural
from tests import test_unit7 as unit7


VECTOR_CANDIDATE_ID = "sha256:7f5ec0e7ad1a70565f1ef852f0b466213b03600214505408e61b809d9fae7a7c"
VECTOR_EVALUATION_ID = "eval-sha256:b13074925b58de0b3595d088e7f6c505906d1f34500e1af78bb017aa6eaf83b0"
VECTOR_BYTES = (
    '["macula.evaluated-structural-interpretation.v1",'
    '"sha256:7f5ec0e7ad1a70565f1ef852f0b466213b03600214505408e61b809d9fae7a7c",'
    '"human","example-reviewer","human-structural-adequacy","1","accepted",'
    '[["syntax_node","n:\\u03b1"],["token","MAT 1:1!3"]],'
    '["  \\u03b1\\r\\n","el"],"event:1",null]'
).encode("utf-8")


def frozen_vector() -> evaluation.EvaluatedStructuralInterpretation:
    candidate = structural.StructuralCandidate(
        VECTOR_CANDIDATE_ID, "apposition", "source-np-appos", "1",
        structural.SourceSnapshot("family", "edition", "urn:source", "revision",
                                  "manifest", "source.xml", "digest"),
        structural.CandidateScope("n:\u03b1", ("MAT 1:1!3",)),
        (structural.EvidenceRef("anchor", "syntax_node", "n:\u03b1"),),
        structural.AppositionCandidatePayload("n:\u03b1", ()),
    )
    return evaluation.EvaluatedStructuralInterpretation(
        evaluation.RECORD_PROTOCOL, VECTOR_EVALUATION_ID, candidate, "human",
        "example-reviewer", "human-structural-adequacy", "1", "accepted",
        (evaluation.RationaleCitation("syntax_node", "n:\u03b1"),
         evaluation.RationaleCitation("token", "MAT 1:1!3")),
        evaluation.RationaleNote("  \u03b1\r\n", "el"), "event:1",
    )


def candidate_id(candidate: structural.StructuralCandidate) -> str:
    """Independent test encoding permits a self-consistent forgery for V2 tests."""
    snapshot = candidate.source_snapshot
    value = [
        "macula.structural-candidate.v1",
        [snapshot.source_family, snapshot.edition, snapshot.repository_uri,
         snapshot.revision, snapshot.manifest_sha256, snapshot.relative_path, snapshot.source_sha256],
        candidate.candidate_kind, candidate.derivation_kind, candidate.derivation_version,
        [candidate.scope.source_node_id, list(candidate.scope.member_token_refs)],
        [[ref.role, ref.kind, ref.source_node_id] for ref in candidate.evidence],
        [candidate.payload.anchor_source_node_id, list(candidate.payload.child_source_node_ids)],
    ]
    return "sha256:" + hashlib.sha256(json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")).hexdigest()


def reidentify(candidate: structural.StructuralCandidate) -> structural.StructuralCandidate:
    return replace(candidate, candidate_id=candidate_id(candidate))


def tamper(value: object, **changes: object) -> object:
    for name, changed in changes.items():
        object.__setattr__(value, name, changed)
    return value


class Unit8FastTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = unit7.Unit7FastTests(methodName="runTest")
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.path = self.fixture.path
        self.db = self.fixture.db
        candidates = structural.derive_structural_candidates(self.path, "MAT 1:1!3")
        assert candidates is not None
        self.candidate = candidates[0]
        self.outer = candidates[1]
        self.citations = (
            evaluation.RationaleCitation("syntax_node", "z-inner"),
            evaluation.RationaleCitation("syntax_node", "z-leaf"),
            evaluation.RationaleCitation("syntax_node", "a-leaf"),
            evaluation.RationaleCitation("token", "MAT 1:1!3"),
            evaluation.RationaleCitation("token", "MAT 1:1!4"),
        )
        self.note = evaluation.RationaleNote("  Structural evidence inspected.\r\n", "en")

    def create(
        self, candidate: structural.StructuralCandidate | None = None, **changes: object,
    ) -> evaluation.EvaluatedStructuralInterpretation:
        arguments = {
            "evaluator_class": "human", "evaluator_label": "reviewer-a",
            "evaluation_protocol_id": "human-structural-adequacy",
            "evaluation_protocol_version": "1", "disposition": "accepted",
            "rationale_evidence": self.citations, "rationale_note": self.note, "event_key": "event:1",
            **changes,
        }
        return evaluation.create_evaluated_interpretation(
            self.path, self.candidate if candidate is None else candidate, **arguments,
        )

    def test_valid_human_accepted_preserves_candidate(self) -> None:
        before = asdict(self.candidate)
        record = self.create()
        self.assertEqual(record.disposition, "accepted")
        self.assertIs(record.candidate, self.candidate)
        self.assertEqual(asdict(self.candidate), before)
        self.assertEqual(record.candidate.status, "candidate")
        self.assertIsNone(evaluation.verify_evaluated_interpretation(record))
        self.assertIsNone(evaluation.verify_evaluated_interpretation(record, db_path=self.path))

    def test_valid_human_rejected(self) -> None:
        self.assertEqual(self.create(disposition="rejected").disposition, "rejected")

    def test_valid_human_undetermined_without_citations(self) -> None:
        record = self.create(disposition="undetermined", rationale_evidence=())
        self.assertEqual(record.rationale_evidence, ())
        self.assertEqual(record.rationale_note, self.note)

    def test_frozen_literal_identity_vector_and_canonical_bytes(self) -> None:
        record = frozen_vector()
        self.assertEqual(candidate_id(record.candidate), VECTOR_CANDIDATE_ID)
        self.assertEqual("eval-sha256:" + hashlib.sha256(VECTOR_BYTES).hexdigest(), VECTOR_EVALUATION_ID)
        with patch.object(evaluation, "_identity_bytes", wraps=evaluation._identity_bytes) as serialize:
            evaluation.verify_evaluated_interpretation(record)
        self.assertEqual(serialize.call_args_list[-1].args[0], json.loads(VECTOR_BYTES))
        self.assertEqual(evaluation._identity_bytes(json.loads(VECTOR_BYTES)), VECTOR_BYTES)
        self.assertEqual(record.evaluation_id, VECTOR_EVALUATION_ID)

    def test_identity_across_processes_hashseeds_and_database_paths(self) -> None:
        expected = self.create().evaluation_id
        moved = self.path.with_name("another # location.sqlite3")
        moved.write_bytes(self.path.read_bytes())
        code = (
            "from scripts import structural_candidates as s, evaluated_interpretations as e; "
            "import sys; c=s.derive_structural_candidates(sys.argv[1], 'MAT 1:1!3')[0]; "
            "r=e.create_evaluated_interpretation(sys.argv[1], c, evaluator_class='human', "
            "evaluator_label='reviewer-a', evaluation_protocol_id='human-structural-adequacy', "
            "evaluation_protocol_version='1', disposition='accepted', "
            "rationale_evidence=tuple(e.RationaleCitation('syntax_node', x.source_node_id) for x in c.evidence)"
            "+tuple(e.RationaleCitation('token', x) for x in c.scope.member_token_refs), "
            "rationale_note=e.RationaleNote('  Structural evidence inspected.\\r\\n', 'en'), "
            "event_key='event:1'); print(r.evaluation_id)"
        )
        for seed, path in (("1", self.path), ("42", moved)):
            with self.subTest(seed=seed):
                result = subprocess.run(
                    [sys.executable, "-B", "-c", code, str(path)],
                    cwd=Path(__file__).resolve().parents[1],
                    env={**os.environ, "PYTHONHASHSEED": seed},
                    check=True, capture_output=True, text=True,
                )
                self.assertEqual(result.stdout.strip(), expected)

    def test_v1_is_independent_of_unit7_private_identity_helpers(self) -> None:
        with patch.object(structural, "_candidate_id", side_effect=AssertionError("private helper")), \
                patch.object(structural, "_identity_bytes", side_effect=AssertionError("private helper")), \
                patch.object(structural, "derive_structural_candidates", side_effect=AssertionError("offline")):
            evaluation.verify_evaluated_interpretation(frozen_vector())

    def test_creation_and_online_verification_require_public_v2(self) -> None:
        derive = structural.derive_structural_candidates
        with patch.object(structural, "derive_structural_candidates", wraps=derive) as public:
            record = self.create()
            public.assert_called_once_with(self.path, "MAT 1:1!3")
            evaluation.verify_evaluated_interpretation(record, db_path=self.path)
            self.assertEqual(public.call_count, 2)

    def test_malformed_candidate_ids_rejected_before_source_access(self) -> None:
        for identity in ("", "sha256:" + "A" * 64, "sha256:" + "a" * 63,
                         "eval-sha256:" + "a" * 64, "1", 1, None):
            with self.subTest(identity=identity), \
                    patch.object(structural, "derive_structural_candidates") as derive:
                with self.assertRaisesRegex(query.QueryError, "malformed candidate_id"):
                    self.create(replace(self.candidate, candidate_id=identity))
                derive.assert_not_called()

    def test_candidate_id_recomputation_rejects_modified_echo(self) -> None:
        mutations = (
            {"candidate_id": "sha256:" + "0" * 64},
            {"source_snapshot": replace(self.candidate.source_snapshot, revision="changed")},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 1:1!3",))},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaisesRegex(query.QueryError, "does not recompute"):
                self.create(replace(self.candidate, **mutation))

    def test_malformed_or_modified_evaluation_identity_rejected(self) -> None:
        record = self.create()
        for identity in ("", "sha256:" + "a" * 64, "eval-sha256:" + "A" * 64, 1, None):
            with self.subTest(identity=identity), self.assertRaisesRegex(query.QueryError, "malformed evaluation_id"):
                replace(record, evaluation_id=identity)
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            replace(record, evaluation_id="eval-sha256:" + "0" * 64)
        for change in ({"disposition": "rejected"}, {"event_key": "event:2"},
                       {"rationale_note": evaluation.RationaleNote("Other note", "en")}):
            with self.subTest(change=change), self.assertRaisesRegex(query.QueryError, "does not recompute"):
                replace(record, **change)

    def test_verify_revalidates_bypassed_frozen_constructor(self) -> None:
        record = self.create()
        tamper(record, disposition="rejected")
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            evaluation.verify_evaluated_interpretation(record)

    def test_v2_rejects_self_consistent_modified_echo(self) -> None:
        altered = reidentify(replace(
            self.candidate, scope=replace(self.candidate.scope, member_token_refs=("MAT 1:1!3",)),
        ))
        with self.assertRaisesRegex(query.QueryError, "source-grounded re-derivation"):
            self.create(altered, rationale_evidence=(self.citations[0],))

    def test_v2_rejects_wrong_snapshot_but_offline_history_stays_bound(self) -> None:
        record = self.create()
        original = record.candidate.source_snapshot
        self.fixture.mutate("DROP TRIGGER snapshot_no_update; UPDATE dataset_snapshot "
                            "SET revision='" + "2" * 40 + "';")
        evaluation.verify_evaluated_interpretation(record)
        with self.assertRaisesRegex(query.QueryError, "snapshot mismatch"):
            evaluation.verify_evaluated_interpretation(record, db_path=self.path)
        with self.assertRaisesRegex(query.QueryError, "snapshot mismatch"):
            self.create()
        self.assertEqual(record.candidate.source_snapshot, original)

    def test_unknown_candidate_kind_derivation_version_and_status_rejected(self) -> None:
        for field, value, message in (
            ("candidate_kind", "predicate", "candidate kind"),
            ("derivation_kind", "automatic", "derivation"),
            ("derivation_version", "2", "derivation"),
            ("derivation_version", 1, "derivation"),
            ("status", "accepted", "status"),
        ):
            candidate = replace(self.candidate)
            tamper(candidate, **{field: value})
            with self.subTest(field=field, value=value), self.assertRaisesRegex(query.QueryError, message):
                self.create(candidate)

    def test_all_seven_snapshot_fields_are_required(self) -> None:
        for field in fields(self.candidate.source_snapshot):
            for value in ("", " \t", None, 1):
                candidate = replace(self.candidate, source_snapshot=replace(
                    self.candidate.source_snapshot, **{field.name: value},
                ))
                with self.subTest(field=field.name, value=value), \
                        self.assertRaisesRegex(query.QueryError, "snapshot field"):
                    self.create(candidate)
        with self.assertRaisesRegex(query.QueryError, "seven source snapshot"):
            self.create(replace(self.candidate, source_snapshot=None))

    def test_candidate_scope_evidence_and_payload_shapes_are_closed(self) -> None:
        mutations = (
            {"scope": None},
            {"scope": replace(self.candidate.scope, source_node_id=1)},
            {"scope": replace(self.candidate.scope, member_token_refs=())},
            {"scope": replace(self.candidate.scope, member_token_refs=["MAT 1:1!3"])},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 01:1!3",))},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 1:1!3", "MAT 1:1!3"))},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 1:1!4", "MAT 1:1!3"))},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 1:1!3", "MRK 1:1!4"))},
            {"scope": replace(self.candidate.scope, member_token_refs=("MAT 1:1!" + "9" * 30,))},
            {"evidence": ()},
            {"evidence": list(self.candidate.evidence)},
            {"evidence": (("anchor", "syntax_node", "z-inner"),)},
            {"evidence": (replace(self.candidate.evidence[0], role="child"),)},
            {"evidence": (replace(self.candidate.evidence[0], kind="token"),)},
            {"evidence": (self.candidate.evidence[0], self.candidate.evidence[0])},
            {"evidence": tuple(reversed(self.candidate.evidence))},
            {"payload": None},
            {"payload": replace(self.candidate.payload, anchor_source_node_id="different")},
            {"payload": replace(self.candidate.payload, child_source_node_ids=["z-leaf", "a-leaf"])},
            {"payload": replace(self.candidate.payload, child_source_node_ids=("a-leaf", "z-leaf"))},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(query.QueryError):
                self.create(replace(self.candidate, **mutation))

    def test_local_pk_or_unknown_dto_is_not_candidate_identity(self) -> None:
        for candidate in (1, {"candidate_id": 1}, "z-inner"):
            with self.subTest(candidate=candidate), self.assertRaisesRegex(query.QueryError, "not a local PK"):
                self.create(candidate)
        with self.assertRaises(TypeError):
            structural.StructuralCandidate(**{**asdict(self.candidate), "node_id": 1})

    def test_unknown_evaluation_protocol_and_version_rejected(self) -> None:
        for change in ({"evaluation_protocol_id": "accept-all"}, {"evaluation_protocol_version": "2"},
                       {"evaluation_protocol_version": 1}, {"evaluation_protocol_id": None}):
            with self.subTest(change=change), self.assertRaisesRegex(query.QueryError, "unsupported evaluation protocol"):
                self.create(**change)

    def test_unknown_record_protocol_rejected(self) -> None:
        with self.assertRaisesRegex(query.QueryError, "record_protocol"):
            replace(self.create(), record_protocol="other")

    def test_unknown_and_reserved_evaluator_classes_fail_closed(self) -> None:
        for evaluator in ("deterministic-policy", "ai", "llm", "model", "", None):
            with self.subTest(evaluator=evaluator), self.assertRaisesRegex(query.QueryError, "evaluator class"):
                self.create(evaluator_class=evaluator)

    def test_unsupported_dispositions_rejected(self) -> None:
        for disposition in ("confirmed", "correct", "preferred", "canonical", "partial", "", None, 1):
            with self.subTest(disposition=disposition), self.assertRaisesRegex(query.QueryError, "disposition"):
                self.create(disposition=disposition)

    def test_human_label_required_bounded_exact_and_control_free(self) -> None:
        for label in ("", " \t", None, 1, "x" * 129, "reviewer\n", "reviewer\x7f", "reviewer\x85"):
            with self.subTest(label=label), self.assertRaisesRegex(query.QueryError, "evaluator_label"):
                self.create(evaluator_label=label)
        first = self.create(evaluator_label=" Reviewer ")
        self.assertEqual(first.evaluator_label, " Reviewer ")
        self.assertNotEqual(first.evaluation_id, self.create(evaluator_label="reviewer").evaluation_id)
        self.create(evaluator_label="x" * 128)

    def test_event_key_required_bounded_and_never_generated(self) -> None:
        for key in ("", " ", None, 1, "x" * 129, "bad key", "event/\u03b1"):
            with self.subTest(key=key), self.assertRaisesRegex(query.QueryError, "event_key"):
                self.create(event_key=key)
        self.assertEqual(self.create(event_key="A_0.z:1-2").event_key, "A_0.z:1-2")
        self.create(event_key="x" * 128)

    def test_human_note_required_for_all_dispositions(self) -> None:
        for disposition in ("accepted", "rejected", "undetermined"):
            for note in (None, "", ("text", "en")):
                with self.subTest(disposition=disposition, note=note), \
                        self.assertRaisesRegex(query.QueryError, "rationale note"):
                    self.create(disposition=disposition, rationale_note=note)
        for text in ("", " \r\n\t", None, "\ud800"):
            with self.subTest(text=repr(text)), self.assertRaises(query.QueryError):
                evaluation.RationaleNote(text, "en")

    def test_note_and_language_preserved_verbatim_without_normalization(self) -> None:
        notes = (evaluation.RationaleNote("  \u03b1\r\n", "EL"),
                 evaluation.RationaleNote("\u00e9", "fr"),
                 evaluation.RationaleNote("e\u0301", "fr"))
        records = [self.create(rationale_note=note) for note in notes]
        self.assertEqual(records[0].rationale_note, notes[0])
        self.assertEqual(len({record.evaluation_id for record in records}), 3)
        self.assertNotEqual(self.create(rationale_note=replace(notes[0], language="el")).evaluation_id,
                            records[0].evaluation_id)

    def test_language_tag_validation(self) -> None:
        for language in ("en", "en-US", "zh-Hant-TW", "de-CH-1901", "sl-rozaj-biske",
                         "en-u-ca-gregory", "x-private", "x-abcde-abcde", "i-klingon"):
            with self.subTest(language=language):
                self.assertEqual(evaluation.RationaleNote("note", language).language, language)
        for language in ("", None, " en", "en_US", "English!", "e", "en-", "en-a",
                         "en-abcde-abcde", "en-u-ca-u-nu"):
            with self.subTest(language=language), self.assertRaises(query.QueryError):
                evaluation.RationaleNote("note", language)

    def test_accepted_rejected_require_citations(self) -> None:
        for disposition in ("accepted", "rejected"):
            with self.subTest(disposition=disposition), self.assertRaisesRegex(query.QueryError, "at least one"):
                self.create(disposition=disposition, rationale_evidence=())

    def test_citations_only_candidate_nodes_and_scope_tokens(self) -> None:
        for kind, identity in (("syntax_node", "unrelated-appos"), ("syntax_node", "a-outer"),
                               ("token", "MAT 1:1!1"), ("token", "MAT 1:2!6"),
                               ("token", "MAT 1:1!999")):
            with self.subTest(kind=kind, identity=identity), self.assertRaisesRegex(query.QueryError, "outside candidate"):
                self.create(rationale_evidence=(evaluation.RationaleCitation(kind, identity),))
        for kind, identity in (("external", "urn:other"), ("syntax_node", 1), ("token", "")):
            with self.subTest(kind=kind), self.assertRaises(query.QueryError):
                evaluation.RationaleCitation(kind, identity)

    def test_duplicate_and_noncanonical_citation_order_rejected_not_sorted(self) -> None:
        for citations in ((self.citations[0], self.citations[0]),
                          tuple(reversed(self.citations)), (self.citations[2], self.citations[1]),
                          (self.citations[3], self.citations[0])):
            with self.subTest(citations=citations), self.assertRaisesRegex(query.QueryError, "ordered"):
                self.create(rationale_evidence=citations)
        subset = (self.citations[1], self.citations[3])
        self.assertEqual(self.create(rationale_evidence=subset).rationale_evidence, subset)
        self.create(rationale_evidence=(self.citations[3],))

    def test_rationale_collections_require_typed_immutable_records(self) -> None:
        for citations in (list(self.citations), (("syntax_node", "z-inner"),), None):
            with self.subTest(citations=citations), self.assertRaises(query.QueryError):
                self.create(rationale_evidence=citations)

    def test_unsupported_confidence_semantic_theological_and_extra_fields_rejected(self) -> None:
        for name in ("confidence", "probability", "certainty", "score", "percentage", "rank", "weight",
                     "actor", "action", "patient", "event", "result", "identity", "property", "role",
                     "theological_meaning", "doctrine", "timestamp", "node_id", "evaluated_scope"):
            with self.subTest(field=name), self.assertRaises(TypeError):
                self.create(**{name: 1})
            with self.subTest(dto_field=name), self.assertRaises(TypeError):
                replace(self.create(), **{name: 1})

    def test_same_event_same_content_is_idempotent(self) -> None:
        first = self.create()
        second = self.create(prior_records=(first,))
        self.assertEqual(first, second)
        self.assertEqual(first.evaluation_id, second.evaluation_id)
        evaluation.verify_evaluated_interpretation(second, prior_records=(first, first))

    def test_same_event_changed_content_is_rejected(self) -> None:
        first = self.create()
        for change in ({"disposition": "rejected"}, {"rationale_note": evaluation.RationaleNote("changed", "en")},
                       {"rationale_evidence": (self.citations[0],)}):
            with self.subTest(change=change), self.assertRaisesRegex(query.QueryError, "event_key reuse conflict"):
                self.create(prior_records=(first,), **change)
        other = self.create(disposition="rejected")
        with self.assertRaisesRegex(query.QueryError, "event_key reuse conflict"):
            evaluation.verify_evaluated_interpretation(other, prior_records=(first,))

    def test_event_reuse_conflict_also_spans_candidates(self) -> None:
        first = self.create()
        with self.assertRaisesRegex(query.QueryError, "event_key reuse conflict"):
            self.create(self.outer, rationale_evidence=(
                evaluation.RationaleCitation("syntax_node", "a-outer"),
            ), prior_records=(first,))

    def test_different_events_produce_distinct_records(self) -> None:
        first = self.create()
        second = self.create(event_key="event:2", prior_records=(first,))
        self.assertNotEqual(first.evaluation_id, second.evaluation_id)

    def test_opposing_evaluations_and_different_evaluators_coexist(self) -> None:
        first = self.create()
        second = self.create(disposition="rejected", evaluator_label="reviewer-b", prior_records=(first,))
        third = self.create(disposition="rejected", event_key="event:2", prior_records=(first, second))
        for record in (first, second, third):
            evaluation.verify_evaluated_interpretation(record, prior_records=(third, first, second))
        self.assertEqual(first.disposition, "accepted")

    def test_same_evaluator_supersession_forks_and_chain_preserve_predecessor(self) -> None:
        first = self.create()
        before = asdict(first)
        second = self.create(event_key="event:2", disposition="rejected", supersedes=first.evaluation_id,
                             prior_records=(first,))
        fork = self.create(event_key="event:3", disposition="undetermined", supersedes=first.evaluation_id,
                           prior_records=(first, second))
        third = self.create(event_key="event:4", supersedes=second.evaluation_id,
                            prior_records=(fork, second, first))
        evaluation.verify_evaluated_interpretation(first, prior_records=(third, fork, second))
        self.assertEqual(asdict(first), before)

    def test_missing_and_cross_candidate_predecessors_rejected(self) -> None:
        with self.assertRaisesRegex(query.QueryError, "predecessor not found"):
            self.create(supersedes="eval-sha256:" + "1" * 64)
        first = self.create()
        with self.assertRaisesRegex(query.QueryError, "same candidate"):
            self.create(self.outer, rationale_evidence=(evaluation.RationaleCitation("syntax_node", "a-outer"),),
                        event_key="event:2", supersedes=first.evaluation_id, prior_records=(first,))

    def test_another_evaluator_cannot_supersede(self) -> None:
        first = self.create()
        with self.assertRaisesRegex(query.QueryError, "same evaluator"):
            self.create(evaluator_label="reviewer-b", supersedes=first.evaluation_id, prior_records=(first,))

    def test_supersession_requires_one_predecessor_and_rejects_self_reference(self) -> None:
        first = self.create()
        for predecessor in ("bad", (first.evaluation_id,), [first.evaluation_id], 1):
            with self.subTest(predecessor=predecessor), self.assertRaisesRegex(query.QueryError, "one evaluation_id"):
                self.create(event_key="event:2", supersedes=predecessor, prior_records=(first,))
        with self.assertRaisesRegex(query.QueryError, "supersede itself"):
            replace(first, supersedes=first.evaluation_id)

    def test_invalid_prior_record_and_incomplete_history_fail_closed(self) -> None:
        first = self.create()
        second = self.create(event_key="event:2", supersedes=first.evaluation_id, prior_records=(first,))
        with self.assertRaisesRegex(query.QueryError, "predecessor not found"):
            self.create(event_key="event:3", supersedes=second.evaluation_id, prior_records=(second,))
        tamper(first, evaluation_id="eval-sha256:" + "0" * 64)
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            self.create(event_key="event:4", prior_records=(first,))
        for prior in ([second], (1,)):
            with self.subTest(prior=prior), self.assertRaises(query.QueryError):
                self.create(prior_records=prior)

    def test_existing_history_conflicts_are_not_hidden(self) -> None:
        first = self.create()
        conflicting = self.create(disposition="rejected")
        with self.assertRaisesRegex(query.QueryError, "event_key reuse conflict"):
            self.create(event_key="event:2", prior_records=(first, conflicting))

    def test_unknown_exact_candidate_has_explicit_not_found_error(self) -> None:
        unknown = reidentify(replace(self.candidate, scope=replace(
            self.candidate.scope, member_token_refs=("MAT 1:1!999",),
        )))
        with self.assertRaisesRegex(query.QueryError, "candidate not found"):
            self.create(unknown, rationale_evidence=(self.citations[0],))
        valid_non_candidate = reidentify(replace(self.candidate, scope=replace(
            self.candidate.scope, member_token_refs=("MAT 1:2!5",),
        )))
        with self.assertRaisesRegex(query.QueryError, "candidate not found"):
            self.create(valid_non_candidate, rationale_evidence=(self.citations[0],))
        unknown_anchor = reidentify(replace(
            self.candidate, scope=replace(self.candidate.scope, source_node_id="unknown-anchor"),
            evidence=(structural.EvidenceRef("anchor", "syntax_node", "unknown-anchor"),),
            payload=structural.AppositionCandidatePayload("unknown-anchor", ()),
        ))
        with self.assertRaisesRegex(query.QueryError, "candidate not found"):
            self.create(unknown_anchor, rationale_evidence=(evaluation.RationaleCitation("token", "MAT 1:1!3"),))

    def test_v2_requires_exact_evidence_and_payload_order(self) -> None:
        altered = reidentify(replace(
            self.candidate,
            evidence=(self.candidate.evidence[0], *reversed(self.candidate.evidence[1:])),
            payload=replace(self.candidate.payload,
                            child_source_node_ids=tuple(reversed(self.candidate.payload.child_source_node_ids))),
        ))
        with self.assertRaisesRegex(query.QueryError, "source-grounded re-derivation"):
            self.create(altered, rationale_evidence=(self.citations[0],))

    def test_source_infrastructure_errors_propagate_not_not_found(self) -> None:
        with patch.object(structural, "derive_structural_candidates",
                          side_effect=query.QueryError("source infrastructure failure")):
            with self.assertRaisesRegex(query.QueryError, "source infrastructure failure"):
                self.create()
        with self.assertRaises(query.QueryError):
            evaluation.verify_evaluated_interpretation(self.create(), db_path=self.path.with_name("missing.sqlite3"))
        with self.assertRaisesRegex(query.QueryError, "requires a source database"):
            evaluation.create_evaluated_interpretation(None, self.candidate, evaluator_class="human",
                evaluator_label="reviewer", evaluation_protocol_id="human-structural-adequacy",
                evaluation_protocol_version="1", disposition="accepted", rationale_evidence=self.citations,
                rationale_note=self.note, event_key="one")

    def test_surrogate_pk_reallocation_does_not_change_any_output(self) -> None:
        moved = self.path.with_name("reallocated.sqlite3")
        self.fixture.make_store(moved, 20000)
        derived = structural.derive_structural_candidates(moved, "MAT 1:1!3")
        assert derived is not None
        before = self.create()
        self.path = moved
        after = self.create(derived[0])
        self.assertEqual(before, after)
        evaluation.verify_evaluated_interpretation(before, db_path=moved)
        for table, column in (("token", "token_id"), ("syntax_node", "node_id"),
                              ("tree", "tree_id"), ("book", "book_id"), ("xml_element", "element_id")):
            left = self.db.execute(f"SELECT {column} FROM {table} ORDER BY {column}").fetchall()
            right = unit7.sqlite_rows(moved, f"SELECT {column} FROM {table} ORDER BY {column}")
            self.assertNotEqual(left, right)

    def test_readonly_connections_closed_bytes_schema_and_no_sidecars(self) -> None:
        before = self.path.read_bytes()
        catalog = self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall()
        files_before = set(self.path.parent.iterdir())
        statements: list[str] = []
        opened: list[sqlite3.Connection] = []
        connect = query._connect_readonly

        def checked_connect(path: Path) -> sqlite3.Connection:
            db = connect(path)
            opened.append(db)
            for pragma in ("query_only", "foreign_keys", "recursive_triggers"):
                self.assertEqual(db.execute(f"PRAGMA {pragma}").fetchone()[0], 1)
            db.execute("PRAGMA query_only=OFF")
            for sql in ("UPDATE token SET english='changed'", "CREATE TABLE forbidden(x)",
                        "DELETE FROM node_token_membership"):
                with self.assertRaisesRegex(sqlite3.OperationalError, "readonly"):
                    db.execute(sql)
            db.execute("PRAGMA query_only=ON")
            db.set_trace_callback(statements.append)
            return db

        with patch.object(query, "_connect_readonly", side_effect=checked_connect):
            record = self.create()
            evaluation.verify_evaluated_interpretation(record, db_path=self.path)
        self.assertEqual(len(opened), 4)
        for db in opened:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")
        self.assertFalse(any(sql.lstrip().split()[0].upper() in (
            "INSERT", "UPDATE", "DELETE", "REPLACE", "CREATE", "DROP", "ALTER", "ATTACH", "VACUUM",
        ) for sql in statements))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.db.execute("SELECT * FROM sqlite_schema ORDER BY type,name").fetchall(), catalog)
        self.assertEqual(self.db.execute("PRAGMA user_version").fetchone(), (2,))
        self.assertEqual(set(self.path.parent.iterdir()), files_before)

    def test_matthew_1_1_verbless_cannot_fabricate_copula_or_verb(self) -> None:
        source = query.get_source_evidence(self.path, "MAT 1:1!3")
        assert source is not None
        self.assertIn(("P2CL", "Verbless"), [(node.rule, node.cl_type) for node in source.ancestors])
        for identity in ("implicit-copula", "invented-verb"):
            with self.subTest(identity=identity), self.assertRaisesRegex(query.QueryError, "outside candidate"):
                self.create(rationale_evidence=(evaluation.RationaleCitation("syntax_node", identity),))
        self.create()
        self.assertEqual(source, query.get_source_evidence(self.path, "MAT 1:1!3"))

    def test_matthew_1_2_envelope_cannot_introduce_token_six(self) -> None:
        members = query.get_members(self.path, unit7.BOUNDARY)
        assert members is not None
        self.assertEqual(tuple(token.ref for token in members),
                         tuple(f"MAT 1:2!{word}" for word in (5, 7, 8, 9)))
        self.assertEqual(structural.derive_structural_candidates(self.path, "MAT 1:2!5"), ())
        forged = replace(self.candidate, scope=structural.CandidateScope(
            unit7.BOUNDARY, tuple(f"MAT 1:2!{word}" for word in (5, 6, 7, 8, 9))),
            evidence=(structural.EvidenceRef("anchor", "syntax_node", unit7.BOUNDARY),),
            payload=structural.AppositionCandidatePayload(unit7.BOUNDARY, ()))
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            self.create(forged, rationale_evidence=(evaluation.RationaleCitation("token", "MAT 1:2!6"),))
        with self.assertRaisesRegex(query.QueryError, "candidate not found"):
            self.create(reidentify(forged),
                        rationale_evidence=(evaluation.RationaleCitation("token", "MAT 1:2!6"),))

    def test_all_dtos_frozen_collections_tuples_and_closed_field_set(self) -> None:
        record = self.create()
        self.assertNotIsInstance(record, structural.StructuralCandidate)
        for obj in (record, record.rationale_note, record.rationale_evidence[0], record.candidate,
                    record.candidate.source_snapshot, record.candidate.scope, record.candidate.payload,
                    record.candidate.evidence[0]):
            with self.assertRaises(FrozenInstanceError):
                setattr(obj, fields(obj)[0].name, "changed")
            self.assertTrue(unit7.LOCAL_IDS.isdisjoint(field.name for field in fields(obj)))
        for collection in (record.rationale_evidence, record.candidate.evidence,
                           record.candidate.scope.member_token_refs, record.candidate.payload.child_source_node_ids):
            self.assertIsInstance(collection, tuple)
        self.assertEqual({field.name for field in fields(record)}, {
            "record_protocol", "evaluation_id", "candidate", "evaluator_class", "evaluator_label",
            "evaluation_protocol_id", "evaluation_protocol_version", "disposition", "rationale_evidence",
            "rationale_note", "event_key", "supersedes",
        })


_LOCAL_DATABASE = Path(os.environ.get(
    "MACULA_UNIT8_DATABASE", r"C:\Projects\MACULA-Extract\sblgnt-matthew.sqlite3",
))


@unittest.skipUnless(os.environ.get("MACULA_UNIT8_INTEGRATION") == "1" and _LOCAL_DATABASE.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit8MatthewIntegrationTests(unittest.TestCase):
    def test_actual_matthew_1_1_apposition_and_preservation(self) -> None:
        before = hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest()
        size = _LOCAL_DATABASE.stat().st_size
        catalog = unit7.sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name")
        version = unit7.sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version")
        try:
            candidates = structural.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3")
            assert candidates is not None
            self.assertEqual(len(candidates), 3)
            self.assertEqual(candidates[0].candidate_id,
                             "sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c")
            source = query.get_source_evidence(_LOCAL_DATABASE, "MAT 1:1!3")
            verse = query.get_verse(_LOCAL_DATABASE, "MAT", 1, 1)
            assert source is not None and verse is not None
            self.assertEqual([(node.rule, node.cl_type) for node in source.ancestors if node.cat == "CL"],
                             [("P2CL", "Verbless")])
            self.assertEqual([token.cat for token in verse.tokens], ["noun"] * 8)
            for candidate in candidates:
                record = evaluation.create_evaluated_interpretation(
                    _LOCAL_DATABASE, candidate, evaluator_class="human", evaluator_label="test-only-reviewer",
                    evaluation_protocol_id="human-structural-adequacy", evaluation_protocol_version="1",
                    disposition="undetermined",
                    rationale_evidence=(evaluation.RationaleCitation("syntax_node", candidate.scope.source_node_id),),
                    rationale_note=evaluation.RationaleNote("Test-only record, not a recorded source judgment.", "en"),
                    event_key="test:" + candidate.scope.source_node_id,
                )
                evaluation.verify_evaluated_interpretation(record)
                evaluation.verify_evaluated_interpretation(record, db_path=_LOCAL_DATABASE)
                self.assertIs(record.candidate, candidate)
                print(f"Unit 8 test-only evaluation: {record.evaluation_id}; candidate={candidate.candidate_id}",
                      flush=True)
            self.assertEqual(candidates, structural.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:1!3"))
            self.assertEqual(structural.derive_structural_candidates(_LOCAL_DATABASE, "MAT 1:2!5"), ())
            members = query.get_members(_LOCAL_DATABASE, unit7.BOUNDARY)
            assert members is not None
            self.assertEqual(tuple(token.ref for token in members),
                             tuple(f"MAT 1:2!{word}" for word in (5, 7, 8, 9)))
        finally:
            self.assertEqual(hashlib.sha256(_LOCAL_DATABASE.read_bytes()).hexdigest(), before)
            self.assertEqual(_LOCAL_DATABASE.stat().st_size, size)
            self.assertEqual(unit7.sqlite_rows(_LOCAL_DATABASE, "SELECT * FROM sqlite_schema ORDER BY type,name"), catalog)
            self.assertEqual(unit7.sqlite_rows(_LOCAL_DATABASE, "PRAGMA user_version"), version)
        print(f"Unit 8 read-only store unchanged: {size} bytes; SHA-256 {before}; user_version {version[0][0]}",
              flush=True)


if __name__ == "__main__":
    unittest.main()
