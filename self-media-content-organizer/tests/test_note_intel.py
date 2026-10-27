#!/usr/bin/env python3
"""
NoteIntel - pytest 单元测试
覆盖核心脚本的关键函数：analyze_material, validate_pack, score_topics,
extract_candidates, scan_risks
"""

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from analyze_material import (
    count_words, split_sentences, split_paragraphs, clean_text,
    count_facts, check_has_data, check_has_case, check_has_method,
    calculate_repeat_ratio, calculate_topic_independence,
    count_verifiable_conclusions, check_has_comparison, check_has_trend,
    calculate_data_diversity, calculate_logic_coherence,
    calculate_viewpoint_balance, calculate_information_freshness,
    evaluate_density, determine_mode, generate_quotas,
    load_config, DEFAULT_CONFIG
)
from validate_pack import (
    check_structure_complete, check_no_placeholders, check_quotes_traceable,
    check_facts_within_quota, check_topic_has_dimensions,
    check_topic_fact_references, check_summary_length,
    check_topic_title_uniqueness, check_facts_have_quotes,
    check_no_fabricated_data, check_optional_section_content,
    validate
)
from score_topics import (
    score_angle, score_audience, score_form, score_difficulty,
    score_related_facts, score_topic, get_recommendation,
    AUDIENCE_ALIASES
)
from extract_candidates import (
    classify_candidate, extract_candidates, filter_by_quota
)
from scan_risks import (
    scan_unverified_data, scan_subjective_opinion, scan_sensitive_topic,
    scan_time_risk, scan_single_source, scan_risks
)


# ============================================================
# analyze_material.py 测试
# ============================================================

class TestCountWords:
    def test_chinese_only(self):
        assert count_words("短视频平台用户行为") == 9

    def test_english_only(self):
        assert count_words("hello world test") == 3

    def test_mixed(self):
        assert count_words("AI市场规模3800亿美元") == 8

    def test_empty(self):
        assert count_words("") == 0


class TestSplitSentences:
    def test_chinese_periods(self):
        result = split_sentences("这是第一句话内容。这是第二句话内容！这是第三句话内容？")
        assert len(result) == 3

    def test_empty(self):
        assert split_sentences("") == []

    def test_short_filtered(self):
        result = split_sentences("啊。很长的一句话在这里")
        assert len(result) == 1


class TestSplitParagraphs:
    def test_multiple_paragraphs(self):
        text = "这是第一段的内容，足够长。\n\n这是第二段的内容，足够长。\n\n这是第三段的内容，足够长。"
        assert len(split_paragraphs(text)) == 3

    def test_single_paragraph(self):
        assert len(split_paragraphs("这是一段足够长的内容文字")) == 1


class TestCleanText:
    def test_windows_line_endings(self):
        assert "\r" not in clean_text("line1\r\nline2\r")

    def test_extra_spaces(self):
        assert "  " not in clean_text("text  with   spaces")

    def test_multiple_newlines(self):
        assert "\n\n\n" not in clean_text("a\n\n\n\nb")


class TestCountFacts:
    def test_with_numbers(self):
        sentences = ["2025年销量达到950万辆", "同比增长37%"]
        assert count_facts(sentences) == 2

    def test_no_facts(self):
        sentences = ["这是一段普通叙述", "没有数据"]
        assert count_facts(sentences) == 0

    def test_proper_noun_with_keyword(self):
        sentences = ["比亚迪市场渗透率突破40%"]
        assert count_facts(sentences) >= 1


class TestCheckHasData:
    def test_has_percentage(self):
        assert check_has_data("增长37%") is True

    def test_has_money(self):
        assert check_has_data("投资1200亿美元") is True

    def test_no_data(self):
        assert check_has_data("这是一段叙述") is False


class TestCheckHasCase:
    def test_has_keyword(self):
        assert check_has_case("例如，比亚迪销量领先") is True

    def test_has_quotes(self):
        assert check_has_case("\u201c引用内容\u201d") is True

    def test_no_case(self):
        assert check_has_case("普通叙述没有引用") is False


class TestCheckHasMethod:
    def test_has_method_keyword(self):
        assert check_has_method("第一步是明确目标") is True

    def test_no_method(self):
        assert check_has_method("2025年销量增长") is False


class TestDetermineMode:
    def test_concise_by_word_count(self):
        assert determine_mode(500, 0.5) == "concise"

    def test_standard_by_word_count(self):
        assert determine_mode(1500, 0.5) == "standard"

    def test_deep_by_word_count(self):
        assert determine_mode(4000, 0.5) == "deep"

    def test_high_density_upgrade_concise(self):
        assert determine_mode(500, 0.8) == "standard"

    def test_high_density_upgrade_standard(self):
        assert determine_mode(1500, 0.8) == "deep"

    def test_low_density_downgrade_standard(self):
        assert determine_mode(1500, 0.2) == "concise"

    def test_low_density_downgrade_deep(self):
        assert determine_mode(4000, 0.2) == "standard"

    def test_mid_density_upgrade_with_factors(self):
        factors = {"fact_count": 5, "data_diversity": 4}
        assert determine_mode(500, 0.65, factors) == "standard"

    def test_mid_density_no_upgrade_without_factors(self):
        assert determine_mode(500, 0.65) == "concise"

    def test_boundary_750_850_high_density(self):
        assert determine_mode(800, 0.6) == "standard"

    def test_boundary_2900_3100_low_density(self):
        assert determine_mode(3000, 0.3) == "standard"

    def test_boundary_2900_3100_high_density(self):
        assert determine_mode(3000, 0.8) == "deep"

    def test_example_concise_values(self):
        assert determine_mode(520, 0.58) == "concise"

    def test_example_standard_values(self):
        assert determine_mode(1850, 0.75) == "standard"

    def test_example_deep_values(self):
        assert determine_mode(4500, 0.82) == "deep"

    def test_with_custom_config(self):
        config = dict(DEFAULT_CONFIG)
        config["mode_thresholds"] = dict(DEFAULT_CONFIG["mode_thresholds"])
        config["mode_thresholds"]["concise_max_words"] = 500
        assert determine_mode(600, 0.5, config=config) == "standard"


class TestGenerateQuotas:
    def test_concise_quotas(self):
        q = generate_quotas("concise")
        assert q["core_facts"] == "2-4"
        assert q["topics"] == "1-2"

    def test_standard_quotas(self):
        q = generate_quotas("standard")
        assert q["core_facts"] == "4-8"
        assert q["topics"] == "3-5"

    def test_deep_quotas(self):
        q = generate_quotas("deep")
        assert q["core_facts"] == "6-12"
        assert q["topics"] == "4-7"


class TestLoadConfig:
    def test_default_config(self):
        config = load_config("/nonexistent/path")
        assert "density_weights" in config
        assert "mode_thresholds" in config
        assert config["density_weights"]["fact_count"] == 0.18

    def test_config_from_file(self):
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        if os.path.isfile(config_path):
            config = load_config(config_path)
            assert "density_weights" in config
            assert "mode_thresholds" in config


class TestEvaluateDensity:
    def test_data_rich_text(self):
        text = "2025年销量达到950万辆，同比增长37%。市场渗透率突破40%。"
        sentences = split_sentences(text)
        paragraphs = split_paragraphs(text)
        score, factors = evaluate_density(text, sentences, paragraphs)
        assert 0 < score <= 1.0
        assert factors["fact_count"] >= 2
        assert factors["has_data"] is True

    def test_narrative_text(self):
        text = "短视频创作需要明确定位。内容质量比设备更重要。坚持更新是关键。"
        sentences = split_sentences(text)
        paragraphs = split_paragraphs(text)
        score, factors = evaluate_density(text, sentences, paragraphs)
        assert 0 < score <= 1.0
        assert factors["has_data"] is False


# ============================================================
# validate_pack.py 测试
# ============================================================

class TestCheckStructureComplete:
    def test_all_sections_present(self):
        content = "## 摘要\n内容\n## 核心事实\n内容\n## 创作选题\n内容"
        ok, errors = check_structure_complete(content)
        assert ok is True
        assert len(errors) == 0

    def test_missing_section(self):
        content = "## 摘要\n内容\n## 核心事实\n内容"
        ok, errors = check_structure_complete(content)
        assert ok is False
        assert any("创作选题" in e for e in errors)


class TestCheckNoPlaceholders:
    def test_no_placeholders(self):
        ok, errors = check_no_placeholders("正常内容没有占位符")
        assert ok is True

    def test_has_placeholders(self):
        ok, errors = check_no_placeholders("内容包含 {placeholder}")
        assert ok is False
        assert len(errors) == 1


class TestCheckNoFabricatedData:
    SOURCE = "数据显示，2025年短视频平台用户日均使用时长已达到120分钟，较去年增长15%。"

    def test_valid_quote(self):
        content = '## 核心事实\n\n1. 事实\n   📍 定位\n   📎 原文引用："数据显示，2025年短视频平台用户日均使用时长已达到120分钟，较去年增长15%。"'
        ok, errors = check_no_fabricated_data(content, self.SOURCE)
        assert ok is True

    def test_fabricated_quote(self):
        content = '## 核心事实\n\n1. 事实\n   📍 定位\n   📎 原文引用："完全虚构的内容不在原文中"'
        ok, errors = check_no_fabricated_data(content, self.SOURCE)
        assert ok is False
        assert len(errors) == 1

    def test_ellipsis_valid(self):
        content = '## 核心事实\n\n1. 事实\n   📍 定位\n   📎 原文引用："数据显示[...]已达到120分钟"'
        ok, errors = check_no_fabricated_data(content, self.SOURCE)
        assert ok is True

    def test_ellipsis_partial_fabricated(self):
        content = '## 核心事实\n\n1. 事实\n   📍 定位\n   📎 原文引用："虚构片段[...]已达到120分钟"'
        ok, errors = check_no_fabricated_data(content, self.SOURCE)
        assert ok is False

    def test_unicode_quotes(self):
        content = '## 核心事实\n\n1. 事实\n   📍 定位\n   📎 原文引用：\u201c虚构内容不在原文中\u201d'
        ok, errors = check_no_fabricated_data(content, self.SOURCE)
        assert ok is False

    def test_no_source_text(self):
        ok, errors = check_no_fabricated_data("any content", None)
        assert ok is True


class TestCheckSummaryLength:
    def test_valid_length(self):
        content = "## 摘要\n\n" + "这是一段合适长度的摘要内容，字数在合理范围内。" * 2
        ok, warnings = check_summary_length(content)
        assert ok is True

    def test_too_short(self):
        content = "## 摘要\n\n太短"
        ok, warnings = check_summary_length(content)
        assert ok is False

    def test_too_long(self):
        content = "## 摘要\n\n" + "这是一段非常长的摘要内容" * 50
        ok, warnings = check_summary_length(content)
        assert ok is False


class TestCheckTopicTitleUniqueness:
    def test_unique_titles(self):
        content = "## 创作选题\n\n1. **标题A**\n   - 切入角度：数据冲击\n2. **标题B**\n   - 切入角度：对比反差"
        ok, errors = check_topic_title_uniqueness(content)
        assert ok is True

    def test_duplicate_titles(self):
        content = "## 创作选题\n\n1. **相同标题**\n   - 切入角度：数据冲击\n2. **相同标题**\n   - 切入角度：对比反差"
        ok, errors = check_topic_title_uniqueness(content)
        assert ok is False


class TestValidateExamples:
    @pytest.mark.parametrize("example_file", [
        "example-concise.md",
        "example-standard.md",
        "example-deep.md",
    ])
    def test_example_valid(self, example_file):
        examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
        pack_path = os.path.join(examples_dir, example_file)
        if os.path.isfile(pack_path):
            result = validate(pack_path)
            assert result["valid"] is True, f"{example_file} validation failed: {result['errors']}"


# ============================================================
# score_topics.py 测试
# ============================================================

class TestScoreAngle:
    def test_high_value(self):
        score, desc = score_angle("数据冲击")
        assert score == 3

    def test_medium_value(self):
        score, desc = score_angle("因果追溯")
        assert score == 2

    def test_low_value(self):
        score, desc = score_angle("方法拆解")
        assert score == 1

    def test_unknown(self):
        score, desc = score_angle("未知角度")
        assert score == 1


class TestScoreAudience:
    def test_high_spread(self):
        assert score_audience("普通消费者")[0] == 3
        assert score_audience("媒体创作者")[0] == 3

    def test_medium_spread(self):
        assert score_audience("投资者")[0] == 2
        assert score_audience("决策者")[0] == 2
        assert score_audience("行业从业者")[0] == 2

    def test_low_spread(self):
        assert score_audience("学习者")[0] == 1
        assert score_audience("研究者")[0] == 1

    def test_alias_mapping(self):
        assert score_audience("投资者/决策者")[0] == 2
        assert score_audience("学习者/研究者")[0] == 1

    def test_unknown(self):
        assert score_audience("未知受众")[0] == 1


class TestScoreForm:
    def test_high_spread(self):
        assert score_form("短视频")[0] == 3
        assert score_form("图文卡片")[0] == 3

    def test_medium_spread(self):
        assert score_form("图文长文")[0] == 2

    def test_low_spread(self):
        assert score_form("系列内容")[0] == 1
        assert score_form("直播访谈")[0] == 1


class TestScoreDifficulty:
    def test_easy(self):
        assert score_difficulty("图文卡片")[0] == 1
        assert score_difficulty("短视频")[0] == 1

    def test_medium(self):
        assert score_difficulty("图文长文")[0] == 2

    def test_hard(self):
        assert score_difficulty("系列内容")[0] == 3
        assert score_difficulty("直播访谈")[0] == 3


class TestScoreRelatedFacts:
    def test_no_refs(self):
        assert score_related_facts("", 5)[0] == 1

    def test_valid_refs(self):
        assert score_related_facts("#1,#3", 5)[0] == 2

    def test_many_refs(self):
        assert score_related_facts("#1,#2,#3", 5)[0] == 3

    def test_invalid_ref(self):
        assert score_related_facts("#10", 5)[0] == 1


class TestGetRecommendation:
    def test_strong_recommend(self):
        assert "强烈推荐" in get_recommendation(2.8)

    def test_recommend(self):
        assert "推荐" in get_recommendation(2.2)

    def test_optional(self):
        assert "可选" in get_recommendation(1.7)

    def test_defer(self):
        assert "暂缓" in get_recommendation(1.2)


# ============================================================
# extract_candidates.py 测试
# ============================================================

class TestClassifyCandidate:
    def test_data_comparison(self):
        ctype, priority = classify_candidate("销量同比增长37%，远超去年")
        assert priority == 3

    def test_data_fact(self):
        ctype, priority = classify_candidate("2025年销量达到950万辆")
        assert priority >= 2

    def test_no_candidate(self):
        ctype, priority = classify_candidate("这是一段普通叙述")
        assert ctype is None


class TestExtractCandidates:
    def test_data_rich_text(self):
        text = "2025年销量达到950万辆，同比增长37%。\n\n市场渗透率突破40%。"
        candidates = extract_candidates(text)
        assert len(candidates) >= 2
        assert all("location" in c for c in candidates)
        assert all("type" in c for c in candidates)

    def test_narrative_text(self):
        text = "短视频创作需要明确定位。内容质量比设备更重要。"
        candidates = extract_candidates(text)
        assert len(candidates) >= 0


class TestFilterByQuota:
    def test_quota_limit(self):
        candidates = [
            {"priority": 3, "paragraph": 1, "sentence": 1},
            {"priority": 3, "paragraph": 1, "sentence": 2},
            {"priority": 2, "paragraph": 2, "sentence": 1},
            {"priority": 1, "paragraph": 3, "sentence": 1},
        ]
        filtered = filter_by_quota(candidates, 2)
        assert len(filtered) == 2
        assert all(c["priority"] == 3 for c in filtered)


# ============================================================
# scan_risks.py 测试
# ============================================================

class TestScanUnverifiedData:
    def test_detected(self):
        text = "预计2025年销量突破1200万辆"
        paragraphs = split_paragraphs(text)
        risks = scan_unverified_data(text, [], paragraphs)
        assert len(risks) == 1
        assert risks[0]["type"] == "未经证实的数据"

    def test_not_detected(self):
        text = "2025年销量达到950万辆"
        paragraphs = split_paragraphs(text)
        risks = scan_unverified_data(text, [], paragraphs)
        assert len(risks) == 0


class TestScanSubjectiveOpinion:
    def test_detected(self):
        text = "我认为应该加大投资力度"
        paragraphs = split_paragraphs(text)
        risks = scan_subjective_opinion(text, [], paragraphs)
        assert len(risks) == 1
        assert risks[0]["type"] == "主观观点"

    def test_not_detected(self):
        text = "2025年销量达到950万辆"
        paragraphs = split_paragraphs(text)
        risks = scan_subjective_opinion(text, [], paragraphs)
        assert len(risks) == 0


class TestScanSensitiveTopic:
    def test_detected(self):
        text = "涉及政治敏感话题的内容"
        paragraphs = split_paragraphs(text)
        risks = scan_sensitive_topic(text, [], paragraphs)
        assert len(risks) >= 1


class TestScanTimeRisk:
    def test_old_data(self):
        text = "2018年数据显示销量增长"
        paragraphs = split_paragraphs(text)
        risks = scan_time_risk(text, [], paragraphs)
        assert len(risks) >= 1
        assert risks[0]["type"] == "时效风险"

    def test_recent_data(self):
        text = "2025年数据显示销量增长"
        paragraphs = split_paragraphs(text)
        risks = scan_time_risk(text, [], paragraphs)
        assert len(risks) == 0


class TestScanSingleSource:
    def test_always_present(self):
        risks = scan_single_source("any text")
        assert len(risks) == 1
        assert risks[0]["type"] == "单一来源"


class TestScanRisks:
    def test_multiple_risk_types(self):
        text = "预计2025年销量突破1200万辆。我认为应该加大投资。2018年数据显示增长。"
        risks = scan_risks(text)
        types = [r["type"] for r in risks]
        assert "未经证实的数据" in types
        assert "主观观点" in types
        assert "时效风险" in types
        assert "单一来源" in types


# ============================================================
# 端到端测试：示例文件验证
# ============================================================

class TestEndToEnd:
    def test_all_examples_valid(self):
        examples_dir = os.path.join(os.path.dirname(__file__), '..', 'examples')
        for example_file in ["example-concise.md", "example-standard.md", "example-deep.md"]:
            pack_path = os.path.join(examples_dir, example_file)
            if os.path.isfile(pack_path):
                result = validate(pack_path)
                assert result["valid"] is True, f"{example_file}: {result['errors']}"

    def test_determine_mode_consistency(self):
        assert determine_mode(520, 0.58) == "concise"
        assert determine_mode(1850, 0.75) == "standard"
        assert determine_mode(4500, 0.82) == "deep"