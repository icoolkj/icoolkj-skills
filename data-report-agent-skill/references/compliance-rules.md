# 合规检查规则

Agent 在生成 report.json 时必须在对话层做预检查，本地 compliance.py 会做最终校验。

## 敏感词黑名单

以下词汇禁止出现在报告标题、章节标题、content 字段中：

| 类别 | 禁止词汇 |
|------|---------|
| 绝对化用语 | 最佳、最强、第一、顶级 |
| 百分比承诺 | 100%、百分百 |
| 保证性用语 | 绝对、确保盈利、稳赚 |
| 风险承诺 | 零风险、无风险 |

**处理方式**：Agent 发现这些词时，自动替换为客观表述：
- "最佳" → "优秀" / "领先"
- "第一" → "前列" / "排名靠前"
- "100%" → "全部" / "所有"
- "确保盈利" → "预期盈利"
- "零风险" → "低风险"

## URL 链接规则

- URL 不允许出现在 `content` 字段（正文）中
- URL 应放在 `data_source` 字段（数据来源）或单独的 references 字段
- 检测正则：`https?://\S+` 和 `www\.\S+`

## 数据质量告警

| 条件 | 级别 | 处理 |
|------|------|------|
| 数据完整度 < 50% | 告警 | 提醒用户数据质量风险，但不阻止生成 |
| 数据行数 = 0 | 错误 | 阻止生成，提示用户检查数据文件 |
| 数据列数 = 0 | 错误 | 阻止生成，提示用户检查数据文件 |

## Schema 结构校验

### 顶层必填字段
- `title` — 报告标题
- `data_source` — 数据文件路径
- `sections` — 章节列表（至少 1 个）
- `style` — 风格 ID

### 每节必填字段
- `id` — 节标识
- `title` — 节标题
- `content_type` — 内容类型
- `style` — 风格 ID

### content_type 合法值
text / summary / chart / table / kpi / image

### chart_config.type 合法值
bar / line / pie / scatter / histogram / area

### 图表类型章节
- 必须有 `chart_config` 字段
- `chart_config` 必须有 `type` 字段
- `chart_config` 必须有 `data` 字段

## 合规检查执行方式

1. **对话层预检查**（Agent 执行）：输出 report.json 前自检
2. **本地最终校验**（compliance.py 执行）：流水线运行时强制校验，失败则终止

```bash
# 本地合规检查命令
python scripts/compliance.py report.json
```
