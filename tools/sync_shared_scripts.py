#!/usr/bin/env python3
"""共享脚本主从同步工具。

各技能必须能独立打包上传，同源脚本因此各存一份。本工具保证"副本"不会悄悄
跑偏到与主版不同的实现：

    python tools/sync_shared_scripts.py            # 只报告
    python tools/sync_shared_scripts.py --fix      # 用主版覆盖漂移的副本
    python tools/sync_shared_scripts.py --check    # CI 用，有漂移则退出码 1

主从关系定义在 tools/skill_manifest.json。
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "skill_manifest.json"


def digest(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def load_manifest():
    if not MANIFEST.exists():
        print(f"[ERROR] 缺少清单文件: {MANIFEST}", file=sys.stderr)
        sys.exit(2)
    with MANIFEST.open(encoding="utf-8") as f:
        return json.load(f)


def check_group(group, fix):
    name = group["id"]
    master = group["master"]
    members = group["members"]
    shared = group["shared"]
    drift, fixed, missing_master = [], [], []

    print(f"\n[{name}] 主版: {master}")
    for filename in shared:
        master_path = ROOT / master / "scripts" / filename
        if not master_path.exists():
            missing_master.append(filename)
            print(f"  ✗ {filename}: 主版缺失")
            continue

        base = digest(master_path)
        for member in members:
            if member == master:
                continue
            target = ROOT / member / "scripts" / filename
            if not target.exists():
                drift.append((filename, member, "文件缺失"))
                print(f"  ✗ {filename}: {member} 缺少该文件")
                if fix:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(master_path, target)
                    fixed.append((filename, member))
                continue
            if digest(target) == base:
                print(f"  ✓ {filename}: {member} 与主版一致")
            else:
                drift.append((filename, member, "内容不同"))
                print(f"  ✗ {filename}: {member} 与主版不一致")
                if fix:
                    shutil.copy2(master_path, target)
                    fixed.append((filename, member))

    return drift, fixed, missing_master


def report_divergent(manifest):
    """非共享脚本：同一文件名出现在多个技能里，说明为何不收敛。"""
    notes = manifest.get("divergent_notes", {})
    buckets = {}
    for skill_dir in sorted(ROOT.iterdir()):
        scripts = skill_dir / "scripts"
        if not (skill_dir / "SKILL.md").exists() or not scripts.is_dir():
            continue
        for f in scripts.glob("*.py"):
            buckets.setdefault(f.name, set()).add(skill_dir.name)

    shared_names = {f for g in manifest["groups"] for f in g["shared"]}
    rows = []
    for filename, owners in sorted(buckets.items()):
        if len(owners) < 2 or filename in shared_names:
            continue
        rows.append((filename, sorted(owners), notes.get(filename, "未说明")))
    if not rows:
        return
    print("\n[同名但按设计不收敛的脚本]")
    for filename, owners, note in rows:
        print(f"  · {filename}: {', '.join(owners)}")
        print(f"      {note}")


def main():
    parser = argparse.ArgumentParser(description="共享脚本主从同步")
    parser.add_argument("--fix", action="store_true", help="用主版覆盖漂移的副本")
    parser.add_argument("--check", action="store_true", help="有漂移时以退出码 1 结束")
    args = parser.parse_args()

    manifest = load_manifest()
    all_drift, all_fixed, all_missing = [], [], []
    for group in manifest["groups"]:
        drift, fixed, missing = check_group(group, args.fix)
        all_drift += drift
        all_fixed += fixed
        all_missing += missing

    report_divergent(manifest)

    print()
    if all_missing:
        print(f"主版文件缺失 {len(all_missing)} 个，请先补齐主版。")
        return 2
    if all_fixed:
        print(f"已用主版覆盖 {len(all_fixed)} 个副本：")
        for filename, member in all_fixed:
            print(f"  - {member}/scripts/{filename}")
    if all_drift and not args.fix:
        print(f"发现 {len(all_drift)} 处漂移，运行 --fix 收敛到主版。")
        if args.check:
            return 1
        return 0
    if not all_drift:
        print("共享脚本与主版完全一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
