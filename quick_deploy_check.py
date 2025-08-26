#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速部署检查脚本
"""

import sys
import os
import subprocess
import platform
import urllib.request
from pathlib import Path

def check_internet():
    """检查网络连接"""
    print("[CHECK] 检查网络连接...")
    
    test_urls = [
        "https://www.google.com",
        "https://github.com",
        "https://dl.google.com"
    ]
    
    for url in test_urls:
        try:
            urllib.request.urlopen(url, timeout=10)
            print(f"[OK] 可以访问: {url}")
            return True
        except Exception as e:
            print(f"[FAIL] 无法访问 {url}: {e}")
    
    return False

def check_system():
    """检查系统环境"""
    print("[CHECK] 检查系统环境...")
    print(f"  - 操作系统: {platform.system()} {platform.release()}")
    print(f"  - Python版本: {sys.version}")
    print(f"  - 当前目录: {os.getcwd()}")
    
    # 检查管理员权限
    if platform.system() == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            print(f"  - 管理员权限: {'是' if is_admin else '否'}")
        except:
            print("  - 管理员权限: 无法检测")
    
    return True

def check_existing_tools():
    """检查已有工具"""
    print("[CHECK] 检查已安装的工具...")
    
    tools = {
        'java': 'java -version',
        'python': 'python --version',
        'pip': 'pip --version',
        'git': 'git --version'
    }
    
    available_tools = {}
    
    for tool, command in tools.items():
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Java version输出在stderr
                output = result.stderr if tool == 'java' and result.stderr else result.stdout
                version = output.strip().split('\n')[0]
                print(f"  ✓ {tool}: {version}")
                available_tools[tool] = True
            else:
                print(f"  ✗ {tool}: 未安装")
                available_tools[tool] = False
        except Exception as e:
            print(f"  ✗ {tool}: 检查失败 - {e}")
            available_tools[tool] = False
    
    return available_tools

def install_basic_dependencies():
    """安装基础依赖"""
    print("[INSTALL] 安装基础Python依赖...")
    
    basic_deps = [
        'requests',
        'urllib3'
    ]
    
    for dep in basic_deps:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                         check=True, capture_output=True)
            print(f"  ✓ 已安装: {dep}")
        except subprocess.CalledProcessError:
            print(f"  ✗ 安装失败: {dep}")

def main():
    """主检查函数"""
    print("=== 快速部署环境检查 ===\n")
    
    # 系统检查
    check_system()
    print()
    
    # 网络检查
    if not check_internet():
        print("[WARNING] 网络连接有问题，可能影响下载")
    print()
    
    # 工具检查
    available_tools = check_existing_tools()
    print()
    
    # 安装基础依赖
    install_basic_dependencies()
    print()
    
    # 生成建议
    print("=== 部署建议 ===")
    
    if not available_tools.get('java', False):
        print("1. 需要安装Java JDK 8+")
        print("   - 下载链接: https://adoptium.net/")
        print("   - 或使用chocolatey: choco install openjdk11")
    
    if not available_tools.get('git', False):
        print("2. 建议安装Git（可选）")
        print("   - 下载链接: https://git-scm.com/")
    
    print("3. 主要部署脚本正在后台运行...")
    print("4. 请耐心等待自动下载和安装过程")
    print("5. 整个过程可能需要30-60分钟")

if __name__ == '__main__':
    main()