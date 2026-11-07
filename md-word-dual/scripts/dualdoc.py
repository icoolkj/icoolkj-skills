#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dualdoc —— 双层文档统一入口。

四个子命令
----------
    convert   自动判断方向：.md → .docx，.docx → .md
    verify    体检一个 docx：有没有隐藏层、结构是否合规、能否原样取回
    roundtrip 往返校验：md → docx → md，比对是否逐字节一致
    info      快速查看 docx 的部件与隐藏层体积

用法
----
    python scripts/dualdoc.py convert 文档.md
    python scripts/dualdoc.py verify 交付版.docx
    python scripts/dualdoc.py roundtrip 文档.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import docxkit  # noqa: E402


def cmd_convert(args) -> int:
    src = args.path
    if not os.path.isfile(src):
        print(f"文件不存在：{src}", file=sys.stderr)
        return 2
    ext = os.path.splitext(src)[1].lower()

    if ext in (".md", ".markdown", ".mdown"):
        res = docxkit.markdown_to_docx(src, args.output, embed_source=not args.no_embed, toc=args.toc)
        v = docxkit.validate_docx(res["path"]) if not args.no_validate else {"ok": True, "problems": []}
        print(f"{'✓' if v['ok'] else '✗'} {res['path']}")
        print(f"   {res['blocks']} 个内容块 · {res['size'] / 1024:.1f} KB · "
              f"隐藏层 {'已写入' if res.get('embedded') else '未写入'}")
        for p in v["problems"]:
            print(f"   ! {p}")
        for w in res["warnings"]:
            print(f"   · {w}")
        return 0 if v["ok"] else 1

    if ext == ".docx":
        md, origin = docxkit.docx_to_markdown(src, prefer_embedded=not args.structure)
        out = args.output or os.path.splitext(src)[0] + ".md"
        with open(out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"✓ {out}  （来源：{'隐藏层，无损' if origin == 'embedded' else '结构化反解'}，{len(md)} 字）")
        return 0

    print("只支持 .md / .markdown / .docx", file=sys.stderr)
    return 2


def cmd_verify(args) -> int:
    src = args.path
    if not os.path.isfile(src):
        print(f"文件不存在：{src}", file=sys.stderr)
        return 2

    info = docxkit.inspect_docx(src)
    v = docxkit.validate_docx(src)

    if args.json:
        print(json.dumps({"inspect": info, "validate": v}, ensure_ascii=False, indent=2))
        return 0 if v["ok"] else 1

    print(f"文件：{os.path.basename(src)}  ({info.get('size', 0) / 1024:.1f} KB · {info.get('parts', 0)} 个部件)")
    if not info.get("ok"):
        print(f"✗ 不是有效的 docx：{info.get('error')}")
        return 1
    print(f"{'✓' if v['ok'] else '✗'} 结构自检：{'通过' if v['ok'] else '发现 ' + str(len(v['problems'])) + ' 个问题'}")
    for p in v["problems"]:
        print(f"   ! {p}")

    if info.get("layers"):
        lay = info["layers"]
        marks = " ".join(
            f"{name}={'✓' if lay.get(key) else '✗'}"
            for key, name in (("customxml", "自定义部件"), ("hidden_text", "隐藏文字"))
        )
        print(f"· 隐藏层：{marks}")
    if info.get("has_embedded"):
        if info.get("embedded_readable"):
            print(f"✓ 原始 Markdown：{info['embedded_chars']} 字 / {info['embedded_bytes']} 字节，可无损取回")
        else:
            print("✗ 隐藏层存在但校验不通过（可能被重写过或校验和不符）")
    else:
        print("· 这是一份普通 docx，转 Markdown 时按样式反解，复杂排版可能有细节损失。")

    return 0 if v["ok"] else 1


def cmd_roundtrip(args) -> int:
    src = args.path
    if not os.path.isfile(src):
        print(f"文件不存在：{src}", file=sys.stderr)
        return 2

    if os.path.splitext(src)[1].lower() == ".docx":
        md, origin = docxkit.docx_to_markdown(src)
        if origin != "embedded":
            print("· 这份 docx 没有隐藏层，往返校验以结构化反解结果为准。")
        print(f"取回 {len(md)} 字。")
        return 0

    with open(src, "r", encoding="utf-8-sig") as fh:
        original = fh.read()

    with tempfile.TemporaryDirectory() as tmp:
        docx_path = os.path.join(tmp, "roundtrip.docx")
        docxkit.markdown_to_docx(src, docx_path, embed_source=True, toc=False)
        back, origin = docxkit.docx_to_markdown(docx_path)

    identical = back == original
    print(f"往返方式：{'隐藏层（无损）' if origin == 'embedded' else '结构化反解'}")
    print(f"原文 {len(original)} 字 · 取回 {len(back)} 字")
    if identical:
        print("✓ 逐字节一致，往返无损耗。")
        return 0

    a, b = original.split("\n"), back.split("\n")
    diff = [(i + 1, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y][:5]
    print(f"✗ 存在差异（行数 {len(a)} → {len(b)}）")
    for ln, x, y in diff:
        print(f"   第 {ln} 行\n     原：{x[:90]}\n     新：{y[:90]}")
    return 1


def cmd_info(args) -> int:
    info = docxkit.inspect_docx(args.path)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if info.get("ok") else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="dualdoc",
        description="双层文档统一入口：Markdown ⇄ Word 双向转换与体检",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    c1 = sub.add_parser("convert", help="自动判断方向转换")
    c1.add_argument("path")
    c1.add_argument("-o", "--output")
    c1.add_argument("--toc", action="store_true", help="md→docx 时插入目录域")
    c1.add_argument("--no-embed", action="store_true", help="md→docx 时不写隐藏层")
    c1.add_argument("--structure", action="store_true", help="docx→md 时强制结构化反解")
    c1.add_argument("--no-validate", action="store_true")
    c1.set_defaults(func=cmd_convert)

    c2 = sub.add_parser("verify", help="体检 docx：结构自检 + 隐藏层状态")
    c2.add_argument("path")
    c2.add_argument("--json", action="store_true")
    c2.set_defaults(func=cmd_verify)

    c3 = sub.add_parser("roundtrip", help="往返校验是否无损")
    c3.add_argument("path")
    c3.set_defaults(func=cmd_roundtrip)

    c4 = sub.add_parser("info", help="查看 docx 部件与体积")
    c4.add_argument("path")
    c4.set_defaults(func=cmd_info)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
