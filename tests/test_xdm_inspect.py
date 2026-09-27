from pathlib import Path

import pytest
import xdm_inspect


def test_inspect_preserves_hierarchy_and_enable_metadata(tmp_path: Path) -> None:
    xdm = tmp_path / "Gpt.xdm"
    xdm.write_text(
        """<?xml version='1.0'?>
<datamodel xmlns:d="http://www.tresos.de/_projects/DataModel2/06/data.xsd"
           xmlns:a="http://www.tresos.de/_projects/DataModel2/18/attribute.xsd">
  <d:ctr name="Gpt" type="AR-PACKAGE">
    <d:ctr name="General" type="IDENTIFIABLE">
      <d:var name="GptWakeup" type="BOOLEAN" value="false">
        <a:a name="ENABLE" value="false"/>
      </d:var>
    </d:ctr>
  </d:ctr>
</datamodel>
""",
        encoding="utf-8",
    )

    entries = xdm_inspect.inspect_file(xdm)
    selected = xdm_inspect.select_entries(entries, "GptWakeup", "Gpt", "var")

    assert len(selected) == 1
    assert selected[0].path == "Gpt/General/GptWakeup"
    assert selected[0].value == "false"
    assert selected[0].enabled == "false"


@pytest.mark.parametrize("name", ["McuTimeout", "PortPinPcr", "CanTimeoutDuration", "GptDeinitApi"])
def test_workspace_contains_representative_parameter(name: str) -> None:
    entries = xdm_inspect.inspect_paths(sorted(xdm_inspect.DEFAULT_CONFIG.glob("*.xdm")))

    assert xdm_inspect.select_entries(entries, name, None, "var")


def test_all_workspace_xdm_files_are_parseable() -> None:
    paths = sorted(xdm_inspect.DEFAULT_CONFIG.glob("*.xdm"))

    assert len(paths) == 11
    assert xdm_inspect.inspect_paths(paths)