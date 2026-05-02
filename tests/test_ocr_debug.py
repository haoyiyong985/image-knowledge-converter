#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 调试测试脚本
"""

import os
import sys

# 设置环境变量
os.environ['TESSERACT_CMD'] = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from ocr_manager import OCRManager
from enhanced_batch_processor import EnhancedBatchProcessor, EnhancedOCRManager

def test_basic_ocr():
    """测试基础 OCR"""
    print("=" * 60)
    print("测试 1: 基础 OCRManager")
    print("=" * 60)
    
    manager = OCRManager()
    engine = manager.auto_select_engine()
    print(f"选择的引擎: {engine}")
    print(f"ocr_client 类型: {type(manager.ocr_client)}")
    
    test_image = r'D:\新建文件夹\待处理图片\示范\Screenshot_2020-07-04-18-59-16-52.jpg'
    
    if os.path.exists(test_image):
        print(f"测试图片: {test_image}")
        result = manager.recognize(test_image)
        print(f"结果类型: {type(result)}")
        print(f"Success: {result.get('success')}")
        print(f"Has text: {'text' in result}")
        if 'text' in result:
            print(f"Text length: {len(result['text'])}")
    else:
        print(f"图片不存在: {test_image}")

def test_enhanced_ocr():
    """测试增强版 OCR"""
    print("\n" + "=" * 60)
    print("测试 2: EnhancedOCRManager")
    print("=" * 60)
    
    manager = EnhancedOCRManager()
    print(f"当前引擎: {manager.current_engine}")
    
    test_image = r'D:\新建文件夹\待处理图片\示范\Screenshot_2020-07-04-18-59-16-52.jpg'
    
    if os.path.exists(test_image):
        print(f"测试图片: {test_image}")
        result = manager.recognize_with_fallback(test_image)
        print(f"结果类型: {type(result)}")
        print(f"Success: {result.get('success')}")
        print(f"Has text: {'text' in result}")
        if 'text' in result:
            print(f"Text length: {len(result['text'])}")
    else:
        print(f"图片不存在: {test_image}")

def test_processor():
    """测试处理器"""
    print("\n" + "=" * 60)
    print("测试 3: EnhancedBatchProcessor")
    print("=" * 60)
    
    try:
        processor = EnhancedBatchProcessor()
        print(f"OCR 管理器: {processor.ocr_manager}")
        print(f"分类器: {processor.classifier}")
        print("初始化成功!")
    except Exception as e:
        print(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_ocr()
    test_enhanced_ocr()
    test_processor()
