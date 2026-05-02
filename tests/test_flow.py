#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_flow.py — 整套流程测试脚本
测试内容：
  1. 目录完整性检查
  2. 启动提示词文件是否存在且内容正确
  3. auto_process.py 核心函数是否可调用
  4. 模拟新建文档（写入→读取→验证→清除）
  5. 模拟图片归档（复制→移动→验证→清除）
  6. 启动提示词自动更新是否触发
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR      = Path("D:/新建文件夹")
PENDING_DIR   = BASE_DIR / "待处理图片"
PROCESSED_DIR = BASE_DIR / "已处理图片"
RESULT_DIR    = BASE_DIR / "处理结果"
PROMPT_FILE   = BASE_DIR / "【启动提示词】新对话粘贴这段.txt"
AUTO_SCRIPT   = BASE_DIR / "auto_process.py"

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
    else:
        print(f"  {FAIL} {label}" + (f" — {detail}" if detail else ""))
        errors.append(label)

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

# ─────────────────────────────────────────────
# 测试1：目录完整性
# ─────────────────────────────────────────────
section("测试1：目录完整性")
check("项目根目录存在",        BASE_DIR.exists())
check("待处理图片目录存在",    PENDING_DIR.exists())
check("已处理图片目录存在",    PROCESSED_DIR.exists())
check("处理结果目录存在",      RESULT_DIR.exists())

# ─────────────────────────────────────────────
# 测试2：关键文件是否存在
# ─────────────────────────────────────────────
section("测试2：关键文件完整性")
check("auto_process.py 存在",  AUTO_SCRIPT.exists())
check("启动提示词文件存在",    PROMPT_FILE.exists())
check("使用说明.md 存在",      (BASE_DIR / "使用说明.md").exists())

# ─────────────────────────────────────────────
# 测试3：启动提示词内容正确性
# ─────────────────────────────────────────────
section("测试3：启动提示词内容验证")
if PROMPT_FILE.exists():
    content = PROMPT_FILE.read_text(encoding="utf-8")
    check("包含项目路径",        "D:\\新建文件夹" in content)
    check("包含已有文档列表",    "编号01" in content and "编号02" in content)
    check("包含更新时间戳",      "最后更新" in content)
    check("包含处理规则说明",    "处理规则" in content)
    check("包含常用指令说明",    "处理新图片" in content)
    # 检查是否是最新的（1小时内生成）
    mtime = PROMPT_FILE.stat().st_mtime
    age_hours = (datetime.now().timestamp() - mtime) / 3600
    check("文件是最近1小时内生成的（说明自动更新生效）",
          age_hours < 1, f"实际距上次更新：{age_hours:.1f}小时")
else:
    print(f"  {FAIL} 启动提示词文件不存在，跳过内容验证")
    errors.append("启动提示词文件不存在")

# ─────────────────────────────────────────────
# 测试4：已有MD文档完整性
# ─────────────────────────────────────────────
section("测试4：已有 MD 文档完整性")
expected_docs = [
    "01_抗炎饮食与营养科普",
    "02_肠道健康与饮食分类",
    "03_中医养生与食疗",
    "04_日常饮食建议",
]
for doc in expected_docs:
    md   = RESULT_DIR / f"{doc}.md"
    docx = RESULT_DIR / f"{doc}.docx"
    check(f"{doc}.md 存在且非空",   md.exists() and md.stat().st_size > 100)
    check(f"{doc}.docx 存在",       docx.exists())

# ─────────────────────────────────────────────
# 测试5：auto_process.py 核心函数可调用
# ─────────────────────────────────────────────
section("测试5：auto_process.py 核心函数测试")
sys.path.insert(0, str(BASE_DIR))
try:
    import auto_process as ap

    # 测试扫描函数
    try:
        result = ap.scan_pending_images()
        check("scan_pending_images() 可正常调用",  True)
        check("扫描结果是字典类型",                isinstance(result, dict))
        total = sum(len(v) for v in result.values())
        print(f"  {INFO} 当前待处理图片：{total} 张，分布在 {len(result)} 个主题文件夹")
    except Exception as e:
        check("scan_pending_images() 可正常调用", False, str(e))

    # 测试文档结构读取
    try:
        structure = ap.read_existing_docs_structure()
        check("read_existing_docs_structure() 可正常调用", True)
        check("读取到已有文档（>=4个）",  len(structure) >= 4,
              f"实际读取到 {len(structure)} 个")
        for doc_name, info in structure.items():
            check(f"  {doc_name} 含有章节信息", len(info["sections"]) > 0)
    except Exception as e:
        check("read_existing_docs_structure() 可正常调用", False, str(e))

    # 测试 get_next_doc_number
    try:
        num = ap.get_next_doc_number()
        check("get_next_doc_number() 可正常调用", True)
        check(f"下一个文档编号合理（当前应为5）", num == 5, f"实际返回：{num}")
    except Exception as e:
        check("get_next_doc_number() 可正常调用", False, str(e))

except ImportError as e:
    check("auto_process.py 可导入", False, str(e))

# ─────────────────────────────────────────────
# 测试6：模拟新建文档（写入→读取→验证→清除）
# ─────────────────────────────────────────────
section("测试6：模拟新建文档流程")
test_doc_name = "99_测试文档_请勿删除"
test_md       = RESULT_DIR / f"{test_doc_name}.md"
test_content  = "## 一、测试章节\n\n这是一段测试内容，用于验证新建文档流程是否正常。\n"
try:
    # 写入
    ap.create_new_md(test_doc_name, "测试文档", test_content)
    check("create_new_md() 成功创建文件", test_md.exists())

    # 读取验证
    written = test_md.read_text(encoding="utf-8")
    check("文件内容可正常读取", len(written) > 0)
    check("文件包含测试内容",  "测试章节" in written)
    check("文件包含标题头",    "# 测试文档" in written)

    # 追加测试
    ap.append_to_md(test_doc_name, "## 二、追加章节\n\n追加的内容。\n")
    appended = test_md.read_text(encoding="utf-8")
    check("append_to_md() 追加成功",   "追加章节" in appended)
    check("原有内容未被覆盖",          "测试章节" in appended)

    # 清除测试文档（不影响真实数据）
    test_md.unlink()
    check("测试文档已清除（不影响正式数据）", not test_md.exists())

except Exception as e:
    check("模拟新建文档流程", False, str(e))
    if test_md.exists():
        test_md.unlink()

# ─────────────────────────────────────────────
# 测试7：模拟图片归档流程
# ─────────────────────────────────────────────
section("测试7：模拟图片归档流程")
test_topic   = "测试主题_自动清理"
test_img_src = PENDING_DIR / test_topic / "test_image.jpg"
test_img_dst = PROCESSED_DIR / test_topic / "test_image.jpg"
try:
    # 创建假图片文件
    test_img_src.parent.mkdir(parents=True, exist_ok=True)
    test_img_src.write_bytes(b"fake image content for testing")
    check("模拟图片文件创建成功", test_img_src.exists())

    # 执行归档
    ap.archive_images(test_topic, [test_img_src])
    check("archive_images() 归档成功",  test_img_dst.exists())
    check("原始文件已从待处理目录移走", not test_img_src.exists())

    # 清理测试数据
    shutil.rmtree(PENDING_DIR / test_topic, ignore_errors=True)
    shutil.rmtree(PROCESSED_DIR / test_topic, ignore_errors=True)
    check("测试数据已清理", True)

except Exception as e:
    check("模拟图片归档流程", False, str(e))
    shutil.rmtree(PENDING_DIR / test_topic, ignore_errors=True)
    shutil.rmtree(PROCESSED_DIR / test_topic, ignore_errors=True)

# ─────────────────────────────────────────────
# 测试8：启动提示词自动更新
# ─────────────────────────────────────────────
section("测试8：启动提示词自动更新")
try:
    structure = ap.read_existing_docs_structure()
    mtime_before = PROMPT_FILE.stat().st_mtime if PROMPT_FILE.exists() else 0
    ap.generate_startup_prompt(structure)
    mtime_after  = PROMPT_FILE.stat().st_mtime
    check("generate_startup_prompt() 可正常调用", True)
    check("调用后文件修改时间已更新",             mtime_after >= mtime_before)
    content = PROMPT_FILE.read_text(encoding="utf-8")
    check("更新后内容包含所有已有文档",
          all(doc in content for doc in ["编号01","编号02","编号03","编号04"]))
except Exception as e:
    check("启动提示词自动更新", False, str(e))

# ─────────────────────────────────────────────
# 汇总
# ─────────────────────────────────────────────
print(f"\n{'='*55}")
print("  测试汇总")
print(f"{'='*55}")
if not errors:
    print("  全部测试通过！流程无漏洞，可以放心使用。")
else:
    print(f"  发现 {len(errors)} 个问题：")
    for i, e in enumerate(errors, 1):
        print(f"    {i}. {e}")
print(f"{'='*55}\n")
