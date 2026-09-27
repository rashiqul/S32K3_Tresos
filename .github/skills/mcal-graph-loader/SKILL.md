---
name: mcal-graph-loader
description: "Use for staging, validating, loading, activating, and querying AUTOSAR MCAL knowledge datasets in Docker-based Neo4j and Elasticsearch, including RTD definitions, read-only Tresos XDM instances, register mappings, datasheet constraints, citations, and assertion review states."
argument-hint: "Stage, validate, load, verify, activate, or query an MCAL graph dataset"
user-invocable: true
disable-model-invocation: false
---

# MCAL Graph Loader

Build and query provenance-bearing AUTOSAR MCAL datasets without modifying Tresos configuration.
This skill consumes completed JSON from `mcal-pdf-json-extractor` and
`mcal-hardware-pdf-extractor`, snapshots current XDM state read-only, and coordinates one immutable
dataset across Neo4j and Elasticsearch.

## Workflow

1. Require a complete extractor manifest with no failures or incomplete modules.
2. Snapshot and validate source JSON and current XDM state into an immutable dataset.
3. Generate deterministic graph entities, assertions, citations, and search chunks.
4. Validate stable IDs, endpoints, evidence, counts, hashes, and source applicability offline.
5. Load an inactive dataset into Neo4j and Elasticsearch with bounded, idempotent operations.
6. Verify both stores against the same manifest before activation.
7. Query only the active dataset and preserve citation and assertion-state information.

## Interpretation Rules

- Treat RTD UM records as configuration definitions, not current XDM instances.
- Treat complete XDM paths as project-instance identities; short names are lookup properties only.
- Represent evidence-bearing technical claims as assertion nodes linked to source citations.
- Keep `verified`, `inferred`, `unresolved`, and `rejected` assertions distinct.
- Do not use extraction confidence as assertion truth or human review state.
- Require exact derivative evidence before applying family-level constraints to S32K358.

## Boundaries

- Never modify `config/**/*.xdm`, `.prefs/**/*.xdm`, or generated `output/**`.
- Never load from live extractor output; stage and hash a completed snapshot first.
- Never activate a dataset unless both Neo4j and Elasticsearch verification pass.
- Keep credentials only in ignored `infra/search/.env`; never store them in datasets or logs.
- Query only matching active dataset IDs across Neo4j and Elasticsearch.

## Commands

```powershell
just graph-stage
just graph-activate
just status
just search-down
```

`graph-activate` validates and starts both services before load, verification, and coordinated
activation. It swaps the Elasticsearch alias only after loading succeeds, compensates that swap if
Neo4j activation fails, and writes the local active pointer last. Use `manage_stores.py` directly
for advanced load-only or verify-only operation. The production MCU/FXOSC slice verifies its RTD,
reference-manual, and datasheet text anchors during staging.

The advisory skill uses `query_knowledge.py` for citation-bearing Elasticsearch retrieval followed
by Neo4j entity and assertion expansion.