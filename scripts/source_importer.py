from dataclasses import dataclass, field
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
from tempfile import TemporaryDirectory
import time

from scripts import source_schema as schema
from scripts import verify_unit1 as unit1
from scripts.occurrence_locator import SCHEME, SCHEME_VERSION, encode_locator
from scripts.xmlreader_bridge import ImportFailure, reader_bridge, reader_events, string, strings


XML_NS = "http://www.w3.org/XML/1998/namespace"
NODE_FIELDS = {
    "nodeId": "upstream_node_id", "Id": "id_raw", "Cat": "cat", "Rule": "rule",
    "ClType": "cl_type", "Start": "start_raw", "End": "end_raw", "Head": "head_raw",
    "Length": "length_raw",
}
TOKEN_FIELDS = {
    "xml:id": "xml_id", "morphId": "morph_id", "ref": "ref_raw", "Unicode": "unicode_raw",
    "NormalizedForm": "normalized_form", "UnicodeLemma": "unicode_lemma", "Language": "language_raw",
    "Case": "case_raw", "Gender": "gender_raw", "Number": "number_raw", "Person": "person_raw",
    "Tense": "tense_raw", "Voice": "voice_raw", "Mood": "mood_raw", "Type": "type_raw",
    "Degree": "degree_raw", "HasDet": "has_det_raw", "FunctionalTag": "functional_tag",
    "FormalTag": "formal_tag", "StrongNumber": "strong_number", "English": "english",
    "Mandarin": "mandarin", "Gloss": "gloss", "LexDomain": "lex_domain_raw", "LN": "ln_raw",
    "Frame": "frame_raw", "Ref": "referent_raw", "SubjRef": "subject_referent_raw",
    "Notes": "notes_raw", "LowfatException": "lowfat_exception_raw", "status": "status_raw",
}
IMPORT_CONTRACT = unit1.PROJECT_ROOT / "contracts" / "source-importer.unit3.json"
PROTECTED_ROOTS = (unit1.UPSTREAM_ROOT, Path(r"C:\Projects\bible-research-merged"))


def artifact_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest().upper()


def coordinates(value: str | None) -> tuple[int, int, int]:
    match = re.fullmatch(r"MAT ([1-9][0-9]*):([1-9][0-9]*)!([1-9][0-9]*)", value or "")
    if match is None:
        raise ImportFailure(f"invalid authorized Matthew leaf ref: {value!r}")
    chapter, verse, word = match.groups()
    return int(chapter), int(verse), int(word)


def insert(db: sqlite3.Connection, table: str, values: dict[str, object]) -> int:
    cursor = db.execute(
        f"INSERT INTO {table} ({','.join(values)}) VALUES ({','.join('?' for _ in values)})",
        tuple(values.values()),
    )
    if cursor.lastrowid is None:
        raise ImportFailure(f"{table} insert did not produce a row identity")
    return cursor.lastrowid


@dataclass
class Element:
    element_id: int
    name: tuple[str, ...]
    path: list[tuple[str, str, int]]
    attrs: dict[str, str]
    sibling: int
    tree: int | None
    sentence: int | None
    node: int | None = None
    node_children: int = 0
    content_count: int = 0
    child_count: int = 0
    same_names: dict[tuple[str, str], int] = field(default_factory=dict)
    direct_text: list[str] = field(default_factory=list)


@dataclass
class Leaf:
    element: Element
    traversal: int
    ancestry: list[int]


def _populate(db: sqlite3.Connection, raw: bytes, assembly: Path) -> str:
    """Internal transaction body; production callers must first verify the pinned source."""
    manifest = hashlib.sha256(unit1.CONTRACT_PATH.read_bytes()).hexdigest().upper()
    insert(db, "dataset_snapshot", {
        "snapshot_id": 1, "source_family": "MACULA Greek", "edition": "SBLGNT",
        "repository_uri": "https://github.com/Clear-Bible/macula-greek",
        "revision": unit1.REVISION, "manifest_sha256": manifest,
    })
    insert(db, "book", {"book_id": 1, "snapshot_id": 1, "source_book_code": "MAT", "book_ordinal": 1})
    insert(db, "source_file", {
        "file_id": 1, "snapshot_id": 1, "book_id": 1, "relative_path": unit1.RELATIVE_PATH,
        "source_format": "nodes", "original_bytes": raw,
        "sha256": hashlib.sha256(raw).hexdigest().upper(), "byte_size": len(raw),
        "encoding_evidence": "Authoritative XmlReader decoded the original byte stream; declaration/BOM are archived.",
    })
    stack: list[Element] = []
    document_count = 0
    sentences = 0
    tree_ordinals: dict[int, int] = {}
    tree_leaves: dict[int, list[Leaf]] = {}
    runtime = ""
    tokens = 0

    def content(kind: str, value: str | None = None, child: int | None = None,
                target: str | None = None) -> None:
        nonlocal document_count
        owner = stack[-1] if stack else None
        ordinal = owner.content_count if owner else document_count
        insert(db, "xml_content", {
            "file_id": 1, "owner_element_id": owner.element_id if owner else None,
            "ordinal": ordinal, "kind": kind, "child_element_id": child,
            "value": value, "pi_target": target,
        })
        if owner:
            owner.content_count += 1
            if kind in ("text", "cdata") and value is not None:
                owner.direct_text.append(value)
        else:
            document_count += 1

    for event in reader_events(raw, assembly):
        kind = string(event[0])
        if kind == "profile":
            if runtime or event[1:3] != [1, "System.Xml.XmlReader"]:
                raise ImportFailure("unexpected authoritative reader profile")
            runtime = string(event[3])
        elif kind == "start":
            if not runtime:
                raise ImportFailure("reader facts arrived before profile")
            name = strings(event[1], 4)
            attributes = [strings(value, 5) for value in unit1.list_value(event[2], "reader attributes")]
            parent = stack[-1] if stack else None
            same = (name[0], name[1])
            ordinal = parent.same_names.get(same, 0) + 1 if parent else 1
            path = [*(parent.path if parent else []), (name[0], name[1], ordinal)]
            sibling = parent.child_count if parent else 0
            element_id = insert(db, "xml_element", {
                "file_id": 1, "parent_element_id": parent.element_id if parent else None,
                "namespace_uri": name[0], "local_name": name[1], "prefix": name[2],
                "qualified_name": name[3], "sibling_ordinal": sibling,
                "locator_scheme": SCHEME, "locator_version": SCHEME_VERSION,
                "locator": encode_locator(path), "diagnostic_line": event[3], "diagnostic_column": event[4],
            })
            content("element", child=element_id)
            attrs: dict[str, str] = {}
            for order, attr in enumerate(attributes):
                insert(db, "xml_attribute", {
                    "element_id": element_id, "ordinal": order, "namespace_uri": attr[0],
                    "local_name": attr[1], "prefix": attr[2], "qualified_name": attr[3], "value": attr[4],
                })
                if not attr[0]:
                    attrs[attr[1]] = attr[4]
                elif attr[0] == XML_NS and attr[1] == "id":
                    attrs["xml:id"] = attr[4]
            element = Element(
                element_id, name, path, attrs, sibling,
                parent.tree if parent else None, parent.sentence if parent else None,
            )
            if parent:
                parent.same_names[same] = ordinal
                parent.child_count += 1
            if name[:2] == ("", "Sentence"):
                element.sentence = insert(db, "sentence", {
                    "file_id": 1, "book_id": 1, "element_id": element_id,
                    "ordinal": sentences, "ref_raw": attrs.get("ref"),
                })
                sentences += 1
            elif name[:2] == ("", "Tree"):
                if element.sentence is None:
                    raise ImportFailure("Tree lacks a containing source Sentence")
                order = tree_ordinals.get(element.sentence, 0)
                element.tree = insert(db, "tree", {
                    "sentence_id": element.sentence, "element_id": element_id, "ordinal": order,
                })
                tree_ordinals[element.sentence] = order + 1
                tree_leaves[element.tree] = []
            elif name[:2] == ("", "Node"):
                if element.tree is None:
                    raise ImportFailure("Node lacks a containing source Tree")
                parent_node = parent.node if parent else None
                node_sibling = parent.node_children if parent_node is not None and parent else sibling
                element.node = insert(db, "syntax_node", {
                    "tree_id": element.tree, "element_id": element_id, "parent_node_id": parent_node,
                    "sibling_ordinal": node_sibling,
                    **{column: attrs.get(source) for source, column in NODE_FIELDS.items()},
                })
                if parent_node is not None and parent:
                    parent.node_children += 1
            stack.append(element)
        elif kind == "end":
            if not stack:
                raise ImportFailure("reader end without an open source element")
            element = stack.pop()
            if element.node is not None and element.node_children == 0:
                if element.tree is None:
                    raise ImportFailure("leaf lacks Tree")
                leaves = tree_leaves[element.tree]
                ancestry = [frame.node for frame in [*stack, element] if frame.node is not None]
                leaves.append(Leaf(element, len(leaves), ancestry))
            if element.name[:2] == ("", "Tree") and element.tree is not None:
                leaves = tree_leaves.pop(element.tree)
                ordered = sorted(leaves, key=lambda leaf: coordinates(leaf.element.attrs.get("ref")))
                for canonical, leaf in enumerate(ordered):
                    chapter, verse, word = coordinates(leaf.element.attrs.get("ref"))
                    tokens += 1
                    token_id = insert(db, "token", {
                        "token_id": -tokens, "tree_id": element.tree, "book_id": 1,
                        "node_id": leaf.element.node, "source_direct_text": "".join(leaf.element.direct_text),
                        "tree_leaf_ordinal": leaf.traversal, "canonical_ordinal": canonical,
                        "chapter": chapter, "verse": verse, "verse_token_ordinal": word,
                        **{column: leaf.element.attrs.get(source) for source, column in TOKEN_FIELDS.items()},
                    })
                    for node_id in reversed(leaf.ancestry):
                        db.execute("INSERT INTO node_token_membership VALUES(?,?,?)",
                                   (node_id, token_id, element.tree))
        elif kind in ("text", "cdata", "comment", "pi"):
            content(kind, string(event[1]), target=string(event[2]) if kind == "pi" else None)
        elif kind == "complete":
            if stack or tree_leaves or not runtime:
                raise ImportFailure("incomplete source occurrence import")
        else:
            raise ImportFailure(f"unknown authoritative reader event {kind}")
    return runtime


def safe_output(path: Path) -> Path:
    resolved = path.resolve()
    if any(resolved == root.resolve() or root.resolve() in resolved.parents for root in PROTECTED_ROOTS):
        raise ImportFailure("output may not target a protected repository")
    if resolved.exists():
        raise ImportFailure("output already exists; publication never overwrites")
    if not resolved.parent.is_dir():
        raise ImportFailure("output parent must already exist")
    return resolved


def build_matthew(output: Path, assembly: Path) -> dict[str, object]:
    from scripts.source_fidelity import verify_fidelity

    started = time.perf_counter()
    output = safe_output(output)
    raw = unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH))
    identities = {
        "source_revision": unit1.REVISION, "source_path": unit1.RELATIVE_PATH,
        "source_sha256": hashlib.sha256(raw).hexdigest().upper(), "source_bytes": len(raw),
        "source_manifest_sha256": hashlib.sha256(unit1.CONTRACT_PATH.read_bytes()).hexdigest().upper(),
        "schema_sha256": artifact_sha256(schema.DDL_PATH),
        "parser_contract_sha256": artifact_sha256(schema.PARSER_PATH),
        "locator_contract_sha256": artifact_sha256(schema.LOCATOR_PATH),
        "importer_contract_sha256": artifact_sha256(IMPORT_CONTRACT),
        "importer_sha256": artifact_sha256(Path(__file__)),
        "reader_bridge_sha256": artifact_sha256(unit1.PROJECT_ROOT / "scripts" / "xmlreader_bridge.py"),
        "reader_sha256": artifact_sha256(unit1.PROJECT_ROOT / "parsers" / "XmlReaderBridge" / "Program.cs"),
        "fidelity_verifier_sha256": artifact_sha256(unit1.PROJECT_ROOT / "scripts" / "source_fidelity.py"),
    }
    with TemporaryDirectory(prefix="macula-unit3-build-", dir=output.parent) as directory:
        candidate = Path(directory) / "candidate.sqlite3"
        db = sqlite3.connect(candidate)
        try:
            schema.bootstrap(db)
            db.execute("BEGIN IMMEDIATE")
            runtime = _populate(db, raw, assembly)
            evidence = verify_fidelity(db, raw)
            counts = unit1.object_value(evidence["counts"], "independent full-source counts")
            if (counts["sentences"], counts["nodes"], counts["tokens"]) != (1134, 56488, 18329):
                raise ImportFailure("independently derived Matthew historical counts do not match")
            db.commit()
        finally:
            if db.in_transaction:
                db.rollback()
            db.close()
        os.link(candidate, output)
    return {
        "status": "COMPLETE", "output": str(output), "parser": "System.Xml.XmlReader",
        "runtime": runtime, "python_version": sys.version.split()[0], "sqlite_version": sqlite3.sqlite_version,
        "elapsed_seconds": round(time.perf_counter() - started, 3), **identities, **evidence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import only the pinned SBLGNT Matthew source, with independent fidelity gates.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        with reader_bridge() as assembly:
            result = build_matthew(args.output, assembly)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ImportFailure, schema.SchemaError, unit1.VerificationError, OSError, sqlite3.Error) as error:
        print(f"Matthew import FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
