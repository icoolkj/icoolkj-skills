# Markdown ↔ Word 转换规则详解

## Markdown → Word 元素映射

### 标题

| Markdown | Word 样式 | 字体（standard） | 字号 | 颜色 |
|----------|-----------|------------------|------|------|
| `# H1` | Heading 1 | 黑体 | 22pt | #000000 |
| `## H2` | Heading 2 | 黑体 | 18pt | #000000 |
| `### H3` | Heading 3 | 黑体 | 16pt | #333333 |
| `#### H4` | Heading 4 | 黑体 | 14pt | #333333 |
| `##### H5` | Heading 5 | 黑体 | 12pt | #666666 |
| `###### H6` | Heading 6 | 黑体 | 11pt | #666666 |

### 段落

| Markdown | Word 样式 | 说明 |
|----------|-----------|------|
| 普通段落 | Normal | 宋体 12pt，行距 1.5 |
| `> 引用` | Intense Quote | 左缩进 + 灰色竖线 + 斜体 |
| `---` | 水平线 | 1pt 黑色水平线 |

### 列表

| Markdown | Word 样式 | 说明 |
|----------|-----------|------|
| `- item` / `* item` | List Bullet | 项目符号列表 |
| `+ item` | List Bullet | 项目符号列表（同上） |
| `1. item` | List Number | 编号列表 |
| 嵌套列表 | List Bullet 2 / List Number 2 | 缩进 + 不同符号 |

### 代码

| Markdown | Word 处理 | 说明 |
|----------|-----------|------|
| ```` ```lang ``` ```` | 代码块段落 | 等宽字体（Consolas/Courier New），灰色背景 (#F0F0F0)，保留缩进 |
| `` `code` `` | 行内代码 | 等宽字体，灰色背景 |

代码块处理细节：
- 保留原始缩进和换行
- 语言标识（如 ```python）作为代码块首行注释保留
- 长行不自动换行，保持代码完整性

### 强调

| Markdown | Word 处理 |
|----------|-----------|
| `**粗体**` | Bold run |
| `*斜体*` | Italic run |
| `***粗斜体***` | Bold + Italic run |
| `~~删除线~~` | Strikethrough run |
| `__粗体__` | Bold run（同 `**`） |
| `_斜体_` | Italic run（同 `*`） |

### 链接与图片

| Markdown | Word 处理 |
|----------|-----------|
| `[text](url)` | Hyperlink（蓝色下划线） |
| `![alt](path)` | Inline Image（尝试加载本地图片，失败则插入 alt 文本） |
| `[text](url "title")` | Hyperlink + tooltip |

### 表格

Markdown 表格转换为 Word 原生表格：
- 第一行作为表头（加粗 + 灰色背景）
- 对齐标记（`:---`, `:--:`, `---:`）映射为单元格对齐方式
- 单元格内支持行内格式（粗体、斜体、代码等）

### 特殊元素

| Markdown | Word 处理 |
|----------|-----------|
| `[^1]` 脚注 | 脚注（Word footnote） |
| `~~text~~` | 删除线 |
| HTML 标签 | 忽略（不解析 HTML） |
| 任务列表 `- [x]` | 复选框符号（☐/☑） |

## Word → Markdown 提取规则

### 样式逆向映射

| Word 样式 | Markdown 输出 |
|-----------|---------------|
| Heading 1~6 | `#` ~ `######` |
| Normal | 普通段落 |
| List Bullet | `- item` |
| List Number | `1. item` |
| Intense Quote / Quote | `> 引用` |
| 代码块段落 | ```` ``` ```` |

### 格式提取

| Word 格式 | Markdown 输出 |
|-----------|---------------|
| Bold run | `**text**` |
| Italic run | `*text*` |
| Bold + Italic | `***text***` |
| Strikethrough | `~~text~~` |
| Hyperlink | `[text](url)` |
| 等宽字体段落 | `` `code` `` 或代码块 |

### 表格提取

Word 表格 → Markdown 表格：
- 第一行作为表头
- 自动检测对齐方式
- 合并单元格拆分为独立单元格

### 图片处理

Word 内嵌图片 → Markdown 图片引用：
- 提取图片到输出目录的 `images/` 子文件夹
- 生成相对路径引用 `![image](images/image1.png)`
- 图片命名：`image1.png`, `image2.png`, ...

## 双层文档机制

### 存储方式

双层文档使用 Word 的 `customProperties` 存储 Markdown 源码：

```
customProperties:
  - name: "markdown_source"
    value: <完整 Markdown 源码>
  - name: "markdown_version"
    value: "1.0"
  - name: "dual_layer"
    value: "true"
```

### 提取流程

1. 打开 .docx 文件
2. 读取 customProperties 中的 `markdown_source`
3. 验证 `dual_layer` 标记为 `true`
4. 输出 Markdown 源码到指定文件
5. 如果 customProperties 不存在，回退到 docx2md 模式（从 Word 内容逆向提取）

### 完整性保证

- Markdown 源码存储为完整字符串，不截断
- 包含原始 Markdown 的所有元素（包括 HTML 注释、脚注等）
- 版本标记用于未来格式升级的兼容性处理
