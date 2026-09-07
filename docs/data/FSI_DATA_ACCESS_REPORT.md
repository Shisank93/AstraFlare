# Forest Survey of India (FSI) Data Access & Accessibility Report

## 1. Overview & Official Portals
- **Official Agency**: Forest Survey of India (FSI), Ministry of Environment, Forest and Climate Change (MoEFCC), Govt. of India.
- **Official Geoportal**: [FSI Van Agni Geo-portal 3.0](https://vanagniportal.fsiforestfire.gov.in/) & [FSI Forest Fire Activities](https://fsi.nic.in/forest-fire-activities)
- **Primary Function**: Operational Near Real-Time (NRT) forest fire monitoring, alert generation, and Large Forest Fire (LFF) tracking using MODIS and SNPP-VIIRS sensors.

## 2. Infrastructure & Web Services
- **Web Services**: WMS (Web Map Service) and WFS (Web Feature Service) endpoints exist for integration with state forest department portals.
- **Attributes Exposed in Public Alerts**:
  - `state_name`: Indian State name.
  - `district_name`: District name.
  - `forest_division`: Forest Division / Range / Beat.
  - `detection_timestamp`: Satellite pass detection timestamp.
  - `sensor`: MODIS / VIIRS.
  - `fire_point_count`: Aggregated detection count.

## 3. Historical Accessibility Assessment
- **Current Season Operational Access**: Public access provides active NRT alerts (rolling window) and daily summary bulletins.
- **Raw Historical Vector Geometries**: Historical multi-year vector archives (older than current operating season) are not publicly exposed as open REST endpoints or bulk vector downloads without official state nodal credentials.
- **Scraping Compliance**: FSI geoportals enforce rate limits and session controls. Aggressive web scraping is prohibited and technically restricted.
- **Historical Records Obtained**: `0` bulk historical shapefiles downloaded from open endpoints.

## 4. Governance Summary
- **Data Status**: `PUBLIC_NRT_ACCESSIBLE / HISTORICAL_RESTRICTED`
- **Recommendation**: Integrate FSI NRT WMS/WFS layers into backend dashboard for live operational context, but rely on NASA FIRMS historical archives for multi-year ML training baselines.
