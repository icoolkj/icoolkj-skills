#!/usr/bin/env python3
"""
Security Scanner - 报告生成器
将扫描结果 JSON 转换为可读的 Markdown 或 HTML 报告。

用法:
    python report.py --input <结果JSON路径> --format <md|html> --output <报告路径>
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_results(input_path):
    """加载扫描结果 JSON"""
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_markdown_report(data):
    """生成 Markdown 格式报告"""
    scan_info = data["scan_info"]
    stats = data["stats"]
    results = data["results"]

    lines = []
    lines.append("# 安全扫描报告")
    lines.append("")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 1. 扫描概要
    lines.append("## 1. 扫描概要")
    lines.append("")
    lines.append(f"| 项目 | 内容 |")
    lines.append(f"|------|------|")
    lines.append(f"| 扫描目标 | `{scan_info['target']}` |")
    lines.append(f"| 扫描策略 | {scan_info['strategy']} |")
    lines.append(f"| 文件过滤 | {scan_info['filter'] if scan_info['filter'] else '全部类型'} |")
    lines.append(f"| 扫描耗时 | {scan_info['elapsed']} 秒 |")
    lines.append(f"| 文件总数 | {scan_info['total_files']} |")
    lines.append("")

    # 统计摘要
    lines.append("### 扫描统计")
    lines.append("")
    lines.append(f"| 分类 | 数量 | 占比 |")
    lines.append(f"|------|------|------|")
    total = stats["total"] if stats["total"] > 0 else 1
    lines.append(f"| 安全 | {stats['safe']} | {stats['safe']/total*100:.1f}% |")
    lines.append(f"| 可疑 | {stats['suspicious']} | {stats['suspicious']/total*100:.1f}% |")
    lines.append(f"| 恶意 | {stats['malicious']} | {stats['malicious']/total*100:.1f}% |")
    lines.append(f"| 未能检查 | {stats['unchecked']} | {stats['unchecked']/total*100:.1f}% |")
    lines.append("")

    # 2. 恶意文件（优先展示）
    malicious = [r for r in results if r["classification"] == "malicious"]
    lines.append("## 2. 恶意文件")
    lines.append("")
    if malicious:
        lines.append(f"> 发现 **{len(malicious)}** 个恶意文件，建议立即处理！")
        lines.append("")
        for r in malicious:
            lines.append(f"### {r['name']}")
            lines.append(f"- **路径**: `{r['path']}`")
            lines.append(f"- **大小**: {format_size(r['size'])}")
            lines.append(f"- **扩展名**: {r['ext']}")
            if r.get("sha256"):
                lines.append(f"- **SHA256**: `{r['sha256']}`")
            lines.append(f"- **判定原因**: {r['reason']}")
            lines.append(f"- **检测详情**:")
            for finding in r["findings"]:
                if finding["level"] in ("malicious", "critical"):
                    lines.append(f"  - **{finding['level'].upper()}**: {finding['reason']}")
            lines.append("")
    else:
        lines.append("> 未发现恶意文件。")
        lines.append("")

    # 3. 可疑文件
    suspicious = [r for r in results if r["classification"] == "suspicious"]
    lines.append("## 3. 可疑文件")
    lines.append("")
    if suspicious:
        lines.append(f"> 发现 **{len(suspicious)}** 个可疑文件，建议进一步检查。")
        lines.append("")
        for r in suspicious:
            lines.append(f"### {r['name']}")
            lines.append(f"- **路径**: `{r['path']}`")
            lines.append(f"- **大小**: {format_size(r['size'])}")
            lines.append(f"- **扩展名**: {r['ext']}")
            if r.get("sha256"):
                lines.append(f"- **SHA256**: `{r['sha256']}`")
            lines.append(f"- **判定原因**: {r['reason']}")
            lines.append(f"- **检测详情**:")
            for finding in r["findings"]:
                if finding["level"] in ("suspicious", "high", "medium"):
                    lines.append(f"  - **{finding['level'].upper()}**: {finding['reason']}")
            lines.append("")
    else:
        lines.append("> 未发现可疑文件。")
        lines.append("")

    # 4. 未能检查的文件
    unchecked = [r for r in results if r["classification"] == "unchecked"]
    lines.append("## 4. 未能检查的文件")
    lines.append("")
    if unchecked:
        lines.append(f"> **{len(unchecked)}** 个文件未能完成扫描。")
        lines.append("")
        lines.append("| 文件名 | 路径 | 原因 |")
        lines.append("|--------|------|------|")
        for r in unchecked:
            lines.append(f"| {r['name']} | `{r['path']}` | {r['reason']} |")
        lines.append("")
    else:
        lines.append("> 所有文件均已完成扫描。")
        lines.append("")

    # 5. 安全文件（摘要）
    safe = [r for r in results if r["classification"] == "safe"]
    lines.append("## 5. 安全文件")
    lines.append("")
    if safe:
        lines.append(f"> **{len(safe)}** 个文件未发现安全风险。")
        lines.append("")
        if len(safe) <= 20:
            lines.append("| 文件名 | 路径 | 大小 |")
            lines.append("|--------|------|------|")
            for r in safe:
                lines.append(f"| {r['name']} | `{r['path']}` | {format_size(r['size'])} |")
        else:
            lines.append(f"> 文件数量较多（{len(safe)} 个），仅展示前 20 个：")
            lines.append("")
            lines.append("| 文件名 | 路径 | 大小 |")
            lines.append("|--------|------|------|")
            for r in safe[:20]:
                lines.append(f"| {r['name']} | `{r['path']}` | {format_size(r['size'])} |")
            lines.append(f"| ... | 还有 {len(safe) - 20} 个安全文件 | |")
        lines.append("")

    # 建议
    lines.append("## 6. 处理建议")
    lines.append("")
    if malicious:
        lines.append("- **恶意文件**: 建议立即删除或使用专业杀毒软件处理。不要执行这些文件。")
    if suspicious:
        lines.append("- **可疑文件**: 建议上传到 [VirusTotal](https://www.virustotal.com) 进行进一步分析，或使用专业杀毒软件扫描。")
    if unchecked:
        lines.append("- **未能检查的文件**: 检查文件权限或文件是否损坏，必要时手动检查。")
    if not malicious and not suspicious and not unchecked:
        lines.append("- 本次扫描未发现安全风险。建议定期重复扫描以保持安全。")
    lines.append("")
    lines.append("> **注意**: 本工具仅提供基于静态特征的初步检测，不等同于专业杀毒软件的全面防护。对于重要系统，建议配合专业安全软件使用。")

    return "\n".join(lines)


def generate_html_report(data):
    """生成 HTML 格式报告"""
    scan_info = data["scan_info"]
    stats = data["stats"]
    results = data["results"]

    malicious = [r for r in results if r["classification"] == "malicious"]
    suspicious = [r for r in results if r["classification"] == "suspicious"]
    unchecked = [r for r in results if r["classification"] == "unchecked"]
    safe = [r for r in results if r["classification"] == "safe"]

    html = []
    html.append("<!DOCTYPE html>")
    html.append('<html lang="zh-CN">')
    html.append("<head>")
    html.append('<meta charset="UTF-8">')
    html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html.append("<title>安全扫描报告</title>")
    html.append("<style>")
    html.append("""
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 960px; margin: 0 auto; padding: 20px; color: #333; }
        h1 { color: #1a1a2e; border-bottom: 3px solid #16213e; padding-bottom: 10px; }
        h2 { color: #16213e; margin-top: 30px; }
        h3 { color: #0f3460; }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
        th { background: #16213e; color: white; }
        tr:nth-child(even) { background: #f8f9fa; }
        .malicious { color: #dc3545; font-weight: bold; }
        .suspicious { color: #ffc107; font-weight: bold; }
        .safe { color: #28a745; }
        .unchecked { color: #6c757d; }
        .alert-malicious { background: #f8d7da; border: 1px solid #dc3545; border-radius: 8px;
                          padding: 15px; margin: 10px 0; }
        .alert-suspicious { background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
                           padding: 15px; margin: 10px 0; }
        .alert-safe { background: #d4edda; border: 1px solid #28a745; border-radius: 8px;
                     padding: 15px; margin: 10px 0; }
        .file-card { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .file-card.malicious { border-color: #dc3545; background: #fff5f5; }
        .file-card.suspicious { border-color: #ffc107; background: #fff8e1; }
        .finding { margin: 5px 0; padding: 5px 10px; border-radius: 4px; }
        .finding.malicious { background: #f8d7da; }
        .finding.high { background: #fff3cd; }
        .finding.medium { background: #e2e3e5; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }
        .stat-card { text-align: center; padding: 20px; border-radius: 8px; }
        .stat-card.safe { background: #d4edda; color: #155724; }
        .stat-card.suspicious { background: #fff3cd; color: #856404; }
        .stat-card.malicious { background: #f8d7da; color: #721c24; }
        .stat-card.unchecked { background: #e2e3e5; color: #383d41; }
        .stat-card .count { font-size: 2em; font-weight: bold; }
        .stat-card .label { font-size: 0.9em; }
        code { background: #f1f1f1; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
        .path { word-break: break-all; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #dee2e6;
                 color: #6c757d; font-size: 0.85em; }
    """)
    html.append("</style>")
    html.append("</head>")
    html.append("<body>")

    # 标题
    html.append("<h1>安全扫描报告</h1>")
    html.append(f"<p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

    # 1. 扫描概要
    html.append("<h2>1. 扫描概要</h2>")
    html.append("<table>")
    html.append(f"<tr><th>扫描目标</th><td><code class='path'>{scan_info['target']}</code></td></tr>")
    html.append(f"<tr><th>扫描策略</th><td>{scan_info['strategy']}</td></tr>")
    html.append(f"<tr><th>文件过滤</th><td>{scan_info['filter'] if scan_info['filter'] else '全部类型'}</td></tr>")
    html.append(f"<tr><th>扫描耗时</th><td>{scan_info['elapsed']} 秒</td></tr>")
    html.append(f"<tr><th>文件总数</th><td>{scan_info['total_files']}</td></tr>")
    html.append("</table>")

    # 统计卡片
    total = stats["total"] if stats["total"] > 0 else 1
    html.append('<div class="stats-grid">')
    html.append(f'<div class="stat-card safe"><div class="count">{stats["safe"]}</div><div class="label">安全</div></div>')
    html.append(f'<div class="stat-card suspicious"><div class="count">{stats["suspicious"]}</div><div class="label">可疑</div></div>')
    html.append(f'<div class="stat-card malicious"><div class="count">{stats["malicious"]}</div><div class="label">恶意</div></div>')
    html.append(f'<div class="stat-card unchecked"><div class="count">{stats["unchecked"]}</div><div class="label">未能检查</div></div>')
    html.append('</div>')

    # 2. 恶意文件
    html.append("<h2>2. 恶意文件</h2>")
    if malicious:
        html.append(f'<div class="alert-malicious">发现 <strong>{len(malicious)}</strong> 个恶意文件，建议立即处理！</div>')
        for r in malicious:
            html.append(f'<div class="file-card malicious">')
            html.append(f'<h3 class="malicious">{r["name"]}</h3>')
            html.append(f'<p><strong>路径</strong>: <code class="path">{r["path"]}</code></p>')
            html.append(f'<p><strong>大小</strong>: {format_size(r["size"])} | <strong>扩展名</strong>: {r["ext"]}</p>')
            if r.get("sha256"):
                html.append(f'<p><strong>SHA256</strong>: <code>{r["sha256"]}</code></p>')
            html.append(f'<p><strong>判定原因</strong>: {r["reason"]}</p>')
            html.append('<p><strong>检测详情</strong>:</p>')
            for finding in r["findings"]:
                if finding["level"] in ("malicious", "critical"):
                    html.append(f'<div class="finding malicious">**{finding["level"].upper()}**: {finding["reason"]}</div>')
            html.append('</div>')
    else:
        html.append('<div class="alert-safe">未发现恶意文件。</div>')

    # 3. 可疑文件
    html.append("<h2>3. 可疑文件</h2>")
    if suspicious:
        html.append(f'<div class="alert-suspicious">发现 <strong>{len(suspicious)}</strong> 个可疑文件，建议进一步检查。</div>')
        for r in suspicious:
            html.append(f'<div class="file-card suspicious">')
            html.append(f'<h3 class="suspicious">{r["name"]}</h3>')
            html.append(f'<p><strong>路径</strong>: <code class="path">{r["path"]}</code></p>')
            html.append(f'<p><strong>大小</strong>: {format_size(r["size"])} | <strong>扩展名</strong>: {r["ext"]}</p>')
            if r.get("sha256"):
                html.append(f'<p><strong>SHA256</strong>: <code>{r["sha256"]}</code></p>')
            html.append(f'<p><strong>判定原因</strong>: {r["reason"]}</p>')
            html.append('<p><strong>检测详情</strong>:</p>')
            for finding in r["findings"]:
                if finding["level"] in ("suspicious", "high", "medium"):
                    cls = finding["level"] if finding["level"] in ("malicious", "high", "medium") else "medium"
                    html.append(f'<div class="finding {cls}">**{finding["level"].upper()}**: {finding["reason"]}</div>')
            html.append('</div>')
    else:
        html.append('<div class="alert-safe">未发现可疑文件。</div>')

    # 4. 未能检查
    html.append("<h2>4. 未能检查的文件</h2>")
    if unchecked:
        html.append(f'<p><strong>{len(unchecked)}</strong> 个文件未能完成扫描。</p>')
        html.append("<table>")
        html.append("<tr><th>文件名</th><th>路径</th><th>原因</th></tr>")
        for r in unchecked:
            html.append(f'<tr><td>{r["name"]}</td><td><code class="path">{r["path"]}</code></td><td>{r["reason"]}</td></tr>')
        html.append("</table>")
    else:
        html.append('<div class="alert-safe">所有文件均已完成扫描。</div>')

    # 5. 安全文件
    html.append("<h2>5. 安全文件</h2>")
    if safe:
        html.append(f'<div class="alert-safe"><strong>{len(safe)}</strong> 个文件未发现安全风险。</div>')
        html.append("<table>")
        html.append("<tr><th>文件名</th><th>路径</th><th>大小</th></tr>")
        show_count = min(len(safe), 20)
        for r in safe[:show_count]:
            html.append(f'<tr><td class="safe">{r["name"]}</td><td><code class="path">{r["path"]}</code></td><td>{format_size(r["size"])}</td></tr>')
        if len(safe) > 20:
            html.append(f'<tr><td colspan="3" style="text-align:center">... 还有 {len(safe) - 20} 个安全文件</td></tr>')
        html.append("</table>")
    else:
        html.append('<p>无安全文件。</p>')

    # 6. 建议
    html.append("<h2>6. 处理建议</h2>")
    html.append("<ul>")
    if malicious:
        html.append("<li><strong>恶意文件</strong>: 建议立即删除或使用专业杀毒软件处理。不要执行这些文件。</li>")
    if suspicious:
        html.append("<li><strong>可疑文件</strong>: 建议上传到 VirusTotal 进行进一步分析，或使用专业杀毒软件扫描。</li>")
    if unchecked:
        html.append("<li><strong>未能检查的文件</strong>: 检查文件权限或文件是否损坏，必要时手动检查。</li>")
    if not malicious and not suspicious and not unchecked:
        html.append("<li>本次扫描未发现安全风险。建议定期重复扫描以保持安全。</li>")
    html.append("</ul>")
    html.append('<p style="color:#6c757d;font-size:0.85em;">注意: 本工具仅提供基于静态特征的初步检测，不等同于专业杀毒软件的全面防护。对于重要系统，建议配合专业安全软件使用。</p>')

    html.append('<div class="footer">')
    html.append(f'<p>Security Scanner Report | 扫描目标: {scan_info["target"]} | 策略: {scan_info["strategy"]} | {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>')
    html.append('</div>')

    html.append("</body>")
    html.append("</html>")

    return "\n".join(html)


def format_size(size_bytes):
    """格式化文件大小"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def main():
    parser = argparse.ArgumentParser(
        description="Security Scanner - 报告生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="扫描结果JSON文件路径")
    parser.add_argument("--format", choices=["md", "html"], default="md", help="报告格式（默认: md）")
    parser.add_argument("--output", required=True, help="报告输出路径")

    args = parser.parse_args()

    data = load_results(args.input)

    if args.format == "md":
        report = generate_markdown_report(data)
    else:
        report = generate_html_report(data)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"报告已生成: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
