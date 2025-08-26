#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android APK 构建和部署脚本
使用 Buildozer 自动化构建过程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import argparse

class AndroidBuilder:
    """Android构建器"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.src_dir = self.project_dir.parent / "src"
        self.config_dir = self.project_dir.parent / "config"
        
        # 构建配置
        self.build_modes = {
            'debug': 'android debug',
            'release': 'android release',
            'clean': 'android clean'
        }
    
    def check_dependencies(self):
        """检查构建依赖"""
        print("🔍 检查构建环境...")
        
        # 检查 Python 版本
        if sys.version_info < (3, 8):
            print("❌ 需要 Python 3.8+")
            return False
        print(f"✅ Python {sys.version}")
        
        # 检查 buildozer
        try:
            result = subprocess.run(['buildozer', 'version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Buildozer {result.stdout.strip()}")
            else:
                print("❌ Buildozer 未正确安装")
                return False
        except FileNotFoundError:
            print("❌ Buildozer 未安装")
            print("💡 安装命令: pip install buildozer")
            return False
        
        # 检查 Java
        try:
            result = subprocess.run(['java', '-version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Java JDK 已安装")
            else:
                print("❌ Java JDK 未安装")
                return False
        except FileNotFoundError:
            print("❌ Java JDK 未安装")
            return False
        
        # 检查必要文件
        required_files = [
            'buildozer.spec',
            'main.py',
            'requirements-mobile.txt'
        ]
        
        for file in required_files:
            if not (self.project_dir / file).exists():
                print(f"❌ 缺少必要文件: {file}")
                return False
        
        print("✅ 构建环境检查完成")
        return True
    
    def prepare_build(self):
        """准备构建环境"""
        print("📦 准备构建环境...")
        
        # 创建必要的目录
        dirs_to_create = [
            'assets',
            'data',
            'config',
            'templates'
        ]
        
        for dir_name in dirs_to_create:
            dir_path = self.project_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✅ 创建目录: {dir_name}")
        
        # 复制核心源码文件（移动端需要的部分）
        mobile_required_files = [
            'keyword_manager.py',
            'comment_generator.py',
            'ai_client.py',
            'database.py'
        ]
        
        print("📋 复制核心模块...")
        for file in mobile_required_files:
            src_file = self.src_dir / file
            dst_file = self.project_dir / file
            
            if src_file.exists():
                shutil.copy2(src_file, dst_file)
                print(f"✅ 复制: {file}")
            else:
                print(f"⚠️  未找到: {file}")
        
        # 复制配置文件
        if self.config_dir.exists():
            config_dst = self.project_dir / 'config'
            if config_dst.exists():
                shutil.rmtree(config_dst)
            shutil.copytree(self.config_dir, config_dst)
            print("✅ 复制配置文件")
        
        # 创建空的图标文件（如果不存在）
        icon_file = self.project_dir / 'assets' / 'icon.png'
        if not icon_file.exists():
            print("⚠️  创建默认图标占位符")
            # 这里可以创建一个简单的默认图标或下载一个
        
        print("✅ 构建环境准备完成")
    
    def build_apk(self, mode='debug', clean=False):
        """构建 APK"""
        print(f"🚀 开始构建 {mode} APK...")
        
        if clean:
            print("🧹 清理构建缓存...")
            self.clean_build()
        
        try:
            # 切换到项目目录
            os.chdir(self.project_dir)
            
            # 执行构建命令
            build_cmd = ['buildozer'] + self.build_modes[mode].split()
            print(f"📟 执行命令: {' '.join(build_cmd)}")
            
            # 实时显示构建输出
            process = subprocess.Popen(
                build_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            return_code = process.poll()
            
            if return_code == 0:
                print("✅ APK 构建成功!")
                
                # 查找生成的 APK 文件
                bin_dir = self.project_dir / 'bin'
                if bin_dir.exists():
                    apk_files = list(bin_dir.glob('*.apk'))
                    if apk_files:
                        print(f"📱 APK 文件: {apk_files[0]}")
                        print(f"📂 位置: {apk_files[0].absolute()}")
                        return str(apk_files[0])
                
                return True
            else:
                print("❌ APK 构建失败")
                return False
                
        except Exception as e:
            print(f"❌ 构建异常: {e}")
            return False
    
    def clean_build(self):
        """清理构建"""
        print("🧹 清理构建文件...")
        
        try:
            subprocess.run(['buildozer', 'android', 'clean'], 
                         cwd=self.project_dir, check=True)
            print("✅ 构建清理完成")
        except subprocess.CalledProcessError as e:
            print(f"⚠️  清理失败: {e}")
    
    def install_apk(self, apk_path=None):
        """安装 APK 到设备"""
        if not apk_path:
            # 查找最新的 APK
            bin_dir = self.project_dir / 'bin'
            if bin_dir.exists():
                apk_files = list(bin_dir.glob('*.apk'))
                if apk_files:
                    apk_path = max(apk_files, key=lambda f: f.stat().st_mtime)
                else:
                    print("❌ 未找到 APK 文件")
                    return False
            else:
                print("❌ 构建目录不存在")
                return False
        
        print(f"📱 安装 APK: {apk_path}")
        
        try:
            # 检查设备连接
            result = subprocess.run(['adb', 'devices'], 
                                  capture_output=True, text=True)
            if 'device' not in result.stdout:
                print("❌ 未检测到 Android 设备")
                print("💡 请确保设备已连接并启用 USB 调试")
                return False
            
            # 安装 APK
            subprocess.run(['adb', 'install', '-r', str(apk_path)], 
                          check=True)
            print("✅ APK 安装成功")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ APK 安装失败: {e}")
            return False
        except FileNotFoundError:
            print("❌ ADB 未安装或未配置到 PATH")
            return False
    
    def deploy(self, mode='debug', install=True, clean=False):
        """完整的部署流程"""
        print("🎯 开始完整部署流程...")
        
        # 1. 检查依赖
        if not self.check_dependencies():
            print("❌ 依赖检查失败")
            return False
        
        # 2. 准备构建
        self.prepare_build()
        
        # 3. 构建 APK
        apk_path = self.build_apk(mode, clean)
        if not apk_path:
            print("❌ 构建失败")
            return False
        
        # 4. 安装到设备（可选）
        if install:
            if not self.install_apk(apk_path):
                print("⚠️  安装失败，但 APK 已生成")
        
        print("🎉 部署完成!")
        return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="闲鱼自动评论助手 Android 构建工具")
    parser.add_argument('--mode', choices=['debug', 'release'], 
                       default='debug', help='构建模式')
    parser.add_argument('--clean', action='store_true', 
                       help='清理构建缓存')
    parser.add_argument('--no-install', action='store_true', 
                       help='不安装到设备')
    parser.add_argument('--check-only', action='store_true', 
                       help='只检查环境，不构建')
    
    args = parser.parse_args()
    
    builder = AndroidBuilder()
    
    if args.check_only:
        builder.check_dependencies()
        return
    
    success = builder.deploy(
        mode=args.mode,
        install=not args.no_install,
        clean=args.clean
    )
    
    if success:
        print("\n🎉 构建成功! 可以在 bin/ 目录找到 APK 文件")
        print("📱 使用 'adb install -r bin/xianyucommentassistant-*.apk' 手动安装")
    else:
        print("\n❌ 构建失败! 请检查错误信息")
        sys.exit(1)

if __name__ == '__main__':
    main()