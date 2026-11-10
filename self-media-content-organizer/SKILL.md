---
name: self-media-content-organizer
description: 自媒体内容整理中台。用于把文章、报告、网页、采访、帖子或多份资料转化为结构化、可核对、可继续创作的内容素材包，并按微信公众号、小红书、知乎、视频号、抖音、朋友圈等平台适配成文案、图文卡片、视频脚本和视觉制作清单。支持来源登记、事实/观点/推断分层、图片资产分层、整理图规划、AI示意图规则、选题评分、多素材合并和冲突对比。绝不虚构，不把AI图当证据，不为满足数量强行填充。
agent_created: true
version: 1.0.2
display_name: 自媒体内容整理中台
display_name_en: Self-Media Content Organizer
description_zh: 自媒体内容整理中台。用于把文章、报告、网页、采访、帖子或多份资料转化为结构化、可核对、可继续创作的内容素材包，并按微信公众号、小红书、知乎、视频号、抖音、朋友圈等平台适配成文案、图文卡片、视频脚本和视觉制作清单。支持来源登记、事实/观点/推断分层、图片资产分层、整理图规划、AI示意图规则、选题评分、多素材合并和冲突对比。绝不虚构，不把AI图当证据，不为满足数量强行填充。
description_en: A cross-platform content operations hub for self-media. Converts articles, reports, web pages, interviews, posts or multiple sources into structured, verifiable content packs that are ready for further creation, then adapts them for WeChat Official Accounts, Xiaohongshu, Zhihu, WeChat Channels, Douyin and Moments as copy, carousel cards, video scripts and visual production checklists. Covers source registration, layering of facts, opinions and inferences, image asset layering, infographic planning, AI illustration rules, topic scoring, multi-source merging and conflict comparison. Never fabricates content, never treats AI images as evidence, and never pads output to meet quotas.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  contact: icoolkj@163.com
  qq: "594047667"
---

# 自媒体内容整理：跨平台内容中台

## 1. 定位与最高原则

将每份原始资料先整理为一份平台无关的“事实底座”，再按目标平台重新组织表达。平台可以改变标题、长度、语气、结构和视觉比例，但不能改变事实、限定词、来源口径和证据边界。

遵守以下不可覆盖规则：

- **零虚构**：原文没有的数据、因果、人物动机、结论、来源和图片含义，不得补写。
- **证据优先**：每条事实必须回到 `source_id`、段落/句子和原文摘录。
- **表达分层**：事实、原文观点、编辑推断、待核查问题、平台化建议必须分开。
- **弹性输出**：配额下限只是建议；证据不足时少输出或为空，不凑数、不重复、不把观点伪装成事实。
- **视觉可追溯**：原文图片、基于事实制作的整理图、AI生成示意图必须分开记录。
- **AI图不作证据**：AI生成图片不能证明真实事件、人物、产品、数据或现场。
- **先方案后成品**：用户未明确要求生成视觉成品时，先给视觉资产方案和卡片结构，不擅自批量生成图片。

## 2. 触发条件与交付层级

用户提供文章、报告、网页、采访、帖子、PDF/文档、图片或多份资料，并要求整理、提炼、做选题、改写平台内容、做图文、做卡片、做脚本、识别图片或生成视觉资产时使用。

**边界**：只做单一平台无关的素材包、不需要任何平台适配或视觉资产时，用 `note-intel`；只要小红书 3:4 轮播卡片、可编辑视觉工作台和发布流程时，用 `xhs-content-studio`。本 Skill 覆盖"多平台适配 + 视觉资产规划"，不负责小红书卡片成品渲染。

默认交付层级：

1. **通用内容素材包**：事实底座、证据链、来源、风险、图片索引和可创作方向。
2. **平台适配包**：只有用户指定平台，或明确要求发布文案/脚本时生成。
3. **视觉制作包**：只有用户要求配图、卡片、封面、信息图或图片成品时生成；先确认视觉方向，除非需求已经明确到可直接执行。

若用户只要求润色原文，不要自动执行完整情报流程；若用户要求核对、整理、提炼或再创作，则执行完整流程。

## 3. 输入登记与素材边界

为每份输入建立唯一 `source_id`，记录来源类型、标题/URL/文件名、作者/机构、发布日期、读取时间、完整性和版权可用性。网页正文不完整、付费墙、图片文字无法读取、扫描件OCR不可靠时，显式记录限制，不猜测缺失内容。

对 URL、文件或粘贴文本运行。推荐使用统一入口，不要手动衔接中间文件：

```bash
python scripts/run_pipeline.py --input <URL|文件路径|文本> --output-dir ./pipeline-output
```

流水线按顺序保存 `analysis.json`、`clean_text.txt`、`candidates.json`、`risks.json` 和 `pipeline.json`，并将阶段拆开记录：`preprocess`（预处理）、`model_organization`（模型/人工整理）、`topic_planning`（选题策划）、`platform_creation`（平台创作）、`publication_gate`（发布门禁）。每一步都有 `success/failed/awaiting_input/blocked` 状态；分析失败时停止后续步骤，候选与风险步骤失败时保留已完成产物并返回 `partial_failure`。它不会把规则候选自动升级为已核实事实。

输入解析规则：普通文本使用 UTF-8；PDF 使用 `pypdf` 或 `pdftotext`；DOCX 读取文档 XML；PNG/JPEG/TIFF 等图片使用本机 `tesseract` OCR（若未安装则明确失败，不假装完成视觉识别）；网页使用标准库抓取静态 HTML。需要 JavaScript、登录、付费墙或反爬验证的网页会标记不完整或失败，不能把抓取结果当作完整原文。

分析器仍可单独运行，用于只需要分析卡的场景：

```bash
python scripts/analyze_material.py --input <URL|文件路径|文本> --output analysis.json
```

## 4. 动态定模与事实底座

参考 `analysis.json` 的篇幅、密度、候选事实和 `quotas`。默认模式：精简 `<800` 字、标准 `800–3000` 字、深度 `>3000` 字；密度可上下调整一级，但篇幅长不等于事实多。

遵循：

1. 先计算可独立成立且可定位的事实候选数。
2. `max` 是硬上限；`min` 是软提示。
3. 没有足够证据时，输出真实数量并在 `limitations` 解释。
4. 事实不足时，不用观点、推断或重复句子补位。
5. 每条事实最多支撑 1–2 个明显不同的选题；没有创作增量就不生成选题。

流水线已自动运行候选提取器；若只需单独运行，输入应使用流水线写出的 `clean_text.txt`：

```bash
python scripts/extract_candidates.py --input <清洗后文本文件> --quota <事实上限>
```

每条事实至少包含 `id`、`claim`、`evidence_type`、`status`、`confidence`、`source_ids`、`location`、`quote` 和 `qualifiers`。单一来源默认 `status=reported`，只有有独立来源或原文明确核验时才使用 `verified`。

将原文中的“认为、建议、应该、最好”等归入 `viewpoints`；将基于事实的延伸放入 `inferences`，注明依据和“非原文事实”；将发布前必须补齐的内容放入 `verification_gaps`。

## 5. 图片与视觉资产分层

读取 `references/visual-assets.md`。素材包中不要把所有图片都叫“配图”，至少分为：

### 5.1 原文图片 `source_images`

来自原文、网页、报告或采访的图片、截图、图表和照片。记录来源、页面位置、图片实际展示内容、关联事实、原始URL、版权状态和建议用途。原文存在不等于可以公开发布；版权未知时标为“仅供研究/发布前确认”。

### 5.2 整理图 `derived_visuals`

根据已核对事实重新制作的对比图、时间线、流程图、影响链、数据卡片、表格或信息图。必须列出使用的事实 ID、数据、计算、来源标注和证据边界。数据映射、比例、单位和数字优先使用确定性排版/图表方式，不使用AI凭空绘制。

### 5.3 AI示意图 `generated_visuals`

只用于封面氛围、抽象概念、非真实场景或装饰性视觉。必须写明“AI生成示意图，不代表真实事件或真实人物”。不得生成假新闻现场、假采访、假产品实拍、假数据图表或伪造证据。

### 5.4 平台成品 `card_plan` / `visual_plan`

记录平台、比例、尺寸、页数、每页文字、每页事实 ID、图片类型、视觉层级、来源标注和发布前检查项。默认先输出方案；用户确认后再生成成品。

## 6. 通用选题与图文策划

参考 `references/topic-formulas.md`。每个选题包含：标题、角度、目标受众、内容形式、关联事实 ID、价值增量、开头钩子、结构大纲、视觉计划、CTA/下一步和证据边界。需要给选题排序时用 `python scripts/score_topics.py --pack pack.json` 打分，人工判断优先于分数。

图文策划要做到“可制作”：

- 封面只表达主题、冲突或阅读收益，不塞完整结论。
- 每张卡片/每段只承担一个主要信息。
- 数据卡注明“据原文整理”和来源位置。
- 无明确因果时，使用“可能原因/材料提出的解释/待核查”而不是确定因果。
- `outline` 中为每张卡片关联事实 ID；需要补采的数据放入核查清单。

## 7. 平台适配器

读取 `references/platform-adapters.md`。先复用通用内容素材包，再按平台适配；不得在适配时新增无来源事实。

支持以下默认适配器：

- **微信公众号**：标题、导语、完整正文、小标题、数据图位置、引用、结尾互动；强调上下文、逻辑和来源。
- **小红书**：封面标题、6–9张卡片、短段落、收藏价值、卡片事实 ID；默认3:4竖版，信息视觉化。
- **知乎**：问题式标题、先给结论、背景、证据、机制、反例、争议和边界；避免只制造情绪。
- **视频号/抖音**：15/30/60秒口播、前3秒钩子、分镜、字幕事实、画面建议、结尾互动；口语化但保留限定词。
- **朋友圈/社群**：一句话观点、3行摘要、一张整理图、来源和互动问题；不直接搬运全文。

用户未指定平台时，输出通用包，并推荐 1–3 个适合方向；不要擅自默认小红书风格。

## 8. 平台与视觉规格

按目标平台选择视觉表达，不改变事实：

| 平台 | 默认视觉方向 |
|---|---|
| 微信公众号 | 横图、长图、正文数据图、流程图 |
| 小红书 | 3:4竖版，多页卡片 |
| 知乎 | 横图、解释图、结构图、长图 |
| 视频号/抖音 | 9:16竖版画面、字幕安全区 |
| 朋友圈 | 1:1或4:3分享图 |

精确数字、时间、价格、表格、统计图和长文字优先采用确定性布局或图表路线；概念封面和氛围图才考虑AI生成。生成任何文字图片后，检查关键数字、日期、人名、机构名、单位和来源标注。

视觉与平台记录必须显式写入 `status`：`plan → generated → checked → approved`，失败写 `failed`。只有有真实 `output_path`、事实引用和 `checks.passed=true` 时才能进入 `approved`。使用以下门禁检查，不要把 `card_plan` 或 `generated_visuals` 的存在误认为成品已经生成：

```bash
python scripts/validate_production_artifacts.py --pack pack.json
```

## 9. 风险、版权与发布检查

流水线已自动运行风险扫描；若只需单独运行，输入应使用流水线写出的 `clean_text.txt`：

```bash
python scripts/scan_risks.py --input <清洗后文本文件> --source-count 1
```

至少识别：预测/未证实、时效、单一来源、利益相关、敏感话题、主观观点、样本/口径缺失、因果过度推断、图片版权未知、AI误导风险。风险不删除事实，只说明发布时如何标注、补证或改写。

发布前检查：

- 事实可回到原文；
- 数字、单位、时间和限定词未改变；
- 平台标题没有把可能说成确定；
- 图片类型和来源标注正确；
- 原文图片有版权判断；
- 整理图没有混入未证实数字；
- AI示意图没有冒充真实照片或证据；
- 每张卡片、每个视频关键段落都有事实依据；
- 选题、图文和脚本没有超过素材能支持的结论。

## 10. 组装、校验与多素材

推荐 JSON 契约见 `references/pack-schema.md`。扩展后的视觉字段和平台字段见 `references/visual-assets.md` 与 `references/platform-adapters.md`。

```bash
python scripts/run_pipeline.py --input <原始资料> --output-dir ./pipeline-output \
  --pack pack.json --template-md assets/content-pack-template.md \
  --template-html assets/preview-template.html --formats md,html,json

# 也可单独执行以下门禁：
python scripts/export_pack.py --content pack.json \
  --template-md assets/content-pack-template.md \
  --template-html assets/preview-template.html \
  --output-dir ./output --formats md,html,json
python scripts/validate_json_pack.py --pack output/content-pack.json
python scripts/validate_pack.py --pack output/content-pack.md \
  --quotas analysis.json --source original_text.txt
```

多素材先分别建立事实底座，再合并。合并器会按 `claim` 去重、重映射事实 ID 和 source_id，支持 `related_facts` 数组；合并后必须重新执行 JSON 校验：

```bash
python scripts/merge_packs.py --packs pack_a.json pack_b.json --output merged.json
python scripts/validate_json_pack.py --pack merged.json

# 质量评估（真实人工标注集接入后运行）
python scripts/evaluate_quality.py --gold evaluation/seed_gold.jsonl --predictions predictions.jsonl
python scripts/compare_packs.py --pack-a pack_a.json --pack-b pack_b.json
```

精确重复才去重；数字、时间、统计口径、范围或因果不同，保留并列并写入 `conflicts`，不能平均、拼接或生成“综合数字”。

## 11. 默认输出顺序

默认交付：

1. 一句话结论与素材边界；
2. 来源登记和分析卡；
3. 内容摘要；
4. 核心事实与证据；
5. 原文观点；
6. 可标注推断；
7. 原文图片索引与版权状态；
8. 选题和通用图文方向；
9. 推荐的平台适配方向；
10. 风险、核查缺口和下一步动作。

只有有内容才输出 `source_images`、`derived_visuals`、`generated_visuals`、`card_plan`、`risks`、`conflicts` 等模块；不输出“暂无”占位块。

## 12. 资源导航

- `references/pack-schema.md`：通用数据契约及平台/视觉字段。
- `references/visual-assets.md`：原文图片、整理图、AI示意图、版权和视觉检查。
- `references/platform-adapters.md`：微信公众号、小红书、知乎、视频号/抖音、朋友圈适配规则。
- `references/extraction-guide.md`：事实识别、定位和数据精度。
- `references/topic-formulas.md`：选题、图文结构和受众匹配。
- `references/compliance-rules.md`：风险、引用和发布前核查。
- `references/quality-evaluation.md`：人工标注集格式、双人标注和质量指标。
- `scripts/`：分析、候选提取、风险扫描、导出、校验、评分、合并和对比。

Python 3.8+，脚本仅使用标准库。Skill 本身不替代平台规则、版权审核、事实核查或法律审核。

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
