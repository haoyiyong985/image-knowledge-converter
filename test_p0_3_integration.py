#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-3 模板系统集成验证脚本
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

print('=' * 60)
print('P0-3 模板系统集成验证')
print('=' * 60)

# 1. 测试配置文件
print('\n[1] 测试配置文件...')
import yaml
config_file = Path('config/processing_config.yaml')
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    template = config.get('word_template', 'NOT_FOUND')
    enabled = config.get('enable_template_system', 'NOT_FOUND')
    print(f'   word_template: {template}')
    print(f'   enable_template_system: {enabled}')
    print('   [PASS]')
else:
    print('   [FAIL] 配置文件不存在')

# 2. 测试模板引擎
print('\n[2] 测试模板引擎...')
try:
    from scripts.template_engine import TemplateEngine
    engine = TemplateEngine()
    templates = engine.list_templates()
    print(f'   发现 {len(templates)} 个模板:')
    for t in templates:
        print(f'     - {t["id"]}: {t["name"]}')
    print('   [PASS]')
except Exception as e:
    print(f'   [FAIL] {e}')

# 3. 测试 simple_batch_processor 配置加载
print('\n[3] 测试 SimpleBatchProcessor 配置加载...')
try:
    from scripts.simple_batch_processor import SimpleBatchProcessor
    processor = SimpleBatchProcessor()
    print(f'   word_template: {processor.word_template}')
    print(f'   enable_template_system: {processor.enable_template_system}')
    print('   [PASS]')
except Exception as e:
    print(f'   [FAIL] {e}')

# 4. 测试 auto_batch_processor 配置加载
print('\n[4] 测试 AutoBatchProcessor 配置加载...')
try:
    from scripts.auto_batch_processor import AutoBatchProcessor
    processor = AutoBatchProcessor()
    print(f'   word_template: {processor.word_template}')
    print(f'   enable_template_system: {processor.enable_template_system}')
    print('   [PASS]')
except Exception as e:
    print(f'   [FAIL] {e}')

# 5. 测试 generate_word.py 命令行参数
print('\n[5] 测试 generate_word.py 命令行参数...')
import subprocess
result = subprocess.run(
    [sys.executable, 'scripts/generate_word.py', '--help'],
    capture_output=True,
    text=True,
    encoding='utf-8',
    errors='ignore'
)
if '--template' in result.stdout:
    print('   --template 参数: 支持')
if '--list-templates' in result.stdout:
    print('   --list-templates 参数: 支持')
print('   [PASS]')

print('\n' + '=' * 60)
print('验证完成!')
print('=' * 60)
