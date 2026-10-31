import hashlib
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_ROOT = Path(r"C:\Works\macula-greek")
REVISION = "8423afe47b9e8f24b7772e808af45c7159a6fe7e"
RELATIVE_PATH = "SBLGNT/nodes/01-matthew.xml"
SHA256 = "FE1A8FED24DEC268A0D04160EC15BABDBE90105FFFDB915FD041B572C1FC40F4"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "macula-sblgnt-matthew.unit1.json"

SOURCE_IDENTITY = {
    "contract_version": 1,
    "source_family": "MACULA Greek",
    "edition": "SBLGNT",
    "source_format": "nodes",
    "authorized_book": "Matthew",
    "upstream_repository": "Clear-Bible/macula-greek",
    "upstream_local_checkout": str(UPSTREAM_ROOT),
    "revision": REVISION,
    "allowlist": [{"relative_path": RELATIVE_PATH, "sha256": SHA256}],
    "network_fetch": False,
    "implicit_xinclude": False,
    "directory_wildcard_expansion": False,
    "fixtures": {
        "primary": "fixtures/matthew-1-1.expected.json",
        "boundary": "fixtures/matthew-1-2-boundary.expected.json",
    },
}
FIELD_IDENTITY = {
    "scripture_and_referent": ["ref", "Ref"],
    "identifiers": ["Id", "xml:id", "nodeId", "morphId"],
    "morphology_tags": ["FunctionalTag", "FormalTag"],
    "xml_id_expanded_name": XML_ID,
}
ORDERING_CONCEPTS = [
    "source_child_sibling_order",
    "tree_leaf_traversal_order",
    "source_Start",
    "source_End",
    "scripture_coordinate",
    "canonical_scripture_order",
    "exact_node_token_membership",
]
FIDELITY_INVARIANTS = {
    "F-01": "Raw source is source authority.",
    "F-02": "Typed/normalized fields are deterministic mirrors and must not overwrite raw source.",
    "F-03": "Missing and present-empty must remain distinguishable.",
    "F-04": "XML attribute identity preserves namespace, name, and case.",
    "F-05": "Greek surface text must not undergo destructive normalization.",
    "F-06": "Lemma must not replace token occurrence.",
    "F-07": "Exact canonical membership comes from tree ancestry, not Start/End or an envelope.",
    "F-08": "Upstream identifiers require source, edition, and version scope.",
    "F-09": "Unknown/unresolved information is retained or explicitly diagnosed, never silently discarded.",
    "F-10": "MACULA annotations are not automatically BRW evaluated interpretations.",
}
PROHIBITED_MAPPINGS = [
    ["S", "Actor"], ["V", "Action"], ["V", "Event"], ["O", "Patient"],
    ["P", "Identity"], ["P", "Attribute"], ["A0", "Actor"],
    ["A1", "Patient"], ["A2", "Recipient"],
]


class VerificationError(ValueError):
    pass


def require_equal(actual: object, expected: object, label: str) -> None:
    if type(actual) is not type(expected) or actual != expected:
        raise VerificationError(f"{label}: expected {expected!r}, found {actual!r}")


def object_value(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise VerificationError(f"{label}: expected an object with string keys")
    return value


def list_value(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise VerificationError(f"{label}: expected a list")
    return value


def field_names(value: object, label: str) -> list[str]:
    result: list[str] = []
    for name in list_value(value, label):
        if not isinstance(name, str):
            raise VerificationError(f"{label}: field names must be strings")
        result.append(name)
    return result


def unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise VerificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys)
    return object_value(value, str(path))


def validate_contract(contract: dict[str, object]) -> None:
    expected = {
        **SOURCE_IDENTITY,
        "field_identity": FIELD_IDENTITY,
        "ordering_concepts": ORDERING_CONCEPTS,
        "fidelity_invariants": FIDELITY_INVARIANTS,
        "prohibited_semantic_mappings": PROHIBITED_MAPPINGS,
    }
    require_equal(set(contract), set(expected), "contract fields")
    for key, value in expected.items():
        require_equal(contract[key], value, f"contract {key}")


def verify_source(contract: dict[str, object]) -> bytes:
    validate_contract(contract)
    for arguments, expected, label in (
        (["--show-toplevel"], "C:/Works/macula-greek", "upstream root"),
        (["--verify", "HEAD"], REVISION, "upstream revision"),
    ):
        result = subprocess.run(
            ["git", "-C", str(UPSTREAM_ROOT), "rev-parse", *arguments],
            check=True, capture_output=True, text=True,
        )
        require_equal(result.stdout.strip(), expected, label)
    source_path = UPSTREAM_ROOT.joinpath(*RELATIVE_PATH.split("/"))
    raw = source_path.read_bytes()
    require_equal(hashlib.sha256(raw).hexdigest().upper(), SHA256, "source SHA-256")
    return raw


def one(elements: list[ET.Element], label: str) -> ET.Element:
    require_equal(len(elements), 1, f"{label} count")
    return elements[0]


def leaf_nodes(element: ET.Element) -> list[ET.Element]:
    return [node for node in element.iter("Node") if not node.findall("Node")]


def expected_attributes(element: ET.Element, expected: object, label: str) -> None:
    for name, value in object_value(expected, label).items():
        require_equal(element.attrib.get(XML_ID if name == "xml:id" else name), value, f"{label} {name}")


def verify_fixtures(
    raw: bytes, primary: dict[str, object], boundary: dict[str, object],
) -> dict[str, object]:
    if b"<!DOCTYPE" in raw.upper():
        raise VerificationError("DOCTYPE is not authorized")
    document = ET.fromstring(raw)
    require_equal(document.tag, "Sentences", "source document root")
    if any(element.tag == "{http://www.w3.org/2001/XInclude}include" for element in document.iter()):
        raise VerificationError("XInclude is not authorized")
    sentence = one(
        [s for s in document.findall("Sentence") if s.attrib.get("ref") == primary["sentence_ref"]],
        "primary sentence",
    )
    require_equal(primary["sentence_count"], 1, "primary expected sentence count")
    tree = one(sentence.findall("Trees/Tree"), "primary tree")
    nodes = list(tree.iter("Node"))
    leaves = leaf_nodes(tree)
    counts = {
        "tree_count": len(sentence.findall("Trees/Tree")),
        "node_count": len(nodes),
        "node_to_node_relations": sum(len(node.findall("Node")) for node in nodes),
        "token_count": len(leaves),
        "source_attribute_count": sum(len(element.attrib) for element in sentence.iter()),
        "leaf_attribute_count": sum(len(node.attrib) for node in leaves),
        "verb_leaf_count": sum(node.attrib.get("Cat") == "verb" for node in leaves),
    }
    for key, value in counts.items():
        require_equal(value, primary[key], f"primary {key}")
    root = one(tree.findall("Node"), "primary root")
    require_equal(root.attrib, primary["root"], "primary root attributes")
    clause = one(root.findall("Node"), "primary clause")
    require_equal(clause.attrib, primary["clause"], "primary clause attributes")
    for name in field_names(primary["root_fields_expected_absent"], "root absence"):
        require_equal(name in root.attrib, False, f"root absence {name}")
    tokens = list_value(primary["tokens"], "primary tokens")
    require_equal(len(tokens), len(leaves), "expected token records")
    absent = field_names(primary["leaf_fields_expected_absent"], "leaf absence")
    for index, (node, expected) in enumerate(zip(leaves, tokens), 1):
        label = f"primary token {index}"
        token = object_value(expected, label)
        require_equal(node.attrib.get("Cat"), primary["leaf_category"], f"{label} Cat")
        require_equal(len(node.attrib), primary["leaf_attribute_count_per_token"], f"{label} attributes")
        for name in absent:
            require_equal(name in node.attrib, False, f"{label} absence {name}")
        require_equal(node.text, token["text"], f"{label} text")
        expected_attributes(node, {k: v for k, v in token.items() if k != "text"}, label)
    if leaves[-1].text == leaves[-1].attrib.get("NormalizedForm"):
        raise VerificationError("source surface and NormalizedForm must remain distinct")

    boundary_sentence = one(
        [s for s in document.findall("Sentence") if s.attrib.get("ref") == boundary["sentence_ref"]],
        "boundary sentence",
    )
    boundary_tree = one(boundary_sentence.findall("Trees/Tree"), "boundary tree")
    boundary_leaves = leaf_nodes(boundary_tree)
    order = object_value(boundary["ordering_counterexample"], "ordering counterexample")
    pair: list[ET.Element] = []
    for label in ("first_tree_item", "later_tree_item"):
        expected = object_value(order[label], label)
        node = one([n for n in boundary_leaves if n.attrib.get("ref") == expected["ref"]], label)
        require_equal(node.text, expected["text"], f"{label} text")
        expected_attributes(node, {k: v for k, v in expected.items() if k != "text"}, label)
        pair.append(node)
    if not boundary_leaves.index(pair[0]) < boundary_leaves.index(pair[1]):
        raise VerificationError("tree traversal counterexample is missing")
    if not int(pair[0].attrib["Start"]) < int(pair[1].attrib["Start"]):
        raise VerificationError("source Start counterexample is missing")
    canonical_pair = [int(node.attrib["ref"].rsplit("!", 1)[1]) for node in pair]
    if not canonical_pair[0] > canonical_pair[1]:
        raise VerificationError("canonical scripture order must reverse the tree pair")

    membership = object_value(boundary["discontinuous_membership"], "membership fixture")
    subtree = one(
        [n for n in boundary_tree.iter("Node") if n.attrib.get("nodeId") == membership["nodeId"]],
        "membership subtree",
    )
    expected_attributes(subtree, {k: membership[k] for k in ("nodeId", "Rule", "Start", "End")}, "subtree")
    members: list[int] = []
    for node in leaf_nodes(subtree):
        coordinate, ordinal = node.attrib["ref"].rsplit("!", 1)
        require_equal(coordinate, membership["scripture_coordinate"], "membership coordinate")
        members.append(int(ordinal))
    members.sort()
    require_equal(members, membership["scripture_token_members"], "exact ancestry membership")
    excluded = membership["canonical_envelope_non_member"]
    if not isinstance(excluded, int) or isinstance(excluded, bool):
        raise VerificationError("envelope non-member must be an integer")
    if excluded in members or not min(members) < excluded < max(members):
        raise VerificationError("envelope interior token must be excluded from exact membership")
    return {
        "primary": {"sentence_count": 1, **counts, "ClType": clause.attrib["ClType"]},
        "boundary": {"tree_pair": canonical_pair, "exact_members": members, "excluded": excluded},
    }


def run_unit1() -> dict[str, object]:
    contract = load_json(CONTRACT_PATH)
    raw = verify_source(contract)
    result = verify_fixtures(
        raw,
        load_json(PROJECT_ROOT / "fixtures" / "matthew-1-1.expected.json"),
        load_json(PROJECT_ROOT / "fixtures" / "matthew-1-2-boundary.expected.json"),
    )
    return {
        "revision": REVISION, "relative_path": RELATIVE_PATH,
        "expected_sha256": SHA256, "actual_sha256": hashlib.sha256(raw).hexdigest().upper(),
        **result,
    }


def main() -> int:
    try:
        result = run_unit1()
    except (VerificationError, OSError, subprocess.CalledProcessError,
            UnicodeError, json.JSONDecodeError, ET.ParseError, KeyError) as error:
        print(f"Unit 1 verification FAILED: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
