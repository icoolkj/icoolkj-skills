"""Regression tests for the HTML render path. No Playwright required."""
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_html_poster as checker
import validate_delivery as validator

EXAMPLE = ROOT / "assets" / "example-poster.html"


def write_png(path, width, height):
    header = (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR"
              + struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    path.write_bytes(header + b"\x00" * 16)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class StaticCheckTests(unittest.TestCase):
    def load(self):
        return checker.strip_comments(EXAMPLE.read_text(encoding="utf-8-sig"))

    def test_example_passes_static_checks(self):
        checks, width, height = checker.static_checks(self.load(), "A4", 3)
        self.assertEqual((width, height), (794, 1123))
        self.assertEqual([c for c in checks if c["status"] == "fail"], [])

    def test_forbidden_css_and_undefined_var_fail(self):
        html = self.load().replace(
            "<style>", "<style>\n  .bad{background-clip:text;color:var(--missing-token);}", 1)
        checks, _, _ = checker.static_checks(html, "A4", 3)
        names = {c["id"] for c in checks if c["status"] == "fail"}
        self.assertIn("css_compat", names)
        self.assertIn("css_vars", names)

    def test_wrong_canvas_fails(self):
        html = self.load().replace('data-canvas="794x1123"', 'data-canvas="800x1200"', 1)
        checks, width, height = checker.static_checks(html, "A4", 3)
        self.assertEqual((width, height), (800, 1200))
        self.assertIn("canvas", {c["id"] for c in checks if c["status"] == "fail"})

    def test_remote_image_is_not_export_safe(self):
        html = self.load().replace(
            "<svg viewBox=\"0 0 64 64\" role=\"img\"",
            "<img src=\"https://example.com/logo.png\"><svg viewBox=\"0 0 64 64\" role=\"img\"", 1)
        checks, _, _ = checker.static_checks(html, "A4", 3)
        self.assertIn("embedded_images", {c["id"] for c in checks if c["status"] == "fail"})


class HtmlRenderRecordTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.html = self.base / "poster.html"
        self.html.write_text(EXAMPLE.read_text(encoding="utf-8-sig"), encoding="utf-8")
        self.png = self.base / "poster.png"
        write_png(self.png, 2382, 3369)
        self.report = {
            "schema_version": 1,
            "method": "html_render",
            "artifact": {
                "location": "poster.png", "sha256": digest(self.png),
                "width": 2382, "height": 3369, "format": "PNG",
            },
            "reproducibility": {"config": {"location": "poster.html", "sha256": digest(self.html)}},
            "checks": {
                "layout": {"status": "pass", "evidence": "无越界"},
                "html_export": {"status": "pass", "evidence": "实测导出 2382x3369"},
            },
        }
        self.record = {
            "schema_version": 2,
            "skill_version": "1.2.0",
            "mode": "image",
            "requested_count": 1,
            "required_copy": [{"id": "title", "text": "A4 信息单页模板骨架", "source": "示例"}],
            "items": [{
                "id": "p1", "version": 1, "status": "draft", "reason": "待人工看图",
                "prompt": "A4 单页设计说明", "attempts": 0,
                "artifact": {"kind": "local", "location": "poster.png"},
                "target": {"ratio": [794, 1123], "width": 2382, "height": 3369},
                "actual": {"width": 2382, "height": 3369, "format": "PNG"},
                "required_ids": ["title"],
                "copy_checks": [{"id": "title", "status": "pass", "evidence": "逐字一致"}],
                "checks": {
                    "content": {"status": "pass", "evidence": "核对"},
                    "visual": {"status": "unverified", "evidence": "待看图"},
                    "dimensions": {"status": "pass", "evidence": "2382x3369"},
                    "access": {"status": "pass", "evidence": "本地可读"},
                    "readability": {"status": "unverified", "evidence": "待人工"},
                    "assets": {"status": "unverified", "evidence": "无栅格素材"},
                    "brand": {"status": "pass", "evidence": "示例"},
                    "edit_scope": {"status": "not_applicable", "evidence": "新建"},
                    "qr": {"status": "not_applicable", "evidence": "无二维码"},
                    "rights": {"status": "not_applicable", "evidence": "无外部素材"},
                    "print": {"status": "not_applicable", "evidence": "数字分发"},
                },
                "applicable": ["content", "visual", "dimensions", "access", "readability", "assets", "brand"],
                "production": {
                    "method": "html_render", "recipe": "poster.html",
                    "layout_report": "layout-report.json",
                },
            }],
        }

    def tearDown(self):
        self.temp.cleanup()

    def save(self, report=None, record=None):
        (self.base / "layout-report.json").write_text(
            json.dumps(report or self.report, ensure_ascii=False), encoding="utf-8")
        path = self.base / "delivery.json"
        path.write_text(json.dumps(record or self.record, ensure_ascii=False), encoding="utf-8")
        return validator.validate(json.loads(path.read_text(encoding="utf-8")), self.base)

    def test_valid_html_record(self):
        self.assertEqual(self.save(), [])

    def test_changed_html_blocks_old_report(self):
        self.html.write_text(self.html.read_text(encoding="utf-8") + "\n<!-- edit -->\n", encoding="utf-8")
        self.assertTrue(any("layout report recipe hash mismatch" in e for e in self.save()))

    def test_ready_requires_passed_export(self):
        self.report["checks"]["html_export"] = {"status": "unverified", "evidence": "未实测"}
        record = json.loads(json.dumps(self.record))
        record["items"][0]["status"] = "ready"
        for name in ("visual", "readability", "assets"):
            record["items"][0]["checks"][name] = {"status": "pass", "evidence": "测试替身"}
        errors = self.save(record=record)
        self.assertTrue(any("html_export must pass before ready" in e for e in errors))

    def test_unknown_method_rejected(self):
        record = json.loads(json.dumps(self.record))
        record["items"][0]["production"]["method"] = "html"
        self.assertTrue(any("production.method" in error for error in self.save(record=record)))


if __name__ == "__main__":
    unittest.main()