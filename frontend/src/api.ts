export type FeatureCollection = {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: unknown;
    properties: Record<string, unknown>;
  }>;
};

export type RunSummary = {
  run: { run_id: string; population_available: boolean; row_count: number };
  score_distribution: {
    minimum: number;
    maximum: number;
    mean: number;
    buckets: Record<string, number>;
  };
};

const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`);
  if (!response.ok) throw new Error(`API request failed (${response.status})`);
  return response.json() as Promise<T>;
}

export const api = {
  summary: () => get<RunSummary>("/api/v1/runs/latest/summary"),
  blockGroups: (min: number, max: number) =>
    get<FeatureCollection>(
      `/api/v1/block-groups?min_score=${min}&max_score=${max}&limit=5000`,
    ),
  services: (category: string) =>
    get<FeatureCollection>(
      `/api/v1/services?category=${encodeURIComponent(category)}`,
    ),
  stops: () => get<FeatureCollection>("/api/v1/transit/stops"),
};
