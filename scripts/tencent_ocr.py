#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云 OCR API 集成模块
支持自动识别图片中的文字内容

免费额度：每月 1000 次通用印刷体识别
文档：https://cloud.tencent.com/document/product/866/33526
"""

import os
import json
import base64
import hashlib
import hmac
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class TencentOCR:
    """腾讯云 OCR 客户端"""
    
    def __init__(self, secret_id: str = None, secret_key: str = None):
        """
        初始化 OCR 客户端
        
        Args:
            secret_id: 腾讯云 SecretId
            secret_key: 腾讯云 SecretKey
        """
        self.secret_id = secret_id or os.getenv('TENCENT_SECRET_ID')
        self.secret_key = secret_key or os.getenv('TENCENT_SECRET_KEY')
        self.service = "ocr"
        self.host = "ocr.tencentcloudapi.com"
        self.region = "ap-guangzhou"
        self.version = "2018-11-19"
        
        if not self.secret_id or not self.secret_key:
            raise ValueError("请提供 SecretId 和 SecretKey，或设置环境变量")
    
    def _sign(self, payload: str) -> Dict[str, str]:
        """
        生成腾讯云 API 签名
        """
        timestamp = int(time.time())
        date = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")
        
        # 1. 拼接规范请求串
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"
        canonical_headers = f"content-type:{ct}\nhost:{self.host}\n"
        signed_headers = "content-type;host"
        hashed_request_payload = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        canonical_request = (http_request_method + "\n" +
                           canonical_uri + "\n" +
                           canonical_querystring + "\n" +
                           canonical_headers + "\n" +
                           signed_headers + "\n" +
                           hashed_request_payload)
        
        # 2. 拼接待签名字符串
        algorithm = "TC3-HMAC-SHA256"
        credential_scope = date + "/" + self.service + "/" + "tc3_request"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        string_to_sign = (algorithm + "\n" +
                         str(timestamp) + "\n" +
                         credential_scope + "\n" +
                         hashed_canonical_request)
        
        # 3. 计算签名
        secret_date = hmac.new(("TC3" + self.secret_key).encode('utf-8'),
                               date.encode('utf-8'), hashlib.sha256).digest()
        secret_service = hmac.new(secret_date, self.service.encode('utf-8'), hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, "tc3_request".encode('utf-8'), hashlib.sha256).digest()
        signature = hmac.new(secret_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        
        # 4. 拼接 Authorization
        authorization = (algorithm + " " +
                        "Credential=" + self.secret_id + "/" + credential_scope + ", " +
                        "SignedHeaders=" + signed_headers + ", " +
                        "Signature=" + signature)
        
        return {
            "Authorization": authorization,
            "Content-Type": ct,
            "Host": self.host,
            "X-TC-Action": "GeneralBasicOCR",
            "X-TC-Version": self.version,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": self.region
        }
    
    def recognize(self, image_path: str) -> Dict:
        """
        识别单张图片中的文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            识别结果字典
        """
        try:
            # 读取图片并转为 base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            # 构建请求体
            payload = json.dumps({"ImageBase64": image_data})
            
            # 生成签名
            headers = self._sign(payload)
            
            # 发送请求
            url = f"https://{self.host}"
            response = requests.post(url, headers=headers, data=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_result(result, image_path)
            else:
                logger.error(f"API 请求失败: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"识别失败 {image_path}: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_result(self, api_response: Dict, image_path: str) -> Dict:
        """
        解析 API 响应
        """
        response = api_response.get("Response", {})
        
        if "Error" in response:
            error = response["Error"]
            logger.error(f"API 错误: {error.get('Code')} - {error.get('Message')}")
            return {
                "success": False,
                "error": f"{error.get('Code')}: {error.get('Message')}"
            }
        
        # 提取文字
        text_detections = response.get("TextDetections", [])
        texts = []
        for detection in text_detections:
            text = detection.get("DetectedText", "").strip()
            if text:
                texts.append(text)
        
        full_text = "\n".join(texts)
        
        return {
            "success": True,
            "image_path": image_path,
            "text": full_text,
            "text_count": len(texts),
            "language": response.get("Language", "zh"),
            "request_id": response.get("RequestId", "")
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
        
        logger.info(f"开始批量识别 {total} 张图片...")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"[{i}/{total}] 识别: {Path(image_path).name}")
            result = self.recognize(image_path)
            results.append(result)
            
            # 避免请求过快
            if i < total:
                time.sleep(0.5)
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"批量识别完成: {success_count}/{total} 成功")
        
        return results


def test_ocr():
    """测试 OCR 功能"""
    # 从环境变量获取密钥
    secret_id = os.getenv('TENCENT_SECRET_ID')
    secret_key = os.getenv('TENCENT_SECRET_KEY')
    
    if not secret_id or not secret_key:
        print("请设置环境变量 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")
        print("获取方式：https://console.cloud.tencent.com/cam/capi")
        return
    
    ocr = TencentOCR(secret_id, secret_key)
    
    # 测试图片
    test_image = "test.png"
    if os.path.exists(test_image):
        result = ocr.recognize(test_image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"测试图片不存在: {test_image}")


if __name__ == "__main__":
    test_ocr()
