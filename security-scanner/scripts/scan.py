#!/usr/bin/env python3
"""
Security Scanner - 主扫描引擎
扫描本地目录中的文件，检测潜在恶意文件和可疑脚本。

用法:
    python scan.py --target <路径> --strategy <quick|standard|deep> [--filter <扩展名列表>] [--output <结果JSON路径>]

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
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

# ============================================================
# 文件签名库
# ============================================================
FILE_SIGNATURES = {
    "exe_dll": {"sig": b"\x4d\x5a", "offset": 0, "ext": [".exe", ".dll"]},
    "zip": {"sig": b"\x50\x4b\x03\x04", "offset": 0, "ext": [".zip"]},
    "rar": {"sig": b"\x52\x61\x72\x21", "offset": 0, "ext": [".rar"]},
    "7z": {"sig": b"\x37\x7a\xbc\xaf\x27\x1c", "offset": 0, "ext": [".7z"]},
    "pdf": {"sig": b"\x25\x50\x44\x46", "offset": 0, "ext": [".pdf"]},
    "png": {"sig": b"\x89\x50\x4e\x47", "offset": 0, "ext": [".png"]},
    "jpg": {"sig": b"\xff\xd8\xff", "offset": 0, "ext": [".jpg", ".jpeg"]},
    "gif": {"sig": b"\x47\x49\x46\x38", "offset": 0, "ext": [".gif"]},
    "ole": {"sig": b"\xd0\xcf\x11\xe0", "offset": 0, "ext": [".msi", ".doc", ".xls", ".ppt"]},
    "elf": {"sig": b"\x7f\x45\x4c\x46", "offset": 0, "ext": [".elf"]},
}

# 扩展名到预期签名的映射（反向查找）
EXT_TO_SIG = {}
for sig_key, sig_info in FILE_SIGNATURES.items():
    for ext in sig_info["ext"]:
        EXT_TO_SIG[ext] = sig_key

# ============================================================
# 危险扩展名集合
# ============================================================
DANGEROUS_EXTS = {".exe", ".scr", ".com", ".bat", ".cmd", ".vbs", ".ps1", ".js",
                  ".jar", ".msi", ".dll", ".lnk"}
SAFE_EXTS = {".txt", ".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx",
             ".xls", ".xlsx", ".mp3", ".mp4", ".avi", ".csv"}

# ============================================================
# 可疑文件名关键词
# ============================================================
SUSPICIOUS_NAME_KEYWORDS = [
    "crack", "keygen", "patch", "hack", "cheat", "bot", "trainer",
    "loader", "injector", "bypass", "warez", "serial", "activation",
    "unlock", "reset", "free", "full", "pro", "premium"
]

# 系统关键进程名（在非系统目录出现为可疑）
SYSTEM_PROCESS_NAMES = [
    "svchost.exe", "csrss.exe", "lsass.exe", "winlogon.exe",
    "explorer.exe", "services.exe", "smss.exe", "wininit.exe",
    "spoolsv.exe", "taskmgr.exe", "rundll32.exe", "userinit.exe"
]

# ============================================================
# 内置恶意哈希库（示例）
# ============================================================
MALICIOUS_HASHES = {
    "275a021bb21eebf4f0bf1f7d0c1c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0": "EICAR-Test-File",
    "44d88612fea8a8f36de82e0f7d0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0": "Test-Malware-Sample",
}

# ============================================================
# 脚本内容危险模式
# ============================================================
SCRIPT_PATTERNS = {
    ".js": [
        (r"eval\s*\(\s*atob\s*\(", "high", "eval执行Base64编码数据"),
        (r"\.downloadFile\s*\(.*\)\s*;\s*\.run\s*\(", "high", "下载并执行文件"),
        (r"WScript\.Shell", "medium", "创建WScript.Shell对象"),
        (r"new\s+ActiveXObject\s*\(", "medium", "创建ActiveX对象"),
        (r"powershell\s+.*-enc", "high", "调用PowerShell编码命令"),
        (r"[0-9a-fA-F]{64,}", "medium", "长Hex字符串（可能混淆代码）"),
        (r"document\.write\s*\(.*\.exe", "high", "document.write写入EXE"),
    ],
    ".ps1": [
        (r"-EncodedCommand\s+", "high", "使用编码命令执行"),
        (r"Invoke-WebRequest.*\|\s*Invoke-Expression", "high", "下载并执行远程代码"),
        (r"-WindowStyle\s+Hidden", "medium", "隐藏窗口执行"),
        (r"-ExecutionPolicy\s+Bypass", "medium", "绕过执行策略"),
        (r"Set-ItemProperty.*HKCU.*Run", "high", "注册表持久化"),
        (r"Reflection\.Assembly\]::Load", "high", "反射加载DLL"),
        (r"[A-Za-z0-9+/]{100,}={0,2}", "medium", "长Base64字符串"),
    ],
    ".vbs": [
        (r'CreateObject\s*\(\s*"WScript\.Shell"', "medium", "创建WScript.Shell"),
        (r"\.downloadFile.*\.run", "high", "下载并执行文件"),
        (r"RegWrite", "medium", "注册表写入操作"),
        (r"\.DeleteFile\s*\(\s*WScript", "high", "自删除行为"),
    ],
    ".bat": [
        (r"bitsadmin.*transfer.*(&&|\|)\s*(call|cmd|start)", "high", "bitsadmin下载并执行"),
        (r"powershell\s+.*-enc", "high", "调用PowerShell编码命令"),
        (r"reg\s+add.*Run", "high", "注册表持久化"),
        (r"del\s+/%0", "high", "自删除"),
        (r"format\s+[a-z]:", "critical", "磁盘格式化命令"),
    ],
    ".cmd": [
        (r"bitsadmin.*transfer.*(&&|\|)\s*(call|cmd|start)", "high", "bitsadmin下载并执行"),
        (r"powershell\s+.*-enc", "high", "调用PowerShell编码命令"),
        (r"reg\s+add.*Run", "high", "注册表持久化"),
        (r"del\s+/%0", "high", "自删除"),
        (r"format\s+[a-z]:", "critical", "磁盘格式化命令"),
    ],
    ".py": [
        (r"exec\s*\(\s*base64", "high", "执行Base64编码数据"),
        (r"subprocess.*base64", "high", "subprocess执行编码命令"),
        (r"urllib.*exec|requests.*exec", "high", "下载并执行远程代码"),
        (r"keyboard.*log|pynput.*Listener", "medium", "键盘记录行为"),
        (r"subprocess.*CREATE_NO_WINDOW", "medium", "隐蔽执行（无窗口）"),
        (r"os\.system.*crontab|os\.system.*schtasks", "high", "持久化注入"),
    ],
    ".sh": [
        (r"curl.*\|\s*sh|wget.*\|\s*sh", "high", "下载并执行远程脚本"),
        (r"bash\s+-i\s+>&\s*/dev/tcp", "critical", "反向Shell连接"),
        (r"crontab.*\|\s*sh", "high", "cron持久化"),
        (r"rm\s+-rf\s+/var/log", "high", "清除系统日志"),
        (r"sudo\s+.*\|\s*sh", "medium", "提权后执行脚本"),
    ],
}

# ============================================================
# PE 导入表可疑 API
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

# 进程注入组合检测
PROCESS_INJECTION_COMBO = {"CreateRemoteThread", "VirtualAllocEx", "WriteProcessMemory"}
DOWNLOAD_EXEC_COMBO = {"URLDownloadToFile", "WinExec", "ShellExecute", "ShellExecuteEx"}


# ============================================================
# 工具函数
# ============================================================
def read_file_header(filepath, size=64):
    """读取文件头部字节"""
    try:
        with open(filepath, "rb") as f:
            return f.read(size)
    except (IOError, OSError, PermissionError):
        return None


def compute_sha256(filepath):
    """计算文件 SHA256 哈希"""
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
    """通过文件头检测实际文件类型"""
    if header is None or len(header) < 4:
        return None
    for sig_key, sig_info in FILE_SIGNATURES.items():
        sig = sig_info["sig"]
        offset = sig_info["offset"]
        if header[offset:offset + len(sig)] == sig:
            return sig_key
    return None


def get_file_ext(filepath):
    """获取文件扩展名（小写）"""
    return Path(filepath).suffix.lower()


def is_double_extension(filepath):
    """检测双扩展名"""
    name = Path(filepath).name
    parts = name.split(".")
    if len(parts) < 3:
        return None
    exts = ["." + p.lower() for p in parts[1:]]
    for i in range(len(exts) - 1):
        if exts[i] in SAFE_EXTS and exts[-1] in DANGEROUS_EXTS:
            return f"双扩展名伪装: {''.join(exts)}（伪装为{exts[i]}的可执行文件）"
        if exts[i] in DANGEROUS_EXTS and exts[-1] in SAFE_EXTS:
            return f"双扩展名: {''.join(exts)}（可执行文件改名为安全类型）"
    return None


def has_suspicious_name(filepath):
    """检测可疑文件名"""
    name = Path(filepath).name.lower()
    for keyword in SUSPICIOUS_NAME_KEYWORDS:
        if keyword in name:
            return f"文件名包含可疑关键词: {keyword}"
    if name in SYSTEM_PROCESS_NAMES:
        return f"系统进程名出现在非系统目录: {name}"
    return None


def is_random_name(filepath):
    """检测随机字符文件名"""
    name = Path(filepath).stem
    if len(name) >= 8:
        has_alpha = any(c.isalpha() for c in name)
        has_digit = any(c.isdigit() for c in name)
        no_meaningful = not any(word in name.lower() for word in
                               ["readme", "license", "setup", "install", "update",
                                "config", "data", "test", "demo", "sample", "example"])
        if has_alpha and has_digit and no_meaningful:
            return True
    return False


# ============================================================
# 检测函数
# ============================================================
def check_filename_features(filepath):
    """文件名特征检测"""
    findings = []
    double_ext = is_double_extension(filepath)
    if double_ext:
        findings.append({"level": "malicious", "reason": double_ext})
    suspicious = has_suspicious_name(filepath)
    if suspicious:
        findings.append({"level": "suspicious", "reason": suspicious})
    if is_random_name(filepath):
        ext = get_file_ext(filepath)
        if ext in DANGEROUS_EXTS:
            findings.append({"level": "suspicious", "reason": "随机命名 + 可执行扩展名"})
    return findings


def check_file_signature(filepath):
    """文件头签名检测"""
    findings = []
    header = read_file_header(filepath)
    if header is None:
        return findings, None
    actual_type = detect_file_type(header)
    ext = get_file_ext(filepath)

    if actual_type and ext in EXT_TO_SIG:
        expected_type = EXT_TO_SIG[ext]
        if actual_type != expected_type:
            if actual_type == "exe_dll" and ext in SAFE_EXTS:
                findings.append({
                    "level": "malicious",
                    "reason": f"文件头为可执行文件(MZ)，但扩展名为{ext}（伪装）"
                })
            elif actual_type == "exe_dll" and ext == ".pdf":
                findings.append({
                    "level": "malicious",
                    "reason": "文件头为可执行文件(MZ)，但扩展名为PDF（伪装）"
                })
            else:
                findings.append({
                    "level": "suspicious",
                    "reason": f"文件头类型({actual_type})与扩展名({ext})不一致"
                })
    elif actual_type == "exe_dll" and ext not in DANGEROUS_EXTS and ext not in EXT_TO_SIG:
        findings.append({
            "level": "malicious",
            "reason": f"文件头为可执行文件(MZ)，但扩展名为{ext}（伪装）"
        })
    return findings, actual_type


def check_hash(filepath):
    """文件哈希检测"""
    findings = []
    sha256 = compute_sha256(filepath)
    if sha256 is None:
        return findings, None
    if sha256 in MALICIOUS_HASHES:
        findings.append({
            "level": "malicious",
            "reason": f"哈希匹配已知恶意样本: {MALICIOUS_HASHES[sha256]}"
        })
    return findings, sha256


def check_script_content(filepath):
    """脚本内容模式检测"""
    findings = []
    ext = get_file_ext(filepath)
    if ext not in SCRIPT_PATTERNS:
        return findings

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except (IOError, OSError, PermissionError):
        return findings

    patterns = SCRIPT_PATTERNS[ext]
    high_count = 0
    medium_count = 0
    critical_count = 0

    for pattern, level, description in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            if level == "critical":
                critical_count += 1
                findings.append({"level": "malicious", "reason": f"匹配极高风险模式: {description}"})
            elif level == "high":
                high_count += 1
                findings.append({"level": "high", "reason": f"匹配高风险模式: {description}"})
            elif level == "medium":
                medium_count += 1
                findings.append({"level": "medium", "reason": f"匹配中风险模式: {description}"})

    if high_count >= 2:
        findings.append({"level": "malicious", "reason": f"匹配{high_count}个高风险模式"})
    elif high_count == 1 and medium_count == 0:
        findings.append({"level": "suspicious", "reason": "匹配1个高风险模式"})
    if medium_count >= 2 and high_count == 0:
        findings.append({"level": "suspicious", "reason": f"匹配{medium_count}个中风险模式"})

    return findings


def check_archive_content(filepath):
    """压缩包内容检查（deep策略）"""
    findings = []
    ext = get_file_ext(filepath)

    if ext == ".zip":
        try:
            with zipfile.ZipFile(filepath, "r") as zf:
                names = zf.namelist()
        except (zipfile.BadZipFile, IOError, OSError):
            return findings
    elif ext in (".rar", ".7z"):
        return findings
    else:
        return findings

    for name in names:
        inner_ext = Path(name).suffix.lower()
        if inner_ext in DANGEROUS_EXTS:
            inner_double = is_double_extension(name)
            if inner_double:
                findings.append({
                    "level": "malicious",
                    "reason": f"压缩包内含双扩展名文件: {name}"
                })
            else:
                findings.append({
                    "level": "suspicious",
                    "reason": f"压缩包内含可执行文件: {name}"
                })
        elif inner_ext in (".js", ".ps1", ".vbs", ".bat", ".cmd"):
            findings.append({
                "level": "suspicious",
                "reason": f"压缩包内含脚本文件: {name}"
            })

    return findings


def check_pe_structure(filepath):
    """PE 结构分析（deep策略）"""
    findings = []
    header = read_file_header(filepath, size=1024)
    if header is None or len(header) < 64:
        return findings

    if header[:2] != b"\x4d\x5a":
        return findings

    try:
        pe_offset = struct.unpack_from("<I", header, 0x3c)[0]
        if pe_offset + 4 > len(header):
            header = read_file_header(filepath, size=pe_offset + 256)
            if header is None:
                return findings
        if header[pe_offset:pe_offset + 4] != b"\x50\x45\x00\x00":
            findings.append({"level": "suspicious", "reason": "PE签名无效"})
            return findings
    except (struct.error, IndexError):
        findings.append({"level": "suspicious", "reason": "PE头解析失败"})
        return findings

    # 读取导入表（简化版：搜索可疑 API 名称）
    try:
        with open(filepath, "rb") as f:
            content = f.read(65536)
    except (IOError, OSError, PermissionError):
        return findings

    found_apis = set()
    for api_name in SUSPICIOUS_PE_APIS:
        api_bytes = api_name.encode("ascii")
        if api_bytes in content:
            found_apis.add(api_name)

    if found_apis:
        injection_found = PROCESS_INJECTION_COMBO & found_apis
        download_found = DOWNLOAD_EXEC_COMBO & found_apis

        if injection_found >= 2:
            findings.append({
                "level": "malicious",
                "reason": f"导入进程注入API组合: {', '.join(sorted(injection_found))}"
            })
        if download_found >= 2:
            findings.append({
                "level": "suspicious",
                "reason": f"导入下载执行API组合: {', '.join(sorted(download_found))}"
            })
        for api in found_apis:
            level = SUSPICIOUS_PE_APIS[api]
            if level == "high" and api not in injection_found and api not in download_found:
                findings.append({
                    "level": "suspicious",
                    "reason": f"导入高风险API: {api}"
                })

    return findings


# ============================================================
# 综合判定
# ============================================================
def classify_file(findings):
    """根据所有检测结果综合判定文件分类"""
    if not findings:
        return "safe", "所有检测维度通过"

    has_malicious = any(f["level"] == "malicious" for f in findings)
    has_critical = any(f["level"] == "critical" for f in findings)

    if has_malicious or has_critical:
        reasons = [f["reason"] for f in findings if f["level"] in ("malicious", "critical")]
        return "malicious", "; ".join(reasons)

    has_suspicious = any(f["level"] == "suspicious" for f in findings)
    has_high = any(f["level"] == "high" for f in findings)

    if has_suspicious or has_high:
        reasons = [f["reason"] for f in findings if f["level"] in ("suspicious", "high")]
        return "suspicious", "; ".join(reasons)

    has_medium = any(f["level"] == "medium" for f in findings)
    if has_medium:
        reasons = [f["reason"] for f in findings if f["level"] == "medium"]
        return "suspicious", "; ".join(reasons)

    return "safe", "所有检测维度通过"


# ============================================================
# 扫描引擎
# ============================================================
def scan_file(filepath, strategy):
    """扫描单个文件"""
    result = {
        "path": filepath,
        "name": Path(filepath).name,
        "size": 0,
        "ext": get_file_ext(filepath),
        "classification": "safe",
        "reason": "",
        "findings": [],
        "sha256": None,
    }

    try:
        result["size"] = os.path.getsize(filepath)
    except (OSError, PermissionError):
        result["classification"] = "unchecked"
        result["reason"] = "无法获取文件大小（权限不足）"
        return result

    all_findings = []

    # 1. 文件名特征检测（所有策略）
    all_findings.extend(check_filename_features(filepath))

    # 2. 文件头签名检测（所有策略）
    sig_findings, actual_type = check_file_signature(filepath)
    all_findings.extend(sig_findings)

    if strategy in ("standard", "deep"):
        # 3. 文件哈希检测
        hash_findings, sha256 = check_hash(filepath)
        all_findings.extend(hash_findings)
        result["sha256"] = sha256

        # 4. 脚本内容模式检测
        content_findings = check_script_content(filepath)
        all_findings.extend(content_findings)

    if strategy == "deep":
        # 5. 压缩包内容检查
        archive_findings = check_archive_content(filepath)
        all_findings.extend(archive_findings)

        # 6. PE 结构分析
        pe_findings = check_pe_structure(filepath)
        all_findings.extend(pe_findings)

    result["findings"] = all_findings
    classification, reason = classify_file(all_findings)
    result["classification"] = classification
    result["reason"] = reason

    return result


def collect_files(target, filter_exts, strategy):
    """收集目标路径下待扫描的文件列表"""
    files = []

    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        for root, dirs, filenames in os.walk(target):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                ext = get_file_ext(filepath)
                if filter_exts is None or ext in filter_exts:
                    files.append(filepath)
    else:
        print(f"错误: 目标路径不存在: {target}", file=sys.stderr)
        sys.exit(1)

    return files


def run_scan(target, strategy, filter_exts):
    """执行完整扫描"""
    start_time = time.time()

    print(f"扫描目标: {target}", file=sys.stderr)
    print(f"扫描策略: {strategy}", file=sys.stderr)
    print(f"文件过滤: {filter_exts if filter_exts else '全部类型'}", file=sys.stderr)

    files = collect_files(target, filter_exts, strategy)
    total = len(files)
    print(f"待扫描文件数: {total}", file=sys.stderr)

    results = []
    for i, filepath in enumerate(files, 1):
        elapsed = time.time() - start_time
        print(f"[{i}/{total}] ({elapsed:.1f}s) 扫描: {filepath}", file=sys.stderr)

        result = scan_file(filepath, strategy)
        results.append(result)

    elapsed = time.time() - start_time
    print(f"\n扫描完成! 耗时: {elapsed:.1f}s, 扫描文件数: {total}", file=sys.stderr)

    # 统计
    stats = {
        "total": total,
        "safe": sum(1 for r in results if r["classification"] == "safe"),
        "suspicious": sum(1 for r in results if r["classification"] == "suspicious"),
        "malicious": sum(1 for r in results if r["classification"] == "malicious"),
        "unchecked": sum(1 for r in results if r["classification"] == "unchecked"),
        "elapsed": round(elapsed, 2),
    }

    output = {
        "scan_info": {
            "target": target,
            "strategy": strategy,
            "filter": filter_exts,
            "start_time": start_time,
            "elapsed": stats["elapsed"],
            "total_files": total,
        },
        "stats": stats,
        "results": results,
    }

    return output


# ============================================================
# 主入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description="Security Scanner - 本地文件安全查杀工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--target", required=True, help="扫描目标路径（文件/文件夹/磁盘根目录）")
    parser.add_argument("--strategy", choices=["quick", "standard", "deep"],
                        default="standard", help="扫描策略（默认: standard）")
    parser.add_argument("--filter", default=None,
                        help="文件扩展名过滤，逗号分隔（如: exe,dll,js,ps1）。不指定则扫描全部")
    parser.add_argument("--output", default=None,
                        help="结果JSON输出路径。不指定则仅输出到stdout")

    args = parser.parse_args()

    filter_exts = None
    if args.filter:
        filter_exts = set()
        for ext in args.filter.split(","):
            ext = ext.strip().lower()
            if not ext.startswith("."):
                ext = "." + ext
            filter_exts.add(ext)

    output = run_scan(args.target, args.strategy, filter_exts)

    json_output = json.dumps(output, ensure_ascii=False, indent=2)
    print(json_output)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"结果已保存到: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
