#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
归档美食地图文件夹图片
"""

import os
import shutil
from datetime import datetime
import glob

def archive_images():
    # 路径设置
    source_dir = r'D:\新建文件夹\待处理图片\美食地图'
    target_dir = r'D:\新建文件夹\已处理图片\美食地图'
    
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)
    
    # 获取所有图片文件
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
        image_files.extend(glob.glob(os.path.join(source_dir, ext)))
    
    if not image_files:
        print("[INFO] 没有需要归档的图片")
        return
    
    print(f"[INFO] 找到 {len(image_files)} 张图片，开始归档...")
    
    # 移动文件
    moved_count = 0
    for file_path in image_files:
        file_name = os.path.basename(file_path)
        target_path = os.path.join(target_dir, file_name)
        
        # 如果目标文件已存在，添加时间戳
        if os.path.exists(target_path):
            name, ext = os.path.splitext(file_name)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            target_path = os.path.join(target_dir, f"{name}_{timestamp}{ext}")
        
        try:
            shutil.move(file_path, target_path)
            print(f"[OK] {file_name}")
            moved_count += 1
        except Exception as e:
            print(f"[ERROR] 移动 {file_name} 失败: {e}")
    
    print(f"\n[DONE] 成功归档 {moved_count}/{len(image_files)} 张图片")

if __name__ == '__main__':
    archive_images()
