# ADR-006: Utilization of Weak Supervision & Noisy Label Governance

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
Hand-annotated ground-truth labels for millions of historical global FIRMS thermal anomalies do not exist in a single public dataset.

**Decision:**  
Use **Weak Supervision** (heuristic rules combining OSM industrial boundaries, ESA WorldCover rasters, and FIRMS historical clusters) to bootstrap initial training labels.

**Alternatives Considered:**  
1. **Manual Annotation:** Impractical within hackathon timeframe.

**Trade-offs & Rationale:**  
Weak supervision enables rapid generation of rich synthetic/provisional training datasets. To prevent circular learning, the heuristic rules used for weak supervision are explicitly decoupled from the model inference features, and outputs are rigorously validated against held-out test scenarios.
