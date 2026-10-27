# 视觉资产规则

## 1. 三类图片必须分开

### 原文图片 `source_images`

来自原文、网页、报告、采访或用户提供文件的图片、截图、照片、图表。它们可以作为研究证据或引用候选，但“能访问”不等于“可公开发布”。

记录：

```json
{
  "id": "IMG1",
  "type": "source_image",
  "source_id": "S1",
  "location": "原文第3段后",
  "original_url": "",
  "caption": "原文图片说明",
  "what_it_shows": "只描述实际可见内容",
  "related_facts": ["F2"],
  "rights_status": "owned|licensed|unknown|research_only|public_domain|needs_permission",
  "recommended_use": "研究参考|来源引用|发布前确认|不建议使用",
  "ocr_status": "not_needed|pending|reviewed",
  "note": ""
}
```

不要从图片中臆测人物身份、地点、时间、因果或图片外事实。OCR结果必须标记为待确认，尤其是数字和图表文字。

### 整理图 `derived_visuals`

根据已核对事实重新制作的视觉内容。它不是原文原图，也不是独立来源。

记录：

```json
{
  "id": "VIS1",
  "type": "derived_visual",
  "visual_kind": "comparison|timeline|process|impact_chain|data_card|table|quote_card|map|diagram",
  "title": "两年市场规模变化",
  "based_on_facts": ["F2", "F3"],
  "data_used": ["2023年：100亿元", "2025年：160亿元"],
  "calculation": "仅展示原文已明确的数值；如有计算写出公式",
  "source_note": "据S1第4段整理",
  "evidence_boundary": "未说明统计口径，不推断为全国市场",
  "format": "wechat_inline|xiaohongshu_3_4|zhihu_wide|vertical_9_16|square",
  "status": "plan|draft|checked|approved"
}
```

数字、比例、单位、坐标、趋势线和统计图优先使用确定性图表或HTML静态排版，不用AI生成模型绘制精确数据。

### AI示意图 `generated_visuals`

只用于概念、氛围、装饰或非真实场景。必须写明：

> AI生成示意图，不代表真实事件或真实人物。

禁止把AI图当作：新闻现场、采访照片、真实人物肖像、真实产品实拍、原文截图、实验结果、数据图表或版权来源。

记录：

```json
{
  "id": "GEN1",
  "type": "generated_visual",
  "purpose": "cover_mood|concept|illustration|decorative",
  "prompt_brief": "",
  "disclosure": "AI生成示意图，不代表真实事件或真实人物",
  "not_evidence": true,
  "platform_formats": ["xiaohongshu_3_4", "vertical_9_16"],
  "status": "plan|generated|checked|approved"
}
```

## 2. 卡片和图文视觉方案

`card_plan` 记录可制作的页级方案：

```json
{
  "platform": "xiaohongshu",
  "aspect_ratio": "3:4",
  "page_count": 6,
  "pages": [
    {"page": 1, "role": "cover", "copy": "", "fact_ids": [], "asset_type": "derived_visual"},
    {"page": 2, "role": "fact", "copy": "", "fact_ids": ["F1"], "asset_type": "derived_visual"}
  ],
  "source_label": "据原文整理",
  "checks": ["数字核对", "来源标注", "文字可读性", "版权判断"]
}
```

封面负责主题、冲突或收益；正文每页只承担一个核心信息；最后一页负责总结、行动建议、互动问题或核查边界。不要把整篇文章缩成一张密集海报。

## 3. 图片发布检查

发布前逐项检查：

- 原文图片是否获得使用许可；
- 整理图数字、单位、日期和比例是否与事实一致；
- 图表来源是否清晰；
- AI图是否有示意图披露；
- 图片是否误导性地暗示真实人物或事件；
- 文字图片中的关键专名、数字和来源标注是否逐字正确；
- 平台比例是否适配；
- 低分辨率、裁切、字幕安全区和移动端可读性是否合格。
