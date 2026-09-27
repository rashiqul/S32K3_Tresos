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
    source_span,
    validate_payload,
    write_json_atomic,
)

EXCLUSIVE_AREA_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_]*_EXCLUSIVE_AREA_[0-9]+")
FUNCTION_PATTERN = re.compile(
    r"(?:is\s*)?used\s+in\s+function\s+([A-Za-z][A-Za-z0-9_]*?)(?=to\s+protect|\s|[.,;)])",
    re.IGNORECASE,
)
DEFAULT_TOPICS = {
    "exclusive-area": ["Exclusive areas?"],
    "interrupt": ["ISR", "interrupt"],
    "dependency": ["dependencies"],
    "api": ["API Requirements"],
    "callback": ["Callbacks?", "Notifications?"],
    "memory": ["Memory allocation"],
    "integration": ["Integration Steps"],
    "user-mode": ["User Mode"],
    "partition": ["MultiPartition"],
    "hardware": ["Peripheral Hardware Requirements"],
}
TOPIC_IDENTIFIER_PATTERNS = {
    "interrupt": [re.compile(r"\bISR\s*\(\s*([A-Za-z][A-Za-z0-9_]*)\s*\)")],
    "api": [re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\(\)")],
    "callback": [re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s*\(\)")],
    "memory": [re.compile(r"\b([A-Za-z][A-Za-z0-9_]*_MemMap\.h)\b")],
    "dependency": [
        re.compile(r"\b([A-Za-z][A-Za-z0-9_]*)\s+Driver Dependencies\b", re.IGNORECASE)
    ],
}


def topic_identifiers(reader: Any, section: Section, category: str) -> list[str]:
    patterns = TOPIC_IDENTIFIER_PATTERNS.get(category, [])
    if not patterns:
        return []
    identifiers: set[str] = set()
    for physical_page in range(section.start_page, section.end_page + 1):
        text = " ".join(
            normalize_page_lines(reader.pages[physical_page - 1].extract_text() or "")
        )
        for pattern in patterns:
            identifiers.update(pattern.findall(text))
    return sorted(identifiers, key=str.casefold)


def classify_topics(
    reader: Any, sections: list[Section], topic_patterns: dict[str, list[str]]
) -> list[dict[str, object]]:
    compiled = {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in topic_patterns.items()
    }
    topics: list[dict[str, object]] = []
    for section in sections:
        category = next(
            (
                name
                for name, patterns in compiled.items()
                if any(pattern.search(section.title) for pattern in patterns)
            ),
            None,
        )
        if category is None:
            continue
        topics.append(
            {
                "category": category,
                "title": section.title,
                "identifiers": topic_identifiers(reader, section, category),
                "source": source_span(reader, section),
                "extensions": {
                    "start_page": section.start_page,
                    "end_page": section.end_page,
                },
            }
        )
    return topics


def extract_exclusive_areas(
    reader: Any, sections: list[Section]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    relevant = [
        section
        for section in sections
        if re.search(r"Exclusive areas?", section.title, re.IGNORECASE)
    ]
    areas: dict[str, dict[str, object]] = {}
    warnings: list[dict[str, object]] = []
    visited_pages: set[int] = set()
    for section in relevant:
        for physical_page in range(section.start_page, section.end_page + 1):
            if physical_page in visited_pages:
                continue
            visited_pages.add(physical_page)
            try:
                lines = normalize_page_lines(reader.pages[physical_page - 1].extract_text() or "")
            except Exception as error:  # noqa: BLE001 - isolate malformed individual pages.
                warnings.append(
                    {"code": "page-extraction-failed", "message": str(error), "physical_page": physical_page}
                )
                continue
            text = " ".join(lines)
            matches = list(EXCLUSIVE_AREA_PATTERN.finditer(text))
            for index, match in enumerate(matches):
                identifier = match.group(0)
                next_start = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                uses = FUNCTION_PATTERN.findall(text[match.end() : next_start])
                area = areas.setdefault(
                    identifier,
                    {
                        "identifier": identifier,
                        "uses": [],
                        "source": {
                            "physical_page": physical_page,
                            "page_label": page_label(reader, physical_page),
                            "section": section.title,
                            "extraction_method": "page-text",
                            "confidence": 0.9,
                        },
                        "extensions": {},
                    },
                )
                area["uses"] = sorted(set(area["uses"]) | set(uses), key=str.casefold)
    return sorted(areas.values(), key=lambda area: str(area["identifier"]).casefold()), warnings


def parse_integration_manual(path: Path, profile_path: Path | None = None) -> dict[str, object]:
    from pypdf import PdfReader

    document = classify_rtd_document(path)
    if document is None or document.kind != "IM":
        raise ValueError(f"not an RTD integration manual: {path}")
    reader = PdfReader(path)
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError("PDF is encrypted and cannot be opened without a password")

    profile = load_profile(document.module, profile_path)
    topic_patterns = profile.get("im_topics", DEFAULT_TOPICS)
    if not isinstance(topic_patterns, dict):
        raise TypeError("profile im_topics must be an object")
    sections = outline_sections(reader)
    topics = classify_topics(reader, sections, topic_patterns)
    exclusive_areas, warnings = extract_exclusive_areas(reader, sections)
    if not sections:
        warnings.append({"code": "outline-not-found", "message": "No usable PDF outline was found"})

    selected_titles = {topic["title"] for topic in topics}
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "kind": "IM",
        "module": document.module,
        "source": source_document(path, reader),
        "sections": [section_as_dict(section) for section in sections if section.title in selected_titles],
        "topics": topics,
        "exclusive_areas": exclusive_areas,
        "warnings": warnings,
    }
    validate_payload(payload, "im.schema.json")
    return payload


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Extract structured integration data from an RTD IM")
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
    path = arguments.document or arguments.docs / f"RTD_{arguments.module}_IM.pdf"
    try:
        payload = parse_integration_manual(path.resolve(), arguments.profile)
        if arguments.output:
            write_json_atomic(arguments.output.resolve(), payload)
        if arguments.json or not arguments.output:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print(
                f"extracted {len(payload['topics'])} topics and "
                f"{len(payload['exclusive_areas'])} exclusive areas"
            )
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())