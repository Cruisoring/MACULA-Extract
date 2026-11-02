from contextlib import closing
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

from scripts import evaluated_interpretations as evaluated
from scripts import projection_store as store
from scripts import source_fidelity as fidelity
from scripts import source_query as query
from scripts import source_schema as schema
from scripts import structural_candidates as structural
from tests.support.unit8_amendment1_store import build_amendment1_store


ROOT = Path(__file__).resolve().parents[1]
SVO_ID = "sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087"
EVAL_ID = "eval-sha256:3115087c4d749fa4e1ea2e1f2d16c4d6142798ce2b4505cff930a5f12147257d"
SUCCESSOR_ID = "eval-sha256:1c39cb8d35b4102e313d3a337b4b43c3ad6b73b5b35093574e4c191de6a46e21"
EVAL_BYTES = (
    '["macula.evaluated-structural-interpretation.v1",'
    '"sha256:129c397055985ed0156e320bc543d551be0cf8d3ecfa192e60914540646ff087",'
    '"human","unit10-vector","human-structural-adequacy","1","undetermined",'
    '[["syntax_node","400010020050040"],["token","MAT 1:2!5"]],'
    '["  \\u03b1\\r\\n","el"],"unit10:1",null]'
).encode("utf-8")
REFS = ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
ABSENT_CANDIDATE = "sha256:" + "0" * 64
ABSENT_EVALUATION = "eval-sha256:" + "0" * 64


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)


def independent_candidate_id(candidate: store.Candidate) -> str:
    """The accepted ordered-array wire, not the persistence JSON representation."""
    snapshot = candidate.source_snapshot
    if isinstance(candidate, structural.ClauseStructureCandidate):
        payload = [
            candidate.payload.anchor_source_node_id, candidate.payload.source_rule,
            candidate.payload.source_head_raw,
            [[c.component_role, c.source_cat, c.sibling_ordinal, c.source_node_id,
              list(c.member_token_refs)] for c in candidate.payload.components],
        ]
    else:
        payload = [candidate.payload.anchor_source_node_id, list(candidate.payload.child_source_node_ids)]
    value = [
        "macula.structural-candidate.v1",
        [snapshot.source_family, snapshot.edition, snapshot.repository_uri, snapshot.revision,
         snapshot.manifest_sha256, snapshot.relative_path, snapshot.source_sha256],
        candidate.candidate_kind, candidate.derivation_kind, candidate.derivation_version,
        [candidate.scope.source_node_id, list(candidate.scope.member_token_refs)],
        [[e.role, e.kind, e.source_node_id] for e in candidate.evidence], payload,
    ]
    wire = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(wire).hexdigest()


def independent_evaluation_id(record: evaluated.EvaluatedStructuralInterpretation) -> str:
    value = [
        record.record_protocol, record.candidate.candidate_id, record.evaluator_class,
        record.evaluator_label, record.evaluation_protocol_id, record.evaluation_protocol_version,
        record.disposition, [[c.kind, c.citation_id] for c in record.rationale_evidence],
        [record.rationale_note.text, record.rationale_note.language],
        record.event_key, record.supersedes,
    ]
    wire = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode()
    return "eval-sha256:" + hashlib.sha256(wire).hexdigest()


def derive(path: Path, ref: str) -> tuple[store.Candidate, ...]:
    result = structural.derive_structural_candidates(path, ref)
    if result is None:
        raise AssertionError(f"fixture token missing: {ref}")
    return result


def record_for(source: Path, candidate: store.Candidate, *, event: str = "unit10:1",
               label: str = "unit10-vector", disposition: str = "undetermined",
               predecessor: evaluated.EvaluatedStructuralInterpretation | None = None,
               prior: tuple[evaluated.EvaluatedStructuralInterpretation, ...] = (),
               note: evaluated.RationaleNote | None = None) -> evaluated.EvaluatedStructuralInterpretation:
    if disposition not in ("accepted", "rejected", "undetermined"):
        raise AssertionError("invalid test disposition")
    return evaluated.create_evaluated_interpretation(
        source, candidate, evaluator_class="human", evaluator_label=label,
        evaluation_protocol_id="human-structural-adequacy", evaluation_protocol_version="1",
        disposition=disposition,
        rationale_evidence=(
            evaluated.RationaleCitation("syntax_node", candidate.scope.source_node_id),
            evaluated.RationaleCitation("token", candidate.scope.member_token_refs[0]),
        ),
        rationale_note=note or evaluated.RationaleNote("  \u03b1\r\n", "el"),
        event_key=event, supersedes=None if predecessor is None else predecessor.evaluation_id,
        prior_records=prior,
    )


def state(path: Path) -> tuple[object, ...]:
    with path.open("rb") as stream:
        digest = hashlib.sha256(stream.read()).hexdigest()
    with closing(fidelity.open_readonly(path)) as db:
        catalog = db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name").fetchall()
        return (path.stat().st_size, digest, db.execute("PRAGMA user_version").fetchone()[0],
                canonical(catalog))


def alter_record(path: Path, table: str, identity: str, text: str) -> None:
    """Raw SQL corruption in disposable files only; restore the exact trigger catalog."""
    with closing(sqlite3.connect(path)) as db:
        trigger = table + "_no_update"
        sql = db.execute("SELECT sql FROM sqlite_schema WHERE name=?", (trigger,)).fetchone()[0]
        db.execute(f"DROP TRIGGER {trigger}")
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(f"UPDATE {table} SET record_json=? WHERE {table}_id=?", (text, identity))
        db.execute(sql)
        db.commit()


def reordered_source(original: Path, target: Path) -> None:
    with closing(sqlite3.connect(original)) as src, closing(sqlite3.connect(target)) as dst:
        schema.bootstrap(dst)
        triggers = dst.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger'").fetchall()
        for name, _ in triggers:
            dst.execute(f'DROP TRIGGER "{name}"')
        dst.execute("PRAGMA foreign_keys=OFF")
        for (table,) in src.execute("SELECT name FROM sqlite_schema WHERE type='table'"):
            if table == "schema_version":
                continue
            rows = src.execute(f'SELECT * FROM "{table}" ORDER BY rowid DESC').fetchall()
            if rows:
                placeholders = ",".join("?" for _ in rows[0])
                dst.executemany(f'INSERT INTO "{table}" VALUES ({placeholders})', rows)
        for _, sql in triggers:
            dst.execute(sql)
        dst.commit()
        dst.execute("PRAGMA foreign_keys=ON")
        schema.validate_store(dst)


class Unit10FastTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit10-")
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.source = self.directory / "source.sqlite3"
        self.path = self.directory / "projection.sqlite3"
        build_amendment1_store(self.source)
        store.initialize_projection_store(self.path)
        self.appositions = derive(self.source, "MAT 1:1!3")
        self.clause = derive(self.source, REFS[0])[0]
        self.record = record_for(self.source, self.clause)

    def save_candidate(self, candidate: store.Candidate | None = None) -> None:
        store.store_candidate(self.path, self.clause if candidate is None else candidate,
                              source_db_path=self.source)

    def save_evaluation(self, record: evaluated.EvaluatedStructuralInterpretation | None = None) -> None:
        store.store_evaluation(self.path, self.record if record is None else record,
                               source_db_path=self.source)

    def test_01_schema_identity_strict_and_metadata(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("PRAGMA application_id").fetchone()[0], 0x4D553130)
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            self.assertEqual(db.execute("PRAGMA journal_mode").fetchone()[0], "delete")
            tables = db.execute("PRAGMA table_list").fetchall()
            self.assertEqual({row[1] for row in tables if row[-1] == 1},
                             {"candidate", "evaluation", "projection_metadata"})
            protocol, digest = db.execute(
                "SELECT store_protocol,ddl_sha256 FROM projection_metadata").fetchone()
            self.assertEqual(protocol, "macula.structural-interpretation-store.v1")
            self.assertEqual(digest, hashlib.sha256(store.DDL_PATH.read_text(encoding="utf-8").encode()).hexdigest())
        self.assertIsNone(store.verify_projection_store(self.path))

    def test_02_initialization_rejects_all_existing_files(self) -> None:
        for target in (self.path, self.source, self.directory / "empty", self.directory / "unknown"):
            if not target.exists():
                target.write_bytes(b"" if target.name == "empty" else b"unknown")
            before = target.read_bytes()
            with self.subTest(target=target), self.assertRaises(query.QueryError):
                store.initialize_projection_store(target)
            self.assertEqual(target.read_bytes(), before)

    def test_03_initialization_failure_is_removed(self) -> None:
        target = self.directory / "failed.sqlite3"
        with patch.object(store, "_ddl", return_value="CREATE TABLE partial(x); BAD SQL;"):
            with self.assertRaises(query.QueryError):
                store.initialize_projection_store(target)
        self.assertFalse(target.exists())
        self.assertFalse(list(self.directory.glob("failed.sqlite3-*")))
        store.initialize_projection_store(target)
        store.verify_projection_store(target)

    def test_04_unknown_and_source_never_open_writable(self) -> None:
        original_connect = sqlite3.connect
        uris: list[str] = []

        def connect(database: str, **kwargs: object) -> sqlite3.Connection:
            uris.append(database)
            return original_connect(database, **kwargs)

        other_source = self.directory / "equivalent-source.sqlite3"
        build_amendment1_store(other_source, pk_offset=100000)
        before = state(self.source)
        with patch.object(store.sqlite3, "connect", side_effect=connect):
            with self.assertRaises(query.QueryError):
                store.store_candidate(self.source, self.clause, source_db_path=other_source)
        self.assertFalse(any("mode=rw" in uri for uri in uris))
        self.assertEqual(state(self.source), before)
        for api in (store.get_candidate, store.list_evaluations_for_candidate):
            with self.assertRaises(query.QueryError):
                api(self.source, self.clause.candidate_id)

    def test_05_schema_and_version_drift(self) -> None:
        variants = ("PRAGMA user_version=2", "PRAGMA application_id=0",
                    "CREATE TABLE unexpected(x)", "DROP TRIGGER candidate_no_delete",
                    "CREATE INDEX unexpected ON candidate(record_json)")
        for index, sql in enumerate(variants):
            path = self.directory / f"drift-{index}.sqlite3"
            store.initialize_projection_store(path)
            with closing(sqlite3.connect(path)) as db:
                db.execute(sql)
                db.commit()
            with self.subTest(sql=sql), self.assertRaises(query.QueryError):
                store.verify_projection_store(path)
            with self.assertRaises(query.QueryError):
                store.get_candidate(path, ABSENT_CANDIDATE)
            with self.assertRaises(query.QueryError):
                store.store_candidate(path, self.clause, source_db_path=self.source)

    def test_06_metadata_hash_drift(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            sql = db.execute("SELECT sql FROM sqlite_schema WHERE name='metadata_no_update'").fetchone()[0]
            db.execute("DROP TRIGGER metadata_no_update")
            db.execute("UPDATE projection_metadata SET ddl_sha256='wrong'")
            db.execute(sql)
            db.commit()
        with self.assertRaises(query.QueryError):
            store.verify_projection_store(self.path)

    def test_07_candidate_roundtrip_all_families_every_field(self) -> None:
        for candidate in (*self.appositions, self.clause):
            self.save_candidate(candidate)
            loaded = store.get_candidate(self.path, candidate.candidate_id)
            self.assertIs(type(loaded), type(candidate))
            self.assertEqual(loaded, candidate)
            self.assertEqual(asdict(loaded), asdict(candidate))
            self.assertEqual(independent_candidate_id(loaded), candidate.candidate_id)
        store.verify_projection_store(self.path, self.source)

    def test_08_evaluation_roundtrip_every_field_and_disposition(self) -> None:
        for index, candidate in enumerate((*self.appositions, self.clause)):
            for disposition in ("accepted", "rejected", "undetermined"):
                record = record_for(self.source, candidate, event=f"round:{index}:{disposition}",
                                    disposition=disposition)
                self.save_evaluation(record)
                loaded = store.get_evaluation(self.path, record.evaluation_id)
                self.assertEqual(loaded, record)
                self.assertEqual(asdict(loaded), asdict(record))
                self.assertEqual(independent_evaluation_id(loaded), record.evaluation_id)
        store.verify_projection_store(self.path, self.source)

    def test_09_frozen_dtos_and_no_storage_ids(self) -> None:
        self.save_evaluation()
        loaded = store.get_evaluation(self.path, self.record.evaluation_id)
        self.assertIsNotNone(loaded)
        for value in (loaded, loaded.candidate, loaded.candidate.scope,
                      loaded.candidate.source_snapshot, loaded.rationale_note,
                      *loaded.rationale_evidence, *loaded.candidate.evidence):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, fields(value)[0].name, "changed")
        text = canonical(asdict(loaded))
        for forbidden in ('"rowid"', '"token_id"', '"node_id"', '"snapshot_id"',
                          '"file_id"', '"tree_id"', '"element_id"', '"book_id"'):
            self.assertNotIn(forbidden, text)

    def test_10_duplicates_are_idempotent(self) -> None:
        self.save_evaluation()
        before = state(self.path)
        self.save_candidate()
        self.save_evaluation()
        self.assertEqual(state(self.path), before)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM candidate").fetchone()[0], 1)
            self.assertEqual(db.execute("SELECT count(*) FROM evaluation").fetchone()[0], 1)

    def test_11_conflicting_candidate_id_never_overwrites(self) -> None:
        self.save_candidate()
        data = {"candidate_protocol": structural.IDENTITY_PROTOCOL, "candidate": asdict(self.clause)}
        data["candidate"]["source_snapshot"]["revision"] = "conflict"
        alter_record(self.path, "candidate", self.clause.candidate_id, canonical(data))
        before = state(self.path)
        with self.assertRaises(query.QueryError):
            self.save_candidate()
        self.assertEqual(state(self.path), before)
        with self.assertRaises(query.QueryError):
            store.verify_projection_store(self.path)

    def test_12_conflicting_evaluation_id_never_overwrites(self) -> None:
        self.save_evaluation()
        data = asdict(self.record)
        data["rationale_note"]["text"] = "conflicting human note"
        alter_record(self.path, "evaluation", self.record.evaluation_id, canonical(data))
        before = state(self.path)
        with self.assertRaises(query.QueryError):
            self.save_evaluation()
        self.assertEqual(state(self.path), before)
        with self.assertRaises(query.QueryError):
            store.get_evaluation(self.path, self.record.evaluation_id)

    def test_13_append_only_even_replace_recursive_off(self) -> None:
        self.save_evaluation()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("PRAGMA recursive_triggers=OFF")
            for table in ("candidate", "evaluation", "projection_metadata"):
                row = db.execute(f"SELECT * FROM {table}").fetchone()
                for sql, params in (
                    (f"DELETE FROM {table}", ()),
                    (f"UPDATE {table} SET {('singleton' if table == 'projection_metadata' else table + '_id')}="
                     f"{('singleton' if table == 'projection_metadata' else table + '_id')}", ()),
                    (f"INSERT OR REPLACE INTO {table} VALUES ({','.join('?' for _ in row)})", row),
                ):
                    with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                        db.execute(sql, params)
            db.rollback()
        store.verify_projection_store(self.path)

    def test_14_malformed_lookup_identities(self) -> None:
        for value in ("", "1", "SHA256:" + "a" * 64, "sha256:" + "A" * 64,
                      "sha256:" + "a" * 63, 1, None):
            for api in (store.get_candidate, store.list_evaluations_for_candidate):
                with self.subTest(value=value, api=api), self.assertRaises(query.QueryError):
                    api(self.path, value)
        for value in (self.clause.candidate_id, "", "eval-sha256:" + "g" * 64, None):
            with self.assertRaises(query.QueryError):
                store.get_evaluation(self.path, value)

    def test_15_absent_valid_identities(self) -> None:
        self.assertIsNone(store.get_candidate(self.path, ABSENT_CANDIDATE))
        self.assertIsNone(store.get_evaluation(self.path, ABSENT_EVALUATION))
        self.assertEqual(store.list_evaluations_for_candidate(self.path, ABSENT_CANDIDATE), frozenset())
        with self.assertRaises(query.QueryError):
            store.get_candidate(self.directory / "missing.sqlite3", ABSENT_CANDIDATE)

    def test_16_candidate_v1_stale_identity_gate(self) -> None:
        forged = replace(self.clause, source_snapshot=replace(self.clause.source_snapshot, revision="changed"))
        with self.assertRaisesRegex(query.QueryError, "does not recompute"):
            self.save_candidate(forged)
        self.assertIsNone(store.get_candidate(self.path, self.clause.candidate_id))

    def test_17_reidentified_envelope_requires_v2(self) -> None:
        self.assertIsInstance(self.clause, structural.ClauseStructureCandidate)
        widened = ("MAT 1:2!5", "MAT 1:2!6", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
        components = self.clause.payload.components
        forged = replace(
            self.clause, scope=replace(self.clause.scope, member_token_refs=widened),
            payload=replace(self.clause.payload, components=(
                components[0], components[1],
                replace(components[2], member_token_refs=("MAT 1:2!6", "MAT 1:2!8", "MAT 1:2!9")),
            )),
        )
        with self.assertRaises(query.QueryError):
            self.save_candidate(forged)
        forged = replace(forged, candidate_id=independent_candidate_id(forged))
        evaluated._verify_candidate(forged)
        with self.assertRaisesRegex(query.QueryError, "source-grounded"):
            self.save_candidate(forged)
        record = evaluated.EvaluatedStructuralInterpretation(
            self.record.record_protocol,
            evaluated.compute_evaluation_id(
                forged, evaluator_class="human", evaluator_label=self.record.evaluator_label,
                evaluation_protocol_id=self.record.evaluation_protocol_id,
                evaluation_protocol_version="1", disposition="undetermined",
                rationale_evidence=self.record.rationale_evidence, rationale_note=self.record.rationale_note,
                event_key=self.record.event_key,
            ), forged, "human", self.record.evaluator_label, self.record.evaluation_protocol_id,
            "1", "undetermined", self.record.rationale_evidence, self.record.rationale_note,
            self.record.event_key,
        )
        with self.assertRaisesRegex(query.QueryError, "source-grounded"):
            self.save_evaluation(record)

    def test_18_evaluation_v1_and_registry_gate(self) -> None:
        for name, value in (("evaluation_id", ABSENT_EVALUATION),
                            ("evaluator_class", "llm"), ("evaluation_protocol_version", "2"),
                            ("disposition", "preferred"), ("rationale_evidence", ())):
            copy = replace(self.record)
            object.__setattr__(copy, name, value)
            if name == "rationale_evidence":
                object.__setattr__(copy, "disposition", "accepted")
            with self.subTest(name=name), self.assertRaises(query.QueryError):
                self.save_evaluation(copy)

    def test_19_source_required_no_production_bypass(self) -> None:
        for api, value in ((store.store_candidate, self.clause), (store.store_evaluation, self.record)):
            with self.assertRaises(query.QueryError):
                api(self.path, value, source_db_path=None)
            with self.assertRaises(TypeError):
                api(self.path, value)
            for option in ("skip_validation", "trusted", "unsafe_insert"):
                with self.assertRaises(TypeError):
                    api(self.path, value, source_db_path=self.source, **{option: True})

    def test_20_supersession_and_predecessor_preserved(self) -> None:
        successor = record_for(self.source, self.clause, event="unit10:2", disposition="accepted",
                               predecessor=self.record, prior=(self.record,))
        self.save_evaluation()
        self.save_evaluation(successor)
        self.assertEqual(store.get_evaluation(self.path, self.record.evaluation_id), self.record)
        self.assertEqual(store.get_evaluation(self.path, successor.evaluation_id), successor)
        self.assertEqual(store.list_evaluations_for_candidate(self.path, self.clause.candidate_id),
                         frozenset((self.record, successor)))
        store.verify_projection_store(self.path, self.source)

    def test_21_missing_predecessor_rejected(self) -> None:
        successor = record_for(self.source, self.clause, event="unit10:2",
                               predecessor=self.record, prior=(self.record,))
        with self.assertRaisesRegex(query.QueryError, "predecessor not found"):
            self.save_evaluation(successor)
        self.assertIsNone(store.get_candidate(self.path, self.clause.candidate_id))

    def test_22_cross_candidate_or_evaluator_supersession(self) -> None:
        self.save_evaluation()
        for candidate, label in ((self.appositions[0], self.record.evaluator_label),
                                 (self.clause, "another-evaluator")):
            base = record_for(self.source, candidate, event="cross", label=label)
            values = {
                field.name: getattr(base, field.name) for field in fields(base)
                if field.name not in ("evaluation_id", "supersedes")
            }
            values["supersedes"] = self.record.evaluation_id
            dummy = replace(base)
            object.__setattr__(dummy, "supersedes", self.record.evaluation_id)
            values["evaluation_id"] = independent_evaluation_id(dummy)
            invalid = evaluated.EvaluatedStructuralInterpretation(**values)
            with self.assertRaisesRegex(query.QueryError, "same candidate|same evaluator"):
                self.save_evaluation(invalid)

    def test_23_self_and_malformed_supersession_rejected(self) -> None:
        for value in (self.record.evaluation_id, "bad", ABSENT_EVALUATION):
            invalid = replace(self.record)
            object.__setattr__(invalid, "supersedes", value)
            with self.assertRaises(query.QueryError):
                self.save_evaluation(invalid)

    def test_24_forks_and_opposing_judgments_coexist(self) -> None:
        self.save_evaluation()
        records = [self.record]
        for index, disposition in enumerate(("accepted", "rejected")):
            record = record_for(self.source, self.clause, event=f"fork:{index}",
                                disposition=disposition, predecessor=self.record, prior=(self.record,))
            self.save_evaluation(record)
            records.append(record)
        self.assertEqual(store.list_evaluations_for_candidate(self.path, self.clause.candidate_id),
                         frozenset(records))
        self.assertFalse(hasattr(store, "get_latest_evaluation"))

    def test_25_event_reuse_across_candidates_rejected(self) -> None:
        self.save_evaluation()
        other = record_for(self.source, self.appositions[0])
        before = state(self.path)
        with self.assertRaisesRegex(query.QueryError, "event_key reuse"):
            self.save_evaluation(other)
        self.assertEqual(state(self.path), before)
        self.assertIsNone(store.get_candidate(self.path, other.candidate.candidate_id))
        other_label = record_for(self.source, self.clause, label="different")
        self.save_evaluation(other_label)

    def test_26_corrupt_predecessor_rejected(self) -> None:
        self.save_evaluation()
        successor = record_for(self.source, self.clause, event="unit10:2",
                               predecessor=self.record, prior=(self.record,))
        data = asdict(self.record)
        data["rationale_note"]["text"] = "corrupted predecessor"
        alter_record(self.path, "evaluation", self.record.evaluation_id, canonical(data))
        with self.assertRaises(query.QueryError):
            self.save_evaluation(successor)

    def test_27_snapshot_change_preserves_old_history(self) -> None:
        self.save_evaluation()
        other = self.directory / "new-source.sqlite3"
        build_amendment1_store(other)
        with closing(sqlite3.connect(other)) as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA recursive_triggers=ON")
            triggers = db.execute("SELECT name,sql FROM sqlite_schema WHERE type='trigger' "
                                  "AND tbl_name='dataset_snapshot'").fetchall()
            for name, _ in triggers:
                db.execute(f'DROP TRIGGER "{name}"')
            db.execute("UPDATE dataset_snapshot SET revision=?", ("2" * 40,))
            for _, sql in triggers:
                db.execute(sql)
            db.commit()
            schema.validate_store(db)
        candidate = derive(other, REFS[0])[0]
        self.assertNotEqual(candidate.candidate_id, self.clause.candidate_id)
        store.store_candidate(self.path, candidate, source_db_path=other)
        record = record_for(other, candidate, event="snapshot:2")
        store.store_evaluation(self.path, record, source_db_path=other)
        self.assertEqual(store.get_evaluation(self.path, self.record.evaluation_id), self.record)
        self.assertEqual(store.get_candidate(self.path, candidate.candidate_id), candidate)
        store.verify_projection_store(self.path)
        with self.assertRaises(query.QueryError):
            store.verify_projection_store(self.path, self.source)
        with self.assertRaises(query.QueryError):
            store.verify_projection_store(self.path, other)

    def test_28_derivation_version_distinct_but_unregistered(self) -> None:
        candidate = self.appositions[0]
        changed = replace(candidate, derivation_version="2")
        changed = replace(changed, candidate_id=independent_candidate_id(changed))
        self.assertNotEqual(candidate.candidate_id, changed.candidate_id)
        self.save_candidate(candidate)
        with self.assertRaisesRegex(query.QueryError, "derivation"):
            self.save_candidate(changed)
        self.assertEqual(store.get_candidate(self.path, candidate.candidate_id), candidate)

    def test_29_pk_insertion_and_projection_row_allocation_independence(self) -> None:
        shifted = self.directory / "shifted.sqlite3"
        reordered = self.directory / "reordered.sqlite3"
        second = self.directory / "second-projection.sqlite3"
        build_amendment1_store(shifted, pk_offset=100000)
        reordered_source(shifted, reordered)
        store.initialize_projection_store(second)
        with closing(sqlite3.connect(self.source)) as a, closing(sqlite3.connect(reordered)) as b:
            for table, key in (("dataset_snapshot", "snapshot_id"), ("book", "book_id"),
                               ("source_file", "file_id"), ("tree", "tree_id"),
                               ("syntax_node", "node_id"), ("token", "token_id"),
                               ("xml_element", "element_id")):
                self.assertNotEqual(a.execute(f"SELECT {key} FROM {table}").fetchall(),
                                    b.execute(f"SELECT {key} FROM {table}").fetchall())
        left = (*self.appositions, self.clause)
        right = (*derive(reordered, "MAT 1:1!3"), *derive(reordered, REFS[0]))
        self.assertEqual(left, right)
        for candidate in left:
            self.save_candidate(candidate)
        for candidate in reversed(right):
            store.store_candidate(second, candidate, source_db_path=reordered)
        for candidate in left:
            self.assertEqual(store.get_candidate(self.path, candidate.candidate_id),
                             store.get_candidate(second, candidate.candidate_id))
        self.save_evaluation()
        same_record = record_for(reordered, right[-1])
        self.assertEqual(same_record, self.record)
        filler = record_for(reordered, right[0], event="pk:filler")
        store.store_evaluation(second, filler, source_db_path=reordered)
        store.store_evaluation(second, same_record, source_db_path=reordered)
        with closing(sqlite3.connect(self.path)) as a, closing(sqlite3.connect(second)) as b:
            self.assertNotEqual(a.execute("SELECT rowid FROM candidate WHERE candidate_id=?",
                                         (self.clause.candidate_id,)).fetchone(),
                                b.execute("SELECT rowid FROM candidate WHERE candidate_id=?",
                                         (self.clause.candidate_id,)).fetchone())
            self.assertNotEqual(a.execute("SELECT rowid FROM evaluation WHERE evaluation_id=?",
                                         (self.record.evaluation_id,)).fetchone(),
                                b.execute("SELECT rowid FROM evaluation WHERE evaluation_id=?",
                                         (self.record.evaluation_id,)).fetchone())
        self.assertEqual(store.get_evaluation(second, same_record.evaluation_id), self.record)
        store.verify_projection_store(second, reordered)

    def test_30_readonly_source_profile_enforced(self) -> None:
        original = query._connect_readonly
        profiles: list[tuple[int, int, int]] = []
        actions: list[int] = []

        def connect(path: Path) -> sqlite3.Connection:
            db = original(path)
            profiles.append(tuple(db.execute(f"PRAGMA {p}").fetchone()[0]
                                  for p in ("query_only", "foreign_keys", "recursive_triggers")))
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("CREATE TABLE prohibited_write(x)")
            db.execute("PRAGMA query_only=OFF")
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("CREATE TABLE prohibited_uri_write(x)")
            db.execute("PRAGMA query_only=ON")

            def authorize(action: int, *args: object) -> int:
                actions.append(action)
                return sqlite3.SQLITE_OK

            db.set_authorizer(authorize)
            return db

        before = state(self.source)
        with patch.object(query, "_connect_readonly", side_effect=connect):
            self.save_evaluation()
            store.verify_projection_store(self.path, self.source)
        self.assertTrue(profiles)
        self.assertEqual(set(profiles), {(1, 1, 1)})
        self.assertNotIn(sqlite3.SQLITE_ATTACH, actions)
        self.assertNotIn(sqlite3.SQLITE_INSERT, actions)
        self.assertNotIn(sqlite3.SQLITE_UPDATE, actions)
        self.assertNotIn(sqlite3.SQLITE_DELETE, actions)
        self.assertEqual(state(self.source), before)

    def test_31_same_file_and_hardlink_rejected(self) -> None:
        alias = self.directory / "source-alias.sqlite3"
        os.link(self.source, alias)
        before = state(self.source)
        for path in (self.source, alias):
            with self.assertRaisesRegex(query.QueryError, "physically separate"):
                store.store_candidate(path, self.clause, source_db_path=self.source)
            with self.assertRaises(query.QueryError):
                store.store_evaluation(path, self.record, source_db_path=self.source)
        self.assertEqual(state(self.source), before)

    def test_32_load_never_derives_or_evaluates(self) -> None:
        self.save_evaluation()
        with patch.object(structural, "derive_structural_candidates", side_effect=AssertionError("derive")), \
                patch.object(evaluated, "create_evaluated_interpretation", side_effect=AssertionError("evaluate")):
            self.assertEqual(store.get_candidate(self.path, self.clause.candidate_id), self.clause)
            self.assertEqual(store.get_evaluation(self.path, self.record.evaluation_id), self.record)
            self.assertEqual(store.list_evaluations_for_candidate(self.path, self.clause.candidate_id),
                             frozenset((self.record,)))
            store.verify_projection_store(self.path)
            with self.assertRaises(AssertionError):
                store.verify_projection_store(self.path, self.source)

    def test_33_noncanonical_unknown_duplicate_json_rejected(self) -> None:
        self.save_candidate()
        data = {"candidate_protocol": structural.IDENTITY_PROTOCOL, "candidate": asdict(self.clause)}
        variants = [
            json.dumps(data), canonical({**data, "score": 1}),
            '{"candidate":{},"candidate":{},"candidate_protocol":"macula.structural-candidate.v1"}',
            '{"candidate":NaN,"candidate_protocol":"macula.structural-candidate.v1"}',
            "not json", canonical({**data, "candidate_protocol": "unknown"}),
        ]
        for text in variants:
            alter_record(self.path, "candidate", self.clause.candidate_id, text)
            with self.subTest(text=text[:60]), self.assertRaises(query.QueryError):
                store.get_candidate(self.path, self.clause.candidate_id)

    def test_34_wrong_json_field_types_and_missing_fields_rejected(self) -> None:
        self.save_candidate()
        for mutation in ("missing", "unknown", "primitive", "array", "ordinal", "bool", "kind"):
            data = {"candidate_protocol": structural.IDENTITY_PROTOCOL, "candidate": asdict(self.clause)}
            candidate = data["candidate"]
            if mutation == "missing":
                del candidate["source_snapshot"]["revision"]
            elif mutation == "unknown":
                candidate["payload"]["actor"] = "invented"
            elif mutation == "primitive":
                candidate["source_snapshot"]["revision"] = 1
            elif mutation == "array":
                candidate["scope"]["member_token_refs"] = "MAT 1:2!5"
            elif mutation in ("ordinal", "bool"):
                candidate["payload"]["components"][0]["sibling_ordinal"] = "0" if mutation == "ordinal" else False
            else:
                candidate["candidate_kind"] = "unknown"
            alter_record(self.path, "candidate", self.clause.candidate_id, canonical(data))
            with self.subTest(mutation=mutation), self.assertRaises(query.QueryError):
                store.get_candidate(self.path, self.clause.candidate_id)

    def test_35_candidate_key_and_evaluation_echo_conflicts(self) -> None:
        self.save_evaluation()
        data = {"candidate_protocol": structural.IDENTITY_PROTOCOL, "candidate": asdict(self.clause)}
        data["candidate"]["candidate_id"] = ABSENT_CANDIDATE
        alter_record(self.path, "candidate", self.clause.candidate_id, canonical(data))
        with self.assertRaises(query.QueryError):
            store.get_candidate(self.path, self.clause.candidate_id)
        with self.assertRaises(query.QueryError):
            store.get_evaluation(self.path, self.record.evaluation_id)

    def test_36_relational_evaluation_echo_drift(self) -> None:
        self.save_evaluation()
        with closing(sqlite3.connect(self.path)) as db:
            sql = db.execute("SELECT sql FROM sqlite_schema WHERE name='evaluation_no_update'").fetchone()[0]
            db.execute("DROP TRIGGER evaluation_no_update")
            db.execute("UPDATE evaluation SET evaluator_label='wrong'")
            db.execute(sql)
            db.commit()
        with self.assertRaisesRegex(query.QueryError, "key/echo conflict"):
            store.get_evaluation(self.path, self.record.evaluation_id)

    def test_37_note_label_language_event_preserved_exactly(self) -> None:
        note = evaluated.RationaleNote(" \u03b1\u0301\r\n\t\U0001f4d6 ", "EL-x-Test")
        record = record_for(self.source, self.clause, label=" reviewer \u03b1 ",
                            event="Caller.Exact:Event-1", note=note)
        self.save_evaluation(record)
        loaded = store.get_evaluation(self.path, record.evaluation_id)
        self.assertEqual(loaded, record)
        self.assertEqual(loaded.rationale_note.text.encode(), note.text.encode())
        self.assertEqual(loaded.rationale_note.language, "EL-x-Test")
        self.assertEqual(loaded.evaluator_label, " reviewer \u03b1 ")
        self.assertEqual(loaded.event_key, "Caller.Exact:Event-1")

    def test_38_semantic_theological_confidence_fields_forbidden(self) -> None:
        forbidden = (
            "Actor", "Action", "Patient", "Event", "Result", "Identity", "Property",
            "Recipient", "semantic_role", "ontology", "theology", "doctrine", "canonical_truth",
            "confidence", "probability", "certainty", "score", "rank", "weight", "percentage", "priority",
        )
        self.save_evaluation()
        with closing(sqlite3.connect(self.path)) as db:
            columns = {row[1] for table in ("candidate", "evaluation", "projection_metadata")
                       for row in db.execute(f"PRAGMA table_info({table})")}
            self.assertFalse(columns.intersection(forbidden))
        for name in forbidden:
            with self.subTest(name=name), self.assertRaises(TypeError):
                store.store_evaluation(self.path, self.record, source_db_path=self.source, **{name: 1})
            data = asdict(self.record)
            data[name] = "forbidden"
            alter_record(self.path, "evaluation", self.record.evaluation_id, canonical(data))
            with self.assertRaises(query.QueryError):
                store.get_evaluation(self.path, self.record.evaluation_id)

    def test_39_verbless_and_exact_scope_synthetic(self) -> None:
        self.assertEqual(len(self.appositions), 3)
        for candidate in self.appositions:
            self.assertIs(type(candidate), structural.StructuralCandidate)
            self.save_candidate(candidate)
            self.assertEqual(store.get_candidate(self.path, candidate.candidate_id), candidate)
            self.assertNotIn("source_rule", asdict(candidate.payload))
        self.save_evaluation()
        loaded = store.get_evaluation(self.path, self.record.evaluation_id).candidate
        self.assertEqual(loaded.scope.member_token_refs, REFS)
        self.assertEqual([c.member_token_refs for c in loaded.payload.components],
                         [("MAT 1:2!5",), ("MAT 1:2!7",), ("MAT 1:2!8", "MAT 1:2!9")])
        self.assertNotIn("MAT 1:2!6", loaded.scope.member_token_refs)

    def test_40_cross_process_durability(self) -> None:
        self.save_evaluation()
        code = (
            "import json,sys; from dataclasses import asdict; "
            "from scripts.projection_store import get_evaluation,verify_projection_store; "
            "verify_projection_store(sys.argv[1]); "
            "print(json.dumps(asdict(get_evaluation(sys.argv[1],sys.argv[2])),sort_keys=True))"
        )
        output = subprocess.check_output(
            [sys.executable, "-B", "-c", code, str(self.path), self.record.evaluation_id],
            cwd=ROOT, text=True,
        )
        self.assertEqual(json.loads(output), json.loads(canonical(asdict(self.record))))

    def test_41_connections_close_on_success_and_error(self) -> None:
        connections: list[sqlite3.Connection] = []
        original_connect = sqlite3.connect

        def connect(*args: object, **kwargs: object) -> sqlite3.Connection:
            db = original_connect(*args, **kwargs)
            connections.append(db)
            return db

        with patch.object(store.sqlite3, "connect", side_effect=connect):
            self.save_evaluation()
            store.get_evaluation(self.path, self.record.evaluation_id)
            store.verify_projection_store(self.path, self.source)
            successor = record_for(self.source, self.clause, event="closure:2",
                                   predecessor=self.record, prior=(self.record,))
            other = self.directory / "empty-projection.sqlite3"
            store.initialize_projection_store(other)
            with self.assertRaises(query.QueryError):
                store.store_evaluation(other, successor, source_db_path=self.source)
            with self.assertRaises(query.QueryError):
                store.get_candidate(self.source, self.clause.candidate_id)
            with patch.object(store, "_ddl", return_value="BAD SQL"):
                with self.assertRaises(query.QueryError):
                    store.initialize_projection_store(self.directory / "failed.sqlite3")
        self.assertTrue(connections)
        for db in connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")

    def test_42_transaction_rolls_back_after_candidate_insertion(self) -> None:
        original = store._insert_candidate

        def interrupted(db: sqlite3.Connection, candidate: store.Candidate) -> None:
            original(db, candidate)
            raise sqlite3.OperationalError("simulated append failure")

        with patch.object(store, "_insert_candidate", side_effect=interrupted):
            with self.assertRaisesRegex(query.QueryError, "simulated append failure"):
                self.save_evaluation()
        self.assertIsNone(store.get_candidate(self.path, self.clause.candidate_id))
        self.assertIsNone(store.get_evaluation(self.path, self.record.evaluation_id))
        self.save_evaluation()

    def test_43_projection_connection_profiles(self) -> None:
        with store._open(self.path) as db:
            self.assertEqual(db.execute("PRAGMA query_only").fetchone()[0], 1)
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("CREATE TABLE no_write(x)")
        with store._open(self.path, write=True) as db:
            self.assertEqual(db.execute("PRAGMA query_only").fetchone()[0], 0)
            self.assertEqual(db.execute("PRAGMA synchronous").fetchone()[0], 2)
            self.assertEqual(db.execute("PRAGMA busy_timeout").fetchone()[0], 5000)
            self.assertEqual(db.execute("PRAGMA foreign_keys").fetchone()[0], 1)
            self.assertEqual(db.execute("PRAGMA recursive_triggers").fetchone()[0], 1)

    def test_44_journal_drift_and_invalid_paths(self) -> None:
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute("PRAGMA journal_mode=WAL").fetchone()[0], "wal")
        with self.assertRaises(query.QueryError):
            store.verify_projection_store(self.path)
        for value in ("", " ", None, 1):
            with self.assertRaises(query.QueryError):
                store.initialize_projection_store(value)

    def test_45_schema_ddl_hash_change_fails_closed(self) -> None:
        with patch.object(store, "_ddl", return_value=store.DDL_PATH.read_text(encoding="utf-8") + "\n"):
            with self.assertRaisesRegex(query.QueryError, "hash drift"):
                store.verify_projection_store(self.path)


_MATTHEW = Path(os.environ.get("MACULA_MATTHEW_DB", str(ROOT / "sblgnt-matthew.sqlite3")))


@unittest.skipUnless(os.environ.get("MACULA_UNIT10_INTEGRATION") == "1" and _MATTHEW.is_file(),
                     "opt-in read-only existing full-Matthew integration")
class Unit10MatthewIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.before = state(_MATTHEW)

    @classmethod
    def tearDownClass(cls) -> None:
        if state(_MATTHEW) != cls.before:
            raise AssertionError("Unit 10 changed authoritative Matthew database")

    def setUp(self) -> None:
        directory = TemporaryDirectory(prefix="macula-unit10-matthew-")
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "projection.sqlite3"
        store.initialize_projection_store(self.path)

    def test_46_real_svo_candidate_fixture_and_independent_identity(self) -> None:
        fixture = json.loads((ROOT / "fixtures" / "matthew-1-2-svo-candidate.expected.json").read_text())
        for ref in REFS:
            candidate = derive(_MATTHEW, ref)[0]
            self.assertEqual(candidate.candidate_id, SVO_ID)
            store.store_candidate(self.path, candidate, source_db_path=_MATTHEW)
            loaded = store.get_candidate(self.path, SVO_ID)
            self.assertEqual(loaded, candidate)
            actual = json.loads(canonical(asdict(loaded)))
            for name in ("source_snapshot", "scope", "evidence", "payload", "status",
                         "candidate_id", "candidate_kind", "derivation_kind", "derivation_version"):
                self.assertEqual(actual[name], fixture[name])
            self.assertEqual(independent_candidate_id(loaded), SVO_ID)
            self.assertEqual(loaded.scope.member_token_refs, REFS)
            self.assertFalse(any("MAT 1:2!6" in c.member_token_refs for c in loaded.payload.components))
        self.assertEqual(derive(_MATTHEW, "MAT 1:2!6"), ())
        store.verify_projection_store(self.path, _MATTHEW)

    def test_47_real_human_and_supersession_literal_vectors(self) -> None:
        candidate = derive(_MATTHEW, REFS[0])[0]
        record = record_for(_MATTHEW, candidate)
        self.assertEqual("eval-sha256:" + hashlib.sha256(EVAL_BYTES).hexdigest(), EVAL_ID)
        self.assertEqual(record.evaluation_id, EVAL_ID)
        successor = record_for(_MATTHEW, candidate, event="unit10:2", disposition="accepted",
                               predecessor=record, prior=(record,))
        self.assertEqual(successor.evaluation_id, SUCCESSOR_ID)
        for item in (record, successor):
            store.store_evaluation(self.path, item, source_db_path=_MATTHEW)
            loaded = store.get_evaluation(self.path, item.evaluation_id)
            self.assertEqual(loaded, item)
            self.assertEqual(independent_evaluation_id(loaded), item.evaluation_id)
            self.assertEqual(independent_candidate_id(loaded.candidate), SVO_ID)
        self.assertEqual(store.list_evaluations_for_candidate(self.path, SVO_ID),
                         frozenset((record, successor)))
        store.verify_projection_store(self.path, _MATTHEW)

    def test_48_real_verbless_apposition_lossless(self) -> None:
        candidates = derive(_MATTHEW, "MAT 1:1!3")
        self.assertEqual(tuple(c.candidate_id for c in candidates), (
            "sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c",
            "sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f",
            "sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220",
        ))
        self.assertTrue(any(node.cl_type == "Verbless"
                            for node in query.get_ancestors_by_token(_MATTHEW, "MAT 1:1!3")))
        verse = query.get_verse(_MATTHEW, "MAT", 1, 1)
        self.assertEqual(len(verse.tokens), 8)
        self.assertFalse(any(token.cat == "verb" for token in verse.tokens))
        for index, candidate in enumerate(candidates):
            self.assertIs(type(candidate), structural.StructuralCandidate)
            record = record_for(_MATTHEW, candidate, event=f"verbless:{index}")
            store.store_evaluation(self.path, record, source_db_path=_MATTHEW)
            self.assertEqual(store.get_evaluation(self.path, record.evaluation_id), record)
            self.assertEqual(independent_candidate_id(candidate), candidate.candidate_id)
        store.verify_projection_store(self.path, _MATTHEW)


if __name__ == "__main__":
    unittest.main()
