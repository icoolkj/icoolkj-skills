# Changelog

## 1.0.0 - 2026-11-19

- 新增 icoolkj-platform 多租户 Web 数据库技能。
- 保留 33 张框架系统表的 PostgreSQL/pgvector 基线 DDL。
- 将 DDL 定义为框架规范，移除历史源库、转换过程和具体项目记忆。
- 明确仅表名使用 `icoolkj_` 前缀，字段、索引、约束、触发器和函数不加前缀。
