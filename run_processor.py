#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版处理器运行脚本 v2.1
==========================

使用方法:
    python run_processor.py

功能:
    1. 自动扫描待处理图片
    2. 智能分批处理
    3. 生成处理报告
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, r'D:\新建文件夹')

# 导入处理器
from enhanced_batch_processor_v2 import (
    EnhancedBatchProcessor, SmartBatcher,
    BASE_DIR, PENDING_DIR, PROCESSED_DIR, RESULT_DIR,
    IMAGE_EXTENSIONS
)


def print_header():
    """打印标题"""
    print("=" * 60)
    print("  图片知识库转化工具 v2.1")
    print("  增强版处理器 (修复版)")
    print("=" * 60)
    print()


def print_summary(topics):
    """打印统计信息"""
    if not topics:
        print("[INFO] 没有待处理的图片")
        print(f"[INFO] 请将图片放入: {PENDING_DIR}")
        return False
    
    total_images = sum(len(imgs) for imgs in topics.values())
    
    print(f"[INFO] 发现 {len(topics)} 个主题, 共 {total_images} 张图片")
    print()
    
    for topic_name, images in topics.items():
        # 计算图片大小分布
        sizes = [img.stat().st_size for img in images]
        total_size = sum(sizes) / (1024 * 1024)  # MB
        avg_size = total_size / len(images) if images else 0
        
        print(f"  主题: {topic_name}")
        print(f"    - 图片数量: {len(images)} 张")
        print(f"    - 总大小: {total_size:.2f} MB")
        print(f"    - 平均大小: {avg_size:.2f} MB")
        print()
    
    return True


def process_with_batches(topics):
    """使用智能分批处理"""
    batcher = SmartBatcher()
    
    all_results = []
    
    for topic_name, images in topics.items():
        print(f"\n{'='*60}")
        print(f"处理主题: {topic_name}")
        print(f"{'='*60}\n")
        
        # 创建批次
        batches = batcher.create_batches(images)
        print(f"[INFO] 分成 {len(batches)} 个批次")
        print()
        
        # 处理每个批次
        topic_results = []
        for i, batch in enumerate(batches, 1):
            print(f"批次 {i}/{len(batches)} ({len(batch)} 张图片)...")
            
            # 模拟处理（实际使用时接入OCR）
            for img in batch:
                result = {
                    "image": img.name,
                    "path": str(img),
                    "topic": topic_name,
                    "batch": i,
                    "status": "pending"
                }
                topic_results.append(result)
            
            print(f"  [OK] 批次 {i} 完成")
        
        all_results.extend(topic_results)
        
        print(f"\n[OK] 主题 '{topic_name}' 处理完成")
    
    return all_results


def generate_report(results, topics):
    """生成处理报告"""
    report_file = RESULT_DIR / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("图片处理报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        # 统计
        f.write("【处理统计】\n")
        f.write(f"主题数量: {len(topics)}\n")
        f.write(f"图片总数: {len(results)}\n")
        f.write(f"批次数量: {max(r['batch'] for r in results) if results else 0}\n")
        f.write("\n")
        
        # 详细结果
        f.write("【详细结果】\n")
        for r in results:
            f.write(f"\n图片: {r['image']}\n")
            f.write(f"  主题: {r['topic']}\n")
            f.write(f"  批次: {r['batch']}\n")
            f.write(f"  状态: {r['status']}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("报告生成完成\n")
    
    print(f"\n[OK] 报告已保存: {report_file}")
    return report_file


def main():
    """主函数"""
    print_header()
    
    # 检查目录
    if not PENDING_DIR.exists():
        print(f"[ERROR] 待处理目录不存在: {PENDING_DIR}")
        return
    
    # 扫描主题
    print("[INFO] 扫描待处理图片...\n")
    topics = {}
    
    for topic_dir in PENDING_DIR.iterdir():
        if not topic_dir.is_dir():
            continue
        
        images = [
            f for f in topic_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        
        if images:
            topics[topic_dir.name] = sorted(images)
    
    # 打印统计
    if not print_summary(topics):
        input("\n按回车键退出...")
        return
    
    # 确认处理
    confirm = input("是否开始处理? (y/n): ").strip().lower()
    if confirm != 'y':
        print("[INFO] 已取消处理")
        return
    
    print("\n" + "=" * 60)
    print("开始处理...")
    print("=" * 60 + "\n")
    
    # 处理图片
    try:
        results = process_with_batches(topics)
        
        # 生成报告
        report_path = generate_report(results, topics)
        
        print("\n" + "=" * 60)
        print("处理完成!")
        print(f"报告位置: {report_path}")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
