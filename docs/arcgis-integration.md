# Optional ArcGIS / Esri integration

This guide adds an Esri-friendly path without changing the free local stack.
The completed, locally runnable system remains PostgreSQL/PostGIS, FastAPI,
React, and MapLibre. The project has not claimed ArcGIS Pro execution,
ArcGIS Online publication, or licensed Esri access.

## What is ready for Esri users

Milestone 3/4 provide PostGIS analysis results, GeoJSON/CSV exports, the
documented analysis CRS (EPSG:26916), WGS84 web GeoJSON, a source catalog, run
lineage, score fields, service categories, and status flags. Generate an
export with `python -m indy_accessibility_etl export <run-id>`; outputs are in
ignored `data/processed/`.

| Capability | Requirement | Status |
| --- | --- | --- |
| Add GeoJSON/CSV, symbolize, configure pop-ups, export a layout | ArcGIS Pro | Runbook provided; license-dependent and not executed here |
| Upload a small export, create a web map, configure sharing | ArcGIS Online | Runbook provided; account-dependent and not executed here |
| ArcGIS Maps SDK for JavaScript provider | Developer account/API key may be required | Design only; MapLibre remains default |
| `arcgis/prepare_accessibility.py` | ArcGIS Pro for ArcPy actions | Gracefully checked; ArcPy execution not claimed |

## ArcGIS Pro workflow

1. Generate a small run export and copy it outside ignored working data if you
   intend to keep it. Add the GeoJSON with **Map > Add Data > Data**.
2. Confirm the map is WGS 84 for web GeoJSON, or use **Project** to EPSG:26916
   when comparing with the PostGIS analysis CRS. Do not assign a CRS merely to
   hide a misalignment: assign only when the source CRS is known.
3. Symbolize `total_accessibility_score` with a graduated color ramp and a
   0–100 range. Add `transit_access_score` and `service_access_score` as
   optional popup fields.
4. Configure pop-ups with `geoid`, all three scores, `transit_stop_count`,
   `service_categories`, and `status_flags`. Use readable aliases from the
   field table below.
5. Add a text note that scores are centroid-based proximity indicators, not
   walking access or policy recommendations. Export a layout only after
   checking the coordinate system and legend.

For repeatable preparation, ArcGIS Pro users may run:

```text
<ArcGIS Pro Python>> python arcgis/prepare_accessibility.py \
  --input data/processed/analysis-<run-id>.geojson \
  --output-gdb C:/gis/indy.gdb --config arcgis/config.example.json
```

## ArcGIS Online workflow

1. Keep uploads small and purposeful; use a filtered/exported run rather than
   uploading a production-sized dataset. Sign in only in your own browser.
2. Add the GeoJSON as a hosted feature layer, inspect the detected WGS84
   coordinates, and set field aliases/pop-ups using the table below.
3. Create a web map, apply the score color ramp, add a description of the
   methodology and limitations, and save it privately first.
4. Share only with the intended group or organization. Do not enable public
   sharing or publish credentials from this repository.
5. A Dashboard can use a map, a score indicator, a histogram of
   `total_accessibility_score`, and a category/status filter. Experience
   Builder can place the map beside a selected-feature details panel.

These steps require an ArcGIS Online account and may incur account/storage
limits. No publication has been performed for this project.

## ArcGIS-ready fields and CRS

| Field | Alias | Type | Meaning |
| --- | --- | --- | --- |
| `geoid` | Census block-group GEOID | text | Stable geographic identifier |
| `total_accessibility_score` | Total accessibility score | double | 0–100 composite score |
| `transit_access_score` | Transit access score | double | 0–100 proximity component |
| `service_access_score` | Essential service score | double | 0–100 category component |
| `transit_stop_count` | Nearby transit stops | integer | Stops within 400 m of centroid |
| `service_categories` | Available service categories | text[]/text | Categories within 1,600 m |
| `status_flags` | Data status flags | text[]/text | Missing-data/quality notes |

ArcGIS feature services commonly prefer scalar text fields. If the target
format cannot preserve arrays, serialize `service_categories` and
`status_flags` as semicolon-delimited text in a copy; do not alter the
reproducible source export. Analysis geometry is EPSG:26916; API GeoJSON is
EPSG:4326.

## Troubleshooting

- **Shifted features:** check whether the source is EPSG:4326 or EPSG:26916;
  project rather than redefining the coordinate system.
- **Field aliases missing:** configure aliases manually or use the ArcPy
  helper in an ArcGIS Pro Python environment.
- **Large upload rejected:** filter to a small study area/run or use a local
  feature class; hosted-service limits vary by account.
- **ArcGIS Online sharing blocked:** verify ownership, organization policy,
  credits, and intended sharing scope.
- **Credentials unavailable:** keep using MapLibre and local FastAPI. Esri
  credentials are optional and must remain uncommitted.

## Explicit limitations

No ArcGIS Pro, ArcGIS Online, Dashboard, Experience Builder, or ArcGIS Maps
SDK execution is represented as completed evidence. The accessibility result
is a transparent centroid-based proximity screen; it is not a network travel
time, causal finding, or policy recommendation.
