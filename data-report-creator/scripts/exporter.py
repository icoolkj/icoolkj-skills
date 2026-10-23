#!/usr/bin/env python3
"""Report exporter — outputs Markdown, HTML, and PDF formats.

Uses Jinja2 templates for HTML, direct Markdown generation,
and WeasyPrint for PDF (with HTML intermediate).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from styler import get_style


MARKDOWN_TEMPLATE = """# {{ title }}

> 数据来源: {{ data_source }} | 生成日期: {{ created }} | 风格: {{ style }}

{% for section in sections %}
## {{ loop.index }}. {{ section.title }}

{% if section.content_type == "text" %}
{{ section.content }}

{% elif section.content_type == "summary" %}
{{ section.content }}

{% elif section.content_type == "kpi" %}
{% for kpi in section.kpis %}
- **{{ kpi.label }}**: {{ kpi.value }} {{ kpi.unit }}
{% endfor %}

{% elif section.content_type == "chart" %}
{% if section.chart_path %}
![{{ section.title }}]({{ section.chart_path }})
{% endif %}
{{ section.content }}

{% elif section.content_type == "table" %}
{% if section.table_path %}
![{{ section.title }}]({{ section.table_path }})
{% endif %}
{% if section.table_data %}
| {% for h in section.table_data.headers %}{{ h }} |{% endfor %}
| {% for h in section.table_data.headers %}---|{% endfor %}
{% for row in section.table_data.rows %}
| {% for cell in row %}{{ cell }} |{% endfor %}
{% endfor %}
{% endif %}

{% endif %}
{% endfor %}

---
*本报告由 data-report-creator 自动生成*
"""


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }}</title>
<style>
:root {
  --primary: {{ style_profile.primary_color }};
  --secondary: {{ style_profile.secondary_color }};
  --accent: {{ style_profile.accent_color }};
  --bg: {{ style_profile.background }};
  --text: {{ style_profile.text_color }};
  --heading-size: {{ style_profile.heading_size }};
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: {{ style_profile.font_family }};
  background: var(--bg);
  color: var(--text);
  line-height: 1.7;
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 30px;
}
h1 {
  color: var(--primary);
  font-size: 2em;
  margin-bottom: 8px;
  border-bottom: 3px solid var(--accent);
  padding-bottom: 10px;
}
h2 {
  color: var(--primary);
  font-size: var(--heading-size);
  margin-top: 30px;
  margin-bottom: 12px;
  border-left: 4px solid var(--accent);
  padding-left: 12px;
}
.meta {
  color: var(--secondary);
  font-size: 0.9em;
  margin-bottom: 30px;
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin: 20px 0;
}
.kpi-card {
  background: var(--primary);
  color: white;
  padding: 20px;
  border-radius: 8px;
  text-align: center;
}
.kpi-card .label { font-size: 0.85em; opacity: 0.9; }
.kpi-card .value { font-size: 1.8em; font-weight: bold; margin-top: 6px; }
.kpi-card .unit { font-size: 0.8em; opacity: 0.8; }
.chart-container, .table-container {
  margin: 20px 0;
  text-align: center;
}
.chart-container img, .table-container img {
  max-width: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 16px 0;
  font-size: 0.9em;
}
th {
  background: var(--primary);
  color: white;
  padding: 10px 12px;
  text-align: left;
}
td {
  padding: 8px 12px;
  border-bottom: 1px solid #e0e0e0;
}
tr:nth-child(even) td { background: rgba(0,0,0,0.02); }
.content-block { margin: 12px 0; }
.footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #ddd;
  color: #888;
  font-size: 0.85em;
  text-align: center;
}
</style>
</head>
<body>
<h1>{{ title }}</h1>
<div class="meta">数据来源: {{ data_source }} | 生成日期: {{ created }} | 风格: {{ style }}</div>

{% for section in sections %}
<h2>{{ loop.index }}. {{ section.title }}</h2>

{% if section.content_type == "text" %}
<div class="content-block">{{ section.content | replace('\\n', '<br>') }}</div>

{% elif section.content_type == "summary" %}
<div class="content-block">{{ section.content | replace('\\n', '<br>') }}</div>

{% elif section.content_type == "kpi" %}
<div class="kpi-grid">
{% for kpi in section.kpis %}
<div class="kpi-card">
  <div class="label">{{ kpi.label }}</div>
  <div class="value">{{ kpi.value }}</div>
  <div class="unit">{{ kpi.unit }}</div>
</div>
{% endfor %}
</div>

{% elif section.content_type == "chart" %}
{% if section.chart_path %}
<div class="chart-container">
  <img src="{{ section.chart_path }}" alt="{{ section.title }}">
</div>
{% endif %}
<div class="content-block">{{ section.content }}</div>

{% elif section.content_type == "table" %}
{% if section.table_path %}
<div class="table-container">
  <img src="{{ section.table_path }}" alt="{{ section.title }}">
</div>
{% endif %}
{% if section.table_data %}
<table>
<thead><tr>{% for h in section.table_data.headers %}<th>{{ h }}</th>{% endfor %}</tr></thead>
<tbody>
{% for row in section.table_data.rows %}
<tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
{% endfor %}
</tbody>
</table>
{% endif %}

{% endif %}
{% endfor %}

<div class="footer">本报告由 data-report-creator 自动生成</div>
</body>
</html>
"""


def export_markdown(composed: dict, output_path: Path) -> Path:
    template = Template(MARKDOWN_TEMPLATE)
    content = template.render(**composed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def export_html(composed: dict, output_path: Path) -> Path:
    template = Template(HTML_TEMPLATE)
    content = template.render(**composed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def export_pdf(composed: dict, output_path: Path) -> Path:
    html_path = output_path.with_suffix(".html")
    export_html(composed, html_path)

    # Try WeasyPrint first (best quality, needs GTK3 on Windows)
    try:
        from weasyprint import HTML
        HTML(str(html_path)).write_pdf(str(output_path))
        return output_path
    except ImportError:
        pass
    except Exception as exc:
        print(f"[WARN] WeasyPrint PDF export failed: {exc}")

    # Fallback: xhtml2pdf (pure Python, no external C libraries needed)
    try:
        from xhtml2pdf import pisa
        html_content = html_path.read_text(encoding="utf-8")
        with open(output_path, "wb") as f:
            pisa_status = pisa.CreatePDF(html_content, dest=f)
        if pisa_status.err:
            print(f"[WARN] xhtml2pdf reported {pisa_status.err} errors")
        print("[INFO] PDF exported via xhtml2pdf (fallback)")
        return output_path
    except ImportError:
        print("[WARN] PDF export requires weasyprint or xhtml2pdf:")
        print("       pip install weasyprint   (best quality, needs GTK3 on Windows)")
        print("       pip install xhtml2pdf    (pure Python, no extra deps)")
        return html_path
    except Exception as exc:
        print(f"[WARN] xhtml2pdf PDF export failed: {exc}")
        print("[INFO] Try: pip install weasyprint (needs GTK3) or pip install xhtml2pdf")
        return html_path


EXPORTERS = {
    "markdown": export_markdown,
    "html": export_html,
    "pdf": export_pdf,
}


def export_report(composed: dict, work_dir: Path, formats: list[str]) -> list[Path]:
    outputs = []
    for fmt in formats:
        if fmt not in EXPORTERS:
            print(f"[WARN] Unknown format: {fmt}, skipping")
            continue
        ext = {"markdown": ".md", "html": ".html", "pdf": ".pdf"}[fmt]
        output_path = work_dir / f"report{ext}"
        try:
            result = EXPORTERS[fmt](composed, output_path)
            outputs.append(result)
            print(f"[OK] Exported {fmt}: {result}")
        except Exception as exc:
            print(f"[FAIL] Export {fmt} failed: {exc}")
    return outputs
