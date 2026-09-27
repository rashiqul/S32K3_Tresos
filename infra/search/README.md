# Graph and Full-Text Search

This local-only stack runs the active Neo4j and Elasticsearch datasets used by the AUTOSAR MCAL
advisory workflow.

## Start the Services

Docker Desktop with its WSL 2 backend is supported. From the workspace root:

```powershell
Copy-Item infra/search/.env.example infra/search/.env
# Set a unique NEO4J_PASSWORD in infra/search/.env.
just graph-activate
just status
```

Neo4j Browser is available at <http://localhost:7474> and Bolt at
`bolt://localhost:7687`. Elasticsearch is available at <http://localhost:9200>. All published
ports bind only to localhost. `just search-down` stops the services and preserves their named
volumes.

The stack is intended for local development, not production. Elasticsearch authentication and
TLS are disabled, and the example resource limits assume at least 3 GB of Docker memory is
available.

## Storage Responsibilities

- **Neo4j** owns canonical concepts and relationships: AUTOSAR terms, XDM parameters and
  containers, MCAL modules, peripherals, registers, fields, devices, documents, and citations.
- **Elasticsearch** owns searchable text chunks, aliases, abbreviations, and denormalized filter
  fields used to retrieve candidates quickly.
- Stable application-generated IDs join Elasticsearch documents to Neo4j nodes. Database-native
  IDs must not cross the boundary.
- Every extracted assertion must retain provenance: source document, revision or hash, physical
  page, embedded page label when available, and the extractor version.

## Graph Contract

The ingestion implementation uses these primary labels:

| Label | Stable key | Purpose |
| --- | --- | --- |
| `Term` | `term_id` | Canonical AUTOSAR, RTD, and hardware terminology |
| `McalModule` | `module_id` | Configured modules such as `Mcu`, `Port`, and `Can_43_FLEXCAN` |
| `XdmInstance` | `xdm_id` | Read-only parameter or container paths from XDM files |
| `Peripheral` | `peripheral_id` | Hardware blocks such as FlexCAN, SIUL2, and LPUART |
| `Register` | `register_id` | Reference-manual registers and optional fields |
| `Device` | `device_id` | Family or derivative applicability |
| `Document` | `document_id` | RM, datasheet, UM, IM, board manual, or application note |
| `Citation` | `citation_id` | A source location with page and extraction provenance |

Evidence-bearing claims such as `CONFIGURES`, `MAPS_TO`, `DOCUMENTED_BY`, and `APPLIES_TO` are
reified as assertion nodes with `SUBJECT`, `OBJECT`, and `SUPPORTED_BY` links. Deterministic
topology such as `BELONGS_TO` and `HAS_CITATION` remains a direct relationship.

Use canonical container paths as XDM identities. Short names are display properties only: the
same parameter name can occur under multiple containers with different semantics. Add
`RegisterField`, `Constraint`, and `GeneratedSymbol` labels when field-level mappings, numeric
limits, or generated macros need their own evidence and lifecycle.

Every assertion carries an `assertion_status` of `verified`, `inferred`, `unresolved`, or
`rejected`. A verified assertion requires a citation that supports the relationship itself, not
merely both endpoint names. Inferred assertions record a rationale and remain out of authoritative
query expansion until reviewed.

## MCU/FXOSC Evidence Slice

The production profile is
`.github/skills/mcal-hardware-pdf-extractor/profiles/mcu-fxosc.json`. The independent hardware
extractor verifies local RTD, reference-manual, and datasheet anchors and emits neutral JSON. The
graph loader turns that artifact into the FXOSC peripheral, `CTRL` register, `OSCON` field,
crystal-mode constraint, and their evidence-bearing assertions.

The saved global FXOSC-control value is true while `McuClockSettingConfig` is empty. The documented
any-per-setting derivation cannot be demonstrated from saved XDM alone, so this remains unresolved
pending Tresos validation and effective/generated configuration inspection.

The separate `mcal-graph-loader` skill normalizes completed RTD extractor output, read-only XDM
state, and the evidence-checked MCU/FXOSC hardware slice under
`.cache/mcal-graph-loader/datasets/`. `just graph-activate` idempotently loads the latest complete
dataset into both stores, verifies counts and citation support, swaps the Elasticsearch alias,
marks the Neo4j dataset active, and writes `.cache/mcal-graph-loader/active-dataset.json` last.

Use `manage_stores.py load` or `manage_stores.py verify` directly when those advanced phases need
to be inspected separately. Re-running a load is safe. Do not use `docker compose down -v`; named
volumes preserve loaded datasets between normal restarts.

## Elasticsearch Contract

The active alias is `mcal-reference-chunks`. Each chunk contains citation, source-chunk continuity,
document path, source type, module/peripheral/term/device IDs, physical and printed pages, heading,
text, document hash, and chunker version. Keep exact identifiers as `keyword` fields and prose as `text`
with an English analyzer plus an exact-match subfield.

The intended query flow is:

1. Normalize exact XDM/register names and known aliases.
2. Retrieve candidate chunks and filters from Elasticsearch.
3. Expand and constrain those candidates through Neo4j relationships.
4. Rank results while preserving source authority and device applicability.
5. Return citations from stored provenance, never from generated relationships alone.

## Query Boundary

The advisory adapter verifies that the Elasticsearch alias, local active pointer, and active Neo4j
dataset agree before returning results. See
[MCAL_GRAPH_SEARCH_ARCHITECTURE.md](../../docs/architecture/MCAL_GRAPH_SEARCH_ARCHITECTURE.md) for the complete
contracts, cutover evidence, and remaining limitations.