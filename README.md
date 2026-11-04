# icoolkj-skills
icoolkj AI Agent 标准化技能库，沉淀可直接给大模型调用的工具能力与任务编排流程。

> 官网：https://icoolkj.com  
> 邮箱：icoolkj@163.com  
> QQ：594047667

## 现有技能列表

| 技能 | 版本 | 定位 | 典型触发 |
|------|------|------|----------|
| `note-intel` | 1.0.2 | 内容情报：把资料整理成可核对的事实素材包，出选题与图文骨架 | 摘要、事实提炼、情报分析、选题、素材包、多素材合并 |
| `self-media-content-organizer` | 1.0.2 | 自媒体内容中台：事实底座 + 多平台适配（公众号/小红书/知乎/视频号/抖音/朋友圈）+ 视觉资产规划 | 多平台改写、平台适配、图文卡片方案、视频脚本、视觉清单 |
| `xhs-content-studio` | 1.0.2 | 小红书专用：事实驱动文案 + 自适应 3:4 轮播卡片 + 可编辑视觉工作台 | 小红书、轮播图、卡片、发布小红书 |
| `data-report-agent-skill` | 1.2.0 | 数据分析报告 Agent：模型主导需求澄清、章节与图表设计、生成并修复 report.json | 分析这份数据、出个分析报告、按业务目标定制报告 |
| `data-report-creator` | 1.2.1 | 数据分析报告生成工具：人工配置 report.json + CLI 流水线导出 | report.json、CLI 生成报告、手工调章节 |
| `security-scanner` | 1.0.0 | 本地文件安全查杀：快速/标准/深度三档扫描，四类结果分级 | 扫描、查毒、杀毒、检查病毒、扫描U盘 |

技能边界：`note-intel` 只做平台无关的素材包；需要多平台差异化表达用 `self-media-content-organizer`；小红书卡片成品用 `xhs-content-studio`；数据分析报告按"模型主导 / 人工配置"二选一。

## 目录规范

- `skill-name/`：单个技能完整源码目录，**hyphen-case 命名**，与 `SKILL.md` 的 `name` 字段一致
- `skill-name/SKILL.md`：技能定义、触发条件、工作流、脚本索引（含 YAML frontmatter）
- `skill-name/scripts/`：可执行脚本（CLI 带 `--help`，可复用模块不提供 CLI）
- `skill-name/references/`：按需加载的参考文档，`SKILL.md` 只放索引
- `skill-name/assets/`：模板、图片等静态素材
- `skill-name/examples/`：调用示例
- `skill-name/tests/`：单元测试（**不进上传包**）
- `tools/`：仓库级维护脚本（主从同步、打包校验），不属于任何技能，不随技能上传
- `build / dist / work / output / *.spec`：打包与运行时产物，已加入 `.gitignore`，不上传仓库

目录层级上限为 **2 级**（`根/子目录/文件`）。平台打包不接受三级嵌套，新增文件请平铺到现有目录内。

## 元数据规范

`SKILL.md` 的 YAML frontmatter 字段顺序固定：

```yaml
name: skill-name
description: 中文描述（决定自动触发，末尾用"不用于…"划清边界）
agent_created: true
version: 1.0.0            # SemVer 2.0.0 裸版本号，禁止 v 前缀
display_name: 中文名
display_name_en: English Name
description_zh: 与 description 一致
description_en: 英文描述（供英文环境匹配）
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
```

`version` 必须是 `1.0.0` 形式，写成 `v1.0.0` 会被平台判为格式不合法。

## 共享脚本主从关系

`note-intel` / `self-media-content-organizer` / `xhs-content-studio` 共享一批同源脚本。三个技能各自要能独立打包上传，所以文件必须各存一份，但**内容以主版为准**，不要各改各的。主从关系定义在 `tools/skill_manifest.json`：

| 脚本 | 主版位置 | 覆盖技能 |
|------|----------|----------|
| `analyze_material.py` `extract_candidates.py` `scan_risks.py` | `xhs-content-studio/scripts/` | 三个内容类技能 |
| `compare_packs.py` `score_topics.py` | `note-intel/scripts/` | note-intel、self-media |
| `composer.py` `data_loader.py` `styler.py` | `data-report-creator/scripts/` | 两个 data-report 技能 |

同名但**按设计不收敛**的脚本在清单的 `divergent_notes` 里逐条写明理由（例如 `validate_pack.py` 在 note-intel 是素材包校验器，在 xhs 是小红书成品校验器，不能互相覆盖）。

```bash
python tools/sync_shared_scripts.py            # 只报告漂移
python tools/sync_shared_scripts.py --fix      # 用主版覆盖副本
python tools/sync_shared_scripts.py --check    # CI 用，有漂移退出码 1
```

改共享脚本的正确顺序：改主版 → `--fix` 同步副本 → `--check` 确认无漂移 → 重新打包。

## 打包上传

```bash
python tools/build_skills.py            # 校验并生成 dist/*.zip
python tools/build_skills.py --check    # 只校验，不写包
```

打包会排除 `tests/`、`evaluation/`、`DESIGN.md`、`work/`、`output/`、`__pycache__` 等非运行时文件，并校验：目录层级 ≤2、包内仅一份 `SKILL.md`、`version` 为 SemVer 裸版本号、`name` 与目录同名、`agent_created: true`、`description` 与 `description_zh` 一致。

`config.json` 是运行时配置（`analyze_material.py` 默认读取 `<skill>/config.json`），必须留在技能根目录，不要挪进 `references/`。

## 运行时适配
可无缝对接 DeepSeek Harness、LM Studio、私有化 Agent 调度平台，支持本地离线模型调用。

## 开源协议
[MIT](./LICENSE)

Copyright © 2026 icoolkj.com

## 联系方式

| 项目 | 信息 |
|------|------|
| 官网 | https://icoolkj.com |
| 邮箱 | icoolkj@163.com |
| QQ | 594047667 |
