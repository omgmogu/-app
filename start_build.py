#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK构建启动脚本
设置环境变量并开始构建
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """设置构建环境变量"""
    print("[INFO] 设置构建环境...")
    
    project_root = Path(__file__).parent
    deploy_dir = project_root / ".deploy"
    
    # Java环境
    java_dir = deploy_dir / "jdk-11.0.22+7"
    if java_dir.exists():
        os.environ['JAVA_HOME'] = str(java_dir)
        os.environ['PATH'] = f"{java_dir}/bin;{os.environ.get('PATH', '')}"
        print(f"[OK] JAVA_HOME = {java_dir}")
    else:
        print("[WARNING] Java目录未找到")
    
    # Android SDK环境
    android_dir = deploy_dir / "android-sdk"
    if android_dir.exists():
        os.environ['ANDROID_HOME'] = str(android_dir)
        os.environ['ANDROID_SDK_ROOT'] = str(android_dir)
        android_path = f"{android_dir}/cmdline-tools/latest/bin;{android_dir}/platform-tools"
        os.environ['PATH'] = f"{android_path};{os.environ.get('PATH', '')}"
        print(f"[OK] ANDROID_HOME = {android_dir}")
    else:
        print("[WARNING] Android SDK目录未找到")
    
    # 验证环境
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] Java环境验证通过")
        else:
            print("[WARNING] Java环境验证失败")
    except Exception as e:
        print(f"[WARNING] Java环境验证异常: {e}")
    
    print("[INFO] 环境设置完成")

def build_apk():
    """构建APK"""
    print("[INFO] 开始APK构建...")
    
    mobile_dir = Path(__file__).parent / "mobile"
    if not mobile_dir.exists():
        print("[ERROR] mobile目录不存在")
        return False
    
    # 切换到mobile目录
    os.chdir(mobile_dir)
    print(f"[INFO] 切换到目录: {mobile_dir}")
    
    # buildozer初始化
    print("[INFO] 运行buildozer初始化...")
    try:
        result = subprocess.run(['buildozer', 'init'], 
                              capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("[OK] buildozer初始化成功")
        else:
            print(f"[WARNING] buildozer初始化可能失败: {result.stderr}")
    except Exception as e:
        print(f"[WARNING] buildozer初始化异常: {e}")
    
    # 构建debug APK
    print("[INFO] 开始构建APK（这可能需要很长时间）...")
    print("[INFO] 请耐心等待，buildozer会自动下载NDK、SDK组件等...")
    
    try:
        # 使用实时输出显示构建过程
        process = subprocess.Popen(
            ['buildozer', 'android', 'debug'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # 实时显示输出
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(f"[BUILD] {output.strip()}")
        
        exit_code = process.poll()
        
        if exit_code == 0:
            print("[SUCCESS] APK构建成功！")
            
            # 查找生成的APK
            bin_dir = mobile_dir / "bin"
            if bin_dir.exists():
                apk_files = list(bin_dir.glob("*.apk"))
                for apk in apk_files:
                    size_mb = apk.stat().st_size / (1024 * 1024)
                    print(f"[SUCCESS] 生成APK: {apk.name} ({size_mb:.1f} MB)")
            
            return True
        else:
            print(f"[ERROR] APK构建失败，退出码: {exit_code}")
            return False
            
    except KeyboardInterrupt:
        print("[INFO] 构建被用户中断")
        return False
    except Exception as e:
        print(f"[ERROR] 构建过程异常: {e}")
        return False

def main():
    """主函数"""
    print("=== 开始APK构建 ===")
    
    # 设置环境
    setup_environment()
    
    # 构建APK
    success = build_apk()
    
    if success:
        print("\n🎉 APK构建成功完成！")
        print("请在mobile/bin目录查看生成的APK文件")
    else:
        print("\n❌ APK构建失败")
        print("请检查错误信息并重试")
    
    return success

if __name__ == '__main__':
    sys.exit(0 if main() else 1)