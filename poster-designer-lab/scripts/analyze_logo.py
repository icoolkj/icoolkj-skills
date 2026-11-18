#!/usr/bin/env python3
"""Inspect a logo before layout: size, transparency, dominant color, safe display size.

Requires Pillow. Exit code 1 when the requested display size exceeds 1.5x the
source, or when a dark background needs a white container.
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

SKILL_VERSION = "1.3.0"


def quantize(value, step=8):
    return (value // step) * step


def saturation(rgb):
    high = max(rgb)
    low = min(rgb)
    return 0.0 if high == 0 else (high - low) / high


def inspect(path, display_size, background):
    try:
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("需要 Pillow：python -m pip install 'Pillow>=10.4,<13'") from exc

    image = Image.open(path)
    mode = image.mode
    image = image.convert("RGBA")
    width, height = image.size
    pixels = list(image.getdata())
    alpha = [p[3] for p in pixels]
    transparent = sum(1 for a in alpha if a < 16) / len(alpha)
    opaque = [(r, g, b) for r, g, b, a in pixels if a > 180]
    quantized = Counter((quantize(r), quantize(g), quantize(b)) for r, g, b in opaque)
    non_white = [(c, n) for c, n in quantized.items() if not (c[0] > 235 and c[1] > 235 and c[2] > 235)]
    dominant = max(non_white, key=lambda item: item[1])[0] if non_white else (31, 41, 51)
    dominant_ratio = dict(non_white).get(dominant, 0) / max(1, len(opaque))
    color_ratio = sum(saturation(c) >= 0.25 for c in opaque) / max(1, len(opaque))

    warnings = []
    if display_size > max(width, height):
        warnings.append("显示尺寸大于源尺寸，需记录放大倍率并标记清晰度 unverified")
    if display_size > max(width, height) * 1.5:
        warnings.append("显示尺寸超过源尺寸 1.5 倍，禁止作为严格原版 Logo 使用")
    if background == "dark" and transparent > 0.5:
        warnings.append("透明 Logo 放在深色背景上会丢失对比，建议加白底容器")
    if transparent < 0.05:
        warnings.append("Logo 无透明通道，深色或彩色背景上可能带底色方块")
    if len(opaque) == 0:
        warnings.append("未检测到不透明像素，检查文件是否损坏")

    return {
        "schema_version": 1,
        "skill_version": SKILL_VERSION,
        "file": str(Path(path).resolve()),
        "source": {"width": width, "height": height, "mode": mode,
                   "aspect": round(width / height, 3)},
        "transparency": {"transparent_pixel_ratio": round(transparent, 3),
                         "has_alpha": transparent > 0.01},
        "color": {"dominant": "#%02X%02X%02X" % dominant,
                  "dominant_ratio": round(dominant_ratio, 3),
                  "colored_pixel_ratio": round(color_ratio, 3)},
        "display": {"requested_px": display_size,
                    "safe_max_px": max(width, height),
                    "scale": round(display_size / max(width, height), 3),
                    "background": background},
        "suggestions": {
            "white_container": bool(background == "dark" and transparent > 0.5),
            "display_px": min(display_size, max(width, height)),
            "note": "优先使用矢量原稿或 >=512px PNG；不要用 AI 重绘替代原版 Logo",
        },
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logo", help="Logo 文件（PNG/JPEG）")
    parser.add_argument("--display-size", type=int, default=44, help="计划显示边长，默认 44")
    parser.add_argument("--background", choices=("light", "dark"), default="light",
                        help="Logo 将放在浅色还是深色背景上")
    args = parser.parse_args(argv)

    report = inspect(args.logo, args.display_size, args.background)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    blocking = [w for w in report["warnings"] if "1.5 倍" in w or "未检测到" in w]
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())