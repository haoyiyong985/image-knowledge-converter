#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ima_sync_v2.py — 改进版ima同步脚本（覆盖更新模式）
=====================================================
解决问题：原脚本追加更新导致ima文档内容越来越长
解决方案：删除旧文档 → 重新导入完整新文档

功能：
  1. 读取 ima_config.txt 中的 API 凭证
  2. 扫描 处理结果/*.md 文件
  3. 文件有变更时：删除ima旧文档 → 重新导入完整新文档
  4. 文件未变更时：跳过
  5. 记录同步日志

使用方法：
  python ima_sync_v2.py          # 智能同步（变更的覆盖更新，未变更的跳过）
  python ima_sync_v2.py --force  # 强制重新同步所有文件（删除后重新导入）
  python ima_sync_v2.py --check  # 仅检查凭证是否有效

注意：
  运行前请先在 ima_config.txt 中填入你的 ClientID 和 APIKey
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# ============================================================
# 路径配置
# ============================================================
BASE_DIR    = Path("D:/新建文件夹")
RESULT_DIR  = BASE_DIR / "处理结果"
CONFIG_FILE = BASE_DIR / "ima_config.txt"
LOG_FILE    = BASE_DIR / ".workbuddy" / "memory" / "ima_sync_log.json"

# ima OpenAPI 基础地址
IMA_API_BASE = "https://ima.qq.com/openapi/note/v1"


# ============================================================
# 工具函数
# ============================================================

def load_config() -> tuple[str, str]:
    """从 ima_config.txt 读取凭证，返回 (client_id, api_key)"""
    if not CONFIG_FILE.exists():
        print(f"[错误] 找不到配置文件：{CONFIG_FILE}")
        print("       请确认 ima_config.txt 在 D:\\新建文件夹\\ 目录下")
        sys.exit(1)

    client_id = ""
    api_key   = ""

    for line in CONFIG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key   = key.strip()
        value = value.strip()
        if key == "IMA_CLIENT_ID":
            client_id = value
        elif key == "IMA_API_KEY":
            api_key = value

    # 检查是否还是占位文字
    if not client_id or "填入" in client_id:
        print("[错误] ima_config.txt 中的 IMA_CLIENT_ID 还没有填写！")
        print("       请打开 D:\\新建文件夹\\ima_config.txt，填入真实的 ClientID")
        sys.exit(1)
    if not api_key or "填入" in api_key:
        print("[错误] ima_config.txt 中的 IMA_API_KEY 还没有填写！")
        print("       请打开 D:\\新建文件夹\\ima_config.txt，填入真实的 APIKey")
        sys.exit(1)

    return client_id, api_key


def load_sync_log() -> dict:
    """读取同步日志（记录哪些文件已经同步过，以及对应的 doc_id）"""
    if LOG_FILE.exists():
        try:
            return json.loads(LOG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_sync_log(log: dict):
    """保存同步日志"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text(
        json.dumps(log, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def ima_request(endpoint: str, payload: dict, client_id: str, api_key: str) -> dict:
    """
    向 ima OpenAPI 发送 POST 请求
    返回响应的 JSON 字典，失败时返回 {"error": "..."}
    """
    url  = f"{IMA_API_BASE}/{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type":          "application/json",
            "ima-openapi-clientid":  client_id,
            "ima-openapi-apikey":    api_key,
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {e.code}: {body}"}
    except urllib.error.URLError as e:
        return {"error": f"网络错误: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def check_credentials(client_id: str, api_key: str) -> bool:
    """用「获取笔记本列表」接口验证凭证是否有效"""
    print("  正在验证 API 凭证...")
    result = ima_request(
        "list_note_folder_by_cursor",
        {"cursor": "0", "limit": 1},
        client_id, api_key
    )
    if "error" in result:
        print(f"  [失败] {result['error']}")
        return False

    # ima API 返回结构：{"code": 0, "msg": "success", "data": {...}}
    if result.get("code") == 0 and "data" in result:
        data = result["data"]
        folder_count = len(data.get("note_book_folders", []))
        print(f"  [成功] 凭证验证通过！（当前笔记本数：{folder_count}）")
        return True
    # 兼容旧结构（直接返回数据）
    elif "is_end" in result or "note_book_folders" in result:
        folder_count = len(result.get("note_book_folders", []))
        print(f"  [成功] 凭证验证通过！（当前笔记本数：{folder_count}）")
        return True
    else:
        print(f"  [失败] 返回内容异常：{result}")
        return False


def delete_doc_from_ima(doc_id: str, client_id: str, api_key: str) -> bool:
    """
    从 ima 删除指定文档
    成功返回 True，失败返回 False
    """
    if not doc_id or doc_id == "unknown" or doc_id == "imported_no_id":
        return False
    
    # 尝试使用 delete_doc 接口，如果不存在则尝试 trash_doc
    result = ima_request(
        "delete_doc",
        {"doc_id": doc_id},
        client_id, api_key
    )
    
    # 如果 delete_doc 失败，尝试 trash_doc（移到回收站）
    if "error" in result:
        result = ima_request(
            "trash_doc",
            {"doc_id": doc_id},
            client_id, api_key
        )
    
    if "error" in result:
        # 如果文档不存在，也认为是成功的（已经删除了）
        if "not found" in result.get("error", "").lower() or "404" in result.get("error", ""):
            return True
        print(f"    [删除失败] {result['error']}")
        return False
    
    return True


def import_md_to_ima(md_path: Path, client_id: str, api_key: str) -> str | None:
    """
    将一个 .md 文件导入到 ima 个人笔记。
    成功返回 doc_id（字符串），失败返回 None。
    """
    content = md_path.read_text(encoding="utf-8")

    result = ima_request(
        "import_doc",
        {
            "content":        content,
            "content_format": 1,   # 1 = Markdown
        },
        client_id, api_key
    )

    if "error" in result:
        print(f"    [失败] 网络/请求错误：{result['error']}")
        return None

    # ima 返回格式：{"code": 0, "msg": "success", "data": {"note_id": "xxx"}}
    doc_id = (
        result.get("doc_id")
        or result.get("data", {}).get("note_id")  # 新API使用note_id
        or result.get("data", {}).get("doc_id")
        or result.get("data", {}).get("id")
        or result.get("id")
    )
    if doc_id:
        return str(doc_id)
    else:
        print(f"    [警告] 请求成功但未找到 doc_id，完整响应：{result}")
        return "imported_no_id"


# ============================================================
# 主流程
# ============================================================

def sync_all(force: bool = False):
    """
    扫描 处理结果/*.md，逐一同步到 ima。
    改进策略：文件有变更时，删除旧文档 → 重新导入完整新文档
    force=True 时强制重新同步所有文件。
    """
    print("=" * 60)
    print("ima 知识库自动同步 v2（覆盖更新模式）")
    print("=" * 60)

    # 1. 读取凭证
    print("\n[Step 1] 读取 API 凭证...")
    client_id, api_key = load_config()
    print(f"  ClientID: {client_id[:6]}{'*' * (len(client_id)-6)}")
    print(f"  APIKey:   {'*' * 8}（已隐藏）")

    # 2. 验证凭证
    print("\n[Step 2] 验证凭证...")
    if not check_credentials(client_id, api_key):
        print("\n[中止] 凭证无效，请检查 ima_config.txt 中的配置。")
        print("       也可能是网络问题，稍后重试。")
        return

    # 3. 扫描 MD 文件
    print("\n[Step 3] 扫描待同步文件...")
    md_files = sorted(RESULT_DIR.glob("[0-9][0-9]_*.md"))
    if not md_files:
        print("  [提示] 没有找到任何 .md 文件，请先处理图片生成文档。")
        return
    print(f"  找到 {len(md_files)} 个文档：")
    for f in md_files:
        print(f"    - {f.name}")

    # 4. 读取同步日志
    sync_log = load_sync_log()

    # 5. 逐一同步
    print(f"\n[Step 4] 开始同步{'（强制模式，全部重新导入）' if force else ''}...")
    print("  策略：文件变更时删除旧文档 → 重新导入完整新文档\n")
    
    success_count = 0
    skip_count    = 0
    fail_count    = 0
    skipped_files = []  # 记录跳过的文件

    for md_path in md_files:
        doc_name = md_path.stem

        # 获取文件最后修改时间
        mtime = md_path.stat().st_mtime

        if doc_name in sync_log and not force:
            last_sync_mtime = sync_log[doc_name].get("mtime", 0)
            if mtime <= last_sync_mtime:
                # 文件未变更，记录到跳过列表，不显示详细日志
                skip_count += 1
                skipped_files.append(md_path.name)
                continue
            else:
                # 文件有变更：删除旧文档 → 重新导入
                print(f"  [更新] {md_path.name}")
                old_doc_id = sync_log[doc_name].get("doc_id", "")
                
                # 删除旧文档
                if old_doc_id and old_doc_id not in ["unknown", "imported_no_id"]:
                    print(f"      正在删除旧文档...")
                    if delete_doc_from_ima(old_doc_id, client_id, api_key):
                        print("      旧文档已删除")
                    else:
                        print("      旧文档删除失败，继续导入新文档...")
                
                # 导入新文档
                print("      正在导入新文档...")
                doc_id = import_md_to_ima(md_path, client_id, api_key)
                if doc_id:
                    sync_log[doc_name] = {
                        "doc_id":     doc_id,
                        "mtime":      mtime,
                        "first_sync": sync_log[doc_name].get("first_sync", datetime.now().isoformat()),
                        "last_sync":  datetime.now().isoformat(),
                        "sync_count": sync_log[doc_name].get("sync_count", 1) + 1,
                    }
                    print(f"      [OK] 已覆盖更新")
                    success_count += 1
                else:
                    fail_count += 1
        else:
            # 首次同步或强制重新导入
            action = "强制重新导入" if force and doc_name in sync_log else "首次导入"
            print(f"  [{action}] {md_path.name}")
            
            # 如果是强制模式，先尝试删除旧文档
            if force and doc_name in sync_log:
                old_doc_id = sync_log[doc_name].get("doc_id", "")
                if old_doc_id and old_doc_id not in ["unknown", "imported_no_id"]:
                    print(f"      正在删除旧文档...")
                    delete_doc_from_ima(old_doc_id, client_id, api_key)
            
            doc_id = import_md_to_ima(md_path, client_id, api_key)
            if doc_id:
                sync_log[doc_name] = {
                    "doc_id":     doc_id,
                    "mtime":      mtime,
                    "first_sync": datetime.now().isoformat(),
                    "last_sync":  datetime.now().isoformat(),
                    "sync_count": 1,
                }
                print(f"      [OK] 已导入")
                success_count += 1
            else:
                fail_count += 1

        # 每次操作后保存日志
        save_sync_log(sync_log)

        # 礼貌地暂停一下
        time.sleep(0.5)
    
    # 显示跳过的文件摘要（如果数量不多）
    if skipped_files and len(skipped_files) <= 5:
        print(f"\n  [跳过] {len(skipped_files)} 个文件未变更：")
        for f in skipped_files:
            print(f"      - {f}")
    elif skipped_files:
        print(f"\n  [跳过] {len(skipped_files)} 个文件未变更（使用 --force 可强制重新同步）")

    # 6. 汇总结果
    print("\n" + "=" * 60)
    print("同步完成！")
    print(f"  [OK] 成功：{success_count} 个")
    if skip_count > 0:
        print(f"  [--] 跳过：{skip_count} 个（文件未变更）")
    if fail_count > 0:
        print(f"  [XX] 失败：{fail_count} 个")
    print("=" * 60)

    if fail_count > 0:
        print("\n[提示] 有文件同步失败，可能原因：")
        print("  1. 网络不稳定 → 稍后重新运行脚本即可")
        print("  2. API Key 过期 → 去 https://ima.qq.com/agent-interface 刷新 Key")
        print("  3. 文件内容过大 → ima 单个笔记有大小限制")

    if success_count > 0:
        print(f"\n[提示] 请打开 ima 客户端，在「笔记」中查看刚导入的内容。")
        print("[改进] 本次同步采用覆盖更新模式，ima中只保留最新版本。")

    # 7. API Key 到期提醒
    print(f"\n[提醒] 你的 API Key 有效期至 2026-04-16，请在到期前刷新。")


# ============================================================
# 入口
# ============================================================
if __name__ == "__main__":
    if "--check" in sys.argv:
        print("=" * 60)
        print("仅验证 API 凭证")
        print("=" * 60)
        cid, key = load_config()
        check_credentials(cid, key)
    elif "--force" in sys.argv:
        sync_all(force=True)
    else:
        sync_all(force=False)
