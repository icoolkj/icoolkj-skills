# Changelog

## 1.0.0 (2026-11-18)

- 初始版本，把 PharmaMind-AI Docker 部署踩坑全链路固化为可复用 Skill。
- SKILL.md：8 段工作流（前置检查、镜像源配置、预拉取、TS 修复、构建启动、健康检查、DB 连接、故障排查）+ 决策树 + 收尾清单。
- scripts：pre-check.ps1 / pull-base-images.ps1 / start.ps1 / logs-follow.ps1 四个脚本，带 Docker 检测、UTF-8 输出与错误处理。
- assets/tsconfig.json：TS 快速兜底配置模板。
- references：ts-compile-fix.md、db-connection.md、troubleshooting.md 三份详细参考。
