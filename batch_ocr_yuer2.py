#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量OCR识别脚本 - 处理育儿知识图片 第二批(11-21)
"""

import json
import time
from pathlib import Path
from ocr_engine_manager import OCREngineManager

# 路径配置
SOURCE_DIR = Path("D:/新建文件夹/待处理图片/育儿知识")
OUTPUT_FILE = Path("D:/新建文件夹/.workbuddy/memory/yuer_batch2.json")

# 图片列表 (第二批11-21)
IMAGES = [
    "Screenshot_20250313_221456_com.tencent.mm.jpg",
    "Screenshot_20250316_125800_com.tencent.mm.jpg",
    "Screenshot_20250516_191643_com.tencent.mm.jpg",
    "Screenshot_20250516_191646_com.tencent.mm.jpg",
    "Screenshot_20250516_191648_com.tencent.mm.jpg",
    "Screenshot_20250910_174402_com.tencent.mm.jpg",
    "Screenshot_20250917_215033_com.tencent.mm.jpg",
    "Screenshot_20251011_214427_com.tencent.mm.jpg",
    "Screenshot_20251220_193616_com.tencent.mm.jpg",
    "Screenshot_20260113_204213_com.tencent.mm.jpg",
    "Screenshot_20260116_165334_com.tencent.mm.jpg",
]

def main():
    manager = OCREngineManager()
    results = []
    
    for i, img_name in enumerate(IMAGES, 11):
        img_path = SOURCE_DIR / img_name
        print(f"[{i}/21] 识别: {img_name}")
        
        try:
            text, engine = manager.recognize_image(str(img_path))
            results.append({
                "filename": img_name,
                "engine": engine,
                "text": text,
                "success": True
            })
            print(f"  OK")
            time.sleep(0.5)
        except Exception as e:
            results.append({
                "filename": img_name,
                "engine": "",
                "text": "",
                "success": False,
                "error": str(e)
            })
            print(f"  FAIL: {e}")
    
    # 保存结果
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n识别完成!成功: {sum(1 for r in results if r['success'])}/{len(results)}")

if __name__ == "__main__":
    main()
