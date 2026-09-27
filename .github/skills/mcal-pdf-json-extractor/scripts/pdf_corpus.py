from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from rtd_pdf_common import (
    DEFAULT_DOCS,
    PROJECT_ROOT,
    SCHEMA_VERSION,
    document_module,
    file_sha256,
    normalize_page_lines,
    outline_sections,
    page_label,
    relative_document,
    stable_id,
    validate_payload,
    write_json_atomic,
)

CORPUS_TOOL_VERSION = "0.1.0"
DEFAULT_OUTPUT = PROJECT_ROOT / ".cache" / "mcal-pdf-json-extractor" / "corpus"
DEFAULT_MAX_CHARS = 6000
DEFAULT_OVERLAP_CHARS = 500


def classify_document(path: Path) -> tuple[str, str]:
    name = path.stem
    upper = name.upper()
    rtd = re.fullmatch(r"RTD_(.+)_(UM|IM)", name, flags=re.IGNORECASE)
    if rtd:
        module = document_module(path)
        source_type = "RTD-user-manual" if rtd.group(2).upper() == "UM" else "RTD-integration-manual"
        return source_type, module
    if upper == "S32K3XXRM":
        return "reference-manual", "Hardware"
    if "DATASHEET" in upper:
        return "datasheet", "Hardware"
    if "EVB" in upper and "HWUM" in upper:
        return "board-manual", "Board"
    if upper.startswith("AN"):
        return "application-note", "ApplicationNote"
    if upper.startswith("HOWTO_"):
        return "application-guide", "ApplicationGuide"
    return "supplemental-manual", "Unclassified"


def split_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if max_chars < 1 or overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("chunk sizes require max_chars > overlap_chars >= 0")
    if len(text) <= max_chars:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", start, end), text.rfind(" ", start, end))
            if boundary > start + max_chars // 2:
                end = boundary
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(start + 1, end - overlap_chars)
    return chunks


def heading_path_for_page(sections: list[Any], physical_page: int) -> list[str]:
    path: list[str] = []
    for section in sections:
        if section.start_page <= physical_page <= section.end_page:
            path = path[: section.depth]
            path.append(section.title)
    return path


def extract_document(
    path: Path,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    if reader.is_encrypted and reader.decrypt("") == 0:
        raise ValueError(f"PDF is encrypted and cannot be opened: {path}")
    document = relative_document(path)
    digest = file_sha256(path)
    document_id = stable_id("document", document, digest)
    source_type, module = classify_document(path)
    sections = outline_sections(reader)
    document_record = {
        "schema_version": SCHEMA_VERSION,
        "document_id": document_id,
        "path": document,
        "sha256": digest,
        "page_count": len(reader.pages),
        "source_type": source_type,
        "module": module,
    }
    chunks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    for physical_page, page in enumerate(reader.pages, 1):
        if physical_page == 1 or physical_page % 100 == 0:
            print(
                f"Corpus: {path.name} page {physical_page}/{len(reader.pages)}",
                file=sys.stderr,
                flush=True,
            )
        try:
            text = "\n".join(normalize_page_lines(page.extract_text() or "", omit_figure_captions=False))
        except Exception as error:  # noqa: BLE001 - isolate malformed individual pages.
            warnings.append({"document": document, "physical_page": physical_page, "error": str(error)})
            continue
        if not text:
            warnings.append({"document": document, "physical_page": physical_page, "error": "no extractable text"})
            continue
        heading_path = heading_path_for_page(sections, physical_page)
        parts = split_text(text, max_chars, overlap_chars)
        page_ids = [
            stable_id("source-chunk", document_id, physical_page, ordinal, CORPUS_TOOL_VERSION)
            for ordinal in range(len(parts))
        ]
        for ordinal, (source_chunk_id, part) in enumerate(zip(page_ids, parts, strict=True)):
            chunks.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "source_chunk_id": source_chunk_id,
                    "document_id": document_id,
                    "document": document,
                    "document_sha256": digest,
                    "source_type": source_type,
                    "module": module,
                    "physical_page": physical_page,
                    "page_label": page_label(reader, physical_page),
                    "heading_path": heading_path,
                    "chunk_ordinal": ordinal,
                    "previous_chunk_id": page_ids[ordinal - 1] if ordinal else None,
                    "next_chunk_id": page_ids[ordinal + 1] if ordinal + 1 < len(page_ids) else None,
                    "text": part,
                    "extraction_method": "page-text",
                }
            )
    validate_payload(document_record, "corpus-document.schema.json")
    for chunk in chunks:
        validate_payload(chunk, "corpus-chunk.schema.json")
    return document_record, chunks, warnings


def write_jsonl_atomic(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            for record in records:
                stream.write(json.dumps(record, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
                stream.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def extract_corpus(docs: Path, output: Path) -> dict[str, Any]:
    paths = sorted(docs.glob("*.pdf"), key=lambda item: item.name.casefold())
    documents: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    source_hashes = [
        {"path": relative_document(path), "sha256": file_sha256(path)} for path in paths
    ]
    for document_number, path in enumerate(paths, 1):
        print(
            f"Corpus: document {document_number}/{len(paths)} {path.name}",
            file=sys.stderr,
            flush=True,
        )
        try:
            document, document_chunks, document_warnings = extract_document(path)
            documents.append(document)
            chunks.extend(document_chunks)
            warnings.extend(document_warnings)
        except Exception as error:  # noqa: BLE001 - report all malformed corpus documents.
            failures.append({"document": relative_document(path), "error": str(error)})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": CORPUS_TOOL_VERSION,
        "state": "failed" if failures else "complete",
        "documents_found": len(paths),
        "documents_extracted": len(documents),
        "chunks": len(chunks),
        "source_hashes": source_hashes,
        "warnings": warnings,
        "failures": failures,
    }
    validate_payload(manifest, "corpus-manifest.schema.json")
    write_jsonl_atomic(output / "documents.jsonl", documents)
    write_jsonl_atomic(output / "chunks.jsonl", chunks)
    write_json_atomic(output / "manifest.json", manifest)
    return manifest


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Extract the complete local PDF search corpus")
    command.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        payload = extract_corpus(arguments.docs.resolve(), arguments.output.resolve())
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 1 if payload["failures"] else 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())