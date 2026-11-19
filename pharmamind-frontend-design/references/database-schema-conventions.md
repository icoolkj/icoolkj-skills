# Database Schema Conventions

## Naming Contract

Only physical table names introduced for PharmaMind use the lowercase `icoolkj_` prefix. Column, index, constraint, trigger, and function names remain ordinary lowercase `snake_case` without that prefix. Keep table names recognizable and consistent with the approved domain schema. The complete 33-table baseline is mandatory for every project using this skill; feature-specific scope does not reduce the initialization set.

| Object | Pattern | Example |
| --- | --- | --- |
| Table | `icoolkj_<source_table>` | `icoolkj_sys_user` |
| Column | `<source_column>` | `tenant_id` |
| Primary key | `pk_<short_table>` | `pk_sys_user` |
| Foreign key | `fk_<short_table>_<short_target>` | `fk_user_tenant` |
| Unique constraint | `uk_<short_table>_<purpose>` | `uk_user_tenant_name` |
| Index | `idx_<short_table>_<purpose>` | `idx_user_tenant_status` |
| Check constraint | `ck_<short_table>_<purpose>` | `ck_user_status` |

Use ordinary lowercase `snake_case` for other database objects, including triggers and functions. Never add `icoolkj_` to a column or non-table object name. Use deterministic abbreviations only when the target engine's identifier limit requires them, and verify uniqueness after shortening.

## Logical-to-Physical Mapping

The database naming convention does not require awkward names in Python, TypeScript, or JSON. Map physical identifiers at the persistence boundary and preserve established logical contracts.

```python
class User(Base):
    __tablename__ = "icoolkj_sys_user"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(nullable=False)
```

Foreign-key declarations, indexes, constraints, raw SQL, fixtures, and migration operations must point to the physical names. API request and response fields remain `id` and `tenant_id` unless a separately versioned API contract requires otherwise.

## Mandatory System Baseline

- Initialize every table in [system-schema.postgresql.sql](system-schema.postgresql.sql) through a versioned migration, even if the first release uses only a subset. Add business tables on top; do not select only currently visible features.
- Keep this baseline as the shared source for authentication, tenant, department, role, menu, audit, configuration, and messaging system data. Map feature models to it rather than creating parallel legacy-name equivalents.
- The provided MySQL 8.4/InnoDB export has 33 tables, 455 columns, 33 primary keys, 18 unique indexes, and 97 ordinary indexes. The PostgreSQL conversion preserves table/column comments and the 21 automatic `updated_at` behaviors with triggers.
- The source DDL has no foreign-key declarations and no `INSERT` seed rows. Do not claim referential constraints or populated reference data exist; add them only through a reviewed design/migration.
- The conversion maps MySQL `datetime(3)` to PostgreSQL `timestamp(3) without time zone` to retain the source's timezone-naive storage. Confirm the application's timezone convention before exposing these values through APIs.
- MySQL's `utf8mb4_0900_ai_ci`/`utf8mb4_unicode_ci` collation behavior has no automatic one-to-one PostgreSQL default. Review case/accent handling for lookups, uniqueness, and search; add explicit collation or normalized indexes where required.

## Schema Source and Engine Adaptation

- Start from the approved schema/design artifact for domain entities, relationships, lifecycle fields, tenant scope, and business constraints.
- Reconcile the artifact with the current ORM models, migrations, seed data, and runtime database before implementation. Record differences rather than silently choosing one.
- The supplied `icoolkj.sql` is the domain schema source, not executable project DDL. The PostgreSQL-converted system file is the target-dialect baseline for PharmaMind and other projects using this skill.
- Convert engine-specific types and behavior deliberately, including auto-increment/identity, JSON, timestamps, indexes, collations, defaults, and foreign-key semantics. Review PostgreSQL identifier limits and extension requirements.
- A schema change should define primary keys, nullability, defaults, foreign keys, deletion behavior, unique rules, query indexes, tenant boundaries, and audit/soft-delete behavior where applicable.
- Tenant-scoped data must include the correct tenant key and enforce tenant-aware uniqueness and authorization. A frontend organization selector is never a substitute for database/query/API isolation.
- Preserve the platform's pgvector and pgcrypto extension bootstrap; do not remove it when applying the baseline. The system schema currently contains no vector columns and does not replace those extensions.

## Existing Database Migration

Applying the prefix to an existing database is a data migration, not a search-and-replace task.

1. Initialize the entire missing system baseline in the initial versioned migration; on an existing database, inventory tables, columns, indexes, constraints, views, triggers, raw SQL, ORM mappings, reports, and integrations first.
2. Produce a complete name/model mapping and verify there are no collisions or target-engine length violations.
3. Decide whether convergence requires a maintenance window or staged compatibility migration. Include backup, deployment order, rollback/forward recovery, and API compatibility.
4. Update ORM mappings and migrations together. Test a clean database install and an upgrade from each supported prior revision, then verify all 33 required table names.
5. Do not use destructive `drop_all`/recreate workflows on deployed data. Do not perform a broad database rename unless the user explicitly requested and approved that migration scope.

## Copyright and Ownership

`icoolkj_` helps identify the project's database namespace, but a prefix does not establish or enforce copyright ownership. Use the repository's license and copyright notices, retain project/version history, and obtain legal advice for jurisdiction-specific ownership questions. Avoid putting a copyright notice in every column name.

## Review Checklist

- Do all physical table names use exactly one `icoolkj_` prefix while columns and other object names remain unprefixed?
- Do named indexes and constraints use ordinary `snake_case` and fit target-engine limits?
- Do ORM mappings preserve stable logical property and API names?
- Do foreign keys, migrations, fixtures, seed data, and raw SQL consistently use physical names?
- Is the DDL adapted to the active database engine rather than copied from another dialect?
- Are tenant isolation, upgrade safety, rollback/recovery, and existing data accounted for?
