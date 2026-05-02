#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 配置向导
帮助用户配置百度 OCR 和 Tesseract 路径
"""

import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog


def config_baidu_ocr():
    """配置百度 OCR"""
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showinfo(
        "配置百度 OCR",
        "请提供您的百度 OCR API 密钥\n\n"
        "获取地址: https://ai.baidu.com/tech/ocr\n"
        "免费额度: 50000次/月"
    )
    
    # 输入 AppID
    app_id = simpledialog.askstring(
        "百度 OCR - AppID",
        "请输入百度 OCR 的 AppID:\n(纯数字)",
        parent=root
    )
    
    if not app_id:
        messagebox.showwarning("取消", "未输入 AppID，配置取消")
        root.destroy()
        return False
    
    # 输入 API Key
    api_key = simpledialog.askstring(
        "百度 OCR - API Key",
        "请输入百度 OCR 的 API Key:",
        parent=root
    )
    
    if not api_key:
        messagebox.showwarning("取消", "未输入 API Key，配置取消")
        root.destroy()
        return False
    
    # 输入 Secret Key
    secret_key = simpledialog.askstring(
        "百度 OCR - Secret Key",
        "请输入百度 OCR 的 Secret Key:",
        parent=root
    )
    
    if not secret_key:
        messagebox.showwarning("取消", "未输入 Secret Key，配置取消")
        root.destroy()
        return False
    
    root.destroy()
    
    # 更新 ocr_manager.py 文件
    return update_ocr_manager_config(app_id, api_key, secret_key)


def update_ocr_manager_config(app_id, api_key, secret_key):
    """更新 ocr_manager.py 配置文件"""
    config_file = "ocr_manager.py"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置
        old_config = """BAIDU_CONFIG = {
    'app_id': '',      # 填入您的 AppID
    'api_key': '',     # 填入您的 API Key
    'secret_key': ''   # 填入您的 Secret Key
}"""
        
        new_config = f"""BAIDU_CONFIG = {{
    'app_id': '{app_id}',      # 填入您的 AppID
    'api_key': '{api_key}',     # 填入您的 API Key
    'secret_key': '{secret_key}'   # 填入您的 Secret Key
}}"""
        
        if old_config in content:
            content = content.replace(old_config, new_config)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            messagebox.showinfo(
                "配置成功",
                f"百度 OCR 配置已保存到 {config_file}\n\n"
                f"AppID: {app_id[:4]}****\n"
                f"API Key: {api_key[:8]}****\n"
                f"Secret Key: {secret_key[:8]}****"
            )
            return True
        else:
            messagebox.showerror(
                "配置失败",
                "无法找到配置模板，请手动编辑 ocr_manager.py"
            )
            return False
            
    except Exception as e:
        messagebox.showerror("配置失败", f"保存配置时出错: {e}")
        return False


def config_tesseract_path():
    """配置 Tesseract 路径"""
    root = tk.Tk()
    root.withdraw()
    
    # 询问是否已安装 Tesseract
    answer = messagebox.askyesno(
        "Tesseract 配置",
        "您是否已安装 Tesseract-OCR?\n\n"
        "如果未安装，请先下载安装:\n"
        "https://github.com/UB-Mannheim/tesseract/wiki"
    )
    
    if not answer:
        messagebox.showinfo(
            "安装提示",
            "请按以下步骤安装 Tesseract:\n\n"
            "1. 访问 https://github.com/UB-Mannheim/tesseract/wiki\n"
            "2. 下载最新版安装程序\n"
            "3. 运行安装程序\n"
            "4. 安装时勾选中文语言包 (chi_sim)\n"
            "5. 完成安装后重新运行此配置"
        )
        root.destroy()
        return False
    
    # 选择 Tesseract 安装目录
    messagebox.showinfo(
        "选择路径",
        "请选择 Tesseract 安装目录\n"
        "(通常位于 C:\\Program Files\\Tesseract-OCR)"
    )
    
    tess_path = filedialog.askopenfilename(
        title="选择 tesseract.exe",
        filetypes=[("Executable", "tesseract.exe")],
        initialdir=r"C:\Program Files"
    )
    
    root.destroy()
    
    if not tess_path:
        messagebox.showwarning("取消", "未选择路径，配置取消")
        return False
    
    if not os.path.exists(tess_path):
        messagebox.showerror("错误", f"文件不存在: {tess_path}")
        return False
    
    # 更新配置
    return update_tesseract_config(tess_path)


def update_tesseract_config(tess_path):
    """更新 Tesseract 路径配置"""
    config_file = "ocr_manager.py"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换配置
        old_config = """TESSERACT_PATH = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
if os.path.exists(TESSERACT_PATH):
    os.environ['TESSERACT_CMD'] = TESSERACT_PATH"""
        
        new_config = f"""TESSERACT_PATH = r'{tess_path}'
if os.path.exists(TESSERACT_PATH):
    os.environ['TESSERACT_CMD'] = TESSERACT_PATH"""
        
        if old_config in content:
            content = content.replace(old_config, new_config)
        else:
            # 尝试替换其他形式
            content = content.replace(
                "TESSERACT_PATH = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'",
                f"TESSERACT_PATH = r'{tess_path}'"
            )
        
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        messagebox.showinfo(
            "配置成功",
            f"Tesseract 路径已配置:\n{tess_path}"
        )
        return True
        
    except Exception as e:
        messagebox.showerror("配置失败", f"保存配置时出错: {e}")
        return False


def main():
    """主函数"""
    root = tk.Tk()
    root.withdraw()
    
    # 显示主菜单
    choice = simpledialog.askstring(
        "OCR 配置向导",
        "请选择要配置的 OCR 引擎:\n\n"
        "1 - 配置百度 OCR\n"
        "2 - 配置 Tesseract 路径\n"
        "3 - 配置全部\n"
        "0 - 退出",
        parent=root
    )
    
    root.destroy()
    
    if choice == "1":
        config_baidu_ocr()
    elif choice == "2":
        config_tesseract_path()
    elif choice == "3":
        config_baidu_ocr()
        config_tesseract_path()
    else:
        print("退出配置")


if __name__ == "__main__":
    main()
