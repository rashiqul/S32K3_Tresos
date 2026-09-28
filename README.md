# S32K358 Tresos MCAL Project

This workspace contains the Tresos AUTOSAR MCAL configuration for the S32K358 EVB and a local Copilot skill for evidence-based configuration guidance.

## MCAL Reference Skill

Invoke `/mcal-reference-s32k358` in Copilot Chat or ask about an S32K358/S32K3 MCAL module, register, clock, pin, interrupt, DMA, or Tresos parameter.

The skill:

- Inspects the current XDM configuration read-only.
- Searches manuals under `docs/` before considering web sources.
- Reports PDF page citations and exact Tresos parameter paths.
- Identifies cross-module dependencies and required validation.
- Never changes `config/` or generated `output/` files.

## Project Commands

Install [just](https://github.com/casey/just) and ensure Python 3.11 through 3.14 is available:

```powershell
winget install --id Casey.Just --exact --scope user
```

If VS Code was already running during installation, restart VS Code so new terminals inherit the updated user `PATH`. To refresh the current PowerShell session without restarting, run:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' + [Environment]::GetEnvironmentVariable('Path', 'User')
just --version
```

Then run these commands from the project root:

```powershell
just configure
```

- `just configure` ensures Poetry 2.x is installed and installs the locked project dependencies into the root `.venv`.
- `just clean` removes `.venv`, disposable Python tool caches, and nested `__pycache__` directories while preserving extracted JSON, staged graph datasets, and the active pointer.
- For an intentional full local reset, remove `.venv` and `.cache` explicitly. Docker named volumes are unaffected.

## Python Setup

Python 3.11 through 3.14 and Poetry 2.x are supported. Poetry is configured by `poetry.toml` to create `.venv` at the project root.

The preferred setup command is `just configure`. The underlying commands remain available for troubleshooting:

If `poetry` is not on `PATH`, use it as a Python module:

```powershell
python -m pip install poetry
python -m poetry install
```

The root `.venv`, generated knowledge datasets, and `.git` internals are excluded from Eclipse
resources in `.project`. Local build state is ignored by Git. Tresos-generated C sources and
headers under `output/src` and `output/include` are versioned alongside their configuration inputs.

## Git and Tresos Project Layout

This workspace is a Git repository on the `main` branch. Commit the reproducible project inputs:

- `.project` and `.prefs/pref_general.xdm`, which define the Eclipse/Tresos project and module set.
- `config/*.xdm`, which contains the saved MCAL configuration.
- `config/SystemModel2.tdb`, which is Tresos system-model project data. It is a binary SQLite file;
	coordinate changes and do not resolve conflicts by text-merging it.
- `output/src` and `output/include`, which contain generated C sources and headers. Regenerate and
	review them whenever the corresponding XDM configuration changes.
- `.github/skills/`, `tests/`, `justfile`, Poetry files, shared `.vscode/tasks.json`, and the checked-in
	Docker configuration and `.env.example`.

Do not commit generated or machine-local material:

- Vendor PDFs and other supplied documents are ignored globally. Provision the licensed manuals
	under `docs/` on each workstation before extraction; Markdown architecture documentation remains
	tracked.
- `output/output` contains generated EPC metadata and remains ignored.
- `.cache/`, `.venv/`, local databases, test/lint output, logs, archives, credentials, `.env` files,
	Eclipse workspace metadata, and developer-specific VS Code settings are ignored.

After cloning, import the repository root as an existing Tresos/Eclipse project, verify that the
required RTD plug-ins match `.prefs/pref_general.xdm`, provision the manuals, and run:

```powershell
just configure
just extract-all
just graph-stage
just graph-activate
```

Review XDM diffs as configuration changes and validate them in Tresos before merging. The
`SystemModel2.tdb` file is currently small enough for normal Git; use Git LFS only if its history
begins growing materially or the hosting platform requires it.

## Knowledge Query

Query the active Elasticsearch corpus and expand linked entities and assertions from Neo4j:

```powershell
python -m poetry run python .github/skills/mcal-graph-loader/scripts/query_knowledge.py "FXOSC OSCON" --source-type reference-manual --json
python -m poetry run python .github/skills/mcal-graph-loader/scripts/query_knowledge.py "CanControllerBaudrateConfig" --module Can_43_FLEXCAN --json
```

The adapter refuses inactive or mixed Neo4j/Elasticsearch dataset state. Results retain document,
physical page, printed page label, heading, citation ID, linked entities, and evidence-bearing
assertions.

## XDM Inspection

Find one parameter across the project:

```powershell
python -m poetry run python .github/skills/mcal-reference-s32k358/scripts/xdm_inspect.py --name McuTimeout --json
```

Inspect one module or one file:

```powershell
python -m poetry run python .github/skills/mcal-reference-s32k358/scripts/xdm_inspect.py --module Port --kind var
python -m poetry run python .github/skills/mcal-reference-s32k358/scripts/xdm_inspect.py config/Can_43_FLEXCAN.xdm --json
```

The inspector has no write operation. Current XDM values are project state and must not be presented as documented vendor defaults.

## Structured RTD Manual Extraction

The separate `/mcal-pdf-json-extractor` workspace skill owns structured PDF extraction and JSON
validation. It is independent from the advisory `/mcal-reference-s32k358` skill.

Extract the configuration parameters from one module's user manual, integration topics and exclusive
areas from its integration manual, and evidence-backed relationships between them:

```powershell
python -m poetry run python .github/skills/mcal-pdf-json-extractor/scripts/rtd_extract.py --module ADC --json
```

Extract all discovered complete RTD UM/IM pairs:

```powershell
just extract-all
```

The two source parsers remain independent. Their schema-validated outputs are written atomically to
`.cache/mcal-pdf-json-extractor/structured/<module>/um.json` and `im.json`; `module.json` contains typed
relationships without overwriting source facts. Each record preserves the physical PDF page, printed
page label, section, extraction method, and confidence. ADC and FlexCAN provide explicit profile
overrides, while other modules use shared RTD section conventions.

Figures and image content are ignored. Extraction warnings, fuzzy or unresolved relationships, and
table-layout anomalies require confirmation against the cited PDF page.

The separate `/mcal-hardware-pdf-extractor` skill validates reference-manual, datasheet, and board
manual anchors and emits database-neutral hardware entities, constraints, target-platform topology,
and mapping candidates. It never connects to Neo4j or Elasticsearch; only `mcal-graph-loader` loads
its validated artifact. The declared platform and unresolved oscillator evidence are recorded in
[TARGET_HARDWARE_PLATFORM.md](docs/architecture/TARGET_HARDWARE_PLATFORM.md).

## Immutable Graph Dataset

The separate `/mcal-graph-loader` skill stages completed extractor output and all 11 current XDM
files into one immutable, validated dataset without modifying Tresos configuration:

```powershell
just graph-stage
```

Generated datasets are stored under `.cache/mcal-graph-loader/datasets/<digest>/`. Each dataset
contains copied source artifacts, a read-only XDM snapshot, canonical graph JSONL, citation-backed
Elasticsearch chunks, and a manifest with source hashes and record counts. Repeating the command
with unchanged inputs returns the same dataset ID.

Load, verify, and activate the latest complete dataset after starting the local services:

```powershell
just graph-activate
just status
```

`graph-activate` validates and starts the local services, then idempotently loads, verifies, and
activates the latest complete dataset. The active pointer is written to
`.cache/mcal-graph-loader/active-dataset.json` only after both stores pass.

## Development Checks

```powershell
python -m poetry run pytest -q
python -m poetry run ruff check .github/skills/mcal-reference-s32k358/scripts .github/skills/mcal-pdf-json-extractor/scripts .github/skills/mcal-hardware-pdf-extractor/scripts .github/skills/mcal-graph-loader/scripts tests
```

VS Code also provides `MCAL Skill: Verify`, `MCAL PDF Extractor: Extract All`, and
`MCAL Graph Loader: Stage Dataset` and `MCAL Graph Loader: Activate Dataset` tasks.

After changing `.project`, refresh the project in Eclipse/Tresos and verify that `.venv` and `.cache` do not appear as project resources. Configuration recommendations still require Tresos validation and generation, generated-code compilation, and target-hardware testing.

## Graph and Full-Text Search

A local Docker Compose stack for Neo4j and Elasticsearch is available under `infra/search`.
The graph loader coordinates activation across both stores, and the advisory skill queries only
their matching active dataset.

```powershell
Copy-Item infra/search/.env.example infra/search/.env
# Set a unique NEO4J_PASSWORD in infra/search/.env.
just graph-activate
just status
```

See [infra/search/README.md](infra/search/README.md) for service endpoints, the initial data
contract, and local operations. See
[MCAL_GRAPH_SEARCH_ARCHITECTURE.md](docs/architecture/MCAL_GRAPH_SEARCH_ARCHITECTURE.md) for the implemented source
pipeline, graph and evidence contracts, coordinated activation behavior, and remaining work.

## Project Status

Last updated: 2026-09-27

### Current Milestone

The first advisory MCAL reference workflow is implemented and validated:

- One project skill covers all 11 currently configured MCAL modules.
- The complete searchable corpus contains 79 PDFs and 11,996 bounded page chunks with no extraction warnings.
- `S32K3XXRM.pdf` contributes 5,394 reference-manual pages.
- `S32K3xx_Datasheet.pdf` contributes 170 datasheet pages.
- The XDM inspector is read-only and resolves parameter/container hierarchy and enable metadata.
- Generated extractor, dataset, Pytest, and Ruff data is consolidated beneath the root `.cache/` directory rather than mixed into the disposable `.venv` environment.
- The automated suite contains 52 passing tests, with Ruff reporting no findings.
- `just configure` installs the supported environment, and `just clean` preserves pipeline data during routine cleanup.
- Tresos-generated C sources and headers are versioned under `output/src` and `output/include`;
	generated EPC metadata remains local.
- A localhost-only Docker Compose stack runs the active Neo4j graph and complete Elasticsearch PDF corpus used by the advisory query adapter.
- Independent UM and IM parsers cover all 36 discovered RTD manual pairs and validate their output with committed JSON Schemas.
- Structured extraction captures configuration parameter/container records, integration topics and identifiers, exclusive areas, source provenance, confidence, and typed relationships.
- ADC and FlexCAN pilot extractions validated the shared parser against differing manual structures.
- The Docker search workflow uses completed, immutable JSON datasets as the common source for Neo4j and Elasticsearch.
- The independent graph-loader skill stages all 36 RTD definition modules, 11 current XDM files, and a production MCU/FXOSC plus Q289 target-platform evidence slice into deterministic immutable datasets.
- The active dataset `dataset:d2b817d52eff606b5d84067b48a47252c77fbcd211ef0b9b4d68615c1907e90e` contains 22,568 nodes, 26,821 structural relationships, 6,597 assertions, and 16,556 Elasticsearch chunks.
- Neo4j and Elasticsearch loading is idempotent and dataset-scoped. Activation verifies both stores, swaps the `mcal-reference-chunks` alias, marks the matching Neo4j dataset active, and writes the local pointer last.
- The independent hardware extractor validates 15 local PDF evidence anchors and emits the MCU/FXOSC and Q289 platform artifact. The graph includes the board, MCU population, CAN0 and LIN1 transceivers, connectors, routed signals, and the Ethernet-only 50 MHz TXCLK source.
- Four migration queries matched or improved on the retired SQLite results for exact parameters, reference-manual register fields, and datasheet limits.

### Current Limitations

- PDF retrieval is lexical Elasticsearch search, not semantic or vector search. Queries work best with exact register, field, peripheral, or Tresos parameter terminology.
- PDF tables may be extracted in imperfect reading order. Images, block diagrams, schematics, and scanned pages are not interpreted or OCR-processed.
- Use `--source-type reference-manual` or `--source-type datasheet` when source authority matters.
- Physical PDF pages and embedded page labels are retained, but a result still requires visual confirmation when extraction and page layout disagree.
- S32K3 family-level statements do not prove that a feature applies to the exact S32K358 derivative. Applicability must be checked against the datasheet and project derivative evidence.
- Current XDM values represent saved project state, not vendor defaults or validated application intent.
- Project intent is reconciled as S32K358 MAPBGA289 on the Q289 revision C reference platform, and
	Resource records `s32k358_mapbga289`. The physical PCB revision, U80 marking, fitted components,
	and jumper population still require inspection before hardware-dependent release decisions.
- The Q289 board manual does not identify the MCU FXOSC component or frequency. Its explicit 50 MHz
	oscillator is Ethernet TXCLK; the saved 16 MHz MCU value remains unconfirmed until checked against
	the schematic/BOM, component marking, or measurement.
- The workflow is advisory-only. It does not edit XDM, automate the Tresos GUI, generate code, certify functional safety, or perform hardware-in-the-loop validation.
- Corpus extraction currently processes every PDF in one run and stores page text in generated JSONL before immutable staging.
- Structured extraction relies on embedded PDF outlines and text. It does not OCR figures or reconstruct complex visual table geometry.
- Configuration attributes are limited to reliably labeled text properties; ambiguous wrapped rows remain omitted rather than inferred.
- Reconciliation currently creates exact document and exclusive-area usage relationships. Fuzzy cross-document candidates are reserved for a later milestone.
- Coordinated store activation uses compensating rollback because Neo4j and Elasticsearch cannot share one database transaction. An explicit operator rollback command remains unimplemented.

### Improvement Backlog

- Add query aliases and domain expansion for register abbreviations, peripheral names, and Tresos parameter terminology while preserving exact-match search.
- Add structured extraction for register tables, reset values, bit fields, electrical limits, and package/device applicability.
- Add optional OCR and diagram/table handling for pages without reliable embedded text.
- Add document revision and exact-device metadata, then detect conflicts between family-level manuals, S32K358 limits, and RTD releases.
- Expand the target-platform profile with power rails, jumpers, termination population, protection
	components, and schematic-derived MCU FXOSC evidence.
- Add result-quality checks that compare extracted citations with rendered page content for critical recommendations.
- Add authority-aware ranking and a larger fixed query-quality regression suite.
- Add text-TOC fallback for RTD manuals without usable PDF outlines and richer parsing of wrapped enum, range, and constraint tables.
- Add structured ISR, dependency, callback, memory-section, and integration-step records beyond identifiers attached to IM topics.
- Add an explicit operator rollback command and retention policy for inactive Neo4j datasets and Elasticsearch indices.

### Status Update Policy

Update this section with the current date whenever work changes project capabilities, supported modules/documents, workflow behavior, setup requirements, known limitations, improvement priorities, validation results, or milestone status. Read-only investigations and changes with no contextual or functional project impact do not require a status update.

### Milestone History

- **2026-09-27:** Began versioning Tresos-generated C sources and headers under `output/src` and
	`output/include` while retaining generated EPC metadata as ignored local output.
- **2026-09-27:** Declared the `SW32K3_S32M27x_RTD_R23-11_7.0.1` release and Q289 revision C
	reference platform; corrected Resource to S32K358 MAPBGA289; added a cited hardware-platform
	subgraph for MCU, CAN0, LIN1, connectors, routes, and Ethernet TXCLK; activated it in both stores
	and verified board-manual retrieval; retained physical-board and MCU-oscillator confirmation gates.
- **2026-09-27:** Initialized Git on `main`; added repository rules that retain Tresos project
	inputs while excluding licensed manuals, generated output, caches, local stores, credentials,
	archives, and machine-specific IDE state; documented clone and regeneration workflow.
- **2026-09-27:** Made derivative/package/board/component reconciliation a mandatory cross-module
	advisory gate for clocks, transceivers, NVM, pins, PHYs, and other hardware-dependent settings;
	removed the obsolete ADC-only extraction task.
- **2026-09-27:** Retired SQLite retrieval after four parity queries matched or improved source/page ranking; activated a 79-PDF corpus with 11,996 source-page chunks and switched the advisory skill to the dataset-consistent Elasticsearch/Neo4j adapter.
- **2026-09-27:** Added the independent `mcal-hardware-pdf-extractor` skill; hardware PDFs and profiles now produce validated database-neutral JSON, while only `mcal-graph-loader` creates and loads graph records.
- **2026-09-27:** Streamlined the Just interface to seven public workflows; graph activation now validates and starts both stores, and one `status` command reports the active dataset and service state.
- **2026-09-27:** Renamed the advisory skill from `s32k358-mcal-reference` to `mcal-reference-s32k358` and updated its invocation, runtime paths, tasks, tests, instructions, and architecture references.
- **2026-09-27:** Removed orphaned development caches and pre-chunk datasets, consolidated graph/search design records into one current architecture document, retired the detached FXOSC fixture after preserving its unresolved finding, and made routine cleanup preserve active pipeline state.
- **2026-09-27:** Activated the first dual-store dataset with 10,317 Neo4j entities, 14,818 structural relationships, 6,305 provenance-bearing assertions, and 4,553 Elasticsearch chunks; added the evidence-checked MCU/FXOSC slice, idempotent loaders, cross-store verification, compensated activation, and operator commands.
- **2026-09-27:** Added the independent `mcal-graph-loader` skill foundation, strict graph contracts, deterministic IDs, collision-safe RTD normalization, read-only XDM overlays, and atomic immutable dataset staging for all 36 RTD modules and 11 configured XDM files.
- **2026-09-27:** Added a detailed PDF-to-JSON-to-Neo4j pipeline guide covering implemented extraction, required graph contracts, loader design, validation, activation, rollback, and cross-skill sequencing.
- **2026-09-27:** Replaced the preliminary search handoff with a JSON-first Docker Neo4j/Elasticsearch integration plan covering current parsers, schema corrections, immutable datasets, coordinated activation, required additions, and gated SQLite removal.
- **2026-09-27:** Split structured PDF extraction into the standalone `mcal-pdf-json-extractor` skill, with independent TOC-aware UM/IM parsers, Draft 2020-12 JSON Schemas, ADC/FlexCAN profiles, source-preserving reconciliation, atomic incremental corpus orchestration, and coverage of all 36 RTD manual pairs.
- **2026-09-27:** Added a detached MCU FXOSC knowledge-graph fixture demonstrating canonical XDM path identity, evidence-backed relation states, and unresolved configuration findings; no search integration or ingestion was enabled.
- **2026-09-27:** Added an isolated Docker Compose foundation and data contract for future Neo4j relationship traversal and Elasticsearch full-text retrieval; no parser, ingestion, or SQLite cutover was performed.
- **2026-09-27:** Documented the Windows PATH refresh required when Just is installed while VS Code is already running.
- **2026-09-27:** Added Windows-compatible `just configure` and `just clean` commands for reproducible Poetry setup and complete removal of the Python environment and generated caches.
- **2026-09-27:** Consolidated project-generated caches under `.cache/` while keeping `.venv` limited to the Poetry-managed Python environment.
- **2026-09-27:** Implemented the first advisory skill, Poetry tooling, page-level PDF index, read-only XDM inspector, source-routing policy, tests, VS Code tasks, and Eclipse exclusions. Indexed the expanded 79-document corpus and documented current limitations and planned improvements.