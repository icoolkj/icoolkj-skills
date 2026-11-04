---
name: security-scanner
description: |
  本地文件安全查杀工具。扫描用户电脑目录中的文件、文件夹或磁盘，检测潜在恶意文件和可疑脚本。
  支持快速/标准/深度三种扫描策略，按 EXE/DLL/MSI/JS/PS1 等文件类型过滤，实时显示扫描进度，
  生成安全/可疑/恶意/未能检查四类分类报告。
  触发词：扫描、查杀、查毒、杀毒、检查病毒、扫描目录、扫描U盘、检查EXE、安全扫描、malware scan、virus scan。
agent_created: true
version: 1.0.0
display_name: 本地文件安全查杀
display_name_en: Security Scanner
description_zh: |
  本地文件安全查杀工具。扫描用户电脑目录中的文件、文件夹或磁盘，检测潜在恶意文件和可疑脚本。
  支持快速/标准/深度三种扫描策略，按 EXE/DLL/MSI/JS/PS1 等文件类型过滤，实时显示扫描进度，
  生成安全/可疑/恶意/未能检查四类分类报告。
description_en: |
  A local file security scanning tool. Scans files, folders or disks on the user machine to detect
  potential malware and suspicious scripts. Supports quick, standard and deep scanning strategies with
  filtering by file type such as EXE, DLL, MSI, JS and PS1, shows live scanning progress, and produces a
  classified report covering safe, suspicious, malicious and unscannable files.
allowed-tools: Bash(python:*)
author: icoolkj
license: MIT
metadata:
  homepage: https://icoolkj.com
  email: icoolkj@163.com
  qq: "594047667"
---

# Security Scanner：本地文件安全查杀工具

> 扫描本地目录，检测潜在恶意文件和可疑脚本，生成分类安全报告。

## 核心原则

1. **只检测不清除**：本工具仅扫描和报告，不删除、不隔离、不修改任何文件。
2. **多维度检测**：结合文件哈希、文件头签名、脚本内容模式、文件名特征、PE 导入表等多维度判断。
3. **分类清晰**：每个文件归类为安全、可疑、恶意或未能检查，附带具体原因。
4. **进度可见**：扫描过程中实时输出已扫描文件数、耗时和当前目标。
5. **策略可选**：快速/标准/深度三种策略，适配不同场景和时间预算。
6. **全策略递归**：三档策略均递归子目录，差异仅在检测深度。

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

扫描引擎按以下顺序对每个文件执行检测（具体规则见 `references/threat-detection-rules.md`）：

1. **文件名特征检测**：双扩展名（含多段）、可疑命名（强/弱信号）、伪装扩展名
2. **文件头签名检测**：文件实际类型与扩展名是否匹配（含 .docx/.xlsx/.docm/.xlsm/.jar 映射至 ZIP 签名）
3. **文件哈希检测**：计算 SHA256，与内置 + `references/hashes.json` + `references/hash-sources.json` 合并比对
4. **脚本内容分析**：JS/PS1/PSM1/VBS/VBE/BAT/CMD/PY/SH/HTA/WSF/WSH/REG 中的危险模式
5. **Office 宏流检测**（standard/deep）：OOXML（docx/xlsx/pptx/docm/xlsm/pptm）查 `vbaProject.bin`；OLE（doc/xls/ppt）解析复合文档流名
6. **压缩包内容检查**（deep）：ZIP 内部文件名 + 读取每个条目文件头（伪装 EXE/类型不一致）；RAR/7Z 仅提示"依赖外部工具"
7. **PE 导入表分析**（deep）：真实解析 DOS→PE→OptionalHeader→Section Table→Import Descriptor→Thunk 链，检测进程注入/下载执行组合
8. **LNK 目标检测**（deep）：校验 Shell Link 签名并检查目标字符串中是否包含 powershell/cmd/mshta/网络路径

### Phase 3：生成报告

```bash
python scripts/report.py --input <结果JSON路径> --format <md|html> --output <报告路径>
```

报告包含五个区域：

1. **扫描概要**：目标、策略、耗时、文件总数
2. **安全文件**：未发现风险的文件列表（HTML 报告中折叠展示）
3. **可疑文件**：存在风险特征但无法确认恶意的文件，附带可疑原因
4. **恶意文件**：高度确信为恶意的文件，附带完整判定依据
5. **未能检查**：因权限、格式、损坏、超限等原因无法扫描的文件，附带原因

Agent 在呈现报告时：
- 恶意文件优先展示，红色标注，展示全部 findings
- 可疑文件次优先，黄色标注
- 安全文件可折叠或摘要展示
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
| 威胁检测规则 | `references/threat-detection-rules.md` | 各检测维度的具体规则和判定标准 |
| 扫描策略详解 | `references/scan-strategies.md` | 三种策略的检测项、适用场景和性能预期 |
| 文件类型风险矩阵 | `references/file-type-risk-matrix.md` | 各文件类型的风险等级和检测重点 |
| 恶意哈希库 | `references/hashes.json` | 可更新的 SHA256 恶意样本库（与内置 fallback 合并） |
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
