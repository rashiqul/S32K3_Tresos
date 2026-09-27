from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rtd_im_parser import parse_integration_manual
from rtd_pdf_common import (
    DEFAULT_DOCS,
    PROJECT_ROOT,
    SCHEMA_VERSION,
    TOOL_VERSION,
    ManualPair,
    discover_manual_pairs,
    file_sha256,
    write_json_atomic,
)
from rtd_reconcile import reconcile
from rtd_um_parser import parse_user_manual

DEFAULT_OUTPUT = PROJECT_ROOT / ".cache" / "mcal-pdf-json-extractor" / "structured"


def _load_json(path: Path) -> dict[str, object] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def outputs_are_current(pair: ManualPair, output: Path) -> bool:
    if not pair.complete or pair.user_manual is None or pair.integration_manual is None:
        return False
    um = _load_json(output / "um.json")
    im = _load_json(output / "im.json")
    module = _load_json(output / "module.json")
    if um is None or im is None or module is None:
        return False
    return (
        um.get("schema_version") == SCHEMA_VERSION
        and im.get("schema_version") == SCHEMA_VERSION
        and module.get("schema_version") == SCHEMA_VERSION
        and um.get("tool_version") == TOOL_VERSION
        and im.get("tool_version") == TOOL_VERSION
        and module.get("tool_version") == TOOL_VERSION
        and um.get("source", {}).get("sha256") == file_sha256(pair.user_manual.path)
        and im.get("source", {}).get("sha256") == file_sha256(pair.integration_manual.path)
    )


def _warning_count(um: dict[str, object], im: dict[str, object]) -> int:
    return len(um.get("warnings", [])) + len(im.get("warnings", []))


def extract_pair(pair: ManualPair, output_root: Path, force: bool = False) -> tuple[str, int]:
    if not pair.complete or pair.user_manual is None or pair.integration_manual is None:
        raise ValueError(f"module {pair.module} does not have a complete UM/IM pair")
    output = output_root / pair.module
    if not force and outputs_are_current(pair, output):
        um = _load_json(output / "um.json") or {}
        im = _load_json(output / "im.json") or {}
        return "unchanged", _warning_count(um, im)

    um = parse_user_manual(pair.user_manual.path)
    im = parse_integration_manual(pair.integration_manual.path)
    module = reconcile(um, im)
    write_json_atomic(output / "um.json", um)
    write_json_atomic(output / "im.json", im)
    write_json_atomic(output / "module.json", module)
    return "parsed", _warning_count(um, im)


def extract_corpus(
    docs: Path, output: Path, modules: list[str] | None = None, force: bool = False
) -> dict[str, object]:
    pairs = discover_manual_pairs(docs)
    requested = {module.casefold() for module in modules or []}
    selected = [pair for pair in pairs if not requested or pair.module.casefold() in requested]
    found = {pair.module.casefold() for pair in selected}
    missing = sorted(set(requested) - found)
    if missing:
        raise ValueError(f"unknown modules: {', '.join(missing)}")

    parsed: list[str] = []
    unchanged: list[str] = []
    failures: list[dict[str, str]] = []
    incomplete: list[str] = []
    warnings: list[dict[str, object]] = []
    for pair in selected:
        if not pair.complete:
            incomplete.append(pair.module)
            continue
        try:
            status, warning_count = extract_pair(pair, output, force)
            (parsed if status == "parsed" else unchanged).append(pair.module)
            if warning_count:
                warnings.append({"module": pair.module, "count": warning_count})
        except Exception as error:  # noqa: BLE001 - one malformed module must not abort the corpus.
            failures.append({"module": pair.module, "error": str(error)})

    manifest: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "pairs_discovered": len(pairs),
        "modules_selected": len(selected),
        "parsed": parsed,
        "unchanged": unchanged,
        "incomplete": incomplete,
        "failures": failures,
        "warnings": warnings,
    }
    write_json_atomic(output / "manifest.json", manifest)
    return manifest


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Extract structured data from paired RTD manuals")
    command.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    command.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    command.add_argument("--module", action="append")
    command.add_argument("--all", action="store_true")
    command.add_argument("--force", action="store_true")
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    if not arguments.all and not arguments.module:
        print("error: select --module at least once or use --all", file=sys.stderr)
        return 2
    try:
        payload = extract_corpus(
            arguments.docs.resolve(),
            arguments.output.resolve(),
            None if arguments.all else arguments.module,
            arguments.force,
        )
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 1 if payload["failures"] else 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())