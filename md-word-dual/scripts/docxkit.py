#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docxkit —— Markdown ⇄ DOCX 双向引擎（双层文档核心库）

设计要点
--------
1. 零第三方依赖：只用标准库构造 / 解析 OOXML 包。
2. 双层结构：
   - 可见层：真正的 Word 排版（Heading 样式、大纲级别、表格、代码框、引用块）
   - 隐藏层：原始 Markdown 经 gzip+base64 后写入 customXml/item1.xml
     载体为 OOXML 官方「自定义 XML 部件」，Word 不渲染但随包保存，
     因此同一个 .docx 既可给人读，又可被程序无损取回 Markdown。
3. 退化路径：若隐藏层缺失（被第三方工具重排、或被另存为纯净 docx），
   docx_to_markdown() 自动改用「结构化反解」，按样式 / 编号还原 Markdown。

本模块不提供 CLI，供 md2docx.py / docx2md.py / dualdoc.py 调用。
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import html
import os
import re
import struct
import zipfile
from datetime import datetime, timezone

# ---------------------------------------------------------------- 命名空间
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CUSTOM_XML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/customXml"

MD_NS = "https://icoolkj.com/ns/md-word-dual/1.0"
MD_PART = "customXml/item1.xml"
MD_PROPS_PART = "customXml/itemProps1.xml"
HIDDEN_MARK = "MDWORDDUAL:v1:gzip+base64:"

# 版心宽度：A4（11906 twips）减去左右各 2cm（1134 twips）→ EMU
CONTENT_WIDTH_EMU = (11906 - 1134 * 2) * 635

# ---------------------------------------------------------------- 小工具


def esc(text: str) -> str:
    """XML 文本转义（保留引号原样，便于阅读）。"""
    return html.escape(text, quote=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_cjk(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    return (
        0x3040 <= o <= 0x30FF
        or 0x4E00 <= o <= 0x9FFF
        or 0x3400 <= o <= 0x4DBF
        or 0x3000 <= o <= 0x303F
        or 0xFF00 <= o <= 0xFFEF
    )


def join_soft_lines(lines: list[str]) -> str:
    """把 Markdown 的软换行合并成一行：中英文之间按需补空格。"""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if not out:
            out = ln
        elif _is_cjk(out[-1]) or _is_cjk(ln[0]):
            out += ln
        else:
            out += " " + ln
    return out


# ---------------------------------------------------------------- Markdown 解析


def _split_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    cells, buf, i = [], "", 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            buf += "|"
            i += 2
            continue
        if ch == "|":
            cells.append(buf.strip())
            buf = ""
            i += 1
            continue
        buf += ch
        i += 1
    cells.append(buf.strip())
    return cells


def _parse_align(line: str) -> list[str]:
    out = []
    for c in _split_row(line):
        c = c.strip()
        left, right = c.startswith(":"), c.endswith(":")
        out.append("center" if left and right else ("right" if right else ("left" if left else "")))
    return out


_LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_HEAD_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR_RE = re.compile(r"^\s{0,3}([-*_])\s*(\1\s*){2,}$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w+#.-]*)\s*$")
_QUOTE_RE = re.compile(r"^\s{0,3}>\s?")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?[\s:|-]*$")


def _is_block_start(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    return bool(
        _HEAD_RE.match(line)
        or _FENCE_RE.match(line)
        or _HR_RE.match(line)
        or _QUOTE_RE.match(line)
        or _LIST_RE.match(line)
    )


def parse_markdown(text: str) -> list[dict]:
    """把 Markdown 切成块。支持：标题/段落/代码块/引用/列表/表格/分隔线。"""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[dict] = []
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        m = _FENCE_RE.match(line)
        if m:
            fence, lang = m.group(1), m.group(2) or ""
            i += 1
            buf = []
            close = re.compile(r"^\s*" + re.escape(fence[0]) + "{3,}\\s*$")
            while i < n and not close.match(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            blocks.append({"t": "code", "lang": lang, "text": "\n".join(buf)})
            continue

        m = _HEAD_RE.match(line)
        if m:
            blocks.append({"t": "heading", "level": len(m.group(1)), "text": m.group(2).strip()})
            i += 1
            continue

        if _HR_RE.match(line):
            blocks.append({"t": "hr"})
            i += 1
            continue

        if _QUOTE_RE.match(line):
            buf = []
            while i < n:
                if _QUOTE_RE.match(lines[i]):
                    buf.append(_QUOTE_RE.sub("", lines[i], count=1))
                    i += 1
                elif not lines[i].strip() and i + 1 < n and _QUOTE_RE.match(lines[i + 1]):
                    buf.append("")
                    i += 1
                else:
                    break
            blocks.append({"t": "quote", "text": "\n".join(buf)})
            continue

        if "|" in line and i + 1 < n and _TABLE_SEP_RE.match(lines[i + 1]) and "-" in lines[i + 1]:
            header = _split_row(line)
            aligns = _parse_align(lines[i + 1])
            i += 2
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(_split_row(lines[i]))
                i += 1
            blocks.append({"t": "table", "header": header, "align": aligns, "rows": rows})
            continue

        m = _LIST_RE.match(line)
        if m:
            items = []
            while i < n:
                mm = _LIST_RE.match(lines[i])
                if mm:
                    indent = len(mm.group(1).expandtabs(4))
                    marker = mm.group(2)
                    items.append(
                        {
                            "ordered": bool(re.match(r"^\d", marker)),
                            "level": min(indent // 2, 4),
                            "text": mm.group(3).strip(),
                        }
                    )
                    i += 1
                elif lines[i].strip() and items and lines[i].startswith((" ", "\t")):
                    items[-1]["text"] += "\n" + lines[i].strip()
                    i += 1
                else:
                    break
            blocks.append({"t": "list", "items": items})
            continue

        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not _is_block_start(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        blocks.append({"t": "para", "text": join_soft_lines(buf)})

    return blocks


# ---------------------------------------------------------------- 行内解析


def parse_inline(text: str, fmt: dict | None = None) -> list[tuple[str, dict]]:
    """把一段行内文本拆成 (文字, 样式) 片段。"""
    fmt = fmt or {}
    out: list[tuple[str, dict]] = []
    buf = ""
    i = 0

    def flush():
        nonlocal buf
        if buf:
            out.append((buf, dict(fmt)))
            buf = ""

    def merged(**kw):
        d = dict(fmt)
        d.update(kw)
        return d

    while i < len(text):
        ch = text[i]

        if ch == "\\" and i + 1 < len(text):
            buf += text[i + 1]
            i += 2
            continue

        if ch == "`":
            m = re.match(r"(`+)(.+?)\1", text[i:], re.S)
            if m:
                flush()
                out.append((m.group(2), merged(code=True)))
                i += m.end()
                continue

        if text.startswith("**", i) or text.startswith("__", i):
            mk = text[i : i + 2]
            m = re.match(re.escape(mk) + r"(.+?)" + re.escape(mk), text[i:], re.S)
            if m:
                flush()
                out.extend(parse_inline(m.group(1), merged(bold=True)))
                i += m.end()
                continue

        if ch in "*_":
            pat = r"\*(?!\*)(.+?)(?<!\*)\*" if ch == "*" else r"_(?!_)(.+?)(?<!_)_"
            m = re.match(pat, text[i:], re.S)
            if m:
                flush()
                out.extend(parse_inline(m.group(1), merged(italic=True)))
                i += m.end()
                continue

        if text.startswith("~~", i):
            m = re.match(r"~~(.+?)~~", text[i:], re.S)
            if m:
                flush()
                out.extend(parse_inline(m.group(1), merged(strike=True)))
                i += m.end()
                continue

        if text.startswith("![", i):
            m = re.match(r'!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"[^"]*")?\s*\)', text[i:])
            if m:
                flush()
                out.append(("\x00IMG", merged(image=m.group(2), alt=m.group(1))))
                i += m.end()
                continue

        if ch == "[":
            m = re.match(r'\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+"[^"]*")?\s*\)', text[i:])
            if m:
                flush()
                for t, f in parse_inline(m.group(1), fmt):
                    f = dict(f)
                    f["link"] = m.group(2)
                    out.append((t, f))
                i += m.end()
                continue

        if text.startswith("<br", i):
            m = re.match(r"<br\s*/?>", text[i:], re.I)
            if m:
                flush()
                out.append(("\n", dict(fmt)))
                i += m.end()
                continue

        buf += ch
        i += 1

    flush()
    return out


def tokens_to_plain(text: str) -> str:
    """去掉行内标记，得到纯文本（用于表格单元格、目录等）。"""
    return "".join(t for t, f in parse_inline(text) if t != "\x00IMG" or f.get("alt"))


# ---------------------------------------------------------------- 样式 / 编号常量

# OOXML 对属性子元素顺序有严格要求，顺序错会被 Word 判定为需要修复
RPR_ORDER = [
    "rStyle", "rFonts", "b", "bCs", "i", "iCs", "caps", "smallCaps", "strike", "dstrike",
    "outline", "shadow", "emboss", "imprint", "noProof", "snapToGrid", "vanish", "webHidden",
    "color", "spacing", "w", "kern", "position", "sz", "szCs", "highlight", "u", "effect",
    "bdr", "shd", "fitText", "vertAlign", "rtl", "cs", "em", "lang", "eastAsianLayout",
    "specVanish", "oMath",
]

PPR_ORDER = [
    "pStyle", "keepNext", "keepLines", "pageBreakBefore", "framePr", "widowControl", "numPr",
    "suppressLineNumbers", "pBdr", "shd", "tabs", "suppressAutoHyphens", "kinsoku", "wordWrap",
    "overflowPunct", "topLinePunct", "autoSpaceDE", "autoSpaceDN", "bidi", "adjustRightInd",
    "snapToGrid", "spacing", "ind", "contextualSpacing", "mirrorIndents", "suppressOverlap",
    "jc", "textDirection", "textAlignment", "textboxTightWrap", "outlineLvl", "divId",
    "cnfStyle", "rPr", "sectPr", "pPrChange",
]


def ordered_xml(wrapper: str, parts: dict, order: list[str]) -> str:
    """按 OOXML 规定顺序拼接子元素。"""
    if not parts:
        return ""
    body = "".join(parts[k] for k in order if k in parts)
    return f"<w:{wrapper}>{body}</w:{wrapper}>"

# ---------------------------------------------------------------- 排版预设
#
# 每种预设只改参数，不改结构。字号单位为半磅（w:sz），行距/段后单位为二十分之一磅。
# 代码块底色一律用浅色：正文 run 未设颜色，深色底会让代码变成黑底黑字。

PRESETS: dict[str, dict] = {
    "standard": {
        "label": "通用：等线正文 + 雅黑标题",
        "body_ascii": "Calibri",
        "body_ea": "\u7b49\u7ebf",
        "head_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "mono": "Consolas",
        "mono_ea": "\u5b8b\u4f53",
        "body_sz": 22,
        "title_sz": 40,
        "h1_sz": 32,
        "h2_sz": 28,
        "h3_sz": 24,
        "h4_sz": 22,
        "code_sz": 17,
        "quote_sz": 21,
        "table_sz": 20,
        "line_body": 340,
        "after_body": 140,
        "head_color": "1F2328",
        "head4_color": "3D444D",
        "code_fill": "F6F8FA",
        "code_border": "D8DEE4",
        "quote_fill": "F7F8FA",
        "quote_border": "D0D7DE",
        "quote_color": "4A5158",
        "link_color": "0969DA",
        "table_head_fill": "F2F4F7",
        "page_w": 11906,
        "page_h": 16838,
        "margin": (1134, 1134, 1134, 1134),
    },
    "clean": {
        "label": "简约：全域雅黑，宽行距，适合屏幕阅读",
        "body_ascii": "Microsoft YaHei",
        "body_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "head_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "mono": "Consolas",
        "mono_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "body_sz": 21,
        "title_sz": 38,
        "h1_sz": 32,
        "h2_sz": 26,
        "h3_sz": 23,
        "h4_sz": 21,
        "code_sz": 17,
        "quote_sz": 20,
        "table_sz": 19,
        "line_body": 380,
        "after_body": 160,
        "head_color": "111827",
        "head4_color": "374151",
        "code_fill": "F5F5F5",
        "code_border": "E0E0E0",
        "quote_fill": "F5F7FA",
        "quote_border": "DDE3EA",
        "quote_color": "4B5563",
        "link_color": "1A73E8",
        "table_head_fill": "E8F0FE",
        "page_w": 11906,
        "page_h": 16838,
        "margin": (1134, 1134, 1134, 1134),
    },
    "formal": {
        "label": "正式：仿宋正文 + 黑体标题，适合打印与公文",
        "body_ascii": "Times New Roman",
        "body_ea": "\u4eff\u5b8b",
        "head_ea": "\u9ed1\u4f53",
        "mono": "Courier New",
        "mono_ea": "\u4eff\u5b8b",
        "body_sz": 24,
        "title_sz": 40,
        "h1_sz": 32,
        "h2_sz": 28,
        "h3_sz": 24,
        "h4_sz": 22,
        "code_sz": 18,
        "quote_sz": 22,
        "table_sz": 21,
        "line_body": 360,
        "after_body": 120,
        "head_color": "000000",
        "head4_color": "000000",
        "code_fill": "F2F2F2",
        "code_border": "C8C8C8",
        "quote_fill": "F7F7F7",
        "quote_border": "B0B0B0",
        "quote_color": "333333",
        "link_color": "000000",
        "table_head_fill": "E8E8E8",
        "page_w": 11906,
        "page_h": 16838,
        "margin": (1440, 1800, 1440, 1800),
    },
    "blog": {
        "label": "博客：大标题、宽段距，适合在线发布",
        "body_ascii": "Microsoft YaHei",
        "body_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "head_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "mono": "Consolas",
        "mono_ea": "\u5fae\u8f6f\u96c5\u9ed1",
        "body_sz": 24,
        "title_sz": 46,
        "h1_sz": 36,
        "h2_sz": 30,
        "h3_sz": 26,
        "h4_sz": 23,
        "code_sz": 19,
        "quote_sz": 22,
        "table_sz": 20,
        "line_body": 420,
        "after_body": 200,
        "head_color": "111827",
        "head4_color": "374151",
        "code_fill": "F4F6F8",
        "code_border": "DDE3EA",
        "quote_fill": "F6F8FA",
        "quote_border": "CFD8E3",
        "quote_color": "4B5563",
        "link_color": "0066CC",
        "table_head_fill": "EAF2FB",
        "page_w": 11906,
        "page_h": 16838,
        "margin": (851, 1134, 851, 1134),
    },
}


def get_preset(name: str | None) -> dict:
    """取预设；名字不认识时回落到 standard，绝不因参数报错。"""
    return PRESETS.get((name or "standard").lower()) or PRESETS["standard"]


_STYLES_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{w_ns}">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="{body_ascii}" w:hAnsi="{body_ascii}" w:eastAsia="{body_ea}" w:cs="{body_ascii}"/>
        <w:sz w:val="{body_sz}"/><w:szCs w:val="{body_sz}"/>
        <w:lang w:val="en-US" w:eastAsia="zh-CN"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr><w:spacing w:line="{line_body}" w:lineRule="auto" w:after="120"/></w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:line="{line_body}" w:lineRule="auto" w:after="120"/></w:pPr>
    <w:rPr><w:rFonts w:ascii="{body_ascii}" w:hAnsi="{body_ascii}" w:eastAsia="{body_ea}"/><w:sz w:val="{body_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="BodyText">
    <w:name w:val="Body Text"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:line="{line_body}" w:lineRule="auto" w:after="{after_body}"/><w:ind w:firstLine="0"/></w:pPr>
    <w:rPr><w:sz w:val="{body_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
    <w:pPr>
      <w:keepNext/>
      <w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" w:color="{head_color}"/></w:pBdr>
      <w:spacing w:before="0" w:after="240" w:line="300" w:lineRule="auto"/>
    </w:pPr>
    <w:rPr><w:rFonts w:eastAsia="{head_ea}"/><w:b/><w:color w:val="{head_color}"/><w:sz w:val="{title_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
    <w:pPr>
      <w:keepNext/><w:keepLines/>
      <w:pBdr><w:bottom w:val="single" w:sz="6" w:space="4" w:color="{quote_border}"/></w:pBdr>
      <w:spacing w:before="360" w:after="140" w:line="300" w:lineRule="auto"/>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr><w:rFonts w:eastAsia="{head_ea}"/><w:b/><w:color w:val="{head_color}"/><w:sz w:val="{h1_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
    <w:pPr>
      <w:keepNext/><w:keepLines/><w:spacing w:before="280" w:after="120" w:line="300" w:lineRule="auto"/>
      <w:outlineLvl w:val="1"/>
    </w:pPr>
    <w:rPr><w:rFonts w:eastAsia="{head_ea}"/><w:b/><w:color w:val="{head_color}"/><w:sz w:val="{h2_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading3">
    <w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
    <w:pPr>
      <w:keepNext/><w:keepLines/><w:spacing w:before="240" w:after="100" w:line="300" w:lineRule="auto"/>
      <w:outlineLvl w:val="2"/>
    </w:pPr>
    <w:rPr><w:rFonts w:eastAsia="{head_ea}"/><w:b/><w:color w:val="{head_color}"/><w:sz w:val="{h3_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading4">
    <w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="BodyText"/><w:qFormat/>
    <w:pPr>
      <w:keepNext/><w:keepLines/><w:spacing w:before="200" w:after="80" w:line="300" w:lineRule="auto"/>
      <w:outlineLvl w:val="3"/>
    </w:pPr>
    <w:rPr><w:rFonts w:eastAsia="{head_ea}"/><w:b/><w:color w:val="{head4_color}"/><w:sz w:val="{h4_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="CodeBlock">
    <w:name w:val="Code Block"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr>
      <w:pBdr>
        <w:top w:val="single" w:sz="4" w:space="4" w:color="{code_border}"/>
        <w:left w:val="single" w:sz="4" w:space="4" w:color="{code_border}"/>
        <w:bottom w:val="single" w:sz="4" w:space="4" w:color="{code_border}"/>
        <w:right w:val="single" w:sz="4" w:space="4" w:color="{code_border}"/>
      </w:pBdr>
      <w:shd w:val="clear" w:color="auto" w:fill="{code_fill}"/>
      <w:spacing w:before="120" w:after="120" w:line="240" w:lineRule="auto"/>
      <w:ind w:left="113" w:right="113"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="{mono}" w:hAnsi="{mono}" w:cs="{mono}" w:eastAsia="{mono_ea}"/>
      <w:sz w:val="{code_sz}"/><w:szCs w:val="{code_sz}"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Quote">
    <w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr>
      <w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="{quote_border}"/></w:pBdr>
      <w:shd w:val="clear" w:color="auto" w:fill="{quote_fill}"/>
      <w:spacing w:before="120" w:after="140" w:line="320" w:lineRule="auto"/>
      <w:ind w:left="284" w:right="113"/>
    </w:pPr>
    <w:rPr><w:color w:val="{quote_color}"/><w:sz w:val="{quote_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="ListParagraph">
    <w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/><w:qFormat/>
    <w:pPr><w:spacing w:line="320" w:lineRule="auto" w:after="60"/></w:pPr>
    <w:rPr><w:sz w:val="{body_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="TableText">
    <w:name w:val="Table Text"/><w:basedOn w:val="Normal"/>
    <w:pPr><w:spacing w:before="40" w:after="40" w:line="280" w:lineRule="auto"/></w:pPr>
    <w:rPr><w:sz w:val="{table_sz}"/></w:rPr>
  </w:style>
  <w:style w:type="character" w:styleId="Hyperlink">
    <w:name w:val="Hyperlink"/>
    <w:rPr><w:color w:val="{link_color}"/><w:u w:val="single"/></w:rPr>
  </w:style>
</w:styles>
"""


def styles_xml(preset: str | None = "standard") -> str:
    """按预设生成 styles.xml。"""
    p = dict(get_preset(preset))
    p["w_ns"] = W_NS
    return _STYLES_TEMPLATE.format(**p)


def preset_choices() -> list[str]:
    return list(PRESETS.keys())


NUMBERING_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="{W_NS}">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="420" w:hanging="300"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:hint="default"/></w:rPr>
    </w:lvl>
    <w:lvl w:ilvl="1">
      <w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u25e6"/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="840" w:hanging="300"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:hint="default"/></w:rPr>
    </w:lvl>
    <w:lvl w:ilvl="2">
      <w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u25aa"/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="1260" w:hanging="300"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:hint="default"/></w:rPr>
    </w:lvl>
    <w:lvl w:ilvl="3">
      <w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="\u2022"/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="1680" w:hanging="300"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
  <w:abstractNum w:abstractNumId="1">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="420" w:hanging="360"/></w:pPr>
    </w:lvl>
    <w:lvl w:ilvl="1">
      <w:start w:val="1"/><w:numFmt w:val="lowerLetter"/><w:lvlText w:val="%2)"/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="840" w:hanging="360"/></w:pPr>
    </w:lvl>
    <w:lvl w:ilvl="2">
      <w:start w:val="1"/><w:numFmt w:val="lowerRoman"/><w:lvlText w:val="%3."/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="1260" w:hanging="360"/></w:pPr>
    </w:lvl>
    <w:lvl w:ilvl="3">
      <w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%4."/><w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="1680" w:hanging="360"/></w:pPr>
    </w:lvl>
  </w:abstractNum>
{{NUM_OVERRIDES}}
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
</w:numbering>
"""

SETTINGS_XML = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="{W_NS}">
  <w:defaultTabStop w:val="420"/>
  <w:characterSpacingControl w:val="compressPunctuation"/>
  <w:compat>
    <w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>
  </w:compat>
</w:settings>
"""


# ---------------------------------------------------------------- 图片尺寸


def image_size(data: bytes) -> tuple[int, int]:
    """返回图片像素宽高（支持 PNG / JPEG / GIF / BMP），失败时给 480x320。"""
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack(">II", data[16:24])
        return int(w), int(h)
    if data[:6] in (b"GIF87a", b"GIF89a") and len(data) >= 10:
        w, h = struct.unpack("<HH", data[6:10])
        return int(w), int(h)
    if data[:2] == b"BM" and len(data) >= 26:
        w, h = struct.unpack("<ii", data[18:26])
        return abs(int(w)), abs(int(h))
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
                h, w = struct.unpack(">HH", data[i + 5 : i + 9])
                return int(w), int(h)
            seg = struct.unpack(">H", data[i + 2 : i + 4])[0]
            i += 2 + seg
    return 480, 320


# ---------------------------------------------------------------- DOCX 构造器


class DocxBuilder:
    """把 Markdown 块渲染成 word/document.xml 的 body 片段。"""

    def __init__(self, media_dir: str | None = None, preset: str | None = "standard"):
        self.p = get_preset(preset)
        # 版心宽度（EMU）：图片超过这个宽度就等比缩到版心内
        self.content_width_emu = (self.p["page_w"] - self.p["margin"][1] - self.p["margin"][3]) * 635
        self.body: list[str] = []
        self.rels: list[tuple[str, str, str, bool]] = []  # (id, type, target, external)
        self.media: list[tuple[str, bytes]] = []  # (zip 内路径, 数据)
        self.media_index = 0
        self.link_index = 0
        self.link_cache: dict[str, str] = {}
        self.num_overrides: list[str] = []
        self.next_num_id = 10
        self.media_dir = media_dir
        self.image_index = 0
        self.warnings: list[str] = []

    # ---- 关系 / 资源
    def add_link(self, url: str) -> str:
        if url in self.link_cache:
            return self.link_cache[url]
        self.link_index += 1
        rid = f"rIdL{self.link_index}"
        self.link_cache[url] = rid
        self.rels.append((rid, f"{R_NS}/hyperlink", url, True))
        return rid

    def add_image(self, src: str, alt: str = "") -> str | None:
        path = self._resolve_media(src)
        if not path or not os.path.isfile(path):
            self.warnings.append(f"图片未找到，已跳过：{src}")
            return None
        with open(path, "rb") as fh:
            data = fh.read()
        ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
        if ext in ("jpg", "jpeg"):
            ext = "jpeg"
        if ext not in ("png", "jpeg", "gif", "bmp"):
            self.warnings.append(f"不支持的图片格式，已跳过：{src}")
            return None
        self.image_index += 1
        name = f"image{self.image_index}.{ext}"
        target = f"media/{name}"
        self.media.append((f"word/{target}", data))
        rid = f"rIdImg{self.image_index}"
        self.rels.append((rid, f"{R_NS}/image", target, False))
        w, h = image_size(data)
        cx = int(w * 9525)
        cy = int(h * 9525)
        if cx > self.content_width_emu:
            cy = int(cy * self.content_width_emu / cx)
            cx = self.content_width_emu
        if cy > 9_000_000:
            cx = int(cx * 9_000_000 / cy)
            cy = 9_000_000
        return self._drawing_xml(rid, cx, cy, alt or name)

    def _resolve_media(self, src: str) -> str | None:
        if re.match(r"^[a-zA-Z]+://", src):
            self.warnings.append(f"外链图片不下载，已跳过：{src}")
            return None
        if os.path.isabs(src):
            return src
        if self.media_dir:
            return os.path.join(self.media_dir, src)
        return src

    def _drawing_xml(self, rid: str, cx: int, cy: int, name: str) -> str:
        pid = self.image_index
        return (
            "<w:r><w:drawing>"
            f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:effectExtent l="0" t="0" r="0" b="0"/>'
            f'<wp:docPr id="{pid}" name="{esc(name)}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr>'
            f'<pic:cNvPr id="{pid}" name="{esc(name)}"/>'
            "<pic:cNvPicPr/></pic:nvPicPr>"
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            "</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r>"
        )

    # ---- 行内渲染
    def runs(self, text: str, base: dict | None = None) -> str:
        out = []
        for tok, fmt in parse_inline(text, base or {}):
            if tok == "\x00IMG":
                img = self.add_image(fmt.get("image", ""), fmt.get("alt", ""))
                if img:
                    out.append(img)
                else:
                    out.append(f"<w:r><w:t xml:space=\"preserve\">[{esc(fmt.get('alt') or '图片')}]</w:t></w:r>")
                continue
            if tok == "\n":
                out.append("<w:r><w:br/></w:r>")
                continue
            rp: dict[str, str] = {}
            if fmt.get("code"):
                rp["rFonts"] = '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
                rp["color"] = '<w:color w:val="A31515"/>'
                rp["shd"] = '<w:shd w:val="clear" w:color="auto" w:fill="F2F3F5"/>'
            if fmt.get("bold"):
                rp["b"] = "<w:b/>"
                rp["bCs"] = "<w:bCs/>"
            if fmt.get("italic"):
                rp["i"] = "<w:i/>"
                rp["iCs"] = "<w:iCs/>"
            if fmt.get("strike"):
                rp["strike"] = "<w:strike/>"
            if fmt.get("link"):
                rp["color"] = f'<w:color w:val="{self.p["link_color"]}"/>'
                rp["u"] = '<w:u w:val="single"/>'
            rpr_xml = ordered_xml("rPr", rp, RPR_ORDER)
            run = f'<w:r>{rpr_xml}<w:t xml:space="preserve">{esc(tok)}</w:t></w:r>'
            if fmt.get("link"):
                run = f'<w:hyperlink r:id="{self.add_link(fmt["link"])}">{run}</w:hyperlink>'
            out.append(run)
        return "".join(out)

    # ---- 块级渲染
    def heading(self, level: int, text: str):
        style = f"Heading{min(max(level, 1), 4)}" if level > 0 else "Heading1"
        if level >= 5:
            style = "Heading4"
        self.body.append(
            f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{self.runs(text)}</w:p>'
        )

    def title(self, text: str):
        self.body.append(f'<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>{self.runs(text)}</w:p>')

    def para(self, text: str, style: str = "BodyText"):
        self.body.append(
            f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>{self.runs(text)}</w:p>'
        )

    def code(self, text: str, lang: str = ""):
        lines = text.split("\n") if text else [""]
        pieces = []
        for idx, line in enumerate(lines):
            if idx:
                pieces.append("<w:r><w:br/></w:r>")
            pieces.append(f'<w:r><w:t xml:space="preserve">{esc(line)}</w:t></w:r>')
        self.body.append(f'<w:p><w:pPr><w:pStyle w:val="CodeBlock"/></w:pPr>{"".join(pieces)}</w:p>')

    def quote(self, text: str):
        for line in text.split("\n"):
            self.body.append(
                f'<w:p><w:pPr><w:pStyle w:val="Quote"/></w:pPr>{self.runs(line)}</w:p>'
            )

    def hr(self):
        self.body.append(
            '<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" w:space="1" w:color="D0D7DE"/></w:pBdr>'
            '<w:spacing w:before="120" w:after="120"/></w:pPr></w:p>'
        )

    def lists(self, items: list[dict]):
        num_ids: dict[tuple[str, int], int] = {}
        for it in items:
            ordered = it["ordered"]
            lvl = min(it["level"], 3)
            key = ("ord" if ordered else "bul", lvl)
            if key not in num_ids:
                if ordered and lvl == 0:
                    self.next_num_id += 1
                    nid = self.next_num_id
                    self.num_overrides.append(
                        f'<w:num w:numId="{nid}"><w:abstractNumId w:val="1"/>'
                        f'<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>'
                    )
                    # 同一列表的更深层级复用该 numId
                    num_ids[key] = nid
                    num_ids[("ord", 1)] = nid
                    num_ids[("ord", 2)] = nid
                    num_ids[("ord", 3)] = nid
                else:
                    num_ids[key] = 1 if not ordered else self.next_num_id
                nid = num_ids[key]
            else:
                nid = num_ids[key]
            self.body.append(
                f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/>'
                f'<w:numPr><w:ilvl w:val="{lvl}"/><w:numId w:val="{nid}"/></w:numPr>'
                f"</w:pPr>{self.runs(it['text'])}</w:p>"
            )

    def table(self, header: list[str], rows: list[list[str]], aligns: list[str] | None = None):
        cols = max([len(header)] + [len(r) for r in rows]) if (header or rows) else 0
        if cols == 0:
            return
        total = 5000
        base = total // cols
        grid = "".join(f'<w:gridCol w:w="{int(11906 * base / 5000)}"/>' for _ in range(cols))

        def cell(text: str, is_head: bool) -> str:
            shd = (
                f'<w:shd w:val="clear" w:color="auto" w:fill="{self.p["table_head_fill"]}"/>' if is_head else ""
            )
            # 单元格内 <br> 转真实换行
            parts = re.split(r"<br\s*/?>", text, flags=re.I)
            runs = ""
            for i, p in enumerate(parts):
                if i:
                    runs += "<w:r><w:br/></w:r>"
                if p:
                    runs += self.runs(p, {"bold": True} if is_head else None)
            return (
                "<w:tc><w:tcPr>"
                f'<w:tcW w:w="{base}" w:type="pct"/>{shd}'
                '<w:vAlign w:val="center"/>'
                "</w:tcPr>"
                f'<w:p><w:pPr><w:pStyle w:val="TableText"/></w:pPr>{runs}</w:p></w:tc>'
            )

        border = (
            '<w:tblBorders>'
            '<w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            '<w:left w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            '<w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>'
            "</w:tblBorders>"
        )
        xml = [
            "<w:tbl><w:tblPr>",
            '<w:tblW w:w="5000" w:type="pct"/>',
            border,
            '<w:tblLayout w:type="autofit"/>',
            '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="100" w:type="dxa"/>'
            '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="100" w:type="dxa"/></w:tblCellMar>',
            "</w:tblPr>",
            f"<w:tblGrid>{grid}</w:tblGrid>",
        ]
        if header:
            head_cells = [cell(h, True) for h in header] + [
                cell("", True) for _ in range(cols - len(header))
            ]
            xml.append(f'<w:tr><w:trPr><w:tblHeader/></w:trPr>{"".join(head_cells)}</w:tr>')
        for row in rows:
            cells = [cell(c, False) for c in row] + [cell("", False) for _ in range(cols - len(row))]
            xml.append(f'<w:tr>{"".join(cells)}</w:tr>')
        xml.append("</w:tbl>")
        self.body.append("".join(xml))
        self.body.append('<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:after="0"/></w:pPr></w:p>')

    def toc(self):
        self.body.append(
            '<w:p><w:pPr><w:pStyle w:val="BodyText"/></w:pPr>'
            '<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
            '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-4" \\h \\z \\u </w:instrText></w:r>'
            '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
            '<w:r><w:t>（目录：在 Word 中按 F9 或右键「更新域」生成）</w:t></w:r>'
            '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>'
        )


# ---------------------------------------------------------------- 打包


def hidden_md_paragraph(payload: str) -> str:
    """把 Markdown 载荷渲染成「隐藏文字」段落（第二重保险）。

    customXml 部件会被部分编辑器（在线文档、另存为纯净 docx）丢弃，
    而隐藏文字属于正文内容，随文档一起走，能扛住这类转存。
    """
    return (
        '<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:rPr><w:vanish/></w:rPr></w:pPr>'
        '<w:r><w:rPr><w:vanish/><w:sz w:val="2"/><w:szCs w:val="2"/></w:rPr>'
        f'<w:t xml:space="preserve">{esc(payload)}</w:t></w:r></w:p>'
    )


def build_docx(
    blocks: list[dict],
    out_path: str,
    *,
    markdown_source: str | None = None,
    title: str = "",
    author: str = "icoolkj",
    toc: bool = False,
    media_dir: str | None = None,
    with_title: bool = True,
    embed_mode: str = "both",
    preset: str | None = "standard",
) -> dict:
    """把块渲染成 .docx；markdown_source 非空时同时写入隐藏层。"""
    b = DocxBuilder(media_dir=media_dir, preset=preset)

    if toc:
        b.toc()

    for blk in blocks:
        t = blk["t"]
        if t == "heading":
            b.heading(blk["level"], blk["text"])
        elif t == "para":
            b.para(blk["text"])
        elif t == "code":
            b.code(blk["text"], blk.get("lang", ""))
        elif t == "quote":
            b.quote(blk["text"])
        elif t == "hr":
            b.hr()
        elif t == "list":
            b.lists(blk["items"])
        elif t == "table":
            b.table(blk["header"], blk["rows"], blk.get("align"))

    # 先算好隐藏层载荷：customXml 与隐藏文字共用同一份数据
    packed = digest = None
    raw_bytes = b""
    write_custom = markdown_source is not None and embed_mode in ("both", "customXml")
    if markdown_source is not None:
        raw_bytes = markdown_source.encode("utf-8")
        packed = base64.b64encode(gzip.compress(raw_bytes, 9)).decode("ascii")
        digest = hashlib.sha256(raw_bytes).hexdigest()
        if embed_mode in ("both", "hidden"):
            b.body.append(hidden_md_paragraph(f"{HIDDEN_MARK}{digest}:{packed}"))

    p = b.p
    m_top, m_right, m_bottom, m_left = p["margin"]
    sect = (
        "<w:sectPr>"
        f'<w:pgSz w:w="{p["page_w"]}" w:h="{p["page_h"]}"/>'
        f'<w:pgMar w:top="{m_top}" w:right="{m_right}" w:bottom="{m_bottom}" w:left="{m_left}" '
        'w:header="851" w:footer="992" w:gutter="0"/>'
        '<w:docGrid w:type="lines" w:linePitch="312"/>'
        "</w:sectPr>"
    )

    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}" '
        'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f"<w:body>{''.join(b.body)}{sect}</w:body></w:document>"
    )

    # 关系表
    rels = [
        ("rId1", f"{R_NS}/styles", "styles.xml", False),
        ("rId2", f"{R_NS}/numbering", "numbering.xml", False),
        ("rId3", f"{R_NS}/settings", "settings.xml", False),
    ]
    if write_custom:
        rels.append(("rIdCx1", f"{R_NS}/customXml", "../customXml/item1.xml", False))
    rels.extend(b.rels)

    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG_REL_NS}">'
        + "".join(
            f'<Relationship Id="{rid}" Type="{typ}" Target="{esc(tgt)}"'
            + (' TargetMode="External"' if ext else "")
            + "/>"
            for rid, typ, tgt, ext in rels
        )
        + "</Relationships>"
    )

    has_image = any(p.endswith((".png", ".jpeg", ".gif", ".bmp")) for p, _ in b.media)
    defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
    ]
    if has_image:
        defaults.append('<Default Extension="png" ContentType="image/png"/>')
        defaults.append('<Default Extension="jpeg" ContentType="image/jpeg"/>')
        defaults.append('<Default Extension="gif" ContentType="image/gif"/>')
        defaults.append('<Default Extension="bmp" ContentType="image/bmp"/>')

    overrides = [
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>',
        '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>',
        '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>',
        '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    if write_custom:
        overrides.append(
            f'<Override PartName="/{MD_PROPS_PART}" ContentType="application/vnd.openxmlformats-officedocument.customXmlProperties+xml"/>'
        )

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Types xmlns="{CT_NS}">' + "".join(defaults + overrides) + "</Types>"
    )

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<Relationships xmlns="{PKG_REL_NS}">'
        f'<Relationship Id="rId1" Type="{R_NS}/officeDocument" Target="word/document.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        f'<Relationship Id="rId3" Type="{R_NS}/extended-properties" Target="docProps/app.xml"/>'
        "</Relationships>"
    )

    core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        f"<dc:title>{esc(title)}</dc:title>"
        f"<dc:creator>{esc(author)}</dc:creator>"
        f"<cp:lastModifiedBy>{esc(author)}</cp:lastModifiedBy>"
        f'<dcterms:created xsi:type="dcterms:W3CDTF">{now_iso()}</dcterms:created>'
        f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now_iso()}</dcterms:modified>'
        "</cp:coreProperties>"
    )

    app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
        'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
        "<Application>icoolkj md-word-dual</Application>"
        "<DocSecurity>0</DocSecurity>"
        "</Properties>"
    )

    numbering = NUMBERING_XML.replace("{NUM_OVERRIDES}", "".join(b.num_overrides))

    parts: list[tuple[str, str]] = [
        ("[Content_Types].xml", content_types),
        ("_rels/.rels", root_rels),
        ("word/document.xml", doc),
        ("word/styles.xml", styles_xml(preset)),
        ("word/numbering.xml", numbering),
        ("word/settings.xml", SETTINGS_XML),
        ("word/_rels/document.xml.rels", rels_xml),
        ("docProps/core.xml", core),
        ("docProps/app.xml", app),
    ]
    binary: list[tuple[str, bytes]] = list(b.media)

    payload_info = {}
    if markdown_source is not None:
        payload_info = {"md_bytes": len(raw_bytes), "md_sha256": digest, "packed_bytes": len(packed or "")}
    if write_custom:
        parts.append(
            (
                MD_PART,
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<md:source xmlns:md="{MD_NS}" version="1.0" encoding="gzip+base64" '
                f'sha256="{digest}" bytes="{len(raw_bytes)}" created="{now_iso()}">'
                f"{packed}</md:source>",
            )
        )
        parts.append(
            (
                MD_PROPS_PART,
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<ds:datastoreItem ds:itemID="{{6B1F4C11-3D6A-4C1E-9A57-2E8E4B7D1A02}}" xmlns:ds="{CUSTOM_XML_NS}">'
                f'<ds:schemaRefs><ds:schemaRef ds:uri="{MD_NS}"/></ds:schemaRefs>'
                "</ds:datastoreItem>",
            )
        )
        parts.append(
            (
                "customXml/_rels/item1.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<Relationships xmlns="{PKG_REL_NS}">'
                f'<Relationship Id="rId1" Type="{R_NS}/customXmlProps" Target="itemProps1.xml"/>'
                "</Relationships>",
            )
        )

    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, text in parts:
            zf.writestr(name, text.encode("utf-8"))
        for name, data in binary:
            zf.writestr(name, data)

    return {
        "path": os.path.abspath(out_path),
        "size": os.path.getsize(out_path),
        "warnings": b.warnings,
        **payload_info,
    }


def markdown_to_docx(
    md_path: str,
    out_path: str | None = None,
    *,
    embed_source: bool = True,
    embed_mode: str = "both",
    toc: bool = False,
    title: str | None = None,
    preset: str | None = "standard",
) -> dict:
    with open(md_path, "r", encoding="utf-8-sig") as fh:
        src = fh.read()
    blocks = parse_markdown(src)
    first_head = next((x["text"] for x in blocks if x["t"] == "heading" and x["level"] == 1), None)
    doc_title = title or first_head or os.path.splitext(os.path.basename(md_path))[0]
    if out_path is None:
        out_path = os.path.splitext(md_path)[0] + ".docx"
    res = build_docx(
        blocks,
        out_path,
        markdown_source=src if embed_source else None,
        embed_mode=embed_mode,
        title=doc_title,
        toc=toc,
        media_dir=os.path.dirname(os.path.abspath(md_path)),
        preset=preset,
    )
    res["title"] = doc_title
    res["preset"] = get_preset(preset)["label"]
    res["blocks"] = len(blocks)
    res["embedded"] = embed_source
    return res


# ---------------------------------------------------------------- 隐藏层读取


def _decode_payload(b64: str, expect_sha: str | None) -> str | None:
    try:
        data = base64.b64decode("".join(b64.split()))
        data = gzip.decompress(data)
        text = data.decode("utf-8")
    except Exception:
        return None
    if expect_sha and hashlib.sha256(data).hexdigest() != expect_sha:
        return None
    return text


def _from_custom_xml(raw: str) -> str | None:
    if MD_NS not in raw:
        return None
    m = re.search(r"<(?:\w+:)?source\b([^>]*)>(.*?)</(?:\w+:)?source>", raw, re.S)
    if not m:
        return None
    attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(1)))
    return _decode_payload(m.group(2), attrs.get("sha256"))


def _from_hidden_text(xml: str) -> str | None:
    m = re.search(re.escape(HIDDEN_MARK) + r"([0-9a-f]{64}):([A-Za-z0-9+/=]+)", xml)
    if not m:
        return None
    return _decode_payload(m.group(2), m.group(1))


def embedded_layers(docx_path: str) -> dict:
    """报告两层各自是否存在且可解。"""
    layers = {"customxml": False, "hidden_text": False}
    with zipfile.ZipFile(docx_path) as zf:
        names = zf.namelist()
        if MD_PART in names:
            try:
                layers["customxml"] = _from_custom_xml(zf.read(MD_PART).decode("utf-8", "replace")) is not None
            except Exception:
                layers["customxml"] = False
        if "word/document.xml" in names:
            try:
                layers["hidden_text"] = _from_hidden_text(zf.read("word/document.xml").decode("utf-8", "replace")) is not None
            except Exception:
                layers["hidden_text"] = False
    return layers


def read_embedded_markdown(docx_path: str) -> str | None:
    """取出隐藏层里的原始 Markdown；customXml 优先，其次隐藏文字；都没有则 None。"""
    with zipfile.ZipFile(docx_path) as zf:
        names = zf.namelist()
        candidate = MD_PART if MD_PART in names else next(
            (n for n in names if n.startswith("customXml/") and n.endswith(".xml") and "Props" not in n),
            None,
        )
        if candidate:
            text = _from_custom_xml(zf.read(candidate).decode("utf-8", "replace"))
            if text is not None:
                return text
        if "word/document.xml" in names:
            return _from_hidden_text(zf.read("word/document.xml").decode("utf-8", "replace"))
    return None


# ---------------------------------------------------------------- DOCX → Markdown


def _q(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


class _Docx:
    """极简 docx 读取器：样式表、编号表、关系、正文。"""

    def __init__(self, path: str):
        import xml.etree.ElementTree as ET

        self.zf = zipfile.ZipFile(path)
        self.root = ET.fromstring(self.zf.read("word/document.xml"))
        self.rels = {}
        if "word/_rels/document.xml.rels" in self.zf.namelist():
            r = ET.fromstring(self.zf.read("word/_rels/document.xml.rels"))
            for rel in r:
                self.rels[rel.get("Id")] = (rel.get("Target", ""), rel.get("TargetMode", "") == "External")
        self.style_names = {}
        # 样式继承的编号 / 底色：python-docx 这类工具会把列表编号和代码底纹写进样式定义，
        # 段落上反而没有 numPr，只看段落会漏掉整份列表和代码块
        self.style_num: dict[str, tuple[str | None, int]] = {}
        self.style_based: dict[str, str] = {}
        self.style_shaded: set[str] = set()
        if "word/styles.xml" in self.zf.namelist():
            s = ET.fromstring(self.zf.read("word/styles.xml"))
            for st in s.findall(_q("style")):
                sid = st.get(_q("styleId"))
                nm = st.find(_q("name"))
                self.style_names[sid] = nm.get(_q("val")) if nm is not None else sid
                based = st.find(_q("basedOn"))
                if based is not None and based.get(_q("val")):
                    self.style_based[sid] = based.get(_q("val"))
                ppr_s = st.find(_q("pPr"))
                if ppr_s is None:
                    continue
                npr_s = ppr_s.find(_q("numPr"))
                if npr_s is not None:
                    n_s = npr_s.find(_q("numId"))
                    l_s = npr_s.find(_q("ilvl"))
                    self.style_num[sid] = (
                        n_s.get(_q("val")) if n_s is not None else None,
                        int(l_s.get(_q("val")) or 0) if l_s is not None else 0,
                    )
                shd_s = ppr_s.find(_q("shd"))
                if shd_s is not None and (shd_s.get(_q("fill")) or "auto").upper() not in ("AUTO", "FFFFFF"):
                    self.style_shaded.add(sid)
        self.num_fmt = {}
        if "word/numbering.xml" in self.zf.namelist():
            nb = ET.fromstring(self.zf.read("word/numbering.xml"))
            abs_map = {}
            for an in nb.findall(_q("abstractNum")):
                aid = an.get(_q("abstractNumId"))
                lv = {}
                for lvl in an.findall(_q("lvl")):
                    il = int(lvl.get(_q("ilvl")) or 0)
                    fmt = lvl.find(_q("numFmt"))
                    lv[il] = fmt.get(_q("val")) if fmt is not None else "bullet"
                abs_map[aid] = lv
            for num in nb.findall(_q("num")):
                nid = num.get(_q("numId"))
                ref = num.find(_q("abstractNumId"))
                if ref is not None:
                    self.num_fmt[nid] = abs_map.get(ref.get(_q("val")), {})
        self._img_seq = 0

    def close(self):
        self.zf.close()

    def style_numpr(self, sid: str | None) -> tuple[str | None, int] | None:
        """沿 basedOn 链找样式定义里的编号。"""
        seen: set[str] = set()
        cur = sid
        while cur and cur not in seen:
            seen.add(cur)
            if cur in self.style_num:
                return self.style_num[cur]
            cur = self.style_based.get(cur)
        return None

    def style_level(self, sid: str | None) -> int | None:
        if not sid:
            return None
        name = (self.style_names.get(sid) or sid).lower().replace("_", " ")
        if name.startswith("heading"):
            digits = re.findall(r"\d+", name)
            return int(digits[0]) if digits else 1
        if name in ("title", "标题"):
            return 0
        m = re.match(r"^标题\s*(\d)$", name)
        if m:
            return int(m.group(1))
        return None

    def run_text(self, r) -> str:
        out = []
        for node in r.iter():
            tag = node.tag.split("}")[-1]
            if tag == "t" and node.text:
                out.append(node.text)
            elif tag == "tab":
                out.append("\t")
            elif tag in ("br", "cr"):
                out.append("\n")
        return "".join(out)

    def run_fmt(self, r) -> dict:
        fmt = {}
        rpr = r.find(_q("rPr"))
        if rpr is None:
            return fmt
        if rpr.find(_q("b")) is not None:
            fmt["bold"] = True
        if rpr.find(_q("i")) is not None:
            fmt["italic"] = True
        if rpr.find(_q("strike")) is not None:
            fmt["strike"] = True
        fonts = rpr.find(_q("rFonts"))
        if fonts is not None:
            asc = (fonts.get(_q("ascii")) or "").lower()
            if asc in ("consolas", "courier new", "couriernew", "monaco", "menlo"):
                fmt["code"] = True
        return fmt

    def para_md(self, p, list_state: dict) -> tuple[str, str]:
        """返回 (kind, markdown 文本)。kind ∈ heading/para/code/quote/list/empty"""
        ppr = p.find(_q("pPr"))
        style = None
        num_id = ilvl = None
        if ppr is not None:
            ps = ppr.find(_q("pStyle"))
            if ps is not None:
                style = ps.get(_q("val"))
            npr = ppr.find(_q("numPr"))
            if npr is not None:
                n = npr.find(_q("numId"))
                l = npr.find(_q("ilvl"))
                num_id = n.get(_q("val")) if n is not None else None
                ilvl = int(l.get(_q("val")) or 0) if l is not None else 0

        # 段落上没写编号时，去样式定义里找（python-docx 的 List Bullet / List Number 就是这种）
        if (num_id is None or num_id == "0") and style:
            sn = self.style_numpr(style)
            if sn and sn[0] not in (None, "0"):
                num_id, ilvl = sn

        # 段落级底色 = 代码块，左侧竖线 = 引用块：有的工具不建样式，直接给段落上格式
        para_shaded = bool(style and style in self.style_shaded)
        para_left_bar = False
        if ppr is not None:
            shd_p = ppr.find(_q("shd"))
            if shd_p is not None and (shd_p.get(_q("fill")) or "auto").upper() not in ("AUTO", "FFFFFF"):
                para_shaded = True
            pbdr_p = ppr.find(_q("pBdr"))
            if pbdr_p is not None and pbdr_p.find(_q("left")) is not None:
                para_left_bar = True

        # 收集图文
        chunks = []
        for child in p:
            tag = child.tag.split("}")[-1]
            if tag == "r":
                txt = self.run_text(child)
                if txt:
                    fmt = self.run_fmt(child)
                    chunks.append((txt, fmt))
                for dr in child.iter(f"{{{W_NS}}}drawing"):
                    chunks.append((self._drawing_to_md(dr), {}))
            elif tag == "hyperlink":
                rid = child.get(f"{{{R_NS}}}id")
                inner = "".join(self.run_text(r) for r in child.findall(_q("r")))
                target = self.rels.get(rid, ("", False))[0]
                if inner:
                    chunks.append((f"[{inner}]({target})" if target else inner, {}))

        text = ""
        for txt, fmt in chunks:
            piece = txt
            if fmt.get("code") and txt.strip():
                piece = f"`{txt}`"
            if fmt.get("bold") and txt.strip():
                piece = f"**{txt}**" if not fmt.get("code") else piece
            if fmt.get("italic") and txt.strip():
                piece = f"*{txt}*"
            if fmt.get("strike") and txt.strip():
                piece = f"~~{txt}~~"
            text += piece

        style_name = (self.style_names.get(style) or style or "").lower()
        level = self.style_level(style)
        # 底色 + 全等宽才算代码：引用块同样有底纹，只看底纹会把引用误判成代码
        runs_text = [(t, f) for t, f in chunks if t.strip()]
        all_mono = bool(runs_text) and all(f.get("code") for _t, f in runs_text)

        if level is not None:
            # 标题本身通常是加粗的，反解时要把行内标记剥掉，否则会出现 "# **标题**"
            clean = re.sub(r"\*\*|~~|`", "", text).strip().strip("*").strip()
            if level == 0:
                return "heading", "# " + clean
            return "heading", f"{'#' * min(max(level, 1), 6)} {clean}"

        if style_name in ("code block", "codeblock", "code") or (para_shaded and all_mono):
            # 代码行里不再叠加行内标记：等宽字体本身会被判成 `code`，套上反引号反而污染代码
            return "code", "".join(t for t, _f in chunks).rstrip("\n")

        if style_name in ("quote", "block quote", "intense quote") or para_left_bar:
            return "quote", text

        if num_id is not None:
            fmts = self.num_fmt.get(num_id, {})
            kind = fmts.get(ilvl)
            if kind is None:
                kind = "decimal" if "number" in style_name else "bullet"
            indent = "  " * ilvl
            if kind == "bullet":
                return "list", f"{indent}- {text.strip()}"
            key = (num_id, ilvl)
            list_state[key] = list_state.get(key, 0) + 1
            for (nid, il) in list(list_state.keys()):
                if nid == num_id and il > ilvl:
                    list_state.pop((nid, il), None)
            return "list", f"{indent}{list_state[key]}. {text.strip()}"

        if not text.strip():
            return "empty", ""
        return "para", text.strip()

    def _drawing_to_md(self, drawing) -> str:
        rid = None
        for blip in drawing.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
            rid = blip.get(f"{{{R_NS}}}embed")
            break
        if not rid:
            return ""
        target = self.rels.get(rid, ("", False))[0]
        return f"![](media/{os.path.basename(target)})" if target else ""

    def table_md(self, tbl) -> str:
        rows = []
        for tr in tbl.findall(_q("tr")):
            cells = []
            for tc in tr.findall(_q("tc")):
                parts = []
                for p in tc.findall(_q("p")):
                    _, t = self.para_md(p, {})
                    if t:
                        parts.append(t.strip())
                cells.append("<br>".join(parts).replace("|", "\\|") or " ")
            rows.append(cells)
        if not rows:
            return ""
        cols = max(len(r) for r in rows)
        rows = [r + [" "] * (cols - len(r)) for r in rows]
        head = [re.sub(r"\*\*(.+?)\*\*", r"\1", c) for c in rows[0]]
        out = ["| " + " | ".join(head) + " |", "|" + "|".join([" --- "] * cols) + "|"]
        for r in rows[1:]:
            out.append("| " + " | ".join(r) + " |")
        return "\n".join(out)


def docx_to_markdown(docx_path: str, *, prefer_embedded: bool = True) -> tuple[str, str]:
    """返回 (markdown, 来源说明)。来源 ∈ embedded / structure"""
    if prefer_embedded:
        emb = read_embedded_markdown(docx_path)
        if emb is not None:
            return emb, "embedded"

    d = _Docx(docx_path)
    try:
        body = d.root.find(_q("body"))
        if body is None:
            return "", "structure"
        state: dict = {}
        items: list[tuple[str, str]] = []
        for child in body:
            tag = child.tag.split("}")[-1]
            if tag == "p":
                kind, text = d.para_md(child, state)
                if kind == "empty" or not text.strip():
                    continue
                if kind == "code":
                    items.append(("code", text.rstrip("\n")))
                elif kind == "quote":
                    items.append(("quote", "\n".join("> " + ln for ln in text.split("\n"))))
                else:
                    items.append((kind, text))
            elif tag == "tbl":
                t = d.table_md(child)
                if t:
                    items.append(("table", t))

        # 相邻代码段落合成一个围栏块：有的工具把每行代码写成独立段落
        merged: list[tuple[str, str]] = []
        for kind, text in items:
            if kind == "code" and merged and merged[-1][0] == "code":
                merged[-1] = ("code", merged[-1][1] + "\n" + text)
            else:
                merged.append((kind, text))
        items = [("code", f"```\n{t}\n```") if k == "code" else (k, t) for k, t in merged]

        chunks: list[str] = []
        for i, (kind, text) in enumerate(items):
            if i:
                prev_kind, prev_text = items[i - 1]
                same_list = kind == "list" and prev_kind == "list" and _list_marker_kind(text) == _list_marker_kind(prev_text)
                chunks.append("\n" if (same_list or (kind == "quote" and prev_kind == "quote")) else "\n\n")
            chunks.append(text)
        md = "".join(chunks)
        return md.rstrip() + "\n", "structure"
    finally:
        d.close()


def _list_marker_kind(line: str) -> str:
    """判断列表行的标记类型：bullet / ordered，用于判断是否紧凑拼接。"""
    s = line.lstrip()
    return "ordered" if re.match(r"^\d+[.)]", s) else "bullet"


def _merge(parts: list[str]) -> list[str]:
    """合并相邻列表项之间的空行，保持 Markdown 列表紧凑。"""
    out: list[str] = []
    for p in parts:
        if not p.strip():
            continue
        out.append(p)
    return out


# ---------------------------------------------------------------- 校验


def inspect_docx(path: str) -> dict:
    """检查文件形态：是否含隐藏层、能否解出、包结构是否完整。"""
    info = {"path": os.path.abspath(path), "size": os.path.getsize(path)}
    try:
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            info["parts"] = len(names)
            info["has_document"] = "word/document.xml" in names
            info["has_embedded"] = MD_PART in names
            bad = zf.testzip()
            info["zip_ok"] = bad is None
    except zipfile.BadZipFile:
        return {**info, "ok": False, "error": "不是合法的 zip / docx"}
    emb = read_embedded_markdown(path)
    info["embedded_readable"] = emb is not None
    try:
        info["layers"] = embedded_layers(path)
    except Exception:
        info["layers"] = {"customxml": False, "hidden_text": False}
    if emb is not None:
        info["embedded_chars"] = len(emb)
        info["embedded_bytes"] = len(emb.encode("utf-8"))
    info["ok"] = bool(info.get("has_document") and info.get("zip_ok"))
    return info


def validate_docx(path: str) -> dict:
    """严格自检：XML 合法性 + OOXML 元素顺序 + 关系/样式/编号引用完整性。

    Word 对属性子元素顺序敏感，顺序错会触发「文件已损坏，需要修复」，
    因此生成后必须过这一关。
    """
    import xml.etree.ElementTree as ET

    problems: list[str] = []
    info = inspect_docx(path)
    if not info.get("ok"):
        return {"ok": False, "problems": [info.get("error", "包结构异常")]}

    with zipfile.ZipFile(path) as zf:
        names = set(zf.namelist())
        trees = {}
        for name in names:
            if name.endswith((".xml", ".rels")):
                try:
                    trees[name] = ET.fromstring(zf.read(name))
                except ET.ParseError as exc:
                    problems.append(f"{name} XML 不合法：{exc}")

        doc = trees["word/document.xml"]
        rels = {}
        if "word/_rels/document.xml.rels" in names:
            for rel in ET.fromstring(zf.read("word/_rels/document.xml.rels")):
                rels[rel.get("Id")] = rel.get("Target")

        style_ids, num_ids, abs_ids = set(), set(), set()
        if "word/styles.xml" in names:
            for st in ET.fromstring(zf.read("word/styles.xml")).findall(_q("style")):
                style_ids.add(st.get(_q("styleId")))
        if "word/numbering.xml" in names:
            nb = ET.fromstring(zf.read("word/numbering.xml"))
            for an in nb.findall(_q("abstractNum")):
                abs_ids.add(an.get(_q("abstractNumId")))
            for num in nb.findall(_q("num")):
                num_ids.add(num.get(_q("numId")))
                ref = num.find(_q("abstractNumId"))
                if ref is not None and ref.get(_q("val")) not in abs_ids:
                    problems.append(f"num {num.get(_q('numId'))} 指向不存在的 abstractNum")

        # 元素顺序（正文 + 样式表 + 编号表都检查）
        for tree_name, tree in trees.items():
            if not tree_name.endswith(".xml"):
                continue
            for parent, order, label in (
                ("pPr", PPR_ORDER, "pPr"),
                ("rPr", RPR_ORDER, "rPr"),
                ("tcPr", TCPR_ORDER, "tcPr"),
                ("tblPr", TBLPR_ORDER, "tblPr"),
                ("trPr", TRPR_ORDER, "trPr"),
            ):
                for el in tree.iter(_q(parent)):
                    seen = [c.tag.split("}")[-1] for c in el]
                    idx = [order.index(t) for t in seen if t in order]
                    if idx != sorted(idx):
                        problems.append(f"{tree_name} 中 {label} 子元素顺序不合规：{seen}")
                        break

        # 引用完整性
        for el in doc.iter():
            rid = el.get(f"{{{R_NS}}}id")
            if rid and rid not in rels:
                problems.append(f"引用了不存在的关系 {rid}")
            if el.tag == _q("pStyle"):
                sid = el.get(_q("val"))
                if style_ids and sid not in style_ids:
                    problems.append(f"引用了不存在的样式 {sid}")
            if el.tag == _q("numId"):
                nid = el.get(_q("val"))
                if num_ids and nid not in num_ids:
                    problems.append(f"引用了不存在的编号 {nid}")

        body = doc.find(_q("body"))
        if body is None or len(list(body)) == 0:
            problems.append("document.xml 缺少 body")
        elif body[-1].tag != _q("sectPr"):
            problems.append("body 末尾缺少 sectPr")

        # 内容类型覆盖
        if "[Content_Types].xml" in names:
            ct = ET.fromstring(zf.read("[Content_Types].xml"))
            defaults = {d.get("Extension", "").lower() for d in ct.findall(f"{{{CT_NS}}}Default")}
            overrides = {o.get("PartName", "").lstrip("/") for o in ct.findall(f"{{{CT_NS}}}Override")}
            for name in names:
                if name == "[Content_Types].xml":
                    continue
                base = os.path.basename(name)
                ext = base.split(".")[-1].lower() if "." in base else ""
                if name not in overrides and ext not in defaults:
                    problems.append(f"部件缺少内容类型声明：{name}")

    return {"ok": not problems, "problems": problems[:20], "checked_parts": len(names)}


TCPR_ORDER = [
    "cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap",
    "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark",
]
TBLPR_ORDER = [
    "tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize",
    "tblStyleColBandSize", "tblW", "jc", "tblCellSpacing", "tblInd", "tblBorders", "shd",
    "tblLayout", "tblCellMar", "tblLook", "tblCaption", "tblDescription",
]
TRPR_ORDER = [
    "cnfStyle", "divId", "gridBefore", "gridAfter", "wBefore", "wAfter", "cantSplit",
    "trHeight", "tblHeader", "tblCellSpacing", "jc", "hidden",
]


if __name__ == "__main__":
    print(__doc__)
