#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回归测试：Markdown ⇄ DOCX 往返一致性 + 包结构自检。

运行（在 skill 根目录）：
    python tests/test_roundtrip.py
    python -m unittest discover -s tests -v

本目录不进上传包，仅用于开发自测。
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import docxkit  # noqa: E402

SAMPLE = """# 标题一

普通段落，含**加粗**、*斜体*、`行内代码`和[链接](https://example.com)。

## 标题二

- 项目一
- 项目二
  - 嵌套

1. 第一步
2. 第二步

> 引用一行
> 引用两行

```python
def f(x):
    return x + 1
```

| 名称 | 说明 |
| --- | --- |
| A | 第一个 |
| B | 第二个 |

---

收敛句。
"""


class TestParse(unittest.TestCase):
    def test_block_kinds(self):
        kinds = [b["t"] for b in docxkit.parse_markdown(SAMPLE)]
        self.assertEqual(
            kinds,
            ["heading", "para", "heading", "list", "list", "quote", "code", "table", "hr", "para"],
        )

    def test_nested_list_level(self):
        lists = [b for b in docxkit.parse_markdown(SAMPLE) if b["t"] == "list"]
        self.assertEqual([i["level"] for i in lists[0]["items"]], [0, 0, 1])

    def test_inline_formats(self):
        toks = docxkit.parse_inline("a**b**c* d `e`")
        joined = "".join(t for t, _ in toks)
        self.assertIn("b", joined)
        self.assertIn("e", joined)


class TestRoundTrip(unittest.TestCase):
    def test_embedded_roundtrip_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "a.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            out = os.path.join(tmp, "a.docx")
            docxkit.markdown_to_docx(md, out)
            back, origin = docxkit.docx_to_markdown(out)
            self.assertEqual(origin, "embedded")
            self.assertEqual(back, SAMPLE)

    def test_two_layers_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "b.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            out = os.path.join(tmp, "b.docx")
            docxkit.markdown_to_docx(md, out)
            layers = docxkit.embedded_layers(out)
            self.assertTrue(layers["customxml"])
            self.assertTrue(layers["hidden_text"])

    def test_validate_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "c.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            out = os.path.join(tmp, "c.docx")
            docxkit.markdown_to_docx(md, out)
            v = docxkit.validate_docx(out)
            self.assertTrue(v["ok"], v["problems"])

    def test_plain_docx_falls_back_to_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "d.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            out = os.path.join(tmp, "d.docx")
            docxkit.markdown_to_docx(md, out, embed_source=False)
            back, origin = docxkit.docx_to_markdown(out)
            self.assertEqual(origin, "structure")
            self.assertIn("# 标题一", back)
            self.assertIn("| 名称 | 说明 |", back)

    def test_structure_keeps_lists_and_fences(self):
        """纯 Word 反解时，列表标记与代码围栏不能丢——这是最容易退化的两处。"""
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "e.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            out = os.path.join(tmp, "e.docx")
            docxkit.markdown_to_docx(md, out, embed_source=False)
            back, _ = docxkit.docx_to_markdown(out)
            self.assertIn("- 项目一", back)
            self.assertIn("1. 第一步", back)
            self.assertIn("2. 第二步", back)
            self.assertIn("```", back)
            self.assertIn("def f(x):", back)
            self.assertIn("> 引用一行", back)
            # 标题本身加粗，不能把加粗标记带进标题文本
            self.assertNotIn("# **", back)


class TestPresets(unittest.TestCase):
    def test_all_presets_render_and_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "p.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write(SAMPLE)
            seen = set()
            for name in docxkit.preset_choices():
                out = os.path.join(tmp, f"p_{name}.docx")
                res = docxkit.markdown_to_docx(md, out, preset=name)
                self.assertEqual(res["path"], out)
                v = docxkit.validate_docx(out)
                self.assertTrue(v["ok"], f"{name}: {v['problems']}")
                # 往返不受预设影响
                back, origin = docxkit.docx_to_markdown(out)
                self.assertEqual(origin, "embedded")
                self.assertEqual(back, SAMPLE)
                seen.add(docxkit.styles_xml(name))
            self.assertEqual(len(seen), len(docxkit.preset_choices()), "各预设应产生不同的样式表")

    def test_preset_page_margins(self):
        import zipfile

        with tempfile.TemporaryDirectory() as tmp:
            md = os.path.join(tmp, "q.md")
            with open(md, "w", encoding="utf-8") as fh:
                fh.write("# 标题\n\n正文\n")
            out = os.path.join(tmp, "q.docx")
            docxkit.markdown_to_docx(md, out, preset="formal")
            with zipfile.ZipFile(out) as zf:
                doc = zf.read("word/document.xml").decode("utf-8")
            self.assertIn('w:left="1800"', doc)

    def test_unknown_preset_falls_back(self):
        self.assertEqual(docxkit.get_preset("nope")["label"], docxkit.get_preset("standard")["label"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
