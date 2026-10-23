---
name: data-report-agent-skill
description: "数据分析报告 Agent Skill：用户用自然语言描述数据分析需求，Agent 交互式生成合规 report.json 配置，本地 Python 脚本完成数据加载、图表渲染、导出。支持 10 种视觉风格、6 种图表类型、KPI 卡片、Markdown/HTML/PDF 导出、LLM 自动补写。Use for 数据分析报告, 数据报告, 自动报告, CSV分析, Excel分析, JSON分析, 数据可视化, 报告生成, AI数据分析."
---

# 数据分析报告 Agent Skill

用户说自然语言 → Agent 输出合规 report.json → 本地 Python 脚本完成统计、绘图、导出。

**核心理念**：Agent（对话大模型）负责需求理解、交互引导、配置生成；本地 Python 脚本负责数据解析、图表渲染、文件导出。Agent 不直接读取、解析、计算原始大数据，不生成 PNG/PDF。

## 限制边界（Agent 不能做什么）

1. **不直接读取原始大 CSV/Excel 数据**：只根据用户描述 + planner 输出的数据画像元信息来构建 report.json
2. **不生成 PNG 图表、不生成 PDF**：这些全部由本地 Python 完成
3. **不接收全部明细数据**：原始数据行数巨大时，仅接收数据画像元信息（行数、列数、缺失值、数值列等）
4. **不做统计分析计算**：求和、均值、分组聚合等交给本地 data_loader.py 和 planner.py

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
| AI 文字生成 | 是否开启 LLM 自动补写摘要/解读/结论 | 默认关闭 |
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

**模式 B：自定义模式（LLM 手动编排）**
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

有问题立刻修正，不往下流转。

### Phase 3：输出产物

Agent 输出完整可直接复制的 **report.json** 文本，附带说明：

```
已经生成报告配置 report.json，请在本地执行流水线脚本：

1. 保存 report.json 到本地目录（如 ./my-report/）
2. 将数据文件放到对应路径（report.json 中 data_source 指定的路径）
3. 安装依赖：pip install -r requirements.txt
4. 执行流水线：
   python scripts/run_pipeline.py report.json --work-dir ./my-report

可选参数：
   --formats markdown html pdf    # 指定输出格式
   --llm                          # 启用 AI 自动补写文字
   --api-key "sk-..."             # LLM API Key
   --model "deepseek-flash"       # LLM 模型

输出文件：
   report.md / report.html / report.pdf + charts/ 图表目录
```

**占位符处理**：
- 未开启 AI 文字生成时，结论与建议章节的 content 写 `[填写] 基于以上数据分析的结论和建议`
- 开启 AI 文字生成时，content 仍写 `[填写]`，本地 llm_writer.py 会自动替换

### Phase 4：本地流水线执行（用户电脑执行）

用户在本地执行 Python 脚本，Agent 不执行代码：

```
report.json → compliance.py合规校验 → data_loader.py数据加载
→ charts.py图表渲染 → composer.py报告组装 → exporter.py导出md/html/pdf
→ (可选) llm_writer.py AI文字补写
```

本地执行链路完全继承 data-report-creator 项目，脚本位于 `scripts/` 目录。

### Phase 5：错误修复闭环

用户将本地脚本报错信息复制粘贴回对话，Agent 修改修复 report.json：

- 合规检查失败 → Agent 修正违规内容
- 图表 type 错误 → Agent 修正 chart_config
- 缺少必填字段 → Agent 补全字段
- 数据路径错误 → Agent 修正 data_source

常见报错修复指引见 [references/error-repair-guide.md](references/error-repair-guide.md)。

## report.json 核心字段

**顶层**：`title`, `data_source`, `data_format`, `style`, `output_formats`, `sections[]`, `data_profile`, `llm_config`

**每节**：
| 字段 | 必填 | 说明 |
|------|------|------|
| `id` | ✓ | 节标识（cover / kpi_overview / cross_XX / dist_XX / conclusion 等） |
| `title` | ✓ | 节标题 |
| `content_type` | ✓ | text / summary / chart / table / kpi / image |
| `style` | ✓ | 用户选定的风格 ID |
| `content` | ✓ | 文字内容（`[填写]` 表示待 AI 补写） |
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

## LLM 自动生成（可选）

启用后，报告中的 `[填写]` 占位符会自动替换为 AI 生成的专业内容。采用 OpenAI 兼容 API 协议。

| 提供商 | `--base-url` | `--model` 示例 |
|--------|-------------|---------------|
| DeepSeek（默认） | `https://api.deepseek.com/v1` | `deepseek-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |
| 智谱 | `https://open.bigmodel.cn/api/paas/v4` | `glm-4-flash` |

使用方式：
```bash
# 环境变量
export LLM_API_KEY="sk-..."
python scripts/run_pipeline.py report.json --work-dir ./output --llm

# 命令行参数
python scripts/run_pipeline.py report.json --work-dir ./output \
  --llm --api-key "sk-..." --model "deepseek-flash"
```

LLM 生成失败时不中断流程，`[填写]` 占位符保留。

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
| `scripts/llm_writer.py` | LLM 自动生成结论与建议 |

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
- 可选：requests（LLM 自动生成内容）
