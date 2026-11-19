# PharmaMind-AI 前端界面规划

用于 PharmaMind-AI 前端页面的信息架构、导航布局和交互流程设计。

## 覆盖范围

- Vue 3 + Element Plus 页面设计
- 单栏、左右、左中右布局决策
- 一级菜单与二级菜单规划
- 组织范围上下文和多组织数据切换体验
- 表格、表单、弹窗、权限操作和响应式行为
- 按钮语义、异步状态、错误恢复、危险操作与可访问性规范
- 可选按钮动效目录（仅在明确需要时使用，不是默认要求）
- 认证上下文、JWT 当前组织、页面数据范围和 RBAC 菜单
- API 权限契约、请求竞态、表格规模化和字段级校验
- 宽屏、中等宽度、移动端和键盘焦点验收
- 必须完整初始化的 33 张 PostgreSQL 系统表；仅表名使用 `icoolkj_` 前缀，字段及其他对象名保持常规命名

## 使用原则

技能不会强制所有页面使用三栏布局，而是根据任务复杂度选择最小可用布局：

- 单栏：单一主任务或向导式流程
- 左右：主从列表、详情或权限编辑
- 左中右：稳定的产品级一级导航、三个以上二级功能和右侧工作区

详细规则见 [SKILL.md](./SKILL.md)、[layout-patterns.md](./references/layout-patterns.md)、[button-interaction.md](./references/button-interaction.md)、[auth-scope-rbac.md](./references/auth-scope-rbac.md)、[async-workflows.md](./references/async-workflows.md)、[table-form-patterns.md](./references/table-form-patterns.md)、[database-schema-conventions.md](./references/database-schema-conventions.md)、[system-schema-inventory.md](./references/system-schema-inventory.md)、[system-schema.postgresql.sql](./references/system-schema.postgresql.sql) 和 [visual-qa.md](./references/visual-qa.md)。

多路由、权限或验收状态的改动可直接参考 [templates](./templates/)。

## 许可证

MIT
