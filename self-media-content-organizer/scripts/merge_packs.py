#!/usr/bin/env python3
"""Merge NoteIntel packs while preserving the full supported JSON contract."""
import argparse
import copy
import json
import re
import sys
from datetime import datetime
from difflib import SequenceMatcher

SUPPORTED_LIST_FIELDS = (
    "viewpoints", "inferences", "verification_gaps", "topics", "quotes", "risks",
    "conflicts", "next_actions", "platform_adaptations", "source_images",
    "derived_visuals", "generated_visuals", "card_plan",
)
FACT_REF_KEYS = {"related_facts", "based_on", "fact_ids", "fact_id"}
SOURCE_REF_KEYS = {"source_ids", "source_id"}


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


def fact_ref_key(value):
    match = re.fullmatch(r"F?(\d+)", str(value))
    return int(match.group(1)) if match else value


def remap_recursive(value, fact_map, source_map, key=None):
    if isinstance(value, dict):
        return {k: remap_recursive(v, fact_map, source_map, k) for k, v in value.items()}
    if isinstance(value, list):
        return [remap_recursive(v, fact_map, source_map, key) for v in value]
    if key in FACT_REF_KEYS:
        mapped = fact_map.get(value, fact_map.get(fact_ref_key(value), value))
        return mapped if isinstance(mapped, str) else f"F{mapped}"
    if key in SOURCE_REF_KEYS:
        return source_map.get(value, value)
    return value


def normalize_ref_list(value):
    return [str(item) for item in as_list(value) if item not in (None, "")]


def merge_locations(existing, incoming):
    values = []
    for value in (existing.get("location"), existing.get("locations"), incoming.get("location"), incoming.get("locations")):
        values.extend(as_list(value))
    values = list(dict.fromkeys(str(v) for v in values if v))
    if values:
        existing["location"] = values[0]
        if len(values) > 1:
            existing["locations"] = values
    return existing


def source_records(pack, pack_idx):
    raw_sources = [dict(s) for s in pack.get("sources", []) if isinstance(s, dict)]
    referenced = []
    for fact in pack.get("facts", []):
        referenced.extend(normalize_ref_list(fact.get("source_ids")))
    for field in SUPPORTED_LIST_FIELDS:
        for item in pack.get(field, []) if isinstance(pack.get(field, []), list) else []:
            if isinstance(item, dict):
                referenced.extend(normalize_ref_list(item.get("source_ids")))
                referenced.extend(normalize_ref_list(item.get("source_id")))
    old_ids = []
    for source in raw_sources:
        old_ids.append(str(source.get("source_id") or f"S{len(old_ids) + 1}"))
    for sid in referenced:
        if sid not in old_ids:
            old_ids.append(sid)
    if not old_ids and (pack.get("facts") or referenced):
        old_ids.append("S1")
    source_map = {old: f"P{pack_idx}_{old}" for old in old_ids}
    records = []
    by_id = {str(s.get("source_id")): s for s in raw_sources if s.get("source_id")}
    for old in old_ids:
        record = copy.deepcopy(by_id.get(old, {"source_id": old, "type": "unknown",
                                                "title": "未登记来源", "completeness": "unknown"}))
        record["source_id"] = source_map[old]
        records.append(record)
    return records, source_map


def merge_packs(pack_paths):
    packs = [data for path in pack_paths if (data := read_json(path))]
    if not packs:
        raise ValueError("没有有效的素材包")

    merged = {"schema_version": "1.0", "source": " + ".join(str(p.get("source", "")) for p in packs),
              "sources": [], "facts": [], "topics": [], "quotes": [], "risks": [], "conflicts": []}
    all_fact_by_key, all_lists = {}, {field: [] for field in SUPPORTED_LIST_FIELDS if field not in {"topics", "quotes", "risks", "conflicts"}}
    all_lists.update({"topics": merged["topics"], "quotes": merged["quotes"], "risks": merged["risks"], "conflicts": merged["conflicts"]})
    word_count, max_density, original_facts, original_topics = 0, 0, 0, 0

    for pack_idx, pack in enumerate(packs, 1):
        pack_sources, source_map = source_records(pack, pack_idx)
        merged["sources"].extend(pack_sources)
        word_count += pack.get("word_count", 0) or 0
        max_density = max(max_density, pack.get("density_score", 0) or 0)
        original_facts += len(pack.get("facts", []))
        original_topics += len(pack.get("topics", []))
        fact_map = {}

        for position, raw in enumerate(pack.get("facts", []), 1):
            fact = copy.deepcopy(raw) if isinstance(raw, dict) else {"claim": str(raw)}
            old_id = fact.get("id") or f"F{position}"
            fact = remap_recursive(fact, {}, source_map)
            if not fact.get("source_ids") and source_map:
                fact["source_ids"] = [next(iter(source_map.values()))]
            key = fact_text(fact)
            if key and key in all_fact_by_key:
                new_id = all_fact_by_key[key]
                fact_map[old_id] = new_id
                existing = merged["facts"][new_id - 1]
                existing["source_ids"] = list(dict.fromkeys(normalize_ref_list(existing.get("source_ids")) + normalize_ref_list(fact.get("source_ids"))))
                merge_locations(existing, fact)
                for field in ("qualifiers", "alternate_quotes"):
                    values = as_list(existing.get(field)) + as_list(fact.get(field))
                    if values:
                        existing[field] = list(dict.fromkeys(json.dumps(v, ensure_ascii=False, sort_keys=True) for v in values))
                        existing[field] = [json.loads(v) for v in existing[field]]
                if fact.get("quote") and fact.get("quote") != existing.get("quote"):
                    existing.setdefault("alternate_quotes", []).append({"source_ids": fact.get("source_ids", []), "quote": fact.get("quote"), "location": fact.get("location", "")})
            else:
                new_id = len(merged["facts"]) + 1
                fact_map[old_id] = f"F{new_id}"
                fact["id"] = f"F{new_id}"
                if key:
                    all_fact_by_key[key] = new_id
                merged["facts"].append(fact)

        for left in pack.get("facts", []):
            for other in packs[pack_idx:]:
                for right in other.get("facts", []):
                    left_text, right_text = fact_text(left), fact_text(right)
                    if left_text and right_text and 0.72 <= SequenceMatcher(None, left_text, right_text).ratio() < 1.0:
                        merged["conflicts"].append({"type": "相似事实待核对", "statements": [left, right], "difference": "表述相似但未达到安全去重条件", "resolution": "保留并列，发布前核查数字、时间和口径"})

        for field in SUPPORTED_LIST_FIELDS:
            values = pack.get(field, [])
            if not isinstance(values, list):
                continue
            target = merged.setdefault(field, [])
            if field == "facts":
                continue
            for value in values:
                item = remap_recursive(copy.deepcopy(value), fact_map, source_map)
                if field == "topics" and isinstance(item, dict):
                    item["related_facts"] = [fact_map.get(ref, fact_map.get(fact_ref_key(ref), ref)) for ref in as_list(item.get("related_facts"))]
                target.append(item)

        # 保留未知顶层字段，列表按记录追加，标量按首个非空值保留。
        for key, value in pack.items():
            if key in merged or key in {"facts", "sources", "source", "word_count", "density_score", "timestamp", "merge_info"}:
                continue
            if isinstance(value, list):
                merged.setdefault(key, []).extend(copy.deepcopy(value))
            elif key not in merged and value not in (None, ""):
                merged[key] = copy.deepcopy(value)

    for field in ("quotes", "risks"):
        seen, unique = set(), []
        for item in merged.get(field, []):
            key = normalize_text(item.get("text", "") if field == "quotes" else item.get("type", "") + item.get("content", "")) if isinstance(item, dict) else normalize_text(item)
            if key not in seen:
                seen.add(key); unique.append(item)
        merged[field] = unique
    merged.update({"mode": "concise" if word_count < 800 else "standard" if word_count <= 3000 else "deep", "word_count": word_count, "density_score": round(max_density, 2), "timestamp": datetime.now().isoformat(), "summary": f"合并自{len(packs)}个素材包，共{len(merged['facts'])}条事实（去重后），{len(merged.get('topics', []))}条选题。", "merge_info": {"original_pack_count": len(packs), "original_fact_count": original_facts, "deduped_fact_count": len(merged["facts"]), "original_topic_count": original_topics, "deduped_topic_count": len(merged.get("topics", []))}})
    return merged


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 多素材合并器")
    parser.add_argument("--packs", required=True, nargs="+")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = merge_packs(args.packs)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as handle: handle.write(text)
            print(f"合并结果已写入: {args.output}", file=sys.stderr)
        else: print(text)
    except Exception as exc:
        print(str(exc), file=sys.stderr); sys.exit(1)

if __name__ == "__main__": main()
