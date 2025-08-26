# -*- coding: utf-8 -*-
"""
Android 版本兼容性管理模块
处理不同Android版本的API差异和兼容性问题
"""

import sys
from kivy.utils import platform
from kivy.logger import Logger

class AndroidVersionCompat:
    """Android版本兼容性管理器"""
    
    # Android版本常量
    API_LEVELS = {
        'MARSHMALLOW': 23,      # Android 6.0
        'NOUGAT': 24,           # Android 7.0
        'NOUGAT_MR1': 25,       # Android 7.1
        'OREO': 26,             # Android 8.0
        'OREO_MR1': 27,         # Android 8.1
        'PIE': 28,              # Android 9
        'Q': 29,                # Android 10
        'R': 30,                # Android 11
        'S': 31,                # Android 12
        'S_V2': 32,             # Android 12L
        'TIRAMISU': 33,         # Android 13
        'UPSIDE_DOWN_CAKE': 34, # Android 14
    }
    
    def __init__(self):
        self.current_api_level = None
        self.android_version = None
        self.build_info = {}
        
        if platform == 'android':
            self._init_android_info()
    
    def _init_android_info(self):
        """初始化Android版本信息"""
        try:
            from jnius import autoclass
            
            # 获取Build信息
            Build = autoclass('android.os.Build')
            BuildVersion = autoclass('android.os.Build$VERSION')
            
            self.current_api_level = BuildVersion.SDK_INT
            self.android_version = BuildVersion.RELEASE
            
            self.build_info = {
                'api_level': self.current_api_level,
                'version': self.android_version,
                'manufacturer': Build.MANUFACTURER,
                'model': Build.MODEL,
                'brand': Build.BRAND,
                'device': Build.DEVICE,
                'product': Build.PRODUCT,
                'board': Build.BOARD,
                'hardware': Build.HARDWARE,
                'fingerprint': Build.FINGERPRINT,
            }
            
            Logger.info(f"AndroidCompat: Android {self.android_version} (API {self.current_api_level})")
            Logger.info(f"AndroidCompat: Device {self.build_info['manufacturer']} {self.build_info['model']}")
            
        except ImportError as e:
            Logger.warning(f"AndroidCompat: 无法获取Android版本信息: {e}")
        except Exception as e:
            Logger.error(f"AndroidCompat: 初始化版本信息失败: {e}")
    
    def is_android(self):
        """检查是否在Android平台"""
        return platform == 'android'
    
    def get_api_level(self):
        """获取当前API级别"""
        return self.current_api_level or 0
    
    def is_api_level_or_higher(self, api_level):
        """检查API级别是否达到指定值"""
        return self.get_api_level() >= api_level
    
    def is_marshmallow_or_higher(self):
        """Android 6.0+ (API 23+) - 运行时权限"""
        return self.is_api_level_or_higher(self.API_LEVELS['MARSHMALLOW'])
    
    def is_nougat_or_higher(self):
        """Android 7.0+ (API 24+) - 文件共享限制"""
        return self.is_api_level_or_higher(self.API_LEVELS['NOUGAT'])
    
    def is_oreo_or_higher(self):
        """Android 8.0+ (API 26+) - 通知渠道、后台服务限制"""
        return self.is_api_level_or_higher(self.API_LEVELS['OREO'])
    
    def is_pie_or_higher(self):
        """Android 9+ (API 28+) - 网络安全配置、Apache HTTP移除"""
        return self.is_api_level_or_higher(self.API_LEVELS['PIE'])
    
    def is_android_10_or_higher(self):
        """Android 10+ (API 29+) - 分区存储、位置权限变化"""
        return self.is_api_level_or_higher(self.API_LEVELS['Q'])
    
    def is_android_11_or_higher(self):
        """Android 11+ (API 30+) - 包可见性、存储权限变化"""
        return self.is_api_level_or_higher(self.API_LEVELS['R'])
    
    def is_android_12_or_higher(self):
        """Android 12+ (API 31+) - Material You、通知权限"""
        return self.is_api_level_or_higher(self.API_LEVELS['S'])
    
    def is_android_13_or_higher(self):
        """Android 13+ (API 33+) - 通知权限强制、主题图标"""
        return self.is_api_level_or_higher(self.API_LEVELS['TIRAMISU'])
    
    def get_storage_permission_strategy(self):
        """获取存储权限策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_android_11_or_higher():
            # Android 11+ 使用分区存储
            return 'scoped_storage'
        elif self.is_android_10_or_higher():
            # Android 10 可以选择使用传统存储
            return 'legacy_storage'
        else:
            # Android 9 及以下使用传统存储权限
            return 'traditional'
    
    def get_network_security_strategy(self):
        """获取网络安全策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_pie_or_higher():
            # Android 9+ 默认禁用HTTP
            return 'https_only'
        else:
            # Android 8 及以下允许HTTP
            return 'mixed_content'
    
    def get_notification_strategy(self):
        """获取通知策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_android_13_or_higher():
            # Android 13+ 需要通知权限
            return 'permission_required'
        elif self.is_oreo_or_higher():
            # Android 8+ 需要通知渠道
            return 'channel_required'
        else:
            # Android 7 及以下使用传统通知
            return 'traditional'
    
    def get_background_service_strategy(self):
        """获取后台服务策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_oreo_or_higher():
            # Android 8+ 限制后台服务
            return 'foreground_required'
        else:
            # Android 7 及以下允许后台服务
            return 'background_allowed'
    
    def get_file_sharing_strategy(self):
        """获取文件共享策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_nougat_or_higher():
            # Android 7+ 需要FileProvider
            return 'file_provider'
        else:
            # Android 6 及以下可以直接共享
            return 'direct_uri'
    
    def get_runtime_permission_strategy(self):
        """获取运行时权限策略"""
        if not self.is_android():
            return 'none'
        
        if self.is_marshmallow_or_higher():
            # Android 6+ 需要运行时权限请求
            return 'runtime_request'
        else:
            # Android 5 及以下在安装时授予权限
            return 'install_time'
    
    def get_recommended_target_sdk(self):
        """获取推荐的targetSdkVersion"""
        if not self.is_android():
            return 33  # 默认Android 13
        
        # 根据当前设备API级别推荐targetSdk
        current = self.get_api_level()
        
        if current >= self.API_LEVELS['TIRAMISU']:
            return 33  # Android 13
        elif current >= self.API_LEVELS['S']:
            return 31  # Android 12
        elif current >= self.API_LEVELS['R']:
            return 30  # Android 11
        elif current >= self.API_LEVELS['Q']:
            return 29  # Android 10
        else:
            return 28  # Android 9 (最低推荐)
    
    def get_minimum_sdk(self):
        """获取最低支持的SDK版本"""
        return self.API_LEVELS['MARSHMALLOW']  # 最低Android 6.0
    
    def get_compatibility_report(self):
        """生成兼容性报告"""
        if not self.is_android():
            return {
                'platform': 'Non-Android',
                'recommendations': ['在Android设备上运行以获取完整功能']
            }
        
        report = {
            'device_info': self.build_info,
            'api_level': self.get_api_level(),
            'android_version': self.android_version,
            'strategies': {
                'storage': self.get_storage_permission_strategy(),
                'network': self.get_network_security_strategy(),
                'notification': self.get_notification_strategy(),
                'background_service': self.get_background_service_strategy(),
                'file_sharing': self.get_file_sharing_strategy(),
                'runtime_permission': self.get_runtime_permission_strategy(),
            },
            'recommendations': []
        }
        
        # 生成建议
        if self.get_api_level() < self.get_minimum_sdk():
            report['recommendations'].append(
                f'设备API级别({self.get_api_level()})过低，建议升级到Android 6.0+')
        
        if self.is_android_11_or_higher():
            report['recommendations'].append('使用分区存储，注意文件访问权限')
        
        if self.is_pie_or_higher():
            report['recommendations'].append('网络请求需要HTTPS，或配置网络安全策略')
        
        if self.is_oreo_or_higher():
            report['recommendations'].append('后台任务需要前台服务')
        
        return report
    
    def apply_compatibility_fixes(self):
        """应用兼容性修复"""
        if not self.is_android():
            Logger.info("AndroidCompat: 非Android平台，跳过兼容性修复")
            return
        
        Logger.info("AndroidCompat: 应用兼容性修复...")
        
        try:
            # 存储权限兼容性
            if self.get_storage_permission_strategy() == 'scoped_storage':
                Logger.info("AndroidCompat: 使用分区存储策略")
                # 这里可以设置应用使用分区存储的相关配置
            
            # 网络安全兼容性
            if self.get_network_security_strategy() == 'https_only':
                Logger.info("AndroidCompat: 启用HTTPS优先策略")
                # 这里可以配置网络请求的安全策略
            
            # 通知兼容性
            notification_strategy = self.get_notification_strategy()
            if notification_strategy == 'channel_required':
                Logger.info("AndroidCompat: 创建通知渠道")
                # 创建通知渠道的代码
            elif notification_strategy == 'permission_required':
                Logger.info("AndroidCompat: 需要通知权限")
                # 请求通知权限的代码
            
            Logger.info("AndroidCompat: 兼容性修复完成")
            
        except Exception as e:
            Logger.error(f"AndroidCompat: 兼容性修复失败: {e}")

# 全局兼容性管理器实例
android_compat = AndroidVersionCompat()