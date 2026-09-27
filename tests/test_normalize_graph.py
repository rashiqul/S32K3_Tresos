import graph_common
import normalize_graph


def test_hardware_references_preserve_ambiguous_register_notation() -> None:
    references = normalize_graph.hardware_references(
        "Configure FXOSC_CTRL[OSCON], check FLASH:CTL register, and ignore lowercase text."
    )

    assert references == [
        ("register", "FLASH:CTL"),
        ("register-field", "FXOSC_CTRL[OSCON]"),
    ]


def source(document: str) -> dict[str, object]:
    return {"document": document, "sha256": "a" * 64, "page_count": 100}


def span(page: int, section: str) -> dict[str, object]:
    return {
        "physical_page": page,
        "page_label": str(page - 12),
        "section": section,
        "extraction_method": "page-text",
        "confidence": 0.95,
    }


def test_normalizer_preserves_duplicate_mcu_definitions_and_marks_xdm_mapping_unresolved() -> None:
    dataset = graph_common.stable_id("dataset", "fixture")
    um = {
        "module": "Mcu",
        "source": source("docs/RTD_MCU_UM.pdf"),
        "configuration_items": [
            {
                "kind": "parameter",
                "identifier": "McuFxoscUnderMcuControl",
                "raw_title": "4.1.32 Parameter McuFxoscUnderMcuControl",
                "description": "Global calculated flag.",
                "attributes": {"data_type": "ECUC-BOOLEAN-PARAM-DEF"},
                "source": span(69, "4.1.32 Parameter McuFxoscUnderMcuControl"),
                "extensions": {"section_number": "4.1.32"},
            },
            {
                "kind": "parameter",
                "identifier": "McuFxoscUnderMcuControl",
                "raw_title": "4.1.97 Parameter McuFxoscUnderMcuControl",
                "description": "Per-clock-setting ownership flag.",
                "attributes": {"data_type": "ECUC-BOOLEAN-PARAM-DEF"},
                "source": span(98, "4.1.97 Parameter McuFxoscUnderMcuControl"),
                "extensions": {"section_number": "4.1.97"},
            },
        ],
    }
    im = {
        "module": "Mcu",
        "source": source("docs/RTD_MCU_IM.pdf"),
        "topics": [],
        "exclusive_areas": [],
    }

    definition_nodes, relationships, definition_assertions = normalize_graph.normalize_rtd_module(
        dataset, um, im
    )
    xdm_nodes, xdm_relationships, xdm_assertions = normalize_graph.normalize_xdm_entries(
        dataset,
        "S32K358_EVB",
        [
            {
                "file": "config/Mcu.xdm",
                "module": "Mcu",
                "path": "Mcu/McuGeneralConfiguration/McuControlledClocksConfiguration/McuFxoscUnderMcuControl",
                "kind": "var",
                "name": "McuFxoscUnderMcuControl",
                "type": "BOOLEAN",
                "value": "true",
                "enabled": None,
            }
        ],
        definition_nodes,
    )

    definitions = [node for node in definition_nodes if node["label"] == "ConfigurationDefinition"]
    assert len(definitions) == 2
    assert len({node["stable_id"] for node in definitions}) == 2
    assert relationships
    assert definition_assertions
    assert xdm_nodes
    assert xdm_relationships
    assert len(xdm_assertions) == 2
    assert {assertion["assertion_status"] for assertion in xdm_assertions} == {"unresolved"}
    assert {assertion["object_id"] for assertion in xdm_assertions} == {
        node["stable_id"] for node in definitions
    }


def test_unique_xdm_name_creates_inferred_candidate() -> None:
    dataset = graph_common.stable_id("dataset", "fixture")
    um = {
        "module": "Mcu",
        "source": source("docs/RTD_MCU_UM.pdf"),
        "configuration_items": [
            {
                "kind": "parameter",
                "identifier": "McuCrystalFrequencyHz",
                "raw_title": "4.1.71 Parameter McuCrystalFrequencyHz",
                "description": "Crystal frequency.",
                "attributes": {"data_type": "ECUC-FLOAT-PARAM-DEF"},
                "source": span(86, "4.1.71 Parameter McuCrystalFrequencyHz"),
                "extensions": {"section_number": "4.1.71"},
            }
        ],
    }
    im = {
        "module": "Mcu",
        "source": source("docs/RTD_MCU_IM.pdf"),
        "topics": [],
        "exclusive_areas": [],
    }
    definitions, _, _ = normalize_graph.normalize_rtd_module(dataset, um, im)

    _, _, assertions = normalize_graph.normalize_xdm_entries(
        dataset,
        "S32K358_EVB",
        [
            {
                "file": "config/Mcu.xdm",
                "module": "Mcu",
                "path": "Mcu/McuModuleConfiguration/McuCrystalFrequencyHz",
                "kind": "var",
                "name": "McuCrystalFrequencyHz",
                "type": "FLOAT",
                "value": "1.6E7",
                "enabled": None,
            }
        ],
        definitions,
    )

    assert len(assertions) == 1
    assert assertions[0]["assertion_status"] == "inferred"