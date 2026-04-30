#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分批处理器
==============
功能：
1. 智能分批（按文件大小、内容相关性）
2. 断点续传（记录处理状态）
3. 进度追踪（显示每批处理进度）
4. 失败重试（自动重试失败的批次）

作者：AI Assistant
版本：v1.0
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path("D:/新建文件夹")
STATE_FILE = BASE_DIR / ".workbuddy" / "memory" / "batch_state.json"

# 分批配置
BATCH_CONFIG = {
    "small": {"max_size": 500 * 1024, "batch_size": 10},     # <500KB: 10张/批
    "medium": {"max_size": 2 * 1024 * 1024, "batch_size": 6},  # 500KB-2MB: 6张/批
    "large": {"max_size": 5 * 1024 * 1024, "batch_size": 4},   # 2MB-5MB: 4张/批
    "xlarge": {"max_size": float('inf'), "batch_size": 2}      # >5MB: 2张/批
}

# ============================================================
# 数据类
# ============================================================

@dataclass
class ImageInfo:
    """图片信息"""
    path: str
    name: str
    size: int
    folder: str
    hash: str = ""  # 文件哈希，用于检测重复
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class BatchInfo:
    """批次信息"""
    batch_id: str           # 批次ID
    folder: str             # 所属文件夹
    images: List[str]       # 图片路径列表
    status: str             # pending/processing/completed/failed
    created_at: str         # 创建时间
    started_at: Optional[str] = None   # 开始处理时间
    completed_at: Optional[str] = None # 完成时间
    result: Optional[str] = None       # 处理结果摘要
    retry_count: int = 0    # 重试次数
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class ProcessingState:
    """处理状态"""
    session_id: str         # 会话ID
    started_at: str         # 开始时间
    total_images: int       # 总图片数
    total_batches: int      # 总批次数
    completed_batches: int = 0  # 已完成批次数
    failed_batches: int = 0     # 失败批次数
    batches: Dict[str, BatchInfo] = None  # 批次信息
    
    def __post_init__(self):
        if self.batches is None:
            self.batches = {}
    
    def to_dict(self):
        data = asdict(self)
        if self.batches:
            data['batches'] = {k: v.to_dict() if isinstance(v, BatchInfo) else v 
                              for k, v in self.batches.items()}
        return data
    
    @classmethod
    def from_dict(cls, data):
        if 'batches' in data and data['batches']:
            data['batches'] = {k: BatchInfo.from_dict(v) for k, v in data['batches'].items()}
        return cls(**data)

# ============================================================
# 工具函数
# ============================================================

def calculate_file_hash(file_path: str) -> str:
    """计算文件MD5哈希"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()[:16]  # 取前16位
    except Exception:
        return ""

def get_batch_size(image_path: str) -> Tuple[int, str]:
    """根据图片大小获取批次大小"""
    try:
        size = os.path.getsize(image_path)
        for category, config in BATCH_CONFIG.items():
            if size < config['max_size']:
                return config['batch_size'], category
    except Exception:
        pass
    return 5, "medium"

def load_state() -> Optional[ProcessingState]:
    """加载处理状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return ProcessingState.from_dict(data)
        except Exception as e:
            print(f"[WARN] 加载状态失败: {e}")
    return None

def save_state(state: ProcessingState):
    """保存处理状态"""
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] 保存状态失败: {e}")

def clear_state():
    """清除处理状态"""
    if STATE_FILE.exists():
        try:
            STATE_FILE.unlink()
            print("[INFO] 处理状态已清除")
        except Exception as e:
            print(f"[ERROR] 清除状态失败: {e}")

# ============================================================
# 分批处理器
# ============================================================

class BatchProcessor:
    """智能分批处理器"""
    
    def __init__(self, source_dir: Path = None):
        self.source_dir = source_dir or (BASE_DIR / "待处理图片")
        self.state: Optional[ProcessingState] = None
        
    def scan_images(self) -> List[ImageInfo]:
        """扫描所有待处理图片"""
        images = []
        seen_paths = set()  # 用于去重
        
        if not self.source_dir.exists():
            return images
        
        for folder in self.source_dir.iterdir():
            if folder.is_dir():
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                    # 扫描小写扩展名
                    for img_path in folder.glob(ext):
                        path_str = str(img_path)
                        if path_str not in seen_paths:
                            seen_paths.add(path_str)
                            images.append(ImageInfo(
                                path=path_str,
                                name=img_path.name,
                                size=img_path.stat().st_size,
                                folder=folder.name,
                                hash=calculate_file_hash(path_str)
                            ))
                    # 扫描大写扩展名（但检查是否已存在）
                    for img_path in folder.glob(ext.upper()):
                        path_str = str(img_path)
                        if path_str not in seen_paths:
                            seen_paths.add(path_str)
                            images.append(ImageInfo(
                                path=path_str,
                                name=img_path.name,
                                size=img_path.stat().st_size,
                                folder=folder.name,
                                hash=calculate_file_hash(path_str)
                            ))
        
        return images
    
    def create_batches(self, images: List[ImageInfo]) -> List[BatchInfo]:
        """创建批次（按文件夹和大小智能分批）"""
        # 按文件夹分组
        folder_groups: Dict[str, List[ImageInfo]] = {}
        for img in images:
            if img.folder not in folder_groups:
                folder_groups[img.folder] = []
            folder_groups[img.folder].append(img)
        
        batches = []
        batch_counter = 0
        
        for folder_name, folder_images in folder_groups.items():
            # 按大小排序
            folder_images.sort(key=lambda x: x.size)
            
            current_batch = []
            current_batch_size_limit = 5
            
            for img in folder_images:
                batch_size, category = get_batch_size(img.path)
                
                # 如果当前批次已满，创建新批次
                if len(current_batch) >= batch_size:
                    batch_counter += 1
                    batch_id = f"{folder_name}_{batch_counter:03d}"
                    batches.append(BatchInfo(
                        batch_id=batch_id,
                        folder=folder_name,
                        images=[i.path for i in current_batch],
                        status="pending",
                        created_at=datetime.now().isoformat()
                    ))
                    current_batch = [img]
                else:
                    current_batch.append(img)
            
            # 处理剩余图片
            if current_batch:
                batch_counter += 1
                batch_id = f"{folder_name}_{batch_counter:03d}"
                batches.append(BatchInfo(
                    batch_id=batch_id,
                    folder=folder_name,
                    images=[i.path for i in current_batch],
                    status="pending",
                    created_at=datetime.now().isoformat()
                ))
        
        return batches
    
    def initialize(self) -> ProcessingState:
        """初始化处理会话"""
        # 检查是否有未完成的会话
        existing_state = load_state()
        if existing_state:
            pending = sum(1 for b in existing_state.batches.values() if b.status == "pending")
            processing = sum(1 for b in existing_state.batches.values() if b.status == "processing")
            
            if pending > 0 or processing > 0:
                print(f"[INFO] 发现未完成的会话: {existing_state.session_id}")
                print(f"       已完成: {existing_state.completed_batches}/{existing_state.total_batches}")
                return existing_state
        
        # 创建新会话
        images = self.scan_images()
        if not images:
            print("[INFO] 没有待处理的图片")
            return None
        
        batches = self.create_batches(images)
        
        self.state = ProcessingState(
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            started_at=datetime.now().isoformat(),
            total_images=len(images),
            total_batches=len(batches),
            batches={b.batch_id: b for b in batches}
        )
        
        save_state(self.state)
        
        print(f"[INFO] 新会话已创建: {self.state.session_id}")
        print(f"       共 {self.state.total_images} 张图片，分成 {self.state.total_batches} 批次")
        
        return self.state
    
    def get_next_batch(self) -> Optional[BatchInfo]:
        """获取下一个待处理的批次"""
        if not self.state:
            self.state = load_state()
        
        if not self.state:
            return None
        
        # 查找pending状态的批次
        for batch_id, batch in self.state.batches.items():
            if batch.status == "pending":
                batch.status = "processing"
                batch.started_at = datetime.now().isoformat()
                save_state(self.state)
                return batch
        
        return None
    
    def mark_batch_completed(self, batch_id: str, result: str = ""):
        """标记批次为已完成"""
        if not self.state:
            self.state = load_state()
        
        if self.state and batch_id in self.state.batches:
            batch = self.state.batches[batch_id]
            # 只有当状态不是completed时才增加计数
            if batch.status != "completed":
                batch.status = "completed"
                batch.completed_at = datetime.now().isoformat()
                batch.result = result
                self.state.completed_batches += 1
                save_state(self.state)
                print(f"[INFO] 批次 {batch_id} 已完成")
            else:
                print(f"[INFO] 批次 {batch_id} 已经是完成状态")
    
    def mark_batch_failed(self, batch_id: str, error: str = ""):
        """标记批次为失败"""
        if self.state and batch_id in self.state.batches:
            batch = self.state.batches[batch_id]
            batch.status = "failed"
            batch.result = error
            batch.retry_count += 1
            self.state.failed_batches += 1
            
            # 如果重试次数小于3，重置为pending状态
            if batch.retry_count < 3:
                batch.status = "pending"
                print(f"[WARN] 批次 {batch_id} 失败，将在下次重试 ({batch.retry_count}/3)")
            else:
                print(f"[ERROR] 批次 {batch_id} 失败超过3次，已放弃")
            
            save_state(self.state)
    
    def get_progress(self) -> Dict:
        """获取处理进度"""
        if not self.state:
            self.state = load_state()
        
        if not self.state:
            return {}
        
        pending = sum(1 for b in self.state.batches.values() if b.status == "pending")
        processing = sum(1 for b in self.state.batches.values() if b.status == "processing")
        completed = sum(1 for b in self.state.batches.values() if b.status == "completed")
        failed = sum(1 for b in self.state.batches.values() if b.status == "failed")
        
        total = self.state.total_batches
        progress_pct = (completed / total * 100) if total > 0 else 0
        
        return {
            "session_id": self.state.session_id,
            "total": total,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "progress": progress_pct,
            "is_complete": pending == 0 and processing == 0
        }
    
    def print_progress(self):
        """打印进度"""
        progress = self.get_progress()
        if not progress:
            print("[INFO] 没有正在进行的处理任务")
            return
        
        print("\n" + "=" * 60)
        print(f"处理进度 - 会话 {progress['session_id']}")
        print("=" * 60)
        print(f"总批次: {progress['total']}")
        print(f"已完成: {progress['completed']} ({progress['progress']:.1f}%)")
        print(f"处理中: {progress['processing']}")
        print(f"待处理: {progress['pending']}")
        print(f"失败: {progress['failed']}")
        print("=" * 60)
        
        if progress['is_complete']:
            print("[INFO] 所有批次处理完成！")
    
    def reset_failed_batches(self):
        """重置失败的批次为pending状态"""
        if not self.state:
            self.state = load_state()
        
        if not self.state:
            return
        
        reset_count = 0
        for batch in self.state.batches.values():
            if batch.status == "failed":
                batch.status = "pending"
                batch.retry_count = 0
                reset_count += 1
        
        if reset_count > 0:
            save_state(self.state)
            print(f"[INFO] 已重置 {reset_count} 个失败批次")

# ============================================================
# 命令行接口
# ============================================================

def main():
    """命令行入口"""
    import sys
    
    processor = BatchProcessor()
    
    if len(sys.argv) < 2:
        print("用法: python batch_processor.py <命令>")
        print("")
        print("命令:")
        print("  init          - 初始化处理会话")
        print("  next          - 获取下一个批次")
        print("  progress      - 显示处理进度")
        print("  complete <id> - 标记批次完成")
        print("  fail <id>     - 标记批次失败")
        print("  reset         - 重置失败批次")
        print("  clear         - 清除处理状态")
        return
    
    command = sys.argv[1]
    
    if command == "init":
        state = processor.initialize()
        if state:
            processor.print_progress()
    
    elif command == "next":
        batch = processor.get_next_batch()
        if batch:
            print(f"[INFO] 下一批次: {batch.batch_id}")
            print(f"       文件夹: {batch.folder}")
            print(f"       图片数: {len(batch.images)}")
            for img in batch.images:
                print(f"         - {os.path.basename(img)}")
        else:
            print("[INFO] 没有待处理的批次")
    
    elif command == "progress":
        processor.print_progress()
    
    elif command == "complete":
        if len(sys.argv) < 3:
            print("[ERROR] 请提供批次ID")
            return
        processor.mark_batch_completed(sys.argv[2])
    
    elif command == "fail":
        if len(sys.argv) < 3:
            print("[ERROR] 请提供批次ID")
            return
        processor.mark_batch_failed(sys.argv[2])
    
    elif command == "reset":
        processor.reset_failed_batches()
    
    elif command == "clear":
        clear_state()
    
    else:
        print(f"[ERROR] 未知命令: {command}")

if __name__ == "__main__":
    main()
