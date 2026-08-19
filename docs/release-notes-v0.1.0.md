# v0.1.0 release notes (draft)

> Preparation only: do not publish a Git tag or GitHub Release until the
> portfolio-release pull request is approved and merged.

## Highlights

- Reproducible Marion County public-data acquisition and PostGIS ETL.
- Transparent proximity-based accessibility analysis for 5,290 block groups.
- FastAPI GeoJSON API and responsive MapLibre explorer with clicked feature
  details.
- Optional ArcGIS Pro/Online documentation and a graceful ArcPy helper.

## Verification

Backend tests, frontend tests, linting, formatting, mypy, production build,
Docker/PostGIS migration and ETL commands were verified where documented. The
latest CI run is the authoritative quality gate. Production npm dependencies
reported zero vulnerabilities with `npm audit --omit=dev --audit-level=high`.
`pip-audit` was not installed in the verification environment, so a Python
dependency audit remains an explicit limitation. No ArcGIS licensed execution,
online publication, benchmark, or production deployment is claimed.

## Known limitations and next steps

Centroid-based proximity is not network access or travel time. School geocoding,
ACS normalization, network analysis, deployment, and optional Esri account
workflows remain future work.
