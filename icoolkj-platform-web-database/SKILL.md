---
name: icoolkj-platform-web-database
description: icoolkj-platform 多租户 Web 数据库技能，覆盖框架系统表创建、PostgreSQL/pgvector 基线 DDL、表命名、租户隔离、迁移、索引和初始化校验。当用户要求创建系统表、编写 PostgreSQL DDL、设计迁移或规范多租户表结构时使用。不用于前端布局或项目业务需求猜测。
agent_created: true
version: 1.0.0
display_name: icoolkj-platform Web 数据库
display_name_en: icoolkj-platform Web Database
description_zh: icoolkj-platform 多租户 Web 数据库技能，覆盖框架系统表创建、PostgreSQL/pgvector 基线 DDL、表命名、租户隔离、迁移、索引和初始化校验。当用户要求创建系统表、编写 PostgreSQL DDL、设计迁移或规范多租户表结构时使用。不用于前端布局或项目业务需求猜测。
description_en: |
  Database skill for the icoolkj-platform multi-tenant Web framework, including PostgreSQL/pgvector baseline DDL, system table creation, naming, tenant isolation, migrations and initialization checks.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
---

# icoolkj-platform Web Database

## Purpose

Create and evolve the database foundation required by projects that adopt the icoolkj-platform multi-tenant Web framework. The PostgreSQL file in [system-schema.postgresql.sql](references/system-schema.postgresql.sql) is the framework's canonical executable baseline. Project-specific extensions belong in the adopting project's migrations and architecture documentation.

## Required Baseline

- Use PostgreSQL as the framework database and preserve the project's pgvector and pgcrypto bootstrap when those extensions are enabled.
- Initialize the complete system-table baseline from the bundled PostgreSQL DDL through the project's versioned migration mechanism.
- Keep the baseline as the shared source for authentication, tenants, organizations, departments, roles, menus, configuration, audit and messaging support.
- Add application business tables on top of the baseline after checking for an existing framework table with the same responsibility.
- The baseline DDL is schema only. It does not create demo accounts, roles, menus, dictionaries or other seed data.
- Treat the bundled DDL as the canonical PostgreSQL target; document approved deviations in the adopting project's migrations and architecture records.

Use [system-schema-inventory.md](references/system-schema-inventory.md) to understand the baseline table groups.

## Naming Contract

- Prefix physical table names with exactly one `icoolkj_` prefix.
- Keep column, index, primary key, foreign key, unique constraint, check constraint, trigger and function names in ordinary lowercase `snake_case` without the prefix.
- Use stable names such as `icoolkj_sys_user`, `id`, `tenant_id`, `pk_sys_user` and `idx_sys_user_tenant_id`.
- Keep ORM attributes and API fields idiomatic; map them to the same unprefixed column names unless the project has an explicit compatibility contract.
- Apply the same table prefix to new framework or application tables that belong to the project namespace.

The complete naming rules and mapping examples are in [database-schema-conventions.md](references/database-schema-conventions.md).

## Migration Workflow

1. Inspect the current database, ORM models, migrations, extensions, seed process and deployment environment.
2. Compare the live structure with the framework baseline before applying changes; record conflicts instead of silently choosing a side.
3. Add the baseline through a versioned migration or the project's approved initialization path.
4. Preserve existing data and deployment history. Do not use `drop_all`, broad renames or destructive recreation on an initialized environment.
5. Add tenant predicates, tenant-aware uniqueness, ownership checks and query indexes for application tables.
6. Validate a clean initialization and an upgrade path in an isolated database or transaction where supported.
7. Query the PostgreSQL catalog to confirm table names, columns, indexes, constraints, triggers and extensions.

## PostgreSQL Rules

- Use PostgreSQL types and syntax directly in the executable DDL.
- Define nullability, defaults, primary keys, unique rules, indexes, lifecycle fields and update behavior explicitly.
- Add foreign keys or row-level security only when the current framework/application policy requires them; do not claim they exist if the baseline does not define them.
- Keep timestamp and timezone behavior explicit at the schema and API boundary.
- Review identifier length and case behavior before generating names.
- Keep vector columns and vector indexes in application-specific migrations unless they are explicitly added to the framework baseline.

## Verification Checklist

- The migration targets PostgreSQL and runs on a clean database.
- All baseline tables are present exactly once under their `icoolkj_` names.
- Columns and non-table objects do not accidentally receive the `icoolkj_` prefix.
- No project-specific user, tenant or RBAC duplicate competes with the framework tables.
- Tenant-scoped reads and writes enforce the same scope rules as the backend policy.
- A failed migration leaves the database recoverable and does not destroy existing data.

## Boundaries

- Use `icoolkj-platform-web-frontend` for page layout and organization selector behavior.
- Use `icoolkj-platform-web-backend` for authorization, API policies and service-layer isolation.
- Keep project-specific schema decisions in that project's migrations and architecture documentation, not in this reusable skill.
