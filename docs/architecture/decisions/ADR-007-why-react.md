# ADR-007: Selection of React + TypeScript for Analyst Frontend

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
The analyst dashboard requires complex UI state management (map bounds, selected hotspot filters, evidence modals, real-time alert updates, timeline charts).

**Decision:**  
Use **React with TypeScript** and a modern state store (Zustand or React Context).

**Alternatives Considered:**  
1. **Vanilla HTML/JS:** Difficult to maintain for complex interactive map + sidebar state sync.
2. **Streamlit / Gradio:** Limited custom layout control, lacks native MapLibre GL integration for mission-critical operations dashboard aesthetic.

**Trade-offs & Rationale:**  
React provides component reusability, rich ecosystem support for MapLibre GL and Recharts, and TypeScript compile-time type safety for GeoJSON and API response contracts.
