# ADR 0001: Platform foundation and provider boundaries

- Status: Accepted
- Date: 2026-08-18
- Decision owners: Project maintainer
- Related issue: #1

## Context

The portfolio must demonstrate reproducible open-source GIS engineering while
leaving a credible path for licensed Esri tools. It must support spatial ETL,
PostGIS queries, an API, and an accessible web map without requiring paid cloud
infrastructure or exposing browser credentials.

## Decision

Use a monorepo with independently testable Python and TypeScript applications.
Python owns acquisition, validation, spatial processing, and the FastAPI
service. PostGIS will be the canonical processed-data store. React owns the
user interface and talks to the backend through a versioned API.

The web client will depend on a small map-provider interface rather than
business logic tied directly to one SDK. MapLibre is the planned local default
because it can run without a private API key. An ArcGIS Maps SDK adapter may be
added after authentication, terms, basemap access, and public deployment are
verified. Optional ArcPy code lives under `arcgis/` and cannot be required by
the open-source pipeline.

Spatial analysis will use an appropriate Indiana projected CRS selected and
documented after source inspection. A first proximity baseline may use
straight-line distances or buffers, but it must be named as such. Network
accessibility is a separate method and result.

## Component boundaries

- `backend/`: HTTP API and application-domain code
- `scripts/`: command-line acquisition and processing entry points
- `database/`: versioned PostGIS schema and migrations
- `frontend/`: UI, map-provider adapters, and browser tests
- `arcgis/`: optional proprietary automation and publishing guidance
- `data/`: ignored local artifacts; only documented legal fixtures may be
  tracked under a future dedicated test-fixture path
- `docs/`: decisions, provenance, methodology, risks, and case study

## Consequences

This separation improves local reproducibility and makes proprietary
requirements explicit. It introduces adapter and integration-test overhead.
The exact datasets, projected CRS, schema, score weights, routing engine, and
ArcGIS publishing method remain open decisions that require evidence from later
milestones.

## Milestone 0 boundary

Milestone 0 proves that both application stacks install and pass automated
quality checks. It does not include data acquisition, PostGIS configuration,
spatial calculations, production endpoints, a functional map, ArcPy execution,
or accessibility findings.
