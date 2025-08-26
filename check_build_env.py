#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速检查构建环境并尝试构建APK
"""

import os
import sys
import subprocess
from pathlib import Path

def check_and_build():
    """检查环境并尝试构建"""
    print("=== APK构建环境检查 ===\n")
    
    # 检查Java
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] Java已安装")
            java_version = result.stderr.split('\n')[0]
            print(f"     版本: {java_version}")
        else:
            print("[ERROR] Java未正确配置")
            return False
    except FileNotFoundError:
        print("[ERROR] Java未安装")
        return False
    except Exception as e:
        print(f"[ERROR] Java检查失败: {e}")
        return False
    
    # 检查buildozer
    try:
        result = subprocess.run(['buildozer', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("[OK] buildozer已安装")
            print(f"     版本: {result.stdout.strip()}")
        else:
            print("[ERROR] buildozer未正确安装")
            return False
    except FileNotFoundError:
        print("[ERROR] buildozer未安装")
        print("     请运行: pip install buildozer")
        return False
    except Exception as e:
        print(f"[ERROR] buildozer检查失败: {e}")
        return False
    
    # 检查mobile目录
    mobile_dir = Path(__file__).parent / "mobile"
    if not mobile_dir.exists():
        print("[ERROR] mobile目录不存在")
        return False
    
    buildozer_spec = mobile_dir / "buildozer.spec"
    if not buildozer_spec.exists():
        print("[ERROR] buildozer.spec不存在")
        return False
    
    print("[OK] 项目文件检查通过")
    print(f"     mobile目录: {mobile_dir}")
    print(f"     buildozer.spec: {buildozer_spec}")
    
    # 尝试构建
    print("\n=== 开始APK构建 ===")
    print("切换到mobile目录...")
    os.chdir(mobile_dir)
    
    print("执行: buildozer android debug")
    print("(这可能需要较长时间，首次构建会下载Android NDK等工具)\n")
    
    try:
        # 执行构建
        result = subprocess.run(
            ['buildozer', 'android', 'debug'], 
            timeout=3600,  # 1小时超时
            check=False
        )
        
        if result.returncode == 0:
            print("\n[SUCCESS] APK构建成功!")
            
            # 查找生成的APK
            bin_dir = mobile_dir / "bin"
            if bin_dir.exists():
                apk_files = list(bin_dir.glob("*.apk"))
                if apk_files:
                    print(f"\n生成的APK文件:")
                    for apk in apk_files:
                        size_mb = apk.stat().st_size / (1024 * 1024)
                        print(f"  {apk.name} ({size_mb:.1f} MB)")
                        print(f"  位置: {apk.absolute()}")
                else:
                    print("\n[WARNING] bin目录存在但未找到APK文件")
            else:
                print("\n[WARNING] bin目录不存在")
                
            return True
        else:
            print(f"\n[ERROR] APK构建失败，返回码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n[ERROR] 构建超时（超过1小时）")
        return False
    except Exception as e:
        print(f"\n[ERROR] 构建异常: {e}")
        return False

def main():
    """主函数"""
    success = check_and_build()
    
    if success:
        print("\n🎉 APK构建完成!")
        print("APK文件位置: mobile/bin/")
    else:
        print("\n❌ APK构建失败")
        print("\n可能的解决方案:")
        print("1. 检查Java JDK是否正确安装")
        print("2. 检查Android SDK环境变量")
        print("3. 运行: pip install buildozer")
        print("4. 手动执行: cd mobile && buildozer android debug")
    
    return success

if __name__ == '__main__':
    sys.exit(0 if main() else 1)