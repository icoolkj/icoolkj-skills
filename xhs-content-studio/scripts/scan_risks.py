#!/usr/bin/env python3
"""
NoteIntel - 风险扫描器
基于 compliance-rules.md 的6类风险识别特征，自动扫描素材文本中的候选风险项，
辅助 Agent 在候选列表上做判断和补充，降低漏标风险。
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os
from datetime import datetime


UNVERIFIED_PATTERN = re.compile(
    r'(预计|估计|大约|可能|或将|大概|或许|疑似|据称|传闻|有望|预期|推测|预判)'
)
SUBJECTIVE_PATTERN = re.compile(
    r'(我认为|我觉得|应该|最好|必须|显然|无疑|肯定|绝对|毫无疑问|不可否认|理所应当|理应)'
)
SENSITIVE_PATTERN = re.compile(
    r'(政治|宗教|种族|性别歧视|民族|领土|主权|意识形态|阶级|文革|六四|台独|藏独|疆独)'
)
INTEREST_PATTERN = re.compile(
    r'(赞助|广告|推广|合作|利益|持股|投资|代言|背书|冠名|赞助商|甲方|金主)'
)


def split_sentences(text):
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]


def split_paragraphs(text):
    paragraphs = re.split(r'\n{2,}', text)
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]


def scan_unverified_data(text, sentences, paragraphs):
    risks = []
    for para_idx, para in enumerate(paragraphs, 1):
        para_sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(para_sentences, 1):
            matches = UNVERIFIED_PATTERN.findall(sentence)
            if matches:
                risks.append({
                    "type": "未经证实的数据",
                    "content": sentence,
                    "location": f"第{para_idx}段，第{sent_idx}句",
                    "trigger_words": matches,
                    "suggestion": f"限定词{'、'.join(matches)}标注的数据为预测/估计值，创作时需注明其性质"
                })
    return risks


def scan_subjective_opinion(text, sentences, paragraphs):
    risks = []
    for para_idx, para in enumerate(paragraphs, 1):
        para_sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(para_sentences, 1):
            matches = SUBJECTIVE_PATTERN.findall(sentence)
            if matches:
                risks.append({
                    "type": "主观观点",
                    "content": sentence,
                    "location": f"第{para_idx}段，第{sent_idx}句",
                    "trigger_words": matches,
                    "suggestion": "此句含主观判断词，应标注为观点而非事实"
                })
    return risks


def scan_sensitive_topic(text, sentences, paragraphs):
    risks = []
    for para_idx, para in enumerate(paragraphs, 1):
        para_sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(para_sentences, 1):
            matches = SENSITIVE_PATTERN.findall(sentence)
            if matches:
                risks.append({
                    "type": "敏感话题",
                    "content": sentence,
                    "location": f"第{para_idx}段，第{sent_idx}句",
                    "trigger_words": matches,
                    "suggestion": "涉及敏感内容，建议谨慎处理或回避"
                })
    return risks


def scan_time_risk(text, sentences, paragraphs):
    risks = []
    current_year = datetime.now().year
    threshold = current_year - 2
    for para_idx, para in enumerate(paragraphs, 1):
        para_sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(para_sentences, 1):
            years = re.findall(r'(20\d{2})年', sentence)
            old_years = [y for y in years if int(y) < threshold]
            if old_years:
                risks.append({
                    "type": "时效风险",
                    "content": sentence,
                    "location": f"第{para_idx}段，第{sent_idx}句",
                    "trigger_words": old_years,
                    "suggestion": f"数据年份{','.join(old_years)}距今超过2年，可能已过时，创作时需注明数据时间节点"
                })
    return risks


def scan_interest_related(text, sentences, paragraphs):
    risks = []
    for para_idx, para in enumerate(paragraphs, 1):
        para_sentences = split_sentences(para)
        for sent_idx, sentence in enumerate(para_sentences, 1):
            matches = INTEREST_PATTERN.findall(sentence)
            if matches:
                risks.append({
                    "type": "利益相关",
                    "content": sentence,
                    "location": f"第{para_idx}段，第{sent_idx}句",
                    "trigger_words": matches,
                    "suggestion": "内容可能涉及利益相关方，提示读者注意可能的利益倾向"
                })
    return risks


def scan_single_source(text, source_count=1):
    if source_count > 1:
        return []
    return [{
        "type": "单一来源",
        "content": "所有数据均来自同一素材来源，无交叉验证",
        "location": "全局",
        "trigger_words": [],
        "suggestion": "关键数据建议补充其他来源交叉验证"
    }]


def scan_risks(text, source_count=1):
    sentences = split_sentences(text)
    paragraphs = split_paragraphs(text)

    all_risks = []
    all_risks.extend(scan_unverified_data(text, sentences, paragraphs))
    all_risks.extend(scan_subjective_opinion(text, sentences, paragraphs))
    all_risks.extend(scan_sensitive_topic(text, sentences, paragraphs))
    all_risks.extend(scan_time_risk(text, sentences, paragraphs))
    all_risks.extend(scan_interest_related(text, sentences, paragraphs))
    all_risks.extend(scan_single_source(text, source_count))

    return all_risks


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 风险扫描器")
    parser.add_argument("--input", required=True, help="输入源：文件路径或文本")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    parser.add_argument("--source-count", type=int, default=1,
                        help="文本合并时的独立来源数；>1 时不再报“单一来源”风险")
    args = parser.parse_args()

    if os.path.isfile(args.input):
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
    else:
        text = args.input

    risks = scan_risks(text, source_count=args.source_count)

    result = {
        "total_risks": len(risks),
        "risks": risks
    }

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"风险扫描结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
