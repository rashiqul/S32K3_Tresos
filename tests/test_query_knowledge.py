from typing import Any

import pytest
from query_knowledge import query_active, search_request


class FakeNeo4j:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def query(self, statement: str, parameters: dict[str, Any] | None = None) -> list[list[Any]]:
        values = parameters or {}
        self.calls.append((statement, values))
        if "dataset.state" in statement:
            return [["active"]]
        if "labels(entity)" in statement:
            return [["register-field:one", ["GraphEntity", "RegisterField"], {"name": "OSCON"}]]
        return []


class FakeElasticsearch:
    def __init__(self, index: str) -> None:
        self.index = index
        self.request: dict[str, Any] | None = None

    def json(self, method: str, path: str, payload: object | None = None) -> Any:
        if path.startswith("/_alias/"):
            return {self.index: {"aliases": {"mcal-reference-chunks": {}}}}
        self.request = payload if isinstance(payload, dict) else None
        return {
            "hits": {
                "hits": [
                    {
                        "_index": self.index,
                        "_score": 4.2,
                        "_source": {
                            "dataset_id": "dataset:" + "a" * 64,
                            "citation_id": "citation:one",
                            "document_id": "document:one",
                            "document_path": "docs/S32K3XXRM.pdf",
                            "source_type": "reference-manual",
                            "physical_page": 10,
                            "page_label": "10",
                            "heading_path": ["FXOSC"],
                            "text": "OSCON controls the oscillator.",
                            "term_ids": ["register-field:one"],
                        },
                        "highlight": {"text": ["<em>OSCON</em> controls the oscillator."]},
                    }
                ]
            }
        }


def test_search_request_requires_all_terms_and_active_dataset() -> None:
    request = search_request("dataset:" + "a" * 64, "FXOSC OSCON", module="Mcu")

    multi_match = request["query"]["bool"]["must"][0]["multi_match"]
    assert multi_match["operator"] == "and"
    assert request["query"]["bool"]["filter"][0]["term"]["dataset_id"].startswith("dataset:")


def test_query_active_returns_citations_and_graph_entities() -> None:
    index = "mcal-reference-chunks-abc"
    pointer = {
        "dataset_id": "dataset:" + "a" * 64,
        "elasticsearch_index": index,
    }
    neo4j = FakeNeo4j()
    elasticsearch = FakeElasticsearch(index)

    result = query_active(neo4j, elasticsearch, pointer, "OSCON")

    assert result["hits"][0]["physical_page"] == 10
    assert result["hits"][0]["document"] == "docs/S32K3XXRM.pdf"
    assert result["hits"][0]["citation_id"] == "citation:one"
    assert result["entities"][0]["properties"]["name"] == "OSCON"
    assert elasticsearch.request is not None


def test_query_active_rejects_alias_mismatch() -> None:
    pointer = {
        "dataset_id": "dataset:" + "a" * 64,
        "elasticsearch_index": "expected-index",
    }

    with pytest.raises(ValueError, match="alias does not match"):
        query_active(FakeNeo4j(), FakeElasticsearch("other-index"), pointer, "OSCON")