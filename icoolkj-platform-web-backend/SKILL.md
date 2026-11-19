---
name: icoolkj-platform-web-backend
description: icoolkj-platform 多租户 Web 后端工程技能，覆盖 JWT 身份认证、组织租户上下文、RBAC、API 契约、数据范围、审计和服务端隔离。当用户要求实现或审查登录、权限、组织切换、多租户隔离或接口保护时使用。不用于前端视觉布局或数据库基线建表。
agent_created: true
version: 1.0.0
display_name: icoolkj-platform Web 后端
display_name_en: icoolkj-platform Web Backend
description_zh: icoolkj-platform 多租户 Web 后端工程技能，覆盖 JWT 身份认证、组织租户上下文、RBAC、API 契约、数据范围、审计和服务端隔离。当用户要求实现或审查登录、权限、组织切换、多租户隔离或接口保护时使用。不用于前端视觉布局或数据库基线建表。
description_en: |
  Backend authentication, organization context, RBAC, API contracts, data scope and server-side isolation skill for icoolkj-platform multi-tenant Web applications. It does not define frontend visual layouts or the database baseline.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
---

# icoolkj-platform Web Backend

## Purpose

Implement and review the server-side contracts that make a multi-tenant Web application safe and understandable. Inspect the current project's framework, models, migrations, middleware, route handlers and deployed schema before changing behavior. This skill provides framework rules, not a copy of any project's users, roles or business data.

## Request Workflow

1. Inspect authentication middleware, token creation and verification, current-user endpoints, organization membership checks and route dependencies.
2. Identify the resource tenant, organization hierarchy, actor identity and requested data scope for every operation.
3. Define success, validation, authentication, authorization, not-found, conflict and server-error responses.
4. Apply authorization at the service or policy boundary, not only in route visibility or frontend menus.
5. Add audit or revocation behavior when the operation changes access, identity, organization membership or sensitive data.
6. Update API documentation, tests or migration references that are part of the existing project workflow.

## Identity and JWT

- Distinguish the authenticated user, token claims, active organization context and requested page or query scope.
- Verify signature, expiry, issuer, audience and required claims according to the project's token policy.
- Keep access tokens short-lived and use the project's established refresh or reauthentication flow; do not invent browser storage behavior in backend code.
- Resolve the current user from server-side state when needed. A valid token alone does not prove the account is active or still a member of the organization.
- Return consistent `401` behavior for missing, invalid or expired credentials. Do not reveal whether a credential partially matched.

## Organization and Tenant Isolation

- Resolve the tenant and organization context from trusted server-side claims, membership checks and route parameters together.
- Never use a client-provided organization id as authorization by itself.
- Check that the actor can access the target organization, including parent/child scope rules defined by the project.
- Apply tenant predicates in every list, detail, update, delete, relation and aggregate query.
- Validate that related users, roles, departments, posts and resources belong to a compatible scope before linking them.
- Treat organization switching as a server operation when it changes token permissions; issue the resulting context through the established token flow.

See [auth-scope-rbac.md](references/auth-scope-rbac.md) for the detailed context model.

## RBAC and API Contracts

- Model page access, action permission and data scope separately.
- Enforce permissions on the backend even when the frontend hides an action.
- Keep global roles, organization roles, inherited permissions and read-only roles distinct.
- Use stable permission codes and document which endpoint and action each code protects.
- Use `403` for an authenticated actor without permission, `404` when the resource should not be disclosed or does not exist according to project policy, `409` for state or uniqueness conflicts, and `422` for correctable request validation.
- Keep response shapes, pagination, filtering, sorting and error fields stable across related endpoints.
- Use [permission-matrix.md](templates/permission-matrix.md) to review route, action and data-scope coverage.

## Change Safety

- Do not create a parallel identity, tenant or RBAC source when the project already has one.
- Do not bypass the active migration system with ad hoc production DDL.
- Preserve existing data and provide a compatibility or migration plan for changes to claims, scope rules, permission codes or resource ownership.
- Review logs and audit records for sensitive operations, while avoiding secrets and raw tokens in logs.

## Boundaries

- Use `icoolkj-platform-web-frontend` for navigation, layout, form states and responsive behavior.
- Use `icoolkj-platform-web-database` for the framework PostgreSQL baseline, naming rules and table creation.
- Do not embed a project's historical SQL, copied environment values or remembered business structure in this skill.
