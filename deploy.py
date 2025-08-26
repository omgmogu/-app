#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android APK自动化部署脚本
自动安装Java JDK, Android SDK, 并构建APK
"""

import sys
import os
import subprocess
import platform
import urllib.request
import zipfile
import tarfile
from pathlib import Path
import time
import json

class AndroidDeployment:
    """Android部署管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.mobile_dir = self.project_root / "mobile"
        self.deploy_dir = self.project_root / ".deploy"
        self.system = platform.system()
        
        # 创建部署目录
        self.deploy_dir.mkdir(exist_ok=True)
        
        # 环境配置
        self.java_home = None
        self.android_home = None
        self.buildozer_home = None
        
    def log(self, message, level="INFO"):
        """记录日志"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command, cwd=None, timeout=300):
        """执行系统命令"""
        try:
            self.log(f"执行命令: {' '.join(command) if isinstance(command, list) else command}")
            
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=True if isinstance(command, str) else False
            )
            
            if result.returncode == 0:
                self.log("命令执行成功", "SUCCESS")
                return True, result.stdout
            else:
                self.log(f"命令执行失败: {result.stderr}", "ERROR")
                return False, result.stderr
                
        except subprocess.TimeoutExpired:
            self.log(f"命令执行超时 ({timeout}s)", "ERROR")
            return False, "Timeout"
        except Exception as e:
            self.log(f"命令执行异常: {e}", "ERROR")
            return False, str(e)
    
    def check_system_requirements(self):
        """检查系统要求"""
        self.log("检查系统环境...")
        
        # 检查操作系统
        if self.system != 'Windows':
            self.log("当前脚本优化为Windows系统", "WARNING")
        
        # 检查Python版本
        if sys.version_info < (3, 8):
            self.log("Python版本过低，需要3.8+", "ERROR")
            return False
        
        # 检查管理员权限
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.log("建议以管理员权限运行以避免权限问题", "WARNING")
        except:
            pass
        
        # 检查网络连接
        try:
            urllib.request.urlopen('https://www.google.com', timeout=5)
            self.log("网络连接正常")
        except:
            self.log("网络连接可能有问题，可能影响下载", "WARNING")
        
        self.log("系统环境检查完成")
        return True
    
    def install_java_jdk(self):
        """安装Java JDK"""
        self.log("检查Java JDK...")
        
        # 检查是否已安装Java
        success, output = self.run_command("java -version")
        if success:
            self.log("Java已安装，跳过安装步骤")
            
            # 尝试找到JAVA_HOME
            java_home_candidates = [
                os.environ.get('JAVA_HOME'),
                'C:\\Program Files\\Java\\jdk-11',
                'C:\\Program Files\\Java\\jdk-17',
                'C:\\Program Files\\OpenJDK\\jdk-11',
            ]
            
            for path in java_home_candidates:
                if path and Path(path).exists():
                    self.java_home = path
                    break
            
            if not self.java_home:
                self.log("未找到JAVA_HOME，使用系统Java", "WARNING")
            
            return True
        
        # 下载并安装OpenJDK
        self.log("开始下载OpenJDK 11...")
        
        if self.system == 'Windows':
            jdk_url = "https://github.com/adoptium/temurin11-binaries/releases/download/jdk-11.0.21%2B9/OpenJDK11U-jdk_x64_windows_hotspot_11.0.21_9.zip"
            jdk_file = self.deploy_dir / "openjdk11.zip"
            jdk_dir = self.deploy_dir / "jdk-11.0.21+9"
        else:
            self.log("非Windows系统，请手动安装Java JDK", "ERROR")
            return False
        
        # 下载JDK
        try:
            self.log("正在下载OpenJDK，请稍候...")
            urllib.request.urlretrieve(jdk_url, jdk_file)
            self.log("OpenJDK下载完成")
        except Exception as e:
            self.log(f"下载OpenJDK失败: {e}", "ERROR")
            # 尝试使用Chocolatey安装
            self.log("尝试使用Chocolatey安装OpenJDK...")
            success, _ = self.run_command("choco install openjdk11 -y")
            if success:
                self.log("通过Chocolatey安装OpenJDK成功")
                return True
            else:
                self.log("请手动安装Java JDK 8+", "ERROR")
                return False
        
        # 解压JDK
        try:
            self.log("正在解压OpenJDK...")
            with zipfile.ZipFile(jdk_file, 'r') as zip_ref:
                zip_ref.extractall(self.deploy_dir)
            
            # 设置JAVA_HOME
            self.java_home = str(jdk_dir)
            os.environ['JAVA_HOME'] = self.java_home
            os.environ['PATH'] = f"{self.java_home}\\bin;{os.environ['PATH']}"
            
            self.log(f"OpenJDK安装完成: {self.java_home}")
            return True
            
        except Exception as e:
            self.log(f"解压OpenJDK失败: {e}", "ERROR")
            return False
    
    def install_android_sdk(self):
        """安装Android SDK"""
        self.log("检查Android SDK...")
        
        # 检查是否已安装
        android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if android_home and Path(android_home).exists():
            self.log("Android SDK已安装，跳过安装步骤")
            self.android_home = android_home
            return True
        
        # 下载命令行工具
        self.log("开始下载Android SDK命令行工具...")
        
        if self.system == 'Windows':
            sdk_url = "https://dl.google.com/android/repository/commandlinetools-win-9477386_latest.zip"
            sdk_file = self.deploy_dir / "android-sdk-tools.zip"
            sdk_dir = self.deploy_dir / "android-sdk"
        else:
            self.log("非Windows系统，请手动安装Android SDK", "ERROR")
            return False
        
        # 下载SDK工具
        try:
            self.log("正在下载Android SDK工具，请稍候...")
            urllib.request.urlretrieve(sdk_url, sdk_file)
            self.log("Android SDK工具下载完成")
        except Exception as e:
            self.log(f"下载Android SDK工具失败: {e}", "ERROR")
            return False
        
        # 解压SDK工具
        try:
            self.log("正在解压Android SDK工具...")
            sdk_dir.mkdir(exist_ok=True)
            with zipfile.ZipFile(sdk_file, 'r') as zip_ref:
                zip_ref.extractall(sdk_dir)
            
            # 创建目录结构
            cmdline_tools_dir = sdk_dir / "cmdline-tools"
            if not cmdline_tools_dir.exists():
                # 可能解压到了不同的目录结构
                for item in sdk_dir.iterdir():
                    if item.is_dir() and 'cmdline-tools' in item.name:
                        cmdline_tools_dir = item
                        break
            
            # 设置Android SDK环境
            self.android_home = str(sdk_dir)
            os.environ['ANDROID_HOME'] = self.android_home
            os.environ['ANDROID_SDK_ROOT'] = self.android_home
            
            # 更新PATH
            sdk_tools_path = f"{sdk_dir}\\cmdline-tools\\bin;{sdk_dir}\\platform-tools"
            os.environ['PATH'] = f"{sdk_tools_path};{os.environ['PATH']}"
            
            self.log(f"Android SDK工具安装完成: {self.android_home}")
            
            # 安装必要的SDK组件
            self.install_android_components()
            
            return True
            
        except Exception as e:
            self.log(f"解压Android SDK工具失败: {e}", "ERROR")
            return False
    
    def install_android_components(self):
        """安装Android SDK组件"""
        self.log("安装Android SDK组件...")
        
        # 首先接受许可证
        sdkmanager_path = Path(self.android_home) / "cmdline-tools" / "bin" / "sdkmanager.bat"
        
        if not sdkmanager_path.exists():
            # 尝试其他可能的路径
            possible_paths = [
                Path(self.android_home) / "cmdline-tools" / "latest" / "bin" / "sdkmanager.bat",
                Path(self.android_home) / "tools" / "bin" / "sdkmanager.bat"
            ]
            
            for path in possible_paths:
                if path.exists():
                    sdkmanager_path = path
                    break
        
        if sdkmanager_path.exists():
            # 接受许可证
            self.log("接受Android SDK许可证...")
            self.run_command(f'echo y | "{sdkmanager_path}" --licenses')
            
            # 安装核心组件
            components = [
                "platform-tools",
                "build-tools;33.0.2",
                "platforms;android-33",
                "platforms;android-23"
            ]
            
            for component in components:
                self.log(f"安装组件: {component}")
                self.run_command(f'"{sdkmanager_path}" "{component}"', timeout=600)
        else:
            self.log("未找到sdkmanager工具", "ERROR")
    
    def install_python_dependencies(self):
        """安装Python依赖"""
        self.log("安装Python构建依赖...")
        
        # 升级pip
        success, _ = self.run_command([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        if not success:
            self.log("升级pip失败", "WARNING")
        
        # 安装buildozer
        self.log("安装buildozer...")
        success, _ = self.run_command([sys.executable, "-m", "pip", "install", "buildozer"])
        if not success:
            self.log("安装buildozer失败", "ERROR")
            return False
        
        # 安装Kivy相关依赖
        dependencies = [
            "kivy==2.1.0",
            "kivymd==1.1.1", 
            "pyyaml",
            "requests",
            "aiohttp",
            "plyer",
            "loguru",
            "jieba",
            "python-dateutil",
            "cython"
        ]
        
        self.log("安装Python依赖包...")
        for dep in dependencies:
            self.log(f"安装: {dep}")
            success, output = self.run_command([sys.executable, "-m", "pip", "install", dep])
            if not success:
                self.log(f"安装{dep}失败: {output}", "WARNING")
        
        self.log("Python依赖安装完成")
        return True
    
    def setup_build_environment(self):
        """设置构建环境"""
        self.log("配置构建环境...")
        
        # 设置环境变量
        env_vars = {
            'JAVA_HOME': self.java_home,
            'ANDROID_HOME': self.android_home,
            'ANDROID_SDK_ROOT': self.android_home
        }
        
        # 写入环境变量到批处理文件
        env_file = self.project_root / "set_env.bat"
        with open(env_file, 'w') as f:
            f.write("@echo off\n")
            f.write("echo 设置Android开发环境变量...\n")
            for key, value in env_vars.items():
                if value:
                    f.write(f'set {key}={value}\n')
            
            # 更新PATH
            if self.java_home:
                f.write(f'set PATH=%JAVA_HOME%\\bin;%PATH%\n')
            if self.android_home:
                f.write(f'set PATH=%ANDROID_HOME%\\cmdline-tools\\bin;%ANDROID_HOME%\\platform-tools;%PATH%\n')
            
            f.write("echo 环境变量设置完成\n")
            f.write("echo JAVA_HOME=%JAVA_HOME%\n")
            f.write("echo ANDROID_HOME=%ANDROID_HOME%\n")
        
        self.log(f"环境变量配置文件创建: {env_file}")
        
        # 执行环境设置
        self.run_command(str(env_file))
        
        return True
    
    def build_apk(self):
        """构建APK"""
        self.log("开始构建Android APK...")
        
        # 切换到mobile目录
        if not self.mobile_dir.exists():
            self.log("mobile目录不存在", "ERROR")
            return False
        
        # 检查buildozer.spec
        spec_file = self.mobile_dir / "buildozer.spec"
        if not spec_file.exists():
            self.log("buildozer.spec文件不存在", "ERROR")
            return False
        
        # 初始化buildozer
        self.log("初始化buildozer...")
        success, output = self.run_command("buildozer init", cwd=self.mobile_dir)
        if success:
            self.log("buildozer初始化成功")
        else:
            self.log("buildozer可能已初始化，继续构建", "WARNING")
        
        # 构建debug APK
        self.log("开始构建APK，这可能需要较长时间...")
        success, output = self.run_command(
            "buildozer android debug", 
            cwd=self.mobile_dir, 
            timeout=3600  # 1小时超时
        )
        
        if success:
            self.log("APK构建成功！", "SUCCESS")
            
            # 查找生成的APK文件
            bin_dir = self.mobile_dir / "bin"
            if bin_dir.exists():
                apk_files = list(bin_dir.glob("*.apk"))
                if apk_files:
                    for apk_file in apk_files:
                        self.log(f"生成的APK: {apk_file}")
                    return True
            
            self.log("APK构建完成但未找到APK文件", "WARNING")
            return True
        else:
            self.log(f"APK构建失败: {output}", "ERROR")
            return False
    
    def verify_build(self):
        """验证构建结果"""
        self.log("验证构建结果...")
        
        bin_dir = self.mobile_dir / "bin"
        if not bin_dir.exists():
            self.log("bin目录不存在", "ERROR")
            return False
        
        apk_files = list(bin_dir.glob("*.apk"))
        if not apk_files:
            self.log("未找到APK文件", "ERROR")
            return False
        
        for apk_file in apk_files:
            size_mb = apk_file.stat().st_size / (1024 * 1024)
            self.log(f"APK文件: {apk_file.name} ({size_mb:.1f} MB)")
            
            # 验证APK完整性
            if self.android_home:
                aapt_path = Path(self.android_home) / "build-tools" / "*" / "aapt.exe"
                # 简单验证APK结构
                try:
                    with zipfile.ZipFile(apk_file, 'r') as apk_zip:
                        file_list = apk_zip.namelist()
                        self.log(f"APK包含{len(file_list)}个文件")
                        
                        # 检查关键文件
                        required_files = ['AndroidManifest.xml', 'classes.dex']
                        for req_file in required_files:
                            if any(req_file in f for f in file_list):
                                self.log(f"✓ 找到关键文件: {req_file}")
                            else:
                                self.log(f"✗ 缺少关键文件: {req_file}", "WARNING")
                        
                except Exception as e:
                    self.log(f"APK验证异常: {e}", "WARNING")
        
        self.log("构建验证完成", "SUCCESS")
        return True
    
    def deploy(self):
        """执行完整部署流程"""
        self.log("=== 开始Android APK自动化部署 ===")
        
        # 检查系统要求
        if not self.check_system_requirements():
            return False
        
        # 安装Java JDK
        if not self.install_java_jdk():
            self.log("Java JDK安装失败，终止部署", "ERROR")
            return False
        
        # 安装Android SDK
        if not self.install_android_sdk():
            self.log("Android SDK安装失败，终止部署", "ERROR")
            return False
        
        # 安装Python依赖
        if not self.install_python_dependencies():
            self.log("Python依赖安装失败，终止部署", "ERROR")
            return False
        
        # 设置构建环境
        if not self.setup_build_environment():
            self.log("构建环境设置失败，终止部署", "ERROR")
            return False
        
        # 构建APK
        if not self.build_apk():
            self.log("APK构建失败", "ERROR")
            return False
        
        # 验证构建结果
        if not self.verify_build():
            self.log("构建验证失败", "WARNING")
        
        self.log("=== Android APK部署完成 ===", "SUCCESS")
        self.log("接下来可以:")
        self.log("1. 在mobile/bin/目录找到生成的APK文件")
        self.log("2. 将APK传输到Android设备并安装")
        self.log("3. 在设备上测试应用功能")
        
        return True

def main():
    """主函数"""
    deployment = AndroidDeployment()
    success = deployment.deploy()
    
    if success:
        print("\n🎉 部署成功完成!")
        return 0
    else:
        print("\n❌ 部署过程中遇到错误")
        return 1

if __name__ == '__main__':
    sys.exit(main())