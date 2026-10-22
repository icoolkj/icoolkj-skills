# 报告风格目录

10 种预设风格，在 report.json 的 `sections[].style` 或顶层 `style` 字段中指定。用户必须选择。

| style ID | 名称 | 适用场景 |
|----------|------|----------|
| `corporate` | 企业商务风 | 企业年报、商业分析 |
| `minimal` | 极简素雅风 | 学术、技术报告 |
| `vibrant` | 活力多彩风 | 营销、用户增长 |
| `dark` | 暗色科技风 | 技术、运维、安全 |
| `editorial` | 杂志编辑风 | 行业洞察、深度分析 |
| `fresh` | 清新自然风 | 环保、健康、生活方式 |
| `warm` | 温暖人文风 | 社会、教育、公益 |
| `tech_blue` | 科技蓝风 | 产品、技术、数据 |
| `retro` | 复古怀旧风 | 历史、文化、品牌传承 |
| `dashboard` | 仪表盘风 | 实时监控、运营 |

## 风格详情

### corporate — 企业商务风
- 主色: #1a3a6b（深蓝）
- 辅色: #2d5a9e（中蓝）
- 强调: #e8a838（金色）
- 背景: #ffffff（白）
- 字体: Helvetica Neue, Arial
- 图表配色: 深蓝/中蓝/浅蓝/金/灰
- 布局: 单栏，宽边距，正式页眉页脚

### minimal — 极简素雅风
- 主色: #222222（近黑）
- 辅色: #555555（深灰）
- 强调: #007acc（蓝）
- 背景: #fafafa（浅灰）
- 字体: Segoe UI, system-ui
- 图表配色: 黑/灰/浅灰/蓝/浅灰
- 布局: 单栏，宽边距，极简装饰

### vibrant — 活力多彩风
- 主色: #e74c3c（红）
- 辅色: #3498db（蓝）
- 强调: #2ecc71（绿）
- 背景: #ffffff（白）
- 字体: Source Sans Pro
- 图表配色: 红/蓝/绿/橙/紫
- 布局: 多栏，彩色标题，大胆强调

### dark — 暗色科技风
- 主色: #00d4aa（青绿）
- 辅色: #0ea5e9（天蓝）
- 强调: #f59e0b（琥珀）
- 背景: #1a1a2e（深蓝黑）
- 字体: JetBrains Mono, Consolas
- 图表配色: 青绿/天蓝/琥珀/红/紫
- 布局: 单栏，暗色主题，霓虹强调

### editorial — 杂志编辑风
- 主色: #8b0000（深红）
- 辅色: #2c3e50（深蓝灰）
- 强调: #d4a017（金）
- 背景: #fffef8（暖白）
- 字体: Georgia, Times New Roman
- 图表配色: 深红/深蓝灰/金/灰/红
- 布局: 编辑栏，首字下沉，引文块

### fresh — 清新自然风
- 主色: #27ae60（绿）
- 辅色: #16a085（青绿）
- 强调: #f1c40f（黄）
- 背景: #f0fff4（薄荷白）
- 字体: Nunito
- 图表配色: 绿/青绿/黄/橙/青
- 布局: 圆角，柔和阴影，有机形状

### warm — 温暖人文风
- 主色: #d35400（橙）
- 辅色: #e67e22（浅橙）
- 强调: #7d6608（深金）
- 背景: #fdf6ec（暖白）
- 字体: Lora, Georgia
- 图表配色: 橙/浅橙/金/深橙/红褐
- 布局: 暖色调，以人为本，宽松间距

### tech_blue — 科技蓝风
- 主色: #2563eb（蓝）
- 辅色: #7c3aed（紫）
- 强调: #06b6d4（青）
- 背景: #ffffff（白）
- 字体: Inter, system-ui
- 图表配色: 蓝/紫/青/琥珀/绿
- 布局: 数据密集，渐变强调，仪表盘式

### retro — 复古怀旧风
- 主色: #8b4513（棕）
- 辅色: #cd853f（浅棕）
- 强调: #daa520（金）
- 背景: #f5f0e1（泛黄白）
- 字体: Palatino, Book Antiqua
- 图表配色: 棕/浅棕/金/深棕/灰棕
- 布局: 复古边框，棕褐色调，经典装饰

### dashboard — 仪表盘风
- 主色: #4f46e5（靛蓝）
- 辅色: #0ea5e9（天蓝）
- 强调: #f59e0b（琥珀）
- 背景: #f8fafc（浅灰白）
- 字体: Inter, system-ui
- 图表配色: 靛蓝/天蓝/琥珀/绿/红
- 布局: 网格卡片，KPI 磁贴，紧凑数据展示

## 自定义风格

在 `scripts/styler.py` 的 `STYLES` 字典中添加新条目，每个风格包含以下字段：
- `name`: 风格名称
- `description`: 风格描述
- `primary_color`: 主色（CSS颜色值）
- `secondary_color`: 辅色
- `accent_color`: 强调色
- `background`: 背景色
- `text_color`: 文字颜色
- `font_family`: 字体族
- `heading_size`: 标题字号
- `chart_style`: 图表样式（color_palette, grid_color, background）
- `layout`: 布局描述
