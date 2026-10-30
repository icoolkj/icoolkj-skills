#!/usr/bin/env python3
"""Build fact-grounded Xiaohongshu copy and adaptive 3:4 cards."""
import argparse
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from visual_primitives import STUDIO_CSS, STUDIO_JS, _card, _esc, _bi
from validate_json_pack import validate

BANNED = ("国家级", "世界级", "全网第一", "全网首家", "最牛", "最佳", "顶级", "终极", "100%有效", "包过", "加微", "私信领钱")


def safe(text):
    text = str(text or "")
    for word in BANNED:
        text = text.replace(word, "高质量")
    return text.strip()


def facts_for_topic(pack, topic):
    ids = topic.get("related_facts", []) if isinstance(topic, dict) else []
    by_id = {f.get("id"): f for f in pack.get("facts", []) if isinstance(f, dict)}
    facts = [by_id[i] for i in ids if i in by_id]
    if not facts:
        facts = [f for f in pack.get("facts", []) if isinstance(f, dict)]
    return facts


def topic_title(pack):
    topics = pack.get("topics", [])
    if topics and topics[0].get("title"):
        return safe(topics[0]["title"])
    facts = pack.get("facts", [])
    return safe(facts[0].get("claim", "这份资料的核心信息") if facts else "这份资料的核心信息")


def titles(topic):
    base = re.sub(r"[！!？?。；;：:、\s]+$", "", topic)[:12]
    return [f"{base}到底讲了什么", f"给普通人的{base}拆解", f"从原文看懂{base}", f"{base}信息整理清单", f"3分钟看懂{base}核心信息"]


def make_groups(facts, pack):
    if not facts:
        return []
    # Keep each card readable while allowing long, fact-rich material to grow.
    desired = max(1, math.ceil(len(facts) / 2))
    if (pack.get("word_count") or 0) > 3000:
        desired += 1
    group_count = min(9, desired)
    size = max(1, math.ceil(len(facts) / group_count))
    return [facts[i:i + size] for i in range(0, len(facts), size)][:9]


def page_plan(pack, facts):
    groups = make_groups(facts, pack)
    pages = [("封面", "主题与阅读收益", "cover")]
    if not groups:
        pages.append(("信息范围", "说明材料覆盖范围和阅读边界", "context"))
    for index, group in enumerate(groups, 1):
        pages.append((f"核心事实 {index}", "呈现一组有来源、有定位的事实", "facts"))
    pages.append(("边界与核查", "保留限定词、风险和待核查问题", "boundary"))
    pages.append(("复盘与互动", "来源提示、发布前检查和评论问题", "cta"))
    return pages, groups


def build_markdown(pack):
    topic = topic_title(pack)
    selected = pack.get("topics", [{}])[0] if pack.get("topics") else {}
    facts = facts_for_topic(pack, selected)
    pages, groups = page_plan(pack, facts)
    lines = [f"# 小红书事实驱动图文包｜{topic}", "", "> 事实源：content-pack JSON；卡片页数根据事实数量和内容复杂度自适应。", "", "## 一、标题备选（≤20字，发布前选择一个）"]
    for i, title in enumerate(titles(topic), 1):
        lines.append(f"{i}. **【候选标题{i}】** `{title[:20]}`")
    lines += ["", f"## 二、轮播卡片文案（共 {len(pages)} 页）"]
    fact_group_index = 0
    for number, (role, hint, kind) in enumerate(pages, 1):
        lines += [f"### 【P{number} {role}】", f"- 页面任务：{hint}"]
        if kind == "cover":
            lines += [f"- 主标题：{topic[:16]}", "- 副标题：左滑查看来源、事实与边界"]
        elif kind == "context":
            lines += ["- 文案：本组内容仅覆盖当前来源明确提供的信息，不能替代外部核验。"]
        elif kind == "facts":
            group = groups[fact_group_index]; fact_group_index += 1
            for fact in group:
                lines += [f"- [{fact.get('id', 'F?')}] {safe(fact.get('claim'))}", f"  - 来源：{', '.join(fact.get('source_ids', []))}｜定位：{fact.get('location', '')}", f"  - 原文引用：{fact.get('quote', '')}"]
        elif kind == "boundary":
            lines.append("- 文案：预测、观点、单一来源和待核查问题不改写成确定结论。")
            for risk in pack.get("risks", [])[:4]: lines.append(f"- 风险：{risk.get('type', '')}｜{risk.get('suggestion', '')}")
            for gap in pack.get("verification_gaps", [])[:3]: lines.append(f"- 待核查：{gap.get('question', '')}")
        else:
            lines += ["- 文案：以上信息据原文整理，发布前请核对数字、时间、限定词和来源。", "- 互动：你最想继续核查哪一个问题？"]
        lines.append("")
    lines += ["## 三、小红书正文", f"今天把「{topic}」整理成 {len(pages)} 张卡片。", "", "核心信息："]
    for fact in facts[: min(5, len(facts))]: lines.append(f"- {fact.get('claim')}（{fact.get('id')}）")
    lines += ["", "说明：内容据原文整理；预测、观点和待核查内容不改写成确定事实。", "", "## 四、来源与风险"]
    for risk in pack.get("risks", []): lines.append(f"- 风险：{risk.get('type', '')}｜{risk.get('content', '')}｜建议：{risk.get('suggestion', '')}")
    lines.append("- 发布前：核对数字、时间、限定词、图片版权和平台标题。")
    lines += ["", "## 五、话题建议", "#知识整理 #信息拆解 #小红书图文 #内容创作 #干货分享 #来源核查 #避坑指南 #收藏备用"]
    return "\n".join(lines) + "\n"


def build_html(pack):
    topic = topic_title(pack)
    selected = pack.get("topics", [{}])[0] if pack.get("topics") else {}
    facts = facts_for_topic(pack, selected)
    pages, groups = page_plan(pack, facts)
    cards = []
    group_index = 0
    for number, (role, _hint, kind) in enumerate(pages, 1):
        if kind == "cover":
            inner = f'<h2 class="card-title" contenteditable="true"{_bi(topic[:16], topic[:16])}>{_esc(topic[:16])}</h2><div class="pill" contenteditable="true">左滑查看来源、事实与边界</div>'
            foot = "据原文整理 · 左滑继续"
            badge, en, orbs = "封面", "COVER", "ab"
        elif kind == "context":
            inner = f'<h2 class="card-title" contenteditable="true"{_bi("信息范围", "Scope")}>信息范围</h2><div class="pill" contenteditable="true">本卡只呈现当前来源明确提供的信息</div>'
            foot, badge, en, orbs = "信息范围", "SCOPE", "bc"
        elif kind == "facts":
            group = groups[group_index]; group_index += 1
            pills = "".join(f'<div class="pill" contenteditable="true"><span class="n mono">{_esc(f.get("id", "F?"))}</span>{_esc(safe(f.get("claim")))}</div>' for f in group)
            inner = f'<h2 class="card-title" contenteditable="true">{_esc(role)}</h2>{pills}'
            foot, badge, en, orbs = "数字、时间、限定词不得改写", f"事实 {group_index}", f"FACT {group_index:02d}", "ac" if number % 2 else "ab"
        elif kind == "boundary":
            risks = [safe(r.get("type", "待核查")) for r in pack.get("risks", [])[:3]]
            if not risks: risks = ["来源范围", "时间限定", "是否需要补充核验"]
            inner = f'<h2 class="card-title" contenteditable="true">边界与核查</h2>{"".join(f"<div class=\"pill\" contenteditable=\"true\"><span class=\"n mono\">!</span>{_esc(x)}</div>" for x in risks)}'
            foot, badge, en, orbs = "风险提示不是事实判决", "边界提醒", "BOUNDARY", "bc"
        else:
            inner = '<h2 class="card-title" contenteditable="true">复盘与互动</h2><div class="pill" contenteditable="true"><span class="n mono">✓</span>核对数字、时间、限定词和来源</div><div class="pill" contenteditable="true"><span class="n mono">?</span>你最想继续核查哪一个问题？</div>'
            foot, badge, en, orbs = "发布前完成来源与版权检查", "复盘互动", "CHECKLIST", "ac"
        card = _card(number, badge, en, inner, foot, orbs).replace(f"P{number} / 06", f"P{number} / {len(pages):02d}")
        cards.append(card)
    body = "\n".join(cards)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_esc(topic)} · XHS Fact Carousel Studio</title><style>{STUDIO_CSS}</style></head><body data-world="obsidian"><div class="studio-wrap"><header class="studio-bar"><div><div class="brand-eyebrow mono">FACT-GROUNDED XHS STUDIO</div><div class="brand-title">《{_esc(topic[:18])}》· {len(pages)}页 3:4 事实驱动卡片</div></div><div class="controls"><div class="group"><button class="ctl-btn active" data-set-world="obsidian">黑曜</button><button class="ctl-btn" data-set-world="crimson">绯红</button><button class="ctl-btn" data-set-world="emerald">翡翠</button><button class="ctl-btn" data-set-world="pearl">昼白</button></div><div class="group"><label>模糊</label><input id="blur-range" type="range" min="10" max="44" value="28"><span id="blur-val" class="mono">28px</span></div><div class="group"><label>透明度</label><input id="opacity-range" type="range" min="30" max="85" value="56"><span id="opacity-val" class="mono">56%</span></div><button id="lang-toggle" class="ctl-btn">中 / EN</button><button id="export-all" class="ctl-btn primary">导出全部 PNG</button></div></header><main class="grid">{body}</main></div><script>{STUDIO_JS}</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description="从已校验事实素材包生成自适应页数的小红书文案和卡片工作台")
    parser.add_argument("--pack", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    with open(args.pack, encoding="utf-8") as handle: pack = json.load(handle)
    validation = validate(pack)
    if not validation["valid"]:
        print(json.dumps(validation, ensure_ascii=False, indent=2)); return 1
    os.makedirs(args.output_dir, exist_ok=True)
    md_path = os.path.join(args.output_dir, "xhs-copy-pack.md")
    html_path = os.path.join(args.output_dir, "xhs-card-studio.html")
    with open(md_path, "w", encoding="utf-8") as handle: handle.write(build_markdown(pack))
    with open(html_path, "w", encoding="utf-8") as handle: handle.write(build_html(pack))
    pages = len(page_plan(pack, facts_for_topic(pack, pack.get("topics", [{}])[0] if pack.get("topics") else {}))[0])
    print(json.dumps({"status": "success", "markdown": md_path, "html": html_path, "page_count": pages, "fact_ids": [f.get("id") for f in pack.get("facts", [])]}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__": raise SystemExit(main())
