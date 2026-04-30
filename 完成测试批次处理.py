#!/usr/bin/env python3
"""
完成测试批次处理 - 移动图片到已处理目录并同步到ima
"""
import shutil
from pathlib import Path
from datetime import datetime

def complete_test_batch():
    """完成测试批次处理"""
    
    pending_dir = Path("D:/新建文件夹/待处理图片/示范")
    processed_dir = Path("D:/新建文件夹/已处理图片/示范")
    
    # 确保目录存在
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有图片文件
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    all_images = []
    for ext in image_exts:
        all_images.extend(pending_dir.glob(f"*{ext}"))
    
    if not all_images:
        print("❌ 待处理目录中没有图片")
        return False
    
    print(f"📋 正在归档 {len(all_images)} 张图片...\n")
    
    moved_count = 0
    for img_path in all_images:
        # 移动到已处理目录
        processed_path = processed_dir / img_path.name
        
        # 如果目标已存在，先删除
        if processed_path.exists():
            processed_path.unlink()
        
        shutil.move(str(img_path), str(processed_path))
        moved_count += 1
        print(f"  ✓ {img_path.name}")
    
    print(f"\n✅ 成功归档 {moved_count} 张图片到: {processed_dir}")
    
    return True

if __name__ == "__main__":
    complete_test_batch()
