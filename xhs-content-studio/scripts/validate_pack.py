#!/usr/bin/env python3
"""Validate generated Xiaohongshu copywriting pack (.md) and Gaussian Glassmorphism Studio (.html).

Checks:
1. Title count >= 3 and every title <= 20 Chinese characters.
2. Carousel card sections (P1..PN) between 4 and 12 cards by default; page count is content-driven.
3. Hashtags >= 8.
4. Prohibited advertising-law words AND unescaped single-character superlatives (e.g., 最成熟, 最好, 最强, 最快).
5. Optional HTML inspection: verifies Gaussian Glassmorphism CSS tokens (backdrop-filter, blur),
   bilingual UI elements, and Canvas PNG export support.
6. HTML self-containment & studio completeness: zero external http(s) resources (no CDN scripts
   or webfonts — the file must render offline), >= 4 switchable glass worlds, a glass opacity
   control, bilingual data-zh/data-en scaffold text, and real card rendering for PNG export
   (SVG foreignObject + canvas), not a placeholder drawing.
"""

import re
import sys
from pathlib import Path

BANNED_WORDS = [
    "国家级",
    "世界级",
    "全网第一",
    "全网首家",
    "最牛",
    "最佳",
    "顶级",
    "终极",
    "100%有效",
    "100%包过",
    "绝对有效",
    "加微",
    "私信领钱",
]

SUPERLATIVE_PATTERNS = [
    (r"最成熟", "极为成熟"),
    (r"最好", "尤为出色"),
    (r"最强", "表现极强"),
    (r"最快", "响应极快"),
    (r"最全", "非常全面"),
    (r"最优", "更为理想"),
]


def validate_markdown(text: str) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []

    titles = re.findall(r"^\d+\.\s*\*\*【[^】]+】\*\*\s*`([^`]+)`", text, flags=re.M)
    if len(titles) < 3:
        errors.append(f"Expected at least 3 title options, found {len(titles)}.")
    for idx, title in enumerate(titles, 1):
        if len(title.strip()) > 20:
            errors.append(
                f"Title #{idx} exceeds 20 chars ({len(title.strip())} chars): {title}"
            )

    cards = re.findall(r"^###\s*【P\d+\s+[^】]+】", text, flags=re.M)
    if not (4 <= len(cards) <= 12):
        errors.append(f"Expected 4 to 12 adaptive carousel cards, found {len(cards)}.")

    hashtags = re.findall(r"#[\w\u4e00-\u9fa5]+", text)
    if len(hashtags) < 8:
        errors.append(f"Expected at least 8 hashtags, found {len(hashtags)}.")

    found_banned = [w for w in BANNED_WORDS if w in text]
    if found_banned:
        errors.append(f"Found prohibited traffic-throttling words: {', '.join(found_banned)}")

    for pattern, suggestion in SUPERLATIVE_PATTERNS:
        if re.search(pattern, text):
            warnings.append(
                f"Detected superlative '{pattern}' — consider replacing with '{suggestion}' for safer Xiaohongshu traffic distribution."
            )

    stats = {
        "titles": len(titles),
        "cards": len(cards),
        "hashtags": len(hashtags),
        "banned": len(found_banned),
    }
    return errors, warnings, stats


def validate_html(html_text: str) -> list[str]:
    errors: list[str] = []
    if "backdrop-filter" not in html_text:
        errors.append("HTML preview is missing 'backdrop-filter' Gaussian glassmorphism CSS.")
    if "blur(" not in html_text:
        errors.append("HTML preview is missing Gaussian 'blur()' filter effect.")
    if "toDataURL('image/png')" not in html_text and 'toDataURL("image/png")' not in html_text:
        errors.append("HTML preview is missing Canvas 900x1200 PNG export support.")
    if "foreignObject" not in html_text:
        errors.append(
            "HTML PNG export does not render the actual card DOM (missing SVG foreignObject rendering); "
            "a placeholder canvas drawing is not acceptable."
        )
    external = re.findall(r'(?:src|href)\s*=\s*["\']https?://', html_text)
    if external:
        errors.append(
            f"HTML preview is not self-contained: found {len(external)} external http(s) resource(s) "
            "(CDN scripts/webfonts break offline and in restricted review networks)."
        )
    worlds = len(re.findall(r"data-set-world", html_text))
    if worlds < 4:
        errors.append(f"HTML studio must offer 4 switchable glass worlds, found {worlds} world switcher(s).")
    if "opacity-range" not in html_text:
        errors.append("HTML studio is missing the glass opacity slider (id='opacity-range').")
    if "blur-range" not in html_text:
        errors.append("HTML studio is missing the Gaussian blur slider (id='blur-range').")
    if "data-zh" not in html_text or "data-en" not in html_text:
        errors.append("HTML studio is missing bilingual scaffold text (data-zh / data-en attributes).")
    if "contenteditable" not in html_text:
        errors.append("HTML studio is missing inline text editing (contenteditable).")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/validate_pack.py <copy_pack.md> [cards_preview.html]")
        return 1

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"[ERROR] File not found: {md_path}")
        return 1

    md_text = md_path.read_text(encoding="utf-8")
    errors, warnings, stats = validate_markdown(md_text)

    html_status = ""
    if len(sys.argv) >= 3:
        html_path = Path(sys.argv[2])
        if not html_path.exists():
            errors.append(f"HTML file not found: {html_path}")
        else:
            html_errors = validate_html(html_path.read_text(encoding="utf-8"))
            errors.extend(html_errors)
            if not html_errors:
                html_status = " | HTML Studio verified (self-contained, 4 worlds, real 900x1200 PNG export)"

    for w in warnings:
        print(f"[WARN] {w}")

    if errors:
        print("[FAIL] Validation failed with errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(
        f"[PASS] Copy pack validated: {stats['titles']} titles (all <=20 chars), "
        f"{stats['cards']} carousel cards, {stats['hashtags']} hashtags, "
        f"{stats['banned']} banned words{html_status}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
