from collections.abc import Iterator
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import threading

from scripts.verify_unit1 import PROJECT_ROOT, list_value


class ImportFailure(ValueError):
    pass


@contextmanager
def reader_bridge() -> Iterator[Path]:
    project = PROJECT_ROOT / "parsers" / "XmlReaderBridge"
    with TemporaryDirectory(prefix="macula-unit3-reader-") as directory:
        temporary = Path(directory)
        environment = {
            **os.environ,
            "DOTNET_CLI_TELEMETRY_OPTOUT": "1",
            "DOTNET_SKIP_FIRST_TIME_EXPERIENCE": "1",
            "DOTNET_CLI_HOME": str(temporary / "cli"),
            "NUGET_PACKAGES": str(temporary / "packages"),
            "MSBUILDDISABLENODEREUSE": "1",
        }
        result = subprocess.run(
            ["dotnet", "build", str(project / "XmlReaderBridge.csproj"),
             "--configuration", "Release", "--artifacts-path", str(temporary / "build"),
             "--configfile", str(project / "NuGet.Config"), "-p:UseSharedCompilation=false",
             "-p:NuGetAudit=false", "--nologo"],
            capture_output=True, text=True, encoding="utf-8", env=environment,
        )
        if result.returncode:
            raise ImportFailure(f"offline XmlReader build failed:\n{result.stdout}\n{result.stderr}")
        assembly = temporary / "build" / "bin" / "XmlReaderBridge" / "release" / "XmlReaderBridge.dll"
        if not assembly.is_file():
            raise ImportFailure(f"offline build did not produce {assembly}")
        yield assembly


def string(value: object) -> str:
    if not isinstance(value, str):
        raise ImportFailure("reader protocol requires a string")
    return value


def strings(value: object, size: int) -> tuple[str, ...]:
    values = list_value(value, "reader string array")
    if len(values) != size:
        raise ImportFailure(f"reader array requires {size} fields")
    return tuple(string(item) for item in values)


def reader_events(raw: bytes, assembly: Path) -> Iterator[list[object]]:
    process = subprocess.Popen(
        ["dotnet", str(assembly)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if process.stdin is None or process.stdout is None or process.stderr is None:
        raise ImportFailure("XmlReader process pipes unavailable")
    writer_errors: list[OSError] = []

    def send() -> None:
        try:
            if process.stdin is not None:
                process.stdin.write(raw)
        except OSError as error:
            writer_errors.append(error)
        finally:
            if process.stdin is not None:
                process.stdin.close()

    writer = threading.Thread(target=send)
    writer.start()
    complete = False
    try:
        for line in process.stdout:
            event = list_value(json.loads(line), "reader event")
            if complete:
                raise ImportFailure("reader emitted facts after completion")
            if event == ["complete"]:
                complete = True
            yield event
        errors = process.stderr.read().decode("utf-8")
        code = process.wait()
        writer.join()
        if code or writer_errors or not complete:
            raise ImportFailure(f"authoritative XmlReader parse failed ({code}): {errors}; {writer_errors}")
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        writer.join()
        process.stdout.close()
        process.stderr.close()
