# ADR-002: Selection of FastAPI as Backend Framework

**Status:** Accepted  
**Date:** 2026-09-04  

**Context:**  
AstraFlare needs an asynchronous, high-throughput Python backend framework that integrates seamlessly with Python data science, GIS, and ML libraries (Pandas, GeoPandas, Scikit-Learn, LightGBM).

**Decision:**  
Use **FastAPI** paired with Pydantic v2 and Uvicorn.

**Alternatives Considered:**  
1. **Flask:** Lacks native async request handling and static type validation out of the box.
2. **Django / Django REST Framework:** Heavy overhead, opinionated ORM that adds complexity to spatial data transformation.
3. **Node.js (Express/NestJS):** Requires cross-process IPC to execute Python ML and GIS models, increasing operational complexity.

**Trade-offs & Rationale:**  
FastAPI delivers sub-millisecond route resolution, automated OpenAPI/Swagger documentation, native async/await for external HTTP polling (NASA FIRMS / OSM Overpass), and seamless Pydantic data serialization.
