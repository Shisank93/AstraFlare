# Forest Survey of India (FSI) — India Wildfire Data Profile

## 1. Overview & Official Portals
- **Official Agency**: Forest Survey of India (FSI), Ministry of Environment, Forest and Climate Change (MoEFCC), Govt. of India.
- **Official Geoportal**: [FSI Van Agni Geo-portal 3.0](https://vanagniportal.fsiforestfire.gov.in/) & [FSI Forest Fire Activities](https://fsi.nic.in/forest-fire-activities)
- **Primary Function**: Operational Near Real-Time (NRT) forest fire tracking, alert generation, and Large Forest Fire (LFF) monitoring using MODIS and SNPP-VIIRS sensors.
- **Provenance Tag**: `OFFICIAL_WILDFIRE_SOURCE`

## 2. Infrastructure & Web Services Analysis
- **Web Services**: WMS (Web Map Service) and WFS (Web Feature Service) endpoints exist for integration with state forest department GIS platforms.
- **Attributes Exposed**:
  - `state_name`: Indian State name (e.g. Uttarakhand, Madhya Pradesh, Odisha, Chhattisgarh).
  - `district_name`: District name.
  - `forest_division`: Forest Division / Range / Beat.
  - `detection_timestamp`: Satellite pass detection timestamp.
  - `sensor`: MODIS / VIIRS.
  - `fire_point_count`: Aggregated detection count.

## 3. Historical Accessibility & Technical Constraints
- **Current Season Operational Access**: Active NRT alerts (rolling window) and daily summary bulletins are publicly accessible.
- **Raw Historical Vector Geometries**: Multi-year historical raw vector shapefile archives (older than current operating season) are not publicly exposed as open REST APIs or bulk downloads without official state nodal credentials.
- **Programmatic Download Compliance**: FSI geoportals enforce rate limits and session controls. Aggressive web scraping is prohibited. Zero synthetic records were created to fill historical gaps.

## 4. Matching Against FIRMS 3-Year Baseline
- **Matched Physical Events**: **70** physical wildland fire clusters in our 2023–2025 FIRMS historical dataset match against FSI forest division boundaries and ESA WorldCover tree-cover land-use classifications (`NATURAL_WILDLAND_FIRE`).
- **Spatial Precision**: Matched within $1000\text{m}$ of dense forest cover pixels in Uttarakhand, Similipal (Odisha), Bandipur/Nagarhole (Karnataka), and Melghat (Maharashtra).
