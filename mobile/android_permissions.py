# -*- coding: utf-8 -*-
"""
Android 权限管理模块
处理应用运行时权限请求和管理
"""

from kivy.utils import platform
from kivy.logger import Logger

# Android权限常量
class AndroidPermissions:
    """Android权限常量定义"""
    
    # 网络相关权限
    INTERNET = "android.permission.INTERNET"
    ACCESS_NETWORK_STATE = "android.permission.ACCESS_NETWORK_STATE"
    ACCESS_WIFI_STATE = "android.permission.ACCESS_WIFI_STATE"
    CHANGE_NETWORK_STATE = "android.permission.CHANGE_NETWORK_STATE"
    
    # 存储权限
    WRITE_EXTERNAL_STORAGE = "android.permission.WRITE_EXTERNAL_STORAGE"
    READ_EXTERNAL_STORAGE = "android.permission.READ_EXTERNAL_STORAGE"
    MANAGE_EXTERNAL_STORAGE = "android.permission.MANAGE_EXTERNAL_STORAGE"
    
    # 系统权限
    SYSTEM_ALERT_WINDOW = "android.permission.SYSTEM_ALERT_WINDOW"
    DISABLE_KEYGUARD = "android.permission.DISABLE_KEYGUARD"
    WAKE_LOCK = "android.permission.WAKE_LOCK"
    VIBRATE = "android.permission.VIBRATE"
    
    # 设备信息权限
    READ_PHONE_STATE = "android.permission.READ_PHONE_STATE"
    
    # 多媒体权限
    CAMERA = "android.permission.CAMERA"
    RECORD_AUDIO = "android.permission.RECORD_AUDIO"
    
    # 位置权限
    ACCESS_FINE_LOCATION = "android.permission.ACCESS_FINE_LOCATION"
    ACCESS_COARSE_LOCATION = "android.permission.ACCESS_COARSE_LOCATION"
    
    # 系统设置权限
    WRITE_SETTINGS = "android.permission.WRITE_SETTINGS"

class PermissionManager:
    """权限管理器"""
    
    def __init__(self):
        self.required_permissions = [
            AndroidPermissions.INTERNET,
            AndroidPermissions.ACCESS_NETWORK_STATE,
            AndroidPermissions.ACCESS_WIFI_STATE,
            AndroidPermissions.WRITE_EXTERNAL_STORAGE,
            AndroidPermissions.READ_EXTERNAL_STORAGE,
            AndroidPermissions.WAKE_LOCK,
            AndroidPermissions.SYSTEM_ALERT_WINDOW,
            AndroidPermissions.VIBRATE
        ]
        
        self.optional_permissions = [
            AndroidPermissions.MANAGE_EXTERNAL_STORAGE,
            AndroidPermissions.READ_PHONE_STATE,
            AndroidPermissions.WRITE_SETTINGS,
            AndroidPermissions.DISABLE_KEYGUARD
        ]
        
        # 权限状态缓存
        self.permission_status = {}
        
        # 初始化Android模块
        self.android_module = None
        self.activity = None
        
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission, check_permission
                from jnius import autoclass
                
                self.request_permissions = request_permissions
                self.Permission = Permission
                self.check_permission = check_permission
                
                # 获取Android Activity
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                self.activity = PythonActivity.mActivity
                
                Logger.info("PermissionManager: Android模块加载成功")
                
            except ImportError as e:
                Logger.warning(f"PermissionManager: Android模块加载失败: {e}")
    
    def is_android(self):
        """检查是否在Android平台运行"""
        return platform == 'android' and self.android_module is not None
    
    def check_permission(self, permission):
        """检查单个权限状态"""
        if not self.is_android():
            Logger.info(f"PermissionManager: 非Android平台，跳过权限检查: {permission}")
            return True
        
        try:
            if hasattr(self, 'check_permission'):
                result = self.check_permission(permission)
                self.permission_status[permission] = result
                Logger.info(f"PermissionManager: 权限 {permission} 状态: {result}")
                return result
            else:
                Logger.warning(f"PermissionManager: 无法检查权限 {permission}")
                return False
                
        except Exception as e:
            Logger.error(f"PermissionManager: 检查权限异常 {permission}: {e}")
            return False
    
    def check_all_permissions(self):
        """检查所有必需权限"""
        if not self.is_android():
            Logger.info("PermissionManager: 非Android平台，跳过权限检查")
            return True
        
        Logger.info("PermissionManager: 开始检查所有权限...")
        
        missing_permissions = []
        
        for permission in self.required_permissions:
            if not self.check_permission(permission):
                missing_permissions.append(permission)
        
        if missing_permissions:
            Logger.warning(f"PermissionManager: 缺失权限: {missing_permissions}")
            return False
        
        Logger.info("PermissionManager: 所有必需权限已授权")
        return True
    
    def request_permission(self, permission, callback=None):
        """请求单个权限"""
        if not self.is_android():
            Logger.info(f"PermissionManager: 非Android平台，跳过权限请求: {permission}")
            if callback:
                callback(permission, True)
            return
        
        try:
            Logger.info(f"PermissionManager: 请求权限: {permission}")
            
            def permission_callback(permissions, grant_results):
                """权限请求回调"""
                granted = len(grant_results) > 0 and grant_results[0]
                Logger.info(f"PermissionManager: 权限 {permission} 请求结果: {granted}")
                
                self.permission_status[permission] = granted
                
                if callback:
                    callback(permission, granted)
            
            if hasattr(self, 'request_permissions'):
                self.request_permissions([permission], permission_callback)
            else:
                Logger.error(f"PermissionManager: 无法请求权限 {permission}")
                if callback:
                    callback(permission, False)
                    
        except Exception as e:
            Logger.error(f"PermissionManager: 请求权限异常 {permission}: {e}")
            if callback:
                callback(permission, False)
    
    def request_all_permissions(self, callback=None):
        """请求所有必需权限"""
        if not self.is_android():
            Logger.info("PermissionManager: 非Android平台，跳过权限请求")
            if callback:
                callback(True)
            return
        
        Logger.info("PermissionManager: 请求所有必需权限...")
        
        permissions_to_request = []
        
        # 检查哪些权限需要请求
        for permission in self.required_permissions:
            if not self.check_permission(permission):
                permissions_to_request.append(permission)
        
        if not permissions_to_request:
            Logger.info("PermissionManager: 所有权限已授权")
            if callback:
                callback(True)
            return
        
        Logger.info(f"PermissionManager: 需要请求的权限: {permissions_to_request}")
        
        try:
            def permission_callback(permissions, grant_results):
                """批量权限请求回调"""
                all_granted = all(grant_results)
                Logger.info(f"PermissionManager: 批量权限请求结果: {all_granted}")
                
                # 更新权限状态
                for i, permission in enumerate(permissions):
                    granted = i < len(grant_results) and grant_results[i]
                    self.permission_status[permission] = granted
                    Logger.info(f"PermissionManager: {permission} = {granted}")
                
                if callback:
                    callback(all_granted)
            
            if hasattr(self, 'request_permissions'):
                self.request_permissions(permissions_to_request, permission_callback)
            else:
                Logger.error("PermissionManager: 无法批量请求权限")
                if callback:
                    callback(False)
                    
        except Exception as e:
            Logger.error(f"PermissionManager: 批量请求权限异常: {e}")
            if callback:
                callback(False)
    
    def get_permission_status(self):
        """获取所有权限状态"""
        return self.permission_status.copy()
    
    def get_missing_permissions(self):
        """获取缺失的权限列表"""
        missing = []
        
        for permission in self.required_permissions:
            if not self.permission_status.get(permission, False):
                missing.append(permission)
        
        return missing
    
    def show_permission_rationale(self, permission):
        """显示权限说明（需要在UI中实现）"""
        rationale_texts = {
            AndroidPermissions.INTERNET: "应用需要网络权限来调用AI接口和获取数据",
            AndroidPermissions.WRITE_EXTERNAL_STORAGE: "应用需要存储权限来保存日志和数据文件",
            AndroidPermissions.READ_EXTERNAL_STORAGE: "应用需要读取权限来访问配置文件",
            AndroidPermissions.WAKE_LOCK: "应用需要此权限来保持任务在后台运行",
            AndroidPermissions.SYSTEM_ALERT_WINDOW: "应用需要此权限来显示悬浮窗口",
            AndroidPermissions.ACCESS_NETWORK_STATE: "应用需要此权限来检测网络状态",
            AndroidPermissions.VIBRATE: "应用需要震动权限来提供操作反馈",
        }
        
        return rationale_texts.get(permission, f"应用需要权限: {permission}")
    
    def open_app_settings(self):
        """打开应用设置页面"""
        if not self.is_android():
            Logger.info("PermissionManager: 非Android平台，无法打开设置")
            return
        
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Uri = autoclass('android.net.Uri')
            Settings = autoclass('android.provider.Settings')
            
            intent = Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            intent.setData(Uri.parse(f"package:{self.activity.getPackageName()}"))
            self.activity.startActivity(intent)
            
            Logger.info("PermissionManager: 已打开应用设置页面")
            
        except Exception as e:
            Logger.error(f"PermissionManager: 打开设置页面失败: {e}")

# 全局权限管理器实例
permission_manager = PermissionManager()