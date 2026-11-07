---
name: md-word-dual
description: "Markdown 与 Word 的双向转换与「双层文档」生成。把 Markdown 转成带标题层级、表格、代码框的正规 Word，同时把原始 Markdown 压缩藏进同一个 .docx（自定义 XML 部件 + 隐藏文字双重保险），读者双击看 Word，程序一条命令取回逐字节一致的 Markdown；也能把别人的普通 docx 反解成 Markdown。提供 standard / clean / formal / blog 四套排版预设。适用于「开发写 md、业务方要 Word」的交付场景，适合需要长期维护、反复导出的文档。不用于纯 Word 排版美化（无 Markdown 源），也不用于 PDF 生成或扫描件识别。"
agent_created: true
version: 1.1.0
display_name: 双层文档（Markdown ⇄ Word）
display_name_en: Dual-Layer Document (Markdown ⇄ Word)
description_zh: "Markdown 与 Word 的双向转换与「双层文档」生成。把 Markdown 转成带标题层级、表格、代码框的正规 Word，同时把原始 Markdown 压缩藏进同一个 .docx（自定义 XML 部件 + 隐藏文字双重保险），读者双击看 Word，程序一条命令取回逐字节一致的 Markdown；也能把别人的普通 docx 反解成 Markdown。提供 standard / clean / formal / blog 四套排版预设。适用于「开发写 md、业务方要 Word」的交付场景，适合需要长期维护、反复导出的文档。不用于纯 Word 排版美化（无 Markdown 源），也不用于 PDF 生成或扫描件识别。"
description_en: "Two-way Markdown ↔ Word conversion with a dual-layer .docx: the Markdown is rendered into a properly styled Word document (heading levels, tables, code boxes) while the original Markdown is compressed and stored inside the same .docx as a custom XML part plus hidden text. Readers open it as Word; tools recover byte-identical Markdown with one command. Also converts ordinary .docx files back to Markdown. Four layout presets (standard, clean, formal, blog) are available. Suited to delivery workflows where developers write Markdown but stakeholders read Word, and to documents that must be re-exported repeatedly. Not for Word-only layout beautification without a Markdown source, and not for PDF generation or OCR of scanned documents."
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
---

# 双层文档：Markdown ⇄ Word

## 为什么需要它

开发用 Markdown 写东西，业务方只认 Word。常规做法是导出一份 docx，但导完就成了「死文件」：
下次要改，得回到 md 重导一遍；别人在 Word 里改了两句，改动也回不到 md。

这个技能把 `.docx` 做成**双层结构**：

- **可见层**：真正的 Word 排版，标题带大纲级别（导航窗格可用）、表格首行跨页重复、代码块带边框底纹。
- **隐藏层**：原始 Markdown 压缩后写进同一个文件，双保险存放——
  ① `customXml/item1.xml` 自定义 XML 部件（标准 OOXML 机制，Word 不渲染但随包保存）；
  ② 文末一段「隐藏文字」段落（正文内容，抗得住多数编辑器另存）。

于是同一个文件有了两种读法：读者双击看 Word，开发者一条命令取回**逐字节一致**的 Markdown。
思路与「双层 PDF」（视觉层 + 可提取文字层）一致，只是这里的第二层存的是源文件。

## 快速开始

命令在 **skill 目录内**执行，无需安装任何依赖（纯标准库，Python ≥ 3.10）。

```bash
# Markdown → 双层 Word
python scripts/md2docx.py 文档.md

# 取回 Markdown（自动优先走隐藏层）
python scripts/docx2md.py 文档.docx

# 体检：结构是否合规、两层是否都在
python scripts/dualdoc.py verify 文档.docx

# 验收：往返是否逐字节一致
python scripts/dualdoc.py roundtrip 文档.md
```

一条命令搞定方向判断：

```bash
python scripts/dualdoc.py convert 文档.md      # 出 .docx
python scripts/dualdoc.py convert 文档.docx    # 出 .md
```

## 排版预设

同一份内容可以有四种观感，`--preset` 切换（默认 `standard`），`--style` 是它的别名：

| 预设 | 观感 | 适合 |
| --- | --- | --- |
| `standard` | 等线正文 + 雅黑标题，A4 常规页边距 | 通用交付 |
| `clean` | 全域雅黑，行距更宽，页边距 2cm | 屏幕阅读、内部评审 |
| `formal` | 仿宋正文 + 黑体标题，左 3.18cm 公文页边距 | 打印、正式报告 |
| `blog` | 大标题、宽段距，页边距 1.5cm | 线上发布前的预览稿 |

```bash
python scripts/md2docx.py 报告.md --preset formal
```

预设只影响可见层，隐藏层与往返一致性完全不受影响；四种预设产出的 docx 都会过同一套自检。

## 工作流

**交付流程（最常见）**

1. `python scripts/md2docx.py 需求文档.md --toc`
2. 把生成的 `.docx` 发给业务方，自己保留 `.md`
3. 业务方在 Word 里批注、改错别字
4. 要合并回源文件时：`python scripts/docx2md.py 需求文档.docx`
   —— 若对方只改了文字没动结构，优先拿隐藏层那份原文；若结构被大改，加 `--structure` 按样式反解

**接收流程（别人给的 Word）**

1. `python scripts/dualdoc.py verify 对方文档.docx` 先看有没有隐藏层
2. 有 → `docx2md.py` 直接无损取回
3. 没有 → `docx2md.py` 自动结构化反解，输出里会标注「结构化反解（普通 docx）」

**改完必须验收**

改动了 `scripts/` 下任何代码后，跑一次：

```bash
python tests/test_roundtrip.py
```

## 命令索引

| 脚本 | 用途 | 关键参数 |
| --- | --- | --- |
| `scripts/md2docx.py` | Markdown → 双层 docx | `--preset standard\|clean\|formal\|blog`、`--toc` 目录域、`--embed-mode both\|customxml\|hidden\|none`、`--title`、`--json` |
| `scripts/docx2md.py` | docx → Markdown | `--structure` 强制反解、`--json` |
| `scripts/dualdoc.py` | 统一入口 | 子命令 `convert` / `verify` / `roundtrip` / `info` |
| `scripts/docxkit.py` | 核心引擎（供上面三个调用，无 CLI） | —— |

参数细节见各脚本的 `--help`；语法映射与保真度见 `references/markdown-mapping.md`；
报错与异常场景见 `references/troubleshooting.md`。

## 能力边界

**能做**：标题 1–6、段落、有序/无序列表（含嵌套）、引用块、围栏代码块、表格、分隔线、
行内加粗/斜体/删除线/行内代码/链接、本地图片嵌入、`<br>` 换行。

**不做**：脚注、数学公式、任务列表勾选框、HTML 块、引用式链接——遇到按纯文本照抄，不报错。
外链图片不下载，只在 Word 里留占位文字。

**不该用**：没有 Markdown 源、只想美化一份 Word（这属于排版任务，不是双向转换）；
从扫描件/PDF 提取内容（那是 OCR 与 PDF 解析的范畴）。

## 三条质量红线

1. **写完必须自检**：`md2docx.py` 默认会跑 OOXML 严格校验（元素顺序、关系引用、
   内容类型覆盖）。Word 对属性子元素顺序敏感，顺序错会弹「文件已损坏」——
   自检不通过就不许交付，不要用 `--no-validate` 蒙混。
2. **改结构后必须往返校验**：`dualdoc.py roundtrip 文档.md` 要能输出「逐字节一致」。
3. **隐藏层不是加密**：懂行的人可以把 Markdown 提出来。对外分发且不想暴露源码时，
   用 `--embed-mode none` 只产出纯 Word。
