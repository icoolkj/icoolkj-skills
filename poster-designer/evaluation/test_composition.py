"""确定性排版测试。真实字体通过 POSTER_TEST_FONT / POSTER_TEST_FONT_INDEX 提供。"""
import copy
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compose_poster.py"
spec = importlib.util.spec_from_file_location("composition", SCRIPT)
composition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(composition)


def fixtures():
    brand = {"schema_version": 1, "id": "test-brand", "colors": {"background": "#F4F7FB", "ink": "#11263A"},
             "fonts": {name: {"path": "missing-placeholder.ttf", "index": 0} for name in ("title", "body")}}
    data = {"schema_version": 1, "brand": "brand.json", "canvas": {"width": 600, "height": 800, "background": "background"},
            "reading": {"mode": "mobile", "preview_width": 390, "min_font_px": 12}, "prompt": "公开虚构技术测试",
            "required_copy": [{"id": "copy", "text": "Hello 123!", "source": "测试原文"}],
            "blocks": [{"id": "text", "type": "text", "box": [40, 40, 520, 120], "text": "Hello 123!", "font": "body", "font_size": 40,
                        "color": "ink", "required_ids": ["copy"]}]}
    return data, brand


class MetricFont:
    """纯逻辑测量替身；真实字形和 PNG 测试在集成测试中独立验证。"""
    def getbbox(self, value, anchor="ls"):
        return (-2, -8, len(value) * 10, 3) if value else (0, 0, 0, 0)

    def getlength(self, value):
        return len(value) * 10


class LogicTests(unittest.TestCase):
    def setUp(self):
        self.data, self.brand = fixtures()

    def assert_invalid(self, code):
        with self.assertRaises(composition.CompositionError) as caught:
            composition.validate_config(self.data, self.brand)
        self.assertEqual(caught.exception.code, code)

    def test_valid_structure(self):
        composition.validate_config(self.data, self.brand)

    def test_chinese_long_english_exact_character_preservation(self):
        text = "输入资料字段匹配\nSupercalifragilisticexpialidocious 123!\n\n输出结果"
        result = composition.layout_text(text, MetricFont(), 10, [0, 0, 62, 300])
        reconstructed = "".join(line + ("\n" if ending == "explicit" else "") for line, ending in zip(result["lines"], result["line_breaks"]))
        self.assertEqual(reconstructed, text)
        self.assertGreater(len(result["lines"]), len(text.split("\n")))
        self.assertTrue(all(box[0] >= 0 and box[2] <= 62 and box[1] >= 0 and box[3] <= 300 for box in result["glyph_boxes"]))

    def test_overflow_never_shrinks_or_deletes(self):
        text = "输入资料字段匹配Supercalifragilisticexpialidocious"
        with self.assertRaisesRegex(composition.CompositionError, "禁止缩字"):
            composition.layout_text(text, MetricFont(), 10, [0, 0, 22, 12])
        self.assertEqual(text, "输入资料字段匹配Supercalifragilisticexpialidocious")

    def test_single_glyph_overflow(self):
        with self.assertRaises(composition.CompositionError) as caught:
            composition.layout_text("中", MetricFont(), 10, [0, 0, 11, 100])
        self.assertEqual(caught.exception.code, "text_overflow")

    def test_glyph_bearings_center_alignment(self):
        result = composition.layout_text("AB", MetricFont(), 10, [20, 30, 100, 80], align="center")
        self.assertEqual(result["glyph_boxes"][0], [59.0, 30, 81.0, 41])

    def test_missing_glyph(self):
        with self.assertRaisesRegex(composition.CompositionError, "U\\+4E2D"):
            composition.check_glyphs({ord("A"): "A"}, "A中", "text")
        with self.assertRaises(composition.CompositionError):
            composition.check_glyphs({65: ".notdef"}, "A", "text")
        composition.check_glyphs({65: "A"}, "A\nA", "text")

    def test_background_may_contain_content_and_touching_is_allowed(self):
        self.data["blocks"].append({"id": "background", "type": "rect", "box": [0, 0, 600, 800], "fill": "background"})
        other = copy.deepcopy(self.data["blocks"][0])
        other.update(id="other", box=[40, 160, 520, 120], required_ids=[])
        self.data["blocks"].append(other)
        composition.validate_config(self.data, self.brand)

    def test_content_overlap_rejected(self):
        other = copy.deepcopy(self.data["blocks"][0])
        other.update(id="other", box=[40, 159, 520, 120])
        self.data["blocks"].append(other)
        self.assert_invalid("content_overlap")

    def test_canvas_boundaries(self):
        for box in ([0, 0, 601, 100], [-1, 0, 100, 100], [0, 790, 100, 11]):
            with self.subTest(box=box):
                self.data["blocks"][0]["box"] = box
                self.assert_invalid("outside_canvas")

    def test_required_copy_omitted(self):
        self.data["blocks"][0]["required_ids"] = []
        self.assert_invalid("required_copy_unbound")

    def test_required_copy_changed_digits_punctuation_newlines(self):
        for changed in ("Hello 124!", "Hello 123", "Hello\n123!", "Hello 123！"):
            with self.subTest(changed=changed):
                self.data["blocks"][0]["text"] = changed
                self.assert_invalid("required_copy_changed")

    def test_unknown_required_id(self):
        self.data["blocks"][0]["required_ids"] = ["unknown"]
        self.assert_invalid("unknown_required_id")

    def test_duplicate_ids(self):
        self.data["blocks"].append(copy.deepcopy(self.data["blocks"][0]))
        self.assert_invalid("duplicate_block_id")

    def test_no_cover_or_stretch(self):
        for fit in ("cover", "stretch", None):
            self.data["blocks"].append({"id": "logo", "type": "image", "box": [40, 200, 200, 200], "path": "logo.png", "role": "logo", "fit": fit})
            self.assert_invalid("invalid_fit")
            self.data["blocks"].pop()

    def test_contain_size_and_upscale(self):
        self.assertEqual(composition.contain_size(64, 64, 256, 128), (128, 128, 2))
        self.assertEqual(composition.contain_size(200, 100, 80, 80), (80, 40, 0.4))

    def test_preview_cannot_exceed_canvas(self):
        self.data["reading"]["preview_width"] = 601
        self.assert_invalid("invalid_reading")

    def test_unknown_color_rejected(self):
        self.data["blocks"][0]["color"] = "#11263A"
        self.assert_invalid("unknown_color")

    def test_output_existing_never_touched_even_without_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sentinel = root / "keep.txt"
            sentinel.write_text("原有文件", encoding="utf-8")
            with patch.object(composition, "load_dependencies") as mocked:
                with self.assertRaises(composition.CompositionError) as caught:
                    composition.compose(root / "missing.json", root)
                self.assertEqual(caught.exception.code, "output_exists")
                mocked.assert_not_called()
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "原有文件")
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["keep.txt"])

    def test_missing_dependencies_are_explicit_errors(self):
        with patch.object(composition.importlib, "import_module", side_effect=ImportError("测试缺少依赖")):
            with self.assertRaisesRegex(composition.DependencyError, "pip install -r"):
                composition.load_dependencies()

    def test_delivery_is_draft_and_not_visual_approval(self):
        report = composition.new_report()
        report["brand_id"] = "test-brand"
        report["checks"]["readability"] = composition.check("fail", "测试字号过小")
        result = composition.delivery_record(self.data, Path("config.json").resolve(), report)
        self.assertEqual(result["schema_version"], 2)
        item = result["items"][0]
        self.assertEqual(item["status"], "draft")
        self.assertEqual(item["attempts"], 0)
        self.assertEqual(item["target"]["ratio"], [3, 4])
        self.assertEqual(set(item["checks"]), composition.CHECKS)
        self.assertEqual(item["checks"]["readability"]["status"], "fail")
        self.assertTrue(all(entry["status"] == "unverified" for entry in item["copy_checks"]))
        self.assertEqual(item["production"]["method"], "deterministic")

    def test_example_structure(self):
        assets = SCRIPT.parents[1] / "assets"
        data = composition.read_json(assets / "example-poster.json")
        brand = composition.read_json(assets / "example-brand.json")
        composition.validate_config(data, brand)
        self.assertTrue(all(block["font_size"] * 390 / 1200 >= 12 for block in data["blocks"] if block["type"] == "text"))


class DependencyTests(unittest.TestCase):
    def test_runtime_dependencies_installed_and_supported(self):
        # 缺依赖必须产生失败，不能把未运行的图像测试当作通过。
        composition.load_dependencies()


class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.dependencies = composition.load_dependencies()
        except composition.DependencyError as exc:
            raise unittest.SkipTest("图像集成测试未运行；DependencyTests 将报告依赖失败：%s" % exc)
        cls.font_path = os.environ.get("POSTER_TEST_FONT")
        if not cls.font_path:
            raise unittest.SkipTest("未设置 POSTER_TEST_FONT，真实字体集成测试未运行")
        cls.font_path = str(Path(cls.font_path).resolve())
        cls.font_index = int(os.environ.get("POSTER_TEST_FONT_INDEX", "0"))
        if not Path(cls.font_path).is_file():
            raise RuntimeError("POSTER_TEST_FONT 指向不存在的文件：%s" % cls.font_path)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data, self.brand = fixtures()
        self.Image = self.dependencies[0]
        for spec in self.brand["fonts"].values():
            spec.update(path=self.font_path, index=self.font_index)
        self.config = self.root / "config.json"
        self.output = self.root / "output"

    def write_inputs(self):
        self.config.write_text(json.dumps(self.data, ensure_ascii=False), encoding="utf-8")
        (self.root / "brand.json").write_text(json.dumps(self.brand, ensure_ascii=False), encoding="utf-8")

    def compose(self):
        self.write_inputs()
        return composition.compose(self.config, self.output)

    def assert_blocked(self, code):
        self.write_inputs()
        before = composition.sha256(self.config)
        with self.assertRaises(composition.CompositionError) as caught:
            composition.compose(self.config, self.output)
        self.assertEqual(caught.exception.code, code)
        self.assertFalse((self.output / "poster.png").exists())
        self.assertFalse((self.output / "preview-mobile.png").exists())
        self.assertFalse((self.output / "delivery.json").exists())
        report = json.loads((self.output / "layout-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["checks"]["layout"]["status"], "fail")
        self.assertEqual(composition.sha256(self.config), before)

    def add_image(self, size=(64, 64), box=None):
        path = self.root / "source.png"
        self.Image.new("RGB", size, "red").save(path)
        self.data["blocks"].append({"id": "asset", "type": "image", "path": "source.png", "role": "logo", "fit": "contain", "box": box or [40, 220, 256, 256]})
        return path

    def test_real_png_preview_source_hash_and_reproducibility(self):
        source = self.add_image(size=(400, 200), box=[40, 220, 200, 200])
        self.write_inputs()
        originals = {path: composition.sha256(path) for path in (source, self.config, self.root / "brand.json", Path(self.font_path))}
        report = composition.compose(self.config, self.output)
        for path, digest in originals.items():
            self.assertEqual(composition.sha256(path), digest)
        for filename, expected in (("poster.png", (600, 800)), ("preview-mobile.png", (390, 520))):
            with self.Image.open(self.output / filename) as image:
                image.load()
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, expected)
        self.assertEqual(report["assets"][0]["placed_box"], [40, 270, 200, 100])
        self.assertEqual(report["checks"]["assets"]["status"], "pass")
        self.assertEqual(report["artifact"]["sha256"], composition.sha256(self.output / "poster.png"))
        self.assertFalse(report["visual_approval"])
        self.assertEqual(report["texts"][0]["font"]["sha256"], originals[Path(self.font_path)])
        self.assertEqual(report["reproducibility"]["config"]["sha256"], originals[self.config])
        second = composition.compose(self.config, self.root / "second")
        self.assertEqual(second["artifact"]["sha256"], report["artifact"]["sha256"])
        validator_spec = importlib.util.spec_from_file_location("delivery_validation", SCRIPT.with_name("validate_delivery.py"))
        validator = importlib.util.module_from_spec(validator_spec)
        validator_spec.loader.exec_module(validator)
        delivery = json.loads((self.output / "delivery.json").read_text(encoding="utf-8"))
        self.assertEqual(validator.validate(delivery, self.output), [])

    def test_chinese_and_long_english_real_font(self):
        text = "输入资料字段匹配输出结果\nSupercalifragilisticexpialidocious123!"
        self.data["blocks"][0].update(text=text, box=[40, 40, 220, 700], font_size=30)
        self.data["required_copy"][0]["text"] = text
        report = self.compose()
        entry = report["texts"][0]
        self.assertGreater(len(entry["lines"]), 2)
        self.assertEqual(entry["font_size"], 30)
        reconstructed = "".join(line + ("\n" if kind == "explicit" else "") for line, kind in zip(entry["lines"], entry["line_breaks"]))
        self.assertEqual(reconstructed, text)
        self.assertTrue(all(b[0] >= 40 and b[1] >= 40 and b[2] <= 260 and b[3] <= 740 for b in entry["glyph_boxes"]))

    def test_text_overflow_no_render_no_shrink(self):
        self.data["blocks"][0].update(box=[40, 40, 30, 20])
        self.assert_blocked("text_overflow")
        self.assertEqual(self.data["blocks"][0]["font_size"], 40)
        self.assertEqual(self.data["blocks"][0]["text"], "Hello 123!")

    def test_missing_unicode_glyph_blocks_render(self):
        self.data["blocks"][0]["text"] += "\U0010ffff"
        self.assert_blocked("missing_glyph")

    def test_missing_font_blocks_render(self):
        self.brand["fonts"]["body"]["path"] = "missing.ttf"
        self.assert_blocked("invalid_font")

    def test_corrupt_font_blocks_render(self):
        (self.root / "broken.ttf").write_bytes(b"not a font")
        self.brand["fonts"]["body"]["path"] = "broken.ttf"
        self.assert_blocked("invalid_font")

    def test_corrupt_image_blocks_render(self):
        source = self.add_image()
        source.write_bytes(b"not an image")
        self.assert_blocked("invalid_image")

    def test_mobile_small_font_still_outputs_draft(self):
        self.data["blocks"][0]["font_size"] = 12
        report = self.compose()
        self.assertEqual(report["checks"]["readability"]["status"], "fail")
        self.assertAlmostEqual(report["texts"][0]["mobile_font_px"], 7.8)
        item = json.loads((self.output / "delivery.json").read_text(encoding="utf-8"))["items"][0]
        self.assertEqual(item["status"], "draft")
        self.assertEqual(item["checks"]["readability"]["status"], "fail")
        self.assertTrue((self.output / "poster.png").is_file())

    def test_zoom_is_unverified(self):
        self.data["reading"]["mode"] = "zoom"
        report = self.compose()
        self.assertEqual(report["checks"]["readability"]["status"], "unverified")
        self.assertIn("zoom_readability_unverified", [issue["code"] for issue in report["issues"]])

    def test_64px_upscale_is_unverified(self):
        self.add_image()
        report = self.compose()
        asset = report["assets"][0]
        self.assertEqual((asset["source_width"], asset["source_height"]), (64, 64))
        self.assertEqual((asset["placed_width"], asset["placed_height"]), (256, 256))
        self.assertEqual(asset["scale"], 4)
        self.assertTrue(asset["upscale"])
        self.assertEqual(report["checks"]["assets"]["status"], "unverified")

    def test_exif_orientation_is_applied(self):
        source = self.root / "oriented.jpg"
        exif = self.Image.Exif()
        exif[274] = 6
        self.Image.new("RGB", (120, 60), "blue").save(source, exif=exif)
        before = composition.sha256(source)
        self.data["blocks"].append({"id": "photo", "type": "image", "path": "oriented.jpg", "role": "illustration", "fit": "contain", "box": [40, 220, 120, 120]})
        report = self.compose()
        asset = report["assets"][0]
        self.assertEqual((asset["source_width"], asset["source_height"]), (60, 120))
        self.assertEqual((asset["placed_width"], asset["placed_height"]), (60, 120))
        self.assertEqual(composition.sha256(source), before)

    def test_ttc_font_index(self):
        ttLib = self.dependencies[5]
        with ttLib.TTFont(self.font_path, fontNumber=self.font_index) as font:
            collection = ttLib.TTCollection()
            collection.fonts = [font, font]
            collection.save(str(self.root / "test.ttc"))
        self.brand["fonts"]["body"].update(path="test.ttc", index=1)
        report = self.compose()
        self.assertEqual(report["texts"][0]["font"]["index"], 1)

    def test_font_paths_relative_to_brand_json(self):
        nested = self.root / "brand"
        nested.mkdir()
        # 使用相对路径指向测试根目录内的字体副本，避免跨盘相对路径。
        font_copy = self.root / "font.bin"
        font_copy.write_bytes(Path(self.font_path).read_bytes())
        for value in self.brand["fonts"].values():
            value["path"] = "../font.bin"
        self.data["brand"] = "brand/brand.json"
        self.write_inputs()
        (nested / "brand.json").write_text(json.dumps(self.brand), encoding="utf-8")
        report = composition.compose(self.config, self.output)
        self.assertEqual(report["texts"][0]["font"]["path"], str(font_copy.resolve()))

    def test_cli_success_exit_zero_means_only_draft(self):
        self.write_inputs()
        self.assertEqual(composition.main([str(self.config), "--output-dir", str(self.output)]), 0)
        self.assertEqual(composition.main([str(self.config), "--output-dir", str(self.output)]), 1)


if __name__ == "__main__":
    unittest.main()
