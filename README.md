# 闲鱼自动评论助手

一个基于Appium和AI技术的本地化闲鱼评论自动化工具，支持智能评论生成和反检测机制。

## ⚠️ 重要声明

**本项目仅供学习和研究使用，使用者需要：**
- 遵守闲鱼平台服务条款
- 承担使用风险和责任
- 确保合规使用，不违反相关法规
- 尊重平台规则和其他用户权益

## 🌟 主要特性

- **本地化运行**: 所有数据本地存储，保护隐私安全
- **手动登录**: 用户完全控制账号，系统仅连接已登录会话
- **AI智能生成**: 集成DeepSeek AI，生成多样化自然评论
- **反检测机制**: 模拟人类行为，包含随机间隔和操作模式
- **多类型评论**: 支持询价、感兴趣、夸赞等多种评论类型
- **质量过滤**: 自动过滤和优化评论内容
- **统计分析**: 详细的运行统计和效果分析

## 🏗️ 系统架构

```
用户手动登录闲鱼APP → Appium连接控制 → 商品信息提取 → AI评论生成 → 自动发布评论 → 数据记录统计
```

## 📋 环境要求

### 系统要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **内存**: 4GB+ RAM (含Android模拟器需6GB+)
- **存储**: 2GB+ 可用空间
- **网络**: 稳定网络连接

### 软件依赖
- **Python**: 3.8+
- **Java**: JDK 8+
- **Android SDK**: 最新版本
- **Appium Server**: 2.0+
- **Node.js**: 16+ (用于Appium)

### 硬件设备
- Android手机或模拟器 (API 23+)
- 已安装闲鱼APP

## 🚀 安装配置

### 1. 环境准备

#### 安装Java和Android SDK
```bash
# 下载并安装Java JDK 8+
java -version  # 验证安装

# 下载Android SDK
# 设置环境变量
export JAVA_HOME=/path/to/jdk
export ANDROID_HOME=/path/to/android-sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools
```

#### 安装Node.js和Appium
```bash
# 安装Node.js (16+)
node --version

# 安装Appium
npm install -g appium

# 安装UiAutomator2驱动
appium driver install uiautomator2

# 验证安装
appium --version
```

### 2. Python环境配置

```bash
# 进入项目目录
cd 移动端自动评论

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\\Scripts\\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 设备配置

#### Android手机配置
1. 开启开发者选项
2. 启用USB调试
3. 连接电脑并授权调试
4. 安装闲鱼APP并手动登录账号

#### 验证连接
```bash
adb devices  # 应显示已连接设备
```

### 4. 配置文件设置

编辑 `config/settings.yaml`:

```yaml
# DeepSeek API配置
deepseek_api:
  api_key: "你的DeepSeek API密钥"  # 必填
  
# 设备配置（可选）
appium:
  desired_caps:
    udid: "你的设备ID"  # 可选，多设备时需要指定
```

## 📖 使用方法

### 1. 启动Appium服务
```bash
appium
```

### 2. 手动登录闲鱼APP
在手机或模拟器上：
- 打开闲鱼APP
- 登录你的账号
- 保持APP在前台或后台运行

### 3. 运行程序
```bash
cd src
python main.py
```

### 4. 配置任务
程序启动后会进行系统检查，然后可以：
- 输入商品URL列表
- 选择评论类型
- 开始自动化任务

## 🎛️ 配置说明

### 反检测配置
```yaml
anti_detection:
  comment_interval:
    min: 15  # 最小评论间隔（秒）
    max: 45  # 最大评论间隔（秒）
  daily_limit: 100    # 每日最大评论数
  hourly_limit: 20    # 每小时最大评论数
  typing_speed:
    min: 50   # 最小打字间隔（毫秒）
    max: 150  # 最大打字间隔（毫秒）
```

### 评论类型
- `inquiry`: 询价型评论 ("这个价格还能优惠吗？")
- `interest`: 感兴趣型评论 ("很感兴趣，质量怎么样？")
- `compliment`: 夸赞型评论 ("东西看起来很不错")
- `comparison`: 对比咨询型评论 ("和新的相比性价比如何？")
- `concern`: 关注型评论 ("先关注一下，考虑考虑")

## 📊 功能模块

### 核心模块
- **app_controller.py**: APP控制和页面导航
- **product_analyzer.py**: 商品信息提取和分析
- **comment_generator.py**: AI评论生成和质量过滤
- **comment_publisher.py**: 评论发布和反检测
- **database.py**: 数据存储和统计管理

### 配置模块
- **config.py**: 配置管理
- **ai_client.py**: DeepSeek API客户端

## 🛡️ 安全特性

### 隐私保护
- 完全本地运行，不上传个人数据
- 用户手动登录，系统不存储账号信息
- 所有数据本地SQLite数据库存储

### 反检测机制
- 模拟真实人类操作行为
- 随机化操作间隔和内容
- 动态调整发布频率
- 智能错误处理和重试

### 限制机制
- 每日/每小时评论数量限制
- 连续错误自动停止
- 异常情况自动暂停

## 📈 统计功能

### 实时监控
- 当前任务进度
- 评论生成和发布统计
- 成功率和错误率
- 系统资源使用情况

### 历史数据
- 每日处理统计
- 评论效果分析
- 错误日志记录
- 性能数据追踪

## 🔧 故障排除

### 常见问题

**1. 无法连接到APP**
- 检查USB调试是否开启
- 确认设备已连接且授权
- 验证闲鱼APP是否已启动并登录

**2. 无法找到商品页面**
- 确认商品URL格式正确
- 检查网络连接状态
- 验证商品页面是否存在

**3. 评论发布失败**
- 检查账号是否被限制评论
- 确认评论内容符合平台规范
- 验证APP界面是否正常

**4. AI生成失败**
- 检查DeepSeek API密钥是否正确
- 确认网络连接正常
- 查看API使用额度

### 日志查看
```bash
# 查看实时日志
tail -f data/logs/xianyu_assistant.log

# 查看错误日志
grep "ERROR" data/logs/xianyu_assistant.log
```

## 📄 项目结构
```
移动端自动评论/
├── src/                    # 源代码
│   ├── main.py            # 主程序入口
│   ├── app_controller.py  # APP控制器
│   ├── product_analyzer.py # 商品分析器
│   ├── comment_generator.py # 评论生成器
│   ├── comment_publisher.py # 评论发布器
│   ├── ai_client.py       # AI客户端
│   ├── database.py        # 数据库管理
│   └── config.py          # 配置管理
├── config/                # 配置文件
│   └── settings.yaml      # 主配置文件
├── data/                  # 数据目录
│   ├── logs/              # 日志文件
│   └── *.db              # 数据库文件
├── templates/             # 模板文件
├── requirements.txt       # Python依赖
├── README.md             # 使用说明
└── plan.md               # 开发计划
```

## 🤝 贡献指南

本项目仅供学习研究使用，如需改进：
1. 遵守开源协议
2. 确保代码质量
3. 添加适当的测试
4. 更新相关文档

## 📜 许可证

本项目基于MIT许可证开源。

## ⚖️ 免责声明

- 本工具仅供技术学习和研究使用
- 使用者需要自行承担所有风险和后果
- 开发者不对任何损失或法律问题负责
- 请遵守相关平台的服务条款和法律法规
- 禁止用于商业用途或恶意活动

## 📧 支持联系

如有技术问题，请通过GitHub Issues提交。

---

**请负责任地使用本工具，尊重平台规则和其他用户权益！**