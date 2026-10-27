#!/usr/bin/env python3
"""
NoteIntel - 素材包校验器 v0.3
校验MD素材包的结构完整性、引用可追溯性、占位符残留、配额合规
增强：选题-事实关联一致性、摘要长度合理性、选题标题唯一性、事实编号引用有效性
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
FACT_REF_LINE_PATTERN = re.compile(r'关联事实[：:]\s*(.+)')
FACT_NUM_PATTERN = re.compile(r'#?(\d+)')


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None


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


def split_items(section_content):
    items = re.split(r'\n(?=\d+\.|【|^- )', section_content)
    return [item.strip() for item in items if item.strip() and len(item.strip()) > 5]


# ============================================================
# 原有校验规则
# ============================================================

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

    fact_items = split_items(facts_section)
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


def check_topic_has_dimensions(content):
    topics_section = extract_section(content, "创作选题")
    if not topics_section:
        return True, []

    topic_items = split_items(topics_section)
    missing = []
    required_dims = ["切入角度", "目标受众", "内容形式", "关联事实"]
    for i, item in enumerate(topic_items, 1):
        for dim in required_dims:
            if dim not in item:
                missing.append(f"选题#{i} 缺少维度: {dim}")

    if missing:
        return False, missing
    return True, []


# ============================================================
# 新增校验规则
# ============================================================

def check_topic_fact_references(content):
    topics_section = extract_section(content, "创作选题")
    facts_section = extract_section(content, "核心事实")
    if not topics_section or not facts_section:
        return True, []

    fact_count = count_items(facts_section)
    topic_items = split_items(topics_section)

    errors = []
    for i, item in enumerate(topic_items, 1):
        ref_line = FACT_REF_LINE_PATTERN.search(item)
        if not ref_line:
            continue
        refs = FACT_NUM_PATTERN.findall(ref_line.group(1))
        for ref_num in refs:
            ref_int = int(ref_num)
            if ref_int < 1 or ref_int > fact_count:
                errors.append(f"选题#{i} 引用了不存在的事实#{ref_int}（共{fact_count}条事实）")

    return len(errors) == 0, errors


def check_summary_length(content):
    summary_section = extract_section(content, "摘要")
    if not summary_section:
        return True, []

    summary_text = re.sub(r'[>\s#\-|]', '', summary_section).strip()
    char_count = len(summary_text)

    warnings = []
    if char_count < 30:
        warnings.append(f"摘要过短({char_count}字)，建议至少30字以提供有效概括")
    if char_count > 300:
        warnings.append(f"摘要过长({char_count}字)，建议不超过300字以保持精炼")

    return len(warnings) == 0, warnings


def check_topic_title_uniqueness(content):
    topics_section = extract_section(content, "创作选题")
    if not topics_section:
        return True, []

    topic_items = split_items(topics_section)
    titles = []
    for item in topic_items:
        title_match = re.search(r'\d+\.\s*\*\*(.+?)\*\*', item)
        if title_match:
            titles.append(title_match.group(1).strip())
        else:
            first_line = item.split('\n')[0].strip()
            titles.append(first_line[:50])

    errors = []
    seen = {}
    for i, title in enumerate(titles, 1):
        if title in seen:
            errors.append(f"选题#{i} 与选题#{seen[title]} 标题重复: \"{title}\"")
        else:
            seen[title] = i

    return len(errors) == 0, errors


def check_facts_have_quotes(content):
    facts_section = extract_section(content, "核心事实")
    if not facts_section:
        return True, []

    fact_items = split_items(facts_section)
    warnings = []
    for i, item in enumerate(fact_items, 1):
        if not QUOTE_PATTERN.search(item):
            warnings.append(f"事实#{i} 缺少原文引用标注(📎)")

    return len(warnings) == 0, warnings


def check_no_fabricated_data(content, source_text=None):
    if not source_text:
        return True, []

    facts_section = extract_section(content, "核心事实")
    if not facts_section:
        return True, []

    fact_items = split_items(facts_section)
    errors = []
    for i, item in enumerate(fact_items, 1):
        quote_match = re.search(r'📎.*?["\u201c\u201d\'\u300c\u300d\u300e\u300f](.+?)["\u201c\u201d\'\u300c\u300d\u300e\u300f]', item)
        if quote_match:
            quote_text = quote_match.group(1).strip()
            if not quote_text:
                continue
            segments = re.split(r'\[.*?\]', quote_text)
            segments = [s.strip() for s in segments if s.strip()]
            normalized_source = re.sub(r'[ \t]+', '', source_text)
            for seg in segments:
                normalized_seg = re.sub(r'[ \t]+', '', seg)
                if normalized_seg not in normalized_source:
                    errors.append(f"事实#{i} 的原文引用片段在素材中找不到对应内容，可能为虚构")
                    break

    return len(errors) == 0, errors


def check_optional_section_content(content):
    warnings = []
    for section in OPTIONAL_SECTIONS:
        section_content = extract_section(content, section)
        if section_content:
            items = split_items(section_content)
            if len(items) == 0:
                warnings.append(f"模块 \"{section}\" 存在但内容为空，建议删除该模块")

    return len(warnings) == 0, warnings


# ============================================================
# 主校验函数
# ============================================================

def validate(pack_path, quotas=None, source_text=None):
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

    ok, errors = check_topic_fact_references(content)
    checks["topic_fact_references"] = ok
    all_errors.extend(errors)

    ok, warnings = check_summary_length(content)
    checks["summary_length"] = ok
    all_warnings.extend(warnings)

    ok, errors = check_topic_title_uniqueness(content)
    checks["topic_title_uniqueness"] = ok
    all_errors.extend(errors)

    ok, warnings = check_facts_have_quotes(content)
    checks["facts_have_quotes"] = ok
    all_warnings.extend(warnings)

    if source_text:
        ok, errors = check_no_fabricated_data(content, source_text)
        checks["no_fabricated_data"] = ok
        all_errors.extend(errors)
    else:
        checks["no_fabricated_data"] = "skipped (no source text)"

    ok, warnings = check_optional_section_content(content)
    checks["optional_section_content"] = ok
    all_warnings.extend(warnings)

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
    parser = argparse.ArgumentParser(description="NoteIntel 素材包校验器 v0.3")
    parser.add_argument("--pack", required=True, help="MD素材包文件路径")
    parser.add_argument("--quotas", help="配额表JSON文件路径（可选）")
    parser.add_argument("--source", help="原始素材文本文件路径，用于虚构检测（可选）")
    args = parser.parse_args()

    quotas = None
    if args.quotas and os.path.isfile(args.quotas):
        with open(args.quotas, 'r', encoding='utf-8') as f:
            quotas_data = json.load(f)
            quotas = quotas_data.get("quotas", quotas_data)

    source_text = None
    if args.source and os.path.isfile(args.source):
        with open(args.source, 'r', encoding='utf-8') as f:
            source_text = f.read()

    result = validate(args.pack, quotas, source_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
