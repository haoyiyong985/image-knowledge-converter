#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度 OCR API 集成模块
支持自动识别图片中的文字内容

免费额度：每月 50,000 次通用文字识别
文档：https://cloud.baidu.com/doc/OCR/s/zk3h7xw5e
"""

import os
import json
import base64
import requests
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class BaiduOCR:
    """百度 OCR 客户端"""
    
    def __init__(self, app_id: str = None, api_key: str = None, secret_key: str = None):
        """
        初始化百度 OCR 客户端
        
        Args:
            app_id: 百度应用 ID
            api_key: 百度 API Key
            secret_key: 百度 Secret Key
        """
        self.app_id = app_id or os.getenv('BAIDU_APP_ID')
        self.api_key = api_key or os.getenv('BAIDU_API_KEY')
        self.secret_key = secret_key or os.getenv('BAIDU_SECRET_KEY')
        
        self.access_token = None
        self.token_expire_time = None
        
        if not all([self.app_id, self.api_key, self.secret_key]):
            raise ValueError("请提供百度 OCR 的 app_id, api_key, secret_key，或设置环境变量")
        
        # 获取 access token
        self._get_access_token()
    
    def _get_access_token(self):
        """获取百度 API 访问令牌"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key
        }
        
        try:
            response = requests.post(url, params=params, timeout=10)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                # token 有效期通常为 30 天
                expires_in = result.get('expires_in', 2592000)
                self.token_expire_time = datetime.now().timestamp() + expires_in
                logger.info("[OK] 百度 OCR Access Token 获取成功")
            else:
                error_msg = result.get('error_description', '未知错误')
                raise ValueError(f"获取 Access Token 失败: {error_msg}")
                
        except Exception as e:
            logger.error(f"获取 Access Token 失败: {e}")
            raise
    
    def _check_token(self):
        """检查 token 是否有效"""
        if not self.access_token:
            self._get_access_token()
        elif self.token_expire_time and datetime.now().timestamp() > self.token_expire_time - 3600:
            # token 即将过期，重新获取
            logger.info("Access Token 即将过期，重新获取...")
            self._get_access_token()
    
    def recognize(self, image_path: str) -> Dict:
        """
        识别单张图片中的文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            识别结果字典
        """
        self._check_token()
        
        try:
            # 读取图片并转为 base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 调用通用文字识别（高精度版）
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={self.access_token}"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {
                'image': image_data,
                'language_type': 'CHN_ENG',
                'detect_direction': 'true',
                'paragraph': 'true'
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            result = response.json()
            
            return self._parse_result(result, image_path)
            
        except Exception as e:
            logger.error(f"识别失败 {image_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_result(self, api_response: Dict, image_path: str) -> Dict:
        """解析 API 响应"""
        if 'error_code' in api_response:
            error_msg = api_response.get('error_msg', '未知错误')
            logger.error(f"API 错误: {api_response['error_code']} - {error_msg}")
            return {
                "success": False,
                "error": f"{api_response['error_code']}: {error_msg}"
            }
        
        # 提取文字
        words_result = api_response.get('words_result', [])
        texts = []
        for item in words_result:
            text = item.get('words', '').strip()
            if text:
                texts.append(text)
        
        full_text = '\n'.join(texts)
        
        return {
            "success": True,
            "image_path": image_path,
            "text": full_text,
            "text_count": len(texts),
            "language": "zh",
            "direction": api_response.get('direction', 0)
        }
    
    def recognize_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        批量识别图片
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            识别结果列表
        """
        results = []
        total = len(image_paths)
        
        logger.info(f"开始批量识别 {total} 张图片（百度 OCR）...")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"[{i}/{total}] 识别: {Path(image_path).name}")
            result = self.recognize(image_path)
            results.append(result)
            
            # 百度 OCR 免费版 QPS 限制为 2，适当延迟
            if i < total:
                import time
                time.sleep(0.6)
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"批量识别完成: {success_count}/{total} 成功")
        
        return results


def test_baidu_ocr():
    """测试百度 OCR 功能"""
    # 从环境变量获取密钥
    app_id = os.getenv('BAIDU_APP_ID')
    api_key = os.getenv('BAIDU_API_KEY')
    secret_key = os.getenv('BAIDU_SECRET_KEY')
    
    if not all([app_id, api_key, secret_key]):
        print("请设置环境变量 BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY")
        print("获取方式：https://console.bce.baidu.com/ai/")
        return
    
    ocr = BaiduOCR(app_id, api_key, secret_key)
    
    # 测试图片
    test_image = "test.png"
    if os.path.exists(test_image):
        result = ocr.recognize(test_image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"测试图片不存在: {test_image}")


if __name__ == "__main__":
    test_baidu_ocr()
