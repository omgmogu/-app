#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成Google Colab notebook用于APK构建
"""

import json
from pathlib import Path

def create_colab_notebook():
    """创建Colab notebook配置"""
    
    # 读取buildozer.spec内容
    mobile_dir = Path(__file__).parent / "mobile"
    buildozer_spec = mobile_dir / "buildozer.spec"
    
    if buildozer_spec.exists():
        with open(buildozer_spec, 'r', encoding='utf-8') as f:
            spec_content = f.read()
    else:
        # 使用默认配置
        spec_content = """[app]
title = 闲鱼自动评论助手
package.name = xianyucommentassistant
package.domain = com.xianyuassistant
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,yaml
version = 1.0
requirements = python3,kivy==2.1.0,kivymd==1.1.1,requests,pyyaml
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 0"""
    
    # 读取main.py内容
    main_py_file = mobile_dir / "main.py"
    if main_py_file.exists():
        with open(main_py_file, 'r', encoding='utf-8') as f:
            main_py_content = f.read()
    else:
        # 使用简化版本
        main_py_content = '''from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout

class XianyuApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(
            text='闲鱼自动评论助手',
            font_size='24sp',
            size_hint_y=None,
            height='60dp'
        )
        
        info = Label(
            text='Android版本构建成功!\\\\n\\\\n这是移动端测试版本。\\\\n完整功能请使用桌面版本。',
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        
        layout.add_widget(title)
        layout.add_widget(info)
        
        return layout

if __name__ == '__main__':
    XianyuApp().run()'''

    # 创建Colab notebook JSON
    notebook = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# 闲鱼自动评论助手 - Android APK构建\n",
                    "\n",
                    "这个notebook将自动构建闲鱼自动评论助手的Android APK文件。\n",
                    "\n",
                    "**构建时间**: 约30-45分钟  \n",
                    "**生成文件**: xianyucommentassistant-1.0-debug.apk\n",
                    "\n",
                    "## 步骤说明\n",
                    "1. 安装构建环境\n",
                    "2. 配置Android开发工具\n",
                    "3. 创建应用代码\n",
                    "4. 构建APK文件\n",
                    "5. 下载APK"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 第1步: 安装构建环境\n",
                    "print('📦 安装构建环境...')\n",
                    "\n",
                    "!apt update -qq\n",
                    "!apt install -y openjdk-8-jdk wget unzip git\n",
                    "\n",
                    "# 安装Python依赖\n",
                    "!pip install buildozer cython==0.29.33\n",
                    "\n",
                    "# 设置Java环境\n",
                    "import os\n",
                    "os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-8-openjdk-amd64'\n",
                    "os.environ['PATH'] = f\"{os.environ['JAVA_HOME']}/bin:{os.environ['PATH']}\"\n",
                    "\n",
                    "print('✅ 构建环境安装完成')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 第2步: 创建项目目录和配置文件\n",
                    "print('📁 创建项目结构...')\n",
                    "\n",
                    "!mkdir -p /content/mobile\n",
                    "%cd /content/mobile\n",
                    "\n",
                    "# 创建buildozer.spec配置文件\n",
                    f\"\"\"buildozer_spec = '''{spec_content}'''\n",
                    "\n",
                    "with open('buildozer.spec', 'w', encoding='utf-8') as f:\n",
                    "    f.write(buildozer_spec)\n",
                    "\n",
                    "print('✅ buildozer.spec 创建完成')\"\"\""
                ]
            },
            {
                "cell_type": "code", 
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f\"\"\"# 第3步: 创建应用代码\n",
                    "print('📱 创建Android应用代码...')\n",
                    "\n",
                    "# 创建main.py应用文件\n",
                    "main_py_code = '''{main_py_content}'''\n",
                    "\n",
                    "with open('main.py', 'w', encoding='utf-8') as f:\n",
                    "    f.write(main_py_code)\n",
                    "\n",
                    "print('✅ 应用代码创建完成')\"\"\""
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 第4步: 构建APK\n",
                    "print('🔨 开始构建APK...')\n",
                    "print('⏰ 这个过程大约需要30-45分钟，请耐心等待')\n",
                    "\n",
                    "# 初始化buildozer\n",
                    "!buildozer init\n",
                    "\n",
                    "# 构建debug APK\n",
                    "!buildozer android debug\n",
                    "\n",
                    "print('🎉 APK构建完成！')"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 第5步: 检查和下载APK\n",
                    "print('📱 检查生成的APK文件...')\n",
                    "\n",
                    "!ls -la bin/\n",
                    "!du -h bin/*.apk\n",
                    "\n",
                    "# 显示APK信息\n",
                    "import glob\n",
                    "apk_files = glob.glob('bin/*.apk')\n",
                    "\n",
                    "if apk_files:\n",
                    "    for apk in apk_files:\n",
                    "        size = os.path.getsize(apk) / (1024*1024)\n",
                    "        print(f'📦 生成APK: {apk} ({size:.1f} MB)')\n",
                    "    \n",
                    "    print('\\n📥 下载说明:')\n",
                    "    print('1. 点击左侧文件夹图标')\n",
                    "    print('2. 导航到 mobile/bin/ 目录')\n",
                    "    print('3. 右键点击 .apk 文件')\n",
                    "    print('4. 选择\"下载\"')\n",
                    "    print('\\n🎉 APK构建成功完成！')\n",
                    "else:\n",
                    "    print('❌ 未找到APK文件，构建可能失败')\n"
                ]
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "## 📱 APK安装说明\n",
                    "\n",
                    "下载APK后：\n",
                    "\n",
                    "1. **传输到Android设备** (通过USB、邮件、云盘等)\n",
                    "2. **开启未知来源安装**:\n",
                    "   - Android 8+: 设置 → 应用和通知 → 特殊应用权限 → 安装未知应用\n",
                    "   - Android 7-: 设置 → 安全 → 未知来源\n",
                    "3. **点击APK文件安装**\n",
                    "4. **授予必要权限** (存储、网络等)\n",
                    "5. **启动应用测试**\n",
                    "\n",
                    "## 📋 APK信息\n",
                    "- **应用名称**: 闲鱼自动评论助手\n",
                    "- **包名**: com.xianyuassistant.xianyucommentassistant  \n",
                    "- **版本**: 1.0\n",
                    "- **支持**: Android 6.0+ (API 23+)\n",
                    "- **架构**: armeabi-v7a, arm64-v8a\n",
                    "- **大小**: 约15-30MB\n",
                    "\n",
                    "## ⚠️ 重要说明\n",
                    "- 这是移动端UI测试版本\n",
                    "- 完整功能需要配合桌面版本使用\n",
                    "- APK仅供学习和测试用途"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python",
                "version": "3.10.12"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 0
    }
    
    # 保存notebook
    notebook_file = Path(__file__).parent / "XianyuApp_APK_Builder.ipynb"
    
    with open(notebook_file, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Google Colab notebook已创建: {notebook_file}")
    print("\n📋 使用说明:")
    print("1. 上传 XianyuApp_APK_Builder.ipynb 到 Google Colab")
    print("2. 依次运行所有代码块")
    print("3. 等待构建完成（约30-45分钟）")
    print("4. 下载生成的APK文件")
    print("\n🌐 Google Colab地址: https://colab.research.google.com/")

if __name__ == '__main__':
    create_colab_notebook()