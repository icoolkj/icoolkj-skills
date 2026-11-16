# 交付记录与商业发布门槛

## 1. 输出组织

每个任务使用新目录，保留最终图片、最终提示词（prompt.txt）和 delivery.json。不要复制无必要的客户原始资料进分发包。记录仅包含任务所需内容，不保存密钥，不自动上传或发布。保留旧版本供对照，用户有保密/保留期限要求时遵守实际约定。

纯方案/提示词可直接在回复交付；没有文件能力的平台以同结构文字记录替代。对客户展示图片、说明、适用用途及问题清单，不要求客户填写 JSON。

## 2. delivery.json v1

根字段：

- `schema_version`：固定 1；`skill_version`：当前版本。
- `mode`：plan/prompt/image/edit；`requested_count`：正整数。
- `required_copy`：数组，每项含唯一 `id`、`text`、`source`；包含全部任务必保留文字。
- `items`：与 requested_count 同样多的逐张记录，哪怕某张失败也要保留记录。

每项记录：

- `id`、`version`（正整数）、`status`（plan_only/draft/ready/blocked）、`reason`（非 ready 时必填）。
- `prompt`：实际最终提示词或完整设计说明，不用占位内容。
- `attempts`：本版本实际生成/编辑请求数，0–3；用户增加预算/次数时建立明确的新版本，保留旧记录，不重置任务累计账目。
- `artifact`：无图片为 null，否则 `{kind: local|remote, location: 路径或实际附件标识/URL}`。本地相对路径基于 delivery.json 目录；不得冒充已下载。
- `target`：`{ratio: [宽比例, 高比例], width: 整数或null, height: 整数或null}`；精确宽高同时填。精确尺寸与比例必须相容。
- `actual`：实测 `{width, height, format}`；未测得填 null。
- `required_ids`：本图全部必须呈现的清单 ID；单张必须覆盖根清单，多张按每张的客户需求分配，总体必须覆盖；共享条件必须列入所有适用图片，不能为规避遗漏检查任意分配。
- `copy_checks`：与 required_ids 一一对应的 `{id, status, evidence}`，status 为 pass/fail/unverified；证据写核对位置和观察，不能伪造 OCR/视觉结果。
- `checks`：包含 content/visual/dimensions/access/brand/edit_scope/qr/rights/print 九项；每项为 `{status, evidence}`，status 可为 pass/fail/unverified/not_applicable。
- `applicable`：图片记录必含 content/visual/dimensions/access；按任务追加品牌、改图、二维码、印刷和权利限制项目。edit 模式图片记录必须包含 edit_scope。图片记录中，适用项不得标 not_applicable；非适用项必须标 not_applicable，不能把已失败或未验证项藏在列表之外。纯文字/无图记录的图片检查可不适用。

`ready` 要求：有可访问产物、实际尺寸、所有适用检查通过且有证据、必保留文案逐项通过。`draft` 必须有可访问产物，明确问题。`plan_only`/`blocked` 不填写图片产物；方案/提示词模式禁止生成尝试和 ready 状态。纯方案的图片相关检查可不适用，记录校验只对图片交付执行图片门槛。

## 3. 校验方法与边界

在宿主允许执行 Python 时运行：

```text
python scripts/validate_delivery.py <delivery.json>
```

退出码 0 表示记录内部一致，不代表商业验收通过；合法 blocked/草稿记录也可通过。退出码 1 表示记录或本地文件校验失败。程序仅使用标准库，可直接测量 PNG/JPEG/GIF 的尺寸并核对格式；不支持的图片格式明确报出，使用宿主实际转换后再核验，不能改扩展名。远程产物不自动下载，仅检查记录中的访问及检查证据，不证明远程资源当前可用。

脚本不识别文字、不验证 Logo 合成、不解码二维码、不判断授权和审美，也不能证明 required_copy 已完整提取。这些必须由实际执行者按原始需求和最终图片完成。不能用一段虚构的 evidence 绕过人工/视觉检查。

## 4. 商业发布门槛

V1.0.1 是能力与流程升级候选，不因静态校验自动成为商业正式版。

1. 执行 `evaluation/acceptance.json` 全部适用用例，记录输入、宿主/模型及版本、日期、工具调用记录、费用（未知则明示）、实际图片和检查证据。未跑用例保持 not_run。
2. 至少一个真实可生图宿主完成输入→生成→查看→独立交付；真实无生图能力环境验证降级。欲宣传多个平台已支持，需分别执行其适用用例；模拟不算真实跨平台验收。
3. 必保留事实遗漏、品牌失真却报 ready、重复收费越界、假文件路径、未生成却报成功均为发布阻断项，必须修复回归。
4. 涉及严格 Logo/二维码/印刷的卖点，只有该实际能力链验证通过才能对外宣传；缺能力时限定服务范围为数字海报、方案或草稿。
5. 选取不同场景的真实或获授权样例进行试交付，记录首轮通过率、最终通过率、每张总调用数/费用、人工修改量和失败原因。基于实测制定价格、修改次数及服务范围，不能从指令文本推断盈利或效果。
6. 对外约定交付格式、数量、修改范围、费用口径、素材授权责任和资料保留方式；不自动生成法律保证或模型商用授权承诺。

测试记录建议字段：case_id、status（not_run/pass/fail/blocked）、execution（live/simulated/manual_review）、host、model、date、evidence、cost、notes。仅真实执行后更新状态；独立保存每次运行记录，不覆盖原始用例。
