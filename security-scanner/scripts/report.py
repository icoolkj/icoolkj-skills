#!/usr/bin/env python3
"""
Security Scanner - 报告生成器
将扫描结果 JSON 转换为可读的 Markdown 或 HTML 报告。

用法:
    python report.py --input <结果JSON路径> --format <md|html> --output <报告路径>
"""

import argparse
import html
import json
import sys
from datetime import datetime
from pathlib import Path


def load_results(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def format_time(ts):
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


# ---------- Markdown 转义 ----------
def md_text(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", "")


def md_code(s):
    s = str(s).replace("\n", " ").replace("\r", "")
    if "`" in s:
        return f"`` {s} ``"
    return f"`{s}`"


# ---------- Markdown 报告 ----------
def generate_markdown_report(data):
    scan_info = data["scan_info"]
    stats = data["stats"]
    results = data["results"]

    lines = []
    lines.append("# 安全扫描报告")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**工具版本**: {data.get('tool_version', '-')}  ")
    lines.append(f"**Schema**: {data.get('schema_version', '-')}")
    lines.append("")

    lines.append("## 1. 扫描概要")
    lines.append("")
    lines.append("| 项目 | 内容 |")
    lines.append("|------|------|")
    lines.append(f"| 扫描目标 | {md_code(scan_info['target'])} |")
    lines.append(f"| 扫描策略 | {md_text(scan_info['strategy'])} |")
    filt = scan_info.get("filter")
    lines.append(f"| 文件过滤 | {md_text(', '.join(filt)) if filt else '全部类型'} |")
    lines.append(f"| 扫描耗时 | {scan_info['elapsed']} 秒 |")
    lines.append(f"| 文件总数 | {scan_info['total_files']} |")
    lines.append("")

    lines.append("### 扫描统计")
    lines.append("")
    lines.append("| 分类 | 数量 | 占比 |")
    lines.append("|------|------|------|")
    total = stats["total"] if stats["total"] > 0 else 1
    for key, label in [("safe", "安全"), ("suspicious", "可疑"),
                       ("malicious", "恶意"), ("unchecked", "未能检查")]:
        lines.append(f"| {label} | {stats[key]} | {stats[key]/total*100:.1f}% |")
    lines.append("")

    def file_section(title, items, level_filter, note):
        lines.append(f"## {title}")
        lines.append("")
        if not items:
            lines.append(f"> {note}")
            lines.append("")
            return
        lines.append(f"> 共 **{len(items)}** 个。")
        lines.append("")
        for r in items:
            lines.append(f"### {md_text(r['name'])}")
            lines.append(f"- **路径**: {md_code(r['path'])}")
            lines.append(f"- **大小**: {format_size(r['size'])}")
            lines.append(f"- **扩展名**: {md_text(r['ext']) or '(无)'}")
            if r.get("actual_type"):
                lines.append(f"- **实际类型**: {md_text(r['actual_type'])}")
            if r.get("mtime"):
                lines.append(f"- **修改时间**: {format_time(r['mtime'])}")
            if r.get("sha256"):
                lines.append(f"- **SHA256**: {md_code(r['sha256'])}")
            lines.append(f"- **判定原因**: {md_text(r['reason'])}")
            lines.append("- **检测详情**:")
            matched_any = False
            for f in r.get("findings", []):
                if f["level"] in level_filter:
                    lines.append(f"  - **{f['level'].upper()}**: {md_text(f['reason'])}")
                    matched_any = True
            if not matched_any:
                lines.append("  - (无对应级别详情)")
            lines.append("")

    malicious = [r for r in results if r["classification"] == "malicious"]
    suspicious = [r for r in results if r["classification"] == "suspicious"]
    unchecked = [r for r in results if r["classification"] == "unchecked"]
    safe = [r for r in results if r["classification"] == "safe"]

    file_section("2. 恶意文件", malicious,
                 {"malicious", "critical", "high", "medium"},
                 "未发现恶意文件。")
    file_section("3. 可疑文件", suspicious,
                 {"suspicious", "high", "medium"},
                 "未发现可疑文件。")

    lines.append("## 4. 未能检查的文件")
    lines.append("")
    if unchecked:
        lines.append(f"> **{len(unchecked)}** 个文件未能完成扫描。")
        lines.append("")
        lines.append("| 文件名 | 路径 | 原因 |")
        lines.append("|--------|------|------|")
        for r in unchecked:
            lines.append(f"| {md_text(r['name'])} | {md_code(r['path'])} | {md_text(r['reason'])} |")
        lines.append("")
    else:
        lines.append("> 所有文件均已完成扫描。")
        lines.append("")

    lines.append("## 5. 安全文件")
    lines.append("")
    if safe:
        lines.append(f"> **{len(safe)}** 个文件未发现安全风险。")
        lines.append("")
        if len(safe) <= 50:
            lines.append("| 文件名 | 路径 | 大小 | 修改时间 |")
            lines.append("|--------|------|------|----------|")
            for r in safe:
                lines.append(f"| {md_text(r['name'])} | {md_code(r['path'])} | "
                             f"{format_size(r['size'])} | {format_time(r.get('mtime'))} |")
        else:
            lines.append(f"> 文件数量较多（{len(safe)} 个），仅展示前 50 个。")
            lines.append("")
            lines.append("| 文件名 | 路径 | 大小 | 修改时间 |")
            lines.append("|--------|------|------|----------|")
            for r in safe[:50]:
                lines.append(f"| {md_text(r['name'])} | {md_code(r['path'])} | "
                             f"{format_size(r['size'])} | {format_time(r.get('mtime'))} |")
            lines.append(f"| ... | 还有 {len(safe) - 50} 个安全文件 | | |")
        lines.append("")

    lines.append("## 6. 处理建议")
    lines.append("")
    if malicious:
        lines.append("- **恶意文件**: 立即断网，备份重要数据，使用专业杀毒软件全盘扫描。"
                     "在确认安全前不要执行这些文件。")
    if suspicious:
        lines.append("- **可疑文件**: 上传到 [VirusTotal](https://www.virustotal.com) "
                     "或在沙箱中分析；确认无害后再决定去留。")
    if unchecked:
        lines.append("- **未能检查的文件**: 检查权限、文件完整性；"
                     "对关键目录建议以管理员权限重新扫描。")
    if not (malicious or suspicious or unchecked):
        lines.append("- 本次扫描未发现安全风险。建议定期重复扫描，保持系统更新。")
    lines.append("")
    lines.append("> **注意**: 本工具仅基于静态特征做初步检测，不等同于专业杀毒软件。"
                 "对于重要系统，建议配合专业安全产品使用。")

    return "\n".join(lines)


# ---------- HTML 报告 ----------
def esc(s):
    return html.escape(str(s), quote=True) if s is not None else ""


def generate_html_report(data):
    scan_info = data["scan_info"]
    stats = data["stats"]
    results = data["results"]

    malicious = [r for r in results if r["classification"] == "malicious"]
    suspicious = [r for r in results if r["classification"] == "suspicious"]
    unchecked = [r for r in results if r["classification"] == "unchecked"]
    safe = [r for r in results if r["classification"] == "safe"]

    h = []
    h.append("<!DOCTYPE html>")
    h.append('<html lang="zh-CN">')
    h.append("<head>")
    h.append('<meta charset="UTF-8">')
    h.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    h.append("<title>安全扫描报告</title>")
    h.append("<style>")
    h.append("""
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 1000px; margin: 0 auto; padding: 20px; color: #333; }
        h1 { color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }
        h2 { color: #16213e; margin-top: 30px; }
        h3 { color: #0f3460; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; vertical-align: top; }
        th { background: #16213e; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        .malicious-text { color: #dc3545; font-weight: bold; }
        .suspicious-text { color: #856404; font-weight: bold; }
        .alert-malicious { background: #f8d7da; border: 1px solid #dc3545; border-radius: 8px;
                          padding: 15px; margin: 10px 0; }
        .alert-suspicious { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
                           padding: 15px; margin: 10px 0; }
        .alert-safe { background: #d4edda; border: 1px solid #28a745; border-radius: 8px;
                     padding: 15px; margin: 10px 0; }
        .file-card { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .file-card.malicious { border-color: #dc3545; background: #fff5f5; }
        .file-card.suspicious { border-color: #ffc107; background: #fff8e1; }
        .finding { margin: 5px 0; padding: 5px 10px; border-radius: 4px; font-size: 0.92em; }
        .finding.malicious { background: #f8d7da; }
        .finding.critical { background: #f5c2c7; }
        .finding.high { background: #fff3cd; }
        .finding.suspicious { background: #fff3cd; }
        .finding.medium { background: #e2e3e5; }
        .finding.low { background: #f1f3f5; color: #6c757d; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat-card { text-align: center; padding: 20px; border-radius: 8px; }
        .stat-card.safe { background: #d4edda; color: #155724; }
        .stat-card.suspicious { background: #fff3cd; color: #856404; }
        .stat-card.malicious { background: #f8d7da; color: #721c24; }
        .stat-card.unchecked { background: #e2e3e5; color: #383d41; }
        .stat-card .count { font-size: 2em; font-weight: bold; }
        .stat-card .label { font-size: 0.9em; }
        code { background: #f1f1f1; padding: 2px 6px; border-radius: 3px; font-size: 0.9em;
               word-break: break-all; }
        .meta { color: #6c757d; font-size: 0.9em; }
        details { margin: 10px 0; }
        summary { cursor: pointer; font-weight: bold; padding: 6px 0; color: #16213e; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6;
                 color: #6c757d; font-size: 0.85em; }
    """)
    h.append("</style>")
    h.append("</head>")
    h.append("<body>")

    h.append("<h1>安全扫描报告</h1>")
    h.append(f"<p class='meta'>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
             f"| 工具版本: {esc(data.get('tool_version', '-'))} "
             f"| Schema: {esc(data.get('schema_version', '-'))}</p>")

    h.append("<h2>1. 扫描概要</h2>")
    h.append("<table>")
    h.append(f"<tr><th>扫描目标</th><td><code>{esc(scan_info['target'])}</code></td></tr>")
    h.append(f"<tr><th>扫描策略</th><td>{esc(scan_info['strategy'])}</td></tr>")
    filt = scan_info.get("filter")
    filt_str = ", ".join(filt) if filt else "全部类型"
    h.append(f"<tr><th>文件过滤</th><td>{esc(filt_str)}</td></tr>")
    h.append(f"<tr><th>扫描耗时</th><td>{scan_info['elapsed']} 秒</td></tr>")
    h.append(f"<tr><th>文件总数</th><td>{scan_info['total_files']}</td></tr>")
    h.append("</table>")

    h.append('<div class="stats-grid">')
    for key, cls, label in [
        ("safe", "safe", "安全"),
        ("suspicious", "suspicious", "可疑"),
        ("malicious", "malicious", "恶意"),
        ("unchecked", "unchecked", "未能检查"),
    ]:
        h.append(f'<div class="stat-card {cls}"><div class="count">{stats[key]}</div>'
                 f'<div class="label">{label}</div></div>')
    h.append("</div>")

    def render_file_cards(items, card_cls, alert_cls, alert_text, level_filter):
        if not items:
            h.append(f'<div class="alert-safe">{alert_text}</div>')
            return
        h.append(f'<div class="{alert_cls}">{len(items)} 个文件。</div>')
        for r in items:
            h.append(f'<div class="file-card {card_cls}">')
            h.append(f'<h3>{esc(r["name"])}</h3>')
            h.append(f'<p><strong>路径</strong>: <code>{esc(r["path"])}</code></p>')
            h.append(f'<p><strong>大小</strong>: {format_size(r["size"])} '
                     f'| <strong>扩展名</strong>: {esc(r["ext"]) or "(无)"}'
                     f'| <strong>实际类型</strong>: {esc(r.get("actual_type") or "-")}'
                     f'| <strong>修改时间</strong>: {format_time(r.get("mtime"))}</p>')
            if r.get("sha256"):
                h.append(f'<p><strong>SHA256</strong>: <code>{esc(r["sha256"])}</code></p>')
            h.append(f'<p><strong>判定原因</strong>: {esc(r["reason"])}</p>')
            findings = [f for f in r.get("findings", []) if f["level"] in level_filter]
            if findings:
                h.append("<p><strong>检测详情</strong>:</p>")
                for f in findings:
                    cls = f["level"] if f["level"] in (
                        "malicious", "critical", "high", "suspicious", "medium", "low"
                    ) else "medium"
                    h.append(f'<div class="finding {cls}">'
                             f'<strong>{esc(f["level"].upper())}</strong>: {esc(f["reason"])}'
                             f'</div>')
            h.append("</div>")

    h.append("<h2>2. 恶意文件</h2>")
    render_file_cards(malicious, "malicious", "alert-malicious",
                      "发现恶意文件，建议立即处理！",
                      {"malicious", "critical", "high", "medium", "low", "suspicious"})

    h.append("<h2>3. 可疑文件</h2>")
    render_file_cards(suspicious, "suspicious", "alert-suspicious",
                      "发现可疑文件，建议进一步检查。",
                      {"suspicious", "high", "medium", "low"})

    h.append("<h2>4. 未能检查的文件</h2>")
    if unchecked:
        h.append(f"<p><strong>{len(unchecked)}</strong> 个文件未能完成扫描。</p>")
        h.append("<table><tr><th>文件名</th><th>路径</th><th>原因</th></tr>")
        for r in unchecked:
            h.append(f"<tr><td>{esc(r['name'])}</td>"
                     f"<td><code>{esc(r['path'])}</code></td>"
                     f"<td>{esc(r['reason'])}</td></tr>")
        h.append("</table>")
    else:
        h.append('<div class="alert-safe">所有文件均已完成扫描。</div>')

    h.append("<h2>5. 安全文件</h2>")
    if safe:
        h.append(f'<div class="alert-safe"><strong>{len(safe)}</strong> 个文件未发现安全风险。</div>')
        show = safe[:100]
        h.append("<details>")
        h.append(f"<summary>展开安全文件列表（共 {len(safe)} 个，展示前 {len(show)} 个）</summary>")
        h.append("<table><tr><th>文件名</th><th>路径</th><th>大小</th><th>修改时间</th></tr>")
        for r in show:
            h.append(f"<tr><td>{esc(r['name'])}</td>"
                     f"<td><code>{esc(r['path'])}</code></td>"
                     f"<td>{format_size(r['size'])}</td>"
                     f"<td>{format_time(r.get('mtime'))}</td></tr>")
        if len(safe) > len(show):
            h.append(f'<tr><td colspan="4" style="text-align:center">'
                     f'... 还有 {len(safe) - len(show)} 个安全文件</td></tr>')
        h.append("</table>")
        h.append("</details>")
    else:
        h.append("<p>无安全文件。</p>")

    h.append("<h2>6. 处理建议</h2>")
    h.append("<ul>")
    if malicious:
        h.append("<li><strong>恶意文件</strong>: 立即断网，备份重要数据，"
                 "使用专业杀毒软件全盘扫描；确认安全前不要执行。</li>")
    if suspicious:
        h.append("<li><strong>可疑文件</strong>: 上传到 VirusTotal 或在沙箱中分析，"
                 "确认无害后再决定去留。</li>")
    if unchecked:
        h.append("<li><strong>未能检查的文件</strong>: 检查权限与文件完整性；"
                 "关键目录建议以管理员权限重扫。</li>")
    if not (malicious or suspicious or unchecked):
        h.append("<li>本次扫描未发现安全风险。建议定期重复扫描并保持系统更新。</li>")
    h.append("</ul>")
    h.append('<p class="meta">注意: 本工具仅基于静态特征做初步检测，'
             '不等同于专业杀毒软件。对于重要系统，建议配合专业安全产品使用。</p>')

    h.append('<div class="footer">')
    h.append(f'<p>Security Scanner Report | 目标: {esc(scan_info["target"])} '
             f'| 策略: {esc(scan_info["strategy"])} '
             f'| {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
    h.append("</div>")

    h.append("</body></html>")
    return "\n".join(h)


def main():
    parser = argparse.ArgumentParser(
        description="Security Scanner - 报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="扫描结果 JSON 文件路径")
    parser.add_argument("--format", choices=["md", "html"], default="md",
                        help="报告格式（默认: md）")
    parser.add_argument("--output", required=True, help="报告输出路径")
    args = parser.parse_args()

    data = load_results(args.input)
    report = (generate_markdown_report(data) if args.format == "md"
              else generate_html_report(data))

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"报告已生成: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
