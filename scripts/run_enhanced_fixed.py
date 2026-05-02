#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片知识库转化工具 v2.0 - 修复版启动脚本
============================================

修复内容：
1. 编码问题（使用ASCII字符替代Unicode）
2. 简化输出格式
3. 添加错误处理
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


def check_dependencies():
    """检查依赖"""
    print("=" * 60)
    print("检查依赖...")
    print("=" * 60)
    
    required_modules = [
        "ocr_manager",
        "classifier_engine"
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  [OK] {module}")
        except ImportError as e:
            print(f"  [FAIL] {module}: {e}")
            missing.append(module)
    
    if missing:
        print(f"\n[ERROR] 缺少依赖模块: {', '.join(missing)}")
        return False
    
    print("\n[OK] 依赖检查通过")
    return True


def count_pending_images():
    """统计待处理图片数量"""
    if not PENDING_DIR.exists():
        return 0, {}
    
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    topics = {}
    total = 0
    
    for topic_dir in PENDING_DIR.iterdir():
        if not topic_dir.is_dir():
            continue
        
        images = [f for f in topic_dir.iterdir() if f.suffix.lower() in image_extensions]
        if images:
            topics[topic_dir.name] = len(images)
            total += len(images)
    
    return total, topics


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("图片知识库转化工具 v2.0 (修复版)")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n请先安装必要的依赖模块")
        input("按回车键退出...")
        return
    
    # 统计待处理图片
    total, topics = count_pending_images()
    
    print(f"\n待处理图片统计:")
    if total == 0:
        print("  暂无待处理图片")
        print(f"\n提示: 将图片放入 {PENDING_DIR} 下的子文件夹中")
        input("按回车键退出...")
        return
    
    print(f"  总计: {total} 张图片")
    print(f"  主题数: {len(topics)} 个")
    for topic, count in topics.items():
        print(f"    - {topic}: {count} 张")
    
    # 选择处理方式
    print("\n" + "=" * 60)
    print("场景选择指南:")
    print("=" * 60)
    print("[选项1] 图片多/大小不一/首次使用 -> 选 增强版")
    print("[选项2] 图片少/质量一致/求快速 -> 选 原始版")
    print("[选项3] 想看效果对比/测试安装 -> 选 性能测试")
    print("[选项4] 还没准备好/临时有事 -> 选 退出")
    print("=" * 60)
    print("\n请选择处理方式:")
    print("1. 增强版处理器 (智能分批+并发+自动降级)")
    print("2. 原始处理器 (简单快速+兼容模式)")
    print("3. 运行性能测试 (对比两个版本)")
    print("4. 退出")
    print("=" * 60)
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        print("\n启动增强版处理器...")
        try:
            from enhanced_batch_processor import EnhancedBatchProcessor
            processor = EnhancedBatchProcessor()
            
            # 处理每个主题
            for topic_name in topics.keys():
                topic_dir = PENDING_DIR / topic_name
                images = [f for f in topic_dir.iterdir() 
                         if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}]
                
                if images:
                    print(f"\n处理主题: {topic_name}")
                    print(f"图片数量: {len(images)}")
                    processor.process_topic(topic_name, sorted(images))
            
            print("\n[OK] 处理完成!")
            
            # 询问是否生成报告
            gen_report = input("\n是否生成处理报告? (y/n): ").strip().lower()
            if gen_report == 'y':
                try:
                    from progress_monitor import ReportGenerator
                    reporter = ReportGenerator()
                    report_path = reporter.generate_summary_report()
                    print(f"报告已生成: {report_path}")
                except Exception as e:
                    print(f"生成报告失败: {e}")
        
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "2":
        print("\n启动原始处理器...")
        try:
            from batch_processor import main as original_main
            original_main()
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
    
    elif choice == "3":
        print("\n启动性能测试...")
        try:
            import test_performance
            test_performance.main()
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
    
    elif choice == "4":
        print("\n再见!")
        return
    
    else:
        print("\n[ERROR] 无效选项")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
