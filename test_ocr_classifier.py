#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 OCR + 分类集成"""

from ocr_fallback_manager import OCRManager
from image_classifier import ImageClassifier
from pathlib import Path

def main():
    # 找一张测试图片
    test_dirs = [Path('D:/新建文件夹/已处理图片'), Path('D:/新建文件夹/待处理图片')]
    test_image = None
    for d in test_dirs:
        if d.exists():
            imgs = list(d.glob('**/*.jpg'))[:1]
            if imgs:
                test_image = imgs[0]
                break
    
    if not test_image:
        print('[ERROR] 未找到测试图片')
        return
    
    print(f'测试图片: {test_image.name}')
    print('=' * 60)
    
    # OCR 识别
    print('\n1. OCR 识别中...')
    ocr = OCRManager()
    result = ocr.recognize(str(test_image))
    
    if result['success']:
        text = result['text']
        print(f'[OK] 识别成功，{len(text)} 字符')
        # 安全打印，移除无法显示的字符
        safe_text = ''.join(c if ord(c) < 128 or '\u4e00' <= c <= '\u9fff' else '?' for c in text[:400])
        print(f'\n识别内容预览(部分):\n{safe_text[:200]}...')
        
        # 分类
        print('\n' + '=' * 60)
        print('2. 内容分类中...')
        classifier = ImageClassifier()
        category = classifier.classify(text)
        
        print('\n分类结果:')
        print(f'  分类名称: {category["category_name"]}')
        print(f'  分类ID:   {category["category_id"]}')
        print(f'  置信度:   {category["confidence"]:.1%}')
        print(f'  归档文档: {category["document"]}')
        print(f'  匹配词:   {category["matched_keywords"][:8]}')
        print(f'  原因:     {category["message"]}')
    else:
        print(f'[FAIL] 识别失败: {result.get("error")}')

if __name__ == '__main__':
    main()
