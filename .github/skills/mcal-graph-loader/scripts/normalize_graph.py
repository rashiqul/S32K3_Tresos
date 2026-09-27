from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from graph_common import (
    SCHEMA_VERSION,
    TOOL_VERSION,
    assertion_id,
    citation_id,
    configuration_definition_id,
    document_id,
    graph_id,
    stable_id,
    xdm_instance_id,
)

Node = dict[str, Any]
Relationship = dict[str, Any]
Assertion = dict[str, Any]
REGISTER_FIELD_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9_]*(?::[A-Z][A-Z0-9_]*)?\[[A-Z][A-Z0-9_]*\])"
)
REGISTER_NAME_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])([A-Z][A-Z0-9_]*(?::[A-Z][A-Z0-9_]*)?)\s+registers?\b"
)


def hardware_references(text: str) -> list[tuple[str, str]]:
    references = {
        ("register-field", match.group(1).replace(" ", ""))
        for match in REGISTER_FIELD_PATTERN.finditer(text)
    }
    references.update(
        ("register", match.group(1).replace(" ", ""))
        for match in REGISTER_NAME_PATTERN.finditer(text)
        if "_" in match.group(1) or ":" in match.group(1)
    )
    return sorted(references)


def make_node(dataset_id: str, label: str, entity_id: str, properties: dict[str, Any]) -> Node:
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "stable_id": entity_id,
        "graph_id": graph_id(dataset_id, entity_id),
        "label": label,
        "properties": properties,
    }


def make_relationship(
    dataset_id: str,
    relationship_type: str,
    from_id: str,
    to_id: str,
    properties: dict[str, Any] | None = None,
) -> Relationship:
    relationship_id = stable_id("relationship", relationship_type, from_id, to_id)
    return {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "stable_id": relationship_id,
        "graph_id": graph_id(dataset_id, relationship_id),
        "type": relationship_type,
        "from_id": from_id,
        "to_id": to_id,
        "properties": properties or {},
    }


def make_assertion(
    dataset_id: str,
    subject_id: str,
    predicate: str,
    object_id: str,
    citation_ids: list[str],
    assertion_status: str,
    extraction_confidence: float,
    rationale: str | None = None,
) -> Assertion:
    entity_id = assertion_id(
        subject_id,
        predicate,
        object_id,
        citation_ids,
        TOOL_VERSION,
    )
    assertion: Assertion = {
        "schema_version": SCHEMA_VERSION,
        "dataset_id": dataset_id,
        "stable_id": entity_id,
        "graph_id": graph_id(dataset_id, entity_id),
        "subject_id": subject_id,
        "predicate": predicate,
        "object_id": object_id,
        "citation_ids": sorted(citation_ids),
        "assertion_status": assertion_status,
        "review_status": "unreviewed",
        "extraction_confidence": extraction_confidence,
        "producer_version": TOOL_VERSION,
    }
    if rationale:
        assertion["rationale"] = rationale
    return assertion


def source_document_node(dataset_id: str, source: dict[str, Any], source_type: str) -> Node:
    entity_id = document_id(str(source["document"]), str(source["sha256"]))
    properties = {
        "path": source["document"],
        "sha256": source["sha256"],
        "page_count": source["page_count"],
        "source_type": source_type,
    }
    if source.get("revision"):
        properties["revision"] = source["revision"]
    return make_node(dataset_id, "Document", entity_id, properties)


def citation_node(
    dataset_id: str,
    source_document: Node,
    source_span: dict[str, Any],
    text_anchor: str,
) -> Node:
    entity_id = citation_id(
        source_document["stable_id"],
        int(source_span["physical_page"]),
        str(source_span["page_label"]),
        str(source_span["section"]),
        text_anchor,
    )
    return make_node(
        dataset_id,
        "Citation",
        entity_id,
        {
            "document_id": source_document["stable_id"],
            "physical_page": source_span["physical_page"],
            "page_label": source_span["page_label"],
            "section": source_span["section"],
            "text_anchor": text_anchor,
            "extraction_method": source_span["extraction_method"],
            "extraction_confidence": source_span["confidence"],
        },
    )


def add_unique(records: dict[str, dict[str, Any]], record: dict[str, Any]) -> None:
    entity_id = str(record["stable_id"])
    existing = records.get(entity_id)
    if existing is not None and existing != record:
        raise ValueError(f"conflicting records for stable ID {entity_id}")
    records[entity_id] = record


def normalize_rtd_module(
    dataset_id: str,
    um: dict[str, Any],
    im: dict[str, Any],
) -> tuple[list[Node], list[Relationship], list[Assertion]]:
    if um["module"] != im["module"]:
        raise ValueError(f"module mismatch: UM={um['module']}, IM={im['module']}")

    nodes: dict[str, Node] = {}
    relationships: dict[str, Relationship] = {}
    assertions: dict[str, Assertion] = {}
    module = str(um["module"])
    module_id = stable_id("module", module)
    add_unique(nodes, make_node(dataset_id, "McalModule", module_id, {"canonical_name": module}))

    for payload, source_type in ((um, "RTD-user-manual"), (im, "RTD-integration-manual")):
        document = source_document_node(dataset_id, payload["source"], source_type)
        add_unique(nodes, document)
        relationship = make_relationship(dataset_id, "BELONGS_TO", document["stable_id"], module_id)
        add_unique(relationships, relationship)

    um_document = source_document_node(dataset_id, um["source"], "RTD-user-manual")
    for item in um["configuration_items"]:
        section_number = str(item.get("extensions", {}).get("section_number", item["raw_title"]))
        definition_id = configuration_definition_id(
            module,
            um_document["stable_id"],
            section_number,
            str(item["kind"]),
            str(item["identifier"]),
        )
        label = (
            "ConfigurationContainerDefinition"
            if item["kind"] == "container"
            else "ConfigurationDefinition"
        )
        text_anchor = str(item.get("description") or item["raw_title"])
        citation = citation_node(dataset_id, um_document, item["source"], text_anchor)
        definition = make_node(
            dataset_id,
            label,
            definition_id,
            {
                "module_id": module_id,
                "identifier": item["identifier"],
                "kind": item["kind"],
                "raw_title": item["raw_title"],
                "section_number": section_number,
                "description": item.get("description", ""),
                "attributes": item["attributes"],
                "citation_id": citation["stable_id"],
            },
        )
        for node in (citation, definition):
            add_unique(nodes, node)
        for relationship in (
            make_relationship(dataset_id, "BELONGS_TO", citation["stable_id"], um_document["stable_id"]),
            make_relationship(dataset_id, "BELONGS_TO", definition_id, module_id),
            make_relationship(dataset_id, "HAS_CITATION", definition_id, citation["stable_id"]),
        ):
            add_unique(relationships, relationship)
        assertion = make_assertion(
            dataset_id,
            definition_id,
            "DOCUMENTED_BY",
            um_document["stable_id"],
            [citation["stable_id"]],
            "verified",
            float(item["source"]["confidence"]),
        )
        add_unique(assertions, assertion)
        for category, notation in hardware_references(str(item.get("description", ""))):
            term_id = stable_id("term", "hardware-reference", notation)
            add_unique(
                nodes,
                make_node(
                    dataset_id,
                    "Term",
                    term_id,
                    {"canonical_name": notation, "category": category},
                ),
            )
            add_unique(
                assertions,
                make_assertion(
                    dataset_id,
                    definition_id,
                    "MENTIONS_HARDWARE_TERM",
                    term_id,
                    [citation["stable_id"]],
                    "verified",
                    float(item["source"]["confidence"]),
                ),
            )

    im_document = source_document_node(dataset_id, im["source"], "RTD-integration-manual")
    for topic in im["topics"]:
        topic_id = stable_id(
            "integration-topic",
            module,
            im_document["stable_id"],
            topic["category"],
            topic["title"],
        )
        citation = citation_node(dataset_id, im_document, topic["source"], str(topic["title"]))
        topic_node = make_node(
            dataset_id,
            "IntegrationTopic",
            topic_id,
            {
                "module_id": module_id,
                "category": topic["category"],
                "title": topic["title"],
                "identifiers": topic["identifiers"],
                "citation_id": citation["stable_id"],
            },
        )
        for node in (citation, topic_node):
            add_unique(nodes, node)
        for relationship in (
            make_relationship(dataset_id, "BELONGS_TO", citation["stable_id"], im_document["stable_id"]),
            make_relationship(dataset_id, "BELONGS_TO", topic_id, module_id),
            make_relationship(dataset_id, "HAS_CITATION", topic_id, citation["stable_id"]),
        ):
            add_unique(relationships, relationship)
        assertion = make_assertion(
            dataset_id,
            topic_id,
            "DOCUMENTED_BY",
            im_document["stable_id"],
            [citation["stable_id"]],
            "verified",
            float(topic["source"]["confidence"]),
        )
        add_unique(assertions, assertion)

    for area in im["exclusive_areas"]:
        area_id = stable_id("exclusive-area", module, area["identifier"])
        citation = citation_node(dataset_id, im_document, area["source"], str(area["identifier"]))
        area_node = make_node(
            dataset_id,
            "ExclusiveArea",
            area_id,
            {
                "module_id": module_id,
                "identifier": area["identifier"],
                "citation_id": citation["stable_id"],
            },
        )
        for node in (citation, area_node):
            add_unique(nodes, node)
        for relationship in (
            make_relationship(dataset_id, "BELONGS_TO", citation["stable_id"], im_document["stable_id"]),
            make_relationship(dataset_id, "BELONGS_TO", area_id, module_id),
            make_relationship(dataset_id, "HAS_CITATION", area_id, citation["stable_id"]),
        ):
            add_unique(relationships, relationship)
        documented = make_assertion(
            dataset_id,
            area_id,
            "DOCUMENTED_BY",
            im_document["stable_id"],
            [citation["stable_id"]],
            "verified",
            float(area["source"]["confidence"]),
        )
        add_unique(assertions, documented)
        for symbol in area["uses"]:
            api_id = stable_id("api", module, symbol)
            api_node = make_node(
                dataset_id,
                "Api",
                api_id,
                {"module_id": module_id, "canonical_name": symbol},
            )
            add_unique(nodes, api_node)
            add_unique(
                relationships,
                make_relationship(dataset_id, "BELONGS_TO", api_id, module_id),
            )
            usage = make_assertion(
                dataset_id,
                api_id,
                "USES_EXCLUSIVE_AREA",
                area_id,
                [citation["stable_id"]],
                "inferred",
                float(area["source"]["confidence"]),
                "The source span records the exclusive area and aggregated observed uses; review the cited page before acceptance.",
            )
            add_unique(assertions, usage)

    return (
        sorted(nodes.values(), key=lambda item: item["stable_id"]),
        sorted(relationships.values(), key=lambda item: item["stable_id"]),
        sorted(assertions.values(), key=lambda item: item["stable_id"]),
    )


def configuration_index(nodes: Iterable[Node]) -> dict[tuple[str, str], list[Node]]:
    index: dict[tuple[str, str], list[Node]] = {}
    for node in nodes:
        if node["label"] not in {"ConfigurationDefinition", "ConfigurationContainerDefinition"}:
            continue
        properties = node["properties"]
        key = (str(properties["module_id"]), str(properties["identifier"]).casefold())
        index.setdefault(key, []).append(node)
    return index


def normalize_xdm_entries(
    dataset_id: str,
    project_id: str,
    entries: Iterable[dict[str, Any]],
    definition_nodes: Iterable[Node],
) -> tuple[list[Node], list[Relationship], list[Assertion]]:
    nodes: dict[str, Node] = {}
    relationships: dict[str, Relationship] = {}
    assertions: dict[str, Assertion] = {}
    definitions = configuration_index(definition_nodes)

    for entry in entries:
        module_id = stable_id("module", entry["module"])
        add_unique(
            nodes,
            make_node(dataset_id, "McalModule", module_id, {"canonical_name": entry["module"]}),
        )
        instance_id = xdm_instance_id(project_id, entry["file"], entry["path"])
        instance = make_node(
            dataset_id,
            "XdmInstance",
            instance_id,
            {
                "project_id": project_id,
                "module_id": module_id,
                "file": entry["file"],
                "path": entry["path"],
                "kind": entry["kind"],
                "name": entry["name"],
                "type": entry.get("type"),
                "value": entry.get("value"),
                "enabled": entry.get("enabled"),
            },
        )
        add_unique(nodes, instance)
        add_unique(
            relationships,
            make_relationship(dataset_id, "BELONGS_TO", instance_id, module_id),
        )

        expected_label = {
            "var": "ConfigurationDefinition",
            "ctr": "ConfigurationContainerDefinition",
        }.get(entry["kind"])
        candidates = [
            candidate
            for candidate in definitions.get((module_id, str(entry["name"]).casefold()), [])
            if candidate["label"] == expected_label
        ]
        if not candidates:
            continue
        assertion_status = "inferred" if len(candidates) == 1 else "unresolved"
        rationale = (
            "Unique same-module short-name candidate; full definition-path evidence is not present in extractor v1."
            if len(candidates) == 1
            else "Multiple same-module definitions share this short name; canonical definition-path evidence is required."
        )
        for candidate in candidates:
            citation = str(candidate["properties"]["citation_id"])
            assertion = make_assertion(
                dataset_id,
                instance_id,
                "INSTANCE_OF",
                candidate["stable_id"],
                [citation],
                assertion_status,
                1.0,
                rationale,
            )
            add_unique(assertions, assertion)

    return (
        sorted(nodes.values(), key=lambda item: item["stable_id"]),
        sorted(relationships.values(), key=lambda item: item["stable_id"]),
        sorted(assertions.values(), key=lambda item: item["stable_id"]),
    )