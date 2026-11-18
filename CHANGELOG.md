# 更新记录

## Unreleased

### Added
- `poster-designer` 升级到 1.3.0：新增设计方向手册（D1–D4）、`--compare` 版式重复检测、
  `analyze_logo.py` Logo 分析与实际字体加载校验；1.2.0 的 HTML 出图路径、A4 单页规范、
  导出实测与 `html_render` 交付记录一并纳入。

### Fixed
- 将 `md-word-dual` 纳入默认安全审计技能列表。
- 技能打包校验要求 `SKILL.md` 声明非空 `license` 字段。
- 统一 `security-scanner` 文档版本为 1.1.2，并明确其为静态风险分析工具，不集成 Microsoft Defender、MCP 或动态行为分析。
