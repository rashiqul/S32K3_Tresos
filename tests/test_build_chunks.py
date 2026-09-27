from build_chunks import CHUNKER_VERSION, build_chunks
from graph_common import stable_id
from normalize_graph import citation_node, make_assertion, make_node, make_relationship


def test_build_chunks_links_citation_to_search_filters() -> None:
    dataset_id = "dataset:" + "a" * 64
    document_id = stable_id("document", "docs/manual.pdf", "b" * 64)
    document = make_node(
        dataset_id,
        "Document",
        document_id,
        {
            "path": "docs/manual.pdf",
            "sha256": "b" * 64,
            "page_count": 10,
            "source_type": "reference-manual",
        },
    )
    peripheral = make_node(
        dataset_id,
        "Peripheral",
        stable_id("peripheral", "FXOSC"),
        {"name": "FXOSC"},
    )
    citation = citation_node(
        dataset_id,
        document,
        {
            "physical_page": 3,
            "page_label": "3",
            "section": "FXOSC control",
            "extraction_method": "page-text",
            "confidence": 1.0,
        },
        "FXOSC control register",
    )
    assertion = make_assertion(
        dataset_id,
        peripheral["stable_id"],
        "DOCUMENTED_BY",
        document_id,
        [citation["stable_id"]],
        "verified",
        1.0,
    )
    relationship = make_relationship(
        dataset_id, "BELONGS_TO", citation["stable_id"], document_id
    )

    chunks = build_chunks(
        dataset_id,
        [document, peripheral, citation],
        [relationship],
        [assertion],
    )

    assert len(chunks) == 1
    assert chunks[0]["chunker_version"] == CHUNKER_VERSION
    assert chunks[0]["citation_id"] == citation["stable_id"]
    assert chunks[0]["content_type"] == "evidence"
    assert chunks[0]["document_path"] == "docs/manual.pdf"
    assert chunks[0]["peripheral_ids"] == [peripheral["stable_id"]]
    assert "FXOSC control register" in chunks[0]["text"]