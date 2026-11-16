# index.json 结构规范

## 顶层结构

```json
{
  "version": "1.0.0",
  "root_path": "/home/user/documents/",
  "index_path": "/home/user/documents/.doc-manager/",
  "scan_time": "2026-01-15T10:00:00",
  "last_classified": "2026-01-15T10:30:00",
  "taxonomy": {
    "dimensions": [...]
  },
  "documents": [...]
}
```

## taxonomy（分类维度）

```json
{
  "dimensions": [
    {
      "id": "topic",
      "name": "内容主题",
      "values": ["AI", "职场", "教程", "测评"]
    },
    {
      "id": "status",
      "name": "发布状态",
      "values": ["草稿", "已发布", "待修改"]
    }
  ]
}
```

- `id`：维度标识符，英文小写，用于 documents 中引用
- `name`：维度中文名称，展示给用户
- `values`：该维度的可选标签值列表（3~10个）

维度数量：2~5 个。维度由 Agent 在 Phase 2 根据文件内容动态归纳，不预设固定维度。

## documents（文档列表）

```json
{
  "id": "doc-0001",
  "path": "xhs/2026-ai-trends.md",
  "filename": "2026-ai-trends.md",
  "ext": ".md",
  "type": "text",
  "title": "2026年AI趋势",
  "size_bytes": 3200,
  "created_at": "2026-01-15T10:00:00",
  "modified_at": "2026-01-15T12:00:00",
  "summary": "这篇文案总结了2026年AI领域的5大趋势...",
  "images": [
    {"path": "images/cover.png", "alt": "封面图", "position": 1}
  ],
  "tags": {
    "topic": {"value": "AI", "confidence": "high"},
    "status": {"value": "已发布", "confidence": "high"}
  }
}
```

### 字段说明

| 字段 | 来源 | 说明 |
|------|------|------|
| id | scan.py | 自增编号 |
| path | scan.py | 相对于 root_path 的路径 |
| filename | scan.py | 文件名 |
| ext | scan.py | 扩展名 |
| type | scan.py | 文件类型（text/word/pdf/image/slides/spreadsheet/other） |
| title | scan.py | 从内容提取的标题 |
| size_bytes | scan.py | 文件大小 |
| created_at | scan.py | 创建时间 |
| modified_at | scan.py | 修改时间 |
| summary | scan.py | 前500字摘要 |
| images | scan.py | .md 文件中的图片引用列表 |
| tags | Agent | Phase 3 打的标签，按 taxonomy 维度组织 |

### tags 结构

每个维度对应一个对象：
- `value`：标签值（必须是 taxonomy 中该维度的 values 之一，或"待确认"）
- `confidence`：置信度（high/medium/low）

`low` 置信度的标签，`value` 设为"待确认"，表示需要人工确认。

### images 结构

仅 .md 文件有此字段：
- `path`：图片路径（Markdown 中引用的原始路径）
- `alt`：图片描述（alt text）
- `position`：在文档中的位置序号

## 增量分类规则

当再次运行 classify 时：
1. 读取现有 index.json
2. 对 `tags` 字段为空或不存在的文档进行分类
3. 已有 tags 的文档跳过
4. 新文档追加到 documents 列表
5. 更新 `last_classified` 时间戳