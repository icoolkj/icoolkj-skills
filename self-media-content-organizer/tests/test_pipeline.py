import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_material
import merge_packs
import run_pipeline
import scan_risks
import validate_json_pack


def test_docx_reader(tmp_path):
    path = tmp_path / "source.docx"
    document = """<?xml version='1.0' encoding='UTF-8'?>
    <w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
      <w:body><w:p><w:r><w:t>2025年营收增长20%。</w:t></w:r></w:p></w:body>
    </w:document>"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/document.xml", document)
    text, kind, metadata = analyze_material.read_file(str(path))
    assert "营收增长20%" in text
    assert kind == "docx"
    assert metadata["parser"] == "docx-xml"


def test_pdf_reader(tmp_path):
    pdf = ROOT / "tests" / "text.pdf"
    text, kind, _ = analyze_material.read_file(str(pdf))
    assert "2025" in text
    assert kind == "pdf"


def test_empty_pdf_is_explicit_error():
    pdf = ROOT / "tests" / "empty.pdf"
    try:
        analyze_material.read_file(str(pdf))
    except analyze_material.InputReadError as exc:
        assert "没有可提取文本" in str(exc)
    else:
        raise AssertionError("empty PDF must not be treated as valid text")


def test_scanned_pdf_uses_ocr_or_reports_dependency_boundary():
    pdf = ROOT / "tests" / "scanned.pdf"
    try:
        text, kind, metadata = analyze_material.read_file(str(pdf))
    except analyze_material.InputReadError as exc:
        assert "OCR" in str(exc) or "tesseract" in str(exc)
    else:
        assert kind == "pdf_scanned"
        assert metadata["needs_review"] is True
        assert text.strip()


def test_pipeline_persists_intermediate_results(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("2025年销量达到100万辆，同比增长20%。\n\n这是一个方法步骤。", encoding="utf-8")
    out = tmp_path / "out"
    result = run_pipeline.run_pipeline(str(source), str(out))
    assert result["status"] == "success"
    for name in ("pipeline.json", "analysis.json", "clean_text.txt", "candidates.json", "risks.json"):
        assert (out / name).exists()
    manifest = json.loads((out / "pipeline.json").read_text(encoding="utf-8"))
    assert [step["name"] for step in manifest["steps"][:3]] == ["preprocess", "extract_candidates", "scan_risks"]


def test_pipeline_stops_after_input_failure(tmp_path):
    result = run_pipeline.run_pipeline(str(tmp_path / "missing.pdf"), str(tmp_path / "out"))
    assert result["status"] == "failed"
    assert result["steps"][0]["name"] == "preprocess"
    assert len(result["steps"]) == 1


def test_merge_uses_claim_and_remaps_sources_and_array_refs(tmp_path):
    base = {
        "source": "demo", "summary": "s", "sources": [{"source_id": "S1", "type": "text"}],
        "facts": [{"id": "F1", "claim": "2025年营收增长20%", "source_ids": ["S1"],
                   "location": "第1段", "quote": "2025年营收增长20%", "confidence": "high", "status": "reported"}],
        "topics": [{"id": "T1", "title": "t", "angle": "a", "audience": "u", "form": "f",
                    "related_facts": ["F1"], "value_add": "v"}]
    }
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
    b.write_text(json.dumps({**base, "facts": [{**base["facts"][0], "claim": "员工人数达到500人"}]}, ensure_ascii=False), encoding="utf-8")
    merged = merge_packs.merge_packs([str(a), str(b)])
    assert len(merged["facts"]) == 2
    assert merged["topics"][0]["related_facts"] == ["F1"]
    assert merged["topics"][1]["related_facts"] == ["F2"]
    assert {s["source_id"] for s in merged["sources"]} == {"P1_S1", "P2_S1"}
    assert validate_json_pack.validate(merged)["valid"]


def test_multi_source_risk_does_not_claim_single_source():
    assert not any(r["type"] == "单一来源" for r in scan_risks.scan_risks("数据来自甲乙两方。", source_count=2))


def test_json_validator_separates_structure_and_semantic_risk():
    pack = {"source": "x", "summary": "s", "sources": [{"source_id": "S1"}],
            "facts": [{"id": "F1", "claim": "增长20%", "source_ids": ["S1"], "location": "p1", "quote": "增长", "confidence": "high", "status": "reported"}],
            "topics": []}
    result = validate_json_pack.validate(pack)
    assert result["valid"] is True
    assert result["structure_errors"] == []
    assert result["semantic_risks"]
