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


if __name__ == "__main__":
    unittest.main(verbosity=2)
