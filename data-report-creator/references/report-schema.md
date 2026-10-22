# 报告 JSON Schema

report.json 是报告项目的唯一配置入口。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✓ | 报告标题 |
| `topic` | string | | 主题关键词 |
| `created` | string | | 创建日期（YYYY-MM-DD） |
| `data_source` | string | ✓ | 数据文件路径 |
| `data_format` | string | | 数据格式（csv/xlsx/json） |
| `style` | string | ✓ | **用户选定的**报告风格 ID |
| `output_formats` | string[] | | 输出格式，默认 ["markdown", "html"] |
| `sections` | object[] | ✓ | 章节列表（见下） |
| `data_profile` | object | | 数据画像（自动填充） |
| `llm_config` | object | | LLM 配置（可选，见下） |

## llm_config 格式（可选）

启用 LLM 自动生成时，可在 report.json 中配置，也可通过命令行参数覆盖。
采用 OpenAI 兼容 API 协议（`/v1/chat/completions`），支持任意兼容提供商。

```json
"llm_config": {
  "enabled": true,
  "api_key": "",
  "base_url": "https://api.deepseek.com/v1",
  "model": "deepseek-flash",
  "generate_conclusions": true,
  "generate_descriptions": false,
  "generate_summary": false
}
```

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `enabled` | bool | false | 是否启用 LLM 生成 |
| `api_key` | string | | API Key（优先用环境变量 `LLM_API_KEY` 或 `OPENAI_API_KEY`） |
| `base_url` | string | `https://api.deepseek.com/v1` | API 地址（优先用环境变量 `LLM_BASE_URL` 或 `OPENAI_BASE_URL`） |
| `model` | string | `deepseek-flash` | 模型名称 |
| `generate_conclusions` | bool | true | 自动生成结论与建议（替换 `[填写]` 占位符） |
| `generate_descriptions` | bool | false | 自动生成各章节分析描述 |
| `generate_summary` | bool | false | 自动生成报告封面摘要 |

常见提供商 base_url：
- DeepSeek: `https://api.deepseek.com/v1`（默认）
- OpenAI: `https://api.openai.com/v1`
- Moonshot: `https://api.moonshot.cn/v1`
- 智谱: `https://open.bigmodel.cn/api/paas/v4`
- 通义千问: `https://dashscope.aliyuncs.com/compatible-mode/v1`

命令行参数优先级高于 llm_config 中的设置。

## sections 章节字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 节标识（cover / data_overview / col_XX / conclusion） |
| `title` | string | ✓ | 节标题 |
| `content_type` | string | ✓ | 内容类型（text/summary/chart/table/kpi/image） |
| `style` | string | ✓ | **用户选定的**风格 ID |
| `content` | string | ✓ | 文字内容 |
| `chart_config` | object | | 图表配置（content_type=chart 时必填） |
| `table_config` | object | | 表格配置（content_type=table 时） |
| `kpi_config` | object[] | | KPI 配置（content_type=kpi 时） |

## chart_config 格式

```json
"chart_config": {
  "type": "bar",
  "data": {
    "title": "图表标题",
    "labels": ["A", "B", "C"],
    "values": [100, 200, 150],
    "x_label": "X轴标签",
    "y_label": "Y轴标签",
    "horizontal": false,
    "bins": 20,
    "series": [{"name": "系列1", "values": [1,2,3]}]
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

## table_config 格式

```json
"table_config": {
  "title": "表格标题",
  "headers": ["列1", "列2", "列3"],
  "rows": [["值1", "值2", "值3"]]
}
```

## kpi_config 格式

```json
"kpi_config": [
  {"label": "总行数", "value": 1000, "unit": "行"},
  {"label": "完整度", "value": "98.5%", "unit": ""}
]
```

## 最小可用示例

```json
{
  "title": "销售数据分析报告",
  "data_source": "data/sales.csv",
  "style": "corporate",
  "output_formats": ["markdown", "html"],
  "sections": [
    {
      "id": "cover",
      "title": "销售数据分析报告",
      "content_type": "text",
      "content": "本报告基于销售数据自动生成。",
      "style": "corporate"
    },
    {
      "id": "monthly_sales",
      "title": "月度销售额",
      "content_type": "chart",
      "content": "各月销售额对比",
      "style": "corporate",
      "chart_config": {
        "type": "bar",
        "data": {
          "title": "月度销售额",
          "labels": ["1月", "2月", "3月"],
          "values": [120, 150, 180],
          "y_label": "销售额（万元）"
        }
      }
    }
  ]
}
```
