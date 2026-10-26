#!/usr/bin/env python3
"""
NoteIntel - 素材分析器
输入处理（URL抓取/文件读取/清洗）+ 评估定模（字数+密度+配额表）
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os
from urllib import request, parse
from html.parser import HTMLParser
from datetime import datetime


class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.skip = False
        self.skip_tags = {'script', 'style', 'noscript', 'iframe', 'svg'}
        self.block_tags = {'p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                           'li', 'tr', 'blockquote', 'section', 'article', 'header',
                           'footer', 'main', 'aside', 'figure', 'figcaption'}

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip = True
        if tag in self.block_tags:
            self.result.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags:
            self.skip = False
        if tag in self.block_tags:
            self.result.append('\n')

    def handle_data(self, data):
        if not self.skip:
            self.result.append(data)

    def get_text(self):
        text = ''.join(self.result)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()


def fetch_url(url):
    try:
        req = request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; NoteIntel/1.0)'
        })
        with request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            encoding = resp.headers.get_content_charset() or 'utf-8'
            html = raw.decode(encoding, errors='replace')
        extractor = HTMLTextExtractor()
        extractor.feed(html)
        return extractor.get_text(), 'url'
    except Exception as e:
        print(f"URL抓取失败: {e}", file=sys.stderr)
        sys.exit(1)


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip(), 'file'
    except Exception as e:
        print(f"文件读取失败: {e}", file=sys.stderr)
        sys.exit(1)


def clean_text(text):
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def count_words(text):
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    return chinese_chars + english_words


def split_sentences(text):
    sentences = re.split(r'[。！？；\n]+', text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 3]


def split_paragraphs(text):
    paragraphs = re.split(r'\n{2,}', text)
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]


def count_facts(sentences):
    fact_count = 0
    for s in sentences:
        has_number = bool(re.search(r'\d+[%％]|\d+\.?\d*[亿万千百十]|^\d+', s))
        has_proper_noun = bool(re.search(r'[A-Z][a-z]+|[\u4e00-\u9fff]{2,}(公司|机构|研究|报告|数据)', s))
        has_data_keyword = bool(re.search(r'(达到|增长|下降|占比|超过|约为|同比|环比|首次|突破)', s))
        if has_number or (has_proper_noun and has_data_keyword):
            fact_count += 1
    return fact_count


def check_has_data(text):
    return bool(re.search(r'\d+\.?\d*\s*(%|％|万|亿|千|百|元|吨|辆|人|次|个|家|款|台|份)', text))


def check_has_case(text):
    case_keywords = ['例如', '比如', '案例', '实例', '如：', '举例']
    quote_chars = ['\u201c', '\u201d', '\u2018', '\u2019', '\u300c', '\u300d', '\u300e', '\u300f']
    has_keyword = any(kw in text for kw in case_keywords)
    has_quote = any(qc in text for qc in quote_chars)
    return has_keyword or has_quote


def check_has_method(text):
    method_keywords = ['步骤', '流程', '方法', '策略', '方案', '模式', '框架', '体系',
                       '第一步', '第二步', '首先', '其次', '然后', '最后',
                       'step', 'process', 'method', 'approach']
    return any(kw in text.lower() for kw in method_keywords)


def calculate_repeat_ratio(sentences):
    if len(sentences) < 2:
        return 0.0
    similar_pairs = 0
    total_pairs = 0
    for i in range(len(sentences)):
        for j in range(i + 1, len(sentences)):
            total_pairs += 1
            words_i = set(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', sentences[i]))
            words_j = set(re.findall(r'[\u4e00-\u9fff]|[a-zA-Z]+', sentences[j]))
            if words_i and words_j:
                intersection = words_i & words_j
                union = words_i | words_j
                similarity = len(intersection) / len(union)
                if similarity > 0.5:
                    similar_pairs += 1
    return similar_pairs / total_pairs if total_pairs > 0 else 0.0


def calculate_topic_independence(paragraphs):
    if len(paragraphs) < 2:
        return 1.0
    keyword_sets = []
    for p in paragraphs:
        words = set(re.findall(r'[\u4e00-\u9fff]{2,}', p))
        if words:
            keyword_sets.append(words)
    if len(keyword_sets) < 2:
        return 1.0
    overlaps = []
    for i in range(len(keyword_sets)):
        for j in range(i + 1, len(keyword_sets)):
            intersection = keyword_sets[i] & keyword_sets[j]
            union = keyword_sets[i] | keyword_sets[j]
            if union:
                overlaps.append(1 - len(intersection) / len(union))
    return sum(overlaps) / len(overlaps) if overlaps else 1.0


def count_verifiable_conclusions(sentences):
    conclusion_keywords = ['因此', '所以', '表明', '证明', '说明', '显示', '意味着',
                           '由此', '可见', '可以判断', '可以得出', '证实', '确认']
    count = 0
    for s in sentences:
        if any(kw in s for kw in conclusion_keywords):
            count += 1
    return count


def estimate_creation_angles(fact_count, has_data, has_case, has_method,
                             topic_independence, verifiable_conclusions):
    angles = 0
    if has_data:
        angles += 1
    if has_case:
        angles += 1
    if has_method:
        angles += 1
    if verifiable_conclusions > 0:
        angles += 1
    if topic_independence > 0.6:
        angles += 1
    if fact_count >= 5:
        angles += 1
    return min(angles, 6)


def evaluate_density(text, sentences, paragraphs):
    fact_count = count_facts(sentences)
    has_data = check_has_data(text)
    has_case = check_has_case(text)
    has_method = check_has_method(text)
    repeat_ratio = calculate_repeat_ratio(sentences)
    topic_independence = calculate_topic_independence(paragraphs)
    verifiable_conclusions = count_verifiable_conclusions(sentences)
    creation_angles = estimate_creation_angles(
        fact_count, has_data, has_case, has_method,
        topic_independence, verifiable_conclusions
    )

    score = 0.0
    score += min(fact_count / 8, 1.0) * 0.25
    score += (1.0 if has_data else 0.0) * 0.10
    score += (1.0 if has_case else 0.0) * 0.10
    score += (1.0 if has_method else 0.0) * 0.05
    score += (1.0 - repeat_ratio) * 0.10
    score += topic_independence * 0.20
    score += min(verifiable_conclusions / 3, 1.0) * 0.10
    score += min(creation_angles / 4, 1.0) * 0.10

    density_factors = {
        "fact_count": fact_count,
        "has_data": has_data,
        "has_case": has_case,
        "has_method": has_method,
        "repeat_ratio": round(repeat_ratio, 2),
        "topic_independence": round(topic_independence, 2),
        "verifiable_conclusions": verifiable_conclusions,
        "creation_angles": creation_angles
    }

    return round(score, 2), density_factors


def determine_mode(word_count, density_score):
    if word_count < 800:
        initial = "concise"
    elif word_count <= 3000:
        initial = "standard"
    else:
        initial = "deep"

    if density_score > 0.7:
        if initial == "concise":
            initial = "standard"
        elif initial == "standard":
            initial = "deep"
    elif density_score < 0.3:
        if initial == "deep":
            initial = "standard"
        elif initial == "standard":
            initial = "concise"

    return initial


def generate_quotas(mode):
    if mode == "concise":
        return {
            "summary": 1,
            "core_facts": "2-4",
            "topics": "1-2",
            "quotes": "auto",
            "risks": "auto"
        }
    elif mode == "standard":
        return {
            "summary": 1,
            "core_facts": "4-8",
            "topics": "3-5",
            "quotes": "auto",
            "risks": "auto"
        }
    else:
        return {
            "summary": 1,
            "core_facts": "6-12",
            "topics": "4-7",
            "quotes": "auto",
            "risks": "auto"
        }


def analyze(input_source):
    if input_source.startswith('http://') or input_source.startswith('https://'):
        text, source_type = fetch_url(input_source)
        source = input_source
    elif os.path.isfile(input_source):
        text, source_type = read_file(input_source)
        source = input_source
    else:
        text = input_source
        source_type = "text"
        source = "用户输入文本"

    text = clean_text(text)
    word_count = count_words(text)
    sentences = split_sentences(text)
    paragraphs = split_paragraphs(text)

    density_score, density_factors = evaluate_density(text, sentences, paragraphs)
    mode = determine_mode(word_count, density_score)
    quotas = generate_quotas(mode)

    result = {
        "mode": mode,
        "word_count": word_count,
        "source_type": source_type,
        "source": source,
        "clean_text": text,
        "density_score": density_score,
        "density_factors": density_factors,
        "quotas": quotas,
        "timestamp": datetime.now().isoformat()
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 素材分析器")
    parser.add_argument("--input", required=True, help="输入源：URL、文件路径、或文本")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    args = parser.parse_args()

    result = analyze(args.input)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"分析结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
