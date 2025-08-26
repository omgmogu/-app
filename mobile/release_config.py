#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android应用发布和签名配置管理
处理APK签名、混淆、发布等配置
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib
import base64

class ReleaseConfigManager:
    """发布配置管理器"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.config_file = self.project_dir / 'release_config.json'
        self.keystore_dir = self.project_dir / 'keystore'
        
        # 确保目录存在
        self.keystore_dir.mkdir(exist_ok=True)
        
        # 默认配置
        self.default_config = {
            'app_info': {
                'package_name': 'com.xianyuassistant.xianyucommentassistant',
                'app_name': '闲鱼自动评论助手',
                'version_code': 1,
                'version_name': '1.0.0',
                'min_sdk_version': 23,
                'target_sdk_version': 33,
                'compile_sdk_version': 33
            },
            'signing': {
                'keystore_file': 'keystore/release.keystore',
                'keystore_password': '',
                'key_alias': 'xianyuassistant',
                'key_password': '',
                'validity_years': 25
            },
            'build': {
                'enable_proguard': False,
                'enable_r8': True,
                'shrink_resources': True,
                'zip_align': True,
                'generate_mapping': True
            },
            'distribution': {
                'enable_app_bundle': False,  # APK vs AAB
                'enable_multiple_apks': True,  # 按架构分包
                'architectures': ['armeabi-v7a', 'arm64-v8a'],
                'universal_apk': True
            },
            'security': {
                'enable_code_obfuscation': False,
                'enable_string_encryption': False,
                'enable_api_key_protection': True,
                'remove_debug_info': True
            },
            'optimization': {
                'enable_aapt2': True,
                'optimize_resources': True,
                'compress_native_libs': True,
                'enable_multidex': False
            }
        }
        
        # 加载配置
        self.config = self.load_config()
    
    def load_config(self):
        """加载发布配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置
                merged = self.default_config.copy()
                self._deep_merge(merged, config)
                return merged
            else:
                # 创建默认配置
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            print(f"加载发布配置失败: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """保存发布配置"""
        try:
            config_to_save = config or self.config
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            print("发布配置已保存")
            return True
            
        except Exception as e:
            print(f"保存发布配置失败: {e}")
            return False
    
    def generate_keystore(self, keystore_password=None, key_password=None):
        """生成签名密钥库"""
        try:
            signing_config = self.config['signing']
            keystore_path = self.project_dir / signing_config['keystore_file']
            
            # 如果密钥库已存在，询问是否覆盖
            if keystore_path.exists():
                response = input(f"密钥库 {keystore_path} 已存在，是否覆盖？(y/N): ")
                if response.lower() != 'y':
                    print("跳过密钥库生成")
                    return str(keystore_path)
            
            # 生成随机密码（如果未提供）
            if not keystore_password:
                keystore_password = self._generate_password(16)
                print(f"生成的密钥库密码: {keystore_password}")
            
            if not key_password:
                key_password = self._generate_password(16)
                print(f"生成的密钥密码: {key_password}")
            
            # 构建keytool命令
            cmd = [
                'keytool',
                '-genkey',
                '-v',
                '-keystore', str(keystore_path),
                '-alias', signing_config['key_alias'],
                '-keyalg', 'RSA',
                '-keysize', '2048',
                '-validity', str(signing_config['validity_years'] * 365),
                '-storepass', keystore_password,
                '-keypass', key_password,
                '-dname', 'CN=XianyuAssistant,OU=Development,O=XianyuAssistant,L=Unknown,ST=Unknown,C=CN'
            ]
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ 密钥库生成成功: {keystore_path}")
                
                # 更新配置中的密码
                self.config['signing']['keystore_password'] = keystore_password
                self.config['signing']['key_password'] = key_password
                self.save_config()
                
                # 显示密钥库信息
                self.show_keystore_info(keystore_path, keystore_password)
                
                return str(keystore_path)
            else:
                print(f"❌ 密钥库生成失败: {result.stderr}")
                return None
                
        except FileNotFoundError:
            print("❌ keytool 未找到，请确保 Java JDK 已正确安装并添加到 PATH")
            return None
        except Exception as e:
            print(f"❌ 生成密钥库异常: {e}")
            return None
    
    def show_keystore_info(self, keystore_path, keystore_password):
        """显示密钥库信息"""
        try:
            cmd = [
                'keytool',
                '-list',
                '-v',
                '-keystore', str(keystore_path),
                '-storepass', keystore_password
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📋 密钥库信息:")
                print(result.stdout)
            else:
                print(f"❌ 获取密钥库信息失败: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 显示密钥库信息异常: {e}")
    
    def validate_keystore(self):
        """验证密钥库"""
        try:
            signing_config = self.config['signing']
            keystore_path = self.project_dir / signing_config['keystore_file']
            
            if not keystore_path.exists():
                print(f"❌ 密钥库文件不存在: {keystore_path}")
                return False
            
            # 检查密码是否正确
            if not signing_config['keystore_password']:
                print("❌ 密钥库密码未配置")
                return False
            
            cmd = [
                'keytool',
                '-list',
                '-keystore', str(keystore_path),
                '-storepass', signing_config['keystore_password'],
                '-alias', signing_config['key_alias']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 密钥库验证成功")
                return True
            else:
                print(f"❌ 密钥库验证失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 验证密钥库异常: {e}")
            return False
    
    def get_buildozer_config_updates(self):
        """获取buildozer配置更新"""
        app_config = self.config['app_info']
        signing_config = self.config['signing']
        build_config = self.config['build']
        
        updates = {
            # 应用信息
            'title': app_config['app_name'],
            'package.name': app_config['package_name'].split('.')[-1],
            'package.domain': '.'.join(app_config['package_name'].split('.')[:-1]),
            'version': app_config['version_name'],
            
            # Android配置
            'android.api': app_config['compile_sdk_version'],
            'android.minapi': app_config['min_sdk_version'],
            'android.ndk': '25b',
            'android.sdk': '33',
            
            # 架构支持
            'android.archs': ', '.join(self.config['distribution']['architectures']),
            
            # 签名配置（仅Release模式）
            'android.release_artifact': 'aab' if self.config['distribution']['enable_app_bundle'] else 'apk',
        }
        
        # 如果有签名配置，添加签名相关配置
        if signing_config['keystore_password'] and Path(self.project_dir / signing_config['keystore_file']).exists():
            updates.update({
                'android.release_keystore': signing_config['keystore_file'],
                'android.release_keyalias': signing_config['key_alias'],
                'android.release_keystore_passwd': signing_config['keystore_password'],
                'android.release_key_passwd': signing_config['key_password'],
            })
        
        return updates
    
    def update_buildozer_spec(self):
        """更新buildozer.spec文件"""
        try:
            spec_file = self.project_dir / 'buildozer.spec'
            
            if not spec_file.exists():
                print("❌ buildozer.spec 文件不存在")
                return False
            
            # 读取现有配置
            with open(spec_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 获取更新配置
            updates = self.get_buildozer_config_updates()
            
            # 更新配置行
            updated_lines = []
            updated_keys = set()
            
            for line in lines:
                line_updated = False
                for key, value in updates.items():
                    if line.strip().startswith(f'{key} =') or line.strip().startswith(f'#{key} ='):
                        updated_lines.append(f'{key} = {value}\n')
                        updated_keys.add(key)
                        line_updated = True
                        break
                
                if not line_updated:
                    updated_lines.append(line)
            
            # 添加未找到的配置项
            for key, value in updates.items():
                if key not in updated_keys:
                    updated_lines.append(f'{key} = {value}\n')
            
            # 写回文件
            with open(spec_file, 'w', encoding='utf-8') as f:
                f.writelines(updated_lines)
            
            print("✅ buildozer.spec 已更新")
            return True
            
        except Exception as e:
            print(f"❌ 更新 buildozer.spec 失败: {e}")
            return False
    
    def increment_version(self, increment_type='patch'):
        """增加版本号"""
        try:
            version_parts = self.config['app_info']['version_name'].split('.')
            major, minor, patch = map(int, version_parts)
            
            if increment_type == 'major':
                major += 1
                minor = 0
                patch = 0
            elif increment_type == 'minor':
                minor += 1
                patch = 0
            else:  # patch
                patch += 1
            
            new_version = f"{major}.{minor}.{patch}"
            self.config['app_info']['version_name'] = new_version
            self.config['app_info']['version_code'] += 1
            
            self.save_config()
            print(f"✅ 版本已更新: {new_version} (code: {self.config['app_info']['version_code']})")
            
        except Exception as e:
            print(f"❌ 更新版本失败: {e}")
    
    def generate_release_notes(self):
        """生成发布说明"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            version = self.config['app_info']['version_name']
            version_code = self.config['app_info']['version_code']
            
            notes = f"""# 闲鱼自动评论助手 v{version} 发布说明

## 版本信息
- 版本号: {version} (Build {version_code})
- 发布时间: {timestamp}
- 最低Android版本: {self.config['app_info']['min_sdk_version']} (Android 6.0)
- 目标Android版本: {self.config['app_info']['target_sdk_version']}

## 新功能
- 多关键词循环搜索功能
- 智能评论生成和发布
- 实时任务监控
- 完整的历史记录管理

## 技术特性
- 基于Kivy框架开发的原生Android应用
- 支持Android 6.0 - 14.0
- 完整的权限管理和兼容性适配
- 本地化数据存储和隐私保护

## 安装要求
- Android 6.0+ (API 23+)
- 至少50MB存储空间
- 网络连接（可选，用于AI功能）

## 安全说明
- 本应用仅供学习研究使用
- 所有数据本地存储，不上传用户信息
- 请遵守相关平台服务条款

---
生成时间: {timestamp}
"""
            
            notes_file = self.project_dir / f'RELEASE_NOTES_v{version}.md'
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(notes)
            
            print(f"✅ 发布说明已生成: {notes_file}")
            return str(notes_file)
            
        except Exception as e:
            print(f"❌ 生成发布说明失败: {e}")
            return None
    
    def _generate_password(self, length=16):
        """生成随机密码"""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _deep_merge(self, base, update):
        """深度合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

def main():
    """命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Android应用发布配置管理")
    parser.add_argument('--generate-keystore', action='store_true', 
                       help='生成签名密钥库')
    parser.add_argument('--validate-keystore', action='store_true', 
                       help='验证签名密钥库')
    parser.add_argument('--update-buildozer', action='store_true', 
                       help='更新buildozer配置')
    parser.add_argument('--increment-version', choices=['major', 'minor', 'patch'], 
                       help='增加版本号')
    parser.add_argument('--generate-notes', action='store_true', 
                       help='生成发布说明')
    
    args = parser.parse_args()
    
    manager = ReleaseConfigManager()
    
    if args.generate_keystore:
        manager.generate_keystore()
    
    if args.validate_keystore:
        manager.validate_keystore()
    
    if args.update_buildozer:
        manager.update_buildozer_spec()
    
    if args.increment_version:
        manager.increment_version(args.increment_version)
    
    if args.generate_notes:
        manager.generate_release_notes()
    
    if not any(vars(args).values()):
        print("使用 --help 查看可用命令")

if __name__ == '__main__':
    main()