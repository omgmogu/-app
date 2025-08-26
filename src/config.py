# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 配置管理模块
专门针对闲鱼APP的配置设定
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

class Config:
    """配置管理类"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，默认为config/settings.yaml
        """
        if config_path is None:
            self.config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        else:
            self.config_path = Path(config_path)
            
        self.config_data = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f) or {}
            else:
                # 如果配置文件不存在，创建默认配置
                self.create_default_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.create_default_config()
    
    def save_config(self):
        """保存配置到文件"""
        try:
            # 确保配置目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def create_default_config(self):
        """创建闲鱼APP的默认配置"""
        self.config_data = {
            # 闲鱼APP相关配置
            "xianyu_app": {
                "package_name": "com.taobao.idlefish",
                "main_activity": ".maincontainer.activity.MainActivity",
                "app_name": "闲鱼",
                "version_check": True,
                "wait_timeout": 30
            },
            
            # Appium连接配置
            "appium": {
                "server_url": "http://localhost:4723/wd/hub",
                "desired_caps": {
                    "platformName": "Android",
                    "automationName": "UiAutomator2",
                    "appPackage": "com.taobao.idlefish",
                    "appActivity": ".maincontainer.activity.MainActivity",
                    "noReset": True,
                    "newCommandTimeout": 300,
                    "settings[waitForIdleTimeout]": 100,
                    "unicodeKeyboard": True,
                    "resetKeyboard": True
                },
                "implicit_wait": 10,
                "page_load_timeout": 30
            },
            
            # DeepSeek API配置
            "deepseek_api": {
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "max_tokens": 200,
                "temperature": 0.7,
                "timeout": 30,
                "retry_count": 3
            },
            
            # 反检测配置
            "anti_detection": {
                "comment_interval": {
                    "min": 15,
                    "max": 45
                },
                "typing_speed": {
                    "min": 50,
                    "max": 150
                },
                "daily_limit": 100,
                "hourly_limit": 20,
                "scroll_before_comment": True,
                "random_pause": True,
                "human_behavior": {
                    "mouse_move_delay": [0.1, 0.3],
                    "click_delay": [0.2, 0.8],
                    "scroll_delay": [1.0, 3.0]
                }
            },
            
            # 闲鱼界面元素定位配置
            "xianyu_selectors": {
                # 搜索相关
                "search_btn": "com.taobao.idlefish:id/search_btn",
                "search_input": "com.taobao.idlefish:id/search_input",
                "search_confirm": "com.taobao.idlefish:id/search_confirm",
                
                # 商品页面相关
                "product_title": "//android.widget.TextView[contains(@resource-id,'title')]",
                "product_price": "//android.widget.TextView[contains(@text,'¥')]",
                "product_seller": "//android.widget.TextView[contains(@resource-id,'seller')]",
                "product_location": "//android.widget.TextView[contains(@text,'市') or contains(@text,'区')]",
                
                # 评论相关
                "comment_input": [
                    "//android.widget.EditText[contains(@hint,'评论')]",
                    "//android.widget.EditText[contains(@hint,'留言')]",
                    "//android.widget.EditText[contains(@hint,'说点什么')]"
                ],
                "comment_send": [
                    "//android.widget.Button[contains(@text,'发送')]",
                    "//android.widget.TextView[contains(@text,'发送')]",
                    "//android.widget.ImageView[contains(@resource-id,'send')]"
                ],
                "comment_area": "//android.widget.TextView[contains(@text,'评论')]",
                
                # 导航相关
                "back_btn": "//android.widget.ImageView[contains(@resource-id,'back')]",
                "home_tab": "//android.widget.TextView[@text='首页']",
                "message_tab": "//android.widget.TextView[@text='消息']"
            },
            
            # 评论模板配置
            "comment_templates": {
                "inquiry": [
                    "这个价格还能优惠一些吗？",
                    "包邮吗？可以小刀一下吗？",
                    "能便宜点吗？诚心想要",
                    "这个还有优惠空间吗？"
                ],
                "interest": [
                    "这个还在吗？很感兴趣",
                    "东西看起来不错，用了多久？",
                    "正好需要这个，质量怎么样？",
                    "有意向，可以详细介绍一下吗？"
                ],
                "compliment": [
                    "保养得真好，卖家很用心",
                    "这个价格很合理，良心卖家",
                    "东西看起来跟新的一样",
                    "品相不错，值得购买"
                ]
            },
            
            # 数据库配置
            "database": {
                "products_db": "data/products.db",
                "comments_db": "data/comments.db",
                "backup_interval": 24,  # 小时
                "max_backup_count": 7
            },
            
            # 日志配置
            "logging": {
                "level": "INFO",
                "file_path": "data/logs/xianyu_assistant.log",
                "max_file_size": "10MB",
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            
            # 系统监控配置
            "monitoring": {
                "check_interval": 5,  # 秒
                "memory_threshold": 500,  # MB
                "cpu_threshold": 80,  # %
                "error_threshold": 10  # 连续错误次数
            }
        }
        
        # 保存默认配置
        self.save_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键（如：'appium.server_url'）
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config_data
        
        # 导航到最后一级的父字典
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def get_xianyu_selectors(self) -> Dict[str, Any]:
        """获取闲鱼界面选择器配置"""
        return self.get("xianyu_selectors", {})
    
    def get_appium_caps(self) -> Dict[str, Any]:
        """获取Appium连接配置"""
        return self.get("appium.desired_caps", {})
    
    def get_anti_detection_config(self) -> Dict[str, Any]:
        """获取反检测配置"""
        return self.get("anti_detection", {})
    
    def get_comment_templates(self, comment_type: str = None) -> Dict[str, Any]:
        """
        获取评论模板
        
        Args:
            comment_type: 评论类型，如不指定则返回所有模板
            
        Returns:
            评论模板字典或列表
        """
        templates = self.get("comment_templates", {})
        if comment_type:
            return templates.get(comment_type, [])
        return templates
    
    def update_api_key(self, api_key: str):
        """更新DeepSeek API密钥"""
        self.set("deepseek_api.api_key", api_key)
        self.save_config()
    
    def is_api_configured(self) -> bool:
        """检查API是否已配置"""
        api_key = self.get("deepseek_api.api_key", "")
        return bool(api_key and api_key.strip())


# 全局配置实例
config = Config()

# 便捷访问函数
def get_config(key: str, default: Any = None) -> Any:
    """获取配置值的便捷函数"""
    return config.get(key, default)

def set_config(key: str, value: Any):
    """设置配置值的便捷函数"""
    config.set(key, value)
    config.save_config()

def get_xianyu_app_config() -> Dict[str, Any]:
    """获取闲鱼APP配置"""
    return config.get("xianyu_app", {})