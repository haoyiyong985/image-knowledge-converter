#!/usr/bin/env python3
import os

# 设置环境变量
os.environ['BAIDU_APP_ID'] = '7461042'
os.environ['BAIDU_API_KEY'] = 'sU1YkZbKvxDBs6fGDP3phfPI'
os.environ['BAIDU_SECRET_KEY'] = 'ijqRXVCGjIn1hM0NkQsRjs7mRiwGMSvO'

from baidu_ocr import BaiduOCR
baidu = BaiduOCR()

# 测试识别
test_image = r'D:\新建文件夹\已处理图片\示范\XHS_17128195674261040g00830st63gs1422g45a04qjur9mil69qjig.jpg'
result = baidu.recognize(test_image)
print(f'成功: {result.get("success")}')
print(f'文字长度: {len(result.get("text", ""))}')
print(f'文字预览: {result.get("text", "")[:100]}')
