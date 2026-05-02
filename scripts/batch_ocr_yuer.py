#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量OCR识别脚本 - 处理育儿知识图片
使用腾讯云/百度云OCR识别图片文字
"""

import json
import time
from pathlib import Path
from ocr_engine_manager import OCREngineManager

# 路径配置
SOURCE_DIR = Path("D:/新建文件夹/待处理图片/育儿知识")
OUTPUT_FILE = Path("D:/新建文件夹/.workbuddy/memory/yuer_batch1.json")

# 图片列表 (第一批10张)
IMAGES = [
    "Screenshot_20250208_162840_com.tencent.mm.jpg",
    "Screenshot_20250208_162853_com.tencent.mm.jpg",
    "Screenshot_20250208_162906_com.tencent.mm.jpg",
    "Screenshot_20250305_215559_com.tencent.mm.jpg",
    "Screenshot_20250307_220444_com.tencent.mm.jpg",
    "Screenshot_20250307_220449_com.tencent.mm.jpg",
    "Screenshot_20250307_220456_com.tencent.mm.jpg",
    "Screenshot_20250307_220516_com.tencent.mm.jpg",
    "Screenshot_20250307_220526_com.tencent.mm.jpg",
    "Screenshot_20250308_123344_com.tencent.mm.jpg",
]

def main():
    manager = OCREngineManager()
    results = []
    
    for i, img_name in enumerate(IMAGES, 1):
        img_path = SOURCE_DIR / img_name
        print(f"[{i}/10] 识别: {img_name}")
        
        try:
            text, engine = manager.recognize_image(str(img_path))
            results.append({
                "filename": img_name,
                "engine": engine,
                "text": text,
                "success": True
            })
            print(f"  ✓ 成功 ({engine})")
            # 避免请求过快
            time.sleep(0.5)
        except Exception as e:
            results.append({
                "filename": img_name,
                "engine": "",
                "text": "",
                "success": False,
                "error": str(e)
            })
            print(f"  FAIL 失败: {e}")
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n识别完成！结果已保存到: {OUTPUT_FILE}")
    print(f"成功: {sum(1 for r in results if r['success'])}/{len(results)}")

if __name__ == "__main__":
    main()
