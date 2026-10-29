#!/usr/bin/env python3
"""Merge auditable NoteIntel packs without corrupting the JSON contract."""
import argparse
import json
import os
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher


def read_json(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:
        print(f"读取文件失败: {path} - {exc}", file=sys.stderr)
        return None


def normalize_text(value):
    return re.sub(r"[ \t\n]+", "", str(value or "")).lower()


def as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def fact_text(fact):
    return normalize_text(fact.get("claim") or fact.get("content"))


def remap_source_ids(value, source_map):
    return [source_map.get(item, item) for item in as_list(value)]


def mapped_fact_id(value, mapping):
    if value in mapping:
        return mapping[value]
    match = re.fullmatch(r"F?(\d+)", str(value))
    return mapping.get(int(match.group(1)), value) if match else value


def format_fact_id(value):
    text = str(value)
    return text if text.startswith("F") else f"F{text}"


def merge_packs(pack_paths):
    packs = [data for path in pack_paths if (data := read_json(path))]
    if not packs:
        raise ValueError("没有有效的素材包")

    facts, fact_key_to_id, topics, quotes, risks, conflicts, sources = [], {}, [], [], [], [], []
    total_word_count, max_density, original_topic_count = 0, 0, 0
    for pack_idx, pack in enumerate(packs, 1):
        source_map = {}
        for source in pack.get("sources", []):
            source = dict(source)
            old_id = source.get("source_id") or f"S{len(source_map) + 1}"
            new_id = f"P{pack_idx}_{old_id}"
            source_map[old_id] = new_id
            source["source_id"] = new_id
            sources.append(source)
        if not source_map:
            source_map["S1"] = f"P{pack_idx}_S1"
        total_word_count += pack.get("word_count", 0) or 0
        max_density = max(max_density, pack.get("density_score", 0) or 0)
        pack_fact_id_map = {}
        for position, raw_fact in enumerate(pack.get("facts", []), 1):
            fact = dict(raw_fact)
            old_id = fact.get("id") or f"F{position}"
            key = fact_text(fact)
            fact["source_ids"] = remap_source_ids(fact.get("source_ids"), source_map)
            if key and key in fact_key_to_id:
                new_id = fact_key_to_id[key]
                pack_fact_id_map[old_id] = new_id
                existing = facts[new_id - 1]
                for field in ("source_ids", "locations"):
                    values = list(dict.fromkeys(as_list(existing.get(field)) + as_list(fact.get(field))))
                    if values:
                        existing[field] = values
                if fact.get("quote") and fact.get("quote") != existing.get("quote"):
                    existing.setdefault("alternate_quotes", []).append({
                        "source_ids": fact.get("source_ids", []), "quote": fact.get("quote"),
                        "location": fact.get("location", "")})
            else:
                new_id = len(facts) + 1
                if key:
                    fact_key_to_id[key] = new_id
                pack_fact_id_map[old_id] = new_id
                fact["id"] = f"F{new_id}"
                facts.append(fact)

        for left in pack.get("facts", []):
            for other in packs[pack_idx:]:
                for right in other.get("facts", []):
                    left_text, right_text = fact_text(left), fact_text(right)
                    if left_text and 0.72 <= SequenceMatcher(None, left_text, right_text).ratio() < 1.0:
                        conflicts.append({"type": "相似事实待核对", "statements": [left, right],
                                          "difference": "表述相似但未达到安全去重条件",
                                          "resolution": "保留并列，发布前核查数字、时间和口径"})

        original_topic_count += len(pack.get("topics", []))
        for topic in pack.get("topics", []):
            item = dict(topic)
            refs = as_list(item.get("related_facts"))
            item["related_facts"] = [format_fact_id(mapped_fact_id(ref, pack_fact_id_map)) for ref in refs]
            topics.append(item)
        quotes.extend(dict(q) for q in pack.get("quotes", []))
        risks.extend(dict(r) for r in pack.get("risks", []))

    def dedupe(items, key_fn):
        seen, result = set(), []
        for item in items:
            key = key_fn(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

    quotes = dedupe(quotes, lambda q: normalize_text(q.get("text")))
    risks = dedupe(risks, lambda r: normalize_text(r.get("type", "") + r.get("content", "")))
    mode = "concise" if total_word_count < 800 else "standard" if total_word_count <= 3000 else "deep"
    return {
        "schema_version": "1.0", "source": " + ".join(p.get("source", "") for p in packs),
        "sources": sources, "mode": mode, "word_count": total_word_count,
        "density_score": round(max_density, 2), "timestamp": datetime.now().isoformat(),
        "summary": f"合并自{len(packs)}个素材包，共{len(facts)}条事实（去重后），{len(topics)}条选题。",
        "facts": facts, "topics": topics, "quotes": quotes, "risks": risks, "conflicts": conflicts,
        "merge_info": {"original_pack_count": len(packs), "original_fact_count": sum(len(p.get("facts", [])) for p in packs),
                       "deduped_fact_count": len(facts), "original_topic_count": original_topic_count,
                       "deduped_topic_count": len(topics), "deduped_quote_count": len(quotes), "deduped_risk_count": len(risks)}
    }


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 多素材合并器")
    parser.add_argument("--packs", required=True, nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = merge_packs(args.packs)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle:
                handle.write(text)
            print(f"合并结果已写入: {args.output}", file=sys.stderr)
        else:
            print(text)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
