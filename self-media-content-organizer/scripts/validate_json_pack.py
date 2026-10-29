#!/usr/bin/env python3
"""Validate the NoteIntel JSON contract in separate structural and semantic layers."""
import argparse
import json
import re
import sys

REQUIRED_TOP = ("source", "summary", "facts", "topics")
FACT_REQUIRED = ("id", "claim", "location", "quote", "confidence", "status", "source_ids")
LIST_FIELDS = ("sources", "facts", "topics", "quotes", "risks", "viewpoints", "inferences", "verification_gaps", "conflicts", "next_actions", "platform_adaptations", "source_images", "derived_visuals", "generated_visuals", "card_plan")
ALLOWED_STATUS = {"reported", "verified"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
FACT_REF_KEYS = ("related_facts", "based_on", "fact_ids")


def add_type_error(errors, label, expected, actual):
    errors.append(f"{label} 类型错误：应为 {expected}，实际为 {type(actual).__name__}")


def validate(data):
    structure_errors, semantic_risks, warnings = [], [], []
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["顶层 JSON 必须是对象"], "structure_errors": ["顶层 JSON 必须是对象"], "semantic_risks": [], "warnings": [], "counts": {}}
    for key in REQUIRED_TOP:
        if key not in data:
            structure_errors.append(f"缺少顶层字段: {key}")
    for key in LIST_FIELDS:
        if key in data and not isinstance(data[key], list):
            add_type_error(structure_errors, f"顶层字段 {key}", "数组", data[key])
    sources = data.get("sources", [])
    source_ids = set()
    if isinstance(sources, list):
        for i, source in enumerate(sources, 1):
            if not isinstance(source, dict):
                add_type_error(structure_errors, f"来源#{i}", "对象", source); continue
            sid = source.get("source_id")
            if not isinstance(sid, str) or not sid:
                structure_errors.append(f"来源#{i} source_id 必须是非空字符串")
            elif sid in source_ids:
                structure_errors.append(f"来源 ID 重复: {sid}")
            else: source_ids.add(sid)
    facts = data.get("facts", [])
    fact_ids = set()
    if isinstance(facts, list):
        for i, fact in enumerate(facts, 1):
            if not isinstance(fact, dict):
                add_type_error(structure_errors, f"事实#{i}", "对象", fact); continue
            for key in FACT_REQUIRED:
                if key not in fact or fact[key] in (None, "", []): structure_errors.append(f"事实#{i} 缺少字段: {key}")
            fid = fact.get("id")
            if not isinstance(fid, str) or not ID_PATTERN.fullmatch(fid or ""):
                structure_errors.append(f"事实#{i} id 必须是可用字符串 ID")
            elif fid in fact_ids: structure_errors.append(f"事实 ID 重复: {fid}")
            else: fact_ids.add(fid)
            for key in ("claim", "location", "quote"):
                if key in fact and not isinstance(fact[key], str): add_type_error(structure_errors, f"事实#{i}.{key}", "字符串", fact[key])
            if fact.get("status") not in ALLOWED_STATUS: structure_errors.append(f"事实#{i} status 无效: {fact.get('status')}")
            if fact.get("confidence") not in ALLOWED_CONFIDENCE: structure_errors.append(f"事实#{i} confidence 无效: {fact.get('confidence')}")
            sids = fact.get("source_ids")
            if not isinstance(sids, list) or not all(isinstance(s, str) for s in sids): add_type_error(structure_errors, f"事实#{i}.source_ids", "字符串数组", sids)
            elif not sids: structure_errors.append(f"事实#{i} source_ids 必须是非空数组")
            else:
                for sid in sids:
                    if sid not in source_ids: structure_errors.append(f"事实#{i} 引用了不存在的 source_id: {sid}")
                if isinstance(fact.get("quote"), str) and fact.get("claim") and fact["claim"] not in fact["quote"]:
                    semantic_risks.append({"type": "事实引用支持度待核查", "path": f"facts[{i - 1}]", "message": "claim 未直接包含在 quote 中，需人工判断是否为合理概括"})
    topics = data.get("topics", [])
    if isinstance(topics, list):
        for i, topic in enumerate(topics, 1):
            if not isinstance(topic, dict): add_type_error(structure_errors, f"选题#{i}", "对象", topic); continue
            for key in ("id", "title", "angle", "audience", "form", "related_facts", "value_add"):
                if key not in topic or topic[key] in (None, "", []): structure_errors.append(f"选题#{i} 缺少字段: {key}")
            refs = topic.get("related_facts")
            if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs): add_type_error(structure_errors, f"选题#{i}.related_facts", "字符串数组", refs)
            else:
                for ref in refs:
                    if ref not in fact_ids: structure_errors.append(f"选题#{i} 引用了不存在的事实: {ref}")
    for field in ("inferences", "verification_gaps", "platform_adaptations", "source_images", "derived_visuals", "generated_visuals", "card_plan"):
        for i, item in enumerate(data.get(field, []) if isinstance(data.get(field, []), list) else [], 1):
            if not isinstance(item, dict): add_type_error(structure_errors, f"{field}#{i}", "对象", item); continue
            for key in FACT_REF_KEYS:
                if key in item:
                    refs = item[key] if isinstance(item[key], list) else [item[key]]
                    for ref in refs:
                        if ref not in fact_ids: structure_errors.append(f"{field}#{i} 引用了不存在的事实: {ref}")
            for key in ("source_id",):
                if key in item and item[key] not in source_ids: structure_errors.append(f"{field}#{i} 引用了不存在的 source_id: {item[key]}")
            for key in ("source_ids",):
                if key in item:
                    for sid in item[key] if isinstance(item[key], list) else []:
                        if sid not in source_ids: structure_errors.append(f"{field}#{i} 引用了不存在的 source_id: {sid}")
    for i, item in enumerate(data.get("inferences", []) if isinstance(data.get("inferences", []), list) else [], 1):
        if not item.get("based_on"): structure_errors.append(f"推断#{i} 缺少 based_on，无法追溯依据")
        if "原文事实" not in item.get("disclaimer", "") and "推断" not in item.get("disclaimer", ""): warnings.append(f"推断#{i} 建议明确标注非原文事实")
    for i, image in enumerate(data.get("source_images", []) if isinstance(data.get("source_images", []), list) else [], 1):
        if image.get("type") not in (None, "source_image"): structure_errors.append(f"原文图片#{i} type 必须为 source_image")
        if image.get("rights_status") in ("unknown", "needs_permission") and image.get("recommended_use") == "发布": semantic_risks.append({"type": "版权发布风险", "path": f"source_images[{i - 1}]", "message": "版权状态不明，不得直接发布"})
    for i, image in enumerate(data.get("generated_visuals", []) if isinstance(data.get("generated_visuals", []), list) else [], 1):
        if image.get("not_evidence") is not True: structure_errors.append(f"AI示意图#{i} 必须声明 not_evidence=true")
        if "AI生成" not in image.get("disclosure", ""): warnings.append(f"AI示意图#{i} 建议包含明确的AI生成披露")
    result = {"valid": not structure_errors, "errors": structure_errors, "structure_errors": structure_errors, "semantic_risks": semantic_risks, "warnings": warnings,
              "counts": {"facts": len(facts) if isinstance(facts, list) else 0, "topics": len(topics) if isinstance(topics, list) else 0, "semantic_risks": len(semantic_risks)}}
    return result


def main():
    parser = argparse.ArgumentParser(description="NoteIntel JSON素材包校验器")
    parser.add_argument("--pack", required=True)
    args = parser.parse_args()
    try:
        with open(args.pack, encoding="utf-8") as handle: result = validate(json.load(handle))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [f"无法读取或解析JSON: {exc}"], "structure_errors": [f"无法读取或解析JSON: {exc}"], "semantic_risks": [], "warnings": [], "counts": {}}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]: sys.exit(1)

if __name__ == "__main__": main()
