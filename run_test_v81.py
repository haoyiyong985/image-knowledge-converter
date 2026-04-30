#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, os, re, ast, logging
sys.path.insert(0, 'd:/新建文件夹')
os.chdir('d:/新建文件夹')

with open('auto_process_all_v8_1.py', encoding='utf-8') as f:
    src = f.read()

tree = ast.parse(src)
exec_code = (
    'import re, os, time, hashlib, json, logging, shutil\n'
    'from pathlib import Path\n'
    'from datetime import datetime\n'
    'from typing import Optional, List, Dict, Tuple\n'
    'from collections import Counter, defaultdict\n'
    'logger = logging.getLogger(__name__)\n'
)

g = {}
exec(exec_code, g)
class_start = src.find('\nclass ContentOrganizer:')
class_end_marker = '\n\n# ============================================================\n# [P0-3][P1-5]'
class_end = src.find(class_end_marker)
organizer_src = src[class_start:class_end]
exec(exec_code + organizer_src, g)
CO = g['ContentOrganizer']
o = CO()

passed = 0
failed = 0
def t(name, result, expected=True):
    global passed, failed
    ok = bool(result) == bool(expected)
    sym = 'PASS' if ok else 'FAIL'
    print(f'  [{sym}] {name}')
    if ok:
        passed += 1
    else:
        failed += 1
        print(f'     got: {repr(result)}')

print('=== L-1/L-2 语义标题识别（V2恢复）===')
t('功效 is heading', o._is_heading_line('功效：补肾壮阳'))
t('做法 is heading', o._is_heading_line('做法：先将大米淘洗干净'))
t('禁忌 is heading', o._is_heading_line('禁忌：孕妇不宜服用'))
t('生平经历 is heading', o._is_heading_line('生平经历'))
t('早年生活 is heading', o._is_heading_line('早年生活：出生于书香世家'))
t('一序号 is heading', o._is_heading_line('一、主要成就'))
t('1.编号 is heading', o._is_heading_line('1. 营养价值极高'))
t('纯内容行 not heading', o._is_heading_line('他是一位著名的历史学家'), False)
t('太短不是标题', o._is_heading_line('好'), False)

print('\n=== P1-4 OCR字符替换（V2补充）===')
r1 = o._fix_common_ocr_errors(chr(8218) + '测试')
t('chr(8218) 被替换为单引号', r1 == "'" + '测试')
r2 = o._fix_common_ocr_errors(chr(8222) + '测试')
t('chr(8222) 被替换为双引号', r2 == '"' + '测试')
r3 = o._fix_common_ocr_errors(chr(8242) + '测试')
t('chr(8242) 被替换为单引号', r3 == "'" + '测试')
r4 = o._fix_common_ocr_errors(chr(8220) + '测试')
t('chr(8220) 被替换为双引号', r4 == '"' + '测试')

print('\n=== P1-2 新增噪点过滤 ===')
noise_lines = ['a付费', '内容由A1生成', '相关视频', '已阅读5个网页', '按住说话', 'Kimi', '这是正文内容不应被过滤']
noise_txt = '\n'.join(noise_lines)
cleaned = o.clean_text(noise_txt)
t('a付费被过滤', 'a付费' not in cleaned)
t('内容由A1生成被过滤', '内容由A1生成' not in cleaned)
t('相关视频被过滤', '相关视频' not in cleaned)
t('已阅读5个网页被过滤', '已阅读5个网页' not in cleaned)
t('按住说话被过滤', '按住说话' not in cleaned)
t('正文内容保留', '正文内容' in cleaned)

print('\n=== P0-2 多列排版重建 ===')
lines = ['朱允  1368-1398在位', '洪武帝', '朱棣  1402-1424在位', '永乐帝']
rebuilt = o._rebuild_multicolumn(lines)
rt = '\n'.join(rebuilt)
print('  重建结果:', repr(rt))
t('朱允+年代重建为标题', '### 朱允' in rt)
t('朱棣也被识别', '### 朱棣' in rt)

print('\n=== P0-2 structure_content（V2语义+V8编号融合）===')
content = '功效：补肾壮阳\n1. 主要营养成分\n普通内容行'
structured = o.structure_content(content)
print('  结构化结果:')
for line in structured.split('\n'):
    print('   ', repr(line))
t('功效行变标题', '### 功效' in structured or '#### 功效' in structured)
t('1.编号行变##标题', '## 1. 主要营养成分' in structured)
t('普通行不变', '普通内容行' in structured)

print('\n=== P1-1 _topic_similarity朝代统一+去后缀 ===')
# 构造SmartDocumentManager测试
smart_dm_start = src.find('\nclass SmartDocumentManager:')
smart_dm_end = src.find('\n\n# ============================================================\n# [P1-4] 图片归档器')
smart_dm_src = src[smart_dm_start:smart_dm_end]
g2 = {}
exec(exec_code + smart_dm_src, g2)
SDM = g2['SmartDocumentManager']
# 不能实例化（需要文件系统），只测试_topic_similarity
dm = object.__new__(SDM)
sim1 = SDM._topic_similarity(dm, '明朝历史(上)', '明朝历史(下)')
t('明朝上+下相似度>=0.6', sim1 >= 0.6)
print(f'  明朝上+下相似度: {sim1:.2f}')
sim2 = SDM._topic_similarity(dm, '北宋历史', '南宋历史')
t('北宋+南宋相似度>=0.8（朝代统一）', sim2 >= 0.8)
print(f'  北宋+南宋相似度: {sim2:.2f}')
sim3 = SDM._topic_similarity(dm, '钱谦益', '钱谦益传')
t('钱谦益+钱谦益传相似度>=0.9（去后缀）', sim3 >= 0.9)
print(f'  钱谦益+钱谦益传相似度: {sim3:.2f}')

print('\n=== P1-3 分类关键词补充 ===')
preset_start = src.find('\nPRESET_CATEGORIES = {')
preset_end = src.find('\n}', preset_start) + 2
pg = {}
exec(exec_code + src[preset_start:preset_end], pg)
PC = pg['PRESET_CATEGORIES']
hist = PC.get('历史文化', [])
for kw in ['分封', '诸侯', '郡望', '五姓', '七望', '门阀', '太后']:
    t(f'{kw} 在历史文化关键词', kw in hist)

print(f'\n{"="*50}')
print(f'测试结果: {passed} 通过, {failed} 失败')
if failed == 0:
    print('全部通过！V8.1核心修复项验证成功')
else:
    print(f'有 {failed} 项需要检查')
