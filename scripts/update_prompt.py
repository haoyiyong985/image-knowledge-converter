#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动提示词自动更新脚本
========================
功能：根据处理结果自动更新【启动提示词】文件

作者：AI Assistant
版本：v1.0
"""

import os
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("D:/新建文件夹")
PROMPT_FILE = BASE_DIR / "【启动提示词】新对话粘贴这段.txt"
RESULT_DIR = BASE_DIR / "处理结果"

def extract_doc_summary(file_path: Path) -> tuple:
    """从文档中提取摘要信息"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else file_path.stem
        
        # 提取所有二级标题（## 开头）
        sections = re.findall(r'^## (.+)$', content, re.MULTILINE)
        
        # 提取分类（从文件名或内容判断）
        categories = []
        if '抗炎' in content or '营养' in content:
            categories.append('营养科普')
        if '中医' in content or '养生' in content:
            categories.append('中医养生')
        if '饮食' in content or '食谱' in content:
            categories.append('饮食指南')
        if '肠道' in content:
            categories.append('肠道健康')
        if '经络' in content or '穴位' in content:
            categories.append('中医经络')
            
        return title, sections, categories
    except Exception as e:
        print(f"[ERROR] 读取文档失败 {file_path}: {e}")
        return file_path.stem, [], []

def update_prompt_file():
    """更新启动提示词文件"""
    if not PROMPT_FILE.exists():
        print(f"[ERROR] 启动提示词文件不存在: {PROMPT_FILE}")
        return False
    
    # 读取现有内容
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新时间戳
    current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    content = re.sub(
        r'【已有文档列表】（最后更新：\d{4}年\d{2}月\d{2}日 \d{2}:\d{2}）',
        f'【已有文档列表】（最后更新：{current_time}）',
        content
    )
    
    # 扫描所有文档（只包含编号文档，排除报告文件）
    md_files = sorted([f for f in RESULT_DIR.glob("*.md") 
                       if re.match(r'^\d{2}_', f.name)])
    
    if not md_files:
        print("[WARN] 未找到编号文档（格式：01_xxx.md）")
        return False
    
    # 生成文档列表
    doc_list = []
    for i, md_file in enumerate(md_files, 1):
        title, sections, categories = extract_doc_summary(md_file)
        
        # 格式化编号
        doc_number = f"{i:02d}"
        
        # 提取前5个章节作为内容摘要
        section_summary = "、".join(sections[:5]) if sections else "（基础章节）"
        if len(sections) > 5:
            section_summary += "等"
        
        # 格式化分类
        category_str = "、".join(categories) if categories else "未分类"
        
        doc_entry = f"""编号{doc_number}：{md_file.name}
  - 内容：{section_summary}
  - 分类：{category_str}"""
        
        doc_list.append(doc_entry)
    
    # 替换文档列表部分
    doc_list_str = "\n\n".join(doc_list)
    
    # 使用正则替换文档列表区域
    pattern = r'(【已有文档列表】（最后更新：.+?）)\n+(编号\d+：.+?)(?=\n\n【处理规则】)'
    
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, f'【已有文档列表】（最后更新：{current_time}）\n\n{doc_list_str}', content, flags=re.DOTALL)
    else:
        print("[WARN] 未找到文档列表区域，可能需要手动更新")
    
    # 写回文件
    with open(PROMPT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"[INFO] 启动提示词已更新: {current_time}")
    print(f"[INFO] 共更新 {len(doc_list)} 个文档信息")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("启动提示词自动更新")
    print("=" * 60)
    
    success = update_prompt_file()
    
    if success:
        print("\n[INFO] 更新完成！")
    else:
        print("\n[ERROR] 更新失败！")

if __name__ == "__main__":
    main()
