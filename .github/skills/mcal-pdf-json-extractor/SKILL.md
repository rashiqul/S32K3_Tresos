---
name: mcal-pdf-json-extractor
description: "Use for extracting AUTOSAR MCAL RTD user manuals (UM) and integration manuals (IM) from local PDFs into validated per-module JSON, including configuration parameters, integration topics, exclusive areas, provenance, and relationships."
argument-hint: "Name an MCAL module such as ADC, or request extraction/validation for all manual pairs"
user-invocable: true
disable-model-invocation: false
---

# MCAL PDF JSON Extractor

Extract structured, provenance-bearing JSON from local PDFs under `docs/`. This skill owns the
complete searchable page corpus plus paired RTD UM configuration extraction, IM integration
extraction, JSON Schema validation, and source-preserving reconciliation.

## Workflow

1. Discover complete `RTD_<MODULE>_UM.pdf` and `RTD_<MODULE>_IM.pdf` pairs.
2. Run the UM and IM parsers independently.
3. Validate each source artifact against its committed Draft 2020-12 JSON Schema.
4. Reconcile exact document and exclusive-area relationships without overwriting source facts.
5. Review the manifest, warnings, confidence, physical PDF pages, and printed page labels.
6. Extract all local PDFs into bounded page chunks with document hashes, outline headings, and
    previous/next chunk identity for Elasticsearch ingestion.

Extract one module:

```powershell
poetry run python .github/skills/mcal-pdf-json-extractor/scripts/rtd_extract.py --module ADC --json
```

Extract every complete pair:

```powershell
poetry run python .github/skills/mcal-pdf-json-extractor/scripts/rtd_extract.py --all --json
```

Outputs are written atomically under `.cache/mcal-pdf-json-extractor/structured/<module>/` as
`um.json`, `im.json`, and `module.json`. The root `manifest.json` reports parsed, unchanged,
incomplete, failed, and warning-bearing modules.

## Interpretation Rules

- Treat the UM as authoritative for configuration parameter semantics.
- Treat the IM as authoritative for integration topics and exclusive areas.
- Preserve source document hashes, physical PDF pages, printed page labels, section titles,
  extraction method, and confidence.
- Treat missing or ambiguous values as omissions or warnings; never infer undocumented values.
- Ignore figures and image content. Confirm complex table layouts against the cited PDF page.
- Treat reconciled relationships as extracted links, not as stronger evidence than their sources.

## Boundaries

- Read PDFs only from the requested docs directory unless the user explicitly selects another path.
- Never edit `config/**/*.xdm`, `.prefs/**/*.xdm`, or generated `output/**`.
- Keep generated JSON under `.cache/` unless the user explicitly requests another output directory.
- Do not stop, restart, or clean unrelated parsing, indexing, or editor processes.
- Validate outputs and report failures or warnings; do not silently discard malformed modules.