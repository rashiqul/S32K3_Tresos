from graph_common import stable_id
from normalize_graph import make_node
from normalize_hardware import normalize_hardware_artifact


def definition(dataset_id: str, section: str, identifier: str) -> dict:
    return make_node(
        dataset_id,
        "ConfigurationDefinition",
        stable_id("configuration-definition", section, identifier),
        {
            "module_id": stable_id("module", "Mcu"),
            "section_number": section,
            "identifier": identifier,
        },
    )


def test_normalize_hardware_artifact_preserves_fxosc_stable_ids() -> None:
    import hardware_extract

    profile = hardware_extract.load_profile(hardware_extract.DEFAULT_PROFILE)
    artifact = {
        "state": "complete",
        "failures": [],
        "documents": {
            key: {
                "document": specification["path"],
                "sha256": "a" * 64,
                "page_count": 1200,
                "source_type": specification["source_type"],
            }
            for key, specification in profile["documents"].items()
        },
        "citations": [
            {
                "name": name,
                **specification,
                "extraction_method": "page-text",
                "extraction_confidence": 1.0,
            }
            for name, specification in profile["citations"].items()
        ],
        "entities": profile["entities"],
        "relationships": profile["relationships"],
        "assertions": profile["assertions"],
    }
    dataset_id = "dataset:" + "a" * 64
    definitions = [
        definition(dataset_id, "4.1.32", "McuFxoscUnderMcuControl"),
        definition(dataset_id, "4.1.71", "McuCrystalFrequencyHz"),
        definition(dataset_id, "4.1.97", "McuFxoscUnderMcuControl"),
        definition(dataset_id, "4.1.98", "McuFxoscPowerDownCtr"),
    ]

    nodes, relationships, assertions = normalize_hardware_artifact(
        dataset_id, artifact, definitions
    )

    ctrl_id = stable_id("register", "S32K3XX", "FXOSC", "CTRL", "0x0")
    oscon_id = stable_id("register-field", ctrl_id, "OSCON", "0")
    assert any(node["stable_id"] == ctrl_id for node in nodes)
    assert any(node["stable_id"] == oscon_id for node in nodes)
    assert len(relationships) == 17
    assert len(assertions) == 23


def test_normalize_hardware_artifact_includes_target_platform() -> None:
    import hardware_extract

    profile = hardware_extract.load_profile(hardware_extract.DEFAULT_PROFILE)

    assert profile["entities"]["target_platform"]["label"] == "HardwarePlatform"
    assert profile["entities"]["target_platform"]["properties"]["canonical_name"] == (
        "S32K3X8EVB-Q289"
    )