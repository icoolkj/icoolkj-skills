# 更新记录

## Unreleased

### Added
- 新增 `poster-designer-lab` 1.3.0（实验版）：设计方向手册（D1–D4）、`--compare` 版式重复检测、
  `analyze_logo.py` Logo 分析、实际字体加载校验、HTML 固定画布出图与 A4 单页规范。
- 原 `poster-designer` 恢复并保持 1.1.2，源码与 `scripts/` 不混入实验版；两个版本并存。

### Fixed
- 将 `md-word-dual` 纳入默认安全审计技能列表。
- 技能打包校验要求 `SKILL.md` 声明非空 `license` 字段。
- 统一 `security-scanner` 文档版本为 1.1.2，并明确其为静态风险分析工具，不集成 Microsoft Defender、MCP 或动态行为分析。
