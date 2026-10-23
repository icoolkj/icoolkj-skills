# 图表类型与导出格式

## 图表生成

### 支持的图表类型

| 类型 | 说明 | 必需数据字段 | 可选字段 |
|------|------|--------------|----------|
| `bar` | 柱状图（支持横向） | labels, values | x_label, y_label, horizontal |
| `line` | 折线图（支持多系列） | labels, series 或 values | x_label, y_label |
| `pie` | 饼图 | labels, values | |
| `histogram` | 直方图 | values | x_label, y_label, bins |
| `scatter` | 散点图 | x_values, y_values | x_label, y_label |
| `area` | 面积图 | labels, values | x_label, y_label |

### 图表数据格式示例

**bar（柱状图）**：
```json
"chart_config": {
  "type": "bar",
  "data": {
    "title": "区域销售额对比",
    "labels": ["华东", "华南", "华北"],
    "values": [520, 380, 350],
    "y_label": "销售额（万元）",
    "horizontal": false
  }
}
```

**line（折线图，多系列）**：
```json
"chart_config": {
  "type": "line",
  "data": {
    "title": "月度销售趋势",
    "labels": ["1月", "2月", "3月"],
    "series": [
      {"name": "2025年", "values": [120, 150, 180]},
      {"name": "2024年", "values": [100, 130, 160]}
    ],
    "y_label": "销售额（万元）"
  }
}
```

**pie（饼图）**：
```json
"chart_config": {
  "type": "pie",
  "data": {
    "title": "产品类别占比",
    "labels": ["电子产品", "服装", "食品"],
    "values": [680, 420, 350]
  }
}
```

**histogram（直方图）**：
```json
"chart_config": {
  "type": "histogram",
  "data": {
    "title": "销售额分布",
    "values": [120, 98, 135, 142, 158],
    "x_label": "销售额",
    "y_label": "频次",
    "bins": 10
  }
}
```

**scatter（散点图）**：
```json
"chart_config": {
  "type": "scatter",
  "data": {
    "title": "销售额 vs 订单数",
    "x_values": [120, 98, 135],
    "y_values": [45, 38, 52],
    "x_label": "销售额",
    "y_label": "订单数"
  }
}
```

**area（面积图）**：
```json
"chart_config": {
  "type": "area",
  "data": {
    "title": "累计销售额",
    "labels": ["1月", "2月", "3月"],
    "values": [120, 270, 450],
    "y_label": "累计销售额（万元）"
  }
}
```

### 图表输出

- 格式：PNG
- 分辨率：150 DPI
- 保存路径：`work_dir/charts/<section_id>.png`

## 导出格式

### Markdown（默认）
- Jinja2 模板生成，图表以 `![](chart_path)` 引用

### HTML（默认）
- CSS 变量注入风格配色，KPI 卡片 grid 布局，响应式设计

### PDF（可选）
- 优先 reportlab（纯 Python，无外部依赖，推荐）
- 回退 WeasyPrint（更高质量，需 GTK3）

安装：
```bash
pip install reportlab     # 推荐，纯 Python
pip install weasyprint    # 可选，高质量 HTML→PDF
```

## 依赖配置

### 必需依赖
| 包 | 用途 |
|----|------|
| pandas | 数据加载与分析 |
| openpyxl | Excel 文件读取 |
| matplotlib | 图表生成 |
| Jinja2 | 模板渲染 |

### 可选依赖
| 包 | 用途 |
|----|------|
| reportlab | PDF 导出（推荐） |
