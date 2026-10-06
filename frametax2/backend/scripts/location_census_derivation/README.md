# Location-capability census derivation (2026-10-06)

Reproduces `app/data/jurisdiction_location_capability.py` (the 1,140 census cells) from structured official/authoritative datasets.
It is an offline research tool, NOT runtime code, and needs `shapely pyshp rasterio numpy openpyxl` (not backend dependencies).

Run in an empty work directory containing the downloads below, in this order: `geoms.py`, `vec.py`, `koppen.py <tif>`, `glc.py`, `tab.py`,
`derive.py`, `emit.py`. `emit.py` writes the data module; then `python scripts/build_location_capability_census.py` rebuilds the CSV.

| Dataset | Source | Version used |
|---|---|---|
| Natural Earth 1:10m admin-0/1, land, minor islands, geography regions + elevation points, glaciated areas, populated places | https://naciscdn.org/naturalearth/10m/{cultural,physical}/ne_10m_*.zip | admin 5.1.1/5.1.2, regions 5.0.0 (`ne/<layer>/`) |
| Koppen-Geiger 1991-2020, 1 km (Beck et al. 2023, Sci. Data 10:724) | https://doi.org/10.6084/m9.figshare.21789074.v2 (`koppen_geiger_tif.zip`) | figshare v2 2026-01-14 |
| FAO GLC-SHARE v1.0 layers 01-04, 08-10 | https://storage.googleapis.com/fao-maps-catalog-data/uuid/ba4526fd-cdbf-4028-a1bd-5a559c4bff38/resources/GlcShare_v10_NN.zip (`glc/xNN/`) | v1.0 (2014) |
| World Bank WDI AG.LND.FRST.ZS (FAO FRA) | https://api.worldbank.org/v2/country/all/indicator/AG.LND.FRST.ZS?format=json&per_page=20000&mrnev=1 (`wb_<indicator>.json`) | last updated 2026-07-13 |
| UN DESA WUP 2025 F01 | https://population.un.org/wup/downloads (`wup_f01.xlsx`) | Rev.2025 |
| UNESCO World Heritage List (open data) | https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/exports/csv (`whc_full.csv`) | 1,273 properties |
| US NPS NRHP historic districts by State | https://mapservices.nps.gov/arcgis/rest/services/cultural_resources/nrhp_locations/MapServer/0 (`nrhp_districts.json`) | live 2026-10-06 |
| Australian National Heritage List | https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/National_Heritage_List/MapServer/0 (`au_nhl.geojson`) | updated 2026-02-25 |

Rules (thresholds are in `derive.py`): negatives are only emitted where the category is defined by the dataset's own classification
(no tropical Koppen group-A cell; no marine coastline and no island landmass; no arid/polar cell, no desert region, no UNESCO desert
property and negligible bare/sparse cover; no tropical or temperate Koppen class; fully tropical for snow; no tree cover in two FAO
sources). Everything else that no source establishes stays UNRESOLVED_NEUTRAL.
