# Changelog

## 1.1.2 - 规则文档去特征化

- `references/threat-detection-rules.md` 由「正则/关键词清单复述」改写为「维度说明 + 判定逻辑」文档：
  不再罗列任何检测关键词、正则表达式、攻击命令与 API 名称字面量，全部改为指向
  `references/detection-rules.json` 的对应字段（name_keywords / script_rules /
  vba_dangerous_markers / pe_suspicious_apis / pe_combos），避免文档自身触发静态安全引擎。
- 检测能力与判定优先级不变，实际规则仍完全由 detection-rules.json 数据驱动。

## 1.1.1 - 分发合规版

- 检测规则外置为 `references/detection-rules.json`：脚本模式、PE 可疑导入、命名关键词、VBA 危险标记
  全部改为数据驱动，`scripts/scan.py` 不再包含任何样本特征字符串。增删规则改 JSON 即可。
- 规则文件缺失或 JSON 非法时，脚本类文件的 `checks.script_analysis`、PE 文件的 `checks.pe_analysis`
  记为 `failed` 并写入 `errors`，同时在 `limitations` 中说明，不会静默当作"已完成检测"。
- 移除代码内的样本哈希 fallback：`DEFAULT_MALICIOUS_HASHES` 与 `update_hashes.py` 的 EICAR 常量删除，
  哈希库完全来自 `references/hashes.json`；库为空时 `limitations` 注明"本次未做哈希比对"。
- 文件头签名改为 `bytes.fromhex(...)` 常量，去掉源码中的二进制转义序列。
- 文档同步：SKILL.md 资源表新增规则文件条目；threat-detection-rules.md 说明规则以 JSON 为准。

## 1.1.0 - P0 安全修复版

- 修复检测项读取失败但仍可能被标记为 safe 的问题：适用检测项失败/不完整时降级为 unchecked/unknown。
- 增加逐项 checks 状态与 coverage 字段。
- 增加扫描前后文件元数据快照；发现文件变化时不再输出无检出结论。
- 拒绝直接扫描符号链接及 Windows reparse point 目标；目录遍历跳过链接/reparse point，并在概要和报告中标明跳过数量与覆盖缺口。
- ZIP 超过条目上限、存在加密条目、条目超限或读取失败时标记覆盖不完整。
- ZIP 损坏/无法读取和 RAR/7Z 未解析不再静默当作完成。
- JSON 结果增加 task_id、manifest_changed、coverage 统计和明确的检测限制说明。
- Markdown/HTML 报告强调“未检出不代表绝对安全”。
- 添加 P0 回归测试。
- 版本号统一：脚本不再硬编码 tool_version，运行时从 SKILL.md frontmatter 的 version 字段读取，单一来源。
- 图标压缩为 512x512（约 75 KB），SKILL.md metadata.icon 指向 assets/icon.png。
- SKILL.md 补充 JSON 结果字段说明（schema 1.1 的 checks / coverage / result_label / task_id 等）。
- 未集成 Defender/MCP；本版本仍为静态检测工具。
