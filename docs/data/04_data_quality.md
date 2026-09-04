# Data Quality & Governance Metadata Specification

**Project:** AstraFlare  
**Document:** Source Isolation, Data Quality Flags & Auditability  

---

## 1. Source Classification Matrix

AstraFlare enforces strict source isolation across the pipeline:

| Source Tag | Definition | Analytics / ML Use |
| :--- | :--- | :--- |
| **`REAL`** | Observations ingested directly from official NASA FIRMS or OSM API endpoints. | **PRIMARY** (Production Analytics & Model Evaluation) |
| **`MOCK`** | Offline development fallback records when API keys or network connection are unavailable. | Testing & Local API Validation Only |
| **`SYNTHETIC_DEMO`** | Hand-crafted workflow demonstration scenarios (Scenarios A, B, C, D). | Triage Interface & UI Walkthroughs Only |

---

## 2. Missing Context Quality Flags

When external contextual services (OSM or WorldCover) are unavailable or return incomplete data, AstraFlare flags data quality explicitly:

- `data_quality = 'COMPLETE'`: All GIS, industrial, and land-cover features populated.
- `data_quality = 'PARTIAL_CONTEXT'`: One or more contextual fields (e.g. WorldCover or OSM) missing/fallback.
- `data_quality = 'RAW_OBSERVATION'`: Thermal observation ingested without GIS enrichment.
