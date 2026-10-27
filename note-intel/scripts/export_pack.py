#!/usr/bin/env python3
"""
NoteIntel - 素材包导出器 v0.3
将Agent生成的内容组装为MD + HTML + JSON多格式输出
增强：JSON格式导出、HTML搜索过滤、事实-选题关联高亮、自定义文件名
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os
from datetime import datetime
from html import escape


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败: {path} - {e}", file=sys.stderr)
        return None


# ============================================================
# HTML 片段构建（增强版：关联高亮 + data属性）
# ============================================================

def build_facts_html(facts):
    if not facts:
        return '<div class="empty-note">无核心事实</div>'
    items = []
    for i, fact in enumerate(facts, 1):
        content = escape(fact.get("content", ""))
        location = escape(fact.get("location", ""))
        quote = escape(fact.get("quote", ""))
        html = f'<div class="fact-item" data-fact-id="{i}" id="fact-{i}">'
        html += f'<div class="fact-content">{content}</div>'
        if location:
            html += f'<div class="fact-location">📍 {location}</div>'
        if quote:
            html += f'<div class="fact-quote">📎 "{quote}"</div>'
        html += '</div>'
        items.append(html)
    return '\n'.join(items)


def build_topics_html(topics):
    if not topics:
        return '<div class="empty-note">无创作选题</div>'
    items = []
    for i, topic in enumerate(topics, 1):
        title = escape(topic.get("title", f"选题{i}"))
        angle = escape(topic.get("angle", ""))
        audience = escape(topic.get("audience", ""))
        form = escape(topic.get("form", ""))
        related = escape(topic.get("related_facts", ""))

        related_fact_ids = re.findall(r'(\d+)', related)
        related_attrs = ' '.join(f'data-related-fact="{fid}"' for fid in related_fact_ids)

        html = f'<div class="topic-item" data-topic-id="{i}" {related_attrs}>'
        html += f'<div class="topic-title">{title}</div>'
        if angle:
            html += f'<div class="topic-dim"><span class="topic-dim-label">切入角度</span><span class="topic-dim-value">{angle}</span></div>'
        if audience:
            html += f'<div class="topic-dim"><span class="topic-dim-label">目标受众</span><span class="topic-dim-value">{audience}</span></div>'
        if form:
            html += f'<div class="topic-dim"><span class="topic-dim-label">内容形式</span><span class="topic-dim-value">{form}</span></div>'
        if related:
            related_html = related
            for fid in related_fact_ids:
                related_html = related_html.replace(
                    f'#{fid}', f'<a href="#fact-{fid}" class="fact-link" onclick="highlightFact({fid})">#{fid}</a>'
                )
            html += f'<div class="topic-dim"><span class="topic-dim-label">关联事实</span><span class="topic-dim-value">{related_html}</span></div>'
        html += '</div>'
        items.append(html)
    return '\n'.join(items)


def build_quotes_html(quotes):
    if not quotes:
        return '<div class="empty-note">无原文引用</div>'
    items = []
    for i, quote in enumerate(quotes, 1):
        text = escape(quote.get("text", ""))
        location = escape(quote.get("location", ""))
        html = f'<div class="quote-item">'
        html += f'<div class="quote-text">"{text}"</div>'
        if location:
            html += f'<div class="quote-location">📍 {location}</div>'
        html += '</div>'
        items.append(html)
    return '\n'.join(items)


def build_risks_html(risks):
    if not risks:
        return '<div class="empty-note">无风险提示</div>'
    items = []
    for i, risk in enumerate(risks, 1):
        rtype = escape(risk.get("type", ""))
        content = escape(risk.get("content", ""))
        suggestion = escape(risk.get("suggestion", ""))
        html = f'<div class="risk-item">'
        if rtype:
            html += f'<div class="risk-type">⚠️ {rtype}</div>'
        if content:
            html += f'<div class="risk-content">{content}</div>'
        if suggestion:
            html += f'<div class="risk-suggestion">建议：{suggestion}</div>'
        html += '</div>'
        items.append(html)
    return '\n'.join(items)


# ============================================================
# MD 片段构建（不变）
# ============================================================

def build_facts_md(facts):
    if not facts:
        return "无核心事实"
    lines = []
    for i, fact in enumerate(facts, 1):
        content = fact.get("content", "")
        location = fact.get("location", "")
        quote = fact.get("quote", "")
        line = f"{i}. {content}"
        if location:
            line += f"\n   📍 原文定位：{location}"
        if quote:
            line += f"\n   📎 原文引用：\"{quote}\""
        lines.append(line)
    return '\n'.join(lines)


def build_topics_md(topics):
    if not topics:
        return "无创作选题"
    lines = []
    for i, topic in enumerate(topics, 1):
        title = topic.get("title", f"选题{i}")
        angle = topic.get("angle", "")
        audience = topic.get("audience", "")
        form = topic.get("form", "")
        related = topic.get("related_facts", "")
        line = f"{i}. **{title}**"
        if angle:
            line += f"\n   - 切入角度：{angle}"
        if audience:
            line += f"\n   - 目标受众：{audience}"
        if form:
            line += f"\n   - 内容形式建议：{form}"
        if related:
            line += f"\n   - 关联事实：{related}"
        lines.append(line)
    return '\n'.join(lines)


def build_quotes_md(quotes):
    if not quotes:
        return None
    lines = []
    for i, quote in enumerate(quotes, 1):
        text = quote.get("text", "")
        location = quote.get("location", "")
        line = f"{i}. \"{text}\""
        if location:
            line += f"\n   📍 {location}"
        lines.append(line)
    return '\n'.join(lines)


def build_risks_md(risks):
    if not risks:
        return None
    lines = []
    for i, risk in enumerate(risks, 1):
        rtype = risk.get("type", "")
        content = risk.get("content", "")
        suggestion = risk.get("suggestion", "")
        line = f"{i}. ⚠️ {rtype}"
        if content:
            line += f"\n   内容：{content}"
        if suggestion:
            line += f"\n   建议：{suggestion}"
        lines.append(line)
    return '\n'.join(lines)


# ============================================================
# 导出函数
# ============================================================

def build_optional_md(items, heading_key="text"):
    """Render extension records without imposing a fixed count."""
    if not items:
        return None
    lines = []
    for i, item in enumerate(items, 1):
        if isinstance(item, str):
            lines.append(f"{i}. {item}")
            continue
        text = item.get(heading_key) or item.get("claim") or item.get("question") or item.get("difference") or ""
        details = []
        for key, label in (("source_id", "来源"), ("location", "定位"), ("based_on", "依据"),
                           ("reasoning", "推理"), ("suggested_check", "建议核查"), ("impact", "影响"),
                           ("resolution", "处理")):
            value = item.get(key)
            if value:
                if isinstance(value, list):
                    value = ", ".join(map(str, value))
                details.append(f"   - {label}：{value}")
        lines.append(f"{i}. {text}" + ("\n" + "\n".join(details) if details else ""))
    return '\n'.join(lines)


def escape_md(text):
    if not text:
        return ""
    return text.replace("|", "\\|").replace("{", "\\{").replace("}", "\\}")


def export_md(content_data, template_path, output_path):
    template = read_file(template_path)
    if not template:
        template = "# 内容素材包\n\n> 来源：{source}\n> 模式：{mode} | 字数：{word_count} | 密度分：{density_score}\n> 生成时间：{timestamp}\n\n---\n\n## 摘要\n\n{summary}\n\n---\n\n## 核心事实\n\n{core_facts}\n\n---\n\n## 创作选题\n\n{topics}\n{quotes_section}\n{risks_section}"

    summary = content_data.get("summary", "")
    facts = content_data.get("facts", [])
    topics = content_data.get("topics", [])
    quotes = content_data.get("quotes", [])
    risks = content_data.get("risks", [])
    viewpoints = build_optional_md(content_data.get("viewpoints", []))
    inferences = build_optional_md(content_data.get("inferences", []))
    gaps = build_optional_md(content_data.get("verification_gaps", []))
    conflicts = build_optional_md(content_data.get("conflicts", []))
    next_actions = build_optional_md(content_data.get("next_actions", []))

    facts_md = build_facts_md(facts)
    topics_md = build_topics_md(topics)
    quotes_md = build_quotes_md(quotes)
    risks_md = build_risks_md(risks)

    quotes_section = ""
    if quotes_md:
        quotes_section = f"\n---\n\n## 原文引用\n\n{quotes_md}"

    risks_section = ""
    if risks_md:
        risks_section = f"\n---\n\n## 风险提示\n\n{risks_md}"

    result = template
    result = result.replace("{source}", escape_md(content_data.get("source", "")))
    result = result.replace("{mode}", content_data.get("mode", ""))
    result = result.replace("{word_count}", str(content_data.get("word_count", "")))
    result = result.replace("{density_score}", str(content_data.get("density_score", "")))
    result = result.replace("{timestamp}", content_data.get("timestamp", datetime.now().isoformat()))
    result = result.replace("{summary}", summary)
    result = result.replace("{core_facts}", facts_md)
    result = result.replace("{topics}", topics_md)
    result = result.replace("{quotes_section}", quotes_section)
    result = result.replace("{risks_section}", risks_section)
    optional_sections = {
        "{viewpoints_section}": ("原文观点", viewpoints),
        "{inferences_section}": ("可标注推断", inferences),
        "{gaps_section}": ("核查缺口", gaps),
        "{conflicts_section}": ("来源冲突", conflicts),
        "{next_actions_section}": ("下一步动作", next_actions),
    }
    for placeholder, (heading, body) in optional_sections.items():
        result = result.replace(placeholder, f"\n---\n\n## {heading}\n\n{body}" if body else "")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    return output_path


def export_json(content_data, output_path):
    # JSON 是可继续创作和复核的事实源：保留未知扩展字段，避免导出时丢失证据链。
    export_data = dict(content_data)
    export_data.setdefault("schema_version", "1.0")
    export_data.setdefault("timestamp", datetime.now().isoformat())
    for key, default in {
        "source": "", "mode": "", "word_count": 0, "density_score": 0,
        "summary": "", "facts": [], "topics": [], "quotes": [], "risks": [],
        "sources": [], "viewpoints": [], "inferences": [],
        "verification_gaps": [], "conflicts": [], "next_actions": []
    }.items():
        export_data.setdefault(key, default)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    return output_path


def export_html(content_data, template_path, output_path):
    template = read_file(template_path)
    if not template:
        print("HTML模板读取失败", file=sys.stderr)
        sys.exit(1)

    facts = content_data.get("facts", [])
    topics = content_data.get("topics", [])
    quotes = content_data.get("quotes", [])
    risks = content_data.get("risks", [])

    facts_html = build_facts_html(facts)
    topics_html = build_topics_html(topics)
    quotes_html = build_quotes_html(quotes)
    risks_html = build_risks_html(risks)

    result = template
    result = result.replace("{source}", escape(content_data.get("source", "")))
    result = result.replace("{mode}", escape(content_data.get("mode", "")))
    result = result.replace("{word_count}", escape(str(content_data.get("word_count", ""))))
    result = result.replace("{density_score}", escape(str(content_data.get("density_score", ""))))
    result = result.replace("{summary}", escape(content_data.get("summary", "")))
    result = result.replace("{facts_html}", facts_html)
    result = result.replace("{topics_html}", topics_html)
    result = result.replace("{quotes_html}", quotes_html)
    result = result.replace("{risks_html}", risks_html)
    result = result.replace("{timestamp}", escape(content_data.get("timestamp", datetime.now().isoformat())))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 素材包导出器 v0.3")
    parser.add_argument("--content", required=True, help="素材包内容JSON文件路径")
    parser.add_argument("--template-md", help="MD模板文件路径")
    parser.add_argument("--template-html", help="HTML模板文件路径")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    parser.add_argument("--name", default="content-pack", help="输出文件名前缀（默认content-pack）")
    parser.add_argument("--formats", default="md,html,json", help="输出格式，逗号分隔（默认md,html,json）")
    args = parser.parse_args()

    with open(args.content, 'r', encoding='utf-8') as f:
        content_data = json.load(f)

    os.makedirs(args.output_dir, exist_ok=True)
    formats = [f.strip() for f in args.formats.split(',')]

    outputs = {}

    if 'md' in formats:
        md_path = os.path.join(args.output_dir, f"{args.name}.md")
        if args.template_md:
            export_md(content_data, args.template_md, md_path)
        else:
            export_md(content_data, "", md_path)
        outputs["md_path"] = md_path

    if 'html' in formats and args.template_html:
        html_path = os.path.join(args.output_dir, f"{args.name}.preview.html")
        export_html(content_data, args.template_html, html_path)
        outputs["html_path"] = html_path

    if 'json' in formats:
        json_path = os.path.join(args.output_dir, f"{args.name}.json")
        export_json(content_data, json_path)
        outputs["json_path"] = json_path

    outputs["status"] = "success"
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
