# archive

已归档、不再维护的技能。保留在这里是为了留存历史与实现参考，**不会被 `tools/` 下的脚本扫描或打包**。

| 目录 | 归档时间 | 替代方案 |
| --- | --- | --- |
| `md-doc-bridge/` | 2026-11-07 | `md-word-dual` |

## md-doc-bridge 为什么归档

它是「双层文档」的第一版实现，思路与现在的 `md-word-dual` 一致，但隐藏层不成立：

1. **存放位置不合规**：把原始 Markdown 写进 `word/settings.xml` 里自造的 `<w:customProperties>`。
   OOXML 里自定义属性属于 `docProps/custom.xml`，`settings.xml` 合法的同名机制是 `w:docVars`
   （且有 255 字符上限）。自造元素在 Word 保存时可能被丢弃。
2. **单层无校验**：没有第二份备份、没有哈希，一旦被别的编辑器重写就永久失去源码，
   而且不报错——取回时静默退化成有损反解。
3. **体积膨胀**：整段源码作为 XML 属性值明文存放，换行变成 `&#10;`。
   实测 1.57 万字的文档让 `settings.xml` 从 2.5 KB 涨到 35.5 KB；`md-word-dual` 的同一份文档
   `settings.xml` 仍是 0.4 KB。
4. **生成时丢内容**：`_add_inline_formats` 会漏掉行内代码的文字，
   实测生成的 docx 里根本不含 `docx2md`、`md2docx` 这些字符串——任何读取工具都救不回来。
5. **破坏 pPr 子元素顺序**：引用块的 `pBdr`、代码块的 `shd` 是 `append` 进去的，
   排在 `w:ind` 之后，属于 Word 弹「需要修复」的典型诱因。
6. **工程状态不全**：无测试、未进 README、frontmatter 缺 `version`/`display_name` 等字段，
   `tools/build_skills.py --check` 判 FAIL。

## 如果仍想运行

```bash
pip install python-docx markdown        # 需要两个第三方库
python archive/md-doc-bridge/scripts/convert.py dual 文档.md --output 文档.docx
python archive/md-doc-bridge/scripts/convert.py extract 文档.docx
```

注意：用 `python -m pip install` 装到当前解释器，直接 `pip` 可能装到另一个 Python 上。

新的文档转换需求请使用 `md-word-dual`。
