#!/usr/bin/env python3
"""
Security Scanner - 恶意哈希库维护工具

把用户提供的 SHA256 样本合并进 references/hashes.json，
或把第三方 JSON 放到 references/hash-sources/ 后重建主库。

用法:
    python update_hashes.py --add <sha256> [--name 名称] [--desc 说明]
    python update_hashes.py --from-file hashes.txt
    python update_hashes.py --from-json extra.json
    python update_hashes.py --rebuild
    python update_hashes.py --list
    python update_hashes.py --remove <sha256>

说明:
    - 默认只写本地文件，不访问网络。
    - --from-url 仅在用户明确要求在线更新时使用；只下载哈希清单，不下载样本。
    - 扫描时 scan.py 会合并：内置 EICAR + hashes.json + hash-sources/*.json。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"
HASHES_PATH = REFERENCES_DIR / "hashes.json"
SOURCES_DIR = REFERENCES_DIR / "hash-sources"

SHA256_RE = re.compile(r"\b[a-fA-F0-9]{64}\b")
EICAR_SHA256 = "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def empty_db():
    return {
        "version": 1,
        "updated_at": utc_now(),
        "source": "local",
        "malicious_hashes": [
            {
                "sha256": EICAR_SHA256,
                "name": "EICAR-Test-File",
                "description": "标准防病毒测试文件",
                "added_at": utc_now(),
            }
        ],
    }


def load_db(path=HASHES_PATH):
    if not path.exists():
        return empty_db()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        return empty_db()
    items = data.get("malicious_hashes", [])
    if isinstance(items, dict):
        items = [{"sha256": k, "name": v} for k, v in items.items()]
    data["malicious_hashes"] = items if isinstance(items, list) else []
    data.setdefault("version", 1)
    data.setdefault("source", "local")
    return data


def normalize_item(item, default_name="local"):
    if not isinstance(item, dict):
        return None
    sha = str(item.get("sha256", "")).strip().lower()
    if not SHA256_RE.fullmatch(sha):
        return None
    name = item.get("name") or item.get("malware") or default_name
    desc = item.get("description") or item.get("desc") or ""
    out = {
        "sha256": sha,
        "name": str(name),
        "description": str(desc),
    }
    if item.get("added_at"):
        out["added_at"] = str(item["added_at"])
    if item.get("source"):
        out["source"] = str(item["source"])
    return out


def merge_items(existing, incoming):
    by_sha = {}
    for item in existing:
        norm = normalize_item(item)
        if norm:
            by_sha[norm["sha256"]] = norm
    added = 0
    updated = 0
    for item in incoming:
        norm = normalize_item(item)
        if not norm:
            continue
        if norm["sha256"] in by_sha:
            old = by_sha[norm["sha256"]]
            if norm.get("name") and norm["name"] != old.get("name"):
                old["name"] = norm["name"]
                updated += 1
            if norm.get("description") and not old.get("description"):
                old["description"] = norm["description"]
            if norm.get("source"):
                old["source"] = norm["source"]
        else:
            if "added_at" not in norm:
                norm["added_at"] = utc_now()
            by_sha[norm["sha256"]] = norm
            added += 1
    merged = sorted(by_sha.values(), key=lambda x: x["sha256"])
    return merged, added, updated


def save_db(data, path=HASHES_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = utc_now()
    tmp = path.with_suffix(".json.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp.replace(path)


def items_from_text(text, default_name="imported"):
    items = []
    for sha in SHA256_RE.findall(text):
        items.append({"sha256": sha.lower(), "name": default_name})
    return items


def items_from_json_obj(obj, default_name="imported"):
    items = []
    if isinstance(obj, dict) and "malicious_hashes" in obj:
        raw = obj["malicious_hashes"]
        if isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(v, dict):
                    v = dict(v)
                    v["sha256"] = k
                    items.append(v)
                else:
                    items.append({"sha256": k, "name": str(v)})
        elif isinstance(raw, list):
            items.extend(raw)
    elif isinstance(obj, list):
        items.extend(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if SHA256_RE.fullmatch(str(k)):
                items.append({"sha256": k, "name": str(v)})
    normalized = []
    for item in items:
        norm = normalize_item(item, default_name=default_name)
        if norm:
            normalized.append(norm)
    return normalized


def rebuild_from_sources(db):
    incoming = []
    if SOURCES_DIR.is_dir():
        for path in sorted(SOURCES_DIR.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                print(f"跳过 {path.name}: {e}", file=sys.stderr)
                continue
            incoming.extend(items_from_json_obj(obj, default_name=path.stem))
    merged, added, updated = merge_items(db.get("malicious_hashes", []), incoming)
    db["malicious_hashes"] = merged
    db["source"] = "local+hash-sources"
    return added, updated


def fetch_url(url, timeout=20):
    req = Request(url, headers={"User-Agent": "security-scanner-hash-updater/1.2"})
    with urlopen(req, timeout=timeout) as resp:  # nosec - user-provided URL, hashes only
        data = resp.read(8 * 1024 * 1024)
        ctype = (resp.headers.get("Content-Type") or "").lower()
    return data, ctype


def main():
    parser = argparse.ArgumentParser(description="维护 security-scanner 恶意哈希库")
    parser.add_argument("--add", metavar="SHA256", help="追加一条 SHA256")
    parser.add_argument("--name", default="local", help="条目名称")
    parser.add_argument("--desc", default="", help="条目说明")
    parser.add_argument("--from-file", metavar="PATH", help="从文本/JSON 文件导入")
    parser.add_argument("--from-json", metavar="PATH", help="从 JSON 文件导入（同 --from-file）")
    parser.add_argument("--from-url", metavar="URL", help="从 URL 下载哈希清单（仅哈希，不下载样本）")
    parser.add_argument("--rebuild", action="store_true", help="合并 hash-sources/*.json 到 hashes.json")
    parser.add_argument("--remove", metavar="SHA256", help="删除一条 SHA256")
    parser.add_argument("--list", action="store_true", help="列出当前哈希库")
    args = parser.parse_args()

    if not any([args.add, args.from_file, args.from_json, args.from_url,
                args.rebuild, args.remove, args.list]):
        parser.print_help()
        return 1

    db = load_db()
    incoming = []

    if args.add:
        incoming.append({
            "sha256": args.add,
            "name": args.name,
            "description": args.desc,
            "source": "manual",
        })

    src_path = args.from_file or args.from_json
    if src_path:
        path = Path(src_path)
        raw = path.read_text(encoding="utf-8")
        try:
            obj = json.loads(raw)
            incoming.extend(items_from_json_obj(obj, default_name=path.stem))
        except json.JSONDecodeError:
            incoming.extend(items_from_text(raw, default_name=path.stem))

    if args.from_url:
        try:
            data, ctype = fetch_url(args.from_url)
        except (URLError, TimeoutError, ValueError, OSError) as e:
            print(f"下载失败: {e}", file=sys.stderr)
            return 2
        text = data.decode("utf-8", errors="replace")
        if "json" in ctype or text.lstrip().startswith(("{", "[")):
            try:
                incoming.extend(items_from_json_obj(json.loads(text), default_name="url"))
            except json.JSONDecodeError:
                incoming.extend(items_from_text(text, default_name="url"))
        else:
            incoming.extend(items_from_text(text, default_name="url"))
        db["source"] = args.from_url

    if incoming:
        merged, added, updated = merge_items(db.get("malicious_hashes", []), incoming)
        db["malicious_hashes"] = merged
        save_db(db)
        print(f"已写入 {HASHES_PATH}")
        print(f"新增 {added}，更新 {updated}，当前共 {len(merged)} 条")

    if args.rebuild:
        added, updated = rebuild_from_sources(db)
        save_db(db)
        print(f"已从 hash-sources 重建 {HASHES_PATH}")
        print(f"新增 {added}，更新 {updated}，当前共 {len(db['malicious_hashes'])} 条")

    if args.remove:
        sha = args.remove.strip().lower()
        before = len(db["malicious_hashes"])
        db["malicious_hashes"] = [
            x for x in db["malicious_hashes"]
            if str(x.get("sha256", "")).lower() != sha
        ]
        removed = before - len(db["malicious_hashes"])
        save_db(db)
        print(f"删除 {removed} 条，当前共 {len(db['malicious_hashes'])} 条")

    if args.list:
        items = db.get("malicious_hashes", [])
        print(f"{HASHES_PATH}  ({len(items)} 条, updated {db.get('updated_at', '-')})")
        for item in items:
            print(f"{item.get('sha256')}  {item.get('name', '')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
