Performance Notes and EXPLAIN Guidance

Scope

- Summarizes indexing strategy and example EXPLAINs for the most common API flows:
  - Current list and detail filters
  - As-of snapshots
  - Diff (audit) ranges

Database version: PostgreSQL 14+ (GiST available). Django 5 + DRF.

Current Entities (GET /api/v1/entities)

- Query shape: filter current rows, optionally join/prefetch current details via a separate query.
- Existing indexes/constraints:
  - Partial unique: (entity_uuid) WHERE is_current = true
  - Covering index: (type_code) WHERE is_current = true (see migration ix_entity_type_current)
  - Detail covering index: (entity_uuid, detail_code) WHERE is_current = true (ix_edetail_pair_current)
- Recommendations:
  - Search on display_name: add trigram index for performant ILIKE/search. Example:
    CREATE EXTENSION IF NOT EXISTS pg_trgm;
    CREATE INDEX IF NOT EXISTS ix_entity_display_trgm
      ON entity USING gin (display_name gin_trgm_ops)
      WHERE is_current = true;
  - Detail-value filtering: consider partial/functional indexes for common detail codes (e.g., EMAIL) by value column used:
    CREATE INDEX IF NOT EXISTS ix_edetail_email_text
      ON entity_detail (value_text)
      WHERE is_current = true AND detail_code = 'EMAIL' AND value_kind = 'TEXT';

As-Of Snapshot (GET /api/v1/entities-asof)

- Query shape: valid_from <= ts AND (valid_to > ts OR valid_to IS NULL). Details use the same window predicate when included.
- Existing constraint: GiST exclusion on (entity_uuid, tstzrange(valid_from, valid_to)) and on (entity_uuid, detail_code, tstzrange(...)). This creates/supports a GiST index.
- Tip: Switch to range operator in SQL to fully leverage GiST for read path:
  - Use: tstzrange(valid_from, COALESCE(valid_to, 'infinity'::timestamptz)) @> :ts
  - The same expression/operator family is used by the exclusion constraint, so the underlying GiST index can accelerate the lookup.
- Example (entities):
  EXPLAIN ANALYZE
  SELECT *
  FROM entity e
  WHERE tstzrange(e.valid_from, COALESCE(e.valid_to, 'infinity')) @> TIMESTAMPTZ '2025-01-15T10:30:00Z';

Diff (GET /api/v1/diff)

- Query shape: happened_at BETWEEN :from AND :to, ordered by happened_at.
- Current indexes: btree on (entity_uuid), btree on (module, target_kind).
- Recommendation: add an index on happened_at to accelerate range scans:
  CREATE INDEX IF NOT EXISTS ix_audit_happened_at ON audit_event (happened_at);

General Practices

- Keep SCD2 write path transactional; service functions already use SELECT FOR UPDATE to serialize transitions.
- Prefer EXISTS subqueries for detail presence checks (already used in EntitiesFilter).
- For JSON details, add GIN jsonb_path_ops where containment filters are common by detail_code.

Interpreting EXPLAIN

- For range predicates, expect GiST Index Cond with the @> operator.
- For diff ranges, expect Index Scan on audit_event using ix_audit_happened_at with filter on lower/upper bounds.
- For display_name search, expect Bitmap Index Scan using trigram GIN with Recheck Cond.

