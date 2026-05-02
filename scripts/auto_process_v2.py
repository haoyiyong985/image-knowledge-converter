#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_process_v2.py — 图片知识库自动处理脚本（增强版）
========================================================
改进点：
  1. 强制同步到 ima（不再是可选步骤）
  2. 同步失败时自动重试3次
  3. 重试仍失败则记录到失败队列，提示用户手动修复
  4. 处理报告中增加同步状态和 doc_id
  5. 支持检查待同步的失败文件

使用方法：
  python auto_process_v2.py         ← 完整流程（扫描→处理→强制同步）
  python auto_process_v2.py --scan  ← 仅扫描，不处理
  python auto_process_v2.py --sync  ← 仅同步（处理失败队列）
  python auto_process_v2.py --status ← 查看同步状态

注意：
  此脚本是整套流程的"骨架"，图片识别部分由 AI（WorkBuddy）完成。
"""

import os
import re
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime

# ============================================================
# 路径配置
# ============================================================
BASE_DIR        = Path("D:/新建文件夹")
PENDING_DIR     = BASE_DIR / "待处理图片"
PROCESSED_DIR   = BASE_DIR / "已处理图片"
RESULT_DIR      = BASE_DIR / "处理结果"
SCRIPTS_DIR     = BASE_DIR / "scripts"

# 同步相关文件
FAILED_SYNC_FILE = BASE_DIR / "ima_sync_failed.json"
SYNC_LOG_FILE    = BASE_DIR / "ima_sync_log.json"

# 图片格式
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 同步重试配置
MAX_SYNC_RETRIES = 3
SYNC_RETRY_DELAY = 3  # 秒


def scan_pending_images():
    """扫描所有待处理图片"""
    result = {}
    if not PENDING_DIR.exists():
        print(f"[错误] 待处理图片目录不存在：{PENDING_DIR}")
        return result

    for topic_dir in PENDING_DIR.iterdir():
        if not topic_dir.is_dir():
            continue
        images = [
            f for f in topic_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if images:
            result[topic_dir.name] = sorted(images)
            print(f"[扫描] 主题「{topic_dir.name}」：发现 {len(images)} 张图片")

    return result


def read_existing_docs_structure():
    """读取现有文档结构"""
    structure = {}
    md_files = sorted(RESULT_DIR.glob("[0-9][0-9]_*.md"))

    for md_path in md_files:
        doc_name = md_path.stem
        content  = md_path.read_text(encoding="utf-8")
        lines    = content.splitlines()

        title    = ""
        sections = []

        for line in lines:
            if line.startswith("# ") and not title:
                title = line[2:].strip()
            elif line.startswith("## "):
                sections.append(line[3:].strip())

        structure[doc_name] = {
            "title":       title,
            "sections":    sections,
            "char_count":  len(content),
        }

    return structure


def print_docs_structure(structure):
    """打印文档结构"""
    print("\n" + "=" * 60)
    print("现有文档结构")
    print("=" * 60)
    if not structure:
        print("[提示] 尚无已有文档")
    else:
        for doc_name, info in structure.items():
            print(f"\n[{doc_name}]")
            print(f"  标题：{info['title']}")
            print(f"  章节数：{len(info['sections'])}，字数：{info['char_count']}")
            if info["sections"]:
                print("  章节列表：")
                for s in info["sections"]:
                    print(f"    - {s}")
    print("=" * 60)


def archive_images(topic, image_paths):
    """归档图片"""
    archive_dir = PROCESSED_DIR / topic
    archive_dir.mkdir(parents=True, exist_ok=True)

    moved = []
    for img_path in image_paths:
        dest = archive_dir / img_path.name
        if dest.exists():
            stem = img_path.stem
            suffix = img_path.suffix
            ts = datetime.now().strftime("%Y%m%d%H%M%S")
            dest = archive_dir / f"{stem}_{ts}{suffix}"
        shutil.move(str(img_path), str(dest))
        moved.append(dest)
        print(f"  [归档] {img_path.name}")

    return moved


def get_next_doc_number():
    """获取下一个文档编号"""
    existing = list(RESULT_DIR.glob("[0-9][0-9]_*.md"))
    return len(existing) + 1


def generate_startup_prompt(structure):
    """生成启动提示词"""
    prompt_path = BASE_DIR / "【启动提示词】新对话粘贴这段.txt"
    today = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    doc_lines = []
    for doc_name, info in structure.items():
        sections_str = "、".join(info["sections"]) if info["sections"] else "（暂无章节）"
        doc_lines.append(
            f"编号{doc_name[:2]}：{doc_name}.docx / .md\n"
            f"  - 文档标题：{info['title']}\n"
            f"  - 现有章节：{sections_str}\n"
            f"  - 字数：约{info['char_count']}字"
        )
    docs_block = "\n\n".join(doc_lines) if doc_lines else "（尚无已有文档）"

    content = f"""你好，请帮我继续处理「图片知识库转化工具 v1.0」项目。以下是项目完整背景，请读取后告诉我你已准备好。

========== 项目背景 ==========

【项目位置】D:\\新建文件夹\\

【任务说明】
将手机截图（小红书、微信读书、微信等来源）中的文字识别出来，
按内容分类整理，合并到对应的 Word 和 Markdown 文档中。

【目录结构】
- 待处理图片\\<主题名>\\   ← 新图片放在这里，按主题建子文件夹
- 已处理图片\\<主题名>\\   ← 处理完的图片自动归档到这里
- 处理结果\\              ← 所有输出的 Word (.docx) 和 Markdown (.md) 文件

【已有文档列表】（最后更新：{today}）
{docs_block}

【处理规则】
1. 识别新图片中的文字内容
2. 判断内容属于哪个分类：
   - 若属于上面已有文档之一 → 追加到对应的 .md 文件末尾（追加，不覆盖）
   - 若是全新主题 → 新建下一编号文档（如 {str(len(structure)+1).zfill(2)}_xxx.md 和 .docx）
3. 每次处理时先读取目标 .md 文件，了解已有章节，避免重复插入
4. 处理完毕后，将图片从 待处理图片\\<主题>\\ 移动到 已处理图片\\<主题>\\
5. 处理完成后调用 auto_process.py 自动刷新本启动提示词文件

【等待指令】
准备好后，我会告诉你接下来要做什么。
常用指令：
========================================
📋 图片知识库转化工具 v1.0 - 常用指令
========================================

- "处理新图片"              → 扫描并处理 待处理图片\\ 下的所有新图片
- "处理待处理图片/<主题名>"  → 只处理指定主题文件夹的图片
- "查看现有文档"            → 列出处理结果目录中的所有文档和章节
- "工具优化"                → 对现有转化工具进行技能提升，增强处理能力

========================================
"""

    prompt_path.write_text(content, encoding="utf-8")
    print(f"\n[更新] 启动提示词已刷新：{prompt_path.name}")


def sync_to_ima(force=False):
    """
    强制同步到 ima
    失败时自动重试，最终失败则记录到失败队列
    """
    print("\n" + "=" * 60)
    print("[Step 5] 同步到 ima 知识库")
    print("=" * 60)
    
    ima_sync_path = BASE_DIR / "ima_sync_v2.py"
    
    if not ima_sync_path.exists():
        print("[错误] 找不到 ima_sync_v2.py，无法同步")
        return {"success": False, "error": "找不到同步脚本"}
    
    # 尝试同步（带重试）
    for attempt in range(1, MAX_SYNC_RETRIES + 1):
        print(f"\n  同步尝试 {attempt}/{MAX_SYNC_RETRIES}...")
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("ima_sync_v2", ima_sync_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            report = module.sync_all(force=force)
            
            if report.get("failed", 0) == 0 and not report.get("error"):
                print(f"\n  [成功] 同步完成！")
                return {
                    "success": True,
                    "total": report.get("total", 0),
                    "synced": report.get("success", 0),
                    "skipped": report.get("skipped", 0),
                    "details": report.get("details", [])
                }
            else:
                error_msg = report.get("error", f"有 {report.get('failed', 0)} 个文档同步失败")
                print(f"  [失败] {error_msg}")
                
                if attempt < MAX_SYNC_RETRIES:
                    print(f"  {SYNC_RETRY_DELAY}秒后重试...")
                    time.sleep(SYNC_RETRY_DELAY)
                else:
                    # 最终失败，记录到失败队列
                    print(f"\n  [警告] 已达到最大重试次数，记录到失败队列")
                    return {
                        "success": False,
                        "error": error_msg,
                        "details": report.get("details", []),
                        "need_manual_fix": True
                    }
                    
        except Exception as e:
            print(f"  [错误] 同步异常：{e}")
            if attempt < MAX_SYNC_RETRIES:
                print(f"  {SYNC_RETRY_DELAY}秒后重试...")
                time.sleep(SYNC_RETRY_DELAY)
            else:
                return {
                    "success": False,
                    "error": str(e),
                    "need_manual_fix": True
                }
    
    return {"success": False, "error": "未知错误"}


def check_failed_sync():
    """检查是否有同步失败的文件"""
    if FAILED_SYNC_FILE.exists():
        try:
            import json
            failed = json.loads(FAILED_SYNC_FILE.read_text(encoding="utf-8"))
            return failed
        except:
            pass
    return {}


def print_sync_report(sync_result):
    """打印同步报告"""
    print("\n" + "=" * 60)
    print("同步报告")
    print("=" * 60)
    
    if sync_result.get("success"):
        print(f"✅ 同步成功")
        print(f"   总计：{sync_result.get('total', 0)} 个文档")
        print(f"   同步：{sync_result.get('synced', 0)} 个")
        print(f"   跳过：{sync_result.get('skipped', 0)} 个（未变更）")
        
        # 显示 doc_id
        details = sync_result.get("details", [])
        if details:
            print("\n   文档详情：")
            for d in details:
                if d.get("status") == "success":
                    doc_id = d.get("doc_id", "unknown")
                    doc_id_short = doc_id[:12] if len(doc_id) > 12 else doc_id
                    print(f"   • {d['doc_name']}: {d.get('action', 'synced')} (doc_id: {doc_id_short}...)")
    else:
        print(f"❌ 同步失败")
        print(f"   错误：{sync_result.get('error', '未知错误')}")
        
        if sync_result.get("need_manual_fix"):
            print("\n   ⚠️ 需要手动修复：")
            print("      1. 检查网络连接")
            print("      2. 确认 ima_config.txt 凭证有效")
            print("      3. 运行：python ima_sync_v2.py --force 手动同步")
            print("      4. 或运行：python auto_process_v2.py --sync 重试失败队列")


def generate_processing_report(topic, image_count, sync_result):
    """生成处理报告"""
    report_path = RESULT_DIR / f"处理报告_{topic}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    
    content = f"""# 图片知识库处理报告

**处理时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}  
**处理主题**：{topic}

---

## 处理统计

| 项目 | 数量 |
|------|------|
| 处理图片 | {image_count} 张 |

---

## 同步状态

"""
    
    if sync_result.get("success"):
        content += f"""
✅ **同步成功**

- 总计文档：{sync_result.get('total', 0)} 个
- 成功同步：{sync_result.get('synced', 0)} 个
- 跳过（未变更）：{sync_result.get('skipped', 0)} 个

### 文档详情

"""
        details = sync_result.get("details", [])
        for d in details:
            if d.get("status") == "success":
                doc_id = d.get("doc_id", "unknown")
                content += f"| {d['doc_name']} | {d.get('action', 'synced')} | {doc_id[:16]}... |\n"
    else:
        content += f"""
❌ **同步失败**

错误信息：{sync_result.get('error', '未知错误')}

**修复建议**：
1. 检查网络连接
2. 确认 ima_config.txt 凭证有效
3. 运行：python ima_sync_v2.py --force 手动同步
4. 或运行：python auto_process_v2.py --sync 重试失败队列
"""
    
    content += f"""
---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    report_path.write_text(content, encoding="utf-8")
    print(f"\n[报告] 处理报告已生成：{report_path.name}")
    return report_path


def main():
    """主函数"""
    scan_only = "--scan" in sys.argv
    sync_only = "--sync" in sys.argv
    show_status = "--status" in sys.argv
    
    # 显示同步状态
    if show_status:
        failed = check_failed_sync()
        print("=" * 60)
        print("同步状态检查")
        print("=" * 60)
        if failed:
            print(f"\n⚠️ 有 {len(failed)} 个文档同步失败：")
            for name, info in failed.items():
                print(f"  • {name}: {info.get('error', '未知错误')}")
            print("\n运行以下命令重试：")
            print("  python auto_process_v2.py --sync")
        else:
            print("\n✅ 所有文档同步正常，无失败记录")
        return
    
    # 仅同步模式（处理失败队列）
    if sync_only:
        print("=" * 60)
        print("同步模式 - 处理失败队列")
        print("=" * 60)
        failed = check_failed_sync()
        if not failed:
            print("\n✅ 没有失败的同步记录")
            return
        print(f"\n发现 {len(failed)} 个失败记录，开始重试...")
        sync_result = sync_to_ima(force=True)
        print_sync_report(sync_result)
        return
    
    # 完整流程
    print("=" * 60)
    print("图片知识库自动处理 v2")
    print("=" * 60)
    
    # 确保目录存在
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # 检查失败队列
    failed = check_failed_sync()
    if failed:
        print(f"\n⚠️ 警告：有 {len(failed)} 个文档之前同步失败")
        print("    本次处理后将自动重试同步")
    
    # 读取文档结构
    if not scan_only:
        print("\n[Step 1] 读取现有文档结构...")
        structure = read_existing_docs_structure()
        print_docs_structure(structure)
        
        print("\n[Step 2] 刷新启动提示词...")
        generate_startup_prompt(structure)
    else:
        structure = {}
        print("\n[模式] 仅扫描")
    
    # 扫描待处理图片
    print("\n[Step 3] 扫描待处理图片...")
    pending = scan_pending_images()
    
    total_images = sum(len(v) for v in pending.values())
    if total_images == 0:
        print("\n[提示] 没有发现新的待处理图片")
        # 即使没有新图片，也尝试同步失败队列
        if failed:
            print("\n[Step 4] 尝试同步之前失败的文档...")
            sync_result = sync_to_ima(force=True)
            print_sync_report(sync_result)
        return
    
    print(f"\n[提示] 发现 {total_images} 张待处理图片")
    print("\n请在 WorkBuddy 中发送「处理新图片」开始处理")
    print("处理完成后将自动同步到 ima")
    
    # 如果用户直接运行此脚本（非 WorkBuddy 触发），提示正确的使用方式
    if "--auto" in sys.argv:
        # 自动模式（由 WorkBuddy 调用）
        print("\n[Step 4] 等待 AI 处理图片...")
        print("（此步骤由 WorkBuddy AI 完成）")
        # 处理完成后会自动调用同步


def after_processing(topic, image_paths):
    """
    处理完成后的回调函数（由 WorkBuddy 调用）
    执行：归档图片 → 同步到 ima → 生成报告
    """
    print("\n" + "=" * 60)
    print("处理完成后自动同步")
    print("=" * 60)
    
    # 归档图片
    print(f"\n[归档] 移动 {len(image_paths)} 张图片到已处理目录...")
    archive_images(topic, image_paths)
    
    # 强制同步到 ima
    sync_result = sync_to_ima(force=False)
    
    # 打印同步报告
    print_sync_report(sync_result)
    
    # 生成处理报告
    report_path = generate_processing_report(topic, len(image_paths), sync_result)
    
    # 刷新启动提示词
    structure = read_existing_docs_structure()
    generate_startup_prompt(structure)
    
    return {
        "sync_result": sync_result,
        "report_path": str(report_path)
    }


if __name__ == "__main__":
    main()
