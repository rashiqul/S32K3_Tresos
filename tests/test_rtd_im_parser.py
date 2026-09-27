import rtd_im_parser
from rtd_pdf_common import Section


class Page:
    def __init__(self, text: str) -> None:
        self.text = text

    def extract_text(self) -> str:
        return self.text


class Reader:
    def __init__(self) -> None:
        self.page_labels = ["23", "24"]
        self.pages = [
            Page(
                "ADC_EXCLUSIVE_AREA_03 is used in function Adc_ReadGroup to protect state.\n"
                "ADC_EXCLUSIVE_AREA_10is used in function Adc_StartGroupConversion.\n"
                "ADC_EXCLUSIVE_AREA_11 is used in function Adc_Notificationto protect state."
            ),
            Page(
                "ADC_EXCLUSIVE_AREA_10 is used in function Adc_StopGroupConversion.\n"
                "ISR(Adc_Sar_0_Isr) 180 ADC0 interrupt handler\n"
                "Figure 5. Critical region matrix"
            ),
        ]


def test_extract_exclusive_areas_consolidates_uses_and_provenance() -> None:
    areas, warnings = rtd_im_parser.extract_exclusive_areas(
        Reader(), [Section("5.1 Exclusive areas to be defined", 1, 1, 2)]
    )

    assert warnings == []
    assert [area["identifier"] for area in areas] == [
        "ADC_EXCLUSIVE_AREA_03",
        "ADC_EXCLUSIVE_AREA_10",
        "ADC_EXCLUSIVE_AREA_11",
    ]
    assert areas[1]["uses"] == ["Adc_StartGroupConversion", "Adc_StopGroupConversion"]
    assert areas[2]["uses"] == ["Adc_Notification"]
    assert areas[1]["source"]["page_label"] == "23"


def test_classify_topics_uses_profile_categories() -> None:
    sections = [
        Section("5.4 ISR to configure within AutosarOS - dependencies", 1, 2, 2),
        Section("7 Memory allocation", 0, 1, 1),
    ]

    topics = rtd_im_parser.classify_topics(Reader(), sections, rtd_im_parser.DEFAULT_TOPICS)

    assert [(topic["category"], topic["title"]) for topic in topics] == [
        ("interrupt", "5.4 ISR to configure within AutosarOS - dependencies"),
        ("memory", "7 Memory allocation"),
    ]
    assert topics[0]["identifiers"] == ["Adc_Sar_0_Isr"]