import re
from urllib.parse import parse_qsl

from product.errors import ErrorCategory, ProductError
from product.models import ProductSelection


_NUMBER = re.compile(r"[1-9][0-9]{0,18}")
_CANDIDATE = re.compile(r"sha256:[0-9a-f]{64}")
_EVALUATION = re.compile(r"eval-sha256:[0-9a-f]{64}")
_ALLOWED = {"book", "chapter", "verse", "token", "candidate", "evaluation"}


def invalid_input() -> ProductError:
    return ProductError(ErrorCategory.INVALID_INPUT, "input", "Invalid selection or request.")


def valid_number(value: object) -> bool:
    return type(value) is int and 0 < value <= 2**63 - 1


def validate_selection(selection: ProductSelection) -> ProductError | None:
    if selection.book != "MAT":
        return ProductError(ErrorCategory.UNSUPPORTED, "input", "Only Matthew (MAT) is supported.")
    if not valid_number(selection.chapter) or not valid_number(selection.verse):
        return invalid_input()
    if selection.token_ordinal is not None and not valid_number(selection.token_ordinal):
        return invalid_input()
    for value, pattern in ((selection.candidate_id, _CANDIDATE),
                           (selection.evaluation_id, _EVALUATION)):
        if value is not None and (type(value) is not str or pattern.fullmatch(value) is None):
            return invalid_input()
    return None


def parse_target(target: str) -> tuple[str, ProductSelection | None] | ProductError:
    path, separator, query = target.partition("?")
    try:
        if len(path.encode("utf-8")) > 256 or len(query.encode("utf-8")) > 2048:
            return invalid_input()
        if "#" in target or re.search(r"%(?![0-9a-fA-F]{2})", query):
            return invalid_input()
        pairs = parse_qsl(query, keep_blank_values=True, strict_parsing=True,
                          encoding="utf-8", errors="strict", max_num_fields=6) if query else []
    except (UnicodeError, ValueError):
        return invalid_input()
    values = dict(pairs)
    if len(values) != len(pairs) or set(values) - _ALLOWED:
        return invalid_input()
    if values.get("book", "MAT") != "MAT":
        return ProductError(ErrorCategory.UNSUPPORTED, "input", "Only Matthew (MAT) is supported.")
    if path != "/verse":
        if separator:
            return invalid_input()
        return path, None
    coordinates: dict[str, int] = {}
    for name in ("chapter", "verse", "token"):
        value = values.get(name)
        if value is None and name == "token":
            continue
        if value is None or _NUMBER.fullmatch(value) is None:
            return invalid_input()
        number = int(value)
        if not valid_number(number):
            return invalid_input()
        coordinates[name] = number
    selection = ProductSelection("MAT", coordinates["chapter"], coordinates["verse"],
                                 coordinates.get("token"), values.get("candidate"),
                                 values.get("evaluation"))
    error = validate_selection(selection)
    return error if error is not None else (path, selection)
