#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署状态监控脚本
"""

import os
import sys
from pathlib import Path
import subprocess

def check_deployment_status():
    """检查部署状态"""
    print("=== 部署状态检查 ===\n")
    
    project_root = Path(__file__).parent
    deploy_dir = project_root / ".deploy"
    mobile_dir = project_root / "mobile"
    
    status = {}
    
    # 1. Java环境检查
    print("[1] Java JDK环境:")
    java_dir = deploy_dir / "jdk-11.0.22+7"
    if java_dir.exists():
        print(f"   ✓ Java已安装: {java_dir}")
        os.environ['JAVA_HOME'] = str(java_dir)
        os.environ['PATH'] = f"{java_dir}/bin;{os.environ.get('PATH', '')}"
        
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                version = result.stderr.split('\n')[0]
                print(f"   ✓ Java版本: {version}")
                status['java'] = True
            else:
                print("   ✗ Java版本检查失败")
                status['java'] = False
        except:
            print("   ✗ Java命令执行失败")
            status['java'] = False
    else:
        print("   ✗ Java未安装")
        status['java'] = False
    
    # 2. Android SDK检查
    print("\n[2] Android SDK环境:")
    android_dir = deploy_dir / "android-sdk"
    if android_dir.exists():
        print(f"   ✓ Android SDK已安装: {android_dir}")
        
        # 检查关键工具
        sdkmanager = android_dir / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat"
        if sdkmanager.exists():
            print(f"   ✓ SDKManager已安装")
            status['android_sdk'] = True
        else:
            print(f"   ✗ SDKManager未找到")
            status['android_sdk'] = False
    else:
        print("   ✗ Android SDK未安装")
        status['android_sdk'] = False
    
    # 3. Python依赖检查
    print("\n[3] Python构建依赖:")
    required_modules = [
        'buildozer', 'pyyaml', 'requests', 'aiohttp', 
        'loguru', 'jieba', 'cython'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✓ {module}")
        except ImportError:
            print(f"   ✗ {module}")
            missing_modules.append(module)
    
    status['python_deps'] = len(missing_modules) == 0
    
    # 4. 项目文件检查
    print("\n[4] 项目文件:")
    required_files = [
        mobile_dir / "buildozer.spec",
        mobile_dir / "main.py",
        project_root / "src" / "main.py"
    ]
    
    for file_path in required_files:
        if file_path.exists():
            print(f"   ✓ {file_path.name}")
        else:
            print(f"   ✗ {file_path.name}")
    
    status['project_files'] = all(f.exists() for f in required_files)
    
    # 5. 构建状态检查
    print("\n[5] 构建状态:")
    buildozer_dir = mobile_dir / ".buildozer"
    bin_dir = mobile_dir / "bin"
    
    if buildozer_dir.exists():
        print(f"   ✓ Buildozer工作目录存在")
        status['build_started'] = True
    else:
        print(f"   - Buildozer工作目录不存在（构建未开始）")
        status['build_started'] = False
    
    if bin_dir.exists():
        apk_files = list(bin_dir.glob("*.apk"))
        if apk_files:
            print(f"   ✓ 找到{len(apk_files)}个APK文件:")
            for apk in apk_files:
                size_mb = apk.stat().st_size / (1024 * 1024)
                print(f"      - {apk.name} ({size_mb:.1f} MB)")
            status['build_completed'] = True
        else:
            print(f"   - bin目录存在但无APK文件")
            status['build_completed'] = False
    else:
        print(f"   - bin目录不存在")
        status['build_completed'] = False
    
    # 6. 总体评估
    print("\n=== 总体状态 ===")
    completed_items = sum(status.values())
    total_items = len(status)
    
    print(f"完成进度: {completed_items}/{total_items}")
    
    for key, value in status.items():
        symbol = "✓" if value else "✗"
        print(f"  {symbol} {key}")
    
    if status.get('build_completed', False):
        print("\n🎉 APK构建已完成！")
        print("APK文件位置: mobile/bin/")
        print("可以传输到Android设备进行安装测试")
    elif status.get('build_started', False):
        print("\n⏳ APK构建正在进行中...")
        print("请耐心等待构建完成")
    elif all([status.get('java'), status.get('android_sdk'), status.get('python_deps')]):
        print("\n✅ 环境准备完成，可以开始构建APK")
    else:
        print("\n❌ 环境准备未完成，需要解决问题后再构建")
    
    return status

def main():
    """主函数"""
    status = check_deployment_status()
    return all(status.values())

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)