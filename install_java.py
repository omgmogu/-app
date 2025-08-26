#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
便携式Java JDK安装脚本
"""

import urllib.request
import zipfile
import os
import sys
from pathlib import Path

def download_portable_java():
    """下载便携式OpenJDK"""
    print("[INFO] 开始下载便携式OpenJDK 11...")
    
    # 使用Microsoft的OpenJDK build（较小且稳定）
    java_url = "https://aka.ms/download-jdk/microsoft-jdk-11.0.22-windows-x64.zip"
    
    project_root = Path(__file__).parent
    deploy_dir = project_root / ".deploy"
    deploy_dir.mkdir(exist_ok=True)
    
    java_zip = deploy_dir / "openjdk11.zip"
    java_dir = deploy_dir / "jdk-11.0.22"
    
    try:
        print(f"[INFO] 下载到: {java_zip}")
        urllib.request.urlretrieve(java_url, java_zip)
        print("[SUCCESS] Java下载完成")
        
        # 解压
        print("[INFO] 解压Java...")
        with zipfile.ZipFile(java_zip, 'r') as zip_ref:
            zip_ref.extractall(deploy_dir)
        
        # 查找实际的JDK目录
        for item in deploy_dir.iterdir():
            if item.is_dir() and 'jdk' in item.name.lower():
                java_dir = item
                break
        
        print(f"[SUCCESS] Java安装完成: {java_dir}")
        
        # 创建环境配置脚本
        env_script = project_root / "java_env.bat"
        with open(env_script, 'w') as f:
            f.write(f"@echo off\n")
            f.write(f"set JAVA_HOME={java_dir}\n")
            f.write(f"set PATH={java_dir}\\bin;%PATH%\n")
            f.write(f"echo Java环境已设置\n")
            f.write(f"java -version\n")
        
        print(f"[INFO] 环境脚本创建: {env_script}")
        print(f"[INFO] 运行 {env_script} 设置Java环境")
        
        return str(java_dir)
        
    except Exception as e:
        print(f"[ERROR] Java安装失败: {e}")
        return None

if __name__ == '__main__':
    java_path = download_portable_java()
    if java_path:
        print(f"\n成功安装Java到: {java_path}")
        print("请运行 java_env.bat 设置环境变量")
    else:
        print("\nJava安装失败，请手动安装")
        sys.exit(1)