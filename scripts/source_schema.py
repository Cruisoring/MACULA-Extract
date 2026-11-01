import hashlib
import json
from pathlib import Path
import sqlite3
import sys

from scripts.occurrence_locator import SCHEME, SCHEME_VERSION, Segment, encode_locator
from scripts.verify_unit1 import load_json, object_value


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DDL_PATH = PROJECT_ROOT / "schema" / "001-source-store.sql"
PARSER_PATH = PROJECT_ROOT / "contracts" / "xmlreader-parser.unit2.json"
LOCATOR_PATH = PROJECT_ROOT / "contracts" / "occurrence-locator.unit2.json"
SCHEMA_VERSION = 2
TABLES = {
    "schema_version", "dataset_snapshot", "source_file", "book", "xml_element",
    "xml_attribute", "xml_content", "sentence", "tree", "syntax_node", "token",
    "node_token_membership",
}


class SchemaError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SchemaError(message)


def _rows(connection: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    cursor = connection.cursor()
    cursor.row_factory = sqlite3.Row
    return cursor.execute(sql).fetchall()


def _identity() -> tuple[int, str, str, str]:
    return (
        SCHEMA_VERSION,
        *(hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest().upper()
          for path in (DDL_PATH, PARSER_PATH, LOCATOR_PATH)),
    )


def _unshadowed_main(connection: sqlite3.Connection) -> None:
    _require(all(row[1] in ("main", "temp") for row in connection.execute("PRAGMA database_list")),
             "source schema operation requires a dedicated main database, without attachments")
    _require(not connection.execute(
        "SELECT name FROM sqlite_temp_schema WHERE name NOT GLOB 'sqlite_*'",
    ).fetchall(), "temporary schema objects may shadow source tables")


def _catalog(connection: sqlite3.Connection) -> list[tuple[object, ...]]:
    return [tuple(row) for row in connection.execute(
        "SELECT type,name,tbl_name,sql FROM main.sqlite_schema WHERE sql IS NOT NULL ORDER BY type,name",
    )]


def _contracts() -> None:
    parser = load_json(PARSER_PATH)
    locator = load_json(LOCATOR_PATH)
    _require(type(parser["contract_version"]) is int and parser["contract_version"] == 1
             and parser["authoritative_parser"] == "System.Xml.XmlReader"
             and parser["production_parser_implemented"] is False,
             "unsupported authoritative parser contract")
    expected_settings = {
        "DtdProcessing": "Prohibit", "XmlResolver": None, "ValidationType": "None",
        "ConformanceLevel": "Document", "CheckCharacters": True, "IgnoreWhitespace": False,
        "IgnoreComments": False, "IgnoreProcessingInstructions": False,
    }
    _require(json.dumps(parser["settings"], sort_keys=True) == json.dumps(expected_settings, sort_keys=True),
             "unsafe XmlReader contract settings")
    _require(parser["xmlpro_dependency"] is False and parser["semantic_projection"] is False,
             "forbidden parser dependency/projection")
    source = object_value(parser["input"], "parser input")
    _require(source["original_bytes_required"] is True and source["verify_revision_path_checksum_before_parsing"] is True
             and source["external_acquisition"] is False and source["implicit_xinclude"] is False
             and source["reject_element_expanded_name"] == ["http://www.w3.org/2001/XInclude", "include"],
             "unsafe parser source acquisition contract")
    values = object_value(parser["values"], "parser values")
    _require(all(values[key] is False for key in (
        "application_trim", "greek_normalization", "text_substitution", "html_entity_processing",
    )), "unsafe source value processing contract")
    _require(locator["scheme"] == SCHEME and type(locator["scheme_version"]) is int
             and locator["scheme_version"] == SCHEME_VERSION and locator["physical_mapper_implemented"] is False,
             "unsupported occurrence locator scheme/version")
    _require(locator["ordinal_base"] == 1 and locator["root_ordinal"] == 1
             and locator["serialization"] == "JSON ensure_ascii=true, separators=(',', ':'), no application Unicode normalization.",
             "occurrence locator encoding/ordinal contract mismatch")


def bootstrap(connection: sqlite3.Connection) -> None:
    _require(not connection.in_transaction, "bootstrap requires no active transaction")
    _unshadowed_main(connection)
    _require(sqlite3.sqlite_version_info >= (3, 37, 0), "SQLite 3.37+ with STRICT and JSON support required")
    objects = connection.execute("SELECT name FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*'").fetchall()
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    application = connection.execute("PRAGMA application_id").fetchone()[0]
    _require(not objects and version == 0 and application == 0,
             f"already initialized or version mismatch: user_version={version}; empty database required")
    _contracts()
    ddl = DDL_PATH.read_text(encoding="utf-8")
    identity = _identity()
    _require(hashlib.sha256(ddl.encode("utf-8")).hexdigest().upper() == identity[1], "DDL changed during bootstrap")
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA recursive_triggers=ON")
    _require(connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "foreign keys could not be enabled")
    try:
        connection.executescript("BEGIN IMMEDIATE;\n" + ddl)
        connection.execute(
            "INSERT INTO schema_version VALUES (1, ?, ?, ?, ?)", identity,
        )
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        connection.commit()
    except sqlite3.Error as error:
        connection.rollback()
        raise SchemaError(f"schema bootstrap failed and rolled back: {error}") from error


def _ordered_groups(rows: list[sqlite3.Row], group_key: str, ordinal_key: str) -> None:
    groups: dict[object, list[int]] = {}
    for row in rows:
        groups.setdefault(row[group_key], []).append(row[ordinal_key])
    for owner, ordinals in groups.items():
        _require(sorted(ordinals) == list(range(len(ordinals))),
                 f"non-contiguous {ordinal_key} for {group_key}={owner}")


def _elements(connection: sqlite3.Connection) -> dict[int, sqlite3.Row]:
    elements = {row["element_id"]: row for row in _rows(connection, "SELECT * FROM xml_element")}
    groups: dict[tuple[int, int | None], list[sqlite3.Row]] = {}
    for row in elements.values():
        groups.setdefault((row["file_id"], row["parent_element_id"]), []).append(row)
    name_ordinals: dict[int, int] = {}
    for owner, siblings in groups.items():
        ordered = sorted(siblings, key=lambda r: r["sibling_ordinal"])
        _require([s["sibling_ordinal"] for s in ordered] == list(range(len(ordered))),
                 f"invalid element sibling order at {owner}")
        counts: dict[tuple[str, str], int] = {}
        for sibling in ordered:
            name = (sibling["namespace_uri"], sibling["local_name"])
            counts[name] = counts.get(name, 0) + 1
            name_ordinals[sibling["element_id"]] = counts[name]
    paths: dict[int, list[Segment]] = {}
    pending = dict(elements)
    while pending:
        ready = [
            row for row in pending.values()
            if row["parent_element_id"] is None or row["parent_element_id"] in paths
        ]
        _require(bool(ready), "XML parent cycle or missing parent")
        for row in ready:
            parent = row["parent_element_id"]
            path = ([] if parent is None else paths[parent]) + [
                (row["namespace_uri"], row["local_name"], name_ordinals[row["element_id"]]),
            ]
            _require(row["locator"] == encode_locator(path),
                     f"non-canonical or incorrect occurrence locator at element {row['element_id']}")
            paths[row["element_id"]] = path
            del pending[row["element_id"]]
    return elements


def _content(connection: sqlite3.Connection, elements: dict[int, sqlite3.Row]) -> dict[int, str]:
    content = _rows(connection, "SELECT * FROM xml_content ORDER BY file_id, owner_element_id, ordinal")
    groups: dict[tuple[int, int | None], list[sqlite3.Row]] = {}
    linked: set[int] = set()
    direct_text: dict[int, str] = {}
    for row in content:
        owner = row["owner_element_id"]
        groups.setdefault((row["file_id"], owner), []).append(row)
        if row["kind"] == "element":
            child = elements[row["child_element_id"]]
            _require(child["parent_element_id"] == owner, f"content parent mismatch at {row['content_id']}")
            linked.add(child["element_id"])
        if owner is not None and row["kind"] in ("text", "cdata"):
            direct_text[owner] = direct_text.get(owner, "") + row["value"]
    _require(linked == set(elements), "every XML element requires exactly one ordered content occurrence")
    for owner, entries in groups.items():
        _require([r["ordinal"] for r in entries] == list(range(len(entries))),
                 f"non-contiguous direct content at {owner}")
        child_order = [elements[r["child_element_id"]]["sibling_ordinal"]
                       for r in entries if r["kind"] == "element"]
        _require(child_order == list(range(len(child_order))), f"content/element order mismatch at {owner}")
        for previous, current in zip(entries, entries[1:]):
            _require(not (previous["kind"] == current["kind"] == "text"),
                     f"non-canonical reader text segmentation at {owner}")
    attributes = _rows(connection, "SELECT element_id, ordinal FROM xml_attribute")
    _ordered_groups(attributes, "element_id", "ordinal")
    return direct_text


def _core(connection: sqlite3.Connection, elements: dict[int, sqlite3.Row], direct_text: dict[int, str]) -> None:
    sentences = {r["sentence_id"]: r for r in _rows(connection, "SELECT * FROM sentence")}
    trees = {r["tree_id"]: r for r in _rows(connection, "SELECT * FROM tree")}
    nodes = {r["node_id"]: r for r in _rows(connection, "SELECT * FROM syntax_node")}
    tokens = _rows(connection, "SELECT * FROM token")
    books = {r["book_id"]: r for r in _rows(connection, "SELECT * FROM book")}
    _ordered_groups(list(sentences.values()), "file_id", "ordinal")
    _ordered_groups(list(trees.values()), "sentence_id", "ordinal")
    children: dict[int | None, list[sqlite3.Row]] = {}
    for element in elements.values():
        children.setdefault(element["parent_element_id"], []).append(element)
    for entries in children.values():
        entries.sort(key=lambda e: e["sibling_ordinal"])

    def matching_children(parent: int, local_name: str) -> list[sqlite3.Row]:
        return [e for e in children.get(parent, []) if (e["namespace_uri"], e["local_name"]) == ("", local_name)]

    node_child_ordinals = {
        child["element_id"]: ordinal
        for parent, entries in children.items() if parent is not None
        for ordinal, child in enumerate(
            e for e in entries if (e["namespace_uri"], e["local_name"]) == ("", "Node")
        )
    }
    sentence_elements_by_file: dict[int, set[int]] = {}
    tree_elements_by_sentence: dict[int, set[int]] = {}
    node_elements_by_tree: dict[int, set[int]] = {}
    for sentence in sentences.values():
        sentence_elements_by_file.setdefault(sentence["file_id"], set()).add(sentence["element_id"])
    for tree in trees.values():
        tree_elements_by_sentence.setdefault(tree["sentence_id"], set()).add(tree["element_id"])
    for node in nodes.values():
        node_elements_by_tree.setdefault(node["tree_id"], set()).add(node["element_id"])
    for element in elements.values():
        if element["parent_element_id"] is None and (element["namespace_uri"], element["local_name"]) == ("", "Sentences"):
            expected = {e["element_id"] for e in matching_children(element["element_id"], "Sentence")}
            _require(sentence_elements_by_file.get(element["file_id"], set()) == expected, "missing typed sentence occurrence")

    def named(element_id: int, local_name: str) -> sqlite3.Row:
        row = elements[element_id]
        _require((row["namespace_uri"], row["local_name"]) == ("", local_name),
                 f"typed {local_name} requires its actual source expanded name")
        return row

    for sentence in sentences.values():
        element = named(sentence["element_id"], "Sentence")
        parent = element["parent_element_id"]
        _require(parent is not None, "Sentence requires Sentences wrapper")
        wrapper = named(parent, "Sentences")
        _require(wrapper["parent_element_id"] is None, "Sentences must be the source document root")
        expected = [e["element_id"] for e in matching_children(parent, "Sentence")]
        _require(sentence["ordinal"] == expected.index(element["element_id"]), "XML/typed sentence order mismatch")
        actual = sentence_elements_by_file[sentence["file_id"]]
        _require(actual == set(expected), "missing typed sentence occurrence")
    sentence_tree_order: dict[int, list[int]] = {}
    for sentence in sentences.values():
        expected_trees = [
            element["element_id"] for wrapper in matching_children(sentence["element_id"], "Trees")
            for element in matching_children(wrapper["element_id"], "Tree")
        ]
        sentence_tree_order[sentence["sentence_id"]] = expected_trees
        _require(tree_elements_by_sentence.get(sentence["sentence_id"], set()) == set(expected_trees),
                 "missing typed Tree occurrence")
    for tree in trees.values():
        element = named(tree["element_id"], "Tree")
        wrapper_id = element["parent_element_id"]
        _require(wrapper_id is not None, "Tree requires Trees wrapper")
        wrapper = named(wrapper_id, "Trees")
        sentence = sentences[tree["sentence_id"]]
        _require(wrapper["parent_element_id"] == sentence["element_id"], "Tree sentence scope mismatch")
        expected = sentence_tree_order[tree["sentence_id"]]
        _require(tree["ordinal"] == expected.index(element["element_id"]), "XML/typed Tree order mismatch")
        actual = tree_elements_by_sentence[tree["sentence_id"]]
        _require(actual == set(expected), "missing typed Tree occurrence")
    for tree in trees.values():
        descendants: set[int] = set()
        pending_elements = [tree["element_id"]]
        while pending_elements:
            owner = pending_elements.pop()
            for child in children.get(owner, []):
                pending_elements.append(child["element_id"])
                if (child["namespace_uri"], child["local_name"]) == ("", "Node"):
                    descendants.add(child["element_id"])
        _require(descendants == node_elements_by_tree.get(tree["tree_id"], set()),
                 "missing or misplaced typed syntax node occurrence")
    node_paths: dict[int, tuple[int, ...]] = {}
    pending = dict(nodes)
    while pending:
        ready = [n for n in pending.values() if n["parent_node_id"] is None or n["parent_node_id"] in node_paths]
        _require(bool(ready), "syntax parent cycle or missing parent")
        for node in ready:
            element = named(node["element_id"], "Node")
            parent_id = node["parent_node_id"]
            parent_element = trees[node["tree_id"]]["element_id"] if parent_id is None else nodes[parent_id]["element_id"]
            _require(element["parent_element_id"] == parent_element, "XML/typed syntax parent mismatch")
            expected = node_child_ordinals[element["element_id"]]
            _require(node["sibling_ordinal"] == expected, "XML/typed syntax sibling mismatch")
            node_paths[node["node_id"]] = (() if parent_id is None else node_paths[parent_id]) + (expected,)
            del pending[node["node_id"]]
    token_nodes = {token["node_id"] for token in tokens}
    for node in nodes.values():
        has_children = bool(matching_children(node["element_id"], "Node"))
        _require((node["node_id"] in token_nodes) != has_children, "token must represent exactly a syntax leaf")
    tree_tokens: dict[int, list[sqlite3.Row]] = {}
    for token in tokens:
        node = nodes[token["node_id"]]
        tree = trees[token["tree_id"]]
        sentence = sentences[tree["sentence_id"]]
        _require(token["book_id"] == sentence["book_id"], "token book/snapshot scope mismatch")
        _require(token["source_direct_text"] == direct_text.get(node["element_id"], ""), "typed direct text mismatch")
        expected_ref = f"{books[token['book_id']]['source_book_code']} {token['chapter']}:{token['verse']}!{token['verse_token_ordinal']}"
        _require(token["ref_raw"] == expected_ref, "scripture coordinates differ from raw ref")
        tree_tokens.setdefault(token["tree_id"], []).append(token)
    for tree_id, entries in tree_tokens.items():
        traversal = sorted(entries, key=lambda t: node_paths[t["node_id"]])
        canonical = sorted(entries, key=lambda t: (t["chapter"], t["verse"], t["verse_token_ordinal"], t["tree_leaf_ordinal"]))
        _require([t["tree_leaf_ordinal"] for t in traversal] == list(range(len(entries))),
                 f"tree traversal/leaf order mismatch at Tree {tree_id}")
        _require([t["canonical_ordinal"] for t in canonical] == list(range(len(entries))),
                 f"canonical scripture order mismatch at Tree {tree_id}")


def validate_store(connection: sqlite3.Connection) -> None:
    _unshadowed_main(connection)
    _require(connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1, "foreign keys must be ON during validation")
    _require(connection.execute("PRAGMA recursive_triggers").fetchone()[0] == 1,
             "recursive triggers must be ON to protect immutable rows against REPLACE")
    _require(connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION, "schema version mismatch")
    _require(connection.execute("SELECT version, ddl_sha256, parser_contract_sha256, locator_contract_sha256 FROM schema_version").fetchall()
             == [_identity()], "schema/contract identity mismatch")
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")}
    _require(tables == TABLES, "unexpected or missing source schema tables")
    reference = sqlite3.connect(":memory:")
    try:
        reference.executescript(DDL_PATH.read_text(encoding="utf-8"))
        _require(_catalog(connection) == _catalog(reference), "actual SQL schema objects differ from frozen DDL")
    finally:
        reference.close()
    _require(not connection.execute("PRAGMA foreign_key_check").fetchall(), "foreign key violations")
    _require(connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)], "SQLite integrity check failed")
    for source in _rows(connection, "SELECT * FROM source_file"):
        _require(hashlib.sha256(source["original_bytes"]).hexdigest().upper() == source["sha256"],
                 f"source BLOB checksum mismatch at file {source['file_id']}")
    elements = _elements(connection)
    direct_text = _content(connection, elements)
    _core(connection, elements, direct_text)
    mismatch = connection.execute(
        "SELECT m.record_kind, m.record_id, m.column_name FROM typed_attribute_mirror m "
        "LEFT JOIN xml_attribute a ON a.element_id=m.element_id AND a.namespace_uri=m.namespace_uri AND a.local_name=m.local_name "
        "WHERE m.mirror_value IS NOT a.value LIMIT 1",
    ).fetchone()
    _require(mismatch is None, f"typed/source attribute mismatch: {mismatch}")
    for left, right in (("expected_node_token_membership", "node_token_membership"),
                        ("node_token_membership", "expected_node_token_membership")):
        difference = connection.execute(
            f"SELECT node_id, token_id, tree_id FROM {left} EXCEPT SELECT node_id, token_id, tree_id FROM {right} LIMIT 1",
        ).fetchone()
        _require(difference is None, f"incomplete/incorrect ancestry membership: {difference}")


def source_occurrence_key(connection: sqlite3.Connection, element_id: int) -> tuple[object, ...]:
    _unshadowed_main(connection)
    row = connection.execute(
        "SELECT d.edition, d.repository_uri, d.revision, d.manifest_sha256, f.relative_path, f.sha256, "
        "e.locator_scheme, e.locator_version, e.locator FROM xml_element e "
        "JOIN source_file f USING(file_id) JOIN dataset_snapshot d USING(snapshot_id) WHERE e.element_id=?",
        (element_id,),
    ).fetchone()
    if row is None:
        raise SchemaError(f"unknown source occurrence: {element_id}")
    return tuple(row)


def main() -> int:
    connection = sqlite3.connect(":memory:")
    try:
        bootstrap(connection)
        validate_store(connection)
    except (SchemaError, sqlite3.Error, OSError, ValueError, KeyError) as error:
        print(f"Unit 2 schema verification FAILED: {error}", file=sys.stderr)
        return 1
    finally:
        connection.close()
    print(json.dumps({"schema_version": SCHEMA_VERSION, "sqlite_version": sqlite3.sqlite_version,
                      "tables": sorted(TABLES), "bootstrap": "empty-only; repeat fails closed",
                      "production_ingestion": False}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
