#!/usr/bin/env python3
"""Report composer — assembles content, charts, and styling into a unified report.

Takes report.json, generates charts, builds structured content blocks,
and prepares data for export.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from charts import generate_chart, generate_table_image
from styler import get_style
from data_loader import load_data, summarize_column


def compose_section(section: dict, work_dir: Path, data: dict | None = None) -> dict:
    content_type = section.get("content_type", "text")
    style_id = section.get("style", "corporate")

    composed: dict[str, Any] = {
        "id": section["id"],
        "title": section["title"],
        "content_type": content_type,
        "style": style_id,
        "content": section.get("content", ""),
    }

    if content_type == "chart":
        chart_config = section.get("chart_config", {})
        charts_dir = work_dir / "charts"
        output_path = charts_dir / f"{section['id']}.png"
        try:
            generate_chart(chart_config, output_path, style_id)
            composed["chart_path"] = str(output_path.relative_to(work_dir))
            composed["chart_type"] = chart_config.get("type", "bar")
        except Exception as exc:
            composed["chart_error"] = str(exc)
            composed["chart_path"] = None

    elif content_type == "table":
        table_data = section.get("table_config", {})
        if not table_data and data:
            table_data = _auto_table(section, data)
        if table_data:
            charts_dir = work_dir / "charts"
            output_path = charts_dir / f"{section['id']}_table.png"
            try:
                style_profile = get_style(style_id)
                generate_table_image(table_data, output_path, style_profile)
                composed["table_path"] = str(output_path.relative_to(work_dir))
            except Exception as exc:
                composed["table_error"] = str(exc)
        composed["table_data"] = table_data

    elif content_type == "kpi":
        kpis = section.get("kpi_config", [])
        if not kpis and data:
            kpis = _auto_kpi(section, data)
        composed["kpis"] = kpis

    elif content_type == "summary":
        composed["content"] = section.get("content", "")

    return composed


def _auto_table(section: dict, data: dict) -> dict:
    rows = data.get("rows", [])
    columns = data.get("columns", [])
    return {
        "title": section.get("title", "数据表"),
        "headers": columns[:8],
        "rows": [r[:8] for r in rows[:15]],
    }


def _auto_kpi(section: dict, data: dict) -> list[dict]:
    profile = data.get("profile", {})
    return [
        {"label": "总行数", "value": profile.get("row_count", 0), "unit": "行"},
        {"label": "总列数", "value": profile.get("column_count", 0), "unit": "列"},
        {"label": "完整度", "value": f"{profile.get('completeness', 0):.1%}", "unit": ""},
        {"label": "缺失值", "value": profile.get("missing_cells", 0), "unit": "个"},
    ]


def compose_report(report: dict, work_dir: Path) -> dict:
    data = None
    data_source = report.get("data_source", "")
    if data_source and Path(data_source).exists():
        try:
            data = load_data(data_source)
        except Exception:
            pass

    composed_sections = []
    for section in report.get("sections", []):
        composed = compose_section(section, work_dir, data)
        composed_sections.append(composed)

    style_id = report.get("style", "corporate")
    style_profile = get_style(style_id)

    composed_report = {
        "title": report.get("title", "Untitled Report"),
        "topic": report.get("topic", ""),
        "created": report.get("created", ""),
        "data_source": data_source,
        "style": style_id,
        "style_profile": style_profile,
        "output_formats": report.get("output_formats", ["markdown", "html"]),
        "sections": composed_sections,
        "data_profile": report.get("data_profile", {}),
    }
    return composed_report


def save_composed(composed: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(composed, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return path
