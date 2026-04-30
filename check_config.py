#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查所有OCR和IMA配置"""

import os
import sys
from pathlib import Path

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("配置检查")
print("=" * 60)

print("\n[1] 腾讯云 OCR:")
tencent_id = os.getenv("TENCENT_SECRET_ID", "")
tencent_key = os.getenv("TENCENT_SECRET_KEY", "")
if tencent_id and "替换" not in tencent_id:
    print(f"    SecretId: {tencent_id[:8]}...")
    print(f"    SecretKey: {tencent_key[:8]}...")
else:
    print("    [未配置]")

print("\n[2] 百度云 OCR:")
baidu_appid = os.getenv("BAIDU_APP_ID", "")
baidu_apikey = os.getenv("BAIDU_API_KEY", "")
if baidu_appid and "替换" not in baidu_appid:
    print(f"    AppID: {baidu_appid}")
    print(f"    APIKey: {baidu_apikey[:10]}...")
else:
    print("    [未配置]")

print("\n[3] IMA 笔记:")
ima_clientid = os.getenv("IMA_OPENAPI_CLIENTID", "")
ima_apikey = os.getenv("IMA_OPENAPI_APIKEY", "")
if ima_clientid and "替换" not in ima_clientid:
    print(f"    ClientID: {ima_clientid[:10]}...")
    print(f"    APIKey: {ima_apikey[:10]}...")
else:
    print("    [未配置]")

print("\n" + "=" * 60)
print("模块检查")
print("=" * 60)

# 百度云
try:
    from aip import AipOcr
    print("\n[OK] 百度云OCR (baidu-aip)")
except ImportError as e:
    print(f"\n[FAIL] 百度云OCR: {e}")

# 腾讯云
try:
    from tencentcloud.common import credential
    print("[OK] 腾讯云 (tencentcloud-sdk-python)")
except ImportError as e:
    print(f"[FAIL] 腾讯云: {e}")

# IMA
try:
    import requests
    print("[OK] requests (IMA需要)")
except ImportError as e:
    print(f"[FAIL] requests: {e}")

print("\n" + "=" * 60)
