"""Disposable schema-v2 store for the Unit 8 Amendment 1 tests.

The store reproduces, with the real Matthew node identifiers, the two source-facing
structures that Amendment 1 evaluates: the nested Matthew 1:1 Np-Appos chain and the
frozen Matthew 1:2 S-V-O clause (with its interior connector token 6 present but a
member of neither the anchor nor any component).

It is populated through the Unit 2 ``SchemaFixture`` and the real schema bootstrap and
``validate_store``. Its snapshot is the synthetic Unit 2 snapshot, because
``source_file.sha256`` must equal the SHA-256 of the stored bytes and the real Matthew
bytes are not stored here. Candidate IDs in this store therefore differ from the frozen
real-snapshot IDs only through ``source_snapshot``; ``frozen_candidate_id`` recomputes
the frozen real-snapshot IDs from the derived candidate with an independent encoder.
"""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from xml.sax.saxutils import escape

from scripts import source_schema as schema
from scripts import structural_candidates as candidates
from tests.test_unit2 import SchemaFixture, tag


FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "matthew-1-2-svo-candidate.expected.json"

APPOSITION_FROZEN_IDS = (
    "sha256:ca5dc5188ebf612545856de8bbf2a407783bb6afffbb892bec8d6326d4c05c3c",
    "sha256:ba4de096a1622e6513cf429801a5d9f9035fc25f971f75fc2b0b196a650f4c1f",
    "sha256:af5656c7b793c565b841a91302b752c4cc7283f86d2232fc34aa96ebc6d78220",
)
APPOSITION_LOOKUP = "MAT 1:1!3"
SVO_LOOKUPS = ("MAT 1:2!5", "MAT 1:2!7", "MAT 1:2!8", "MAT 1:2!9")
EXCLUDED_TOKEN = "MAT 1:2!6"

SVO_ANCHOR = "400010020050040"

_ATTRS = {
    "root:opaque": {"Cat": "S"},
    "cl:opaque": {"Cat": "CL", "Rule": "P2CL", "ClType": "Verbless"},
    "400010010010011": {"Cat": "noun", "ref": "MAT 1:1!1"},
    "400010010020011": {"Cat": "noun", "ref": "MAT 1:1!2"},
    "400010010030060": {"Cat": "np", "Rule": "Np-Appos"},
    "400010010030040": {"Cat": "np", "Rule": "Np-Appos"},
    "400010010030020": {"Cat": "np", "Rule": "Np-Appos"},
    "400010010030011": {"Cat": "noun", "ref": "MAT 1:1!3"},
    "400010010040011": {"Cat": "noun", "ref": "MAT 1:1!4"},
    "400010010050020": {"Cat": "np"},
    "400010010050011": {"Cat": "noun", "ref": "MAT 1:1!5"},
    "400010010060011": {"Cat": "noun", "ref": "MAT 1:1!6"},
    "400010010070020": {"Cat": "np"},
    "400010010070011": {"Cat": "noun", "ref": "MAT 1:1!7"},
    "400010010080011": {"Cat": "noun", "ref": "MAT 1:1!8"},
    "400010020060011": {"Cat": "conj", "ref": "MAT 1:2!6"},
    SVO_ANCHOR: {"Cat": "CL", "Rule": "S-V-O", "Head": "1", "Start": "5", "End": "8"},
    "400010020050012": {"Cat": "S", "ref": "MAT 1:2!5"},
    "400010020070012": {"Cat": "V", "ref": "MAT 1:2!7", "Voice": "Passive", "Frame": "A1 A2"},
    "400010020080021": {"Cat": "O"},
    "400010020080011": {"Cat": "OC", "ref": "MAT 1:2!8"},
    "400010020090011": {"Cat": "O2", "ref": "MAT 1:2!9"},
}
_CHILDREN = {
    "root:opaque": ["cl:opaque", "400010020060011", SVO_ANCHOR],
    "cl:opaque": ["400010010010011", "400010010020011", "400010010030060"],
    "400010010030060": ["400010010030040", "400010010070020"],
    "400010010030040": ["400010010030020", "400010010050020"],
    "400010010030020": ["400010010030011", "400010010040011"],
    "400010010050020": ["400010010050011", "400010010060011"],
    "400010010070020": ["400010010070011", "400010010080011"],
    SVO_ANCHOR: ["400010020050012", "400010020070012", "400010020080021"],
    "400010020080021": ["400010020080011", "400010020090011"],
}


class FixtureConstructionError(AssertionError):
    """The disposable store does not reproduce the expected source-facing candidates."""


def frozen_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def frozen_candidate_id(candidate: object) -> str:
    """Independently encode a derived candidate under the frozen real source snapshot."""
    snapshot = list(frozen_fixture()["source_snapshot"].values())  # type: ignore[union-attr]
    if candidate.candidate_kind == "clause-structure":  # type: ignore[attr-defined]
        payload = candidate.payload  # type: ignore[attr-defined]
        payload_value: list[object] = [
            payload.anchor_source_node_id, payload.source_rule, payload.source_head_raw,
            [[c.component_role, c.source_cat, c.sibling_ordinal, c.source_node_id,
              list(c.member_token_refs)] for c in payload.components],
        ]
    else:
        payload = candidate.payload  # type: ignore[attr-defined]
        payload_value = [payload.anchor_source_node_id, list(payload.child_source_node_ids)]
    value = [
        "macula.structural-candidate.v1", snapshot, candidate.candidate_kind,  # type: ignore[attr-defined]
        candidate.derivation_kind, candidate.derivation_version,  # type: ignore[attr-defined]
        [candidate.scope.source_node_id, list(candidate.scope.member_token_refs)],  # type: ignore[attr-defined]
        [[e.role, e.kind, e.source_node_id] for e in candidate.evidence],  # type: ignore[attr-defined]
        payload_value,
    ]
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def build_amendment1_store(path: str | Path, *, pk_offset: int = 0) -> None:
    """Create one validated disposable store at ``path``; remove it if construction fails."""
    target = Path(path)
    if target.exists() and target.stat().st_size:
        raise FixtureConstructionError(f"refusing to build over an existing database: {target}")
    db = sqlite3.connect(target)
    try:
        _populate(db, pk_offset)
        db.commit()
    except BaseException:
        db.close()
        target.unlink(missing_ok=True)
        raise
    db.close()
    try:
        _self_validate(target)
    except BaseException:
        target.unlink(missing_ok=True)
        raise


def _populate(db: sqlite3.Connection, offset: int) -> None:
    schema.bootstrap(db)
    fixture = SchemaFixture(db, offset)
    attrs = {identity: {**values, "nodeId": identity} for identity, values in _ATTRS.items()}

    def node_xml(identity: str) -> str:
        content = "".join(node_xml(child) for child in _CHILDREN.get(identity, []))
        return tag("Node", attrs[identity], content or escape("surface-" + identity))

    coordinates = {
        identity: tuple(int(part) for part in re.fullmatch(r"MAT 1:([0-9]+)!([0-9]+)", values["ref"]).groups())
        for identity, values in attrs.items() if "ref" in values
    }
    canonical = sorted(coordinates, key=coordinates.__getitem__)
    sentence_ref = "MAT 1:1!1-1:2!9"
    raw = tag("Sentences", {}, tag("Sentence", {"ref": sentence_ref},
              tag("Trees", {}, tag("Tree", {}, node_xml("root:opaque"))))).encode("utf-8")
    file_id, book_id = fixture.archive(raw)
    document = fixture.element(file_id, None, "Sentences")
    sentence_element = fixture.element(file_id, document, "Sentence")
    fixture.attribute(sentence_element, "ref", sentence_ref)
    sentence = fixture.insert("sentence", {
        "sentence_id": offset + 1, "file_id": file_id, "book_id": book_id,
        "element_id": sentence_element, "ordinal": 0, "ref_raw": sentence_ref,
    })
    wrapper = fixture.element(file_id, sentence_element, "Trees")
    tree_element = fixture.element(file_id, wrapper, "Tree")
    tree = fixture.insert("tree", {
        "tree_id": offset + 1, "sentence_id": sentence, "element_id": tree_element, "ordinal": 0,
    })
    identities = list(attrs)
    traversal: list[str] = []

    def add_node(identity: str, parent_element: int, parent: int | None, ordinal: int) -> None:
        element = fixture.element(file_id, parent_element, "Node")
        fixture.attributes(element, attrs[identity])
        index = identities.index(identity)
        node = fixture.node(tree, element, parent, ordinal, attrs[identity],
                            {"node_id": offset + 1000 + (index if offset else -index)})
        if identity in coordinates:
            text = "surface-" + identity
            fixture.content(file_id, element, "text", text)
            verse, word = coordinates[identity]
            fixture.token(
                tree, book_id, node, text, attrs[identity],
                traversal=len(traversal), canonical=canonical.index(identity), verse=verse, word=word,
                overrides={"token_id": offset + 10000 + (word + 100 * verse if offset else -(word + 100 * verse))},
            )
            traversal.append(identity)
        for sibling, child in enumerate(_CHILDREN.get(identity, [])):
            add_node(child, element, node, sibling)

    add_node("root:opaque", tree_element, None, 0)
    fixture.memberships()
    schema.validate_store(db)


def _derive(path: Path, token_ref: str) -> tuple[object, ...]:
    result = candidates.derive_structural_candidates(path, token_ref)
    if result is None:
        raise FixtureConstructionError(f"{token_ref} is unknown to the disposable store")
    return result


def _self_validate(path: Path) -> None:
    expected = frozen_fixture()
    apposition = tuple(item for item in _derive(path, APPOSITION_LOOKUP)
                       if item.candidate_kind == "apposition")  # type: ignore[attr-defined]
    if tuple(frozen_candidate_id(item) for item in apposition) != APPOSITION_FROZEN_IDS:
        raise FixtureConstructionError("Apposition candidates do not reproduce the frozen identities")
    reference = None
    for token_ref in SVO_LOOKUPS:
        clauses = tuple(item for item in _derive(path, token_ref)
                        if item.candidate_kind == "clause-structure")  # type: ignore[attr-defined]
        if len(clauses) != 1:
            raise FixtureConstructionError(f"{token_ref} must expose exactly one S-V-O candidate")
        if reference is None:
            reference = clauses[0]
        elif clauses[0] != reference:
            raise FixtureConstructionError(f"{token_ref} exposes a different S-V-O candidate")
    assert reference is not None
    actual = asdict(reference)
    for name in ("candidate_kind", "derivation_kind", "derivation_version", "status",
                 "scope", "evidence", "payload"):
        if json.loads(json.dumps(actual[name])) != expected[name]:
            raise FixtureConstructionError(f"S-V-O candidate field differs from the frozen fixture: {name}")
    if frozen_candidate_id(reference) != expected["candidate_id"]:
        raise FixtureConstructionError("S-V-O candidate does not reproduce the frozen identity")
    if any(item.candidate_kind == "clause-structure"  # type: ignore[attr-defined]
           for item in _derive(path, EXCLUDED_TOKEN)):
        raise FixtureConstructionError("token 6 must not expose the S-V-O candidate")
