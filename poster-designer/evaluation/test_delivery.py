"""Synthetic contract tests only; no model calls or commercial acceptance claims."""
import copy
import importlib.util
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

    def test_cases_are_not_claimed_as_passed(self):
        cases = json.loads((Path(__file__).parent / "acceptance.json").read_text(encoding="utf-8"))["cases"]
        self.assertEqual(len({c["id"] for c in cases}), 18)
        self.assertTrue(all(c["status"] == "not_run" for c in cases))


if __name__ == "__main__":
    unittest.main()
