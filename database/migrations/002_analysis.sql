CREATE SCHEMA IF NOT EXISTS analysis;

CREATE TABLE IF NOT EXISTS analysis.runs (
    run_id uuid PRIMARY KEY,
    calculation_version text NOT NULL,
    configuration_version text NOT NULL,
    configuration_hash text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    population_available boolean NOT NULL DEFAULT false,
    source_lineage jsonb NOT NULL DEFAULT '{}'::jsonb,
    row_count integer NOT NULL DEFAULT 0 CHECK (row_count >= 0),
    error_message text
);

CREATE TABLE IF NOT EXISTS analysis.block_group_results (
    run_id uuid NOT NULL REFERENCES analysis.runs(run_id) ON DELETE CASCADE,
    geoid text NOT NULL,
    geometry geometry(MultiPolygon, 26916) NOT NULL,
    transit_stop_count integer NOT NULL CHECK (transit_stop_count >= 0),
    transit_within_threshold boolean NOT NULL,
    hospitals_available boolean,
    grocery_stores_available boolean,
    libraries_available boolean,
    fire_stations_available boolean,
    schools_available boolean,
    essential_categories_available integer NOT NULL CHECK (essential_categories_available BETWEEN 0 AND 5),
    nearest_hospital_m double precision,
    nearest_grocery_store_m double precision,
    nearest_library_m double precision,
    nearest_fire_station_m double precision,
    nearest_school_m double precision,
    transit_access_score double precision NOT NULL CHECK (transit_access_score BETWEEN 0 AND 100),
    service_access_score double precision NOT NULL CHECK (service_access_score BETWEEN 0 AND 100),
    total_accessibility_score double precision NOT NULL CHECK (total_accessibility_score BETWEEN 0 AND 100),
    population integer CHECK (population IS NULL OR population >= 0),
    transit_stops_per_1000 double precision,
    service_locations_per_1000 double precision,
    status_flags text[] NOT NULL DEFAULT '{}',
    quality_flags jsonb NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (run_id, geoid),
    CHECK (ST_SRID(geometry) = 26916), CHECK (NOT ST_IsEmpty(geometry))
);

CREATE INDEX IF NOT EXISTS analysis_results_run_score_idx ON analysis.block_group_results(run_id, total_accessibility_score);
CREATE INDEX IF NOT EXISTS analysis_results_geoid_idx ON analysis.block_group_results(geoid);
CREATE INDEX IF NOT EXISTS analysis_results_geometry_gix ON analysis.block_group_results USING gist(geometry);
