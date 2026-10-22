#!/usr/bin/env python3
"""Report style profiles for data analysis reports.

10 preset styles, each with color palette, typography, layout, and chart styling.
Users must choose a style before report generation.
"""

from __future__ import annotations


QUALITY = "professional, publication-ready, clear hierarchy, consistent styling"

STYLES = {
    "corporate": {
        "name": "企业商务风",
        "description": "深蓝主色，白底，正式严谨，适合企业年报/商业分析",
        "primary_color": "#1a3a6b",
        "secondary_color": "#2d5a9e",
        "accent_color": "#e8a838",
        "background": "#ffffff",
        "text_color": "#333333",
        "font_family": "'Helvetica Neue', Arial, sans-serif",
        "heading_size": "1.4em",
        "chart_style": {
            "color_palette": ["#1a3a6b", "#2d5a9e", "#5b8dd6", "#e8a838", "#c0c0c0"],
            "grid_color": "#e0e0e0",
            "background": "#ffffff",
        },
        "layout": "single-column, generous margins, formal header/footer",
    },
    "minimal": {
        "name": "极简素雅风",
        "description": "黑白灰为主，大量留白，克制配色，适合学术/技术报告",
        "primary_color": "#222222",
        "secondary_color": "#555555",
        "accent_color": "#007acc",
        "background": "#fafafa",
        "text_color": "#333333",
        "font_family": "'Segoe UI', system-ui, sans-serif",
        "heading_size": "1.3em",
        "chart_style": {
            "color_palette": ["#222222", "#555555", "#888888", "#007acc", "#bbbbbb"],
            "grid_color": "#eeeeee",
            "background": "#fafafa",
        },
        "layout": "single-column, wide margins, minimal decoration",
    },
    "vibrant": {
        "name": "活力多彩风",
        "description": "明亮配色，活泼图表，适合营销/用户增长报告",
        "primary_color": "#e74c3c",
        "secondary_color": "#3498db",
        "accent_color": "#2ecc71",
        "background": "#ffffff",
        "text_color": "#2c3e50",
        "font_family": "'Source Sans Pro', sans-serif",
        "heading_size": "1.5em",
        "chart_style": {
            "color_palette": ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"],
            "grid_color": "#ecf0f1",
            "background": "#ffffff",
        },
        "layout": "multi-column capable, colorful headers, bold accents",
    },
    "dark": {
        "name": "暗色科技风",
        "description": "深色背景，霓虹强调色，适合技术/运维/安全报告",
        "primary_color": "#00d4aa",
        "secondary_color": "#0ea5e9",
        "accent_color": "#f59e0b",
        "background": "#1a1a2e",
        "text_color": "#e0e0e0",
        "font_family": "'JetBrains Mono', 'Consolas', monospace",
        "heading_size": "1.4em",
        "chart_style": {
            "color_palette": ["#00d4aa", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6"],
            "grid_color": "#333355",
            "background": "#1a1a2e",
        },
        "layout": "single-column, dark theme, neon accents, code-friendly",
    },
    "editorial": {
        "name": "杂志编辑风",
        "description": "优雅排版，精致字体，适合行业洞察/深度分析",
        "primary_color": "#8b0000",
        "secondary_color": "#2c3e50",
        "accent_color": "#d4a017",
        "background": "#fffef8",
        "text_color": "#2c3e50",
        "font_family": "Georgia, 'Times New Roman', serif",
        "heading_size": "1.6em",
        "chart_style": {
            "color_palette": ["#8b0000", "#2c3e50", "#d4a017", "#5d6d7e", "#a93226"],
            "grid_color": "#d5d8dc",
            "background": "#fffef8",
        },
        "layout": "editorial columns, drop caps, pull quotes, refined typography",
    },
    "fresh": {
        "name": "清新自然风",
        "description": "绿色系配色，柔和自然，适合环保/健康/生活方式报告",
        "primary_color": "#27ae60",
        "secondary_color": "#16a085",
        "accent_color": "#f1c40f",
        "background": "#f0fff4",
        "text_color": "#2c3e50",
        "font_family": "'Nunito', sans-serif",
        "heading_size": "1.4em",
        "chart_style": {
            "color_palette": ["#27ae60", "#16a085", "#f1c40f", "#e67e22", "#1abc9c"],
            "grid_color": "#d5f5e3",
            "background": "#f0fff4",
        },
        "layout": "rounded corners, soft shadows, organic shapes",
    },
    "warm": {
        "name": "温暖人文风",
        "description": "暖橙棕色系，亲切柔和，适合社会/教育/公益报告",
        "primary_color": "#d35400",
        "secondary_color": "#e67e22",
        "accent_color": "#7d6608",
        "background": "#fdf6ec",
        "text_color": "#4a3728",
        "font_family": "'Lora', Georgia, serif",
        "heading_size": "1.5em",
        "chart_style": {
            "color_palette": ["#d35400", "#e67e22", "#7d6608", "#a04000", "#cd6155"],
            "grid_color": "#f0e6d3",
            "background": "#fdf6ec",
        },
        "layout": "warm tones, human-centered, accessible spacing",
    },
    "tech_blue": {
        "name": "科技蓝风",
        "description": "蓝色渐变，数据驱动感，适合产品/技术/数据报告",
        "primary_color": "#2563eb",
        "secondary_color": "#7c3aed",
        "accent_color": "#06b6d4",
        "background": "#ffffff",
        "text_color": "#1e293b",
        "font_family": "'Inter', system-ui, sans-serif",
        "heading_size": "1.4em",
        "chart_style": {
            "color_palette": ["#2563eb", "#7c3aed", "#06b6d4", "#f59e0b", "#10b981"],
            "grid_color": "#e2e8f0",
            "background": "#ffffff",
        },
        "layout": "data-dense, gradient accents, dashboard-like sections",
    },
    "retro": {
        "name": "复古怀旧风",
        "description": "棕褐配色，怀旧质感，适合历史/文化/品牌传承报告",
        "primary_color": "#8b4513",
        "secondary_color": "#cd853f",
        "accent_color": "#daa520",
        "background": "#f5f0e1",
        "text_color": "#3e2723",
        "font_family": "'Palatino', 'Book Antiqua', serif",
        "heading_size": "1.5em",
        "chart_style": {
            "color_palette": ["#8b4513", "#cd853f", "#daa520", "#6d4c41", "#a1887f"],
            "grid_color": "#d7ccc8",
            "background": "#f5f0e1",
        },
        "layout": "vintage borders, sepia tones, classic ornamentation",
    },
    "dashboard": {
        "name": "仪表盘风",
        "description": "卡片式布局，信息密集，适合实时监控/运营报告",
        "primary_color": "#4f46e5",
        "secondary_color": "#0ea5e9",
        "accent_color": "#f59e0b",
        "background": "#f8fafc",
        "text_color": "#1e293b",
        "font_family": "'Inter', system-ui, sans-serif",
        "heading_size": "1.3em",
        "chart_style": {
            "color_palette": ["#4f46e5", "#0ea5e9", "#f59e0b", "#10b981", "#ef4444"],
            "grid_color": "#e2e8f0",
            "background": "#ffffff",
        },
        "layout": "grid cards, KPI tiles, compact data display",
    },
}


def get_style(style_id: str) -> dict:
    profile = STYLES.get(style_id)
    if not profile:
        known = ", ".join(STYLES)
        raise ValueError(f"Unknown report style '{style_id}'. Choose one of: {known}")
    return profile


def list_styles() -> list[dict]:
    return [{"id": k, "name": v["name"], "description": v["description"]} for k, v in STYLES.items()]


def print_style_menu() -> None:
    print("\n" + "=" * 60)
    print("  【必须】请选择报告风格（10种可选）")
    print("=" * 60)
    for i, (style_id, profile) in enumerate(STYLES.items(), 1):
        print(f"  {i:2d}. {style_id:14s} — {profile['name']}")
        print(f"      {profile['description']}")
    print("-" * 60)
    print("  用法：--style corporate（统一风格）或编辑 report.json 逐节设置")
    print("=" * 60 + "\n")
