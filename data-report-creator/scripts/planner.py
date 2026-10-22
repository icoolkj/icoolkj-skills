#!/usr/bin/env python3
"""Report planner — generates report.json from data analysis.

Takes a data file and topic, produces a structured report plan with
sections, chart configurations, and style selection.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from data_loader import load_data, profile_data, summarize_column
from styler import STYLES, print_style_menu


def build_report_plan(
    data_path: str,
    *,
    title: str | None = None,
    style: str = "corporate",
    topic: str | None = None,
    output_formats: list[str] | None = None,
) -> dict:
    data = load_data(data_path)
    profile = data["profile"]
    columns = data["columns"]
    numeric_cols = profile.get("numeric_columns", [])

    sections = []

    sections.append({
        "id": "cover",
        "title": title or f"数据分析报告 — {Path(data_path).stem}",
        "content_type": "text",
        "content": f"本报告基于 {data['format']} 数据文件 {Path(data_path).name} 自动生成。\n"
                   f"数据规模: {profile['row_count']} 行 × {profile['column_count']} 列\n"
                   f"数据完整度: {profile['completeness']:.1%}",
        "style": style,
    })

    sections.append({
        "id": "data_overview",
        "title": "数据概览",
        "content_type": "summary",
        "content": f"数据来源: {data_path}\n"
                   f"格式: {data['format']}\n"
                   f"行数: {profile['row_count']}\n"
                   f"列数: {profile['column_count']}\n"
                   f"缺失值: {profile['missing_cells']} 个单元格\n"
                   f"完整度: {profile['completeness']:.1%}\n"
                   f"数值列: {', '.join(numeric_cols) if numeric_cols else '无'}",
        "style": style,
    })

    for col_idx, col_name in enumerate(columns[:5]):
        col_summary = summarize_column(data, col_idx)
        if col_summary["type"] == "numeric":
            sections.append({
                "id": f"col_{col_idx+1}",
                "title": f"{col_name} — 数值分析",
                "content_type": "chart",
                "content": f"数值列 {col_name} 的分布分析。"
                           f"最小值: {col_summary.get('min', 'N/A')}, "
                           f"最大值: {col_summary.get('max', 'N/A')}, "
                           f"均值: {col_summary.get('mean', 'N/A')}",
                "style": style,
                "chart_config": {
                    "type": "histogram",
                    "data": {
                        "title": f"{col_name} 分布",
                        "values": [r[col_idx] for r in data["rows"]
                                   if col_idx < len(r) and isinstance(r[col_idx], (int, float))],
                        "x_label": col_name,
                        "y_label": "频次",
                        "bins": 20,
                    },
                },
            })
        else:
            top_values = col_summary.get("top_values", {})
            sections.append({
                "id": f"col_{col_idx+1}",
                "title": f"{col_name} — 分类分析",
                "content_type": "chart",
                "content": f"分类列 {col_name} 的分布分析。"
                           f"唯一值: {col_summary.get('unique_count', 0)} 个",
                "style": style,
                "chart_config": {
                    "type": "bar",
                    "data": {
                        "title": f"{col_name} 分布 (Top 10)",
                        "labels": list(top_values.keys())[:10],
                        "values": list(top_values.values())[:10],
                        "x_label": col_name,
                        "y_label": "频次",
                    },
                },
            })

    if len(numeric_cols) >= 2:
        sections.append({
            "id": "correlation",
            "title": "数值列相关性",
            "content_type": "chart",
            "content": f"{numeric_cols[0]} 与 {numeric_cols[1]} 的散点关系图",
            "style": style,
            "chart_config": {
                "type": "scatter",
                "data": {
                    "title": f"{numeric_cols[0]} vs {numeric_cols[1]}",
                    "x_values": [r[columns.index(numeric_cols[0])] for r in data["rows"]
                                 if isinstance(r[columns.index(numeric_cols[0])], (int, float))],
                    "y_values": [r[columns.index(numeric_cols[1])] for r in data["rows"]
                                 if isinstance(r[columns.index(numeric_cols[1])], (int, float))],
                    "x_label": numeric_cols[0],
                    "y_label": numeric_cols[1],
                },
            },
        })

    sections.append({
        "id": "conclusion",
        "title": "结论与建议",
        "content_type": "text",
        "content": "[填写] 基于以上数据分析的结论和建议",
        "style": style,
    })

    report = {
        "title": title or f"数据分析报告 — {Path(data_path).stem}",
        "topic": topic or Path(data_path).stem,
        "created": datetime.now().strftime("%Y-%m-%d"),
        "data_source": str(data_path),
        "data_format": data["format"],
        "style": style,
        "output_formats": output_formats or ["markdown", "html"],
        "sections": sections,
        "data_profile": profile,
    }
    return report


def validate_report(report: dict) -> list[str]:
    issues = []
    required_top = ["title", "data_source", "sections", "style"]
    for field in required_top:
        if field not in report:
            issues.append(f"缺少顶层字段: {field}")
    sections = report.get("sections", [])
    if not sections:
        issues.append("报告没有章节")
    for i, section in enumerate(sections, 1):
        for field in ["id", "title", "content_type"]:
            if not section.get(field):
                issues.append(f"第{i}节缺少字段: {field}")
    return issues


def save_report(report: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def print_report_summary(report: dict) -> None:
    print(f"\n{'='*60}")
    print(f"  报告规划摘要: {report.get('title', 'Untitled')}")
    print(f"{'='*60}")
    print(f"  数据源: {report.get('data_source', '?')}")
    print(f"  格式: {report.get('data_format', '?')}")
    print(f"  风格: {report.get('style', '?')}")
    print(f"  输出格式: {', '.join(report.get('output_formats', ['markdown']))}")
    print(f"  章节数: {len(report.get('sections', []))}")
    print(f"{'-'*60}")
    for i, section in enumerate(report.get("sections", []), 1):
        print(f"  {i:2d}. [{section.get('id','?'):14s}] {section.get('title','?')[:40]}")
        print(f"      类型: {section.get('content_type','?')}  风格: {section.get('style','?')}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Report planner for data analysis")
    parser.add_argument("data_file", help="Path to CSV/Excel/JSON data file")
    parser.add_argument("--output", "-o", required=True, help="Output report JSON path")
    parser.add_argument("--title", help="Report title")
    parser.add_argument("--style", default="corporate", help="Report visual style")
    parser.add_argument("--topic", help="Report topic/keyword")
    parser.add_argument("--formats", nargs="*", default=["markdown", "html"],
                        help="Output formats: markdown, html, pdf")
    args = parser.parse_args()

    print_style_menu()

    report = build_report_plan(
        args.data_file, title=args.title, style=args.style,
        topic=args.topic, output_formats=args.formats,
    )
    save_report(report, Path(args.output))
    print_report_summary(report)
    print(f"[OK] Report plan saved: {args.output}")
