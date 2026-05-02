#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动新增分类功能测试"""

import sys
import logging
import shutil
from pathlib import Path

# 关闭 INFO 日志，只显示测试输出
logging.disable(logging.INFO)

from image_classifier import ImageClassifier

PASS = "[PASS]"
FAIL = "[FAIL]"

def main():
    src = Path("D:/新建文件夹/config/categories.yaml")
    test_cfg = Path("D:/新建文件夹/config/categories_test2.yaml")
    shutil.copy(src, test_cfg)
    
    results = []
    
    # ------------------------------------------------
    # 测试1：完全陌生内容 → 触发自动新增
    # ------------------------------------------------
    print("=" * 60)
    print("测试1：汽车保养类（完全陌生内容）- classify_with_auto_add")
    print("=" * 60)
    
    classifier = ImageClassifier(config_path=str(test_cfg))
    unknown1 = (
        "汽车保养要注意机油更换周期，一般5000公里或半年换一次机油。"
        "轮胎气压要定期检查，刹车片磨损要及时更换。"
        "空调滤芯每年更换，变速箱油每4万公里更换，火花塞10万公里更换。"
        "冷却液每两年更换一次，润滑油和防冻液也要定期检查。"
    )
    
    r1 = classifier.classify_with_auto_add(unknown1, auto_add_threshold=0.25, min_text_length=20)
    
    print(f"  原始分类: {r1['category_name']} (置信度: {r1['confidence']:.1%})")
    print(f"  触发自动新增: {r1['auto_added']}")
    
    if r1.get("auto_add_result"):
        ar = r1["auto_add_result"]
        print(f"  新增消息: {ar['message']}")
        kws = ar.get("keywords", [])
        print(f"  提取关键词({len(kws)}个): {kws[:8]}")
    
    t1_ok = r1["auto_added"] == True
    print(f"  结果: {PASS if t1_ok else FAIL} (期望 auto_added=True)")
    results.append(("测试1-自动新增触发", t1_ok))
    
    # ------------------------------------------------
    # 测试2：手动指定名称新增（宠物护理）
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试2：宠物护理（手动指定分类名称）")
    print("=" * 60)
    
    unknown2 = (
        "狗狗每天需要喝足够的水，成年犬每公斤体重需要60ml水。"
        "猫咪洗澡频率不宜过高，一般1-2个月一次。宠物猫需要定期驱虫、打疫苗。"
        "狗粮选择要看蛋白质含量，最好在25%以上。猫粮要注意磷含量不能太高。"
        "宠物换毛期需要每天梳毛，防止毛发打结。"
    )
    
    r2 = classifier.auto_add_category(unknown2, category_name="宠物护理")
    print(f"  结果: {r2['message']}")
    print(f"  关键词: {r2.get('keywords', [])[:8]}")
    
    t2_ok = r2["success"] == True and r2.get("category_name") == "宠物护理"
    print(f"  结果: {PASS if t2_ok else FAIL} (期望 success=True, name=宠物护理)")
    results.append(("测试2-手动命名新增", t2_ok))
    
    # ------------------------------------------------
    # 测试3：持久化验证
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试3：重新加载配置，验证持久化")
    print("=" * 60)
    
    c2 = ImageClassifier(config_path=str(test_cfg))
    cats = c2.get_categories()
    auto_cats = [c for c in cats if c.get("id", "").startswith("auto_")]
    
    print(f"  配置文件分类总数: {len(cats)}")
    print(f"  自动新增分类数: {len(auto_cats)}")
    for c in auto_cats:
        print(f"    - [{c['name']}] {c['keywords_count']} 个关键词")
    
    t3_ok = len(auto_cats) >= 1
    print(f"  结果: {PASS if t3_ok else FAIL} (期望 >= 1 个自动分类)")
    results.append(("测试3-持久化验证", t3_ok))
    
    # ------------------------------------------------
    # 测试4：向已有分类追加关键词（去重）
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试4：向已有分类 [宠物护理] 追加关键词")
    print("=" * 60)
    
    extra = "狗狗每年注射狂犬病疫苗和六联苗，猫咪需要三联疫苗，宠物健康检查很重要"
    r4 = c2.auto_add_category(extra, category_name="宠物护理")
    print(f"  结果: {r4['message']}")
    
    # 新增关键词应出现"追加"字样
    t4_ok = "新增关键词" in r4.get("message", "") or "已存在" in r4.get("message", "")
    print(f"  结果: {PASS if t4_ok else FAIL} (期望追加或已有)")
    results.append(("测试4-追加关键词", t4_ok))
    
    # ------------------------------------------------
    # 测试5：原有分类不受影响
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试5：原有分类（肠道健康）不受影响")
    print("=" * 60)
    
    r5 = c2.classify("益生菌对肠道菌群有益，促进消化，改善便秘")
    print(f"  分类: {r5['category_name']} (置信度: {r5['confidence']:.1%})")
    
    t5_ok = r5["category_id"] == "gut_health"
    print(f"  结果: {PASS if t5_ok else FAIL} (期望 gut_health)")
    results.append(("测试5-原有分类不受影响", t5_ok))
    
    # ------------------------------------------------
    # 测试6：文本太短，不触发自动新增
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试6：短文本不触发自动新增")
    print("=" * 60)
    
    short_text = "你好"
    r6 = classifier.classify_with_auto_add(short_text, auto_add_threshold=0.25, min_text_length=30)
    print(f"  分类: {r6['category_name']} (置信度: {r6['confidence']:.1%})")
    print(f"  自动新增: {r6['auto_added']}")
    
    t6_ok = r6["auto_added"] == False
    print(f"  结果: {PASS if t6_ok else FAIL} (期望 auto_added=False)")
    results.append(("测试6-短文本不触发", t6_ok))
    
    # ------------------------------------------------
    # 汇总
    # ------------------------------------------------
    print()
    print("=" * 60)
    print("测试汇总")
    print("=" * 60)
    
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    for name, ok in results:
        print(f"  {PASS if ok else FAIL}  {name}")
    
    print()
    print(f"通过: {passed}/{total} ({passed/total:.0%})")
    
    # 清理测试配置
    if test_cfg.exists():
        test_cfg.unlink()
        print("已清理测试配置文件")
    
    # 清理临时文件
    tmp = Path("D:/新建文件夹/t.txt")
    if tmp.exists():
        tmp.unlink()
    
    return passed == total


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
