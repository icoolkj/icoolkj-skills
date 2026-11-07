---
name: md-doc-bridge
description: |
  Markdown 与 Word 双向转换工具。支持 Markdown→Word、Word→Markdown、以及"双层文档"模式——
  在同一个 Word 文件中同时保留 Markdown 源码层和 Word 排版层，类似双层 PDF 的理念。
  开发者用 Markdown 写作，阅读者用 Word 阅读，一份文件两种格式无缝互通。
  触发词：Markdown转Word、Word转Markdown、双层文档、md转docx、docx转md、格式转换、双层PDF、dual-layer document。
allowed-tools: Bash(python:*)
---

# MD-Doc-Bridge：Markdown ↔ Word 双层文档转换工具

> **已归档（2026-11-07），不再维护。**  
> 隐藏层存放位置不合规（`settings.xml` 里的自造元素）、单层无校验、生成时会丢失行内代码文字，
> 且未通过仓库打包校验。新的文档转换需求请用 **`md-word-dual`**。
> 归档原因与实测数据见 `archive/README.md`。

> 开发者用 Markdown 写作，阅读者用 Word 阅读。一份文件，两种格式，无缝互通。

## 核心理念

类似双层 PDF（图片层 + 文字层），本工具创造"双层文档"概念：
- **Markdown 层**：保留原始 Markdown 源码，开发者可编辑、版本管理
- **Word 层**：专业排版渲染，阅读者可直接阅读、批注
- 两层共存于同一个 .docx 文件中，互不干扰

## 何时触发

- "把这个 Markdown 转成 Word"
- "把这个 Word 转成 Markdown"
- "我要一个既能 Markdown 编辑又能 Word 阅读的文档"
- "创建双层文档"
- "Markdown 和 Word 互相转换"

## 三种转换模式

| 模式 | 命令 | 说明 |
|------|------|------|
| md2docx | `python scripts/convert.py md2docx <md文件> [--output <docx文件>]` | Markdown → Word，纯排版转换 |
| docx2md | `python scripts/convert.py docx2md <docx文件> [--output <md文件>]` | Word → Markdown，提取结构化内容 |
| dual | `python scripts/convert.py dual <md文件> [--output <docx文件>]` | 创建双层文档：Word 排版 + Markdown 源码 |

## 工作流

### Phase 1：确定转换模式

Agent 根据用户意图选择模式：
- 用户给 .md 文件，要 Word → `md2docx`
- 用户给 .docx 文件，要 Markdown → `docx2md`
- 用户要"双层文档"/"既能编辑又能阅读" → `dual`

### Phase 2：执行转换

```bash
python scripts/convert.py <mode> <input> [--output <output>] [--style <style-name>]
```

参数说明：
- `mode`：md2docx / docx2md / dual
- `input`：输入文件路径
- `--output`：输出文件路径（默认：同目录下改扩展名）
- `--style`：Word 排版风格（默认: standard，可选: standard/clean/formal/blog）

### Phase 3：交付结果

Agent 向用户报告：
- 转换模式、输入/输出路径
- 转换统计（段落数、表格数、代码块数等）
- 双层文档模式下，说明如何提取 Markdown 源码（`python scripts/convert.py extract <docx文件>`）

## 双层文档机制

双层文档（dual mode）的工作原理：

1. **Word 排版层**：将 Markdown 渲染为专业排版的 Word 内容（标题、表格、列表、代码块等）
2. **Markdown 源码层**：将原始 Markdown 源码存入 Word 文件的自定义属性（customProperties）
3. **读取时**：`extract` 命令从自定义属性中恢复完整 Markdown 源码

这意味着：
- 阅读者打开 .docx 看到的是排版精美的文档
- 开发者可以用 `extract` 命令恢复原始 Markdown，继续编辑
- 版本管理时只需跟踪 .docx 文件，Markdown 源码不丢失

## Markdown 渲染规则

转换引擎支持的 Markdown 元素及对应的 Word 样式：

| Markdown 元素 | Word 样式 |
|---------------|-----------|
| `# H1` | Heading 1 |
| `## H2` | Heading 2 |
| `### H3` ~ `###### H6` | Heading 3 ~ Heading 6 |
| 普通段落 | Normal |
| `- 列表项` / `* 列表项` | List Bullet |
| `1. 有序列表` | List Number |
| `> 引用` | Quote / Intense Quote |
| ```` ``` 代码块 ```` | 代码块（等宽字体 + 灰色背景） |
| `` `行内代码` `` | 行内代码（等宽字体） |
| `**粗体**` | Bold |
| `*斜体*` | Italic |
| `[链接](url)` | Hyperlink |
| `![图片](path)` | Inline Image |
| `---` 分割线 | 水平线 |
| `| 表格 |` | Table |

## Word 排版风格

| 风格 | 适用场景 | 特点 |
|------|----------|------|
| standard | 通用文档 | 宋体正文 + 黑体标题，A4 页面 |
| clean | 简约风格 | 无衬线字体，宽松行距，适合屏幕阅读 |
| formal | 正式报告 | 仿宋正文 + 黑体标题，页眉页脚，适合打印 |
| blog | 博客文章 | 无衬线字体，宽松段落间距，适合在线发布 |

## 安全约束

- 转换过程不修改原始输入文件
- 图片引用使用相对路径，不嵌入外部图片（除非用户指定）
- 双层文档的 Markdown 源码层不包含敏感信息（如密码、密钥）

## 资源导航

| 资源 | 路径 | 用途 |
|------|------|------|
| 转换规则详解 | `references/conversion-rules.md` | Markdown 元素到 Word 样式的完整映射规则 |
| 排版风格规范 | `references/style-specs.md` | 四种排版风格的字体、间距、页面设置详细规范 |
| 转换脚本 | `scripts/convert.py` | 主转换引擎（md2docx / docx2md / dual / extract） |

## 依赖

Python 3.8+，需要 `python-docx` 和 `markdown` 库。脚本会自动检测并提示安装。
