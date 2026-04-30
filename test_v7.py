#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V7 核心逻辑测试"""
import sys
sys.path.insert(0, '.')

# 加载V7（跳过OCR导入，直接mock）
import importlib, types

# Mock ocr模块
for mod_name in ['local_ocr', 'tencent_ocr', 'baidu_ocr']:
    m = types.ModuleType(mod_name)
    if mod_name == 'local_ocr':
        class FakeLocalOCR:
            tesseract_available = False
            def recognize(self, path): return {'success': False, 'text': ''}
        m.LocalOCR = FakeLocalOCR
    sys.modules[mod_name] = m

# 加载.env
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path('.env'))

# 执行V7脚本定义
import auto_process_all_v7 as v7

print("=== [P0-1] SmartClassifier 分类测试 ===")
classifier = v7.SmartClassifier()

test_cases = [
    ("明末清初文学家钱谦益，历史人物传记，明朝清朝皇帝将军", "历史文化"),
    ("周文王，朝代更替，春秋战国古代史记", "历史文化"),
    ("中医养生，药膳食疗，气血调理，湿气体质", "营养健康"),
    ("宝宝辅食，早教方法，婴儿喂养，幼儿成长", "教育育儿"),
    ("旅游攻略，景点推荐，签证办理，行程安排", "旅游攻略"),
]

all_pass = True
for text, expected in test_cases:
    cat, conf = classifier.classify(text)
    status = "PASS" if cat == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] 期望={expected}, 实际={cat} ({conf:.0%})")

print()
print("=== [P0-2] 文档命名测试 ===")
analyzer = v7.SmartContentAnalyzer(classifier)

doc_tests = [
    ("钱谦益，字受之，明末清初著名文学家，生平事迹记录", "历史文化-钱谦益"),
    ("周文王历史，周朝奠基人，朝代事件", "历史文化-"),
    ("春季养生食谱，山药薏米粥，健脾祛湿中医", "营养健康-"),
]

for text, expected_prefix in doc_tests:
    analysis = analyzer.analyze(text, 1)
    doc_name = analysis["doc_name"]
    cat = analysis["category"]
    ok = doc_name.startswith(expected_prefix.split("-")[0])
    print(f"  [{'OK' if ok else 'WARN'}] 文档名: {doc_name}")
    print(f"       分类: {cat}")

print()
print("=== [P0-3][P1-5] 相似文档检测测试 ===")
import tempfile, os
with tempfile.TemporaryDirectory() as tmpdir:
    manager = v7.SmartDocumentManager(tmpdir)
    # 新建第一个文档
    md1, is_new = manager.save_document(
        "历史文化-钱谦益传", "历史文化",
        "钱谦益，明末清初文学家，字受之，号牧斋",
        "img001.jpg", ["历史", "文学家"], "abc12345", {}
    )
    print(f"  第1次 is_new={is_new}, 文件={Path(md1).name}")

    # 相似文档应该合并
    md2, is_new2 = manager.save_document(
        "历史文化-钱谦益", "历史文化",
        "钱谦益生平详细，明末清初，文学家，诗人",
        "img002.jpg", ["历史"], "def67890", {}
    )
    print(f"  第2次 is_new={is_new2}, 文件={Path(md2).name}")
    if not is_new2:
        print("  OK 相同主题正确合并!")
    else:
        print("  WARN 未合并（主题相似度不足）")

print()
print("=== [P1-4] 归档路径测试 ===")
import tempfile
with tempfile.TemporaryDirectory() as tmpdir:
    archiver = v7.ImageArchiver(tmpdir)
    # 创建临时图片
    tmp_img = Path(tmpdir) / "test.jpg"
    tmp_img.write_bytes(b"fake image")
    archived = archiver.archive_image(str(tmp_img), "历史文化")
    if archived:
        archived_path = Path(archived)
        correct = archived_path.parent.name == "历史文化"
        print(f"  [{'OK' if correct else 'FAIL'}] 归档路径: {archived_path.parent.name}")

print()
print("=== [P1-6] 报告统计测试 ===")
mock_results = [
    {"image": "a.jpg", "category": "历史文化", "is_duplicate": False, "is_new_doc": True, "md_file": "x.md", "docx_file": "x.docx"},
    {"image": "b.jpg", "category": "历史文化", "is_duplicate": False, "is_new_doc": False, "md_file": "x.md", "docx_file": None},
    {"image": "c.jpg", "category": "营养健康", "is_duplicate": True},
    {"image": "d.jpg", "failed": True},
]
report, _ = v7.save_report(mock_results, 4, 10.0, 'test')
print(f"  总图片: {report['total_images']}")
print(f"  成功处理: {report['processed_successfully']}")
print(f"  失败: {report['failed']}")
print(f"  重复跳过: {report['duplicates_skipped']}")
print(f"  新建文档: {report['new_documents']}")
print(f"  合并文档: {report['merged_documents']}")
ok = (report['total_images'] == 4 and report['failed'] == 1 and
      report['duplicates_skipped'] == 1 and report['new_documents'] == 1)
print(f"  [{'OK' if ok else 'FAIL'}] 报告统计正确")

print()
print("所有测试完成!")
