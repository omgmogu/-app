#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK构建脚本 - 绕过root检查
"""

import os
import sys
import subprocess
from pathlib import Path
import tempfile
import shutil

def setup_build_environment():
    """设置构建环境"""
    print("[INFO] 设置构建环境...")
    
    project_root = Path(__file__).parent
    deploy_dir = project_root / ".deploy"
    
    # Java环境
    java_dir = deploy_dir / "jdk-11.0.22+7"
    if java_dir.exists():
        os.environ['JAVA_HOME'] = str(java_dir)
        java_bin = str(java_dir / "bin")
        print(f"[OK] JAVA_HOME = {java_dir}")
    else:
        print("[ERROR] Java未找到")
        return False
    
    # Android SDK环境  
    android_dir = deploy_dir / "android-sdk"
    if android_dir.exists():
        os.environ['ANDROID_HOME'] = str(android_dir)
        os.environ['ANDROID_SDK_ROOT'] = str(android_dir)
        android_tools = str(android_dir / "cmdline-tools" / "latest" / "bin")
        android_platform = str(android_dir / "platform-tools")
        print(f"[OK] ANDROID_HOME = {android_dir}")
    else:
        print("[ERROR] Android SDK未找到")
        return False
    
    # 更新PATH
    current_path = os.environ.get('PATH', '')
    new_path = f"{java_bin};{android_tools};{android_platform};{current_path}"
    os.environ['PATH'] = new_path
    
    print("[OK] 环境变量设置完成")
    return True

def bypass_buildozer_root_check():
    """绕过buildozer的root检查"""
    print("[INFO] 配置buildozer跳过root检查...")
    
    mobile_dir = Path(__file__).parent / "mobile"
    buildozer_spec = mobile_dir / "buildozer.spec"
    
    if not buildozer_spec.exists():
        print("[ERROR] buildozer.spec不存在")
        return False
    
    # 读取buildozer.spec
    with open(buildozer_spec, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加或修改warn_on_root设置
    if 'warn_on_root' in content:
        content = content.replace('warn_on_root = 1', 'warn_on_root = 0')
    else:
        content += '\n# Disable root warning\nwarn_on_root = 0\n'
    
    # 写回文件
    with open(buildozer_spec, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] buildozer root检查已禁用")
    return True

def install_kivy_deps():
    """安装Kivy相关依赖"""
    print("[INFO] 安装Kivy相关依赖...")
    
    # 基础依赖
    basic_deps = [
        'cython',
        'wheel', 
        'setuptools'
    ]
    
    for dep in basic_deps:
        print(f"[INFO] 安装 {dep}...")
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', dep],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode == 0:
                print(f"[OK] {dep} 安装成功")
            else:
                print(f"[WARNING] {dep} 安装失败: {result.stderr}")
        except Exception as e:
            print(f"[ERROR] 安装{dep}异常: {e}")
    
    return True

def create_minimal_main():
    """创建最小化的main.py用于测试构建"""
    print("[INFO] 创建最小化测试应用...")
    
    mobile_dir = Path(__file__).parent / "mobile"
    main_file = mobile_dir / "main.py"
    
    # 备份原main.py
    if main_file.exists():
        shutil.copy(main_file, mobile_dir / "main_backup.py")
        print("[INFO] 原main.py已备份")
    
    # 创建最小化main.py
    minimal_app = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小化Kivy测试应用
"""

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        title_label = Label(
            text='闲鱼自动评论助手',
            font_size='20sp',
            size_hint_y=None,
            height='50dp'
        )
        
        info_label = Label(
            text='Android APK构建测试成功!\\n\\n这是一个最小化的测试版本。\\n完整功能请使用桌面版本。',
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        layout.add_widget(title_label)
        layout.add_widget(info_label)
        
        return layout

if __name__ == '__main__':
    TestApp().run()
'''
    
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(minimal_app)
    
    print("[OK] 最小化应用创建完成")
    return True

def build_apk():
    """构建APK"""
    print("[INFO] 开始APK构建...")
    
    mobile_dir = Path(__file__).parent / "mobile"
    os.chdir(mobile_dir)
    
    try:
        # 首先清理之前的构建
        buildozer_dir = mobile_dir / ".buildozer"
        if buildozer_dir.exists():
            print("[INFO] 清理之前的构建...")
            shutil.rmtree(buildozer_dir)
        
        # 开始构建
        print("[INFO] 执行buildozer android debug...")
        print("[INFO] 这可能需要30-60分钟，请耐心等待...")
        
        # 创建一个自动回答'y'的输入流
        process = subprocess.Popen(
            ['buildozer', 'android', 'debug'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # 发送'y'回答root警告
        try:
            stdout, _ = process.communicate(input='y\\n', timeout=7200)  # 2小时超时
            
            print("[BUILD OUTPUT]")
            print(stdout)
            
            if process.returncode == 0:
                print("[SUCCESS] APK构建成功!")
                
                # 查找APK文件
                bin_dir = mobile_dir / "bin"
                if bin_dir.exists():
                    apk_files = list(bin_dir.glob("*.apk"))
                    for apk in apk_files:
                        size_mb = apk.stat().st_size / (1024 * 1024)
                        print(f"[SUCCESS] 生成APK: {apk.name} ({size_mb:.1f} MB)")
                        print(f"[SUCCESS] APK路径: {apk.absolute()}")
                
                return True
            else:
                print(f"[ERROR] 构建失败，返回码: {process.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            print("[ERROR] 构建超时")
            process.kill()
            return False
            
    except Exception as e:
        print(f"[ERROR] 构建异常: {e}")
        return False

def restore_original_main():
    """恢复原始main.py"""
    mobile_dir = Path(__file__).parent / "mobile"
    main_file = mobile_dir / "main.py"
    backup_file = mobile_dir / "main_backup.py"
    
    if backup_file.exists():
        shutil.copy(backup_file, main_file)
        backup_file.unlink()
        print("[INFO] 原始main.py已恢复")

def main():
    """主函数"""
    print("=== Android APK构建 ===")
    
    try:
        # 1. 设置环境
        if not setup_build_environment():
            print("环境设置失败")
            return False
        
        # 2. 绕过root检查
        if not bypass_buildozer_root_check():
            print("buildozer配置失败")  
            return False
        
        # 3. 安装依赖
        install_kivy_deps()
        
        # 4. 创建最小化应用
        create_minimal_main()
        
        # 5. 构建APK
        success = build_apk()
        
        # 6. 恢复原文件
        restore_original_main()
        
        if success:
            print("\\n🎉 APK构建成功完成!")
            print("APK文件已生成在 mobile/bin/ 目录中")
            print("可以传输到Android设备进行安装测试")
        else:
            print("\\nAPK构建失败")
            
        return success
        
    except KeyboardInterrupt:
        print("\\n构建被用户中断")
        restore_original_main()
        return False
    except Exception as e:
        print(f"\\n构建过程异常: {e}")
        restore_original_main()
        return False

if __name__ == '__main__':
    sys.exit(0 if main() else 1)