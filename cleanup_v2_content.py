#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 2.0 版本添加的混乱内容，恢复 1.0 版本状态
================================================
"""

import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("D:/新建文件夹")
RESULT_DIR = BASE_DIR / "处理结果"

def clean_document(doc_path: Path) -> bool:
    """
    清理文档中的 2.0 版本混乱内容
    保留 1.0 版本的 AI 整理内容，删除自动追加的 OCR 原文
    """
    print(f"[处理] {doc_path.name}")
    
    content = doc_path.read_text(encoding="utf-8")
    original_length = len(content)
    
    # 查找 2.0 版本添加内容的标志（图片文件名 + 识别引擎信息）
    # 模式1: ## 示范 - 日期时间 或 ### 图片文件名
    patterns = [
        r'## 示范 - \d{4}-\d{2}-\d{2} \d{2}:\d{2}.*?\n',  # 批次标题
        r'### [\w\-_]+\.\w+\s*\n',  # 图片文件名
        r'\*\*识别引擎\*\*: 腾讯云 OCR \| \*\*置信度\*\*: \d+\.\d+\s*\n',  # 识别信息
        r'```[\s\S]*?```',  # 代码块内容
        r'> 人体食养地图[\s\S]*?(?=\n## |\n### |$)',  # 未整理的内容块
        r'批次\d+ - \d{4}-\d{2}-\d{2} \d{2}:\d{2}.*?\n',  # 批次标记
    ]
    
    cleaned_content = content
    for pattern in patterns:
        cleaned_content = re.sub(pattern, '', cleaned_content)
    
    # 清理多余的空行
    cleaned_content = re.sub(r'\n{3,}', '\n\n', cleaned_content)
    
    # 如果内容有变化，保存
    if len(cleaned_content) < original_length:
        doc_path.write_text(cleaned_content, encoding="utf-8")
        print(f"  [OK] 清理完成，删除 {original_length - len(cleaned_content)} 字符")
        return True
    else:
        print(f"  [SKIP] 无需清理")
        return False

def restore_original_structure():
    """恢复文档到 1.0 版本的干净状态"""
    print("=" * 60)
    print("清理 2.0 版本混乱内容")
    print("=" * 60)
    
    # 需要清理的文档
    docs_to_clean = [
        "01_抗炎饮食与营养科普.md",
        "02_肠道健康与饮食分类.md",
        "03_中医养生与食疗.md",
        "04_日常饮食建议.md",
    ]
    
    cleaned_count = 0
    for doc_name in docs_to_clean:
        doc_path = RESULT_DIR / doc_name
        if doc_path.exists():
            if clean_document(doc_path):
                cleaned_count += 1
        else:
            print(f"[SKIP] {doc_name} 不存在")
    
    # 删除 2.0 版本生成的新主题文档
    new_topic_docs = list(RESULT_DIR.glob("06_*_新主题.md"))
    for doc in new_topic_docs:
        print(f"[删除] {doc.name}")
        doc.unlink()
    
    print("\n" + "=" * 60)
    print(f"清理完成: {cleaned_count} 个文档已清理")
    print(f"删除新主题文档: {len(new_topic_docs)} 个")
    print("=" * 60)
    print("\n现在可以使用 1.0 版本 workflow:")
    print("  python auto_process.py")
    print("然后在 WorkBuddy 中发送「处理新图片」")

if __name__ == "__main__":
    restore_original_structure()
