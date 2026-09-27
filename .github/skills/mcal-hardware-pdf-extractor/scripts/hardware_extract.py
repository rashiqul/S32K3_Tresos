from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-hardware-pdf-extractor"
DEFAULT_PROFILE = SKILL_ROOT / "profiles" / "mcu-fxosc.json"
DEFAULT_OUTPUT = PROJECT_ROOT / ".cache" / "mcal-hardware-pdf-extractor" / "hardware.json"
SCHEMA_PATH = SKILL_ROOT / "schemas" / "hardware-extract.schema.json"
SCHEMA_VERSION = "1.0.0"
TOOL_VERSION = "0.1.0"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def normalized_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def load_profile(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("hardware profile must be a JSON object")
    return payload


def validate_payload(payload: dict[str, Any]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator_class(schema).validate(payload)


def extract_profile(profile_path: Path = DEFAULT_PROFILE) -> dict[str, Any]:
    from pypdf import PdfReader

    profile = load_profile(profile_path)
    readers: dict[str, Any] = {}
    documents: dict[str, dict[str, Any]] = {}
    for key, specification in profile["documents"].items():
        path = PROJECT_ROOT / specification["path"]
        reader = PdfReader(path)
        if reader.is_encrypted and reader.decrypt("") == 0:
            raise ValueError(f"PDF is encrypted and cannot be opened: {path}")
        readers[key] = reader
        documents[key] = {
            "document": specification["path"],
            "sha256": file_sha256(path),
            "page_count": len(reader.pages),
            "source_type": specification["source_type"],
        }

    citations: list[dict[str, Any]] = []
    for name, specification in profile["citations"].items():
        document_key = str(specification["document"])
        reader = readers[document_key]
        physical_page = int(specification["physical_page"])
        if physical_page > len(reader.pages):
            raise ValueError(f"citation {name} page exceeds document length: {physical_page}")
        text = reader.pages[physical_page - 1].extract_text() or ""
        normalized_page = normalized_text(text)
        missing = [
            term
            for term in specification["required_terms"]
            if normalized_text(str(term)) not in normalized_page
        ]
        if missing:
            raise ValueError(
                f"citation {name} missing required terms on page {physical_page}: {missing}"
            )
        citations.append(
            {
                "name": name,
                **specification,
                "extraction_method": "page-text",
                "extraction_confidence": 1.0,
            }
        )

    payload = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "state": "complete",
        "profile": {
            "path": relative_path(profile_path),
            "sha256": file_sha256(profile_path),
            "version": profile["profile_version"],
        },
        "documents": documents,
        "citations": citations,
        "entities": profile["entities"],
        "relationships": profile["relationships"],
        "assertions": profile["assertions"],
        "warnings": [],
        "failures": [],
    }
    validate_payload(payload)
    return payload


def write_json_atomic(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(
        description="Extract cited hardware facts from local reference and data manuals"
    )
    command.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        payload = extract_profile(arguments.profile.resolve())
        write_json_atomic(arguments.output.resolve(), payload)
        summary = {
            "state": payload["state"],
            "profile": payload["profile"],
            "documents": len(payload["documents"]),
            "citations": len(payload["citations"]),
            "entities": len(payload["entities"]),
            "assertions": len(payload["assertions"]),
        }
        print(json.dumps(summary if arguments.json else payload, indent=2, ensure_ascii=True))
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
