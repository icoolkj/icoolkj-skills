# icoolkj-platform Web 数据库

用于 icoolkj-platform 多租户 Web 框架的系统表创建、PostgreSQL/pgvector DDL、命名规范和迁移校验。

`references/system-schema.postgresql.sql` 是框架的 PostgreSQL 系统表基线，供版本化迁移和全新环境初始化使用。它是框架规范，不是某个项目的历史 SQL 备份，也不要求调用方携带其他数据库方言的源文件。

覆盖：

- 认证、租户、组织、部门、岗位、角色、菜单、配置、审计和消息系统表
- 仅表名使用 `icoolkj_` 前缀，字段和其他数据库对象使用常规 `snake_case`
- 多租户字段、租户唯一性、索引、更新时间触发器和迁移安全
- 干净初始化、升级迁移、目录校验和数据保护
