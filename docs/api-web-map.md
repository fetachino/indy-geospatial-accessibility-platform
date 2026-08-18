# API and interactive web map

Milestone 4 exposes the latest local PostGIS analysis run through a read-only
FastAPI API and renders it in a MapLibre client. The API returns GeoJSON in
WGS84 (EPSG:4326); spatial filtering is performed in the database's projected
CRS before transformation for clients.

## Local startup

```bash
docker compose -f database/docker-compose.yml up -d
python -m indy_accessibility_etl migrate
python -m indy_accessibility_etl production-db
python -m indy_accessibility_etl analyze
uvicorn indy_accessibility_api.main:app --reload
cd frontend && npm ci && npm run dev
```

Set `DATABASE_URL`, `CORS_ORIGINS`, and `VITE_API_BASE_URL` as needed. If
`DATABASE_URL` is omitted, the API derives the same connection URL as ETL from
the `POSTGRES_*` variables (including `POSTGRES_PASSWORD`). Optionally
set `VITE_MAP_TILE_URL` to a public raster tile template with attribution. No
API key or paid map provider is required; raw data and credentials remain
outside Git.

## Endpoint surface

- `GET /api/v1/runs/latest` and `/summary` expose run metadata and score distributions.
- `GET /api/v1/block-groups` supports bbox, score range, pagination, and GeoJSON; `/{geoid}` returns one feature.
- `GET /api/v1/transit/stops` supports bbox and pagination.
- `GET /api/v1/services?category=...` supports hospital, grocery_store, school, library, and fire_station.
- `GET /api/v1/metadata` describes supported categories and CRS.

Invalid parameters return 4xx responses; unavailable database state returns a
client-safe 503. Interactive OpenAPI documentation is available at `/docs`.

## Map behavior and limitations

The client provides score-range filters, service-layer toggles, loading/error
and retry states, a score legend, and click selection on the actual block-group
polygons. The selected feature reports its GEOID, total/transit/service scores,
nearby transit count, service categories, and status flags. Polygon colors
represent each feature's Milestone 3 composite score; transit and service points
are separate layers. The analysis is straight-line proximity with known missing
school geocoding and unavailable ACS normalization, not a routing or travel-time
model. The ArcGIS adapter and production hosting are deferred to Milestone 5.
Automated browser screenshot capture is not available in this environment; CI
validates build and interaction contracts instead.
