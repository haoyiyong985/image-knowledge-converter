#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强版处理器 - 非交互式
"""

import os
import sys
import io

# 设置编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path

BASE_DIR = Path("D:/新建文件夹")
PENDING_DIR = BASE_DIR / "待处理图片"


def test_import():
    """测试导入"""
    print("=" * 60)
    print("测试增强版处理器导入")
    print("=" * 60)
    
    try:
        print("\n1. 导入 enhanced_batch_processor...")
        from enhanced_batch_processor import EnhancedBatchProcessor
        print("   [OK] 导入成功")
        
        print("\n2. 初始化处理器...")
        processor = EnhancedBatchProcessor()
        print("   [OK] 初始化成功")
        
        print("\n3. 检查OCR引擎...")
        engine_name = processor.ocr_manager.get_current_engine_name()
        print(f"   [OK] 当前引擎: {engine_name}")
        
        return processor
        
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_analyze_images(processor):
    """测试图片分析功能"""
    print("\n" + "=" * 60)
    print("测试图片分析功能")
    print("=" * 60)
    
    # 查找待处理图片
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    for topic_dir in PENDING_DIR.iterdir():
        if not topic_dir.is_dir():
            continue
        
        images = [f for f in topic_dir.iterdir() if f.suffix.lower() in image_extensions]
        
        if images:
            print(f"\n主题: {topic_dir.name}")
            print(f"图片数量: {len(images)}")
            
            try:
                print("\n分析图片...")
                image_infos = processor.analyze_images(images[:5])  # 只测试前5张
                
                print("\n分析结果:")
                for info in image_infos:
                    print(f"  - {info.name}: {info.size_mb:.2f} MB ({info.size_category})")
                
                print("\n[OK] 图片分析成功")
                return True
                
            except Exception as e:
                print(f"\n[ERROR] 分析失败: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    print("\n[WARN] 没有找到待处理图片")
    return False


def main():
    """主函数"""
    print("\n图片知识库转化工具 v2.0 - 测试模式")
    
    # 测试导入
    processor = test_import()
    if not processor:
        print("\n[FAIL] 导入测试失败")
        return 1
    
    # 测试图片分析
    if not test_analyze_images(processor):
        print("\n[FAIL] 图片分析测试失败")
        return 1
    
    print("\n" + "=" * 60)
    print("[OK] 所有测试通过!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
