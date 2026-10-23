#!/usr/bin/env python3
"""Run the complete data analysis report pipeline.

Pipeline:
  1. Load data and profile
  2. Compliance check (report prose must already be complete in report.json)
  3. Chart generation
  4. Report composition
  5. Export to Markdown/HTML/PDF
  6. Quality verification
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from data_loader import load_data
from compliance import check_report, check_data_quality
from composer import compose_report, save_composed
from exporter import export_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Data analysis report pipeline")
    parser.add_argument("report_json", help="Path to report JSON (plan)")
    parser.add_argument("--work-dir", required=True, help="Output working directory")
    parser.add_argument("--force-charts", action="store_true", help="Regenerate charts even if files exist")
    parser.add_argument("--formats", nargs="*", default=None, help="Override output formats")
    parser.add_argument("--skip-verify", action="store_true", help="Skip final verification")
    args = parser.parse_args()

    report_path = Path(args.report_json)
    work_dir = Path(args.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    # --- Load data ---
    data = None
    data_source = report.get("data_source", "")
    if data_source and Path(data_source).exists():
        try:
            data = load_data(data_source)
            print(f"[OK] Data loaded: {data['shape']} rows x cols, format={data['format']}")
        except Exception as exc:
            print(f"[WARN] Data loading failed: {exc}")

    # --- Compliance check ---
    issues = check_report(report, data)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 2
    print("[OK] Compliance passed")

    # --- Compose report (generates charts) ---
    composed = compose_report(report, work_dir)
    save_composed(composed, work_dir / "composed.json")
    print(f"[OK] Report composed: {len(composed['sections'])} sections")

    chart_count = sum(1 for s in composed["sections"] if s.get("chart_path"))
    print(f"[OK] Charts generated: {chart_count}")

    # --- Export ---
    formats = args.formats or report.get("output_formats", ["markdown", "html"])
    outputs = export_report(composed, work_dir, formats)
    print(f"[OK] Exported {len(outputs)} files")

    # --- Quality verification ---
    if not args.skip_verify:
        print("\n" + "=" * 50)
        print("  报告质量验证")
        print("=" * 50)
        for output in outputs:
            size = output.stat().st_size
            print(f"  {output.name}: {size:,} bytes")
            if output.suffix == ".md":
                lines = output.read_text(encoding="utf-8").count("\n")
                print(f"    Markdown 行数: {lines}")
            elif output.suffix == ".html":
                has_style = "var(--primary)" in output.read_text(encoding="utf-8")
                print(f"    HTML 样式注入: {'✓' if has_style else '✗'}")
        charts_dir = work_dir / "charts"
        if charts_dir.exists():
            chart_files = list(charts_dir.glob("*.png"))
            print(f"  图表文件: {len(chart_files)} 个")
        print("=" * 50)

    print(f"\n[DONE] All outputs in: {work_dir}")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    raise SystemExit(main())
