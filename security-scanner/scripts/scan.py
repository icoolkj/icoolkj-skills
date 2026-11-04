#!/usr/bin/env python3
"""
Security Scanner - 主扫描引擎
扫描本地目录中的文件，检测潜在恶意文件和可疑脚本。

用法:
    python scan.py --target <路径> --strategy <quick|standard|deep> \
        [--filter <扩展名列表>] [--exclude <正则/前缀>] [--jobs N] \
        [--output <结果JSON路径>] [--quiet] [--dry-run] [--version]

输出:
    stdout: JSON 格式扫描结果
    stderr: 进度信息
"""

import argparse
import hashlib
import json
import os
import re
import struct
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TOOL_VERSION = "1.1.0"
SCHEMA_VERSION = "1.0"

SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"

# 读取上限
MAX_SCRIPT_SIZE = 5 * 1024 * 1024       # 脚本内容分析上限 5 MB
MAX_PE_SIZE = 32 * 1024 * 1024           # PE 分析上限 32 MB
MAX_HEADER_SIZE = 1024

# ============================================================
# 文件签名库
# ============================================================
FILE_SIGNATURES = {
    "exe_dll": {"sig": b"\x4d\x5a", "offset": 0,
                "ext": [".exe", ".dll", ".scr", ".sys", ".cpl", ".com", ".ocx"]},
    "zip":     {"sig": b"\x50\x4b\x03\x04", "offset": 0,
                "ext": [".zip", ".docx", ".xlsx", ".pptx", ".docm", ".xlsm",
                        ".jar", ".apk", ".epub"]},
    "rar":     {"sig": b"\x52\x61\x72\x21", "offset": 0, "ext": [".rar"]},
    "7z":      {"sig": b"\x37\x7a\xbc\xaf\x27\x1c", "offset": 0, "ext": [".7z"]},
    "pdf":     {"sig": b"\x25\x50\x44\x46", "offset": 0, "ext": [".pdf"]},
    "png":     {"sig": b"\x89\x50\x4e\x47", "offset": 0, "ext": [".png"]},
    "jpg":     {"sig": b"\xff\xd8\xff", "offset": 0, "ext": [".jpg", ".jpeg"]},
    "gif":     {"sig": b"\x47\x49\x46\x38", "offset": 0, "ext": [".gif"]},
    "ole":     {"sig": b"\xd0\xcf\x11\xe0", "offset": 0,
                "ext": [".msi", ".doc", ".xls", ".ppt"]},
    "elf":     {"sig": b"\x7f\x45\x4c\x46", "offset": 0, "ext": [".elf", ".so"]},
    "lnk":     {"sig": b"\x4c\x00\x00\x00", "offset": 0, "ext": [".lnk"]},
    "rtf":     {"sig": b"{\\rtf", "offset": 0, "ext": [".rtf"]},
    "hta_sig": {"sig": b"<html", "offset": 0, "ext": []},  # 仅用于 HTA 内容识别
}

# 扩展名 → 预期签名
EXT_TO_SIG = {}
for _key, _info in FILE_SIGNATURES.items():
    for _ext in _info["ext"]:
        EXT_TO_SIG[_ext] = _key

# ============================================================
# 扩展名分类
# ============================================================
DANGEROUS_EXTS = {
    ".exe", ".scr", ".com", ".sys", ".cpl", ".ocx",
    ".bat", ".cmd", ".vbs", ".vbe", ".ps1", ".psm1",
    ".js", ".jse", ".jar", ".msi", ".dll", ".lnk",
    ".hta", ".wsf", ".wsh", ".msh", ".mshxml", ".reg",
}

SAFE_EXTS = {
    ".txt", ".jpg", ".jpeg", ".png", ".gif", ".pdf",
    ".doc", ".docx", ".docm", ".xls", ".xlsx", ".xlsm",
    ".rtf", ".mp3", ".mp4", ".avi", ".csv",
}

# 扩展名与真实类型的一致性检查例外（这些组合属于正常行为）
SIG_EXT_WHITELIST = {
    ("zip", ".docx"), ("zip", ".xlsx"), ("zip", ".pptx"),
    ("zip", ".docm"), ("zip", ".xlsm"),
    ("zip", ".jar"), ("zip", ".apk"), ("zip", ".epub"),
    ("ole", ".doc"), ("ole", ".xls"), ("ole", ".ppt"), ("ole", ".msi"),
}

# ============================================================
# 可疑命名（分强/弱信号）
# ============================================================
STRONG_NAME_KEYWORDS = [
    "crack", "keygen", "injector", "bypass", "keylogger", "ransom",
    "stealer", "backdoor", "rootkit", "trojan", "worm",
]
WEAK_NAME_KEYWORDS = [
    "patch", "hack", "cheat", "loader", "warez", "serial",
    "activation", "unlock",
]

SYSTEM_PROCESS_NAMES = {
    "svchost.exe", "csrss.exe", "lsass.exe", "winlogon.exe",
    "explorer.exe", "services.exe", "smss.exe", "wininit.exe",
    "spoolsv.exe", "taskmgr.exe", "rundll32.exe", "userinit.exe",
}
SYSTEM_DIR_PREFIXES = (
    "c:\\windows\\system32", "c:\\windows\\syswow64",
    "c:\\windows\\winsxs", "/usr/bin/", "/usr/sbin/", "/bin/", "/sbin/",
)

# ============================================================
# 恶意哈希（内置 fallback；真实 EICAR SHA256）
# ============================================================
DEFAULT_MALICIOUS_HASHES = {
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f":
        "EICAR-Test-File (标准防病毒测试文件)",
}

# ============================================================
# 脚本内容规则（带 tag，支持组合语义判定）
# ============================================================
SCRIPT_RULES = {
    ".js": [
        {"pattern": r"eval\s*\(\s*atob\s*\(", "level": "high", "tag": "obfuscation",
         "desc": "eval 执行 Base64 编码数据"},
        {"pattern": r"\.downloadFile\s*\([^)]*\)[^;]*;\s*[^;]*\.run\s*\(",
         "level": "critical", "desc": "下载并执行文件"},
        {"pattern": r"WScript\.Shell", "level": "medium", "tag": "execute",
         "desc": "创建 WScript.Shell 对象"},
        {"pattern": r"new\s+ActiveXObject\s*\(", "level": "medium",
         "desc": "创建 ActiveX 对象"},
        {"pattern": r"powershell(?:\.exe)?\s+.*-enc(?:odedcommand)?",
         "level": "critical", "desc": "调用 PowerShell 编码命令"},
        {"pattern": r"[0-9a-fA-F]{64,}", "level": "medium", "tag": "obfuscation",
         "desc": "长 Hex 字符串（可能混淆代码）"},
        {"pattern": r"document\.write\s*\([^)]*\.exe", "level": "high", "tag": "execute",
         "desc": "document.write 写入 EXE"},
        {"pattern": r"XMLHTTP", "level": "medium", "tag": "download",
         "desc": "XMLHTTP 网络请求"},
    ],
    ".ps1": [
        {"pattern": r"-EncodedCommand\s+", "level": "critical",
         "desc": "使用编码命令执行"},
        {"pattern": r"Invoke-WebRequest[^\n]*\|\s*Invoke-Expression",
         "level": "critical", "desc": "下载并执行远程代码"},
        {"pattern": r"IEX\s*\(\s*New-Object\s+Net\.WebClient",
         "level": "critical", "desc": "IEX 下载并执行远程代码"},
        {"pattern": r"-WindowStyle\s+Hidden", "level": "medium", "tag": "stealth",
         "desc": "隐藏窗口执行"},
        {"pattern": r"-ExecutionPolicy\s+Bypass", "level": "medium", "tag": "stealth",
         "desc": "绕过执行策略"},
        {"pattern": r"Set-ItemProperty[^\n]*HKCU[^\n]*Run",
         "level": "high", "tag": "persist", "desc": "注册表持久化"},
        {"pattern": r"\[Reflection\.Assembly\]::Load", "level": "high", "tag": "inject",
         "desc": "反射加载 DLL"},
        {"pattern": r"[A-Za-z0-9+/]{100,}={0,2}", "level": "medium", "tag": "obfuscation",
         "desc": "长 Base64 字符串"},
        {"pattern": r"DownloadString|DownloadFile", "level": "high", "tag": "download",
         "desc": "下载远程内容"},
        {"pattern": r"(?:Start-Process|Invoke-Expression|&)\s+\$",
         "level": "high", "tag": "execute", "desc": "执行动态内容"},
    ],
    ".psm1": [
        {"pattern": r"-EncodedCommand\s+", "level": "critical",
         "desc": "使用编码命令执行"},
        {"pattern": r"Invoke-WebRequest[^\n]*\|\s*Invoke-Expression",
         "level": "critical", "desc": "下载并执行远程代码"},
        {"pattern": r"\[Reflection\.Assembly\]::Load", "level": "high", "tag": "inject",
         "desc": "反射加载 DLL"},
        {"pattern": r"DownloadString|DownloadFile", "level": "high", "tag": "download",
         "desc": "下载远程内容"},
    ],
    ".vbs": [
        {"pattern": r'CreateObject\s*\(\s*"WScript\.Shell"', "level": "medium",
         "tag": "execute", "desc": "创建 WScript.Shell"},
        {"pattern": r"\.downloadFile[^\n]*\.run", "level": "critical",
         "desc": "下载并执行文件"},
        {"pattern": r"RegWrite", "level": "medium", "tag": "persist",
         "desc": "注册表写入操作"},
        {"pattern": r"\.DeleteFile\s*\(\s*WScript", "level": "high", "tag": "selfdelete",
         "desc": "自删除行为"},
    ],
    ".vbe": [
        {"pattern": r".", "level": "medium", "desc": "VBE 编码脚本（需解码后再判定）"},
    ],
    ".bat": [
        {"pattern": r"bitsadmin[^\n]*(?:transfer|/addfile)[^\n]*(?:&&|\|)[^\n]*(?:call|cmd|start)",
         "level": "critical", "desc": "bitsadmin 下载并执行"},
        {"pattern": r"powershell(?:\.exe)?\s+.*-enc", "level": "critical",
         "desc": "调用 PowerShell 编码命令"},
        {"pattern": r"reg\s+add[^\n]*Run", "level": "high", "tag": "persist",
         "desc": "注册表持久化"},
        {"pattern": r"del\s+/[fq].*%0", "level": "high", "tag": "selfdelete",
         "desc": "自删除"},
        {"pattern": r"format\s+[a-z]:", "level": "critical", "desc": "磁盘格式化命令"},
        {"pattern": r"certutil[^\n]*-urlcache[^\n]*-f", "level": "high",
         "tag": "download", "desc": "certutil 下载文件"},
        {"pattern": r"curl\s+[^\n]*-o\s+\S+[^\n]*&&", "level": "medium",
         "tag": "download", "desc": "curl 下载"},
    ],
    ".cmd": [
        {"pattern": r"bitsadmin[^\n]*(?:transfer|/addfile)[^\n]*(?:&&|\|)[^\n]*(?:call|cmd|start)",
         "level": "critical", "desc": "bitsadmin 下载并执行"},
        {"pattern": r"powershell(?:\.exe)?\s+.*-enc", "level": "critical",
         "desc": "调用 PowerShell 编码命令"},
        {"pattern": r"reg\s+add[^\n]*Run", "level": "high", "tag": "persist",
         "desc": "注册表持久化"},
        {"pattern": r"del\s+/[fq].*%0", "level": "high", "tag": "selfdelete",
         "desc": "自删除"},
        {"pattern": r"format\s+[a-z]:", "level": "critical", "desc": "磁盘格式化命令"},
    ],
    ".py": [
        {"pattern": r"exec\s*\(\s*base64", "level": "high", "tag": "obfuscation",
         "desc": "执行 Base64 编码数据"},
        {"pattern": r"(?:urllib|requests)[^\n]*exec", "level": "critical",
         "desc": "下载并执行远程代码"},
        {"pattern": r"subprocess[^\n]*base64", "level": "high",
         "tag": "obfuscation", "desc": "subprocess 执行编码命令"},
        {"pattern": r"keyboard[^\n]*log|pynput[^\n]*Listener",
         "level": "medium", "tag": "spy", "desc": "键盘记录行为"},
        {"pattern": r"subprocess[^\n]*CREATE_NO_WINDOW",
         "level": "medium", "tag": "stealth", "desc": "隐蔽执行（无窗口）"},
        {"pattern": r"os\.system[^\n]*(?:crontab|schtasks)",
         "level": "high", "tag": "persist", "desc": "持久化注入"},
    ],
    ".sh": [
        {"pattern": r"(?:curl|wget)[^\n]*\|\s*(?:ba)?sh", "level": "critical",
         "desc": "下载并执行远程脚本"},
        {"pattern": r"bash\s+-i\s+>&\s*/dev/tcp", "level": "critical",
         "desc": "反向 Shell 连接"},
        {"pattern": r"crontab[^\n]*\|\s*sh", "level": "high", "tag": "persist",
         "desc": "cron 持久化"},
        {"pattern": r"rm\s+-rf\s+/var/log", "level": "high", "tag": "selfdelete",
         "desc": "清除系统日志"},
        {"pattern": r"sudo[^\n]*\|\s*sh", "level": "medium", "tag": "priv-esc",
         "desc": "提权后执行脚本"},
    ],
    ".hta": [
        {"pattern": r"CreateObject\s*\(\s*\"WScript\.Shell\"", "level": "high",
         "tag": "execute", "desc": "HTA 内创建 WScript.Shell"},
        {"pattern": r"\.Run\s*\(", "level": "medium", "tag": "execute",
         "desc": "HTA 内执行命令"},
    ],
    ".wsf": [
        {"pattern": r"CreateObject\s*\(\s*\"WScript\.Shell\"", "level": "medium",
         "tag": "execute", "desc": "WSF 内创建 WScript.Shell"},
    ],
    ".wsh": [
        {"pattern": r"CreateObject\s*\(\s*\"WScript\.Shell\"", "level": "medium",
         "tag": "execute", "desc": "WSH 内创建 WScript.Shell"},
    ],
    ".reg": [
        {"pattern": r"\[HKEY_CURRENT_USER\\[^\]]*Run[^\]]*\]",
         "level": "high", "tag": "persist", "desc": "注册表 Run 键持久化"},
        {"pattern": r"\[HKEY_LOCAL_MACHINE\\[^\]]*Run[^\]]*\]",
         "level": "high", "tag": "persist", "desc": "注册表 Run 键持久化"},
    ],
}

# ============================================================
# PE 可疑 API
# ============================================================
SUSPICIOUS_PE_APIS = {
    "CreateRemoteThread": "high",
    "VirtualAllocEx": "high",
    "WriteProcessMemory": "high",
    "SetWindowsHookEx": "high",
    "URLDownloadToFile": "high",
    "LoadLibraryA": "medium",
    "LoadLibraryW": "medium",
    "GetProcAddress": "medium",
    "RegSetValueEx": "medium",
    "InternetOpenUrl": "medium",
    "WinExec": "medium",
    "ShellExecute": "medium",
    "ShellExecuteEx": "medium",
    "CreateProcess": "medium",
}
PROCESS_INJECTION_COMBO = {"CreateRemoteThread", "VirtualAllocEx", "WriteProcessMemory"}
DOWNLOAD_EXEC_COMBO = {"URLDownloadToFile", "WinExec", "ShellExecute", "ShellExecuteEx"}

# ============================================================
# 默认排除
# ============================================================
DEFAULT_EXCLUDE_PATTERNS = [
    r"[\\/]node_modules[\\/]", r"[\\/]\.git[\\/]", r"[\\/]\.svn[\\/]",
    r"[\\/]Windows[\\/]WinSxS[\\/]", r"[\\/]\$Recycle\.Bin",
    r"[\\/]System Volume Information",
    r"__pycache__", r"[\\/]\.cache[\\/]",
]

# ============================================================
# 工具函数
# ============================================================
def get_file_ext(filepath):
    return Path(filepath).suffix.lower()


def read_file_header(filepath, size=64):
    try:
        with open(filepath, "rb") as f:
            return f.read(size)
    except (IOError, OSError, PermissionError):
        return None


def compute_sha256(filepath):
    try:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except (IOError, OSError, PermissionError):
        return None


def detect_file_type(header):
    if header is None or len(header) < 2:
        return None
    for sig_key, sig_info in FILE_SIGNATURES.items():
        sig = sig_info["sig"]
        off = sig_info["offset"]
        if header[off:off + len(sig)] == sig:
            return sig_key
    return None


def read_text_with_fallback(filepath, max_size):
    """返回 (text, error_reason)。多编码回退。"""
    try:
        size = os.path.getsize(filepath)
    except (OSError, PermissionError) as e:
        return None, f"无法获取文件大小: {e}"
    if size > max_size:
        return None, f"文件过大（{size} 字节），跳过内容分析"
    try:
        with open(filepath, "rb") as f:
            raw = f.read(max_size)
    except (OSError, PermissionError) as e:
        return None, f"读取失败: {e}"
    for enc in ("utf-8", "gbk", "utf-16", "latin-1"):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace"), None


def is_in_system_dir(filepath):
    norm = os.path.abspath(filepath).lower().replace("/", "\\")
    norm_slash = norm.replace("\\", "/")
    for prefix in SYSTEM_DIR_PREFIXES:
        if prefix.endswith("/"):
            if norm_slash.startswith(prefix.lower()) or ("/" + prefix.lower().lstrip("/")) in norm_slash:
                return True
        else:
            if norm.startswith(prefix) or ("\\" + prefix.lstrip("\\")) in norm:
                return True
    return False


# ============================================================
# 文件名检测
# ============================================================
def is_double_extension(filepath):
    """覆盖 .safe.dangerous、.dangerous.safe 以及多段扩展名。"""
    name = Path(filepath).name.strip().rstrip(". ")  # Windows 忽略尾部点/空格
    parts = name.split(".")
    if len(parts) < 3:
        return None
    exts = ["." + p.lower() for p in parts[1:] if p]
    if not exts:
        return None
    last = exts[-1]
    prev = exts[:-1]
    # 危险扩展名出现在"非末位"位置，视为伪装
    for i, e in enumerate(prev):
        if e in DANGEROUS_EXTS and last in SAFE_EXTS:
            return f"双扩展名伪装: 可执行段 {e} 伪装为 {last} ({'.'.join(parts)})"
    # 末位危险 + 前有安全扩展名
    if last in DANGEROUS_EXTS:
        for e in prev:
            if e in SAFE_EXTS:
                return f"双扩展名伪装: 伪装为 {e} 的可执行文件 ({'.'.join(parts)})"
    return None


def has_suspicious_name(filepath):
    findings = []
    name = Path(filepath).name.lower()
    ext = get_file_ext(filepath)
    for kw in STRONG_NAME_KEYWORDS:
        if kw in name:
            findings.append({"level": "suspicious", "reason": f"文件名含强可疑关键词: {kw}"})
    for kw in WEAK_NAME_KEYWORDS:
        if kw in name and ext in DANGEROUS_EXTS:
            findings.append({"level": "suspicious", "reason": f"可执行文件名含可疑关键词: {kw}"})
    if name in SYSTEM_PROCESS_NAMES and not is_in_system_dir(filepath):
        findings.append({"level": "suspicious",
                         "reason": f"系统进程名出现在非系统目录: {name}"})
    return findings


def is_random_name(filepath):
    stem = Path(filepath).stem
    if len(stem) < 8:
        return False
    has_alpha = any(c.isalpha() for c in stem)
    has_digit = any(c.isdigit() for c in stem)
    if not (has_alpha and has_digit):
        return False
    meaningful = ["readme", "license", "setup", "install", "update", "config",
                  "data", "test", "demo", "sample", "example", "release", "debug"]
    low = stem.lower()
    if any(w in low for w in meaningful):
        return False
    vowels = sum(1 for c in low if c in "aeiou")
    if vowels / max(len(low), 1) < 0.15:
        return True
    return False


def check_filename_features(filepath):
    findings = []
    d = is_double_extension(filepath)
    if d:
        findings.append({"level": "malicious", "reason": d})
    findings.extend(has_suspicious_name(filepath))
    if is_random_name(filepath) and get_file_ext(filepath) in DANGEROUS_EXTS:
        findings.append({"level": "suspicious", "reason": "随机命名 + 可执行扩展名"})
    return findings


# ============================================================
# 签名检测
# ============================================================
def check_file_signature(filepath):
    findings = []
    header = read_file_header(filepath, MAX_HEADER_SIZE)
    if header is None:
        return findings, None, "读取文件头失败"
    actual = detect_file_type(header)
    ext = get_file_ext(filepath)

    if actual is None:
        return findings, None, None

    if (actual, ext) in SIG_EXT_WHITELIST:
        return findings, actual, None

    if ext in EXT_TO_SIG:
        expected = EXT_TO_SIG[ext]
        if actual != expected:
            if actual == "exe_dll" and ext not in DANGEROUS_EXTS:
                findings.append({"level": "malicious",
                                 "reason": f"文件头为可执行(MZ)，扩展名为 {ext}（伪装）"})
            else:
                findings.append({"level": "suspicious",
                                 "reason": f"文件头类型({actual})与扩展名({ext})不一致"})
    else:
        if actual == "exe_dll" and ext not in DANGEROUS_EXTS:
            findings.append({"level": "malicious",
                             "reason": f"文件头为可执行(MZ)，扩展名为 {ext or '(无)'}（伪装）"})
    return findings, actual, None


# ============================================================
# 哈希检测
# ============================================================
def check_hash(filepath, malicious_hashes):
    findings = []
    sha = compute_sha256(filepath)
    if sha is None:
        return findings, None, "计算哈希失败"
    if sha in malicious_hashes:
        findings.append({"level": "malicious",
                         "reason": f"哈希匹配已知恶意样本: {malicious_hashes[sha]}"})
    return findings, sha, None


# ============================================================
# 脚本内容检测
# ============================================================
def check_script_content(filepath):
    findings = []
    ext = get_file_ext(filepath)
    if ext not in SCRIPT_RULES:
        return findings, None

    content, err = read_text_with_fallback(filepath, MAX_SCRIPT_SIZE)
    if content is None:
        return findings, err

    for rule in SCRIPT_RULES[ext]:
        try:
            matched = re.findall(rule["pattern"], content, re.IGNORECASE)
        except re.error:
            continue
        if matched:
            item = {"level": rule["level"], "reason": f"匹配规则: {rule['desc']}"}
            if "tag" in rule:
                item["tag"] = rule["tag"]
            findings.append(item)
    return findings, None


# ============================================================
# 压缩包检查
# ============================================================
def check_archive_content(filepath):
    findings = []
    ext = get_file_ext(filepath)
    if ext == ".zip":
        try:
            import zipfile
            with zipfile.ZipFile(filepath, "r") as zf:
                names = zf.namelist()
        except Exception:
            return findings
        for name in names:
            inner_ext = Path(name).suffix.lower()
            if inner_ext in DANGEROUS_EXTS:
                d = is_double_extension(name)
                if d:
                    findings.append({"level": "malicious",
                                     "reason": f"压缩包内含双扩展名文件: {name}"})
                else:
                    findings.append({"level": "suspicious",
                                     "reason": f"压缩包内含可执行文件: {name}"})
            elif inner_ext in (".js", ".ps1", ".vbs", ".bat", ".cmd", ".hta"):
                findings.append({"level": "suspicious",
                                 "reason": f"压缩包内含脚本文件: {name}"})
    elif ext in (".rar", ".7z"):
        findings.append({"level": "low",
                         "reason": f"{ext} 压缩包内检依赖外部工具，当前未解析"})
    return findings


# ============================================================
# PE 导入表解析
# ============================================================
def _parse_pe_imports(data):
    """解析 PE 导入表，返回 API 名称集合；失败返回 None。"""
    if len(data) < 0x40 or data[:2] != b"MZ":
        return None
    try:
        e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
        if e_lfanew + 0x18 > len(data):
            return None
        if data[e_lfanew:e_lfanew + 4] != b"PE\x00\x00":
            return None
        coff_off = e_lfanew + 4
        num_sections = struct.unpack_from("<H", data, coff_off + 2)[0]
        size_opt = struct.unpack_from("<H", data, coff_off + 16)[0]
        opt_off = coff_off + 20
        magic = struct.unpack_from("<H", data, opt_off)[0]
        if magic == 0x10b:
            dd_off, ptr_size = opt_off + 96, 4
        elif magic == 0x20b:
            dd_off, ptr_size = opt_off + 112, 8
        else:
            return None
        if dd_off + 16 > opt_off + size_opt:
            return None
        import_rva, _ = struct.unpack_from("<II", data, dd_off + 8)
        if import_rva == 0:
            return set()

        sec_off = opt_off + size_opt
        sections = []
        for i in range(num_sections):
            s_off = sec_off + i * 40
            if s_off + 40 > len(data):
                return None
            vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, s_off + 8)
            sections.append((vaddr, vsize, rawptr, rawsize))

        def rva_to_off(rva):
            for vaddr, vsize, rawptr, rawsize in sections:
                span = max(vsize, rawsize)
                if vaddr <= rva < vaddr + span:
                    delta = rva - vaddr
                    if delta < rawsize:
                        return rawptr + delta
            return None

        desc_off = rva_to_off(import_rva)
        if desc_off is None:
            return None

        imports = set()
        for i in range(1024):
            d_off = desc_off + i * 20
            if d_off + 20 > len(data):
                break
            oft, _ts, _fc, _name_rva, ft = struct.unpack_from("<IIIII", data, d_off)
            if _name_rva == 0 and oft == 0 and ft == 0:
                break
            thunk_rva = oft if oft else ft
            thunk_off = rva_to_off(thunk_rva)
            if thunk_off is None:
                continue
            j = 0
            while j < 8192:
                t_off = thunk_off + j * ptr_size
                if t_off + ptr_size > len(data):
                    break
                if ptr_size == 8:
                    val = struct.unpack_from("<Q", data, t_off)[0]
                else:
                    val = struct.unpack_from("<I", data, t_off)[0]
                if val == 0:
                    break
                high_bit = 1 << (ptr_size * 8 - 1)
                if not (val & high_bit):
                    name_off = rva_to_off(val & 0x7FFFFFFF)
                    if name_off is not None and name_off + 2 < len(data):
                        end = data.find(b"\x00", name_off + 2,
                                        min(len(data), name_off + 2 + 256))
                        if end != -1:
                            try:
                                imports.add(data[name_off + 2:end].decode("ascii"))
                            except UnicodeDecodeError:
                                pass
                j += 1
        return imports
    except (struct.error, IndexError):
        return None


def check_pe_structure(filepath):
    findings = []
    ext = get_file_ext(filepath)
    if ext not in (".exe", ".dll", ".scr", ".sys", ".cpl", ".com", ".ocx"):
        return findings
    try:
        size = os.path.getsize(filepath)
    except OSError:
        return findings
    if size > MAX_PE_SIZE:
        findings.append({"level": "medium",
                         "reason": f"文件过大（{size} 字节），跳过 PE 结构分析"})
        return findings
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except (OSError, PermissionError) as e:
        findings.append({"level": "low", "reason": f"PE 读取失败: {e}"})
        return findings
    if data[:2] != b"MZ":
        return findings

    imports = _parse_pe_imports(data)
    if imports is None:
        findings.append({"level": "suspicious", "reason": "PE 头解析失败或格式异常"})
        return findings
    if not imports:
        findings.append({"level": "suspicious", "reason": "PE 导入表为空或无法解析"})
        return findings

    found = {api: level for api, level in SUSPICIOUS_PE_APIS.items() if api in imports}
    injection = PROCESS_INJECTION_COMBO & imports
    download = DOWNLOAD_EXEC_COMBO & imports

    if len(injection) >= 2:
        findings.append({"level": "malicious",
                         "reason": f"导入进程注入 API 组合: {', '.join(sorted(injection))}"})
    if len(download) >= 2:
        findings.append({"level": "suspicious",
                         "reason": f"导入下载执行 API 组合: {', '.join(sorted(download))}"})
    for api, lvl in found.items():
        if api in injection or api in download:
            continue
        if lvl == "high":
            findings.append({"level": "suspicious",
                             "reason": f"导入高风险 API: {api}"})
    return findings


# ============================================================
# LNK 检测
# ============================================================
def check_lnk(filepath):
    findings = []
    ext = get_file_ext(filepath)
    if ext != ".lnk":
        return findings
    header = read_file_header(filepath, 64)
    if not header:
        return findings
    if header[:4] != b"\x4c\x00\x00\x00":
        findings.append({"level": "suspicious", "reason": ".lnk 签名异常"})
        return findings
    text, _ = read_text_with_fallback(filepath, 256 * 1024)
    if text is None:
        return findings
    low = text.lower()
    for suspicious in ("powershell", "wscript", "cmd.exe", "mshta", "rundll32",
                       "regsvr32", "\\\\"):
        if suspicious in low:
            findings.append({"level": "suspicious",
                             "reason": f".lnk 目标疑似包含 {suspicious}"})
            break
    return findings


# ============================================================
# 综合判定
# ============================================================
def classify_file(findings):
    if not findings:
        return "safe", "所有检测维度通过"

    levels = {f["level"] for f in findings}
    if "malicious" in levels or "critical" in levels:
        reasons = [f["reason"] for f in findings if f["level"] in ("malicious", "critical")]
        return "malicious", "; ".join(reasons)

    tags = {f["tag"] for f in findings if "tag" in f}
    combos = [{"download", "execute"}, {"download", "persist"},
              {"download", "inject"}, {"persist", "stealth"}]
    for combo in combos:
        if combo.issubset(tags):
            reasons = [f["reason"] for f in findings if f.get("tag") in combo]
            return "malicious", "组合行为: " + "; ".join(reasons)

    high = sum(1 for f in findings if f["level"] == "high")
    if high >= 2:
        return "malicious", f"匹配 {high} 个高风险模式"

    if "suspicious" in levels or high >= 1:
        reasons = [f["reason"] for f in findings if f["level"] in ("suspicious", "high")]
        return "suspicious", "; ".join(reasons)

    medium = sum(1 for f in findings if f["level"] == "medium")
    if medium >= 1:
        reasons = [f["reason"] for f in findings if f["level"] == "medium"]
        return "suspicious", "; ".join(reasons)

    # 只剩 low：不作为风险，但记录原因供报告展示
    reasons = [f["reason"] for f in findings if f["level"] == "low"]
    return "safe", "; ".join(reasons) if reasons else "所有检测维度通过"


# ============================================================
# 扫描
# ============================================================
def scan_file(filepath, strategy, malicious_hashes):
    result = {
        "path": filepath,
        "name": Path(filepath).name,
        "size": 0,
        "ext": get_file_ext(filepath),
        "actual_type": None,
        "mtime": None,
        "classification": "safe",
        "reason": "",
        "findings": [],
        "sha256": None,
    }

    read_errors = []
    try:
        st = os.stat(filepath)
        result["size"] = st.st_size
        result["mtime"] = int(st.st_mtime)
    except (OSError, PermissionError) as e:
        result["classification"] = "unchecked"
        result["reason"] = f"无法读取文件元数据: {e}"
        return result

    all_findings = []

    # 1. 文件名特征
    all_findings.extend(check_filename_features(filepath))

    # 2. 文件头签名
    sig_findings, actual_type, sig_err = check_file_signature(filepath)
    all_findings.extend(sig_findings)
    result["actual_type"] = actual_type
    if sig_err:
        read_errors.append(sig_err)

    if strategy in ("standard", "deep"):
        # 3. 哈希
        hash_findings, sha, hash_err = check_hash(filepath, malicious_hashes)
        all_findings.extend(hash_findings)
        result["sha256"] = sha
        if hash_err:
            read_errors.append(hash_err)

        # 4. 脚本内容
        content_findings, content_err = check_script_content(filepath)
        all_findings.extend(content_findings)
        if content_err:
            read_errors.append(content_err)

    if strategy == "deep":
        # 5. 压缩包
        all_findings.extend(check_archive_content(filepath))
        # 6. PE
        all_findings.extend(check_pe_structure(filepath))
        # 7. LNK
        all_findings.extend(check_lnk(filepath))

    result["findings"] = all_findings
    classification, reason = classify_file(all_findings)
    result["classification"] = classification
    result["reason"] = reason

    if classification == "safe" and read_errors and \
            not sig_findings and result["sha256"] is None:
        # 所有读取都失败且无检测结果
        result["classification"] = "unchecked"
        result["reason"] = "; ".join(read_errors)
    return result


def collect_files(target, filter_exts, exclude_patterns):
    compiled = [re.compile(p, re.IGNORECASE) for p in exclude_patterns]

    def excluded(path):
        return any(p.search(path) for p in compiled)

    files = []
    if os.path.isfile(target):
        if filter_exts is None or get_file_ext(target) in filter_exts:
            files = [target]
        return files

    if not os.path.isdir(target):
        print(f"错误: 目标路径不存在: {target}", file=sys.stderr)
        sys.exit(1)

    for root, dirs, filenames in os.walk(target, followlinks=False):
        # 目录剪枝
        dirs[:] = [d for d in dirs if not excluded(os.path.join(root, d))]
        for filename in filenames:
            filepath = os.path.join(root, filename)
            if excluded(filepath):
                continue
            ext = get_file_ext(filepath)
            if filter_exts is None or ext in filter_exts:
                files.append(filepath)
    return files


def run_scan(target, strategy, filter_exts, excludes, jobs, quiet, malicious_hashes):
    start = time.time()
    if not quiet:
        print(f"扫描目标: {target}", file=sys.stderr)
        print(f"扫描策略: {strategy}", file=sys.stderr)
        print(f"文件过滤: {sorted(filter_exts) if filter_exts else '全部类型'}",
              file=sys.stderr)
        print(f"排除规则: {len(excludes)} 条", file=sys.stderr)

    files = collect_files(target, filter_exts, excludes)
    total = len(files)
    if not quiet:
        print(f"待扫描文件数: {total}", file=sys.stderr, flush=True)

    results = [None] * total
    if jobs <= 1:
        for i, fp in enumerate(files):
            if not quiet:
                el = time.time() - start
                print(f"[{i+1}/{total}] ({el:.1f}s) {fp}", file=sys.stderr, flush=True)
            results[i] = scan_file(fp, strategy, malicious_hashes)
    else:
        with ThreadPoolExecutor(max_workers=jobs) as ex:
            futures = {ex.submit(scan_file, fp, strategy, malicious_hashes): i
                       for i, fp in enumerate(files)}
            done = 0
            for fut in as_completed(futures):
                idx = futures[fut]
                try:
                    results[idx] = fut.result()
                except Exception as e:
                    results[idx] = {
                        "path": files[idx], "name": Path(files[idx]).name,
                        "size": 0, "ext": get_file_ext(files[idx]),
                        "actual_type": None, "mtime": None,
                        "classification": "unchecked",
                        "reason": f"扫描异常: {e}", "findings": [], "sha256": None,
                    }
                done += 1
                if not quiet:
                    el = time.time() - start
                    print(f"[{done}/{total}] ({el:.1f}s) {files[idx]}",
                          file=sys.stderr, flush=True)

    elapsed = time.time() - start
    if not quiet:
        print(f"\n扫描完成! 耗时: {elapsed:.1f}s, 文件数: {total}",
              file=sys.stderr, flush=True)

    stats = {
        "total": total,
        "safe": sum(1 for r in results if r["classification"] == "safe"),
        "suspicious": sum(1 for r in results if r["classification"] == "suspicious"),
        "malicious": sum(1 for r in results if r["classification"] == "malicious"),
        "unchecked": sum(1 for r in results if r["classification"] == "unchecked"),
        "elapsed": round(elapsed, 2),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "scan_info": {
            "target": target,
            "strategy": strategy,
            "filter": sorted(filter_exts) if filter_exts else None,
            "exclude": excludes,
            "start_time": start,
            "elapsed": stats["elapsed"],
            "total_files": total,
        },
        "stats": stats,
        "results": results,
    }


def load_malicious_hashes():
    hashes = dict(DEFAULT_MALICIOUS_HASHES)
    path = REFERENCES_DIR / "hashes.json"
    if not path.exists():
        return hashes
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("malicious_hashes", []):
            sha = item.get("sha256", "").lower()
            if sha:
                hashes[sha] = item.get("name", "外部哈希库条目")
    except (OSError, json.JSONDecodeError) as e:
        print(f"警告: 外部哈希库加载失败: {e}", file=sys.stderr)
    return hashes


def main():
    parser = argparse.ArgumentParser(
        description="Security Scanner - 本地文件安全查杀工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", help="扫描目标路径（文件/文件夹/磁盘根目录）")
    parser.add_argument("--strategy", choices=["quick", "standard", "deep"],
                        default="standard", help="扫描策略（默认: standard）")
    parser.add_argument("--filter", default=None,
                        help="扩展名过滤，逗号分隔（如: exe,dll,js,ps1）")
    parser.add_argument("--exclude", action="append", default=None,
                        help="额外排除模式（正则），可多次指定")
    parser.add_argument("--jobs", type=int, default=1,
                        help="并发线程数（默认 1；I/O 密集场景可调大）")
    parser.add_argument("--output", default=None, help="结果 JSON 输出路径")
    parser.add_argument("--quiet", action="store_true", help="不输出进度信息")
    parser.add_argument("--dry-run", action="store_true",
                        help="仅列出将扫描的文件，不实际检测")
    parser.add_argument("--version", action="store_true", help="显示版本并退出")

    args = parser.parse_args()

    if args.version:
        print(f"security-scanner {TOOL_VERSION} (schema {SCHEMA_VERSION})")
        return

    if not args.target:
        parser.error("--target 是必需参数（除非使用 --version）")

    filter_exts = None
    if args.filter:
        filter_exts = set()
        for ext in args.filter.split(","):
            ext = ext.strip().lower()
            if not ext:
                continue
            if not ext.startswith("."):
                ext = "." + ext
            filter_exts.add(ext)

    excludes = list(DEFAULT_EXCLUDE_PATTERNS) + (args.exclude or [])

    if args.dry_run:
        files = collect_files(args.target, filter_exts, excludes)
        print(f"dry-run: 将扫描 {len(files)} 个文件", file=sys.stderr)
        for fp in files:
            print(fp)
        return

    malicious_hashes = load_malicious_hashes()
    output = run_scan(args.target, args.strategy, filter_exts, excludes,
                      args.jobs, args.quiet, malicious_hashes)

    json_output = json.dumps(output, ensure_ascii=False, indent=2)
    print(json_output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        if not args.quiet:
            print(f"结果已保存到: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
