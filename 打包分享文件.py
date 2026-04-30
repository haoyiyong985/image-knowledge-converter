#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包分享文件 — 把所有需要分享的文件复制到 分享包/ 目录并压缩
"""

import shutil
import zipfile
from pathlib import Path
from datetime import datetime

BASE_DIR    = Path("D:/新建文件夹")
SHARE_DIR   = BASE_DIR / "分享包"
SHARE_DIR.mkdir(exist_ok=True)

# ── 需要复制进分享包的文件 ──
FILES_TO_COPY = [
    BASE_DIR / "auto_process.py",
    BASE_DIR / "ima_sync.py",
    BASE_DIR / "test_flow.py",
    BASE_DIR / "使用说明.md",
    BASE_DIR / "【启动提示词】新对话粘贴这段.txt",
    BASE_DIR / "README.txt",  # 项目说明文档
    # Word 配置说明已经直接生成在分享包目录里
]

# ima_config.txt 特殊处理：生成一份空模板（不带真实凭证）
IMA_CONFIG_TEMPLATE = """\
# ima OpenAPI 凭证配置文件
# ================================
# 请把下面两行的"填入你的xxx"替换成真实的值
# 注意：等号两边不要有空格，引号也不需要
#
# 获取凭证：登录 https://ima.qq.com/agent-interface
# 有效期通常 30 天，到期后重新获取并替换这两行即可
#
# 安全提示：不要把这个文件发给别人，不要上传到网络

IMA_CLIENT_ID=填入你的ClientID
IMA_API_KEY=填入你的APIKey
"""

print("=" * 50)
print("  打包分享文件")
print("=" * 50)

# ── 复制文件 ──
for src in FILES_TO_COPY:
    if src.exists():
        dest = SHARE_DIR / src.name
        shutil.copy2(str(src), str(dest))
        print(f"  [复制] {src.name}")
    else:
        print(f"  [跳过] 文件不存在：{src.name}")

# ── 生成 ima_config.txt 空模板（不带真实凭证）──
ima_config_dest = SHARE_DIR / "ima_config.txt"
ima_config_dest.write_text(IMA_CONFIG_TEMPLATE, encoding="utf-8")
print(f"  [生成] ima_config.txt（空模板，不含真实凭证）")

# ── 创建「朋友请先看我」说明文件 ──
readme_path = SHARE_DIR / "【朋友请先看我】README.txt"
readme_path.write_text(
    "欢迎使用「图片知识库整理工具」！\n\n"
    "这个工具可以帮你把手机截图自动整理成 Word 文档和 Markdown 文件，\n"
    "并可选择自动同步到 ima 个人笔记。\n\n"
    "【第一步】请先打开这个文件：\n"
    "  图片知识库_配置说明（小白版）.docx\n\n"
    "  里面有详细的图文配置步骤，大约 10 分钟可以配置完成。\n\n"
    "【包含文件清单】\n"
    "  1. 图片知识库_配置说明（小白版）.docx  ← 从这里开始\n"
    "  2. auto_process.py                      ← 核心处理脚本\n"
    "  3. ima_sync.py                          ← ima 自动同步脚本\n"
    "  4. ima_config.txt                       ← ima API 凭证配置（填完即用）\n"
    "  5. test_flow.py                         ← 验证配置是否正确\n"
    "  6. 使用说明.md                          ← 日常操作手册\n"
    "  7. 【启动提示词】新对话粘贴这段.txt    ← 每次新对话时用\n\n"
    "【需要的软件】\n"
    "  - Python 3.8+（免费，官网下载）\n"
    "  - WorkBuddy（AI 对话工具）\n"
    "  - ima PC 客户端（可选，用于知识库管理）\n\n"
    "祝使用愉快！\n",
    encoding="utf-8"
)
print(f"  [生成] 【朋友请先看我】README.txt")

# ── 打包成 ZIP ──
today = datetime.now().strftime("%Y%m%d")
zip_path = BASE_DIR / f"图片知识库整理工具_分享包_{today}.zip"

with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
    for f in SHARE_DIR.iterdir():
        if f.is_file():
            zf.write(str(f), f.name)
            print(f"  [压缩] {f.name}")

print(f"\n[完成] 压缩包已生成：")
print(f"       {zip_path}")
size_kb = zip_path.stat().st_size / 1024
print(f"       大小：{size_kb:.1f} KB")
print(f"\n  把这个 ZIP 文件发给朋友即可！")
print("=" * 50)
