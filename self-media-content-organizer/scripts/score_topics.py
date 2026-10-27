#!/usr/bin/env python3
"""
NoteIntel - 选题评分器
对素材包中的每个创作选题进行评分：增量价值、传播潜力、创作难度
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os


HIGH_VALUE_ANGLES = ['数据冲击', '对比反差', '趋势预判']
MEDIUM_VALUE_ANGLES = ['因果追溯', '影响推演']
LOW_VALUE_ANGLES = ['方法拆解']

HIGH_SPREAD_AUDIENCES = ['普通消费者', '媒体创作者']
MEDIUM_SPREAD_AUDIENCES = ['投资者', '决策者', '行业从业者']
LOW_SPREAD_AUDIENCES = ['学习者', '研究者']

AUDIENCE_ALIASES = {
    '投资者/决策者': '投资者',
    '学习者/研究者': '学习者',
}

HIGH_SPREAD_FORMS = ['短视频', '图文卡片']
MEDIUM_SPREAD_FORMS = ['图文长文']
LOW_SPREAD_FORMS = ['系列内容', '直播访谈']

EASY_FORMS = ['图文卡片', '短视频']
MEDIUM_FORMS = ['图文长文']
HARD_FORMS = ['系列内容', '直播访谈']


def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取文件失败: {e}", file=sys.stderr)
        return None


def score_angle(angle):
    if angle in HIGH_VALUE_ANGLES:
        return 3, "高增量价值角度"
    elif angle in MEDIUM_VALUE_ANGLES:
        return 2, "中等增量价值角度"
    elif angle in LOW_VALUE_ANGLES:
        return 1, "低增量价值角度"
    return 1, "未知角度"


def score_audience(audience):
    if audience in AUDIENCE_ALIASES:
        audience = AUDIENCE_ALIASES[audience]
    if audience in HIGH_SPREAD_AUDIENCES:
        return 3, "高传播潜力受众"
    elif audience in MEDIUM_SPREAD_AUDIENCES:
        return 2, "中等传播潜力受众"
    elif audience in LOW_SPREAD_AUDIENCES:
        return 1, "低传播潜力受众"
    return 1, "未知受众"


def score_form(form):
    if form in HIGH_SPREAD_FORMS:
        return 3, "高传播力形式"
    elif form in MEDIUM_SPREAD_FORMS:
        return 2, "中等传播力形式"
    elif form in LOW_SPREAD_FORMS:
        return 1, "低传播力形式"
    return 1, "未知形式"


def score_difficulty(form):
    if form in EASY_FORMS:
        return 1, "低创作难度"
    elif form in MEDIUM_FORMS:
        return 2, "中等创作难度"
    elif form in HARD_FORMS:
        return 3, "高创作难度"
    return 2, "未知难度"


def score_related_facts(related_str, fact_count):
    refs = re.findall(r'(\d+)', related_str)
    if not refs:
        return 1, "无关联事实"
    unique_refs = set(int(r) for r in refs if int(r) <= fact_count)
    if len(unique_refs) >= 3:
        return 3, f"关联{len(unique_refs)}条事实，证据充分"
    elif len(unique_refs) >= 1:
        return 2, f"关联{len(unique_refs)}条事实，有据可依"
    return 1, "关联事实编号无效"


def score_topic(topic, fact_count):
    angle = topic.get("angle", "")
    audience = topic.get("audience", "")
    form = topic.get("form", "")
    related = topic.get("related_facts", "")

    angle_score, angle_desc = score_angle(angle)
    audience_score, audience_desc = score_audience(audience)
    form_score, form_desc = score_form(form)
    difficulty_score, difficulty_desc = score_difficulty(form)
    related_score, related_desc = score_related_facts(related, fact_count)

    increment_value = angle_score * 0.4 + related_score * 0.6
    spread_potential = audience_score * 0.5 + form_score * 0.5
    creation_difficulty = difficulty_score

    overall = round(
        increment_value * 0.4 + spread_potential * 0.4 + (4 - creation_difficulty) * 0.2,
        2
    )

    return {
        "title": topic.get("title", ""),
        "angle": angle,
        "audience": audience,
        "form": form,
        "related_facts": related,
        "scores": {
            "increment_value": round(increment_value, 2),
            "spread_potential": round(spread_potential, 2),
            "creation_difficulty": creation_difficulty,
            "overall": overall
        },
        "descriptions": {
            "angle": angle_desc,
            "audience": audience_desc,
            "form": form_desc,
            "difficulty": difficulty_desc,
            "related": related_desc
        },
        "recommendation": get_recommendation(overall)
    }


def get_recommendation(overall):
    if overall >= 2.5:
        return "强烈推荐——高增量价值 + 高传播潜力 + 低创作难度"
    elif overall >= 2.0:
        return "推荐——综合评分良好，值得创作"
    elif overall >= 1.5:
        return "可选——有一定价值但存在短板"
    else:
        return "暂缓——增量价值或传播潜力不足"


def score_topics(pack_path):
    data = read_json(pack_path)
    if data is None:
        return None

    facts = data.get("facts", [])
    topics = data.get("topics", [])
    fact_count = len(facts)

    results = []
    for i, topic in enumerate(topics, 1):
        scored = score_topic(topic, fact_count)
        scored["index"] = i
        results.append(scored)

    results.sort(key=lambda x: x["scores"]["overall"], reverse=True)

    return {
        "total_topics": len(results),
        "fact_count": fact_count,
        "rankings": results
    }


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 选题评分器")
    parser.add_argument("--pack", required=True, help="素材包JSON文件路径")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    args = parser.parse_args()

    result = score_topics(args.pack)
    if result is None:
        sys.exit(1)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"评分结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
