import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = PROJECT_ROOT / ".github" / "skills" / "mcal-reference-s32k358"


def test_target_context_blocks_unconfirmed_hardware_identity() -> None:
    skill = (REFERENCE_ROOT / "SKILL.md").read_text(encoding="utf-8")
    target_context = (REFERENCE_ROOT / "references" / "target-context.md").read_text(
        encoding="utf-8"
    )
    workflows = (REFERENCE_ROOT / "references" / "module-workflows.md").read_text(
        encoding="utf-8"
    )

    assert "target-context" in skill
    assert "s32k389_mapbga437" in target_context
    assert "McuClockSettingConfig" in target_context
    assert "CAN transceiver" in target_context
    assert "NVM" in target_context
    assert "Mandatory Target Context" in workflows


def test_tasks_do_not_restore_module_specific_adc_extraction() -> None:
    tasks = json.loads((PROJECT_ROOT / ".vscode" / "tasks.json").read_text(encoding="utf-8"))
    labels = {task["label"] for task in tasks["tasks"]}

    assert "MCAL PDF Extractor: Extract ADC" not in labels
    assert "MCAL PDF Extractor: Extract All" in labels