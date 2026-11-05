#!/usr/bin/env python3
"""把 `evaluation/<skill>/` 下的评测集打成平台可上传的 zip。

    python tools/build_evals.py            # 校验并生成 dist/evals/*.zip
    python tools/build_evals.py --check    # 只校验，不写包
    python tools/build_evals.py security-scanner   # 只处理指定技能

评测集目录结构（对齐平台「评测集管理 → 下载评测模板」）：

    evaluation/<skill>/
      header.json          评分维度、权重、通过/优秀阈值
      cases.jsonl          每行一个用例
      workspace/case_XXX/  用例输入文件（文件名与 cases.jsonl 的 input_files 对应）

平台限制：单文件 ≤ 10MB；支持 zip / xlsx / csv / json。
zip 内路径不含 skills 根目录前缀，直接是 header.json / cases.jsonl / workspace/。
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_ROOT = ROOT / "evaluation"
DIST = ROOT / "dist" / "evals"

MAX_ZIP_BYTES = 10 * 1024 * 1024
CASE_REQUIRED = ("case_name", "user_question", "expected", "difficulty",
                 "case_type", "checklist_by_dim", "anchors_by_dim", "input_files")
ANCHOR_KEYS = {"0", "5.0", "10.0"}


def iter_files(eval_dir):
    for path in sorted(eval_dir.rglob("*")):
        if path.is_file() and path.name not in {".DS_Store", "Thumbs.db"}:
            yield path


def check_eval(eval_dir):
    """返回 (问题列表, 信息字典)。"""
    problems = []
    info = {"name": eval_dir.name, "cases": 0, "files": 0, "dims": 0}

    header_path = eval_dir / "header.json"
    cases_path = eval_dir / "cases.jsonl"
    if not header_path.exists():
        problems.append("缺少 header.json")
    if not cases_path.exists():
        problems.append("缺少 cases.jsonl")
    if problems:
        return problems, info

    # ---- header.json
    dim_keys = set()
    try:
        header = json.loads(header_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"header.json 不是合法 JSON: {exc}"], info
    if not header.get("dataset_name"):
        problems.append("header.json 缺 dataset_name")
    dims = header.get("profile", {}).get("dimensions", [])
    if not dims:
        problems.append("header.json 缺 profile.dimensions")
    total_weight = 0.0
    for d in dims:
        for key in ("key", "name", "weight"):
            if key not in d:
                problems.append(f"维度缺字段 {key}: {d}")
        dim_keys.add(d.get("key"))
        total_weight += float(d.get("weight", 0) or 0)
    if dims and abs(total_weight - 1.0) > 0.01:
        problems.append(f"维度权重之和为 {total_weight:.2f}，应为 1.00")
    agg = header.get("profile", {}).get("aggregation", {})
    if "pass_threshold" not in agg:
        problems.append("header.json 缺 aggregation.pass_threshold")
    info["dims"] = len(dims)

    # ---- cases.jsonl
    seen = set()
    case_dirs = set()
    for lineno, line in enumerate(cases_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"cases.jsonl 第 {lineno} 行不是合法 JSON: {exc}")
            continue
        info["cases"] += 1

        missing = [k for k in CASE_REQUIRED if k not in case]
        if missing:
            problems.append(f"第 {lineno} 行缺字段: {', '.join(missing)}")
            continue

        name = case["case_name"]
        if name in seen:
            problems.append(f"case_name 重复: {name}")
        seen.add(name)
        if case["difficulty"] not in {"easy", "medium", "hard"}:
            problems.append(f"{name}: difficulty 应为 easy/medium/hard，当前 {case['difficulty']!r}")
        if case["case_type"] not in {"positive", "negative", "boundary"}:
            problems.append(f"{name}: case_type 应为 positive/negative/boundary，当前 {case['case_type']!r}")

        extra = set(case["checklist_by_dim"]) - dim_keys
        if extra:
            problems.append(f"{name}: checklist 含未定义维度 {', '.join(sorted(extra))}")
        for dim, items in case["checklist_by_dim"].items():
            if not items:
                problems.append(f"{name}: checklist_by_dim.{dim} 为空")

        for dim, anchors in case["anchors_by_dim"].items():
            if dim not in dim_keys:
                problems.append(f"{name}: anchors 含未定义维度 {dim}")
            if not ANCHOR_KEYS.issubset(anchors):
                problems.append(f"{name}: anchors_by_dim.{dim} 需包含 0 / 5.0 / 10.0 三档")

        for item in case["input_files"]:
            rel = item.get("rel", "")
            if not rel.startswith("workspace/"):
                problems.append(f"{name}: 附件路径应以 workspace/ 开头: {rel}")
            target = eval_dir / rel
            if not target.exists():
                problems.append(f"{name}: 附件不存在: {rel}")
            else:
                case_dirs.add(Path(rel).parts[1] if len(Path(rel).parts) > 1 else "")

    # ---- 冻结的附件不能是空目录之外的孤儿
    ws = eval_dir / "workspace"
    if ws.exists():
        for d in sorted(p for p in ws.iterdir() if p.is_dir()):
            if d.name not in case_dirs:
                problems.append(f"workspace/{d.name} 未被任何用例引用")

    info["files"] = len(list(iter_files(eval_dir)))
    return problems, info


def build(eval_dir):
    DIST.mkdir(parents=True, exist_ok=True)
    out = DIST / f"{eval_dir.name}-eval.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in iter_files(eval_dir):
            z.write(path, path.relative_to(eval_dir).as_posix())
    return out


def main():
    parser = argparse.ArgumentParser(description="评测集打包")
    parser.add_argument("skill", nargs="?", help="只处理指定技能（目录名）")
    parser.add_argument("--check", action="store_true", help="只校验，不生成 zip")
    args = parser.parse_args()

    if not EVAL_ROOT.exists():
        print(f"没有找到评测集目录: {EVAL_ROOT}")
        return 1

    targets = sorted(p for p in EVAL_ROOT.iterdir() if p.is_dir() and (p / "header.json").exists())
    if args.skill:
        targets = [p for p in targets if p.name == args.skill]
        if not targets:
            print(f"没有找到评测集: evaluation/{args.skill}")
            return 1
    if not targets:
        print("evaluation/ 下没有任何评测集（需要 header.json）")
        return 1

    results = []
    failed = 0
    for eval_dir in targets:
        problems, info = check_eval(eval_dir)
        out = None
        if not problems and not args.check:
            out = build(eval_dir)
            if out.stat().st_size > MAX_ZIP_BYTES:
                problems.append(f"包体积 {out.stat().st_size / 1024 / 1024:.1f} MB 超过平台 10MB 限制")
        results.append((info, problems, out))
        if problems:
            failed += 1

    width = max(len(i["name"]) for i, _, _ in results) + 2
    print(f"{'技能'.ljust(width)}{'维度':>4}{'用例':>5}{'文件':>5}  {'大小':>9}  结果")
    print("-" * (width + 34))
    for info, problems, out in results:
        size = f"{out.stat().st_size / 1024:.1f} KB" if out else "-"
        status = "OK" if not problems else f"FAIL ({len(problems)})"
        print(f"{info['name'].ljust(width)}{info['dims']:>4}{info['cases']:>5}"
              f"{info['files']:>5}  {size:>9}  {status}")
        for p in problems:
            print(f"{' ' * width}  - {p}")

    print()
    if failed:
        print(f"{failed}/{len(results)} 个评测集未通过校验。")
        return 1
    if args.check:
        print(f"{len(results)} 个评测集全部通过校验。")
    else:
        print(f"已生成 {len(results)} 个评测集到 dist/evals/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
