from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rtd_pdf_common import SCHEMA_VERSION, TOOL_VERSION, validate_payload, write_json_atomic


def reconcile(um: dict[str, object], im: dict[str, object]) -> dict[str, object]:
    validate_payload(um, "um.schema.json")
    validate_payload(im, "im.schema.json")
    if um["module"] != im["module"]:
        raise ValueError(f"module mismatch: UM={um['module']}, IM={im['module']}")

    relationships: list[dict[str, object]] = []
    for item in um["configuration_items"]:
        relationships.append(
            {
                "type": "documents",
                "from": f"document:{um['source']['document']}",
                "to": f"configuration:{item['identifier']}",
                "confidence": 1.0,
            }
        )
    for area in im["exclusive_areas"]:
        relationships.append(
            {
                "type": "documents",
                "from": f"document:{im['source']['document']}",
                "to": f"exclusive-area:{area['identifier']}",
                "confidence": 1.0,
            }
        )
        for function in area["uses"]:
            relationships.append(
                {
                    "type": "uses-exclusive-area",
                    "from": f"api:{function}",
                    "to": f"exclusive-area:{area['identifier']}",
                    "confidence": area["source"]["confidence"],
                }
            )

    relationships.sort(key=lambda item: (str(item["type"]), str(item["from"]), str(item["to"])))
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "module": um["module"],
        "sources": {"um": um["source"], "im": im["source"]},
        "relationships": relationships,
        "unresolved": [],
        "warnings": [],
    }
    validate_payload(payload, "module.schema.json")
    return payload


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Reconcile schema-valid RTD UM and IM JSON")
    command.add_argument("--um", type=Path, required=True)
    command.add_argument("--im", type=Path, required=True)
    command.add_argument("--output", type=Path)
    command.add_argument("--json", action="store_true")
    return command


def main() -> int:
    arguments = parser().parse_args()
    try:
        um = json.loads(arguments.um.read_text(encoding="utf-8"))
        im = json.loads(arguments.im.read_text(encoding="utf-8"))
        payload = reconcile(um, im)
        if arguments.output:
            write_json_atomic(arguments.output.resolve(), payload)
        if arguments.json or not arguments.output:
            print(json.dumps(payload, indent=2, ensure_ascii=True))
        else:
            print(f"created {len(payload['relationships'])} relationships")
        return 0
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())