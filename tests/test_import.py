#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试导入依赖模块"""

import sys
import os

print("=" * 60)
print("测试 Python 环境和依赖导入")
print("=" * 60)

# 测试基础模块
print("\n1. 测试基础模块...")
try:
    import pathlib
    print("   [OK] pathlib")
except ImportError as e:
    print(f"   [FAIL] pathlib: {e}")

try:
    import logging
    print("   [OK] logging")
except ImportError as e:
    print(f"   [FAIL] logging: {e}")

try:
    import json
    print("   [OK] json")
except ImportError as e:
    print(f"   [FAIL] json: {e}")

try:
    import shutil
    print("   [OK] shutil")
except ImportError as e:
    print(f"   [FAIL] shutil: {e}")

try:
    import time
    print("   [OK] time")
except ImportError as e:
    print(f"   [FAIL] time: {e}")

try:
    import gc
    print("   [OK] gc")
except ImportError as e:
    print(f"   [FAIL] gc: {e}")

try:
    import threading
    print("   [OK] threading")
except ImportError as e:
    print(f"   [FAIL] threading: {e}")

try:
    from datetime import datetime
    print("   [OK] datetime")
except ImportError as e:
    print(f"   [FAIL] datetime: {e}")

try:
    from concurrent.futures import ThreadPoolExecutor
    print("   [OK] concurrent.futures")
except ImportError as e:
    print(f"   [FAIL] concurrent.futures: {e}")

try:
    from collections import defaultdict
    print("   [OK] collections")
except ImportError as e:
    print(f"   [FAIL] collections: {e}")

# 测试项目模块
print("\n2. 测试项目自定义模块...")
sys.path.insert(0, r'D:\新建文件夹')

try:
    from ocr_manager import OCRManager, OCREngine
    print("   [OK] ocr_manager")
except ImportError as e:
    print(f"   [FAIL] ocr_manager: {e}")

try:
    from classifier_engine import ClassifierEngine
    print("   [OK] classifier_engine")
except ImportError as e:
    print(f"   [FAIL] classifier_engine: {e}")

# 测试路径
print("\n3. 测试路径配置...")
from pathlib import Path
BASE_DIR = Path("D:/新建文件夹")
print(f"   BASE_DIR: {BASE_DIR}")
print(f"   是否存在: {BASE_DIR.exists()}")

PENDING_DIR = BASE_DIR / "待处理图片"
print(f"   PENDING_DIR: {PENDING_DIR}")
print(f"   是否存在: {PENDING_DIR.exists()}")

# 测试目录创建
print("\n4. 测试目录创建...")
PROGRESS_DIR = BASE_DIR / "progress"
LOGS_DIR = BASE_DIR / "logs"

try:
    PROGRESS_DIR.mkdir(exist_ok=True)
    print(f"   [OK] PROGRESS_DIR 创建成功")
except Exception as e:
    print(f"   [FAIL] PROGRESS_DIR 创建失败: {e}")

try:
    LOGS_DIR.mkdir(exist_ok=True)
    print(f"   [OK] LOGS_DIR 创建成功")
except Exception as e:
    print(f"   [FAIL] LOGS_DIR 创建失败: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
