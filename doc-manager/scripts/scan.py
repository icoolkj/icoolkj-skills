#!/usr/bin/env python3
"""doc-manager scan.py — 扫描目录，提取文件元数据和摘要"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SUPPORTED_TEXT_EXT = {'.md', '.txt', '.json', '.html', '.csv'}
SUPPORTED_DOC_EXT = {'.docx'}
SUPPORTED_PDF_EXT = {'.pdf'}
SUPPORTED_IMG_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg'}
SUPPORTED_SLIDE_EXT = {'.pptx'}
SUPPORTED_SHEET_EXT = {'.xlsx'}
SUMMARY_LENGTH = 500


def get_file_type(ext):
    ext = ext.lower()
    if ext in SUPPORTED_TEXT_EXT:
        return 'text'
    if ext in SUPPORTED_DOC_EXT:
        return 'word'
    if ext in SUPPORTED_PDF_EXT:
        return 'pdf'
    if ext in SUPPORTED_IMG_EXT:
        return 'image'
    if ext in SUPPORTED_SLIDE_EXT:
        return 'slides'
    if ext in SUPPORTED_SHEET_EXT:
        return 'spreadsheet'
    return 'other'


def extract_text_summary(filepath, max_chars=SUMMARY_LENGTH):
    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.md':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_chars * 2)
            lines = content.split('\n')
            summary_lines = []
            char_count = 0
            for line in lines:
                if char_count >= max_chars:
                    break
                summary_lines.append(line)
                char_count += len(line)
            return '\n'.join(summary_lines)[:max_chars]
        elif ext == '.txt':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_chars)
        elif ext == '.json':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_chars * 2)
            return content[:max_chars]
        elif ext == '.html':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(max_chars * 3)
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:max_chars]
        elif ext == '.csv':
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                return f.read(max_chars)
        elif ext == '.docx':
            try:
                from docx import Document
                doc = Document(filepath)
                paragraphs = []
                char_count = 0
                for p in doc.paragraphs:
                    if char_count >= max_chars:
                        break
                    if p.text.strip():
                        paragraphs.append(p.text)
                        char_count += len(p.text)
                return '\n'.join(paragraphs)[:max_chars]
            except ImportError:
                return '[python-docx not installed, content not extracted]'
        elif ext == '.pdf':
            try:
                import subprocess
                result = subprocess.run(
                    ['python3', '-c', f"""
import sys
try:
    import fitz
    doc = fitz.open('{filepath}')
    text = ''
    for page in doc:
        text += page.get_text()
        if len(text) >= {max_chars}:
            break
    print(text[:{max_chars}])
except ImportError:
    print('[PyMuPDF not installed, content not extracted]')
"""],
                    capture_output=True, text=True, timeout=10
                )
                return result.stdout.strip()[:max_chars] if result.stdout else '[PDF content extraction failed]'
            except Exception:
                return '[PDF content extraction failed]'
        elif ext == '.pptx':
            try:
                from pptx import Presentation
                prs = Presentation(filepath)
                texts = []
                char_count = 0
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, 'text') and shape.text.strip():
                            texts.append(shape.text)
                            char_count += len(shape.text)
                            if char_count >= max_chars:
                                break
                    if char_count >= max_chars:
                        break
                return '\n'.join(texts)[:max_chars]
            except ImportError:
                return '[python-pptx not installed, content not extracted]'
        elif ext == '.xlsx':
            try:
                from openpyxl import load_workbook
                wb = load_workbook(filepath, read_only=True)
                texts = []
                char_count = 0
                for ws in wb.worksheets:
                    for row in ws.iter_rows(max_row=20, values_only=True):
                        for cell in row:
                            if cell is not None:
                                texts.append(str(cell))
                                char_count += len(str(cell))
                                if char_count >= max_chars:
                                    break
                        if char_count >= max_chars:
                            break
                    if char_count >= max_chars:
                        break
                wb.close()
                return '\n'.join(texts)[:max_chars]
            except ImportError:
                return '[openpyxl not installed, content not extracted]'
    except Exception as e:
        return f'[extraction error: {e}]'
    return ''


def extract_md_images(filepath):
    images = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        for i, match in enumerate(re.finditer(pattern, content), 1):
            alt = match.group(1)
            path = match.group(2)
            images.append({
                'path': path,
                'alt': alt,
                'position': i
            })
    except Exception:
        pass
    return images


def extract_title(filepath, ext, summary):
    if ext == '.md':
        for line in summary.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
            if line.startswith('## '):
                return line[3:].strip()
    if ext == '.html':
        m = re.search(r'<title[^>]*>([^<]+)</title>', summary, re.I)
        if m:
            return m.group(1).strip()
    return Path(filepath).stem


def scan_directory(target_dir, index_dir=None):
    target_path = Path(target_dir).resolve()
    if not target_path.exists():
        print(json.dumps({'error': f'Directory not found: {target_dir}'}), file=sys.stderr)
        sys.exit(1)
    if not target_path.is_dir():
        print(json.dumps({'error': f'Not a directory: {target_dir}'}), file=sys.stderr)
        sys.exit(1)

    if index_dir:
        index_path = Path(index_dir).resolve()
    else:
        index_path = target_path / '.doc-manager'
    index_path.mkdir(parents=True, exist_ok=True)

    skip_dirs = {'.doc-manager', '.git', 'node_modules', '__pycache__', '.venv', 'venv'}

    documents = []
    for root, dirs, files in os.walk(target_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for filename in files:
            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, target_path)
            ext = Path(filename).suffix.lower()
            file_type = get_file_type(ext)
            stat = os.stat(filepath)
            modified_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()

            doc = {
                'id': f'doc-{len(documents) + 1:04d}',
                'path': rel_path,
                'filename': filename,
                'ext': ext,
                'type': file_type,
                'size_bytes': stat.st_size,
                'created_at': created_at,
                'modified_at': modified_at,
            }

            if file_type in ('text', 'word', 'pdf', 'slides', 'spreadsheet'):
                summary = extract_text_summary(filepath)
                doc['summary'] = summary
                doc['title'] = extract_title(filepath, ext, summary)
            elif file_type == 'image':
                doc['summary'] = ''
                doc['title'] = Path(filename).stem
            else:
                doc['summary'] = ''
                doc['title'] = Path(filename).stem

            if ext == '.md':
                doc['images'] = extract_md_images(filepath)
            else:
                doc['images'] = []

            documents.append(doc)

    result = {
        'scan_time': datetime.now().isoformat(),
        'root_path': str(target_path),
        'index_path': str(index_path),
        'total_files': len(documents),
        'documents': documents
    }
    return result


def main():
    parser = argparse.ArgumentParser(
        description='扫描目录，提取文件元数据和摘要，输出 JSON 清单'
    )
    parser.add_argument('target_dir', help='要扫描的目标目录')
    parser.add_argument('--index-dir', default=None, help='索引文件存放目录（默认: <目标目录>/.doc-manager/）')
    parser.add_argument('--output', default=None, help='输出文件路径（默认: stdout）')
    args = parser.parse_args()

    result = scan_directory(args.target_dir, args.index_dir)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f'Scan complete: {result["total_files"]} files found', file=sys.stderr)
        print(f'Output saved to: {args.output}', file=sys.stderr)
        print(f'Index directory: {result["index_path"]}', file=sys.stderr)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()