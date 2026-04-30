#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版分批处理器 v2.1
- 移除复杂的state管理
- AI直接扫描文件夹获取图片
- 处理完成后直接调用脚本归档
- 增加归档重试机制和失败提示
- 简单可靠，不易出错
"""

import os
import sys
import shutil
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict, Optional

# 项目根目录
BASE_DIR = Path(__file__).parent.parent


class SimpleBatchProcessor:
    """简化版分批处理器"""
    
    def __init__(self):
        self.base_dir = BASE_DIR
        self.pending_dir = self.base_dir / "待处理图片"
        self.processed_dir = self.base_dir / "已处理图片"
        self.output_dir = self.base_dir / "处理结果"
        
        # 固定批次大小
        self.BATCH_SIZE = 12
        
        # 归档重试配置
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 0.5  # 秒
        
        # 加载配置
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
    
    def scan_images(self) -> List[Path]:
        """扫描所有待处理图片"""
        images = []
        extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}
        
        if not self.pending_dir.exists():
            print(f"[错误] 目录不存在: {self.pending_dir}")
            return images
        
        # 递归扫描所有图片
        for ext in extensions:
            for img_path in self.pending_dir.rglob(f"*{ext}"):
                if img_path.is_file():
                    images.append(img_path)
        
        # 按文件名排序
        images.sort(key=lambda x: x.name)
        return images
    
    def create_batches(self, images: List[Path]) -> List[List[Path]]:
        """将图片分批次"""
        batches = []
        for i in range(0, len(images), self.BATCH_SIZE):
            batch = images[i:i + self.BATCH_SIZE]
            batches.append(batch)
        return batches
    
    def _move_file_with_retry(self, src: Path, dst: Path, max_retries: int = 3) -> bool:
        """
        带重试机制的文件移动
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            max_retries: 最大重试次数
            
        Returns:
            是否成功
        """
        for attempt in range(max_retries):
            try:
                # 如果目标文件已存在，添加数字后缀
                if dst.exists():
                    stem = dst.stem
                    suffix = dst.suffix
                    counter = 1
                    while dst.exists():
                        dst = dst.parent / f"{stem}_{counter}{suffix}"
                        counter += 1
                
                shutil.move(str(src), str(dst))
                return True
                
            except PermissionError as e:
                if attempt < max_retries - 1:
                    print(f"    [重试 {attempt+1}/{max_retries}] 文件可能被占用: {src.name}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))  # 递增延迟
                else:
                    print(f"    [失败] 权限错误（文件可能被占用）: {src.name}")
                    return False
                    
            except Exception as e:
                print(f"    [失败] {src.name}: {e}")
                return False
        
        return False
    
    def archive_images(self, image_paths: List[Path]) -> Tuple[int, int, List[str]]:
        """
        归档指定图片（带重试机制）
        
        Args:
            image_paths: 要归档的图片路径列表
            
        Returns:
            (成功数, 失败数, 失败文件列表)
        """
        success = 0
        failed = 0
        failed_files = []
        
        print("[开始归档图片...]")
        print(f"[配置: 最大重试次数={self.MAX_RETRIES}, 重试延迟={self.RETRY_DELAY}秒]")
        
        for img_path in image_paths:
            # 计算相对路径，保持目录结构
            rel_path = img_path.relative_to(self.pending_dir)
            target_path = self.processed_dir / rel_path
            
            # 创建目标目录
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件（带重试）
            if self._move_file_with_retry(img_path, target_path, self.MAX_RETRIES):
                print(f"  [OK] {rel_path}")
                success += 1
            else:
                failed += 1
                failed_files.append(str(rel_path))
        
        # 显示结果摘要
        print(f"\n[归档结果]")
        print(f"  成功: {success} 个")
        print(f"  失败: {failed} 个")
        
        if failed_files:
            print(f"\n[失败文件列表]")
            for f in failed_files:
                print(f"  - {f}")
            print(f"\n[建议]")
            print(f"  1. 检查文件是否被其他程序占用（如图片查看器）")
            print(f"  2. 手动关闭占用程序后重新运行归档")
            print(f"  3. 或手动移动失败文件到: {self.processed_dir}")
        
        return success, failed, failed_files
    
    def archive_all(self) -> Tuple[int, int, List[str]]:
        """归档所有待处理图片"""
        images = self.scan_images()
        if not images:
            print("[没有待归档的图片]")
            return 0, 0, []
        return self.archive_images(images)
    
    def generate_word(self, template: Optional[str] = None) -> bool:
        """
        生成Word文档
        
        Args:
            template: 指定模板（可选）。如果不指定，使用配置文件中的模板
        """
        print("\n[生成Word文档...]")
        
        # 确定使用的模板
        use_template = template or self.word_template
        
        try:
            import subprocess
            
            # 构建命令：使用新的 generate_word.py（支持模板）
            cmd = [sys.executable, str(self.base_dir / "scripts" / "generate_word.py")]
            
            # 如果启用模板系统且指定了模板
            if self.enable_template_system and use_template:
                cmd.extend(["--template", use_template])
                print(f"[模板: {use_template}]")
            
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
                return True
            else:
                print(f"[警告] Word生成返回: {result.returncode}")
                if result.stderr:
                    print(f"[错误详情] {result.stderr[:200]}")
                return False
        except Exception as e:
            print(f"[错误] Word生成失败: {e}")
            return False
    
    def sync_ima(self) -> bool:
        """同步到ima"""
        print("\n[同步到ima...]")
        try:
            import subprocess
            # 使用实时输出模式，让用户能看到ima同步的详细过程
            result = subprocess.run(
                [sys.executable, str(self.base_dir / "ima_sync_v2.py"), "--force"],
                cwd=str(self.base_dir),
                capture_output=False,  # 改为False，让输出直接显示
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print("[OK] ima同步完成")
                return True
            else:
                print(f"[警告] ima同步返回: {result.returncode}")
                return False
        except Exception as e:
            print(f"[错误] ima同步失败: {e}")
            return False
    
    def update_prompt(self) -> bool:
        """更新启动提示词"""
        print("\n[更新启动提示词...]")
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(self.base_dir / "update_prompt.py")],
                cwd=str(self.base_dir),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode == 0:
                print("[OK] 启动提示词更新完成")
                return True
            else:
                print(f"[警告] 提示词更新返回: {result.returncode}")
                return False
        except Exception as e:
            print(f"[错误] 提示词更新失败: {e}")
            return False
    
    def finish_workflow(self, processed_images: List[Path] = None):
        """
        执行收尾流程
        
        Args:
            processed_images: AI处理的图片路径列表，如果为None则归档所有待处理图片
        """
        print("\n" + "="*50)
        print("[执行收尾流程]")
        print("="*50)
        
        # 1. 归档图片
        if processed_images:
            success, failed, failed_files = self.archive_images(processed_images)
        else:
            success, failed, failed_files = self.archive_all()
        
        # 如果归档有失败，提示用户
        if failed > 0:
            print(f"\n[!] 警告: {failed} 个文件归档失败")
            print("[!] 建议: 请检查失败文件列表，手动处理或重新运行归档")
        
        # 2. 生成Word文档
        self.generate_word()
        
        # 3. 同步到ima
        self.sync_ima()
        
        # 4. 更新启动提示词
        self.update_prompt()
        
        print("\n" + "="*50)
        if failed == 0:
            print("[OK] 收尾流程完成！")
        else:
            print(f"[!] 收尾流程完成，但有 {failed} 个文件未归档")
        print("="*50)
    
    def get_batch_info(self) -> dict:
        """获取批次信息（供AI使用）"""
        images = self.scan_images()
        batches = self.create_batches(images)
        
        return {
            "total_images": len(images),
            "total_batches": len(batches),
            "batch_size": self.BATCH_SIZE,
            "batches": [[str(img.relative_to(self.pending_dir)) for img in batch] for batch in batches]
        }


def main():
    """命令行入口"""
    processor = SimpleBatchProcessor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--status":
            # 显示状态
            info = processor.get_batch_info()
            print(f"\n{'='*50}")
            print("[待处理图片状态]")
            print(f"{'='*50}")
            print(f"总图片数: {info['total_images']} 张")
            print(f"批次数量: {info['total_batches']} 批")
            print(f"每批大小: {info['batch_size']} 张")
            print(f"{'='*50}\n")
            
            for i, batch in enumerate(info['batches'], 1):
                print(f"[第{i}批] {len(batch)}张:")
                for img in batch[:5]:
                    print(f"  - {img}")
                if len(batch) > 5:
                    print(f"  ... 还有 {len(batch)-5} 张")
                print()
        
        elif command == "--finish":
            # 执行收尾流程（归档所有）
            processor.finish_workflow()
        
        elif command == "--archive":
            # 仅归档
            success, failed, failed_files = processor.archive_all()
            if failed > 0:
                sys.exit(1)  # 有失败时返回错误码
        
        elif command == "--verify":
            # 验证归档状态
            print("\n[验证归档状态]")
            images = processor.scan_images()
            if images:
                print(f"[!] 发现 {len(images)} 个未归档文件:")
                for img in images[:10]:
                    rel_path = img.relative_to(processor.pending_dir)
                    print(f"  - {rel_path}")
                if len(images) > 10:
                    print(f"  ... 还有 {len(images)-10} 个文件")
                print("\n[建议] 运行以下命令归档:")
                print(f"  python scripts/simple_batch_processor.py --archive")
            else:
                print("[OK] 所有图片已归档，待处理文件夹为空")
        
        else:
            print(f"未知命令: {command}")
            print("可用命令: --status, --finish, --archive, --verify")
    else:
        # 默认显示状态
        info = processor.get_batch_info()
        print(f"\n[找到 {info['total_images']} 张图片，分 {info['total_batches']} 批处理]")
        print("\nAI处理完成后，请运行:")
        print(f"  python scripts/simple_batch_processor.py --finish")


if __name__ == "__main__":
    main()
