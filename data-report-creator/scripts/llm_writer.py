#!/usr/bin/env python3
"""LLM writer — calls OpenAI-compatible API to auto-generate report content.

Uses standard HTTP requests to call any OpenAI-compatible /v1/chat/completions
endpoint. Supports OpenAI, DeepSeek, Moonshot, Zhipu, Qwen, and any provider
that implements the OpenAI chat completions protocol.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TEMPERATURE = 0.7
REQUEST_TIMEOUT = 60


def _chat_completion(
    prompt: str,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not key:
        raise RuntimeError(
            "API key not set. Set OPENAI_API_KEY or LLM_API_KEY env var, or pass --api-key"
        )
    url = base_url or os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL
    endpoint = url.rstrip("/") + "/chat/completions"

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(endpoint, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_conclusion(
    data_profile: dict,
    section_summaries: list[dict],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    context_parts = []
    context_parts.append(
        f"数据概况: {data_profile.get('row_count', 0)} 行, "
        f"{data_profile.get('column_count', 0)} 列, "
        f"完整度 {data_profile.get('completeness', 0):.1%}"
    )
    if data_profile.get("numeric_columns"):
        context_parts.append(f"数值列: {', '.join(data_profile['numeric_columns'])}")

    for s in section_summaries:
        title = s.get("title", "")
        content = s.get("content", "")
        chart_type = s.get("chart_type", "")
        context_parts.append(f"- {title} ({chart_type}): {content}")

    context = "\n".join(context_parts)

    prompt = (
        "你是一位专业数据分析师。基于以下数据分析结果，撰写一段简洁的结论与建议（200-400字）。\n"
        "要求：\n"
        "1. 总结关键发现\n"
        "2. 指出数据中的趋势或异常\n"
        "3. 给出2-3条可执行的建议\n"
        "4. 语言专业但易懂，使用中文\n\n"
        f"数据分析结果:\n{context}"
    )

    return _chat_completion(
        prompt,
        api_key=api_key, base_url=base_url, model=model,
        max_tokens=max_tokens, temperature=temperature,
    )


def generate_section_description(
    section: dict,
    data_profile: dict,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 500,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    title = section.get("title", "")
    content_type = section.get("content_type", "")
    chart_config = section.get("chart_config", {})
    chart_type = chart_config.get("type", "")
    chart_data = chart_config.get("data", {})

    data_summary = ""
    if chart_data:
        labels = chart_data.get("labels", [])
        values = chart_data.get("values", [])
        if labels and values:
            pairs = [f"{l}: {v}" for l, v in zip(labels[:10], values[:10])]
            data_summary = ", ".join(pairs)

    prompt = (
        "你是一位专业数据分析师。为以下报告章节撰写一段简短的分析描述（50-150字）。\n"
        f"章节标题: {title}\n"
        f"内容类型: {content_type}\n"
        f"图表类型: {chart_type}\n"
        f"数据摘要: {data_summary}\n"
        f"数据概况: {data_profile.get('row_count', 0)} 行, "
        f"{data_profile.get('column_count', 0)} 列\n\n"
        "要求：语言专业简洁，使用中文，描述该章节的数据特征和关键发现。"
    )

    return _chat_completion(
        prompt,
        api_key=api_key, base_url=base_url, model=model,
        max_tokens=max_tokens, temperature=temperature,
    )


def generate_report_summary(
    title: str,
    data_profile: dict,
    section_titles: list[str],
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 300,
    temperature: float = DEFAULT_TEMPERATURE,
) -> str:
    prompt = (
        "你是一位专业数据分析师。为以下报告撰写一段简短的摘要（100-200字）。\n"
        f"报告标题: {title}\n"
        f"数据规模: {data_profile.get('row_count', 0)} 行, "
        f"{data_profile.get('column_count', 0)} 列, "
        f"完整度 {data_profile.get('completeness', 0):.1%}\n"
        f"报告章节: {', '.join(section_titles)}\n\n"
        "要求：概述报告内容和核心发现，语言专业简洁，使用中文。"
    )

    return _chat_completion(
        prompt,
        api_key=api_key, base_url=base_url, model=model,
        max_tokens=max_tokens, temperature=temperature,
    )


def enhance_report(
    report: dict,
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = DEFAULT_MODEL,
    generate_conclusions: bool = True,
    generate_descriptions: bool = False,
    generate_summary: bool = False,
) -> dict:
    data_profile = report.get("data_profile", {})
    sections = report.get("sections", [])

    section_summaries = []
    for s in sections:
        if s.get("content_type") in ("chart", "summary", "kpi"):
            section_summaries.append({
                "title": s.get("title", ""),
                "content": s.get("content", "")[:200],
                "chart_type": s.get("chart_config", {}).get("type", ""),
            })

    if generate_summary:
        title = report.get("title", "")
        section_titles = [s.get("title", "") for s in sections]
        summary = generate_report_summary(
            title, data_profile, section_titles,
            api_key=api_key, base_url=base_url, model=model,
        )
        for s in sections:
            if s.get("id") == "cover":
                s["content"] = summary
                break

    if generate_descriptions:
        for s in sections:
            if s.get("content_type") == "chart" and s.get("content", "").startswith("[填写]"):
                desc = generate_section_description(
                    s, data_profile,
                    api_key=api_key, base_url=base_url, model=model,
                )
                s["content"] = desc

    if generate_conclusions:
        for s in sections:
            if s.get("id") == "conclusion" and s.get("content", "").startswith("[填写]"):
                conclusion = generate_conclusion(
                    data_profile, section_summaries,
                    api_key=api_key, base_url=base_url, model=model,
                )
                s["content"] = conclusion
                break

    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LLM writer for report content generation")
    parser.add_argument("report_json", help="Path to report JSON")
    parser.add_argument("--api-key", help="API key (or set OPENAI_API_KEY / LLM_API_KEY env)")
    parser.add_argument("--base-url", help="API base URL (or set OPENAI_BASE_URL / LLM_BASE_URL env)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--no-conclusions", action="store_true", help="Skip conclusion generation")
    parser.add_argument("--descriptions", action="store_true", help="Generate section descriptions")
    parser.add_argument("--summary", action="store_true", help="Generate report summary")
    parser.add_argument("--output", "-o", help="Output path (default: overwrite input)")
    args = parser.parse_args()

    report = json.loads(Path(args.report_json).read_text(encoding="utf-8"))
    enhanced = enhance_report(
        report,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
        generate_conclusions=not args.no_conclusions,
        generate_descriptions=args.descriptions,
        generate_summary=args.summary,
    )

    output_path = args.output or args.report_json
    Path(output_path).write_text(json.dumps(enhanced, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] Report enhanced: {output_path}")
    for s in enhanced.get("sections", []):
        if s.get("id") == "conclusion":
            print(f"\n结论与建议:\n{s.get('content', '')}")
