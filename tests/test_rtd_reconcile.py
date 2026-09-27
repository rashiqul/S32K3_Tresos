import copy

import pytest
import rtd_reconcile


def payloads() -> tuple[dict, dict]:
    source = {"document": "docs/manual.pdf", "sha256": "0" * 64, "page_count": 2}
    span = {
        "physical_page": 1,
        "page_label": "1",
        "section": "section",
        "extraction_method": "page-text",
        "confidence": 0.9,
    }
    um = {
        "schema_version": "1.0.0",
        "tool_version": "0.2.1",
        "kind": "UM",
        "module": "ADC",
        "source": source,
        "sections": [],
        "configuration_items": [
            {
                "kind": "parameter",
                "identifier": "AdcDevErrorDetect",
                "raw_title": "4.1 Parameter AdcDevErrorDetect",
                "attributes": {},
                "source": span,
                "extensions": {},
            }
        ],
        "warnings": [],
    }
    im = {
        "schema_version": "1.0.0",
        "tool_version": "0.2.1",
        "kind": "IM",
        "module": "ADC",
        "source": {**source, "document": "docs/integration.pdf"},
        "sections": [],
        "topics": [],
        "exclusive_areas": [
            {"identifier": "ADC_EXCLUSIVE_AREA_00", "uses": ["Adc_ReadGroup"], "source": span, "extensions": {}}
        ],
        "warnings": [],
    }
    return um, im


def test_reconcile_preserves_sources_and_creates_typed_edges() -> None:
    um, im = payloads()

    result = rtd_reconcile.reconcile(um, im)

    assert result["module"] == "ADC"
    assert {relationship["type"] for relationship in result["relationships"]} == {
        "documents",
        "uses-exclusive-area",
    }
    assert any(
        relationship["from"] == "api:Adc_ReadGroup"
        and relationship["to"] == "exclusive-area:ADC_EXCLUSIVE_AREA_00"
        for relationship in result["relationships"]
    )


def test_reconcile_rejects_module_mismatch() -> None:
    um, im = payloads()
    other = copy.deepcopy(im)
    other["module"] = "SPI"

    with pytest.raises(ValueError, match="module mismatch"):
        rtd_reconcile.reconcile(um, other)