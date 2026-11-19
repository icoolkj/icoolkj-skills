---
name: pharmamind-frontend-design
description: |
  PharmaMind-AI 前端信息架构与交互设计技能，面向 Vue 3 + Element Plus 页面、菜单、后台工作流、表格、表单、仪表盘、按钮行为和响应式体验的规划与实现。
  当用户要求优化 PharmaMind 前端界面、拆分管理菜单、设计单栏/左右/左中右布局、改善按钮流程或提升页面可用性时使用本技能。
agent_created: true
version: 1.2.0
display_name: PharmaMind-AI 前端界面规划
display_name_en: PharmaMind-AI Frontend Design
description_zh: |
  PharmaMind-AI 前端信息架构、导航布局和业务交互设计技能，支持按任务复杂度选择单栏、左右或左中右布局。
description_en: |
  Frontend information architecture, navigation layout and interaction design skill for PharmaMind-AI. Chooses single-column, two-column or three-column patterns based on the user's task.
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

Use this skill for frontend implementation and for planning a frontend change. Read the relevant current components, routes, API calls, and styles before choosing a layout.

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

## Organization Scope

Organization scope is a shared context, not a separate business module.

- Keep the current organization selector in the administration shell or the page toolbar.
- Persist the selected organization only as a convenience; never treat browser storage as an authorization boundary.
- Reload all organization-scoped data after the scope changes.
- Clear stale lists while loading the new scope so users cannot act on the previous organization's rows.
- Show the current scope near the page title and explain that the backend remains authoritative.
- Preserve the backend's organization and permission checks; frontend visibility is only a usability layer.

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

## Implementation Workflow

1. Inspect current routes, page components, shared styles, API contracts, authorization rules, and nearby patterns.
2. Inventory the task's navigation and actions. For each action, record its intent, frequency, risk, API support, and async/error behavior.
3. Choose the smallest suitable layout and define route metadata/navigation state before page markup.
4. Implement one complete primary workflow using existing Vue and Element Plus patterns; add shared abstractions only for behavior that is genuinely repeated.
5. Verify loading, empty, validation, failure, success, permission, and organization-scope behavior where relevant.
6. Check desktop, medium, and mobile widths, keyboard/focus behavior, reduced motion, and content overlap.
7. Run the focused frontend build or tests. For Docker-delivered frontend changes, run the frontend image build when Docker is available.

## Review Checklist

- Does the layout match the task instead of applying a fixed template?
- Is first-level navigation separate from second-level navigation?
- Is the current route visibly active after direct navigation and refresh?
- Does the right-side work area have one clear primary action?
- Does organization scope remain visible and reload data safely?
- Does every visible action map to an implemented route or API operation?
- Do forms, tables, dialogs, and feedback reflect the API's actual capabilities?
- Are loading and stale-data races handled when switching scope or route?
- Do async actions prevent duplicate submission and preserve input on failure?
- Are destructive actions explicit, keyboard-accessible, and consistent with backend reversibility?
- Are focus and reduced-motion behavior usable without decorative animation?
- Does the page remain usable at mobile width?
- Does the frontend build pass without introducing an unrelated dependency or visual system?
