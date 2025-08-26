# 闲鱼自动评论助手 - 移动端应用

基于Kivy框架开发的Android移动端应用，支持关键词循环搜索和自动评论功能。

## 📱 功能特性

### 核心功能
- **关键词循环搜索**: 支持多个关键词依次搜索处理
- **智能评论生成**: AI+模板混合生成自然评论
- **实时任务监控**: 可视化进度跟踪和统计
- **历史记录管理**: 完整的任务执行记录
- **反检测机制**: 人类行为模拟和频率控制

### 移动端优势
- **本地化运行**: 所有数据本地存储，保护隐私
- **Android原生**: 完整的Android权限支持
- **触控优化**: 专为移动设备优化的界面
- **后台运行**: 支持后台任务执行
- **离线功能**: 基础功能可离线使用

## 🏗️ 架构设计

### 应用结构
```
mobile/
├── main.py                 # 主应用入口
├── mobile_config.py        # 移动端配置管理
├── build_android.py        # Android构建脚本
├── buildozer.spec         # Buildozer配置
├── requirements-mobile.txt # 移动端依赖
└── assets/                # 应用资源
```

### UI界面设计
1. **参数设置界面**: 关键词输入、评论类型选择、任务配置
2. **任务监控界面**: 实时进度显示、状态监控、任务控制
3. **历史记录界面**: 已完成任务记录、统计数据查看

### 技术栈
- **UI框架**: Kivy + KivyMD (Material Design)
- **Android打包**: Buildozer + python-for-android
- **核心逻辑**: 复用桌面版Python模块
- **数据存储**: SQLite本地数据库
- **网络请求**: aiohttp + requests

## 🚀 快速开始

### 环境准备

1. **安装Python依赖**:
```bash
pip install -r requirements-mobile.txt
```

2. **配置Android环境**:
```bash
# 安装Java JDK 8+
# 安装Android SDK
# 设置环境变量 ANDROID_HOME
```

3. **安装Buildozer**:
```bash
pip install buildozer
```

### 构建APK

#### 使用构建脚本（推荐）
```bash
# 检查环境
python build_android.py --check-only

# 构建Debug版本
python build_android.py --mode debug

# 构建Release版本
python build_android.py --mode release --clean

# 只构建不安装
python build_android.py --no-install
```

#### 手动构建
```bash
# 初始化构建环境
buildozer android debug

# 清理重建
buildozer android clean
buildozer android debug

# 构建Release版本
buildozer android release
```

### 安装到设备

```bash
# 通过构建脚本自动安装
python build_android.py --mode debug

# 手动安装APK
adb install -r bin/xianyucommentassistant-*-debug.apk
```

## 📋 使用说明

### 1. 首次使用

1. **安装APK**: 将构建好的APK安装到Android设备
2. **权限授权**: 首次启动时授权必要权限
3. **配置API**: 在设置中配置DeepSeek API密钥（可选）

### 2. 设置任务参数

#### 关键词设置
- 在"关键词设置"卡片中输入搜索关键词
- 多个关键词用逗号分隔：`手机,电脑,相机`
- 每个关键词将依次处理，直到达到设定的商品数量

#### 评论类型选择
- **询价型**: 价格相关的评论
- **感兴趣型**: 表达购买意向
- **夸赞型**: 对商品的正面评价
- **对比咨询型**: 与其他商品对比
- **关注型**: 表示关注但暂不购买

#### 任务配置
- **每个关键词最大处理商品数**: 10-200（默认50）
- **任务名称**: 便于识别的任务名称
- **每日最大评论数**: 20-300（默认100）

### 3. 监控任务执行

切换到"任务监控"标签：
- 查看当前处理的关键词
- 实时统计数据（商品数、评论数、成功率）
- 任务进度条显示
- 随时停止任务

### 4. 查看历史记录

在"历史记录"标签中：
- 查看已完成的关键词任务
- 每个关键词的详细统计
- 成功率和时长信息

## ⚙️ 配置选项

### 反检测设置
- **评论间隔**: 15-45秒随机间隔
- **每日限制**: 防止过度使用
- **打字速度**: 50-150ms模拟人类输入
- **行为随机化**: 滚动、暂停等随机行为

### API配置
```yaml
deepseek_api:
  api_key: "your-api-key"
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
  max_tokens: 200
  temperature: 0.7
```

## 🔧 开发说明

### 项目结构
- `main.py`: 主应用类和界面定义
- `mobile_config.py`: 移动端专用配置管理
- `build_android.py`: 自动化构建脚本
- `buildozer.spec`: Android打包配置

### 核心组件
1. **ParameterInputScreen**: 参数输入界面
2. **MonitorScreen**: 任务监控界面  
3. **HistoryScreen**: 历史记录界面
4. **XianyuMobileApp**: 主应用类

### 自定义开发

#### 添加新的评论类型
```python
# 在mobile_config.py中添加
"new_type": [
    "新类型评论模板1",
    "新类型评论模板2"
]
```

#### 修改界面布局
```python
# 在对应Screen类中修改
def _create_custom_card(self):
    card = MDCard(...)
    # 自定义布局
    return card
```

## 📱 Android权限说明

应用需要以下权限：
- `INTERNET`: 网络访问（API调用）
- `WRITE_EXTERNAL_STORAGE`: 日志和数据存储
- `SYSTEM_ALERT_WINDOW`: 悬浮窗口显示
- `WAKE_LOCK`: 防止设备休眠
- `ACCESS_NETWORK_STATE`: 网络状态检测

## 🐛 故障排除

### 常见问题

1. **构建失败**
   - 检查Java JDK版本（需要8+）
   - 确认Android SDK正确安装
   - 清理构建缓存：`buildozer android clean`

2. **APK安装失败**
   - 启用"未知来源"应用安装
   - 检查设备存储空间
   - 卸载旧版本后重新安装

3. **权限被拒绝**
   - 在设备设置中手动授权
   - 重新启动应用

4. **网络连接问题**
   - 检查网络连接
   - 验证API密钥正确性
   - 查看防火墙设置

### 日志查看
```bash
# 查看应用日志
adb logcat | grep python

# 查看系统日志
adb logcat | grep XianyuComment
```

## 🔒 安全与合规

### 数据安全
- 所有用户数据仅存储在本地
- API密钥使用加密存储
- 不收集或上传用户隐私信息

### 使用规范
- 仅限个人学习研究使用
- 遵守闲鱼平台服务条款
- 不得用于商业目的
- 控制使用频率，避免对平台造成影响

## 📊 性能优化

### 电池优化
- 合理设置任务间隔
- 避免长时间后台运行
- 及时停止不需要的任务

### 存储优化
- 定期清理历史记录
- 控制日志文件大小
- 备份重要数据后清理

## 🆘 技术支持

如遇技术问题：
1. 查看本文档的故障排除部分
2. 检查设备兼容性
3. 提供详细的错误日志

---

**重要提醒**: 本工具仅供学习研究使用，请遵守相关平台服务条款和法律法规，合理使用自动化工具。