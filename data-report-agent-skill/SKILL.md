---
name: data-report-agent-skill
description: "模型编排驱动的数据分析报告 Skill。用户用自然语言描述分析目标，Agent 负责澄清需求、调用本地脚本获取数据画像、设计章节与图表、生成或修复 report.json，并执行合规检查和报告流水线；Python 脚本负责确定性的数据计算、图表渲染及 Markdown/HTML/PDF 导出。适用于 AI 主导、交互式或需要根据业务目标定制分析结构的 CSV/Excel/JSON 报告；不用于以手工编辑配置和直接 CLI 控制为主的流程。"
agent_created: true
version: 1.2.0
display_name: 数据分析报告 Agent
display_name_en: Data Report Agent
description_zh: 模型编排驱动的数据分析报告 Skill。用户用自然语言描述分析目标，Agent 负责澄清需求、调用本地脚本获取数据画像、设计章节与图表、生成或修复 report.json，并执行合规检查和报告流水线；Python 脚本负责确定性的数据计算、图表渲染及 Markdown/HTML/PDF 导出。适用于 AI 主导、交互式或需要根据业务目标定制分析结构的 CSV/Excel/JSON 报告；不用于以手工编辑配置和直接 CLI 控制为主的流程。
description_en: An agent-orchestrated data analysis reporting skill. The user describes the analysis goal in natural language, and the agent clarifies requirements, calls local scripts for data profiling, designs sections and charts, generates or repairs report.json, then runs compliance checks and the reporting pipeline. Python scripts handle deterministic computation, chart rendering and Markdown, HTML or PDF export. Suits AI-led and interactive CSV, Excel or JSON reporting where the analysis structure is tailored to business goals. Not intended for workflows driven mainly by hand-edited configuration and direct CLI control.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
---

# 数据分析报告 Agent Skill

用户说自然语言 → Agent 理解并编排分析 → 本地 Python 脚本完成确定性计算 → Agent 校验并交付报告。

**核心理念**：Agent（对话大模型）负责需求理解、交互引导、分析规划、正文撰写、配置生成、工具调用和错误修复；本地 Python 脚本负责数据解析、统计计算、图表渲染和文件导出。Agent 不凭空推测数据结论，也不在上下文中手工处理完整的大数据集，而是通过脚本获得可验证的结果。报告文字全部由 Agent 撰写，流水线不再调用外部 LLM API。

## 职责边界

1. **Agent 负责决策与编排**：根据用户目标选择快速或自定义模式，设计章节和图表，生成、修改并验证 `report.json`。
2. **Agent 负责撰写全部正文**：封面摘要、章节解读、结论与建议由 Agent 直接撰写，不调用外部 LLM API。文字必须基于脚本计算的统计结果，交付的 report.json 中不得残留 `[填写]` 占位符（compliance.py 会拦截）。
3. **脚本负责确定性计算**：数据读取、求和、均值、分组聚合等由 `data_loader.py` 和 `planner.py` 完成，Agent 使用脚本输出的数据画像和统计结果，不手工猜测。
4. **脚本负责文件生成**：PNG 图表和 PDF/HTML/Markdown 由本地 Python 生成，Agent 可以调用脚本并检查输出，但不在对话中伪造二进制产物。
5. **控制上下文数据量**：对于大型数据文件，Agent 不把全部明细加载到对话上下文，只读取完成规划所需的数据画像、字段信息、聚合结果和少量样本。
6. **必须闭环验证**：环境允许执行本地命令时，Agent 应运行合规检查和报告流水线，并根据错误修复配置；只有环境无法执行或用户明确要求仅生成配置时，才将命令交给用户执行。

## 6 阶段工作流

### Phase 0：需求采集

接收用户输入：
- **数据文件**：CSV / Excel(.xlsx) / JSON / JSONL 文件路径
- **自然语言需求**：如"帮我分析这份销售数据，重点看月度营收，输出 PDF 报告，风格选活力多彩风"

交互式收集缺失信息（**绝不自行猜测风格**）：

| 参数 | 说明 | 是否必填 |
|------|------|---------|
| 报告标题 | 报告的标题 | ✓（可从数据文件名推断） |
| 报告风格 | 10 种风格之一，必须让用户选择 | ✓ |
| 输出格式 | markdown / html / pdf（可多选） | 默认 markdown+html |
| 自定义章节 | 用户指定增删图表、指定图表类型 | 可选 |

**风格选择交互**：必须向用户展示 10 种风格列表，让用户明确选择。不得自动分配。

10 种风格速查：
1. `corporate` 企业商务风 2. `minimal` 极简素雅风 3. `vibrant` 活力多彩风 4. `dark` 暗色科技风
5. `editorial` 杂志编辑风 6. `fresh` 清新自然风 7. `warm` 温暖人文风 8. `tech_blue` 科技蓝风
9. `retro` 复古怀旧风 10. `dashboard` 仪表盘风

完整风格参数见 [references/style-catalog.md](references/style-catalog.md)。

### Phase 1：模式选择

两种工作模式：

**模式 A：快速模式（planner 默认模板）**
- 用户上传数据，选择风格，直接生成标准完整报告配置
- 适合快速分析、初次探索数据
- 调用 `planner.py` 生成默认全套章节（KPI、交叉分析、分布、相关性、数据表、结论）
- Agent 在此基础上可微调（如修改标题、增删章节）

**模式 B：自定义模式（Agent 手动编排）**
- 用户用自然语言描述想看什么分析维度
- Agent 根据用户需求手动组装 sections、chart_config、kpi_config
- 适合有明确分析目标的场景
- 示例：用户说"删掉相关性散点图，增加按季度的折线图，只保留前 5 个品类"
  → Agent 修改 sections 数组，增删 chart_config 配置

**模式选择规则**：
- 用户说"快速分析一下" / "帮我看看这份数据" → 模式 A
- 用户说"我想看月度趋势和品类对比" / "去掉散点图，加个饼图" → 模式 B
- 不确定时询问用户

### Phase 2：合规与 Schema 校验

Agent 在输出 report.json 前做对话层预检查：

**Schema 自检**（按 [references/report-schema.md](references/report-schema.md)）：
- 顶层必填字段：`title`, `data_source`, `sections`, `style`
- 每节必填字段：`id`, `title`, `content_type`, `style`
- content_type 合法值：text / summary / chart / table / kpi / image
- chart_config.type 合法值：bar / line / pie / scatter / histogram / area
- chart 类型章节必须有 chart_config 和 data

**合规预检查**（按 [references/compliance-rules.md](references/compliance-rules.md)）：
- 禁止绝对化敏感词：最佳、最强、第一、顶级、100%、百分百、绝对、确保盈利、零风险、无风险、稳赚
- URL 链接不允许放在正文 content 字段，放到 data_source 或单独的 references
- 数据完整度过低（<50%）时告警提醒用户
- 正文不得残留 `[填写]` 占位符，Agent 撰写的文字必须完整（compliance.py 会拦截）

有问题立刻修正，不往下流转。

### Phase 3：生成配置

Agent 生成完整的 **report.json** 文件。环境允许写入工作区时，应直接保存文件，不要求用户手工复制；仅在无法写文件或用户明确要求文本配置时，才输出可复制的 JSON。

仅生成配置、不执行流水线时，附带以下运行说明：

```
已经生成报告配置 report.json，请在本地执行流水线脚本：

1. 保存 report.json 到本地目录（如 ./my-report/）
2. 将数据文件放到对应路径（report.json 中 data_source 指定的路径）
3. 安装依赖：pip install -r requirements.txt
4. 执行流水线：
   python scripts/run_pipeline.py report.json --work-dir ./my-report

可选参数：
   --formats markdown html pdf    # 指定输出格式

输出文件：
   report.md / report.html / report.pdf + charts/ 图表目录
```

**正文撰写**：
- 报告全部正文（封面摘要、章节解读、结论与建议）由 Agent 直接撰写，不依赖外部 LLM API，也不预留 `[填写]` 占位符
- 文字必须基于脚本输出的统计结果（数据画像、分组聚合、分布指标），不得编造数据中没有的结论
- Agent 写好的文字同样受合规规则约束：不含绝对化用语、正文不含 URL
- 快速模式下 planner.py 生成的结论章节带有 `[填写]` 骨架，Agent 必须替换为正式文字后再交付；最终配置中残留 `[填写]` 会被 compliance.py 拦截

### Phase 4：执行本地流水线

环境允许执行本地命令时，由 Agent 调用 Python 脚本完成流水线；用户明确要求仅生成配置，或当前环境无法执行时，再提供命令由用户运行：

```
report.json → compliance.py合规校验 → data_loader.py数据加载
→ charts.py图表渲染 → composer.py报告组装 → exporter.py导出md/html/pdf
```

本地执行链路继承自 data-report-creator 项目，脚本位于 `scripts/` 目录。差异：本 Skill 不包含 llm_writer.py，报告正文由 Agent 在流水线运行前撰写完毕，流水线内不再有任何 LLM 调用。

### Phase 5：错误修复闭环

Agent 读取本地执行错误并修改 `report.json` 后重试。若流水线由用户在其他环境执行，用户也可以将报错信息粘贴回对话，由 Agent 完成修复：

- 合规检查失败 → Agent 修正违规内容
- 图表 type 错误 → Agent 修正 chart_config
- 缺少必填字段 → Agent 补全字段
- 数据路径错误 → Agent 修正 data_source
- 残留 `[填写]` 占位符 → Agent 撰写正式文字替换

常见报错修复指引见 [references/error-repair-guide.md](references/error-repair-guide.md)。

## report.json 核心字段

**顶层**：`title`, `data_source`, `data_format`, `style`, `output_formats`, `sections[]`, `data_profile`

**每节**：
| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✓ | 节标识（cover / kpi_overview / cross_XX / dist_XX / conclusion 等） |
| `title` | ✓ | 节标题 |
| `content_type` | ✓ | text / summary / chart / table / kpi / image |
| `style` | ✓ | 用户选定的风格 ID |
| `content` | ✓ | 文字内容，由 Agent 撰写（不得残留 `[填写]` 占位符） |
| `chart_config` | | 图表配置（content_type=chart 时必填） |
| `table_config` | | 表格配置（content_type=table 时） |
| `kpi_config` | | KPI 配置（content_type=kpi 时） |

完整字段说明见 [references/report-schema.md](references/report-schema.md)。

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

各图表类型所需字段：
| 类型 | 必需字段 | 可选字段 |
|------|----------|----------|
| bar | labels, values | x_label, y_label, horizontal |
| line | labels, series 或 values | x_label, y_label |
| pie | labels, values | |
| histogram | values | x_label, y_label, bins |
| scatter | x_values, y_values | x_label, y_label |
| area | labels, values | x_label, y_label |

完整图表/导出说明见 [references/providers.md](references/providers.md)。

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scripts/data_loader.py` | 数据加载与画像（CSV/Excel/JSON） |
| `scripts/planner.py` | 从数据生成报告规划（模式 A 使用） |
| `scripts/styler.py` | 10 种报告风格参数定义 |
| `scripts/charts.py` | matplotlib 图表生成（6 种类型） |
| `scripts/compliance.py` | 合规检查（数据质量/结构/敏感词） |
| `scripts/composer.py` | 报告组装（内容+图表+KPI+表格） |
| `scripts/exporter.py` | 导出 Markdown/HTML/PDF |
| `scripts/run_pipeline.py` | 一键流水线 |

## 参考文档

- [references/report-schema.md](references/report-schema.md) — report.json 完整字段规范
- [references/style-catalog.md](references/style-catalog.md) — 10 种风格完整参数
- [references/providers.md](references/providers.md) — 图表类型/导出格式/依赖配置
- [references/compliance-rules.md](references/compliance-rules.md) — 合规黑名单与检查规则
- [references/error-repair-guide.md](references/error-repair-guide.md) — 常见报错修复指引

## 样例

- [examples/example-sales-report.json](examples/example-sales-report.json) — 完整样例配置
- [assets/report.example.json](assets/report.example.json) — 最小可用模板

## 运行时依赖

- Python 3.10+、pandas、openpyxl、matplotlib、Jinja2
- 可选：reportlab（PDF 导出，纯 Python，推荐）

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
