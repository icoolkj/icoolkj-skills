#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docx2md —— 从 docx 取回 Markdown。

两种来源，优先级不同：
  1) 隐藏层（本工具生成的「双层 docx」都有）→ 逐字节还原原始 Markdown，零损耗
  2) 结构化反解（普通 docx、或被其他工具重排过）→ 按样式/编号还原标题、列表、表格、代码块

用法
----
    python scripts/docx2md.py 交付版.docx
    python scripts/docx2md.py 交付版.docx -o 取回.md
    python scripts/docx2md.py 别人的文档.docx --structure   # 强制走结构化反解
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import docxkit  # noqa: E402


def extract_one(src: str, args) -> dict:
    md, origin = docxkit.docx_to_markdown(src, prefer_embedded=not args.structure)

    if args.output and len(args.inputs) > 1:
        os.makedirs(args.output, exist_ok=True)
        out = os.path.join(args.output, os.path.splitext(os.path.basename(src))[0] + ".md")
    elif args.output:
        out = args.output
    else:
        out = os.path.splitext(src)[0] + ".md"

    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)

    return {
        "input": src,
        "output": os.path.abspath(out),
        "origin": "embedded" if origin == "embedded" else "structure",
        "chars": len(md),
        "headings": sum(1 for line in md.split("\n") if line.startswith("#")),
        "tables": md.count("\n| ---") + (1 if md.startswith("| ---") else 0),
        "code_blocks": md.count("```") // 2,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="docx2md",
        description="docx → Markdown（优先取隐藏层，缺失时结构化反解）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("inputs", nargs="+", help=".docx 文件路径，可多个")
    ap.add_argument("-o", "--output", help="输出 .md 路径；多个输入时视为输出目录")
    ap.add_argument("--structure", action="store_true", help="忽略隐藏层，强制按样式反解")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    args = ap.parse_args()

    files: list[str] = []
    for item in args.inputs:
        if any(ch in item for ch in "*?["):
            files.extend(sorted(glob.glob(item)))
        else:
            files.append(item)
    args.inputs = files

    if not files:
        print("没有匹配到任何输入文件。", file=sys.stderr)
        return 2

    results = []
    for src in files:
        if not os.path.isfile(src):
            print(f"文件不存在：{src}", file=sys.stderr)
            return 2
        try:
            results.append(extract_one(src, args))
        except Exception as exc:  # noqa: BLE001
            print(f"提取失败 {src}：{exc}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        label = {"embedded": "隐藏层（无损）", "structure": "结构化反解（普通 docx）"}
        for r in results:
            print(f"✓ {os.path.basename(r['output'])}  {r['chars']} 字 · 标题 {r['headings']} · 表格 {r['tables']} · 代码块 {r['code_blocks']}")
            print(f"   来源：{label[r['origin']]}")
            if r["origin"] == "structure":
                print("   提示：这份 docx 没有内嵌 Markdown，内容按样式推断，复杂排版可能有细节损失。")
            print(f"   → {r['output']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
