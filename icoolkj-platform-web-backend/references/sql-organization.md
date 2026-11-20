# SQL Storage and Repository Convention

This convention applies to Python and SQLAlchemy-based icoolkj-platform Web backends. It separates SQL text from authorization and orchestration code so developers can locate, review and test queries without searching route handlers.

## Default Directory Layout

```text
backend/
  app/
    repositories/
      identity/
        repository.py
      organization/
        repository.py
    sql/
      identity/
        icoolkj_sys_user.sql
        icoolkj_sys_tenant.sql
        queries/
          authentication.sql
          authorization.sql
      organization/
        icoolkj_sys_dept.sql
        icoolkj_sys_role.sql
        queries/
          employee.sql
          organization.sql
      bootstrap/
        icoolkj_sys_user.sql
        queries/
          initial_data.sql
  migrations/
    sql/
      icoolkj-platform-system-schema.sql
  seeds/
    sql/
      platform-menus.sql
```

The exact domain names may follow the project, but the layers stay separate:

- `app/sql/` contains runtime read and write queries.
- Single-table statements belong in a file named after the physical table, including its framework prefix where applicable.
- Queries that join tables or implement a multi-table business operation belong under `<domain>/queries/`, grouped by business area.
- `app/repositories/` contains SQL loading, parameter binding, transaction boundaries and result mapping.
- `migrations/sql/` contains schema DDL used by versioned migrations.
- `seeds/sql/` contains repeatable or versioned initialization data when the project has a seed subsystem.
- `scripts/sql/` is reserved for operator or maintenance scripts and is never loaded by the application.

## Python and SQLAlchemy Default

Use `.sql` files and a shared loader rooted at `backend/app/sql/`. A table file may contain multiple named blocks:

```sql
-- @id: find_active_user
SELECT id, username
FROM icoolkj_sys_user
WHERE tenant_id = :tenant_id AND id = :user_id
  AND status = '0' AND NOT deleted;

-- @id: update_user_status
UPDATE icoolkj_sys_user
SET status = :status
WHERE tenant_id = :tenant_id AND id = :user_id AND NOT deleted;
```

Use the exact marker form `-- @id: lower_snake_case` at the start of a line. The marker is a block boundary, not SQL syntax: the next marker (or end of file) ends the current query. Semicolons do not split blocks. Keep one executable statement per block; a CTE that forms one statement is fine. Ordinary SQL comments may appear inside a block, but do not put content before the first marker.

The shared loader should:

1. Accept only safe relative `.sql` paths and reject absolute paths and `..` traversal.
2. Read UTF-8 files recursively, including the `queries/` subdirectory, and cache parsed blocks or source text.
3. Index each block by its `@id` and reject malformed markers, empty blocks, duplicate IDs within a file and duplicate IDs across the same repository domain.
4. Fail during repository initialization for discovered malformed files or duplicate IDs, and raise a clear error when a call requests an ID that has no matching block. If the project needs missing-query detection at startup, maintain an explicit expected-ID manifest and validate it there.
5. Pass values separately through named SQLAlchemy bind parameters; never interpolate user input into SQL.

Repository methods can retain operation-oriented calls such as `repository.all(db, "find_active_user", params)`. The `@id` must resolve to exactly one block in that repository domain. The example is generic; use the actual project schema and API contract rather than copying it verbatim.

Do not place a query back into a route or service just because it is short. Services coordinate multi-table writes with the established transaction boundary and call the relevant repository operations; do not combine unrelated writes merely to reduce file count.

## XML Exception

XML is allowed only when the selected persistence framework already uses XML mappers, such as a MyBatis-compatible stack. In that case:

- Store XML under `backend/app/sql/<domain>/`.
- Keep one mapper namespace per repository aggregate.
- Keep statement ids stable and named by operation.
- Keep tenant and authorization predicates inside the mapped statement.
- Do not mix XML mapper statements and free-standing `.sql` files for the same repository without a documented reason.

For SQLAlchemy, do not add XML solely to externalize SQL. `.sql` files are easier to inspect, run against PostgreSQL and validate with the existing toolchain.

## File and Parameter Naming

- Name a single-table file exactly after its physical table, such as `icoolkj_sys_user.sql` or `icoolkj_sys_role_menu.sql`.
- Name files under `queries/` after a business area, such as `authentication.sql`, `employee.sql` or `organization.sql`.
- Name each `@id` after its operation using lowercase `snake_case`, such as `find_user_by_username`, `list_employee_roles` or `insert_user_role`.
- Do not create one file per query by default and do not add unused CRUD blocks; one table file can hold only the operations the project actually needs.
- Use named parameters such as `:tenant_id`, `:user_id` and `:role_id`.
- Use SQL aliases that match the API or repository result contract, such as `employee_name AS name`.
- Keep comments limited to intent, scope assumptions or PostgreSQL-specific behavior. Do not store credentials, environment values or historical business notes in SQL files.
- Never use string interpolation or concatenation for values. Dynamic table names, column names and sort expressions must come from a fixed allow-list in Python.

## Authorization and Tenant Safety

Externalizing SQL does not move authorization out of the backend. Every business query must be reviewed for:

- `tenant_id` filtering on every tenant-owned table.
- Organization scope filtering for the active organization and allowed descendants.
- `deleted` and `status` predicates where the schema uses soft deletion or lifecycle status.
- Ownership and relation checks before inserts, updates, deletes or role assignments.
- Stable result cardinality and null behavior for the API contract.

Repository methods must not accept a raw client-provided scope as sufficient authorization. The caller passes a server-resolved tenant or organization context after the policy dependency has run.

## Review Checklist

- Is a true single-table operation in the table-named file, and is a join or cross-table business query under `queries/`?
- Does every executable block have one valid, unique `@id`, and does the repository load nested query files?
- Is the repository query ID easy to find from the operation name?
- Are all values bound parameters and all dynamic identifiers allow-listed?
- Does the query enforce tenant, organization, lifecycle and soft-delete scope?
- Do result aliases and cardinality match the API schema?
- Are write queries covered by transaction and conflict handling tests?
- Is migration DDL kept under `migrations/sql/` instead of runtime SQL?
- If XML is used, is there an existing XML mapper framework that justifies it?
