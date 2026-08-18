CREATE EXTENSION IF NOT EXISTS postgis;

CREATE SCHEMA IF NOT EXISTS boundaries;
CREATE SCHEMA IF NOT EXISTS demographics;
CREATE SCHEMA IF NOT EXISTS transit;
CREATE SCHEMA IF NOT EXISTS services;
CREATE SCHEMA IF NOT EXISTS etl;

CREATE TABLE IF NOT EXISTS etl.schema_migrations (
    version text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS etl.load_runs (
    load_run_id uuid PRIMARY KEY,
    source_dataset_id text NOT NULL,
    source_url text,
    retrieved_at timestamptz,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    row_count integer NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    rejected_count integer NOT NULL DEFAULT 0 CHECK (rejected_count >= 0),
    source_sha256 text,
    transformation_version text NOT NULL,
    error_message text
);

CREATE TABLE IF NOT EXISTS etl.feature_audit (
    audit_id bigserial PRIMARY KEY,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id),
    dataset_id text NOT NULL,
    source_id text NOT NULL,
    action text NOT NULL CHECK (action IN ('loaded', 'repaired', 'quarantined', 'duplicate')),
    reason text,
    original_crs text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS boundaries.marion_county (
    source_id text PRIMARY KEY,
    name text NOT NULL,
    source_crs text,
    source_retrieved_date date,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id),
    geometry geometry(MultiPolygon, 26916) NOT NULL,
    CHECK (ST_SRID(geometry) = 26916),
    CHECK (NOT ST_IsEmpty(geometry))
);

CREATE TABLE IF NOT EXISTS demographics.census_block_groups (
    geoid text PRIMARY KEY,
    name text,
    state_fips text,
    county_fips text,
    tract text,
    block_group text,
    population integer CHECK (population IS NULL OR population >= 0),
    population_moe integer CHECK (population_moe IS NULL OR population_moe >= 0),
    households_no_vehicle integer CHECK (households_no_vehicle IS NULL OR households_no_vehicle >= 0),
    source_crs text,
    source_retrieved_date date,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id),
    geometry geometry(MultiPolygon, 26916) NOT NULL,
    CHECK (ST_SRID(geometry) = 26916),
    CHECK (NOT ST_IsEmpty(geometry))
);

CREATE TABLE IF NOT EXISTS transit.stops (
    source_id text PRIMARY KEY,
    name text NOT NULL,
    code text,
    wheelchair_boarding smallint,
    source_crs text,
    source_retrieved_date date,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id),
    geometry geometry(Point, 26916) NOT NULL,
    CHECK (ST_SRID(geometry) = 26916), CHECK (NOT ST_IsEmpty(geometry))
);

CREATE TABLE IF NOT EXISTS transit.routes (
    source_id text PRIMARY KEY,
    short_name text,
    long_name text NOT NULL,
    route_type integer,
    source_crs text,
    source_retrieved_date date,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id)
);

CREATE TABLE IF NOT EXISTS services.service_locations (
    source_id text NOT NULL,
    service_type text NOT NULL CHECK (service_type IN ('hospital', 'grocery_store', 'school', 'library', 'fire_station')),
    name text NOT NULL,
    address text,
    source_crs text,
    source_retrieved_date date,
    load_run_id uuid REFERENCES etl.load_runs(load_run_id),
    geometry geometry(Point, 26916) NOT NULL,
    PRIMARY KEY (service_type, source_id),
    CHECK (ST_SRID(geometry) = 26916), CHECK (NOT ST_IsEmpty(geometry))
);

CREATE INDEX IF NOT EXISTS marion_county_geometry_gix ON boundaries.marion_county USING gist (geometry);
CREATE INDEX IF NOT EXISTS block_groups_geometry_gix ON demographics.census_block_groups USING gist (geometry);
CREATE INDEX IF NOT EXISTS transit_stops_geometry_gix ON transit.stops USING gist (geometry);
CREATE INDEX IF NOT EXISTS service_locations_geometry_gix ON services.service_locations USING gist (geometry);
CREATE INDEX IF NOT EXISTS service_locations_type_idx ON services.service_locations (service_type);

CREATE OR REPLACE VIEW services.hospitals AS
SELECT source_id, name, address, source_crs, source_retrieved_date, load_run_id, geometry
FROM services.service_locations WHERE service_type = 'hospital';
CREATE OR REPLACE VIEW services.grocery_stores AS
SELECT source_id, name, address, source_crs, source_retrieved_date, load_run_id, geometry
FROM services.service_locations WHERE service_type = 'grocery_store';
CREATE OR REPLACE VIEW services.schools AS
SELECT source_id, name, address, source_crs, source_retrieved_date, load_run_id, geometry
FROM services.service_locations WHERE service_type = 'school';
CREATE OR REPLACE VIEW services.libraries AS
SELECT source_id, name, address, source_crs, source_retrieved_date, load_run_id, geometry
FROM services.service_locations WHERE service_type = 'library';
CREATE OR REPLACE VIEW services.fire_stations AS
SELECT source_id, name, address, source_crs, source_retrieved_date, load_run_id, geometry
FROM services.service_locations WHERE service_type = 'fire_station';
