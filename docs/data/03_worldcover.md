# ESA WorldCover Land-Cover Engine Specification

**Project:** AstraFlare  
**Document:** Land-Cover Context Lookup, Spatial Uncertainty & Raster Sampling  

---

## 1. Overview & Classification Scheme

ESA WorldCover provides 10m resolution global land-cover categories:

| Code | Class Name | Description |
| :--- | :--- | :--- |
| **10** | Tree cover | Forest / Dense tree canopy |
| **20** | Shrubland | Natural shrubland vegetation |
| **30** | Grassland | Natural grassland |
| **40** | Cropland | Farmland & cultivated crops |
| **50** | Built-up | Urban, industrial & built infrastructure |
| **60** | Bare / sparse | Sand, rock, bare soil |
| **80** | Permanent water | Water bodies, lakes, rivers |
| **90** | Herbaceous wetland | Swamps & marshes |
| **95** | Mangroves | Coastal mangrove vegetation |

---

## 2. Spatial Uncertainty & Sampling Rationale

> [!NOTE]
> Satellite thermal anomalies (e.g. VIIRS 375m pixel size) carry spatial uncertainty. The Land-Cover Engine samples both the exact point pixel and the dominant land-cover category within a 375m buffer to prevent land-cover misclassification.
