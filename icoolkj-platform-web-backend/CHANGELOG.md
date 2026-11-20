# Changelog

## 1.1.0 - 2026-11-20

- 增加运行时 SQL 外置和仓储层边界规范。
- 约定 `backend/app/sql/<领域>/`、`backend/app/repositories/<领域>/`、`backend/migrations/sql/` 和 `backend/seeds/sql/` 的职责。
- 明确 Python/SQLAlchemy 默认使用 `.sql`，XML 仅作为已有 XML Mapper 框架的例外。

## 1.0.0 - 2026-11-19

- 新增 icoolkj-platform 多租户 Web 后端技能。
- 从前端技能中拆出 JWT、组织上下文、RBAC、API 契约和服务端隔离规范。
- 明确技能不保存项目用户、角色、权限或历史 SQL 记忆。
