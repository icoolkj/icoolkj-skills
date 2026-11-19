---
name: pharmamind-frontend-design
description: |
  PharmaMind-AI 前端工程与交互设计技能，面向 Vue 3 + Element Plus 的信息架构、认证组织上下文、RBAC 菜单、后台工作流、表格、表单、按钮行为、数据库契约对齐和响应式验收。
  当用户要求优化 PharmaMind 前端、拆分管理菜单、对齐 API 或数据库结构、设计单栏/左右/左中右布局、改善提交流程或检查页面可用性时使用本技能。
agent_created: true
version: 1.5.0
display_name: PharmaMind-AI 前端界面规划
display_name_en: PharmaMind-AI Frontend Design
description_zh: |
  PharmaMind-AI 前端信息架构、导航布局、业务交互和数据库契约对齐技能，包含必须初始化的 PostgreSQL 系统表基线，并支持按任务复杂度选择单栏、左右或左中右布局。
description_en: |
  Frontend information architecture, navigation layout, interaction design and database contract alignment skill for PharmaMind-AI. Includes a mandatory PostgreSQL system-schema baseline and preserves schema/API compatibility.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
---

# PharmaMind Frontend Design

## Purpose

Make PharmaMind feel like a focused enterprise quality-management product: dense enough for repeated operational work, clear enough for new users, and consistent across organization, identity, knowledge, document, training, and Agent modules.

Use this skill for frontend implementation, planning, and alignment audits. Read the relevant current components, routes, API calls, authorization dependencies, database models/migrations when data changes are involved, and styles before choosing a layout or exposing an action.

## Core Design Decision

Choose the smallest layout that supports the task. Do not force every page into three columns.

- **Single column**: dashboards, guided forms, simple settings, placeholder modules, and workflows with one primary task.
- **Left + right**: master-detail work, such as a role list with permission details, organization tree with node details, or document list with preview.
- **Left + middle + right**: modules with a stable global product navigation, a persistent group of 3 or more related secondary functions, and a right-side work area. Use this for platform administration and other high-frequency module navigation.

When a three-column layout is used:

1. The left column contains first-level product modules only.
2. The middle column contains the selected module's second-level navigation only.
3. The right column contains the current page title, scope/context controls, primary actions, and content.
4. Do not duplicate the same navigation in both the left sidebar and the page body.
5. Keep the middle column stable while the right content changes.

See [layout-patterns.md](references/layout-patterns.md) for the detailed decision matrix.

## PharmaMind Information Architecture

Treat these as product-level first-level modules unless the existing product direction changes:

- 工作台
- 组织与权限
- 质量知识库
- 质量文件中心
- 培训与考试
- 培训档案
- AI Agent 接入

For 组织与权限, use these second-level destinations:

- 组织架构
- 部门与岗位
- 员工账号
- 角色与权限

Use route metadata as the source of truth for page titles, descriptions, breadcrumbs, and active navigation. A menu item must map to a real route, and a route refresh must preserve the same active state.

Do not maintain a second hard-coded navigation registry in the shell when route metadata can provide the same information. Every protected route should declare the permission or capability needed to enter it; the backend remains the final authority.

## Organization Scope

Organization scope is a shared context, not a separate business module.

- Keep the current organization selector in the administration shell or the page toolbar.
- Persist the selected organization only as a convenience; never treat browser storage as an authorization boundary.
- Reload all organization-scoped data after the scope changes.
- Clear stale lists while loading the new scope so users cannot act on the previous organization's rows.
- Show the current scope near the page title and explain that the backend remains authoritative.
- Preserve the backend's organization and permission checks; frontend visibility is only a usability layer.
- Keep session identity, JWT active organization, and page data scope as separate concepts. A local-storage selection may restore convenience, but it must not silently change authorization context.
- Bootstrap the session with the current-user endpoint when the app starts. Handle expired tokens, 401 logout, 403 forbidden state, and organization-switch failures consistently.
- When organization context changes, invalidate or cancel old requests before loading new data. Never leave rows from the previous scope actionable while the new scope is loading.

See [auth-scope-rbac.md](references/auth-scope-rbac.md) for the session, organization, and permission contract.

## Database Schema Alignment

When this skill is applied to a project, its complete 33-table system baseline in [system-schema.postgresql.sql](references/system-schema.postgresql.sql) is mandatory. Initialize every baseline table even when the first feature uses only a subset; feature-specific tables are additive. Use PostgreSQL/pgvector, not the MySQL source DDL.

- Treat the supplied `icoolkj.sql` as the domain schema source and its PostgreSQL file as the executable target-dialect baseline. Keep all 33 system tables and their full column/index/default/comment structure; do not hand-pick a minimal subset or replace the baseline with parallel user, tenant, role, or organization tables.
- Prefix physical table names only: `sys_user` becomes `icoolkj_sys_user`. Keep column names, index names, constraint names, trigger names, and function names in ordinary lowercase `snake_case` without an `icoolkj_` prefix.
- Keep application-facing ORM attributes and API fields idiomatic and stable. SQLAlchemy attributes such as `id` and `tenant_id` should map directly to columns with those same names; do not add a storage prefix to fields or JSON contracts.
- Update foreign-key targets, unique constraints, indexes, seed data, raw SQL, tests, and migration references together. Review tenant-scoped uniqueness and query indexes as part of the schema, not as a later UI fix.
- Apply the full baseline through the active project's versioned migration system. Docker init scripts alone are insufficient for an already initialized volume. Retain the existing pgvector/pgcrypto bootstrap and add no duplicate system tables under legacy names.
- For an existing database, reconcile its models and deployed data first. Map existing features to these canonical system tables and stage any convergence migration; do not drop data, blindly rename deployed identifiers, or create competing identity/RBAC sources.
- The supplied schema defines no foreign keys and contains no `INSERT` seed rows. Preserve that fact in the baseline; add referential constraints or seed records only when separately designed and explicitly specified.
- Preserve source semantics during dialect conversion: JSON becomes `jsonb`, `mediumtext` becomes `text`, Boolean flags become PostgreSQL `boolean`, and MySQL `ON UPDATE` timestamps use PostgreSQL triggers. Review MySQL case/accent-insensitive collations and PostgreSQL uniqueness/search behavior before relying on equivalent comparisons.
- Keep vector/pgcrypto extension setup required by the application. The system-table baseline does not replace or remove those extensions.
- Check identifier length and case behavior for the target engine. Shorten long constraint/index names deterministically and verify that generated names remain unique.
- A naming prefix provides a project namespace, not legal copyright protection. Keep ownership evidence in the repository license, copyright notice, and project records; do not treat a database prefix as a substitute.

See [database-schema-conventions.md](references/database-schema-conventions.md) for the naming map, full table inventory, and migration checklist.

## API Contract Alignment

Before adding a button, inspect the complete API contract: route, method, request/response shape, permission dependency, organization-scope check, conflict behavior, and audit/reversibility rules.

- Do not infer frontend permission behavior from URL names alone; inspect backend authorization dependencies.
- Check that list, detail, create, update, assign, unassign, and delete operations have symmetric semantics before presenting them as a complete workflow.
- Treat global/system roles, inherited permissions, and organization roles as distinct states in the UI.
- Map 401, 403, 404, 409, 422, timeout, and network failures to different recovery guidance where the product can act on them.
- Keep a permission matrix or generated contract close to the route configuration. Do not let permission codes drift between frontend labels, backend seed data, and API checks.

## Async Workflows

Use a small explicit state model rather than scattered booleans. A page may need independent states for initial load, refresh, submit, row action, permission load, and scope change.

- Disable only the action that would duplicate the in-flight request; do not freeze unrelated navigation.
- Guard handlers as well as button props so keyboard submit and rapid events cannot bypass the lock.
- Use request ids or cancellation for changing route, organization, selected row, or selected role. Ignore stale responses.
- On failure, restore retryability and preserve user input. On success, update the local baseline from the server result before showing confirmation.
- Render loading, empty, error, retry, permission-denied, and stale-data states deliberately. A spinner alone is not a page state design.

See [async-workflows.md](references/async-workflows.md) for Vue and Element Plus patterns.

## Tables and Forms

Tables are the main surface for repeated work, but their behavior must scale with the data set.

- Small static dictionaries may use a simple list. Employee, document, audit, and training records should plan for search, filters, pagination, sorting, and stable action columns.
- Use field-level `el-form` validation and map server validation responses back to fields when possible. Keep backend validation authoritative.
- Preserve filters and pagination when refreshing a row action; reset them only when organization or query context changes.
- Distinguish no records, no matching records, no permission, failed loading, and not-yet-implemented states.
- Keep row actions independently loading and make bulk actions explicit about selection and scope.

See [table-form-patterns.md](references/table-form-patterns.md) for the decision rules.

## Interaction Rules

- Give each page one obvious primary action in the upper-right toolbar.
- Put create and edit forms in dialogs or dedicated pages when the form is longer than a few fields; do not stack unrelated forms above a table.
- Keep tables as the main surface for repeated operations. Add search, filters, empty states, loading states, and meaningful columns before adding decorative panels.
- Match each control to its intent: navigation navigates, selection selects, and a button performs an action. Do not render an action until its route or API behavior exists.
- Use one primary action per work area; keep secondary actions visually quieter and destructive actions explicit.
- For asynchronous actions, show loading and prevent duplicate submission. On failure, restore the action, keep the user's input, and explain how to recover.
- On success, update the affected view and use concise nearby feedback. Do not require a success animation or a persistent checkmark.
- Confirm destructive or high-impact actions with the target and consequence stated clearly. Prefer reversible operations where the backend supports them.
- Keep permission-dependent actions hidden or disabled based on known user context, while retaining server-side authorization.
- Use familiar icons with visible labels for important actions; icon-only controls need accessible labels and tooltips.
- Preserve user input when validation fails. Explain the field-level problem instead of showing only a generic error.
- Use native Element Plus button behavior first. Define only the states relevant to each action; an error is feedback around a failed request, not a button mode that remains stuck.
- Keep focus visible, support keyboard activation, and respect `prefers-reduced-motion`. Use brief state transitions; omit decorative motion from frequent navigation and table actions.
- Treat spring, magnetic hover, loading morphs, long-press and ripple as opt-in experiments, never product defaults. See [button-interaction.md](references/button-interaction.md) for the default contract and optional motion catalog.

## Visual System

Follow the existing Vue 3 + Element Plus stack and project visual language. Prefer restrained enterprise styling over marketing composition.

- Use a neutral page background, white work surfaces, dark blue navigation, and teal as a focused action/accent color.
- Use an 8px spacing rhythm where practical; keep content sections aligned to a shared grid.
- Keep border radii modest and avoid nested cards. Use panels for genuinely framed work areas, not every page section.
- Use typography hierarchy for scanning: page title, supporting description, section title, table metadata, and muted helper text.
- Keep labels concise and consistent in Chinese. Use the same term for the same concept across route, menu, page, API error, and button text.
- Use Element Plus components already present in the project before introducing a new UI dependency.

## Responsive Behavior

- Desktop administration: left first-level navigation, optional middle second-level navigation, flexible right work area.
- Medium width: keep the left navigation usable and reduce the middle column width; avoid allowing tables to collapse into unreadable text.
- Mobile: collapse or convert the left navigation to a drawer, move second-level navigation to a compact top selector or horizontal tabs, and keep the right work area single-column.
- Keep action buttons reachable and labels inside their controls at all supported widths.
- Set stable widths or min-widths for table actions, selectors, toolbars, and icon buttons so content cannot shift the layout.
- Verify the real implementation at wide desktop, medium tablet, and narrow mobile widths. A rule that says "use a drawer" is incomplete until the drawer, close behavior, focus return, and active route are implemented.

## Implementation Workflow

1. Inspect current routes, page components, shared styles, API contracts, authorization rules, nearby patterns, and database models/migrations if persisted data changes.
2. Produce a short capability inventory: implemented, placeholder, missing API, permission-gated, and unsafe-to-expose actions.
3. Inventory each action's intent, frequency, risk, API support, organization scope, and async/error behavior.
4. Choose the smallest suitable layout and define route metadata, permission metadata, and navigation state before page markup.
5. Define session and organization context behavior before adding organization-scoped data or switching controls.
6. Implement one complete primary workflow using existing Vue and Element Plus patterns; add shared abstractions only for behavior that is genuinely repeated.
7. Verify loading, empty, validation, failure, success, permission, conflict, and organization-scope behavior where relevant.
8. Check wide, medium, and narrow viewports, keyboard/focus behavior, reduced motion, and content overlap.
9. Run focused frontend build/tests and the relevant backend contract tests. For Docker-delivered frontend changes, run the frontend image build when Docker is available.

Use the templates in [templates/](templates/) when a change involves multiple routes, permissions, or acceptance states.

## Review Checklist

- Does the layout match the task instead of applying a fixed template?
- Is first-level navigation separate from second-level navigation?
- Is the current route visibly active after direct navigation and refresh?
- Does the right-side work area have one clear primary action?
- Does organization scope remain visible and reload data safely?
- Are session identity, JWT organization, and page data scope modeled separately?
- Does every protected route declare its required capability and handle direct unauthorized navigation?
- Does every visible action map to an implemented route or API operation?
- Do forms, tables, dialogs, and feedback reflect the API's actual capabilities?
- Were the backend permission dependency and organization membership checks inspected for each new action?
- Is the complete 33-table PostgreSQL baseline initialized, with app-specific tables only added on top?
- Do only physical table names use `icoolkj_`, with columns and other database object names unprefixed?
- Does the versioned migration match PostgreSQL/pgvector and preserve deployed data?
- Are loading and stale-data races handled when switching scope or route?
- Do async actions prevent duplicate submission and preserve input on failure?
- Are no-results, no-permission, API failure, conflict, and not-implemented states distinct?
- Are destructive actions explicit, keyboard-accessible, and consistent with backend reversibility?
- Are focus and reduced-motion behavior usable without decorative animation?
- Does the page pass the viewport and keyboard checks in [visual-qa.md](references/visual-qa.md)?
- Does the frontend build pass without introducing an unrelated dependency or visual system?
