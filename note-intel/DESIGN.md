# NoteIntel 架构设计文档

> 自媒体内容情报与图文策划 Skill
> 版本：v0.1（设计阶段）

---

## 1. 项目概述

### 1.1 定位

把一篇文章/资料/网页转化为结构化、可核对、可继续创作的内容素材包。

### 1.2 核心价值

NoteIntel 不是"生成器"，而是"情报官"——先理解素材的深度和密度，再决定提取多少、生成多少，绝不虚构、绝不强制填充。

### 1.3 设计哲学

**弹性约束，而非固定模板**——先判断素材，再决定输出规模。不预设固定数量的输出条目，而是根据素材的篇幅和信息密度动态决定。

### 1.4 与竞品差异

| 维度 | xhs-carousel-card-maker | NoteIntel |
|------|------------------------|-----------|
| 核心价值 | 把选题变成漂亮的图文卡片 | 把素材变成可核对的结构化情报 |
| 输入 | 选题 + 风格偏好 | 文章/资料/网页（原始素材） |
| 输出 | HTML卡片 + 文案包 | 结构化内容素材包（MD + HTML预览） |
| 弹性 | 固定5张卡片 | 篇幅+密度双维度动态决定输出规模 |
| 合规 | 违禁词替换表 | 风险项识别 + 不虚构原则 + 引用可追溯 |

---

## 2. 执行模式规则

### 2.1 篇幅初判

| 篇幅 | 初判模式 | 事实配额 | 选题配额 |
|------|----------|----------|----------|
| < 800字 | 精简 | 2-4 | 1-2 |
| 800-3000字 | 标准 | 4-8 | 3-5 |
| > 3000字 | 深度 | 6-12 | 4-7 |

### 2.2 信息密度评估指标

| 指标 | 计算方法 | 权重 |
|------|----------|------|
| 独立事实数 | 统计含数字/百分比/专有名词的句子数 | 高 |
| 数据存在性 | 是否包含具体数字、统计、对比 | 中 |
| 案例存在性 | 是否包含引号引用、具体案例描述 | 中 |
| 方法存在性 | 是否包含步骤、流程、方法论关键词 | 中 |
| 重复观点比 | 句子级 Jaccard 相似度去重率 | 低（反向） |
| 主题分散度 | 段落关键词提取，计算主题独立性 | 高 |
| 可核验结论 | 含"因此/所以/表明/证明"等结论词的句子数 | 中 |
| 创作角度数 | 基于关键词分类估算可切入角度 | 高 |

### 2.3 密度修正规则

```
密度分 = 加权综合评分（0-1）
篇幅初判：精简 / 标准 / 深度
密度修正：密度分 > 0.7 可上调一级；密度分 < 0.3 可下调一级
最终模式 = 篇幅初判 ± 密度修正
```

### 2.4 各模块独立数量规则

| 模块 | 数量规则 |
|------|----------|
| 摘要 | 固定1条 |
| 核心事实 | 由配额表动态决定 |
| 创作选题 | 由配额表动态决定 |
| 原文引用 | 有才输出，无则整块省略 |
| 风险提示 | 有才输出，无则整块省略 |

---

## 3. 模块结构

### 3.1 流程概览

```
素材输入 → 评估定模 → 信息提取 → 选题生成 → 合规校验 → 素材包输出 → 校验确认
```

### 3.2 各模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| 素材输入 | 接收URL/文件/文本，预处理为纯文本 | URL、文件路径、或粘贴文本 | 清洗后的纯文本 + 元信息 |
| 评估定模 | 篇幅+信息密度双维度评估，决定执行模式 | 纯文本 + 字数 | 模式判定 + 配额表（JSON） |
| 信息提取 | 提取核心事实，每条标注原文定位 | 纯文本 + 配额表 | 结构化事实列表 |
| 选题生成 | 基于事实生成创作选题 | 事实列表 + 配额表 | 选题列表（含4维度信息） |
| 合规校验 | Agent自检：不虚构、引用可追溯、风险项识别 | 事实+选题+引用+风险 | 校验通过的素材包内容 |
| 素材包输出 | 组装MD + HTML预览 | 素材包内容 | content-pack.md + preview.html |
| 校验确认 | 脚本校验结构完整性 | 生成的文件 | 校验结果 |

### 3.3 选题维度

每个创作选题包含以下4个维度：

| 维度 | 说明 |
|------|------|
| 切入角度 | 从什么角度切入这个选题 |
| 目标受众 | 这个选题适合什么受众群体 |
| 内容形式建议 | 建议用图文/视频/长文等形式 |
| 关联事实 | 这个选题关联了哪些核心事实 |

---

## 4. 文件架构

```
note-intel/
├── SKILL.md                        # 主控文档（工作流 + 设计哲学 + 模式规则）
├── references/
│   ├── extraction-guide.md         # 信息提取指南（事实识别标准、原文定位方法）
│   ├── topic-formulas.md           # 选题生成公式（角度挖掘、受众匹配）
│   └── compliance-rules.md         # 合规规则（风险识别、不虚构原则、引用规范）
├── scripts/
│   ├── analyze_material.py         # 输入处理 + 评估定模（输出配额表JSON）
│   ├── validate_pack.py            # 文案包校验（结构完整性、引用可追溯、占位符残留）
│   └── export_pack.py              # MD + HTML 双格式导出
├── assets/
│   ├── content-pack-template.md    # MD素材包弹性模板
│   └── preview-template.html       # HTML预览模板（模块折叠展开交互）
└── examples/
    ├── example-concise.md          # 精简模式示例输出
    ├── example-standard.md         # 标准模式示例输出
    └── example-deep.md             # 深度模式示例输出
```

### 4.1 各文件职责

| 文件 | 职责 | 依赖 |
|------|------|------|
| SKILL.md | 主控文档，定义工作流、设计哲学、模式规则、Agent指令 | 无 |
| extraction-guide.md | 信息提取的领域知识：事实识别标准、数据提取规则、原文定位方法 | 无 |
| topic-formulas.md | 选题生成的领域知识：角度挖掘方法、受众匹配策略、内容形式判断 | 无 |
| compliance-rules.md | 合规领域知识：风险项识别标准、不虚构原则、引用规范 | 无 |
| analyze_material.py | 输入处理（URL抓取/文件读取/清洗）+ 评估（字数+密度+配额表） | urllib, html.parser（标准库） |
| validate_pack.py | 校验素材包结构完整性、引用可追溯性、占位符残留 | 无（纯标准库） |
| export_pack.py | 将Agent生成的内容组装为MD + HTML双格式输出 | 无（纯标准库） |
| content-pack-template.md | MD素材包的弹性模板骨架 | 无 |
| preview-template.html | HTML预览页面模板，含模块折叠展开交互 | 无（自包含） |

---

## 5. 接口契约

### 5.1 analyze_material.py

**输入**：
```bash
python analyze_material.py --input <URL|文件路径|文本> [--output <输出路径>]
```

**输出**（JSON格式，写入 stdout 或指定文件）：
```json
{
  "mode": "standard",
  "word_count": 1500,
  "source_type": "url",
  "source": "https://example.com/article",
  "clean_text": "清洗后的纯文本...",
  "density_score": 0.72,
  "density_factors": {
    "fact_count": 6,
    "has_data": true,
    "has_case": true,
    "has_method": false,
    "repeat_ratio": 0.15,
    "topic_independence": 0.80,
    "verifiable_conclusions": 2,
    "creation_angles": 4
  },
  "quotas": {
    "summary": 1,
    "core_facts": 5,
    "topics": 4,
    "quotes": "auto",
    "risks": "auto"
  }
}
```

### 5.2 export_pack.py

**输入**：
```bash
python export_pack.py --content <素材包JSON> --template-md <MD模板路径> --template-html <HTML模板路径> --output-dir <输出目录>
```

**输出**：
- `content-pack.md` — Markdown格式素材包
- `preview.html` — HTML预览页面

### 5.3 validate_pack.py

**输入**：
```bash
python validate_pack.py --pack <MD文件路径>
```

**输出**（JSON格式）：
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "checks": {
    "structure_complete": true,
    "no_placeholders": true,
    "quotes_traceable": true,
    "facts_within_quota": true,
    "topic_has_dimensions": true,
    "topic_fact_references": true,
    "summary_length": true,
    "topic_title_uniqueness": true,
    "facts_have_quotes": true,
    "no_fabricated_data": true,
    "optional_section_content": true,
    "optional_sections": {
      "原文引用": true,
      "风险提示": true
    }
  }
}
```

---

## 6. 工作流定义

```
步骤1：素材输入
  → Agent 接收 URL/文件/文本
  → 调用 analyze_material.py --input <素材>
  → 获取配额表JSON

步骤2：评估定模确认
  → Agent 审查配额表（模式、密度分、配额）
  → 确认模式判定合理

步骤3：信息提取
  → Agent 按配额表提取核心事实
  → 每条事实标注原文定位（段落编号或引用片段）
  → 不虚构、不补充原文中没有的信息

步骤4：选题生成
  → Agent 按配额表生成创作选题
  → 每条选题包含4维度：切入角度、目标受众、内容形式建议、关联事实
  → 选题必须基于已提取的核心事实

步骤5：合规校验
  → Agent 自检：
    - 不虚构：所有事实可在原文中找到
    - 引用可追溯：每条引用标注原文位置
    - 风险项识别：识别可能的合规风险（敏感话题、未经证实的数据等）

步骤6：素材包输出
  → Agent 将内容组装为素材包JSON
  → 调用 export_pack.py 生成 MD + HTML预览

步骤7：校验确认
  → 调用 validate_pack.py 校验结构完整性
  → 如有错误，Agent 修正后重新生成
```

---

## 7. 模板设计

### 7.1 content-pack-template.md

```markdown
# 内容素材包

> 来源：{source}
> 模式：{mode} | 字数：{word_count} | 密度分：{density_score}
> 生成时间：{timestamp}

## 摘要

{summary}

## 核心事实

{core_facts}

## 创作选题

{topics}

## 原文引用

{quotes}

## 风险提示

{risks}
```

**弹性规则**：
- `原文引用` 模块：有内容才输出，无则整块省略
- `风险提示` 模块：有内容才输出，无则整块省略
- `核心事实` 和 `创作选题` 条数由配额表决定

### 7.2 preview-template.html

**设计方向**：
- 布局：单栏信息流，各模块卡片式呈现
- 交互：各模块可点击折叠/展开
- 视觉：简洁克制，信息密度高，深色主题
- 顶部：显示模式标识（精简/标准/深度）和密度分
- 自包含：零外部依赖，纯HTML/CSS/JS

---

## 8. 合规规则

### 8.1 不虚构原则

- 所有核心事实必须可在原文中找到对应内容
- 不补充原文中没有的信息、数据或结论
- 如需推断，必须标注为"推断"而非"事实"

### 8.2 引用可追溯

- 每条原文引用标注来源位置（段落编号或引用片段）
- 引用内容必须与原文一致，不得篡改

### 8.3 风险项识别

- 敏感话题：政治、宗教、种族等敏感内容
- 未经证实的数据：原文中标注为"估计""大约""可能"的数据
- 主观判断：原文中的个人观点，需标注为"观点"而非"事实"

---

## 9. 依赖说明

| 脚本 | 依赖 | 说明 |
|------|------|------|
| analyze_material.py | urllib, html.parser | 均为Python标准库，零额外依赖 |
| validate_pack.py | 无 | 纯标准库 |
| export_pack.py | 无 | 纯标准库 |

**跨平台支持**：Linux / Mac / Windows

---

## 10. 版本规划

| 版本 | 内容 | 状态 |
|------|------|------|
| v0.1 | 架构设计文档 | 当前 |
| v0.2 | SKILL.md + references/ + scripts/ + assets/ + examples/ 编码 | 待开始 |
| v0.3 | 端到端测试 + 修复 | 待开始 |
| v1.0 | 正式发布 | 待开始 |
