#!/usr/bin/env python3
"""Check an HTML poster before delivery. Python 3.9+, standard library only.

Static checks always run. With --render, Playwright measures overflow and font
state in a real browser; with --export, the export button is actually clicked
and the downloaded PNG is measured. Machine checks never replace visual review.
"""
import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys
import time
from pathlib import Path

SKILL_VERSION = "1.3.0"
FORMAT = "PNG"
SIZES = {
    "A4": (794, 1123),
    "A3": (1123, 1587),
    "3:4": (1080, 1440),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def png_size(path):
    with Path(path).open("rb") as stream:
        head = stream.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR" or len(head) != 24:
        raise ValueError("not a PNG file")
    width, height = struct.unpack(">II", head[16:24])
    if width <= 0 or height <= 0:
        raise ValueError("invalid PNG dimensions")
    return width, height


def result(name, status, evidence):
    return {"id": name, "status": status, "evidence": evidence}


def strip_comments(html):
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    return re.sub(r"/\*.*?\*/", "", html, flags=re.S)


def canvas_size(html, expected):
    match = re.search(r'data-canvas\s*=\s*["\'](\d+)\s*[xX]\s*(\d+)["\']', html)
    if match:
        return int(match.group(1)), int(match.group(2)), "data-canvas"
    block = None
    for candidate in re.findall(r"\.poster\s*\{([^}]*)\}", html, flags=re.S):
        if re.search(r"\bwidth\s*:", candidate) and re.search(r"\bheight\s*:", candidate):
            block = candidate
            break
    if block:
        width = re.search(r"\bwidth\s*:\s*(\d+)px", block)
        height = re.search(r"\bheight\s*:\s*(\d+)px", block)
        if width and height:
            return int(width.group(1)), int(height.group(1)), ".poster 规则"
    if expected in SIZES:
        return SIZES[expected][0], SIZES[expected][1], "期望值（HTML 未声明）"
    return 0, 0, "未声明"


def static_checks(html, expected, scale):
    checks = []
    width, height, source = canvas_size(html, expected)
    if expected in SIZES and (width, height) != SIZES[expected]:
        checks.append(result("canvas", "fail",
                             f"画布 {width}x{height} 与期望 {expected} {SIZES[expected]} 不符（来源：{source}）"))
    elif width <= 0 or height <= 0:
        checks.append(result("canvas", "fail", "未找到固定画布尺寸，需声明 data-canvas 或 .poster 宽高"))
    else:
        checks.append(result("canvas", "pass", f"画布 {width}x{height}（来源：{source}），导出 {scale}x"))

    has_export = bool(re.search(r"id\s*=\s*[\"']exportBtn[\"']", html)) or bool(
        re.search(r"<button[^>]*>[^<]*导出[^<]*</button>", html))
    checks.append(result("export_button", "pass" if has_export else "fail",
                         "找到导出按钮" if has_export else "未找到导出按钮（id=exportBtn 或含“导出”文本）"))

    lib = re.search(r"html-to-image@(\d+)\.(\d+)\.(\d+)", html)
    banned = "html2canvas" in html
    if lib:
        version = tuple(int(v) for v in lib.groups())
        ok = version >= (1, 11, 0) and not banned
        checks.append(result("export_library", "pass" if ok else "fail",
                             f"html-to-image {'.'.join(lib.groups())}" + ("；禁止 html2canvas" if banned else "")))
    else:
        checks.append(result("export_library", "fail",
                             "未引入 html-to-image@1.11.x" + ("；且使用了 html2canvas" if banned else "")))

    ratio = re.search(r"pixelRatio\s*:\s*(\d+)", html)
    if not ratio:
        checks.append(result("export_scale", "fail", "未设置 pixelRatio"))
    elif int(ratio.group(1)) != scale:
        checks.append(result("export_scale", "fail",
                             f"pixelRatio {ratio.group(1)} 与本图目标 {scale}x 不一致"))
    else:
        checks.append(result("export_scale", "pass", f"pixelRatio {scale}"))

    fonts_ready = "document.fonts" in html and "fonts.ready" in html
    checks.append(result("font_wait", "pass" if fonts_ready else "fail",
                         "导出前等待 document.fonts.ready" if fonts_ready else "导出前未等待字体加载"))

    forbidden = [
        (r"background-clip\s*:\s*text", "background-clip:text"),
        (r"-webkit-text-fill-color\s*:\s*transparent", "-webkit-text-fill-color:transparent"),
        (r"backdrop-filter\s*:", "backdrop-filter"),
        (r"mix-blend-mode\s*:", "mix-blend-mode"),
    ]
    hits = [name for pattern, name in forbidden if re.search(pattern, html, flags=re.I)]
    checks.append(result("css_compat", "fail" if hits else "pass",
                         ("导出不兼容属性：" + "、".join(hits)) if hits else "未使用已知导出不兼容属性"))

    sticky = re.search(r"position\s*:\s*sticky", html, flags=re.I)
    if sticky:
        checks.append(result("css_sticky", "unverified", "使用了 position:sticky，导出时可能退化为静态"))

    defined = set(re.findall(r"(--[\w-]+)\s*:", html))
    missing = set()
    for name, fallback in re.findall(r"var\(\s*(--[\w-]+)\s*(,)?", html):
        if name not in defined:
            missing.add(name + ("（有回退值）" if fallback else "（无回退值）"))
    hard_missing = [name for name in missing if "有回退值" not in name]
    if hard_missing:
        checks.append(result("css_vars", "fail", "未定义的 CSS 变量：" + "、".join(sorted(hard_missing))))
    elif missing:
        checks.append(result("css_vars", "pass", "变量均有回退值：" + "、".join(sorted(missing))))
    else:
        checks.append(result("css_vars", "pass", "所有 var() 均在当前文件有定义或回退"))

    leftovers = re.findall(r"__[A-Z0-9_]{3,}__|CONFIGURE-YOUR", html)
    checks.append(result("placeholders", "fail" if leftovers else "pass",
                         ("存在未替换占位符：" + "、".join(sorted(set(leftovers)))) if leftovers else "无未替换占位符"))

    font_ok = re.search(r"Noto Sans|Noto Serif|Source Han|PingFang|Microsoft YaHei|WenQuanYi|SimSun|Songti", html)
    checks.append(result("font_stack", "pass" if font_ok else "fail",
                         "字体栈含中文可用字体" if font_ok else "字体栈未声明中文回退字体"))

    print_css = re.search(r"@media\s+print", html)
    checks.append(result("print_style", "pass" if print_css else "unverified",
                         "含 @media print 规则" if print_css else "无打印样式；打印时按钮可能入版"))

    sources = re.findall(r"<img[^>]+src\s*=\s*[\"']([^\"']+)[\"']", html)
    bad = [src[:40] for src in sources if not src.startswith("data:")]
    if bad:
        checks.append(result("embedded_images", "fail",
                             "图片未内嵌（导出可能丢失）：" + "、".join(bad)))
    else:
        checks.append(result("embedded_images", "pass",
                             f"{len(sources)} 张栅格图均以 data: 内嵌" if sources else "无外部栅格图"))
    return checks, width, height


def image_features(path):
    """Coarse visual fingerprint: color histogram, row density, dark and edge ratios."""
    from PIL import Image

    image = Image.open(path).convert("RGB").resize((200, 283), Image.LANCZOS)
    pixels = list(image.getdata())
    width, height = image.size

    histogram = [0] * 64
    dark = 0
    for r, g, b in pixels:
        histogram[(r // 64) * 16 + (g // 64) * 4 + (b // 64)] += 1
        if (r + g + b) / 3 < 90:
            dark += 1
    total = float(len(pixels))
    histogram = [value / total for value in histogram]

    background = image.getpixel((2, 2))
    rows = [0.0] * 24
    dark_rows = [0.0] * 24
    edges = 0
    for y in range(1, height):
        start = y * width
        filled = 0
        dark_pixels = 0
        for x in range(width):
            r, g, b = pixels[start + x]
            if max(abs(r - background[0]), abs(g - background[1]), abs(b - background[2])) > 18:
                filled += 1
            if (r + g + b) / 3 < 90:
                dark_pixels += 1
            if x:
                pr, pg, pb = pixels[start + x - 1]
                if abs(r - pr) + abs(g - pg) + abs(b - pb) > 48:
                    edges += 1
        bucket = min(23, y * 24 // height)
        rows[bucket] += filled / float(width)
        dark_rows[bucket] += dark_pixels / float(width)
    rows = [value / (height / 24.0) for value in rows]
    dark_rows = [value / (height / 24.0) for value in dark_rows]
    return {
        "histogram": histogram,
        "rows": rows,
        "dark_rows": dark_rows,
        "dark": dark / total,
        "edge": edges / float((width - 1) * (height - 1)),
    }


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return 0.0 if not na or not nb else dot / (na * nb)


def compare_posters(current, baseline):
    from PIL import Image

    for path in (current, baseline):
        if not Path(path).exists():
            raise ValueError("对比文件不存在：" + str(path))
    now = image_features(current)
    old = image_features(baseline)
    similarity = (0.25 * cosine(now["histogram"], old["histogram"])
                  + 0.30 * cosine(now["rows"], old["rows"])
                  + 0.25 * cosine(now["dark_rows"], old["dark_rows"])
                  + 0.10 * (1 - abs(now["dark"] - old["dark"]))
                  + 0.10 * (1 - abs(now["edge"] - old["edge"])))
    verdict = "reuse" if similarity >= 0.86 else "related" if similarity >= 0.72 else "distinct"
    return {
        "current": str(Path(current).resolve()),
        "baseline": str(Path(baseline).resolve()),
        "similarity": round(similarity, 3),
        "verdict": verdict,
        "metrics": {
            "histogram_similarity": round(cosine(now["histogram"], old["histogram"]), 3),
            "row_similarity": round(cosine(now["rows"], old["rows"]), 3),
            "dark_row_similarity": round(cosine(now["dark_rows"], old["dark_rows"]), 3),
            "dark_ratio": [round(old["dark"], 3), round(now["dark"], 3)],
            "edge_ratio": [round(old["edge"], 3), round(now["edge"], 3)],
        },
    }


def primary_font(family):
    for name in (family or "").split(","):
        name = name.strip().strip("\"'")
        if name and name.lower() not in ("serif", "sans-serif", "monospace", "cursive"):
            return name
    return ""


def render_checks(html_path, button_text, preview, export_path, canvas, scale):
    """Return (browser results, exported png path or None, notes)."""
    results, notes = [], []
    exported = None
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        notes.append("未安装 Playwright，跳过渲染与导出实测")
        return results, None, notes

    executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if not executable:
        roots = [Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "") or "/nonexistent"),
                 Path.home() / ".cache" / "ms-playwright", Path("/ms-playwright")]
        patterns = ("chromium-*/chrome-linux/chrome", "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
                    "chromium-*/chrome-win/chrome.exe")
        for root in roots:
            if not root.exists():
                continue
            matches = []
            for pattern in patterns:
                matches.extend(sorted(root.glob(pattern)))
            if matches:
                executable = str(matches[0])
                break

    with sync_playwright() as runtime:
        try:
            options = {"args": ["--no-sandbox"]}
            if executable:
                options["executable_path"] = executable
            browser = runtime.chromium.launch(**options)
        except Exception as exc:
            notes.append("启动浏览器失败：" + str(exc)[:160])
            return results, None, notes
        page = browser.new_page(viewport={"width": max(canvas[0] + 220, 1000),
                                          "height": max(canvas[1] + 200, 1200)},
                                device_scale_factor=1)
        page.goto(Path(html_path).resolve().as_uri())
        page.evaluate("document.fonts && document.fonts.ready")
        page.wait_for_timeout(400)

        info = page.evaluate("""() => {
          const poster = document.querySelector('.poster');
          if (!poster) return {missing: true};
          const pr = poster.getBoundingClientRect();
          const overflow = [];
          poster.querySelectorAll('*').forEach(el => {
            const r = el.getBoundingClientRect();
            if (!r.width && !r.height) return;
            if (r.right > pr.right + 1 || r.bottom > pr.bottom + 1 || r.left < pr.left - 1 || r.top < pr.top - 1) {
              overflow.push((el.tagName || '') + '.' + ((el.className || '').toString().slice(0, 28))
                            + ' bottom=' + Math.round(r.bottom - pr.top));
            }
          });
          const btn = document.getElementById('exportBtn');
          let overlap = 0;
          if (btn) {
            const br = btn.getBoundingClientRect();
            const w = Math.min(br.right, pr.right) - Math.max(br.left, pr.left);
            const h = Math.min(br.bottom, pr.bottom) - Math.max(br.top, pr.top);
            overlap = (w > 0 && h > 0) ? Math.round(w * h) : 0;
          }
          return {
            missing: false, overflow: overflow.slice(0, 8), overflowCount: overflow.length,
            scrollH: poster.scrollHeight, clientH: poster.clientHeight,
            buttonOverlap: overlap, button: !!btn,
            fontStatus: document.fonts ? document.fonts.status : 'unknown',
            titleFont: getComputedStyle(document.querySelector('h1') || poster).fontFamily,
            bodyFont: getComputedStyle(document.querySelector('.lead, p') || poster).fontFamily,
            fontChecks: (() => {
              const names = ['Noto Serif CJK SC', 'Noto Sans CJK SC', 'Microsoft YaHei',
                             'PingFang SC', 'SimSun', 'Songti SC', 'Source Han Sans SC'];
              const out = {};
              names.forEach(n => { out[n] = document.fonts ? document.fonts.check('16px "' + n + '"') : false; });
              return out;
            })(),
            size: {w: Math.round(pr.width), h: Math.round(pr.height)}
          };
        }""")
        if info.get("missing"):
            results.append(result("render_dom", "fail", "页面中找不到 .poster 容器"))
        else:
            results.append(result("render_dom", "pass",
                                  f".poster 实测 {info['size']['w']}x{info['size']['h']}"))
            results.append(result("render_overflow", "fail" if info["overflowCount"] else "pass",
                                  ("越界元素：" + "；".join(info["overflow"])) if info["overflowCount"]
                                  else "无元素越出画布"))
            results.append(result("render_no_scroll", "pass" if info["scrollH"] == info["clientH"] else "fail",
                                  f"scrollHeight={info['scrollH']} clientHeight={info['clientH']}"))
            results.append(result("render_button_clear", "pass" if info["buttonOverlap"] == 0 else "fail",
                                  "导出按钮不遮挡版心" if info["buttonOverlap"] == 0
                                  else f"按钮与版心重叠 {info['buttonOverlap']}px²"))
            results.append(result("render_font", "pass" if info["fontStatus"] == "loaded" else "fail",
                                  "字体状态：" + str(info["fontStatus"])))
            availability = info.get("fontChecks", {})
            title_font = primary_font(info.get("titleFont", ""))
            body_font = primary_font(info.get("bodyFont", ""))
            missing = [name for name in (title_font, body_font)
                       if name and availability.get(name) is False]
            if missing:
                results.append(result("render_font_actual", "fail",
                                      "首选字体未加载，导出会回退：" + "、".join(sorted(set(missing)))
                                      + "；可用字体：" + "、".join(k for k, v in availability.items() if v)))
            else:
                results.append(result("render_font_actual", "pass",
                                      "标题实际字体：" + (title_font or "未知")
                                      + "；正文实际字体：" + (body_font or "未知")))

        if preview:
            try:
                target = Path(preview)
                target.parent.mkdir(parents=True, exist_ok=True)
                page.locator(".poster").screenshot(path=str(target))
                try:
                    from PIL import Image
                    image = Image.open(target)
                    if image.width > 390:
                        height = max(1, round(image.height * 390 / image.width))
                        image.resize((390, height), Image.LANCZOS).save(target)
                        notes.append("已生成 390px 预览：" + target.name)
                    else:
                        notes.append("已生成预览：" + target.name)
                except ImportError:
                    notes.append("预览未缩放到 390px（未安装 Pillow）：" + target.name)
            except Exception as exc:
                notes.append("预览生成失败：" + str(exc)[:120])

        if export_path:
            try:
                with page.expect_download(timeout=45000) as pending:
                    page.locator("#exportBtn").click(timeout=15000)
                out = Path(export_path)
                out.parent.mkdir(parents=True, exist_ok=True)
                pending.value.save_as(str(out))
                time.sleep(0.1)
                exported = str(out)
                notes.append("已实测导出：" + out.name)
            except Exception as exc:
                notes.append("导出实测失败：" + str(exc)[:160])
        browser.close()
    return results, exported, notes


def build_report(args, checks, width, height, exported, notes, comparison):
    check_map = {item["id"]: item for item in checks}
    layout_fail = any(item["status"] == "fail" and item["id"] in {
        "canvas", "render_dom", "render_overflow", "render_no_scroll", "render_button_clear"}
        for item in checks)
    layout_evidence = "；".join(item["evidence"] for item in checks
                               if item["id"] in {"canvas", "render_overflow", "render_no_scroll"}) or "未执行布局检查"

    export_fields = ["export_button", "export_library", "export_scale", "exported_size"]
    export_fail = any(item["status"] == "fail" and item["id"] in set(export_fields) | {"font_wait"}
                      for item in checks)
    if exported:
        export_status = "fail" if export_fail else "pass"
        export_evidence = "实测导出 " + Path(exported).name
    else:
        export_status = "fail" if export_fail else "unverified"
        export_evidence = "未执行导出实测" if not export_fail else "导出静态检查失败"

    def locate(value):
        path = Path(value).resolve()
        if args.report:
            try:
                return str(path.relative_to(Path(args.report).resolve().parent))
            except ValueError:
                return str(path)
        return str(path)

    artifact = None
    actual = None
    if exported:
        art_w, art_h = png_size(exported)
        artifact = {
            "location": locate(exported),
            "sha256": sha256(exported),
            "width": art_w,
            "height": art_h,
            "format": FORMAT,
        }
        actual = (art_w, art_h)

    preview_entry = None
    if args.preview and Path(args.preview).exists():
        try:
            prev_w, prev_h = png_size(args.preview)
            preview_entry = {
                "location": locate(args.preview),
                "sha256": sha256(args.preview),
                "width": prev_w,
                "height": prev_h,
            }
        except ValueError as exc:
            notes.append("预览尺寸读取失败：" + str(exc))

    if comparison:
        blocked = comparison["verdict"] == "reuse" and not getattr(args, "allow_reuse", False)
        direction_check = {
            "status": "fail" if blocked else "pass",
            "evidence": "与基线相似度 %.3f，判定 %s%s" % (
                comparison["similarity"], comparison["verdict"],
                "；已用 --allow-reuse 人工放行" if comparison["verdict"] == "reuse" and not blocked else ""),
        }
    else:
        direction_check = {"status": "unverified", "evidence": "未提供上一版基线，未检查版式重复"}

    report = {
        "schema_version": 1,
        "skill_version": SKILL_VERSION,
        "method": "html_render",
        "canvas": {"width": width, "height": height, "expected": args.expect_size,
                   "export_scale": args.export_scale},
        "artifact": artifact,
        "preview": preview_entry,
        "reproducibility": {
            "config": {
                "location": locate(args.html),
                "sha256": sha256(args.html),
            }
        },
        "checks": {
            "layout": {
                "status": "fail" if layout_fail else "pass",
                "evidence": layout_evidence,
            },
            "html_export": {"status": export_status, "evidence": export_evidence},
            "readability": {"status": "unverified",
                            "evidence": "需按 390 px 预览人工核对小字，脚本不判断可读性"},
            "assets": {"status": "unverified",
                       "evidence": "需人工核对 Logo 源尺寸、显示倍率与导出清晰度"},
            "direction": direction_check,
        },
        "details": checks,
        "notes": notes,
    }
    if artifact and actual:
        report["actual"] = {"width": actual[0], "height": actual[1], "format": FORMAT}
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", help="poster HTML 文件")
    parser.add_argument("--expect-size", default="",
                        help="期望尺寸：A4/A3/3:4/9:16/16:9 或 WxH")
    parser.add_argument("--export-scale", type=int, default=3, help="导出倍率，默认 3")
    parser.add_argument("--png", help="已导出 PNG，用于尺寸校验（未执行导出时）")
    parser.add_argument("--render", action="store_true", help="用 Playwright 渲染并检查越界")
    parser.add_argument("--export", help="点击导出按钮并保存到该路径（隐含 --render）")
    parser.add_argument("--preview", help="保存画布预览 PNG（隐含 --render）")
    parser.add_argument("--report", help="写出 layout-report.json")
    parser.add_argument("--compare", help="上一版 PNG，用于检查版式重复")
    parser.add_argument("--compare-report", help="写出 compare-report.json")
    parser.add_argument("--allow-reuse", action="store_true",
                        help="人工确认允许沿用上一版版式")
    args = parser.parse_args(argv)

    html_path = Path(args.html)
    try:
        html = strip_comments(html_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError) as exc:
        print(json.dumps({"record_valid": False, "errors": [str(exc)]}, ensure_ascii=False))
        return 1

    expected = args.expect_size.strip()
    custom = re.fullmatch(r"(\d+)x(\d+)", expected, flags=re.I)
    expected_label = expected
    expected_size = None
    if custom:
        expected_size = (int(custom.group(1)), int(custom.group(2)))
    elif expected in SIZES:
        expected_size = SIZES[expected]

    checks, width, height = static_checks(html, expected, args.export_scale)
    if expected_size and (width, height) != expected_size:
        checks[0] = result("canvas", "fail",
                           f"画布 {width}x{height} 与期望 {expected_size[0]}x{expected_size[1]} 不符")

    exported = None
    notes = []
    if args.render or args.export or args.preview:
        rendered, exported, notes = render_checks(
            html_path, "导出", args.preview, args.export, (width, height), args.export_scale)
        checks.extend(rendered)

    if exported:
        try:
            png_w, png_h = png_size(exported)
            want = (width * args.export_scale, height * args.export_scale)
            checks.append(result("exported_size", "pass" if (png_w, png_h) == want else "fail",
                                 f"导出图 {png_w}x{png_h}，期望 {want[0]}x{want[1]}"))
        except ValueError as exc:
            checks.append(result("exported_size", "fail", str(exc)))
    elif args.png:
        try:
            png_w, png_h = png_size(args.png)
            want = (width * args.export_scale, height * args.export_scale)
            checks.append(result("exported_size", "pass" if (png_w, png_h) == want else "fail",
                                 f"{args.png} 尺寸 {png_w}x{png_h}，期望 {want[0]}x{want[1]}"))
        except (OSError, ValueError) as exc:
            checks.append(result("exported_size", "fail", f"{args.png}: {exc}"))
    else:
        checks.append(result("exported_size", "unverified", "未提供导出 PNG"))

    comparison = None
    if args.compare:
        current_image = exported or args.png
        if not current_image:
            checks.append(result("direction", "fail",
                                 "--compare 需要 --export 或 --png 提供当前导出图"))
        else:
            try:
                comparison = compare_posters(current_image, args.compare)
                if args.compare_report:
                    target = Path(args.compare_report)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(json.dumps(comparison, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
            except (OSError, ValueError) as exc:
                checks.append(result("direction", "fail", "对比失败：" + str(exc)))

    report = build_report(args, checks, width, height, exported, notes, comparison)
    if args.report:
        target = Path(args.report)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    failed = [item for item in checks if item["status"] == "fail" and item["id"] != "direction"]
    reuse_blocked = bool(comparison and comparison["verdict"] == "reuse" and not args.allow_reuse)
    direction_failed = report["checks"]["direction"]["status"] == "fail"
    output = {
        "record_valid": not failed and not reuse_blocked and not direction_failed,
        "visual_approval": False,
        "canvas": report["canvas"],
        "checks": report["checks"],
        "failed": [item["id"] + ": " + item["evidence"] for item in failed],
        "comparison": comparison,
        "details": checks,
        "notes": notes,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if reuse_blocked:
        return 2
    return 1 if (failed or direction_failed) else 0


if __name__ == "__main__":
    sys.exit(main())