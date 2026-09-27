import rtd_um_parser
from rtd_pdf_common import Section


class Page:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class Reader:
    def __init__(self) -> None:
        self.page_labels = ["131", "132"]
        self.pages = [
            Page(
                "4.1.173 Parameter AdcDeInitApi\n"
                "Adds or removes the service.\n"
                "Property Value\n"
                "type ECUC-BOOLEAN-PARAM-DEF\n"
                "lowerMultiplicity 1\n"
                "upperMultiplicity 1\n"
                "valueConfigClasses VARIANT-POST-BUILD: POST-BUILD\n"
                "VARIANT-PRE-COMPILE: PRE-COMPILE\n"
                "defaultValue true\n"
            ),
            Page(
                "4.1.174 Parameter AdcDevErrorDetect\n"
                "Switches error detection on or off.\n"
                "Property Value\n"
                "type ECUC-BOOLEAN-PARAM-DEF\n"
                "defaultValue false\n"
            ),
        ]


def test_extract_configuration_items_preserves_attributes_and_provenance() -> None:
    items, warnings = rtd_um_parser.extract_configuration_items(
        Reader(), Section("4 Configuration Parameters", 0, 1, 2)
    )

    assert warnings == []
    assert [item["identifier"] for item in items] == ["AdcDeInitApi", "AdcDevErrorDetect"]
    assert items[0]["attributes"] == {
        "data_type": "ECUC-BOOLEAN-PARAM-DEF",
        "default": True,
        "configuration_classes": ["POST-BUILD", "PRE-COMPILE"],
        "multiplicity": "1..1",
    }
    assert items[1]["source"]["physical_page"] == 2
    assert items[1]["source"]["page_label"] == "132"


def test_adc_profile_exists() -> None:
    profile = rtd_um_parser.load_profile("ADC")

    assert profile["module"] == "ADC"