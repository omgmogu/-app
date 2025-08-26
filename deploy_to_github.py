#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将项目部署到GitHub并自动构建APK
"""

import os
import subprocess
import sys
from pathlib import Path

def setup_git():
    """初始化Git仓库"""
    print("🔧 设置Git仓库...")
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 检查是否已经是git仓库
    if (project_root / ".git").exists():
        print("✅ Git仓库已存在")
        return True
    
    try:
        # 初始化git仓库
        subprocess.run(["git", "init"], check=True, capture_output=True)
        print("✅ Git仓库初始化完成")
        
        # 设置默认分支为main
        subprocess.run(["git", "branch", "-M", "main"], check=True, capture_output=True)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git初始化失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ 未找到Git命令，请先安装Git")
        return False

def create_gitignore():
    """创建.gitignore文件"""
    print("📝 创建.gitignore文件...")
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Buildozer
.buildozer/
bin/
*.apk
*.aab

# Android
*.keystore
local.properties

# Deployment tools
.deploy/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
temp/
"""
    
    gitignore_file = Path(__file__).parent / ".gitignore"
    with open(gitignore_file, 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    
    print("✅ .gitignore文件创建完成")

def create_readme():
    """创建或更新README.md"""
    print("📚 更新README.md...")
    
    readme_content = """# 🎯 闲鱼自动评论助手

[![Build Android APK](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-apk.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/build-apk.yml)

## 📱 项目简介

闲鱼自动评论助手是一个基于Python开发的智能化评论工具，支持：

- 🔄 **多关键词循环搜索** - 依次搜索多个关键词
- 🤖 **AI智能评论生成** - 基于DeepSeek AI的个性化评论
- 📱 **跨平台支持** - Windows桌面版 + Android移动版
- 🎨 **Material Design UI** - 精美的移动端界面
- 🛡️ **反检测机制** - 人性化行为模拟

## 🚀 快速开始

### 桌面版本（立即可用）
```bash
# 1. 克隆项目
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd 移动端自动评论

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
# 编辑 config/settings.yaml，添加DeepSeek API密钥

# 4. 运行程序
cd src
python main.py
```

### 📱 Android APK获取

#### 方法1: 自动构建（推荐）
1. Fork此仓库到你的GitHub账户
2. 在GitHub Actions中自动构建
3. 下载生成的APK文件

#### 方法2: 手动下载
前往 [Releases](../../releases) 页面下载预编译的APK

## 🏗️ 项目架构

```
移动端自动评论/
├── src/                    # 核心源代码
│   ├── main.py            # 主程序入口
│   ├── keyword_manager.py # 关键词管理模块
│   ├── app_controller.py  # APP控制器
│   ├── ai_client.py       # AI接口客户端
│   └── ...               # 其他核心模块
├── mobile/                # Android应用
│   ├── main.py           # Kivy移动应用
│   ├── buildozer.spec    # Android打包配置
│   └── ...              # 移动端相关文件
├── config/               # 配置文件
├── tests/               # 测试代码
└── .github/workflows/   # GitHub Actions配置
```

## 🔧 功能特性

### 核心功能
- ✅ **多关键词循环搜索** - 支持批量关键词处理
- ✅ **商品卡智能遍历** - 自动点击和信息提取
- ✅ **AI评论生成** - DeepSeek API集成
- ✅ **反检测机制** - 随机间隔和行为模拟
- ✅ **数据持久化** - SQLite数据库存储

### 移动端特性
- 📱 **Material Design UI** - 现代化界面设计
- ⚙️ **参数配置界面** - 直观的设置选项
- 📊 **实时监控** - 任务进度和状态显示
- 📋 **历史记录** - 完整的操作历史

### 技术规格
- **前端**: Kivy + KivyMD (Python)
- **后端**: Python 3.8+ 
- **数据库**: SQLite
- **AI模型**: DeepSeek API
- **自动化**: Appium + UiAutomator2
- **打包**: Buildozer (Android)

## 📋 系统要求

### 桌面版本
- **操作系统**: Windows 10/11, macOS, Linux
- **Python**: 3.8+
- **内存**: 4GB+
- **存储**: 1GB可用空间

### 移动版本
- **系统**: Android 6.0+ (API 23+)
- **架构**: arm64-v8a, armeabi-v7a
- **内存**: 2GB+
- **存储**: 50MB+

## 🛠️ 开发指南

### 环境搭建
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\\Scripts\\activate     # Windows

# 安装开发依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 运行测试
```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定测试
python tests/test_keyword_search.py
```

### 构建APK
```bash
# 本地构建（需要Linux/macOS）
cd mobile
buildozer android debug

# 或使用GitHub Actions自动构建
```

## 📱 APK安装说明

1. **下载APK文件** - 从Releases或Actions下载
2. **开启未知来源** - Android设置中允许安装未知来源应用
3. **安装APK** - 点击APK文件进行安装
4. **授予权限** - 允许存储和网络访问权限
5. **启动测试** - 打开应用验证功能

## ⚠️ 重要声明

- ⚖️ **仅供学习研究使用** - 请勿用于商业用途
- 🛡️ **遵守平台规则** - 使用时请遵守相关平台服务条款
- 🔒 **隐私保护** - 所有数据本地存储，不上传云端
- ⚠️ **使用风险** - 用户承担使用过程中的所有风险

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目仅供学习和研究使用。

## 🙏 致谢

- [Kivy](https://kivy.org/) - 跨平台Python框架
- [KivyMD](https://kivymd.readthedocs.io/) - Material Design组件
- [DeepSeek](https://platform.deepseek.com/) - AI语言模型
- [Appium](https://appium.io/) - 移动端自动化框架

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**
"""
    
    readme_file = Path(__file__).parent / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✅ README.md更新完成")

def stage_and_commit():
    """添加文件并提交"""
    print("📦 添加文件到Git...")
    
    try:
        # 添加所有文件
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        
        # 检查是否有文件需要提交
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("✅ 没有新的更改需要提交")
            return True
        
        # 提交更改
        commit_message = "feat: 闲鱼自动评论助手 - 完整功能实现\n\n- 多关键词循环搜索功能\n- Android移动端UI\n- GitHub Actions自动构建APK\n- 完整的测试框架\n- Material Design界面"
        
        subprocess.run(["git", "commit", "-m", commit_message], 
                      check=True, capture_output=True)
        
        print("✅ 代码提交完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git操作失败: {e}")
        return False

def show_github_instructions():
    """显示GitHub操作说明"""
    print("""
🎯 接下来的GitHub操作步骤:

1. 📝 在GitHub上创建新仓库:
   - 访问 https://github.com/new
   - 仓库名: xianyuapp 或 移动端自动评论
   - 描述: 闲鱼自动评论助手 - 多关键词循环搜索工具
   - 选择 Public（以便使用GitHub Actions）

2. 🔗 添加远程仓库并推送:
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main

3. 🚀 启用GitHub Actions:
   - 推送后自动启用，无需额外设置
   - 在Actions页面可以看到APK构建过程

4. 📱 下载APK:
   - 方法1: 在Actions构建完成后下载Artifacts
   - 方法2: 创建Release后自动发布APK

5. 🏷️ 创建Release（可选）:
   git tag v1.0
   git push origin v1.0
   
💡 Tips:
- 构建时间约30-45分钟
- APK文件会自动上传到Artifacts
- 创建tag后会自动发布Release
""")

def main():
    """主函数"""
    print("🚀 GitHub自动化APK构建部署\n")
    
    # 设置Git仓库
    if not setup_git():
        print("❌ Git设置失败")
        return False
    
    # 创建项目文件
    create_gitignore()
    create_readme()
    
    # 提交代码
    if not stage_and_commit():
        print("❌ 代码提交失败")
        return False
    
    # 显示后续操作说明
    show_github_instructions()
    
    print("✅ 项目已准备好推送到GitHub!")
    print("🎯 现在可以享受自动化APK构建了!")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)