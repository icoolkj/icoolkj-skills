#!/usr/bin/env python3
"""
MD-Doc-Bridge: Markdown ↔ Word 双层文档转换引擎
支持 md2docx / docx2md / dual / extract 四种模式。

用法:
    python convert.py md2docx <md文件> [--output <docx文件>] [--style <风格>]
    python convert.py docx2md <docx文件> [--output <md文件>]
    python convert.py dual <md文件> [--output <docx文件>] [--style <风格>]
    python convert.py extract <docx文件> [--output <md文件>]
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    from docx import Document
    from docx.shared import Pt, Inches, Cm, RGBColor, Emu
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except ImportError:
    print("错误: 需要 python-docx 库。请运行: pip install python-docx", file=sys.stderr)
    sys.exit(1)

try:
    import markdown as md_lib
except ImportError:
    print("错误: 需要 markdown 库。请运行: pip install markdown", file=sys.stderr)
    sys.exit(1)

VERSION = "1.0.0"

# ============================================================
# 排版风格定义
# ============================================================
STYLES = {
    "standard": {
        "body_font": "宋体",
        "heading_font": "黑体",
        "body_size": Pt(12),
        "h1_size": Pt(22),
        "h2_size": Pt(18),
        "h3_size": Pt(16),
        "h4_size": Pt(14),
        "h5_size": Pt(12),
        "h6_size": Pt(11),
        "line_spacing": 1.5,
        "code_font": "Consolas",
        "code_size": Pt(10),
        "code_bg": "F0F0F0",
        "quote_font": "仿宋",
        "table_header_bg": "E0E0E0",
        "link_color": RGBColor(0x00, 0x00, 0xFF),
        "page_width": Cm(21),
        "page_height": Cm(29.7),
        "margin_top": Cm(2.54),
        "margin_bottom": Cm(2.54),
        "margin_left": Cm(3.18),
        "margin_right": Cm(3.18),
    },
    "clean": {
        "body_font": "Microsoft YaHei",
        "heading_font": "Microsoft YaHei",
        "body_size": Pt(11),
        "h1_size": Pt(20),
        "h2_size": Pt(16),
        "h3_size": Pt(14),
        "h4_size": Pt(12),
        "h5_size": Pt(11),
        "h6_size": Pt(10),
        "line_spacing": 1.6,
        "code_font": "Consolas",
        "code_size": Pt(10),
        "code_bg": "F5F5F5",
        "quote_font": "Microsoft YaHei",
        "table_header_bg": "E8F0FE",
        "link_color": RGBColor(0x1A, 0x73, 0xE8),
        "page_width": Cm(21),
        "page_height": Cm(29.7),
        "margin_top": Cm(2),
        "margin_bottom": Cm(2),
        "margin_left": Cm(2.5),
        "margin_right": Cm(2.5),
    },
    "formal": {
        "body_font": "仿宋",
        "heading_font": "黑体",
        "body_size": Pt(12),
        "h1_size": Pt(22),
        "h2_size": Pt(18),
        "h3_size": Pt(16),
        "h4_size": Pt(14),
        "h5_size": Pt(12),
        "h6_size": Pt(11),
        "line_spacing": 1.5,
        "code_font": "Courier New",
        "code_size": Pt(10),
        "code_bg": "F0F0F0",
        "quote_font": "楷体",
        "table_header_bg": "E0E0E0",
        "link_color": RGBColor(0x00, 0x00, 0x00),
        "page_width": Cm(21),
        "page_height": Cm(29.7),
        "margin_top": Cm(2.54),
        "margin_bottom": Cm(2.54),
        "margin_left": Cm(3.18),
        "margin_right": Cm(3.18),
    },
    "blog": {
        "body_font": "Microsoft YaHei",
        "heading_font": "Microsoft YaHei",
        "body_size": Pt(12),
        "h1_size": Pt(24),
        "h2_size": Pt(20),
        "h3_size": Pt(16),
        "h4_size": Pt(14),
        "h5_size": Pt(12),
        "h6_size": Pt(11),
        "line_spacing": 1.8,
        "code_font": "Consolas",
        "code_size": Pt(11),
        "code_bg": "282C34",
        "quote_font": "Microsoft YaHei",
        "table_header_bg": "E8F0FE",
        "link_color": RGBColor(0x00, 0x66, 0xCC),
        "page_width": Cm(21),
        "page_height": Cm(29.7),
        "margin_top": Cm(1.5),
        "margin_bottom": Cm(1.5),
        "margin_left": Cm(2),
        "margin_right": Cm(2),
    },
}


# ============================================================
# Markdown 解析器
# ============================================================
class MarkdownParser:
    """解析 Markdown 为结构化元素列表"""

    def __init__(self, content):
        self.lines = content.split("\n")
        self.pos = 0
        self.elements = []

    def parse(self):
        while self.pos < len(self.lines):
            line = self.lines[self.pos]

            if line.strip() == "":
                self.pos += 1
                continue

            if line.startswith("```"):
                self._parse_code_block()
            elif re.match(r"^#{1,6}\s", line):
                self._parse_heading()
            elif re.match(r"^\s*[-*+]\s", line):
                self._parse_unordered_list()
            elif re.match(r"^\s*\d+\.\s", line):
                self._parse_ordered_list()
            elif line.startswith(">"):
                self._parse_quote()
            elif line.startswith("|") and self.pos + 1 < len(self.lines) and "---" in self.lines[self.pos + 1]:
                self._parse_table()
            elif line.strip() == "---" or line.strip() == "***":
                self.elements.append({"type": "hr"})
                self.pos += 1
            elif re.match(r"^!\[.*\]\(.*\)", line.strip()):
                self._parse_image()
            else:
                self._parse_paragraph()

        return self.elements

    def _parse_heading(self):
        line = self.lines[self.pos]
        match = re.match(r"^(#{1,6})\s+(.*)", line)
        if match:
            level = len(match.group(1))
            text = match.group(2).strip()
            self.elements.append({"type": "heading", "level": level, "text": text})
        self.pos += 1

    def _parse_code_block(self):
        line = self.lines[self.pos]
        lang_match = re.match(r"^```(\w*)", line)
        lang = lang_match.group(1) if lang_match else ""
        self.pos += 1
        code_lines = []
        while self.pos < len(self.lines) and not self.lines[self.pos].startswith("```"):
            code_lines.append(self.lines[self.pos])
            self.pos += 1
        self.pos += 1  # skip closing ```
        self.elements.append({"type": "code_block", "lang": lang, "content": "\n".join(code_lines)})

    def _parse_unordered_list(self):
        items = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            match = re.match(r"^(\s*)[-*+]\s+(.*)", line)
            if match:
                indent = len(match.group(1))
                text = match.group(2).strip()
                items.append({"indent": indent, "text": text})
                self.pos += 1
            elif line.strip() == "":
                self.pos += 1
                break
            else:
                break
        self.elements.append({"type": "unordered_list", "items": items})

    def _parse_ordered_list(self):
        items = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            match = re.match(r"^(\s*)(\d+)\.\s+(.*)", line)
            if match:
                indent = len(match.group(1))
                num = int(match.group(2))
                text = match.group(3).strip()
                items.append({"indent": indent, "num": num, "text": text})
                self.pos += 1
            elif line.strip() == "":
                self.pos += 1
                break
            else:
                break
        self.elements.append({"type": "ordered_list", "items": items})

    def _parse_quote(self):
        lines = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            if line.startswith(">"):
                lines.append(line[1:].strip())
                self.pos += 1
            else:
                break
        self.elements.append({"type": "quote", "content": "\n".join(lines)})

    def _parse_table(self):
        header_line = self.lines[self.pos]
        sep_line = self.lines[self.pos + 1]
        self.pos += 2

        headers = [h.strip() for h in header_line.split("|")[1:-1]]
        aligns = []
        for s in sep_line.split("|")[1:-1]:
            s = s.strip()
            if s.startswith(":") and s.endswith(":"):
                aligns.append("center")
            elif s.startswith(":"):
                aligns.append("left")
            elif s.endswith(":"):
                aligns.append("right")
            else:
                aligns.append("left")

        rows = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            if line.startswith("|") and line.strip():
                cells = [c.strip() for c in line.split("|")[1:-1]]
                rows.append(cells)
                self.pos += 1
            else:
                break

        self.elements.append({"type": "table", "headers": headers, "aligns": aligns, "rows": rows})

    def _parse_image(self):
        line = self.lines[self.pos].strip()
        match = re.match(r"^!\[(.*?)\]\((.*?)\)", line)
        if match:
            alt = match.group(1)
            src = match.group(2)
            self.elements.append({"type": "image", "alt": alt, "src": src})
        self.pos += 1

    def _parse_paragraph(self):
        lines = []
        while self.pos < len(self.lines):
            line = self.lines[self.pos]
            if (line.strip() == "" or line.startswith("#") or line.startswith("```") or
                line.startswith(">") or line.startswith("|") or re.match(r"^\s*[-*+]\s", line) or
                re.match(r"^\s*\d+\.\s", line) or line.strip() in ("---", "***")):
                break
            lines.append(line)
            self.pos += 1
        if lines:
            self.elements.append({"type": "paragraph", "content": "\n".join(lines)})


# ============================================================
# 行内格式解析
# ============================================================
def parse_inline(text):
    """解析行内格式（粗体、斜体、代码、链接、删除线），返回 (text, formats) 列表"""
    formats = []

    # 行内代码 `code`
    text = re.sub(r"`([^`]+)`", lambda m: formats.append(("code", m.group(1))) or "", text)

    # 粗体 **text** 或 __text__
    # 斜体 *text* 或 _text_
    # 粗斜体 ***text***
    # 删除线 ~~text~~

    # 链接 [text](url)
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    # 图片 ![alt](src) — 已在外层处理

    # 简化处理：返回原始文本和格式标记列表
    result = []
    remaining = text

    while remaining:
        # 找到最早的格式标记
        matches = []
        for pattern, fmt_type in [
            (r"`([^`]+)`", "code"),
            (r"\*\*\*([^*]+)\*\*\*", "bold_italic"),
            (r"\*\*([^*]+)\*\*", "bold"),
            (r"\*([^*]+)\*", "italic"),
            (r"~~([^~]+)~~", "strikethrough"),
            (r"\[([^\]]+)\]\(([^)]+)\)", "link"),
        ]:
            m = re.search(pattern, remaining)
            if m:
                matches.append((m.start(), m.end(), fmt_type, m))

        if not matches:
            result.append(("text", remaining))
            break

        matches.sort(key=lambda x: x[0])
        start, end, fmt_type, m = matches[0]

        if start > 0:
            result.append(("text", remaining[:start]))

        if fmt_type == "code":
            result.append(("code", m.group(1)))
        elif fmt_type == "bold_italic":
            result.append(("bold_italic", m.group(1)))
        elif fmt_type == "bold":
            result.append(("bold", m.group(1)))
        elif fmt_type == "italic":
            result.append(("italic", m.group(1)))
        elif fmt_type == "strikethrough":
            result.append(("strikethrough", m.group(1)))
        elif fmt_type == "link":
            result.append(("link", m.group(1), m.group(2)))

        remaining = remaining[end:]

    return result


# ============================================================
# Word 文档构建器
# ============================================================
class DocxBuilder:
    """从结构化元素构建 Word 文档"""

    def __init__(self, style_name="standard"):
        self.style_name = style_name
        self.style = STYLES.get(style_name, STYLES["standard"])
        self.doc = Document()
        self.stats = {"paragraphs": 0, "headings": 0, "tables": 0, "code_blocks": 0, "lists": 0, "quotes": 0, "images": 0}
        self._setup_page()
        self._setup_styles()

    def _setup_page(self):
        section = self.doc.sections[0]
        section.page_width = self.style["page_width"]
        section.page_height = self.style["page_height"]
        section.top_margin = self.style["margin_top"]
        section.bottom_margin = self.style["margin_bottom"]
        section.left_margin = self.style["margin_left"]
        section.right_margin = self.style["margin_right"]

    def _setup_styles(self):
        style_normal = self.doc.styles["Normal"]
        style_normal.font.name = self.style["body_font"]
        style_normal.font.size = self.style["body_size"]
        style_normal.paragraph_format.line_spacing = self.style["line_spacing"]

        for i in range(1, 7):
            style_name = f"Heading {i}"
            if style_name in self.doc.styles:
                style = self.doc.styles[style_name]
                style.font.name = self.style["heading_font"]
                size_key = f"h{i}_size"
                style.font.size = self.style[size_key]
                style.font.bold = True

    def _set_cell_background(self, cell, color_hex):
        """设置单元格背景色"""
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), color_hex)
        cell._tc.get_or_add_tcPr().append(shading)

    def _add_inline_formats(self, paragraph, text):
        """添加行内格式（粗体、斜体、代码、链接等）"""
        parts = parse_inline(text)
        for part in parts:
            if part[0] == "text":
                run = paragraph.add_run(part[1])
            elif part[0] == "code":
                run = paragraph.add_run(part[1])
                run.font.name = self.style["code_font"]
                run.font.size = Pt(10)
            elif part[0] == "bold":
                run = paragraph.add_run(part[1])
                run.bold = True
            elif part[0] == "italic":
                run = paragraph.add_run(part[1])
                run.italic = True
            elif part[0] == "bold_italic":
                run = paragraph.add_run(part[1])
                run.bold = True
                run.italic = True
            elif part[0] == "strikethrough":
                run = paragraph.add_run(part[1])
                run.font.strike = True
            elif part[0] == "link":
                run = paragraph.add_run(part[1])
                run.font.color.rgb = self.style["link_color"]
                run.underline = True

    def add_heading(self, level, text):
        p = self.doc.add_heading(level=level)
        run = p.add_run(text)
        run.font.name = self.style["heading_font"]
        size_key = f"h{level}_size"
        run.font.size = self.style[size_key]
        run.bold = True
        self.stats["headings"] += 1

    def add_paragraph(self, text):
        p = self.doc.add_paragraph()
        self._add_inline_formats(p, text)
        self.stats["paragraphs"] += 1

    def add_code_block(self, lang, content):
        p = self.doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.5)
        if lang:
            run = p.add_run(f"# {lang}")
            run.font.name = self.style["code_font"]
            run.font.size = self.style["code_size"]
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
            p.add_run("\n")

        for line in content.split("\n"):
            run = p.add_run(line + "\n")
            run.font.name = self.style["code_font"]
            run.font.size = self.style["code_size"]

        # 设置段落背景色
        shading = OxmlElement("w:shd")
        shading.set(qn("w:fill"), self.style["code_bg"])
        p._p.get_or_add_pPr().append(shading)

        self.stats["code_blocks"] += 1

    def add_quote(self, content):
        p = self.doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(content)
        run.font.name = self.style["quote_font"]
        run.italic = True
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        # 添加左侧竖线
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        left = OxmlElement("w:left")
        left.set(qn("w:val"), "single")
        left.set(qn("w:sz"), "18")
        left.set(qn("w:space"), "8")
        left.set(qn("w:color"), "999999")
        pBdr.append(left)
        pPr.append(pBdr)

        self.stats["quotes"] += 1

    def add_unordered_list(self, items):
        for item in items:
            p = self.doc.add_paragraph(style="List Bullet")
            indent_level = item["indent"] // 2
            if indent_level > 0:
                p.paragraph_format.left_indent = Cm(0.75 * (indent_level + 1))
            self._add_inline_formats(p, item["text"])
        self.stats["lists"] += 1

    def add_ordered_list(self, items):
        for item in items:
            p = self.doc.add_paragraph(style="List Number")
            indent_level = item["indent"] // 2
            if indent_level > 0:
                p.paragraph_format.left_indent = Cm(0.75 * (indent_level + 1))
            self._add_inline_formats(p, item["text"])
        self.stats["lists"] += 1

    def add_table(self, headers, aligns, rows):
        table = self.doc.add_table(rows=1 + len(rows), cols=len(headers))
        table.style = "Table Grid"
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # 表头
        for i, header in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(header)
            run.bold = True
            self._set_cell_background(cell, self.style["table_header_bg"])

        # 数据行
        for r_idx, row in enumerate(rows):
            for c_idx, cell_text in enumerate(row):
                if c_idx < len(table.rows[r_idx + 1].cells):
                    cell = table.rows[r_idx + 1].cells[c_idx]
                    cell.text = ""
                    p = cell.paragraphs[0]
                    self._add_inline_formats(p, cell_text)

        self.stats["tables"] += 1

    def add_hr(self):
        p = self.doc.add_paragraph()
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "000000")
        pBdr.append(bottom)
        pPr.append(pBdr)

    def add_image(self, alt, src):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if os.path.exists(src):
            try:
                run = p.add_run()
                run.add_picture(src, width=Inches(5))
                self.stats["images"] += 1
            except Exception:
                run = p.add_run(f"[图片: {alt}]")
                run.italic = True
        else:
            run = p.add_run(f"[图片: {alt}] ({src})")
            run.italic = True
            run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    def build_from_elements(self, elements):
        for elem in elements:
            t = elem["type"]
            if t == "heading":
                self.add_heading(elem["level"], elem["text"])
            elif t == "paragraph":
                self.add_paragraph(elem["content"])
            elif t == "code_block":
                self.add_code_block(elem["lang"], elem["content"])
            elif t == "quote":
                self.add_quote(elem["content"])
            elif t == "unordered_list":
                self.add_unordered_list(elem["items"])
            elif t == "ordered_list":
                self.add_ordered_list(elem["items"])
            elif t == "table":
                self.add_table(elem["headers"], elem["aligns"], elem["rows"])
            elif t == "hr":
                self.add_hr()
            elif t == "image":
                self.add_image(elem["alt"], elem["src"])

    def save(self, output_path):
        self.doc.save(output_path)
        return self.stats

    def embed_markdown_source(self, md_content):
        """将 Markdown 源码嵌入 Word 自定义属性（双层文档）"""
        core_props = self.doc.core_properties
        # 使用 custom_properties 存储大量文本
        # python-docx 不直接支持 custom_properties，使用 settings.xml
        settings = self.doc.settings.element
        # 创建自定义属性
        props = OxmlElement("w:customProperties")
        prop1 = OxmlElement("w:customProperty")
        prop1.set(qn("w:name"), "markdown_source")
        prop1.set(qn("w:value"), md_content)
        props.append(prop1)

        prop2 = OxmlElement("w:customProperty")
        prop2.set(qn("w:name"), "dual_layer")
        prop2.set(qn("w:value"), "true")
        props.append(prop2)

        prop3 = OxmlElement("w:customProperty")
        prop3.set(qn("w:name"), "markdown_version")
        prop3.set(qn("w:value"), VERSION)
        props.append(prop3)

        settings.append(props)


# ============================================================
# Word → Markdown 提取器
# ============================================================
class DocxToMarkdown:
    """从 Word 文档提取 Markdown"""

    def __init__(self, docx_path):
        self.doc = Document(docx_path)
        self.elements = []
        self.stats = {"paragraphs": 0, "headings": 0, "tables": 0, "lists": 0}

    def extract(self):
        for para in self.doc.paragraphs:
            self._process_paragraph(para)

        for table in self.doc.tables:
            self._process_table(table)

        return self.elements

    def _process_paragraph(self, para):
        style_name = para.style.name if para.style else ""

        if style_name.startswith("Heading"):
            level = int(style_name.split()[-1]) if style_name.split()[-1].isdigit() else 1
            text = para.text.strip()
            if text:
                self.elements.append({"type": "heading", "level": level, "text": text})
                self.stats["headings"] += 1
        elif style_name == "List Bullet":
            text = self._extract_inline(para)
            self.elements.append({"type": "bullet", "text": text})
            self.stats["lists"] += 1
        elif style_name == "List Number":
            text = self._extract_inline(para)
            self.elements.append({"type": "numbered", "text": text})
            self.stats["lists"] += 1
        elif style_name in ("Intense Quote", "Quote"):
            text = para.text.strip()
            if text:
                self.elements.append({"type": "quote", "content": text})
        elif para.text.strip():
            text = self._extract_inline(para)
            self.elements.append({"type": "paragraph", "content": text})
            self.stats["paragraphs"] += 1

    def _extract_inline(self, para):
        """提取段落中的行内格式"""
        result = ""
        for run in para.runs:
            text = run.text
            if not text:
                continue
            if run.bold and run.italic:
                result += f"***{text}***"
            elif run.bold:
                result += f"**{text}**"
            elif run.italic:
                result += f"*{text}*"
            elif run.font.strike:
                result += f"~~{text}~~"
            elif run.font.name and run.font.name in ("Consolas", "Courier New", "Courier"):
                result += f"`{text}`"
            else:
                result += text
        return result

    def _process_table(self, table):
        if len(table.rows) < 2:
            return

        headers = [cell.text.strip() for cell in table.rows[0].cells]
        rows = []
        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            rows.append(cells)

        self.elements.append({"type": "table", "headers": headers, "rows": rows})
        self.stats["tables"] += 1

    def to_markdown(self):
        """将提取的元素转换为 Markdown 文本"""
        lines = []
        for elem in self.elements:
            t = elem["type"]
            if t == "heading":
                prefix = "#" * elem["level"]
                lines.append(f"{prefix} {elem['text']}")
                lines.append("")
            elif t == "paragraph":
                lines.append(elem["content"])
                lines.append("")
            elif t == "bullet":
                lines.append(f"- {elem['text']}")
            elif t == "numbered":
                lines.append(f"1. {elem['text']}")
            elif t == "quote":
                for qline in elem["content"].split("\n"):
                    lines.append(f"> {qline}")
                lines.append("")
            elif t == "table":
                header_line = "| " + " | ".join(elem["headers"]) + " |"
                sep_line = "| " + " | ".join(["---"] * len(elem["headers"])) + " |"
                lines.append(header_line)
                lines.append(sep_line)
                for row in elem["rows"]:
                    lines.append("| " + " | ".join(row) + " |")
                lines.append("")
        return "\n".join(lines)


# ============================================================
# 双层文档提取
# ============================================================
def extract_markdown_from_dual(docx_path):
    """从双层文档中提取嵌入的 Markdown 源码"""
    doc = Document(docx_path)
    settings = doc.settings.element

    custom_props = settings.findall(qn("w:customProperties"))
    for props in custom_props:
        for prop in props.findall(qn("w:customProperty")):
            name = prop.get(qn("w:name"))
            value = prop.get(qn("w:value"))
            if name == "markdown_source":
                return value

    return None


# ============================================================
# 主入口
# ============================================================
def cmd_md2docx(args):
    """Markdown → Word"""
    md_path = args.input
    output = args.output or str(Path(md_path).with_suffix(".docx"))
    style = args.style or "standard"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = MarkdownParser(content)
    elements = parser.parse()

    builder = DocxBuilder(style)
    builder.build_from_elements(elements)
    stats = builder.save(output)

    print(f"转换完成: {md_path} → {output}")
    print(f"风格: {style}")
    print(f"统计: {stats['headings']} 标题, {stats['paragraphs']} 段落, "
          f"{stats['code_blocks']} 代码块, {stats['tables']} 表格, "
          f"{stats['lists']} 列表, {stats['quotes']} 引用, {stats['images']} 图片")

    return output


def cmd_docx2md(args):
    """Word → Markdown"""
    docx_path = args.input
    output = args.output or str(Path(docx_path).with_suffix(".md"))

    extractor = DocxToMarkdown(docx_path)
    extractor.extract()
    md_content = extractor.to_markdown()

    with open(output, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"转换完成: {docx_path} → {output}")
    print(f"统计: {extractor.stats['headings']} 标题, "
          f"{extractor.stats['paragraphs']} 段落, "
          f"{extractor.stats['tables']} 表格, {extractor.stats['lists']} 列表")

    return output


def cmd_dual(args):
    """创建双层文档：Word 排版 + Markdown 源码"""
    md_path = args.input
    output = args.output or str(Path(md_path).with_suffix(".docx"))
    style = args.style or "standard"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    parser = MarkdownParser(content)
    elements = parser.parse()

    builder = DocxBuilder(style)
    builder.build_from_elements(elements)
    builder.embed_markdown_source(content)
    stats = builder.save(output)

    print(f"双层文档创建完成: {md_path} → {output}")
    print(f"风格: {style}")
    print(f"统计: {stats['headings']} 标题, {stats['paragraphs']} 段落, "
          f"{stats['code_blocks']} 代码块, {stats['tables']} 表格, "
          f"{stats['lists']} 列表, {stats['quotes']} 引用, {stats['images']} 图片")
    print(f"Markdown 源码已嵌入自定义属性，可用 extract 模式恢复")

    return output


def cmd_extract(args):
    """从双层文档中提取 Markdown 源码"""
    docx_path = args.input
    output = args.output or str(Path(docx_path).with_suffix(".md"))

    md_source = extract_markdown_from_dual(docx_path)

    if md_source:
        with open(output, "w", encoding="utf-8") as f:
            f.write(md_source)
        print(f"Markdown 源码提取成功: {docx_path} → {output}")
        print(f"源码长度: {len(md_source)} 字符")
    else:
        print(f"未找到嵌入的 Markdown 源码，回退到 Word → Markdown 逆向提取模式", file=sys.stderr)
        extractor = DocxToMarkdown(docx_path)
        extractor.extract()
        md_content = extractor.to_markdown()
        with open(output, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"逆向提取完成: {docx_path} → {output}")
        print(f"统计: {extractor.stats['headings']} 标题, "
              f"{extractor.stats['paragraphs']} 段落, "
              f"{extractor.stats['tables']} 表格, {extractor.stats['lists']} 列表")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="MD-Doc-Bridge: Markdown ↔ Word 双层文档转换工具 v" + VERSION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="mode", help="转换模式")

    p_md2docx = subparsers.add_parser("md2docx", help="Markdown → Word")
    p_md2docx.add_argument("input", help="Markdown 文件路径")
    p_md2docx.add_argument("--output", help="输出 Word 文件路径")
    p_md2docx.add_argument("--style", choices=list(STYLES.keys()), default="standard", help="排版风格")

    p_docx2md = subparsers.add_parser("docx2md", help="Word → Markdown")
    p_docx2md.add_argument("input", help="Word 文件路径")
    p_docx2md.add_argument("--output", help="输出 Markdown 文件路径")

    p_dual = subparsers.add_parser("dual", help="创建双层文档（Word 排版 + Markdown 源码）")
    p_dual.add_argument("input", help="Markdown 文件路径")
    p_dual.add_argument("--output", help="输出 Word 文件路径")
    p_dual.add_argument("--style", choices=list(STYLES.keys()), default="standard", help="排版风格")

    p_extract = subparsers.add_parser("extract", help="从双层文档提取 Markdown 源码")
    p_extract.add_argument("input", help="Word 文件路径")
    p_extract.add_argument("--output", help="输出 Markdown 文件路径")

    args = parser.parse_args()

    if args.mode == "md2docx":
        cmd_md2docx(args)
    elif args.mode == "docx2md":
        cmd_docx2md(args)
    elif args.mode == "dual":
        cmd_dual(args)
    elif args.mode == "extract":
        cmd_extract(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
