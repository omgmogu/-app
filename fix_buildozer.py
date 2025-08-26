#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复buildozer Android支持问题
"""

import subprocess
import sys
import os
from pathlib import Path

def fix_buildozer():
    """修复buildozer Android支持"""
    print("=== 修复buildozer Android支持 ===\n")
    
    print("[INFO] 当前buildozer不支持Android目标")
    print("[INFO] 需要重新安装支持Android的buildozer版本\n")
    
    # 1. 卸载当前buildozer
    print("[STEP 1] 卸载当前buildozer...")
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'buildozer', '-y'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("[OK] 已卸载当前buildozer")
        else:
            print(f"[WARNING] 卸载可能有问题: {result.stderr}")
    except Exception as e:
        print(f"[ERROR] 卸载失败: {e}")
        return False
    
    # 2. 安装正确版本的buildozer
    print("\n[STEP 2] 安装支持Android的buildozer...")
    try:
        # 安装最新版本的buildozer
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', 'buildozer==1.5.0'], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            print("[OK] buildozer安装成功")
        else:
            print(f"[ERROR] buildozer安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 安装异常: {e}")
        return False
    
    # 3. 验证安装
    print("\n[STEP 3] 验证buildozer Android支持...")
    try:
        result = subprocess.run(['buildozer', '--help'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            output = result.stdout
            if 'android' in output.lower():
                print("[SUCCESS] buildozer现在支持Android目标!")
                return True
            else:
                print("[ERROR] buildozer仍不支持Android")
                return False
        else:
            print(f"[ERROR] buildozer验证失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 验证异常: {e}")
        return False

def install_android_requirements():
    """安装Android构建所需的额外依赖"""
    print("\n=== 安装Android构建依赖 ===")
    
    # Android构建需要的额外依赖
    android_deps = [
        'python-for-android',  # buildozer的Android后端
        'cython<3.0',          # 兼容版本的cython
        'colorama',            # 终端颜色支持
    ]
    
    for dep in android_deps:
        print(f"[INFO] 安装 {dep}...")
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', dep], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"[OK] {dep} 安装成功")
            else:
                print(f"[WARNING] {dep} 安装可能有问题: {result.stderr}")
        except Exception as e:
            print(f"[ERROR] 安装{dep}异常: {e}")

def test_build():
    """测试构建"""
    print("\n=== 测试buildozer android命令 ===")
    
    mobile_dir = Path(__file__).parent / "mobile"
    if not mobile_dir.exists():
        print("[ERROR] mobile目录不存在")
        return False
    
    os.chdir(mobile_dir)
    
    try:
        # 测试android命令是否可用
        result = subprocess.run(['buildozer', 'android'], 
                              capture_output=True, text=True, timeout=30)
        
        # 如果返回帮助信息而不是"Unknown command"，说明成功
        if 'Unknown command' not in result.stderr and 'android' in result.stdout:
            print("[SUCCESS] buildozer android 命令现在可用!")
            return True
        else:
            print("[ERROR] buildozer android 命令仍然无法使用")
            print(f"输出: {result.stdout}")
            print(f"错误: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        return False

def main():
    """主函数"""
    print("buildozer Android支持修复工具\n")
    
    # 1. 修复buildozer
    if not fix_buildozer():
        print("\n❌ buildozer修复失败")
        return False
    
    # 2. 安装Android依赖
    install_android_requirements()
    
    # 3. 测试构建命令
    if test_build():
        print("\n🎉 buildozer Android支持修复成功!")
        print("\n现在可以尝试构建APK:")
        print("  cd mobile")
        print("  buildozer android debug")
        return True
    else:
        print("\n❌ 修复未完全成功，可能需要手动处理")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)