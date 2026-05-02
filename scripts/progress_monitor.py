#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时监控与进度报告模块
========================

功能：
  1. 实时进度显示（控制台+Web界面）
  2. 性能指标收集与统计
  3. 可视化报告生成（HTML/图表）
  4. 处理历史记录管理
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path("D:/新建文件夹")
PROGRESS_DIR = BASE_DIR / "progress"
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


@dataclass
class ProcessingSession:
    """处理会话记录"""
    session_id: str
    topic: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_images: int = 0
    processed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    duplicate_count: int = 0
    status: str = "running"  # running, completed, failed, paused
    current_batch: int = 0
    total_batches: int = 0
    engine_name: str = ""
    events: List[Dict] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """获取处理时长（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def progress_percent(self) -> float:
        """获取进度百分比"""
        if self.total_images == 0:
            return 0
        return (self.processed_count / self.total_images) * 100
    
    @property
    def estimated_remaining(self) -> float:
        """预估剩余时间（秒）"""
        if self.processed_count == 0:
            return 0
        avg_time_per_image = self.duration / self.processed_count
        remaining_images = self.total_images - self.processed_count
        return avg_time_per_image * remaining_images


class ProgressMonitor:
    """进度监控器"""
    
    def __init__(self):
        self.sessions: Dict[str, ProcessingSession] = {}
        self.current_session: Optional[ProcessingSession] = None
        self._callbacks: List[Callable] = []
        self._update_interval = 1  # 更新间隔（秒）
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def start_session(self, topic: str, total_images: int, total_batches: int,
                      engine_name: str = "") -> ProcessingSession:
        """
        开始新的处理会话
        
        Args:
            topic: 主题名称
            total_images: 总图片数
            total_batches: 总批次数
            engine_name: OCR引擎名称
            
        Returns:
            会话对象
        """
        session_id = f"{topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = ProcessingSession(
            session_id=session_id,
            topic=topic,
            start_time=datetime.now(),
            total_images=total_images,
            total_batches=total_batches,
            engine_name=engine_name
        )
        
        self.sessions[session_id] = session
        self.current_session = session
        
        logger.info(f"[MONITOR] 开始会话: {session_id}")
        
        # 启动监控线程
        self._start_monitoring()
        
        return session
    
    def update_progress(self, processed: int, batch: int, 
                        success: int = 0, failed: int = 0, duplicates: int = 0):
        """更新进度"""
        if not self.current_session:
            return
        
        session = self.current_session
        session.processed_count = processed
        session.current_batch = batch
        session.success_count = success
        session.failed_count = failed
        session.duplicate_count = duplicates
        
        # 触发回调
        for callback in self._callbacks:
            try:
                callback(session)
            except Exception as e:
                logger.error(f"回调执行失败: {e}")
    
    def add_event(self, event_type: str, message: str, data: Dict = None):
        """添加事件"""
        if not self.current_session:
            return
        
        event = {
            "time": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "data": data or {}
        }
        
        self.current_session.events.append(event)
        
        # 只保留最近100个事件
        if len(self.current_session.events) > 100:
            self.current_session.events = self.current_session.events[-100:]
    
    def end_session(self, status: str = "completed"):
        """结束当前会话"""
        if not self.current_session:
            return
        
        session = self.current_session
        session.end_time = datetime.now()
        session.status = status
        
        logger.info(f"[MONITOR] 会话结束: {session.session_id} ({status})")
        
        # 保存会话记录
        self._save_session(session)
        
        # 停止监控
        self._stop_monitoring()
        
        self.current_session = None
    
    def _start_monitoring(self):
        """启动监控线程"""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def _stop_monitoring(self):
        """停止监控线程"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
    
    def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            if self.current_session:
                self._display_progress(self.current_session)
            time.sleep(self._update_interval)
    
    def _display_progress(self, session: ProcessingSession):
        """显示进度（控制台）"""
        # 清行并显示进度
        bar_length = 30
        filled = int(bar_length * session.progress_percent / 100)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        remaining_str = str(timedelta(seconds=int(session.estimated_remaining)))
        
        print(f"\r[{bar}] {session.progress_percent:.1f}% | "
              f"{session.processed_count}/{session.total_images} | "
              f"剩余: {remaining_str} | "
              f"✓{session.success_count} ✗{session.failed_count} ⚡{session.duplicate_count}", 
              end="", flush=True)
    
    def _save_session(self, session: ProcessingSession):
        """保存会话记录"""
        session_file = PROGRESS_DIR / f"{session.session_id}.json"
        
        data = {
            "session_id": session.session_id,
            "topic": session.topic,
            "start_time": session.start_time.isoformat(),
            "end_time": session.end_time.isoformat() if session.end_time else None,
            "total_images": session.total_images,
            "processed_count": session.processed_count,
            "success_count": session.success_count,
            "failed_count": session.failed_count,
            "duplicate_count": session.duplicate_count,
            "status": session.status,
            "duration": session.duration,
            "engine_name": session.engine_name,
            "events": session.events[-50:]  # 只保存最近50个事件
        }
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def register_callback(self, callback: Callable):
        """注册进度回调函数"""
        self._callbacks.append(callback)
    
    def get_session_history(self, limit: int = 10) -> List[Dict]:
        """获取会话历史"""
        sessions = []
        
        for session_file in sorted(PROGRESS_DIR.glob("*.json"), reverse=True)[:limit]:
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append(data)
            except Exception as e:
                logger.error(f"读取会话文件失败: {e}")
        
        return sessions


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.reports_dir = REPORTS_DIR
    
    def generate_html_report(self, session: ProcessingSession) -> str:
        """
        生成HTML报告
        
        Args:
            session: 处理会话
            
        Returns:
            HTML文件路径
        """
        report_file = self.reports_dir / f"report_{session.session_id}.html"
        
        # 计算统计
        success_rate = (session.success_count / session.processed_count * 100) if session.processed_count > 0 else 0
        avg_time = (session.duration / session.processed_count) if session.processed_count > 0 else 0
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片处理报告 - {session.topic}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: #333;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            color: #666;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-2px);
        }}
        .stat-card .label {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-card .subvalue {{
            font-size: 14px;
            color: #666;
            margin-top: 5px;
        }}
        .progress-section {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 15px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 15px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .events-section {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        .events-section h2 {{
            color: #333;
            margin-bottom: 15px;
        }}
        .event-item {{
            padding: 12px;
            border-left: 3px solid #667eea;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }}
        .event-time {{
            font-size: 12px;
            color: #888;
        }}
        .event-message {{
            color: #333;
            margin-top: 5px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-completed {{
            background: #d4edda;
            color: #155724;
        }}
        .status-running {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📸 图片处理报告</h1>
            <div class="subtitle">
                主题: {session.topic} | 
                时间: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')} | 
                状态: <span class="status-badge status-{session.status}">{session.status}</span>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">总图片数</div>
                <div class="value">{session.total_images}</div>
            </div>
            <div class="stat-card">
                <div class="label">成功识别</div>
                <div class="value" style="color: #28a745;">{session.success_count}</div>
                <div class="subvalue">成功率 {success_rate:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="label">识别失败</div>
                <div class="value" style="color: #dc3545;">{session.failed_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">重复内容</div>
                <div class="value" style="color: #ffc107;">{session.duplicate_count}</div>
            </div>
            <div class="stat-card">
                <div class="label">处理时长</div>
                <div class="value">{timedelta(seconds=int(session.duration))}</div>
            </div>
            <div class="stat-card">
                <div class="label">平均每张</div>
                <div class="value">{avg_time:.1f}s</div>
            </div>
        </div>
        
        <div class="progress-section">
            <h3>处理进度</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {session.progress_percent}%">
                    {session.progress_percent:.1f}%
                </div>
            </div>
            <p style="margin-top: 15px; color: #666;">
                已处理: {session.processed_count} / {session.total_images} 张图片
                ({session.current_batch} / {session.total_batches} 批次)
            </p>
        </div>
        
        <div class="events-section">
            <h2>📝 处理日志</h2>
            {self._generate_events_html(session.events[-20:])}
        </div>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)
    
    def _generate_events_html(self, events: List[Dict]) -> str:
        """生成事件HTML"""
        if not events:
            return "<p style='color: #888;'>暂无事件记录</p>"
        
        html = ""
        for event in events:
            time_str = event.get("time", "")[11:19]  # 只显示时分秒
            html += f"""
            <div class="event-item">
                <div class="event-time">{time_str}</div>
                <div class="event-message">{event.get("message", "")}</div>
            </div>
            """
        
        return html
    
    def generate_summary_report(self) -> str:
        """
        生成汇总报告
        
        Returns:
            HTML文件路径
        """
        monitor = ProgressMonitor()
        sessions = monitor.get_session_history(limit=50)
        
        # 计算汇总统计
        total_images = sum(s.get("total_images", 0) for s in sessions)
        total_success = sum(s.get("success_count", 0) for s in sessions)
        total_failed = sum(s.get("failed_count", 0) for s in sessions)
        total_duration = sum(s.get("duration", 0) for s in sessions)
        
        report_file = self.reports_dir / f"summary_report_{datetime.now().strftime('%Y%m%d')}.html"
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>图片知识库处理汇总报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
        }}
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-card .label {{ color: #888; font-size: 14px; }}
        .sessions-table {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        .sessions-table table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .sessions-table th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        .sessions-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        .sessions-table tr:hover {{
            background: #f8f9fa;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 图片知识库处理汇总报告</h1>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{len(sessions)}</div>
                <div class="label">总会话数</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_images}</div>
                <div class="label">总处理图片</div>
            </div>
            <div class="stat-card">
                <div class="value">{total_success}</div>
                <div class="label">成功识别</div>
            </div>
            <div class="stat-card">
                <div class="value">{timedelta(seconds=int(total_duration))}</div>
                <div class="label">总处理时长</div>
            </div>
        </div>
        
        <div class="sessions-table">
            <table>
                <thead>
                    <tr>
                        <th>主题</th>
                        <th>时间</th>
                        <th>图片数</th>
                        <th>成功</th>
                        <th>失败</th>
                        <th>状态</th>
                        <th>时长</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_sessions_rows(sessions)}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(report_file)
    
    def _generate_sessions_rows(self, sessions: List[Dict]) -> str:
        """生成会话表格行"""
        rows = ""
        for session in sessions:
            status_color = {
                "completed": "#28a745",
                "running": "#ffc107",
                "failed": "#dc3545",
                "paused": "#6c757d"
            }.get(session.get("status"), "#666")
            
            start_time = session.get("start_time", "")
            if start_time:
                start_time = start_time[:16].replace("T", " ")
            
            duration = session.get("duration", 0)
            duration_str = str(timedelta(seconds=int(duration)))
            
            rows += f"""
            <tr>
                <td>{session.get("topic", "未知")}</td>
                <td>{start_time}</td>
                <td>{session.get("total_images", 0)}</td>
                <td>{session.get("success_count", 0)}</td>
                <td>{session.get("failed_count", 0)}</td>
                <td style="color: {status_color}; font-weight: bold;">{session.get("status", "未知")}</td>
                <td>{duration_str}</td>
            </tr>
            """
        
        return rows


def main():
    """测试进度监控"""
    print("=" * 60)
    print("进度监控与报告生成测试")
    print("=" * 60)
    
    monitor = ProgressMonitor()
    reporter = ReportGenerator()
    
    # 模拟处理会话
    session = monitor.start_session(
        topic="测试主题",
        total_images=100,
        total_batches=10,
        engine_name="腾讯云OCR"
    )
    
    # 模拟处理过程
    for i in range(1, 11):
        time.sleep(0.5)
        monitor.update_progress(
            processed=i * 10,
            batch=i,
            success=i * 9,
            failed=i,
            duplicates=0
        )
        monitor.add_event("batch_complete", f"批次 {i} 完成")
    
    monitor.end_session("completed")
    
    # 生成报告
    report_path = reporter.generate_html_report(session)
    print(f"\n报告已生成: {report_path}")
    
    # 生成汇总报告
    summary_path = reporter.generate_summary_report()
    print(f"汇总报告已生成: {summary_path}")


if __name__ == "__main__":
    main()
