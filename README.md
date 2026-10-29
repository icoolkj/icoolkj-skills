# icoolkj-skills
icoolkj AI Agent 标准化技能库，沉淀可直接给大模型调用的工具能力与任务编排流程。

> 官网：https://icoolkj.com

## 现有技能列表
- ✅ **note-intel**：笔记智能解析与知识提取技能，支持素材梳理、要点提炼、内容结构化
- ✅ **data-report-agent-skill**：数据报表智能Agent技能，自动分析数据、生成报表结论
- ✅ **data-report-creator**：报表生成工具，基于结构化数据输出文档报表
- ✅ **self-media-content-organizer**：自媒体内容整理技能，素材归类、脚本梳理、选题加工

## 目录规范
- `xxx_skill/`：单个技能完整源码目录
- `xxx_skill/assets/`：资源、截图、静态素材
- `xxx_skill/examples/`：调用示例脚本
- `xxx_skill/references/`：参考文档
- `xxx_skill/scripts/`：辅助执行脚本
- `xxx_skill/tests/`：单元测试脚本
- `xxx_skill/SKILL.md`：技能定义、参数、描述文档
- `build / dist / *.spec`：打包产物，已加入.gitignore，不上传仓库

## 运行时适配
可无缝对接 DeepSeek Harness、LM Studio、私有化 Agent 调度平台，支持本地离线模型调用。

## 开源协议
[MIT](./LICENSE)

Copyright © 2026 icoolkj.com
