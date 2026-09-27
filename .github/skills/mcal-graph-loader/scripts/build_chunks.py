from __future__ import annotations

from typing import Any

from graph_common import SCHEMA_VERSION, stable_id

CHUNKER_VERSION = "0.3.0"


def searchable_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [text for child in value.values() for text in searchable_values(child)]
    if isinstance(value, list):
        return [text for child in value for text in searchable_values(child)]
    if value is None or isinstance(value, bool):
        return []
    return [str(value)]


def build_chunks(
    dataset_id: str,
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    assertions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {str(node["stable_id"]): node for node in nodes}
    document_ids = {
        str(node["stable_id"]): node for node in nodes if node["label"] == "Document"
    }
    linked_entities: dict[str, set[str]] = {}
    for relationship in relationships:
        if relationship["type"] == "HAS_CITATION":
            linked_entities.setdefault(relationship["to_id"], set()).add(relationship["from_id"])
    for assertion in assertions:
        for citation_id in assertion["citation_ids"]:
            linked_entities.setdefault(citation_id, set()).update(
                (assertion["subject_id"], assertion["object_id"])
            )

    chunks: list[dict[str, Any]] = []
    for citation in (node for node in nodes if node["label"] == "Citation"):
        properties = citation["properties"]
        document_id = str(properties["document_id"])
        document = document_ids.get(document_id) or by_id.get(document_id)
        if document is None or document["label"] != "Document":
            raise ValueError(f"citation references missing document: {citation['stable_id']}")
        entities = [by_id[entity_id] for entity_id in sorted(linked_entities.get(citation["stable_id"], set()))]
        module_ids = sorted(
            {
                str(entity["properties"]["module_id"])
                for entity in entities
                if entity["properties"].get("module_id")
            }
        )
        peripheral_ids = sorted(
            entity["stable_id"] for entity in entities if entity["label"] == "Peripheral"
        )
        device_ids = sorted(entity["stable_id"] for entity in entities if entity["label"] == "Device")
        term_ids = sorted(entity["stable_id"] for entity in entities)
        text_parts = [str(properties["text_anchor"])]
        for entity in entities:
            text_parts.extend(searchable_values(entity["properties"]))
        text = "\n".join(dict.fromkeys(part for part in text_parts if part.strip()))
        chunks.append(
            {
                "schema_version": SCHEMA_VERSION,
                "dataset_id": dataset_id,
                "chunk_id": stable_id(
                    "chunk", citation["stable_id"], CHUNKER_VERSION
                ),
                "citation_id": citation["stable_id"],
                "source_chunk_id": None,
                "previous_chunk_id": None,
                "next_chunk_id": None,
                "content_type": "evidence",
                "document_id": document_id,
                "document_path": document["properties"]["path"],
                "source_type": document["properties"]["source_type"],
                "module_ids": module_ids,
                "peripheral_ids": peripheral_ids,
                "term_ids": term_ids,
                "device_ids": device_ids,
                "physical_page": int(properties["physical_page"]),
                "page_label": str(properties["page_label"]),
                "heading_path": [str(properties["section"])],
                "text": text,
                "document_sha256": document["properties"]["sha256"],
                "extraction_method": properties["extraction_method"],
                "chunker_version": CHUNKER_VERSION,
            }
        )
    return sorted(chunks, key=lambda item: item["chunk_id"])