---
name: mcal-hardware-pdf-extractor
description: "Use for extracting cited hardware facts from S32K3 reference manuals, datasheets, and board manuals, including peripherals, registers, fields, constraints, device applicability, and candidate links to AUTOSAR MCAL configuration definitions."
argument-hint: "Name the hardware peripheral or profile to extract and validate"
user-invocable: true
disable-model-invocation: false
---

# MCAL Hardware PDF Extractor

Extract provenance-bearing hardware facts from local reference manuals, datasheets, and board
manuals. This skill emits validated JSON only; it never connects to or modifies Neo4j,
Elasticsearch, Tresos XDM, preferences, or generated output.

## Workflow

1. Select a committed hardware profile under `profiles/`.
2. Hash each declared source PDF and validate every required text anchor on its physical page.
3. Emit source-neutral documents, citations, entities, topology, and assertion candidates.
4. Preserve assertion status, extraction confidence, rationale, device scope, units, and page labels.
5. Write the complete artifact atomically under `.cache/mcal-hardware-pdf-extractor/`.
6. Let `mcal-graph-loader` resolve RTD definition selectors and load the resulting immutable dataset.

## Commands

```powershell
poetry run python .github/skills/mcal-hardware-pdf-extractor/scripts/hardware_extract.py --json
```

## Interpretation Rules

- Profile facts must be supported by declared citations.
- Use `verified` only when the cited text directly supports the candidate relationship.
- Use `inferred` or `unresolved` when terminology or device applicability requires interpretation.
- Preserve family and exact-derivative applicability as different entities.
- A `Device` entity records source applicability only; it does not bind the current project or
	physical board to that device without separate explicit project evidence.
- Do not derive peripheral/register hierarchy from underscore or colon notation alone.

## Boundaries

- Never edit `config/**/*.xdm`, `.prefs/**/*.xdm`, or generated `output/**`.
- Never write directly to Neo4j or Elasticsearch.
- Never store database credentials in profiles or generated artifacts.
- Never treat extraction confidence as technical truth or review approval.
