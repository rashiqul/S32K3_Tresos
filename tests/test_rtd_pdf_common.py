from pathlib import Path
from types import SimpleNamespace

import rtd_pdf_common


def test_classify_rtd_document_preserves_vendor_module_name(tmp_path: Path) -> None:
    path = tmp_path / "RTD_CANTRCV_43_AE_IM.pdf"

    document = rtd_pdf_common.classify_rtd_document(path)

    assert document is not None
    assert document.module == "CANTRCV_43_AE"
    assert document.kind == "IM"


def test_discover_manual_pairs_reports_complete_and_incomplete_pairs(tmp_path: Path) -> None:
    for name in ("RTD_ADC_UM.pdf", "RTD_ADC_IM.pdf", "RTD_SPI_UM.pdf", "AN13435.pdf"):
        (tmp_path / name).touch()

    pairs = rtd_pdf_common.discover_manual_pairs(tmp_path)

    assert [(pair.module, pair.complete) for pair in pairs] == [("ADC", True), ("SPI", False)]
    assert pairs[0].user_manual is not None
    assert pairs[0].integration_manual is not None


def test_outline_sections_use_next_sibling_as_section_boundary() -> None:
    chapter = SimpleNamespace(title="4 Configuration Parameters")
    parameter = SimpleNamespace(title="4.1.1 Parameter AdcFoo")
    next_chapter = SimpleNamespace(title="5 Published Information")
    pages = {id(chapter): 9, id(parameter): 11, id(next_chapter): 19}

    class Reader:
        def __init__(self) -> None:
            self.outline = [chapter, [parameter], next_chapter]
            self.pages = [object()] * 30

        @staticmethod
        def get_destination_page_number(item: object) -> int:
            return pages[id(item)]

    sections = rtd_pdf_common.outline_sections(Reader())

    assert sections == [
        rtd_pdf_common.Section("4 Configuration Parameters", 0, 10, 19),
        rtd_pdf_common.Section("4.1.1 Parameter AdcFoo", 1, 12, 19),
        rtd_pdf_common.Section("5 Published Information", 0, 20, 30),
    ]


def test_normalize_page_lines_joins_hyphenation_and_omits_figure_captions() -> None:
    lines = rtd_pdf_common.normalize_page_lines(
        "AdcEnableHard-\n wareTrigger\nFigure 4. Example signal path\nDefault value: false"
    )

    assert lines == ["AdcEnableHardwareTrigger", "Default value: false"]