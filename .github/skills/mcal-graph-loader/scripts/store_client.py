from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from graph_common import PROJECT_ROOT, file_sha256, validate_payload

DEFAULT_DATASETS = PROJECT_ROOT / ".cache" / "mcal-graph-loader" / "datasets"
DEFAULT_ENV = PROJECT_ROOT / "infra" / "search" / ".env"
ACTIVE_DATASET = PROJECT_ROOT / ".cache" / "mcal-graph-loader" / "active-dataset.json"
SEARCH_ALIAS = "mcal-reference-chunks"


def load_env(path: Path = DEFAULT_ENV) -> dict[str, str]:
    if not path.is_file():
        raise ValueError(f"missing environment file: {path}")
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    password = values.get("NEO4J_PASSWORD", "")
    if not password or password == "change-this-local-password":
        raise ValueError("set a non-example NEO4J_PASSWORD in infra/search/.env")
    return values


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError(f"expected JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise TypeError(f"expected JSON object at {path}:{line_number}")
        records.append(record)
    return records


def batches(records: list[dict[str, Any]], size: int = 500) -> Iterable[list[dict[str, Any]]]:
    for offset in range(0, len(records), size):
        yield records[offset : offset + size]


def resolve_dataset(dataset: Path | None, root: Path = DEFAULT_DATASETS) -> tuple[Path, dict[str, Any]]:
    if dataset is not None:
        directory = dataset.resolve()
        manifest = load_json(directory / "manifest.json")
    else:
        candidates: list[tuple[str, Path, dict[str, Any]]] = []
        for manifest_path in root.glob("*/manifest.json"):
            manifest = load_json(manifest_path)
            if manifest.get("state") == "complete":
                candidates.append((str(manifest["completed_at"]), manifest_path.parent, manifest))
        if not candidates:
            raise ValueError(f"no complete datasets found under {root}")
        _, directory, manifest = max(candidates, key=lambda item: item[0])
    validate_payload(manifest, "dataset.schema.json")
    if manifest["state"] != "complete":
        raise ValueError(f"dataset is not complete: {directory}")
    for artifact in manifest["artifacts"]:
        path = directory / artifact["path"]
        if not path.is_file() or file_sha256(path) != artifact["sha256"]:
            raise ValueError(f"dataset artifact failed hash validation: {artifact['path']}")
    return directory, manifest


def request_json(
    method: str,
    url: str,
    payload: object | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Accept": "application/json", **(headers or {})}
    if data is not None:
        request_headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise ValueError(f"HTTP {error.code} from {url}: {detail}") from error
    return json.loads(body) if body else {}


class Neo4jClient:
    def __init__(self, environment: dict[str, str]) -> None:
        port = environment.get("NEO4J_HTTP_PORT", "7474")
        self.url = f"http://127.0.0.1:{port}/db/neo4j/tx/commit"
        token = base64.b64encode(
            f"neo4j:{environment['NEO4J_PASSWORD']}".encode()
        ).decode("ascii")
        self.headers = {"Authorization": f"Basic {token}"}

    def query(self, statement: str, parameters: dict[str, Any] | None = None) -> list[list[Any]]:
        response = request_json(
            "POST",
            self.url,
            {"statements": [{"statement": statement, "parameters": parameters or {}}]},
            self.headers,
        )
        if response.get("errors"):
            raise ValueError(f"Neo4j query failed: {response['errors']}")
        results = response.get("results", [])
        if not results:
            return []
        return [row["row"] for row in results[0].get("data", [])]


class ElasticsearchClient:
    def __init__(self, environment: dict[str, str]) -> None:
        port = environment.get("ELASTICSEARCH_HTTP_PORT", "9200")
        self.url = f"http://127.0.0.1:{port}"

    def json(self, method: str, path: str, payload: object | None = None) -> Any:
        return request_json(method, f"{self.url}{path}", payload)

    def bulk(self, operations: list[dict[str, Any]]) -> None:
        body = b"".join(
            json.dumps(operation, separators=(",", ":")).encode("utf-8") + b"\n"
            for operation in operations
        )
        request = urllib.request.Request(
            f"{self.url}/_bulk",
            data=body,
            headers={"Content-Type": "application/x-ndjson"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"Elasticsearch bulk request failed: {detail}") from error
        if payload.get("errors"):
            failures = [item for item in payload["items"] if item["index"].get("error")]
            raise ValueError(f"Elasticsearch bulk indexing failed: {failures[:3]}")


def index_name(dataset_id: str) -> str:
    return f"mcal-reference-chunks-{dataset_id.removeprefix('dataset:')}"


def neo4j_properties(properties: dict[str, Any]) -> dict[str, Any]:
    converted: dict[str, Any] = {}
    for key, value in properties.items():
        if isinstance(value, dict) or (
            isinstance(value, list) and any(isinstance(item, (dict, list)) for item in value)
        ):
            converted[key] = json.dumps(value, sort_keys=True, separators=(",", ":"))
        elif value is not None:
            converted[key] = value
    return converted