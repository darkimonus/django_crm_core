PII Handling Guidelines

Purpose

- Provide pragmatic guidance for handling personally identifiable information (PII) in the CRM core.

Classification

- Public: non-sensitive metadata (entity type codes, non-identifying labels).
- Internal: business data that is not directly identifying on its own.
- PII (direct/indirect): names, emails, phone numbers, government IDs, addresses, birth dates, etc.

Minimization

- Store only what is necessary for operations.
- Prefer generic detail codes (e.g., CONTACT_EMAIL) and avoid storing duplicates across modules.

Access Control

- Enforce least privilege via API tokens/roles (JWT in this project; RBAC future-ready).
- Restrict write endpoints; log actors via audit for all mutations.

Field-Level Protections (optional patterns)

- Hashing: store a hashed variant (e.g., lowercased email SHA256) alongside cleartext where exact match lookups are required without exposing value in indexes. Example detail pair:
  - EMAIL_TEXT (clear), EMAIL_SHA256 (hash) — filter on hash when possible.
- Encryption: for highly sensitive PII, use application-level encryption (e.g., Fernet/KMS) with envelope keys; keep ciphertext at rest and decrypt only in trusted contexts.
- Redaction in audit: when writing audit before/after, omit or mask sensitive fields (e.g., partially mask emails/phones).

Transport & Storage

- TLS for all external transport (outside Docker dev).
- Backups treated with same sensitivity; ensure access logging and rotation.

Retention & Erasure

- Define TTLs per detail code where feasible; schedule archival or deletion jobs.
- Support right-to-erasure by hard-deleting or anonymizing non-essential history, balancing regulatory needs with auditability.

Testing & Fixtures

- Use synthetic or anonymized data in tests and demos (already true in this repo). Avoid real PII in commits.

Observability

- Monitor access to PII-bearing endpoints; alert on unusual access patterns.
- Keep audit logs immutable and searchable; consider masking sensitive before/after values when not required for investigations.

