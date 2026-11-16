#!/usr/bin/env python3
"""把每个技能目录打成可直接上传平台的 zip。

    python tools/build_skills.py            # 校验并生成 dist/*.zip
    python tools/build_skills.py --check    # 只校验，不写包

平台限制（踩过坑，别改）：
- 目录层级最多 2 级：包内路径必须是 `<skill>/<子目录>/<文件>`
- 包根必须是技能目录本身，`<skill>/SKILL.md` 只能有一份且在最外层
- frontmatter 的 version 必须是 SemVer 2.0.0 裸版本号，带 `v` 前缀会被拒绝

打包会排除测试、设计文档、运行产物等非运行时文件。
"""

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"

# 非运行时文件：不进包，避免把测试固件、离线评测集和临时产物一起上传
EXCLUDE_DIRS = {"tests", "evaluation", "__pycache__", "work", "output", ".pytest_cache", ".idea", "dist", ".git"}
EXCLUDE_FILES = {"DESIGN.md", ".DS_Store", "Thumbs.db", ".gitignore"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".log", ".zip", ".tmp"}

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
REQUIRED_KEYS = ("name", "description", "agent_created", "version",
                 "display_name", "display_name_en", "description_zh", "description_en", "license")


def iter_files(skill_dir):
    """产出应进包的文件，已按排除规则过滤。"""
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(skill_dir)
        if any(part in EXCLUDE_DIRS for part in rel.parts[:-1]):
            continue
        if rel.name in EXCLUDE_FILES or rel.suffix in EXCLUDE_SUFFIXES:
            continue
        yield rel


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = {}
    for line in parts[1].splitlines():
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            value = m.group(2).strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fm[m.group(1)] = value
    return fm


def check_skill(skill_dir):
    """返回 (问题列表, 信息字典)。"""
    problems = []
    info = {"name": skill_dir.name, "version": "-", "files": 0}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["缺少 SKILL.md"], info

    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    if fm is None:
        problems.append("SKILL.md 缺少 YAML frontmatter")
        fm = {}
    else:
        missing = [k for k in REQUIRED_KEYS if k not in fm]
        if missing:
            problems.append(f"frontmatter 缺字段: {', '.join(missing)}")
        if not fm.get("license", "").strip():
            problems.append("license 字段为空，必须明确技能许可证")
        if not fm.get("license", "").strip():
            problems.append("license 字段为空，必须明确技能许可证")
        if fm.get("name") != skill_dir.name:
            problems.append(f"name 字段({fm.get('name')}) 与目录名({skill_dir.name}) 不一致")
        version = fm.get("version", "")
        info["version"] = version or "-"
        if not SEMVER.match(version):
            hint = "，不能带 v 前缀" if version.startswith("v") else ""
            problems.append(f"version 不是合法 SemVer: {version!r}{hint}")
        if fm.get("agent_created") != "true":
            problems.append("agent_created 不为 true，应用内将无法修改该技能")
        if fm.get("description") and fm.get("description_zh") and fm["description"] != fm["description_zh"]:
            problems.append("description 与 description_zh 不一致")

    files = list(iter_files(skill_dir))
    info["files"] = len(files)
    for rel in files:
        if len(rel.parts) > 2:
            problems.append(f"目录层级超限(>2级): {rel.as_posix()}")
    if len([f for f in files if f.name == "SKILL.md"]) != 1:
        problems.append("包内 SKILL.md 数量不为 1")

    return problems, info


def build(skill_dir, files):
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{skill_dir.name}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            z.write(skill_dir / rel, (Path(skill_dir.name) / rel).as_posix())
    return out


def main():
    parser = argparse.ArgumentParser(description="技能打包")
    parser.add_argument("--check", action="store_true", help="只校验，不生成 zip")
    args = parser.parse_args()

    skills = sorted(p for p in ROOT.iterdir() if p.is_dir() and (p / "SKILL.md").exists())
    if not skills:
        print("没有找到任何技能目录（根目录下含 SKILL.md 的文件夹）")
        return 1

    results = []
    failed = 0
    for skill_dir in skills:
        problems, info = check_skill(skill_dir)
        if args.check or problems:
            out = None
        else:
            out = build(skill_dir, list(iter_files(skill_dir)))
        results.append((info, problems, out))
        if problems:
            failed += 1

    width = max(len(i["name"]) for i, _, _ in results) + 2
    print(f"{'技能'.ljust(width)}{'版本':10}{'文件':>5}  {'大小':>9}  结果")
    print("-" * (width + 34))
    for info, problems, out in results:
        size = f"{out.stat().st_size / 1024:.1f} KB" if out else "-"
        status = "OK" if not problems else f"FAIL ({len(problems)})"
        print(f"{info['name'].ljust(width)}{info['version']:10}{info['files']:>5}  {size:>9}  {status}")
        for p in problems:
            print(f"{' ' * width}  - {p}")

    print()
    if failed:
        print(f"{failed}/{len(results)} 个技能未通过校验，未生成包。")
        return 1
    if args.check:
        print(f"{len(results)} 个技能全部通过校验。")
    else:
        print(f"已生成 {len(results)} 个包到 dist/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
