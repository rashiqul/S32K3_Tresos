from types import SimpleNamespace

import hardware_extract


class FakePages:
    def __init__(self, count: int, text: str) -> None:
        self.count = count
        self.page = SimpleNamespace(extract_text=lambda: text)

    def __len__(self) -> int:
        return self.count

    def __getitem__(self, index: int) -> SimpleNamespace:
        if index < 0 or index >= self.count:
            raise IndexError(index)
        return self.page


def test_extract_profile_validates_anchors_and_emits_neutral_facts(monkeypatch) -> None:
    profile = hardware_extract.load_profile(hardware_extract.DEFAULT_PROFILE)
    terms_by_document: dict[str, set[str]] = {}
    for citation in profile["citations"].values():
        terms_by_document.setdefault(citation["document"], set()).update(citation["required_terms"])

    def reader(path):
        key = next(
            key
            for key, specification in profile["documents"].items()
            if path.as_posix().endswith(specification["path"])
        )
        return SimpleNamespace(
            is_encrypted=False,
            pages=FakePages(1200, " ".join(sorted(terms_by_document[key]))),
        )

    monkeypatch.setattr("pypdf.PdfReader", reader)
    monkeypatch.setattr(hardware_extract, "file_sha256", lambda path: "a" * 64)

    artifact = hardware_extract.extract_profile()

    assert artifact["state"] == "complete"
    assert len(artifact["documents"]) == 3
    assert len(artifact["citations"]) == 8
    assert len(artifact["entities"]) == 7
    assert len(artifact["assertions"]) == 9
    assert "dataset_id" not in artifact