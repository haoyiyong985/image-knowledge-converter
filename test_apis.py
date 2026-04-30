#!/usr/bin/env python3
"""测试三个API的可用性"""
import requests
import os
from dotenv import load_dotenv

load_dotenv()

print('=== API 可用性测试 ===')
print()

# 1. 测试 Kimi
print('1. Kimi 测试...')
try:
    resp = requests.post(
        'https://api.moonshot.cn/v1/chat/completions',
        json={'model': 'moonshot-v1-8k', 'messages': [{'role': 'user', 'content': '你好'}], 'temperature': 0.3},
        headers={'Authorization': f'Bearer {os.getenv("MOONSHOT_API_KEY")}'},
        timeout=10
    )
    print(f'   状态码: {resp.status_code}')
    if resp.status_code == 200:
        print('   可用')
    elif resp.status_code == 429:
        print('   429 - 余额不足或超限')
        print(f'   详情: {resp.text[:200]}')
    else:
        print(f'   错误: {resp.text[:200]}')
except Exception as e:
    print(f'   异常: {e}')

print()

# 2. 测试硅基流动
print('2. 硅基流动测试...')
try:
    resp = requests.post(
        'https://api.siliconflow.cn/v1/chat/completions',
        json={'model': os.getenv('SILICONFLOW_MODEL', 'Qwen/Qwen3-8B'), 'messages': [{'role': 'user', 'content': '你好'}], 'max_tokens': 50, 'temperature': 0.3},
        headers={'Authorization': f'Bearer {os.getenv("SILICONFLOW_API_KEY")}'},
        timeout=15
    )
    print(f'   状态码: {resp.status_code}')
    if resp.status_code == 200:
        print('   可用')
    else:
        print(f'   错误: {resp.text[:200]}')
except Exception as e:
    print(f'   异常: {e}')

print()

# 3. 测试豆包
print('3. 豆包测试...')
try:
    base_url = os.getenv('DOUBAO_BASE_URL', 'https://ark.cn-beijing.volces.com/api/v3')
    resp = requests.post(
        f"{base_url}/chat/completions",
        json={'model': os.getenv('DOUBAO_MODEL', 'volcengine/doubao-seed-2.0-mini'), 'messages': [{'role': 'user', 'content': '你好'}], 'temperature': 0.3},
        headers={'Authorization': f'Bearer {os.getenv("DOUBAO_API_KEY")}'},
        timeout=15
    )
    print(f'   状态码: {resp.status_code}')
    if resp.status_code == 200:
        print('   可用')
    else:
        print(f'   错误: {resp.text[:200]}')
except Exception as e:
    print(f'   异常: {e}')
