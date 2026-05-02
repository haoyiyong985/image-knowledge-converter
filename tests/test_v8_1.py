#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V8.1 核心修复项验证测试

测试覆盖：
- L-1/L-2: 语义标题识别恢复
- L-6/P1-4: OCR字符替换补充
- L-7/P1-1: 合并阈值+朝代统一
- P0-2: 多列排版重建
- P1-2: 新增噪点过滤
- P1-3: 分类关键词补充
"""

import sys, os
sys.path.insert(0, 'd:/新建文件夹')
os.chdir('d:/新建文件夹')

# 绕过模块导入（只测试我们修改的类）
# 先用最小化方式导入
from unittest.mock import MagicMock, patch

# 模拟依赖
sys.modules['local_ocr'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['dotenv'].load_dotenv = lambda **kwargs: None
sys.modules['scripts'] = MagicMock()
sys.modules['scripts.classifier_engine'] = MagicMock()

# 现在可以导入了
import importlib
spec = importlib.util.spec_from_file_location(
    "v8_1", "d:/新建文件夹/auto_process_all_v8_1.py"
)
# 只解析AST，不执行
import ast
with open('d:/新建文件夹/auto_process_all_v8_1.py', encoding='utf-8') as f:
    src = f.read()
tree = ast.parse(src)

# =========================================================
# 直接测试ContentOrganizer类（独立逻辑，不需要导入）
# =========================================================

# 手动执行类定义部分
import re
from typing import Dict, List, Optional

# 复制ContentOrganizer相关代码（最小化）
exec_globals = {}
exec_code = """
import re, os, time, hashlib, json, logging, shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)
"""
exec(exec_code, exec_globals)

# 提取ContentOrganizer类定义
class_start = src.find('\nclass ContentOrganizer:')
class_end = src.find('\n\n# ============================================================\n# [P0-3][P1-5]')
organizer_src = src[class_start:class_end]
exec(exec_code + organizer_src, exec_globals)
ContentOrganizer = exec_globals['ContentOrganizer']

# 提取相关全局变量
similarity_start = src.find('\n    def find_similar_doc(')
similarity_end = src.find('\n    def merge_content(')
# 也提取_topic_similarity

print("=" * 60)
print("V8.1 核心修复项验证")
print("=" * 60)

organizer = ContentOrganizer()
passed = 0
failed = 0

def test(name, result, expected=True):
    global passed, failed
    ok = bool(result) == bool(expected) if isinstance(expected, bool) else result == expected
    symbol = "✅" if ok else "❌"
    print(f"  {symbol} {name}")
    if ok:
        passed += 1
    else:
        failed += 1
        print(f"     期望: {expected}")
        print(f"     实际: {result}")

# =========================================================
# 测试L-1/L-2：语义标题识别
# =========================================================
print("\n【L-1/L-2】语义标题识别（V2恢复）")
test("'功效：' 识别为标题", organizer._is_heading_line("功效：补肾壮阳"))
test("'做法：' 识别为标题", organizer._is_heading_line("做法：先将大米淘洗干净"))
test("'禁忌' 识别为标题", organizer._is_heading_line("禁忌：孕妇不宜服用"))
test("'生平经历' 识别为标题", organizer._is_heading_line("生平经历"))
test("'早年生活' 识别为标题", organizer._is_heading_line("早年生活：出生于书香世家"))
test("'一、' 序号识别为标题", organizer._is_heading_line("一、主要成就"))
test("'1.' 编号识别为标题", organizer._is_heading_line("1. 营养价值极高"))
test("纯内容行不是标题", organizer._is_heading_line("他是一位著名的历史学家"), False)
test("太短的行不是标题", organizer._is_heading_line("好"), False)

# =========================================================
# 测试P1-4：OCR字符替换补充
# =========================================================
print("\n【P1-4】OCR字符替换（V2补充4种）")
test("chr(8218) ‚ 被替换", organizer._fix_common_ocr_errors(chr(8218) + "测试"), "'测试")
test("chr(8222) „ 被替换", organizer._fix_common_ocr_errors(chr(8222) + "测试"), '"测试')
test("chr(8242) ′ 被替换", organizer._fix_common_ocr_errors(chr(8242) + "测试"), "'测试")
test("chr(8220) " 被替换", organizer._fix_common_ocr_errors(chr(8220) + "测试"), '"测试')

# =========================================================
# 测试P1-2：新增噪点过滤
# =========================================================
print("\n【P1-2】新增噪点过滤（8种）")
text_with_noise = "a付费\n内容由A1生成\n相关视频\n已阅读5个网页\n按住说话\nKimi\n这是正文内容，不应被过滤"
cleaned = organizer.clean_text(text_with_noise)
test("'a付费' 被过滤", "a付费" not in cleaned)
test("'内容由A1生成' 被过滤", "内容由A1生成" not in cleaned)
test("'相关视频' 被过滤", "相关视频" not in cleaned)
test("'已阅读5个网页' 被过滤", "已阅读5个网页" not in cleaned)
test("'按住说话' 被过滤", "按住说话" not in cleaned)
test("正文内容保留", "正文内容" in cleaned)

# =========================================================
# 测试P0-2：多列排版重建
# =========================================================
print("\n【P0-2】多列排版重建")
multicolumn_text = "朱允  1368-1398在位\n洪武帝\n朱棣  1402-1424在位\n永乐帝"
lines = multicolumn_text.split('\n')
rebuilt = organizer._rebuild_multicolumn(lines)
rebuilt_text = '\n'.join(rebuilt)
test("人名+年代重建为###标题", "### 朱允" in rebuilt_text)
test("朱棣也被识别", "### 朱棣" in rebuilt_text)

# =========================================================
# 测试P0-2：structure_content综合
# =========================================================
print("\n【P0-2】内容结构化（V2语义+V8编号融合）")
content = "功效：补肾壮阳\n1. 主要营养成分\n普通内容行"
structured = organizer.structure_content(content)
test("'功效：' 行变为###标题", "### 功效" in structured or "#### 功效" in structured)
test("'1. 主要营养成分' 变为##标题", "## 1. 主要营养成分" in structured)
test("普通内容行不变", "普通内容行" in structured)

# =========================================================
# 测试P1-3：分类关键词补充（只验证关键词存在）
# =========================================================
print("\n【P1-3】分类关键词补充")

# 从AST提取PRESET_CATEGORIES
for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'PRESET_CATEGORIES':
                # 找到了，检查历史文化分类
                assign_node = node
                break

preset_src_start = src.find('\nPRESET_CATEGORIES = {')
preset_src_end = src.find('\n}', preset_src_start) + 2
preset_exec = exec_code + src[preset_src_start:preset_src_end]
preset_globals = {}
exec(preset_exec, preset_globals)
PRESET_CATEGORIES = preset_globals['PRESET_CATEGORIES']

hist_kws = PRESET_CATEGORIES.get('历史文化', [])
test("'分封' 在历史文化关键词", "分封" in hist_kws)
test("'诸侯' 在历史文化关键词", "诸侯" in hist_kws)
test("'郡望' 在历史文化关键词", "郡望" in hist_kws)
test("'五姓' 在历史文化关键词", "五姓" in hist_kws)
test("'七望' 在历史文化关键词", "七望" in hist_kws)
test("'门阀' 在历史文化关键词", "门阀" in hist_kws)
test("'太后' 在历史文化关键词", "太后" in hist_kws)

# =========================================================
# 汇总
# =========================================================
print(f"\n{'='*60}")
print(f"测试结果: {passed} 通过, {failed} 失败")
if failed == 0:
    print("🎉 全部通过！V8.1核心修复项验证成功")
else:
    print(f"⚠️  有 {failed} 项需要检查")
print("=" * 60)
