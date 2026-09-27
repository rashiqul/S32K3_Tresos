from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CONFIG = PROJECT_ROOT / "config"
DATA_NAMESPACE = "http://www.tresos.de/_projects/DataModel2/06/data.xsd"
ATTRIBUTE_NAMESPACE = "http://www.tresos.de/_projects/DataModel2/18/attribute.xsd"
DATA_TAGS = {f"{{{DATA_NAMESPACE}}}{name}": name for name in ("ctr", "lst", "var", "ref", "chc")}
ATTRIBUTE_TAG = f"{{{ATTRIBUTE_NAMESPACE}}}a"


@dataclass(frozen=True)
class XdmEntry:
    file: str
    module: str
    path: str
    kind: str
    name: str
    type: str | None
    value: str | None
    enabled: str | None


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def attribute_value(element: ET.Element, name: str) -> str | None:
    for child in element:
        if child.tag == ATTRIBUTE_TAG and child.get("name") == name:
            if child.get("value") is not None:
                return child.get("value")
            values = [value.text or "" for value in child if value.text]
            return ", ".join(values) if values else None
    return None


def inspect_file(path: Path) -> list[XdmEntry]:
    root = ET.parse(path).getroot()
    entries: list[XdmEntry] = []

    def visit(element: ET.Element, ancestors: tuple[str, ...], module: str) -> None:
        kind = DATA_TAGS.get(element.tag)
        current_ancestors = ancestors
        current_module = module
        if kind:
            name = element.get("name") or f"<{kind}>"
            current_ancestors = (*ancestors, name)
            if kind == "ctr" and element.get("type") == "AR-PACKAGE" and element.get("name"):
                current_module = element.get("name", module)
            entries.append(
                XdmEntry(
                    file=relative_path(path),
                    module=current_module,
                    path="/".join(current_ancestors),
                    kind=kind,
                    name=name,
                    type=element.get("type"),
                    value=element.get("value"),
                    enabled=attribute_value(element, "ENABLE"),
                )
            )
        for child in element:
            visit(child, current_ancestors, current_module)

    visit(root, (), path.stem)
    return entries


def inspect_paths(paths: Iterable[Path]) -> list[XdmEntry]:
    entries: list[XdmEntry] = []
    for path in paths:
        entries.extend(inspect_file(path))
    return entries


def select_entries(
    entries: Iterable[XdmEntry], name: str | None, module: str | None, kind: str | None
) -> list[XdmEntry]:
    selected = []
    for entry in entries:
        if name and entry.name.casefold() != name.casefold():
            continue
        if module and entry.module.casefold() != module.casefold():
            continue
        if kind and entry.kind != kind:
            continue
        selected.append(entry)
    return selected


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Read-only inspection of Tresos XDM configuration")
    command.add_argument("paths", nargs="*", type=Path, help="XDM files; defaults to config/*.xdm")
    command.add_argument("--name", help="exact parameter or container name")
    command.add_argument("--module", help="exact module name")
    command.add_argument("--kind", choices=sorted(set(DATA_TAGS.values())))
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    paths = arguments.paths or sorted(DEFAULT_CONFIG.glob("*.xdm"))
    try:
        entries = select_entries(
            inspect_paths(path.resolve() for path in paths),
            arguments.name,
            arguments.module,
            arguments.kind,
        )
        if arguments.json:
            print(json.dumps([asdict(entry) for entry in entries], indent=2, ensure_ascii=True))
        else:
            for entry in entries:
                details = [f"kind={entry.kind}"]
                if entry.type:
                    details.append(f"type={entry.type}")
                if entry.value is not None:
                    details.append(f"value={entry.value}")
                if entry.enabled is not None:
                    details.append(f"enabled={entry.enabled}")
                print(f"{entry.file}:{entry.path} | {' | '.join(details)}")
        return 0
    except (OSError, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())