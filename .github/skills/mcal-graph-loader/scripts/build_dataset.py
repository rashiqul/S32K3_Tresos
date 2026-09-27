from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from build_chunks import CHUNKER_VERSION, build_chunks
from graph_common import (
    PROJECT_ROOT,
    SCHEMA_VERSION,
    TOOL_VERSION,
    canonical_json,
    file_sha256,
    stable_id,
    validate_payload,
    validate_payload_from_directory,
)
from normalize_corpus import normalize_corpus
from normalize_graph import add_unique, normalize_rtd_module, normalize_xdm_entries
from normalize_hardware import normalize_hardware_artifact

EXTRACTOR_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-pdf-json-extractor"
HARDWARE_EXTRACTOR_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-hardware-pdf-extractor"
REFERENCE_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-reference-s32k358"
EXTRACTOR_SCHEMA_ROOT = EXTRACTOR_ROOT / "schemas"
HARDWARE_SCHEMA_ROOT = HARDWARE_EXTRACTOR_ROOT / "schemas"
XDM_INSPECTOR = REFERENCE_ROOT / "scripts" / "xdm_inspect.py"

DEFAULT_SOURCE = PROJECT_ROOT / ".cache" / "mcal-pdf-json-extractor" / "structured"
DEFAULT_CORPUS = PROJECT_ROOT / ".cache" / "mcal-pdf-json-extractor" / "corpus"
DEFAULT_HARDWARE = PROJECT_ROOT / ".cache" / "mcal-hardware-pdf-extractor" / "hardware.json"
DEFAULT_CONFIG = PROJECT_ROOT / "config"
DEFAULT_OUTPUT = PROJECT_ROOT / ".cache" / "mcal-graph-loader" / "datasets"
DEFAULT_PROJECT_ID = "S32K358_EVB"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object: {path}")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise TypeError(f"expected JSON object at {path}:{line_number}")
            records.append(payload)
    return records


def inspect_xdm(paths: list[Path]) -> list[dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, str(XDM_INSPECTOR), *(str(path) for path in paths), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise ValueError(f"XDM inspection failed: {result.stderr.strip()}")
    payload = json.loads(result.stdout)
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise TypeError("XDM inspector output must be an array of objects")
    return payload


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for record in records:
            stream.write(canonical_json(record))
            stream.write("\n")


def extractor_modules(source_root: Path, manifest: dict[str, Any]) -> list[str]:
    if manifest.get("incomplete") or manifest.get("failures"):
        raise ValueError("extractor manifest contains incomplete modules or failures")
    modules = sorted({str(module) for key in ("parsed", "unchanged") for module in manifest[key]})
    if len(modules) != manifest["modules_selected"]:
        raise ValueError("extractor manifest module count does not match parsed/unchanged modules")
    for module in modules:
        for name in ("um.json", "im.json", "module.json"):
            if not (source_root / module / name).is_file():
                raise ValueError(f"missing extractor artifact: {module}/{name}")
    return modules


def source_artifacts(source_root: Path, modules: list[str]) -> list[Path]:
    return [source_root / "manifest.json"] + [
        source_root / module / name
        for module in modules
        for name in ("um.json", "im.json", "module.json")
    ]


def source_documents(module_payloads: list[tuple[dict[str, Any], dict[str, Any]]]) -> list[dict[str, Any]]:
    documents: dict[tuple[str, str], dict[str, Any]] = {}
    for um, im in module_payloads:
        for payload, source_type in ((um, "RTD-user-manual"), (im, "RTD-integration-manual")):
            source = payload["source"]
            key = (str(source["document"]), str(source["sha256"]))
            document = {
                "path": source["document"],
                "sha256": source["sha256"],
                "source_type": source_type,
            }
            if source.get("revision"):
                document["revision"] = source["revision"]
            documents[key] = document
    return sorted(documents.values(), key=lambda item: (item["path"], item["sha256"]))


def verify_document_hashes(documents: list[dict[str, Any]]) -> None:
    for document in documents:
        path = PROJECT_ROOT / document["path"]
        if file_sha256(path) != document["sha256"]:
            raise ValueError(f"source document hash changed: {document['path']}")


def validate_graph_records(
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> None:
    node_ids = {str(node["stable_id"]) for node in nodes}
    citation_ids = {
        str(node["stable_id"]) for node in nodes if node["label"] == "Citation"
    }
    if len(node_ids) != len(nodes):
        raise ValueError("duplicate graph node IDs")

    for node in nodes:
        validate_payload(node, "node.schema.json")
    for relationship in relationships:
        validate_payload(relationship, "relationship.schema.json")
        if relationship["from_id"] not in node_ids or relationship["to_id"] not in node_ids:
            raise ValueError(f"dangling structural relationship: {relationship['stable_id']}")
    for assertion in assertions:
        validate_payload(assertion, "assertion.schema.json")
        if assertion["subject_id"] not in node_ids or assertion["object_id"] not in node_ids:
            raise ValueError(f"dangling assertion endpoint: {assertion['stable_id']}")
        missing_citations = set(assertion["citation_ids"]) - citation_ids
        if missing_citations:
            raise ValueError(
                f"assertion {assertion['stable_id']} has missing citations: {sorted(missing_citations)}"
            )


def publish_dataset(
    staging: Path,
    dataset_directory: Path,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    try:
        staging.rename(dataset_directory)
        return {"status": "created", **manifest}
    except FileExistsError:
        existing = load_json(dataset_directory / "manifest.json")
        validate_payload(existing, "dataset.schema.json")
        if existing["dataset_id"] != manifest["dataset_id"] or existing["state"] != "complete":
            raise ValueError(f"concurrently published dataset is invalid: {dataset_directory}")
        shutil.rmtree(staging)
        return {"status": "unchanged", **existing}


def build_dataset(
    source_root: Path,
    corpus_root: Path,
    hardware_path: Path,
    config_root: Path,
    output_root: Path,
    project_id: str,
) -> dict[str, Any]:
    extractor_manifest = load_json(source_root / "manifest.json")
    modules = extractor_modules(source_root, extractor_manifest)
    payloads: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for module in modules:
        um = load_json(source_root / module / "um.json")
        im = load_json(source_root / module / "im.json")
        reconciled = load_json(source_root / module / "module.json")
        validate_payload_from_directory(um, EXTRACTOR_SCHEMA_ROOT, "um.schema.json")
        validate_payload_from_directory(im, EXTRACTOR_SCHEMA_ROOT, "im.schema.json")
        validate_payload_from_directory(reconciled, EXTRACTOR_SCHEMA_ROOT, "module.schema.json")
        payloads.append((um, im))

    corpus_manifest = load_json(corpus_root / "manifest.json")
    validate_payload_from_directory(
        corpus_manifest, EXTRACTOR_SCHEMA_ROOT, "corpus-manifest.schema.json"
    )
    if corpus_manifest["state"] != "complete" or corpus_manifest["failures"]:
        raise ValueError("PDF corpus manifest is not complete")
    corpus_documents = load_jsonl(corpus_root / "documents.jsonl")
    corpus_source_chunks = load_jsonl(corpus_root / "chunks.jsonl")
    for document in corpus_documents:
        validate_payload_from_directory(
            document, EXTRACTOR_SCHEMA_ROOT, "corpus-document.schema.json"
        )
    for chunk in corpus_source_chunks:
        validate_payload_from_directory(chunk, EXTRACTOR_SCHEMA_ROOT, "corpus-chunk.schema.json")
    if len(corpus_documents) != corpus_manifest["documents_extracted"]:
        raise ValueError("PDF corpus document count does not match its manifest")
    if len(corpus_source_chunks) != corpus_manifest["chunks"]:
        raise ValueError("PDF corpus chunk count does not match its manifest")

    hardware_artifact = load_json(hardware_path)
    validate_payload_from_directory(
        hardware_artifact, HARDWARE_SCHEMA_ROOT, "hardware-extract.schema.json"
    )
    if hardware_artifact["state"] != "complete" or hardware_artifact["failures"]:
        raise ValueError("hardware extraction artifact is not complete")

    documents = source_documents(payloads)
    verify_document_hashes(documents)
    for source in hardware_artifact["documents"].values():
        if not any(
            item["path"] == source["document"] and item["sha256"] == source["sha256"]
            for item in documents
        ):
            documents.append(
                {
                    "path": source["document"],
                    "sha256": source["sha256"],
                    "source_type": source["source_type"],
                }
            )
    artifacts = source_artifacts(source_root, modules)
    artifact_hashes = {path: file_sha256(path) for path in artifacts}
    corpus_artifacts = [
        corpus_root / "manifest.json",
        corpus_root / "documents.jsonl",
        corpus_root / "chunks.jsonl",
    ]
    corpus_artifact_hashes = {path: file_sha256(path) for path in corpus_artifacts}
    hardware_artifact_hash = file_sha256(hardware_path)
    for source in corpus_manifest["source_hashes"]:
        if file_sha256(PROJECT_ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"PDF corpus source changed: {source['path']}")
    for source in corpus_documents:
        if not any(
            item["path"] == source["path"] and item["sha256"] == source["sha256"]
            for item in documents
        ):
            documents.append(
                {
                    "path": source["path"],
                    "sha256": source["sha256"],
                    "source_type": source["source_type"],
                }
            )
    config_paths = sorted(config_root.glob("*.xdm"))
    if not config_paths:
        raise ValueError(f"no XDM files found under {config_root}")
    xdm_hashes = {path: file_sha256(path) for path in config_paths}
    identity = {
        "schema_version": SCHEMA_VERSION,
        "normalizer_version": TOOL_VERSION,
        "chunker_version": CHUNKER_VERSION,
        "extractor_schema_version": extractor_manifest["schema_version"],
        "extractor_tool_version": extractor_manifest["tool_version"],
        "corpus_tool_version": corpus_manifest["tool_version"],
        "artifacts": [
            [path.relative_to(source_root).as_posix(), digest]
            for path, digest in sorted(artifact_hashes.items(), key=lambda item: item[0].as_posix())
        ],
        "corpus_artifacts": [
            [path.relative_to(corpus_root).as_posix(), digest]
            for path, digest in sorted(
                corpus_artifact_hashes.items(), key=lambda item: item[0].as_posix()
            )
        ],
        "xdm": [
            [path.relative_to(PROJECT_ROOT).as_posix(), digest]
            for path, digest in sorted(xdm_hashes.items(), key=lambda item: item[0].as_posix())
        ],
        "hardware_artifact": [
            hardware_path.relative_to(PROJECT_ROOT).as_posix(),
            hardware_artifact_hash,
        ],
        "hardware_tool_version": hardware_artifact["tool_version"],
        "hardware_profile": hardware_artifact["profile"],
        "hardware_documents": [
            [source["document"], source["sha256"]]
            for source in sorted(
                hardware_artifact["documents"].values(), key=lambda item: str(item["document"])
            )
        ],
    }
    dataset_id = stable_id("dataset", canonical_json(identity))
    dataset_directory = output_root / dataset_id.removeprefix("dataset:")
    if dataset_directory.exists():
        manifest = load_json(dataset_directory / "manifest.json")
        validate_payload(manifest, "dataset.schema.json")
        if manifest["dataset_id"] != dataset_id or manifest["state"] != "complete":
            raise ValueError(f"existing dataset is invalid: {dataset_directory}")
        return {"status": "unchanged", **manifest}

    output_root.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=output_root))
    try:
        copied_artifacts: list[dict[str, str]] = []
        hardware_destination = staging / "sources" / "hardware" / hardware_path.name
        hardware_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(hardware_path, hardware_destination)
        if (
            file_sha256(hardware_destination) != hardware_artifact_hash
            or file_sha256(hardware_path) != hardware_artifact_hash
        ):
            raise ValueError("hardware extraction artifact changed during staging")
        copied_artifacts.append(
            {
                "path": hardware_destination.relative_to(staging).as_posix(),
                "sha256": hardware_artifact_hash,
                "kind": "hardware-extract",
            }
        )
        for path in artifacts:
            relative = path.relative_to(source_root)
            destination = staging / "sources" / "rtd" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            digest = file_sha256(destination)
            if digest != artifact_hashes[path] or file_sha256(path) != artifact_hashes[path]:
                raise ValueError(f"extractor artifact changed during staging: {relative.as_posix()}")
            copied_artifacts.append(
                {"path": destination.relative_to(staging).as_posix(), "sha256": digest, "kind": "rtd-json"}
            )

        for path in corpus_artifacts:
            relative = path.relative_to(corpus_root)
            destination = staging / "sources" / "corpus" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            digest = file_sha256(destination)
            if digest != corpus_artifact_hashes[path] or file_sha256(path) != corpus_artifact_hashes[path]:
                raise ValueError(f"corpus artifact changed during staging: {relative.as_posix()}")
            copied_artifacts.append(
                {
                    "path": destination.relative_to(staging).as_posix(),
                    "sha256": digest,
                    "kind": "pdf-corpus",
                }
            )

        for path in config_paths:
            relative = path.relative_to(PROJECT_ROOT)
            destination = staging / "sources" / "xdm" / path.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            digest = file_sha256(destination)
            if digest != xdm_hashes[path] or file_sha256(path) != xdm_hashes[path]:
                raise ValueError(f"XDM source changed during staging: {relative.as_posix()}")
            copied_artifacts.append(
                {"path": destination.relative_to(staging).as_posix(), "sha256": digest, "kind": "xdm-source"}
            )
            documents.append(
                {"path": relative.as_posix(), "sha256": digest, "source_type": "tresos-xdm"}
            )

        nodes: dict[str, dict[str, Any]] = {}
        relationships: dict[str, dict[str, Any]] = {}
        assertions: dict[str, dict[str, Any]] = {}
        for um, im in payloads:
            module_nodes, module_relationships, module_assertions = normalize_rtd_module(
                dataset_id, um, im
            )
            for record in module_nodes:
                add_unique(nodes, record)
            for record in module_relationships:
                add_unique(relationships, record)
            for record in module_assertions:
                add_unique(assertions, record)

        xdm_entries = inspect_xdm(config_paths)
        xdm_nodes, xdm_relationships, xdm_assertions = normalize_xdm_entries(
            dataset_id,
            project_id,
            xdm_entries,
            nodes.values(),
        )
        for record in xdm_nodes:
            add_unique(nodes, record)
        for record in xdm_relationships:
            add_unique(relationships, record)
        for record in xdm_assertions:
            add_unique(assertions, record)

        hardware_nodes, hardware_relationships, hardware_assertions = normalize_hardware_artifact(
            dataset_id,
            hardware_artifact,
            list(nodes.values()),
        )
        for record in hardware_nodes:
            add_unique(nodes, record)
        for record in hardware_relationships:
            add_unique(relationships, record)
        for record in hardware_assertions:
            add_unique(assertions, record)

        evidence_nodes = sorted(nodes.values(), key=lambda item: item["stable_id"])
        evidence_relationships = sorted(
            relationships.values(), key=lambda item: item["stable_id"]
        )
        sorted_assertions = sorted(assertions.values(), key=lambda item: item["stable_id"])
        chunks = build_chunks(
            dataset_id, evidence_nodes, evidence_relationships, sorted_assertions
        )
        corpus_nodes, corpus_relationships, corpus_chunks = normalize_corpus(
            dataset_id, corpus_documents, corpus_source_chunks, nodes.values()
        )
        for record in corpus_nodes:
            add_unique(nodes, record)
        for record in corpus_relationships:
            add_unique(relationships, record)
        chunks.extend(corpus_chunks)
        chunks.sort(key=lambda item: item["chunk_id"])
        sorted_nodes = sorted(nodes.values(), key=lambda item: item["stable_id"])
        sorted_relationships = sorted(relationships.values(), key=lambda item: item["stable_id"])
        validate_graph_records(sorted_nodes, sorted_relationships, sorted_assertions)
        for chunk in chunks:
            validate_payload(chunk, "chunk.schema.json")

        graph_paths = {
            "nodes": staging / "graph" / "nodes.jsonl",
            "relationships": staging / "graph" / "relationships.jsonl",
            "assertions": staging / "graph" / "assertions.jsonl",
            "xdm_snapshot": staging / "graph" / "xdm-snapshot.json",
            "chunks": staging / "search" / "chunks.jsonl",
        }
        write_jsonl(graph_paths["nodes"], sorted_nodes)
        write_jsonl(graph_paths["relationships"], sorted_relationships)
        write_jsonl(graph_paths["assertions"], sorted_assertions)
        write_json(graph_paths["xdm_snapshot"], xdm_entries)
        write_jsonl(graph_paths["chunks"], chunks)
        for kind, path in graph_paths.items():
            copied_artifacts.append(
                {
                    "path": path.relative_to(staging).as_posix(),
                    "sha256": file_sha256(path),
                    "kind": kind.replace("_", "-"),
                }
            )

        timestamp = datetime.now(UTC).isoformat()
        manifest: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "state": "complete",
            "created_at": timestamp,
            "completed_at": timestamp,
            "normalizer_version": TOOL_VERSION,
            "chunker_version": CHUNKER_VERSION,
            "sources": sorted(documents, key=lambda item: item["path"]),
            "artifacts": sorted(copied_artifacts, key=lambda item: item["path"]),
            "counts": {
                "rtd_modules": len(modules),
                "xdm_files": len(config_paths),
                "hardware_profiles": 1,
                "pdf_documents": len(corpus_documents),
                "source_page_chunks": len(corpus_source_chunks),
                "chunks": len(chunks),
                "nodes": len(sorted_nodes),
                "structural_relationships": len(sorted_relationships),
                "assertions": len(sorted_assertions),
                "verified_assertions": sum(
                    record["assertion_status"] == "verified" for record in sorted_assertions
                ),
                "inferred_assertions": sum(
                    record["assertion_status"] == "inferred" for record in sorted_assertions
                ),
                "unresolved_assertions": sum(
                    record["assertion_status"] == "unresolved" for record in sorted_assertions
                ),
            },
            "warnings": list(extractor_manifest["warnings"]),
            "failures": [],
        }
        validate_payload(manifest, "dataset.schema.json")
        write_json(staging / "manifest.json", manifest)
        return publish_dataset(staging, dataset_directory, manifest)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Build an immutable MCAL graph dataset")
    command.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    command.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    command.add_argument("--hardware", type=Path, default=DEFAULT_HARDWARE)
    command.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    command.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        payload = build_dataset(
            arguments.source.resolve(),
            arguments.corpus.resolve(),
            arguments.hardware.resolve(),
            arguments.config.resolve(),
            arguments.output.resolve(),
            arguments.project_id,
        )
        summary = {
            "status": payload["status"],
            "dataset_id": payload["dataset_id"],
            "state": payload["state"],
            "counts": payload["counts"],
            "warning_count": len(payload["warnings"]),
            "failure_count": len(payload["failures"]),
        }
        print(json.dumps(summary, indent=2, ensure_ascii=True))
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())