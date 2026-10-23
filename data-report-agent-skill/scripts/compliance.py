#!/usr/bin/env python3
"""Compliance checker for data analysis reports.

Validates data quality, report structure, content guidelines, and format rules.
Fails the pipeline if critical issues are found.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


BLOCKED_WORDS = (
    "最佳", "最强", "第一", "顶级", "100%", "百分百", "绝对", " guaranteed",
    "确保盈利", "零风险", "无风险", "稳赚",
)

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.I)

PLACEHOLDER_MARK = "[填写]"

REQUIRED_SECTION_FIELDS = ("id", "title", "content_type", "style")


def check_data_quality(data: dict) -> list[str]:
    issues = []
    profile = data.get("profile", {})
    completeness = profile.get("completeness", 1.0)
    if completeness < 0.5:
        issues.append(f"数据完整度过低: {completeness:.1%}（建议≥50%）")
    if profile.get("row_count", 0) == 0:
        issues.append("数据行数为0，无法生成报告")
    if profile.get("column_count", 0) == 0:
        issues.append("数据列数为0，无法生成报告")
    return issues


def check_text_content(text: str) -> list[str]:
    issues = []
    if URL_PATTERN.search(text or ""):
        issues.append("正文包含URL链接，请移至 references 字段")
    if PLACEHOLDER_MARK in (text or ""):
        issues.append("正文包含未替换的占位符 [填写]，请由 Agent 撰写正式内容后重新提交")
    for word in BLOCKED_WORDS:
        if word.lower() in (text or "").lower():
            issues.append(f"包含敏感/绝对化用语: {word}")
    return issues


def check_report_structure(report: dict) -> list[str]:
    issues = []
    required_top = ["title", "data_source", "sections"]
    for field in required_top:
        if field not in report:
            issues.append(f"缺少顶层字段: {field}")
    sections = report.get("sections", [])
    if not sections:
        issues.append("报告没有章节，至少需要1个章节")
    for i, section in enumerate(sections, 1):
        for field in REQUIRED_SECTION_FIELDS:
            if not section.get(field):
                issues.append(f"第{i}节缺少必填字段: {field}")
        content_type = section.get("content_type", "")
        valid_types = ("text", "table", "chart", "summary", "kpi", "image")
        if content_type and content_type not in valid_types:
            issues.append(f"第{i}节 content_type 无效: {content_type}（可选: {valid_types}）")
    return issues


def check_chart_config(section: dict) -> list[str]:
    issues = []
    if section.get("content_type") != "chart":
        return issues
    chart = section.get("chart_config", {})
    if not chart:
        issues.append(f"章节 {section.get('id', '?')} 是图表类型但缺少 chart_config")
        return issues
    chart_type = chart.get("type", "")
    valid_types = ("bar", "line", "pie", "scatter", "histogram", "area", "table")
    if chart_type not in valid_types:
        issues.append(f"章节 {section.get('id', '?')} 图表类型无效: {chart_type}")
    chart_data = chart.get("data", {})
    if not chart_data:
        issues.append(f"章节 {section.get('id', '?')} 图表缺少 data 配置")
    return issues


def check_report(report: dict, data: dict | None = None) -> list[str]:
    issues = []
    issues.extend(check_report_structure(report))
    issues.extend(check_text_content(report.get("title", "")))
    for section in report.get("sections", []):
        issues.extend(check_text_content(section.get("content", "")))
        issues.extend(check_text_content(section.get("title", "")))
        issues.extend(check_chart_config(section))
    if data:
        issues.extend(check_data_quality(data))
    return issues


def validate_report_file(report_path: str | Path, data: dict | None = None) -> int:
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    issues = check_report(report, data)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print("[OK] 合规检查通过")
    section_count = len(report.get("sections", []))
    print(f"章节数: {section_count}")
    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compliance check for report JSON")
    parser.add_argument("report_json", help="Path to report JSON")
    args = parser.parse_args()
    raise SystemExit(validate_report_file(args.report_json))
