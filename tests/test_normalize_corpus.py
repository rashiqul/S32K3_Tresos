from graph_common import stable_id
from normalize_corpus import mentioned_entity_ids, normalize_corpus
from normalize_graph import make_node


def test_mentioned_entity_ids_use_identifier_boundaries() -> None:
    aliases = {
        "oscon": {"register-field:one"},
        "ctrl": {"register:one"},
        "fxosc.ctrl.oscon": {"register-field:qualified"},
    }

    assert mentioned_entity_ids("FXOSC.CTRL.OSCON is configured", aliases) == [
        "register-field:one",
        "register-field:qualified",
        "register:one",
    ]
    assert mentioned_entity_ids("MY_OSCON_VALUE", aliases) == []


def test_normalize_corpus_creates_searchable_citation() -> None:
    dataset_id = "dataset:" + "a" * 64
    document_id = stable_id("document", "docs/manual.pdf", "b" * 64)
    module_id = stable_id("module", "Mcu")
    field_id = stable_id("register-field", "FXOSC.CTRL.OSCON")
    graph_nodes = [
        make_node(dataset_id, "McalModule", module_id, {"canonical_name": "Mcu"}),
        make_node(
            dataset_id,
            "RegisterField",
            field_id,
            {"name": "OSCON", "qualified_name": "FXOSC.CTRL.OSCON"},
        ),
    ]
    documents = [
        {
            "document_id": document_id,
            "path": "docs/manual.pdf",
            "sha256": "b" * 64,
            "page_count": 3,
            "source_type": "RTD-user-manual",
            "module": "Mcu",
        }
    ]
    source_chunks = [
        {
            "source_chunk_id": stable_id("source-chunk", "one"),
            "document_id": document_id,
            "document_sha256": "b" * 64,
            "source_type": "RTD-user-manual",
            "module": "Mcu",
            "physical_page": 2,
            "page_label": "1",
            "heading_path": ["FXOSC"],
            "chunk_ordinal": 0,
            "previous_chunk_id": None,
            "next_chunk_id": None,
            "text": "The OSCON field controls FXOSC.",
            "extraction_method": "page-text",
        }
    ]

    nodes, relationships, chunks = normalize_corpus(
        dataset_id, documents, source_chunks, graph_nodes
    )

    assert [node["label"] for node in nodes] == ["Document", "Citation"]
    assert relationships[0]["type"] == "BELONGS_TO"
    assert chunks[0]["citation_id"] == nodes[1]["stable_id"]
    assert chunks[0]["document_path"] == "docs/manual.pdf"
    assert chunks[0]["module_ids"] == [module_id]
    assert chunks[0]["term_ids"] == [field_id]
    assert chunks[0]["content_type"] == "source-page"