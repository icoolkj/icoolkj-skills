# 确定性排版与预检（V1.0.2）

## 使用范围与执行

将长中文、品牌素材、表格标签和流程说明交给确定性绘制，生成模型仅承担主视觉。使用 `scripts/compose_poster.py` 绘制矩形、文本、原图；用多个矩形和文本组合卡片、简化表格、编号流程。根据真实操作顺序排序，不凭视觉猜流程，不把示意表格当真实软件截图。

宿主能运行 Python 3.9+ 时，检查 `Pillow` 与 `fontTools`。依赖清单在 `requirements.txt`，按宿主安装授权规则在隔离环境安装。脚本不自动安装或联网；不提供 Python 的平台使用宿主等价排字能力或降级。不打包系统字体，不推断字体商用许可。

```text
python -m pip install -r <技能目录>/requirements.txt
python <技能目录>/scripts/compose_poster.py <任务目录>/poster.json --output-dir <任务目录>/v001
python <技能目录>/scripts/validate_delivery.py <任务目录>/v001/delivery.json
```

先复制 assets 的两个 JSON 样例到任务目录。填写真实字体路径、原始文案、素材和目标尺寸后再执行；样例的字体字段是待替换路径，不是已提供字体。输出目录必须不存在；每轮使用新目录。排版失败先修配置，禁止覆盖上一版或原素材。成功输出仍为草稿，不自动转为 ready。

## 配置契约

所有相对文件路径基于声明它的 JSON 所在目录。品牌配置中的字体相对品牌文件，海报中的图片和品牌文件路径相对海报配置。矩形位置、字体大小均用最终输出像素，不隐式乘以倍率。

品牌配置：

- `schema_version: 1`、稳定的 `id`；同系列复用 id，修改主题或品牌规则时更新版本。
- `colors`：具名颜色 token，例如 background、surface、ink、muted、accent，各值为实际颜色；可切换深浅主题，但保持品牌约束。
- `fonts`：title/body 两个具名配置，每项含 `path` 和 `index`（TTC 字体索引，默认 0）。明确实际字体，禁止缺字时静默换成西文字体或方框。

海报配置：

- `schema_version: 1`、`brand`（品牌 JSON 路径）。
- `canvas`：width、height、background（颜色 token）。
- `reading`：mode（mobile/zoom）、preview_width（默认建议 390）、min_font_px（默认建议 12）。预览宽度不能大于原画布。
- `prompt`：该张实际设计说明/最终提示词；没有生成背景时写真实排版方案。
- `required_copy`：与交付契约同格式的 id/text/source 数组。
- `blocks`：唯一 id、type、box `[x,y,width,height]`，不得越过画布。

块的具体字段：

| type | 字段 | 行为 |
|---|---|---|
| rect | fill、可选 radius | 背景/卡片，允许包围内容，不得后画遮住文字 |
| text | text、font、font_size、line_spacing（默认 1.25）、color、align（left/center）、可选 required_ids | 根据真实字形宽度换行，检查字体覆盖、四边与容器高度；不缩字、不省略 |
| image | path、role（logo/illustration/product/screenshot）、fit: contain | 原图等比完整合成，记录实际放置宽高、源尺寸与放大倍率；不裁切和拉伸 |

内容块之间不可相互重叠，边缘接触允许。装饰矩形不作为内容冲突，但实际层次与可读性仍须看图。刻意复杂叠放、二维码、矢量 Logo、字形特效、复杂脚本排字等超出本组件范围时，用经过验证的宿主能力，不塞进不支持的字段。

必保留 ID 要绑定到包含完整原文的 text 块；未知 ID、未绑定或改字均阻断。不以“自动换行”为理由丢失标点、价格条件或空格。自动换行只改变视觉行，不更改源文字。

## 素材与阅读预检

记录每张素材的源尺寸、完整使用尺寸和倍率。64×64 Logo 放到 152×152 时应报告约 2.375 倍放大，并将清晰度记为 unverified；等比保真不代表清晰度足够。优先换高清原稿或缩小用图，不能用 AI 重绘替代严格原版 Logo。组件支持的栅格图先完整解码，并处理 EXIF 方向；原文件只读。

按 `font_size × preview_width / canvas.width` 估算手机字号。mobile 模式低于阈值标 fail；仍可生成供修正的 draft，不能 ready。zoom 模式标 unverified，查看实际图片并确认用途后再判断；不得为了过检擅自把手机海报改成放大阅读页。阈值不是通用无障碍或印刷标准，也不替代对比度和真实字形检查。

文本溢出、内容重叠、缺字、越界、缺少必保留项属于阻断错误，不输出被裁切的海报。优先调整版式、扩大文字区或减少非必要装饰，不删事实，不偷偷降字号。一个大画布缩成同样手机宽度，不会自动改善阅读。

## 输出与复现

成功生成：`poster.png`、`preview-mobile.png`、`layout-report.json`、`delivery.json`。最终 PNG 是扁平图；JSON 是复现配方，不冒充 PSD/AI 或可编辑设计源文件。

布局报告记录真实文字行、字号、块位置、字体和配方来源、品牌 ID、素材使用尺寸以及最终图 SHA-256。交付记录初始状态只能为 draft；content/visual/brand 和必保留文案仍需实际看图。先查看全尺寸与预览，再补真实证据。生成次数初值 0 只表示该排版组件没有调用模型；若主视觉来自生图，必须在交付前合并该版本实际调用次数、提示词、费用和来源。不能抹掉主视觉生成成本。

同一品牌可跨多份配方复用品牌 JSON。每个交付版本保留对应配方和品牌配置快照（字体/原素材仅记录来源与哈希，按授权和隐私需求决定是否复制）。可用新目录保存配方后再运行，保证旧版能复现；不要只引用会持续被覆盖的活动配置。

此组件只生成单张；多张分别调用并合并真实 delivery 记录。跨版本改字可复用配方，但整图排版可能触发换行和位移，严格保持要求仍需前后像素对照与 edit_scope 验收。
