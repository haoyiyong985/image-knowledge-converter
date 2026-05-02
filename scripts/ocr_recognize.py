#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR识别脚本 - 多引擎自动切换
=============================
调用顺序: 腾讯云 → 百度云 → AI视觉(返回标记)

使用方法:
  python ocr_recognize.py <图片路径>

返回:
  - 成功: 打印识别到的文字
  - 失败: 打印错误信息，返回空字符串或AI视觉标记
"""

import sys
import json
import base64
import hmac
import hashlib
import time
import urllib.request
import urllib.parse
from pathlib import Path

# 路径配置
CONFIG_FILE = Path("D:/新建文件夹/ocr_config.json")


def load_config():
    """加载OCR配置"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] 加载配置失败: {e}", file=sys.stderr)
    return {}


def recognize_tencent(image_path: str, config: dict) -> str:
    """腾讯云OCR识别"""
    secret_id = config['tencent']['secret_id']
    secret_key = config['tencent']['secret_key']
    
    # 读取图片
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 构建请求参数
    payload = {"ImageBase64": image_base64}
    
    # 构建签名
    endpoint = "ocr.tencentcloudapi.com"
    service = "ocr"
    version = "2018-11-19"
    action = "GeneralBasicOCR"
    region = "ap-guangzhou"
    
    timestamp = int(time.time())
    date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
    
    # 构建规范请求
    http_request_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    canonical_headers = f"content-type:application/json\nhost:{endpoint}\n"
    signed_headers = "content-type;host"
    payload_hash = hashlib.sha256(json.dumps(payload).encode('utf-8')).hexdigest()
    canonical_request = f"{http_request_method}\n{canonical_uri}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
    
    # 构建待签名字符串
    algorithm = "TC3-HMAC-SHA256"
    credential_scope = f"{date}/{service}/tc3_request"
    string_to_sign = f"{algorithm}\n{timestamp}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
    
    # 计算签名
    secret_date = hmac.new(f"TC3{secret_key}".encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    secret_service = hmac.new(secret_date, service.encode('utf-8'), hashlib.sha256).digest()
    secret_signing = hmac.new(secret_service, "tc3_request".encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
    
    # 构建Authorization
    authorization = f"{algorithm} Credential={secret_id}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    # 发送请求
    url = f"https://{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "Host": endpoint,
        "X-TC-Action": action,
        "X-TC-Version": version,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Region": region,
        "Authorization": authorization
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
    response = urllib.request.urlopen(req, timeout=30)
    result = json.loads(response.read().decode('utf-8'))
    
    if 'Response' in result and 'Error' in result['Response']:
        error = result['Response']['Error']
        raise Exception(f"腾讯云OCR错误: {error.get('Code')} - {error.get('Message')}")
    
    # 提取文字
    words = []
    for item in result.get('Response', {}).get('TextDetections', []):
        words.append(item.get('DetectedText', ''))
    
    return '\n'.join(words)


def recognize_baidu(image_path: str, config: dict) -> str:
    """百度云OCR识别 - 使用高精度版"""
    api_key = config['baidu']['api_key']
    secret_key = config['baidu']['secret_key']
    
    # 获取access_token
    token_url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
    response = urllib.request.urlopen(token_url, timeout=10)
    token_result = json.loads(response.read().decode('utf-8'))
    access_token = token_result['access_token']
    
    # 读取图片
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # 构建请求 - 使用标准版 general_basic（免费额度更多）
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = urllib.parse.urlencode({
        'image': image_base64,
        'language_type': 'CHN_ENG'
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    response = urllib.request.urlopen(req, timeout=30)
    result = json.loads(response.read().decode('utf-8'))
    
    if 'error_code' in result:
        raise Exception(f"百度云OCR错误: {result['error_msg']}")
    
    # 提取文字
    words = []
    for item in result.get('words_result', []):
        words.append(item['words'])
    
    return '\n'.join(words)


def recognize_image(image_path: str) -> tuple:
    """
    识别图片文字，按优先级尝试不同引擎
    
    Returns:
        (识别结果, 使用的引擎)
        识别结果: 识别到的文字，或空字符串，或"__AI_VISION__"
        使用的引擎: 引擎名称
    """
    config = load_config()
    
    # 1. 尝试腾讯云OCR
    if config.get('tencent', {}).get('secret_id') and config.get('tencent', {}).get('secret_key'):
        try:
            result = recognize_tencent(image_path, config)
            if result:
                return result, "腾讯云OCR"
        except Exception as e:
            print(f"[WARN] 腾讯云OCR失败: {e}", file=sys.stderr)
    
    # 2. 尝试百度云OCR
    if config.get('baidu', {}).get('api_key') and config.get('baidu', {}).get('secret_key'):
        try:
            result = recognize_baidu(image_path, config)
            if result:
                return result, "百度云OCR"
        except Exception as e:
            print(f"[WARN] 百度云OCR失败: {e}", file=sys.stderr)
    
    # 3. 回退到AI视觉
    return "__AI_VISION__", "AI视觉识别"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python ocr_recognize.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    result, engine = recognize_image(image_path)
    
    # 输出使用的引擎到stderr
    print(f"[INFO] 使用引擎: {engine}", file=sys.stderr)
    
    # 输出结果到stdout
    print(result)
