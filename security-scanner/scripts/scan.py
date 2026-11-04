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
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TOOL_VERSION = "1.2.0"
SCHEMA_VERSION = "1.0"

SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"
HASH_SOURCES_DIR = REFERENCES_DIR / "hash-sources"

# 读取上限
MAX_SCRIPT_SIZE = 5 * 1024 * 1024
MAX_PE_SIZE = 32 * 1024 * 1024
MAX_HEADER_SIZE = 1024
MAX_ZIP_ENTRIES = 500
MAX_ZIP_NEST_BYTES = 8 * 1024 * 1024
MAX_OLE_PARSE_SIZE = 32 * 1024 * 1024
MAX_OFFICE_ZIP_SCAN_BYTES = 64 * 1024 * 1024

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
    "hta_sig": {"sig": b"<html", "offset": 0, "ext": []},
}

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

SIG_EXT_WHITELIST = {
    ("zip", ".docx"), ("zip", ".xlsx"), ("zip", ".pptx"),
    ("zip", ".docm"), ("zip", ".xlsm"), ("zip", ".pptm"),
    ("zip", ".jar"), ("zip", ".apk"), ("zip", ".epub"),
    ("ole", ".doc"), ("ole", ".xls"), ("ole", ".ppt"), ("ole", ".msi"),
}

OOXML_EXTS = {".docx", ".xlsx", ".pptx", ".docm", ".xlsm", ".pptm"}
OLE_OFFICE_EXTS = {".doc", ".xls", ".ppt"}
MACRO_OOXML_EXTS = {".docm", ".xlsm", ".pptm"}
OOXML_VBA_PATHS = (
    "word/vbaproject.bin",
    "xl/vbaproject.bin",
    "ppt/vbaproject.bin",
)
OLE_MACRO_NAME_HINTS = (
    "vba", "_vba_project", "vba_project_cur", "macros",
)
VBA_AUTO_MARKERS = (
    b"Auto_Open", b"AutoOpen", b"Document_Open", b"Workbook_Open",
    b"Auto_Close", b"Document_Close", b"AutoExec", b"Auto_Exec",
)
VBA_DANGEROUS_MARKERS = (
    b"CreateObject", b"WScript.Shell", b"URLDownloadToFile",
    b"powershell", b"cmd.exe", b"bitsadmin", b"wscript",
    b"Shell(", b"Shell ", b"Call Shell",
)

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

DEFAULT_MALICIOUS_HASHES = {
    "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f":
        "EICAR-Test-File (标准防病毒测试文件)",
}

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

DEFAULT_EXCLUDE_PATTERNS = [
    r"[\\/]node_modules[\\/]", r"[\\/]\.git[\\/]", r"[\\/]\.svn[\\/]",
    r"[\\/]Windows[\\/]WinSxS[\\/]", r"[\\/]\$Recycle\.Bin",
    r"[\\/]System Volume Information",
    r"__pycache__", r"[\\/]\.cache[\\/]",
]


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


def signature_mismatch_findings(name, header):
    """根据文件名与文件头签名生成 findings，供磁盘文件和 ZIP 内条目共用。"""
    findings = []
    actual = detect_file_type(header)
    ext = Path(name).suffix.lower()
    if actual is None:
        return findings, None
    if (actual, ext) in SIG_EXT_WHITELIST:
        return findings, actual
    if ext in EXT_TO_SIG:
        expected = EXT_TO_SIG[ext]
        if actual != expected:
            if actual == "exe_dll" and ext not in DANGEROUS_EXTS:
                findings.append({
                    "level": "malicious",
                    "reason": f"文件头为可执行(MZ)，扩展名为 {ext}（伪装）",
                })
            else:
                findings.append({
                    "level": "suspicious",
                    "reason": f"文件头类型({actual})与扩展名({ext})不一致",
                })
    elif actual == "exe_dll" and ext not in DANGEROUS_EXTS:
        findings.append({
            "level": "malicious",
            "reason": f"文件头为可执行(MZ)，扩展名为 {ext or '(无)'}（伪装）",
        })
    return findings, actual


def read_text_with_fallback(filepath, max_size):
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


def is_double_extension(filepath):
    name = Path(filepath).name.strip().rstrip(". ")
    parts = name.split(".")
    if len(parts) < 3:
        return None
    exts = ["." + p.lower() for p in parts[1:] if p]
    if not exts:
        return None
    last = exts[-1]
    prev = exts[:-1]
    for i, e in enumerate(prev):
        if e in DANGEROUS_EXTS and last in SAFE_EXTS:
            return f"双扩展名伪装: 可执行段 {e} 伪装为 {last} ({'.'.join(parts)})"
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


def check_file_signature(filepath):
    findings = []
    header = read_file_header(filepath, MAX_HEADER_SIZE)
    if header is None:
        return findings, None, "读取文件头失败"
    findings, actual = signature_mismatch_findings(filepath, header)
    return findings, actual, None


def check_hash(filepath, malicious_hashes):
    findings = []
    sha = compute_sha256(filepath)
    if sha is None:
        return findings, None, "计算哈希失败"
    if sha in malicious_hashes:
        findings.append({"level": "malicious",
                         "reason": f"哈希匹配已知恶意样本: {malicious_hashes[sha]}"})
    return findings, sha, None


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


def inspect_zipfile(zf, prefix="压缩包"):
    """检查 ZIP：文件名特征 + 内部文件头（不解压到磁盘）。"""
    findings = []
    try:
        names = zf.namelist()
    except Exception:
        return findings
    if len(names) > MAX_ZIP_ENTRIES:
        findings.append({
            "level": "medium",
            "reason": f"{prefix}内文件过多（{len(names)}），仅检查前 {MAX_ZIP_ENTRIES} 个",
        })
        names = names[:MAX_ZIP_ENTRIES]

    for name in names:
        if not name or name.endswith("/"):
            continue
        inner_ext = Path(name).suffix.lower()
        d = is_double_extension(name)
        if d:
            findings.append({
                "level": "malicious",
                "reason": f"{prefix}内含双扩展名文件: {name}",
            })
        elif inner_ext in DANGEROUS_EXTS:
            findings.append({
                "level": "suspicious",
                "reason": f"{prefix}内含可执行文件: {name}",
            })
        elif inner_ext in (".js", ".ps1", ".vbs", ".bat", ".cmd", ".hta"):
            findings.append({
                "level": "suspicious",
                "reason": f"{prefix}内含脚本文件: {name}",
            })

        try:
            info = zf.getinfo(name)
        except KeyError:
            continue
        if info.file_size > MAX_ZIP_NEST_BYTES:
            continue
        try:
            with zf.open(name, "r") as inner:
                header = inner.read(MAX_HEADER_SIZE)
        except Exception:
            continue
        sig_findings, actual = signature_mismatch_findings(name, header)
        for item in sig_findings:
            item["reason"] = f"{prefix}内 {name}: {item['reason']}"
            findings.append(item)
        if actual == "exe_dll" and inner_ext not in DANGEROUS_EXTS and not sig_findings:
            findings.append({
                "level": "malicious",
                "reason": f"{prefix}内 {name}: 文件头为可执行(MZ)（伪装）",
            })
    return findings


def check_archive_content(filepath):
    findings = []
    ext = get_file_ext(filepath)
    if ext == ".zip":
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                findings.extend(inspect_zipfile(zf, prefix="压缩包"))
        except Exception:
            return findings
    elif ext in (".rar", ".7z"):
        findings.append({"level": "low",
                         "reason": f"{ext} 压缩包内检依赖外部工具，当前未解析"})
    return findings


def _vba_payload_findings(blob, source):
    findings = []
    if not blob:
        return findings
    blob_l = blob.lower()
    auto_hits = [m.decode("ascii") for m in VBA_AUTO_MARKERS if m.lower() in blob_l]
    danger_hits = [m.decode("ascii") for m in VBA_DANGEROUS_MARKERS if m.lower() in blob_l]
    if auto_hits and danger_hits:
        findings.append({
            "level": "malicious",
            "reason": (
                f"{source} 含自动执行宏({', '.join(auto_hits[:3])}) "
                f"且调用危险 API({', '.join(danger_hits[:3])})"
            ),
        })
    elif danger_hits:
        findings.append({
            "level": "suspicious",
            "reason": f"{source} 宏代码含危险 API: {', '.join(danger_hits[:4])}",
        })
    elif auto_hits:
        findings.append({
            "level": "suspicious",
            "reason": f"{source} 含自动执行宏: {', '.join(auto_hits[:3])}",
        })
    else:
        findings.append({
            "level": "suspicious",
            "reason": f"{source} 存在 VBA 宏流",
        })
    return findings


def inspect_ooxml_macros(zf, ext):
    findings = []
    names = []
    try:
        names = zf.namelist()
    except Exception:
        return findings
    lower_map = {n.lower(): n for n in names}
    vba_name = None
    for candidate in OOXML_VBA_PATHS:
        if candidate in lower_map:
            vba_name = lower_map[candidate]
            break
    if vba_name is None:
        for low, orig in lower_map.items():
            if low.endswith("vbaproject.bin"):
                vba_name = orig
                break

    if vba_name:
        blob = b""
        try:
            with zf.open(vba_name, "r") as fh:
                blob = fh.read(MAX_SCRIPT_SIZE)
        except Exception:
            blob = b""
        findings.extend(_vba_payload_findings(blob, f"OOXML {vba_name}"))
    elif ext in MACRO_OOXML_EXTS:
        findings.append({
            "level": "medium",
            "reason": f"{ext} 为宏启用格式，但未找到 vbaProject.bin",
        })
    return findings


def _read_ole_u16(data, offset):
    if offset + 2 > len(data):
        return None
    return struct.unpack_from("<H", data, offset)[0]


def _read_ole_u32(data, offset):
    if offset + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, offset)[0]


def _decode_ole_name(raw):
    try:
        return raw.decode("utf-16le").rstrip("\x00")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace").rstrip("\x00")


def _ole_fat_chain(fat, start, max_sectors):
    chain = []
    seen = set()
    cur = start
    while cur < 0xFFFFFFF8:
        if cur in seen or len(chain) >= max_sectors:
            break
        seen.add(cur)
        chain.append(cur)
        if cur >= len(fat):
            break
        cur = fat[cur]
    return chain


def _parse_ole_streams(data):
    """解析 OLE 复合文档的目录流，返回 {stream_name: bytes}（截断到 MAX_SCRIPT_SIZE）。"""
    if len(data) < 76 or data[:8] != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
        return None
    sector_shift = _read_ole_u16(data, 0x1E)
    mini_shift = _read_ole_u16(data, 0x20)
    fat_count = _read_ole_u32(data, 0x2C)
    dir_start = _read_ole_u32(data, 0x30)
    mini_cutoff = _read_ole_u32(data, 0x38)
    mini_fat_start = _read_ole_u32(data, 0x3C)
    mini_fat_count = _read_ole_u32(data, 0x40)
    difat_start = _read_ole_u32(data, 0x44)
    difat_count = _read_ole_u32(data, 0x48)
    if None in (sector_shift, mini_shift, fat_count, dir_start, mini_cutoff,
                mini_fat_start, mini_fat_count, difat_start, difat_count):
        return None
    if sector_shift < 7 or sector_shift > 12:
        return None
    sector_size = 1 << sector_shift
    mini_size = 1 << mini_shift

    def sector_offset(index):
        return 512 + index * sector_size

    def read_sector(index):
        off = sector_offset(index)
        if off < 0 or off + sector_size > len(data):
            return None
        return data[off:off + sector_size]

    fat_sids = []
    header_difat = data[0x4C:0x4C + 109 * 4]
    for i in range(109):
        sid = struct.unpack_from("<I", header_difat, i * 4)[0]
        if sid < 0xFFFFFFF8:
            fat_sids.append(sid)
    cur = difat_start
    for _ in range(min(difat_count, 32)):
        blob = read_sector(cur)
        if blob is None or len(blob) < 4:
            break
        for i in range((sector_size // 4) - 1):
            sid = struct.unpack_from("<I", blob, i * 4)[0]
            if sid < 0xFFFFFFF8:
                fat_sids.append(sid)
        nxt = struct.unpack_from("<I", blob, sector_size - 4)[0]
        if nxt >= 0xFFFFFFF8:
            break
        cur = nxt

    fat = []
    for sid in fat_sids[: max(fat_count, 1) + 8]:
        blob = read_sector(sid)
        if blob is None:
            continue
        for i in range(len(blob) // 4):
            fat.append(struct.unpack_from("<I", blob, i * 4)[0])
    if not fat:
        return None

    def read_chain(start, size_limit):
        chunks = []
        total = 0
        for sid in _ole_fat_chain(fat, start, max_sectors=4096):
            blob = read_sector(sid)
            if blob is None:
                break
            remain = size_limit - total
            if remain <= 0:
                break
            chunks.append(blob[:remain])
            total += min(len(blob), remain)
        return b"".join(chunks)

    dir_data = read_chain(dir_start, 2 * 1024 * 1024)
    if len(dir_data) < 128:
        return None

    entries = []
    for i in range(len(dir_data) // 128):
        raw = dir_data[i * 128:(i + 1) * 128]
        name_len = struct.unpack_from("<H", raw, 64)[0]
        obj_type = raw[66]
        start_sid = struct.unpack_from("<I", raw, 116)[0]
        stream_size = struct.unpack_from("<I", raw, 120)[0]
        name = _decode_ole_name(raw[:min(64, name_len)])
        entries.append({
            "name": name,
            "type": obj_type,
            "start": start_sid,
            "size": stream_size,
        })

    mini_stream = b""
    root = next((e for e in entries if e["type"] == 5), None)
    if root and root["size"]:
        mini_stream = read_chain(root["start"], min(root["size"], 8 * 1024 * 1024))

    mini_fat = []
    if mini_fat_count and mini_fat_start < 0xFFFFFFF8:
        mini_fat_data = read_chain(mini_fat_start, mini_fat_count * sector_size)
        for i in range(len(mini_fat_data) // 4):
            mini_fat.append(struct.unpack_from("<I", mini_fat_data, i * 4)[0])

    def read_mini_chain(start, size_limit):
        chunks = []
        total = 0
        seen = set()
        cur = start
        while cur < 0xFFFFFFF8 and total < size_limit:
            if cur in seen:
                break
            seen.add(cur)
            off = cur * mini_size
            if off + mini_size > len(mini_stream):
                break
            remain = size_limit - total
            chunks.append(mini_stream[off:off + min(mini_size, remain)])
            total += min(mini_size, remain)
            if cur >= len(mini_fat):
                break
            cur = mini_fat[cur]
        return b"".join(chunks)

    streams = {}
    for entry in entries:
        if entry["type"] != 2 or not entry["name"]:
            continue
        limit = min(entry["size"], MAX_SCRIPT_SIZE)
        if limit <= 0:
            streams[entry["name"]] = b""
            continue
        if entry["size"] < mini_cutoff and mini_stream:
            streams[entry["name"]] = read_mini_chain(entry["start"], limit)
        else:
            streams[entry["name"]] = read_chain(entry["start"], limit)
    return streams


def inspect_ole_macros(data):
    findings = []
    streams = _parse_ole_streams(data)
    if streams is None:
        findings.append({
            "level": "low",
            "reason": "OLE 复合文档解析失败，未能检查宏流",
        })
        return findings

    macro_streams = []
    for name, blob in streams.items():
        low = name.lower().replace("\x05", "").replace("\x01", "")
        if any(hint in low for hint in OLE_MACRO_NAME_HINTS):
            macro_streams.append((name, blob))

    if not macro_streams:
        return findings

    combined = b"".join(blob for _, blob in macro_streams)
    names = ", ".join(n for n, _ in macro_streams[:4])
    findings.extend(_vba_payload_findings(combined, f"OLE 宏流 ({names})"))
    return findings


def check_office_macros(filepath):
    findings = []
    ext = get_file_ext(filepath)
    try:
        size = os.path.getsize(filepath)
    except OSError:
        return findings

    if ext in OOXML_EXTS:
        if size > MAX_OFFICE_ZIP_SCAN_BYTES:
            findings.append({
                "level": "medium",
                "reason": f"Office 文档过大（{size} 字节），跳过宏流检查",
            })
            return findings
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                findings.extend(inspect_ooxml_macros(zf, ext))
        except (zipfile.BadZipFile, OSError, PermissionError) as e:
            findings.append({"level": "low", "reason": f"OOXML 打开失败: {e}"})
        return findings

    if ext in OLE_OFFICE_EXTS:
        if size > MAX_OLE_PARSE_SIZE:
            findings.append({
                "level": "medium",
                "reason": f"OLE 文档过大（{size} 字节），跳过宏流检查",
            })
            return findings
        try:
            with open(filepath, "rb") as f:
                data = f.read()
        except (OSError, PermissionError) as e:
            findings.append({"level": "low", "reason": f"OLE 读取失败: {e}"})
            return findings
        findings.extend(inspect_ole_macros(data))
    return findings


def _parse_pe_imports(data):
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

    reasons = [f["reason"] for f in findings if f["level"] == "low"]
    return "safe", "; ".join(reasons) if reasons else "所有检测维度通过"


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

    all_findings.extend(check_filename_features(filepath))

    sig_findings, actual_type, sig_err = check_file_signature(filepath)
    all_findings.extend(sig_findings)
    result["actual_type"] = actual_type
    if sig_err:
        read_errors.append(sig_err)

    if strategy in ("standard", "deep"):
        hash_findings, sha, hash_err = check_hash(filepath, malicious_hashes)
        all_findings.extend(hash_findings)
        result["sha256"] = sha
        if hash_err:
            read_errors.append(hash_err)

        content_findings, content_err = check_script_content(filepath)
        all_findings.extend(content_findings)
        if content_err:
            read_errors.append(content_err)

        all_findings.extend(check_office_macros(filepath))

    if strategy == "deep":
        all_findings.extend(check_archive_content(filepath))
        all_findings.extend(check_pe_structure(filepath))
        all_findings.extend(check_lnk(filepath))

    result["findings"] = all_findings
    classification, reason = classify_file(all_findings)
    result["classification"] = classification
    result["reason"] = reason

    if classification == "safe" and read_errors and \
            not sig_findings and result["sha256"] is None:
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


def _ingest_hash_item(hashes, item, default_name="外部哈希库条目"):
    sha = str(item.get("sha256", "")).strip().lower()
    if len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        return
    hashes[sha] = item.get("name") or item.get("description") or default_name


def load_malicious_hashes():
    """合并内置 fallback、hashes.json、hash-sources/*.json。后者覆盖前者。"""
    hashes = dict(DEFAULT_MALICIOUS_HASHES)
    sources = [REFERENCES_DIR / "hashes.json"]
    if HASH_SOURCES_DIR.is_dir():
        sources.extend(sorted(HASH_SOURCES_DIR.glob("*.json")))
    for path in sources:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"警告: 哈希库加载失败 {path.name}: {e}", file=sys.stderr)
            continue
        items = data.get("malicious_hashes", [])
        if isinstance(items, dict):
            items = [{"sha256": k, "name": v} for k, v in items.items()]
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                _ingest_hash_item(hashes, item, default_name=path.stem)
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
