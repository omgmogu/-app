#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
备用APK构建方案
使用python-for-android直接构建
"""

import os
import sys
import subprocess
from pathlib import Path

def build_with_p4a():
    """使用python-for-android直接构建"""
    print("=== 使用python-for-android构建APK ===\n")
    
    print("[INFO] buildozer不可用，尝试使用python-for-android直接构建")
    
    # 1. 安装python-for-android
    print("[STEP 1] 安装python-for-android...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'python-for-android', 'colorama', 'appdirs', 'sh', 'jinja2'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("[OK] python-for-android安装成功")
        else:
            print(f"[ERROR] 安装失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] 安装异常: {e}")
        return False
    
    # 2. 设置环境变量
    print("\n[STEP 2] 配置环境变量...")
    project_root = Path(__file__).parent
    
    # Java环境
    java_dir = project_root / ".deploy" / "jdk-11.0.22+7"
    if java_dir.exists():
        os.environ['JAVA_HOME'] = str(java_dir)
        os.environ['PATH'] = f"{java_dir}/bin;{os.environ.get('PATH', '')}"
        print(f"[OK] JAVA_HOME = {java_dir}")
    else:
        print("[ERROR] Java环境未找到")
        return False
    
    # Android SDK环境
    android_dir = project_root / ".deploy" / "android-sdk"
    if android_dir.exists():
        os.environ['ANDROID_HOME'] = str(android_dir)
        os.environ['ANDROID_SDK_ROOT'] = str(android_dir)
        print(f"[OK] ANDROID_HOME = {android_dir}")
    else:
        print("[ERROR] Android SDK环境未找到")
        return False
    
    # 3. 准备构建目录
    print("\n[STEP 3] 准备构建...")
    mobile_dir = project_root / "mobile"
    build_dir = mobile_dir / "p4a_build"
    build_dir.mkdir(exist_ok=True)
    
    os.chdir(build_dir)
    
    # 4. 执行p4a构建
    print("\n[STEP 4] 使用p4a构建APK...")
    print("[INFO] 这可能需要很长时间（首次会下载NDK等工具）...")
    
    try:
        # p4a构建命令
        cmd = [
            'p4a', 'apk',
            '--name', '闲鱼自动评论助手',
            '--package', 'com.xianyuassistant.xianyucommentassistant',  
            '--version', '1.0',
            '--bootstrap', 'sdl2',
            '--requirements', 'python3,kivy,kivymd,requests,pyyaml',
            '--permission', 'INTERNET',
            '--permission', 'WRITE_EXTERNAL_STORAGE',
            '--orientation', 'portrait',
            '--arch', 'armeabi-v7a',
            '--private', str(mobile_dir),
            '--debug'
        ]
        
        print(f"[INFO] 执行命令: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, timeout=3600, check=False)  # 1小时超时
        
        if result.returncode == 0:
            print("[SUCCESS] p4a构建成功!")
            
            # 查找APK文件
            apk_files = list(build_dir.rglob("*.apk"))
            if apk_files:
                print(f"\n生成的APK文件:")
                for apk in apk_files:
                    size_mb = apk.stat().st_size / (1024 * 1024)
                    print(f"  {apk.name} ({size_mb:.1f} MB)")
                    print(f"  位置: {apk.absolute()}")
                    
                    # 复制到mobile/bin目录
                    bin_dir = mobile_dir / "bin"
                    bin_dir.mkdir(exist_ok=True)
                    target = bin_dir / apk.name
                    import shutil
                    shutil.copy2(apk, target)
                    print(f"  已复制到: {target}")
                
                return True
            else:
                print("[WARNING] 构建完成但未找到APK文件")
                return False
        else:
            print(f"[ERROR] p4a构建失败，返回码: {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("[ERROR] 构建超时")
        return False
    except FileNotFoundError:
        print("[ERROR] p4a命令未找到，python-for-android可能未正确安装")
        return False
    except Exception as e:
        print(f"[ERROR] 构建异常: {e}")
        return False

def create_simple_apk_guide():
    """创建简单的APK构建指南"""
    print("\n=== 创建手动构建指南 ===")
    
    guide = """# 手动APK构建指南

## 方法1: 使用Colab在线构建
1. 打开Google Colab
2. 创建新notebook
3. 运行以下代码:

```python
!pip install buildozer cython
!apt update
!apt install -y git zip unzip openjdk-8-jdk wget
!wget https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip
!unzip commandlinetools-linux-8512546_latest.zip
!mkdir -p /root/.android/sdk
!mv cmdline-tools /root/.android/sdk/
!mkdir -p /root/.android/sdk/cmdline-tools/latest
!mv /root/.android/sdk/cmdline-tools/* /root/.android/sdk/cmdline-tools/latest/

# 上传你的mobile目录到Colab
# 然后运行:
%cd mobile
!buildozer android debug
```

## 方法2: 使用Docker构建
```bash
docker run -it --rm -v $(pwd):/app kivy/buildozer android debug
```

## 方法3: 使用GitHub Actions自动构建
创建.github/workflows/build.yml文件，自动构建APK

## APK文件位置
成功构建后，APK将在以下位置:
- mobile/bin/*.apk
"""
    
    guide_file = Path(__file__).parent / "APK_BUILD_GUIDE.md"
    with open(guide_file, 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print(f"[INFO] 构建指南已保存: {guide_file}")

def main():
    """主函数"""
    print("备用APK构建工具\n")
    
    # 尝试p4a构建
    success = build_with_p4a()
    
    if success:
        print("\n🎉 APK构建成功!")
        print("APK位置: mobile/bin/")
    else:
        print("\n❌ 自动构建失败")
        create_simple_apk_guide()
        print("\n建议使用以下替代方案:")
        print("1. 查看生成的 APK_BUILD_GUIDE.md")
        print("2. 使用Google Colab在线构建")
        print("3. 使用Docker容器构建")
        print("4. 联系开发者获取预编译APK")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)