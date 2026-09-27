---
name: mcal-reference-s32k358
description: "Use for S32K358 or S32K3 AUTOSAR MCAL configuration in Tresos, including RTD parameters, registers, clocks, pins, interrupts, DMA, MCU, Port, Dio, Platform, MCL, GPT, FlexCAN, LIN, BaseNXP, Resource, and EcuC. Searches local manuals and inspects XDM read-only before giving cited configuration guidance."
argument-hint: "Describe the peripheral behavior or MCAL configuration to investigate"
user-invocable: true
disable-model-invocation: false
---

# S32K358 MCAL Reference

Provide evidence-based configuration guidance for this S32K358 Tresos project. This skill is advisory-only: never modify `config/**/*.xdm`, `.prefs/**/*.xdm`, or `output/**`.

## Workflow

1. Restate the requested hardware behavior and identify missing inputs such as bus frequency, baud rate, pin, peripheral instance, timing tolerance, interrupt model, or low-power requirement.
2. Read [target-context](./references/target-context.md) and
   [project-profile](./references/project-profile.md), then select the affected modules using
   [module-workflows](./references/module-workflows.md). Stop final hardware-dependent recommendations
   when derivative, package, board revision, fitted component, or oscillator identity is unresolved.
3. Inspect current values without editing them:

   ```powershell
   poetry run python .github/skills/mcal-reference-s32k358/scripts/xdm_inspect.py --name McuTimeout --json
   ```

4. Select authoritative local sources using [document-map](./references/document-map.md) and [source-policy](./references/source-policy.md).
5. Query the active Elasticsearch corpus and linked Neo4j entities using exact register/parameter names and broader concepts:

   ```powershell
   poetry run python .github/skills/mcal-graph-loader/scripts/query_knowledge.py "McuTimeout" --module Mcu --json
   poetry run python .github/skills/mcal-graph-loader/scripts/query_knowledge.py "FXOSC OSCON" --source-type reference-manual --json
   ```

6. Reconcile the current XDM, RTD guidance, reference-manual behavior, datasheet limits, and EVB routing. Treat current values as project state, not vendor defaults.
7. Show calculations with units and intermediate values. State every assumed clock, tolerance, divider, timing segment, or package pin.
8. Respond using [response-contract](./references/response-contract.md). Recommend exact Tresos container/parameter paths, but do not apply changes.

## Dataset Maintenance

Extract, stage, and activate a new immutable dataset when a PDF, XDM file, or extraction profile changes:

```powershell
just extract-all
just graph-stage
just graph-activate
```

Query only the active dataset. Never combine an Elasticsearch result with entities from a different
Neo4j dataset ID.

## Structured RTD Extraction

Use `/mcal-pdf-json-extractor` for RTD structures and searchable page text. Use
`/mcal-hardware-pdf-extractor` for cited reference-manual, datasheet, and board-manual hardware facts.
Their validated artifacts support this advisory workflow, but recommendations must still be
confirmed against source citations and current XDM state.

## Boundaries

- Use local project documents before external sources.
- Ask for explicit permission before web research when local evidence is insufficient.
- Do not invent manual sections, page numbers, reset values, field meanings, limits, or supported instances.
- Do not treat structured extraction as stronger evidence than the cited manual page.
- Do not treat a graph `Device` entity, project name, board-manual filename, or default XDM
   subderivative as proof of the fitted target.
- Do not edit generated EPC output or claim static analysis proves hardware correctness.
- Clearly distinguish confirmed facts, calculations, recommendations, and unresolved assumptions.
- When implementation changes this skill's capabilities, scope, workflow, setup, limitations, validation status, or milestone, update the dated `Project Status` section in `README.md` in the same change.
