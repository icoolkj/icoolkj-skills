#!/usr/bin/env python3
"""上传前安全自检：找出平台「基础安全检测」容易误判的内容。

用法：
    python tools/audit_safety.py                # 检查全部技能（打包视角，忽略 tests/ 等）
    python tools/audit_safety.py security-scanner
    python tools/audit_safety.py --zip dist/security-scanner.zip
    python tools/audit_safety.py --strict       # 中风险也算失败

规则按"会不会被多引擎扫描/静态规则命中"设计，不追求覆盖所有安全问题：
  - 高危：可执行代码（.py/.js/.sh…）中出现病毒特征词、Windows 注入类 API 名、
          序列化反序列化、命令执行 + 网络下载组合
  - 中危：文档里出现同类特征串、外部 URL、混淆式字节序列
  - 低危：删除类操作、敏感路径
退出码：0 通过，1 有高危（--strict 时含中危）。
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = [
    "note-intel",
    "data-report-agent-skill",
    "data-report-creator",
    "security-scanner",
    "self-media-content-organizer",
    "xhs-content-studio",
]

# 打包时会被排除、不需要检查的目录/文件
EXCLUDE_DIRS = {"tests", "evaluation", "__pycache__", "work", "output", "dist", ".git",
                ".pytest_cache", ".idea"}
EXCLUDE_FILES = {"DESIGN.md"}

CODE_EXTS = {".py", ".js", ".sh", ".ps1", ".bat", ".cmd", ".vbs", ".wsf"}
DOC_EXTS = {".md", ".txt", ".json", ".html", ".yaml", ".yml"}

RULES = [
    # (等级, 名称, 正则, 至少命中几个不同取值才算风险)
    ("high", "真实病毒测试样本",
     r"X5O!P%@AP\[4\\PZX54\(P\^\)7CC\)7\}\$EICAR", 1),
    ("high", "病毒特征词（多家族）",
     r"\b(malware|ransomware|keylogger|backdoor|rootkit|trojan|stealer|botnet)\b", 2),
    ("high", "注入类 API 名（多个）",
     r"\b(CreateRemoteThread|VirtualAllocEx|WriteProcessMemory|SetWindowsHookEx|"
     r"NtUnmapViewOfSection|QueueUserAPC)\b", 2),
    ("high", "编码命令执行",
     r"(EncodedCommand|FromBase64String\s*\(|DownloadString|IEX\s*\()", 1),
    ("high", "动态执行",
     r"\b(eval|exec)\s*\(\s*(base64|atob|compile|__import__)", 1),
    ("high", "反序列化执行",
     r"\b(pickle\.loads?|marshal\.loads)\s*\(", 1),
    ("high", "命令执行",
     r"\b(os\.system|subprocess\.(run|call|Popen|check_output)[^\n]*shell\s*=\s*True)", 1),
    ("medium", "长字节转义（疑似 shellcode）",
     r"(\\x[0-9a-fA-F]{2}){4,}", 1),
    ("medium", "外部网络地址",
     r"https?://([a-zA-Z0-9.-]+)", 1),
    ("low", "删除类操作",
     r"(shutil\.rmtree|os\.remove|os\.unlink|\.unlink\()", 1),
    ("low", "敏感路径",
     r"(\.ssh|id_rsa|Login Data|Cookies\b|/etc/shadow)", 1),
]

# 文档里出现同类特征串只说明规则，不构成可执行内容
DOC_DOWNGRADE = {"病毒特征词（多家族）", "注入类 API 名（多个）", "编码命令执行"}

# 公开 API 文档地址与规范链接，出现它们属正常配置，不算外联风险
URL_ALLOWLIST = (
    "localhost", "127.0.0.1", "www.w3.org", "schemas.openxmlformats.org",
    "github.com", "icoolkj.com",
    "api.deepseek.com", "api.moonshot.cn", "api.openai.com", "api.baichuan-ai.com",
    "dashscope.aliyuncs.com", "www.virustotal.com", "open.bigmodel.cn",
    "ark.cn-beijing.volces.com",
)


def iter_files(target: Path):
    if target.is_file():
        yield target, target.name
        return
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(target)
        if any(part in EXCLUDE_DIRS for part in rel.parts[:-1]):
            continue
        if rel.name in EXCLUDE_FILES:
            continue
        yield path, rel.as_posix()


def check_text(text: str, ext: str):
    hits = []
    for level, name, pattern, min_distinct in RULES:
        found = re.findall(pattern, text)
        if not found:
            continue
        distinct = sorted({(f if isinstance(f, str) else f[0]) for f in found})
        if name == "外部网络地址":
            distinct = [d for d in distinct if not any(a in d for a in URL_ALLOWLIST)]
            if not distinct:
                continue
        if len(distinct) < min_distinct:
            continue
        # 文档里的同类特征串降一级：说明文档本身不是可执行内容
        eff = level
        if ext in DOC_EXTS and name in DOC_DOWNGRADE:
            eff = "medium"
        hits.append((eff, name, len(found), distinct[:3]))
    return hits


def audit_tree(target: Path, label: str):
    problems = []
    for path, rel in iter_files(target):
        if path.suffix.lower() not in CODE_EXTS | DOC_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hits = check_text(text, path.suffix.lower())
        if hits:
            problems.append((f"{label}/{rel}", hits))
    return problems


def audit_zip(zp: Path):
    problems = []
    with zipfile.ZipFile(zp) as z:
        for name in sorted(z.namelist()):
            if name.endswith("/"):
                continue
            if any(part in EXCLUDE_DIRS for part in name.split("/")[:-1]):
                continue
            if Path(name).suffix.lower() not in CODE_EXTS | DOC_EXTS:
                continue
            try:
                text = z.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            hits = check_text(text, Path(name).suffix.lower())
            if hits:
                problems.append((name, hits))
    return problems


def main():
    ap = argparse.ArgumentParser(description="上传前安全自检")
    ap.add_argument("skill", nargs="*", help="只检查指定技能目录名")
    ap.add_argument("--zip", action="append", default=None, help="检查指定 zip")
    ap.add_argument("--strict", action="store_true", help="中风险也判失败")
    args = ap.parse_args()

    problems = []
    if args.zip:
        for z in args.zip:
            problems += audit_zip(Path(z))
    else:
        targets = args.skill or SKILLS
        for name in targets:
            d = ROOT / name
            if not d.is_dir():
                print(f"跳过（不存在）: {name}", file=sys.stderr)
                continue
            problems += audit_tree(d, name)

    if not problems:
        print("未发现上传风险项。")
        return 0

    order = {"high": 0, "medium": 1, "low": 2}
    problems.sort(key=lambda p: min(order[h[0]] for h in p[1]))
    worst = "low"
    for where, hits in problems:
        print(where)
        for level, name, count, samples in sorted(hits, key=lambda h: order[h[0]]):
            print(f"  [{ {'high': '高', 'medium': '中', 'low': '低'}[level] }] {name} ×{count}  {samples}")
            if order[level] < order[worst]:
                worst = level
    print(f"\n汇总：{len(problems)} 个文件存在风险项，最高等级 {worst}")
    if worst == "high" or (args.strict and worst == "medium"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
