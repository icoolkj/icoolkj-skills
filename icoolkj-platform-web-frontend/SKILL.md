---
name: icoolkj-platform-web-frontend
description: icoolkj-platform 多租户 Web 前端工程与交互设计技能，覆盖 Vue/React 信息架构、菜单、单栏/左右/左中右布局、表格表单、按钮状态、组织范围和响应式验收。当用户要求设计或实现 icoolkj-platform Web 前端、拆分管理菜单、优化页面布局或提交流程时使用。不用于后端授权或数据库建表。
agent_created: true
version: 1.0.0
display_name: icoolkj-platform Web 前端设计
display_name_en: icoolkj-platform Web Frontend
description_zh: icoolkj-platform 多租户 Web 前端工程与交互设计技能，覆盖 Vue/React 信息架构、菜单、单栏/左右/左中右布局、表格表单、按钮状态、组织范围和响应式验收。当用户要求设计或实现 icoolkj-platform Web 前端、拆分管理菜单、优化页面布局或提交流程时使用。不用于后端授权或数据库建表。
description_en: |
  Web frontend information architecture, layout, interaction and usability skill for icoolkj-platform multi-tenant applications. Covers navigation, tables, forms, action states, organization scope and responsive acceptance; it does not implement backend authorization or database schema creation.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
---

# icoolkj-platform Web Frontend

## Purpose

Design and implement clear, efficient Web interfaces for projects that adopt the icoolkj-platform multi-tenant conventions. Treat the current project code, route definitions, API contracts and permission model as the source of product-specific truth. Do not invent fixed business modules from this skill.

## Workflow

1. Inspect the current frontend structure, routes, layout shell, design tokens, API client and permission composables.
2. Identify the user's task, the information hierarchy and the smallest layout that supports it.
3. Map every visible navigation item and action to a real route, state transition or API operation.
4. Design loading, empty, no-permission, validation, conflict and failure states before polishing visuals.
5. Check organization scope changes, stale requests, direct route refresh and responsive behavior.
6. Implement the smallest coherent change and verify the affected build or checks when the project supports them.

## Layout Decision

Choose the smallest layout that preserves context:

- **Single column** for dashboards, focused forms, settings, wizards and simple workflows.
- **Left + right** for master-detail work such as an organization tree with details, a role list with permission editing, or a record list with preview.
- **Left + middle + right** only when the shell has product navigation, at least three stable related second-level destinations, and a persistent work area.

For a three-column shell:

1. The left column contains first-level product modules.
2. The middle column contains only the selected module's second-level routes.
3. The right column contains title, context, primary action and work content.
4. Record selectors and detail panes belong inside the right work area.
5. Derive active state from the router; do not maintain a duplicate hard-coded navigation registry.

Use the detailed decision matrix in [layout-patterns.md](references/layout-patterns.md).

## Navigation and Scope

- Use route metadata as the source for titles, descriptions, breadcrumbs, active state and required capabilities.
- Do not show an action that has no implemented route, API operation or local state transition.
- Keep the current organization or data scope visible near the page heading or toolbar.
- A frontend selector is a usability control, not an authorization boundary.
- On scope change, prevent duplicate switching, invalidate old requests, clear or freeze stale rows, reload dependent data and restore the previous scope on failure.
- Keep session identity, token organization context and page data scope conceptually separate. Backend authorization remains authoritative.

## Forms, Tables and Actions

- Give each work area one clear primary action; demote secondary and destructive actions.
- Use field-level validation for correctable input and preserve user input after a failed request.
- Prevent duplicate submit in both the handler and the UI state.
- Use keyed row loading so one row action does not freeze an entire table.
- Distinguish initial loading, refresh, empty result, filtered no-result, no permission, conflict and API failure.
- Keep confirmation proportional to risk and explain whether an action is reversible.
- Use accessible native or component-library focus behavior; do not replace meaning with decorative animation.

See [button-interaction.md](references/button-interaction.md), [table-form-patterns.md](references/table-form-patterns.md) and [async-workflows.md](references/async-workflows.md).

## Responsive Acceptance

Check wide desktop, medium screens, tablet and narrow mobile widths. A qualifying three-column shell should collapse secondary navigation before the work area becomes unusable. Tables may scroll inside their container; the whole page should not become accidentally horizontal. Direct navigation and refresh must preserve the correct first-level and second-level active state.

Use [visual-qa.md](references/visual-qa.md) and [page-acceptance-checklist.md](templates/page-acceptance-checklist.md) for review.

## Boundaries

- Use `icoolkj-platform-web-backend` for JWT, API authorization, tenant isolation and server-side RBAC.
- Use `icoolkj-platform-web-database` for framework tables, PostgreSQL DDL and migrations.
- Do not place project-specific memories, copied database dumps or historical source SQL into this skill.
