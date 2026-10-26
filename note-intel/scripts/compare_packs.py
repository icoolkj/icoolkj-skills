#!/usr/bin/env python3
"""
NoteIntel - 素材对比器
对比两个素材包的信息覆盖差异：事实差异、选题差异、引用差异
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件失败: {path} - {e}", file=sys.stderr)
        return None


def normalize_text(text):
    return re.sub(r'[ \t\n]+', '', text).lower()


def extract_fact_keys(facts):
    keys = set()
    key_to_fact = {}
    for fact in facts:
        key = normalize_text(fact.get("content", ""))
        keys.add(key)
        key_to_fact[key] = fact
    return keys, key_to_fact


def extract_topic_keys(topics):
    keys = set()
    key_to_topic = {}
    for topic in topics:
        key = normalize_text(topic.get("title", ""))
        keys.add(key)
        key_to_topic[key] = topic
    return keys, key_to_topic


def extract_quote_keys(quotes):
    keys = set()
    key_to_quote = {}
    for quote in quotes:
        key = normalize_text(quote.get("text", ""))
        keys.add(key)
        key_to_quote[key] = quote
    return keys, key_to_quote


def compare_packs(pack_a_path, pack_b_path):
    pack_a = read_json(pack_a_path)
    pack_b = read_json(pack_b_path)

    if pack_a is None or pack_b is None:
        sys.exit(1)

    facts_a_keys, facts_a_map = extract_fact_keys(pack_a.get("facts", []))
    facts_b_keys, facts_b_map = extract_fact_keys(pack_b.get("facts", []))

    topics_a_keys, topics_a_map = extract_topic_keys(pack_a.get("topics", []))
    topics_b_keys, topics_b_map = extract_topic_keys(pack_b.get("topics", []))

    quotes_a_keys, quotes_a_map = extract_quote_keys(pack_a.get("quotes", []))
    quotes_b_keys, quotes_b_map = extract_quote_keys(pack_b.get("quotes", []))

    fact_only_a = facts_a_keys - facts_b_keys
    fact_only_b = facts_b_keys - facts_a_keys
    fact_common = facts_a_keys & facts_b_keys

    topic_only_a = topics_a_keys - topics_b_keys
    topic_only_b = topics_b_keys - topics_a_keys
    topic_common = topics_a_keys & topics_b_keys

    quote_only_a = quotes_a_keys - quotes_b_keys
    quote_only_b = quotes_b_keys - quotes_a_keys
    quote_common = quotes_a_keys & quotes_b_keys

    result = {
        "pack_a": {
            "source": pack_a.get("source", ""),
            "mode": pack_a.get("mode", ""),
            "word_count": pack_a.get("word_count", 0),
            "density_score": pack_a.get("density_score", 0),
            "fact_count": len(pack_a.get("facts", [])),
            "topic_count": len(pack_a.get("topics", []))
        },
        "pack_b": {
            "source": pack_b.get("source", ""),
            "mode": pack_b.get("mode", ""),
            "word_count": pack_b.get("word_count", 0),
            "density_score": pack_b.get("density_score", 0),
            "fact_count": len(pack_b.get("facts", [])),
            "topic_count": len(pack_b.get("topics", []))
        },
        "fact_comparison": {
            "only_in_a": [facts_a_map[k].get("content", "") for k in fact_only_a],
            "only_in_b": [facts_b_map[k].get("content", "") for k in fact_only_b],
            "common_count": len(fact_common),
            "coverage_a": round(len(fact_common) / max(len(facts_a_keys), 1), 2),
            "coverage_b": round(len(fact_common) / max(len(facts_b_keys), 1), 2)
        },
        "topic_comparison": {
            "only_in_a": [topics_a_map[k].get("title", "") for k in topic_only_a],
            "only_in_b": [topics_b_map[k].get("title", "") for k in topic_only_b],
            "common_count": len(topic_common),
            "coverage_a": round(len(topic_common) / max(len(topics_a_keys), 1), 2),
            "coverage_b": round(len(topic_common) / max(len(topics_b_keys), 1), 2)
        },
        "quote_comparison": {
            "only_in_a_count": len(quote_only_a),
            "only_in_b_count": len(quote_only_b),
            "common_count": len(quote_common)
        },
        "summary": {
            "fact_overlap": f"A覆盖B的{round(len(fact_common) / max(len(facts_b_keys), 1) * 100)}%事实，B覆盖A的{round(len(fact_common) / max(len(facts_a_keys), 1) * 100)}%事实",
            "topic_overlap": f"A覆盖B的{round(len(topic_common) / max(len(topics_b_keys), 1) * 100)}%选题，B覆盖A的{round(len(topic_common) / max(len(topics_a_keys), 1) * 100)}%选题",
            "unique_facts_a": len(fact_only_a),
            "unique_facts_b": len(fact_only_b),
            "unique_topics_a": len(topic_only_a),
            "unique_topics_b": len(topic_only_b)
        }
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 素材对比器")
    parser.add_argument("--pack-a", required=True, help="素材包A的JSON文件路径")
    parser.add_argument("--pack-b", required=True, help="素材包B的JSON文件路径")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    args = parser.parse_args()

    result = compare_packs(args.pack_a, args.pack_b)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"对比结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
