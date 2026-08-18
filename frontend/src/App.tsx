import { useEffect, useMemo, useRef, useState } from "react";
import { Map, NavigationControl, type StyleSpecification } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { api, type FeatureCollection, type RunSummary } from "./api";
import { selectedFeatureProperties } from "./selection";

const categories = ["hospital", "grocery_store", "library", "fire_station"];

function displayValue(value: unknown): string {
  return typeof value === "string" || typeof value === "number"
    ? String(value)
    : "unavailable";
}

export function App() {
  const mapNode = useRef<HTMLDivElement>(null);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [blocks, setBlocks] = useState<FeatureCollection | null>(null);
  const [stops, setStops] = useState<FeatureCollection | null>(null);
  const [services, setServices] = useState<Record<string, FeatureCollection>>(
    {},
  );
  const mapRef = useRef<Map | null>(null);
  const [mapReady, setMapReady] = useState(false);
  const [enabled, setEnabled] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(categories.map((category) => [category, true])),
  );
  const [minScore, setMinScore] = useState(0);
  const [maxScore, setMaxScore] = useState(100);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, unknown> | null>(
    null,
  );

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [nextSummary, nextBlocks, nextStops, ...nextServices] =
        await Promise.all([
          api.summary(),
          api.blockGroups(minScore, maxScore),
          api.stops(),
          ...categories.map((category) => api.services(category)),
        ]);
      setSummary(nextSummary);
      setBlocks(nextBlocks);
      setStops(nextStops);
      setServices(
        Object.fromEntries(
          categories.map((category, index) => [category, nextServices[index]]),
        ),
      );
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to load local analysis data",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (import.meta.env.MODE !== "test") void load();
  }, [minScore, maxScore]);
  useEffect(() => {
    if (!mapNode.current || import.meta.env.MODE === "test") return;
    const tileUrl = import.meta.env.VITE_MAP_TILE_URL;
    const style = tileUrl
      ? {
          version: 8 as const,
          sources: {
            osm: {
              type: "raster" as const,
              tiles: [tileUrl],
              tileSize: 256,
              attribution: "© OpenStreetMap contributors",
            },
          },
          layers: [{ id: "osm", type: "raster" as const, source: "osm" }],
        }
      : {
          version: 8 as const,
          sources: {},
          layers: [
            {
              id: "background",
              type: "background" as const,
              paint: { "background-color": "#e8eee9" },
            },
          ],
        };
    const mapStyle = style as unknown as StyleSpecification;
    const map = new Map({
      container: mapNode.current,
      center: [-86.16, 39.77],
      zoom: 10,
      style: mapStyle,
      attributionControl: {},
    });
    mapRef.current = map;
    map.on("load", () => setMapReady(true));
    map.on("click", "blocks-fill", (event) => {
      const feature = event.features?.[0];
      if (feature?.properties) {
        setSelected(
          selectedFeatureProperties({ properties: feature.properties }),
        );
      }
    });
    map.on("mouseenter", "blocks-fill", () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", "blocks-fill", () => {
      map.getCanvas().style.cursor = "";
    });
    map.addControl(new NavigationControl(), "top-right");
    return () => {
      map.remove();
      mapRef.current = null;
      setMapReady(false);
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const sync = (id: string, data: FeatureCollection) => {
      const source = map.getSource(id) as
        { setData?: (value: unknown) => void } | undefined;
      if (source?.setData) source.setData(data);
      else map.addSource(id, { type: "geojson", data });
    };
    if (blocks) {
      sync("blocks", blocks);
      if (!map.getLayer("blocks-fill"))
        map.addLayer({
          id: "blocks-fill",
          type: "fill",
          source: "blocks",
          paint: {
            "fill-color": [
              "interpolate",
              ["linear"],
              ["coalesce", ["get", "total_accessibility_score"], 0],
              0,
              "#b2182b",
              50,
              "#fddbc7",
              100,
              "#2166ac",
            ],
            "fill-opacity": 0.7,
          },
        });
      if (!map.getLayer("blocks-outline"))
        map.addLayer({
          id: "blocks-outline",
          type: "line",
          source: "blocks",
          paint: { "line-color": "#334e68", "line-width": 0.5 },
        });
    }
    if (stops) {
      sync("stops", stops);
      if (!map.getLayer("stops-points"))
        map.addLayer({
          id: "stops-points",
          type: "circle",
          source: "stops",
          paint: { "circle-color": "#0b7285", "circle-radius": 3 },
        });
    }
    categories.forEach((category) => {
      const data = services[category];
      if (!data) return;
      const id = `services-${category}`;
      sync(id, data);
      const layerId = `${id}-points`;
      if (!map.getLayer(layerId))
        map.addLayer({
          id: layerId,
          type: "circle",
          source: id,
          layout: { visibility: enabled[category] ? "visible" : "none" },
          paint: {
            "circle-color": "#7b2cbf",
            "circle-radius": 4,
            "circle-stroke-color": "#fff",
            "circle-stroke-width": 1,
          },
        });
      else
        map.setLayoutProperty(
          layerId,
          "visibility",
          enabled[category] ? "visible" : "none",
        );
    });
  }, [blocks, stops, services, enabled, mapReady]);

  const visibleServices = useMemo(
    () => categories.filter((category) => enabled[category]),
    [enabled],
  );

  return (
    <main>
      <header className="app-header">
        <div>
          <p className="eyebrow">
            Accessibility Explorer · Marion County, Indiana
          </p>
          <h1>Indy Geospatial Accessibility Platform</h1>
        </div>
        <p className="warning">
          Straight-line, centroid-based proximity screening — not walking
          access, travel time, a causal finding, or a policy recommendation.
        </p>
      </header>
      <section className="controls" aria-label="Analysis filters">
        <label>
          Minimum score{" "}
          <input
            type="number"
            min="0"
            max="100"
            value={minScore}
            onChange={(event) => setMinScore(Number(event.target.value))}
          />
        </label>
        <label>
          Maximum score{" "}
          <input
            type="number"
            min="0"
            max="100"
            value={maxScore}
            onChange={(event) => setMaxScore(Number(event.target.value))}
          />
        </label>
        <fieldset>
          <legend>Service layers</legend>
          {categories.map((category) => (
            <label key={category}>
              <input
                type="checkbox"
                checked={enabled[category]}
                onChange={() =>
                  setEnabled((current) => ({
                    ...current,
                    [category]: !current[category],
                  }))
                }
              />{" "}
              {category.replace("_", " ")}
            </label>
          ))}
        </fieldset>
        <button type="button" onClick={() => void load()}>
          Retry / refresh
        </button>
      </section>
      {loading && (
        <p role="status" className="notice">
          Loading local PostGIS analysis…
        </p>
      )}
      {error && (
        <p role="alert" className="notice error">
          {error}. Start PostGIS and the API, then retry.
        </p>
      )}
      {!loading && !error && summary && (
        <section className="summary" aria-label="Run summary">
          <strong>{summary.run.row_count.toLocaleString()}</strong> block groups
          · mean score{" "}
          <strong>{summary.score_distribution.mean.toFixed(1)}</strong> ·
          ACS-normalized metrics unavailable
        </section>
      )}
      <section className="map-shell" aria-label="Interactive accessibility map">
        <div ref={mapNode} className="map" />
        <div className="map-fallback">
          MapLibre map is ready for local data. {blocks?.features.length ?? 0}{" "}
          block groups, {stops?.features.length ?? 0} transit stops, and{" "}
          {visibleServices.length} enabled service layers loaded.
        </div>
      </section>
      {selected && (
        <aside className="popup" aria-label="Block group detail">
          <button
            type="button"
            onClick={() => setSelected(null)}
            aria-label="Close detail"
          >
            ×
          </button>
          <h2>Block-group result</h2>
          <p>
            <strong>{displayValue(selected.geoid)}</strong>
          </p>
          <p>Total score: {displayValue(selected.total_accessibility_score)}</p>
          <p>Transit score: {displayValue(selected.transit_access_score)}</p>
          <p>Service score: {displayValue(selected.service_access_score)}</p>
          <p>
            Transit stops nearby: {displayValue(selected.transit_stop_count)}
          </p>
          <p>
            Service categories:{" "}
            {Array.isArray(selected.service_categories)
              ? selected.service_categories.join(", ") || "none"
              : "unavailable"}
          </p>
          <p>
            Status:{" "}
            {Array.isArray(selected.status_flags)
              ? selected.status_flags.join(", ")
              : "none"}
          </p>
        </aside>
      )}
      <section className="legend" aria-label="Accessibility score legend">
        <h2>Score legend</h2>
        <div className="legend-items">
          <span>
            <i className="score-low" /> 0–19
          </span>
          <span>
            <i className="score-midlow" /> 20–39
          </span>
          <span>
            <i className="score-mid" /> 40–59
          </span>
          <span>
            <i className="score-midhigh" /> 60–79
          </span>
          <span>
            <i className="score-high" /> 80–100
          </span>
        </div>
      </section>
      <aside className="methodology">
        <h2>How to read this</h2>
        <p>
          Scores combine transit-stop proximity within 400 meters (40%) and
          diversity of known essential-service categories within 1,600 meters
          (60%). Schools are excluded because the available source has no
          geocoded points; ACS population-normalized fields are unavailable. A
          future network analysis is deferred.
        </p>
      </aside>
    </main>
  );
}
