#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_sync.py — 定时自动同步脚本
================================
功能：
  1. 定时检查处理结果目录的变更
  2. 自动同步变更的文件到 ima
  3. 可作为后台服务运行
  4. 支持 Windows 任务计划程序

使用方法：
  python auto_sync.py              ← 单次同步（立即执行一次）
  python auto_sync.py --daemon     ← 守护模式（每30分钟检查一次）
  python auto_sync.py --install    ← 安装到 Windows 任务计划程序
  python auto_sync.py --status     ← 查看同步状态
  python auto_sync.py --retry      ← 重试失败的同步

定时配置（守护模式）：
  默认每 30 分钟检查一次
  可通过 --interval 参数调整（单位：分钟）
"""

import os
import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime

# 路径配置
BASE_DIR = Path("D:/新建文件夹")
RESULT_DIR = BASE_DIR / "处理结果"
SYNC_LOG_FILE = BASE_DIR / "ima_sync_log.json"
FAILED_SYNC_FILE = BASE_DIR / "ima_sync_failed.json"
AUTO_SYNC_LOG = BASE_DIR / "auto_sync.log"

# 默认检查间隔（分钟）
DEFAULT_INTERVAL = 30


def log_message(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    
    # 写入日志文件
    with open(AUTO_SYNC_LOG, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


def calculate_file_hash(filepath):
    """计算文件哈希"""
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    except:
        return None


def load_sync_log():
    """加载同步日志"""
    if SYNC_LOG_FILE.exists():
        try:
            return json.loads(SYNC_LOG_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}


def load_failed_log():
    """加载失败日志"""
    if FAILED_SYNC_FILE.exists():
        try:
            return json.loads(FAILED_SYNC_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}


def get_changed_files():
    """
    获取有变更的文件列表
    返回: [(文件名, 变更类型), ...]
    变更类型: "new" | "modified"
    """
    sync_log = load_sync_log()
    changed = []
    
    md_files = list(RESULT_DIR.glob("[0-9][0-9]_*.md"))
    
    for md_path in md_files:
        doc_name = md_path.stem
        current_hash = calculate_file_hash(md_path)
        
        if not current_hash:
            continue
        
        if doc_name not in sync_log:
            # 新文件
            changed.append((doc_name, "new"))
        elif sync_log[doc_name].get("content_hash") != current_hash:
            # 有变更
            changed.append((doc_name, "modified"))
    
    return changed


def run_sync(force=False, retry_failed=False):
    """
    执行同步
    返回: (success: bool, message: str)
    """
    ima_sync_path = BASE_DIR / "ima_sync_v2.py"
    
    if not ima_sync_path.exists():
        return False, "找不到 ima_sync_v2.py"
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("ima_sync_v2", ima_sync_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if retry_failed:
            # 只重试失败的
            failed = load_failed_log()
            if not failed:
                return True, "没有失败的同步记录"
            log_message(f"重试 {len(failed)} 个失败的文档...")
            report = module.sync_all(force=True)
        else:
            # 正常同步
            report = module.sync_all(force=force)
        
        if report.get("error"):
            return False, report["error"]
        
        success_count = report.get("success", 0)
        failed_count = report.get("failed", 0)
        skipped_count = report.get("skipped", 0)
        
        msg = f"同步完成: 成功{success_count}, 失败{failed_count}, 跳过{skipped_count}"
        return failed_count == 0, msg
        
    except Exception as e:
        return False, f"同步异常: {e}"


def single_sync():
    """单次同步"""
    log_message("=" * 60)
    log_message("开始单次同步检查")
    log_message("=" * 60)
    
    # 检查是否有变更
    changed = get_changed_files()
    failed = load_failed_log()
    
    if not changed and not failed:
        log_message("没有变更的文件，无需同步")
        return True
    
    if changed:
        log_message(f"检测到 {len(changed)} 个文件有变更:")
        for name, change_type in changed:
            type_str = "新增" if change_type == "new" else "修改"
            log_message(f"  - {name} ({type_str})")
    
    if failed:
        log_message(f"有 {len(failed)} 个文件之前同步失败，将一并重试")
    
    # 执行同步
    log_message("\n开始同步...")
    success, msg = run_sync(force=False)
    log_message(msg)
    
    return success


def daemon_mode(interval_minutes=DEFAULT_INTERVAL):
    """守护模式 - 定时检查并同步"""
    interval_seconds = interval_minutes * 60
    
    log_message("=" * 60)
    log_message(f"启动守护模式 (检查间隔: {interval_minutes}分钟)")
    log_message("=" * 60)
    log_message("按 Ctrl+C 停止")
    
    try:
        while True:
            single_sync()
            
            next_check = datetime.now().timestamp() + interval_seconds
            next_check_str = datetime.fromtimestamp(next_check).strftime("%H:%M:%S")
            log_message(f"\n下次检查时间: {next_check_str}")
            log_message("-" * 60)
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        log_message("\n守护模式已停止")


def install_scheduler():
    """安装到 Windows 任务计划程序"""
    import subprocess
    
    script_path = Path(__file__).resolve()
    task_name = "ImageKnowledgeBase_AutoSync"
    
    # 创建任务命令
    cmd = [
        "schtasks",
        "/create",
        "/tn", task_name,
        "/tr", f'"{sys.executable}" "{script_path}"',
        "/sc", "minute",
        "/mo", str(DEFAULT_INTERVAL),
        "/f",  # 强制覆盖
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 定时任务已创建: {task_name}")
            print(f"   执行频率: 每 {DEFAULT_INTERVAL} 分钟")
            print(f"   脚本路径: {script_path}")
            print("\n管理命令:")
            print(f"   查看: schtasks /query /tn {task_name}")
            print(f"   删除: schtasks /delete /tn {task_name} /f")
            print(f"   运行: schtasks /run /tn {task_name}")
        else:
            print(f"❌ 创建失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 错误: {e}")


def show_status():
    """显示同步状态"""
    print("=" * 60)
    print("自动同步状态")
    print("=" * 60)
    
    sync_log = load_sync_log()
    failed_log = load_failed_log()
    
    print(f"\n已同步文档: {len(sync_log)} 个")
    print(f"失败文档: {len(failed_log)} 个")
    
    if sync_log:
        print("\n已同步列表:")
        for name, info in sync_log.items():
            last_sync = info.get("last_sync", "未知")[:19]
            print(f"  - {name} (上次同步: {last_sync})")
    
    if failed_log:
        print("\n[警告] 失败列表:")
        for name, info in failed_log.items():
            error = info.get("error", "未知错误")[:50]
            print(f"  - {name}: {error}...")
        print("\n修复命令: python auto_sync.py --retry")
    
    # 检查变更
    changed = get_changed_files()
    if changed:
        print(f"\n[待同步] 变更: {len(changed)} 个")
        for name, change_type in changed:
            type_str = "新增" if change_type == "new" else "修改"
            print(f"  - {name} ({type_str})")
    else:
        print("\n[OK] 所有文件已同步")
    
    # 检查日志
    if AUTO_SYNC_LOG.exists():
        log_size = AUTO_SYNC_LOG.stat().st_size
        print(f"\n日志文件: {AUTO_SYNC_LOG} ({log_size/1024:.1f} KB)")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ima 知识库自动同步工具")
    parser.add_argument("--daemon", action="store_true", help="守护模式")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="检查间隔（分钟）")
    parser.add_argument("--install", action="store_true", help="安装到任务计划程序")
    parser.add_argument("--status", action="store_true", help="查看状态")
    parser.add_argument("--retry", action="store_true", help="重试失败的同步")
    parser.add_argument("--force", action="store_true", help="强制重新同步所有文件")
    
    args = parser.parse_args()
    
    if args.install:
        install_scheduler()
    elif args.status:
        show_status()
    elif args.retry:
        log_message("重试失败的同步...")
        success, msg = run_sync(retry_failed=True)
        log_message(msg)
    elif args.force:
        log_message("强制重新同步所有文件...")
        success, msg = run_sync(force=True)
        log_message(msg)
    elif args.daemon:
        daemon_mode(args.interval)
    else:
        # 默认单次同步
        single_sync()


if __name__ == "__main__":
    main()
