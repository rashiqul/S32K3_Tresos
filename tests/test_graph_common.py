import graph_common


def test_payload_validator_is_cached() -> None:
    graph_common._payload_validator.cache_clear()
    payload = {
        "schema_version": graph_common.SCHEMA_VERSION,
        "dataset_id": "dataset:" + "a" * 64,
        "stable_id": "term:" + "b" * 64,
        "graph_id": "graph:" + "c" * 64,
        "label": "Term",
        "properties": {},
    }

    graph_common.validate_payload(payload, "node.schema.json")
    graph_common.validate_payload(payload, "node.schema.json")

    assert graph_common._payload_validator.cache_info().misses == 1
    assert graph_common._payload_validator.cache_info().hits == 1

import pytest
from jsonschema import ValidationError


def test_canonical_json_is_independent_of_mapping_order() -> None:
    first = graph_common.canonical_json({"module": "Mcu", "page": 69})
    second = graph_common.canonical_json({"page": 69, "module": "Mcu"})

    assert first == second


def test_duplicate_parameter_names_are_distinguished_by_section() -> None:
    document = graph_common.document_id("docs/RTD_MCU_UM.pdf", "a" * 64)

    global_definition = graph_common.configuration_definition_id(
        "Mcu", document, "4.1.32", "parameter", "McuFxoscUnderMcuControl"
    )
    clock_setting_definition = graph_common.configuration_definition_id(
        "Mcu", document, "4.1.97", "parameter", "McuFxoscUnderMcuControl"
    )

    assert global_definition != clock_setting_definition


def test_xdm_instance_identity_normalizes_path_separators() -> None:
    windows_path = graph_common.xdm_instance_id("S32K358_EVB", "config\\Mcu.xdm", "Mcu/A/B")
    portable_path = graph_common.xdm_instance_id("S32K358_EVB", "config/Mcu.xdm", "Mcu/A/B")

    assert windows_path == portable_path


def test_verified_assertion_requires_citation() -> None:
    dataset = graph_common.stable_id("dataset", "fixture")
    assertion = graph_common.assertion_id("subject:test", "MAPS_TO", "object:test", [], "0.1.0")
    payload = {
        "schema_version": graph_common.SCHEMA_VERSION,
        "dataset_id": dataset,
        "stable_id": assertion,
        "graph_id": graph_common.graph_id(dataset, assertion),
        "subject_id": "subject:test",
        "predicate": "MAPS_TO",
        "object_id": "object:test",
        "citation_ids": [],
        "assertion_status": "verified",
        "review_status": "unreviewed",
        "extraction_confidence": 0.95,
        "producer_version": graph_common.TOOL_VERSION,
    }

    with pytest.raises(ValidationError):
        graph_common.validate_payload(payload, "assertion.schema.json")


def test_inferred_assertion_may_remain_uncited_with_rationale() -> None:
    dataset = graph_common.stable_id("dataset", "fixture")
    assertion = graph_common.assertion_id("subject:test", "MAPS_TO", "object:test", [], "0.1.0")
    payload = {
        "schema_version": graph_common.SCHEMA_VERSION,
        "dataset_id": dataset,
        "stable_id": assertion,
        "graph_id": graph_common.graph_id(dataset, assertion),
        "subject_id": "subject:test",
        "predicate": "MAPS_TO",
        "object_id": "object:test",
        "citation_ids": [],
        "assertion_status": "inferred",
        "review_status": "unreviewed",
        "extraction_confidence": 0.8,
        "producer_version": graph_common.TOOL_VERSION,
        "rationale": "Unique same-module short-name candidate.",
    }

    graph_common.validate_payload(payload, "assertion.schema.json")


@pytest.mark.parametrize("prefix", ["", "Dataset", "has space", "under_score"])
def test_stable_id_rejects_invalid_prefix(prefix: str) -> None:
    with pytest.raises(ValueError):
        graph_common.stable_id(prefix, "value")