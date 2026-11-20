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
        find_login_user.sql
        list_user_roles.sql
      organization/
        list_employees.sql
        list_organization_tree.sql
      rbac/
        list_roles.sql
        update_role_permissions.sql
  migrations/
    sql/
      icoolkj-platform-system-schema.sql
  seeds/
    sql/
      platform-menus.sql
```

The exact domain names may follow the project, but the layers stay separate:

- `app/sql/` contains runtime read and write queries.
- `app/repositories/` contains SQL loading, parameter binding, transaction boundaries and result mapping.
- `migrations/sql/` contains schema DDL used by versioned migrations.
- `seeds/sql/` contains repeatable or versioned initialization data when the project has a seed subsystem.
- `scripts/sql/` is reserved for operator or maintenance scripts and is never loaded by the application.

## Python and SQLAlchemy Default

Use a small shared loader so every repository resolves SQL relative to one known root. The loader should:

1. Accept a relative path such as `organization/list_employees.sql`.
2. Reject absolute paths and `..` traversal.
3. Read UTF-8 text and fail during application startup or repository construction when the file is missing.
4. Cache immutable SQL text after the first read.
5. Return SQL text only; parameter values remain in Python and are passed through SQLAlchemy bind parameters.

Repositories should make the query location obvious:

```python
LIST_EMPLOYEES_SQL = load_sql("organization/list_employees.sql")

def list_employees(db: Session, *, tenant_id: str, organization_id: str):
    return db.execute(
        text(LIST_EMPLOYEES_SQL),
        {"tenant_id": tenant_id, "organization_id": organization_id},
    ).mappings().all()
```

The example is a location and binding pattern, not a project-specific implementation. Do not place the query back into a route or service just because it is short.

## XML Exception

XML is allowed only when the selected persistence framework already uses XML mappers, such as a MyBatis-compatible stack. In that case:

- Store XML under `backend/app/sql/<domain>/`.
- Keep one mapper namespace per repository aggregate.
- Keep statement ids stable and named by operation.
- Keep tenant and authorization predicates inside the mapped statement.
- Do not mix XML mapper statements and free-standing `.sql` files for the same repository without a documented reason.

For SQLAlchemy, do not add XML solely to externalize SQL. `.sql` files are easier to inspect, run against PostgreSQL and validate with the existing toolchain.

## File and Parameter Naming

- Use lowercase `snake_case` file names: `find_user_by_username.sql`, `list_employee_roles.sql`, `insert_user_role.sql`.
- Start with the operation: `find`, `list`, `count`, `insert`, `update`, `delete`, `assign`, `remove` or `exists`.
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

- Is the query in `app/sql/<domain>/` rather than a route or service module?
- Is the repository path easy to find from the domain and operation name?
- Are all values bound parameters and all dynamic identifiers allow-listed?
- Does the query enforce tenant, organization, lifecycle and soft-delete scope?
- Do result aliases and cardinality match the API schema?
- Are write queries covered by transaction and conflict handling tests?
- Is migration DDL kept under `migrations/sql/` instead of runtime SQL?
- If XML is used, is there an existing XML mapper framework that justifies it?
