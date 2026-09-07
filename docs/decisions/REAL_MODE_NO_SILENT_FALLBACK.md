# Architecture Decision Record (ADR) — REAL Mode & No Silent Fallback

**Status:** Approved & Enforced  
**Date:** September 5, 2026  
**Deciders:** AstraFlare Engineering Team  

---

## Context

In early prototypes, when a PostgreSQL database connection failed, the database access manager (`database/db.py`) would silently initialize an empty in-memory SQLite database. While helpful for basic isolated unit tests, this silent fallback created severe data integrity risks in operational environments:
1. Operational API requests in `REAL` mode could silently execute against an empty database, returning 0 records without alerting operators.
2. Synthetic demo data could accidentally enter production intelligence workflows.
3. System errors would be swallowed rather than flagged as infrastructure outages.

---

## Decision

AstraFlare Phase 4 mandates explicit mode separation via the configuration variable `ASTRAFLARE_MODE`:

1. **`ASTRAFLARE_MODE=REAL` (Default):**
   * PostgreSQL + PostGIS is **REQUIRED**.
   * Only real observations (`data_source = 'REAL'`) are queried and returned.
   * If PostgreSQL or PostGIS cannot be connected to, the system MUST **FAIL CLEARLY**.
   * The database manager will raise a `RuntimeError` and return a standard HTTP 503 JSON error:
     ```json
     {
       "error": {
         "code": "DATABASE_UNAVAILABLE",
         "message": "PostgreSQL/PostGIS is required in REAL mode but connection failed."
       }
     }
     ```
   * Silent fallback to SQLite, in-memory data, or generated demo data is strictly **PROHIBITED**.

2. **`ASTRAFLARE_MODE=DEMO`:**
   * Synthetic/demo data queries are explicitly permitted.
   * Fallback to SQLite is allowed for isolated offline test environments.
   * Every synthetic record MUST remain clearly tagged with `data_source = 'SYNTHETIC_DEMO'`.
   * Demo records are strictly excluded from all scientific ML baseline training and evaluation datasets.

---

## Consequences

* **Positive:** Guaranteed data integrity in production. Operational users are immediately notified if database infrastructure is offline rather than viewing misleading empty screens.
* **Operational Requirement:** Production deployments must provide valid PostgreSQL + PostGIS environment credentials (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`).
