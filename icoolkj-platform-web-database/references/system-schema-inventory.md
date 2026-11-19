# Mandatory System Table Inventory

Every project using this skill initializes all 33 tables from [system-schema.postgresql.sql](system-schema.postgresql.sql), regardless of which feature is being delivered first. This inventory is for orientation; the PostgreSQL DDL is the structure authority.

| Domain | Required tables |
| --- | --- |
| Tenant and organization | `icoolkj_sys_tenant`, `icoolkj_sys_dept`, `icoolkj_sys_region` |
| Identity and access | `icoolkj_sys_user`, `icoolkj_sys_user_password_history`, `icoolkj_sys_user_preference`, `icoolkj_sys_role`, `icoolkj_sys_user_role`, `icoolkj_sys_user_post`, `icoolkj_sys_post`, `icoolkj_sys_role_dept`, `icoolkj_sys_role_region`, `icoolkj_sys_role_menu`, `icoolkj_sys_menu` |
| Configuration and localization | `icoolkj_sys_config`, `icoolkj_sys_dict_type`, `icoolkj_sys_dict_item`, `icoolkj_sys_i18n_locale`, `icoolkj_sys_i18n_message`, `icoolkj_sys_product`, `icoolkj_sys_brand_pack` |
| Platform features | `icoolkj_sys_ai_skill`, `icoolkj_sys_banner`, `icoolkj_sys_ip_access_rule`, `icoolkj_sys_job`, `icoolkj_sys_job_log`, `icoolkj_sys_notice` |
| Audit history | `icoolkj_sys_login_log`, `icoolkj_sys_login_log_archive`, `icoolkj_sys_operation_log`, `icoolkj_sys_operation_log_archive` |
| Messaging | `icoolkj_sys_site_message`, `icoolkj_sys_site_message_recipient` |

## Initialization Rules

- Initialize the full table set, not only the rows above a feature area.
- Apply schema through the project's versioned database migration system. Container entrypoint initialization can support a fresh local volume, but is not a substitute for migrations on existing deployments.
- Preserve all columns, primary and unique keys, indexes, defaults, table/column comments, and timestamp-update triggers from the PostgreSQL reference.
- Keep the application's PostgreSQL/pgvector stack and extension bootstrap. Apply the bundled PostgreSQL DDL rather than an external or historical SQL export.
- Add project-specific business tables after the baseline. Prefix each new physical table name with `icoolkj_`; keep column, index, constraint, trigger, and function names unprefixed.
- If an existing codebase already has identity, tenant, department, role, or menu tables, plan compatibility and data convergence; do not silently maintain two competing sources of truth.
- The reference contains schema only: it does not create demo users, roles, menus, dictionaries, or other seed rows.

## Completion Check

After migration, query the target database catalog and confirm all 33 listed names exist, with no same-purpose legacy duplicate introduced by the feature. Test both clean initialization and upgrade from the prior supported revision.
