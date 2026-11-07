#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md2docx —— 把 Markdown 转成「双层 docx」：Word 排版给人读，原始 Markdown 藏在文件里。

用法
----
    python scripts/md2docx.py 文档.md
    python scripts/md2docx.py 文档.md -o 交付版.docx --toc
    python scripts/md2docx.py 文档.md --no-embed      # 只生成纯 Word，不带隐藏层
    python scripts/md2docx.py 文档.md --preset formal # 换排版预设（standard/clean/formal/blog）

生成的 .docx 同时具备两种形态：
  · 双击打开 → 带标题层级、表格、代码框的 Word 文档
  · docx2md.py 读取 → 逐字节还原原始 Markdown

多文件：支持通配（shell 展开）或一次传多个路径。
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import docxkit  # noqa: E402


def human(n: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n < 1024 or unit == "MB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}MB"


def convert_one(src: str, args) -> dict:
    out = args.output
    if out and len(args.inputs) > 1:
        os.makedirs(out, exist_ok=True)
        out = os.path.join(out, os.path.splitext(os.path.basename(src))[0] + ".docx")

    res = docxkit.markdown_to_docx(
        src,
        out,
        embed_source=args.embed_mode != "none",
        embed_mode=args.embed_mode,
        toc=args.toc,
        title=args.title,
        preset=args.preset,
    )

    ok_validate = True
    problems: list[str] = []
    if not args.no_validate:
        v = docxkit.validate_docx(res["path"])
        ok_validate, problems = v["ok"], v["problems"]

    return {
        "input": src,
        "output": res["path"],
        "size": human(res["size"]),
        "blocks": res["blocks"],
        "preset": res.get("preset", ""),
        "embedded": res.get("embedded"),
        "md_kb": round(res.get("md_bytes", 0) / 1024, 1),
        "valid": ok_validate,
        "problems": problems,
        "warnings": res["warnings"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="md2docx",
        description="Markdown → 双层 docx（Word 可见排版 + 内嵌原始 Markdown）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("inputs", nargs="+", help="Markdown 文件路径，可多个")
    ap.add_argument("-o", "--output", help="输出 .docx 路径；多个输入时视为输出目录")
    ap.add_argument("--toc", action="store_true", help="插入目录域（Word 中右键更新域生成）")
    ap.add_argument("--title", help="文档属性里的标题，默认取第一个一级标题")
    ap.add_argument("--preset", "--style", dest="preset", default="standard",
                    choices=docxkit.preset_choices(),
                    help="排版预设：standard 通用（默认）/ clean 简约 / formal 正式公文 / blog 博客")
    ap.add_argument("--embed-mode", choices=["both", "customxml", "hidden", "none"], default="both",
                    help="隐藏层写入方式：both=双保险（默认）、customxml=仅自定义部件、hidden=仅隐藏文字、none=纯 Word")
    ap.add_argument("--no-embed", action="store_true", help="等价于 --embed-mode none")
    ap.add_argument("--no-validate", action="store_true", help="跳过 OOXML 严格自检（不建议）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出结果，便于程序调用")
    args = ap.parse_args()
    if args.no_embed:
        args.embed_mode = "none"

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
            results.append(convert_one(src, args))
        except Exception as exc:  # noqa: BLE001
            print(f"转换失败 {src}：{exc}", file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            flag = "✓" if r["valid"] else "✗"
            print(f"{flag} {os.path.basename(r['output'])}  {r['size']}  {r['blocks']} 块")
            print(f"   排版：{r['preset']}")
            print(f"   隐藏层：{'已写入 ' + str(r['md_kb']) + ' KB' if r['embedded'] else '未写入（纯 Word）'}")
            if not r["valid"]:
                for p in r["problems"]:
                    print(f"   ! {p}")
            for w in r["warnings"]:
                print(f"   · {w}")
            print(f"   → {r['output']}")
        if not all(r["valid"] for r in results):
            print("\n自检未通过：文档可能在 Word 中触发「修复」提示，请把上面的问题反馈给维护者。", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
