import argparse
from dataclasses import dataclass
import os
from pathlib import Path
from collections.abc import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ProductConfig:
    source_db_path: Path
    projection_db_path: Path | None = None
    host: str = "127.0.0.1"
    port: int = 8765

    def __post_init__(self) -> None:
        if self.host not in ("127.0.0.1", "::1"):
            raise ValueError("host must be a loopback literal")
        if type(self.port) is not int or not 0 <= self.port <= 65535:
            raise ValueError("port must be an integer from 0 through 65535")
        source = self.source_db_path.resolve()
        projection = None if self.projection_db_path is None else self.projection_db_path.resolve()
        if projection is not None and (
            source == projection or (
                source.exists() and projection.exists() and source.samefile(projection)
            )
        ):
            raise ValueError("source and projection stores must be separate files")
        object.__setattr__(self, "source_db_path", source)
        object.__setattr__(self, "projection_db_path", projection)


def _value(cli: str | None, environment: str | None) -> str | None:
    value = cli if cli is not None else environment
    return value if value is not None and value.strip() else None


def parse_config(
    args: Sequence[str] | None = None, environment: Mapping[str, str] | None = None,
) -> ProductConfig:
    parser = argparse.ArgumentParser(description="Matthew Scripture Structural Explorer")
    parser.add_argument("--source-db")
    parser.add_argument("--projection-db")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    values = parser.parse_args(args)
    env = os.environ if environment is None else environment
    source = _value(values.source_db, env.get("MACULA_EXPLORER_SOURCE_DB"))
    projection = _value(values.projection_db, env.get("MACULA_EXPLORER_PROJECTION_DB"))
    if source is None:
        parser.error("--source-db or MACULA_EXPLORER_SOURCE_DB is required")
    try:
        return ProductConfig(Path(source), None if projection is None else Path(projection),
                             values.host, values.port)
    except (ValueError, OSError) as error:
        if isinstance(error, OSError):
            parser.error("store paths could not be resolved")
        parser.error(str(error))
