from __future__ import annotations

from typing import Any

from graph_common import stable_id
from normalize_graph import (
    Assertion,
    Node,
    Relationship,
    add_unique,
    citation_node,
    make_assertion,
    make_node,
    make_relationship,
    source_document_node,
)

LABEL_PREFIXES = {
    "Peripheral": "peripheral",
    "Register": "register",
    "RegisterField": "register-field",
    "Constraint": "constraint",
    "Device": "device",
    "GeneratedSymbol": "generated-symbol",
}


def find_definition(nodes: list[Node], selector: dict[str, Any]) -> Node:
    module_id = stable_id("module", selector["module"])
    matches = [
        node
        for node in nodes
        if node["label"] == "ConfigurationDefinition"
        and node["properties"]["identifier"] == selector["identifier"]
        and node["properties"]["section_number"] == selector["section_number"]
        and node["properties"]["module_id"] == module_id
    ]
    if len(matches) != 1:
        raise ValueError(
            "expected one configuration definition for "
            f"{selector['module']} {selector['section_number']} {selector['identifier']}, "
            f"found {len(matches)}"
        )
    return matches[0]


def resolve_identity_parts(parts: list[str], entity_ids: dict[str, str]) -> list[str]:
    resolved: list[str] = []
    for part in parts:
        prefix, separator, key = part.partition(":")
        if separator and key in entity_ids and prefix in LABEL_PREFIXES.values():
            resolved.append(entity_ids[key])
        else:
            resolved.append(part)
    return resolved


def resolve_endpoint(
    endpoint: dict[str, Any],
    entity_ids: dict[str, str],
    document_nodes: dict[str, Node],
    definition_nodes: list[Node],
) -> str:
    if "entity" in endpoint:
        key = str(endpoint["entity"])
        if key not in entity_ids:
            raise ValueError(f"unknown hardware entity endpoint: {key}")
        return entity_ids[key]
    if "document" in endpoint:
        key = str(endpoint["document"])
        if key not in document_nodes:
            raise ValueError(f"unknown hardware document endpoint: {key}")
        return str(document_nodes[key]["stable_id"])
    if "definition" in endpoint:
        return str(find_definition(definition_nodes, endpoint["definition"])["stable_id"])
    raise ValueError(f"unsupported hardware endpoint: {endpoint}")


def normalize_hardware_artifact(
    dataset_id: str,
    artifact: dict[str, Any],
    definition_nodes: list[Node],
) -> tuple[list[Node], list[Relationship], list[Assertion]]:
    if artifact.get("state") != "complete" or artifact.get("failures"):
        raise ValueError("hardware extraction artifact is not complete")

    nodes: dict[str, Node] = {}
    relationships: dict[str, Relationship] = {}
    assertions: dict[str, Assertion] = {}
    document_nodes: dict[str, Node] = {}
    citation_nodes: dict[str, Node] = {}
    entity_ids: dict[str, str] = {}

    for key, source in artifact["documents"].items():
        document = source_document_node(dataset_id, source, str(source["source_type"]))
        document_nodes[key] = document
        add_unique(nodes, document)

    for specification in artifact["citations"]:
        document_key = str(specification["document"])
        if document_key not in document_nodes:
            raise ValueError(f"citation references unknown document: {document_key}")
        citation = citation_node(
            dataset_id,
            document_nodes[document_key],
            {
                "physical_page": specification["physical_page"],
                "page_label": specification["page_label"],
                "section": specification["section"],
                "extraction_method": specification["extraction_method"],
                "confidence": specification["extraction_confidence"],
            },
            str(specification["text_anchor"]),
        )
        citation_nodes[str(specification["name"])] = citation
        add_unique(nodes, citation)
        add_unique(
            relationships,
            make_relationship(
                dataset_id, "BELONGS_TO", citation["stable_id"], document_nodes[document_key]["stable_id"]
            ),
        )

    for key, specification in artifact["entities"].items():
        label = str(specification["label"])
        prefix = LABEL_PREFIXES.get(label)
        if prefix is None:
            raise ValueError(f"unsupported hardware entity label: {label}")
        identity = resolve_identity_parts(list(specification["identity"]), entity_ids)
        entity_id = stable_id(prefix, *identity)
        entity_ids[key] = entity_id
        add_unique(
            nodes,
            make_node(dataset_id, label, entity_id, dict(specification["properties"])),
        )

    for specification in artifact["relationships"]:
        try:
            from_id = entity_ids[str(specification["from"])]
            to_id = entity_ids[str(specification["to"])]
        except KeyError as error:
            raise ValueError(f"hardware relationship references unknown entity: {error.args[0]}") from error
        add_unique(
            relationships,
            make_relationship(dataset_id, str(specification["type"]), from_id, to_id),
        )

    for specification in artifact["assertions"]:
        missing = set(specification["citations"]) - citation_nodes.keys()
        if missing:
            raise ValueError(f"hardware assertion references unknown citations: {sorted(missing)}")
        citation_ids = [citation_nodes[name]["stable_id"] for name in specification["citations"]]
        add_unique(
            assertions,
            make_assertion(
                dataset_id,
                resolve_endpoint(
                    specification["subject"], entity_ids, document_nodes, definition_nodes
                ),
                str(specification["predicate"]),
                resolve_endpoint(
                    specification["object"], entity_ids, document_nodes, definition_nodes
                ),
                citation_ids,
                str(specification["assertion_status"]),
                float(specification["extraction_confidence"]),
                specification.get("rationale"),
            ),
        )

    return (
        sorted(nodes.values(), key=lambda item: item["stable_id"]),
        sorted(relationships.values(), key=lambda item: item["stable_id"]),
        sorted(assertions.values(), key=lambda item: item["stable_id"]),
    )
