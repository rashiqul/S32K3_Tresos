# MCAL Graph and Search Architecture

Last updated: 2026-09-27

## Purpose

This document is the authoritative architecture, implementation, and operations reference for the
local AUTOSAR MCAL knowledge pipeline. It replaces the earlier Neo4j/Elasticsearch handoff and
PDF-to-graph implementation plan.

The pipeline converts local manuals and read-only Tresos project state into one immutable dataset
shared by Neo4j and Elasticsearch. The advisory `mcal-reference-s32k358` skill queries only the
matching active dataset through the graph/search adapter.

## Current Implementation

Four independent skills own the workflow:

| Skill | Responsibility |
| --- | --- |
| `mcal-pdf-json-extractor` | Extract RTD UM/IM structures and the complete searchable PDF page corpus. |
| `mcal-hardware-pdf-extractor` | Validate reference-manual/datasheet anchors and emit database-neutral hardware facts and mapping candidates. |
| `mcal-graph-loader` | Normalize source facts, snapshot XDM read-only, build search chunks, load both stores, verify, and activate datasets. |
| `mcal-reference-s32k358` | Provide evidence-backed advisory guidance using active graph/search retrieval and read-only XDM inspection. |

The active dataset is
`dataset:1cc76962f28df7770c464f2009b74079aff8ce43c084a5f8321412346ceb6f74`.
Its verified manifest contains:

- 36 RTD modules and 11 XDM files.
- 79 PDFs and 11,996 source-page chunks.
- 22,548 graph entities.
- 26,814 structural relationships.
- 6,583 evidence-bearing assertions.
- 16,549 Elasticsearch chunks.

The primary implementation surfaces are:

| File or symbol | Responsibility |
| --- | --- |
| `.github/skills/mcal-graph-loader/scripts/build_dataset.py::build_dataset` | Validate inputs and atomically publish an immutable dataset. |
| `.github/skills/mcal-graph-loader/scripts/normalize_graph.py` | Normalize RTD definitions and current XDM instances without short-name collisions. |
| `.github/skills/mcal-hardware-pdf-extractor/scripts/hardware_extract.py::extract_profile` | Validate PDF anchors and emit database-neutral hardware JSON. |
| `.github/skills/mcal-graph-loader/scripts/normalize_hardware.py::normalize_hardware_artifact` | Resolve hardware facts and RTD selectors into graph records. |
| `.github/skills/mcal-graph-loader/scripts/normalize_corpus.py::normalize_corpus` | Join complete page chunks to citations and mentioned graph entities. |
| `.github/skills/mcal-graph-loader/scripts/build_chunks.py::build_chunks` | Produce citation-backed Elasticsearch documents. |
| `.github/skills/mcal-graph-loader/scripts/query_knowledge.py::query_active` | Search the active alias and expand linked active-dataset graph context. |
| `.github/skills/mcal-graph-loader/scripts/manage_stores.py::load_neo4j` | Install constraints and idempotently load graph records. |
| `.github/skills/mcal-graph-loader/scripts/manage_stores.py::load_elasticsearch` | Create and bulk-load the immutable concrete search index. |
| `.github/skills/mcal-graph-loader/scripts/manage_stores.py::verify_stores` | Compare both stores with the dataset manifest and verify assertion support. |
| `.github/skills/mcal-graph-loader/scripts/manage_stores.py::activate` | Coordinate the alias, Neo4j state, and local active pointer. |

## Safety Boundary

- Never modify `config/**/*.xdm`, `.prefs/**/*.xdm`, or generated `output/**` through this
  workflow.
- Treat XDM values as saved project state, not vendor defaults or validated application intent.
- Load only immutable datasets whose manifest state is `complete` and whose artifact hashes pass.
- Keep credentials only in ignored `infra/search/.env`; never write them to datasets or logs.
- Bind Neo4j and Elasticsearch ports to localhost only.
- Do not use `docker compose down -v` during normal operation. Named volumes preserve loaded data.
- Do not classify family-level S32K3 statements as exact S32K358 applicability without derivative
  evidence.

## Source and Dataset Flow

1. `mcal-pdf-json-extractor` writes validated UM/IM structures and complete page chunks beneath
   `.cache/mcal-pdf-json-extractor/`.
2. `mcal-hardware-pdf-extractor` validates configured PDF anchors and writes neutral hardware JSON
   beneath `.cache/mcal-hardware-pdf-extractor/` without database access.
3. `build_dataset.py` requires complete extractor artifacts with no failures and validates every
   source artifact.
4. The builder hashes and snapshots source JSON plus all current `config/*.xdm` files. XDM
   inspection is delegated to the read-only `xdm_inspect.py --json` interface.
5. RTD definitions, XDM instances, hardware evidence, assertions, citations, and search chunks are
   normalized with deterministic IDs.
6. The builder validates schemas, endpoints, citation reachability, hashes, and counts before an
   atomic rename publishes `.cache/mcal-graph-loader/datasets/<digest>/`.
7. A concurrent builder that loses the publication race accepts the winner only when its manifest
   has the same complete dataset identity.

A complete dataset contains:

```text
manifest.json
graph/nodes.jsonl
graph/relationships.jsonl
graph/assertions.jsonl
graph/xdm-snapshot.json
search/chunks.jsonl
sources/rtd/
sources/corpus/
sources/hardware/
sources/xdm/
```

The dataset ID includes graph schema, normalizer, chunker, both extractor versions and artifacts,
source PDF hashes, XDM, hardware profile, and hardware-document identities. Timestamps are metadata,
not identity inputs. Unchanged inputs therefore produce the same dataset ID.

## Identity and Evidence Contracts

Stable IDs are SHA-256 values derived from normalized identity-bearing fields. Database-native IDs
and display names never cross store boundaries.

- A document is identified by normalized path and SHA-256.
- A citation includes document identity, physical page, embedded page label, section, and text
  anchor.
- A manual configuration definition includes module, document, section, kind, and identifier.
- An XDM instance includes project ID, XDM file, and complete instance path.
- A register field includes its parent register, field name, and bit range.
- A dataset-scoped `graph_id` joins immutable records safely inside Neo4j.

Short identifiers are search/display properties only. This preserves distinct definitions such as
the global and per-clock-setting instances of `McuFxoscUnderMcuControl`.

Evidence-bearing claims are reified as `Assertion` nodes:

```text
(Assertion)-[:SUBJECT]->(Entity)
(Assertion)-[:OBJECT]->(Entity)
(Assertion)-[:SUPPORTED_BY]->(Citation)
```

Only deterministic topology such as `BELONGS_TO` and `HAS_CITATION` is stored as a direct
relationship. Assertions keep these independent dimensions:

- `assertion_status`: `verified`, `inferred`, `unresolved`, or `rejected`.
- `review_status`: human review lifecycle, independent of extraction.
- `extraction_confidence`: confidence in text extraction, not technical truth.
- `citation_ids`: evidence supporting the relationship itself.
- `rationale`: required context for inferred or unresolved links.

Verified assertions must reach at least one citation. Inferred and unresolved assertions remain out
of authoritative expansion until accepted by review policy.

## Store Responsibilities

Neo4j owns canonical entities, structural relationships, assertions, and citation traversal.
Constraints enforce dataset-scoped `graph_id` uniqueness, and a shared `GraphEntity` index supports
endpoint loading by dataset and stable ID.

Elasticsearch owns citation-backed prose retrieval and denormalized filters. Each chunk records the
same dataset ID plus citation, source-chunk continuity, document path, module, peripheral, term,
device, page, heading, extraction method, document hash, and chunker version. The active alias is
`mcal-reference-chunks`.

`query_knowledge.py` verifies that the alias, local pointer, and active Neo4j `Dataset` agree before
searching. It rejects inactive or mixed-dataset results, then expands returned `term_ids` through
Neo4j entities and evidence-bearing assertions.

## Operations

Configure and start the local services:

```powershell
Copy-Item infra/search/.env.example infra/search/.env
# Set a unique NEO4J_PASSWORD in infra/search/.env.
just graph-activate
```

Build and operate datasets:

```powershell
just extract-all
just graph-stage
just graph-activate
just status
just search-down
```

`graph-activate` validates and starts both stores, then resolves, loads, verifies, and activates the
latest complete local dataset. The Python CLI remains available for advanced load-only,
verify-only, or exact `--dataset <path>` operation.

Routine cleanup preserves pipeline state:

```powershell
just clean
```

This removes the Python environment and disposable test/lint/type caches. For an intentional local
reset, remove `.venv` and `.cache` explicitly; that also removes extractor output, staged datasets,
and the active pointer. Docker named volumes are unaffected.

## Loading, Verification, and Activation

Loading is bounded and idempotent:

1. Validate the selected complete dataset and every listed artifact hash.
2. Create allowlisted Neo4j constraints and indexes if absent.
3. `MERGE` graph entities, structural relationships, assertions, and citation links by stable
   dataset-scoped identity.
4. Create the immutable Elasticsearch index
   `mcal-reference-chunks-<dataset-digest>` and bulk-index chunks by `chunk_id`.

Verification then requires:

- Neo4j entity, structural-relationship, and assertion counts equal the manifest.
- Every verified assertion has a `SUPPORTED_BY` citation.
- Elasticsearch chunk count equals the manifest.

Activation occurs only after verification succeeds:

1. Atomically move the Elasticsearch alias to the candidate index.
2. Mark the matching Neo4j `Dataset` node active and demote the previous active marker.
3. Atomically write `.cache/mcal-graph-loader/active-dataset.json` last.

If Neo4j activation fails after the alias swap, the implementation compensates by restoring the
previous Elasticsearch alias. There is no explicit operator rollback command yet, and the two
stores cannot share one database transaction.

## MCU/FXOSC Evidence Slice

The production profile is
`.github/skills/mcal-hardware-pdf-extractor/profiles/mcu-fxosc.json`. The hardware extractor verifies
eight text anchors in the RTD MCU user manual, S32K3 reference manual, and S32K3xx datasheet before
emitting neutral hardware facts and mapping candidates. The graph loader resolves those candidates
against exact RTD definition selectors.

The slice includes:

- `Peripheral(FXOSC)`.
- `Register(FXOSC.CTRL)` and `RegisterField(FXOSC.CTRL.OSCON)`.
- The 8-40 MHz crystal-mode constraint.
- A verified mapping from `McuFxoscPowerDownCtr` to `FXOSC.CTRL.OSCON`.
- An inferred `McuCrystalFrequencyHz` to FXOSC link because the RTD parameter description does not
  explicitly name the peripheral.
- Family and derivative applicability kept distinct.

One project observation remains unresolved: the saved global FXOSC-control value is true while
`McuClockSettingConfig` is empty. The documented any-per-setting derivation therefore cannot be
demonstrated from saved XDM alone. Run Tresos validation and inspect effective/generated
configuration before classifying this as an error.

## Advisory Query Cutover

SQLite retrieval was retired after the active adapter met these implemented gates:

1. It constrains Elasticsearch and Neo4j to the same active dataset.
2. Exact parameter queries rank the cited definition page above the former overview-page result.
3. Reference-manual register and datasheet-limit queries match the former source and physical page.
4. Returned search hits retain citation IDs, document paths, pages, headings, and linked entities.
5. Tests reject inactive alias/pointer mismatches and mixed-dataset search hits.

The fixed comparison queries were `McuTimeout`, `McuFxoscPowerDownCtr`, `FXOSC OSCON`, and
`FXOSC_CLK crystal mode 40 MHz`. The first two improved ranking; the latter two matched the former
SQLite source/page result.

## Remaining Work

- Expand the fixed query-quality regression suite and add authority-aware ranking.
- Add explicit inferred/unresolved assertion query options.
- Add an operator rollback command, dataset diff utility, and store retention policy.
- Generalize reference-manual register/field extraction beyond MCU/FXOSC.
- Generalize datasheet constraints and exact device/package applicability.
- Add OCR and complex table/diagram recovery where embedded text is insufficient.
- Add conflict detection across RTD, reference-manual, datasheet, and project-state evidence.
- Add structured ISR, callback, memory-section, and integration-step relationships.