# Security Scanner 1.1.2

本版本是 P0 安全修复版，保留原有静态检测能力，重点修复“检查失败仍显示安全”、扫描覆盖率不透明、链接路径风险和压缩包部分检查被误认为完整等问题。

## 环境

- Python 3.9+（建议 Python 3.10 或更高）
- Windows 10/11；部分静态扫描逻辑也可在 Linux/macOS 上运行
- 不需要管理员权限；访问受限的文件会标记为未能检查

## 运行

```powershell
python scripts/scan.py --version
python scripts/scan.py --target ".\sample" --strategy standard --output ".\scan-result.json"
python scripts/scan.py --target ".\sample" --strategy deep --quiet --output ".\scan-result.json"
python scripts/report.py --input ".\scan-result.json" --format html --output ".\scan-report.html"
```

## 结果语义

- `safe`：为兼容旧版保留的内部枚举值；报告应理解为 `no_detection`（当前范围未检出已知风险），不是绝对安全。
- `suspicious`：存在可疑静态特征。
- `malicious`：命中当前规则定义的高风险特征；静态规则判断不等同于专业引擎确证。
- `unchecked` / `result_label=unknown`：至少一个适用检查项失败或不完整，不能得出无检出结论。
- `coverage`：`complete` 表示当前策略下适用检查项已执行完成，不代表覆盖所有恶意软件。

## 本版安全边界

- 不执行被扫描文件，不自动删除、隔离或修改文件。
- 拒绝将符号链接和 Windows reparse point 作为直接扫描目标；遍历目录时跳过这些链接节点，并在扫描概要中统计跳过数量、标记目录覆盖不完整。
- 扫描前后检查文件元数据变化；检测到变化时将无风险结论降级为未能检查。
- ZIP 条目超限、加密、损坏、条目读取失败或条目大小超限时，标记检查不完整。
- RAR/7Z 尚未解析，深度扫描会明确标记为未完整检查。
- 当前版本未集成 Microsoft Defender、MCP、动态行为分析或云端样本上传。

## 版本

版本号统一维护在 `SKILL.md` frontmatter 的 `version` 字段，`scan.py` 运行时自动读取并在 JSON 的 `tool_version` 与 `--version` 中输出；脚本内不保留独立版本常量。

## 图标

Skill 图标资源位于 `assets/icon.png`（512x512，约 75 KB）。部分 Skill 宿主不读取自定义 frontmatter 图标字段；如平台要求单独配置头像，请在平台的 Skill 设置中选择该文件。

## 测试

```powershell
python -m unittest discover -s tests -v
```

本仓库的回归测试覆盖检测读取失败降级、符号链接拒绝、ZIP 条目超限和 no-detection 语义。
