from pathlib import Path
from types import SimpleNamespace

import pdf_corpus
from graph_common import stable_id as graph_stable_id
from rtd_pdf_common import Section, stable_id


def test_stable_ids_match_graph_identity_contract() -> None:
    assert stable_id("document", "docs/manual.pdf", "a" * 64) == graph_stable_id(
        "document", "docs/manual.pdf", "a" * 64
    )


def test_split_text_is_bounded_and_overlapping() -> None:
    text = " ".join(f"word{index}" for index in range(80))

    chunks = pdf_corpus.split_text(text, max_chars=100, overlap_chars=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    assert chunks[0][-10:] in chunks[1]


def test_heading_path_uses_nested_outline_context() -> None:
    sections = [
        Section("Chapter 2", 0, 10, 30),
        Section("Registers", 1, 12, 20),
        Section("CTRL", 2, 14, 15),
    ]

    assert pdf_corpus.heading_path_for_page(sections, 14) == ["Chapter 2", "Registers", "CTRL"]


def test_extract_document_preserves_page_context(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "S32K3XXRM.pdf"
    source.write_bytes(b"pdf")
    reader = SimpleNamespace(
        is_encrypted=False,
        pages=[SimpleNamespace(extract_text=lambda: "FXOSC CTRL OSCON " * 20)],
        page_labels=["1149"],
    )
    monkeypatch.setattr("pypdf.PdfReader", lambda path: reader)
    monkeypatch.setattr(pdf_corpus, "outline_sections", lambda value: [Section("FXOSC CTRL", 0, 1, 1)])
    monkeypatch.setattr(pdf_corpus, "relative_document", lambda path: "docs/S32K3XXRM.pdf")

    document, chunks, warnings = pdf_corpus.extract_document(
        source, max_chars=80, overlap_chars=10
    )

    assert document["source_type"] == "reference-manual"
    assert document["document_id"] == graph_stable_id(
        "document", "docs/S32K3XXRM.pdf", document["sha256"]
    )
    assert warnings == []
    assert len(chunks) > 1
    assert chunks[0]["heading_path"] == ["FXOSC CTRL"]
    assert chunks[0]["page_label"] == "1149"
    assert chunks[0]["next_chunk_id"] == chunks[1]["source_chunk_id"]
    assert chunks[1]["previous_chunk_id"] == chunks[0]["source_chunk_id"]