#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P0-4 智能分类器引擎 - 测试脚本"""

import sys
import io
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# 修复 Windows 控制台编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print('=' * 60)
print('P0-4 智能分类器引擎 - 基础测试')
print('=' * 60)

# 测试1: 导入和初始化
print('\n[1] 导入和初始化...')
try:
    from scripts.classifier_engine import ClassifierEngine, ClassificationResult
    engine = ClassifierEngine()
    print(f'    成功加载 {len(engine.categories)} 个分类')
    print('    [PASS]')
except Exception as e:
    print(f'    [FAIL] {e}')
    sys.exit(1)

# 测试2: 基本分类
print('\n[2] 测试分类功能...')
test_cases = [
    ('抗炎饮食金字塔：每天摄入足够的Omega-3', '营养科普'),
    ('宝宝6个月辅食添加指南', '育儿知识'),
    ('中医养生：春季养肝食谱', '中医养生'),
    ('健身房器械使用教程', '健身运动'),
    ('厦门三日游必去景点推荐', '旅游攻略'),
]

passed = 0
for content, expected in test_cases:
    results = engine.classify(content, threshold=0.3)
    if results:
        top = results[0]
        status = '✓' if expected in top.category_name else '○'
        print(f'    {status} "{content[:25]}..."')
        print(f'        → {top.category_name} (置信度: {top.confidence:.2%})')
        if top.matched_keywords:
            print(f'          匹配: {top.matched_keywords}')
        if expected in top.category_name:
            passed += 1

print(f'\n    预期匹配: {passed}/{len(test_cases)}')

# 测试3: 多重分类
print('\n[3] 测试多重分类...')
content = '宝宝辅食：抗炎饮食对婴儿肠道健康的影响'
results = engine.classify(content, threshold=0.2, multi_class=True, max_results=3)
print(f'    内容: {content}')
for r in results:
    print(f'    → {r.category_name} ({r.confidence:.2%})')

# 测试4: 置信度阈值
print('\n[4] 测试置信度阈值...')
content = '测试一些无关内容'
results_low = engine.classify(content, threshold=0.5)
results_high = engine.classify(content, threshold=0.1)
print(f'    内容: {content}')
print(f'    threshold=0.5: {len(results_low)} 个结果')
print(f'    threshold=0.1: {len(results_high)} 个结果')

# 测试5: suggest 方法
print('\n[5] 测试 suggest 方法...')
results = engine.suggest('中医养生', top_k=3)
print(f'    suggest("中医养生"): {results}')

# 测试6: explain_classification
print('\n[6] 测试 explain_classification...')
explanation = engine.explain_classification('抗炎饮食金字塔')
print(f'    分类结果数: {len(explanation["categories"])}')

# 测试7: get_categories
print('\n[7] 测试 get_categories...')
cats = engine.get_categories()
print(f'    分类数量: {len(cats)}')
for cat in cats[:3]:
    print(f'    - {cat["name"]}: {len(cat.get("keywords", []))} 个关键词')

print('\n' + '=' * 60)
print('基础测试完成!')
print('=' * 60)
