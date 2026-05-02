#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量OCR识别脚本 - 处理育儿知识图片 第三批(weread)
"""

import json
import time
from pathlib import Path
from ocr_engine_manager import OCREngineManager

# 路径配置
SOURCE_DIR = Path("D:/新建文件夹/待处理图片/育儿知识")
OUTPUT_FILE = Path("D:/新建文件夹/.workbuddy/memory/yuer_batch3.json")

# 图片列表 (第三批 weread)
IMAGES = [
    "weread_image_477672432533361.jpeg",
    "weread_image_477697594806794.jpeg",
    "weread_image_477737839314601.jpeg",
    "weread_image_478199320397863.jpeg",
    "weread_image_478366797466067.jpeg",
    "weread_image_478369732925962.jpeg",
    "weread_image_479191451331566.jpeg",
]

def main():
    manager = OCREngineManager()
    results = []
    
    for i, img_name in enumerate(IMAGES, 22):
        img_path = SOURCE_DIR / img_name
        print(f"[{i}/28] 识别: {img_name}")
        
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
