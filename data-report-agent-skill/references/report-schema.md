# report.json 完整字段规范

report.json 是报告项目的唯一配置入口，由 Agent 生成，本地 Python 脚本消费。

## 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | ✓ | 报告标题 |
| `topic` | string | | 主题关键词 |
| `created` | string | | 创建日期（YYYY-MM-DD） |
| `data_source` | string | ✓ | 数据文件路径（相对或绝对） |
| `data_format` | string | | 数据格式（csv/xlsx/json/jsonl） |
| `style` | string | ✓ | **用户选定的**报告风格 ID（10 种之一） |
| `output_formats` | string[] | | 输出格式，默认 ["markdown", "html"]，可选 "pdf" |
| `sections` | object[] | ✓ | 章节列表（至少 1 个） |
| `data_profile` | object | | 数据画像（planner 自动填充，Agent 可不填） |

## sections 章节字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 节标识，唯一（cover / kpi_overview / cross_XX / dist_XX / correlation / data_table / conclusion） |
| `title` | string | ✓ | 节标题（显示在报告中） |
| `content_type` | string | ✓ | text / summary / chart / table / kpi / image |
| `style` | string | ✓ | **用户选定的**风格 ID（与顶层 style 一致） |
| `content` | string | ✓ | 文字内容，由 Agent 基于统计结果撰写（最终配置中不得残留 `[填写]` 占位符） |
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
  {"label": "总销售额", "value": "1,850", "unit": "万元"},
  {"label": "同比增长", "value": "23.5%", "unit": ""}
]
```

## 常见 section id 命名规则

| id 模式 | 说明 | content_type |
|----------|------|-------------|
| `cover` | 封面页 | text |
| `kpi_overview` | KPI 概览 | kpi |
| `data_overview` | 数据概览 | summary |
| `cross_{分类列}` | 分类×数值交叉分析 | chart |
| `dist_{数值列}` | 数值分布分析 | chart |
| `correlation` | 相关性散点图 | chart |
| `data_table` | 原始数据表 | table |
| `conclusion` | 结论与建议 | text |

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
