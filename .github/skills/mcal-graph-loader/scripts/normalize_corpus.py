from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from build_chunks import CHUNKER_VERSION
from graph_common import SCHEMA_VERSION, citation_id, stable_id
from normalize_graph import Node, Relationship, make_node, make_relationship


@dataclass(frozen=True)
class EntityAliases:
    words: dict[str, set[str]]
    qualified: tuple[tuple[str, set[str]], ...]


def prepare_aliases(aliases: dict[str, set[str]]) -> EntityAliases:
    words: dict[str, set[str]] = {}
    qualified: list[tuple[str, set[str]]] = []
    for alias, entity_ids in aliases.items():
        if re.fullmatch(r"[a-z][a-z0-9_]*", alias):
            words[alias] = entity_ids
        else:
            qualified.append((alias, entity_ids))
    return EntityAliases(words, tuple(qualified))


def entity_aliases(nodes: Iterable[Node]) -> EntityAliases:
    aliases: dict[str, set[str]] = {}
    fields = {
        "ConfigurationDefinition": ("identifier",),
        "ConfigurationContainerDefinition": ("identifier",),
        "Peripheral": ("name",),
        "Register": ("qualified_name",),
        "RegisterField": ("qualified_name", "name"),
        "Device": ("canonical_name",),
        "Term": ("canonical_name",),
    }
    for node in nodes:
        for field in fields.get(str(node["label"]), ()):
            value = str(node["properties"].get(field, "")).strip()
            if len(value) >= 4:
                aliases.setdefault(value.casefold(), set()).add(str(node["stable_id"]))
    return prepare_aliases(aliases)


def mentioned_entity_ids(
    text: str, aliases: EntityAliases | dict[str, set[str]]
) -> list[str]:
    index = prepare_aliases(aliases) if isinstance(aliases, dict) else aliases
    folded = text.casefold()
    matches: set[str] = set()
    tokens = set(re.findall(r"[a-z][a-z0-9_]*", folded))
    for token in tokens:
        matches.update(index.words.get(token, ()))
    for alias, entity_ids in index.qualified:
        pattern = rf"(?<![a-z0-9_]){re.escape(alias)}(?![a-z0-9_])"
        if re.search(pattern, folded):
            matches.update(entity_ids)
    return sorted(matches)


def normalize_corpus(
    dataset_id: str,
    documents: list[dict[str, Any]],
    source_chunks: list[dict[str, Any]],
    graph_nodes: Iterable[Node],
) -> tuple[list[Node], list[Relationship], list[dict[str, Any]]]:
    document_nodes = {
        str(document["document_id"]): make_node(
            dataset_id,
            "Document",
            str(document["document_id"]),
            {
                "path": document["path"],
                "sha256": document["sha256"],
                "page_count": document["page_count"],
                "source_type": document["source_type"],
            },
        )
        for document in documents
    }
    module_ids = {
        str(node["properties"].get("canonical_name", "")).casefold(): str(node["stable_id"])
        for node in graph_nodes
        if node["label"] == "McalModule"
    }
    aliases = entity_aliases(graph_nodes)
    nodes = list(document_nodes.values())
    relationships: list[Relationship] = []
    chunks: list[dict[str, Any]] = []
    for source in source_chunks:
        document = document_nodes.get(str(source["document_id"]))
        if document is None:
            raise ValueError(f"corpus chunk references missing document: {source['source_chunk_id']}")
        section = " > ".join(source["heading_path"]) or f"PDF page {source['page_label']}"
        text_anchor = f"Chunk {source['chunk_ordinal']}: {source['text'][:240]}"
        citation = citation_id(
            document["stable_id"],
            int(source["physical_page"]),
            str(source["page_label"]),
            section,
            text_anchor,
        )
        nodes.append(
            make_node(
                dataset_id,
                "Citation",
                citation,
                {
                    "document_id": document["stable_id"],
                    "physical_page": source["physical_page"],
                    "page_label": source["page_label"],
                    "section": section,
                    "text_anchor": text_anchor,
                    "source_chunk_id": source["source_chunk_id"],
                    "extraction_method": source["extraction_method"],
                    "extraction_confidence": 1.0,
                },
            )
        )
        relationships.append(
            make_relationship(dataset_id, "BELONGS_TO", citation, document["stable_id"])
        )
        term_ids = mentioned_entity_ids(str(source["text"]), aliases)
        module_id = module_ids.get(str(source["module"]).casefold())
        chunks.append(
            {
                "schema_version": SCHEMA_VERSION,
                "dataset_id": dataset_id,
                "chunk_id": stable_id("chunk", source["source_chunk_id"], CHUNKER_VERSION),
                "citation_id": citation,
                "source_chunk_id": source["source_chunk_id"],
                "previous_chunk_id": source["previous_chunk_id"],
                "next_chunk_id": source["next_chunk_id"],
                "content_type": "source-page",
                "document_id": document["stable_id"],
                "document_path": document["properties"]["path"],
                "source_type": source["source_type"],
                "module_ids": [module_id] if module_id else [],
                "peripheral_ids": [item for item in term_ids if item.startswith("peripheral:")],
                "term_ids": term_ids,
                "device_ids": [item for item in term_ids if item.startswith("device:")],
                "physical_page": source["physical_page"],
                "page_label": source["page_label"],
                "heading_path": source["heading_path"],
                "text": source["text"],
                "document_sha256": source["document_sha256"],
                "extraction_method": source["extraction_method"],
                "chunker_version": CHUNKER_VERSION,
            }
        )
    return nodes, relationships, chunks