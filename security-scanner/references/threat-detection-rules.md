# 威胁检测规则

## 检测维度概览

| 维度 | 适用策略 | 检测内容 | 判定权重 |
|------|----------|----------|----------|
| 文件名特征 | quick/standard/deep | 双扩展名、可疑命名、伪装扩展名 | 中 |
| 文件头签名 | quick/standard/deep | 实际类型与扩展名是否匹配 | 高 |
| 文件哈希 | standard/deep | SHA256 与已知恶意哈希比对 | 极高 |
| 脚本内容模式 | standard/deep | 危险代码模式匹配 | 高 |
| 压缩包内容 | deep | 内部文件列表检查 | 中 |
| PE 结构分析 | deep | 导入表、节区特征 | 高 |

## 1. 文件名特征检测

### 1.1 双扩展名检测

文件名中出现两个或以上扩展名，且最后一个扩展名为"安全"类型（如 .txt, .jpg, .pdf），而前一个为"危险"类型（如 .exe, .scr, .com）。

判定规则：
- `report.pdf.exe` → 恶意（伪装 PDF 的 EXE）
- `photo.jpg.scr` → 恶意（伪装图片的 SCR）
- `data.txt.zip` → 安全（正常压缩包命名）
- `file.exe.txt` → 可疑（EXE 改名为 TXT，可能是隐藏执行）

危险扩展名集合：`.exe, .scr, .com, .bat, .cmd, .vbs, .ps1, .js, .jar, .msi, .dll, .lnk`

### 1.2 可疑命名模式

- 包含 `crack, keygen, patch, hack, cheat, bot, trainer, loader, injector, bypass` 等关键词
- 文件名完全由随机字符组成（如 `a1b2c3d4.exe`）
- 文件名伪装为系统文件（如 `svchost.exe` 在非系统目录）

判定：
- 系统目录（C:\Windows\System32）外的 `svchost.exe`, `csrss.exe`, `lsass.exe` → 可疑
- 包含破解/外挂关键词 → 可疑
- 随机命名 + 可执行扩展名 → 可疑

### 1.3 伪装扩展名

文件头签名显示为可执行文件，但扩展名为非可执行类型。

## 2. 文件头签名检测

读取文件前 64 字节，与已知文件签名比对。

### 常见文件签名

| 文件类型 | 签名（Hex） | 偏移 |
|----------|-------------|------|
| EXE/DLL | `4D 5A` (MZ) | 0 |
| ZIP | `50 4B 03 04` | 0 |
| RAR | `52 61 72 21` | 0 |
| 7Z | `37 7A BC AF 27 1C` | 0 |
| PDF | `25 50 44 46` (%PDF) | 0 |
| PNG | `89 50 4E 47` | 0 |
| JPG | `FF D8 FF` | 0 |
| GIF | `47 49 46 38` | 0 |
| MSI | `D0 CF 11 E0` (OLE) | 0 |
| DOC/XLS | `D0 CF 11 E0` (OLE) | 0 |
| DOCX/XLSX | `50 4B 03 04` (ZIP) | 0 |
| ELF | `7F 45 4C 46` | 0 |
| Mach-O | `FE ED FA CE/CF` | 0 |

### 判定规则

- 扩展名为 .exe 但文件头不是 MZ → 可疑（可能是伪装文件或损坏文件）
- 扩展名为 .jpg/.png/.gif 但文件头为 MZ → 恶意（伪装为图片的可执行文件）
- 扩展名为 .pdf 但文件头为 MZ → 恶意（伪装为 PDF 的可执行文件）
- 扩展名为 .txt 但文件头为 MZ → 恶意（伪装为文本的可执行文件）
- 文件头与扩展名不一致但都不是危险类型 → 可疑

## 3. 文件哈希检测

计算文件 SHA256 哈希值，与内置恶意哈希库比对。

### 内置哈希库

脚本内置少量已知恶意样本哈希用于演示。实际使用中，Agent 可根据用户需求扩展哈希库。

判定规则：
- 哈希匹配已知恶意样本 → 恶意
- 哈希不匹配 → 不影响其他检测结果

### 哈希库格式

```json
{
  "malicious_hashes": [
    {
      "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "name": "EICAR-Test-File",
      "description": "标准 antivirus 测试文件"
    }
  ]
}
```

## 4. 脚本内容模式检测

对 JS、PS1、VBS、BAT、CMD、PY、SH 文件进行内容扫描，匹配危险代码模式。

### 4.1 JavaScript 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| eval 执行编码数据 | `eval\s*\(\s*atob\s*\(` | 高 |
| 从远程下载并执行 | `\.downloadFile\s*\(.*\)\s*;\s*\.run\s*\(` | 高 |
| WScript.Shell 调用 | `WScript\.Shell` | 中 |
| ActiveX 对象创建 | `new\s+ActiveXObject\s*\(` | 中 |
| PowerShell 调用 | `powershell\s+.*-enc` | 高 |
| 混淆代码（长 hex 字符串） | `[0-9a-fA-F]{64,}` | 中 |
| document.write + 可执行内容 | `document\.write\s*\(.*\.exe` | 高 |

### 4.2 PowerShell 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| 编码命令执行 | `-EncodedCommand\s+` | 高 |
| 下载执行 | `Invoke-WebRequest.*\|\s*Invoke-Expression` | 高 |
| 隐藏窗口执行 | `-WindowStyle\s+Hidden` | 中 |
| 绕过执行策略 | `-ExecutionPolicy\s+Bypass` | 中 |
| 注册表持久化 | `Set-ItemProperty.*HKCU.*Run` | 高 |
| 反射加载 DLL | `Reflection\.Assembly]::Load` | 高 |
| Base64 编码内容 | `[A-Za-z0-9+/]{100,}={0,2}` | 中 |

### 4.3 VBS 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| CreateObject WScript.Shell | `CreateObject\s*\(\s*"WScript\.Shell"` | 中 |
| 下载并执行 | `\.downloadFile.*\.run` | 高 |
| 注册表操作 | `RegWrite` | 中 |
| 自删除 | `\.DeleteFile\s*\(\s*WScript` | 高 |

### 4.4 BAT/CMD 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| 下载并执行 | `bitsadmin.*transfer.*\|\s*call` | 高 |
| PowerShell 调用 | `powershell\s+.*-enc` | 高 |
| 注册表持久化 | `reg\s+add.*Run` | 高 |
| 自删除 | `del\s+/%0` | 高 |
| 磁盘格式化 | `format\s+[a-z]:` | 极高 |

### 4.5 Python 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| 执行编码数据 | `exec\s*\(\s*base64` | 高 |
| subprocess + 编码命令 | `subprocess.*base64` | 高 |
| 下载执行 | `urllib.*exec\|requests.*exec` | 高 |
| 键盘记录 | `keyboard.*log\|pynput.*Listener` | 中 |
| 隐蔽执行 | `subprocess.*CREATE_NO_WINDOW` | 中 |
| 持久化注入 | `os\.system.*crontab\|os\.system.*schtasks` | 高 |

### 4.6 Shell 危险模式

| 模式 | 正则 | 风险等级 |
|------|------|----------|
| 下载并执行 | `curl.*\|\s*sh\|wget.*\|\s*sh` | 高 |
| 反向连接 | `bash\s+-i\s+>&\s*/dev/tcp` | 极高 |
| 持久化 cron | `crontab.*\|\s*sh` | 高 |
| 清除日志 | `rm\s+-rf\s+/var/log` | 高 |
| 提权尝试 | `sudo\s+.*\|\s*sh` | 中 |

### 内容检测判定规则

- 匹配到"极高"风险模式 → 恶意
- 匹配到 2 个以上"高"风险模式 → 恶意
- 匹配到 1 个"高"风险模式 → 可疑
- 匹配到 2 个以上"中"风险模式 → 可疑
- 匹配到 1 个"中"风险模式 → 可疑（标注原因）
- 无匹配 → 安全（在脚本维度）

## 5. 压缩包内容检查（deep 策略）

读取 ZIP/RAR/7Z 内部文件列表（不解压），检查：

- 内部是否包含可执行文件（exe, dll, scr, com）
- 内部文件是否有双扩展名
- 内部是否包含脚本文件（js, ps1, vbs, bat）
- 压缩包内文件名是否可疑
- 是否包含自解压脚本

判定规则：
- 压缩包内含 exe + 双扩展名 → 恶意
- 压缩包内含可执行文件但外部扩展名伪装 → 可疑
- 压缩包内含脚本文件 → 可疑
- 压缩包内只有文档/图片 → 安全

## 6. PE 结构分析（deep 策略）

对 EXE/DLL 文件进行 PE 头解析：

### 6.1 PE 头基本检查

- 验证 MZ 头和 PE 签名完整性
- 检查节区数量和名称
- 检查入口点是否在合理范围

### 6.2 导入表可疑 API

| API | 风险等级 | 原因 |
|-----|----------|------|
| CreateRemoteThread | 高 | 进程注入 |
| VirtualAllocEx | 高 | 跨进程内存分配 |
| WriteProcessMemory | 高 | 跨进程内存写入 |
| LoadLibraryA/W | 中 | 动态加载 DLL |
| GetProcAddress | 中 | 动态获取 API 地址 |
| SetWindowsHookEx | 高 | 全局钩子安装 |
| RegSetValueEx | 中 | 注册表修改 |
| InternetOpenUrl | 中 | 网络请求 |
| URLDownloadToFile | 高 | 下载文件 |
| WinExec | 中 | 执行程序 |
| ShellExecute | 中 | 执行程序 |
| CreateProcess | 中 | 创建进程 |

判定规则：
- 导入表中同时存在 CreateRemoteThread + VirtualAllocEx + WriteProcessMemory → 恶意（进程注入组合）
- 导入 URLDownloadToFile + WinExec/ShellExecute → 可疑（下载执行组合）
- 导入表为空或异常 → 可疑
- 正常导入表 → 安全（在 PE 维度）

## 综合判定逻辑

单个文件可能触发多个检测维度，最终判定按优先级：

```
恶意哈希匹配 → 恶意（直接判定）
文件头伪装（图片/文档扩展名 + 可执行签名） → 恶意
匹配极高风险内容模式 → 恶意
匹配 2+ 高风险内容模式 → 恶意
进程注入 API 组合 → 恶意

否则：
匹配 1 高风险内容模式 → 可疑
匹配 2+ 中风险内容模式 → 可疑
文件头与扩展名不一致（非危险类型） → 可疑
双扩展名 → 可疑
可疑命名模式 → 可疑
压缩包内含可执行文件 → 可疑

否则：
所有检测维度通过 → 安全

扫描失败（权限/损坏/不支持） → 未能检查
```
