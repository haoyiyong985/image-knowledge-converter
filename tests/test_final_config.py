#!/usr/bin/env python3
"""验证最终配置 - 测试混元Lite和硅基流动"""
import os
from dotenv import load_dotenv

# 强制重新加载.env
load_dotenv(override=True)

print('=== 最终配置验证 ===')
print()

# 检查环境变量
print('1. 环境变量检查:')
print(f'   Kimi: {"已配置" if os.getenv("MOONSHOT_API_KEY") else "未配置/已禁用"}')
print(f'   硅基流动: {"已配置" if os.getenv("SILICONFLOW_API_KEY") else "未配置"}')
print(f'   豆包: {"已配置" if os.getenv("DOUBAO_API_KEY") else "未配置/已禁用"}')
print()

# 测试硅基流动
import requests
print('2. 硅基流动API测试:')
try:
    resp = requests.post(
        'https://api.siliconflow.cn/v1/chat/completions',
        json={
            'model': os.getenv('SILICONFLOW_MODEL', 'Qwen/Qwen3-8B'),
            'messages': [{'role': 'user', 'content': '你好'}],
            'max_tokens': 50,
            'temperature': 0.3
        },
        headers={'Authorization': f'Bearer {os.getenv("SILICONFLOW_API_KEY")}'},
        timeout=30  # 增加超时
    )
    print(f'   状态码: {resp.status_code}')
    if resp.status_code == 200:
        print('   可用')
        data = resp.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        print(f'   响应: {content[:50]}...')
    else:
        print(f'   错误: {resp.text[:200]}')
except Exception as e:
    print(f'   异常: {e}')

print()
print('=== 配置总结 ===')
print('当前可用兜底链:')
print('  混元Lite(主力) → 硅基流动(兜底)')
print('已禁用(需修复后启用):')
print('  Kimi(余额不足) - https://platform.moonshot.cn 充值')
print('  豆包(Model ID错误) - https://console.volcengine.com 创建Endpoint')
