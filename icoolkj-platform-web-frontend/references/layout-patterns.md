# icoolkj-platform Layout Patterns

Choose the smallest layout that preserves the user's task context. Column count is a consequence of information architecture, not a visual target.

## Single Column

Use for one primary task, a short form, login/settings, a dashboard summary, a wizard, or a module that is still a placeholder.

Order content as: page title and purpose, one action toolbar if needed, primary content, then contextual loading/empty/validation/result feedback. Do not split a short form or small list just to fill space.

## Left + Right

Use when the user selects a record or category and works on its detail.

Examples: role list + permission editor; organization tree + selected-node details; knowledge items + document preview; training tasks + task configuration.

Keep the selector pane around 280–360px on wide desktop, with a flexible detail pane and a readable minimum width. The detail pane owns the selected item's title and primary action. On narrow layouts, stack or use a compact selector; do not preserve side-by-side panes at the expense of readable content.

## Left + Middle + Right

Use only if the application shell has three persistent jobs at once: product-level navigation, at least three related module destinations used repeatedly, and the current work area.

```text
Left: product modules | Middle: selected module destinations | Right: current page and work
```

- Left contains first-level product modules only.
- Middle contains second-level route navigation only; it is not a dashboard, filter panel, or record list.
- Right contains the page title, organization/task context, primary action, and page content.
- Keep each navigation destination linked to a real route and derive its active state from the router.
- Do not duplicate the middle menu in the right page body.
- Put record-level master/detail panes inside the right work area; do not confuse those panes with the app's middle navigation.

Use a middle navigation only when the current product module has at least three stable, related destinations that users switch between repeatedly. Do not automatically add a middle navigation to every module.

## Choosing the Pattern

1. Identify the user's task and frequency before counting screens.
2. Count stable destinations the user switches between in the same module. Fewer than three usually means no middle navigation.
3. If the user must select an entity before editing it, add a left + right master/detail region inside the page.
4. If the task is a wizard, focused form, or one-off action, use a focused single-column page even when launched from a three-column shell.
5. Verify each column has a distinct job. Remove any column that only repeats context or decorates the page.

## Generic Administration Example

```text
Product modules     Organization & access       Current work area
Dashboard           Organization                Organization tree + details
Administration      Departments and posts       Directory tables + create action
Knowledge           User accounts                User list + account action
Documents           Roles and permissions        Role list + permission editor
```

The organization scope is shared context for admin pages, not another menu level. Display it once near the right page heading/toolbar. Keep its meaning explicit: a data-management filter is not the same thing as changing the authentication token's active organization.

## Responsive Behavior

- Wide desktop (about 1200px and above): use three columns only for qualifying modules; preserve a useful right work width.
- Medium screens (about 760–1199px): keep product navigation usable and move qualifying secondary navigation to a compact horizontal row or rail above the work area.
- Narrow screens (below about 760px): collapse product navigation into a drawer or compact menu; expose second-level destinations as a compact selector or scrollable tabs.
- In-page master/detail panes stack or switch to a selector when side-by-side content becomes cramped.
- Keep primary actions reachable; table content may scroll horizontally, but do not force the whole page to scroll sideways.
