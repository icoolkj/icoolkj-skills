#!/usr/bin/env python3
"""
NoteIntel - 素材分析器 v0.3
输入处理（URL抓取/文件读取/清洗）+ 评估定模（字数+密度+配额表）
增强：4个新密度指标、多级密度修正、改进的事实识别和主题分析
零额外依赖，仅使用Python标准库
"""

import argparse
import json
import re
import sys
import os
import shutil
import subprocess
import zipfile
import tempfile
from xml.etree import ElementTree
from collections import Counter
from urllib import request, parse
from html.parser import HTMLParser
from datetime import datetime


DEFAULT_CONFIG = {
    "mode_thresholds": {
        "concise_max_words": 800,
        "standard_max_words": 3000,
        "boundary_low": 750,
        "boundary_high": 850,
        "boundary_standard_low": 2900,
        "boundary_standard_high": 3100
    },
    "density_modifiers": {
        "upgrade_high": 0.75,
        "upgrade_mid": 0.6,
        "downgrade_low": 0.25,
        "downgrade_mid": 0.35,
        "upgrade_mid_fact_threshold": 4,
        "upgrade_mid_diversity_threshold": 3,
        "downgrade_mid_fact_threshold": 5,
        "downgrade_mid_diversity_threshold": 2,
        "downgrade_mid_fact_low": 2,
        "downgrade_mid_diversity_low": 1
    },
    "density_weights": {
        "fact_count": 0.18,
        "has_data": 0.08,
        "has_case": 0.06,
        "has_method": 0.04,
        "repeat_ratio": 0.08,
        "topic_independence": 0.12,
        "verifiable_conclusions": 0.08,
        "creation_angles": 0.08,
        "data_diversity": 0.10,
        "logic_coherence": 0.06,
        "viewpoint_balance": 0.06,
        "info_freshness": 0.06
    },
    "quotas": {
        "concise": {"summary": 1, "core_facts": "2-4", "topics": "1-2", "quotes": "auto", "risks": "auto"},
        "standard": {"summary": 1, "core_facts": "4-8", "topics": "3-5", "quotes": "auto", "risks": "auto"},
        "deep": {"summary": 1, "core_facts": "6-12", "topics": "4-7", "quotes": "auto", "risks": "auto"}
    },
    "fact_count_max_for_density": 8,
    "verifiable_conclusions_max_for_density": 3,
    "creation_angles_max": 6,
    "data_diversity_max": 6
}


def load_config(config_path=None):
    if config_path and os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_path = os.path.join(script_dir, '..', 'config.json')
    if os.path.isfile(default_path):
        with open(default_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return DEFAULT_CONFIG


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


class InputReadError(RuntimeError):
    """Raised when an input exists but cannot be reliably extracted."""


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
        text = extractor.get_text()
        if not text:
            raise InputReadError("网页未提取到正文；可能需要 JavaScript 渲染、登录或人工提供正文")
        return text, 'url', {"completeness": "partial", "renderer": "standard-library-html"}
    except Exception as e:
        raise InputReadError(f"URL抓取失败: {e}") from e


def _decode_pdf_stream(stream_data):
    """解压 PDF 内容流；覆盖 FlateDecode 与 ASCII85+FlateDecode 两种常见编码。"""
    import base64
    import zlib
    data = stream_data
    if data.endswith(b'~>'):
        try:
            return zlib.decompress(base64.a85decode(data[:-2]))
        except Exception:
            pass
    try:
        return zlib.decompress(data)
    except Exception:
        return data


def read_pdf_stream(path):
    """零依赖 PDF 文本抽取兜底：只覆盖未加密、字体未子集化的常见 PDF。

    依赖 pypdf / pdftotext 时优先走它们；本函数用于两者都缺失时尽量拿到正文，
    拿不到就返回空串，由上层决定报错或转 OCR。
    """
    with open(path, 'rb') as f:
        raw = f.read()
    parts = []
    for stream_data in re.findall(b'stream\r?\n(.*?)endstream', raw, re.DOTALL):
        decoded = _decode_pdf_stream(stream_data.rstrip(b'\r\n'))
        if b'Tj' not in decoded and b'TJ' not in decoded:
            continue
        chunks = re.findall(b'\\(([^)]*)\\)\\s*Tj', decoded)
        for arr in re.findall(b'\\[([^\\]]*)\\]\\s*TJ', decoded):
            chunks.extend(re.findall(b'\\(([^)]*)\\)', arr))
        for chunk in chunks:
            try:
                parts.append(chunk.decode('latin-1'))
            except Exception:
                pass
    return ' '.join(parts).strip()


def read_file(path):
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.pdf':
            text, parser = '', ''
            try:
                from pypdf import PdfReader
                text = '\n\n'.join(page.extract_text() or '' for page in PdfReader(path).pages)
                parser = 'pypdf'
            except Exception:
                text = ''
            if not text.strip() and shutil.which('pdftotext'):
                proc = subprocess.run(['pdftotext', '-enc', 'UTF-8', path, '-'],
                                      capture_output=True, text=True, timeout=60)
                if proc.returncode == 0:
                    text, parser = proc.stdout, 'pdftotext'
            if not text.strip():
                text, parser = read_pdf_stream(path), 'pdf-stream'
            if not text.strip():
                if not shutil.which('tesseract') or not shutil.which('pdftoppm'):
                    raise InputReadError("PDF没有可提取文本；可安装 pypdf 或 pdftotext，扫描件另需 tesseract 与 pdftoppm")
                with tempfile.TemporaryDirectory() as work:
                    prefix = os.path.join(work, 'page')
                    render = subprocess.run(['pdftoppm', '-png', '-r', '200', path, prefix], capture_output=True, text=True, timeout=120)
                    if render.returncode:
                        raise InputReadError(render.stderr.strip() or "扫描件 PDF 渲染失败")
                    pages = sorted(os.path.join(work, name) for name in os.listdir(work) if name.endswith('.png'))
                    chunks = []
                    for page in pages:
                        ocr = subprocess.run(['tesseract', page, 'stdout', '-l', 'chi_sim+eng'], capture_output=True, text=True, timeout=120)
                        if ocr.returncode == 0 and ocr.stdout.strip():
                            chunks.append(ocr.stdout)
                    text = '\n\n'.join(chunks)
                    if not text.strip():
                        raise InputReadError("扫描件 PDF OCR 未识别到文字；请人工确认")
                    return text, 'pdf_scanned', {"completeness": "partial", "parser": "pdftoppm+tesseract", "needs_review": True}
            completeness = "full" if parser in ('pypdf', 'pdftotext') else "partial"
            meta = {"completeness": completeness, "parser": parser}
            if completeness == "partial":
                meta["needs_review"] = True
            return text, 'pdf', meta
        if ext == '.docx':
            with zipfile.ZipFile(path) as archive:
                xml = archive.read('word/document.xml')
            root = ElementTree.fromstring(xml)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = []
            for paragraph in root.findall('.//w:p', ns):
                value = ''.join(node.text or '' for node in paragraph.findall('.//w:t', ns))
                if value.strip():
                    paragraphs.append(value)
            text = '\n\n'.join(paragraphs)
            if not text.strip():
                raise InputReadError("DOCX没有可提取正文")
            return text, 'docx', {"completeness": "partial", "parser": "docx-xml", "note": "未提取嵌入图片中的文字"}
        if ext in {'.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp'}:
            if not shutil.which('tesseract'):
                raise InputReadError("图片/OCR解析失败：未找到 tesseract；请安装 OCR 引擎或提供图片文字")
            proc = subprocess.run(['tesseract', path, 'stdout', '-l', 'chi_sim+eng'],
                                  capture_output=True, text=True, timeout=120)
            if proc.returncode:
                raise InputReadError(proc.stderr.strip() or "tesseract OCR失败")
            if not proc.stdout.strip():
                raise InputReadError("OCR未识别到文字；请人工确认图片内容")
            return proc.stdout, 'image', {"completeness": "partial", "parser": "tesseract-ocr", "needs_review": True}
        with open(path, 'r', encoding='utf-8') as f:
            return f.read().strip(), 'file', {"completeness": "full", "parser": "utf-8"}
    except Exception as e:
        if isinstance(e, InputReadError):
            raise
        raise InputReadError(f"文件读取失败: {e}") from e


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


# ============================================================
# 原有密度指标（优化版）
# ============================================================

def count_facts(sentences):
    fact_count = 0
    for s in sentences:
        has_number = bool(re.search(
            r'\d+[%％]|\d+\.?\d*\s*[亿万千百十]|^\d+|\d{4}年', s
        ))
        has_proper_noun = bool(re.search(
            r'[A-Z][a-z]+|[\u4e00-\u9fff]{2,}(公司|机构|研究|报告|数据|集团|品牌|平台|市场|行业|政策|法案)',
            s
        ))
        has_data_keyword = bool(re.search(
            r'(达到|增长|下降|占比|超过|约为|同比|环比|首次|突破|预计|降低|提升|占据|领先|规模|渗透|投资|出口)',
            s
        ))
        has_comparison = bool(re.search(
            r'(相比|对比|高于|低于|多于|少于|相当于|差距|领先|落后| versus|vs)',
            s, re.IGNORECASE
        ))
        if has_number or (has_proper_noun and has_data_keyword) or (has_number and has_comparison):
            fact_count += 1
    return fact_count


def check_has_data(text):
    return bool(re.search(
        r'\d+\.?\d*\s*(%|％|万|亿|千|百|元|吨|辆|人|次|个|家|款|台|份|美元|千瓦时|度)',
        text
    ))


def check_has_case(text):
    case_keywords = ['例如', '比如', '案例', '实例', '如：', '举例', '以...为例', '其中']
    quote_chars = ['\u201c', '\u201d', '\u2018', '\u2019', '\u300c', '\u300d', '\u300e', '\u300f']
    has_keyword = any(kw in text for kw in case_keywords)
    has_quote = any(qc in text for qc in quote_chars)
    return has_keyword or has_quote


def check_has_method(text):
    method_keywords = ['步骤', '流程', '方法', '策略', '方案', '模式', '框架', '体系',
                       '第一步', '第二步', '首先', '其次', '然后', '最后',
                       'step', 'process', 'method', 'approach', '方法论', '路径']
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
                           '由此', '可见', '可以判断', '可以得出', '证实', '确认',
                           '标志着', '反映了', '揭示了', '导致了']
    count = 0
    for s in sentences:
        if any(kw in s for kw in conclusion_keywords):
            count += 1
    return count


def estimate_creation_angles(fact_count, has_data, has_case, has_method,
                             topic_independence, verifiable_conclusions,
                             has_comparison, has_trend):
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
    if has_comparison:
        angles += 1
    if has_trend:
        angles += 1
    return min(angles, 6)


# ============================================================
# 新增密度指标
# ============================================================

def check_has_comparison(text):
    comparison_keywords = ['相比', '对比', '高于', '低于', '多于', '少于',
                           '相当于', '差距', '领先', '落后', ' versus ', 'vs',
                           '同比', '环比', '较', '相比去年', '相比上月']
    return any(kw in text for kw in comparison_keywords)


def check_has_trend(text):
    trend_keywords = ['趋势', '预测', '预计', '未来', '展望', '前景',
                      '将持续', '将增长', '将下降', '将提升', '将突破',
                      '发展方向', '演进', '转型', '升级', '迭代']
    return any(kw in text for kw in trend_keywords)


def calculate_data_diversity(text):
    data_types = 0
    if re.search(r'\d+\.?\d*\s*(%|％)', text):
        data_types += 1
    if re.search(r'\d+\.?\d*\s*(万|亿|千|百)', text):
        data_types += 1
    if re.search(r'\d+\.?\d*\s*(元|美元|千瓦时|度)', text):
        data_types += 1
    if re.search(r'\d+\.?\d*\s*(辆|人|次|个|家|款|台|份|吨)', text):
        data_types += 1
    if re.search(r'\d{4}年', text):
        data_types += 1
    if re.search(r'(第\d+|排名|最大|最小|首位|领先)', text):
        data_types += 1
    return min(data_types, 6)


def calculate_logic_coherence(text, paragraphs):
    if len(paragraphs) < 2:
        return 1.0
    transition_keywords = ['因此', '所以', '然而', '但是', '此外', '另外',
                           '同时', '与此同时', '另一方面', '首先', '其次',
                           '然后', '最后', '总之', '综上', '换言之', '不仅如此',
                           '相比之下', '值得注意的是', '更重要的是']
    transition_count = 0
    for p in paragraphs:
        for kw in transition_keywords:
            if kw in p:
                transition_count += 1
    max_possible = len(paragraphs) * 2
    return min(transition_count / max_possible, 1.0) if max_possible > 0 else 0.0


def calculate_viewpoint_balance(text):
    positive_keywords = ['增长', '提升', '突破', '领先', '成功', '优势', '利好', '进步']
    negative_keywords = ['下降', '降低', '落后', '失败', '劣势', '风险', '挑战', '问题']
    cautionary_keywords = ['但是', '然而', '需要注意', '值得注意', '尽管', '虽然', '不过']
    pos_count = sum(1 for kw in positive_keywords if kw in text)
    neg_count = sum(1 for kw in negative_keywords if kw in text)
    cau_count = sum(1 for kw in cautionary_keywords if kw in text)
    if pos_count + neg_count == 0:
        return 0.0
    balance = 1.0 - abs(pos_count - neg_count) / (pos_count + neg_count)
    if cau_count > 0:
        balance = min(balance + 0.1 * min(cau_count, 3), 1.0)
    return round(balance, 2)


def calculate_information_freshness(text):
    current_year = datetime.now().year
    years_found = re.findall(r'(20\d{2})年', text)
    if not years_found:
        return 0.0
    recent_count = 0
    for y in years_found:
        try:
            if int(y) >= current_year - 2:
                recent_count += 1
        except ValueError:
            continue
    return round(min(recent_count / max(len(years_found), 1), 1.0), 2)


# ============================================================
# 增强的评估和模式判定
# ============================================================

def evaluate_density(text, sentences, paragraphs, config=None):
    if config is None:
        config = DEFAULT_CONFIG
    weights = config["density_weights"]
    fc_max = config.get("fact_count_max_for_density", 8)
    vc_max = config.get("verifiable_conclusions_max_for_density", 3)
    ca_max = config.get("creation_angles_max", 6)
    dd_max = config.get("data_diversity_max", 6)

    fact_count = count_facts(sentences)
    has_data = check_has_data(text)
    has_case = check_has_case(text)
    has_method = check_has_method(text)
    repeat_ratio = calculate_repeat_ratio(sentences)
    topic_independence = calculate_topic_independence(paragraphs)
    verifiable_conclusions = count_verifiable_conclusions(sentences)

    has_comparison = check_has_comparison(text)
    has_trend = check_has_trend(text)
    data_diversity = calculate_data_diversity(text)
    logic_coherence = calculate_logic_coherence(text, paragraphs)
    viewpoint_balance = calculate_viewpoint_balance(text)
    info_freshness = calculate_information_freshness(text)

    creation_angles = estimate_creation_angles(
        fact_count, has_data, has_case, has_method,
        topic_independence, verifiable_conclusions,
        has_comparison, has_trend
    )

    score = 0.0
    score += min(fact_count / fc_max, 1.0) * weights["fact_count"]
    score += (1.0 if has_data else 0.0) * weights["has_data"]
    score += (1.0 if has_case else 0.0) * weights["has_case"]
    score += (1.0 if has_method else 0.0) * weights["has_method"]
    score += (1.0 - repeat_ratio) * weights["repeat_ratio"]
    score += topic_independence * weights["topic_independence"]
    score += min(verifiable_conclusions / vc_max, 1.0) * weights["verifiable_conclusions"]
    score += min(creation_angles / 4, 1.0) * weights["creation_angles"]
    score += min(data_diversity / 4, 1.0) * weights["data_diversity"]
    score += logic_coherence * weights["logic_coherence"]
    score += viewpoint_balance * weights["viewpoint_balance"]
    score += info_freshness * weights["info_freshness"]

    density_factors = {
        "fact_count": fact_count,
        "has_data": has_data,
        "has_case": has_case,
        "has_method": has_method,
        "repeat_ratio": round(repeat_ratio, 2),
        "topic_independence": round(topic_independence, 2),
        "verifiable_conclusions": verifiable_conclusions,
        "creation_angles": creation_angles,
        "has_comparison": has_comparison,
        "has_trend": has_trend,
        "data_diversity": data_diversity,
        "logic_coherence": round(logic_coherence, 2),
        "viewpoint_balance": viewpoint_balance,
        "info_freshness": info_freshness
    }

    return round(score, 2), density_factors


def determine_mode(word_count, density_score, density_factors=None, config=None):
    if config is None:
        config = DEFAULT_CONFIG
    mt = config["mode_thresholds"]
    dm = config["density_modifiers"]

    if word_count < mt["concise_max_words"]:
        initial = "concise"
    elif word_count <= mt["standard_max_words"]:
        initial = "standard"
    else:
        initial = "deep"

    if density_score > dm["upgrade_high"]:
        if initial == "concise":
            initial = "standard"
        elif initial == "standard":
            initial = "deep"
    elif density_score > dm["upgrade_mid"]:
        if initial == "concise" and density_factors:
            if (density_factors.get("fact_count", 0) >= dm["upgrade_mid_fact_threshold"] or
                density_factors.get("data_diversity", 0) >= dm["upgrade_mid_diversity_threshold"]):
                initial = "standard"
    elif density_score < dm["downgrade_low"]:
        if initial == "deep":
            initial = "standard"
        elif initial == "standard":
            initial = "concise"
    elif density_score < dm["downgrade_mid"]:
        if initial == "deep" and density_factors:
            if (density_factors.get("fact_count", 0) < dm["downgrade_mid_fact_threshold"] and
                density_factors.get("data_diversity", 0) < dm["downgrade_mid_diversity_threshold"]):
                initial = "standard"
        if initial == "standard" and density_factors:
            if (density_factors.get("fact_count", 0) < dm["downgrade_mid_fact_low"] and
                density_factors.get("data_diversity", 0) < dm["downgrade_mid_diversity_low"]):
                initial = "concise"

    if mt["boundary_low"] <= word_count <= mt["boundary_high"]:
        if density_score > 0.5:
            initial = "standard"
        elif density_score < 0.3:
            initial = "concise"
    if mt["boundary_standard_low"] <= word_count <= mt["boundary_standard_high"]:
        if density_score < 0.4:
            initial = "standard"
        elif density_score > 0.7:
            initial = "deep"

    return initial


def generate_quotas(mode, config=None):
    if config is None:
        config = DEFAULT_CONFIG
    return dict(config["quotas"][mode])


def analyze(input_source, config=None):
    if config is None:
        config = load_config()

    if input_source.startswith('http://') or input_source.startswith('https://'):
        text, source_type, input_metadata = fetch_url(input_source)
        source = input_source
    elif os.path.isfile(input_source):
        text, source_type, input_metadata = read_file(input_source)
        source = input_source
    else:
        known_file_exts = {'.txt', '.md', '.html', '.htm', '.pdf', '.docx',
                           '.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff', '.bmp'}
        if (os.path.splitext(input_source)[1].lower() in known_file_exts or
                (os.path.sep in input_source and '\n' not in input_source)):
            raise InputReadError(f"输入文件不存在或不可读取: {input_source}")
        text = input_source
        source_type = "text"
        source = "用户输入文本"
        input_metadata = {"completeness": "full", "parser": "direct-text"}

    text = clean_text(text)
    word_count = count_words(text)
    sentences = split_sentences(text)
    paragraphs = split_paragraphs(text)

    density_score, density_factors = evaluate_density(text, sentences, paragraphs, config)
    mode = determine_mode(word_count, density_score, density_factors, config)
    quotas = generate_quotas(mode, config)

    result = {
        "mode": mode,
        "word_count": word_count,
        "source_type": source_type,
        "source": source,
        "input_metadata": input_metadata,
        "limitations": ([input_metadata["note"]] if input_metadata.get("note") else []),
        "clean_text": text,
        "density_score": density_score,
        "density_factors": density_factors,
        "quotas": quotas,
        "timestamp": datetime.now().isoformat()
    }

    return result


def main():
    parser = argparse.ArgumentParser(description="NoteIntel 素材分析器 v0.3")
    parser.add_argument("--input", required=True, help="输入源：URL、文件路径、或文本")
    parser.add_argument("--output", help="输出文件路径（默认输出到stdout）")
    parser.add_argument("--config", help="配置文件路径（默认读取 ../config.json）")
    args = parser.parse_args()

    config = load_config(args.config)
    result = analyze(args.input, config)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"分析结果已写入: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
