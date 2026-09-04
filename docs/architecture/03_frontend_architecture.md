# Frontend Architecture & Analyst UX Specification

**Project:** AstraFlare  
**Document:** React + TypeScript Application & UX Design System  

---

## 1. Application Layout Architecture

The AstraFlare Analyst Interface is designed as a **high-density, mission-critical geospatial operations dashboard**:

```text
+-----------------------------------------------------------------------------------+
|                        ASTRAFLARE | Geospatial Intelligence Platform               |
| Filters: [ All Risk Levels ▼ ] [ All Classes ▼ ] [ Last 24 Hours ▼ ]  [Refresh ↻] |
+------------------------------------+----------------------------------------------+
| ALERT TRIAGE LIST (35% Width)      | INTERACTIVE MAP VIEW (65% Width)             |
| ────────────────────────────────── | ──────────────────────────────────────────-- |
| 🔴 CRITICAL RISK (0.94)            | MapLibre GL Canvas / Leaflet                 |
|    Jamnagar Refinery Anomaly       |  - Color-coded thermal hotspot markers       |
|    Likely Industrial Incident      |  - Industrial facility polygons / points     |
|    FRP: 142.5 MW | 12m ago         |  - Radius search buffers (1km / 5km)         |
| ---------------------------------- |  - Heatmap & satellite tile layer toggle     |
| 🟡 MEDIUM RISK (0.61)              |                                              |
|    Surat Industrial Area           | ──────────────────────────────────────────-- |
|    Persistent Industrial Heat      | SELECTED EVENT INVESTIGATION PANEL (Slide-over)|
|    FRP: 45.1 MW | 45m ago          |  - Event Summary & Risk Score Badge          |
| ---------------------------------- |  - ML Confidence & Probabilities             |
| ⚪ HUMAN REVIEW REQUIRED (0.42)   |  - Evidence List & Key Drivers               |
|    Forest Margin Anomaly           |  - Historical FRP Timeline Graph             |
|    Abstained - Conflicting Signal  |  - Analyst Action Buttons:                   |
|                                    |    [ Confirm Incident ] [ Flag As Natural ]   |
+------------------------------------+----------------------------------------------+
```

---

## 2. Key Components Hierarchy

```text
src/
├── components/
│   ├── layout/
│   │   ├── Navbar.tsx
│   │   └── FilterBar.tsx
│   ├── map/
│   │   ├── GeospatialMap.tsx
│   │   ├── HotspotMarker.tsx
│   │   ├── IndustrialLayer.tsx
│   │   └── MapControls.tsx
│   ├── alerts/
│   │   ├── AlertList.tsx
│   │   ├── AlertCard.tsx
│   │   └── RiskBadge.tsx
│   ├── investigation/
│   │   ├── InvestigationPanel.tsx
│   │   ├── EvidenceCard.tsx
│   │   ├── HistoricalChart.tsx
│   │   └── ReviewModal.tsx
│   └── analytics/
│       └── SystemMetrics.tsx
├── services/
│   ├── api.ts
│   └── geojson.ts
├── store/
│   └── useHotspotStore.ts
└── types/
    └── index.ts
```

---

## 3. Visual Styling & Design System Rules

- **Theme:** Dark Mode Tactical Palette (Sleek slate background `#0f172a`, card containers `#1e293b`, borders `#334155`).
- **Accent Color Hierarchy:**
  - `Likely Industrial Incident`: Bright Crimson Red (`#ef4444`)
  - `Persistent Industrial Heat`: Solar Amber (`#f59e0b`)
  - `Natural/Wildland Fire`: Emerald Forest Green (`#10b981`)
  - `Human Review Required`: Indigo Abstention (`#6366f1`)
- **Typography:** Inter / Outfit clean sans-serif for numerical data and metrics.
- **No Decorative Gimmicks:** Focus strictly on spatial clarity, information density, map responsiveness, and analyst workflow speed.
