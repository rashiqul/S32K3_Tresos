from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema.validators import validator_for
from referencing import Registry, Resource

PROJECT_ROOT = Path(__file__).resolve().parents[4]
SKILL_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-graph-loader"
SCHEMA_ROOT = SKILL_ROOT / "schemas"
SCHEMA_VERSION = "1.0.0"
TOOL_VERSION = "0.3.0"

PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


def normalize_identity_part(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value)).strip().replace("\\", "/")
    return re.sub(r"\s+", " ", text)


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_id(prefix: str, *identity_parts: object) -> str:
    if PREFIX_PATTERN.fullmatch(prefix) is None:
        raise ValueError(f"invalid stable ID prefix: {prefix}")
    if not identity_parts:
        raise ValueError("at least one identity part is required")
    normalized = [normalize_identity_part(part) for part in identity_parts]
    if any(not part for part in normalized):
        raise ValueError("identity parts must not be empty")
    digest = hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def graph_id(dataset_id: str, entity_id: str) -> str:
    return stable_id("graph", dataset_id, entity_id)


def document_id(path: str, sha256: str) -> str:
    if re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
        raise ValueError("document SHA-256 must be 64 lowercase hexadecimal characters")
    return stable_id("document", path, sha256)


def citation_id(
    source_document_id: str,
    physical_page: int,
    page_label: str,
    section: str,
    text_anchor: str,
) -> str:
    if physical_page < 1:
        raise ValueError("physical page must be at least 1")
    return stable_id(
        "citation",
        source_document_id,
        physical_page,
        page_label,
        section,
        text_anchor,
    )


def configuration_definition_id(
    module: str,
    source_document_id: str,
    section_number: str,
    kind: str,
    identifier: str,
) -> str:
    return stable_id(
        "configuration-definition",
        module,
        source_document_id,
        section_number,
        kind,
        identifier,
    )


def xdm_instance_id(project_id: str, file: str, path: str) -> str:
    return stable_id("xdm-instance", project_id, file, path)


def assertion_id(
    subject_id: str,
    predicate: str,
    object_id: str,
    citation_ids: list[str],
    producer_version: str,
) -> str:
    return stable_id(
        "assertion",
        subject_id,
        predicate,
        object_id,
        canonical_json(sorted(citation_ids)),
        producer_version,
    )


@cache
def _payload_validator(schema_root: Path, schema_name: str) -> Any:
    resources: list[tuple[str, Resource[Any]]] = []
    for path in schema_root.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resources.append((contents["$id"], Resource.from_contents(contents)))
    schema_path = schema_root / schema_name
    schema: dict[str, Any] = json.loads(schema_path.read_text(encoding="utf-8"))
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    return validator_class(schema, registry=Registry().with_resources(resources))


def validate_payload_from_directory(payload: object, schema_root: Path, schema_name: str) -> None:
    _payload_validator(schema_root.resolve(), schema_name).validate(payload)


def validate_payload(payload: object, schema_name: str) -> None:
    validate_payload_from_directory(payload, SCHEMA_ROOT, schema_name)