#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P2 集成验证测试"""

# 修复 Windows 控制台编码 - 必须放在最前面
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def log(msg):
    print(msg, flush=True)

log('=' * 60)
log('P2 集成验证测试')
log('=' * 60)

# 测试1: 模块导入
log('\n[1] 模块导入测试')
tests = [
    ('init_wizard', 'scripts.init_wizard', 'InitWizard'),
    ('progress_logger', 'scripts.progress_logger', 'ProgressBar'),
    ('interactive_confirm', 'scripts.interactive_confirm', 'InteractiveConfirm'),
    ('auto_batch_processor', 'scripts.auto_batch_processor', 'AutoBatchProcessor'),
    ('ocr_engine', 'scripts.ocr_engine', 'OCREngine'),
    ('classifier_engine', 'scripts.classifier_engine', 'ClassifierEngine'),
]

for name, module, cls in tests:
    try:
        mod = __import__(module, fromlist=[cls])
        getattr(mod, cls)
        log(f'    {name}: OK')
    except Exception as e:
        log(f'    {name}: FAIL - {type(e).__name__}')

# 测试2: 功能测试
log('\n[2] 功能测试')

try:
    from scripts.progress_logger import ProgressBar, StructuredLogger
    bar = ProgressBar(total=5, prefix='测试', show_current=True)
    for i in range(1, 6):
        bar.update(i, f'test_{i}.jpg')
    bar.finish()
    log('    ProgressBar: OK')
except Exception as e:
    log(f'    ProgressBar: FAIL - {e}')

try:
    from scripts.interactive_confirm import InteractiveConfirm, CategoryCandidate
    auto_confirm = InteractiveConfirm(auto_confirm=True)
    result = auto_confirm.confirm_category(
        'test.jpg', '测试',
        [CategoryCandidate('测试.md', 0.8)],
        threshold=0.5
    )
    log(f'    InteractiveConfirm: OK (返回: {result})')
except Exception as e:
    log(f'    InteractiveConfirm: FAIL - {e}')

# 测试3: 分类器测试
log('\n[3] 分类器测试')
try:
    from scripts.classifier_engine import ClassifierEngine
    classifier = ClassifierEngine()
    test_text = '宝宝辅食添加指南'
    result = classifier.classify(test_text, threshold=0.3)
    if result:
        log(f'    分类结果: {result[0].category_name} ({result[0].confidence:.0%})')
    else:
        log('    分类结果: 无匹配')
    log('    ClassifierEngine: OK')
except Exception as e:
    log(f'    ClassifierEngine: FAIL - {e}')

log('\n' + '=' * 60)
log('集成验证完成!')
log('=' * 60)
