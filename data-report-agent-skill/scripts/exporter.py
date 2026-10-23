#!/usr/bin/env python3
"""Report exporter — outputs Markdown, HTML, and PDF formats.

Uses Jinja2 templates for HTML, direct Markdown generation,
and reportlab for PDF (direct rendering, no HTML intermediate).
WeasyPrint is optional for higher-quality PDF via HTML.
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Any

from jinja2 import Template

from styler import get_style


MARKDOWN_TEMPLATE = """# {{ title }}

> 数据来源: {{ data_source }} | 生成日期: {{ created }} | 风格: {{ style }}

{% set ns = namespace(counter=0) %}
{% for section in sections %}
{% if section.id != 'cover' %}
{% set ns.counter = ns.counter + 1 %}
## {{ ns.counter }}. {{ section.title }}

{% else %}
## {{ section.title }}

{% endif %}
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
*本报告由数据分析报告 Agent 自动生成*
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

{% set ns = namespace(counter=0) %}
{% for section in sections %}
{% if section.id != 'cover' %}
{% set ns.counter = ns.counter + 1 %}
<h2>{{ ns.counter }}. {{ section.title }}</h2>

{% else %}
<h2>{{ section.title }}</h2>

{% endif %}
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

<div class="footer">本报告由数据分析报告 Agent 自动生成</div>
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
    """Export HTML with base64-embedded images for self-contained output."""
    import base64
    import copy

    composed_copy = copy.deepcopy(composed)
    sections = composed_copy.get("sections", [])
    work_dir = output_path.parent

    for section in sections:
        chart_path = section.get("chart_path")
        if chart_path:
            full_path = work_dir / chart_path
            if full_path.exists():
                with open(full_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                section["chart_path"] = f"data:image/png;base64,{b64}"
            else:
                section["chart_path"] = ""

        table_path = section.get("table_path")
        if table_path:
            full_path = work_dir / table_path
            if full_path.exists():
                with open(full_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("ascii")
                section["table_path"] = f"data:image/png;base64,{b64}"
            else:
                section["table_path"] = ""

    template = Template(HTML_TEMPLATE)
    content = template.render(**composed_copy)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _find_chinese_font() -> str:
    """Find a Chinese font path on the current system."""
    system = platform.system()
    candidates = []

    if system == "Windows":
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
    elif system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]

    for path in candidates:
        if os.path.exists(path):
            return path

    return ""


def export_pdf_reportlab(composed: dict, output_path: Path) -> Path:
    """Export PDF using reportlab — direct rendering, no HTML intermediate."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle,
        PageBreak,
    )
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Register Chinese font
    font_path = _find_chinese_font()
    font_name = "ChineseFont"
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
        except Exception:
            font_name = "Helvetica"
    else:
        font_name = "Helvetica"

    style_profile = composed.get("style_profile", {})
    primary_color = colors.HexColor(style_profile.get("primary_color", "#1a3a6b"))
    accent_color = colors.HexColor(style_profile.get("accent_color", "#e8a838"))
    text_color = colors.HexColor(style_profile.get("text_color", "#333333"))

    # Styles
    styles = getSampleStyleSheet()
    h1_style = ParagraphStyle(
        "ChineseH1", parent=styles["Heading1"],
        fontName=font_name, fontSize=20, textColor=primary_color,
        spaceAfter=6, spaceBefore=0,
    )
    h2_style = ParagraphStyle(
        "ChineseH2", parent=styles["Heading2"],
        fontName=font_name, fontSize=14, textColor=primary_color,
        spaceAfter=8, spaceBefore=20,
        leftIndent=10, borderColor=accent_color, borderWidth=0,
        borderPadding=0,
    )
    body_style = ParagraphStyle(
        "ChineseBody", parent=styles["BodyText"],
        fontName=font_name, fontSize=10, textColor=text_color,
        leading=16, spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=body_style,
        fontSize=9, textColor=colors.HexColor(style_profile.get("secondary_color", "#2d5a9e")),
    )
    kpi_label_style = ParagraphStyle(
        "KpiLabel", fontName=font_name, fontSize=8, textColor=colors.white,
        alignment=1, leading=10,
    )
    kpi_value_style = ParagraphStyle(
        "KpiValue", fontName=font_name, fontSize=14, textColor=colors.white,
        alignment=1, leading=18,
    )
    footer_style = ParagraphStyle(
        "Footer", fontName=font_name, fontSize=8, textColor=colors.grey,
        alignment=1, spaceBefore=20,
    )

    doc = SimpleDocTemplate(
        str(output_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )

    story = []

    # Title
    story.append(Paragraph(composed.get("title", "Report"), h1_style))
    meta_text = f"数据来源: {composed.get('data_source', '')} | 生成日期: {composed.get('created', '')} | 风格: {composed.get('style', '')}"
    story.append(Paragraph(meta_text, meta_style))
    story.append(Spacer(1, 10 * mm))

    work_dir = output_path.parent

    section_number = 0
    for section in composed.get("sections", []):
        ct = section.get("content_type", "text")
        section_id = section.get("id", "")

        # Section title (cover has no number, others are numbered sequentially)
        if section_id == "cover":
            story.append(Paragraph(section.get("title", ""), h2_style))
        else:
            section_number += 1
            story.append(Paragraph(f"{section_number}. {section.get('title', '')}", h2_style))

        if ct == "text" or ct == "summary":
            content = section.get("content", "").replace("\n", "<br/>")
            if content:
                story.append(Paragraph(content, body_style))

        elif ct == "kpi":
            kpis = section.get("kpis", [])
            if kpis:
                # Build KPI table: each KPI is a column
                kpi_data = [[]]
                for kpi in kpis:
                    cell = [
                        Paragraph(kpi.get("label", ""), kpi_label_style),
                        Paragraph(str(kpi.get("value", "")), kpi_value_style),
                        Paragraph(kpi.get("unit", ""), kpi_label_style),
                    ]
                    kpi_data[0].append(cell)

                col_width = (A4[0] - 4 * cm) / max(len(kpis), 1)
                kpi_table = Table(kpi_data, colWidths=[col_width] * len(kpis))
                kpi_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), primary_color),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(kpi_table)
                story.append(Spacer(1, 4 * mm))

        elif ct == "chart":
            chart_path = section.get("chart_path")
            if chart_path:
                full_path = work_dir / chart_path
                if full_path.exists():
                    try:
                        from PIL import Image as PILImage
                        import tempfile
                        pil_img = PILImage.open(str(full_path))
                        if pil_img.mode in ("RGBA", "P"):
                            pil_img = pil_img.convert("RGB")
                            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
                            pil_img.save(tmp.name)
                            img = Image(tmp.name, width=16 * cm, height=10 * cm, kind="proportional")
                        else:
                            img = Image(str(full_path), width=16 * cm, height=10 * cm, kind="proportional")
                        story.append(img)
                    except Exception as exc:
                        print(f"[WARN] Chart image embed failed for {section_id}: {exc}")
            content = section.get("content", "")
            if content:
                story.append(Paragraph(content, body_style))

        elif ct == "table":
            table_data = section.get("table_data", {})
            headers = table_data.get("headers", [])
            rows = table_data.get("rows", [])
            if headers and rows:
                # Build table data with Paragraphs for Chinese support
                table_content = [[Paragraph(str(h), ParagraphStyle(
                    "TH", fontName=font_name, fontSize=9, textColor=colors.white,
                    leading=12
                )) for h in headers]]
                for row in rows:
                    table_content.append([Paragraph(str(c), ParagraphStyle(
                        "TD", fontName=font_name, fontSize=8, textColor=text_color,
                        leading=11
                    )) for c in row])

                col_count = len(headers)
                col_width = (A4[0] - 4 * cm) / col_count
                tbl = Table(table_content, colWidths=[col_width] * col_count)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), primary_color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
                ]))
                story.append(tbl)

        story.append(Spacer(1, 4 * mm))

    # Footer
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("本报告由 data-report-creator 自动生成", footer_style))

    doc.build(story)
    return output_path


def export_pdf(composed: dict, output_path: Path) -> Path:
    """Export PDF — tries reportlab first (pure Python, no external deps),
    then WeasyPrint (higher quality, needs GTK3 on Windows)."""

    # Primary: reportlab (pure Python, reliable, no external deps)
    try:
        return export_pdf_reportlab(composed, output_path)
    except ImportError:
        pass
    except Exception as exc:
        print(f"[WARN] reportlab PDF export failed: {exc}")

    # Fallback: WeasyPrint (higher quality HTML→PDF, needs system libs)
    try:
        from weasyprint import HTML
        html_path = output_path.with_suffix(".html")
        export_html(composed, html_path)
        HTML(str(html_path)).write_pdf(str(output_path))
        print("[INFO] PDF exported via WeasyPrint")
        return output_path
    except ImportError:
        pass
    except Exception as exc:
        print(f"[WARN] WeasyPrint PDF export failed: {exc}")

    print("[WARN] PDF export requires reportlab or weasyprint:")
    print("       pip install reportlab    (recommended, pure Python)")
    print("       pip install weasyprint   (higher quality, needs GTK3)")
    return output_path.with_suffix(".html")


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
