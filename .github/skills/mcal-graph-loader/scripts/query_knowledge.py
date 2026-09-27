from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from graph_common import stable_id
from store_client import (
    ACTIVE_DATASET,
    SEARCH_ALIAS,
    ElasticsearchClient,
    Neo4jClient,
    load_env,
)


def load_active_pointer(path: Path = ACTIVE_DATASET) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload.get("dataset_id"):
        raise ValueError("active dataset pointer is invalid")
    return payload


def verify_active_stores(
    neo4j: Neo4jClient,
    elasticsearch: ElasticsearchClient,
    pointer: dict[str, Any],
) -> None:
    dataset_id = str(pointer["dataset_id"])
    state = neo4j.query(
        "MATCH (dataset:Dataset {dataset_id: $dataset_id}) RETURN dataset.state",
        {"dataset_id": dataset_id},
    )
    if state != [["active"]]:
        raise ValueError(f"Neo4j dataset is not active: {dataset_id}")
    aliases = elasticsearch.json("GET", f"/_alias/{SEARCH_ALIAS}")
    expected_index = str(pointer["elasticsearch_index"])
    if expected_index not in aliases or len(aliases) != 1:
        raise ValueError("Elasticsearch alias does not match the active dataset pointer")


def search_request(
    dataset_id: str,
    query: str,
    *,
    module: str | None = None,
    source_type: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    filters: list[dict[str, Any]] = [{"term": {"dataset_id": dataset_id}}]
    if module:
        filters.append({"term": {"module_ids": stable_id("module", module)}})
    if source_type:
        filters.append({"term": {"source_type": source_type}})
    return {
        "size": limit,
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["text^3", "heading_path^2"],
                            "operator": "and",
                        }
                    }
                ],
                "filter": filters,
                "should": [{"match_phrase": {"text": {"query": query, "boost": 2}}}],
            }
        },
        "highlight": {
            "fields": {"text": {"fragment_size": 240, "number_of_fragments": 1}}
        },
    }


def expand_entities(
    neo4j: Neo4jClient, dataset_id: str, entity_ids: list[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not entity_ids:
        return [], []
    entity_rows = neo4j.query(
        "MATCH (entity:GraphEntity {dataset_id: $dataset_id}) "
        "WHERE entity.stable_id IN $entity_ids "
        "RETURN entity.stable_id, labels(entity), properties(entity)",
        {"dataset_id": dataset_id, "entity_ids": entity_ids},
    )
    assertion_rows = neo4j.query(
        "MATCH (claim:Assertion {dataset_id: $dataset_id})-[:SUBJECT]->(subject:GraphEntity) "
        "MATCH (claim)-[:OBJECT]->(object:GraphEntity) "
        "WHERE subject.stable_id IN $entity_ids OR object.stable_id IN $entity_ids "
        "OPTIONAL MATCH (claim)-[:SUPPORTED_BY]->(citation:Citation) "
        "RETURN claim.stable_id, properties(claim), subject.stable_id, object.stable_id, "
        "collect(citation.stable_id) LIMIT 100",
        {"dataset_id": dataset_id, "entity_ids": entity_ids},
    )
    entities = [
        {"stable_id": row[0], "labels": row[1], "properties": row[2]}
        for row in entity_rows
    ]
    assertions = [
        {
            "stable_id": row[0],
            "properties": row[1],
            "subject_id": row[2],
            "object_id": row[3],
            "citation_ids": row[4],
        }
        for row in assertion_rows
    ]
    return entities, assertions


def query_active(
    neo4j: Neo4jClient,
    elasticsearch: ElasticsearchClient,
    pointer: dict[str, Any],
    query: str,
    *,
    module: str | None = None,
    source_type: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    verify_active_stores(neo4j, elasticsearch, pointer)
    dataset_id = str(pointer["dataset_id"])
    response = elasticsearch.json(
        "POST",
        f"/{SEARCH_ALIAS}/_search",
        search_request(
            dataset_id, query, module=module, source_type=source_type, limit=limit
        ),
    )
    hits: list[dict[str, Any]] = []
    entity_ids: set[str] = set()
    for hit in response.get("hits", {}).get("hits", []):
        if hit.get("_index") != pointer["elasticsearch_index"]:
            raise ValueError("search returned a result from an inactive dataset")
        source = hit["_source"]
        if source.get("dataset_id") != dataset_id:
            raise ValueError("search returned a mixed-dataset result")
        entity_ids.update(str(item) for item in source.get("term_ids", []))
        hits.append(
            {
                "score": hit.get("_score"),
                "citation_id": source["citation_id"],
                "document_id": source["document_id"],
                "document": source["document_path"],
                "source_type": source["source_type"],
                "physical_page": source["physical_page"],
                "page_label": source["page_label"],
                "heading_path": source["heading_path"],
                "snippet": (hit.get("highlight", {}).get("text") or [source["text"][:240]])[0],
                "term_ids": source.get("term_ids", []),
            }
        )
    entities, assertions = expand_entities(neo4j, dataset_id, sorted(entity_ids))
    return {
        "dataset_id": dataset_id,
        "query": query,
        "hits": hits,
        "entities": entities,
        "assertions": assertions,
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Query the active MCAL graph/search dataset")
    command.add_argument("query")
    command.add_argument("--module")
    command.add_argument("--source-type")
    command.add_argument("--limit", type=int, default=10)
    command.add_argument("--env", type=Path)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.limit < 1 or arguments.limit > 100:
            raise ValueError("limit must be between 1 and 100")
        environment = load_env(arguments.env.resolve()) if arguments.env else load_env()
        payload = query_active(
            Neo4jClient(environment),
            ElasticsearchClient(environment),
            load_active_pointer(),
            arguments.query,
            module=arguments.module,
            source_type=arguments.source_type,
            limit=arguments.limit,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())