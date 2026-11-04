---
name: note-intel
description: 自媒体内容情报与图文策划 Skill。用于把文章、报告、网页、采访、帖子或多份资料转化为结构化、可核对、可继续创作的内容素材包；支持动态篇幅与信息密度评估、事实/观点/推断分层、证据链、风险扫描、选题评分、多素材合并、冲突对比和图文策划。绝不虚构，不为满足数量强行填充。不用于多平台适配改写或视觉资产制作，那些场景使用 self-media-content-organizer；不用于小红书轮播卡片与发布，那类场景使用 xhs-content-studio。
agent_created: true
version: 1.0.2
display_name: 笔记情报：内容情报与图文策划
display_name_en: Note Intel Content Intelligence
description_zh: 自媒体内容情报与图文策划 Skill。用于把文章、报告、网页、采访、帖子或多份资料转化为结构化、可核对、可继续创作的内容素材包；支持动态篇幅与信息密度评估、事实/观点/推断分层、证据链、风险扫描、选题评分、多素材合并、冲突对比和图文策划。绝不虚构，不为满足数量强行填充。不用于多平台适配改写或视觉资产制作，那些场景使用 self-media-content-organizer；不用于小红书轮播卡片与发布，那类场景使用 xhs-content-studio。
description_en: A skill for converting articles, reports, web pages, interviews, posts or multiple sources into structured, verifiable content packs that are ready for further creation. Covers dynamic length and information density assessment, layering of facts, opinions and inferences, evidence chains, risk scanning, topic scoring, multi-source merging, conflict comparison and visual planning. Never fabricates content and never pads output to meet quotas. Not intended for multi-platform adaptation or visual asset production (use self-media-content-organizer), nor for Xiaohongshu carousel cards and publishing (use xhs-content-studio).
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
---

# NoteIntel：自媒体内容情报与图文策划

## 核心原则

把素材当作证据库，而不是写作提示词。先判断素材能支撑什么，再决定输出多少。

- **零虚构**：原文没有的数据、因果、人物动机、结论和来源，不得补写。
- **证据优先**：每条事实都必须能回到来源、段落/句子和原文摘录。
- **分层表达**：事实、原文观点、基于事实的推断、待核查问题必须分开。
- **弹性输出**：配额是“建议区间”；下限不是强制任务。证据不足时少输出、输出空列表并说明原因，不能凑数。
- **创作增量**：选题不是改写标题；必须说明新的切入角度、受众收益和可制作的图文结构。
- **不确定性可见**：保留“约、预计、可能、截至某日、据某机构”等限定词，不把预测写成已证实事实。

## 何时触发

用户提供文章、网页、PDF/文档、采访记录、社交媒体帖子、研究资料，要求做摘要、事实提炼、情报分析、选题、图文策划、素材整理、对比或多素材合并时使用。若用户只要求润色成稿，不要自动套用完整情报流程，除非需要核对来源。

## 何时不触发

- 用户要**同一素材多平台改写**（公众号/小红书/知乎/视频号差异化文案）、平台适配或视觉资产清单 → `self-media-content-organizer`。
- 用户要**小红书 3:4 轮播卡片、可编辑视觉工作台或发布** → `xhs-content-studio`。
- 用户要**CSV/Excel 数据分析报告** → `data-report-agent-skill` 或 `data-report-creator`。

本 Skill 的产出一律停在"素材包 + 选题与图文骨架"，不产出平台成品文案，也不产出卡片成品。

## 标准工作流

### 1. 建立素材登记

为每份输入建立 `source_id`，记录来源类型、标题/URL/文件名、作者或发布机构（若原文有）、发布日期、抓取/读取时间和可用性。网页抓取失败、正文不完整、付费墙或图片文字无法读取时，明确标注，不猜测缺失内容。

对文本调用：

```bash
python scripts/analyze_material.py --input <URL|文件路径|文本> --output analysis.json
```

分析器只负责清洗、篇幅、密度和候选配额；它不是事实核查器，不能替代人工/模型对原文的逐条回看。

### 2. 动态定模，而非硬凑数量

先参考 `analysis.json` 的 `word_count`、`density_score`、`density_factors` 和 `quotas`，再结合素材实际调整。默认模式：精简 `<800` 字、标准 `800–3000` 字、深度 `>3000` 字；密度可上下调整一级，但不要因为篇幅长就机械增加事实。

输出决策遵循：

1. 先计算“可独立成立且可定位”的事实候选数。
2. 事实数不足配额下限时，按真实数量输出，并在 `limitations` 说明“素材只支持 N 条”。
3. 每条事实最多支撑 1–2 个明显不同的选题；没有增量角度就不生成选题。
4. `max` 是硬上限；`min` 只是建议，不得为了达标制造观点、推断或重复事实。
5. 极短、纯观点或低密度素材可以输出 0 条核心事实，但必须提供 `source_summary`、`source_viewpoints` 或 `verification_gaps`，说明为什么不能提取事实。

### 3. 构建证据单元

先运行候选提取器，再逐条回看原文：

```bash
python scripts/extract_candidates.py --input <清洗后文本文件> --quota <事实上限>
```

每条事实至少包含：

- `id`：如 `F1`；
- `claim`：不添加原文没有的因果或范围；
- `evidence_type`：`data`、`event`、`quote`、`method`、`comparison`、`description`；
- `source_id`、`location`、`quote`；
- `confidence`：`high` / `medium` / `low`，依据来源明确性和原文限定词；
- `qualifiers`：约、预计、截至日期、样本范围、来源口径等；
- `status`：`reported`（原文报道）或 `verified`（有独立核验；默认不要写 verified）。

原文的主观判断放入 `viewpoints`，不能伪装成事实。基于事实的合理延伸放入 `inferences`，写明依据和“这不是原文事实”。原文缺少而创作前必须补齐的信息放入 `verification_gaps`。

定位从第 1 段、第 1 句开始；跨段事实列出全部位置。引用必须原样保留，截断用 `[...]`，不得改数字、单位、范围、时间和限定词。

### 4. 生成自媒体选题与图文骨架

参考 `references/topic-formulas.md`。每个选题至少包含：

- `title`：有明确冲突/问题/收益，不夸大；
- `angle`：数据冲击、对比反差、因果追溯、影响推演、方法拆解、趋势预判之一；
- `audience`、`form`；
- `related_facts`：事实 ID 数组，如 `['F1','F3']`；
- `value_add`：原文没有直接给出的编辑视角；
- `visual_plan`：建议做成什么对比图、时间线、流程图、卡片组或表格；
- `hook`、`outline`、`cta_or_next_step`；
- `evidence_boundary`：明确哪些能说、哪些只能说“可能/待核查”。

图文优先输出可执行策划，而不是只给标题：首图/封面信息、3–7 张卡片或段落顺序、每张卡片对应事实 ID、需要补采的数据和免责声明。涉及对比时优先使用左右并列或前后对照；中文图文必须建议清晰可读的文字层级，不能承诺未经生成和检查的视觉结果。

### 5. 风险与核查

```bash
python scripts/scan_risks.py --input <清洗后文本文件>
```

风险至少检查：未证实/预测、时效、单一来源、利益相关、敏感话题、主观观点、样本/口径缺失、因果过度推断。风险提示不删除事实，只说明发布时如何标注和需要补核查什么。

### 6. 组装、校验和导出

推荐 JSON 顶层结构见 `references/pack-schema.md`。导出前先过 JSON 契约校验，再导出：

```bash
python scripts/validate_json_pack.py --pack pack.json
python scripts/export_pack.py --content pack.json \
  --template-md assets/content-pack-template.md \
  --template-html assets/preview-template.html \
  --output-dir ./output --formats md,html,json
python scripts/validate_pack.py --pack output/content-pack.md \
  --quotas analysis.json --source original_text.txt
```

校验失败时先修事实定位、引用、事实 ID、风险边界和选题证据，再重新导出。下限不足只应是 warning；引用不在原文、事实 ID 不存在、占位符残留和无证据选题是 error。

### 7. 多素材合并与对比

分别分析并生成包后再处理：

```bash
python scripts/merge_packs.py --packs pack_a.json pack_b.json --output merged.json
python scripts/compare_packs.py --pack-a pack_a.json --pack-b pack_b.json
```

合并时保留每条事实的全部 `source_id` 和定位；相同表述去重但不吞掉来源。数字、时间、口径或结论不一致时不要强行合并，创建 `conflicts`，列出 A/B 原文、差异字段和解决方式。对比结果要区分“事实覆盖差异”“来源可信度差异”“时间差异”和“选题差异”，不能把文本相似当作事实一致。

## 最终输出顺序

默认交付一个可读素材包，顺序为：

1. 一句话结论与素材边界；
2. 来源登记与分析卡；
3. `source_summary`；
4. 核心事实（逐条证据）；
5. 原文观点；
6. 可标注的推断；
7. 创作选题与图文骨架；
8. 原文金句/可引用片段；
9. 风险与核查清单；
10. 未解决问题、建议补采和下一步动作。

`quotes`、`risks`、`viewpoints`、`inferences`、`verification_gaps`、`conflicts` 没有内容时整块省略；不要输出“暂无”占位块。若素材极少，宁愿短而真实，不要填满模板。

## 资源导航

- `references/pack-schema.md`：JSON 字段、证据链和状态枚举；处理结构化输出前阅读。
- `references/extraction-guide.md`：事实识别、定位、数据精度和事实/观点/推断边界。
- `references/topic-formulas.md`：选题、图文结构、受众与形式匹配。
- `references/compliance-rules.md`：风险、引用和发布前核查。

## 脚本清单

| 脚本 | 用途 | 关键参数 |
|------|------|----------|
| `scripts/analyze_material.py` | 素材分析，输出画像与信息密度 | `--input` `--output` `--config` |
| `scripts/extract_candidates.py` | 事实候选提取 | `--input` `--output` `--quota` |
| `scripts/scan_risks.py` | 风险扫描 | `--input` `--output` `--source-count` |
| `scripts/score_topics.py` | 选题评分 | `--pack` `--output` |
| `scripts/validate_json_pack.py` | JSON 契约校验（结构 + 语义，导出前门禁） | `--pack` |
| `scripts/export_pack.py` | 导出 Markdown/HTML/JSON | `--content` `--template-md` `--template-html` `--output-dir` `--formats` |
| `scripts/validate_pack.py` | 成品包校验（引用、事实 ID、占位符、选题证据） | `--pack` `--quotas` `--source` |
| `scripts/merge_packs.py` | 多素材包合并 | `--packs` `--output` |
| `scripts/compare_packs.py` | 双包对比 | `--pack-a` `--pack-b` |

导出前先过 `validate_json_pack.py`，导出后再过 `validate_pack.py`；前者管结构，后者管内容真实性。

## 依赖

Python 3.8+，脚本仅使用标准库；Skill 本身不替代平台、行业或法律审核。

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
