"""Regression tests for direction comparison and logo analysis."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_logo
import check_html_poster as checker


def make_image(path, background, accent, blocks):
    from PIL import Image, ImageDraw
    image = Image.new("RGB", (400, 566), background)
    draw = ImageDraw.Draw(image)
    for index, (x, y, w, h) in enumerate(blocks):
        draw.rectangle([x, y, x + w, y + h], fill=accent)
    image.save(path)


class CompareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_same_image_is_reuse(self):
        path = self.base / "a.png"
        make_image(path, "#F4F1E8", "#1F3A5F", [(20, 20, 360, 40)])
        result = checker.compare_posters(path, path)
        self.assertEqual(result["verdict"], "reuse")
        self.assertGreater(result["similarity"], 0.98)

    def test_different_layout_is_distinct(self):
        first = self.base / "first.png"
        second = self.base / "second.png"
        make_image(first, "#1F3A5F", "#FFFFFF", [(20, 20, 360, 80)])
        make_image(second, "#FFFFFF", "#0060A0",
                   [(40, 60, 120, 10), (40, 90, 120, 10), (40, 120, 120, 10)])
        result = checker.compare_posters(second, first)
        self.assertEqual(result["verdict"], "distinct")
        self.assertLess(result["similarity"], 0.72)


class LogoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.logo = Path(self.temp.name) / "logo.png"
        from PIL import Image
        image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        for x in range(12, 52):
            for y in range(12, 52):
                image.putpixel((x, y), (0, 96, 160, 255))
        image.save(self.logo)

    def tearDown(self):
        self.temp.cleanup()

    def test_transparency_and_color(self):
        report = analyze_logo.inspect(self.logo, 44, "light")
        self.assertTrue(report["transparency"]["has_alpha"])
        self.assertEqual(report["color"]["dominant"], "#0060A0")
        self.assertEqual(report["display"]["scale"], 0.688)

    def test_dark_background_suggests_container(self):
        report = analyze_logo.inspect(self.logo, 44, "dark")
        self.assertTrue(report["suggestions"]["white_container"])

    def test_oversized_display_warns(self):
        report = analyze_logo.inspect(self.logo, 120, "light")
        self.assertTrue(any("1.5 倍" in warning for warning in report["warnings"]))
        self.assertEqual(analyze_logo.main([str(self.logo), "--display-size", "120"]), 1)


if __name__ == "__main__":
    unittest.main()
