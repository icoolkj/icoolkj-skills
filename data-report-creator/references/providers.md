# 图表类型与导出格式

## 图表生成

### 支持的图表类型

| 类型 | 说明 | 必需数据字段 |
|------|------|--------------|
| `bar` | 柱状图（支持横向） | labels, values |
| `line` | 折线图（支持多系列） | labels, series 或 values |
| `pie` | 饼图 | labels, values |
| `histogram` | 直方图 | values |
| `scatter` | 散点图 | x_values, y_values |
| `area` | 面积图 | labels, values |

### 图表样式

图表自动应用用户选择的风格配色：
- 颜色来自 `style_profile.chart_style.color_palette`
- 背景色来自 `style_profile.chart_style.background`
- 网格线来自 `style_profile.chart_style.grid_color`
- 标题颜色来自 `style_profile.primary_color`

### 图表输出

- 格式：PNG
- 分辨率：150 DPI
- 尺寸：10×5.5 英寸（柱状/折线/直方/散点/面积），8×6 英寸（饼图）
- 保存路径：`work_dir/charts/<section_id>.png`

## 导出格式

### Markdown（默认）

- 使用 Jinja2 模板生成
- 图表以 `![](chart_path)` 引用
- 表格使用 Markdown 表格语法
- KPI 使用列表语法

### HTML（默认）

- 使用 Jinja2 模板生成
- CSS 变量注入风格配色（`--primary`, `--secondary`, `--accent`, `--bg`, `--text`）
- KPI 卡片使用 grid 布局
- 图表以 `<img>` 标签引用
- 响应式设计，最大宽度 900px

### PDF（可选）

支持两种 PDF 导出引擎，自动选择：优先 WeasyPrint（更高质量），失败时回退 xhtml2pdf（纯 Python）。

| 引擎 | 质量 | 依赖 | Windows 兼容 | 推荐场景 |
|------|------|------|-------------|---------|
| WeasyPrint | 高 | 需 GTK3 系统库 | 需安装 GTK3 Runtime | Linux/Mac |
| xhtml2pdf | 中 | 纯 Python，无外部依赖 | 直接可用 | Windows / 快速安装 |

安装：
```bash
# 推荐 Windows 用户（纯 Python，无需 GTK3）
pip install xhtml2pdf

# Linux/Mac 用户（更高质量）
pip install weasyprint

# 两者都安装时自动优先使用 WeasyPrint
```

#### PDF 导出示例

**方式1：在 report.json 中指定**

```json
{
  "output_formats": ["markdown", "html", "pdf"]
}
```

```bash
python scripts/run_pipeline.py report.json --work-dir ./output
# 输出: report.md + report.html + report.pdf
```

**方式2：命令行覆盖**

```json
{
  "output_formats": ["markdown", "html"]
}
```

```bash
python scripts/run_pipeline.py report.json --work-dir ./output --formats markdown html pdf
# 输出: report.md + report.html + report.pdf
```

**方式3：只导出 PDF**

```bash
python scripts/run_pipeline.py report.json --work-dir ./output --formats pdf
# 输出: report.pdf
```

#### WeasyPrint 安装注意事项

| 系统 | 安装命令 | 备注 |
|------|---------|------|
| Linux | `pip install weasyprint` | 可能需要 `sudo apt install libpango-1.0-0 libpangoft2-1.0-0` |
| macOS | `pip install weasyprint` | 可能需要 `brew install pango` |
| Windows | `pip install weasyprint` | 可能需要安装 GTK3 Runtime |

## 依赖配置

### 必需依赖

| 包 | 用途 | 安装 |
|----|------|------|
| pandas | 数据加载与分析 | `pip install pandas` |
| openpyxl | Excel 文件读取 | `pip install openpyxl` |
| matplotlib | 图表生成 | `pip install matplotlib` |
| Jinja2 | 模板渲染 | `pip install Jinja2` |

### 可选依赖

| 包 | 用途 | 安装 |
|----|------|------|
| weasyprint | PDF 导出（高质量） | `pip install weasyprint` |
| xhtml2pdf | PDF 导出（纯 Python，Windows 推荐） | `pip install xhtml2pdf` |

### 跨平台注意事项

- **Linux/Mac**: matplotlib 使用 Agg 后端（无需 GUI）
- **Windows**: 同样使用 Agg 后端，无需额外配置
- **字体**: matplotlib 默认使用系统字体，中文标签可能需要安装中文字体
  - Linux: `sudo apt install fonts-wqy-zenhei`
  - Mac: 系统自带 PingFang SC
  - Windows: 系统自带 Microsoft YaHei
