#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查同名文档内容"""

from pathlib import Path
import re

result_dir = Path('处理结果')
docs = {}

for sub in sorted(result_dir.iterdir()):
    if sub.is_dir():
        for md in sub.glob('*.md'):
            name = md.stem
            if name not in docs:
                docs[name] = []
            content = md.read_text(encoding='utf-8', errors='ignore')
            # 提取正文内容
            match = re.search(r'CONTENT_START -->\s*(.*?)\s*<!-- CONTENT_END', content, re.DOTALL)
            text = match.group(1) if match else content
            summary = text[:150].replace('\n', ' ').strip()
            docs[name].append({
                'folder': sub.name,
                'file': md.name,
                'summary': summary,
                'full_text': text[:500]
            })

print('=== 同名文档检查 ===\n')
for name, files in sorted(docs.items()):
    if len(files) > 1:
        print(f'【{name}】出现 {len(files)} 次')
        for i, f in enumerate(files):
            print(f'  [{i+1}] 位置: {f["folder"]}/')
            print(f'      内容: {f["summary"][:60]}...')
        print()
