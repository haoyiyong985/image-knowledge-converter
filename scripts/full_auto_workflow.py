#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片知识库完整全自动工作流
============================
整合分批处理、AI识别、文档更新、归档同步的完整流程

使用方式：
  python full_auto_workflow.py           # 完整流程
  python full_auto_workflow.py --batch   # 仅分批，等待AI处理
  python full_auto_workflow.py --finish  # AI处理完成后，执行收尾

作者：AI Assistant
版本：v1.0
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = Path("D:/新建文件夹")
SOURCE_DIR = BASE_DIR / "待处理图片"
TARGET_DIR = BASE_DIR / "已处理图片"
RESULT_DIR = BASE_DIR / "处理结果"
CONFIG_FILE = BASE_DIR / "ima_config.txt"
LOG_FILE = BASE_DIR / ".workbuddy/memory/processing_log.json"

# ============================================================
# 工具函数
# ============================================================

def log_message(msg, level="INFO"):
    """打印并记录日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def run_command(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if check and result.returncode != 0:
            log_message(f"命令失败: {result.stderr}", "ERROR")
            return None
        return result
    except Exception as e:
        log_message(f"命令异常: {e}", "ERROR")
        return None

# ============================================================
# 分批处理
# ============================================================

def init_batch_processing():
    """初始化分批处理"""
    log_message("=" * 60)
    log_message("步骤1: 初始化分批处理")
    log_message("=" * 60)
    
    result = run_command([sys.executable, "batch_processor.py", "init"])
    if result:
        log_message("分批处理会话已初始化")
        return True
    return False

def get_next_batch():
    """获取下一批次"""
    result = run_command([sys.executable, "batch_processor.py", "next"])
    if result and "批次ID" in result.stdout:
        # 解析批次信息
        import re
        match = re.search(r'批次ID:\s*(\S+)', result.stdout)
        if match:
            batch_id = match.group(1)
            log_message(f"获取到批次: {batch_id}")
            return batch_id
    return None

def show_batch_progress():
    """显示分批进度"""
    result = run_command([sys.executable, "batch_processor.py", "progress"])
    if result:
        try:
            print(result.stdout)
        except UnicodeEncodeError:
            # 忽略编码错误，直接显示成功
            log_message("分批进度显示完成")
        return True
    return False

def mark_batch_complete(batch_id):
    """标记批次完成"""
    result = run_command([sys.executable, "batch_processor.py", "complete", batch_id])
    if result:
        log_message(f"批次 {batch_id} 已标记完成")
        return True
    return False

# ============================================================
# AI处理提示
# ============================================================

def show_ai_processing_guide(batch_id):
    """显示AI处理指南"""
    print("\n" + "=" * 60)
    print("🤖 AI处理阶段")
    print("=" * 60)
    print(f"批次 {batch_id} 已准备就绪")
    print("\n请AI执行以下步骤：")
    print("1. 读取批次中的图片")
    print("2. 使用OCR识别文字内容")
    print("3. 整理、分类、生成Markdown")
    print("4. 更新对应的文档")
    print("\n完成后，请运行：")
    print(f"  python full_auto_workflow.py --finish")
    print("=" * 60 + "\n")

# ============================================================
# 收尾流程
# ============================================================

def archive_images():
    """归档图片"""
    log_message("=" * 60)
    log_message("步骤2: 归档图片")
    log_message("=" * 60)
    
    archived = 0
    failed = 0
    
    if not SOURCE_DIR.exists():
        log_message("待处理图片文件夹不存在", "WARN")
        return 0, 0
    
    for folder in SOURCE_DIR.iterdir():
        if folder.is_dir():
            target_folder = TARGET_DIR / folder.name
            target_folder.mkdir(parents=True, exist_ok=True)
            
            for img_file in folder.iterdir():
                if img_file.is_file():
                    try:
                        target_file = target_folder / img_file.name
                        # 处理重名
                        counter = 1
                        while target_file.exists():
                            target_file = target_folder / f"{img_file.stem}_{counter}{img_file.suffix}"
                            counter += 1
                        
                        shutil.move(str(img_file), str(target_file))
                        archived += 1
                        log_message(f"  已归档: {img_file.name}")
                    except Exception as e:
                        failed += 1
                        log_message(f"  失败: {img_file.name} - {e}", "ERROR")
    
    log_message(f"归档完成: {archived} 成功, {failed} 失败")
    return archived, failed

def generate_docx():
    """生成Word文档"""
    log_message("=" * 60)
    log_message("步骤3: 生成Word文档")
    log_message("=" * 60)
    
    script_path = RESULT_DIR / "create_docx.py"
    if not script_path.exists():
        log_message("找不到 create_docx.py", "ERROR")
        return False
    
    result = run_command([sys.executable, str(script_path)], cwd=str(RESULT_DIR))
    if result and result.returncode == 0:
        log_message("Word文档生成完成")
        return True
    return False

def sync_to_ima():
    """同步到ima"""
    log_message("=" * 60)
    log_message("步骤4: 同步到ima")
    log_message("=" * 60)
    
    if not CONFIG_FILE.exists():
        log_message("找不到ima配置文件，跳过同步", "WARN")
        return False
    
    script_path = BASE_DIR / "ima_sync_v2.py"
    if not script_path.exists():
        script_path = BASE_DIR / "ima_sync.py"
    
    if not script_path.exists():
        log_message("找不到ima同步脚本", "ERROR")
        return False
    
    result = run_command([sys.executable, str(script_path)])
    if result and result.returncode == 0:
        log_message("ima同步完成")
        return True
    return False

def update_prompt():
    """更新启动提示词"""
    log_message("=" * 60)
    log_message("步骤5: 更新启动提示词")
    log_message("=" * 60)
    
    script_path = BASE_DIR / "update_prompt.py"
    if not script_path.exists():
        log_message("找不到update_prompt.py", "WARN")
        return False
    
    result = run_command([sys.executable, str(script_path)])
    if result and result.returncode == 0:
        log_message("启动提示词更新完成")
        return True
    return False

def save_log(data):
    """保存处理日志"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append({
        'timestamp': datetime.now().isoformat(),
        'data': data
    })
    logs = logs[-50:]
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# ============================================================
# 主流程
# ============================================================

def main():
    """主流程"""
    print("=" * 60)
    print("图片知识库完整全自动工作流 v1.0")
    print("=" * 60)
    
    # 解析参数
    batch_mode = "--batch" in sys.argv
    finish_mode = "--finish" in sys.argv
    
    start_time = datetime.now()
    
    if finish_mode:
        # 收尾模式：AI处理完成后执行
        log_message("执行收尾流程...")
        
        archived, failed = archive_images()
        docx_ok = generate_docx()
        sync_ok = sync_to_ima()
        prompt_ok = update_prompt()
        
        # 保存日志
        elapsed = (datetime.now() - start_time).total_seconds()
        save_log({
            'mode': 'finish',
            'archived': archived,
            'failed': failed,
            'docx': docx_ok,
            'sync': sync_ok,
            'prompt': prompt_ok,
            'elapsed': elapsed
        })
        
        # 汇总
        print("\n" + "=" * 60)
        print("✅ 收尾流程完成!")
        print(f"  归档: {archived} 成功, {failed} 失败")
        print(f"  Word: {'成功' if docx_ok else '失败'}")
        print(f"  同步: {'成功' if sync_ok else '失败'}")
        print(f"  提示词: {'成功' if prompt_ok else '失败'}")
        print(f"  耗时: {elapsed:.1f} 秒")
        print("=" * 60)
        
    else:
        # 分批模式（默认）
        if not init_batch_processing():
            log_message("初始化失败", "ERROR")
            return
        
        # 显示当前进度
        show_batch_progress()
        
        # 获取下一批次
        batch_id = get_next_batch()
        if batch_id:
            show_ai_processing_guide(batch_id)
        else:
            log_message("没有待处理的批次", "WARN")
            # 询问是否执行收尾
            print("\n是否直接执行收尾流程？")
            print("  python full_auto_workflow.py --finish")

if __name__ == "__main__":
    main()
