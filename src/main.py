# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 主程序
整合所有功能模块，提供完整的自动评论服务
"""

import sys
import os
import time
import logging
import traceback
import threading
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入各功能模块
from config import config, get_config
from database import get_db
from app_controller import create_xianyu_controller
from product_analyzer import create_product_analyzer  
from comment_generator import create_comment_generator
from comment_publisher import create_comment_publisher
from ai_client import test_deepseek_connection
from keyword_manager import create_keyword_manager, KeywordStatus

class XianyuCommentAssistant:
    """闲鱼自动评论助手主控制器"""
    
    def __init__(self):
        """初始化助手"""
        self.app_controller = None
        self.product_analyzer = None
        self.comment_generator = None
        self.comment_publisher = None
        self.keyword_manager = None
        self.database = get_db()
        
        # 运行状态
        self.is_running = False
        self.current_task = None
        self.current_keyword_task = None
        self.task_thread = None
        
        # 统计信息
        self.session_stats = {
            'start_time': None,
            'products_processed': 0,
            'comments_generated': 0,
            'comments_published': 0,
            'errors_encountered': 0
        }
        
        # 初始化日志
        self._setup_logging()
        
        logging.info("闲鱼自动评论助手初始化完成")
    
    def _setup_logging(self):
        """设置日志配置"""
        try:
            log_config = get_config("logging", {})
            log_level = getattr(logging, log_config.get("level", "INFO"))
            log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            log_file = log_config.get("file_path", "data/logs/xianyu_assistant.log")
            
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 配置日志
            logging.basicConfig(
                level=log_level,
                format=log_format,
                handlers=[
                    logging.FileHandler(str(log_path), encoding='utf-8'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
        except Exception as e:
            print(f"设置日志失败: {e}")
            logging.basicConfig(level=logging.INFO)
    
    def initialize_components(self, device_id: str = None) -> bool:
        """
        初始化各个组件
        
        Args:
            device_id: 设备ID
            
        Returns:
            是否初始化成功
        """
        try:
            logging.info("开始初始化系统组件...")
            
            # 1. 初始化APP控制器
            logging.info("初始化APP控制器...")
            self.app_controller = create_xianyu_controller(device_id)
            if not self.app_controller.connect():
                logging.error("无法连接到闲鱼APP")
                return False
            
            # 2. 初始化商品分析器
            logging.info("初始化商品分析器...")
            self.product_analyzer = create_product_analyzer(self.app_controller)
            
            # 3. 初始化评论生成器
            logging.info("初始化评论生成器...")
            self.comment_generator = create_comment_generator()
            
            # 4. 初始化评论发布器
            logging.info("初始化评论发布器...")
            self.comment_publisher = create_comment_publisher(self.app_controller)
            
            # 5. 初始化关键词管理器
            logging.info("初始化关键词管理器...")
            self.keyword_manager = create_keyword_manager()
            
            # 6. 测试DeepSeek API连接
            logging.info("测试AI服务连接...")
            if config.is_api_configured():
                if not test_deepseek_connection():
                    logging.warning("AI服务连接失败，将仅使用模板生成评论")
            else:
                logging.warning("未配置AI API，将仅使用模板生成评论")
            
            logging.info("系统组件初始化完成")
            return True
            
        except Exception as e:
            logging.error(f"初始化组件失败: {e}")
            logging.debug(traceback.format_exc())
            return False
    
    def start_batch_task(self, product_urls: List[str], 
                        comment_types: List[str],
                        task_name: str = None) -> bool:
        """
        开始批量任务
        
        Args:
            product_urls: 商品URL列表
            comment_types: 评论类型列表
            task_name: 任务名称
            
        Returns:
            是否启动成功
        """
        try:
            if self.is_running:
                logging.warning("任务已在运行中")
                return False
            
            if not self.app_controller or not self.app_controller.is_connected:
                logging.error("系统未正确初始化或APP未连接")
                return False
            
            # 验证参数
            if not product_urls:
                logging.error("商品URL列表为空")
                return False
            
            if not comment_types:
                logging.error("评论类型列表为空")
                return False
            
            # 创建任务
            self.current_task = {
                'name': task_name or f"批量任务_{int(time.time())}",
                'product_urls': product_urls,
                'comment_types': comment_types,
                'total_products': len(product_urls),
                'current_index': 0,
                'start_time': time.time(),
                'status': 'running'
            }
            
            # 保存任务到数据库
            task_data = {
                'task_name': self.current_task['name'],
                'product_urls': product_urls,
                'comment_types': comment_types,
                'total_products': len(product_urls),
                'completed_products': 0,
                'successful_comments': 0,
                'failed_comments': 0,
                'status': 'running'
            }
            
            task_id = self.database.save_task(task_data)
            self.current_task['task_id'] = task_id
            
            # 重置统计信息
            self.session_stats = {
                'start_time': time.time(),
                'products_processed': 0,
                'comments_generated': 0,
                'comments_published': 0,
                'errors_encountered': 0
            }
            
            # 在新线程中启动任务
            self.is_running = True
            self.task_thread = threading.Thread(target=self._execute_batch_task, daemon=True)
            self.task_thread.start()
            
            logging.info(f"批量任务已启动: {len(product_urls)}个商品，{comment_types}类型评论")
            return True
            
        except Exception as e:
            logging.error(f"启动批量任务失败: {e}")
            logging.debug(traceback.format_exc())
            return False
    
    def start_keyword_batch_task(self, keywords: List[str],
                                comment_types: List[str],
                                max_products_per_keyword: int = 50,
                                task_name: str = None) -> bool:
        """
        开始关键词批量任务
        
        Args:
            keywords: 关键词列表
            comment_types: 评论类型列表
            max_products_per_keyword: 每个关键词最大处理商品数
            task_name: 任务名称
            
        Returns:
            是否启动成功
        """
        try:
            if self.is_running:
                logging.warning("任务已在运行中")
                return False
            
            if not self.app_controller or not self.app_controller.is_connected:
                logging.error("系统未正确初始化或APP未连接")
                return False
            
            if not self.keyword_manager:
                logging.error("关键词管理器未初始化")
                return False
            
            # 验证参数
            if not keywords:
                logging.error("关键词列表为空")
                return False
            
            if not comment_types:
                logging.error("评论类型列表为空")
                return False
            
            # 添加关键词到管理器
            success = self.keyword_manager.add_keywords(
                keywords=keywords,
                max_products=max_products_per_keyword
            )
            
            if not success:
                logging.error("添加关键词到管理器失败")
                return False
            
            # 创建任务
            self.current_task = {
                'name': task_name or f"关键词任务_{int(time.time())}",
                'type': 'keyword_batch',
                'keywords': keywords,
                'comment_types': comment_types,
                'max_products_per_keyword': max_products_per_keyword,
                'total_keywords': len(keywords),
                'start_time': time.time(),
                'status': 'running'
            }
            
            # 保存任务到数据库
            task_data = {
                'task_name': self.current_task['name'],
                'product_urls': keywords,  # 关键词存在这里
                'comment_types': comment_types,
                'total_products': len(keywords) * max_products_per_keyword,  # 预估数量
                'completed_products': 0,
                'successful_comments': 0,
                'failed_comments': 0,
                'status': 'running'
            }
            
            task_id = self.database.save_task(task_data)
            self.current_task['task_id'] = task_id
            
            # 重置统计信息
            self.session_stats = {
                'start_time': time.time(),
                'products_processed': 0,
                'comments_generated': 0,
                'comments_published': 0,
                'errors_encountered': 0
            }
            
            # 在新线程中启动任务
            self.is_running = True
            self.task_thread = threading.Thread(target=self._execute_keyword_batch_task, daemon=True)
            self.task_thread.start()
            
            logging.info(f"关键词批量任务已启动: {len(keywords)}个关键词，{comment_types}类型评论")
            return True
            
        except Exception as e:
            logging.error(f"启动关键词批量任务失败: {e}")
            logging.debug(traceback.format_exc())
            return False
    
    def _execute_keyword_batch_task(self):
        """执行关键词批量任务（在独立线程中运行）"""
        try:
            task = self.current_task
            comment_types = task['comment_types']
            max_products_per_keyword = task['max_products_per_keyword']
            
            logging.info(f"开始执行关键词批量任务: {task['name']}")
            
            # 处理每个关键词
            while not self.keyword_manager.is_empty() and self.is_running:
                # 获取下一个关键词任务
                keyword_task = self.keyword_manager.get_next_keyword()
                if not keyword_task:
                    break
                
                self.current_keyword_task = keyword_task
                keyword = keyword_task.keyword
                
                try:
                    logging.info(f"开始处理关键词: {keyword}")
                    
                    # 1. 搜索关键词
                    if not self.app_controller.search_by_keyword(keyword):
                        logging.error(f"关键词搜索失败: {keyword}")
                        self.keyword_manager.fail_current_keyword(f"搜索失败: {keyword}")
                        continue
                    
                    # 2. 处理搜索结果中的商品卡
                    processed_count = 0
                    page_count = 0
                    max_pages = keyword_task.max_pages
                    
                    while processed_count < max_products_per_keyword and page_count < max_pages and self.is_running:
                        # 获取当前页面的所有商品卡
                        product_cards = self.app_controller.get_all_product_cards()
                        if not product_cards:
                            logging.warning(f"未找到商品卡: {keyword} (第{page_count+1}页)")
                            break
                        
                        keyword_task.products_found += len(product_cards)
                        
                        # 逐个处理商品卡
                        for i, _ in enumerate(product_cards):
                            if processed_count >= max_products_per_keyword or not self.is_running:
                                break
                            
                            try:
                                # 点击商品卡进入详情页
                                if not self.app_controller.click_product_card_by_index(i):
                                    logging.warning(f"点击商品卡失败: {keyword} #{i}")
                                    continue
                                
                                # 处理商品（提取信息、生成评论、发布）
                                result = self._process_single_product_from_search(comment_types)
                                
                                if result['success']:
                                    processed_count += 1
                                    keyword_task.products_processed += 1
                                    keyword_task.comments_generated += result.get('comments_generated', 0)
                                    keyword_task.comments_published += result.get('comments_published', 0)
                                    
                                    # 更新会话统计
                                    self.session_stats['products_processed'] += 1
                                    self.session_stats['comments_generated'] += result.get('comments_generated', 0)
                                    self.session_stats['comments_published'] += result.get('comments_published', 0)
                                    
                                    logging.info(f"商品处理成功: {keyword} #{i+1} "
                                               f"(已处理: {processed_count}/{max_products_per_keyword})")
                                else:
                                    keyword_task.errors_count += 1
                                    self.session_stats['errors_encountered'] += 1
                                    logging.warning(f"商品处理失败: {keyword} #{i+1} - {result.get('error_message')}")
                                
                                # 返回搜索结果页面
                                if not self.app_controller.navigate_back_to_search_results():
                                    logging.error(f"返回搜索结果页失败: {keyword}")
                                    break
                                
                                # 商品间隔
                                interval = self._calculate_product_interval()
                                logging.info(f"等待间隔: {interval}秒")
                                time.sleep(interval)
                                
                                # 更新关键词管理器进度
                                self.keyword_manager.update_current_progress(
                                    products_processed=keyword_task.products_processed,
                                    comments_generated=keyword_task.comments_generated,
                                    comments_published=keyword_task.comments_published
                                )
                                
                            except Exception as e:
                                logging.error(f"处理商品卡异常: {keyword} #{i} - {e}")
                                keyword_task.errors_count += 1
                                self.session_stats['errors_encountered'] += 1
                                continue
                        
                        # 如果还需要更多商品，尝试加载下一页
                        if processed_count < max_products_per_keyword and self.is_running:
                            if self.app_controller.has_more_products():
                                if self.app_controller.scroll_to_load_more_products():
                                    page_count += 1
                                    logging.info(f"加载更多商品: {keyword} (第{page_count+1}页)")
                                    time.sleep(2)  # 等待加载
                                else:
                                    logging.info(f"无法加载更多商品: {keyword}")
                                    break
                            else:
                                logging.info(f"已到达商品底部: {keyword}")
                                break
                    
                    # 完成当前关键词处理
                    if processed_count > 0:
                        self.keyword_manager.complete_current_keyword()
                        logging.info(f"关键词处理完成: {keyword} "
                                   f"(处理商品: {processed_count}, "
                                   f"发布评论: {keyword_task.comments_published})")
                    else:
                        self.keyword_manager.fail_current_keyword("未成功处理任何商品")
                        logging.warning(f"关键词处理失败: {keyword} - 未成功处理任何商品")
                    
                    # 关键词间隔
                    if not self.keyword_manager.is_empty():
                        keyword_interval = random.randint(30, 90)  # 30-90秒间隔
                        logging.info(f"关键词间隔: {keyword_interval}秒")
                        time.sleep(keyword_interval)
                
                except Exception as e:
                    logging.error(f"处理关键词异常: {keyword} - {e}")
                    self.keyword_manager.fail_current_keyword(str(e))
                    continue
            
            # 完成任务
            self._finish_task()
            logging.info("关键词批量任务执行完成")
            
        except Exception as e:
            logging.error(f"执行关键词批量任务异常: {e}")
            self._finish_task(str(e))
    
    def _process_single_product_from_search(self, comment_types: List[str]) -> Dict[str, Any]:
        """
        处理从搜索结果进入的单个商品（已在商品详情页）
        
        Args:
            comment_types: 评论类型列表
            
        Returns:
            处理结果
        """
        result = {
            'success': False,
            'comments_generated': 0,
            'comments_published': 0,
            'error_message': None
        }
        
        try:
            # 1. 提取商品信息（跳过导航步骤）
            logging.info("提取商品信息...")
            product_info = self.product_analyzer.extract_product_info()
            if not product_info:
                result['error_message'] = "无法提取商品信息"
                return result
            
            # 生成唯一商品URL（基于当前时间和商品标题）
            import hashlib
            product_title = product_info.get('title', 'unknown')
            timestamp = str(int(time.time()))
            unique_id = hashlib.md5(f"{product_title}{timestamp}".encode()).hexdigest()[:8]
            product_url = f"search_result_{unique_id}"
            
            # 保存商品信息到数据库
            product_info['url'] = product_url
            product_info['id'] = unique_id
            self.database.save_product(product_info)
            
            # 2. 生成评论
            logging.info(f"生成评论: {comment_types}")
            comments = self.comment_generator.generate_comments(
                product_info, comment_types, count_per_type=2
            )
            
            if not comments:
                result['error_message'] = "无法生成评论"
                return result
            
            result['comments_generated'] = len(comments)
            
            # 保存评论到数据库
            for comment in comments:
                comment['product_id'] = product_info.get('id')
                comment_id = self.database.save_comment(comment)
                comment['comment_id'] = comment_id
            
            # 3. 发布评论
            logging.info(f"发布评论: {len(comments)}条")
            publish_result = self.comment_publisher.publish_comments(
                comments, product_info.get('id')
            )
            
            result['comments_published'] = publish_result.get('successful', 0)
            result['success'] = result['comments_published'] > 0
            
            if result['success']:
                logging.info(f"商品处理成功: 生成{result['comments_generated']}条，发布{result['comments_published']}条")
            else:
                logging.warning(f"商品处理失败: {publish_result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            logging.error(f"处理搜索商品异常: {e}")
            result['error_message'] = str(e)
            return result
    
    def _execute_batch_task(self):
        """执行批量任务（在独立线程中运行）"""
        try:
            task = self.current_task
            product_urls = task['product_urls']
            comment_types = task['comment_types']
            
            logging.info(f"开始执行批量任务: {task['name']}")
            
            for i, product_url in enumerate(product_urls):
                if not self.is_running:
                    logging.info("任务被停止")
                    break
                
                try:
                    # 更新任务进度
                    task['current_index'] = i
                    logging.info(f"处理商品 {i+1}/{len(product_urls)}: {product_url}")
                    
                    # 处理单个商品
                    result = self._process_single_product(product_url, comment_types)
                    
                    # 更新统计
                    self.session_stats['products_processed'] += 1
                    if result['success']:
                        self.session_stats['comments_generated'] += result.get('comments_generated', 0)
                        self.session_stats['comments_published'] += result.get('comments_published', 0)
                    else:
                        self.session_stats['errors_encountered'] += 1
                    
                    # 更新数据库任务进度
                    if task.get('task_id'):
                        progress_data = {
                            'completed_products': self.session_stats['products_processed'],
                            'successful_comments': self.session_stats['comments_published'],
                            'failed_comments': (self.session_stats['comments_generated'] - 
                                              self.session_stats['comments_published'])
                        }
                        self.database.update_task_progress(task['task_id'], progress_data)
                    
                    # 商品间隔
                    if i < len(product_urls) - 1:  # 不是最后一个商品
                        interval = self._calculate_product_interval()
                        logging.info(f"商品处理间隔: {interval}秒")
                        time.sleep(interval)
                    
                except Exception as e:
                    logging.error(f"处理商品失败 {product_url}: {e}")
                    self.session_stats['errors_encountered'] += 1
                    
                    # 记录错误到数据库
                    self.database.log_error(
                        'main', '_execute_batch_task', 
                        type(e).__name__, str(e), 
                        traceback.format_exc(), product_url
                    )
                    
                    # 检查是否应该停止
                    if self.session_stats['errors_encountered'] >= 10:
                        logging.error("错误过多，停止任务")
                        break
            
            # 任务完成
            self._finish_task()
            
        except Exception as e:
            logging.error(f"执行批量任务异常: {e}")
            logging.debug(traceback.format_exc())
            self._finish_task(error=str(e))
    
    def _process_single_product(self, product_url: str, 
                              comment_types: List[str]) -> Dict[str, Any]:
        """
        处理单个商品
        
        Args:
            product_url: 商品URL
            comment_types: 评论类型列表
            
        Returns:
            处理结果
        """
        result = {
            'success': False,
            'product_url': product_url,
            'comments_generated': 0,
            'comments_published': 0,
            'error_message': None
        }
        
        try:
            # 1. 导航到商品页面
            logging.info(f"导航到商品页面: {product_url}")
            if not self.app_controller.navigate_to_product(product_url):
                result['error_message'] = "无法导航到商品页面"
                return result
            
            # 2. 提取商品信息
            logging.info("提取商品信息...")
            product_info = self.product_analyzer.extract_product_info()
            if not product_info:
                result['error_message'] = "无法提取商品信息"
                return result
            
            # 保存商品信息到数据库
            product_info['url'] = product_url
            self.database.save_product(product_info)
            
            # 3. 生成评论
            logging.info(f"生成评论: {comment_types}")
            comments = self.comment_generator.generate_comments(
                product_info, comment_types, count_per_type=2
            )
            
            if not comments:
                result['error_message'] = "无法生成评论"
                return result
            
            result['comments_generated'] = len(comments)
            
            # 保存评论到数据库
            for comment in comments:
                comment['product_id'] = product_info.get('id')
                comment_id = self.database.save_comment(comment)
                comment['comment_id'] = comment_id
            
            # 4. 发布评论
            logging.info(f"发布评论: {len(comments)}条")
            publish_result = self.comment_publisher.publish_comments(
                comments, product_info.get('id')
            )
            
            result['comments_published'] = publish_result.get('successful', 0)
            result['success'] = result['comments_published'] > 0
            
            if result['success']:
                logging.info(f"商品处理成功: 生成{result['comments_generated']}条，发布{result['comments_published']}条")
            else:
                logging.warning(f"商品处理失败: {publish_result.get('error', '未知错误')}")
            
            return result
            
        except Exception as e:
            logging.error(f"处理商品异常: {e}")
            result['error_message'] = str(e)
            return result
    
    def _calculate_product_interval(self) -> int:
        """
        计算商品处理间隔
        
        Returns:
            间隔时间（秒）
        """
        # 基础间隔
        base_interval = 60  # 1分钟
        
        # 根据当前统计动态调整
        error_rate = 0
        if self.session_stats['products_processed'] > 0:
            error_rate = (self.session_stats['errors_encountered'] / 
                         self.session_stats['products_processed'])
        
        # 错误率高时增加间隔
        if error_rate > 0.3:
            base_interval *= 2
        elif error_rate > 0.1:
            base_interval *= 1.5
        
        # 添加随机性
        import random
        actual_interval = base_interval + random.randint(-10, 30)
        return max(30, actual_interval)  # 最小30秒
    
    def _finish_task(self, error: str = None):
        """
        完成任务
        
        Args:
            error: 错误信息（如果有）
        """
        try:
            self.is_running = False
            
            if self.current_task:
                # 计算任务总时长
                duration = time.time() - self.current_task['start_time']
                
                # 更新任务状态
                task_status = 'failed' if error else 'completed'
                
                # 更新数据库
                if self.current_task.get('task_id'):
                    progress_data = {
                        'status': task_status,
                        'error_log': error,
                        'completed_products': self.session_stats['products_processed'],
                        'successful_comments': self.session_stats['comments_published']
                    }
                    self.database.update_task_progress(self.current_task['task_id'], progress_data)
                
                # 生成任务报告
                report = self._generate_task_report(duration, error)
                logging.info(f"任务完成报告:\n{report}")
                
                self.current_task = None
            
            # 更新每日统计
            self.database.update_daily_statistics()
            
            logging.info("任务执行完成")
            
        except Exception as e:
            logging.error(f"完成任务处理异常: {e}")
    
    def _generate_task_report(self, duration: float, error: str = None) -> str:
        """
        生成任务报告
        
        Args:
            duration: 任务时长
            error: 错误信息
            
        Returns:
            报告文本
        """
        stats = self.session_stats
        
        # 计算成功率
        success_rate = 0
        if stats['comments_generated'] > 0:
            success_rate = (stats['comments_published'] / stats['comments_generated']) * 100
        
        # 格式化时长
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        report = f"""
{'='*50}
任务执行报告
{'='*50}
任务名称: {self.current_task.get('name', '未知任务')}
执行时间: {duration_str}
任务状态: {'失败' if error else '成功'}

处理统计:
- 商品处理数量: {stats['products_processed']}
- 评论生成数量: {stats['comments_generated']}
- 评论发布数量: {stats['comments_published']}
- 发布成功率: {success_rate:.1f}%
- 遇到错误数量: {stats['errors_encountered']}

{f'错误信息: {error}' if error else ''}
{'='*50}
"""
        return report
    
    def stop_task(self):
        """停止当前任务"""
        if self.is_running:
            logging.info("停止任务请求")
            self.is_running = False
            
            if self.task_thread and self.task_thread.is_alive():
                self.task_thread.join(timeout=10)  # 等待最多10秒
            
            logging.info("任务已停止")
            return True
        else:
            logging.info("没有运行中的任务")
            return False
    
    def get_keyword_task_status(self) -> Dict[str, Any]:
        """
        获取关键词任务状态
        
        Returns:
            关键词任务状态信息
        """
        try:
            if not self.keyword_manager:
                return {'error': '关键词管理器未初始化'}
            
            # 基础状态信息
            queue_status = self.keyword_manager.get_queue_status()
            
            # 当前关键词任务详情
            current_keyword_info = None
            if self.current_keyword_task:
                current_keyword_info = {
                    'keyword': self.current_keyword_task.keyword,
                    'status': self.current_keyword_task.status.value,
                    'products_found': self.current_keyword_task.products_found,
                    'products_processed': self.current_keyword_task.products_processed,
                    'comments_generated': self.current_keyword_task.comments_generated,
                    'comments_published': self.current_keyword_task.comments_published,
                    'errors_count': self.current_keyword_task.errors_count,
                    'success_rate': self.current_keyword_task.get_success_rate(),
                    'max_products': self.current_keyword_task.max_products
                }
            
            # 整体任务信息
            task_info = None
            if self.current_task and self.current_task.get('type') == 'keyword_batch':
                task_info = {
                    'name': self.current_task.get('name'),
                    'type': self.current_task.get('type'),
                    'total_keywords': self.current_task.get('total_keywords', 0),
                    'comment_types': self.current_task.get('comment_types', []),
                    'max_products_per_keyword': self.current_task.get('max_products_per_keyword', 0),
                    'start_time': self.current_task.get('start_time'),
                    'status': self.current_task.get('status')
                }
            
            return {
                'is_running': self.is_running,
                'queue_status': queue_status,
                'current_keyword': current_keyword_info,
                'task_info': task_info,
                'session_stats': self.session_stats.copy()
            }
            
        except Exception as e:
            logging.error(f"获取关键词任务状态失败: {e}")
            return {'error': str(e)}
    
    def get_keyword_history(self) -> List[Dict[str, Any]]:
        """
        获取关键词处理历史
        
        Returns:
            关键词历史记录列表
        """
        try:
            if not self.keyword_manager:
                return []
            
            return self.keyword_manager.get_keyword_history()
            
        except Exception as e:
            logging.error(f"获取关键词历史失败: {e}")
            return []
    
    def add_keywords_to_queue(self, keywords: List[str], **kwargs) -> bool:
        """
        向队列中添加新关键词（任务运行期间）
        
        Args:
            keywords: 关键词列表
            **kwargs: 其他配置参数
            
        Returns:
            是否添加成功
        """
        try:
            if not self.keyword_manager:
                logging.error("关键词管理器未初始化")
                return False
            
            return self.keyword_manager.add_keywords(keywords, **kwargs)
            
        except Exception as e:
            logging.error(f"添加关键词到队列失败: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取当前状态
        
        Returns:
            状态信息
        """
        status = {
            'is_running': self.is_running,
            'app_connected': bool(self.app_controller and self.app_controller.is_connected),
            'api_configured': config.is_api_configured(),
            'session_stats': self.session_stats.copy(),
            'current_task': None
        }
        
        if self.current_task:
            status['current_task'] = {
                'name': self.current_task.get('name'),
                'total_products': self.current_task.get('total_products', 0),
                'current_index': self.current_task.get('current_index', 0),
                'progress_percent': (self.current_task.get('current_index', 0) / 
                                   max(self.current_task.get('total_products', 1), 1)) * 100
            }
        
        return status
    
    def test_system(self) -> Dict[str, bool]:
        """
        测试系统各组件
        
        Returns:
            测试结果
        """
        results = {}
        
        try:
            # 测试APP连接
            results['app_connection'] = (self.app_controller and 
                                       self.app_controller.is_connected)
            
            # 测试AI API
            results['ai_api'] = config.is_api_configured() and test_deepseek_connection()
            
            # 测试数据库
            try:
                self.database.get_today_statistics()
                results['database'] = True
            except:
                results['database'] = False
            
            # 测试评论功能
            if self.comment_publisher:
                results['comment_function'] = self.comment_publisher.test_comment_function()
            else:
                results['comment_function'] = False
            
            logging.info(f"系统测试结果: {results}")
            return results
            
        except Exception as e:
            logging.error(f"系统测试失败: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止任务
            self.stop_task()
            
            # 断开APP连接
            if self.app_controller:
                self.app_controller.disconnect()
            
            # 清理数据库连接
            if self.database:
                self.database.close()
            
            logging.info("资源清理完成")
            
        except Exception as e:
            logging.error(f"清理资源失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.cleanup()


def main():
    """主函数"""
    print("="*60)
    print("     闲鱼自动评论助手 v1.0")
    print("="*60)
    print()
    
    try:
        # 创建助手实例
        assistant = XianyuCommentAssistant()
        
        # 初始化组件
        print("正在初始化系统组件...")
        if not assistant.initialize_components():
            print("❌ 系统初始化失败")
            return False
        
        print("✅ 系统初始化成功")
        
        # 系统测试
        print("\n正在进行系统测试...")
        test_results = assistant.test_system()
        
        print(f"APP连接: {'✅' if test_results.get('app_connection') else '❌'}")
        print(f"AI服务: {'✅' if test_results.get('ai_api') else '❌'}")
        print(f"数据库: {'✅' if test_results.get('database') else '❌'}")
        print(f"评论功能: {'✅' if test_results.get('comment_function') else '❌'}")
        
        # 示例任务配置
        example_urls = [
            "https://www.xianyu.com/item/123456789",
            "https://www.xianyu.com/item/987654321"
        ]
        
        example_types = ['inquiry', 'interest', 'compliment']
        
        print(f"\n📝 示例配置:")
        print(f"商品URL: {len(example_urls)} 个")
        print(f"评论类型: {example_types}")
        
        # 询问用户是否开始任务
        user_input = input("\n是否开始示例任务？(y/n): ").strip().lower()
        
        if user_input == 'y':
            print("\n🚀 开始执行任务...")
            success = assistant.start_batch_task(
                product_urls=example_urls,
                comment_types=example_types,
                task_name="示例任务"
            )
            
            if success:
                print("✅ 任务已启动")
                
                # 监控任务进度
                while assistant.is_running:
                    time.sleep(5)
                    status = assistant.get_status()
                    
                    if status.get('current_task'):
                        task = status['current_task']
                        progress = task.get('progress_percent', 0)
                        print(f"\r进度: {progress:.1f}% ({task.get('current_index', 0)}/{task.get('total_products', 0)})", end='', flush=True)
                
                print("\n✅ 任务执行完成")
            else:
                print("❌ 任务启动失败")
        else:
            print("👋 程序退出")
        
        # 清理资源
        assistant.cleanup()
        return True
        
    except KeyboardInterrupt:
        print("\n\n用户中断程序")
        return True
    except Exception as e:
        logging.error(f"主程序异常: {e}")
        logging.debug(traceback.format_exc())
        print(f"❌ 程序运行异常: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)