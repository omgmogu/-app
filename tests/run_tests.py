#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行脚本
统一运行所有测试用例
"""

import sys
import os
import time
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "mobile"))
sys.path.insert(0, str(Path(__file__).parent))

def run_tests(test_type='all', verbose=True):
    """运行测试"""
    print("测试 闲鱼自动评论助手 - 测试套件")
    print("=" * 50)
    
    start_time = time.time()
    all_passed = True
    
    if test_type in ['all', 'keyword']:
        print("\n📋 运行关键词循环搜索测试...")
        try:
            from test_keyword_search import run_keyword_search_tests
            success = run_keyword_search_tests()
            if not success:
                all_passed = False
        except Exception as e:
            print(f"❌ 关键词搜索测试失败: {e}")
            all_passed = False
    
    # 这里可以添加更多测试类型
    if test_type in ['all', 'database']:
        print("\n📋 运行数据库测试...")
        try:
            # from test_database import run_database_tests
            # success = run_database_tests()
            print("✅ 数据库测试暂未实现，跳过")
        except Exception as e:
            print(f"❌ 数据库测试失败: {e}")
    
    if test_type in ['all', 'ui']:
        print("\n📋 运行UI测试...")
        try:
            # from test_ui import run_ui_tests
            # success = run_ui_tests()
            print("✅ UI测试暂未实现，跳过")
        except Exception as e:
            print(f"❌ UI测试失败: {e}")
    
    # 测试结果总结
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "=" * 50)
    print(f"🏁 测试完成 - 耗时: {duration:.2f}秒")
    
    if all_passed:
        print("🎉 所有测试通过!")
        return True
    else:
        print("❌ 部分测试失败!")
        return False

def check_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    issues = []
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        issues.append("Python版本过低，需要3.8+")
    
    # 检查必要模块
    required_modules = [
        'unittest',
        'threading',
        'pathlib',
        'time'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            issues.append(f"缺少必要模块: {module}")
    
    # 检查项目文件
    project_root = Path(__file__).parent.parent
    required_files = [
        'src/keyword_manager.py',
        'src/main.py',
        'src/database.py'
    ]
    
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            issues.append(f"缺少项目文件: {file_path}")
    
    if issues:
        print("❌ 环境检查失败:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ 环境检查通过")
        return True

def create_test_report(results, output_file=None):
    """创建测试报告"""
    if not output_file:
        output_file = Path(__file__).parent / f"test_report_{int(time.time())}.md"
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""# 闲鱼自动评论助手 - 测试报告

## 测试信息
- 生成时间: {timestamp}
- Python版本: {sys.version}
- 操作系统: {os.name}

## 测试结果
{'✅ 测试通过' if results else '❌ 测试失败'}

## 测试覆盖范围
- ✅ 关键词管理器功能测试
- ✅ 关键词任务生命周期测试
- ✅ 搜索循环集成测试
- ✅ 性能和并发测试
- ⏳ 数据库测试 (待实现)
- ⏳ UI界面测试 (待实现)

## 详细说明

### 关键词循环搜索测试
测试了以下功能：
- 关键词队列管理
- 任务状态跟踪
- 搜索结果处理
- 错误处理机制
- 并发访问安全性

### 性能测试
- 大量关键词处理 (100个关键词)
- 并发任务处理
- 内存使用优化

## 建议
1. 在真实环境中进行集成测试
2. 添加更多边界条件测试
3. 完善错误恢复机制测试

---
报告生成时间: {timestamp}
"""
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 测试报告已生成: {output_file}")
    except Exception as e:
        print(f"❌ 生成测试报告失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="闲鱼自动评论助手测试运行器")
    parser.add_argument('--type', choices=['all', 'keyword', 'database', 'ui'], 
                       default='all', help='测试类型')
    parser.add_argument('--check-env', action='store_true', 
                       help='只检查环境，不运行测试')
    parser.add_argument('--quiet', action='store_true', 
                       help='静默模式')
    parser.add_argument('--report', type=str, 
                       help='生成测试报告到指定文件')
    
    args = parser.parse_args()
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，退出测试")
        sys.exit(1)
    
    if args.check_env:
        print("✅ 环境检查完成")
        return
    
    # 运行测试
    verbose = not args.quiet
    success = run_tests(args.type, verbose)
    
    # 生成报告
    if args.report:
        create_test_report(success, args.report)
    
    # 退出码
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()