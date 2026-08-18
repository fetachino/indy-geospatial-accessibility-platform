# PostGIS database

The local database uses `postgis/postgis:16-3.5` and a named `postgis-data`
volume. The schema stores source identifiers and load-run lineage on every
feature. EPSG:26916 (NAD83 / UTM zone 16N) is the analysis CRS: it is a
meter-based projected CRS whose zone covers Marion County. Source CRS values
are retained in each table for auditability.

```powershell
Copy-Item .env.example .env       # set a local POSTGRES_PASSWORD
docker compose -f database/docker-compose.yml up -d
python -m indy_accessibility_etl migrate
python -m indy_accessibility_etl load-fixture
docker compose -f database/docker-compose.yml down
```

To reset the local database (irreversible for the named volume), use
`docker compose -f database/docker-compose.yml down -v` after confirming that
no local work needs the volume. If the Docker engine is unavailable, fixture
transform tests and migration SQL validation still run; set
`POSTGIS_TEST_DATABASE_URL` when a PostgreSQL/PostGIS instance is available to
run integration tests. Production raw files are never committed.
