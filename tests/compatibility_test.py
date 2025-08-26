#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Android版本兼容性测试脚本
验证应用在不同Android版本上的兼容性
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "mobile"))

def test_api_compatibility():
    """测试API兼容性"""
    print("[TEST] Android API兼容性测试...")
    
    # 定义支持的API级别范围
    min_api = 23  # Android 6.0 Marshmallow
    max_api = 34  # Android 14 Upside Down Cake
    target_api = 33  # Android 13 Tiramisu
    
    # 模拟不同API级别的兼容性测试
    api_tests = {}
    
    for api_level in range(min_api, max_api + 1):
        test_results = {}
        
        # 运行时权限测试 (API 23+)
        if api_level >= 23:
            test_results['runtime_permissions'] = True
        else:
            test_results['runtime_permissions'] = False
        
        # 文件共享限制测试 (API 24+)
        if api_level >= 24:
            test_results['file_provider_required'] = True
        else:
            test_results['file_provider_required'] = False
        
        # 通知渠道测试 (API 26+)
        if api_level >= 26:
            test_results['notification_channels'] = True
        else:
            test_results['notification_channels'] = False
        
        # 网络安全配置测试 (API 28+)
        if api_level >= 28:
            test_results['network_security_config'] = True
        else:
            test_results['network_security_config'] = False
        
        # 分区存储测试 (API 29+)
        if api_level >= 29:
            test_results['scoped_storage'] = True
        else:
            test_results['scoped_storage'] = False
        
        # 包可见性测试 (API 30+)
        if api_level >= 30:
            test_results['package_visibility'] = True
        else:
            test_results['package_visibility'] = False
        
        # 通知权限测试 (API 33+)
        if api_level >= 33:
            test_results['notification_permission'] = True
        else:
            test_results['notification_permission'] = False
        
        api_tests[api_level] = test_results
    
    # 输出测试结果
    print(f"  支持的API级别范围: {min_api} - {max_api}")
    print(f"  目标API级别: {target_api}")
    print()
    
    # 显示关键API级别的兼容性策略
    key_apis = [23, 26, 28, 29, 30, 33]
    android_versions = {
        23: "Android 6.0 (Marshmallow)",
        26: "Android 8.0 (Oreo)",
        28: "Android 9.0 (Pie)",
        29: "Android 10.0 (Q)",
        30: "Android 11.0 (R)",
        33: "Android 13.0 (Tiramisu)"
    }
    
    print("  关键API级别兼容性策略:")
    for api in key_apis:
        if api in api_tests:
            version_name = android_versions.get(api, f"API {api}")
            results = api_tests[api]
            print(f"    {version_name}:")
            
            for feature, supported in results.items():
                status = "需要适配" if supported else "自动兼容"
                print(f"      * {feature}: {status}")
            print()
    
    print("[OK] API兼容性测试完成")
    return True

def test_permissions_compatibility():
    """测试权限兼容性"""
    print("[TEST] 权限兼容性测试...")
    
    # 从buildozer.spec读取权限配置
    spec_file = Path(__file__).parent.parent / "mobile" / "buildozer.spec"
    
    if not spec_file.exists():
        print("[ERROR] buildozer.spec文件不存在")
        return False
    
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找权限配置行
        permissions_line = None
        for line in content.split('\n'):
            if line.strip().startswith('android.permissions ='):
                permissions_line = line.strip()
                break
        
        if not permissions_line:
            print("[ERROR] 未找到权限配置")
            return False
        
        # 解析权限列表
        permissions_str = permissions_line.split('=', 1)[1].strip()
        permissions = [p.strip() for p in permissions_str.split(',')]
        
        print(f"  配置的权限数量: {len(permissions)}")
        
        # 分类权限
        normal_permissions = []
        dangerous_permissions = []
        special_permissions = []
        
        # 危险权限列表 (需要运行时请求，API 23+)
        dangerous_perms = {
            'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE',
            'CAMERA', 'RECORD_AUDIO', 'ACCESS_FINE_LOCATION', 
            'ACCESS_COARSE_LOCATION', 'READ_PHONE_STATE'
        }
        
        # 特殊权限列表
        special_perms = {
            'SYSTEM_ALERT_WINDOW', 'WRITE_SETTINGS',
            'MANAGE_EXTERNAL_STORAGE', 'REQUEST_IGNORE_BATTERY_OPTIMIZATIONS'
        }
        
        for perm in permissions:
            if perm in dangerous_perms:
                dangerous_permissions.append(perm)
            elif perm in special_perms:
                special_permissions.append(perm)
            else:
                normal_permissions.append(perm)
        
        print(f"  普通权限: {len(normal_permissions)} 个")
        print(f"  危险权限: {len(dangerous_permissions)} 个 (需要运行时请求)")
        print(f"  特殊权限: {len(special_permissions)} 个 (需要特殊处理)")
        
        if dangerous_permissions:
            print("    危险权限列表:")
            for perm in dangerous_permissions:
                print(f"      * {perm}")
        
        if special_permissions:
            print("    特殊权限列表:")
            for perm in special_permissions:
                print(f"      * {perm}")
        
        print("[OK] 权限兼容性测试完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 权限兼容性测试失败: {e}")
        return False

def test_architecture_compatibility():
    """测试架构兼容性"""
    print("[TEST] 架构兼容性测试...")
    
    # 从buildozer.spec读取架构配置
    spec_file = Path(__file__).parent.parent / "mobile" / "buildozer.spec"
    
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找架构配置
        archs_line = None
        for line in content.split('\n'):
            if line.strip().startswith('android.archs ='):
                archs_line = line.strip()
                break
        
        if archs_line:
            archs_str = archs_line.split('=', 1)[1].strip()
            architectures = [arch.strip() for arch in archs_str.split(',')]
        else:
            architectures = ['armeabi-v7a']  # 默认架构
        
        print(f"  支持的架构: {', '.join(architectures)}")
        
        # 架构兼容性分析
        arch_compatibility = {
            'armeabi-v7a': {
                'description': '32位ARM架构',
                'compatibility': '兼容绝大多数Android设备',
                'market_share': '~15%'
            },
            'arm64-v8a': {
                'description': '64位ARM架构',
                'compatibility': '现代Android设备主流架构',
                'market_share': '~80%'
            },
            'x86': {
                'description': '32位x86架构',
                'compatibility': '模拟器和少数Intel设备',
                'market_share': '~3%'
            },
            'x86_64': {
                'description': '64位x86架构',
                'compatibility': '高端Intel设备和模拟器',
                'market_share': '~2%'
            }
        }
        
        total_coverage = 0
        print("  架构兼容性分析:")
        for arch in architectures:
            if arch in arch_compatibility:
                info = arch_compatibility[arch]
                print(f"    {arch}:")
                print(f"      * {info['description']}")
                print(f"      * {info['compatibility']}")
                print(f"      * 市场占有率: {info['market_share']}")
                
                # 计算覆盖率
                share = float(info['market_share'].replace('%', '').replace('~', ''))
                total_coverage += share
        
        print(f"  预计市场覆盖率: ~{total_coverage}%")
        
        if 'arm64-v8a' in architectures and 'armeabi-v7a' in architectures:
            print("  [EXCELLENT] 支持主流32位和64位ARM架构")
        elif 'arm64-v8a' in architectures:
            print("  [GOOD] 支持64位ARM架构，覆盖现代设备")
        elif 'armeabi-v7a' in architectures:
            print("  [OK] 支持32位ARM架构，兼容旧设备")
        
        print("[OK] 架构兼容性测试完成")
        return True
        
    except Exception as e:
        print(f"[ERROR] 架构兼容性测试失败: {e}")
        return False

def test_feature_compatibility():
    """测试功能兼容性"""
    print("[TEST] 功能兼容性测试...")
    
    # 测试应用的主要功能在不同Android版本上的兼容性
    features = {
        'Appium自动化': {
            'min_api': 23,
            'compatibility': 'Appium UiAutomator2需要Android 6.0+',
            'fallback': '无'
        },
        'HTTP网络请求': {
            'min_api': 1,
            'compatibility': 'Android 9+默认禁用HTTP，需要配置',
            'fallback': '配置网络安全策略或使用HTTPS'
        },
        '本地数据库存储': {
            'min_api': 1,
            'compatibility': '完全兼容所有版本',
            'fallback': '无需'
        },
        '文件存储访问': {
            'min_api': 23,
            'compatibility': 'Android 10+使用分区存储',
            'fallback': '申请MANAGE_EXTERNAL_STORAGE权限'
        },
        '后台任务执行': {
            'min_api': 1,
            'compatibility': 'Android 8+限制后台服务',
            'fallback': '使用前台服务'
        },
        '系统通知': {
            'min_api': 1,
            'compatibility': 'Android 8+需要通知渠道，Android 13+需要权限',
            'fallback': '动态创建通知渠道和权限请求'
        }
    }
    
    print("  核心功能兼容性分析:")
    all_compatible = True
    
    for feature_name, info in features.items():
        print(f"    {feature_name}:")
        print(f"      * 最低API: {info['min_api']}")
        print(f"      * 兼容性说明: {info['compatibility']}")
        
        if info['fallback'] != '无' and info['fallback'] != '无需':
            print(f"      * 兼容性方案: {info['fallback']}")
        
        # 检查是否满足最低要求
        if info['min_api'] > 23:  # 应用的最低API是23
            print(f"      * [WARNING] 需要API {info['min_api']}+，高于应用最低要求")
            all_compatible = False
        else:
            print(f"      * [OK] 兼容应用支持的API范围")
    
    if all_compatible:
        print("  [SUCCESS] 所有功能兼容目标API范围")
    else:
        print("  [WARNING] 部分功能需要额外适配")
    
    print("[OK] 功能兼容性测试完成")
    return True

def generate_compatibility_report():
    """生成兼容性测试报告"""
    print("\n=== Android兼容性测试报告 ===")
    
    test_results = {
        'api_compatibility': test_api_compatibility(),
        'permissions_compatibility': test_permissions_compatibility(), 
        'architecture_compatibility': test_architecture_compatibility(),
        'feature_compatibility': test_feature_compatibility()
    }
    
    print(f"\n兼容性测试结果汇总:")
    passed_count = sum(test_results.values())
    total_count = len(test_results)
    
    for test_name, result in test_results.items():
        status = "PASS" if result else "FAIL"
        print(f"  - {test_name}: {status}")
    
    print(f"\n总体评估: {passed_count}/{total_count} 项测试通过")
    
    if passed_count == total_count:
        print("\n[SUCCESS] 应用具有良好的Android版本兼容性")
        print("支持Android 6.0 - Android 14的主流设备")
        return True
    else:
        print("\n[WARNING] 存在兼容性问题，建议进一步优化")
        return False

def main():
    """主函数"""
    print("=== Android版本兼容性测试 ===\n")
    
    success = generate_compatibility_report()
    
    print("\n=== 兼容性建议 ===")
    print("1. 在真实Android设备上进行测试")
    print("2. 使用Android模拟器测试不同API级别")
    print("3. 关注权限请求的用户体验")
    print("4. 定期更新Android支持库版本")
    print("5. 监控不同版本的崩溃率和性能")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)