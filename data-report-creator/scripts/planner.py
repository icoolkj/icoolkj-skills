#!/usr/bin/env python3
"""Report planner — generates report.json from data analysis.

Takes a data file and topic, produces a structured report plan with
sections, chart configurations, and style selection.

Analysis logic:
  - KPI cards: aggregate stats for numeric columns (sum, mean, etc.)
  - Categorical × Numeric cross-analysis: group by category, aggregate numeric
  - Numeric distribution: histogram for each numeric column
  - Correlation: scatter plot for top 2 numeric columns
  - Data table: show raw data rows
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from data_loader import load_data, profile_data, summarize_column
from styler import STYLES, print_style_menu


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and value == value


def _aggregate_by_category(
    rows: list, cat_col_idx: int, num_col_idx: int, agg: str = "sum"
) -> dict[str, float]:
    groups: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if cat_col_idx < len(r) and num_col_idx < len(r):
            cat = str(r[cat_col_idx])
            val = r[num_col_idx]
            if _is_numeric(val):
                groups[cat].append(val)
    result = {}
    for cat, vals in groups.items():
        if not vals:
            continue
        if agg == "sum":
            result[cat] = round(sum(vals), 2)
        elif agg == "mean":
            result[cat] = round(sum(vals) / len(vals), 2)
        elif agg == "count":
            result[cat] = len(vals)
        elif agg == "max":
            result[cat] = max(vals)
        elif agg == "min":
            result[cat] = min(vals)
    return result


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
    rows = data["rows"]
    numeric_cols = profile.get("numeric_columns", [])
    categorical_cols = [c for c in columns if c not in numeric_cols]

    sections = []

    # --- Cover ---
    sections.append({
        "id": "cover",
        "title": title or f"数据分析报告 — {Path(data_path).stem}",
        "content_type": "text",
        "content": f"本报告基于 {data['format']} 数据文件 {Path(data_path).name} 自动生成。\n"
                   f"数据规模: {profile['row_count']} 行 × {profile['column_count']} 列\n"
                   f"数据完整度: {profile['completeness']:.1%}",
        "style": style,
    })

    # --- KPI cards ---
    kpi_items = []
    for num_col in numeric_cols[:4]:
        col_idx = columns.index(num_col)
        values = [r[col_idx] for r in rows if col_idx < len(r) and _is_numeric(r[col_idx])]
        if values:
            kpi_items.append({
                "label": f"总{num_col}",
                "value": f"{sum(values):,.0f}",
                "unit": "",
            })
            kpi_items.append({
                "label": f"平均{num_col}",
                "value": f"{sum(values)/len(values):,.1f}",
                "unit": "",
            })
    if kpi_items:
        sections.append({
            "id": "kpi_overview",
            "title": "关键指标",
            "content_type": "kpi",
            "content": "核心数据指标概览",
            "style": style,
            "kpi_config": kpi_items[:8],
        })

    # --- Data overview ---
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
                   f"数值列: {', '.join(numeric_cols) if numeric_cols else '无'}\n"
                   f"分类列: {', '.join(categorical_cols) if categorical_cols else '无'}",
        "style": style,
    })

    # --- Categorical × Numeric cross-analysis ---
    # For each categorical column, group by it and aggregate the first numeric column
    if numeric_cols and categorical_cols:
        primary_num = numeric_cols[0]
        primary_num_idx = columns.index(primary_num)
        for cat_col in categorical_cols[:3]:
            cat_idx = columns.index(cat_col)
            agg_data = _aggregate_by_category(rows, cat_idx, primary_num_idx, "sum")
            if agg_data:
                labels = list(agg_data.keys())
                values = list(agg_data.values())
                sections.append({
                    "id": f"cross_{cat_col}",
                    "title": f"{cat_col} × {primary_num} 分析",
                    "content_type": "chart",
                    "content": f"按 {cat_col} 分组的 {primary_num} 汇总分析。"
                               f"共 {len(labels)} 个分组，"
                               f"总{primary_num}: {sum(values):,.0f}",
                    "style": style,
                    "chart_config": {
                        "type": "bar",
                        "data": {
                            "title": f"按 {cat_col} 分组的 {primary_num}",
                            "labels": labels,
                            "values": values,
                            "x_label": cat_col,
                            "y_label": f"{primary_num}（合计）",
                        },
                    },
                })

    # --- Numeric distribution (histogram) ---
    for num_col in numeric_cols[:3]:
        col_idx = columns.index(num_col)
        values = [r[col_idx] for r in rows if col_idx < len(r) and _is_numeric(r[col_idx])]
        if values:
            sections.append({
                "id": f"dist_{num_col}",
                "title": f"{num_col} 分布分析",
                "content_type": "chart",
                "content": f"数值列 {num_col} 的分布分析。"
                           f"最小值: {min(values)}, "
                           f"最大值: {max(values)}, "
                           f"均值: {round(sum(values)/len(values), 2)}",
                "style": style,
                "chart_config": {
                    "type": "histogram",
                    "data": {
                        "title": f"{num_col} 分布",
                        "values": values,
                        "x_label": num_col,
                        "y_label": "频次",
                        "bins": min(20, max(5, len(values) // 3)),
                    },
                },
            })

    # --- Correlation scatter ---
    if len(numeric_cols) >= 2:
        x_col, y_col = numeric_cols[0], numeric_cols[1]
        x_idx, y_idx = columns.index(x_col), columns.index(y_col)
        x_values = [r[x_idx] for r in rows if x_idx < len(r) and _is_numeric(r[x_idx])]
        y_values = [r[y_idx] for r in rows if y_idx < len(r) and _is_numeric(r[y_idx])]
        if x_values and y_values:
            sections.append({
                "id": "correlation",
                "title": f"{x_col} 与 {y_col} 相关性",
                "content_type": "chart",
                "content": f"{x_col} 与 {y_col} 的散点关系图，用于分析两数值列的相关性",
                "style": style,
                "chart_config": {
                    "type": "scatter",
                    "data": {
                        "title": f"{x_col} vs {y_col}",
                        "x_values": x_values,
                        "y_values": y_values,
                        "x_label": x_col,
                        "y_label": y_col,
                    },
                },
            })

    # --- Data table ---
    sections.append({
        "id": "data_table",
        "title": "原始数据",
        "content_type": "table",
        "content": f"原始数据表（前 {min(len(rows), 20)} 行）",
        "style": style,
        "table_config": {
            "title": "原始数据",
            "headers": columns,
            "rows": [r[:len(columns)] for r in rows[:20]],
        },
    })

    # --- Conclusion ---
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
