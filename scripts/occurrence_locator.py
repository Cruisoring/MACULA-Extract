import json
from collections.abc import Sequence


SCHEME = "macula.xml-expanded-ordinal-path"
SCHEME_VERSION = 1
Segment = tuple[str, str, int]


def encode_locator(segments: Sequence[Segment]) -> str:
    if not segments:
        raise ValueError("occurrence locator requires a root segment")
    for namespace, local_name, ordinal in segments:
        if not isinstance(namespace, str) or not isinstance(local_name, str) or not local_name:
            raise ValueError("locator names require exact namespace/local-name strings")
        if type(ordinal) is not int or ordinal < 1:
            raise ValueError("locator same-expanded-name ordinal must be a positive integer")
    if segments[0][2] != 1:
        raise ValueError("document root locator ordinal must be 1")
    return json.dumps(segments, ensure_ascii=True, separators=(",", ":"))
