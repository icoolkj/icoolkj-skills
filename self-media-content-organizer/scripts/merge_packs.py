#!/usr/bin/env python3
"""
NoteIntel - 多素材合并器 v0.3
合并多个素材包JSON，去重事实，整合选题，合并引用和风险
增强：正确的事实编号重映射（基于去重后的编号）
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os
from datetime import datetime
from difflib import SequenceMatcher


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件失败: {path} - {e}", file=sys.stderr)
        return None


def normalize_text(text):
    return re.sub(r'[ \t\n]+', '', text).lower()


def merge_packs(pack_paths):
    packs = []
    for path in pack_paths:
        data = read_json(path)
        if data:
            packs.append(data)

    if not packs:
        print("没有有效的素材包", file=sys.stderr)
        sys.exit(1)

    deduped_facts = []
    fact_key_to_new_id = {}
    fact_id_to_index = {}
    all_topics = []
    all_quotes = []
    all_risks = []
    all_sources = []
    conflicts = []
    total_word_count = 0
    max_density = 0

    original_topic_count = 0
    for pack_idx, pack in enumerate(packs):
        total_word_count += pack.get("word_count", 0)
        max_density = max(max_density, pack.get("density_score", 0))

        pack_source_id_map = {}
        for src in pack.get("sources", []):
            old_sid = src.get("source_id", "")
            new_sid = f"P{pack_idx + 1}_{old_sid}"
            pack_source_id_map[old_sid] = new_sid
            src_copy = dict(src)
            src_copy["source_id"] = new_sid
            all_sources.append(src_copy)

        facts = pack.get("facts", [])
        original_topic_count += len(pack.get("topics", []))
        pack_fact_id_map = {}
        for fact_idx, fact in enumerate(facts, 1):
            key = normalize_text(fact.get("claim", fact.get("content", "")))
            fact_copy = dict(fact)
            fact_copy["source_ids"] = [pack_source_id_map.get(sid, sid)
                                       for sid in fact.get("source_ids", [])]
            old_fid = fact.get("id", str(fact_idx))

            if key in fact_key_to_new_id:
                new_fid = fact_key_to_new_id[key]
                pack_fact_id_map[old_fid] = new_fid
                pack_fact_id_map[fact_idx] = new_fid
                existing = deduped_facts[fact_id_to_index[new_fid]]
                for field in ("source_ids", "locations"):
                    values = []
                    for item in (existing.get(field, []), fact_copy.get(field, [])):
                        values.extend(item if isinstance(item, list) else ([item] if item else []))
                    if values:
                        existing[field] = list(dict.fromkeys(values))
                if fact_copy.get("quote") and fact_copy.get("quote") != existing.get("quote"):
                    existing.setdefault("alternate_quotes", []).append({
                        "source_ids": fact_copy.get("source_ids", []),
                        "quote": fact_copy.get("quote"),
                        "location": fact_copy.get("location", "")})
            else:
                new_fid = f"F{len(deduped_facts) + 1}"
                fact_key_to_new_id[key] = new_fid
                fact_id_to_index[new_fid] = len(deduped_facts)
                pack_fact_id_map[old_fid] = new_fid
                pack_fact_id_map[fact_idx] = new_fid
                fact_copy["id"] = new_fid
                deduped_facts.append(fact_copy)

        for left in facts:
            for right_pack in packs[pack_idx + 1:]:
                for right in right_pack.get("facts", []):
                    left_text = normalize_text(left.get("claim", left.get("content", "")))
                    right_text = normalize_text(right.get("claim", right.get("content", "")))
                    ratio = SequenceMatcher(None, left_text, right_text).ratio()
                    if 0.72 <= ratio < 1.0:
                        conflicts.append({"type": "相似事实待核对", "statements": [left, right],
                                          "difference": "表述相似但未达到安全去重条件",
                                          "resolution": "保留并列，发布前核查数字、时间和口径"})

        for topic in pack.get("topics", []):
            topic_copy = dict(topic)
            related = topic_copy.get("related_facts", "")
            if isinstance(related, list):
                topic_copy["related_facts"] = [pack_fact_id_map.get(ref, ref)
                                               for ref in related]
            elif isinstance(related, str):
                for old_id in sorted(pack_fact_id_map.keys(), key=lambda x: -len(str(x))):
                    new_id = pack_fact_id_map[old_id]
                    related = re.sub(r'#' + re.escape(str(old_id)) + r'(?!\d)',
                                     f'#{new_id}', related)
                topic_copy["related_facts"] = related
            all_topics.append(topic_copy)

        for quote in pack.get("quotes", []):
            all_quotes.append(dict(quote))

        for risk in pack.get("risks", []):
            all_risks.append(dict(risk))

    seen_quotes = {}
    deduped_quotes = []
    for quote in all_quotes:
        key = normalize_text(quote.get("text", ""))
        if key not in seen_quotes:
            seen_quotes[key] = True
            deduped_quotes.append(quote)

    seen_risks = {}
    deduped_risks = []
    for risk in all_risks:
        key = normalize_text(risk.get("type", "") + risk.get("content", ""))
        if key not in seen_risks:
            seen_risks[key] = True
            deduped_risks.append(risk)

    if total_word_count < 800:
        mode = "concise"
    elif total_word_count <= 3000:
        mode = "standard"
    else:
        mode = "deep"

    original_fact_count = sum(len(p.get("facts", [])) for p in packs)

    merged = {
        "source": " + ".join(p.get("source", "") for p in packs),
        "mode": mode,
        "word_count": total_word_count,
        "density_score": round(max_density, 2),
        "timestamp": datetime.now().isoformat(),
        "summary": f"合并自{len(packs)}个素材包，共{len(deduped_facts)}条事实（去重后），{len(all_topics)}条选题。",
        "sources": all_sources,
        "facts": deduped_facts,
        "topics": all_topics,
        "quotes": deduped_quotes,
        "risks": deduped_risks,
        "conflicts": conflicts,
        "merge_info": {
            "original_pack_count": len(packs),
            "original_fact_count": original_fact_count,
            "deduped_fact_count": len(deduped_facts),
            "original_topic_count": original_topic_count,
            "original_quote_count": len(all_quotes),
            "deduped_quote_count": len(deduped_quotes),
            "original_risk_count": len(all_risks),
            "deduped_risk_count": len(deduped_risks)
        }
    }

    return merged


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 多素材合并器 v0.3")
    parser.add_argument("--packs", required=True, nargs='+', help="多个素材包JSON文件路径")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    args = parser.parse_args()

    result = merge_packs(args.packs)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"合并结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
