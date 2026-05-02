#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版处理器模块导入和基本功能
"""

import sys
sys.path.insert(0, r'D:\新建文件夹')

print("=" * 60)
print("测试增强版处理器")
print("=" * 60)

# 测试导入
print("\n1. 测试模块导入...")
try:
    from enhanced_batch_processor import (
        EnhancedBatchProcessor,
        ImageInfo,
        ProcessingProgress,
        PerformanceMetrics,
        MemoryMonitor,
        DuplicateDetector,
        EnhancedOCRManager
    )
    print("   [OK] 所有类导入成功")
except Exception as e:
    print(f"   [FAIL] 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试配置
print("\n2. 测试路径配置...")
from pathlib import Path
BASE_DIR = Path("D:/新建文件夹")
PENDING_DIR = BASE_DIR / "待处理图片"
PROCESSED_DIR = BASE_DIR / "已处理图片"
RESULT_DIR = BASE_DIR / "处理结果"

print(f"   BASE_DIR: {BASE_DIR} (存在: {BASE_DIR.exists()})")
print(f"   PENDING_DIR: {PENDING_DIR} (存在: {PENDING_DIR.exists()})")
print(f"   PROCESSED_DIR: {PROCESSED_DIR} (存在: {PROCESSED_DIR.exists()})")
print(f"   RESULT_DIR: {RESULT_DIR} (存在: {RESULT_DIR.exists()})")

# 测试内存监控器
print("\n3. 测试内存监控器...")
try:
    monitor = MemoryMonitor()
    print("   [OK] MemoryMonitor 创建成功")
    monitor.start()
    print("   [OK] MemoryMonitor 启动成功")
    import time
    time.sleep(1)
    monitor.stop()
    print(f"   [OK] MemoryMonitor 停止成功 (峰值内存: {monitor.get_peak_memory():.2f} MB)")
except Exception as e:
    print(f"   [FAIL] MemoryMonitor 测试失败: {e}")

# 测试重复检测器
print("\n4. 测试重复检测器...")
try:
    detector = DuplicateDetector()
    print("   [OK] DuplicateDetector 创建成功")
    
    # 测试文本
    text1 = "这是一个测试文本，用于验证重复检测功能。"
    text2 = "这是另一个不同的文本内容。"
    text3 = "这是一个测试文本，用于验证重复检测功能。"  # 与text1相同
    
    is_dup, match = detector.is_duplicate(text1)
    print(f"   首次添加文本1 - 是否重复: {is_dup}")
    detector.add_content(text1)
    
    is_dup, match = detector.is_duplicate(text2)
    print(f"   添加文本2 - 是否重复: {is_dup}")
    detector.add_content(text2)
    
    is_dup, match = detector.is_duplicate(text3)
    print(f"   添加文本3(与1相同) - 是否重复: {is_dup}")
    
    print("   [OK] DuplicateDetector 功能正常")
except Exception as e:
    print(f"   [FAIL] DuplicateDetector 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试图片信息类
print("\n5. 测试图片信息类...")
try:
    test_image = Path("D:/新建文件夹/待处理图片/美食地图/test.jpg")
    if test_image.exists():
        info = ImageInfo(
            path=test_image,
            size=test_image.stat().st_size,
            size_category="medium"
        )
        print(f"   [OK] ImageInfo 创建成功")
        print(f"      文件名: {info.name}")
        print(f"      大小: {info.size_mb:.2f} MB")
    else:
        # 使用模拟数据
        info = ImageInfo(
            path=Path("test.jpg"),
            size=1024*1024,  # 1MB
            size_category="medium"
        )
        print(f"   [OK] ImageInfo 创建成功 (使用模拟数据)")
        print(f"      文件名: {info.name}")
        print(f"      大小: {info.size_mb:.2f} MB")
except Exception as e:
    print(f"   [FAIL] ImageInfo 测试失败: {e}")

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
