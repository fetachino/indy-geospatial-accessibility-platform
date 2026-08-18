# Indy Geospatial Accessibility Platform

A production-style GIS portfolio project investigating which Marion County,
Indiana neighborhoods have inadequate access to public transit and essential
services such as hospitals, grocery stores, schools, libraries, and fire
stations.

> **Current status:** Milestone 0 establishes the tested project foundation.
> No datasets have been acquired and no accessibility results have been
> calculated. The map and analysis shown in the roadmap are not yet available.

## Project question

> Which Marion County neighborhoods have inadequate access to public transit
> and essential services?

The finished platform will calculate transparent, population-normalized
accessibility indicators and expose them through a documented API and an
interactive web map. It will distinguish straight-line proximity from true
network accessibility and document uncertainty and limitations.

## Planned architecture

- **Data and spatial processing:** Python, GeoPandas, Shapely, PyProj, and
  Rasterio where raster analysis is genuinely useful
- **Spatial storage:** PostgreSQL with PostGIS, run locally with Docker Compose
- **API:** FastAPI with a versioned HTTP interface
- **Web client:** React, TypeScript, and a provider-neutral mapping boundary
- **Web map:** MapLibre for the credential-free local baseline, with an ArcGIS
  Maps SDK adapter evaluated in Milestone 5
- **Esri automation:** Optional ArcPy and ArcGIS Pro workflows kept separate
  from the open-source core
- **Quality:** Pytest, Ruff, mypy, Vitest, Testing Library, ESLint, Prettier,
  and GitHub Actions

The rationale and component boundaries are recorded in
[`docs/architecture/0001-platform-foundation.md`](docs/architecture/0001-platform-foundation.md).

## Repository layout

```text
backend/                 FastAPI application and Python tests
frontend/                React and TypeScript web client
database/                PostGIS migrations and database documentation
data/{raw,interim,processed}/  Local data products (contents ignored)
docs/                    ADRs, methodology, risk register, and future case study
scripts/                 Reproducible project and data commands
arcgis/                  Optional ArcGIS Pro and ArcPy workflows
.github/workflows/       Continuous integration
```

## Quick start

Prerequisites are Python 3.11+, Node.js 22+, and npm 10+.

### Backend

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
uvicorn indy_accessibility_api.main:app --reload
```

The health check is available at `http://127.0.0.1:8000/health` and interactive
API documentation at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm ci
npm run test
npm run dev
```

Copy `.env.example` to `.env` only when local overrides are needed. Never
commit secrets. The current frontend is a foundation page, not the completed
interactive GIS application.

## Verification

```bash
ruff check .
ruff format --check .
mypy backend/src
pytest

cd frontend
npm run lint
npm run format:check
npm run test
npm run build
```

## Data policy

Authoritative public sources are preferred. Each dataset added in Milestone 1
must have a catalog entry recording its provider, direct URL, retrieval date,
license or terms, coverage, important fields, CRS, and limitations. Downloaded
and generated data are ignored by Git; reproducible acquisition scripts and
small legally redistributable test fixtures are committed instead. OpenStreetMap
will be used only when an authoritative source is unavailable or when its road
network is methodologically appropriate and attribution requirements are met.

## Roadmap and acceptance criteria

| Milestone | Acceptance boundary |
| --- | --- |
| **0 — Foundation (current)** | Architecture and risks documented; repository guidance and safe environment template present; installable FastAPI and React foundations; lint, type, test, and build checks pass in CI. No analytical claims. |
| **1 — Data acquisition** | Authoritative sources verified and cataloged; reproducible downloads, provenance controls, schemas, quality tests, manual fallbacks, and a legal test fixture added. |
| **2 — Spatial database and ETL** | PostGIS Compose service, spatial schema/indexes, projected-CRS transformations, geometry repair, reproducible loads, lineage, and integration tests complete. |
| **3 — Accessibility analysis** | Transparent proximity baseline, population normalization, composite score, spatial edge-case tests, documented exports, and—if feasible—a separately described network comparison complete. |
| **4 — API and web map** | Versioned API and responsive interactive map expose real results with filters, legends, accessible controls, loading/error states, and backend/frontend tests. |
| **5 — Esri integration** | Optional ArcGIS Pro/ArcPy workflow and safe publishing path documented; ArcGIS web adapter implemented only if licensing and credential handling are reproducible. |
| **6 — Portfolio release** | Verified clean-environment commands, screenshots, architecture diagram, technical case study, findings and limitations, user guide, release notes, measured benchmarks if any, and evidence-based résumé bullets complete. |

## Known limitations

- Data availability, licensing, schemas, and update frequency still require
  source-by-source verification.
- Docker is installed in the initial development environment, but the Docker
  engine was not responsive during the first inspection; PostGIS support will
  be validated in Milestone 2.
- No local `psql` client was detected during the first inspection.
- No ArcGIS credentials or licenses are assumed. The open-source core must work
  without them.
- A circular proximity buffer is not a walking route. Any baseline using one
  will be labeled accordingly and kept distinct from network analysis.

See [`docs/risk-register.md`](docs/risk-register.md) for mitigations and
validation milestones.

## Contributing and license

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow. This
project is licensed under the [MIT License](LICENSE).
