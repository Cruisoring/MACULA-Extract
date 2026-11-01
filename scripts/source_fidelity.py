from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
import argparse
import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
from xml.parsers import expat
from xml.sax.saxutils import escape, quoteattr

from scripts import source_schema as schema
from scripts import verify_unit1 as unit1
from scripts.source_importer import NODE_FIELDS, TOKEN_FIELDS, XML_NS, safe_output
from scripts.xmlreader_bridge import ImportFailure


DIGEST_VERSION = "macula.source-logical.v1"
XMLNS_NS = "http://www.w3.org/2000/xmlns/"


def open_readonly(path: Path) -> sqlite3.Connection:
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("PRAGMA recursive_triggers=ON")
    return db


@dataclass
class Reference:
    elements: int = 0
    attributes: int = 0
    content: int = 0
    sentences: list[tuple[object, ...]] = field(default_factory=list)
    trees: list[tuple[object, ...]] = field(default_factory=list)
    nodes: dict[str, tuple[object, ...]] = field(default_factory=dict)
    tokens: dict[str, tuple[object, ...]] = field(default_factory=dict)
    memberships: list[tuple[object, ...]] = field(default_factory=list)


@dataclass
class SourceFrame:
    locator: str
    path: list[list[object]]
    names: dict[tuple[str, str], int]
    scope: dict[str, str]
    attrs: dict[str, str]
    sentence: str | None
    tree: str | None
    node: bool
    sibling: int
    node_children: int = 0
    element_children: int = 0
    direct_text: list[str] = field(default_factory=list)


def reference_events(raw: bytes, facts: Reference) -> Iterator[list[object]]:
    """Independent Expat source parse; never reads SQLite or importer reader events."""
    parser = expat.ParserCreate()
    parser.ordered_attributes = True
    queue: deque[list[object]] = deque()
    stack: list[SourceFrame] = []
    pending: list[str] = []
    cdata = False
    sentence_ordinal = 0
    trees_per_sentence: dict[str, int] = {}
    leaves_per_tree: dict[str, int] = {}

    def flush(force_cdata: bool = False) -> None:
        if pending or force_cdata:
            value = "".join(pending)
            if not stack:
                value = value.replace("\r\n", "\n").replace("\r", "\n")
            queue.append(["cdata" if cdata else "text", value])
            facts.content += 1
            pending.clear()

    def expanded(qname: str, scope: dict[str, str], attribute: bool = False) -> list[str]:
        if attribute and (qname == "xmlns" or qname.startswith("xmlns:")):
            return [XMLNS_NS, qname.split(":")[-1], "xmlns" if ":" in qname else "", qname]
        prefix, local = qname.split(":", 1) if ":" in qname else ("", qname)
        if prefix and prefix not in scope:
            raise ImportFailure(f"independent source parse: unbound prefix {prefix}")
        return [scope.get(prefix, "") if prefix or not attribute else "", local, prefix, qname]

    def start(qname: str, raw_attrs: list[str]) -> None:
        nonlocal sentence_ordinal
        flush()
        parent = stack[-1] if stack else None
        scope = dict(parent.scope if parent else {"xml": XML_NS, "": ""})
        for index in range(0, len(raw_attrs), 2):
            key, value = raw_attrs[index:index + 2]
            if key == "xmlns":
                scope[""] = value
            elif key.startswith("xmlns:"):
                scope[key.split(":", 1)[1]] = value
        name = expanded(qname, scope)
        attributes = [
            [*expanded(raw_attrs[index], scope, True), raw_attrs[index + 1]]
            for index in range(0, len(raw_attrs), 2)
        ]
        if name[:2] == ["http://www.w3.org/2001/XInclude", "include"]:
            raise ImportFailure("independent source parse: XInclude prohibited")
        identities = [(attr[0], attr[1]) for attr in attributes]
        if len(identities) != len(set(identities)):
            raise ImportFailure("independent source parse: duplicate expanded attribute")
        same = (name[0], name[1])
        order = parent.names.get(same, 0) + 1 if parent else 1
        path = [*(parent.path if parent else []), [name[0], name[1], order]]
        locator = json.dumps(path, ensure_ascii=True, separators=(",", ":"))
        attrs = {attr[1]: attr[4] for attr in attributes if not attr[0]}
        attrs.update({"xml:id": attr[4] for attr in attributes if attr[:2] == [XML_NS, "id"]})
        sibling = parent.element_children if parent else 0
        frame = SourceFrame(
            locator, path, {}, scope, attrs, parent.sentence if parent else None,
            parent.tree if parent else None, name[:2] == ["", "Node"], sibling,
        )
        if parent:
            parent.names[same] = order
            parent.element_children += 1
        if name[:2] == ["", "Sentence"]:
            frame.sentence = locator
            facts.sentences.append((locator, sentence_ordinal, attrs.get("ref")))
            sentence_ordinal += 1
        elif name[:2] == ["", "Tree"]:
            if frame.sentence is None:
                raise ImportFailure("independent source Tree lacks Sentence")
            frame.tree = locator
            order = trees_per_sentence.get(frame.sentence, 0)
            facts.trees.append((locator, frame.sentence, order))
            trees_per_sentence[frame.sentence] = order + 1
            leaves_per_tree[locator] = 0
        elif frame.node:
            if frame.tree is None:
                raise ImportFailure("independent source Node lacks Tree")
            parent_node = parent.locator if parent and parent.node else None
            sibling = parent.node_children if parent and parent.node else sibling
            facts.nodes[locator] = (
                locator, frame.tree, parent_node, sibling,
                *(attrs.get(key) for key in NODE_FIELDS),
            )
            if parent and parent.node:
                parent.node_children += 1
        stack.append(frame)
        queue.append(["start", name, attributes, locator])
        facts.elements += 1
        facts.attributes += len(attributes)
        facts.content += 1

    def end(qname: str) -> None:
        flush()
        frame = stack.pop()
        if frame.node and frame.node_children == 0:
            ref = frame.attrs.get("ref", "")
            address = ref.removeprefix("MAT ").replace(":", "!").split("!")
            if not ref.startswith("MAT ") or len(address) != 3 or not all(part.isdecimal() for part in address):
                raise ImportFailure("independent source leaf has invalid Matthew coordinate")
            chapter, verse, word = (int(part) for part in address)
            if frame.tree is None:
                raise ImportFailure("independent source leaf lacks Tree")
            traversal = leaves_per_tree[frame.tree]
            leaves_per_tree[frame.tree] = traversal + 1
            facts.tokens[frame.locator] = (
                frame.locator, frame.tree, "".join(frame.direct_text), traversal, None,
                chapter, verse, word, *(frame.attrs.get(key) for key in TOKEN_FIELDS),
            )
            facts.memberships.extend(
                (ancestor.locator, frame.locator, frame.tree)
                for ancestor in [*stack, frame] if ancestor.node
            )
        queue.append(["end"])

    def data(value: str) -> None:
        pending.append(value)
        if stack:
            stack[-1].direct_text.append(value)

    def start_cdata() -> None:
        nonlocal cdata
        flush()
        cdata = True

    def end_cdata() -> None:
        nonlocal cdata
        flush(True)
        cdata = False

    def comment(value: str) -> None:
        flush()
        queue.append(["comment", value])
        facts.content += 1

    def pi(target: str, value: str) -> None:
        flush()
        queue.append(["pi", value, target])
        facts.content += 1

    def doctype(*args: object) -> None:
        raise ImportFailure("independent source parse: DOCTYPE prohibited")

    def document_misc(value: str) -> None:
        if stack or any(character not in "\t\r\n " for character in value):
            raise ImportFailure("independent source parse: unsupported default XML event")
        pending.append(value)

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = data
    parser.StartCdataSectionHandler = start_cdata
    parser.EndCdataSectionHandler = end_cdata
    parser.CommentHandler = comment
    parser.ProcessingInstructionHandler = pi
    parser.StartDoctypeDeclHandler = doctype
    parser.ExternalEntityRefHandler = lambda *args: 0
    parser.XmlDeclHandler = lambda *args: None
    parser.DefaultHandler = document_misc
    for offset in range(0, len(raw), 65536):
        parser.Parse(raw[offset:offset + 65536], False)
        while queue:
            yield queue.popleft()
    parser.Parse(b"", True)
    flush()
    while queue:
        yield queue.popleft()
    grouped: dict[object, list[tuple[object, ...]]] = {}
    for token in facts.tokens.values():
        grouped.setdefault(token[1], []).append(token)
    for tokens in grouped.values():
        for rank, token in enumerate(sorted(tokens, key=lambda value: value[5:8])):
            locator = token[0]
            if not isinstance(locator, str):
                raise ImportFailure("invalid reference token occurrence")
            facts.tokens[locator] = (*token[:4], rank, *token[5:])


def db_xml_events(db: sqlite3.Connection) -> Iterator[list[object]]:
    """Reconstruct only from generic DB rows; original_bytes is never selected."""
    files = db.execute("SELECT file_id FROM source_file").fetchall()
    if len(files) != 1:
        raise ImportFailure("normalized reconstruction requires exactly one source file")
    file_id = files[0][0]

    def contents(owner: int | None) -> Iterator[tuple[object, ...]]:
        return iter(db.execute(
            "SELECT kind,child_element_id,value,pi_target FROM xml_content "
            "WHERE file_id=? AND owner_element_id IS ? ORDER BY ordinal", (file_id, owner),
        ).fetchall())

    stack = [contents(None)]
    while stack:
        row = next(stack[-1], None)
        if row is None:
            stack.pop()
            if stack:
                yield ["end"]
            continue
        kind, child, value, target = row
        if kind == "element":
            element = db.execute(
                "SELECT namespace_uri,local_name,prefix,qualified_name,locator FROM xml_element WHERE element_id=?",
                (child,),
            ).fetchone()
            if element is None or not isinstance(child, int):
                raise ImportFailure("DB reconstruction has an unknown child")
            attributes = [list(attr) for attr in db.execute(
                "SELECT namespace_uri,local_name,prefix,qualified_name,value FROM xml_attribute "
                "WHERE element_id=? ORDER BY ordinal", (child,),
            )]
            yield ["start", list(element[:4]), attributes, element[4]]
            stack.append(contents(child))
        elif kind == "pi":
            yield [kind, value, target]
        else:
            yield [kind, value]


def core_rows(db: sqlite3.Connection) -> dict[str, Iterator[tuple[object, ...]]]:
    result = {
        "sentences": iter(db.execute(
            "SELECT e.locator,s.ordinal,s.ref_raw FROM sentence s JOIN xml_element e USING(element_id) ORDER BY e.locator")),
        "trees": iter(db.execute(
            "SELECT e.locator,se.locator,t.ordinal FROM tree t JOIN xml_element e USING(element_id) "
            "JOIN sentence s USING(sentence_id) JOIN xml_element se ON se.element_id=s.element_id ORDER BY e.locator")),
        "nodes": iter(db.execute(
            "SELECT e.locator,te.locator,pe.locator,n.sibling_ordinal," +
            ",".join("n." + column for column in NODE_FIELDS.values()) +
            " FROM syntax_node n JOIN xml_element e USING(element_id) JOIN tree tr USING(tree_id) "
            "JOIN xml_element te ON te.element_id=tr.element_id "
            "LEFT JOIN syntax_node p ON p.node_id=n.parent_node_id "
            "LEFT JOIN xml_element pe ON pe.element_id=p.element_id ORDER BY e.locator")),
        "tokens": iter(db.execute(
            "SELECT e.locator,te.locator,t.source_direct_text,t.tree_leaf_ordinal,t.canonical_ordinal,"
            "t.chapter,t.verse,t.verse_token_ordinal," +
            ",".join("t." + column for column in TOKEN_FIELDS.values()) +
            " FROM token t JOIN syntax_node n USING(node_id) JOIN xml_element e USING(element_id) "
            "JOIN tree tr ON tr.tree_id=t.tree_id JOIN xml_element te ON te.element_id=tr.element_id ORDER BY e.locator")),
        "memberships": iter(db.execute(
            "SELECT ne.locator,le.locator,te.locator FROM node_token_membership m "
            "JOIN syntax_node n ON n.node_id=m.node_id JOIN xml_element ne ON ne.element_id=n.element_id "
            "JOIN token t ON t.token_id=m.token_id JOIN syntax_node l ON l.node_id=t.node_id "
            "JOIN xml_element le ON le.element_id=l.element_id "
            "JOIN tree tr ON tr.tree_id=m.tree_id JOIN xml_element te ON te.element_id=tr.element_id "
            "ORDER BY ne.locator,le.locator,te.locator")),
    }
    return result


def canonical_line(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode("ascii")


def logical_digest(db: sqlite3.Connection) -> str:
    digest = hashlib.sha256(canonical_line(DIGEST_VERSION))
    identities = list(db.execute(
        "SELECT d.source_family,d.edition,d.repository_uri,d.revision,d.manifest_sha256,"
        "f.relative_path,f.source_format,f.sha256,f.byte_size,b.source_book_code,b.book_ordinal,b.source_book_name "
        "FROM source_file f JOIN dataset_snapshot d USING(snapshot_id) JOIN book b ON b.book_id=f.book_id"))
    for row in db.execute("SELECT version,ddl_sha256,parser_contract_sha256,locator_contract_sha256 FROM schema_version"):
        digest.update(canonical_line(["schema", *row]))
    digest.update(canonical_line(["source", identities]))
    for event in db_xml_events(db):
        digest.update(canonical_line(event))
    for category, rows in core_rows(db).items():
        for row in rows:
            digest.update(canonical_line([category, *row]))
    return digest.hexdigest().upper()


def archive_bytes(db: sqlite3.Connection) -> bytes:
    rows = db.execute("SELECT original_bytes FROM source_file").fetchall()
    if len(rows) != 1 or not isinstance(rows[0][0], bytes):
        raise ImportFailure("archive export requires exactly one source-byte BLOB")
    return rows[0][0]


def normalized_xml(db: sqlite3.Connection) -> bytes:
    output: list[str] = []
    names: list[str] = []
    for event in db_xml_events(db):
        if event[0] == "start":
            name = unit1.list_value(event[1], "DB element name")
            if not isinstance(name[3], str):
                raise ImportFailure("DB reconstruction requires qualified-name evidence")
            names.append(name[3])
            attributes: list[str] = []
            for value in unit1.list_value(event[2], "DB attributes"):
                attr = unit1.list_value(value, "DB attribute")
                if not isinstance(attr[3], str) or not isinstance(attr[4], str):
                    raise ImportFailure("DB reconstruction requires attribute QName/value evidence")
                attributes.append(" " + attr[3] + "=" + quoteattr(attr[4]))
            output.append("<" + name[3] + "".join(attributes) + ">")
        elif event[0] == "end":
            output.append("</" + names.pop() + ">")
        else:
            value = event[1]
            if not isinstance(value, str):
                raise ImportFailure("DB content requires a string")
            if event[0] == "text":
                output.append(escape(value).replace("\r", "&#13;"))
            elif event[0] == "cdata":
                output.append("<![CDATA[" + value + "]]>")
            elif event[0] == "comment":
                output.append("<!--" + value + "-->")
            elif event[0] == "pi":
                output.append("<?" + str(event[2]) + (" " + value if value else "") + "?>")
    return "".join(output).encode("utf-8")


def verify_fidelity(db: sqlite3.Connection, raw: bytes) -> dict[str, object]:
    schema.validate_store(db)
    if archive_bytes(db) != raw:
        raise ImportFailure("BYTE fidelity failed: archived bytes differ from independently supplied source")
    reference = Reference()
    sentinel = object()
    for ordinal, (expected, actual) in enumerate(zip_longest(
            reference_events(raw, reference), db_xml_events(db), fillvalue=sentinel)):
        if expected != actual:
            raise ImportFailure(f"NORMALIZED source fidelity failed at ordered XML event {ordinal}: {expected!r} != {actual!r}")
    expected_core = {
        "sentences": sorted(reference.sentences), "trees": sorted(reference.trees),
        "nodes": sorted(reference.nodes.values()), "tokens": sorted(reference.tokens.values()),
        "memberships": sorted(reference.memberships),
    }
    actual_core = core_rows(db)
    for category, expected in expected_core.items():
        for ordinal, (source_row, db_row) in enumerate(zip_longest(
                expected, actual_core[category], fillvalue=sentinel)):
            if source_row != db_row:
                raise ImportFailure(f"NORMALIZED source fidelity failed: {category} occurrence {ordinal}: {source_row!r} != {db_row!r}")
    counts = {
        "elements": reference.elements, "attributes": reference.attributes, "content": reference.content,
        **{category: len(rows) for category, rows in expected_core.items()},
        "single_character_tokens": sum(isinstance(row[2], str) and len(row[2]) == 1 for row in reference.tokens.values()),
    }
    return {
        "byte_fidelity": "PASS", "normalized_fidelity": "PASS",
        "independent_reference": "Expat direct original-byte parse",
        "counts": counts, "logical_digest_version": DIGEST_VERSION, "logical_digest": logical_digest(db),
    }


def export_bytes(path: Path, data: bytes) -> None:
    output = safe_output(path)
    with TemporaryDirectory(prefix="macula-unit3-export-", dir=output.parent) as directory:
        candidate = Path(directory) / "export.xml"
        candidate.write_bytes(data)
        os.link(candidate, output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently verify the pinned Matthew store; export either fidelity channel.")
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--archive-output", type=Path)
    parser.add_argument("--normalized-output", type=Path)
    args = parser.parse_args()
    try:
        for path in (args.archive_output, args.normalized_output):
            if path is not None:
                safe_output(path)
        raw = unit1.verify_source(unit1.load_json(unit1.CONTRACT_PATH))
        db = open_readonly(args.database)
        try:
            report = verify_fidelity(db, raw)
            if args.archive_output is not None:
                export_bytes(args.archive_output, archive_bytes(db))
            if args.normalized_output is not None:
                data = normalized_xml(db)
                export_bytes(args.normalized_output, data)
                report["normalized_xml_sha256"] = hashlib.sha256(data).hexdigest().upper()
        finally:
            db.close()
        print(json.dumps(report, ensure_ascii=True, indent=2))
        return 0
    except (ImportFailure, schema.SchemaError, unit1.VerificationError, OSError, sqlite3.Error, expat.ExpatError) as error:
        print(f"Matthew source fidelity FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
