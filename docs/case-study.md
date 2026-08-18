# Technical case study: Marion County accessibility screening

## Problem and users

The project asks which Marion County neighborhoods may have inadequate access
to public transit and essential services. A GIS developer, planner, or
community analyst can use the application to inspect a transparent screening
indicator, compare block groups, and trace results back to public sources.

## Data flow

Public City/County, IndyGo, Indiana, USDA, IDOE, and Census sources are
cataloged and cached by Python acquisition commands. The ETL validates formats,
projects data to EPSG:26916, quarantines invalid/out-of-county records, and
loads PostGIS transactionally with lineage. The analysis runner computes a
versioned result for each Census block group. FastAPI exposes the latest run and
WGS84 GeoJSON; React/MapLibre renders scores, stops, services, filters, and
clicked feature details. GeoJSON/CSV exports provide a bridge to optional Esri
workflows.

## Methods and decisions

- EPSG:26916 (NAD83 / UTM zone 16N) supports meter-based distance comparisons
  around Indianapolis; API responses are transformed to EPSG:4326 for web
  clients.
- The score is `0.4 * transit_score + 0.6 * service_score`. Transit score is
  100 when at least one stop is within 400 m of the block-group centroid.
  Service score is the proportion of available essential-service categories
  within 1,600 m, scaled to 100. Missing categories and ACS population are
  represented with status flags rather than silently imputed.
- Server-side bbox/score filtering, typed response models, and safe 503 errors
  keep the API predictable. MapLibre is the default because it needs no paid
  account; the ArcGIS path is explicitly optional.

## Testing and the hardest bug

Backend tests cover catalog integrity, ETL validation, API parameters and
responses, analysis edge cases, and optional ArcGIS helpers. Frontend tests
cover the rendered shell and feature-selection helpers; CI runs lint,
formatting, coverage, type checks, and builds. During Milestone 4, every API
query returned 503 despite successful ETL. The cause was a generator returned
through `next(connection())`: its finalization closed psycopg before the query.
Replacing it with an explicit context manager and adding fallback configuration
and logging tests fixed the real local failure.

## Limitations and responsible next steps

The result is a centroid-based straight-line proximity indicator, not walking
access, travel time, network accessibility, a causal finding, or a policy
recommendation. School records remain ungeocoded and ACS normalization is
unavailable in the verified environment. Next steps are true network analysis,
school geocoding, ACS normalization, temporal freshness checks, optional
ArcGIS Online publication with an account, and deployment hardening. None of
those are represented as complete here.
