#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试脚本：检查凭证读取是否正确，并测试 ima API"""
import urllib.request
import urllib.error
import json
from pathlib import Path

CONFIG_FILE = Path("D:/新建文件夹/ima_config.txt")

# ── 1. 读取并打印凭证原始内容（用 repr 显示隐藏字符）──
print("=" * 60)
print("第一步：检查配置文件读取")
print("=" * 60)

raw = CONFIG_FILE.read_text(encoding="utf-8")
client_id = ""
api_key   = ""

for line in raw.splitlines():
    stripped = line.strip()
    if stripped.startswith("#") or "=" not in stripped:
        continue
    k, _, v = stripped.partition("=")
    k = k.strip()
    v = v.strip()
    if k == "IMA_CLIENT_ID":
        client_id = v
    elif k == "IMA_API_KEY":
        api_key = v

print(f"  ClientID 长度: {len(client_id)}")
print(f"  ClientID 内容: {client_id}")
print(f"  APIKey 长度:   {len(api_key)}")
print(f"  APIKey 前10位: {api_key[:10]}...")
print(f"  APIKey repr:   {repr(api_key[:20])}...（检查有无异常字符）")

# ── 2. 发送请求并打印完整响应 ──
print("\n" + "=" * 60)
print("第二步：发送 API 请求")
print("=" * 60)

endpoints_to_try = [
    ("list_note_folder_by_cursor", {"cursor": "0", "limit": 1}),
    ("search_note_book", {"search_type": 0, "query_info": {"title": "test"}, "start": 0, "end": 1}),
]

for endpoint, payload in endpoints_to_try:
    url  = f"https://ima.qq.com/openapi/note/v1/{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(
        url, data=data,
        headers={
            "Content-Type":         "application/json",
            "ima-openapi-clientid": client_id,
            "ima-openapi-apikey":   api_key,
        },
        method="POST"
    )
    print(f"\n  >>> POST /{endpoint}")
    print(f"      clientid header 值: {client_id}")
    print(f"      apikey header 前20: {api_key[:20]}...")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            print(f"      状态码: {resp.status} [OK]")
            print(f"      响应体: {body[:300]}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"      状态码: {e.code} [FAIL]  ({e.reason})")
        print(f"      响应体: '{body}' （空=服务端直接拒绝，非空=有错误说明）")
        print(f"      响应头: {dict(e.headers)}")
    except Exception as ex:
        print(f"      ERROR: {ex}")
