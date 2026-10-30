#!/usr/bin/env python3
"""
NoteIntel - 事实候选提取器
从素材文本中提取事实候选句子，标注段落/句子编号和候选类型，
辅助 Agent 在候选列表上做筛选和定位标注，降低从头通读原文的成本。
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os


NUMBER_PATTERN = re.compile(
    r'\d+[%％]|\d+\.?\d*\s*[亿万千百十]|^\d+|\d{4}年'
)
PROPER_NOUN_PATTERN = re.compile(
    r'[A-Z][a-z]+|[\u4e00-\u9fff]{2,}(公司|机构|研究|报告|数据|集团|品牌|平台|市场|行业|政策|法案)'
)
DATA_KEYWORD_PATTERN = re.compile(
    r'(达到|增长|下降|占比|超过|约为|同比|环比|首次|突破|预计|降低|提升|占据|领先|规模|渗透|投资|出口)'
)
COMPARISON_PATTERN = re.compile(
    r'(相比|对比|高于|低于|多于|少于|相当于|差距|领先|落后| versus|vs)',
    re.IGNORECASE
)
CONCLUSION_PATTERN = re.compile(
    r'(因此|所以|表明|证明|说明|显示|意味着|由此|可见|可以判断|可以得出|证实|确认|标志着|反映了|揭示了|导致了)'
)


def split_sentences(text):
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]


def split_paragraphs(text):
    paragraphs = re.split(r'\n{2,}', text)
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]


def classify_candidate(sentence):
    has_number = bool(NUMBER_PATTERN.search(sentence))
    has_proper_noun = bool(PROPER_NOUN_PATTERN.search(sentence))
    has_data_keyword = bool(DATA_KEYWORD_PATTERN.search(sentence))
    has_comparison = bool(COMPARISON_PATTERN.search(sentence))
    has_conclusion = bool(CONCLUSION_PATTERN.search(sentence))

    if has_number and has_comparison:
        return "数据对比", 3
    if has_number and has_data_keyword:
        return "数据事实", 3
    if has_number:
        return "数值事实", 2
    if has_proper_noun and has_data_keyword:
        return "实体事件", 2
    if has_conclusion:
        return "结论推断", 2
    if has_proper_noun:
        return "实体提及", 1
    return None, 0


def extract_candidates(text):
    paragraphs = split_paragraphs(text)
    candidates = []

    for para_idx, para in enumerate(paragraphs, 1):
        sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(sentences, 1):
            candidate_type, priority = classify_candidate(sentence)
            if candidate_type:
                candidates.append({
                    "paragraph": para_idx,
                    "sentence": sent_idx,
                    "text": sentence,
                    "type": candidate_type,
                    "priority": priority,
                    "location": f"第{para_idx}段，第{sent_idx}句"
                })

    candidates.sort(key=lambda x: x["priority"], reverse=True)
    return candidates


def filter_by_quota(candidates, quota_max):
    high = [c for c in candidates if c["priority"] >= 3]
    medium = [c for c in candidates if c["priority"] == 2]
    low = [c for c in candidates if c["priority"] == 1]

    selected = high[:quota_max]
    if len(selected) < quota_max:
        remaining = quota_max - len(selected)
        selected.extend(medium[:remaining])
    if len(selected) < quota_max:
        remaining = quota_max - len(selected)
        selected.extend(low[:remaining])

    selected.sort(key=lambda x: (x["paragraph"], x["sentence"]))
    return selected


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 事实候选提取器")
    parser.add_argument("--input", required=True, help="输入源：文件路径或文本")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    parser.add_argument("--quota", type=int, help="配额上限，筛选优先级最高的N条候选")
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = args.input

    candidates = extract_candidates(text)

    if args.quota:
        candidates = filter_by_quota(candidates, args.quota)

    result = {
        "total_candidates": len(candidates),
        "candidates": candidates
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"候选事实已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()