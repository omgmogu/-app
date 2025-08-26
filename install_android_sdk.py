#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android SDK安装脚本
"""

import urllib.request
import zipfile
import os
import sys
import subprocess
from pathlib import Path

def download_android_sdk():
    """下载Android SDK命令行工具"""
    print("[INFO] 开始下载Android SDK命令行工具...")
    
    # Android命令行工具URL
    sdk_url = "https://dl.google.com/android/repository/commandlinetools-win-9477386_latest.zip"
    
    project_root = Path(__file__).parent
    deploy_dir = project_root / ".deploy"
    deploy_dir.mkdir(exist_ok=True)
    
    sdk_zip = deploy_dir / "android-sdk-tools.zip"
    sdk_dir = deploy_dir / "android-sdk"
    
    try:
        print(f"[INFO] 下载到: {sdk_zip}")
        urllib.request.urlretrieve(sdk_url, sdk_zip)
        print("[SUCCESS] Android SDK工具下载完成")
        
        # 解压
        print("[INFO] 解压Android SDK工具...")
        sdk_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(sdk_zip, 'r') as zip_ref:
            zip_ref.extractall(sdk_dir)
        
        # 移动cmdline-tools到正确位置
        cmdline_dir = sdk_dir / "cmdline-tools"
        latest_dir = cmdline_dir / "latest"
        
        # 检查目录结构
        if not latest_dir.exists():
            # 可能需要重新组织目录结构
            temp_dir = sdk_dir / "temp_cmdline_tools"
            cmdline_dir.rename(temp_dir)
            cmdline_dir.mkdir(exist_ok=True)
            temp_dir.rename(latest_dir)
        
        print(f"[SUCCESS] Android SDK工具安装完成: {sdk_dir}")
        
        # 创建环境配置脚本
        env_script = project_root / "android_env.bat"
        with open(env_script, 'w') as f:
            f.write(f"@echo off\n")
            f.write(f"set ANDROID_HOME={sdk_dir}\n")
            f.write(f"set ANDROID_SDK_ROOT={sdk_dir}\n")
            f.write(f"set PATH={sdk_dir}\\cmdline-tools\\latest\\bin;{sdk_dir}\\platform-tools;%PATH%\n")
            f.write(f"echo Android SDK环境已设置\n")
            f.write(f"echo ANDROID_HOME=%ANDROID_HOME%\n")
        
        print(f"[INFO] 环境脚本创建: {env_script}")
        
        return str(sdk_dir)
        
    except Exception as e:
        print(f"[ERROR] Android SDK安装失败: {e}")
        return None

def install_android_components(sdk_dir):
    """安装必要的Android组件"""
    print("[INFO] 安装Android组件...")
    
    sdkmanager = Path(sdk_dir) / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat"
    
    if not sdkmanager.exists():
        print(f"[ERROR] 找不到sdkmanager: {sdkmanager}")
        return False
    
    # 组件列表
    components = [
        "platform-tools",
        "build-tools;33.0.2",
        "platforms;android-33",
        "platforms;android-23"
    ]
    
    try:
        # 接受许可证
        print("[INFO] 接受Android SDK许可证...")
        subprocess.run(
            f'echo y | "{sdkmanager}" --licenses',
            shell=True,
            check=False,
            timeout=300
        )
        
        # 安装组件
        for component in components:
            print(f"[INFO] 安装组件: {component}")
            result = subprocess.run(
                f'"{sdkmanager}" "{component}"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                print(f"[SUCCESS] {component} 安装成功")
            else:
                print(f"[WARNING] {component} 安装可能有问题: {result.stderr}")
        
        return True
        
    except subprocess.TimeoutExpired:
        print("[ERROR] 组件安装超时")
        return False
    except Exception as e:
        print(f"[ERROR] 组件安装失败: {e}")
        return False

if __name__ == '__main__':
    sdk_path = download_android_sdk()
    if sdk_path:
        print(f"\n成功下载Android SDK到: {sdk_path}")
        
        # 安装组件
        if install_android_components(sdk_path):
            print("Android SDK组件安装完成")
            print("请运行 android_env.bat 设置环境变量")
        else:
            print("Android SDK组件安装失败")
            sys.exit(1)
    else:
        print("\nAndroid SDK安装失败")
        sys.exit(1)