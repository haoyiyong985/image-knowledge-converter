#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
from pathlib import Path

file_path = Path("D:/新建文件夹/auto_process.py")
content = file_path.read_text(encoding="utf-8")

# 替换第一行
content = re.sub(
    r'content = f"""你好，请帮我继续处理图片知识库项目。',
    r'content = f"""你好，请帮我继续处理「图片知识库转化工具 v1.0」项目。',
    content
)

file_path.write_text(content, encoding="utf-8")
print("[OK] 第一行已更新")
