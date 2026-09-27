from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DOCS = PROJECT_ROOT / "docs"

DOCUMENT_PATTERN = re.compile(r"^RTD_(?P<module>.+)_(?P<kind>UM|IM)\.pdf$", re.IGNORECASE)
FIGURE_CAPTION_PATTERN = re.compile(r"^(?:Figure|Fig\.)\s+\d", re.IGNORECASE)
SKILL_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-pdf-json-extractor"
SCHEMA_ROOT = SKILL_ROOT / "schemas"
TOOL_VERSION = "0.2.1"
SCHEMA_VERSION = "1.0.0"
PROFILE_ROOT = SKILL_ROOT / "profiles"
PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def stable_id(prefix: str, *identity_parts: object) -> str:
    if PREFIX_PATTERN.fullmatch(prefix) is None:
        raise ValueError(f"invalid stable ID prefix: {prefix}")
    normalized = [
        re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(part)).strip().replace("\\", "/"))
        for part in identity_parts
    ]
    if not normalized or any(not part for part in normalized):
        raise ValueError("identity parts must not be empty")
    digest = hashlib.sha256(canonical_json(normalized).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def document_module(path: Path) -> str:
    raw_module = re.sub(r"_(UM|IM)$", "", path.stem.removeprefix("RTD_"), flags=re.IGNORECASE)
    canonical_names = {
        "BASENXP": "BaseNXP",
        "CAN_43_FLEXCAN": "Can_43_FLEXCAN",
        "DIO": "Dio",
        "GPT": "Gpt",
        "LIN_43_LPUART_FLEXIO": "Lin_43_LPUART_FLEXIO",
        "MCL": "Mcl",
        "MCU": "Mcu",
        "PLATFORM": "Platform",
        "PORT": "Port",
        "RESOURCE": "Resource",
    }
    return canonical_names.get(raw_module.upper(), raw_module.upper())


def relative_document(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class ManualDocument:
    module: str
    kind: Literal["UM", "IM"]
    path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "module": self.module,
            "kind": self.kind,
            "document": relative_document(self.path),
        }


@dataclass(frozen=True)
class ManualPair:
    module: str
    user_manual: ManualDocument | None
    integration_manual: ManualDocument | None

    @property
    def complete(self) -> bool:
        return self.user_manual is not None and self.integration_manual is not None

    def as_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "complete": self.complete,
            "user_manual": self.user_manual.as_dict() if self.user_manual else None,
            "integration_manual": (
                self.integration_manual.as_dict() if self.integration_manual else None
            ),
        }


@dataclass(frozen=True)
class Section:
    title: str
    depth: int
    start_page: int
    end_page: int


def page_label(reader: Any, physical_page: int) -> str:
    try:
        labels = reader.page_labels
        return str(labels[physical_page - 1])
    except Exception:  # noqa: BLE001 - malformed optional page labels vary by PDF.
        return str(physical_page)


def source_document(path: Path, reader: Any) -> dict[str, object]:
    return {
        "document": relative_document(path),
        "sha256": file_sha256(path),
        "page_count": len(reader.pages),
    }


def source_span(reader: Any, section: Section) -> dict[str, object]:
    return {
        "physical_page": section.start_page,
        "page_label": page_label(reader, section.start_page),
        "section": section.title,
        "extraction_method": "pdf-outline",
        "confidence": 1.0,
    }


def section_as_dict(section: Section) -> dict[str, object]:
    return {
        "title": section.title,
        "depth": section.depth,
        "start_page": section.start_page,
        "end_page": section.end_page,
    }


def load_profile(module: str, explicit_path: Path | None = None) -> dict[str, object]:
    path = explicit_path or PROFILE_ROOT / f"{module}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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


def validate_payload(payload: object, schema_name: str) -> None:
    from jsonschema.validators import validator_for
    from referencing import Registry, Resource

    resources: list[tuple[str, Resource[Any]]] = []
    for path in SCHEMA_ROOT.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resource = Resource.from_contents(contents)
        resources.append((contents["$id"], resource))

    schema_path = SCHEMA_ROOT / schema_name
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator_class = validator_for(schema)
    validator_class.check_schema(schema)
    validator_class(schema, registry=Registry().with_resources(resources)).validate(payload)


def classify_rtd_document(path: Path) -> ManualDocument | None:
    match = DOCUMENT_PATTERN.fullmatch(path.name)
    if match is None:
        return None
    kind = match.group("kind").upper()
    if kind not in {"UM", "IM"}:
        return None
    return ManualDocument(
        module=document_module(path),
        kind=kind,
        path=path.resolve(),
    )


def discover_manual_pairs(docs: Path) -> list[ManualPair]:
    grouped: dict[str, dict[str, ManualDocument]] = {}
    for path in sorted(docs.glob("*.pdf")):
        document = classify_rtd_document(path)
        if document is None:
            continue
        kinds = grouped.setdefault(document.module, {})
        if document.kind in kinds:
            raise ValueError(f"duplicate {document.kind} manual for module {document.module}")
        kinds[document.kind] = document

    return [
        ManualPair(
            module=module,
            user_manual=kinds.get("UM"),
            integration_manual=kinds.get("IM"),
        )
        for module, kinds in sorted(grouped.items(), key=lambda item: item[0].casefold())
    ]


def normalize_page_lines(text: str, *, omit_figure_captions: bool = True) -> list[str]:
    text = text.replace("\x00", " ").replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    return [
        line
        for line in lines
        if line and not (omit_figure_captions and FIGURE_CAPTION_PATTERN.match(line))
    ]


def _flatten_outline(reader: Any, items: Iterable[Any], depth: int = 0) -> list[tuple[str, int, int]]:
    entries: list[tuple[str, int, int]] = []
    for item in items:
        if isinstance(item, list):
            entries.extend(_flatten_outline(reader, item, depth + 1))
            continue
        try:
            page = int(reader.get_destination_page_number(item)) + 1
        except Exception:  # noqa: BLE001, S112 - skip malformed optional outline entries.
            continue
        title = re.sub(r"\s+", " ", str(getattr(item, "title", item))).strip()
        if title:
            entries.append((title, depth, page))
    return entries


def outline_sections(reader: Any) -> list[Section]:
    try:
        entries = _flatten_outline(reader, reader.outline)
    except Exception:  # noqa: BLE001 - a missing outline is a supported input condition.
        return []

    page_count = len(reader.pages)
    sections: list[Section] = []
    for index, (title, depth, start_page) in enumerate(entries):
        end_page = page_count
        for _, next_depth, next_page in entries[index + 1 :]:
            if next_depth <= depth and next_page >= start_page:
                end_page = max(start_page, next_page - 1)
                break
        sections.append(
            Section(
                title=title,
                depth=depth,
                start_page=start_page,
                end_page=end_page,
            )
        )
    return sections