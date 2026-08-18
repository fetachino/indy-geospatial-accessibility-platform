# Milestone 3 accessibility methodology

## Question and unit

The project asks: **Which Marion County neighborhoods have inadequate access to
public transit and essential services?** This baseline reports Census block
groups, not resident-defined neighborhoods. Each block group is represented by
its centroid for proximity calculations, while its original EPSG:26916
MultiPolygon is retained in the result.

## Sources and thresholds

The analysis uses the Milestone 2 PostGIS load: IndyGo stops, IndianaMap
hospitals, USDA SNAP retailers, Indiana library locations, and IFD fire
stations. The IDOE school workbook is excluded because it contains addresses,
not geocoded points. ACS population is used only when valid data has been
loaded; otherwise population and per-1,000 fields are null and flagged.

All distances use EPSG:26916 (NAD83 / UTM zone 16N), in meters. The configured
thresholds are 400 m for transit stops and 1,600 m for each service category.
Adjust them in `backend/src/indy_accessibility_analysis/config.json`.

## Formula

The default configuration uses transit weight 0.4, service weight 0.6, and a
transit saturation target of three stops:

```text
transit_access = min(transit_stops_within_400m / 3, 1) * 100
service_access = (categories represented within 1600m / known categories) * 100
total_score = 0.4 * transit_access + 0.6 * service_access
```

Unavailable source categories are excluded from the service denominator and
add a `category_unavailable` flag; they are not silently treated as zero.
Scores are clamped to 0–100 and are deterministic planning-screening
indicators. They are not causal measures, policy recommendations, walking
routes, travel times, or proof of network accessibility. Multiple facilities in
one category do not substitute for diversity across categories.

## Lineage, interpretation, and limitations

Each run stores a calculation version, configuration version/hash, source
lineage, timestamp, and quality flags in `analysis.runs` and
`analysis.block_group_results`. Results indicate proximity from a block-group
centroid to loaded points; they do not model entrances, barriers, sidewalks,
service hours, capacity, transfers, or actual travel behavior. SNAP retailers
are not a complete grocery inventory, the hospital and fire layers have stated
coverage limitations, and libraries require category filtering. ACS margins of
error and population availability must be carried into later interpretation.

A future network analysis would require a reproducible pedestrian/road network,
routing engine, impedance assumptions, time-of-day service schedules, and tests
for disconnected or inaccessible paths. That work is explicitly deferred.

## Commands and exports

```powershell
python -m indy_accessibility_etl analyze
python -m indy_accessibility_etl export <run-id>
```

Commands write ignored CSV, GeoJSON, and JSON summary artifacts under
`data/processed/`.
