# 60-second interview talk track

“I built a recruiter-ready GIS application around a real Marion County question:
which block groups may have weaker transit and essential-service access? Public
sources are cataloged and cached, transformed into a meter-based projected CRS,
validated and loaded transactionally into PostGIS, then scored with a simple
0.4 transit / 0.6 service proximity formula. FastAPI serves typed GeoJSON and a
React/MapLibre client lets users filter scores, toggle layers, and click a
block group for its component scores and data-status flags. I deliberately
label it a straight-line screening indicator, not a walking or policy result.
The most instructive bug was an API connection generator that closed psycopg
before queries; I reproduced it locally, fixed the lifecycle, and added tests.
The next technical step would be network accessibility and better population
normalization.”

Likely follow-ups: explain why EPSG:26916 is used for meter distances, how
status flags prevent silent missing-data assumptions, why MapLibre is default,
and which ArcGIS steps require a separate account or ArcGIS Pro license.
