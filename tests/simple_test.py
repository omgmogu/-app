#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本 - 避免编码问题
"""

import sys
import os
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

def run_keyword_tests():
    """运行关键词测试"""
    print("[INFO] 开始运行关键词循环搜索测试...")
    
    try:
        from test_keyword_search import run_keyword_search_tests
        success = run_keyword_search_tests()
        
        if success:
            print("[SUCCESS] 关键词测试通过!")
            return True
        else:
            print("[FAILED] 关键词测试失败!")
            return False
            
    except Exception as e:
        print(f"[ERROR] 测试异常: {e}")
        return False

def check_environment():
    """检查测试环境"""
    print("[CHECK] 检查测试环境...")
    
    issues = []
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        issues.append("Python版本过低，需要3.8+")
    
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
        print("[ERROR] 环境检查失败:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("[OK] 环境检查通过")
        return True

def main():
    """主函数"""
    start_time = time.time()
    
    print("=== 闲鱼自动评论助手 - 测试套件 ===")
    
    # 检查环境
    if not check_environment():
        print("[ERROR] 环境检查失败，退出测试")
        return False
    
    # 运行关键词测试
    success = run_keyword_tests()
    
    # 结果总结
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[DONE] 测试完成 - 耗时: {duration:.2f}秒")
    
    if success:
        print("[SUCCESS] 测试通过!")
    else:
        print("[FAILED] 测试失败!")
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)