#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR引擎管理器 - 多引擎自动切换
===============================
功能：
  1. 管理多个OCR引擎（腾讯云、百度云、AI视觉）
  2. 主引擎达到限制时自动切换到备用引擎
  3. 优先使用云OCR（精度高），AI视觉作为兜底

引擎优先级：
  1. 腾讯云OCR（精度最高，每日1000次）
  2. 百度云OCR（精度高，每日50000次）
  3. AI视觉识别（兜底，无限制但精度略低）

版本：v1.2
作者：AI Assistant
"""

import os
import json
import base64
import hashlib
import hmac
import time
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple

# 路径配置
BASE_DIR = Path("D:/新建文件夹")
CONFIG_FILE = BASE_DIR / "ocr_config.json"
LOG_FILE = BASE_DIR / ".workbuddy" / "memory" / "ocr_engine_log.json"


class OCREngineManager:
    """OCR引擎管理器 - 优先使用云OCR"""
    
    # 引擎配置：优先级数字越小越优先
    ENGINES = {
        'tencent': {
            'name': '腾讯云OCR',
            'priority': 1,
            'daily_limit': 1000,
            'endpoint': 'ocr.tencentcloudapi.com'
        },
        'baidu': {
            'name': '百度云OCR',
            'priority': 2,
            'daily_limit': 1000,  # 个人认证1000次/月，企业认证2000次/月
            'token_url': 'https://aip.baidubce.com/oauth/2.0/token',
            'ocr_url': 'https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic'
        },
        'ai_vision': {
            'name': 'AI视觉识别',
            'priority': 3,
            'daily_limit': float('inf')
        }
    }
    
    def __init__(self):
        self.usage = {k: 0 for k in self.ENGINES.keys()}
        self.config = {}
        self.baidu_access_token = None
        self.load_config()
        self.load_usage()
    
    def load_config(self):
        """加载OCR配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                print(f"[INFO] 已加载OCR配置")
            except Exception as e:
                print(f"[WARN] 加载OCR配置失败: {e}")
    
    def load_usage(self):
        """加载今日使用量"""
        today = datetime.now().strftime("%Y-%m-%d")
        if LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                    if logs.get('date') == today:
                        self.usage = logs.get('usage', self.usage)
            except Exception:
                pass
    
    def save_usage(self):
        """保存使用量"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        logs = {
            'date': today,
            'usage': self.usage
        }
        try:
            with open(LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] 保存OCR使用量失败: {e}")
    
    def get_available_engine(self) -> str:
        """获取当前可用的引擎（按优先级）"""
        # 按优先级排序
        sorted_engines = sorted(
            self.ENGINES.items(), 
            key=lambda x: x[1]['priority']
        )
        
        for engine_id, engine_info in sorted_engines:
            # 检查是否达到限额
            if self.usage.get(engine_id, 0) >= engine_info['daily_limit']:
                continue
            
            # 检查密钥是否配置
            if engine_id == 'tencent':
                if self.config.get('tencent', {}).get('secret_id'):
                    return engine_id
            elif engine_id == 'baidu':
                if self.config.get('baidu', {}).get('api_key'):
                    return engine_id
            elif engine_id == 'ai_vision':
                # AI视觉始终可用
                return engine_id
        
        # 默认返回AI视觉
        return 'ai_vision'
    
    def recognize_image(self, image_path: str) -> Tuple[str, str]:
        """
        识别图片文字
        
        Args:
            image_path: 图片路径
            
        Returns:
            (识别结果, 使用的引擎名称)
            识别结果：
              - 成功：返回识别到的文字
              - AI视觉兜底：返回 "__AI_VISION__" 标记
        """
        engine_id = self.get_available_engine()
        engine_name = self.ENGINES[engine_id]['name']
        
        try:
            if engine_id == 'tencent':
                result = self._recognize_tencent(image_path)
            elif engine_id == 'baidu':
                result = self._recognize_baidu(image_path)
            else:
                # AI视觉识别 - 返回特殊标记，由上层AI处理
                return "__AI_VISION__", engine_name
            
            # 更新使用量
            self.usage[engine_id] = self.usage.get(engine_id, 0) + 1
            self.save_usage()
            
            return result, engine_name
            
        except Exception as e:
            print(f"[ERROR] {engine_name} 识别失败: {e}")
            # 标记当前引擎失败，下次跳过
            self.usage[engine_id] = self.ENGINES[engine_id]['daily_limit']
            # 递归尝试下一个引擎
            return self.recognize_image(image_path)
    
    def _recognize_tencent(self, image_path: str) -> str:
        """
        腾讯云OCR识别
        通用印刷体识别（高精度版）
        """
        import json
        import hmac
        import hashlib
        import time
        import urllib.request
        
        secret_id = self.config['tencent']['secret_id']
        secret_key = self.config['tencent']['secret_key']
        
        # 读取图片并转为base64
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 构建请求参数
        payload = {
            "ImageBase64": image_base64
        }
        
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
        
        try:
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
            
        except urllib.error.HTTPError as e:
            raise Exception(f"腾讯云OCR请求失败: {e.code} {e.reason}")
    
    def _get_baidu_token(self) -> str:
        """获取百度云访问令牌"""
        if self.baidu_access_token:
            return self.baidu_access_token
        
        api_key = self.config['baidu']['api_key']
        secret_key = self.config['baidu']['secret_key']
        
        url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
        
        try:
            response = urllib.request.urlopen(url, timeout=10)
            result = json.loads(response.read().decode('utf-8'))
            self.baidu_access_token = result['access_token']
            return self.baidu_access_token
        except Exception as e:
            raise Exception(f"获取百度云token失败: {e}")
    
    def _recognize_baidu(self, image_path: str) -> str:
        """
        百度云OCR识别
        通用文字识别（标准版）
        """
        # 获取access_token
        token = self._get_baidu_token()
        
        # 读取图片
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        # 构建请求
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={token}"
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = urllib.parse.urlencode({
            'image': image_base64,
            'language_type': 'CHN_ENG'  # 中英文混合
        }).encode('utf-8')
        
        # 发送请求
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode('utf-8'))
            
            if 'error_code' in result:
                raise Exception(f"百度云OCR错误: {result['error_msg']}")
            
            # 提取文字
            words = []
            for item in result.get('words_result', []):
                words.append(item['words'])
            
            return '\n'.join(words)
            
        except urllib.error.HTTPError as e:
            raise Exception(f"百度云OCR请求失败: {e.code} {e.reason}")
    
    def get_status(self) -> Dict:
        """获取引擎状态"""
        current = self.get_available_engine()
        return {
            'current_engine': self.ENGINES[current]['name'],
            'engines': {
                k: {
                    'name': v['name'],
                    'used_today': self.usage.get(k, 0),
                    'daily_limit': v['daily_limit'],
                    'remaining': max(0, v['daily_limit'] - self.usage.get(k, 0))
                }
                for k, v in self.ENGINES.items()
            }
        }


# 全局管理器实例
_ocr_manager = None

def get_ocr_manager() -> OCREngineManager:
    """获取OCR管理器实例（单例模式）"""
    global _ocr_manager
    if _ocr_manager is None:
        _ocr_manager = OCREngineManager()
    return _ocr_manager


def test_ocr_engines():
    """测试OCR引擎"""
    print("=" * 60)
    print("OCR引擎测试")
    print("=" * 60)
    
    manager = get_ocr_manager()
    
    # 显示状态
    status = manager.get_status()
    print("\n当前引擎状态:")
    print(f"  当前可用: {status['current_engine']}")
    print("\n各引擎使用情况:")
    for engine_id, info in status['engines'].items():
        print(f"  {info['name']}: {info['used_today']}/{info['daily_limit']} (剩余: {info['remaining']})")
    
    # 检查配置
    print("\n配置检查:")
    if manager.config.get('tencent', {}).get('secret_id'):
        print("  [OK] 腾讯云OCR: 已配置")
    else:
        print("  [NO] 腾讯云OCR: 未配置")
    
    if manager.config.get('baidu', {}).get('api_key'):
        print("  [OK] 百度云OCR: 已配置")
    else:
        print("  [NO] 百度云OCR: 未配置")
    
    print("\n  [OK] AI视觉识别: 始终可用")


if __name__ == "__main__":
    test_ocr_engines()
