# **Advanced Technical Assignment — Management Cockpit CRM Core (SCD2 In-Table)**
## **1. Vision & Scope**
Build the foundation of a modular Management Cockpit for the firm. The Cockpit is composed of tetherable modules that share a coherent data model and ingestion/update semantics. The CRM serves as the central component; additional modules Money Markets, Portfolio Management (multi-asset), Data Modeling, Trade Analytics, Risk, Compliance) plug into the same core patterns so information flows consistently.

- Design for modularity: modules can be built and deployed independently but interoperate via shared concepts.
- Consistency of ingestion semantics from real-time APIs to flat-file batch loads.
- SCD Type 2 versioning integrated into core tables, not separate history tables.
- Clean DRF APIs, database-first constraints, and test coverage are mandatory.
## **2. Objectives**
- Primary objective: demonstrate understanding of the conceptual framework and high-quality technical implementation of the CRM framework.
- Secondary objectives: performance, auditability, and extensibility for future modules.
## **3. Architectural Principles**
- Single shared core with Entities, Entity Types, and Entity Detail values.
- SCD2 in-table versioning using valid\_from/valid\_to/is\_current; exclusion constraints prevent overlaps.
- Separation of concerns: ingestion services, SCD2 services, API layer, admin layer, module adapters.
- Database is the source of truth: invariants enforced with Postgres constraints and indexes.
- Idempotent operations: replays must not create duplicate versions.
- As-of correctness and reproducibility for all queries.
- Observability: audit log for who/when changed data.
## **4. Tech Stack**
- Python 3.11+, Django 5.x, Django REST Framework
- PostgreSQL 14+ with btree\_gist (for GiST exclusion constraints)
- pytest + pytest-django
- docker-compose for local development
- Django admin and DRF browsable API only (no custom frontend required – segregated UI dev)
## **5. Core Data Model (SCD2 Integrated into Core Tables)**
Start from the base principle: Entities are typed (Entity Type) and have Detail values. All mutable records are versioned in-place via SCD2 columns (valid\_from, valid\_to, is\_current). Constraints are independent from the primary key and use a stable business identifier plus validity windows.
### **5.1 Entity (versioned in place)**
- Representative of a person, institution or other. Each version of an Entity is a row associated to a stable entity\_uid.
- Unique current row per entity\_uid (partial unique index on is\_current=true).
- Exclusion constraint on (entity\_uid, tstzrange(valid\_from, coalesce(valid\_to,'infinity'))) to prevent overlaps.
- Text search index for display\_name recommended.
### **5.2 Entity Type**
Defines the type of entity (PERSON, INSTITUTION). Other modules may extend with additional types but the relationship remains: Entity → Entity Type → Entity Detail.
### **5.3 Entity Detail (versioned in place)**
- Stores typed values for details associated to an entity.
- Natural key for versioning: (entity\_uid, detail\_code).
- Unique current row per (entity\_uid, detail\_code).
- Exclusion constraint on (entity\_uid, detail\_code, tstzrange(valid\_from, coalesce(valid\_to,'infinity'))) to prevent overlaps.
- Hashdiff computed from the normalized business value for idempotency.
## **6. Ingestion & Update Semantics**
- Idempotent ingestion: identical payloads at the same change\_ts must create no new versions.
- Delta detection via hashdiff for both Entity and Entity Detail.
- Transactional close-and-open: close current row then insert new row.
- Batch commands for file ingestion; service functions for real-time updates.
- Post-ingest: refresh materialized views for current snapshots (optional).
## **7. API Surface (DRF)**
- GET /api/v1/entities — filterable list by q=search, type, and by detail\_code filters (current only).
- GET /api/v1/entities/{entity\_uid} — current snapshot of core attributes and details.
- POST /api/v1/entities — create new entity (first versions).
- PATCH /api/v1/entities/{entity\_uid} — apply updates with SCD2 transitions.
- GET /api/v1/entities/{entity\_uid}/history — combined history.
- GET /api/v1/entities-asof?as\_of=YYYY-MM-DD — as-of snapshot resolution.
- GET /api/v1/diff?from=YYYY-MM-DD&to=YYYY-MM-DD — list of changes grouped by entity and field.
## **8. Module Tethering & Extensibility**
- Shared identifiers: entity\_uid is the pivot for cross-module joins.
- Shared SCD2 semantics: validity windows enable consistent as-of reconstructions across modules.
- Shared ingestion contracts: a common interface for real-time and batch updates.
- Shared audit: centralized audit trail schema that records who/when/what changed.
## **9. Audit, Security, and Observability**
- Audit log for every change: actor, timestamp, entity\_uid, detail\_code, before/after.
- Row-level timestamps: created\_at, updated\_at.
- Token-based auth for APIs; structure to support RBAC later.
- PII handling guidelines (restricted fields).
## **10. Performance & Indexing**
- Partial unique indexes for current rows.
- GiST exclusion constraints to prevent overlapping validity intervals.
- Covering indexes for common filters.
- Provide EXPLAIN ANALYZE notes for key queries.
- Optional: materialized view for fast list views.
## **11. Testing Requirements**
- Unit tests for SCD2 transitions.
- API tests: create, update, list, as-of, diff.
- Idempotency tests for ingestion and updates.
- Negative tests for constraint violations.
## **12. Deliverables**
- Django project with DRF endpoints, migrations, and tests.
- docker-compose environment (Postgres + app).
- Management commands for batch ingest and optional snapshot refresh.
- README with architecture overview and example curl sequences.
- Optional short design walkthrough.
## **13. Acceptance Criteria**
- Migrations create SCD2-integrated tables with exclusion constraints.
- Idempotent updates verified by tests.
- APIs provide current, as-of, and diff views correctly.
- Audit trail captures change events.
- Documentation explains the conceptual framework and extensions.
