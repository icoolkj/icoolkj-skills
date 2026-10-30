#!/usr/bin/env python3
"""XHS workflow: preprocess source, validate model pack, build copy + studio."""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_pipeline
import build_xhs_from_pack


def main():
    parser = argparse.ArgumentParser(description="事实驱动的小红书内容与卡片工作流")
    parser.add_argument("--input", required=True, help="原始文字、文本文件、PDF、DOCX、图片或网页")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pack", help="模型/人工整理后的 content-pack JSON；没有它只完成预处理")
    args = parser.parse_args()
    result = run_pipeline.run_pipeline(args.input, args.output_dir, pack_path=args.pack)
    if args.pack and result.get("status") in {"success", "partial_failure"}:
        with open(args.pack, encoding="utf-8") as handle: pack = json.load(handle)
        validation = build_xhs_from_pack.validate(pack)
        if validation["valid"]:
            md_path = os.path.join(args.output_dir, "xhs-copy-pack.md")
            html_path = os.path.join(args.output_dir, "xhs-card-studio.html")
            with open(md_path, "w", encoding="utf-8") as handle: handle.write(build_xhs_from_pack.build_markdown(pack))
            with open(html_path, "w", encoding="utf-8") as handle: handle.write(build_xhs_from_pack.build_html(pack))
            result.setdefault("steps", []).append({"name": "xhs_copy_and_cards", "status": "success", "outputs": [md_path, html_path]})
        else:
            result.setdefault("steps", []).append({"name": "xhs_copy_and_cards", "status": "blocked", "warning": "素材包未通过 JSON 门禁"})
        with open(os.path.join(args.output_dir, "pipeline.json"), "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") != "failed" else 1

if __name__ == "__main__": raise SystemExit(main())
