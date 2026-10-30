# NoteIntel 素材包数据契约

JSON 是唯一事实源；Markdown 和 HTML 只是视图。字段可省略，但省略必须符合“无内容则不输出”的规则。

## 顶层

```json
{
  "schema_version": "1.0",
  "pack_id": "pack-20261027-001",
  "source": "来源标题或 URL",
  "sources": [{"source_id":"S1","type":"url|file|text|interview","title":"","url":"","author":"","publisher":"","published_at":"","accessed_at":"","completeness":"full|partial|unknown"}],
  "mode": "concise|standard|deep",
  "word_count": 0,
  "density_score": 0.0,
  "analysis": {"density_factors": {}, "quotas": {}, "limitations": []},
  "summary": "只概括来源明确表达的内容",
  "facts": [],
  "viewpoints": [],
  "inferences": [],
  "topics": [],
  "quotes": [],
  "risks": [],
  "verification_gaps": [],
  "conflicts": [],
  "next_actions": []
}
```

## 事实对象

```json
{
  "id": "F1",
  "claim": "可独立成立的事实，保留范围、时间和限定词",
  "evidence_type": "data|event|quote|method|comparison|description",
  "status": "reported|verified",
  "confidence": "high|medium|low",
  "source_ids": ["S1"],
  "location": "S1：第2段，第1句",
  "quote": "原文完整摘录",
  "qualifiers": ["预计", "截至2025年12月", "样本为某地区"]
}
```

`verified` 只有在素材中明确给出独立核验或用户提供第二来源时使用；单一来源报道默认是 `reported`，不是 `verified`。

## 观点、推断和核查缺口

- `viewpoints`：`{id, text, source_id, location, quote, speaker_or_owner}`；把“认为、应该、最好”等原文观点留在这里。
- `inferences`：`{id, text, based_on:["F1"], reasoning, certainty:"hypothesis|likely|uncertain", disclaimer}`；不得混进 `facts`。
- `verification_gaps`：`{id, question, why_it_matters, related_facts:["F1"], suggested_check}`。

## 选题对象

```json
{
  "id": "T1",
  "title": "不夸大的内容标题",
  "angle": "数据冲击|对比反差|因果追溯|影响推演|方法拆解|趋势预判",
  "audience": "普通消费者",
  "form": "图文卡片",
  "related_facts": ["F1", "F3"],
  "value_add": "原文没有直接展开的编辑视角",
  "hook": "开头问题或反差",
  "outline": ["封面：...", "第2张：..."],
  "visual_plan": "左右对比图/时间线/流程图/数据卡片",
  "cta_or_next_step": "引导读者核查、讨论或继续阅读",
  "evidence_boundary": "可以说什么；哪些只能写成推断或待核查"
}
```

选题必须至少关联一个 `F`，且 `value_add` 不得只是重复 `claim`。`outline` 中可为每张卡片追加 `fact_ids`，方便继续制作图文。

## 风险、引用与冲突

- `quotes`：`{text, source_id, location, use:"金句|数据引用|标题素材", context_note}`。
- `risks`：`{type, severity:"low|medium|high", content, source_ids, suggestion}`。
- `conflicts`：`{field, source_ids, statements, difference, resolution:"保留并列|以较新来源为准|待核查", impact}`。

数值、时间、统计口径或因果关系不同都属于潜在冲突。没有充分依据时保留并列，不生成“综合数字”。

## 平台与视觉扩展字段

以下字段按需出现；没有内容时省略，不输出空占位块。

```json
{
  "platform_adaptations": [
    {
      "platform": "wechat|xiaohongshu|zhihu|video_short|moments",
      "title_options": [""],
      "format": "article|card_deck|answer|script|short_post",
      "hook": "",
      "body_or_outline": [],
      "cta": "",
      "visual_format": "wechat_inline|xiaohongshu_3_4|zhihu_wide|vertical_9_16|square",
      "fact_ids": ["F1"],
      "evidence_boundary": ""
    }
  ],
  "source_images": [],
  "derived_visuals": [],
  "generated_visuals": [],
  "card_plan": []
}
```

详细字段和发布检查见 `references/visual-assets.md` 与 `references/platform-adapters.md`。
