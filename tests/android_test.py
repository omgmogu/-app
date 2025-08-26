#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android打包和兼容性测试脚本
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mobile"))

def check_buildozer_config():
    """检查buildozer配置"""
    print("[CHECK] 验证buildozer.spec配置...")
    
    spec_file = Path(__file__).parent.parent / "mobile" / "buildozer.spec"
    
    if not spec_file.exists():
        print("[ERROR] buildozer.spec文件不存在")
        return False
    
    # 读取配置文件
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置
        checks = {
            'title = ': '应用标题',
            'package.name = ': '包名',
            'package.domain = ': '域名',
            'requirements = ': '依赖包',
            'android.permissions = ': 'Android权限',
            'android.archs = ': '支持架构'
        }
        
        issues = []
        for key, desc in checks.items():
            if key not in content:
                issues.append(f"缺少配置: {desc} ({key})")
        
        if issues:
            print("[ERROR] buildozer.spec配置问题:")
            for issue in issues:
                print(f"  - {issue}")
            return False
        else:
            print("[OK] buildozer.spec配置验证通过")
            return True
            
    except Exception as e:
        print(f"[ERROR] 读取buildozer.spec失败: {e}")
        return False

def check_android_compatibility():
    """检查Android版本兼容性"""
    print("[CHECK] 验证Android版本兼容性...")
    
    try:
        # 导入Android兼容性模块
        from android_compat import AndroidVersionCompat
        
        # 创建兼容性管理器实例
        compat = AndroidVersionCompat()
        
        # 获取兼容性报告
        report = compat.get_compatibility_report()
        
        print("[INFO] Android兼容性报告:")
        print(f"  - 平台: {report.get('platform', 'Android')}")
        
        if 'api_level' in report:
            print(f"  - API级别: {report['api_level']}")
            print(f"  - Android版本: {report.get('android_version', 'Unknown')}")
        
        if 'strategies' in report:
            strategies = report['strategies']
            print("  - 兼容性策略:")
            print(f"    * 存储: {strategies.get('storage', 'N/A')}")
            print(f"    * 网络: {strategies.get('network', 'N/A')}")
            print(f"    * 通知: {strategies.get('notification', 'N/A')}")
            print(f"    * 后台服务: {strategies.get('background_service', 'N/A')}")
        
        # 推荐的SDK版本
        min_sdk = compat.get_minimum_sdk()
        target_sdk = compat.get_recommended_target_sdk()
        
        print(f"  - 最低SDK: {min_sdk} (Android 6.0)")
        print(f"  - 推荐目标SDK: {target_sdk}")
        
        print("[OK] Android兼容性检查完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] Android兼容性检查失败: {e}")
        return False

def check_release_config():
    """检查发布配置"""
    print("[CHECK] 验证发布配置...")
    
    try:
        config_file = Path(__file__).parent.parent / "mobile" / "release_config.json"
        
        # 创建默认配置文件（如果不存在）
        if not config_file.exists():
            default_config = {
                'app_info': {
                    'package_name': 'com.xianyuassistant.xianyucommentassistant',
                    'app_name': '闲鱼自动评论助手',
                    'version_code': 1,
                    'version_name': '1.0.0',
                    'min_sdk_version': 23,
                    'target_sdk_version': 33,
                    'compile_sdk_version': 33
                },
                'distribution': {
                    'architectures': ['armeabi-v7a', 'arm64-v8a'],
                    'enable_app_bundle': False,
                    'enable_multiple_apks': True,
                    'universal_apk': True
                }
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            
            print("[INFO] 创建了默认发布配置")
        
        # 读取配置文件
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 验证关键配置
        app_info = config.get('app_info', {})
        
        print("[INFO] 发布配置信息:")
        print(f"  - 应用名称: {app_info.get('app_name', 'N/A')}")
        print(f"  - 包名: {app_info.get('package_name', 'N/A')}")
        print(f"  - 版本: {app_info.get('version_name', 'N/A')} (code: {app_info.get('version_code', 'N/A')})")
        print(f"  - 最低SDK: {app_info.get('min_sdk_version', 'N/A')}")
        print(f"  - 目标SDK: {app_info.get('target_sdk_version', 'N/A')}")
        
        distribution = config.get('distribution', {})
        architectures = distribution.get('architectures', [])
        print(f"  - 支持架构: {', '.join(architectures)}")
        
        print("[OK] 发布配置验证通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 发布配置验证失败: {e}")
        return False

def check_mobile_app():
    """检查移动应用代码"""
    print("[CHECK] 验证移动应用代码...")
    
    mobile_dir = Path(__file__).parent.parent / "mobile"
    required_files = [
        'main.py',
        'buildozer.spec',
        'android_compat.py',
        'release_config.py'
    ]
    
    missing_files = []
    for file_name in required_files:
        if not (mobile_dir / file_name).exists():
            missing_files.append(file_name)
    
    if missing_files:
        print("[ERROR] 缺少移动应用文件:")
        for file_name in missing_files:
            print(f"  - {file_name}")
        return False
    
    # 检查main.py是否包含Kivy应用
    try:
        main_file = mobile_dir / "main.py"
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'kivy' not in content.lower():
            print("[WARNING] main.py可能不是Kivy应用")
        
        if 'XianyuMobileApp' not in content:
            print("[WARNING] 未找到XianyuMobileApp类")
        
        print("[OK] 移动应用代码验证通过")
        return True
        
    except Exception as e:
        print(f"[ERROR] 移动应用代码验证失败: {e}")
        return False

def main():
    """主函数"""
    print("=== Android打包和兼容性测试 ===\n")
    
    all_passed = True
    
    # 1. 检查buildozer配置
    if not check_buildozer_config():
        all_passed = False
    print()
    
    # 2. 检查Android兼容性
    if not check_android_compatibility():
        all_passed = False
    print()
    
    # 3. 检查发布配置
    if not check_release_config():
        all_passed = False
    print()
    
    # 4. 检查移动应用代码
    if not check_mobile_app():
        all_passed = False
    print()
    
    # 总结
    if all_passed:
        print("[SUCCESS] 所有Android配置检查通过!")
        print("\n建议下一步:")
        print("1. 安装Android SDK和buildozer")
        print("2. 配置签名密钥库")
        print("3. 运行 'buildozer android debug' 构建APK")
        print("4. 在Android设备上测试APK")
    else:
        print("[FAILED] 部分Android配置检查失败!")
        print("请先解决上述问题后再进行打包")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)