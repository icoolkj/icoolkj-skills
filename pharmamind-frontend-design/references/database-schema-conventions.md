# Database Schema Conventions

## Naming Contract

All physical database identifiers introduced for PharmaMind use the lowercase `icoolkj_` namespace. Keep the name after the prefix recognizable and consistent with the approved domain schema.

| Object | Pattern | Example |
| --- | --- | --- |
| Table | `icoolkj_<source_table>` | `icoolkj_sys_user` |
| Column | `icoolkj_<source_column>` | `icoolkj_tenant_id` |
| Primary key | `icoolkj_pk_<short_table>` | `icoolkj_pk_sys_user` |
| Foreign key | `icoolkj_fk_<short_table>_<short_target>` | `icoolkj_fk_user_tenant` |
| Unique constraint | `icoolkj_uk_<short_table>_<purpose>` | `icoolkj_uk_user_tenant_name` |
| Index | `icoolkj_idx_<short_table>_<purpose>` | `icoolkj_idx_user_tenant_status` |
| Check constraint | `icoolkj_ck_<short_table>_<purpose>` | `icoolkj_ck_user_status` |

For other explicitly named database objects, use the same prefix. Avoid adding the prefix more than once. Keep names lowercase snake case, and use deterministic abbreviations only when the target engine's identifier limit requires them. Verify uniqueness after shortening.

## Logical-to-Physical Mapping

The database naming convention does not require awkward names in Python, TypeScript, or JSON. Map physical identifiers at the persistence boundary and preserve established logical contracts.

```python
class User(Base):
    __tablename__ = "icoolkj_sys_user"

    id: Mapped[UUID] = mapped_column("icoolkj_id", primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column("icoolkj_tenant_id", nullable=False)
```

Foreign-key declarations, indexes, constraints, raw SQL, fixtures, and migration operations must point to the physical names. API request and response fields remain `id` and `tenant_id` unless a separately versioned API contract requires otherwise.

## Schema Source and Engine Adaptation

- Start from the approved schema/design artifact for domain entities, relationships, lifecycle fields, tenant scope, and business constraints.
- Reconcile the artifact with the current ORM models, migrations, seed data, and runtime database before implementation. Record differences rather than silently choosing one.
- The supplied `icoolkj.sql` is MySQL 8.4/InnoDB and contains 33 `sys_*` tables with unprefixed columns. It is a business-schema reference, not a ready-to-run migration for PharmaMind, whose current database is PostgreSQL with pgvector.
- Convert engine-specific types and behavior deliberately, including auto-increment/identity, JSON, timestamps, indexes, collations, defaults, and foreign-key semantics. Review PostgreSQL identifier limits and extension requirements.
- A schema change should define primary keys, nullability, defaults, foreign keys, deletion behavior, unique rules, query indexes, tenant boundaries, and audit/soft-delete behavior where applicable.
- Tenant-scoped data must include the correct tenant key and enforce tenant-aware uniqueness and authorization. A frontend organization selector is never a substitute for database/query/API isolation.

## Existing Database Migration

Applying the prefix to an existing database is a data migration, not a search-and-replace task.

1. Inventory tables, columns, indexes, constraints, views, triggers, raw SQL, ORM mappings, reports, and external integrations that use the old names.
2. Produce a complete old-to-new name map and verify there are no collisions or target-engine length violations.
3. Decide whether to use a maintenance-window rename or a staged compatibility migration. Include data backup, deployment order, rollback/forward recovery, and API compatibility.
4. Update the ORM and Alembic migration together. Test both a clean database install and an upgrade from the supported prior revision.
5. Do not use destructive `drop_all`/recreate workflows on deployed data. Do not perform a broad database rename unless the user explicitly requested and approved that migration scope.

## Copyright and Ownership

`icoolkj_` helps identify the project's database namespace, but a prefix does not establish or enforce copyright ownership. Use the repository's license and copyright notices, retain project/version history, and obtain legal advice for jurisdiction-specific ownership questions. Avoid putting a copyright notice in every column name.

## Review Checklist

- Do all new physical table and column identifiers start with exactly one `icoolkj_` prefix?
- Do named indexes and constraints follow the same namespace and fit target-engine limits?
- Do ORM mappings preserve stable logical property and API names?
- Do foreign keys, migrations, fixtures, seed data, and raw SQL consistently use physical names?
- Is the DDL adapted to the active database engine rather than copied from another dialect?
- Are tenant isolation, upgrade safety, rollback/recovery, and existing data accounted for?
