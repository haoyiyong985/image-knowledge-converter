#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片知识库全自动处理主控脚本
================================
功能：一键完成图片处理后续流程（归档、生成Word、同步ima、更新提示词）

使用方式：
  python auto_process.py              # 标准模式（扫描→归档→生成→同步→更新提示词）
  python auto_process.py --dry-run    # 模拟运行（不实际执行操作）
  python auto_process.py --sync-only  # 仅执行同步
  python auto_process.py --post-process [folder1,folder2]  # 仅执行后续处理（指定文件夹）

注意：
  分批处理由 batch_processor.py 负责，本脚本不再包含分批逻辑
  新的工作流程：
  1. AI 调用 batch_processor.py init 创建分批会话
  2. AI 调用 batch_processor.py next 获取批次
  3. AI 识别图片内容并整理
  4. AI 调用 batch_processor.py complete 标记完成
  5. 最后调用本脚本执行归档、生成Word、同步ima

作者：AI Assistant
版本：v2.0
更新：移除内部分批逻辑，统一使用 batch_processor.py 进行分批管理
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 导入OCR引擎管理器
try:
    from ocr_engine_manager import get_ocr_manager, create_ocr_config_template
    OCR_MANAGER_AVAILABLE = True
except ImportError:
    OCR_MANAGER_AVAILABLE = False
    print("[WARN] OCR引擎管理器未加载，将使用默认AI视觉识别")

# ============================================================
# 路径配置
# ============================================================
BASE_DIR = Path("D:/新建文件夹")
SOURCE_DIR = BASE_DIR / "待处理图片"
TARGET_DIR = BASE_DIR / "已处理图片"
RESULT_DIR = BASE_DIR / "处理结果"
CONFIG_FILE = BASE_DIR / "ima_config.txt"
LOG_FILE = BASE_DIR / ".workbuddy" / "memory" / "processing_log.json"

# ============================================================
# 分批处理说明
# ============================================================
# 分批处理已由 batch_processor.py 负责，本脚本不再包含分批逻辑
# 请使用: python batch_processor.py init/next/complete/progress

# ============================================================
# 工具函数
# ============================================================

def log_message(msg, level="INFO"):
    """打印并记录日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def scan_images(specific_folders=None):
    """
    扫描待处理图片
    
    Args:
        specific_folders: 指定要扫描的文件夹列表（如 ['示范', '游攻略']），None表示扫描所有
    
    Returns:
        folders: 文件夹信息列表
        all_images: 所有图片路径列表
    """
    log_message("扫描待处理图片...")
    
    all_images = []
    folders = []
    
    if SOURCE_DIR.exists():
        for folder in SOURCE_DIR.iterdir():
            if folder.is_dir():
                # 如果指定了特定文件夹，跳过其他文件夹
                if specific_folders and folder.name not in specific_folders:
                    continue
                    
                folder_images = []
                seen_paths = set()  # 去重
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                    for img_path in folder.glob(ext):
                        if str(img_path) not in seen_paths:
                            seen_paths.add(str(img_path))
                            folder_images.append(img_path)
                    for img_path in folder.glob(ext.upper()):
                        if str(img_path) not in seen_paths:
                            seen_paths.add(str(img_path))
                            folder_images.append(img_path)
                
                if folder_images:
                    folders.append({
                        'name': folder.name,
                        'path': folder,
                        'images': folder_images
                    })
                    all_images.extend(folder_images)
    
    log_message(f"发现 {len(folders)} 个文件夹，共 {len(all_images)} 张图片")
    
    # 显示分批处理状态（由 batch_processor.py 管理）
    try:
        result = subprocess.run(
            [sys.executable, str(BASE_DIR / "batch_processor.py"), "progress"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.returncode == 0:
            log_message("分批处理状态由 batch_processor.py 管理")
    except:
        pass
    
    return folders, all_images

def archive_images(folders):
    """归档已处理图片"""
    log_message("开始归档图片...")
    
    archived_count = 0
    failed_count = 0
    
    for folder in folders:
        source_path = folder['path']
        target_path = TARGET_DIR / folder['name']
        
        # 确保目标目录存在
        target_path.mkdir(parents=True, exist_ok=True)
        
        for img_path in folder['images']:
            try:
                target_file = target_path / img_path.name
                
                # 如果目标已存在，添加数字后缀
                counter = 1
                while target_file.exists():
                    stem = img_path.stem
                    suffix = img_path.suffix
                    target_file = target_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                shutil.move(str(img_path), str(target_file))
                archived_count += 1
                log_message(f"  已归档: {img_path.name}")
                
            except Exception as e:
                failed_count += 1
                log_message(f"  失败: {img_path.name} - {e}", "ERROR")
    
    log_message(f"归档完成: {archived_count} 成功, {failed_count} 失败")
    return archived_count, failed_count

def generate_docx():
    """生成Word文档"""
    log_message("生成Word文档...")
    
    try:
        # 使用现有的create_docx.py
        script_path = RESULT_DIR / "create_docx.py"
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(RESULT_DIR),
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                log_message("Word文档生成完成")
                return True
            else:
                log_message(f"生成失败: {result.stderr}", "ERROR")
                return False
        else:
            log_message("找不到 create_docx.py 脚本", "ERROR")
            return False
    except Exception as e:
        log_message(f"生成异常: {e}", "ERROR")
        return False

def sync_to_ima():
    """同步到ima（使用v2覆盖更新模式）"""
    log_message("同步到ima...")
    
    # 检查配置文件
    if not CONFIG_FILE.exists():
        log_message("找不到ima配置文件，跳过同步", "WARN")
        return False
    
    try:
        # 优先使用ima_sync_v2.py（覆盖更新模式）
        script_path = BASE_DIR / "ima_sync_v2.py"
        if not script_path.exists():
            # 回退到旧版本
            script_path = BASE_DIR / "ima_sync.py"
        
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                log_message("ima同步完成")
                return True
            else:
                log_message(f"同步失败: {result.stderr}", "ERROR")
                return False
        else:
            log_message("找不到 ima_sync 脚本", "ERROR")
            return False
    except Exception as e:
        log_message(f"同步异常: {e}", "ERROR")
        return False

def update_prompt_file():
    """自动更新启动提示词文件"""
    log_message("更新启动提示词...")
    
    try:
        script_path = BASE_DIR / "update_prompt.py"
        if script_path.exists():
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if result.returncode == 0:
                log_message("启动提示词更新完成")
                return True
            else:
                log_message(f"更新失败: {result.stderr}", "ERROR")
                return False
        else:
            log_message("找不到 update_prompt.py 脚本，跳过更新", "WARN")
            return False
    except Exception as e:
        log_message(f"更新异常: {e}", "ERROR")
        return False

def save_processing_log(data):
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
    
    # 只保留最近50条记录
    logs = logs[-50:]
    
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# ============================================================
# 主流程
# ============================================================

def show_ocr_status():
    """显示OCR引擎状态"""
    if OCR_MANAGER_AVAILABLE:
        try:
            manager = get_ocr_manager()
            status = manager.get_status()
            log_message(f"OCR引擎: {status.get('current_engine', 'AI视觉')}")
        except Exception as e:
            log_message(f"OCR状态获取失败: {e}", "WARN")

def show_folder_info(folders):
    """显示文件夹信息"""
    for folder in folders:
        log_message(f"文件夹 '{folder['name']}': {len(folder['images'])}张图片")

def parse_post_process_folders():
    """解析 --post-process 参数中的文件夹列表"""
    for i, arg in enumerate(sys.argv):
        if arg == "--post-process" and i + 1 < len(sys.argv):
            folders_str = sys.argv[i + 1]
            if folders_str.startswith('[') and folders_str.endswith(']'):
                folders_str = folders_str[1:-1]
            return [f.strip() for f in folders_str.split(',') if f.strip()]
    return None

def main():
    """主处理流程"""
    print("=" * 60)
    print("图片知识库全自动处理 v2.0")
    print("=" * 60)
    
    dry_run = "--dry-run" in sys.argv
    sync_only = "--sync-only" in sys.argv
    post_process = "--post-process" in sys.argv
    
    if dry_run:
        log_message("【模拟模式】不会实际执行操作")
    
    # 显示OCR引擎状态
    show_ocr_status()
    
    start_time = datetime.now()
    
    # --post-process 模式：仅执行后续处理（归档、生成Word、同步等）
    if post_process:
        log_message("【后处理模式】仅执行归档、生成Word、同步ima等操作")
        specific_folders = parse_post_process_folders()
        if specific_folders:
            log_message(f"指定文件夹: {', '.join(specific_folders)}")
        
        folders, all_images = scan_images(specific_folders)
        
        if not all_images:
            log_message("没有待处理的图片", "WARN")
            return
        
        show_folder_info(folders)
        
        if dry_run:
            log_message(f"模拟: 将处理 {len(all_images)} 张图片")
            return
        
        # 执行后续处理
        archived, failed = archive_images(folders)
        docx_ok = generate_docx()
        sync_ok = sync_to_ima()
        prompt_ok = update_prompt_file()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        save_processing_log({
            'mode': 'post_process',
            'images_count': len(all_images),
            'archived': archived,
            'failed': failed,
            'docx_generated': docx_ok,
            'synced': sync_ok,
            'prompt_updated': prompt_ok,
            'elapsed_seconds': elapsed
        })
        
        print("\n" + "=" * 60)
        print("后处理完成!")
        print(f"  图片数量: {len(all_images)}")
        print(f"  归档成功: {archived}")
        print(f"  归档失败: {failed}")
        print(f"  Word生成: {'成功' if docx_ok else '失败'}")
        print(f"  ima同步: {'成功' if sync_ok else '失败'}")
        print(f"  提示词更新: {'成功' if prompt_ok else '失败'}")
        print(f"  耗时: {elapsed:.1f} 秒")
        print("=" * 60)
        return
    
    # --sync-only 模式：仅执行同步
    if sync_only:
        sync_to_ima()
        return
    
    # 标准模式
    log_message("【标准模式】扫描待处理图片并执行后续操作")
    log_message("提示: 分批处理请使用 batch_processor.py 管理")
    
    folders, all_images = scan_images()
    
    if not all_images:
        log_message("没有待处理的图片", "WARN")
        return
    
    show_folder_info(folders)
    
    if dry_run:
        log_message(f"模拟: 将处理 {len(all_images)} 张图片")
        return
    
    # 归档图片
    archived, failed = archive_images(folders)
    
    # 生成Word文档
    docx_ok = generate_docx()
    
    # 同步到ima
    sync_ok = sync_to_ima()
    
    # 自动更新启动提示词
    prompt_ok = update_prompt_file()
    
    # 保存日志
    elapsed = (datetime.now() - start_time).total_seconds()
    save_processing_log({
        'mode': 'standard',
        'images_count': len(all_images),
        'archived': archived,
        'failed': failed,
        'docx_generated': docx_ok,
        'synced': sync_ok,
        'prompt_updated': prompt_ok,
        'elapsed_seconds': elapsed
    })
    
    # 汇总
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"  图片数量: {len(all_images)}")
    print(f"  归档成功: {archived}")
    print(f"  归档失败: {failed}")
    print(f"  Word生成: {'成功' if docx_ok else '失败'}")
    print(f"  ima同步: {'成功' if sync_ok else '失败'}")
    print(f"  提示词更新: {'成功' if prompt_ok else '失败'}")
    print(f"  耗时: {elapsed:.1f} 秒")
    print("=" * 60)

if __name__ == "__main__":
    main()
