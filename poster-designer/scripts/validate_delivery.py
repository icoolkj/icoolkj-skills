"""Validate delivery records, not visual quality. Python 3.9+, standard library only."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

CHECKS = {"content", "visual", "dimensions", "access", "brand", "edit_scope", "qr", "rights", "print"}
BASE = {"content", "visual", "dimensions", "access"}
EXTENDED = {"readability", "assets"}
STATES = {"pass", "fail", "unverified", "not_applicable"}


def positive(value):
    return type(value) is int and value > 0


def text(value):
    return isinstance(value, str) and bool(value.strip())


def image_info(path):
    """Read header dimensions; this does not prove that all pixels decode correctly."""
    with path.open("rb") as stream:
        head = stream.read(24)
        if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR" and len(head) == 24:
            return (*struct.unpack(">II", head[16:24]), "PNG")
        if head[:6] in (b"GIF87a", b"GIF89a") and len(head) >= 10:
            return (*struct.unpack("<HH", head[6:10]), "GIF")
        if head[:2] == b"\xff\xd8":
            stream.seek(2)
            while True:
                lead = stream.read(1)
                if not lead:
                    break
                if lead != b"\xff":
                    raise ValueError("invalid JPEG marker")
                marker = stream.read(1)
                while marker == b"\xff":
                    marker = stream.read(1)
                if not marker or marker in (b"\xd9", b"\xda"):
                    break
                code = marker[0]
                if code == 0x01 or 0xD0 <= code <= 0xD8:
                    continue
                raw = stream.read(2)
                if len(raw) != 2:
                    break
                length = int.from_bytes(raw, "big")
                if length < 2:
                    raise ValueError("invalid JPEG segment")
                if code in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                    raw = stream.read(5)
                    if len(raw) != 5:
                        break
                    height, width = struct.unpack(">HH", raw[1:5])
                    return width, height, "JPEG"
                stream.seek(length - 2, 1)
    raise ValueError("unsupported or invalid image header (PNG/JPEG/GIF required)")


def check_production(item, base, checks):
    """Bind deterministic preflight evidence to the actual output; no visual approval."""
    production = item.get("production")
    if not isinstance(production, dict) or production.get("method") not in ("generated", "edited", "deterministic"):
        return ["production.method must be generated/edited/deterministic"]
    if production["method"] != "deterministic":
        return []
    errors = []
    if not text(production.get("brand_id")) or not text(production.get("recipe")):
        errors.append("deterministic production requires brand_id and recipe")
    if not text(production.get("layout_report")):
        return errors + ["deterministic production requires layout_report"]
    artifact = item.get("artifact", {})
    if artifact.get("kind") != "local":
        return errors + ["deterministic evidence requires local artifact"]
    try:
        path = base / production["layout_report"]
        report = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(report, dict) or report.get("schema_version") != 1:
            return errors + ["invalid layout report schema"]
        recipe_path = (base / production["recipe"]).resolve()
        recipe_bytes = recipe_path.read_bytes()
        recipe = json.loads(recipe_bytes.decode("utf-8-sig"))
        if (not isinstance(recipe, dict) or recipe.get("schema_version") != 1
                or not isinstance(recipe.get("blocks"), list) or not recipe["blocks"]
                or not isinstance(recipe.get("canvas"), dict) or not text(recipe.get("brand"))):
            return errors + ["invalid deterministic recipe"]
        provenance = report.get("reproducibility", {})
        recorded_recipe = provenance.get("config", {})
        if recorded_recipe.get("sha256") != hashlib.sha256(recipe_bytes).hexdigest():
            errors.append("layout report recipe hash mismatch")
        brand_path = (recipe_path.parent / recipe["brand"]).resolve()
        brand_bytes = brand_path.read_bytes()
        brand = json.loads(brand_bytes.decode("utf-8-sig"))
        if not isinstance(brand, dict) or brand.get("id") != production.get("brand_id"):
            errors.append("recipe brand id mismatch")
        if provenance.get("brand", {}).get("sha256") != hashlib.sha256(brand_bytes).hexdigest():
            errors.append("layout report brand config hash mismatch")
        actual_path = (base / artifact["location"]).resolve()
        digest = hashlib.sha256(actual_path.read_bytes()).hexdigest()
        meta = report.get("artifact", {})
        if not isinstance(meta, dict) or meta.get("sha256") != digest:
            errors.append("layout report artifact hash mismatch")
        else:
            if not text(meta.get("location")) or (path.parent / meta["location"]).resolve() != actual_path:
                errors.append("layout report artifact location mismatch")
            actual = item.get("actual", {})
            if any(meta.get(k) != actual.get(k) for k in ("width", "height", "format")):
                errors.append("layout report metadata mismatch")
        if report.get("brand_id") != production.get("brand_id"):
            errors.append("layout report brand mismatch")
        preview = report.get("preview", {})
        if not isinstance(preview, dict) or not text(preview.get("location")):
            errors.append("layout report preview required")
        else:
            preview_path = path.parent / preview["location"]
            w, h, fmt = image_info(preview_path)
            if w != preview.get("width") or h != preview.get("height") or fmt != "PNG":
                errors.append("layout preview metadata mismatch")
            if preview.get("sha256") != hashlib.sha256(preview_path.read_bytes()).hexdigest():
                errors.append("layout preview hash mismatch")
            actual = item.get("actual", {})
            if (not positive(actual.get("width")) or not positive(actual.get("height"))
                    or w > actual["width"] or h != max(1, round(actual["height"] * w / actual["width"]))):
                errors.append("layout preview ratio/size mismatch")
        preflight = report.get("checks", {})
        if not isinstance(preflight, dict):
            return errors + ["layout report checks required"]
        layout = preflight.get("layout", {})
        if not isinstance(layout, dict) or layout.get("status") != "pass" or not text(layout.get("evidence")):
            errors.append("layout preflight must pass before image delivery")
        overrides = production.get("review_overrides", {})
        if not isinstance(overrides, dict) or not set(overrides) <= EXTENDED:
            return errors + ["invalid review_overrides"]
        for name in EXTENDED:
            result = preflight.get(name, {})
            claim = checks.get(name, {})
            if not isinstance(result, dict) or result.get("status") not in ("pass", "fail", "unverified") or not text(result.get("evidence")):
                errors.append("invalid " + name + " preflight evidence")
                continue
            if not isinstance(claim, dict):
                continue
            override = overrides.get(name, {})
            manual = (result["status"] == "unverified" and isinstance(override, dict)
                      and text(override.get("evidence")) and override.get("artifact_sha256") == digest)
            if claim.get("status") == "pass" and result["status"] != "pass" and not manual:
                errors.append(name + " preflight unresolved; fail cannot be overridden")
        return errors
    except (OSError, ValueError, TypeError, KeyError, AttributeError, struct.error) as exc:
        return errors + ["layout report: " + str(exc)]


def validate(data, base):
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    if not isinstance(data, dict):
        return ["record must be an object"]
    schema = data.get("schema_version")
    require(type(schema) is int and schema in (1, 2), "schema_version must be 1 or 2")
    check_names = CHECKS | EXTENDED if schema == 2 else CHECKS
    base_checks = BASE | EXTENDED if schema == 2 else BASE
    require(text(data.get("skill_version")), "skill_version required")
    if data.get("skill_version") == "1.0.2":
        require(schema == 2, "V1.0.2 requires schema_version 2")
    mode = data.get("mode")
    require(mode in ("plan", "prompt", "image", "edit"), "invalid mode")
    require(positive(data.get("requested_count")), "requested_count must be a positive integer")
    required = data.get("required_copy")
    items = data.get("items")
    if not isinstance(required, list) or not isinstance(items, list):
        return errors + ["required_copy and items must be arrays"]
    ids = set()
    for entry in required:
        if not isinstance(entry, dict) or not all(text(entry.get(k)) for k in ("id", "text", "source")):
            errors.append("invalid required_copy entry")
            continue
        require(entry["id"] not in ids, "duplicate required_copy id")
        ids.add(entry["id"])
    require(len(items) == data.get("requested_count"), "item count mismatch")
    item_ids, locations, covered = set(), set(), set()
    for index, item in enumerate(items):
        prefix = "item[%d]: " % index
        if not isinstance(item, dict):
            errors.append(prefix + "must be an object")
            continue
        ident = item.get("id")
        if text(ident):
            require(ident not in item_ids, prefix + "duplicate id")
            item_ids.add(ident)
        else:
            errors.append(prefix + "id required")
        status = item.get("status")
        require(status in ("ready", "draft", "blocked", "plan_only"), prefix + "invalid status")
        require(positive(item.get("version")), prefix + "version required")
        require(text(item.get("prompt")), prefix + "prompt/design required")
        attempts = item.get("attempts")
        require(type(attempts) is int and 0 <= attempts <= 3, prefix + "attempts must be 0..3")
        if status != "ready":
            require(text(item.get("reason")), prefix + "reason required")
        if mode in ("plan", "prompt"):
            require(status == "plan_only" and attempts == 0, prefix + "text-only request cannot generate images")
        req = item.get("required_ids")
        if not isinstance(req, list) or not all(text(v) for v in req):
            errors.append(prefix + "required_ids must be a string array")
            req = []
        require(len(req) == len(set(req)), prefix + "duplicate required_ids")
        require(set(req) <= ids, prefix + "unknown required id")
        covered.update(req)
        if len(items) == 1:
            require(set(req) == ids, prefix + "mandatory copy missing")
        cc = item.get("copy_checks")
        cc_ids = []
        if not isinstance(cc, list):
            errors.append(prefix + "copy_checks must be an array")
            cc = []
        for check in cc:
            if not isinstance(check, dict) or not text(check.get("id")):
                errors.append(prefix + "invalid copy check")
                continue
            cc_ids.append(check["id"])
            require(check.get("status") in ("pass", "fail", "unverified") and text(check.get("evidence")), prefix + "invalid copy check evidence/status")
            if status == "ready":
                require(check.get("status") == "pass", prefix + "mandatory copy not passed")
        require(set(cc_ids) == set(req) and len(cc_ids) == len(req), prefix + "copy_checks coverage mismatch")
        checks = item.get("checks")
        applicable = item.get("applicable")
        if not isinstance(checks, dict):
            errors.append(prefix + "checks must be an object")
            checks = {}
        if not isinstance(applicable, list) or not all(text(v) for v in applicable):
            errors.append(prefix + "invalid applicable checks")
            applicable = []
        require(set(applicable) <= check_names, prefix + "unknown applicable check")
        require(set(checks) <= check_names, prefix + "unknown check field")
        for name in check_names:
            check = checks.get(name)
            if not isinstance(check, dict):
                errors.append(prefix + name + " check missing")
                continue
            require(check.get("status") in STATES and text(check.get("evidence")), prefix + name + " invalid status/evidence")
            if status in ("ready", "draft"):
                require((name in applicable) == (check.get("status") != "not_applicable"), prefix + name + " applicability contradicts status")
            if status == "ready" and name in applicable:
                require(check.get("status") == "pass", prefix + name + " not passed")
        artifact = item.get("artifact")
        if status in ("plan_only", "blocked"):
            require(artifact is None, prefix + "non-image status must not claim artifact")
            continue
        require(base_checks <= set(applicable), prefix + "base checks must be applicable")
        if mode == "edit":
            require("edit_scope" in applicable, prefix + "edit_scope required")
        if not isinstance(artifact, dict) or artifact.get("kind") not in ("local", "remote") or not text(artifact.get("location")):
            errors.append(prefix + "accessible artifact required")
            continue
        access = checks.get("access", {})
        require(isinstance(access, dict) and access.get("status") == "pass", prefix + "artifact access must pass")
        location = artifact["location"]
        key = str((base / location).resolve()) if artifact["kind"] == "local" else location
        require(key not in locations, prefix + "separate posters must have distinct artifacts")
        locations.add(key)
        actual = item.get("actual")
        if artifact["kind"] == "local":
            try:
                width, height, fmt = image_info(Path(key))
                require(width > 0 and height > 0, prefix + "invalid image dimensions")
                require(actual == {"width": width, "height": height, "format": fmt}, prefix + "actual metadata differs from file")
                extensions = {"PNG": {".png"}, "JPEG": {".jpg", ".jpeg"}, "GIF": {".gif"}}
                require(Path(key).suffix.lower() in extensions[fmt], prefix + "extension differs from format")
            except (OSError, ValueError, struct.error) as exc:
                errors.append(prefix + "artifact: " + str(exc))
        if schema == 2:
            errors.extend(prefix + error for error in check_production(item, base, checks))
        valid_actual = isinstance(actual, dict) and positive(actual.get("width")) and positive(actual.get("height")) and text(actual.get("format"))
        if status == "ready":
            require(valid_actual, prefix + "ready requires actual metadata")
        target = item.get("target")
        if not isinstance(target, dict):
            errors.append(prefix + "target required")
            continue
        ratio = target.get("ratio")
        valid_ratio = isinstance(ratio, list) and len(ratio) == 2 and all(positive(v) for v in ratio)
        require(valid_ratio, prefix + "ratio must contain two positive integers")
        tw, th = target.get("width"), target.get("height")
        exact = tw is not None or th is not None
        if exact:
            require(positive(tw) and positive(th), prefix + "exact dimensions must be positive pairs")
            if positive(tw) and positive(th) and valid_ratio:
                require(tw * ratio[1] == th * ratio[0], prefix + "target dimensions conflict with ratio")
        dim = checks.get("dimensions", {})
        if valid_actual and isinstance(dim, dict) and dim.get("status") == "pass":
            if exact:
                require(actual["width"] == tw and actual["height"] == th, prefix + "exact size mismatch")
            if valid_ratio:
                require(actual["width"] * ratio[1] == actual["height"] * ratio[0], prefix + "ratio mismatch")
    require(covered == ids, "required_copy not fully assigned to posters")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.record.read_text(encoding="utf-8-sig"))
        errors = validate(data, args.record.resolve().parent)
    except (OSError, ValueError, TypeError) as exc:
        errors = [str(exc)]
    print(json.dumps({"record_valid": not errors, "visual_approval": False, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
