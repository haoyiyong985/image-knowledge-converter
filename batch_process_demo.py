#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批处理演示 - 模拟之前的 Kimi 批处理流程
"""

import os
from pathlib import Path
from datetime import datetime

PENDING_DIR = Path("D:/新建文件夹/待处理图片/示范")
RESULT_DIR = Path("D:/新建文件夹/处理结果")

# 扫描示范文件夹的图片
images = list(PENDING_DIR.glob("*.*"))
images = [img for img in images if img.suffix.lower() in {".jpg", ".jpeg", ".png"}]

print(f"找到 {len(images)} 张图片")
print(f"将分成 {len(images)//5 + 1} 个批次（每批5张）\n")

# 生成批处理文件
batch_num = 1
for i in range(0, len(images), 5):
    batch_images = images[i:i+5]

    # 生成图片列表
    images_file = RESULT_DIR / f"batch_{batch_num:02d}_images.txt"
    images_file.write_text("\n".join([str(img) for img in batch_images]), encoding="utf-8")

    # 生成提示词
    prompt_file = RESULT_DIR / f"batch_{batch_num:02d}_prompt.txt"
    prompt_content = f"""请识别以下图片中的文字内容，并按以下要求处理：

【图片列表】
{chr(10).join([f"{j+1}. {img.name}" for j, img in enumerate(batch_images)])}

【处理要求】
1. 识别每张图片中的所有文字内容
2. 判断内容属于哪个主题：
   - 抗炎饮食与营养科普（坚果、ω-3、ω-6、营养素、脂肪酸、抗炎食物）
   - 肠道健康与饮食分类（肠道、益生菌、益生元、绿灯食物、红灯食物）
   - 中医养生与食疗（中医、养生、食疗、茶饮、汤药）
   - 日常饮食建议（早餐、食谱、搭配、热量、蛋白质）
   - 其他全新主题
3. 对于每个主题，按以下格式输出：
   - 图片名称
   - 识别到的文字内容
   - 建议的主题分类
   - 简要内容

【输出格式】
请以清晰的文本格式输出，方便后续合并到文档。

【时间】
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    prompt_file.write_text(prompt_content, encoding="utf-8")

    print(f"[生成] 批次 {batch_num:02d}: {len(batch_images)} 张图片")
    print(f"  - 图片列表: {images_file.name}")
    print(f"  - 提示词: {prompt_file.name}")

    batch_num += 1

print(f"\n[完成] 共生成 {batch_num-1} 个批处理文件")
print(f"\n[下一步]")
print(f"1. 打开每个批次的 prompt 文件")
print(f"2. 复制内容到 Kimi 或其他支持图片的 AI")
print(f"3. 上传对应批次的图片")
print(f"4. 让 AI 识别并返回结果")
print(f"5. 将结果保存为 batch_XX_result.txt")
print(f"6. 所有批次完成后，通知我合并结果")
