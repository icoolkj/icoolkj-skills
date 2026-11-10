---
name: security-scanner
description: |
  本地静态风险扫描工具。扫描用户电脑目录中的文件、文件夹或磁盘，检测潜在恶意文件和可疑脚本。
  支持快速/标准/深度三种扫描策略，按 EXE/DLL/MSI/JS/PS1 等文件类型过滤，实时显示扫描进度，
  生成未检出/可疑/恶意/未能检查四类分类报告，并标注检测覆盖情况。
  触发词：扫描文件、检查可疑脚本、扫描目录、扫描U盘、检查EXE、安全扫描、malware scan、virus scan。
agent_created: true
version: 1.1.2
display_name: 本地静态风险扫描
display_name_en: Security Scanner
description_zh: |
  本地静态风险扫描工具。扫描用户电脑目录中的文件、文件夹或磁盘，检测潜在恶意文件和可疑脚本。
  支持快速/标准/深度三种扫描策略，按 EXE/DLL/MSI/JS/PS1 等文件类型过滤，实时显示扫描进度，
  生成未检出/可疑/恶意/未能检查四类分类报告，并标注检测覆盖情况。
description_en: |
  A local file security scanning tool. Scans files, folders or disks on the user machine to detect
  potential malware and suspicious scripts. Supports quick, standard and deep scanning strategies with
  filtering by file type such as EXE, DLL, MSI, JS and PS1, shows live scanning progress, and produces a
  classified report covering no-detection, suspicious, malicious and unscannable files, with coverage status.
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  repository: https://github.com/icoolkj/icoolkj-skills
  contact: icoolkj@163.com
  qq: "594047667"
  icon: assets/icon.png
allowed-tools: Bash(python:*)
---

# Security Scanner：本地静态风险扫描工具

> 对本地文件进行静态风险分析，检测可疑特征并生成分类报告；不执行、删除或隔离文件。

## 核心原则

1. **只检测不清除**：本工具仅扫描和报告，不删除、不隔离、不修改任何文件。
2. **多维度检测**：结合文件哈希、文件头签名、脚本内容模式、文件名特征、PE 导入表等多维度判断。
3. **分类清晰**：每个文件归类为未检出、可疑、恶意或未能检查，附带具体原因；“未检出”不代表绝对安全。
4. **覆盖率透明**：逐项记录文件头、哈希、脚本、Office、压缩包、PE、LNK 检查状态；失败或未完整执行时不得给出无风险结论。
5. **路径安全**：拒绝符号链接和 Windows reparse point；扫描前后核对文件元数据，发现变化时标记未完整。
6. **压缩包透明**：超出条目/大小限制、加密、损坏或依赖外部工具的压缩包必须明确标记未完整检查。
7. **进度可见**：扫描过程中实时输出已扫描文件数、耗时和当前目标。
8. **策略可选**：快速/标准/深度三种策略，适配不同场景和时间预算。
9. **全策略递归**：三档策略均递归子目录，差异仅在检测深度。

## 何时触发

用户要求扫描目录、检查文件安全性、排查可疑脚本、扫描U盘或下载目录时使用。典型场景：
- "帮我扫描下载目录"
- "检查这个 EXE 有没有病毒"
- "扫描我的 U 盘"
- "检查这个 ZIP 里面有没有危险文件"
- "扫描我的 Python 项目，排查可疑脚本"

## 工作流

### Phase 1：确定扫描参数

Agent 根据用户意图确定三个核心参数：

| 参数 | 选项 | 默认值 |
|------|------|--------|
| 扫描目标 | 文件路径 / 文件夹路径 / 磁盘根目录 | 用户指定 |
| 扫描策略 | quick / standard / deep | standard |
| 文件过滤 | exe,dll,msi,js,ps1,vbs,bat,cmd,py,sh,zip,rar,7z,lnk,scr,com,hta | 全部类型 |

策略说明：
- **quick**：文件名特征 + 文件头签名，不读取文件内容，速度最快
- **standard**：quick + 文件哈希 + 脚本内容模式匹配，平衡速度与深度
- **deep**：standard + 压缩包内检（ZIP 文件名 + 内部文件头，RAR/7Z 仅提示）+ 可执行文件 PE 导入表解析 + LNK 目标检测

如果用户未明确指定策略，根据目标规模自动选择：单文件 → quick，文件夹 → standard，磁盘/大型目录 → standard（提示用户可切换 deep）。

### Phase 2：执行扫描

```bash
python scripts/scan.py \
  --target <路径> \
  --strategy <quick|standard|deep> \
  [--filter <扩展名列表>] \
  [--exclude <正则>]... \
  [--jobs N] \
  [--output <结果JSON路径>] \
  [--quiet] [--dry-run] [--version]
```

常用参数：

| 参数 | 说明 | 默认 |
|------|------|------|
| `--target` | 扫描目标路径 | 必填（除 --version） |
| `--strategy` | quick / standard / deep | standard |
| `--filter` | 逗号分隔的扩展名列表 | 全部 |
| `--exclude` | 额外排除正则，可重复 | 内置排除 node_modules/.git/WinSxS 等 |
| `--jobs` | 并发线程数 | 1（I/O 密集可调至 4-8） |
| `--output` | 结果 JSON 输出路径 | 仅 stdout |
| `--quiet` | 不输出进度 | false |
| `--dry-run` | 仅列出待扫描文件 | false |
| `--version` | 显示版本 | - |

脚本输出 JSON 格式结果到 stdout 和指定文件，进度信息输出到 stderr。

扫描引擎按以下顺序对每个文件执行检测（规则数据见 `references/detection-rules.json`，规则说明见 `references/threat-detection-rules.md`）：

1. **文件名特征检测**：双扩展名（含多段）、可疑命名（强/弱信号）、伪装扩展名
2. **文件头签名检测**：文件实际类型与扩展名是否匹配（含 .docx/.xlsx/.docm/.xlsm/.jar 映射至 ZIP 签名）
3. **文件哈希检测**：计算 SHA256，与 `references/hashes.json` + `references/hash-sources.json` 合并比对；代码内不内置样本哈希，库为空时在 `limitations` 中明确写出"本次未做哈希比对"
4. **脚本内容分析**：JS/PS1/PSM1/VBS/VBE/BAT/CMD/PY/SH/HTA/WSF/WSH/REG 中的危险模式
5. **Office 宏流检测**（standard/deep）：OOXML（docx/xlsx/pptx/docm/xlsm/pptm）查 `vbaProject.bin`；OLE（doc/xls/ppt）解析复合文档流名
6. **压缩包内容检查**（deep）：ZIP 内部文件名 + 读取每个条目文件头（伪装 EXE/类型不一致）；RAR/7Z 仅提示"依赖外部工具"
7. **PE 导入表分析**（deep）：真实解析 DOS→PE→OptionalHeader→Section Table→Import Descriptor→Thunk 链，检测进程注入/下载执行组合
8. **LNK 目标检测**（deep）：校验 Shell Link 签名并检查目标字符串中是否包含 powershell/cmd/mshta/网络路径

#### JSON 结果字段（schema 1.1）

顶层字段：

| 字段 | 说明 |
|---|---|
| `schema_version` | 结果结构版本（当前 `1.1`） |
| `tool_version` | 工具版本，自动读取自 `SKILL.md` 的 `version` 字段，脚本内不再硬编码 |
| `scan_info` | 本次扫描参数与目录覆盖信息 |
| `stats` | 分类统计，含 `coverage_complete` / `incomplete` 覆盖计数 |
| `results` | 逐文件结果数组 |
| `limitations` | 固定的检测边界说明，呈现结论时应一并转述 |

`scan_info` 关键字段：`task_id`（任务标识）、`manifest_changed`（扫描期间目录清单或元数据是否变化）、`skipped_reparse_points` / `skipped_reparse_point_paths`（被跳过的链接节点数与路径，上限 100 条）、`collection_coverage`（`complete` / `incomplete`）。

每个文件结果：

| 字段 | 说明 |
|---|---|
| `classification` | 内部枚举：`safe` / `suspicious` / `malicious` / `unchecked`；`safe` 仅为兼容旧报告保留 |
| `result_label` | 对外展示标签：`no_detection` / `suspicious` / `malicious` / `unknown` |
| `coverage` | `complete` / `partial` / `incomplete`，适用检测项的执行完成度 |
| `checks` | 逐项检测状态：`path_validation` `file_signature` `sha256` `script_analysis` `office_macro` `archive` `pe_analysis` `lnk_analysis`，取值 `completed` / `failed` / `incomplete` / `not_applicable` |
| `errors` | 检测项未完成的具体原因列表 |
| `file_changed_during_scan` | 扫描期间文件元数据是否发生变化 |
| `findings` `reason` `sha256` `size` `mtime` 等 | 含义同旧版 |

解析约定：`result_label` 与 `coverage` 优先于 `classification`；只要 `coverage != complete`，或 `checks` 中存在 `failed` / `incomplete`，就不得对外给出"安全"或"无风险"结论。

### Phase 3：生成报告

```bash
python scripts/report.py --input <结果JSON路径> --format <md|html> --output <报告路径>
```

报告包含五个区域：

1. **扫描概要**：目标、策略、耗时、文件总数
2. **未检出文件**：当前检测范围内未检出已知风险的文件列表（HTML 报告中折叠展示；不代表绝对安全）
3. **可疑文件**：存在风险特征但无法确认恶意的文件，附带可疑原因
4. **恶意文件**：高度确信为恶意的文件，附带完整判定依据
5. **未能检查**：因权限、格式、损坏、超限等原因无法扫描的文件，附带原因

Agent 在呈现报告时：
- 恶意文件优先展示，红色标注，展示全部 findings
- 可疑文件次优先，黄色标注
- 未检出文件可折叠或摘要展示，并说明该结论不等于确认文件安全
- 未能检查文件列出原因，建议用户手动检查

维护哈希库（只写本地，默认不上网）：

```bash
python scripts/update_hashes.py --add <sha256> --name "样本名"
python scripts/update_hashes.py --from-file hashes.txt
python scripts/update_hashes.py --rebuild   # 合并 references/hash-sources.json（或 hash-sources/ 目录）
python scripts/update_hashes.py --list
```

仅当用户明确要求在线更新时，才使用 `update_hashes.py --from-url <清单URL>`；只下载哈希清单，不下载样本。

## 决策规则

| 用户场景 | 推荐策略 | 文件过滤 |
|----------|----------|----------|
| 检查单个 EXE | quick | exe |
| 扫描下载目录 | standard | exe,dll,msi,js,ps1,vbs,bat,zip,rar,7z,lnk,scr,hta,docm,xlsm |
| 扫描 U 盘 | standard | exe,dll,msi,lnk,scr,com,js,ps1,vbs,bat,hta |
| 检查 ZIP 内危险文件 | deep | zip,rar,7z |
| 排查 Python 项目可疑脚本 | standard | py,sh,bat,ps1,js |
| 全盘深度扫描 | deep | 全部类型 |

## 安全约束

以下操作**禁止**：
- 删除、隔离或修改任何被扫描文件
- 上传文件内容到外部服务器（哈希查询除外，且仅发送哈希值）
- 执行任何被扫描的可执行文件
- 修改文件权限或属性

以下操作**优先**：
- 只读访问目标文件
- 所有检测在本地完成
- 哈希值比对使用内置 + 本地外置规则库，默认不依赖网络
- 压缩包检查只在内存读取文件头/名单，不解压到磁盘

## 资源导航

| 资源 | 路径 | 用途 |
|------|------|------|
| 检测规则数据 | `references/detection-rules.json` | 脚本模式 / PE 可疑导入 / 命名关键词 / VBA 危险标记；可自行增删，无需改代码 |
| 威胁检测规则 | `references/threat-detection-rules.md` | 各检测维度的具体规则和判定标准 |
| 扫描策略详解 | `references/scan-strategies.md` | 三种策略的检测项、适用场景和性能预期 |
| 文件类型风险矩阵 | `references/file-type-risk-matrix.md` | 各文件类型的风险等级和检测重点 |
| 恶意哈希库 | `references/hashes.json` | 可更新的 SHA256 恶意样本库（代码内不内置任何样本哈希） |
| 哈希源 | `references/hash-sources.json` | 第三方 JSON 清单（平铺单文件，分发兼容；本地也可用 hash-sources/ 目录），扫描时自动合并 |
| 扫描脚本 | `scripts/scan.py` | 主扫描引擎 |
| 报告脚本 | `scripts/report.py` | 报告生成器 |
| 哈希更新脚本 | `scripts/update_hashes.py` | 追加 / 导入 / 重建哈希库 |

## 依赖

Python 3.8+，脚本仅使用标准库（hashlib, zipfile, json, os, struct, html 等）。不安装任何第三方依赖。

RAR/7Z 内检需外部工具（`unrar` / `7z`），当前版本仅提示"依赖外部工具，未解析"，不阻塞扫描。

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


## V1.1 安全边界与结果解释

- `safe` 是为兼容旧报告保留的内部分类值；新报告应显示为“未检出（非绝对安全）”，并通过 `result_label: no_detection` 表达。
- `unchecked` 表示至少一个适用检测项失败、未完成或目标文件在扫描期间发生变化。
- `coverage=complete` 只表示当前策略定义的适用检查项已执行完成，不代表具备专业杀毒软件的检测覆盖率。
- 当前版本仍是静态特征分析工具，**尚未集成 Microsoft Defender、MCP 或动态行为分析**。
- ZIP 条目超限、加密、无法读取、条目大小超限，以及 RAR/7Z 未解析，均应视为覆盖不完整。
- 扫描前后文件元数据变化会触发未完整状态；该检查是风险缓解措施，不是抵御本机高权限攻击者的强安全边界。
- 不得执行被扫描文件，不得自动删除、隔离或修改文件。
