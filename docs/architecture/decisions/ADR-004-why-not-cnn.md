# ADR-004: Justification Against Initial CNN / Computer Vision Architecture

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
SIH evaluation panels frequently query why deep learning computer vision (CNN/ResNet/UNet) was not chosen for thermal anomaly classification.

**Decision:**  
De-prioritize CNN/Vision models for the MVP in favor of enriched Tabular GBDT.

**Alternatives Considered:**  
1. **Satellite Imagery Segmentation (CNN / Vision Transformer):** Requires downloading optical RGB/Multispectral tiles (Sentinel-2/Landsat-8) for every thermal coordinate.

**Trade-offs & Rationale:**  
- **Data Reality:** NASA FIRMS outputs tabular thermal points (lat, lon, FRP, brightness), not real-time imagery streams.
- **Latency & Bandwidth:** Fetching 10m satellite optical rasters dynamically introduces 5–30 second latency per point and API rate limiting.
- **Cost & Compute:** CNN inference requires GPU infrastructure, whereas tabular GBDT runs ultra-fast on standard CPU instances.
- **Conclusion:** Tabular GBDT with PostGIS spatial enrichment achieves the desired classification accuracy and latency without image download bottlenecks.
