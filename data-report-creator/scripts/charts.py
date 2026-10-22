#!/usr/bin/env python3
"""Chart generation using matplotlib with style-aware theming."""

from __future__ import annotations

import json
import platform
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import font_manager

from styler import get_style


def _setup_chinese_font() -> None:
    system = platform.system()
    candidate_fonts = []

    if system == "Windows":
        candidate_fonts = [
            "Microsoft YaHei", "SimHei", "SimSun", "KaiTi",
            "Microsoft YaHei UI", "FangSong",
        ]
    elif system == "Darwin":
        candidate_fonts = [
            "PingFang SC", "Heiti SC", "STHeiti", "Arial Unicode MS",
            "Hiragino Sans GB", "Songti SC",
        ]
    else:
        candidate_fonts = [
            "WenQuanYi Micro Hei", "WenQuanYi Zen Hei", "Noto Sans CJK SC",
            "Noto Sans CJK", "Source Han Sans SC", "Source Han Sans CN",
            "Droid Sans Fallback", "AR PL UMing CN",
        ]

    available_fonts = set(f.name for f in font_manager.fontManager.ttflist)

    for font_name in candidate_fonts:
        if font_name in available_fonts:
            plt.rcParams["font.sans-serif"] = [font_name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            return

    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_setup_chinese_font()


CHART_TYPES = ("bar", "line", "pie", "scatter", "histogram", "area", "heatmap", "table")


def _apply_style(ax, style_profile: dict) -> None:
    chart_cfg = style_profile.get("chart_style", {})
    palette = chart_cfg.get("color_palette", ["#1a3a6b", "#2d5a9e", "#e8a838"])
    bg = chart_cfg.get("background", "#ffffff")
    grid = chart_cfg.get("grid_color", "#e0e0e0")
    ax.set_facecolor(bg)
    ax.figure.set_facecolor(bg)
    ax.grid(True, color=grid, linewidth=0.6, alpha=0.7)
    ax.tick_params(colors=style_profile.get("text_color", "#333333"))
    for spine in ax.spines.values():
        spine.set_color(grid)
    ax.set_prop_cycle("color", palette)


def generate_bar(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    _apply_style(ax, style_profile)
    labels = data.get("labels", [])
    values = data.get("values", [])
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    bars = ax.bar(labels, values, color=colors[:len(values)], edgecolor="none", width=0.6)
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    ax.set_xlabel(data.get("x_label", ""), fontsize=10)
    ax.set_ylabel(data.get("y_label", ""), fontsize=10)
    if data.get("horizontal"):
        ax.barh(labels, values, color=colors[:len(values)])
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                f"{val:,.0f}" if isinstance(val, (int, float)) else str(val),
                ha="center", va="bottom", fontsize=8, color=style_profile.get("text_color", "#333333"))
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_line(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    _apply_style(ax, style_profile)
    labels = data.get("labels", [])
    series = data.get("series", [{"name": "Series 1", "values": data.get("values", [])}])
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    for i, s in enumerate(series):
        ax.plot(labels, s["values"], marker="o", markersize=4, linewidth=2,
                color=colors[i % len(colors)], label=s.get("name", f"Series {i+1}"))
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    ax.set_xlabel(data.get("x_label", ""), fontsize=10)
    ax.set_ylabel(data.get("y_label", ""), fontsize=10)
    if len(series) > 1:
        ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_pie(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)
    _apply_style(ax, style_profile)
    labels = data.get("labels", [])
    values = data.get("values", [])
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct="%1.1f%%", startangle=90,
        colors=colors[:len(values)], textprops={"fontsize": 9},
    )
    for autotext in autotexts:
        autotext.set_color("white")
        autotext.set_fontweight("bold")
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_histogram(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    _apply_style(ax, style_profile)
    values = data.get("values", [])
    bins = data.get("bins", 20)
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    ax.hist(values, bins=bins, color=colors[0], edgecolor="white", alpha=0.85)
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    ax.set_xlabel(data.get("x_label", ""), fontsize=10)
    ax.set_ylabel(data.get("y_label", "频次"), fontsize=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_scatter(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    _apply_style(ax, style_profile)
    x = data.get("x_values", [])
    y = data.get("y_values", [])
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    ax.scatter(x, y, c=colors[0], alpha=0.6, s=30, edgecolors="none")
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    ax.set_xlabel(data.get("x_label", ""), fontsize=10)
    ax.set_ylabel(data.get("y_label", ""), fontsize=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


def generate_area(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5.5), dpi=150)
    _apply_style(ax, style_profile)
    labels = data.get("labels", [])
    values = data.get("values", [])
    colors = style_profile.get("chart_style", {}).get("color_palette", ["#1a3a6b"])
    ax.fill_between(range(len(labels)), values, alpha=0.4, color=colors[0])
    ax.plot(range(len(labels)), values, color=colors[0], linewidth=2)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    ax.set_xlabel(data.get("x_label", ""), fontsize=10)
    ax.set_ylabel(data.get("y_label", ""), fontsize=10)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path


GENERATORS = {
    "bar": generate_bar,
    "line": generate_line,
    "pie": generate_pie,
    "histogram": generate_histogram,
    "scatter": generate_scatter,
    "area": generate_area,
}


def generate_chart(chart_config: dict, output_path: Path, style_id: str = "corporate") -> Path:
    chart_type = chart_config.get("type", "bar")
    if chart_type not in GENERATORS:
        raise ValueError(f"Unknown chart type: {chart_type}. Available: {list(GENERATORS)}")
    style_profile = get_style(style_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return GENERATORS[chart_type](chart_config.get("data", {}), output_path, style_profile)


def generate_table_image(data: dict, output_path: Path, style_profile: dict) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)
    ax.axis("off")
    headers = data.get("headers", [])
    rows = data.get("rows", [])
    cell_colors = [[style_profile.get("background", "#ffffff")] * len(headers) for _ in rows]
    table = ax.table(cellText=rows, colLabels=headers, cellColours=cell_colors,
                     loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.5)
    for (r, c), cell in table.get_celld().items():
        if r == 0:
            cell.set_facecolor(style_profile.get("primary_color", "#1a3a6b"))
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_edgecolor(style_profile.get("chart_style", {}).get("grid_color", "#e0e0e0"))
    ax.set_title(data.get("title", ""), fontsize=14, fontweight="bold",
                 color=style_profile.get("primary_color", "#333333"), pad=12)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return output_path
