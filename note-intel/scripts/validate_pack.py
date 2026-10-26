#!/usr/bin/env python3
"""
NoteIntel - 素材包校验器
校验MD素材包的结构完整性、引用可追溯性、占位符残留、配额合规
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os


REQUIRED_SECTIONS = ["摘要", "核心事实", "创作选题"]
OPTIONAL_SECTIONS = ["原文引用", "风险提示"]
PLACEHOLDER_PATTERN = re.compile(r'\{[a-z_]+\}')
LOCATION_PATTERN = re.compile(r'📍|原文定位|来源位置|第\d+段')
QUOTE_PATTERN = re.compile(r'📎|原文引用')


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None


def check_structure_complete(content):
    errors = []
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in content:
            errors.append(f"缺少必需模块: {section}")
    return len(errors) == 0, errors


def check_no_placeholders(content):
    matches = PLACEHOLDER_PATTERN.findall(content)
    if matches:
        return False, [f"发现占位符残留: {', '.join(matches)}"]
    return True, []


def check_quotes_traceable(content):
    facts_section = extract_section(content, "核心事实")
    if not facts_section:
        return True, []

    fact_items = re.split(r'\n(?=\d+\.|【|^- )', facts_section)
    fact_items = [item.strip() for item in fact_items if item.strip()]

    missing = []
    for i, item in enumerate(fact_items, 1):
        if not LOCATION_PATTERN.search(item):
            missing.append(f"事实#{i} 缺少原文定位标注")

    if missing:
        return False, missing
    return True, []


def check_facts_within_quota(content, quotas=None):
    if not quotas:
        return True, []

    facts_section = extract_section(content, "核心事实")
    topics_section = extract_section(content, "创作选题")

    errors = []

    if facts_section and quotas.get("core_facts"):
        fact_count = count_items(facts_section)
        quota_range = quotas["core_facts"]
        min_q, max_q = parse_quota_range(quota_range)
        if fact_count < min_q or fact_count > max_q:
            errors.append(f"核心事实数量({fact_count})超出配额范围({quota_range})")

    if topics_section and quotas.get("topics"):
        topic_count = count_items(topics_section)
        quota_range = quotas["topics"]
        min_q, max_q = parse_quota_range(quota_range)
        if topic_count < min_q or topic_count > max_q:
            errors.append(f"创作选题数量({topic_count})超出配额范围({quota_range})")

    return len(errors) == 0, errors


def extract_section(content, section_name):
    pattern = rf'## {re.escape(section_name)}\s*\n(.*?)(?=\n## |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def count_items(section_content):
    items = re.split(r'\n(?=\d+\.|【|^- )', section_content)
    items = [item.strip() for item in items if item.strip() and len(item.strip()) > 5]
    return len(items)


def parse_quota_range(quota_str):
    match = re.match(r'(\d+)-(\d+)', str(quota_str))
    if match:
        return int(match.group(1)), int(match.group(2))
    match = re.match(r'(\d+)', str(quota_str))
    if match:
        return int(match.group(1)), int(match.group(1))
    return 0, 999


def check_topic_has_dimensions(content):
    topics_section = extract_section(content, "创作选题")
    if not topics_section:
        return True, []

    topic_items = re.split(r'\n(?=\d+\.|【|^- )', topics_section)
    topic_items = [item.strip() for item in topic_items if item.strip() and len(item.strip()) > 5]

    missing = []
    required_dims = ["切入角度", "目标受众", "内容形式", "关联事实"]
    for i, item in enumerate(topic_items, 1):
        for dim in required_dims:
            if dim not in item:
                missing.append(f"选题#{i} 缺少维度: {dim}")

    if missing:
        return False, missing
    return True, []


def validate(pack_path, quotas=None):
    content = read_file(pack_path)
    if content is None:
        return {
            "valid": False,
            "errors": [f"无法读取文件: {pack_path}"],
            "warnings": [],
            "checks": {}
        }

    checks = {}
    all_errors = []
    all_warnings = []

    ok, errors = check_structure_complete(content)
    checks["structure_complete"] = ok
    all_errors.extend(errors)

    ok, errors = check_no_placeholders(content)
    checks["no_placeholders"] = ok
    all_errors.extend(errors)

    ok, errors = check_quotes_traceable(content)
    checks["quotes_traceable"] = ok
    all_errors.extend(errors)

    ok, errors = check_facts_within_quota(content, quotas)
    checks["facts_within_quota"] = ok
    all_errors.extend(errors)

    ok, errors = check_topic_has_dimensions(content)
    checks["topic_has_dimensions"] = ok
    all_warnings.extend(errors)

    optional_present = {}
    for section in OPTIONAL_SECTIONS:
        optional_present[section] = f"## {section}" in content
    checks["optional_sections"] = optional_present

    return {
        "valid": len(all_errors) == 0,
        "errors": all_errors,
        "warnings": all_warnings,
        "checks": checks
    }


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 素材包校验器")
    parser.add_argument("--pack", required=True, help="MD素材包文件路径")
    parser.add_argument("--quotas", help="配额表JSON文件路径（可选）")
    args = parser.parse_args()

    quotas = None
    if args.quotas and os.path.isfile(args.quotas):
        with open(args.quotas, 'r', encoding='utf-8') as f:
            quotas_data = json.load(f)
            quotas = quotas_data.get("quotas", quotas_data)

    result = validate(args.pack, quotas)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
