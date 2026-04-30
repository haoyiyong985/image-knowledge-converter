#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分批全自动处理器 v1.2
固定12张/批次，全自动连续处理，零人工干预
"""

import os
import sys
import json
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

# 导入现有模块
try:
    from scripts.batch_processor import BatchProcessor
    from scripts.ocr_recognize import OCRProcessor
except ImportError:
    pass


class AutoBatchProcessor:
    """智能分批全自动处理器"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or BASE_DIR
        self.pending_dir = self.base_dir / "待处理图片"
        self.processed_dir = self.base_dir / "已处理图片"
        self.output_dir = self.base_dir / "处理结果"
        self.knowledge_base_dir = self.base_dir / "knowledge_base"
        
        # 固定批次大小
        self.BATCH_SIZE = 12
        
        # 状态文件
        self.state_file = self.base_dir / "progress" / "auto_batch_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载状态和配置
        self.state = self._load_state()
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        self.word_template = "default"
        self.enable_template_system = True
        
        config_file = self.base_dir / "config" / "processing_config.yaml"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                self.word_template = config.get("word_template", "default")
                self.enable_template_system = config.get("enable_template_system", True)
            except Exception as e:
                print(f"[警告] 加载配置失败: {e}")
    
    def _load_state(self) -> Dict:
        """加载处理状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[警告] 加载状态失败: {e}")
        return {
            "total_images": 0,
            "total_batches": 0,
            "completed_batches": 0,
            "current_batch": 0,
            "processed_images": [],
            "failed_images": [],
            "start_time": None,
            "end_time": None
        }
    
    def _save_state(self):
        """保存处理状态"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[警告] 保存状态失败: {e}")
    
    def scan_images(self, folder_name: str = "") -> List[Path]:
        """
        扫描待处理图片
        
        Args:
            folder_name: 指定子文件夹，为空则扫描所有
        
        Returns:
            图片路径列表
        """
        images = []
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
        
        if folder_name:
            target_dir = self.pending_dir / folder_name
        else:
            target_dir = self.pending_dir
        
        if not target_dir.exists():
            print(f"[错误] 目录不存在: {target_dir}")
            return images
        
        # 递归扫描所有图片
        for ext in extensions:
            for img_path in target_dir.rglob(f"*{ext}"):
                if img_path.is_file():
                    images.append(img_path)
        
        # 去重并排序
        seen = set()
        unique_images = []
        for img in images:
            if str(img) not in seen:
                seen.add(str(img))
                unique_images.append(img)
        
        return sorted(unique_images)
    
    def calculate_batches(self, images: List[Path]) -> List[List[Path]]:
        """
        计算批次 (固定12张/批)
        
        Args:
            images: 图片路径列表
        
        Returns:
            批次列表，每个批次包含12张或更少的图片
        """
        batches = []
        for i in range(0, len(images), self.BATCH_SIZE):
            batch = images[i:i + self.BATCH_SIZE]
            batches.append(batch)
        return batches
    
    def get_image_size_category(self, img_path: Path) -> str:
        """获取图片大小类别(仅用于显示)"""
        try:
            size = img_path.stat().st_size
            size_kb = size / 1024
            
            if size_kb < 500:
                return f"小图({size_kb:.0f}KB)"
            elif size_kb < 2048:
                return f"中图({size_kb:.0f}KB)"
            elif size_kb < 5120:
                return f"大图({size_kb:.0f}KB)"
            else:
                return f"超大图({size_kb/1024:.1f}MB)"
        except:
            return "未知大小"
    
    def display_batch_info(self, batches: List[List[Path]]):
        """显示批次信息"""
        print(f"\n{'='*50}")
        print(f"[分批处理计划]")
        print(f"{'='*50}")
        print(f"总图片数: {sum(len(b) for b in batches)} 张")
        print(f"批次数量: {len(batches)} 批")
        print(f"每批数量: 最多 {self.BATCH_SIZE} 张")
        print(f"{'='*50}")
        
        for i, batch in enumerate(batches, 1):
            print(f"\n[第{i}批] {len(batch)}张图片:")
            for j, img in enumerate(batch, 1):
                size_info = self.get_image_size_category(img)
                print(f"  {j}. {img.name[:40]}... ({size_info})")
        
        print(f"\n{'='*50}\n")
    
    def process_batch(self, batch: List[Path], batch_num: int) -> Dict:
        """
        处理单个批次
        
        注意: 实际的OCR和分类由AI完成，这里只准备批次信息
        
        Args:
            batch: 批次图片列表
            batch_num: 批次编号
        
        Returns:
            批次处理结果
        """
        result = {
            "batch_num": batch_num,
            "total": len(batch),
            "images": [str(img) for img in batch],
            "image_names": [img.name for img in batch],
            "status": "prepared",
            "timestamp": datetime.now().isoformat()
        }
        
        # 保存批次信息供AI处理
        batch_info_file = self.output_dir / f"batch_{batch_num:03d}_info.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(batch_info_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        return result
    
    def prepare_all_batches(self, folder_name: str = "") -> Tuple[List[List[Path]], int]:
        """
        准备所有批次
        
        Args:
            folder_name: 指定子文件夹
        
        Returns:
            (批次列表, 总图片数)
        """
        # 1. 扫描图片
        print("[扫描待处理图片...]")
        images = self.scan_images(folder_name)
        
        if not images:
            print("[信息] 没有找到待处理图片")
            return [], 0
        
        # 2. 计算批次
        batches = self.calculate_batches(images)
        
        # 3. 显示批次信息
        self.display_batch_info(batches)
        
        # 4. 初始化状态
        self.state["total_images"] = len(images)
        self.state["total_batches"] = len(batches)
        self.state["completed_batches"] = 0
        self.state["current_batch"] = 0
        self.state["start_time"] = datetime.now().isoformat()
        self.state["end_time"] = None
        self._save_state()
        
        # 5. 准备批次文件
        print("[准备批次文件...]")
        for i, batch in enumerate(batches, 1):
            self.process_batch(batch, i)
        
        print(f"[OK] 已生成 {len(batches)} 个批次文件")
        
        return batches, len(images)
    
    def mark_batch_completed(self, batch_num: int):
        """标记批次完成"""
        self.state["completed_batches"] += 1
        self.state["current_batch"] = batch_num
        self._save_state()
    
    def get_progress(self) -> Dict:
        """获取处理进度"""
        total = self.state.get("total_batches", 0)
        completed = self.state.get("completed_batches", 0)
        
        return {
            "total_batches": total,
            "completed_batches": completed,
            "remaining_batches": total - completed,
            "progress_percent": (completed / total * 100) if total > 0 else 0,
            "is_complete": completed >= total and total > 0
        }
    
    def display_progress(self):
        """显示当前进度"""
        progress = self.get_progress()
        
        print(f"\n{'='*50}")
        print(f"[处理进度]")
        print(f"{'='*50}")
        print(f"总批次: {progress['total_batches']}")
        print(f"已完成: {progress['completed_batches']}")
        print(f"剩余: {progress['remaining_batches']}")
        print(f"进度: {progress['progress_percent']:.1f}%")
        print(f"{'='*50}\n")
        
        return progress
    
    def archive_images(self, folder_name: str = "") -> Tuple[int, int]:
        """
        归档已处理图片
        
        Returns:
            (成功数, 失败数)
        """
        print("[归档图片...]")
        
        success = 0
        failed = 0
        
        # 获取已处理的图片列表
        processed = self.state.get("processed_images", [])
        
        for img_path_str in processed:
            img_path = Path(img_path_str)
            if not img_path.exists():
                continue
            
            # 计算目标路径
            relative_path = img_path.relative_to(self.pending_dir)
            target_path = self.processed_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                shutil.move(str(img_path), str(target_path))
                success += 1
            except Exception as e:
                print(f"[错误] 归档失败 {img_path.name}: {e}")
                failed += 1
        
        print(f"归档完成: {success} 成功, {failed} 失败")
        return success, failed
    
    def finish_workflow(self):
        """完成工作流程 - 归档、生成Word、同步、更新提示词"""
        print("\n" + "="*50)
        print("[执行收尾流程]")
        print("="*50)
        
        # 1. 归档图片
        self.archive_images()
        
        # 2. 生成Word文档
        print("\n[生成Word文档...]")
        try:
            import subprocess
            
            # 构建命令：使用新的 generate_word.py（支持模板）
            cmd = [sys.executable, str(self.base_dir / "scripts" / "generate_word.py")]
            
            # 如果启用模板系统，添加模板参数
            if self.enable_template_system and self.word_template:
                cmd.extend(["--template", self.word_template])
                print(f"[模板: {self.word_template}]")
            
            result = subprocess.run(
                cmd,
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print("[OK] Word文档生成完成")
            else:
                print(f"[警告] Word生成返回: {result.returncode}")
                if result.stderr:
                    print(f"[错误详情] {result.stderr[:200]}")
        except Exception as e:
            print(f"[错误] Word生成失败: {e}")
        
        # 3. 同步到ima (使用--force模式确保文档变更一定能同步)
        print("\n[同步到ima...]")
        try:
            import subprocess
            # 使用 --force 模式强制重新同步所有文档，确保变更一定同步到ima
            result = subprocess.run(
                [sys.executable, str(self.base_dir / "ima_sync_v2.py"), "--force"],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print("[OK] ima强制同步完成")
            else:
                print(f"[警告] ima同步返回: {result.returncode}")
        except Exception as e:
            print(f"[错误] ima同步失败: {e}")
        
        # 4. 更新启动提示词
        print("\n[更新启动提示词...]")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(self.base_dir / "scripts" / "update_prompt.py")],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print("[OK] 启动提示词更新完成")
            else:
                print(f"[警告] 提示词更新返回: {result.returncode}")
        except Exception as e:
            print(f"[错误] 提示词更新失败: {e}")
        
        # 更新状态
        self.state["end_time"] = datetime.now().isoformat()
        self._save_state()
        
        print("\n" + "="*50)
        print("[OK] 收尾流程完成！")
        print("="*50)
    
    def generate_ai_prompt(self, batches: List[List[Path]]) -> str:
        """
        生成AI处理提示词
        
        Args:
            batches: 批次列表
        
        Returns:
            AI提示词
        """
        total = sum(len(b) for b in batches)
        
        prompt = f"""# 智能分批全自动处理任务

## 任务概览
- 总图片数: {total} 张
- 分 {len(batches)} 批处理
- 每批最多 12 张

## 处理流程

"""
        
        for i, batch in enumerate(batches, 1):
            prompt += f"""
### 第{i}批 ({len(batch)}张图片)
"""
            for j, img in enumerate(batch, 1):
                prompt += f"{j}. {img.name}\n"
            
            prompt += f"""
处理步骤:
1. 使用 read_file 读取以上{len(batch)}张图片
2. 识别图片中的文字内容
3. 根据内容分类整理
4. 更新对应的Markdown文档

"""
        
        prompt += f"""
## 收尾操作
所有批次处理完成后，请运行:
```bash
python scripts/auto_batch_processor.py --finish
```

## 注意事项
- 请按批次顺序处理
- 每批处理完更新文档
- 最后统一执行收尾命令
"""
        
        return prompt


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='智能分批全自动处理器')
    parser.add_argument('--folder', '-f', default='', help='指定子文件夹')
    parser.add_argument('--finish', action='store_true', help='执行收尾流程')
    parser.add_argument('--status', '-s', action='store_true', help='显示状态')
    
    args = parser.parse_args()
    
    processor = AutoBatchProcessor()
    
    if args.finish:
        # 执行收尾流程
        processor.finish_workflow()
    
    elif args.status:
        # 显示状态
        processor.display_progress()
    
    else:
        # 准备批次
        batches, total = processor.prepare_all_batches(args.folder)
        
        if total > 0:
            # 生成AI提示词
            prompt = processor.generate_ai_prompt(batches)
            
            # 保存提示词
            prompt_file = processor.output_dir / "ai_processing_prompt.txt"
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(prompt)
            
            print(f"\n[AI处理提示词已保存到: {prompt_file}]")
            print("\n" + "="*50)
            print("请AI按以下流程处理:")
            print("="*50)
            print(f"1. 读取批次信息文件 (batch_xxx_info.json)")
            print(f"2. 按批次处理图片 (OCR识别 + 分类)")
            print(f"3. 更新Markdown文档")
            print(f"4. 运行收尾命令: python scripts/auto_batch_processor.py --finish")
            print("="*50)


if __name__ == "__main__":
    main()
