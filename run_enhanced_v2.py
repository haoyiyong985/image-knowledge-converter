#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版图片处理器 v2.0 - 简化启动脚本
=====================================

解决编码问题和依赖问题，确保稳定运行
"""

import sys
import os

# 设置编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 添加项目路径
sys.path.insert(0, r'D:\新建文件夹')

def check_dependencies():
    """检查依赖"""
    print("=" * 60)
    print("检查依赖...")
    print("=" * 60)
    
    required_modules = [
        ('pathlib', 'Path'),
        ('logging', 'basicConfig'),
        ('json', 'loads'),
        ('shutil', 'copy'),
        ('time', 'sleep'),
        ('gc', 'collect'),
        ('threading', 'Thread'),
        ('datetime', 'datetime'),
        ('collections', 'defaultdict'),
        ('dataclasses', 'dataclass'),
        ('typing', 'List'),
        ('psutil', 'Process'),
    ]
    
    missing = []
    for module, attr in required_modules:
        try:
            mod = __import__(module)
            if attr:
                getattr(mod, attr)
            print(f"  [OK] {module}")
        except ImportError as e:
            print(f"  [FAIL] {module}: {e}")
            missing.append(module)
    
    # 检查项目模块
    print("\n检查项目模块...")
    try:
        from ocr_manager import OCRManager
        print("  [OK] ocr_manager")
    except ImportError as e:
        print(f"  [FAIL] ocr_manager: {e}")
        missing.append('ocr_manager')
    
    try:
        from classifier_engine import ClassifierEngine
        print("  [OK] classifier_engine")
    except ImportError as e:
        print(f"  [FAIL] classifier_engine: {e}")
        missing.append('classifier_engine')
    
    if missing:
        print(f"\n[ERROR] 缺少依赖: {', '.join(missing)}")
        return False
    
    print("\n[OK] 所有依赖检查通过!")
    return True


def count_pending_images():
    """统计待处理图片"""
    from pathlib import Path
    
    BASE_DIR = Path("D:/新建文件夹")
    PENDING_DIR = BASE_DIR / "待处理图片"
    
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
    print("图片知识库转化工具 v2.0 - 增强版处理器")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n请先安装缺少的依赖")
        input("按回车键退出...")
        return
    
    # 统计待处理图片
    total, topics = count_pending_images()
    
    print(f"\n待处理图片统计:")
    if total == 0:
        print("  暂无待处理图片")
        print(f"\n提示: 将图片放入 D:\\新建文件夹\\待处理图片\\ 下的子文件夹中")
        input("按回车键退出...")
        return
    
    print(f"  总计: {total} 张图片")
    print(f"  主题数: {len(topics)} 个")
    for topic, count in topics.items():
        print(f"    - {topic}: {count} 张")
    
    # 选择处理方式
    print("\n" + "=" * 60)
    print("请选择处理方式:")
    print("=" * 60)
    print("1. [增强版处理器] 智能分批 + 并发 + 自动降级")
    print("2. [原始处理器] 简单快速 + 兼容模式")
    print("3. [测试模式] 运行性能测试")
    print("4. [退出]")
    print("=" * 60)
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        print("\n启动增强版处理器...")
        try:
            # 导入并运行增强版处理器
            from enhanced_batch_processor import EnhancedBatchProcessor
            
            processor = EnhancedBatchProcessor()
            
            # 处理每个主题
            from pathlib import Path
            BASE_DIR = Path("D:/新建文件夹")
            PENDING_DIR = BASE_DIR / "待处理图片"
            image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
            
            for topic_name in topics.keys():
                topic_dir = PENDING_DIR / topic_name
                images = [f for f in topic_dir.iterdir() 
                         if f.suffix.lower() in image_extensions]
                
                if images:
                    print(f"\n处理主题: {topic_name} ({len(images)} 张图片)")
                    processor.process_topic(topic_name, sorted(images))
            
            print("\n[OK] 处理完成!")
            
            # 询问是否生成报告
            gen_report = input("\n是否生成处理报告? (y/n): ").strip().lower()
            if gen_report == 'y':
                try:
                    from progress_monitor import ReportGenerator
                    reporter = ReportGenerator()
                    report_path = reporter.generate_summary_report()
                    print(f"[OK] 报告已生成: {report_path}")
                except Exception as e:
                    print(f"[WARNING] 生成报告失败: {e}")
        
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "2":
        print("\n启动原始处理器...")
        try:
            # 运行原始处理器
            import batch_processor
            batch_processor.main()
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "3":
        print("\n启动性能测试...")
        try:
            import test_performance
            test_performance.main()
        except Exception as e:
            print(f"\n[ERROR] 错误: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "4":
        print("\n再见!")
        return
    
    else:
        print("\n[ERROR] 无效选项")
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
