# 威胁检测规则

## 检测维度概览

| 维度 | 适用策略 | 检测内容 | 判定权重 |
|------|----------|----------|----------|
| 文件名特征 | quick/standard/deep | 双扩展名、可疑命名、伪装扩展名 | 中 |
| 文件头签名 | quick/standard/deep | 实际类型与扩展名是否匹配 | 高 |
| 文件哈希 | standard/deep | SHA256 与已知恶意哈希比对（hashes.json + hash-sources） | 极高 |
| 脚本内容模式 | standard/deep | 危险代码模式匹配（含组合语义） | 高 |
| Office 宏流 | standard/deep | OOXML vbaProject.bin / OLE 宏流名 + 自动执行标记 | 高 |
| 压缩包内容 | deep | ZIP 内部文件名 + 文件头签名（不解压到磁盘） | 中 |
| PE 导入表分析 | deep | 真实导入表解析、API 组合 | 高 |
| LNK 目标检测 | deep | Shell Link 签名 + 目标关键词 | 中 |

## 1. 文件名特征检测

### 1.1 双扩展名检测

文件名中出现两个或以上扩展名，且最后一个为"安全"类型，而前面的段包含"危险"类型（或反之）。

判定规则：
- `report.pdf.exe` → 恶意（伪装 PDF 的 EXE）
- `photo.jpg.scr` → 恶意（伪装图片的 SCR）
- `data.txt.zip` → 安全（正常压缩包命名，zip 不在 DANGEROUS_EXTS）
- `file.exe.txt` → 恶意（EXE 改名为 TXT，可执行段出现在非末位）
- `a.exe.b.txt.exe` → 恶意（多段，末位危险 + 中间安全）

实现细节：
- 处理 Windows 尾部点号/空格（`file.exe. ` → `file.exe`）
- 多段扩展名从右向左扫描，任一危险段 + 末位安全段 → 恶意
- 危险扩展名集合见 `scan.py::DANGEROUS_EXTS`

危险扩展名集合（与 `scan.py` 一致）：
`.exe, .scr, .com, .sys, .cpl, .ocx, .bat, .cmd, .vbs, .vbe, .ps1, .psm1, .js, .jse, .jar, .msi, .dll, .lnk, .hta, .wsf, .wsh, .msh, .mshxml, .reg`

### 1.2 可疑命名模式（强/弱信号）

**强信号**（命中即 suspicious，不限扩展名）：
`crack, keygen, injector, bypass, keylogger, ransom, stealer, backdoor, rootkit, trojan, worm`

**弱信号**（仅在可执行/脚本扩展名上触发）：
`patch, hack, cheat, loader, warez, serial, activation, unlock`

**系统进程名**：
`svchost.exe, csrss.exe, lsass.exe, winlogon.exe, explorer.exe, services.exe, smss.exe, wininit.exe, spoolsv.exe, taskmgr.exe, rundll32.exe, userinit.exe`
仅当出现在**非系统目录**（`C:\Windows\System32`、`SysWOW64`、`WinSxS`、`/usr/bin` 等之外）时标记为 suspicious。

**随机命名**：
- 文件名主体长度 ≥ 8
- 同时包含字母与数字
- 不含常见语义词（readme/license/setup/install/update/config/data/test/demo/sample/example/release/debug）
- 元音比例 < 15%（避免误伤 `report2final.docx` 类命名）
- 且扩展名 ∈ DANGEROUS_EXTS

### 1.3 伪装扩展名

文件头签名显示为可执行文件（MZ），但扩展名为非可执行类型。

## 2. 文件头签名检测

读取文件前 1024 字节，与已知文件签名比对。

### 常见文件签名

| 文件类型 | 签名（Hex） | 偏移 | 对应扩展名 |
|----------|-------------|------|------------|
| EXE/DLL | `4D 5A` (MZ) | 0 | .exe/.dll/.scr/.sys/.cpl/.com/.ocx |
| ZIP 容器 | `50 4B 03 04` | 0 | .zip/.docx/.xlsx/.pptx/.docm/.xlsm/.jar/.apk/.epub |
| RAR | `52 61 72 21` | 0 | .rar |
| 7Z | `37 7A BC AF 27 1C` | 0 | .7z |
| PDF | `25 50 44 46` (%PDF) | 0 | .pdf |
| PNG | `89 50 4E 47` | 0 | .png |
| JPG | `FF D8 FF` | 0 | .jpg/.jpeg |
| GIF | `47 49 46 38` | 0 | .gif |
| OLE 复合文档 | `D0 CF 11 E0` | 0 | .msi/.doc/.xls/.ppt |
| ELF | `7F 45 4C 46` | 0 | .elf/.so |
| LNK | `4C 00 00 00` | 0 | .lnk |
| RTF | `7B 5C 72 74 66` | 0 | .rtf |

### 签名-扩展名白名单

以下组合属于正常行为，不触发"类型不一致"：
- (zip, .docx) / (zip, .xlsx) / (zip, .pptx) / (zip, .docm) / (zip, .xlsm)
- (zip, .jar) / (zip, .apk) / (zip, .epub)
- (ole, .doc) / (ole, .xls) / (ole, .ppt) / (ole, .msi)

### 判定规则

- 扩展名为 .exe 但文件头不是 MZ → 可疑（可能是伪装文件或损坏文件）
- 扩展名为 .jpg/.png/.gif 但文件头为 MZ → 恶意（伪装为图片的可执行文件）
- 扩展名为 .pdf 但文件头为 MZ → 恶意
- 扩展名为 .txt/.docx/.xlsx 等安全类型但文件头为 MZ → 恶意
- 文件头与扩展名不一致但都不涉及 MZ → 可疑

## 3. 文件哈希检测

计算文件 SHA256 哈希值，与哈希库比对。

### 哈希库来源与格式

扫描启动时加载（后者覆盖前者）：
1. **内置 fallback**（`scan.py::DEFAULT_MALICIOUS_HASHES`）：真实 EICAR 测试样本
2. **外置库**（`references/hashes.json`）：与内置合并
3. **哈希源目录**（`references/hash-sources/*.json`）：第三方清单，扫描时自动合并

内置 EICAR SHA256（真实值）：
```
275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f
```

外置库格式：
```json
{
  "malicious_hashes": [
    {
      "sha256": "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f",
      "name": "EICAR-Test-File",
      "description": "标准防病毒测试文件"
    }
  ]
}
```

判定规则：
- 哈希匹配 → 恶意（直接判定，不看其他维度）
- 哈希不匹配 → 不影响其他检测结果

### 扩展哈希库

用 `scripts/update_hashes.py` 维护：
- `--add <sha256> --name "..."` 追加单条
- `--from-file hashes.txt` 导入文本清单（每行一个 SHA256，可用 `#` 注释和 `sha256 名称`）
- `--rebuild` 把 `hash-sources/*.json` 合并进 `hashes.json`
- `--from-url` 仅在用户明确要求时使用；只下载哈希清单，不下载样本

## 4. 脚本内容模式检测

对 JS、PS1、PSM1、VBS、VBE、BAT、CMD、PY、SH、HTA、WSF、WSH、REG 文件进行内容扫描。
文件读取上限 5MB，超限记录"文件过大，跳过内容分析"。
编码回退：UTF-8 → GBK → UTF-16 → Latin-1。

### 4.1 JavaScript

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| eval 执行 Base64 | `eval\s*\(\s*atob\s*\(` | 高 | obfuscation |
| 下载并执行 | `\.downloadFile\s*\([^)]*\)[^;]*;\s*[^;]*\.run\s*\(` | 极高 | - |
| WScript.Shell | `WScript\.Shell` | 中 | execute |
| ActiveX 对象 | `new\s+ActiveXObject\s*\(` | 中 | - |
| PowerShell 编码调用 | `powershell(?:\.exe)?\s+.*-enc(?:odedcommand)?` | 极高 | - |
| 长 Hex 字符串 | `[0-9a-fA-F]{64,}` | 中 | obfuscation |
| document.write + EXE | `document\.write\s*\([^)]*\.exe` | 高 | execute |
| XMLHTTP 请求 | `XMLHTTP` | 中 | download |

### 4.2 PowerShell（.ps1 / .psm1）

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| 编码命令执行 | `-EncodedCommand\s+` | 极高 | - |
| IWR + IEX | `Invoke-WebRequest[^\n]*\|\s*Invoke-Expression` | 极高 | - |
| IEX WebClient | `IEX\s*\(\s*New-Object\s+Net\.WebClient` | 极高 | - |
| 隐藏窗口 | `-WindowStyle\s+Hidden` | 中 | stealth |
| 绕过执行策略 | `-ExecutionPolicy\s+Bypass` | 中 | stealth |
| 注册表 Run 持久化 | `Set-ItemProperty[^\n]*HKCU[^\n]*Run` | 高 | persist |
| 反射加载 DLL | `\[Reflection\.Assembly\]::Load` | 高 | inject |
| 长 Base64 | `[A-Za-z0-9+/]{100,}={0,2}` | 中 | obfuscation |
| 下载远程内容 | `DownloadString|DownloadFile` | 高 | download |
| 执行动态内容 | `(?:Start-Process|Invoke-Expression|&)\s+\$` | 高 | execute |

### 4.3 VBS / VBE

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| WScript.Shell | `CreateObject\s*\(\s*"WScript\.Shell"` | 中 | execute |
| 下载并执行 | `\.downloadFile[^\n]*\.run` | 极高 | - |
| RegWrite | `RegWrite` | 中 | persist |
| 自删除 | `\.DeleteFile\s*\(\s*WScript` | 高 | selfdelete |

VBE 为编码脚本，命中任意内容 → 中风险（需解码后复判）。

### 4.4 BAT / CMD

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| bitsadmin 下载执行 | `bitsadmin[^\n]*(?:transfer|/addfile)[^\n]*(?:&&|\|)[^\n]*(?:call|cmd|start)` | 极高 | - |
| PowerShell 编码 | `powershell(?:\.exe)?\s+.*-enc` | 极高 | - |
| 注册表持久化 | `reg\s+add[^\n]*Run` | 高 | persist |
| 自删除 | `del\s+/[fq].*%0` | 高 | selfdelete |
| 磁盘格式化 | `format\s+[a-z]:` | 极高 | - |
| certutil 下载 | `certutil[^\n]*-urlcache[^\n]*-f` | 高 | download |
| curl 下载 | `curl\s+[^\n]*-o\s+\S+[^\n]*&&` | 中 | download |

### 4.5 Python

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| Base64 exec | `exec\s*\(\s*base64` | 高 | obfuscation |
| 下载执行 | `(?:urllib|requests)[^\n]*exec` | 极高 | - |
| subprocess + base64 | `subprocess[^\n]*base64` | 高 | obfuscation |
| 键盘记录 | `keyboard[^\n]*log|pynput[^\n]*Listener` | 中 | spy |
| 隐蔽执行 | `subprocess[^\n]*CREATE_NO_WINDOW` | 中 | stealth |
| 持久化 | `os\.system[^\n]*(?:crontab|schtasks)` | 高 | persist |

### 4.6 Shell

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| 下载执行 | `(?:curl|wget)[^\n]*\|\s*(?:ba)?sh` | 极高 | - |
| 反向 Shell | `bash\s+-i\s+>&\s*/dev/tcp` | 极高 | - |
| cron 持久化 | `crontab[^\n]*\|\s*sh` | 高 | persist |
| 清除日志 | `rm\s+-rf\s+/var/log` | 高 | selfdelete |
| 提权执行 | `sudo[^\n]*\|\s*sh` | 中 | priv-esc |

### 4.7 HTA / WSF / WSH

| 文件类型 | 模式 | 等级 | 标签 |
|----------|------|------|------|
| HTA | `CreateObject\s*\(\s*"WScript\.Shell"` | 高 | execute |
| HTA | `\.Run\s*\(` | 中 | execute |
| WSF/WSH | `CreateObject\s*\(\s*"WScript\.Shell"` | 中 | execute |

### 4.8 REG

| 模式 | 正则 | 等级 | 标签 |
|------|------|------|------|
| HKCU Run 持久化 | `\[HKEY_CURRENT_USER\\[^\]]*Run[^\]]*\]` | 高 | persist |
| HKLM Run 持久化 | `\[HKEY_LOCAL_MACHINE\\[^\]]*Run[^\]]*\]` | 高 | persist |

### 内容检测判定规则

- 匹配到"极高" → 恶意
- 匹配到 tag 组合 `{download, execute}` / `{download, persist}` / `{download, inject}` / `{persist, stealth}` → 恶意（组合行为）
- 匹配到 2+ "高" → 恶意
- 匹配到 1 "高" → 可疑
- 匹配到 1+ "中" → 可疑
- 无匹配 → 安全（在脚本维度）

## 5. Office 宏流检测（standard / deep）

对 `.doc/.xls/.ppt`（OLE）和 `.docx/.xlsx/.pptx/.docm/.xlsm/.pptm`（OOXML）检查是否携带 VBA。
**不执行宏，不解压到磁盘。**

### 5.1 OOXML

读取 ZIP 名单，命中 `word/vbaProject.bin`、`xl/vbaProject.bin`、`ppt/vbaProject.bin` 即视为含宏。
- `.docx/.xlsx/.pptx` 含宏流 → 可疑（扩展名声称无宏）
- `.docm/.xlsm/.pptm` 含宏流 → 继续读 bin 内标记：
  - `Auto_Open` / `Document_Open` / `Workbook_Open` 等自动执行 → 可疑
  - 同时出现 `CreateObject` / `powershell` / `WScript.Shell` 等 → 恶意
- 宏文档但找不到宏流 → 可疑（可能加密或结构异常）

### 5.2 OLE 复合文档

解析 CFB 目录流名（简化实现，不完整实现所有 OLE 变体）：
- 流名含 `vba` / `_vba_project` / `macros` → 含宏，判可疑
- 再在目录区搜索自动执行 / 危险 API 字节标记，组合命中 → 恶意
- 解析失败 → `low` 提示，不升级为可疑（避免旧版正常表格误报）

## 6. 压缩包内容检查（deep 策略）

### 6.1 ZIP

读取 ZIP 内部文件列表，并对每个条目**在内存中读取文件头**（默认前 1024 字节，条目数上限 500，单条目读取上限 8MB）：
- 内部是否包含可执行文件（exe/dll/scr/com 等）
- 内部文件是否有双扩展名
- 内部是否包含脚本文件（js/ps1/vbs/bat/cmd/hta）
- 内部文件头与扩展名是否一致（例如 `photo.jpg` 实际是 MZ / PNG）

判定：
- 压缩包内含双扩展名文件 → 恶意
- 压缩包内条目文件头为 MZ 且扩展名非可执行类型 → 恶意
- 压缩包内含可执行文件 → 可疑
- 压缩包内含脚本文件 → 可疑
- 压缩包内文件头与扩展名不一致（非 MZ） → 可疑
- 压缩包内只有文档/图片且文件头匹配 → 安全（在该维度）

### 6.2 RAR / 7Z

当前版本**依赖外部工具**（`unrar` / `7z`），未内置解析。命中时记录 `low` 级别提示：
```
{ext} 压缩包内检依赖外部工具，当前未解析
```
不阻塞扫描，不影响其他维度判定。若需完整内检，可安装 `unrar` / `p7zip` 后由 Agent 手动调用。

## 7. PE 导入表分析（deep 策略）

对 EXE/DLL/SCR/SYS/CPL/OCX 文件执行真实 PE 结构解析（非字符串搜索）：

### 7.1 解析流程

```
DOS Header (e_lfanew @ 0x3C)
  → PE Signature ("PE\0\0")
  → COFF Header (NumberOfSections, SizeOfOptionalHeader)
  → Optional Header (Magic: 0x10B=PE32 / 0x20B=PE32+)
  → DataDirectory[1] (Import Directory RVA)
  → Section Table (建立 RVA → File Offset 映射)
  → IMAGE_IMPORT_DESCRIPTOR 数组
  → OriginalFirstThunk / FirstThunk (Thunk 链)
  → IMAGE_IMPORT_BY_NAME (API 名称)
```

### 7.2 导入表可疑 API

| API | 风险 | 原因 |
|-----|------|------|
| CreateRemoteThread | 高 | 进程注入 |
| VirtualAllocEx | 高 | 跨进程内存分配 |
| WriteProcessMemory | 高 | 跨进程内存写入 |
| SetWindowsHookEx | 高 | 全局钩子安装 |
| URLDownloadToFile | 高 | 下载文件 |
| LoadLibraryA/W | 中 | 动态加载 DLL |
| GetProcAddress | 中 | 动态获取 API 地址 |
| RegSetValueEx | 中 | 注册表修改 |
| InternetOpenUrl | 中 | 网络请求 |
| WinExec / ShellExecute / ShellExecuteEx | 中 | 执行程序 |
| CreateProcess | 中 | 创建进程 |

### 7.3 组合判定

- 同时导入 `CreateRemoteThread + VirtualAllocEx + WriteProcessMemory`（≥2 个） → 恶意（进程注入）
- 同时导入 `URLDownloadToFile + WinExec/ShellExecute/ShellExecuteEx`（≥2 个） → 可疑（下载执行）
- 单独导入高风险 API（非组合） → 可疑
- 导入表为空或解析失败 → 可疑（可能是加壳/损坏/伪装）
- 文件超过 32MB 跳过 PE 分析 → medium 提示

## 8. LNK 目标检测（deep 策略）

对 `.lnk` 文件执行：

1. **签名校验**：首 4 字节应为 `4C 00 00 00`（Shell Link Header），否则 suspicious
2. **目标字符串检查**：读取前 256KB，搜索以下关键词，命中即 suspicious：
   - `powershell`、`wscript`、`cmd.exe`、`mshta`、`rundll32`、`regsvr32`
   - `\\`（网络路径，可能是 UNC 横向移动）

## 综合判定逻辑

单个文件可能触发多个检测维度，最终判定按优先级：

```
1. 恶意哈希匹配 → 恶意（直接判定，不看其他）
2. 文件头伪装（图片/文档扩展名 + MZ 签名，含 ZIP 内条目） → 恶意
3. 双扩展名伪装（含 ZIP 内条目） → 恶意
4. Office 宏 + 自动执行 + 危险 API 组合 → 恶意
5. 匹配"极高"内容模式 → 恶意
6. 脚本 tag 组合（download+execute 等） → 恶意
7. 匹配 2+ "高"内容模式 → 恶意
8. PE 进程注入 API 组合 → 恶意

否则：
9. 匹配 1 "高"内容模式 → 可疑
10. 匹配 1+ "中"内容模式 → 可疑
11. 文件头与扩展名不一致（非危险类型，含 ZIP 内） → 可疑
12. 无宏扩展名的 OOXML 含 vbaProject.bin → 可疑
13. OLE/宏文档含宏流或自动执行标记 → 可疑
14. 可疑命名（强/弱信号） → 可疑
15. 系统进程名在非系统目录 → 可疑
16. 随机命名 + 可执行扩展名 → 可疑
17. PE 下载执行组合 / 单个高风险 API → 可疑
18. PE 导入表为空/异常 → 可疑
19. ZIP 内可执行/脚本文件 → 可疑
20. RAR/7Z 未解析 / OLE 解析失败 → low 提示（不升级为可疑）
21. LNK 目标可疑 → 可疑

否则：
22. 所有维度通过 → 安全
23. 扫描失败（权限/损坏/超限） → 未能检查（unchecked）
```

### unchecked 判定条件

以下任一情况会将"看似安全"的文件标记为 `unchecked`：
- 文件元数据（stat）读取失败
- 文件头读取失败且无其他 finding
- 哈希计算失败且无其他 finding
- 脚本内容读取失败（权限/IO）
- 并发扫描时线程异常

报告会列出 unchecked 文件及原因，提醒用户手动复查。
