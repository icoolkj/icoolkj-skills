# icoolkj-platform Web 后端

用于 icoolkj-platform 多租户 Web 应用的认证、组织上下文、RBAC、API 契约和服务端数据隔离。

覆盖：

- JWT 登录、会话生命周期和当前用户解析
- 租户、集团、子公司、生产基地等组织范围校验
- 页面权限、操作权限和数据范围的分层授权
- 统一错误语义、冲突处理、审计和敏感操作保护
- 多租户查询、关联资源和组织切换的服务端隔离
- 运行时 SQL 外置、仓储层调用和 SQL 文件定位规范

默认使用 `.sql` 文件存放运行时查询：单表操作按真实表名合并到 `backend/app/sql/<领域>/<表名>.sql`，用 `-- @id: 查询名` 分隔调用；多表关联和业务查询按业务领域放入 `<领域>/queries/<业务名>.sql`。由 `backend/app/repositories/<领域>/` 递归加载并绑定参数；PostgreSQL DDL 及迁移 SQL 仍使用 `backend/migrations/sql/`。XML 仅适用于项目已经采用 XML Mapper 的后端，不作为 SQLAlchemy 项目的默认方案。

前端界面使用 `icoolkj-platform-web-frontend`；框架表结构、PostgreSQL DDL 和迁移使用 `icoolkj-platform-web-database`。详细规则见 `references/sql-organization.md`。
