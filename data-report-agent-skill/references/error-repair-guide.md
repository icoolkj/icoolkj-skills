# 常见报错修复指引

用户将本地脚本报错信息粘贴回对话后，Agent 按以下指引修复 report.json。

## 数据加载失败

**报错**：`FileNotFoundError` 或 `ValueError: Unsupported format`

**修复**：
1. 确认 `data_source` 路径正确（相对路径相对于 work_dir）
2. 确认文件格式在支持列表中：CSV、Excel(.xlsx/.xls)、JSON、JSONL
3. Excel 文件需要 pandas + openpyxl：`pip install pandas openpyxl`
4. 检查 CSV 文件编码（推荐 UTF-8）

## 图表生成失败

**报错**：`[FAIL] Export chart failed` 或图表区域空白

**修复**：
1. 确认 matplotlib 已安装：`pip install matplotlib`
2. 检查 `chart_config.type` 是否在支持列表中（bar/line/pie/scatter/histogram/area）
3. 检查 `chart_config.data` 是否包含必需字段：
   - bar: labels + values
   - line: labels + series 或 values
   - pie: labels + values
   - histogram: values
   - scatter: x_values + y_values
   - area: labels + values
4. 中文字体问题：安装中文字体或使用英文标签

## 合规检查不通过

**报错**：`[FAIL] 数据完整度过低` 或 `[FAIL] 包含敏感/绝对化用语`

**修复**：
- 数据完整度低于 50%：提醒用户清洗数据或补充缺失值
- 包含 URL：将链接移至 data_source 字段
- 包含绝对化用语：替换"最佳"→"优秀"、"第一"→"前列"等
- 章节缺少必填字段：补全 id、title、content_type、style

## PDF 导出失败

**报错**：`[WARN] reportlab PDF export failed` 或 PDF 导出报错

**修复**：
1. 安装 reportlab：`pip install reportlab`（推荐，纯 Python）
2. 如 reportlab 失败，尝试 WeasyPrint：`pip install weasyprint`
3. 如两者都不可用，使用 HTML 格式替代

## Schema 校验失败

**报错**：`第N节缺少必填字段: xxx` 或 `content_type 无效`

**修复**：
1. 补全缺失的必填字段（id/title/content_type/style）
2. 修正 content_type 为合法值（text/summary/chart/table/kpi/image）
3. 修正 chart_config.type 为合法值（bar/line/pie/scatter/histogram/area）
4. chart 类型章节必须有 chart_config 和 data

## HTML 样式未生效

**报错**：HTML 报告看起来没有风格配色

**修复**：
1. 检查 report.json 的 style 字段是否正确（10 种之一）
2. 确认每节 style 字段与顶层 style 一致
3. 检查 composed.json 的 style_profile 是否完整

## 流水线执行命令参考

```bash
# 基本执行
python scripts/run_pipeline.py report.json --work-dir ./output

# 指定输出格式
python scripts/run_pipeline.py report.json --work-dir ./output --formats markdown html pdf

# 启用 LLM 自动补写
python scripts/run_pipeline.py report.json --work-dir ./output --llm --api-key "sk-..."

# 强制重新生成图表
python scripts/run_pipeline.py report.json --work-dir ./output --force-charts

# 跳过最终验证
python scripts/run_pipeline.py report.json --work-dir ./output --skip-verify
```
