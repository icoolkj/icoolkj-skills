# 故障排查与质量检查

## 常见问题

### 数据加载失败

**症状**：`FileNotFoundError` 或 `ValueError: Unsupported format`

**排查**：
1. 确认文件路径正确
2. 确认文件格式在支持列表中：CSV、Excel（.xlsx/.xls）、JSON、JSONL
3. Excel 文件需要 pandas + openpyxl：`pip install pandas openpyxl`
4. 检查文件编码（CSV 推荐 UTF-8）

### 图表生成失败

**症状**：`[FAIL] Export chart failed` 或图表区域空白

**排查**：
1. 确认 matplotlib 已安装：`pip install matplotlib`
2. 检查 chart_config 的 type 是否在支持列表中
3. 检查 data 字段是否包含必需的数据（labels/values 等）
4. 中文字体问题：安装中文字体或使用英文标签

### 合规检查不通过

**症状**：`[FAIL] 数据完整度过低` 或 `[FAIL] 包含敏感/绝对化用语`

**解决**：
- 数据完整度低于 50%：清洗数据或补充缺失值
- 包含 URL：将链接移至 references 字段
- 包含绝对化用语：移除"最佳"、"最强"、"第一"等词汇
- 章节缺少必填字段：补全 id、title、content_type、style

### PDF 导出失败

**症状**：`[WARN] WeasyPrint not installed` 或 PDF 导出报错

**解决**：
1. 安装 WeasyPrint：`pip install weasyprint`
2. Linux 需要系统依赖：`sudo apt install libpango-1.0-0 libpangoft2-1.0-0`
3. 如果无法安装 WeasyPrint，使用 HTML 格式替代

### HTML 样式未生效

**症状**：HTML 报告看起来没有风格配色

**排查**：
1. 检查 report.json 的 style 字段是否正确
2. 确认 style ID 在 10 种预设风格中
3. 检查 composed.json 的 style_profile 是否完整

## 质量检查清单

报告生成完成后，逐项检查：

- [ ] **数据加载**：数据行数和列数与预期一致
- [ ] **合规检查**：通过所有合规检查项
- [ ] **图表**：每个 chart 类型章节都有对应的 PNG 图表
- [ ] **风格**：报告视觉风格与用户选择一致
- [ ] **Markdown**：文件非空，章节结构完整
- [ ] **HTML**：CSS 变量注入正确，图表引用路径正确
- [ ] **PDF**（如有）：文件可正常打开，排版正确
- [ ] **KPI 卡片**：数值显示正确，单位正确
- [ ] **表格**：表头和数据行对齐，无溢出

## 性能优化

- 大数据集（>10万行）建议先采样再分析
- 图表生成是主要耗时步骤，可用 `--force-charts` 控制是否重新生成
- PDF 导出比 HTML 慢，大报告建议先输出 HTML
- 多节报告的图表可以并行生成（未来优化方向）

## 目录结构

```
work/my-report/
├── report.json          # 报告配置（输入）
├── composed.json        # 组装后的完整数据
├── report.md            # Markdown 输出
├── report.html          # HTML 输出
├── report.pdf           # PDF 输出（可选）
├── charts/              # 图表 PNG 文件
│   ├── col_1.png
│   ├── col_2.png
│   └── ...
└── data/                # 原始数据副本（可选）
```
