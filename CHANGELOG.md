# 更新记录

## Unreleased

### Added
- 为三项 icoolkj-platform Web 技能新增回归评测集，覆盖布局、权限保存、组织授权、PostgreSQL 命名和安全初始化。
- 新增 `icoolkj-platform-web-frontend`、`icoolkj-platform-web-backend` 和 `icoolkj-platform-web-database` 三项框架技能。
- 将前端交互、后端认证授权和数据库建表职责分开；数据库技能保留框架 PostgreSQL/pgvector 基线 DDL。
- 移除旧项目化技能入口和项目专属数据库来源说明，避免将项目记忆固化到可复用技能。
- 新增 `poster-designer-lab` 1.3.0（实验版）：设计方向手册（D1–D4）、`--compare` 版式重复检测、
  `analyze_logo.py` Logo 分析、实际字体加载校验、HTML 固定画布出图与 A4 单页规范。
- 原 `poster-designer` 恢复并保持 1.1.2，源码与 `scripts/` 不混入实验版；两个版本并存。

### Fixed
- 将 `md-word-dual` 纳入默认安全审计技能列表。
- 技能打包校验要求 `SKILL.md` 声明非空 `license` 字段。
- 统一 `security-scanner` 文档版本为 1.1.2，并明确其为静态风险分析工具，不集成 Microsoft Defender、MCP 或动态行为分析。
