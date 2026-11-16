---
name: data-report-creator
description: "人工配置驱动的数据分析报告生成工具。用户通过命令行生成并手动编辑 report.json，再由本地 Python 流水线完成合规检查、图表渲染和 Markdown/HTML/PDF 导出。适用于希望直接控制配置、手工调整章节或使用 CLI 生成 CSV/Excel/JSON 数据报告的场景；不用于由模型通过自然语言主导报告规划的交互式分析。"
agent_created: true
version: 1.2.1
display_name: 数据分析报告生成工具
display_name_en: Data Report Creator
description_zh: 人工配置驱动的数据分析报告生成工具。用户通过命令行生成并手动编辑 report.json，再由本地 Python 流水线完成合规检查、图表渲染和 Markdown/HTML/PDF 导出。适用于希望直接控制配置、手工调整章节或使用 CLI 生成 CSV/Excel/JSON 数据报告的场景；不用于由模型通过自然语言主导报告规划的交互式分析。
description_en: A configuration-driven data analysis report generator. The user creates and edits report.json from the command line, then a local Python pipeline runs compliance checks, renders charts and exports Markdown, HTML or PDF. Suits users who want direct control over configuration, manual section adjustments, or CLI-generated reports from CSV, Excel or JSON data. Not intended for interactive analysis where the model leads report planning from natural language.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
---

# 数据分析报告创作 Skill

从数据文件（CSV/Excel/JSON）生成专业数据分析报告。该 Skill 面向人工配置与 CLI 操作：用户决定报告结构和风格、检查并编辑 `report.json`，本地脚本负责数据处理和报告生成。

**两条强制流程**：①生成前必须由用户选择风格；②报告必须通过合规检查。

## 快速开始

以下命令都在 **skill 目录内** 执行，路径相对于 skill 目录：

```bash
pip install -r requirements.txt

# 1. 从数据文件创建报告规划（会列出10种风格供用户选择）
python scripts/planner.py <数据文件.csv|.xlsx|.json> --output work/my-report/report.json --style corporate

# 2. 编辑 report.json：确认每节 style 是用户选定的风格，填写 content

# 3. 合规检查
python scripts/compliance.py work/my-report/report.json

# 4. 一键生成（自动生成图表→组装内容→导出 Markdown/HTML/PDF）
python scripts/run_pipeline.py work/my-report/report.json --work-dir work/my-report

# 5. 导出 PDF（需先安装 PDF 库）
pip install reportlab
python scripts/run_pipeline.py work/my-report/report.json --work-dir work/my-report --formats markdown html pdf
```

输出：`report.md` + `report.html` + `report.pdf`（可选）+ `charts/` 图表目录。

## 工作流（6步，两步强制）

```
1. 数据加载与画像 (data_loader.py)
   ↓ 自动检测格式，统计行数/列数/缺失值/数值列
2. 报告规划 (planner.py)
   ↓ 【强制】列出10种风格，必须让用户选择，写入 sections[].style
3. 合规检查 (compliance.py) — 不通过必须停止
4. 图表生成 (charts.py)
   ↓ 根据每节 chart_config 生成 matplotlib 图表
5. 报告组装 (composer.py)
   ↓ 组装内容 + 图表 + KPI + 表格 + 风格
6. 导出 (exporter.py)
   ↓ 导出 Markdown / HTML / PDF
```

## 10种报告风格（用户必须选择）

| # | style ID | 名称 | 适用场景 |
|---|----------|------|----------|
| 1 | `corporate` | 企业商务风 | 企业年报、商业分析 |
| 2 | `minimal` | 极简素雅风 | 学术、技术报告 |
| 3 | `vibrant` | 活力多彩风 | 营销、用户增长 |
| 4 | `dark` | 暗色科技风 | 技术、运维、安全 |
| 5 | `editorial` | 杂志编辑风 | 行业洞察、深度分析 |
| 6 | `fresh` | 清新自然风 | 环保、健康、生活方式 |
| 7 | `warm` | 温暖人文风 | 社会、教育、公益 |
| 8 | `tech_blue` | 科技蓝风 | 产品、技术、数据 |
| 9 | `retro` | 复古怀旧风 | 历史、文化、品牌传承 |
| 10 | `dashboard` | 仪表盘风 | 实时监控、运营 |

用户可选统一风格（`--style corporate`）或每节不同风格（编辑 report.json 的 `sections[].style`）。
完整风格参数（配色/字体/布局/图表样式）见 [references/style-catalog.md](references/style-catalog.md)。

## 核心规则

- **【强制】风格选择**：生成前必须让用户从10种风格中选择，不得自动分配。
- **【强制】合规检查**：报告必须通过合规检查才能进入生成流程。检查内容包括数据质量、结构完整性、敏感词、URL链接等。
- **数据格式**：支持 CSV、Excel（.xlsx/.xls）、JSON、JSONL。
- **图表类型**：bar、line、pie、scatter、histogram、area、table。
- **输出格式**：Markdown（默认）、HTML（默认）、PDF（需 reportlab）。
- **配置驱动**：report.json 是唯一配置入口，所有脚本围绕它工作。

## report.json 核心字段

**顶层**：`title`, `data_source`, `data_format`, `style`, `output_formats`, `sections[]`, `data_profile`

**每节**：
| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✓ | 节标识（cover / data_overview / col_XX / conclusion 等） |
| `title` | ✓ | 节标题 |
| `content_type` | ✓ | 内容类型（text / summary / chart / table / kpi / image） |
| `style` | ✓ | **用户选定的风格ID**（见上方10种） |
| `content` | ✓ | 文字内容 |
| `chart_config` | | 图表配置（content_type=chart 时必填） |
| `table_config` | | 表格配置（content_type=table 时） |
| `kpi_config` | | KPI 配置（content_type=kpi 时） |

完整字段说明见 [references/report-schema.md](references/report-schema.md)。
可直接复制的模板：[assets/report.example.json](assets/report.example.json)。

## 图表配置格式

```json
"chart_config": {
  "type": "bar",
  "data": {
    "title": "月度销售额",
    "labels": ["1月", "2月", "3月"],
    "values": [120, 150, 180],
    "x_label": "月份",
    "y_label": "销售额（万元）"
  }
}
```

支持的图表类型和完整参数见 [references/providers.md](references/providers.md)。

## LLM 自动生成（可选）

启用 LLM 后，报告中的 `[填写]` 占位符会自动替换为 AI 生成的专业内容。
采用 OpenAI 兼容 API 协议（`/v1/chat/completions`），支持任何兼容该协议的模型提供商。

### 支持的提供商示例

| 提供商 | `--base-url` | `--model` 示例 |
|--------|-------------|---------------|
| DeepSeek | `https://api.deepseek.com/v1`（默认） | `deepseek-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Moonshot (Kimi) | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 (Zhipu) | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |
| 通义千问 (Qwen) | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-turbo` |
| 百川 (Baichuan) | `https://api.baichuan-ai.com/v1` | `baichuan2-turbo` |
| 自部署 (vLLM/Ollama) | `http://localhost:8000/v1` | 自定义 |

### 使用方式

```bash
# 方式1：环境变量（默认使用 DeepSeek）
export LLM_API_KEY="sk-..."
python scripts/run_pipeline.py report.json --work-dir ./output --llm

# 方式2：命令行参数（DeepSeek，默认）
python scripts/run_pipeline.py report.json --work-dir ./output \
  --llm --api-key "sk-..." --model "deepseek-flash"

# 方式3：OpenAI
python scripts/run_pipeline.py report.json --work-dir ./output \
  --llm --api-key "sk-..." --base-url "https://api.openai.com/v1" --model "gpt-4o-mini"

# 方式4：Moonshot (Kimi)
python scripts/run_pipeline.py report.json --work-dir ./output \
  --llm --api-key "sk-..." --base-url "https://api.moonshot.cn/v1" --model "moonshot-v1-8k"

# 附加选项
python scripts/run_pipeline.py report.json --work-dir ./output \
  --llm --llm-descriptions --llm-summary
```

| 参数 | 说明 |
|------|------|
| `--llm` | 启用 LLM 内容生成（默认只生成结论与建议） |
| `--api-key` | API Key（或设 `LLM_API_KEY` / `OPENAI_API_KEY` 环境变量） |
| `--base-url` | API 地址（或设 `LLM_BASE_URL` / `OPENAI_BASE_URL` 环境变量） |
| `--model` | 模型名称，默认 `deepseek-flash` |
| `--llm-descriptions` | 同时生成各章节的数据分析描述 |
| `--llm-summary` | 同时生成报告封面摘要 |

LLM 生成失败时不会中断流程，`[填写]` 占位符保留，可手动填写。

## 命令行参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--work-dir` | 必填 | 输出目录 |
| `--formats` | markdown,html | 输出格式（可选 pdf） |
| `--force-charts` | false | 强制重新生成图表 |
| `--skip-verify` | false | 跳过最终验证 |
| `--llm` | false | 启用 LLM 自动生成内容 |
| `--api-key` | | OpenAI API Key |
| `--base-url` | | OpenAI 兼容 API 地址 |
| `--model` | deepseek-flash | LLM 模型名称 |
| `--llm-descriptions` | false | 生成章节描述 |
| `--llm-summary` | false | 生成报告摘要 |

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scripts/data_loader.py` | 数据加载与画像（CSV/Excel/JSON） |
| `scripts/planner.py` | 从数据生成报告规划，**列出10种风格供用户选择** |
| `scripts/styler.py` | 10种报告风格参数定义 |
| `scripts/charts.py` | matplotlib 图表生成（6种类型） |
| `scripts/compliance.py` | 合规检查（数据质量/结构/敏感词） |
| `scripts/composer.py` | 报告组装（内容+图表+KPI+表格） |
| `scripts/exporter.py` | 导出 Markdown/HTML/PDF |
| `scripts/run_pipeline.py` | 一键流水线 |
| `scripts/llm_writer.py` | LLM 自动生成结论与建议（OpenAI 兼容 API） |

## 参考文档（按需加载）

- [references/style-catalog.md](references/style-catalog.md) — 10种风格完整参数（配色/字体/布局/图表样式）
- [references/report-schema.md](references/report-schema.md) — report.json 完整字段说明 + 最小可用示例
- [references/providers.md](references/providers.md) — 图表类型/导出格式/依赖配置
- [references/troubleshooting.md](references/troubleshooting.md) — 故障排查 + 质量检查清单 + 目录结构

## 运行时依赖

- Python 3.10+、pandas、openpyxl、matplotlib、Jinja2
- 可选：reportlab（PDF 导出，纯 Python 无外部依赖，推荐）
- 可选：WeasyPrint（PDF 导出，更高质量，Linux/Mac 推荐，Windows 需 GTK3）
- 可选：requests（LLM 自动生成内容，支持 OpenAI 兼容 API）

---

## 关于

| 项目 | 信息 |
|------|------|
| 出品 | icoolkj |
| 官网 | https://icoolkj.com |
| 邮箱 | icoolkj@163.com |
| QQ | 594047667 |
| 许可 | MIT License |

Copyright © 2026 icoolkj.com
