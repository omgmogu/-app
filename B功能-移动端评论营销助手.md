# B功能：移动端评论助手 - 生产实施文档

## 📊 系统概述

### 核心功能
**移动端评论营销助手** - 基于手动登录的智能商品评论自动化系统

### 主要特色
- **手动登录**：用户控制账号安全，系统连接已登录APP会话
- **智能分析**：深度提取商品信息和竞品评论数据
- **AI文案生成**：基于DeepSeek AI根据规则生成多样化评论
- **本地运行**：完全本地化部署，数据安全可控

### 工作流程
```
用户手动登录APP → 系统连接会话 → 导航商品页面 → 提取商品信息 → AI生成文案 → 自动发布评论 → 记录统计
```

## 🏗️ 技术架构

### 系统架构图
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户手动登录   │ →  │  Appium控制器   │ →  │  商品信息提取   │
│   移动APP   │    │   APP会话      │    │   UI元素定位    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ↓                        ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   管理界面GUI   │ ←  │  SQLite数据库   │ ←  │  DeepSeek AI    │
│   任务控制台    │    │   商品数据      │    │   文案生成      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ↓                        ↓
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   效果统计      │ ←  │  评论发布模块   │ ←  │  反检测控制     │
│   数据分析      │    │   自动操作      │    │   行为模拟      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 技术栈
```yaml
编程语言: Python 3.8+
移动自动化: Appium + UiAutomator2
AI服务: DeepSeek API
数据库: SQLite
GUI框架: Tkinter
部署方式: 单机本地运行
```

## 🛠️ 环境搭建

### 系统要求
- **操作系统**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **内存**: 6GB+ RAM (含Android模拟器)
- **存储**: 3GB+ 可用空间
- **设备**: Android手机或模拟器 (API 23+)
- **网络**: 稳定网络连接（用于API调用）

### 安装步骤

#### 1. Java和Android环境
```bash
# 安装Java JDK 8+
java -version  # 确认安装

# 下载Android SDK
# 设置环境变量
export JAVA_HOME=/path/to/jdk
export ANDROID_HOME=/path/to/android-sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools
```

#### 2. Python环境配置
```bash
# 创建虚拟环境
python -m venv xianyu_comment_env

# 激活环境
# Windows
xianyu_comment_env\Scripts\activate
# macOS/Linux
source xianyu_comment_env/bin/activate

# 安装核心依赖
pip install appium-python-client selenium requests sqlite3 tkinter Pillow
```

#### 3. Appium Server安装
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

#### 4. Android设备配置
```bash
# 真机配置
# 1. 开启开发者选项
# 2. 启用USB调试
# 3. 连接设备，确认授权

# 验证连接
adb devices

# 模拟器配置（可选）
# 推荐使用Android Studio AVD或夜神模拟器
```

#### 5. 项目目录结构
```
xianyu-comment-assistant/
├── src/
│   ├── main.py                 # 主程序入口
│   ├── app_controller.py       # APP控制器
│   ├── product_analyzer.py     # 商品分析器
│   ├── comment_generator.py    # 评论生成器
│   ├── comment_publisher.py    # 评论发布器
│   ├── ai_client.py           # AI客户端
│   ├── database.py            # 数据库管理
│   ├── gui.py                 # GUI界面
│   └── config.py              # 配置管理
├── data/
│   ├── products.db            # 商品数据库
│   ├── comments.db            # 评论记录
│   └── logs/                  # 日志文件
├── config/
│   └── settings.yaml          # 配置文件
├── templates/                 # 文案模板
├── requirements.txt
└── README.md
```

## 💻 核心代码实现

### 1. 主程序控制器
```python
# src/main.py
import asyncio
import logging
from app_controller import AppController
from product_analyzer import ProductAnalyzer
from comment_generator import CommentGenerator
from comment_publisher import CommentPublisher
from gui import CommentAssistantGUI
from database import Database

class CommentAssistant:
    def __init__(self):
        self.app_controller = AppController()
        self.product_analyzer = ProductAnalyzer()
        self.comment_generator = CommentGenerator()
        self.comment_publisher = CommentPublisher()
        self.database = Database()
        self.gui = CommentAssistantGUI(self)
        self.running = False
        self.current_task = None
    
    def start_batch_task(self, product_urls, comment_types):
        """开始批量任务"""
        try:
            # 连接APP
            if not self.app_controller.connect():
                raise Exception("无法连接到APP")
            
            self.running = True
            self.current_task = {
                'product_urls': product_urls,
                'comment_types': comment_types,
                'total': len(product_urls),
                'completed': 0,
                'errors': 0
            }
            
            # 启动任务处理
            self.process_products()
            
        except Exception as e:
            logging.error(f"启动批量任务失败: {e}")
            self.gui.show_error(f"启动失败: {e}")
    
    def process_products(self):
        """处理商品列表"""
        for i, product_url in enumerate(self.current_task['product_urls']):
            if not self.running:
                break
            
            try:
                # 更新进度
                self.gui.update_progress(i + 1, self.current_task['total'])
                
                # 导航到商品页面
                if not self.app_controller.navigate_to_product(product_url):
                    self.current_task['errors'] += 1
                    continue
                
                # 提取商品信息
                product_info = self.product_analyzer.extract_product_info()
                if not product_info:
                    self.current_task['errors'] += 1
                    continue
                
                # 生成评论文案
                comments = self.comment_generator.generate_comments(
                    product_info, 
                    self.current_task['comment_types']
                )
                
                # 发布评论
                success_count = self.comment_publisher.publish_comments(
                    comments, product_info['id']
                )
                
                # 保存记录
                self.database.save_product_task(
                    product_url, product_info, comments, success_count
                )
                
                self.current_task['completed'] += 1
                
                # 任务间隔
                time.sleep(random.uniform(30, 60))  # 30-60秒间隔
                
            except Exception as e:
                logging.error(f"处理商品失败 {product_url}: {e}")
                self.current_task['errors'] += 1
        
        # 任务完成
        self.finish_task()
    
    def finish_task(self):
        """完成任务"""
        self.running = False
        
        # 生成任务报告
        report = {
            'total': self.current_task['total'],
            'completed': self.current_task['completed'],
            'errors': self.current_task['errors'],
            'success_rate': self.current_task['completed'] / self.current_task['total']
        }
        
        self.gui.show_task_report(report)
        self.current_task = None

if __name__ == "__main__":
    assistant = CommentAssistant()
    assistant.gui.run()
```

### 2. APP控制器
```python
# src/app_controller.py
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
import time
import logging

class AppController:
    def __init__(self):
        self.driver = None
        self.desired_caps = {
            'platformName': 'Android',
            'automationName': 'UiAutomator2',
            'appPackage': 'com.taobao.idlefish',
            'appActivity': '.maincontainer.activity.MainActivity',
            'noReset': True,  # 保持登录状态
            'newCommandTimeout': 300,
            'settings[waitForIdleTimeout]': 100
        }
    
    def connect(self, device_id=None):
        """连接到APP"""
        try:
            if device_id:
                self.desired_caps['udid'] = device_id
            
            self.driver = webdriver.Remote(
                'http://localhost:4723/wd/hub',
                self.desired_caps
            )
            
            # 设置隐式等待
            self.driver.implicitly_wait(10)
            
            # 等待APP完全加载
            time.sleep(3)
            
            # 验证APP是否正常
            if self.verify_app_ready():
                logging.info("成功连接到APP")
                return True
            else:
                raise Exception("APP未正确加载")
                
        except Exception as e:
            logging.error(f"连接APP失败: {e}")
            return False
    
    def verify_app_ready(self):
        """验证APP是否就绪"""
        try:
            # 检查是否存在主要导航元素
            tab_elements = self.driver.find_elements(
                AppiumBy.XPATH, 
                "//android.widget.TabWidget//android.widget.TextView"
            )
            
            return len(tab_elements) > 0
            
        except:
            return False
    
    def navigate_to_product(self, product_url):
        """导航到商品页面"""
        try:
            # 方法1: 通过URL scheme
            if product_url.startswith('http'):
                # 提取商品ID
                product_id = self.extract_product_id(product_url)
                scheme_url = f"fleamarket://item?id={product_id}"
                self.driver.get(scheme_url)
            else:
                # 直接使用URL
                self.driver.get(product_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 验证商品页面加载成功
            if self.verify_product_page():
                return True
            else:
                # 方法2: 通过搜索导航
                return self.navigate_by_search(product_url)
                
        except Exception as e:
            logging.error(f"导航到商品页面失败: {e}")
            return False
    
    def verify_product_page(self):
        """验证商品页面"""
        try:
            # 检查商品标题元素
            title_element = self.driver.find_element(
                AppiumBy.XPATH,
                "//android.widget.TextView[contains(@resource-id,'title')]"
            )
            
            return title_element is not None
            
        except:
            return False
    
    def navigate_by_search(self, product_url):
        """通过搜索导航到商品"""
        try:
            # 点击搜索按钮
            search_btn = self.driver.find_element(
                AppiumBy.ID, "com.taobao.idlefish:id/search_btn"
            )
            search_btn.click()
            
            # 输入商品URL或关键词
            search_input = self.driver.find_element(
                AppiumBy.ID, "com.taobao.idlefish:id/search_input"
            )
            search_input.send_keys(product_url)
            
            # 点击搜索
            search_confirm = self.driver.find_element(
                AppiumBy.ID, "com.taobao.idlefish:id/search_confirm"
            )
            search_confirm.click()
            
            time.sleep(3)
            return True
            
        except Exception as e:
            logging.error(f"搜索导航失败: {e}")
            return False
    
    def extract_product_id(self, url):
        """提取商品ID"""
        import re
        pattern = r'item/(\d+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def scroll_page(self, direction='down', distance=1000):
        """滚动页面"""
        try:
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            if direction == 'down':
                self.driver.swipe(width//2, height*0.8, width//2, height*0.2)
            elif direction == 'up':
                self.driver.swipe(width//2, height*0.2, width//2, height*0.8)
                
            time.sleep(1)
            return True
            
        except Exception as e:
            logging.error(f"滚动页面失败: {e}")
            return False
    
    def take_screenshot(self, filename):
        """截图"""
        try:
            self.driver.save_screenshot(filename)
            return True
        except Exception as e:
            logging.error(f"截图失败: {e}")
            return False
    
    def quit(self):
        """退出驱动"""
        if self.driver:
            self.driver.quit()
            self.driver = None
```

### 3. 商品信息分析器
```python
# src/product_analyzer.py
from appium.webdriver.common.appiumby import AppiumBy
import time
import logging
import re

class ProductAnalyzer:
    def __init__(self, app_controller):
        self.app = app_controller
        self.driver = app_controller.driver
    
    def extract_product_info(self):
        """提取商品信息"""
        try:
            product_info = {}
            
            # 提取商品标题
            product_info['title'] = self.extract_title()
            
            # 提取价格
            product_info['price'] = self.extract_price()
            
            # 提取描述
            product_info['description'] = self.extract_description()
            
            # 提取卖家信息
            product_info['seller'] = self.extract_seller_info()
            
            # 提取商品状态
            product_info['condition'] = self.extract_condition()
            
            # 提取位置信息
            product_info['location'] = self.extract_location()
            
            # 提取现有评论
            product_info['existing_comments'] = self.extract_existing_comments()
            
            # 生成商品ID
            product_info['id'] = self.generate_product_id(product_info)
            
            logging.info(f"成功提取商品信息: {product_info['title']}")
            return product_info
            
        except Exception as e:
            logging.error(f"提取商品信息失败: {e}")
            return None
    
    def extract_title(self):
        """提取商品标题"""
        try:
            # 尝试多种选择器
            selectors = [
                "//android.widget.TextView[contains(@resource-id,'title')]",
                "//android.widget.TextView[contains(@text,'')][@index='0']",
                "//*[contains(@class,'TextView')][1]"
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, selector)
                    text = element.text.strip()
                    if text and len(text) > 5:  # 确保是有意义的标题
                        return text
                except:
                    continue
            
            return "未知商品"
            
        except Exception as e:
            logging.error(f"提取标题失败: {e}")
            return "未知商品"
    
    def extract_price(self):
        """提取价格"""
        try:
            # 寻找包含¥符号的元素
            price_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView[contains(@text,'¥')]"
            )
            
            for element in price_elements:
                text = element.text
                # 提取数字价格
                price_match = re.search(r'¥(\d+(?:\.\d{2})?)', text)
                if price_match:
                    return float(price_match.group(1))
            
            return 0.0
            
        except Exception as e:
            logging.error(f"提取价格失败: {e}")
            return 0.0
    
    def extract_description(self):
        """提取商品描述"""
        try:
            # 滚动到描述部分
            self.app.scroll_page('down')
            time.sleep(2)
            
            # 查找描述文本
            desc_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView"
            )
            
            # 合并描述文本，过滤掉短文本
            descriptions = []
            for element in desc_elements:
                text = element.text.strip()
                if text and len(text) > 10 and not self.is_ui_element(text):
                    descriptions.append(text)
            
            return ' '.join(descriptions[:3])  # 取前3段描述
            
        except Exception as e:
            logging.error(f"提取描述失败: {e}")
            return ""
    
    def extract_seller_info(self):
        """提取卖家信息"""
        try:
            # 查找卖家名称
            seller_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView[contains(@resource-id,'seller') or contains(@resource-id,'user')]"
            )
            
            for element in seller_elements:
                text = element.text.strip()
                if text and not text.isdigit():
                    return text
            
            return "未知卖家"
            
        except Exception as e:
            logging.error(f"提取卖家信息失败: {e}")
            return "未知卖家"
    
    def extract_condition(self):
        """提取商品成色"""
        try:
            # 查找成色相关文本
            condition_keywords = ['全新', '几乎全新', '轻微使用痕迹', '明显使用痕迹']
            
            all_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView"
            )
            
            for element in all_elements:
                text = element.text.strip()
                for keyword in condition_keywords:
                    if keyword in text:
                        return keyword
            
            return "未知成色"
            
        except Exception as e:
            logging.error(f"提取成色失败: {e}")
            return "未知成色"
    
    def extract_location(self):
        """提取位置信息"""
        try:
            # 查找位置元素
            location_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView[contains(@text,'市') or contains(@text,'区') or contains(@text,'县')]"
            )
            
            for element in location_elements:
                text = element.text.strip()
                if '市' in text or '区' in text:
                    return text
            
            return "未知位置"
            
        except Exception as e:
            logging.error(f"提取位置失败: {e}")
            return "未知位置"
    
    def extract_existing_comments(self, limit=5):
        """提取现有评论"""
        try:
            # 滚动到评论区
            self.scroll_to_comments()
            
            comment_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.LinearLayout[contains(@resource-id,'comment')]"
            )
            
            comments = []
            for element in comment_elements[:limit]:
                try:
                    # 提取评论内容
                    content_elem = element.find_element(
                        AppiumBy.XPATH,
                        ".//android.widget.TextView"
                    )
                    
                    comment_text = content_elem.text.strip()
                    if comment_text and len(comment_text) > 3:
                        comments.append(comment_text)
                        
                except:
                    continue
            
            return comments
            
        except Exception as e:
            logging.error(f"提取现有评论失败: {e}")
            return []
    
    def scroll_to_comments(self):
        """滚动到评论区"""
        try:
            # 多次向下滚动寻找评论区
            for _ in range(3):
                self.app.scroll_page('down')
                time.sleep(1)
                
                # 检查是否找到评论区
                comment_indicators = [
                    "//android.widget.TextView[contains(@text,'评论')]",
                    "//android.widget.TextView[contains(@text,'留言')]",
                    "//*[contains(@resource-id,'comment')]"
                ]
                
                for indicator in comment_indicators:
                    try:
                        self.driver.find_element(AppiumBy.XPATH, indicator)
                        return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            logging.error(f"滚动到评论区失败: {e}")
            return False
    
    def is_ui_element(self, text):
        """判断是否为UI元素文本"""
        ui_texts = [
            '立即购买', '加入购物车', '收藏', '分享', '评论', '点赞',
            '查看详情', '联系卖家', '举报', '取消', '确定'
        ]
        
        return any(ui_text in text for ui_text in ui_texts)
    
    def generate_product_id(self, product_info):
        """生成商品ID"""
        import hashlib
        
        content = f"{product_info.get('title', '')}{product_info.get('price', 0)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def analyze_market_position(self, product_info):
        """分析市场定位"""
        try:
            analysis = {
                'price_level': self.categorize_price(product_info['price']),
                'condition_score': self.score_condition(product_info['condition']),
                'description_quality': self.score_description(product_info['description']),
                'competition_level': len(product_info.get('existing_comments', []))
            }
            
            return analysis
            
        except Exception as e:
            logging.error(f"市场定位分析失败: {e}")
            return {}
    
    def categorize_price(self, price):
        """价格分类"""
        if price <= 50:
            return "低价"
        elif price <= 200:
            return "中低价"
        elif price <= 500:
            return "中价"
        elif price <= 1000:
            return "中高价"
        else:
            return "高价"
    
    def score_condition(self, condition):
        """成色评分"""
        condition_scores = {
            "全新": 5,
            "几乎全新": 4,
            "轻微使用痕迹": 3,
            "明显使用痕迹": 2
        }
        return condition_scores.get(condition, 1)
    
    def score_description(self, description):
        """描述质量评分"""
        if len(description) > 100:
            return 5
        elif len(description) > 50:
            return 4
        elif len(description) > 20:
            return 3
        else:
            return 2
```

### 4. AI评论生成器
```python
# src/comment_generator.py
import aiohttp
import asyncio
import random
import logging
from ai_client import DeepSeekClient

class CommentGenerator:
    def __init__(self):
        self.ai_client = DeepSeekClient()
        self.comment_types = {
            'inquiry': '询价型评论',
            'interest': '感兴趣型评论',
            'comparison': '对比咨询型评论',
            'compliment': '夸赞型评论',
            'concern': '关注型评论'
        }
    
    def generate_comments(self, product_info, comment_types, count=3):
        """生成多种类型评论"""
        try:
            all_comments = []
            
            for comment_type in comment_types:
                comments = self.generate_type_comments(
                    product_info, comment_type, count
                )
                all_comments.extend(comments)
            
            # 去重和质量过滤
            filtered_comments = self.filter_comments(all_comments)
            
            logging.info(f"生成评论数量: {len(filtered_comments)}")
            return filtered_comments
            
        except Exception as e:
            logging.error(f"生成评论失败: {e}")
            return []
    
    def generate_type_comments(self, product_info, comment_type, count=3):
        """生成特定类型评论"""
        try:
            prompt = self.build_comment_prompt(product_info, comment_type)
            
            # 调用AI生成
            response = asyncio.run(
                self.ai_client.generate_content(prompt, max_tokens=200)
            )
            
            # 解析生成的评论
            comments = self.parse_generated_comments(response, comment_type)
            
            return comments[:count]
            
        except Exception as e:
            logging.error(f"生成{comment_type}评论失败: {e}")
            return []
    
    def build_comment_prompt(self, product_info, comment_type):
        """构建评论生成提示词"""
        base_context = f"""
        商品信息：
        标题：{product_info.get('title', '未知商品')}
        价格：¥{product_info.get('price', 0)}
        成色：{product_info.get('condition', '未知')}
        卖家：{product_info.get('seller', '未知卖家')}
        位置：{product_info.get('location', '未知位置')}
        描述：{product_info.get('description', '')[:100]}
        现有评论：{product_info.get('existing_comments', [])[:3]}
        """
        
        if comment_type == 'inquiry':
            prompt = base_context + """
            请生成3条询价型评论，要求：
            1. 语气自然友善，像真实买家
            2. 体现对商品的兴趣和价格敏感
            3. 每条评论10-25字
            4. 避免过分直接砍价
            5. 可以询问细节或议价空间
            
            示例格式：
            1. 这个价格还能优惠一些吗？东西看起来不错
            2. 包邮吗？可以小刀一下吗？
            3. 能便宜点吗？诚心想要
            """
        
        elif comment_type == 'interest':
            prompt = base_context + """
            请生成3条感兴趣型评论，要求：
            1. 表达对商品的兴趣和购买意向
            2. 语气积极正面
            3. 每条评论8-20字
            4. 可以询问使用情况或细节
            
            示例格式：
            1. 这个还在吗？很感兴趣
            2. 东西看起来不错，用了多久？
            3. 正好需要这个，质量怎么样？
            """
        
        elif comment_type == 'comparison':
            prompt = base_context + """
            请生成3条对比咨询型评论，要求：
            1. 询问商品细节和与其他商品的对比
            2. 显示专业的购买眼光
            3. 每条评论15-30字
            4. 体现对商品的深入了解
            
            示例格式：
            1. 这个和XX品牌的有什么区别？功能一样吗？
            2. 这款比新的便宜多少？成色看起来很好
            3. 和同类产品相比优势在哪里？
            """
        
        elif comment_type == 'compliment':
            prompt = base_context + """
            请生成3条夸赞型评论，要求：
            1. 夸赞商品或卖家
            2. 语气真诚自然
            3. 每条评论8-18字
            4. 可以夸商品保养好或价格合理
            
            示例格式：
            1. 保养得真好，卖家很用心
            2. 这个价格很合理，良心卖家
            3. 东西看起来跟新的一样
            """
        
        elif comment_type == 'concern':
            prompt = base_context + """
            请生成3条关注型评论，要求：
            1. 表达关注和后续联系意向
            2. 语气友善
            3. 每条评论8-15字
            4. 暗示可能购买
            
            示例格式：
            1. 先关注一下，考虑考虑
            2. 已关注，有优惠记得通知
            3. 收藏了，过两天联系
            """
        
        return prompt
    
    def parse_generated_comments(self, response, comment_type):
        """解析AI生成的评论"""
        try:
            comments = []
            lines = response.split('\n')
            
            for line in lines:
                line = line.strip()
                
                # 移除序号和格式符号
                import re
                cleaned = re.sub(r'^\d+\.\s*', '', line)
                cleaned = re.sub(r'^[-•]\s*', '', cleaned)
                cleaned = cleaned.strip()
                
                # 验证评论质量
                if self.validate_comment(cleaned):
                    comments.append({
                        'content': cleaned,
                        'type': comment_type,
                        'length': len(cleaned)
                    })
            
            return comments
            
        except Exception as e:
            logging.error(f"解析评论失败: {e}")
            return []
    
    def validate_comment(self, comment):
        """验证评论质量"""
        if not comment or len(comment) < 5:
            return False
        
        if len(comment) > 50:
            return False
        
        # 过滤重复内容
        if comment.count('。') > 2:
            return False
        
        # 过滤不当内容
        inappropriate_words = ['垃圾', '骗子', '假货', '差评']
        if any(word in comment for word in inappropriate_words):
            return False
        
        return True
    
    def filter_comments(self, comments):
        """过滤和去重评论"""
        try:
            # 去重
            seen_contents = set()
            filtered = []
            
            for comment in comments:
                content = comment['content']
                if content not in seen_contents:
                    seen_contents.add(content)
                    filtered.append(comment)
            
            # 按类型平衡
            balanced = self.balance_comment_types(filtered)
            
            # 随机排序
            random.shuffle(balanced)
            
            return balanced[:10]  # 最多返回10条
            
        except Exception as e:
            logging.error(f"过滤评论失败: {e}")
            return comments
    
    def balance_comment_types(self, comments):
        """平衡不同类型评论数量"""
        type_groups = {}
        for comment in comments:
            comment_type = comment['type']
            if comment_type not in type_groups:
                type_groups[comment_type] = []
            type_groups[comment_type].append(comment)
        
        balanced = []
        max_per_type = 3
        
        for comment_type, type_comments in type_groups.items():
            balanced.extend(type_comments[:max_per_type])
        
        return balanced
    
    def customize_comment_style(self, comment, style='friendly'):
        """自定义评论风格"""
        styles = {
            'friendly': {'suffix': '~', 'emoji': '😊'},
            'professional': {'suffix': '。', 'emoji': ''},
            'casual': {'suffix': '哈哈', 'emoji': '😄'},
            'polite': {'suffix': '，谢谢', 'emoji': '🙏'}
        }
        
        if style in styles:
            style_config = styles[style]
            # 这里可以根据风格调整评论
            pass
        
        return comment
```

### 5. 评论发布器
```python
# src/comment_publisher.py
from appium.webdriver.common.appiumby import AppiumBy
import time
import random
import logging

class CommentPublisher:
    def __init__(self, app_controller):
        self.app = app_controller
        self.driver = app_controller.driver
        self.anti_detection = {
            'min_interval': 15,  # 最小间隔15秒
            'max_interval': 45,  # 最大间隔45秒
            'typing_speed': (50, 150),  # 打字速度区间(毫秒)
            'scroll_before_comment': True,  # 评论前滚动
            'random_pause': True  # 随机暂停
        }
    
    def publish_comments(self, comments, product_id):
        """发布评论列表"""
        try:
            success_count = 0
            
            for i, comment in enumerate(comments):
                if self.publish_single_comment(comment, product_id):
                    success_count += 1
                    logging.info(f"评论发布成功: {comment['content']}")
                else:
                    logging.error(f"评论发布失败: {comment['content']}")
                
                # 发布间隔控制
                if i < len(comments) - 1:  # 不是最后一条
                    interval = random.randint(
                        self.anti_detection['min_interval'],
                        self.anti_detection['max_interval']
                    )
                    time.sleep(interval)
            
            return success_count
            
        except Exception as e:
            logging.error(f"批量发布评论失败: {e}")
            return 0
    
    def publish_single_comment(self, comment, product_id):
        """发布单条评论"""
        try:
            # 1. 滚动到评论区
            if not self.navigate_to_comment_area():
                return False
            
            # 2. 点击评论输入框
            if not self.click_comment_input():
                return False
            
            # 3. 模拟人类打字
            if not self.simulate_typing(comment['content']):
                return False
            
            # 4. 提交评论
            if not self.submit_comment():
                return False
            
            # 5. 验证发布成功
            return self.verify_comment_posted()
            
        except Exception as e:
            logging.error(f"发布评论失败: {e}")
            return False
    
    def navigate_to_comment_area(self):
        """导航到评论区"""
        try:
            # 多次滚动寻找评论区
            for _ in range(5):
                # 查找评论相关元素
                comment_selectors = [
                    "//android.widget.EditText[contains(@hint,'评论')]",
                    "//android.widget.EditText[contains(@hint,'留言')]",
                    "//*[contains(@resource-id,'comment_input')]",
                    "//android.widget.TextView[contains(@text,'写评论')]",
                    "//android.widget.TextView[contains(@text,'说点什么')]"
                ]
                
                for selector in comment_selectors:
                    try:
                        element = self.driver.find_element(AppiumBy.XPATH, selector)
                        if element.is_displayed():
                            return True
                    except:
                        continue
                
                # 如果没找到，继续滚动
                self.app.scroll_page('down')
                time.sleep(2)
            
            # 尝试点击评论按钮或图标
            comment_buttons = [
                "//android.widget.TextView[contains(@text,'评论')]",
                "//android.widget.ImageView[contains(@resource-id,'comment')]"
            ]
            
            for button_selector in comment_buttons:
                try:
                    button = self.driver.find_element(AppiumBy.XPATH, button_selector)
                    button.click()
                    time.sleep(2)
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"导航到评论区失败: {e}")
            return False
    
    def click_comment_input(self):
        """点击评论输入框"""
        try:
            # 多种输入框选择器
            input_selectors = [
                "//android.widget.EditText[contains(@hint,'评论')]",
                "//android.widget.EditText[contains(@hint,'留言')]",
                "//android.widget.EditText[contains(@hint,'说点什么')]",
                "//*[contains(@resource-id,'comment_input')]",
                "//*[contains(@resource-id,'edit_text')]"
            ]
            
            for selector in input_selectors:
                try:
                    input_element = self.driver.find_element(AppiumBy.XPATH, selector)
                    if input_element.is_displayed() and input_element.is_enabled():
                        # 先点击激活
                        input_element.click()
                        time.sleep(1)
                        
                        # 清空现有内容
                        input_element.clear()
                        time.sleep(0.5)
                        
                        return True
                        
                except Exception as e:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"点击评论输入框失败: {e}")
            return False
    
    def simulate_typing(self, text):
        """模拟人类打字"""
        try:
            # 获取当前活动的输入框
            active_input = self.get_active_input_element()
            if not active_input:
                return False
            
            # 模拟逐字符输入
            for char in text:
                active_input.send_keys(char)
                
                # 随机打字间隔
                interval = random.randint(
                    self.anti_detection['typing_speed'][0],
                    self.anti_detection['typing_speed'][1]
                ) / 1000.0
                time.sleep(interval)
            
            # 随机暂停思考
            if self.anti_detection['random_pause']:
                pause_time = random.uniform(0.5, 2.0)
                time.sleep(pause_time)
            
            return True
            
        except Exception as e:
            logging.error(f"模拟打字失败: {e}")
            return False
    
    def get_active_input_element(self):
        """获取当前活动的输入元素"""
        try:
            # 查找已获得焦点的输入框
            focused_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.EditText[@focused='true']"
            )
            
            if focused_elements:
                return focused_elements[0]
            
            # 如果没有焦点元素，返回可见的输入框
            visible_inputs = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.EditText"
            )
            
            for input_elem in visible_inputs:
                if input_elem.is_displayed() and input_elem.is_enabled():
                    return input_elem
            
            return None
            
        except Exception as e:
            logging.error(f"获取活动输入元素失败: {e}")
            return None
    
    def submit_comment(self):
        """提交评论"""
        try:
            # 查找发送按钮
            submit_selectors = [
                "//android.widget.Button[contains(@text,'发送')]",
                "//android.widget.Button[contains(@text,'提交')]",
                "//android.widget.TextView[contains(@text,'发送')]",
                "//*[contains(@resource-id,'send') or contains(@resource-id,'submit')]",
                "//android.widget.ImageView[contains(@resource-id,'send')]"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        # 随机延迟后点击
                        delay = random.uniform(0.3, 1.0)
                        time.sleep(delay)
                        
                        submit_btn.click()
                        time.sleep(2)
                        
                        return True
                        
                except:
                    continue
            
            # 尝试回车键提交
            try:
                self.driver.press_keycode(66)  # Enter键
                time.sleep(2)
                return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logging.error(f"提交评论失败: {e}")
            return False
    
    def verify_comment_posted(self):
        """验证评论已发布"""
        try:
            # 等待一段时间让评论显示
            time.sleep(3)
            
            # 查找成功提示或评论显示
            success_indicators = [
                "//android.widget.TextView[contains(@text,'评论成功')]",
                "//android.widget.TextView[contains(@text,'发送成功')]",
                "//android.widget.Toast[contains(@text,'成功')]"
            ]
            
            for indicator in success_indicators:
                try:
                    self.driver.find_element(AppiumBy.XPATH, indicator)
                    return True
                except:
                    continue
            
            # 检查输入框是否已清空（暗示发送成功）
            input_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.EditText"
            )
            
            for input_elem in input_elements:
                if input_elem.text == "":
                    return True
            
            # 默认认为成功（某些版本可能没有明显提示）
            return True
            
        except Exception as e:
            logging.error(f"验证评论发布状态失败: {e}")
            return True  # 默认成功
    
    def handle_comment_restrictions(self):
        """处理评论限制"""
        try:
            # 检查是否有限制提示
            restriction_texts = [
                "评论太频繁",
                "请稍后再试",
                "评论失败",
                "网络异常",
                "系统维护"
            ]
            
            all_elements = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.TextView"
            )
            
            for element in all_elements:
                text = element.text
                for restriction in restriction_texts:
                    if restriction in text:
                        logging.warning(f"遇到评论限制: {text}")
                        return False
            
            return True
            
        except Exception as e:
            logging.error(f"处理评论限制失败: {e}")
            return True
    
    def get_comment_statistics(self):
        """获取评论统计"""
        try:
            stats = {
                'total_attempted': 0,
                'successful': 0,
                'failed': 0,
                'restricted': 0
            }
            
            # 从数据库获取统计信息
            from database import Database
            db = Database()
            stats = db.get_comment_statistics()
            
            return stats
            
        except Exception as e:
            logging.error(f"获取评论统计失败: {e}")
            return {}
```

### 6. GUI管理界面
```python
# src/gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import json
from datetime import datetime

class CommentAssistantGUI:
    def __init__(self, assistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.setup_ui()
        self.task_running = False
    
    def setup_ui(self):
        """设置界面"""
        self.root.title("评论助手")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 创建主布局
        self.create_main_layout()
        
        # 创建菜单栏
        self.create_menu()
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_main_layout(self):
        """创建主布局"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建笔记本控件（选项卡）
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 任务配置选项卡
        self.create_task_config_tab(notebook)
        
        # 运行监控选项卡
        self.create_monitoring_tab(notebook)
        
        # 数据统计选项卡
        self.create_statistics_tab(notebook)
        
        # 设置选项卡
        self.create_settings_tab(notebook)
    
    def create_task_config_tab(self, parent):
        """创建任务配置选项卡"""
        tab_frame = ttk.Frame(parent)
        parent.add(tab_frame, text="任务配置")
        
        # 商品URL输入区域
        url_frame = ttk.LabelFrame(tab_frame, text="商品URL列表")
        url_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # URL输入文本框
        self.url_text = scrolledtext.ScrolledText(
            url_frame, height=8, wrap=tk.WORD
        )
        self.url_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 批量导入按钮
        url_buttons_frame = ttk.Frame(url_frame)
        url_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            url_buttons_frame, text="从文件导入", 
            command=self.import_urls_from_file
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            url_buttons_frame, text="清空列表", 
            command=self.clear_url_list
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            url_buttons_frame, text="示例URL", 
            command=self.load_sample_urls
        ).pack(side=tk.LEFT, padx=5)
        
        # 评论类型选择
        comment_frame = ttk.LabelFrame(tab_frame, text="评论类型设置")
        comment_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 评论类型复选框
        self.comment_types = {
            'inquiry': tk.BooleanVar(value=True),
            'interest': tk.BooleanVar(value=True), 
            'comparison': tk.BooleanVar(value=False),
            'compliment': tk.BooleanVar(value=True),
            'concern': tk.BooleanVar(value=False)
        }
        
        comment_checkboxes = ttk.Frame(comment_frame)
        comment_checkboxes.pack(fill=tk.X, padx=5, pady=5)
        
        type_labels = {
            'inquiry': '询价型',
            'interest': '感兴趣型',
            'comparison': '对比咨询型',
            'compliment': '夸赞型',
            'concern': '关注型'
        }
        
        for i, (type_key, var) in enumerate(self.comment_types.items()):
            ttk.Checkbutton(
                comment_checkboxes,
                text=type_labels[type_key],
                variable=var
            ).grid(row=i//3, column=i%3, sticky=tk.W, padx=10, pady=2)
        
        # 任务控制区域
        control_frame = ttk.LabelFrame(tab_frame, text="任务控制")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        control_buttons = ttk.Frame(control_frame)
        control_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = ttk.Button(
            control_buttons, text="开始任务", 
            command=self.start_task, style="Accent.TButton"
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(
            control_buttons, text="停止任务", 
            command=self.stop_task, state="disabled"
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(
            control_buttons, text="暂停任务", 
            command=self.pause_task, state="disabled"
        )
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # 进度显示
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(progress_frame, text="任务进度:").pack(side=tk.LEFT)
        
        self.progress_var = tk.StringVar(value="0/0")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(side=tk.LEFT, padx=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, length=300, mode='determinate'
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def create_monitoring_tab(self, parent):
        """创建运行监控选项卡"""
        tab_frame = ttk.Frame(parent)
        parent.add(tab_frame, text="运行监控")
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(tab_frame, text="系统状态")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # 状态指标
        self.status_vars = {
            'app_status': tk.StringVar(value="未连接"),
            'current_product': tk.StringVar(value="无"),
            'comments_generated': tk.StringVar(value="0"),
            'comments_published': tk.StringVar(value="0")
        }
        
        status_labels = {
            'app_status': "APP状态:",
            'current_product': "当前商品:",
            'comments_generated': "生成评论:",
            'comments_published': "发布评论:"
        }
        
        for i, (key, label) in enumerate(status_labels.items()):
            ttk.Label(status_grid, text=label).grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=5, pady=2
            )
            ttk.Label(status_grid, textvariable=self.status_vars[key]).grid(
                row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=5, pady=2
            )
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(tab_frame, text="运行日志")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=15, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志控制按钮
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            log_buttons, text="清空日志", 
            command=self.clear_log
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            log_buttons, text="保存日志", 
            command=self.save_log
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            log_buttons, text="刷新", 
            command=self.refresh_log
        ).pack(side=tk.RIGHT, padx=5)
    
    def create_statistics_tab(self, parent):
        """创建数据统计选项卡"""
        tab_frame = ttk.Frame(parent)
        parent.add(tab_frame, text="数据统计")
        
        # 今日统计
        today_frame = ttk.LabelFrame(tab_frame, text="今日统计")
        today_frame.pack(fill=tk.X, padx=5, pady=5)
        
        today_grid = ttk.Frame(today_frame)
        today_grid.pack(fill=tk.X, padx=5, pady=5)
        
        self.today_stats = {
            'products_processed': tk.StringVar(value="0"),
            'comments_generated': tk.StringVar(value="0"),
            'comments_published': tk.StringVar(value="0"),
            'success_rate': tk.StringVar(value="0%")
        }
        
        today_labels = {
            'products_processed': "处理商品:",
            'comments_generated': "生成评论:",
            'comments_published': "发布评论:",
            'success_rate': "成功率:"
        }
        
        for i, (key, label) in enumerate(today_labels.items()):
            ttk.Label(today_grid, text=label).grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=10, pady=5
            )
            ttk.Label(today_grid, textvariable=self.today_stats[key]).grid(
                row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=10, pady=5
            )
        
        # 历史记录表格
        history_frame = ttk.LabelFrame(tab_frame, text="历史记录")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建表格
        columns = ("时间", "商品标题", "生成评论数", "发布成功数", "成功率")
        self.history_tree = ttk.Treeview(
            history_frame, columns=columns, show="headings", height=12
        )
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        
        # 滚动条
        history_scrollbar = ttk.Scrollbar(
            history_frame, orient=tk.VERTICAL, command=self.history_tree.yview
        )
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 统计按钮
        stats_buttons = ttk.Frame(history_frame)
        stats_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(
            stats_buttons, text="刷新数据", 
            command=self.refresh_statistics
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            stats_buttons, text="导出报告", 
            command=self.export_report
        ).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self, parent):
        """创建设置选项卡"""
        tab_frame = ttk.Frame(parent)
        parent.add(tab_frame, text="系统设置")
        
        # DeepSeek API设置
        api_frame = ttk.LabelFrame(tab_frame, text="DeepSeek API 配置")
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        api_grid = ttk.Frame(api_frame)
        api_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_grid, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.api_key_entry = ttk.Entry(api_grid, width=50, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(api_grid, text="测试连接", command=self.test_api_connection).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # 反检测设置
        detection_frame = ttk.LabelFrame(tab_frame, text="反检测设置")
        detection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        detection_grid = ttk.Frame(detection_frame)
        detection_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # 评论间隔设置
        ttk.Label(detection_grid, text="评论间隔(秒):").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        interval_frame = ttk.Frame(detection_grid)
        interval_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.min_interval = tk.IntVar(value=15)
        self.max_interval = tk.IntVar(value=45)
        
        ttk.Entry(interval_frame, textvariable=self.min_interval, width=8).pack(side=tk.LEFT)
        ttk.Label(interval_frame, text=" - ").pack(side=tk.LEFT)
        ttk.Entry(interval_frame, textvariable=self.max_interval, width=8).pack(side=tk.LEFT)
        
        # 每小时最大评论数
        ttk.Label(detection_grid, text="每小时最大评论数:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5
        )
        
        self.max_hourly_comments = tk.IntVar(value=20)
        ttk.Entry(detection_grid, textvariable=self.max_hourly_comments, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        # 设备设置
        device_frame = ttk.LabelFrame(tab_frame, text="设备设置")
        device_frame.pack(fill=tk.X, padx=5, pady=5)
        
        device_grid = ttk.Frame(device_frame)
        device_grid.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(device_grid, text="设备ID:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.device_id_entry = ttk.Entry(device_grid, width=30)
        self.device_id_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Button(device_grid, text="检测设备", command=self.detect_devices).grid(
            row=0, column=2, padx=5, pady=5
        )
        
        # 保存设置按钮
        ttk.Button(
            tab_frame, text="保存设置", 
            command=self.save_settings
        ).pack(pady=10)
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入URL列表", command=self.import_urls_from_file)
        file_menu.add_command(label="导出配置", command=self.export_config)
        file_menu.add_command(label="导入配置", command=self.import_config)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="清空数据库", command=self.clear_database)
        tools_menu.add_command(label="备份数据", command=self.backup_data)
        tools_menu.add_command(label="系统诊断", command=self.system_diagnosis)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    # 事件处理方法
    def start_task(self):
        """开始任务"""
        try:
            # 获取URL列表
            urls = self.get_url_list()
            if not urls:
                messagebox.showwarning("警告", "请先添加商品URL")
                return
            
            # 获取选中的评论类型
            selected_types = [
                type_key for type_key, var in self.comment_types.items() 
                if var.get()
            ]
            
            if not selected_types:
                messagebox.showwarning("警告", "请至少选择一种评论类型")
                return
            
            # 更新UI状态
            self.task_running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.pause_button.config(state="normal")
            
            # 在新线程中启动任务
            task_thread = threading.Thread(
                target=self.run_task_thread,
                args=(urls, selected_types),
                daemon=True
            )
            task_thread.start()
            
            self.add_log("任务已启动")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动任务失败: {e}")
    
    def stop_task(self):
        """停止任务"""
        self.task_running = False
        self.assistant.running = False
        
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.pause_button.config(state="disabled")
        
        self.add_log("任务已停止")
    
    def pause_task(self):
        """暂停任务"""
        # 实现暂停逻辑
        pass
    
    def run_task_thread(self, urls, comment_types):
        """在线程中运行任务"""
        try:
            self.assistant.start_batch_task(urls, comment_types)
        except Exception as e:
            self.root.after(0, lambda: self.show_error(f"任务执行错误: {e}"))
        finally:
            self.root.after(0, self.task_finished)
    
    def task_finished(self):
        """任务完成"""
        self.task_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.pause_button.config(state="disabled")
        self.add_log("任务已完成")
    
    def get_url_list(self):
        """获取URL列表"""
        text = self.url_text.get("1.0", tk.END).strip()
        urls = [url.strip() for url in text.split('\n') if url.strip()]
        return urls
    
    def update_progress(self, current, total):
        """更新进度"""
        self.progress_var.set(f"{current}/{total}")
        if total > 0:
            self.progress_bar['value'] = (current / total) * 100
    
    def add_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show_error(self, message):
        """显示错误"""
        messagebox.showerror("错误", message)
        self.add_log(f"错误: {message}")
    
    def show_task_report(self, report):
        """显示任务报告"""
        report_text = f"""
任务完成报告
════════════
处理商品总数: {report['total']}
成功处理数量: {report['completed']}
失败数量: {report['errors']}
成功率: {report['success_rate']:.1%}
"""
        messagebox.showinfo("任务报告", report_text)
    
    # 其他UI辅助方法
    def import_urls_from_file(self):
        """从文件导入URL"""
        filename = filedialog.askopenfilename(
            title="选择URL文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    urls = file.read()
                    self.url_text.delete("1.0", tk.END)
                    self.url_text.insert("1.0", urls)
                self.add_log(f"已导入URL文件: {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导入文件失败: {e}")
    
    def clear_url_list(self):
        """清空URL列表"""
        self.url_text.delete("1.0", tk.END)
    
    def load_sample_urls(self):
        """加载示例URL"""
        sample_urls = """https://www.xianyu.com/item/123456789
https://www.xianyu.com/item/987654321
https://www.xianyu.com/item/456789123"""
        
        self.url_text.delete("1.0", tk.END)
        self.url_text.insert("1.0", sample_urls)
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.task_running:
            if messagebox.askokcancel("退出", "任务正在运行，确定要退出吗？"):
                self.stop_task()
                self.root.after(1000, self.root.destroy)
        else:
            self.root.destroy()
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()
```

## 🚀 部署和运行

### 本地部署步骤

#### 1. 环境准备
```bash
# 确保Android设备已连接并开启调试
adb devices

# 启动Appium Server
appium

# 在新终端启动Python程序
cd xianyu-comment-assistant
python src/main.py
```

#### 2. 设备配置
```bash
# 真机配置步骤
1. 开启开发者选项
2. 启用USB调试
3. 安装APP并手动登录
4. 保持APP在前台或后台运行

# 模拟器配置（推荐夜神模拟器）
1. 下载安装夜神模拟器
2. 启动模拟器
3. 安装APP
4. 手动登录账号
```

#### 3. 使用流程
```
1. 手动登录APP
2. 启动助手程序
3. 配置DeepSeek API密钥
4. 添加商品URL列表
5. 选择评论类型
6. 开始执行任务
7. 监控运行状态
```

## 🔒 安全和风险控制

### 反检测机制
```python
# 反检测配置示例
ANTI_DETECTION_CONFIG = {
    # 时间控制
    'comment_interval': (15, 45),      # 评论间隔15-45秒
    'daily_limit': 100,                # 每日最大评论数
    'hourly_limit': 20,                # 每小时最大评论数
    
    # 行为模拟
    'typing_speed': (50, 150),         # 打字速度区间
    'scroll_before_comment': True,     # 评论前滚动
    'random_pause': True,              # 随机暂停
    
    # 内容多样化
    'content_variation': True,         # 内容变化
    'template_rotation': True,         # 模板轮换
}
```

### 安全措施
- **本地运行**：所有数据本地存储
- **手动登录**：用户完全控制账号
- **行为模拟**：模拟真实用户操作
- **频率控制**：避免过于频繁操作
- **异常监控**：自动检测和处理异常

## 📊 效果评估

### 关键指标
- **处理效率**：每小时处理商品数量
- **生成质量**：AI文案的相关性和自然度
- **发布成功率**：评论成功发布的比例
- **检测规避率**：成功避免平台检测的比例

### 优化建议
1. **定期更新**：保持与闲鱼APP版本同步
2. **模板优化**：根据效果调整文案模板
3. **行为调整**：观察平台变化调整操作策略
4. **数据分析**：分析发布效果优化投放策略

---

**系统版本**: v1.0.0  
**文档更新**: 2025-01-25  
**适用平台**: Android  
**技术支持**: 基于手动登录的本地运行架构