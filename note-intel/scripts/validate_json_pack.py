#!/usr/bin/env python3
"""Validate the auditable JSON contract used by NoteIntel."""
import argparse
import json
import sys

REQUIRED_TOP = ("source", "summary", "facts", "topics")
FACT_REQUIRED = ("id", "claim", "location", "quote", "confidence", "status")
ALLOWED_STATUS = {"reported", "verified"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def validate(data):
    errors, warnings = [], []
    for key in REQUIRED_TOP:
        if key not in data:
            errors.append(f"缺少顶层字段: {key}")
    sources = {s.get("source_id") for s in data.get("sources", []) if isinstance(s, dict)}
    fact_ids = set()
    for i, fact in enumerate(data.get("facts", []), 1):
        if not isinstance(fact, dict):
            errors.append(f"事实#{i} 不是对象")
            continue
        for key in FACT_REQUIRED:
            if not fact.get(key):
                errors.append(f"事实#{i} 缺少字段: {key}")
        fid = fact.get("id")
        if fid in fact_ids:
            errors.append(f"事实 ID 重复: {fid}")
        fact_ids.add(fid)
        if fact.get("status") not in ALLOWED_STATUS:
            errors.append(f"事实#{i} status 无效: {fact.get('status')}")
        if fact.get("confidence") not in ALLOWED_CONFIDENCE:
            errors.append(f"事实#{i} confidence 无效: {fact.get('confidence')}")
        for sid in fact.get("source_ids", []):
            if sources and sid not in sources:
                errors.append(f"事实#{i} 引用了不存在的 source_id: {sid}")
    for i, topic in enumerate(data.get("topics", []), 1):
        if not isinstance(topic, dict):
            errors.append(f"选题#{i} 不是对象")
            continue
        for key in ("id", "title", "angle", "audience", "form", "related_facts", "value_add"):
            if not topic.get(key):
                errors.append(f"选题#{i} 缺少字段: {key}")
        refs = topic.get("related_facts", [])
        for ref in refs if isinstance(refs, list) else []:
            if ref not in fact_ids:
                errors.append(f"选题#{i} 引用了不存在的事实: {ref}")
        if not topic.get("outline") and topic.get("form") in {"图文卡片", "系列内容", "图文长文"}:
            warnings.append(f"选题#{i} 缺少可继续创作的 outline")
    for i, item in enumerate(data.get("inferences", []), 1):
        if not item.get("based_on"):
            errors.append(f"推断#{i} 缺少 based_on，无法追溯依据")
        if "原文事实" not in item.get("disclaimer", "") and "推断" not in item.get("disclaimer", ""):
            warnings.append(f"推断#{i} 建议明确标注“非原文事实”")
    if data.get("facts") and not data.get("sources"):
        warnings.append("存在事实但没有 sources 登记；建议补充来源登记")
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "counts": {"facts": len(data.get("facts", [])), "topics": len(data.get("topics", [])),
                       "viewpoints": len(data.get("viewpoints", [])), "inferences": len(data.get("inferences", [])),
                       "conflicts": len(data.get("conflicts", []))}}


def main():
    parser = argparse.ArgumentParser(description="NoteIntel JSON素材包校验器")
    parser.add_argument("--pack", required=True)
    args = parser.parse_args()
    try:
        with open(args.pack, encoding="utf-8") as f:
            result = validate(json.load(f))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [f"无法读取或解析JSON: {exc}"], "warnings": [], "counts": {}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
