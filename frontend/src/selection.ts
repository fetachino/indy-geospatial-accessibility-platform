export type MapFeature = { properties: Record<string, unknown> };

export type SelectableCollection = {
  features: Array<MapFeature & { geometry: unknown }>;
};

export function selectedFeatureProperties(
  feature: MapFeature,
): Record<string, unknown> {
  return feature.properties;
}

/** Lightweight fallback hit-test for browsers that do not report a rendered fill. */
export function featureAtCoordinate(
  collection: SelectableCollection,
  longitude: number,
  latitude: number,
): MapFeature | null {
  let nearest: MapFeature | null = null;
  let nearestDistance = Number.POSITIVE_INFINITY;
  for (const feature of collection.features) {
    const values: number[][] = [];
    const visit = (value: unknown): void => {
      if (Array.isArray(value) && typeof value[0] === "number") {
        values.push(value as number[]);
      } else if (Array.isArray(value)) {
        value.forEach(visit);
      }
    };
    visit((feature.geometry as { coordinates?: unknown } | null)?.coordinates);
    if (!values.length) continue;
    const lons = values.map((value) => value[0]);
    const lats = values.map((value) => value[1]);
    const centerLon = (Math.min(...lons) + Math.max(...lons)) / 2;
    const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const distance = (longitude - centerLon) ** 2 + (latitude - centerLat) ** 2;
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearest = feature;
    }
    if (
      longitude >= Math.min(...lons) &&
      longitude <= Math.max(...lons) &&
      latitude >= Math.min(...lats) &&
      latitude <= Math.max(...lats)
    ) {
      return feature;
    }
  }
  return nearest;
}
