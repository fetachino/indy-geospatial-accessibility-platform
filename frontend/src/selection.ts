export type MapFeature = { properties: Record<string, unknown> };

export function selectedFeatureProperties(
  feature: MapFeature,
): Record<string, unknown> {
  return feature.properties;
}
