#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P2-1 初始化向导模块
首次使用时引导用户完成环境配置
"""

import sys
import os
import io
from pathlib import Path

# 修复 Windows 控制台编码 (只在需要时修复)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # 忽略编码修复失败

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


class InitWizard:
    """初始化向导"""
    
    VERSION = "1.0.0"
    
    # 颜色定义
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bg_blue': '\033[44m',
        'bold': '\033[1m',
    }
    
    def __init__(self, silent=False):
        self.silent = silent
        self.config = {
            'ocr_mode': None,
            'ima_sync': False,
            'template': 'default',
            'test_run': True
        }
    
    def _color(self, text, color):
        """添加颜色"""
        if self.silent:
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _print(self, text, color=None):
        """打印文本"""
        if color:
            print(self._color(text, color))
        else:
            print(text)
    
    def _print_header(self, text):
        """打印标题"""
        width = 60
        border = "=" * width
        self._print(f"\n{self._color(border, 'cyan')}")
        self._print(f"{self._color(text.center(width), 'cyan')}{self._color(border, 'cyan')}")
    
    def _print_step(self, num, total, text):
        """打印步骤"""
        self._print(f"\n{self._color(f'▶ 步骤 {num}/{total}', 'yellow')} {self._color(text, 'white')}")
    
    def _print_success(self, text):
        """打印成功信息"""
        self._print(f"  {self._color('✓', 'green')} {text}", 'green')
    
    def _print_error(self, text):
        """打印错误信息"""
        self._print(f"  {self._color('✗', 'red')} {text}", 'red')
    
    def _print_warning(self, text):
        """打印警告信息"""
        self._print(f"  {self._color('⚠', 'yellow')} {text}", 'yellow')
    
    def _print_info(self, text):
        """打印信息"""
        self._print(f"  {self._color('ℹ', 'blue')} {text}", 'blue')
    
    def _input_choice(self, prompt, options):
        """获取用户选择"""
        print(f"\n{prompt}")
        for i, (key, desc) in enumerate(options, 1):
            print(f"  [{i}] {desc}")
        
        while True:
            try:
                choice = input(f"\n请选择 [1-{len(options)}]: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(options):
                    return options[idx][0]
                print("无效选择，请重试")
            except ValueError:
                print("请输入数字")
    
    def _input_yesno(self, prompt, default='y'):
        """获取是/否选择"""
        suffix = "[Y/n]" if default == 'y' else "[y/N]"
        while True:
            choice = input(f"{prompt} {suffix}: ").strip().lower()
            if not choice:
                return default == 'y'
            if choice in ['y', 'yes', '是']:
                return True
            if choice in ['n', 'no', '否']:
                return False
            print("请输入 y 或 n")
    
    def check_environment(self):
        """检查环境"""
        self._print_header("环境检测")
        
        checks = []
        
        # Python 版本
        version = sys.version_info
        py_ok = version.major >= 3 and (version.major > 3 or version.minor >= 8)
        checks.append(("Python 版本", f"{version.major}.{version.minor}.{version.micro}", py_ok))
        
        # 依赖库
        deps = [
            ('PIL / Pillow', 'PIL'),
            ('pytesseract', 'pytesseract'),
            ('python-docx', 'docx'),
            ('PyYAML', 'yaml'),
            ('requests', 'requests'),
            ('tencentcloud-sdk-python', 'tencentcloud.common'),
            ('baidu-aip', 'aip'),
        ]
        
        for name, module in deps:
            try:
                __import__(module)
                checks.append((name, "已安装", True))
            except ImportError:
                checks.append((name, "未安装", False))
        
        # 显示结果
        all_ok = True
        for name, status, ok in checks:
            status_str = self._color("✓", 'green') + f" {status}" if ok else self._color("✗", 'red') + f" {status}"
            self._print(f"  {name:30} {status_str}")
            if not ok:
                all_ok = False
        
        if not all_ok:
            self._print_warning("\n部分依赖未安装，部分功能可能无法使用")
            self._print_info("安装依赖: pip install pillow pytesseract python-docx pyyaml requests")
        
        return all_ok
    
    def check_directories(self):
        """检查目录结构"""
        self._print_header("目录结构检测")
        
        root = Path(__file__).parent.parent
        dirs = [
            '待处理图片',
            '已处理图片',
            '知识库',
            'config',
            'logs',
        ]
        
        all_exist = True
        for d in dirs:
            path = root / d
            if path.exists():
                self._print_success(f"{d}/ 存在")
            else:
                self._print_error(f"{d}/ 不存在")
                all_exist = False
        
        return all_exist
    
    def configure_ocr(self):
        """配置 OCR"""
        self._print_header("OCR 配置选择")
        
        self._print("\n请选择 OCR 模式：\n")
        
        options = [
            ('local', '快速模式（仅本地 Tesseract）', 
             '  - 免费使用，无需 API 密钥\n  - 准确率较低，适合清晰的截图\n  - 需要安装 Tesseract OCR'),
            ('cloud', '标准模式（腾讯/百度云 OCR）', 
             '  - 推荐，准确率高\n  - 需要配置云服务 API 密钥\n  - 有免费额度'),
            ('full', '完整模式（全部启用）', 
             '  - 最稳定，自动切换\n  - 同时使用本地 + 云端 OCR\n  - 云端作为备用方案'),
        ]
        
        for i, (key, title, desc) in enumerate(options, 1):
            self._print(f"  [{i}] {self._color(title, 'white')}")
            self._print(f"      {desc}\n")
        
        mode = self._input_choice("\n请选择 OCR 模式:", [(o[0], o[1]) for o in options])
        self.config['ocr_mode'] = mode
        
        if mode != 'local':
            self._print_info("云端 OCR 需要在 config/credentials.yaml 中配置 API 密钥")
            self._check_cloud_credentials(mode)
        
        return mode
    
    def _check_cloud_credentials(self, mode):
        """检查云端凭证"""
        cred_file = Path(__file__).parent.parent / 'config' / 'credentials.yaml'
        
        if not cred_file.exists():
            self._print_warning(f"凭证文件不存在: {cred_file}")
            self._print_info("将创建默认配置模板")
            return
        
        import yaml
        try:
            with open(cred_file, 'r', encoding='utf-8') as f:
                creds = yaml.safe_load(f) or {}
            
            if mode in ['cloud', 'full']:
                if 'tencent' in mode and not creds.get('tencent'):
                    self._print_warning("腾讯云 OCR 未配置")
                if 'baidu' in str(mode) and not creds.get('baidu'):
                    self._print_warning("百度 OCR 未配置")
        except Exception as e:
            self._print_error(f"读取凭证失败: {e}")
    
    def configure_ima_sync(self):
        """配置 ima 同步"""
        self._print_header("IMA 同步配置（可选）")
        
        self._print("\n是否启用 IMA 笔记同步？")
        self._print("  - 启用后，处理完成的文档将自动同步到 IMA\n")
        
        enabled = self._input_yesno("启用 IMA 同步", default='n')
        self.config['ima_sync'] = enabled
        
        if enabled:
            self._print_info("IMA 同步需要配置 IMA API 凭证")
            self._print_info("请在 config/credentials.yaml 中配置 ima 相关设置")
    
    def select_template(self):
        """选择模板"""
        self._print_header("模板选择")
        
        self._print("\n请选择输出文档模板：\n")
        
        templates = [
            ('default', '默认模板', 
             '包含标题、来源、日期、内容摘要'),
            ('simple', '极简模板', 
             '仅包含标题和核心内容'),
            ('detailed', '详细模板', 
             '包含标题、来源、日期、关键词标签、完整内容'),
            ('custom', '自定义模板', 
             '从配置文件加载自定义模板'),
        ]
        
        for i, (key, title, desc) in enumerate(templates, 1):
            self._print(f"  [{i}] {self._color(title, 'white')}")
            self._print(f"      {desc}\n")
        
        template = self._input_choice("\n请选择模板:", [(t[0], t[1]) for t in templates])
        self.config['template'] = template
        
        if template == 'custom':
            self._print_info("请确保 config/templates.yaml 存在并包含自定义模板")
    
    def run_test(self):
        """运行测试"""
        self._print_header("测试运行")
        
        self._print("\n是否运行测试以确认配置正确？")
        
        if self._input_yesno("运行测试", default='y'):
            self._print_info("运行测试...")
            
            # 测试导入
            test_items = [
                ("导入 OCR 引擎", self._test_import_ocr),
                ("导入分类器", self._test_import_classifier),
                ("导入文档生成器", self._test_import_docgen),
            ]
            
            all_passed = True
            for name, test_func in test_items:
                try:
                    result = test_func()
                    if result:
                        self._print_success(f"{name}: 通过")
                    else:
                        self._print_error(f"{name}: 失败")
                        all_passed = False
                except Exception as e:
                    self._print_error(f"{name}: {e}")
                    all_passed = False
            
            if all_passed:
                self._print("\n" + self._color("=" * 60, 'green'))
                self._print(self._color("测试全部通过！".center(60), 'green'))
                self._print(self._color("=" * 60, 'green'))
            else:
                self._print_warning("\n部分测试失败，但仍可继续使用")
            
            return all_passed
        
        return True
    
    def _test_import_ocr(self):
        """测试 OCR 导入"""
        from scripts.ocr_engine import OCREngine
        return True
    
    def _test_import_classifier(self):
        """测试分类器导入"""
        from scripts.classifier_engine import ClassifierEngine
        return True
    
    def _test_import_docgen(self):
        """测试文档生成器导入"""
        from scripts.doc_generator import DocGenerator
        return True
    
    def save_config(self):
        """保存配置"""
        self._print_header("保存配置")
        
        config_file = Path(__file__).parent.parent / 'config' / 'init_config.yaml'
        
        import yaml
        try:
            # 确保目录存在
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            
            self._print_success(f"配置已保存到: {config_file}")
        except Exception as e:
            self._print_error(f"保存配置失败: {e}")
    
    def show_summary(self):
        """显示配置摘要"""
        self._print_header("配置摘要")
        
        summary = [
            ("OCR 模式", {
                'local': '快速模式（本地 Tesseract）',
                'cloud': '标准模式（云端 OCR）',
                'full': '完整模式（本地 + 云端）',
            }.get(self.config['ocr_mode'], '未知')),
            ("IMA 同步", "已启用" if self.config['ima_sync'] else "未启用"),
            ("文档模板", self.config['template']),
            ("测试运行", "已完成" if self.config['test_run'] else "已跳过"),
        ]
        
        for key, value in summary:
            self._print(f"  {key:15} {value}")
        
        self._print(f"\n{self._color('初始化完成！', 'green')}")
        self._print(f"\n{self._color('下一步：', 'cyan')} 将图片放入 '待处理图片/' 目录，然后运行:")
        self._print(f"  {self._color('python scripts/auto_batch_processor.py', 'white')}")
    
    def run(self):
        """运行完整初始化流程"""
        # 欢迎界面
        print("\n" + "=" * 60)
        print(self._color("  图片知识库整理工具 v2.0".center(60), 'bold'))
        print(self._color("  Image Knowledge Converter".center(60), 'cyan'))
        print("=" * 60)
        print(self._color("\n首次使用向导".center(60), 'yellow'))
        
        # 环境检测
        self._print_step(1, 5, "环境检测")
        self.check_environment()
        
        # 目录检测
        self._print_step(2, 5, "目录结构检测")
        self.check_directories()
        
        # OCR 配置
        self._print_step(3, 5, "OCR 配置")
        self.configure_ocr()
        
        # IMA 同步
        self._print_step(4, 5, "IMA 同步配置")
        self.configure_ima_sync()
        
        # 模板选择
        self._print_step(5, 5, "模板选择")
        self.select_template()
        
        # 测试运行
        if self._input_yesno("\n是否运行配置测试"):
            self.config['test_run'] = True
            self.run_test()
        
        # 保存配置
        self.save_config()
        
        # 显示摘要
        self.show_summary()
        
        return self.config


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='图片知识库整理工具 - 初始化向导')
    parser.add_argument('--silent', action='store_true', help='静默模式（无颜色）')
    parser.add_argument('--check-only', action='store_true', help='仅检查环境')
    
    args = parser.parse_args()
    
    wizard = InitWizard(silent=args.silent)
    
    if args.check_only:
        wizard.check_environment()
        wizard.check_directories()
    else:
        wizard.run()


if __name__ == '__main__':
    main()
