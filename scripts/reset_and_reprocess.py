#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置并重新处理图片
==================
1. 将已处理图片移回待处理目录
2. 删除生成的文档（保留原有4个分类文档）
3. 清理进度文件
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("D:/新建文件夹")
PENDING_DIR = BASE_DIR / "待处理图片"
PROCESSED_DIR = BASE_DIR / "已处理图片"
RESULT_DIR = BASE_DIR / "处理结果"
PROGRESS_DIR = BASE_DIR / "progress"

def move_images_back():
    """将图片从已处理目录移回待处理目录"""
    print("[STEP 1] 移动图片回待处理目录...")
    
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    moved_count = 0
    
    for topic_dir in PROCESSED_DIR.iterdir():
        if topic_dir.is_dir():
            pending_topic_dir = PENDING_DIR / topic_dir.name
            pending_topic_dir.mkdir(parents=True, exist_ok=True)
            
            for ext in image_exts:
                for img in topic_dir.rglob(f'*{ext}'):
                    dst = pending_topic_dir / img.name
                    if not dst.exists():
                        shutil.move(str(img), str(dst))
                        moved_count += 1
    
    print(f"[OK] 移回 {moved_count} 张图片")
    return moved_count

def clean_new_topic_docs():
    """删除新主题文档"""
    print("\n[STEP 2] 清理新主题文档...")
    
    # 保留原有分类文档，只删除新主题文档
    protected_docs = [
        "01_抗炎饮食与营养科普.md",
        "02_肠道健康与饮食分类.md", 
        "03_中医养生与食疗.md",
        "04_日常饮食建议.md",
        "05_石家庄美食地图.md"
    ]
    
    deleted = []
    for doc in RESULT_DIR.glob("*.md"):
        if doc.name not in protected_docs:
            doc.unlink()
            deleted.append(doc.name)
    
    if deleted:
        print(f"[OK] 删除 {len(deleted)} 个文档:")
        for d in deleted:
            print(f"  - {d}")
    else:
        print("[OK] 没有需要删除的新主题文档")

def clean_progress():
    """清理进度文件"""
    print("\n[STEP 3] 清理进度文件...")
    
    count = 0
    for pf in PROGRESS_DIR.glob("*.json"):
        pf.unlink()
        count += 1
    
    print(f"[OK] 删除 {count} 个进度文件")

def main():
    print("=" * 60)
    print("重置并准备重新处理")
    print("=" * 60)
    
    move_images_back()
    clean_new_topic_docs()
    clean_progress()
    
    print("\n" + "=" * 60)
    print("重置完成！")
    print("=" * 60)
    print("\n现在可以运行: python run_enhanced.py")

if __name__ == "__main__":
    main()
