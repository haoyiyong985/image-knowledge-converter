#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试SmartDocumentGenerator"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from datetime import datetime
import re

# 模拟 SmartDocumentGenerator 的初始化
output_dir = Path('处理结果')
merger = None  # 跳过merger初始化

class TestGenerator:
    def __init__(self, output_dir='处理结果'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.generated_docs = set()
        
    def _get_doc_key(self, theme, doc_name):
        safe_name = re.sub(r'[<>:"/\\|?*]', '', doc_name)
        if len(safe_name) > 25:
            safe_name = safe_name[:25]
        return f"{theme}/{safe_name}"
    
    def is_doc_generated(self, theme, doc_name):
        return self._get_doc_key(theme, doc_name) in self.generated_docs
    
    def mark_doc_generated(self, theme, doc_name):
        self.generated_docs.add(self._get_doc_key(theme, doc_name))

# 测试
gen = TestGenerator()

# 模拟处理流程
test_cases = [
    ("历史文化", "文学日著"),
    ("历史文化", "太祖第四子"),
    ("历史文化", "一张图看完明朝276年历史下"),
    ("历史文化", "更多直播"),  # 这个应该合并到"一张图看完明朝276年历史下"
    ("历史文化", "太后她和昌平君有着非常紧密"),
    ("历史文化", "查一下明末钱穆斋的历史"),
    ("综合知识", "小厚看展指北"),
    ("综合知识", "小厚看展指北"),  # 重复
    ("综合知识", "小厚看展指北"),  # 重复
]

for theme, doc_name in test_cases:
    key = gen._get_doc_key(theme, doc_name)
    is_gen = gen.is_doc_generated(theme, doc_name)
    print(f"{theme}/{doc_name}: key={key}, generated={is_gen}")
    if not is_gen:
        gen.mark_doc_generated(theme, doc_name)
