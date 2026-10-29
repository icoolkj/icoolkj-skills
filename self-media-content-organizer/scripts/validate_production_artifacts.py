#!/usr/bin/env python3
"""Validate visual/platform production records without claiming generation happened."""
import argparse
import json
import os
import sys

STATES = {"plan", "generated", "checked", "approved", "failed"}


def validate(pack):
    errors, warnings = [], []
    facts = {f.get("id") for f in pack.get("facts", []) if isinstance(f, dict)}
    for field in ("derived_visuals", "generated_visuals", "card_plan", "platform_adaptations"):
        for i, item in enumerate(pack.get(field, []) if isinstance(pack.get(field, []), list) else [], 1):
            if not isinstance(item, dict):
                errors.append(f"{field}#{i} 必须是对象"); continue
            state = item.get("status", "plan")
            if state not in STATES: errors.append(f"{field}#{i} status 无效: {state}")
            refs = item.get("fact_ids", item.get("based_on", []))
            if isinstance(refs, str): refs = [refs]
            for ref in refs or []:
                if ref not in facts: errors.append(f"{field}#{i} 引用了不存在的事实: {ref}")
            if state in {"generated", "checked", "approved"} and not item.get("output_path"):
                errors.append(f"{field}#{i} 状态为 {state} 但缺少 output_path")
            if state in {"checked", "approved"} and not item.get("checks"):
                errors.append(f"{field}#{i} 状态为 {state} 但缺少 checks 验收记录")
            if state == "approved" and item.get("checks", {}).get("passed") is not True:
                errors.append(f"{field}#{i} approved 必须有 checks.passed=true")
            if item.get("output_path") and not os.path.exists(item["output_path"]):
                warnings.append(f"{field}#{i} output_path 当前不存在: {item['output_path']}")
    return {"valid": not errors, "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description="校验视觉与平台生产状态")
    parser.add_argument("--pack", required=True)
    args = parser.parse_args()
    with open(args.pack, encoding="utf-8") as handle: result = validate(json.load(handle))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["valid"]: sys.exit(1)

if __name__ == "__main__": main()
