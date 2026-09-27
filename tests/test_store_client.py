import json
from pathlib import Path

import pytest
from store_client import batches, index_name, load_env, neo4j_properties


def test_load_env_rejects_example_password(tmp_path: Path) -> None:
    path = tmp_path / ".env"
    path.write_text("NEO4J_PASSWORD=change-this-local-password\n", encoding="utf-8")

    with pytest.raises(ValueError, match="non-example"):
        load_env(path)


def test_store_helpers_are_deterministic() -> None:
    assert list(batches([{"id": 1}, {"id": 2}, {"id": 3}], 2)) == [
        [{"id": 1}, {"id": 2}],
        [{"id": 3}],
    ]
    assert index_name("dataset:" + "a" * 64) == "mcal-reference-chunks-" + "a" * 64
    properties = neo4j_properties({"nested": {"b": 2, "a": 1}, "plain": "value"})
    assert properties == {"nested": json.dumps({"a": 1, "b": 2}, separators=(",", ":")), "plain": "value"}