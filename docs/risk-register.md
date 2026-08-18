# Initial risk register

This register captures risks known before data acquisition. Likelihood and
impact will be reassessed when evidence becomes available.

| Risk | Why it matters | Initial mitigation | Validation milestone |
| --- | --- | --- | --- |
| Authoritative source URLs or schemas change | Automated downloads and field mappings can break silently. | Record direct URLs, retrieval dates, checksums where useful, schemas, and quality assertions; document manual fallbacks. | 1 |
| Facility data have unclear reuse terms | A public portfolio cannot redistribute data without permission. | Verify terms per source, store metadata, commit scripts rather than raw files, and use only legal minimal fixtures. | 1 |
| Neighborhood boundaries are not a single official analytical unit | Results can change with tract, block-group, or neighborhood aggregation. | Compare available geographies and justify the selected reporting unit; preserve stable source identifiers. | 1–3 |
| Transit schedules and service levels vary over time | A static stop layer can overstate useful access. | Preserve GTFS feed dates and service calendars; state the analysis period and test temporal assumptions. | 1–3 |
| Euclidean proximity overstates walkable access | Rivers, highways, sidewalks, crossings, and network topology affect travel. | Label the baseline as proximity only; add a separately validated network method if routing data support it. | 3 |
| Composite score weights embed value judgments | Rankings may appear more objective than they are. | Publish formulas, normalize inputs transparently, justify weights, and include sensitivity checks. | 3 |
| Docker engine or PostGIS is unavailable locally | Database integration tests and reproducible ETL could be blocked. | Use an official pinned PostGIS image, add health checks, and document native-client alternatives. Docker CLI is installed but the engine did not respond during initial inspection; `psql` was absent. | 2 |
| ArcGIS use requires credentials, entitlements, or attribution | A public client must not expose private tokens and may not be reproducible for reviewers. | Keep MapLibre as the credential-free baseline; isolate the map provider; document account/license requirements before enabling ArcGIS features. | 5 |
| CRS choice creates distance or area distortion | Accessibility distances and population-normalized areas can be misleading. | Inspect source CRSs and select a suitable local projected CRS with units and transformation recorded in metadata. | 2 |
| Demographic aggregation introduces uncertainty and ecological fallacy | Neighborhood indicators do not describe every resident or individual trip. | Preserve Census vintages and margins of error where applicable; document aggregation and interpretation limits. | 1–3 |
