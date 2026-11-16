"""Synthetic contract tests only; no model calls or commercial acceptance claims."""
import copy
import importlib.util
import hashlib
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_delivery.py"
spec = importlib.util.spec_from_file_location("delivery", SCRIPT)
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


def png(width=3, height=4):
    def chunk(name, data):
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress((b"\0" + b"\xff\xff\xff" * width) * height)) + chunk(b"IEND", b""))


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        (self.base / "poster.png").write_bytes(png())
        checks = {k: {"status": "pass" if k in delivery.BASE else "not_applicable", "evidence": "synthetic test, not visual evidence"} for k in delivery.CHECKS}
        self.data = {"schema_version": 1, "skill_version": "1.0.1", "mode": "image", "requested_count": 1,
                     "required_copy": [{"id": "c1", "text": "仅限新用户", "source": "test fixture"}],
                     "items": [{"id": "p1", "version": 1, "status": "ready", "prompt": "synthetic test only", "attempts": 1,
                                "artifact": {"kind": "local", "location": "poster.png"},
                                "target": {"ratio": [3, 4], "width": 3, "height": 4},
                                "actual": {"width": 3, "height": 4, "format": "PNG"},
                                "required_ids": ["c1"], "copy_checks": [{"id": "c1", "status": "pass", "evidence": "synthetic test"}],
                                "checks": checks, "applicable": sorted(delivery.BASE)}]}

    def tearDown(self):
        self.temp.cleanup()

    def errors(self):
        return delivery.validate(self.data, self.base)

    def test_valid_record_not_visual_approval(self):
        self.assertEqual(self.errors(), [])

    def test_missing_file(self):
        self.data["items"][0]["artifact"]["location"] = "missing.png"
        self.assertTrue(self.errors())

    def test_forged_metadata(self):
        self.data["items"][0]["actual"]["width"] = 30
        self.assertTrue(self.errors())

    def test_wrong_dimensions(self):
        self.data["items"][0]["target"].update(width=6, height=8)
        self.assertTrue(self.errors())

    def test_conflicting_ratio(self):
        self.data["items"][0]["target"]["ratio"] = [16, 9]
        self.assertTrue(self.errors())

    def test_unverified_cannot_be_ready(self):
        self.data["items"][0]["checks"]["visual"]["status"] = "unverified"
        self.assertTrue(self.errors())

    def test_draft_with_unverified_is_valid(self):
        item = self.data["items"][0]
        item.update(status="draft", reason="visual not checked")
        item["checks"]["visual"]["status"] = "unverified"
        self.assertEqual(self.errors(), [])

    def test_failed_brand_cannot_hide_outside_applicable(self):
        self.data["items"][0]["checks"]["brand"]["status"] = "fail"
        self.assertTrue(self.errors())

    def test_unverified_qr_cannot_hide_outside_applicable(self):
        self.data["items"][0]["checks"]["qr"]["status"] = "unverified"
        self.assertTrue(self.errors())

    def test_applicable_cannot_be_not_applicable(self):
        self.data["items"][0]["checks"]["visual"]["status"] = "not_applicable"
        self.assertTrue(self.errors())

    def test_missing_copy(self):
        self.data["items"][0]["required_ids"] = []
        self.assertTrue(self.errors())

    def test_failed_copy(self):
        self.data["items"][0]["copy_checks"][0]["status"] = "fail"
        self.assertTrue(self.errors())

    def test_retries(self):
        self.data["items"][0]["attempts"] = 4
        self.assertTrue(self.errors())

    def test_text_request_cannot_generate(self):
        self.data["mode"] = "prompt"
        self.assertTrue(self.errors())

    def test_plan_only(self):
        self.data["mode"] = "prompt"
        self.data["items"][0].update(status="plan_only", attempts=0, artifact=None, reason="prompt only", actual=None)
        self.assertEqual(self.errors(), [])

    def test_blocked_without_image(self):
        self.data["items"][0].update(status="blocked", artifact=None, reason="provider failed", actual=None)
        self.assertEqual(self.errors(), [])

    def test_duplicate_artifacts(self):
        self.data["requested_count"] = 2
        second = copy.deepcopy(self.data["items"][0])
        second["id"] = "p2"
        self.data["items"].append(second)
        self.assertTrue(self.errors())

    def test_edit_requires_scope_check(self):
        self.data["mode"] = "edit"
        self.assertTrue(self.errors())

    def test_rename_is_not_format_conversion(self):
        (self.base / "poster.jpg").write_bytes(png())
        self.data["items"][0]["artifact"]["location"] = "poster.jpg"
        self.assertTrue(self.errors())

    def test_boolean_not_count(self):
        self.data["requested_count"] = True
        self.assertTrue(self.errors())

    def test_malformed_record(self):
        self.assertTrue(delivery.validate([], self.base))
        self.data["items"][0]["checks"] = None
        self.assertTrue(self.errors())

    def test_remote_metadata_is_record_only(self):
        self.data["items"][0]["artifact"] = {"kind": "remote", "location": "attachment:test-only"}
        self.assertEqual(self.errors(), [])

    def make_v2(self, method="generated"):
        self.data.update(schema_version=2, skill_version="1.0.2")
        item = self.data["items"][0]
        item["production"] = {"method": method}
        for key in delivery.EXTENDED:
            item["checks"][key] = {"status": "pass", "evidence": "synthetic test only"}
            item["applicable"].append(key)
        if method == "deterministic":
            item["production"].update(brand_id="test", recipe="test.json", layout_report="layout.json")
            (self.base / "preview.png").write_bytes(png())
            recipe = {"schema_version": 1, "canvas": {"width": 3, "height": 4}, "brand": "brand.json", "blocks": [{"type": "rect"}]}
            (self.base / "test.json").write_text(json.dumps(recipe), encoding="utf-8")
            (self.base / "brand.json").write_text(json.dumps({"schema_version": 1, "id": "test"}), encoding="utf-8")
            self.report = {"schema_version": 1, "brand_id": "test",
                           "artifact": {"location": "poster.png", "sha256": hashlib.sha256(png()).hexdigest(),
                                        "width": 3, "height": 4, "format": "PNG"},
                           "preview": {"location": "preview.png", "width": 3, "height": 4, "sha256": hashlib.sha256(png()).hexdigest()},
                           "reproducibility": {"config": {"sha256": hashlib.sha256((self.base / "test.json").read_bytes()).hexdigest()},
                                               "brand": {"sha256": hashlib.sha256((self.base / "brand.json").read_bytes()).hexdigest()}},
                           "checks": {k: {"status": "pass", "evidence": "synthetic"}
                                      for k in ("layout", "readability", "assets")}}
            self.save_report()
        return item

    def save_report(self):
        (self.base / "layout.json").write_text(json.dumps(self.report), encoding="utf-8")

    def test_v2_generated_record(self):
        self.make_v2()
        self.assertEqual(self.errors(), [])

    def test_v2_cannot_downgrade_schema(self):
        self.data["skill_version"] = "1.0.2"
        self.assertTrue(self.errors())

    def test_v2_requires_readability(self):
        item = self.make_v2()
        del item["checks"]["readability"]
        self.assertTrue(self.errors())

    def test_v2_unknown_check_not_silently_ignored(self):
        item = self.make_v2()
        item["checks"]["assetz"] = {"status": "fail", "evidence": "typo"}
        self.assertTrue(self.errors())

    def test_v2_requires_production(self):
        item = self.make_v2()
        del item["production"]
        self.assertTrue(self.errors())

    def test_bound_report_valid(self):
        self.make_v2("deterministic")
        self.assertEqual(self.errors(), [])

    def test_stale_report_hash(self):
        self.make_v2("deterministic")
        (self.base / "poster.png").write_bytes(png() + b"changed")
        self.assertTrue(self.errors())

    def test_missing_mobile_preview(self):
        self.make_v2("deterministic")
        self.report["preview"]["location"] = "missing.png"
        self.save_report()
        self.assertTrue(self.errors())

    def test_missing_recipe_blocks_delivery(self):
        item = self.make_v2("deterministic")
        item["production"]["recipe"] = "missing.json"
        self.assertTrue(self.errors())

    def test_changed_recipe_blocks_old_evidence(self):
        self.make_v2("deterministic")
        with (self.base / "test.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
        self.assertTrue(self.errors())

    def test_changed_brand_config_blocks_old_evidence(self):
        self.make_v2("deterministic")
        with (self.base / "brand.json").open("a", encoding="utf-8") as stream:
            stream.write(" ")
        self.assertTrue(self.errors())

    def test_stale_preview_same_dimensions(self):
        self.make_v2("deterministic")
        (self.base / "preview.png").write_bytes(png() + b"changed")
        self.assertTrue(self.errors())

    def test_preview_wrong_ratio(self):
        self.make_v2("deterministic")
        raw = png(3, 3)
        (self.base / "preview.png").write_bytes(raw)
        self.report["preview"].update(height=3, sha256=hashlib.sha256(raw).hexdigest())
        self.save_report()
        self.assertTrue(self.errors())

    def test_report_brand_mismatch(self):
        self.make_v2("deterministic")
        self.report["brand_id"] = "other"
        self.save_report()
        self.assertTrue(self.errors())

    def test_failed_readability_cannot_claim_pass(self):
        self.make_v2("deterministic")
        self.report["checks"]["readability"]["status"] = "fail"
        self.save_report()
        self.assertTrue(self.errors())

    def test_draft_can_record_readability_failure(self):
        item = self.make_v2("deterministic")
        item.update(status="draft", reason="small type")
        item["checks"]["readability"]["status"] = "fail"
        self.report["checks"]["readability"]["status"] = "fail"
        self.save_report()
        self.assertEqual(self.errors(), [])

    def test_manual_asset_review_binds_same_artifact(self):
        item = self.make_v2("deterministic")
        self.report["checks"]["assets"]["status"] = "unverified"
        self.save_report()
        self.assertTrue(self.errors())
        item["production"]["review_overrides"] = {"assets": {"evidence": "synthetic review", "artifact_sha256": self.report["artifact"]["sha256"]}}
        self.assertEqual(self.errors(), [])
        item["production"]["review_overrides"]["assets"]["artifact_sha256"] = "stale"
        self.assertTrue(self.errors())

    def test_fail_cannot_be_overridden(self):
        item = self.make_v2("deterministic")
        self.report["checks"]["readability"]["status"] = "fail"
        item["production"]["review_overrides"] = {"readability": {"evidence": "synthetic review", "artifact_sha256": self.report["artifact"]["sha256"]}}
        self.save_report()
        self.assertTrue(self.errors())

    def test_malformed_layout_report(self):
        self.make_v2("deterministic")
        self.report["artifact"] = None
        self.save_report()
        self.assertTrue(self.errors())

    def test_v2_text_only_needs_no_layout_report(self):
        item = self.make_v2()
        self.data["mode"] = "prompt"
        item.update(status="plan_only", artifact=None, attempts=0, reason="prompt only")
        del item["production"]
        self.assertEqual(self.errors(), [])

    def test_cases_are_not_claimed_as_passed(self):
        cases = json.loads((Path(__file__).parent / "acceptance.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len({c["id"] for c in cases}), 26)
        self.assertTrue(all(c["status"] == "not_run" for c in cases))


if __name__ == "__main__":
    unittest.main()
