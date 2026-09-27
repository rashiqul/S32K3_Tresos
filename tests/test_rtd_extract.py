from pathlib import Path

import pytest
import rtd_extract
from rtd_pdf_common import discover_manual_pairs


def test_workspace_has_complete_rtd_manual_pairs() -> None:
    pairs = discover_manual_pairs(rtd_extract.DEFAULT_DOCS)

    assert len(pairs) >= 36
    assert all(pair.complete for pair in pairs)


def test_extract_corpus_writes_manifest_and_isolates_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "RTD_ADC_UM.pdf").touch()
    (docs / "RTD_ADC_IM.pdf").touch()
    output = tmp_path / "output"

    monkeypatch.setattr(rtd_extract, "extract_pair", lambda pair, output, force: ("parsed", 2))

    manifest = rtd_extract.extract_corpus(docs, output, ["adc"])

    assert manifest["parsed"] == ["ADC"]
    assert manifest["warnings"] == [{"module": "ADC", "count": 2}]
    assert (output / "manifest.json").exists()


def test_extract_corpus_rejects_unknown_module(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown modules"):
        rtd_extract.extract_corpus(tmp_path, tmp_path / "output", ["ADC"])