set shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

# Install Poetry and the locked project dependencies.
configure:
    python -m pip install "poetry>=2.0"
    python -m poetry install --no-root

# Remove the Python environment and disposable tool caches while preserving pipeline data.
clean:
    $targets = @('.venv', '.cache/pytest', '.cache/ruff', '.pytest_cache', '.ruff_cache', '.mypy_cache') | Where-Object { Test-Path $_ }; if ($targets) { Remove-Item -Path $targets -Recurse -Force }
    Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Extract structured RTD records and the complete searchable PDF corpus.
extract-all:
    .\.venv\Scripts\python.exe .github/skills/mcal-pdf-json-extractor/scripts/rtd_extract.py --all --json
    .\.venv\Scripts\python.exe .github/skills/mcal-pdf-json-extractor/scripts/pdf_corpus.py --json
    .\.venv\Scripts\python.exe .github/skills/mcal-hardware-pdf-extractor/scripts/hardware_extract.py --json

# Build and validate an immutable graph dataset from completed RTD JSON and read-only XDM state.
graph-stage:
    .\.venv\Scripts\python.exe .github/skills/mcal-graph-loader/scripts/build_dataset.py --json

# Load, verify, and activate the latest dataset, starting both stores when needed.
graph-activate: _search-up
    .\.venv\Scripts\python.exe .github/skills/mcal-graph-loader/scripts/manage_stores.py all

# Show the active dataset and local service state.
status:
    .\.venv\Scripts\python.exe .github/skills/mcal-graph-loader/scripts/manage_stores.py status
    docker compose --env-file infra/search/.env -f infra/search/compose.yaml ps

# Internal: validate the local Neo4j and Elasticsearch stack.
_search-config:
    if (-not (Test-Path 'infra/search/.env')) { throw 'Copy infra/search/.env.example to infra/search/.env and set NEO4J_PASSWORD first.' }
    docker compose --env-file infra/search/.env -f infra/search/compose.yaml config --quiet

# Internal: start the local graph and full-text search services.
_search-up: _search-config
    docker compose --env-file infra/search/.env -f infra/search/compose.yaml up -d --wait

# Stop the local services while preserving indexed data volumes.
search-down:
    if (-not (Test-Path 'infra/search/.env')) { throw 'Copy infra/search/.env.example to infra/search/.env and set NEO4J_PASSWORD first.' }
    docker compose --env-file infra/search/.env -f infra/search/compose.yaml down
