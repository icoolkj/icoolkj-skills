# 内容质量评估集

质量评估必须使用人工标注的真实素材，不能把规则分数当作质量结论。每条样本使用 JSONL 记录，字段如下：

```json
{"id":"sample-001","source":"原始资料文件名或来源登记","facts_supported":["F1","F3"],"topic_pairs_independent":["T1|T2"],"risks_detected":["时效风险","单一来源"],"notes":"人工裁决依据"}
```

- `facts_supported`：人工判断事实是否被原文引用、限定词和来源共同支持。
- `topic_pairs_independent`：只记录核心问题、受众和增量都明显独立的选题对。
- `risks_detected`：人工确认应被提示的风险类型，而不是关键词命中数。
- `notes`：记录争议、标注者和复核者，不把不确定样本强行二分类。

`evaluation/seed_gold.jsonl` 只包含用于跑通评估器的最小示例，不代表真实素材质量基线。接入真实素材后，至少由两名标注者独立标注，计算一致性并由第三人裁决冲突。

运行：

```bash
python scripts/evaluate_quality.py --gold evaluation/seed_gold.jsonl --predictions predictions.jsonl
```

输出分别报告事实支持、选题独立性和风险识别的 precision、recall、F1。模型或规则升级时应保留旧版本结果进行回归比较。
