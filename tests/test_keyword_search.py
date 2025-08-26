#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词循环搜索功能测试
测试关键词管理、搜索循环、商品卡遍历等核心功能
"""

import sys
import unittest
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "mobile"))

try:
    from keyword_manager import KeywordManager, KeywordTask, KeywordStatus
    from main import XianyuCommentAssistant
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

class TestKeywordManager(unittest.TestCase):
    """关键词管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.keyword_manager = KeywordManager()
    
    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'keyword_manager'):
            self.keyword_manager.clear_completed_tasks()
    
    def test_add_single_keyword(self):
        """测试添加单个关键词"""
        keywords = ["手机"]
        result = self.keyword_manager.add_keywords(keywords, priority=5, max_products=30)
        
        self.assertTrue(result)
        self.assertEqual(self.keyword_manager.total_keywords, 1)
    
    def test_add_multiple_keywords(self):
        """测试添加多个关键词"""
        keywords = ["手机", "电脑", "相机", "耳机", "音响"]
        result = self.keyword_manager.add_keywords(keywords, priority=3, max_products=50)
        
        self.assertTrue(result)
        self.assertEqual(self.keyword_manager.total_keywords, 5)
    
    def test_keyword_priority_handling(self):
        """测试关键词优先级处理"""
        # 添加不同优先级的关键词
        self.keyword_manager.add_keywords(["低优先级"], priority=1)
        self.keyword_manager.add_keywords(["高优先级"], priority=10)
        self.keyword_manager.add_keywords(["中优先级"], priority=5)
        
        # 获取关键词（应该按优先级排序）
        first_task = self.keyword_manager.get_next_keyword()
        self.assertIsNotNone(first_task)
        self.assertEqual(first_task.keyword, "高优先级")
    
    def test_keyword_queue_operations(self):
        """测试关键词队列操作"""
        keywords = ["测试1", "测试2", "测试3"]
        self.keyword_manager.add_keywords(keywords)
        
        # 获取第一个关键词
        task1 = self.keyword_manager.get_next_keyword()
        self.assertIsNotNone(task1)
        self.assertEqual(task1.keyword, "测试1")
        self.assertEqual(task1.status, KeywordStatus.PROCESSING)
        
        # 完成当前关键词
        success = self.keyword_manager.complete_current_keyword()
        self.assertTrue(success)
        
        # 获取下一个关键词
        task2 = self.keyword_manager.get_next_keyword()
        self.assertIsNotNone(task2)
        self.assertEqual(task2.keyword, "测试2")
    
    def test_keyword_progress_tracking(self):
        """测试关键词进度跟踪"""
        self.keyword_manager.add_keywords(["进度测试"])
        task = self.keyword_manager.get_next_keyword()
        
        # 更新进度
        self.keyword_manager.update_current_progress(
            products_found=10,
            products_processed=5,
            comments_generated=8,
            comments_published=6
        )
        
        self.assertEqual(task.products_found, 10)
        self.assertEqual(task.products_processed, 5)
        self.assertEqual(task.comments_generated, 8)
        self.assertEqual(task.comments_published, 6)
    
    def test_keyword_failure_handling(self):
        """测试关键词失败处理"""
        self.keyword_manager.add_keywords(["失败测试"])
        task = self.keyword_manager.get_next_keyword()
        
        # 标记失败
        success = self.keyword_manager.fail_current_keyword("测试错误")
        self.assertTrue(success)
        self.assertEqual(task.status, KeywordStatus.FAILED)
    
    def test_empty_queue_handling(self):
        """测试空队列处理"""
        # 不添加任何关键词
        task = self.keyword_manager.get_next_keyword()
        self.assertIsNone(task)
        
        self.assertTrue(self.keyword_manager.is_empty())
    
    def test_queue_status_report(self):
        """测试队列状态报告"""
        keywords = ["状态1", "状态2", "状态3"]
        self.keyword_manager.add_keywords(keywords, max_products=25)
        
        status = self.keyword_manager.get_queue_status()
        
        self.assertIn('total_keywords', status)
        self.assertIn('processed_keywords', status)
        self.assertIn('pending_keywords', status)
        self.assertEqual(status['total_keywords'], 3)
        self.assertEqual(status['processed_keywords'], 0)

class TestKeywordTask(unittest.TestCase):
    """关键词任务测试"""
    
    def test_task_creation(self):
        """测试任务创建"""
        task = KeywordTask(
            keyword="创建测试",
            priority=5,
            max_products=100,
            enable_pagination=True,
            max_pages=3
        )
        
        self.assertEqual(task.keyword, "创建测试")
        self.assertEqual(task.priority, 5)
        self.assertEqual(task.max_products, 100)
        self.assertEqual(task.status, KeywordStatus.PENDING)
        self.assertTrue(task.enable_pagination)
        self.assertEqual(task.max_pages, 3)
    
    def test_task_lifecycle(self):
        """测试任务生命周期"""
        task = KeywordTask("生命周期测试")
        
        # 初始状态
        self.assertEqual(task.status, KeywordStatus.PENDING)
        self.assertIsNone(task.started_at)
        self.assertIsNone(task.completed_at)
        
        # 开始处理
        task.start_processing()
        self.assertEqual(task.status, KeywordStatus.PROCESSING)
        self.assertIsNotNone(task.started_at)
        
        # 完成处理
        time.sleep(0.1)  # 确保有时间差
        task.complete_processing()
        self.assertEqual(task.status, KeywordStatus.COMPLETED)
        self.assertIsNotNone(task.completed_at)
        
        # 检查时长
        duration = task.get_duration()
        self.assertIsNotNone(duration)
        self.assertGreater(duration, 0)
    
    def test_task_success_rate(self):
        """测试任务成功率计算"""
        task = KeywordTask("成功率测试")
        
        # 没有处理任何商品
        self.assertEqual(task.get_success_rate(), 0.0)
        
        # 处理一些商品
        task.products_processed = 10
        task.errors_count = 2
        
        expected_rate = (10 - 2) / 10 * 100  # 80%
        self.assertEqual(task.get_success_rate(), expected_rate)

class MockAppController:
    """模拟APP控制器"""
    
    def __init__(self):
        self.is_connected = True
        self.search_results = {
            "手机": ["手机1", "手机2", "手机3"],
            "电脑": ["电脑1", "电脑2"],
            "相机": ["相机1", "相机2", "相机3", "相机4"]
        }
        self.current_keyword = None
        self.current_product_index = 0
    
    def search_by_keyword(self, keyword):
        """模拟关键词搜索"""
        self.current_keyword = keyword
        self.current_product_index = 0
        return keyword in self.search_results
    
    def get_all_product_cards(self):
        """模拟获取商品卡"""
        if not self.current_keyword:
            return []
        
        products = self.search_results.get(self.current_keyword, [])
        return [f"card_{product}" for product in products]
    
    def click_product_card_by_index(self, index):
        """模拟点击商品卡"""
        if not self.current_keyword:
            return False
        
        products = self.search_results.get(self.current_keyword, [])
        return 0 <= index < len(products)
    
    def navigate_back_to_search_results(self):
        """模拟返回搜索结果"""
        return True
    
    def has_more_products(self):
        """模拟检查是否有更多商品"""
        return False  # 简化测试，不测试分页
    
    def scroll_to_load_more_products(self):
        """模拟滚动加载更多"""
        return False

class MockProductAnalyzer:
    """模拟商品分析器"""
    
    def extract_product_info(self):
        """模拟提取商品信息"""
        return {
            "title": "测试商品",
            "price": 99.99,
            "seller": "测试卖家",
            "location": "测试城市",
            "condition_score": 8
        }

class MockCommentGenerator:
    """模拟评论生成器"""
    
    def generate_comments(self, product_info, comment_types, count_per_type=2):
        """模拟生成评论"""
        comments = []
        for comment_type in comment_types:
            for i in range(count_per_type):
                comments.append({
                    "content": f"测试{comment_type}评论{i+1}",
                    "type": comment_type
                })
        return comments

class MockCommentPublisher:
    """模拟评论发布器"""
    
    def publish_comments(self, comments, product_id):
        """模拟发布评论"""
        # 模拟90%成功率
        successful = int(len(comments) * 0.9)
        return {
            "successful": successful,
            "failed": len(comments) - successful,
            "error": None
        }

class TestKeywordSearchIntegration(unittest.TestCase):
    """关键词搜索集成测试"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟组件
        self.mock_app_controller = MockAppController()
        self.mock_product_analyzer = MockProductAnalyzer()
        self.mock_comment_generator = MockCommentGenerator()
        self.mock_comment_publisher = MockCommentPublisher()
        
        # 创建主助手实例（不初始化真实组件）
        self.assistant = XianyuCommentAssistant()
        self.assistant.app_controller = self.mock_app_controller
        self.assistant.product_analyzer = self.mock_product_analyzer
        self.assistant.comment_generator = self.mock_comment_generator
        self.assistant.comment_publisher = self.mock_comment_publisher
    
    def test_single_keyword_processing(self):
        """测试单个关键词处理流程"""
        keywords = ["手机"]
        comment_types = ["inquiry", "interest"]
        
        # 模拟启动关键词任务
        success = self.assistant.keyword_manager.add_keywords(keywords, max_products=3)
        self.assertTrue(success)
        
        # 获取关键词任务
        task = self.assistant.keyword_manager.get_next_keyword()
        self.assertIsNotNone(task)
        self.assertEqual(task.keyword, "手机")
        
        # 模拟搜索和处理
        search_success = self.mock_app_controller.search_by_keyword(task.keyword)
        self.assertTrue(search_success)
        
        # 获取商品卡
        cards = self.mock_app_controller.get_all_product_cards()
        self.assertGreater(len(cards), 0)
        
        # 模拟处理每个商品卡
        processed_count = 0
        for i in range(min(len(cards), task.max_products)):
            # 点击商品卡
            click_success = self.mock_app_controller.click_product_card_by_index(i)
            if click_success:
                # 提取商品信息
                product_info = self.mock_product_analyzer.extract_product_info()
                self.assertIsNotNone(product_info)
                
                # 生成评论
                comments = self.mock_comment_generator.generate_comments(
                    product_info, comment_types, 2)
                self.assertGreater(len(comments), 0)
                
                # 发布评论
                publish_result = self.mock_comment_publisher.publish_comments(
                    comments, "test_id")
                self.assertGreater(publish_result["successful"], 0)
                
                processed_count += 1
                
                # 返回搜索结果
                back_success = self.mock_app_controller.navigate_back_to_search_results()
                self.assertTrue(back_success)
        
        # 更新任务进度
        self.assistant.keyword_manager.update_current_progress(
            products_processed=processed_count,
            comments_generated=processed_count * 4,  # 2种类型 * 2条/类型
            comments_published=int(processed_count * 4 * 0.9)  # 90%成功率
        )
        
        # 完成任务
        complete_success = self.assistant.keyword_manager.complete_current_keyword()
        self.assertTrue(complete_success)
        
        # 检查任务状态
        self.assertEqual(task.status, KeywordStatus.COMPLETED)
        self.assertEqual(task.products_processed, processed_count)
    
    def test_multiple_keywords_processing(self):
        """测试多个关键词处理流程"""
        keywords = ["手机", "电脑", "相机"]
        comment_types = ["inquiry"]
        max_products = 2
        
        # 添加关键词
        success = self.assistant.keyword_manager.add_keywords(
            keywords, max_products=max_products)
        self.assertTrue(success)
        
        processed_keywords = []
        
        # 处理所有关键词
        while not self.assistant.keyword_manager.is_empty():
            task = self.assistant.keyword_manager.get_next_keyword()
            if not task:
                break
            
            # 搜索关键词
            search_success = self.mock_app_controller.search_by_keyword(task.keyword)
            if search_success:
                # 获取并处理商品
                cards = self.mock_app_controller.get_all_product_cards()
                processed_count = min(len(cards), max_products)
                
                # 更新进度
                self.assistant.keyword_manager.update_current_progress(
                    products_processed=processed_count,
                    comments_generated=processed_count * 2,
                    comments_published=processed_count * 2
                )
                
                # 完成关键词
                self.assistant.keyword_manager.complete_current_keyword()
                processed_keywords.append(task.keyword)
            else:
                # 失败处理
                self.assistant.keyword_manager.fail_current_keyword("搜索失败")
        
        # 检查处理结果
        self.assertEqual(len(processed_keywords), len(keywords))
        self.assertIn("手机", processed_keywords)
        self.assertIn("电脑", processed_keywords)
        self.assertIn("相机", processed_keywords)
    
    def test_error_handling_in_keyword_processing(self):
        """测试关键词处理中的错误处理"""
        keywords = ["不存在的关键词"]
        
        self.assistant.keyword_manager.add_keywords(keywords)
        task = self.assistant.keyword_manager.get_next_keyword()
        
        # 模拟搜索失败
        search_success = self.mock_app_controller.search_by_keyword(task.keyword)
        self.assertFalse(search_success)  # 不存在的关键词应该搜索失败
        
        # 标记失败
        fail_success = self.assistant.keyword_manager.fail_current_keyword("关键词搜索失败")
        self.assertTrue(fail_success)
        self.assertEqual(task.status, KeywordStatus.FAILED)
    
    def test_keyword_processing_statistics(self):
        """测试关键词处理统计"""
        keywords = ["统计测试1", "统计测试2"]
        
        self.assistant.keyword_manager.add_keywords(keywords, max_products=5)
        
        # 处理第一个关键词
        task1 = self.assistant.keyword_manager.get_next_keyword()
        self.assistant.keyword_manager.update_current_progress(
            products_processed=3,
            comments_generated=6,
            comments_published=5
        )
        self.assistant.keyword_manager.complete_current_keyword()
        
        # 处理第二个关键词
        task2 = self.assistant.keyword_manager.get_next_keyword()
        self.assistant.keyword_manager.update_current_progress(
            products_processed=4,
            comments_generated=8,
            comments_published=7
        )
        self.assistant.keyword_manager.complete_current_keyword()
        
        # 检查总体统计
        status = self.assistant.keyword_manager.get_queue_status()
        self.assertEqual(status['processed_keywords'], 2)
        self.assertEqual(status['total_products_processed'], 7)  # 3 + 4
        self.assertEqual(status['total_comments_published'], 12)  # 5 + 7

class TestPerformanceAndStress(unittest.TestCase):
    """性能和压力测试"""
    
    def test_large_keyword_queue(self):
        """测试大量关键词队列"""
        keyword_manager = KeywordManager()
        
        # 添加大量关键词
        large_keywords = [f"关键词{i}" for i in range(100)]
        
        start_time = time.time()
        success = keyword_manager.add_keywords(large_keywords, max_products=10)
        end_time = time.time()
        
        self.assertTrue(success)
        self.assertEqual(keyword_manager.total_keywords, 100)
        
        # 检查性能（应该在1秒内完成）
        processing_time = end_time - start_time
        self.assertLess(processing_time, 1.0)
    
    def test_concurrent_keyword_access(self):
        """测试并发关键词访问"""
        keyword_manager = KeywordManager()
        keyword_manager.add_keywords([f"并发测试{i}" for i in range(20)])
        
        results = []
        
        def worker():
            task = keyword_manager.get_next_keyword()
            if task:
                # 模拟处理
                time.sleep(0.01)
                keyword_manager.complete_current_keyword()
                results.append(task.keyword)
        
        # 创建多个线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 检查结果
        self.assertGreater(len(results), 0)
        self.assertEqual(len(set(results)), len(results))  # 确保没有重复处理

def run_keyword_search_tests():
    """运行关键词搜索测试套件"""
    print("🚀 开始关键词循环搜索功能测试...")
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_classes = [
        TestKeywordManager,
        TestKeywordTask,
        TestKeywordSearchIntegration,
        TestPerformanceAndStress
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # 输出结果
    print(f"\n📊 测试结果:")
    print(f"✅ 成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ 失败: {len(result.failures)}")
    print(f"💥 错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n💥 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\n🎯 测试{'通过' if success else '失败'}!")
    
    return success

if __name__ == '__main__':
    success = run_keyword_search_tests()
    sys.exit(0 if success else 1)