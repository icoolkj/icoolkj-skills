import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scan.py"
spec = importlib.util.spec_from_file_location("sod_scan", SCRIPT)
sod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sod)


class P0RegressionTests(unittest.TestCase):
    def test_failed_script_read_is_not_no_detection(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sample.ps1"
            p.write_text("Write-Output 'hello'", encoding="utf-8")
            original = sod.check_script_content
            sod.check_script_content = lambda _p: ([], "simulated read failure")
            try:
                result = sod.scan_file(str(p), "standard", {})
            finally:
                sod.check_script_content = original
            self.assertEqual(result["classification"], "unchecked")
            self.assertEqual(result["result_label"], "unknown")
            self.assertEqual(result["checks"]["script_analysis"], "failed")

    def test_symlink_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = base / "target.txt"
            target.write_text("hello", encoding="utf-8")
            link = base / "link.txt"
            try:
                link.symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("symlink creation unavailable")
            with self.assertRaises(ValueError):
                sod.collect_files(str(link), None, [])

    def test_zip_entry_limit_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "many.zip"
            with zipfile.ZipFile(p, "w") as zf:
                for i in range(sod.MAX_ZIP_ENTRIES + 1):
                    zf.writestr(f"f{i}.txt", "x")
            result = sod.scan_file(str(p), "deep", {})
            self.assertEqual(result["classification"], "unchecked")
            self.assertEqual(result["checks"]["archive"], "incomplete")

    def test_clean_file_is_labelled_no_detection_not_safe_claim(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "note.txt"
            p.write_text("hello", encoding="utf-8")
            result = sod.scan_file(str(p), "standard", {})
            self.assertEqual(result["classification"], "safe")  # compatibility field
            self.assertEqual(result["result_label"], "no_detection")
            self.assertEqual(result["coverage"], "complete")


if __name__ == "__main__":
    unittest.main()
