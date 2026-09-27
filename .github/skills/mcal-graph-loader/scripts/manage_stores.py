from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from graph_common import PROJECT_ROOT
from store_client import (
    ACTIVE_DATASET,
    SEARCH_ALIAS,
    ElasticsearchClient,
    Neo4jClient,
    batches,
    index_name,
    load_env,
    neo4j_properties,
    read_jsonl,
    resolve_dataset,
)

NODE_LABELS = {
    "Term",
    "McalModule",
    "ConfigurationDefinition",
    "ConfigurationContainerDefinition",
    "IntegrationTopic",
    "ExclusiveArea",
    "Api",
    "XdmInstance",
    "Peripheral",
    "Register",
    "RegisterField",
    "Constraint",
    "Device",
    "Document",
    "Citation",
    "GeneratedSymbol",
}
RELATIONSHIP_TYPES = {"BELONGS_TO", "HAS_CITATION"}


def graph_records(directory: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    return (
        read_jsonl(directory / "graph" / "nodes.jsonl"),
        read_jsonl(directory / "graph" / "relationships.jsonl"),
        read_jsonl(directory / "graph" / "assertions.jsonl"),
    )


def create_constraints(client: Neo4jClient) -> None:
    for label in sorted(NODE_LABELS | {"Assertion", "Dataset"}):
        client.query(
            f"CREATE CONSTRAINT `{label}_graph_id` IF NOT EXISTS "
            f"FOR (node:`{label}`) REQUIRE node.graph_id IS UNIQUE"
        )
    client.query(
        "CREATE INDEX graph_entity_identity IF NOT EXISTS "
        "FOR (node:GraphEntity) ON (node.dataset_id, node.stable_id)"
    )


def load_neo4j(
    client: Neo4jClient, directory: Path, manifest: dict[str, Any]
) -> None:
    nodes, relationships, assertions = graph_records(directory)
    create_constraints(client)
    client.query(
        "MATCH (node {dataset_id: $dataset_id}) "
        "WHERE NOT node:Assertion AND NOT node:Dataset SET node:GraphEntity",
        {"dataset_id": manifest["dataset_id"]},
    )
    print("Neo4j: loading nodes", file=sys.stderr, flush=True)
    for label in sorted(NODE_LABELS):
        rows = [
            {
                "graph_id": node["graph_id"],
                "stable_id": node["stable_id"],
                "dataset_id": node["dataset_id"],
                "properties": neo4j_properties(node["properties"]),
            }
            for node in nodes
            if node["label"] == label
        ]
        for batch in batches(rows):
            client.query(
                f"UNWIND $rows AS row MERGE (node:GraphEntity:`{label}` {{graph_id: row.graph_id}}) "
                "SET node.stable_id = row.stable_id, node.dataset_id = row.dataset_id, "
                "node += row.properties",
                {"rows": batch},
            )
    unknown_labels = {node["label"] for node in nodes} - NODE_LABELS
    if unknown_labels:
        raise ValueError(f"unsupported Neo4j labels: {sorted(unknown_labels)}")

    for relationship_type in sorted(RELATIONSHIP_TYPES):
        rows = [record for record in relationships if record["type"] == relationship_type]
        for batch in batches(rows):
            client.query(
                "UNWIND $rows AS row "
                "MATCH (source:GraphEntity {stable_id: row.from_id, dataset_id: row.dataset_id}) "
                "MATCH (target:GraphEntity {stable_id: row.to_id, dataset_id: row.dataset_id}) "
                f"MERGE (source)-[link:`{relationship_type}` {{graph_id: row.graph_id}}]->(target) "
                "SET link.stable_id = row.stable_id, link.dataset_id = row.dataset_id, "
                "link += row.properties",
                {"rows": batch},
            )
    unknown_types = {record["type"] for record in relationships} - RELATIONSHIP_TYPES
    if unknown_types:
        raise ValueError(f"unsupported Neo4j relationship types: {sorted(unknown_types)}")

    print("Neo4j: loading assertions", file=sys.stderr, flush=True)
    assertion_rows = [
        {**assertion, "properties": neo4j_properties(assertion)} for assertion in assertions
    ]
    assertion_batches = list(batches(assertion_rows))
    for batch_number, batch in enumerate(assertion_batches, 1):
        client.query(
            "UNWIND $rows AS row MERGE (claim:Assertion {graph_id: row.graph_id}) "
            "SET claim += row.properties "
            "WITH row, claim "
            "MATCH (subject:GraphEntity {stable_id: row.subject_id, dataset_id: row.dataset_id}) "
            "MATCH (object:GraphEntity {stable_id: row.object_id, dataset_id: row.dataset_id}) "
            "MERGE (claim)-[:SUBJECT]->(subject) MERGE (claim)-[:OBJECT]->(object) "
            "WITH row, claim UNWIND row.citation_ids AS citation_id "
            "MATCH (citation:Citation {stable_id: citation_id, dataset_id: row.dataset_id}) "
            "MERGE (claim)-[:SUPPORTED_BY]->(citation)",
            {"rows": batch},
        )
        print(
            f"Neo4j: assertions {batch_number}/{len(assertion_batches)}",
            file=sys.stderr,
            flush=True,
        )
    client.query(
        "MERGE (dataset:Dataset {graph_id: $dataset_id}) "
        "SET dataset.dataset_id = $dataset_id, dataset.state = 'loaded', dataset.loaded_at = $loaded_at, "
        "dataset.expected_nodes = $nodes, dataset.expected_relationships = $relationships, "
        "dataset.expected_assertions = $assertions",
        {
            "dataset_id": manifest["dataset_id"],
            "loaded_at": datetime.now(UTC).isoformat(),
            "nodes": manifest["counts"]["nodes"],
            "relationships": manifest["counts"]["structural_relationships"],
            "assertions": manifest["counts"]["assertions"],
        },
    )
    print("Neo4j: load complete", file=sys.stderr, flush=True)


def load_elasticsearch(
    client: ElasticsearchClient, directory: Path, manifest: dict[str, Any]
) -> str:
    name = index_name(manifest["dataset_id"])
    template = json.loads(
        (PROJECT_ROOT / "infra" / "search" / "elasticsearch-index.json").read_text(encoding="utf-8")
    )
    try:
        client.json("PUT", f"/{name}", template)
    except ValueError as error:
        if "resource_already_exists_exception" not in str(error):
            raise
    chunks = read_jsonl(directory / "search" / "chunks.jsonl")
    print("Elasticsearch: loading chunks", file=sys.stderr, flush=True)
    chunk_batches = list(batches(chunks, 250))
    for batch_number, batch in enumerate(chunk_batches, 1):
        operations: list[dict[str, Any]] = []
        for chunk in batch:
            operations.extend(({"index": {"_index": name, "_id": chunk["chunk_id"]}}, chunk))
        client.bulk(operations)
        print(
            f"Elasticsearch: chunks {batch_number}/{len(chunk_batches)}",
            file=sys.stderr,
            flush=True,
        )
    client.json("POST", f"/{name}/_refresh")
    print("Elasticsearch: load complete", file=sys.stderr, flush=True)
    return name


def verify_stores(
    neo4j: Neo4jClient,
    elasticsearch: ElasticsearchClient,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    dataset_id = manifest["dataset_id"]
    graph_counts = neo4j.query(
        "MATCH (node {dataset_id: $dataset_id}) "
        "WITH count(CASE WHEN NOT node:Assertion AND NOT node:Dataset THEN 1 END) AS nodes, "
        "count(CASE WHEN node:Assertion THEN 1 END) AS assertions "
        "MATCH ()-[link]->() WHERE link.dataset_id = $dataset_id "
        "RETURN nodes, assertions, count(CASE WHEN type(link) IN ['BELONGS_TO','HAS_CITATION'] "
        "THEN 1 END) AS relationships",
        {"dataset_id": dataset_id},
    )
    if len(graph_counts) != 1:
        raise ValueError("Neo4j verification returned no counts")
    actual_nodes, actual_assertions, actual_relationships = graph_counts[0]
    expected = manifest["counts"]
    if [actual_nodes, actual_assertions, actual_relationships] != [
        expected["nodes"],
        expected["assertions"],
        expected["structural_relationships"],
    ]:
        raise ValueError(
            "Neo4j counts do not match manifest: "
            f"{[actual_nodes, actual_assertions, actual_relationships]}"
        )
    unsupported = neo4j.query(
        "MATCH (claim:Assertion {dataset_id: $dataset_id, assertion_status: 'verified'}) "
        "WHERE NOT (claim)-[:SUPPORTED_BY]->(:Citation) RETURN count(claim)",
        {"dataset_id": dataset_id},
    )[0][0]
    if unsupported:
        raise ValueError(f"Neo4j contains {unsupported} unsupported verified assertions")
    search_count = elasticsearch.json("GET", f"/{index_name(dataset_id)}/_count")["count"]
    if search_count != expected["chunks"]:
        raise ValueError(f"Elasticsearch count {search_count} does not match {expected['chunks']}")
    return {
        "dataset_id": dataset_id,
        "neo4j_nodes": actual_nodes,
        "neo4j_relationships": actual_relationships,
        "neo4j_assertions": actual_assertions,
        "elasticsearch_chunks": search_count,
        "verified": True,
    }


def alias_indices(client: ElasticsearchClient) -> list[str]:
    try:
        payload = client.json("GET", f"/_alias/{SEARCH_ALIAS}")
    except ValueError as error:
        if "alias_not_found_exception" in str(error) or "HTTP 404" in str(error):
            return []
        raise
    return sorted(payload)


def set_alias(client: ElasticsearchClient, target: str | None, previous: list[str]) -> None:
    actions: list[dict[str, Any]] = [
        {"remove": {"index": name, "alias": SEARCH_ALIAS}} for name in previous
    ]
    if target:
        actions.append({"add": {"index": target, "alias": SEARCH_ALIAS}})
    if actions:
        client.json("POST", "/_aliases", {"actions": actions})


def activate(
    neo4j: Neo4jClient,
    elasticsearch: ElasticsearchClient,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    verification = verify_stores(neo4j, elasticsearch, manifest)
    dataset_id = manifest["dataset_id"]
    target_index = index_name(dataset_id)
    previous_indices = alias_indices(elasticsearch)
    set_alias(elasticsearch, target_index, previous_indices)
    try:
        neo4j.query(
            "MATCH (dataset:Dataset) WHERE dataset.state = 'active' SET dataset.state = 'loaded' "
            "WITH count(dataset) AS ignored MATCH (target:Dataset {dataset_id: $dataset_id}) "
            "SET target.state = 'active', target.activated_at = $activated_at RETURN target.dataset_id",
            {"dataset_id": dataset_id, "activated_at": datetime.now(UTC).isoformat()},
        )
    except BaseException:
        set_alias(elasticsearch, None, [target_index])
        set_alias(elasticsearch, previous_indices[0] if previous_indices else None, [])
        raise
    pointer = {
        "dataset_id": dataset_id,
        "neo4j_state": "active",
        "elasticsearch_alias": SEARCH_ALIAS,
        "elasticsearch_index": target_index,
        "activated_at": datetime.now(UTC).isoformat(),
    }
    ACTIVE_DATASET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=ACTIVE_DATASET.parent, delete=False
    ) as stream:
        json.dump(pointer, stream, indent=2)
        stream.write("\n")
        temporary = Path(stream.name)
    temporary.replace(ACTIVE_DATASET)
    return {**verification, **pointer, "status": "active"}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Load, verify, and activate MCAL search stores")
    command.add_argument("action", choices=("load", "verify", "activate", "all", "status"))
    command.add_argument("--dataset", type=Path)
    command.add_argument("--env", type=Path, default=None)
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.action == "status":
            payload = json.loads(ACTIVE_DATASET.read_text(encoding="utf-8")) if ACTIVE_DATASET.is_file() else {"status": "inactive"}
        else:
            environment = load_env(arguments.env.resolve()) if arguments.env else load_env()
            neo4j = Neo4jClient(environment)
            elasticsearch = ElasticsearchClient(environment)
            directory, manifest = resolve_dataset(arguments.dataset)
            if arguments.action in {"load", "all"}:
                print(f"Loading {manifest['dataset_id']}", file=sys.stderr, flush=True)
                load_neo4j(neo4j, directory, manifest)
                index = load_elasticsearch(elasticsearch, directory, manifest)
                payload = {"status": "loaded", "dataset_id": manifest["dataset_id"], "index": index}
            if arguments.action == "verify":
                payload = verify_stores(neo4j, elasticsearch, manifest)
            if arguments.action in {"activate", "all"}:
                print("Verifying and activating both stores", file=sys.stderr, flush=True)
                payload = activate(neo4j, elasticsearch, manifest)
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())