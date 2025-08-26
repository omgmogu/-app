# -*- coding: utf-8 -*-
"""
移动端配置管理模块
简化版配置，适配移动端环境
"""

import os
import yaml
from pathlib import Path
from kivy.logger import Logger

class MobileConfig:
    """移动端配置管理器"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.config_file = self.config_dir / "mobile_settings.yaml"
        self.data_dir = Path(__file__).parent / "data"
        
        # 确保目录存在
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            "app": {
                "name": "闲鱼自动评论助手",
                "version": "1.0.0",
                "debug": False
            },
            "deepseek_api": {
                "api_key": "",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat",
                "max_tokens": 200,
                "temperature": 0.7,
                "timeout": 30
            },
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
                "hourly_limit": 20
            },
            "comment_templates": {
                "inquiry": [
                    "这个价格还能优惠一些吗？",
                    "包邮吗？可以小刀一下吗？",
                    "能便宜点吗？诚心想要",
                    "这个还有优惠空间吗？",
                    "还在吗？能便宜点不？"
                ],
                "interest": [
                    "这个还在吗？很感兴趣",
                    "东西看起来不错，用了多久？",
                    "正好需要这个，质量怎么样？",
                    "有意向，可以详细介绍一下吗？",
                    "看起来挺好的，成色如何？"
                ],
                "compliment": [
                    "保养得真好，卖家很用心",
                    "这个价格很合理，良心价",
                    "东西看起来跟新的一样",
                    "品相不错，值得购买",
                    "卖家很实诚，东西不错"
                ],
                "comparison": [
                    "和新的比起来性价比怎么样？",
                    "这款和XX品牌的有什么区别？",
                    "比全新便宜多少？功能一样吗？",
                    "这个型号和新版本差别大吗？",
                    "相比其他卖家，你这个有什么优势？"
                ],
                "concern": [
                    "先关注一下，考虑考虑",
                    "收藏了，过几天联系",
                    "关注了，有优惠通知我",
                    "先收藏，对比一下",
                    "看中了，再想想"
                ]
            },
            "database": {
                "path": "data/mobile_xianyu.db",
                "backup_enabled": True,
                "max_backups": 3
            },
            "logging": {
                "level": "INFO",
                "file_path": "data/logs/mobile_app.log",
                "max_file_size": "5MB",
                "backup_count": 3
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # 合并默认配置
                merged_config = self.default_config.copy()
                self._deep_merge(merged_config, config)
                return merged_config
            else:
                # 创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            Logger.error(f"MobileConfig: 加载配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """保存配置文件"""
        try:
            config_to_save = config or self.config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            Logger.info("MobileConfig: 配置已保存")
            return True
            
        except Exception as e:
            Logger.error(f"MobileConfig: 保存配置失败: {e}")
            return False
    
    def get(self, key, default=None):
        """获取配置值"""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            Logger.error(f"MobileConfig: 获取配置失败: {e}")
            return default
    
    def set(self, key, value):
        """设置配置值"""
        try:
            keys = key.split('.')
            current = self.config
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            return True
            
        except Exception as e:
            Logger.error(f"MobileConfig: 设置配置失败: {e}")
            return False
    
    def update_api_key(self, api_key):
        """更新API密钥"""
        try:
            self.set('deepseek_api.api_key', api_key)
            return self.save_config()
        except Exception as e:
            Logger.error(f"MobileConfig: 更新API密钥失败: {e}")
            return False
    
    def update_daily_limit(self, limit):
        """更新每日限制"""
        try:
            self.set('anti_detection.daily_limit', int(limit))
            return self.save_config()
        except Exception as e:
            Logger.error(f"MobileConfig: 更新每日限制失败: {e}")
            return False
    
    def get_data_path(self, filename=""):
        """获取数据目录路径"""
        if filename:
            return self.data_dir / filename
        return self.data_dir
    
    def _deep_merge(self, base, update):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

# 全局配置实例
mobile_config = MobileConfig()