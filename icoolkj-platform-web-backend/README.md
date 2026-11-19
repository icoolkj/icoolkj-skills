# icoolkj-platform Web 后端

用于 icoolkj-platform 多租户 Web 应用的认证、组织上下文、RBAC、API 契约和服务端数据隔离。

覆盖：

- JWT 登录、会话生命周期和当前用户解析
- 租户、集团、子公司、生产基地等组织范围校验
- 页面权限、操作权限和数据范围的分层授权
- 统一错误语义、冲突处理、审计和敏感操作保护
- 多租户查询、关联资源和组织切换的服务端隔离

前端界面使用 `icoolkj-platform-web-frontend`；框架表结构、PostgreSQL DDL 和迁移使用 `icoolkj-platform-web-database`。
