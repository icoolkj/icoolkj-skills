---
name: note-intel
description: 自媒体内容情报与图文策划 Skill。把一篇文章/资料/网页转化为结构化、可核对、可继续创作的内容素材包。弹性约束设计——先判断素材的篇幅和信息密度，再动态决定提取多少事实、生成多少选题，绝不虚构、绝不强制填充。
---

# NoteIntel — 自媒体内容情报与图文策划

## 设计哲学

**弹性约束，而非固定模板。** 先判断素材的深度和密度，再决定输出规模。

NoteIntel 不是"生成器"，而是"情报官"——先理解素材，再决定提取多少、生成多少。不预设固定数量的输出条目，而是根据素材的篇幅和信息密度动态决定。绝不虚构、绝不强制填充。

---

## 工作流

### 步骤1：素材输入

接收用户提供的素材来源（URL、文件路径、或粘贴文本），调用分析器脚本进行输入处理和评估。

```bash
python scripts/analyze_material.py --input <URL|文件路径|文本> --output analysis.json
```

脚本完成：
- URL抓取（内置，自动转为纯文本）
- 文件读取
- 文本清洗
- 字数统计
- 信息密度评估（8项指标）
- 模式判定（精简/标准/深度）
- 配额表生成

输出 `analysis.json`，包含 `mode`、`density_score`、`density_factors`、`quotas`、`clean_text`。

### 步骤2：评估定模确认

审查 `analysis.json` 中的配额表，确认模式判定合理：

- 查看篇幅初判与密度修正是否匹配素材实际
- 确认配额表中的事实/选题数量范围
- 如模式判定明显不合理（如高密度短文被判为精简），可手动调整

**模式规则**：

| 模式 | 篇幅 | 事实配额 | 选题配额 |
|------|------|----------|----------|
| 精简 | <800字 | 2-4 | 1-2 |
| 标准 | 800-3000字 | 4-8 | 3-5 |
| 深度 | >3000字 | 6-12 | 4-7 |

密度修正：密度分 >0.7 可上调一级；密度分 <0.3 可下调一级。

### 步骤3：信息提取

按配额表提取核心事实。**必须遵循 `references/extraction-guide.md` 中的提取标准。**

关键规则：
- 每条事实必须可在原文中找到对应内容（不虚构）
- 每条事实必须标注原文定位（段落编号+引用片段）
- 数据精度与原文一致（不篡改、不四舍五入）
- 事实与观点严格区分
- 事实去重：同一数据只提取一次

提取格式：
```
1. 【事实内容】
   📍 原文定位：第X段，第Y句
   📎 原文引用："原文对应片段"
```

### 步骤4：选题生成

按配额表生成创作选题。**必须遵循 `references/topic-formulas.md` 中的选题公式。**

每条选题包含4个维度：

| 维度 | 说明 |
|------|------|
| 切入角度 | 从六大角度中选择一个：数据冲击/对比反差/因果追溯/影响推演/方法拆解/趋势预判 |
| 目标受众 | 行业从业者/投资者/普通消费者/学习者/媒体创作者 |
| 内容形式建议 | 图文长文/短视频/图文卡片/系列内容/直播访谈 |
| 关联事实 | 关联的核心事实编号 |

选题必须提供增量价值——不能只是复述事实，必须提供原文中没有直接阐述的视角。

### 步骤5：合规校验

**必须遵循 `references/compliance-rules.md` 中的合规规则。**

逐项自检：

| 检查项 | 标准 |
|--------|------|
| 事实可追溯 | 每条事实有原文定位 |
| 数据不篡改 | 提取数据与原文一致 |
| 不虚构 | 无原文中不存在的信息 |
| 观点不混入事实 | 观点标注为观点 |
| 引用完整 | 引用片段未截断、未修改 |
| 风险项识别 | 敏感/未证实/主观内容已标注 |
| 选题有据 | 每条选题关联至少一条事实 |

### 步骤6：素材包输出

将内容组装为素材包JSON，调用导出脚本生成MD + HTML预览。

素材包JSON格式：
```json
{
  "source": "素材来源",
  "mode": "standard",
  "word_count": 1500,
  "density_score": 0.72,
  "timestamp": "2026-01-01T00:00:00",
  "summary": "一段摘要文字",
  "facts": [
    {"content": "事实内容", "location": "第X段，第Y句", "quote": "原文片段"}
  ],
  "topics": [
    {"title": "选题标题", "angle": "切入角度", "audience": "目标受众", "form": "内容形式", "related_facts": "关联事实#1,#3"}
  ],
  "quotes": [
    {"text": "原文引用片段", "location": "第X段，第Y句"}
  ],
  "risks": [
    {"type": "风险类型", "content": "风险内容", "suggestion": "处理建议"}
  ]
}
```

调用导出脚本：
```bash
python scripts/export_pack.py --content pack.json --template-md assets/content-pack-template.md --template-html assets/preview-template.html --output-dir ./output
```

输出：
- `content-pack.md` — Markdown格式素材包
- `preview.html` — HTML预览页面（含模块折叠展开交互）

**弹性规则**：`quotes` 和 `risks` 数组为空时，MD和HTML中对应模块整块省略。

### 步骤7：校验确认

调用校验脚本验证结构完整性：

```bash
python scripts/validate_pack.py --pack output/content-pack.md --quotas analysis.json
```

校验项：
- 结构完整性（必需模块齐全）
- 占位符残留（无 `{xxx}` 残留）
- 引用可追溯（每条事实有原文定位）
- 配额合规（事实/选题数量在配额范围内）
- 选题维度完整（每条选题含4维度）

如有错误，修正后重新生成。

---

## 文件结构

```
note-intel/
├── SKILL.md                        # 本文档
├── references/
│   ├── extraction-guide.md         # 信息提取指南
│   ├── topic-formulas.md           # 选题生成公式
│   └── compliance-rules.md         # 合规规则
├── scripts/
│   ├── analyze_material.py         # 输入处理 + 评估定模
│   ├── validate_pack.py            # 素材包校验
│   └── export_pack.py              # MD + HTML 导出
├── assets/
│   ├── content-pack-template.md    # MD素材包模板
│   └── preview-template.html       # HTML预览模板
└── examples/
    ├── example-concise.md          # 精简模式示例
    ├── example-standard.md         # 标准模式示例
    └── example-deep.md             # 深度模式示例
```

---

## 依赖

- Python 3.8+
- 零额外依赖（仅使用Python标准库）
- 跨平台支持：Linux / Mac / Windows
