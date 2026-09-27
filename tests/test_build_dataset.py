from pathlib import Path

import build_dataset
import pytest


def test_extractor_modules_rejects_incomplete_manifest(tmp_path: Path) -> None:
    manifest = {
        "modules_selected": 1,
        "parsed": [],
        "unchanged": [],
        "incomplete": ["Mcu"],
        "failures": [],
    }

    with pytest.raises(ValueError, match="incomplete modules or failures"):
        build_dataset.extractor_modules(tmp_path, manifest)


def test_extractor_modules_requires_all_artifacts(tmp_path: Path) -> None:
    module = tmp_path / "Mcu"
    module.mkdir()
    (module / "um.json").write_text("{}", encoding="utf-8")
    manifest = {
        "modules_selected": 1,
        "parsed": ["Mcu"],
        "unchanged": [],
        "incomplete": [],
        "failures": [],
    }

    with pytest.raises(ValueError, match="missing extractor artifact"):
        build_dataset.extractor_modules(tmp_path, manifest)


def test_publish_dataset_accepts_identical_concurrent_winner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset_id = "dataset:" + "a" * 64
    manifest = {"dataset_id": dataset_id, "state": "complete", "winner": True}
    staging = tmp_path / "staging"
    destination = tmp_path / "dataset"
    staging.mkdir()
    destination.mkdir()
    build_dataset.write_json(destination / "manifest.json", manifest)
    monkeypatch.setattr(build_dataset, "validate_payload", lambda payload, schema: None)

    result = build_dataset.publish_dataset(staging, destination, manifest)

    assert result == {"status": "unchanged", **manifest}
    assert not staging.exists()