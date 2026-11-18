"""确定性海报排版：先完整预检，再生成待人工看图的草稿。Python 3.9+。"""
import argparse
import hashlib
import importlib
import json
import math
import os
import re
import sys
from pathlib import Path

SKILL_VERSION = "1.1.2"
CHECKS = {"content", "visual", "dimensions", "access", "brand", "edit_scope", "qr", "rights", "print", "readability", "assets"}
APPLICABLE = {"content", "visual", "dimensions", "access", "brand", "readability", "assets"}


class CompositionError(ValueError):
    def __init__(self, code, message, block_id=None):
        super().__init__(message)
        self.code = code
        self.block_id = block_id

    def issue(self):
        return {"code": self.code, "block_id": self.block_id, "message": str(self)}


class DependencyError(RuntimeError):
    pass


def load_dependencies():
    try:
        pil = importlib.import_module("PIL")
        tools = importlib.import_module("fontTools")
        for name, version, lower, upper in (
            ("Pillow", pil.__version__, (10, 4), (13, 0)),
            ("fontTools", tools.__version__, (4, 55), (5, 0)),
        ):
            match = re.match(r"^(\d+)\.(\d+)", version)
            if not match or not lower <= tuple(map(int, match.groups())) < upper:
                raise ImportError("%s 版本不受支持：%s" % (name, version))
        return tuple(importlib.import_module(name) for name in (
            "PIL.Image", "PIL.ImageDraw", "PIL.ImageFont", "PIL.ImageOps", "PIL.ImageColor", "fontTools.ttLib"))
    except (ImportError, AttributeError) as exc:
        requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
        raise DependencyError('依赖缺失或版本不兼容（Pillow>=10.4,<13；fontTools>=4.55,<5）。请运行 python -m pip install -r "%s"。详情：%s' % (requirements, exc)) from exc


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition, code, message, block_id=None):
    if not condition:
        raise CompositionError(code, message, block_id)


def positive(value):
    return type(value) is int and value > 0


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def resolve_path(base, value):
    require(nonempty(value), "invalid_path", "文件路径必须为非空字符串")
    return (base / value).resolve()


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise CompositionError("invalid_json", "无法读取 JSON %s：%s" % (path, exc)) from exc
    require(isinstance(data, dict), "invalid_schema", "JSON 顶层必须为对象：%s" % path)
    return data


def overlaps(a, b):
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def validate_config(data, brand):
    """不加载图像或字体的结构、文案绑定和几何预检。"""
    require(isinstance(data, dict) and type(data.get("schema_version")) is int and data["schema_version"] == 1,
            "invalid_schema", "配置 schema_version 必须为 1")
    require(isinstance(brand, dict) and type(brand.get("schema_version")) is int and brand["schema_version"] == 1,
            "invalid_brand", "品牌 schema_version 必须为 1")
    require(nonempty(brand.get("id")), "invalid_brand", "品牌 id 必填")
    colors, fonts = brand.get("colors"), brand.get("fonts")
    require(isinstance(colors, dict) and all(nonempty(k) and nonempty(v) for k, v in colors.items()),
            "invalid_brand", "colors 必须为显式颜色 token 对象")
    require(isinstance(fonts, dict), "invalid_brand", "fonts 必须为对象")
    for name in ("title", "body"):
        font = fonts.get(name)
        require(isinstance(font, dict) and nonempty(font.get("path")) and type(font.get("index", 0)) is int and font.get("index", 0) >= 0,
                "invalid_font", "fonts.%s 必须配置实际字体 path 及非负整数 index" % name)
    canvas, reading = data.get("canvas"), data.get("reading")
    require(isinstance(canvas, dict) and positive(canvas.get("width")) and positive(canvas.get("height")),
            "invalid_canvas", "画布宽高必须为正整数")
    require(isinstance(canvas.get("background"), str) and canvas["background"] in colors,
            "unknown_color", "画布背景必须引用品牌颜色 token")
    require(isinstance(reading, dict) and reading.get("mode") in ("mobile", "zoom")
            and positive(reading.get("preview_width")) and reading["preview_width"] <= canvas["width"]
            and number(reading.get("min_font_px")) and reading["min_font_px"] > 0,
            "invalid_reading", "reading 需配置 mobile/zoom、正数 min_font_px 及不超过画布宽度的 preview_width")
    require(nonempty(data.get("prompt")), "invalid_prompt", "prompt 必须为实际设计说明或提示词")
    required = data.get("required_copy")
    require(isinstance(required, list), "invalid_copy", "required_copy 必须为数组")
    copy_by_id = {}
    for entry in required:
        require(isinstance(entry, dict) and all(nonempty(entry.get(k)) for k in ("id", "text", "source")),
                "invalid_copy", "每项必保留文案需要 id、text、source")
        require(entry["id"] not in copy_by_id, "duplicate_copy_id", "必保留文案 id 重复：%s" % entry["id"])
        copy_by_id[entry["id"]] = entry["text"]
    blocks = data.get("blocks")
    require(isinstance(blocks, list) and blocks, "invalid_blocks", "blocks 必须为非空数组")
    seen, bound, content = set(), set(), []
    for block in blocks:
        require(isinstance(block, dict) and nonempty(block.get("id")), "invalid_block", "每个块必须有唯一 id")
        ident = block["id"]
        require(ident not in seen, "duplicate_block_id", "块 id 重复", ident)
        seen.add(ident)
        kind, box = block.get("type"), block.get("box")
        require(kind in ("rect", "text", "image"), "invalid_type", "块类型必须为 rect/text/image", ident)
        require(isinstance(box, list) and len(box) == 4 and all(type(v) is int for v in box)
                and box[2] > 0 and box[3] > 0, "invalid_box", "box 必须为整数 [x,y,w,h]，宽高大于零", ident)
        x, y, width, height = box
        require(x >= 0 and y >= 0 and x + width <= canvas["width"] and y + height <= canvas["height"],
                "outside_canvas", "块超出画布边界", ident)
        if kind == "rect":
            require(isinstance(block.get("fill"), str) and block["fill"] in colors, "unknown_color", "fill 必须引用品牌 token", ident)
            radius = block.get("radius", 0)
            require(type(radius) is int and 0 <= radius <= min(width, height) / 2,
                    "invalid_radius", "radius 必须为不超过短边一半的非负整数", ident)
            require(not block.get("required_ids"), "invalid_copy_binding", "必保留文案只能绑定 text 块", ident)
        else:
            for other in content:
                require(not overlaps(box, other["box"]), "content_overlap", "内容块与 %s 重叠" % other["id"], ident)
            content.append(block)
        if kind == "text":
            value = block.get("text")
            require(nonempty(value), "invalid_text", "text 必须为非空原文", ident)
            require(not any((ord(ch) < 32 and ch != "\n") or ord(ch) == 127 for ch in value),
                    "unsupported_control", "文本仅支持 LF 换行，不支持其他控制字符", ident)
            require(isinstance(block.get("font"), str) and block["font"] in ("title", "body"),
                    "invalid_font", "font 必须为 title/body", ident)
            require(positive(block.get("font_size")), "invalid_font_size", "font_size 必须为正整数，组件不会缩小字号", ident)
            require(number(block.get("line_spacing", 1.25)) and block.get("line_spacing", 1.25) >= 1,
                    "invalid_line_spacing", "line_spacing 必须为不小于 1 的有限数值", ident)
            require(isinstance(block.get("color"), str) and block["color"] in colors,
                    "unknown_color", "color 必须引用品牌 token", ident)
            require(block.get("align", "left") in ("left", "center"), "invalid_align", "align 只支持 left/center", ident)
            ids = block.get("required_ids", [])
            require(isinstance(ids, list) and all(nonempty(v) for v in ids) and len(ids) == len(set(ids)),
                    "invalid_copy_binding", "required_ids 必须为无重复的字符串数组", ident)
            for rid in ids:
                require(rid in copy_by_id, "unknown_required_id", "未知必保留文案 id：%s" % rid, ident)
                require(copy_by_id[rid] in value, "required_copy_changed", "必保留原文未完整匹配：%s" % rid, ident)
                bound.add(rid)
        elif kind == "image":
            require(nonempty(block.get("path")), "invalid_image", "image path 必填", ident)
            require(block.get("role") in ("logo", "illustration", "product", "screenshot"), "invalid_role", "素材 role 无效", ident)
            require(block.get("fit") == "contain", "invalid_fit", "图片仅允许 contain 等比完整放置", ident)
            require(not block.get("required_ids"), "invalid_copy_binding", "必保留文案只能绑定 text 块", ident)
    require(bound == set(copy_by_id), "required_copy_unbound", "未绑定必保留文案：%s" % ", ".join(sorted(set(copy_by_id) - bound)))


def glyph_span(font, value):
    bbox = font.getbbox(value, anchor="ls")
    left = min(0, bbox[0])
    right = max(font.getlength(value), bbox[2])
    return right - left, bbox, left


def layout_text(text, font, font_size, box, spacing=1.25, align="left", block_id=None):
    """逐字符测量，保留原始字符和显式换行，不缩字、不省略。"""
    x, y, width, height = box
    lines, breaks = [], []
    paragraphs = text.split("\n")
    for pindex, paragraph in enumerate(paragraphs):
        current = ""
        for char in paragraph:
            candidate = current + char
            if glyph_span(font, candidate)[0] <= width:
                current = candidate
            else:
                require(bool(current), "text_overflow", "单个字符宽度超出容器，禁止缩字或裁切", block_id)
                lines.append(current)
                breaks.append("wrap")
                current = char
                require(glyph_span(font, current)[0] <= width, "text_overflow", "单个字符宽度超出容器，禁止缩字或裁切", block_id)
        lines.append(current)
        breaks.append("explicit" if pindex < len(paragraphs) - 1 else "end")
    step = math.ceil(font_size * spacing)
    measured = [glyph_span(font, line) for line in lines]
    top = min([0] + [i * step + m[1][1] for i, m in enumerate(measured)])
    bottom = max([0, (len(lines) - 1) * step] + [i * step + m[1][3] for i, m in enumerate(measured)])
    measured_height = max(font_size, bottom - top)
    require(measured_height <= height, "text_overflow", "文字所需高度 %s 超过容器 %s，禁止缩字、删除或裁切" % (measured_height, height), block_id)
    origins, glyph_boxes = [], []
    for i, (line_width, bbox, left) in enumerate(measured):
        dx = (width - line_width) / 2 if align == "center" else 0
        px, py = x + dx - left, y - top + i * step
        origins.append([px, py])
        glyph_boxes.append([px + bbox[0], py + bbox[1], px + bbox[2], py + bbox[3]])
    return {"lines": lines, "line_breaks": breaks, "draw_origins": origins, "glyph_boxes": glyph_boxes,
            "measured_height": measured_height, "line_step": step}


def contain_size(source_width, source_height, box_width, box_height):
    scale = min(box_width / source_width, box_height / source_height)
    return max(1, min(box_width, round(source_width * scale))), max(1, min(box_height, round(source_height * scale))), scale


def check_glyphs(cmap, text, block_id):
    missing = sorted({ord(ch) for ch in text if ch != "\n" and (ord(ch) not in cmap or cmap[ord(ch)] == ".notdef")})
    require(not missing, "missing_glyph", "配置字体缺少字符：%s" % ", ".join("U+%04X" % cp for cp in missing), block_id)


def load_font(spec, base, size, ImageFont, ttLib, block_id):
    path = resolve_path(base, spec["path"])
    index = spec.get("index", 0)
    try:
        with path.open("rb") as stream:
            collection = stream.read(4) == b"ttcf"
        require(collection or index == 0, "invalid_font_index", "单字体文件 index 必须为 0", block_id)
        with ttLib.TTFont(str(path), fontNumber=index, lazy=False) as parsed:
            cmap = parsed.getBestCmap()
            require(bool(cmap), "invalid_font", "字体没有可用 Unicode 字符映射", block_id)
        font = ImageFont.truetype(str(path), size=size, index=index, layout_engine=ImageFont.Layout.BASIC)
        evidence = {"path": str(path), "sha256": sha256(path), "index": index, "layout_engine": "BASIC"}
        return font, cmap, evidence
    except CompositionError:
        raise
    except Exception as exc:
        raise CompositionError("invalid_font", "无法读取配置字体 %s（index=%s）：%s" % (path, index, exc), block_id) from exc


def check(status, evidence):
    return {"status": status, "evidence": evidence}


def new_report():
    return {"schema_version": 1, "skill_version": SKILL_VERSION, "artifact": None, "preview": None, "brand_id": None,
            "checks": {"layout": check("fail", "尚未完成布局预检"), "readability": check("unverified", "尚未检查"),
                       "assets": check("unverified", "尚未检查")},
            "texts": [], "assets": [], "issues": [], "visual_approval": False, "reproducibility": {}}


def prepare(data, brand, config_path, brand_path, report, dependencies):
    Image, ImageDraw, ImageFont, ImageOps, ImageColor, ttLib = dependencies
    validate_config(data, brand)
    report["brand_id"] = brand["id"]
    try:
        colors = {key: ImageColor.getcolor(value, "RGBA") for key, value in brand["colors"].items()}
    except (ValueError, TypeError) as exc:
        raise CompositionError("invalid_color", "品牌颜色无法解析：%s" % exc) from exc
    reading = data["reading"]
    fonts, images, cache = {}, {}, {}
    for block in data["blocks"]:
        ident, kind = block["id"], block["type"]
        if kind == "text":
            key = (block["font"], block["font_size"])
            if key not in cache:
                cache[key] = load_font(brand["fonts"][block["font"]], brand_path.parent, block["font_size"], ImageFont, ttLib, ident)
            font, cmap, evidence = cache[key]
            check_glyphs(cmap, block["text"], ident)
            layout = layout_text(block["text"], font, block["font_size"], block["box"], block.get("line_spacing", 1.25), block.get("align", "left"), ident)
            mobile_px = block["font_size"] * reading["preview_width"] / data["canvas"]["width"]
            report["texts"].append(dict(layout, id=ident, text=block["text"], font_size=block["font_size"],
                                        mobile_font_px=mobile_px, box=block["box"], font=evidence,
                                        required_ids=block.get("required_ids", [])))
            fonts[ident] = font
            if reading["mode"] == "mobile" and mobile_px < reading["min_font_px"]:
                report["issues"].append({"code": "mobile_font_too_small", "block_id": ident,
                                         "message": "手机预览字号 %.3fpx 低于阈值 %spx；保留原字号输出草稿" % (mobile_px, reading["min_font_px"])})
        elif kind == "image":
            path = resolve_path(config_path.parent, block["path"])
            try:
                with Image.open(path) as original:
                    original.load()
                    original_size = list(original.size)
                    corrected = ImageOps.exif_transpose(original)
                    mode = "RGBA" if "A" in corrected.getbands() or "transparency" in corrected.info else "RGB"
                    image = corrected.convert(mode)
                source_hash = sha256(path)
            except Exception as exc:
                raise CompositionError("invalid_image", "无法解码图片 %s：%s" % (path, exc), ident) from exc
            width, height, scale = contain_size(image.width, image.height, block["box"][2], block["box"][3])
            x = block["box"][0] + (block["box"][2] - width) // 2
            y = block["box"][1] + (block["box"][3] - height) // 2
            report["assets"].append({"id": ident, "path": str(path), "sha256": source_hash, "role": block["role"], "fit": "contain",
                                      "original_size": original_size, "source_width": image.width, "source_height": image.height,
                                      "placed_width": width, "placed_height": height, "placed_box": [x, y, width, height],
                                      "box": block["box"], "scale": scale, "scale_x": width / image.width,
                                      "scale_y": height / image.height, "upscale": scale > 1,
                                      "status": "unverified" if scale > 1 else "pass", "exif_corrected": True})
            images[ident] = image
            if scale > 1:
                report["issues"].append({"code": "asset_upscaled", "block_id": ident, "message": "素材放大 %.4f 倍，清晰度需人工检查" % scale})
    report["checks"]["layout"] = check("pass", "全部内容块无交叠、无画布越界；原文字符覆盖、换行、字形边界和必保留文案绑定预检通过")
    if reading["mode"] == "zoom":
        report["checks"]["readability"] = check("unverified", "zoom 模式：手机可读性未验证，须人工检查最终实际图片与放大阅读效果")
        report["issues"].append({"code": "zoom_readability_unverified", "block_id": None, "message": "警告：zoom 模式需要最终人工看图"})
    else:
        failed = any(t["mobile_font_px"] < reading["min_font_px"] for t in report["texts"])
        report["checks"]["readability"] = check("fail" if failed else "pass", "按配置字号 × %s / %s 对比 %spx 阈值；此数值检查不代表视觉批准" % (reading["preview_width"], data["canvas"]["width"], reading["min_font_px"]))
    enlarged = any(asset["upscale"] for asset in report["assets"])
    report["checks"]["assets"] = check("unverified" if enlarged else "pass", "素材已完整解码、EXIF 校正并等比 contain；" + ("存在放大素材，倍率见 assets，清晰度待人工检查" if enlarged else "没有放大素材"))
    return colors, fonts, images


def delivery_record(data, config_path, report):
    width, height = data["canvas"]["width"], data["canvas"]["height"]
    divisor = math.gcd(width, height)
    checks = {name: check("not_applicable", "本次确定性图片排版不适用") for name in CHECKS}
    for name in ("content", "visual", "brand"):
        checks[name] = check("unverified", "配置和文件预检不能代替实际看图，需人工核验原文、视觉效果及品牌呈现")
    checks["dimensions"] = check("pass", "实际输出 PNG 尺寸与配置一致")
    checks["access"] = check("pass", "本地 poster.png 已成功写入并计算 SHA-256")
    checks["readability"] = report["checks"]["readability"]
    checks["assets"] = report["checks"]["assets"]
    item = {"id": "p1", "version": 1, "status": "draft", "reason": "待实际看图与人工批准；attempts=0 表示本组件无生图调用，交付前需合并真实生图记录", "attempts": 0,
            "prompt": data["prompt"], "artifact": {"kind": "local", "location": "poster.png"},
            "target": {"ratio": [width // divisor, height // divisor], "width": width, "height": height},
            "actual": {"width": width, "height": height, "format": "PNG"},
            "required_ids": [entry["id"] for entry in data["required_copy"]],
            "copy_checks": [{"id": entry["id"], "status": "unverified", "evidence": "仅做配置中绑定原文的精确匹配；最终图片中的可见性和完整性待人工核对"} for entry in data["required_copy"]],
            "checks": checks, "applicable": sorted(APPLICABLE),
            "production": {"method": "deterministic", "brand_id": report["brand_id"], "recipe": str(config_path), "layout_report": "layout-report.json"}}
    return {"schema_version": 2, "skill_version": SKILL_VERSION, "mode": "image", "requested_count": 1,
            "required_copy": data["required_copy"], "items": [item]}


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def compose(config_path, output_dir):
    """返回成功草稿报告；预检失败只在新目录保存诊断，不写海报。"""
    config_path, output_dir = Path(config_path).resolve(), Path(output_dir).absolute()
    require(not os.path.lexists(output_dir), "output_exists", "输出目录必须不存在，禁止覆盖：%s" % output_dir)
    dependencies = load_dependencies()
    report = new_report()
    try:
        data = read_json(config_path)
        brand_path = resolve_path(config_path.parent, data.get("brand"))
        brand = read_json(brand_path)
        report["reproducibility"] = {"config": {"path": str(config_path), "sha256": sha256(config_path)},
                                     "brand": {"path": str(brand_path), "sha256": sha256(brand_path)},
                                     "python": sys.version.split()[0],
                                     "pillow": importlib.import_module("PIL").__version__,
                                     "fonttools": importlib.import_module("fontTools").__version__}
        colors, fonts, images = prepare(data, brand, config_path, brand_path, report, dependencies)
    except (CompositionError, OSError) as exc:
        failure = exc if isinstance(exc, CompositionError) else CompositionError("io_error", "文件读取失败：%s" % exc)
        report["issues"].append(failure.issue())
        report["checks"]["layout"] = check("fail", str(failure))
        output_dir.mkdir(parents=False, exist_ok=False)
        write_json(output_dir / "layout-report.json", report)
        if failure is exc:
            raise
        raise failure from exc
    Image, ImageDraw, _, _, _, _ = dependencies
    canvas = data["canvas"]
    image = Image.new("RGBA", (canvas["width"], canvas["height"]), colors[canvas["background"]])
    draw = ImageDraw.Draw(image)
    # 装饰背景先画，防止配置顺序让背景遮盖内容。
    for block in data["blocks"]:
        if block["type"] == "rect":
            x, y, width, height = block["box"]
            draw.rounded_rectangle([x, y, x + width - 1, y + height - 1], radius=block.get("radius", 0), fill=colors[block["fill"]])
    text_records = {entry["id"]: entry for entry in report["texts"]}
    asset_records = {entry["id"]: entry for entry in report["assets"]}
    for block in data["blocks"]:
        ident = block["id"]
        if block["type"] == "text":
            entry = text_records[ident]
            for line, origin in zip(entry["lines"], entry["draw_origins"]):
                draw.text(tuple(origin), line, font=fonts[ident], fill=colors[block["color"]], anchor="ls")
        elif block["type"] == "image":
            x, y, width, height = asset_records[ident]["placed_box"]
            resized = images[ident].resize((width, height), Image.Resampling.LANCZOS).convert("RGBA")
            image.alpha_composite(resized, (x, y))
    preview_width = data["reading"]["preview_width"]
    preview_height = max(1, round(canvas["height"] * preview_width / canvas["width"]))
    preview = image.resize((preview_width, preview_height), Image.Resampling.LANCZOS)
    # mkdir 独占创建防止预检期间其他进程建立输出目录。
    output_dir.mkdir(parents=False, exist_ok=False)
    poster_path = output_dir / "poster.png"
    with poster_path.open("xb") as stream:
        image.save(stream, format="PNG")
    with (output_dir / "preview-mobile.png").open("xb") as stream:
        preview.save(stream, format="PNG")
    report["artifact"] = {"location": "poster.png", "sha256": sha256(poster_path), "width": canvas["width"], "height": canvas["height"], "format": "PNG"}
    report["preview"] = {"location": "preview-mobile.png", "sha256": sha256(output_dir / "preview-mobile.png"),
                         "width": preview_width, "height": preview_height}
    write_json(output_dir / "layout-report.json", report)
    write_json(output_dir / "delivery.json", delivery_record(data, config_path, report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = compose(args.config, args.output_dir)
    except (CompositionError, DependencyError, OSError) as exc:
        print(json.dumps({"generated": False, "visual_approval": False, "error": str(exc),
                          "code": getattr(exc, "code", "dependency_error" if isinstance(exc, DependencyError) else "io_error")}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"generated": True, "status": "draft", "visual_approval": False,
                      "output_dir": str(args.output_dir.absolute()), "checks": report["checks"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
