#!/usr/bin/env python3
"""Data loader for CSV, Excel, and JSON files.

Provides unified loading interface with automatic type detection,
data profiling, and quality assessment.
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


SUPPORTED_FORMATS = (".csv", ".xlsx", ".xls", ".json", ".jsonl")


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {suffix}. Supported: {SUPPORTED_FORMATS}")
    return suffix.lstrip(".")


def load_csv(path: Path) -> dict[str, Any]:
    if HAS_PANDAS:
        df = pd.read_csv(path)
        return {
            "columns": list(df.columns),
            "rows": df.values.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "shape": list(df.shape),
        }
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    columns = list(rows[0].keys()) if rows else []
    return {
        "columns": columns,
        "rows": [list(r.values()) for r in rows],
        "dtypes": {col: "str" for col in columns},
        "shape": [len(rows), len(columns)],
    }


def load_excel(path: Path) -> dict[str, Any]:
    if not HAS_PANDAS:
        raise RuntimeError("pandas+openpyxl required for Excel loading. pip install pandas openpyxl")
    df = pd.read_excel(path)
    return {
        "columns": list(df.columns),
        "rows": df.values.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "shape": list(df.shape),
    }


def load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        columns = list(raw[0].keys()) if raw and isinstance(raw[0], dict) else []
        rows = [list(item.values()) if isinstance(item, dict) else [item] for item in raw]
        return {
            "columns": columns,
            "rows": rows,
            "dtypes": {col: "auto" for col in columns},
            "shape": [len(rows), len(columns)],
        }
    if isinstance(raw, dict):
        return {"columns": list(raw.keys()), "rows": [list(raw.values())], "dtypes": "auto", "shape": [1, len(raw)]}
    return {"columns": [], "rows": [], "dtypes": {}, "shape": [0, 0]}


LOADERS = {"csv": load_csv, "xlsx": load_excel, "xls": load_excel, "json": load_json, "jsonl": load_json}


def load_data(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    fmt = detect_format(path)
    data = LOADERS[fmt](path)
    data["source_path"] = str(path)
    data["format"] = fmt
    data["profile"] = profile_data(data)
    return data


def profile_data(data: dict[str, Any]) -> dict[str, Any]:
    rows = data.get("rows", [])
    columns = data.get("columns", [])
    n_rows = len(rows)
    n_cols = len(columns)
    missing_cells = 0
    numeric_cols = []
    for col_idx, col in enumerate(columns):
        values = [r[col_idx] if col_idx < len(r) else None for r in rows]
        missing = sum(1 for v in values if v is None or v == "" or (isinstance(v, float) and v != v))
        missing_cells += missing
        numeric_count = sum(1 for v in values if isinstance(v, (int, float)) and v == v)
        if numeric_count > n_rows * 0.7 and n_rows > 0:
            numeric_cols.append(col)
    return {
        "row_count": n_rows,
        "column_count": n_cols,
        "missing_cells": missing_cells,
        "completeness": round(1 - missing_cells / max(n_rows * n_cols, 1), 4),
        "numeric_columns": numeric_cols,
    }


def summarize_column(data: dict[str, Any], col_index: int) -> dict[str, Any]:
    rows = data.get("rows", [])
    values = [r[col_index] if col_index < len(r) else None for r in rows]
    numeric = [v for v in values if isinstance(v, (int, float)) and v == v]
    result: dict[str, Any] = {"count": len(values), "missing": sum(1 for v in values if v is None or v == "")}
    if numeric:
        result.update({
            "type": "numeric",
            "min": min(numeric),
            "max": max(numeric),
            "mean": round(sum(numeric) / len(numeric), 4),
        })
    else:
        result["type"] = "categorical"
        unique = set(str(v) for v in values if v is not None and v != "")
        result["unique_count"] = len(unique)
        result["top_values"] = dict(sorted(
            {v: sum(1 for x in values if str(x) == v) for v in unique}.items(),
            key=lambda x: x[1], reverse=True,
        )[:5])
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load and profile a data file")
    parser.add_argument("data_file", help="Path to CSV/Excel/JSON data file")
    args = parser.parse_args()
    data = load_data(args.data_file)
    print(json.dumps({"columns": data["columns"], "shape": data["shape"], "profile": data["profile"]}, indent=2, ensure_ascii=False))
