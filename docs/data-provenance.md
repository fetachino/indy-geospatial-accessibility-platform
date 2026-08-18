# Milestone 1 data provenance and source decisions

Verified on 2026-08-18. The machine-readable source of truth is
[`data/catalog/datasets.json`](../data/catalog/datasets.json). This document
explains how each source supports the later analysis and where source terms or
coverage require caution.

## Selection principles

Sources were evaluated in this order: Indianapolis/Marion County, IndyGo,
Indiana agencies or IndianaMap, the U.S. Census Bureau or another responsible
federal agency, and then OpenStreetMap only if no authoritative source was
usable. No OpenStreetMap dataset is needed for Milestone 1. Public reachability
does not imply permission to redistribute, so production responses remain in
the ignored local cache and ambiguous terms are recorded rather than guessed.

## Geographic framework

The City of Indianapolis and Marion County ArcGIS service supplies the official
county boundary. Its query endpoint returned GeoJSON publicly and its schema
advertises `DISPLAY` and area attributes. The service does not state a clear
open-data license, so it is suitable for reproducible local retrieval but its
terms must be clarified before publishing a copied boundary layer.

The 2024 Census TIGER/Line Indiana block-group file supplies stable GEOIDs and
small-area geometry aligned with the selected 2024 ACS release. Block groups
are not resident-defined neighborhoods. Milestone 2 or 3 must choose and defend
the reporting geography and transform geometries to an appropriate projected
CRS before measuring area or distance.

## Transit

IndyGo is the authoritative transit operator. Its official developer page says
that static GTFS schedule data are available and links to a request form and
terms. The operational IndyGo realtime host returned a valid GTFS ZIP on
2026-08-18 containing agency, stops, routes, trips, stop times, shapes, and
calendar-date files. Because the request form and terms remain the official
access path, the catalog records both the verified endpoint and the exact form
fallback. The feed is a schedule snapshot, not evidence that a trip operated.

## Essential services

### Hospitals

IndianaMap's Hospital Locations 2023 feature service is a public statewide
aggregator republished by the Indiana Geographic Information Office from
HIFLD-derived sources. It exposes source, source-date, validation, status, type,
and coordinate fields and can be filtered to Marion County. The item explicitly
states that missing source facilities are absent and that nursing homes and
health centers are excluded. The 2023 title also makes currentness a material
limitation; later ETL must preserve provenance fields and assess closures.

### Grocery stores

No verified Indianapolis or Indiana agency grocery-location dataset with a
clear public machine-readable source was found. The selected fallback is USDA
Food and Nutrition Service's historical SNAP Retailer Locator file, current
through 2025-12-31. It is authoritative for SNAP authorization, not for every
grocery store. Later ETL must select active records and defensible grocery store
types; convenience stores cannot automatically represent full-service grocery
access. This limitation is preferable to silently substituting unverified or
crowdsourced locations.

### Schools

The Indiana Department of Education 2025–2026 School Directory is the official
state workbook and was updated on 2026-04-01 according to the IDOE Data Center.
It contains separate public-school (`SCHL`) and accredited non-public-school
(`NPSCHL`) sheets with school IDs, names, grade spans, counties, and addresses.
It has no coordinates. Geocoding is deliberately deferred and must retain the
original address and school identifier.

### Libraries

The Indianapolis Public Library locations page is the preferred local
cross-check and publicly renders current branch names and addresses. Its raw
downloaded HTML did not contain those rendered address records during
verification, so it was not selected as the reproducible production source.
Instead, the catalog uses Indiana State Library's Library Locations of Indiana
2025 point inventory published by IndianaMap. It has branch, address, library
type, update, and geometry fields. The statewide layer includes non-public
library types and predates the analysis, so later ETL must spatially select
Marion County, define eligible public-service locations, and cross-check them
against the current official IndyPL page.

### Fire stations

The City/County IFD feature service provides official IFD station points and
station, address, and battalion fields. A separate service layer contains
non-IFD stations, so the IFD layer alone may not represent all fire-service
access across Marion County. Milestone 2 must evaluate and document whether the
non-IFD layer is required. The service metadata does not provide an explicit
license or update date.

## Population and demographics

The 2020–2024 ACS 5-year detailed-table API is selected for block-group total
population (`B01003`) and household vehicle availability (`B08201`), including
the total-population margin of error. These variables can support population
normalization and later sensitivity analysis, but they do not describe every
person's travel behavior.

On 2026-08-18 the Census API returned an HTML `Missing Key` response for the
pinned query without a key. The CLI therefore requires `CENSUS_API_KEY` for this
dataset and fails before making a misleading cache entry. The documented
fallback is an equivalent manual download from data.census.gov. A key must be
provided only through the environment and is never written to logs, manifests,
or Git.

## What this milestone does not do

Milestone 1 downloads and validates immutable raw responses. It does not filter
facilities into analytical definitions, geocode address-only sources, repair
geometry, select a projected CRS, load PostGIS, calculate accessibility scores,
or publish source data. Those decisions require the later ETL and analysis
milestones.
