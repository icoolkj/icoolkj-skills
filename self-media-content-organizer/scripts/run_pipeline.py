#!/usr/bin/env python3
"""NoteIntel deterministic pipeline.

The pipeline is the single hand-off point for source ingestion, analysis,
candidate extraction and risk scanning. It persists every intermediate result
and returns a machine-readable status instead of silently dropping failures.
A model-created pack can optionally be supplied for JSON validation and view
export; the pipeline never promotes heuristic candidates to verified facts.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze_material
import extract_candidates
import scan_risks


def load_module(name):
    path = os.path.join(HERE, name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)


def run_pipeline(input_source, output_dir, config_path=None, pack_path=None,
                 template_md=None, template_html=None, formats="md,html,json"):
    os.makedirs(output_dir, exist_ok=True)
    started = datetime.now().isoformat()
    manifest = {
        "pipeline_version": "1.0",
        "status": "running",
        "started_at": started,
        "input": input_source,
        "output_dir": os.path.abspath(output_dir),
        "steps": [],
        "errors": [],
        "warnings": [],
    }
    write_json(os.path.join(output_dir, "pipeline.json"), manifest)

    def step(name, status, outputs=None, error=None, warning=None):
        item = {"name": name, "status": status}
        if outputs:
            item["outputs"] = outputs
        if error:
            item["error"] = str(error)
            manifest["errors"].append({"step": name, "message": str(error)})
        if warning:
            item["warning"] = str(warning)
            manifest["warnings"].append({"step": name, "message": str(warning)})
        manifest["steps"].append(item)
        write_json(os.path.join(output_dir, "pipeline.json"), manifest)

    try:
        analysis = analyze_material.analyze(input_source, analyze_material.load_config(config_path))
        clean_path = os.path.join(output_dir, "clean_text.txt")
        with open(clean_path, "w", encoding="utf-8") as handle:
            handle.write(analysis["clean_text"])
        analysis_path = os.path.join(output_dir, "analysis.json")
        write_json(analysis_path, analysis)
        step("analyze", "success", [analysis_path, clean_path],
             warning="；".join(analysis.get("limitations", [])) or None)
    except Exception as exc:
        step("analyze", "failed", error=exc)
        manifest["status"] = "failed"
        manifest["finished_at"] = datetime.now().isoformat()
        write_json(os.path.join(output_dir, "pipeline.json"), manifest)
        return manifest

    try:
        candidates = extract_candidates.extract_candidates(analysis["clean_text"])
        quota = analysis.get("quotas", {}).get("core_facts")
        if isinstance(quota, str) and "-" in quota:
            quota = int(quota.split("-")[-1])
        if isinstance(quota, int):
            candidates = extract_candidates.filter_by_quota(candidates, quota)
        candidate_result = {"total_candidates": len(candidates), "candidates": candidates,
                            "source": analysis.get("source"), "source_type": analysis.get("source_type"),
                            "note": "候选项是规则筛查结果，不等同于已核实事实。"}
        candidate_path = os.path.join(output_dir, "candidates.json")
        write_json(candidate_path, candidate_result)
        step("extract_candidates", "success", [candidate_path])
    except Exception as exc:
        step("extract_candidates", "failed", error=exc)

    try:
        risks = scan_risks.scan_risks(analysis["clean_text"], source_count=1)
        risk_result = {"total_risks": len(risks), "risks": risks,
                       "note": "风险扫描是提示机制，需上下文判定和人工/外部核验。"}
        risk_path = os.path.join(output_dir, "risks.json")
        write_json(risk_path, risk_result)
        step("scan_risks", "success", [risk_path])
    except Exception as exc:
        step("scan_risks", "failed", error=exc)

    if pack_path:
        try:
            validate_json_pack = load_module("validate_json_pack")
            with open(pack_path, encoding="utf-8") as handle:
                pack = json.load(handle)
            validation = validate_json_pack.validate(pack)
            validation_path = os.path.join(output_dir, "pack-validation.json")
            write_json(validation_path, validation)
            if validation["valid"]:
                step("validate_json_pack", "success", [validation_path])
            else:
                step("validate_json_pack", "failed", [validation_path],
                     error="; ".join(validation["errors"]))
            if validation["valid"]:
                export_pack = load_module("export_pack")
                exported = {}
                requested = {item.strip() for item in formats.split(",") if item.strip()}
                if "md" in requested:
                    path = os.path.join(output_dir, "content-pack.md")
                    export_pack.export_md(pack, template_md or "", path)
                    exported["md"] = path
                if "html" in requested and template_html:
                    path = os.path.join(output_dir, "content-pack.preview.html")
                    export_pack.export_html(pack, template_html, path)
                    exported["html"] = path
                if "json" in requested:
                    path = os.path.join(output_dir, "content-pack.json")
                    export_pack.export_json(pack, path)
                    exported["json"] = path
                step("export", "success", list(exported.values()))
        except Exception as exc:
            step("validate_or_export", "failed", error=exc)
    else:
        step("pack", "awaiting_input", warning="分析产物已完成；提供 --pack 后才执行素材包门禁和导出。")

    manifest["source_sha256"] = hashlib.sha256(
        analysis["clean_text"].encode("utf-8")).hexdigest()
    manifest["status"] = "success" if not manifest["errors"] else "partial_failure"
    manifest["finished_at"] = datetime.now().isoformat()
    write_json(os.path.join(output_dir, "pipeline.json"), manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 统一素材处理流水线")
    parser.add_argument("--input", required=True, help="URL、文本文件、PDF、DOCX 或图片路径")
    parser.add_argument("--output-dir", required=True, help="中间结果和最终产物目录")
    parser.add_argument("--config")
    parser.add_argument("--pack", help="可选：模型整理后的 JSON 素材包，启用校验与导出")
    parser.add_argument("--template-md")
    parser.add_argument("--template-html")
    parser.add_argument("--formats", default="md,html,json")
    args = parser.parse_args()
    result = run_pipeline(args.input, args.output_dir, args.config, args.pack,
                          args.template_md, args.template_html, args.formats)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
