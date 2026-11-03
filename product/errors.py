from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ErrorCategory(str, Enum):
    ABSENT = "ABSENT"
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED = "UNSUPPORTED"
    SOURCE_STORE_ERROR = "SOURCE_STORE_ERROR"
    PROJECTION_STORE_NOT_CONFIGURED = "PROJECTION_STORE_NOT_CONFIGURED"
    PROJECTION_STORE_ERROR = "PROJECTION_STORE_ERROR"
    SOURCE_PROJECTION_MISMATCH = "SOURCE_PROJECTION_MISMATCH"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"


@dataclass(frozen=True, slots=True)
class ProductError:
    category: ErrorCategory
    scope: Literal["input", "source", "projection", "selection"]
    message: str
    detail_code: str | None = None
