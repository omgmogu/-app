#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK构建验证脚本
检查构建环境和依赖
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

def check_python_environment():
    """检查Python环境"""
    print("[CHECK] 检查Python环境...")
    
    print(f"  - Python版本: {sys.version}")
    print(f"  - 操作系统: {platform.system()} {platform.release()}")
    
    if sys.version_info < (3, 8):
        print("[WARNING] Python版本较低，建议使用3.8+")
        return False
    
    print("[OK] Python环境检查通过")
    return True

def check_java_environment():
    """检查Java环境"""
    print("[CHECK] 检查Java环境...")
    
    try:
        result = subprocess.run(['java', '-version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            java_version = result.stderr.strip().split('\n')[0]
            print(f"  - Java版本: {java_version}")
            print("[OK] Java环境检查通过")
            return True
        else:
            print("[ERROR] Java未正确安装或配置")
            return False
            
    except FileNotFoundError:
        print("[ERROR] Java未找到，请安装JDK 8+")
        return False
    except Exception as e:
        print(f"[ERROR] Java环境检查失败: {e}")
        return False

def check_android_sdk():
    """检查Android SDK"""
    print("[CHECK] 检查Android SDK...")
    
    # 检查常见的Android SDK路径
    possible_paths = []
    
    if platform.system() == 'Windows':
        possible_paths = [
            os.path.expanduser('~/AppData/Local/Android/Sdk'),
            'C:/Android/Sdk',
            'C:/Users/Administrator/AppData/Local/Android/Sdk'
        ]
    else:
        possible_paths = [
            os.path.expanduser('~/Android/Sdk'),
            '/opt/android-sdk',
            '/usr/local/android-sdk'
        ]
    
    # 检查环境变量
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    if android_home:
        possible_paths.insert(0, android_home)
    
    sdk_path = None
    for path in possible_paths:
        if os.path.exists(path):
            sdk_path = path
            break
    
    if sdk_path:
        print(f"  - Android SDK路径: {sdk_path}")
        
        # 检查关键工具
        tools_check = {}
        if platform.system() == 'Windows':
            tools_check['adb'] = os.path.exists(os.path.join(sdk_path, 'platform-tools', 'adb.exe'))
            tools_check['aapt'] = any(os.path.exists(os.path.join(sdk_path, 'build-tools', v, 'aapt.exe')) 
                                    for v in os.listdir(os.path.join(sdk_path, 'build-tools')) 
                                    if os.path.exists(os.path.join(sdk_path, 'build-tools', v)))
        else:
            tools_check['adb'] = os.path.exists(os.path.join(sdk_path, 'platform-tools', 'adb'))
            tools_check['aapt'] = any(os.path.exists(os.path.join(sdk_path, 'build-tools', v, 'aapt')) 
                                    for v in os.listdir(os.path.join(sdk_path, 'build-tools')) 
                                    if os.path.exists(os.path.join(sdk_path, 'build-tools', v)))
        
        print("  - SDK工具检查:")
        for tool, available in tools_check.items():
            status = "[OK]" if available else "[MISSING]"
            print(f"    * {tool}: {status}")
        
        if all(tools_check.values()):
            print("[OK] Android SDK检查通过")
            return True
        else:
            print("[WARNING] 部分Android SDK工具缺失")
            return False
    else:
        print("[ERROR] 未找到Android SDK")
        print("请安装Android SDK并设置ANDROID_HOME环境变量")
        return False

def check_buildozer():
    """检查buildozer"""
    print("[CHECK] 检查buildozer...")
    
    try:
        result = subprocess.run(['buildozer', 'version'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  - Buildozer版本: {version}")
            print("[OK] Buildozer检查通过")
            return True
        else:
            print("[ERROR] Buildozer命令执行失败")
            return False
            
    except FileNotFoundError:
        print("[WARNING] Buildozer未安装")
        print("  安装命令: pip install buildozer")
        return False
    except Exception as e:
        print(f"[ERROR] Buildozer检查失败: {e}")
        return False

def check_python_dependencies():
    """检查Python依赖"""
    print("[CHECK] 检查Python依赖...")
    
    # buildozer.spec中定义的依赖
    required_deps = [
        'kivy',
        'kivymd', 
        'requests',
        'pyyaml',
        'aiohttp',
        'plyer',
        'loguru',
        'jieba',
        'python-dateutil',
        'urllib3',
        'cython'
    ]
    
    missing_deps = []
    for dep in required_deps:
        try:
            __import__(dep.replace('-', '_'))
            print(f"  - {dep}: [OK]")
        except ImportError:
            print(f"  - {dep}: [MISSING]")
            missing_deps.append(dep)
    
    if missing_deps:
        print(f"[WARNING] 缺少{len(missing_deps)}个依赖包:")
        for dep in missing_deps:
            print(f"  * {dep}")
        print("  安装命令: pip install " + " ".join(missing_deps))
        return False
    else:
        print("[OK] Python依赖检查通过")
        return True

def check_project_structure():
    """检查项目结构"""
    print("[CHECK] 检查项目结构...")
    
    project_root = Path(__file__).parent.parent
    mobile_dir = project_root / "mobile"
    
    required_files = {
        mobile_dir / "buildozer.spec": "Buildozer配置文件",
        mobile_dir / "main.py": "主应用文件",
        project_root / "src" / "main.py": "核心逻辑文件",
        project_root / "config" / "settings.yaml": "配置文件"
    }
    
    missing_files = []
    for file_path, desc in required_files.items():
        if file_path.exists():
            print(f"  - {desc}: [OK]")
        else:
            print(f"  - {desc}: [MISSING]")
            missing_files.append(str(file_path))
    
    if missing_files:
        print(f"[ERROR] 缺少{len(missing_files)}个关键文件")
        return False
    else:
        print("[OK] 项目结构检查通过")
        return True

def simulate_build_preparation():
    """模拟构建准备过程"""
    print("[CHECK] 模拟构建准备...")
    
    mobile_dir = Path(__file__).parent.parent / "mobile"
    
    try:
        # 切换到mobile目录
        os.chdir(mobile_dir)
        
        # 检查buildozer初始化
        if not (mobile_dir / ".buildozer").exists():
            print("  - .buildozer目录不存在，需要首次初始化")
        else:
            print("  - .buildozer目录存在")
        
        # 检查build目录
        if not (mobile_dir / "bin").exists():
            print("  - bin目录不存在，将在构建时创建")
        else:
            print("  - bin目录存在")
        
        print("[OK] 构建准备检查完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 构建准备失败: {e}")
        return False

def generate_build_report():
    """生成构建报告"""
    print("\n=== 构建环境报告 ===")
    
    report = {
        'python': check_python_environment(),
        'java': check_java_environment(), 
        'android_sdk': check_android_sdk(),
        'buildozer': check_buildozer(),
        'dependencies': check_python_dependencies(),
        'project': check_project_structure(),
        'preparation': simulate_build_preparation()
    }
    
    print(f"\n检查结果汇总:")
    passed_count = sum(report.values())
    total_count = len(report)
    
    for check, result in report.items():
        status = "PASS" if result else "FAIL"
        print(f"  - {check}: {status}")
    
    print(f"\n总体评估: {passed_count}/{total_count} 项检查通过")
    
    if passed_count == total_count:
        print("\n[SUCCESS] 构建环境完整，可以进行APK打包")
        print("\n构建命令:")
        print("  cd mobile")
        print("  buildozer android debug")
        return True
    elif passed_count >= total_count - 2:
        print("\n[WARNING] 构建环境基本就绪，建议解决缺失项后再打包")
        return True
    else:
        print("\n[ERROR] 构建环境不完整，需要解决多个问题")
        print("\n建议步骤:")
        if not report['java']:
            print("  1. 安装Java JDK 8+")
        if not report['android_sdk']:
            print("  2. 安装Android SDK并设置环境变量")
        if not report['buildozer']:
            print("  3. 安装buildozer: pip install buildozer")
        if not report['dependencies']:
            print("  4. 安装缺失的Python依赖包")
        return False

def main():
    """主函数"""
    print("=== Android APK构建环境验证 ===\n")
    
    success = generate_build_report()
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)