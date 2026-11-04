---
name: xhs-content-studio
description: 事实驱动的小红书内容与轮播卡片工作室。用于把原始文字、报告、网页、PDF、DOCX 或图片整理成可追溯的事实素材包，并根据文章事实与信息密度生成自适应页数的3:4卡片文案、可编辑视觉工作台和PNG导出；支持在用户明确确认后通过浏览器辅助发布到小红书。
agent_created: true
version: 1.0.0
display_name: 小红书内容与卡片工作室
display_name_en: XHS Content Studio
description_zh: 事实驱动的小红书内容与轮播卡片工作室。用于把原始文字、报告、网页、PDF、DOCX 或图片整理成可追溯的事实素材包，并根据文章事实与信息密度生成自适应页数的3:4卡片文案、可编辑视觉工作台和PNG导出；支持在用户明确确认后通过浏览器辅助发布到小红书。
description_en: A fact-driven Xiaohongshu content and carousel card studio. Turns raw text, reports, web pages, PDF, DOCX or images into a traceable fact pack, then generates adaptive-length 3 by 4 carousel copy, an editable visual workbench and PNG export based on article facts and information density. Supports browser-assisted publishing to Xiaohongshu only after explicit user confirmation.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
---

# 小红书事实驱动内容与卡片工作室

## 1. 核心定位

把“内容情报底座”和“小红书卡片生产”合成一条工作流：

```text
原始文字/报告/网页/文件
  → 来源登记与预处理
  → 候选事实与风险扫描
  → 模型/人工整理 content-pack JSON
  → JSON 契约与引用门禁
  → 小红书标题与正文
  → 按内容自适应页数的 3:4 轮播卡片
  → 可编辑 HTML 工作台
  → 用户确认后导出 PNG / 辅助发布
```

JSON 素材包是唯一事实源。标题、正文、卡片、图片和平台文案都只能改变表达，不能改变数字、时间、范围、限定词、来源或证据边界。

## 最短使用路径

用户只需提供原始文字、报告或网页，并说明希望发布到小红书。先完成预处理，再由模型/人工整理 `content-pack.json`，最后运行：

```bash
python scripts/run_xhs_pipeline.py \
  --input <原始资料> \
  --pack content-pack.json \
  --output-dir ./xhs-output
```

最终重点查看 `xhs-output/xhs-copy-pack.md` 和 `xhs-output/xhs-card-studio.html`；前者用于审阅事实与文案，后者用于编辑卡片并导出 `P1–PN` PNG。

## 2. 不可覆盖原则

- 不虚构原文没有的数据、因果、人物动机、用户反馈、收益或案例。
- 每条事实必须有 `id`、`source_ids`、`location` 和 `quote`。
- 把事实、原文观点、编辑推断、风险和待核查问题分开。
- 单一来源事实默认 `reported`，不能无依据标记为 `verified`。
- 标题可以有传播性，但不能把“可能、预计、据称、报告认为”写成确定结论。
- 没有足够证据时少做卡片、少做选题，不用重复或观点凑数。
- 原文图片、整理图和 AI 示意图必须分开；AI 图不能作为事实证据。
- 用户未明确要求发布时，只生成发布包，不打开发布提交流程。

## 3. 输入与工作流

### 3.1 预处理

用户提供原始文字、报告、网页、PDF、DOCX、图片或多来源材料时，先运行：

```bash
python scripts/run_xhs_pipeline.py \
  --input <原始资料> \
  --output-dir ./xhs-output
```

输入能力：普通文本、静态网页、PDF、DOCX、图片 OCR 和扫描件 PDF OCR。需要 JavaScript、登录、付费墙或反爬验证的网页必须记录为不完整或失败，不能假装拿到了全文。

预处理产物包括：

- `analysis.json`：篇幅、输入类型、密度和限制
- `clean_text.txt`：清洗后的文本
- `candidates.json`：规则提取候选，不等同于事实
- `risks.json`：风险初筛，不等同于最终发布判断
- `pipeline.json`：每一步状态、错误和输出路径

### 3.2 整理事实素材包

根据 `references/pack-schema.md` 生成 `content-pack.json`。至少整理：

- `sources`
- `facts`
- `viewpoints`
- `inferences`
- `verification_gaps`
- `risks`
- `topics`
- `source_images`

事实字段最低要求：`id`、`claim`、`source_ids`、`location`、`quote`、`confidence`、`status`。选题必须通过 `related_facts` 关联事实。

先执行门禁：

```bash
python scripts/validate_json_pack.py --pack content-pack.json
```

结构错误会阻止生产；语义支持度、版权和外部核验问题会作为风险保留，不能用一个 `valid=true` 代替事实核查。

### 3.3 生成小红书创作包

素材包通过 JSON 门禁后运行：

```bash
python scripts/build_xhs_from_pack.py \
  --pack content-pack.json \
  --output-dir ./xhs-output
```

或一次执行预处理、门禁和小红书产物：

```bash
python scripts/run_xhs_pipeline.py \
  --input <原始资料> \
  --pack content-pack.json \
  --output-dir ./xhs-output
```

输出：

- `xhs-copy-pack.md`：标题、自适应页数卡片文案、小红书正文、来源、风险和话题
- `xhs-card-studio.html`：单文件、离线可打开的 3:4 卡片工作台

## 4. 小红书内容结构

### 标题

生成 5 个不同角度的标题，默认每个不超过 20 个汉字：

1. 数字痛点型
2. 受众点名型
3. 前后反差型
4. 清单/模板型
5. 实测拆解型

如果原始资料没有可靠数字，不得为了套公式凭空添加数字。

### 自适应页数轮播

页数不固定。根据事实数量、文章篇幅、主题覆盖度、风险和核查缺口决定，短文少页，长文多页；默认建议控制在 4–12 页，确有必要时可以继续扩展。不得为了凑页数重复事实或加入文章没有的内容。

常见结构是：

1. **封面**：主题、冲突或阅读收益，不塞完整结论
2. **事实卡片组**：每页承载一组同主题事实，保留事实 ID、来源和引用
3. **边界与核查**：限定词、风险、争议或待核查问题
4. **复盘互动**：来源提示、核对清单和评论问题

如果原文存在真实的前后变化或多方案差异，优先使用左右对比/前后对比布局；没有对比证据时不要强行制作“旧做法 vs 新做法”。

每张卡片只承担一个主要信息。卡片文案应保留 `fact_id` 与来源信息，方便回看和修改。

### 正文

小红书正文至少包含：

- 一个不夸大的开头
- 3条以内核心信息
- “据原文整理”或相应来源说明
- 风险/时间范围/核查边界
- 一个自然互动问题
- 8个左右相关话题标签，但不使用违规导流词

## 5. 视觉卡片规范

默认使用用户偏好的 **3:4 竖版**，中文必须清晰、不乱码。比较内容优先采用左右对比或前后对比布局；精确数据优先采用确定性排版，不让 AI 绘制数字图表。

卡片工作台提供：

- 黑曜、绯红、翡翠、昼白四套主题
- 高斯模糊调节
- 玻璃透明度调节
- 中英双语切换
- 文字直接编辑
- 单卡或全部卡片导出 900×1200 PNG

卡片生产状态应按以下顺序记录：

```text
plan → generated → checked → approved
```

不要把 HTML 工作台或 `card_plan` 的存在误认为图片已经生成。交付前必须人工/模型确认 `plan → generated → checked → approved` 状态，并确认工作台中实际导出了 PNG。

## 6. 发布到小红书

本 Skill 支持“用户确认后辅助发布”，不支持未经确认的自动公开发帖。

发布前准备一个发布包：

- 选择后的标题
- 小红书正文
- 已导出的 3:4 PNG，按 P1–PN 排序
- 话题标签
- 来源/免责声明文本
- 发布检查结果

只有在以下条件全部满足后，才进入浏览器发布：

1. 用户明确指定“小红书发布”或类似请求；
2. JSON 素材包通过结构门禁；
3. 标题、正文、图片和来源已完成人工/模型复核；
4. 图片状态达到 `approved`；
5. 在最终点击“发布”前向用户展示准确的标题、正文、图片数量和可见范围，并获得明确确认。

浏览器发布阶段可以打开小红书创作页面、上传图片、填写标题和正文、选择话题并停在最终提交前。登录、验证码和最终公开发布需要用户接管或明确确认；不要绕过验证码、风控或平台限制。

## 7. 参考资料

按需阅读：

- `references/pack-schema.md`：事实素材包字段契约
- `references/copywriting-formulas.md`：小红书标题与轮播结构
- `references/frontend-design-system.md`：3:4 卡片、毛玻璃和中文排版
- `references/compliance-rules.md`：风险、来源和发布核查
- `references/extraction-guide.md`：事实提取和证据定位
- `references/quality-evaluation.md`：事实支持、选题独立性和风险评估
- `scripts/`：预处理、事实门禁、小红书文案/卡片生成和 HTML/PNG 质量校验

Skill 不替代事实核查、版权审核、平台规则或法律审核。

---

## 关于

| 项目 | 信息 |
|------|------|
| 出品 | icoolkj |
| 官网 | https://icoolkj.com |
| 邮箱 | icoolkj@163.com |
| QQ | 594047667 |
| 许可 | MIT License |

Copyright © 2026 icoolkj.com
