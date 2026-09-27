from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from rtd_pdf_common import (
    DEFAULT_DOCS,
    SCHEMA_VERSION,
    TOOL_VERSION,
    Section,
    classify_rtd_document,
    load_profile,
    normalize_page_lines,
    outline_sections,
    page_label,
    section_as_dict,
    source_document,
    validate_payload,
    write_json_atomic,
)

ITEM_HEADING = re.compile(
    r"^(?P<section>\d+(?:\.\d+)*)\s+(?P<kind>Parameter|Container)\s+"
    r"(?P<identifier>[A-Za-z][A-Za-z0-9_]*)$"
)
PROPERTY_NAMES = {
    "type": "data_type",
    "lowerMultiplicity": "lower_multiplicity",
    "upperMultiplicity": "upper_multiplicity",
    "defaultValue": "default",
    "min": "minimum",
    "max": "maximum",
}


def configuration_range(sections: list[Section], patterns: list[str]) -> Section | None:
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    return next(
        (section for section in sections if any(pattern.search(section.title) for pattern in compiled)),
        None,
    )


def _parse_scalar(value: str) -> object:
    if value.casefold() == "true":
        return True
    if value.casefold() == "false":
        return False
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def _finish_item(item: dict[str, Any], body: list[str]) -> dict[str, Any]:
    property_index = body.index("Property Value") if "Property Value" in body else len(body)
    description = " ".join(body[:property_index]).strip()
    if description:
        item["description"] = description

    attributes = item["attributes"]
    configuration_classes: set[str] = set()
    for line in body[property_index + 1 :]:
        for config_class in re.findall(r"VARIANT-[A-Z-]+:\s*([A-Z-]+)", line):
            configuration_classes.add(config_class)
        name, separator, value = line.partition(" ")
        target = PROPERTY_NAMES.get(name)
        if not separator or target is None or not value.strip():
            continue
        parsed = _parse_scalar(value.strip())
        if target in {"minimum", "maximum"} and not isinstance(parsed, (int, float)):
            continue
        attributes[target] = parsed
    if configuration_classes:
        attributes["configuration_classes"] = sorted(configuration_classes)
    lower = attributes.pop("lower_multiplicity", None)
    upper = attributes.pop("upper_multiplicity", None)
    if lower is not None or upper is not None:
        attributes["multiplicity"] = f"{lower if lower is not None else '?'}..{upper if upper is not None else '?'}"
    return item


def extract_configuration_items(reader: Any, section: Section) -> tuple[list[dict[str, Any]], list[dict[str, object]]]:
    items: list[dict[str, Any]] = []
    warnings: list[dict[str, object]] = []
    current: dict[str, Any] | None = None
    body: list[str] = []

    for physical_page in range(section.start_page, section.end_page + 1):
        try:
            lines = normalize_page_lines(reader.pages[physical_page - 1].extract_text() or "")
        except Exception as error:  # noqa: BLE001 - isolate malformed individual pages.
            warnings.append(
                {"code": "page-extraction-failed", "message": str(error), "physical_page": physical_page}
            )
            continue
        for line in lines:
            match = ITEM_HEADING.fullmatch(line)
            if match is None:
                if current is not None:
                    body.append(line)
                continue
            if current is not None:
                items.append(_finish_item(current, body))
            raw_title = match.group(0)
            current = {
                "kind": match.group("kind").casefold(),
                "identifier": match.group("identifier"),
                "raw_title": raw_title,
                "attributes": {},
                "source": {
                    "physical_page": physical_page,
                    "page_label": page_label(reader, physical_page),
                    "section": raw_title,
                    "extraction_method": "page-text",
                    "confidence": 0.95,
                },
                "extensions": {"section_number": match.group("section")},
            }
            body = []

    if current is not None:
        items.append(_finish_item(current, body))
    return items, warnings


def parse_user_manual(path: Path, profile_path: Path | None = None) -> dict[str, object]:
    from pypdf import PdfReader

    document = classify_rtd_document(path)
    if document is None or document.kind != "UM":
        raise ValueError(f"not an RTD user manual: {path}")
    reader = PdfReader(path)
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("PDF is encrypted and cannot be opened without a password")

    profile = load_profile(document.module, profile_path)
    patterns = profile.get("um_configuration_sections", [r"^\d+\s+Configuration Parameters$"])
    if not isinstance(patterns, list) or not all(isinstance(pattern, str) for pattern in patterns):
        raise TypeError("profile um_configuration_sections must be a list of strings")

    sections = outline_sections(reader)
    config_section = configuration_range(sections, patterns)
    warnings: list[dict[str, object]] = []
    if config_section is None:
        items: list[dict[str, Any]] = []
        warnings.append(
            {"code": "configuration-section-not-found", "message": "No configuration section matched the profile"}
        )
        selected_sections: list[Section] = []
    else:
        items, page_warnings = extract_configuration_items(reader, config_section)
        warnings.extend(page_warnings)
        selected_sections = [
            section
            for section in sections
            if config_section.start_page <= section.start_page <= config_section.end_page
        ]

    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "kind": "UM",
        "module": document.module,
        "source": source_document(path, reader),
        "sections": [section_as_dict(section) for section in selected_sections],
        "configuration_items": items,
        "warnings": warnings,
    }
    validate_payload(payload, "um.schema.json")
    return payload


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Extract structured configuration data from an RTD UM")
    source = command.add_mutually_exclusive_group(required=True)
    source.add_argument("--module")
    source.add_argument("--document", type=Path)
    command.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    command.add_argument("--profile", type=Path)
    command.add_argument("--output", type=Path)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    path = arguments.document or arguments.docs / f"RTD_{arguments.module}_UM.pdf"
    try:
        payload = parse_user_manual(path.resolve(), arguments.profile)
        if arguments.output:
            write_json_atomic(arguments.output.resolve(), payload)
        if arguments.json or not arguments.output:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print(f"extracted {len(payload['configuration_items'])} configuration items")
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())