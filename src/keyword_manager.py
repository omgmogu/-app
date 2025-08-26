# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 关键词搜索管理模块
负责管理多个关键词的搜索队列和处理状态
"""

import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from queue import Queue, Empty
import threading
from database import get_db

class KeywordStatus(Enum):
    """关键词状态枚举"""
    PENDING = "pending"      # 待处理
    PROCESSING = "processing"  # 处理中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    SKIPPED = "skipped"      # 跳过

@dataclass
class KeywordTask:
    """关键词任务"""
    keyword: str                    # 关键词
    priority: int = 1               # 优先级（1-10，数字越大优先级越高）
    max_products: int = 50          # 最大处理商品数量
    status: KeywordStatus = KeywordStatus.PENDING  # 状态
    
    # 统计信息
    products_found: int = 0         # 找到的商品数量
    products_processed: int = 0     # 已处理的商品数量
    comments_generated: int = 0     # 生成的评论数量
    comments_published: int = 0     # 发布的评论数量
    errors_count: int = 0           # 错误数量
    
    # 时间信息
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    
    # 处理配置
    enable_pagination: bool = True  # 是否启用分页
    max_pages: int = 5             # 最大页数
    scroll_delay: Tuple[float, float] = (1.0, 3.0)  # 滚动延迟范围
    
    def start_processing(self):
        """开始处理"""
        self.status = KeywordStatus.PROCESSING
        self.started_at = time.time()
    
    def complete_processing(self):
        """完成处理"""
        self.status = KeywordStatus.COMPLETED
        self.completed_at = time.time()
    
    def fail_processing(self):
        """处理失败"""
        self.status = KeywordStatus.FAILED
        self.completed_at = time.time()
    
    def get_duration(self) -> Optional[float]:
        """获取处理时长"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.products_processed == 0:
            return 0.0
        return (self.products_processed - self.errors_count) / self.products_processed * 100

class KeywordManager:
    """关键词管理器"""
    
    def __init__(self):
        """初始化关键词管理器"""
        self.keyword_queue = Queue()
        self.completed_tasks: List[KeywordTask] = []
        self.current_task: Optional[KeywordTask] = None
        self.database = get_db()
        self.lock = threading.Lock()
        
        # 统计信息
        self.total_keywords = 0
        self.processed_keywords = 0
        self.total_products_found = 0
        self.total_products_processed = 0
        self.total_comments_published = 0
        
        # 配置
        self.batch_size = 20           # 批量处理大小
        self.retry_failed_keywords = True  # 是否重试失败的关键词
        self.max_retry_count = 3       # 最大重试次数
        
        logging.info("关键词管理器初始化完成")
    
    def add_keywords(self, keywords: List[str], priority: int = 1, 
                    max_products: int = 50, **kwargs) -> bool:
        """
        添加关键词到队列
        
        Args:
            keywords: 关键词列表
            priority: 优先级
            max_products: 每个关键词最大处理商品数
            **kwargs: 其他配置参数
            
        Returns:
            是否添加成功
        """
        try:
            with self.lock:
                for keyword in keywords:
                    if not keyword or not keyword.strip():
                        continue
                    
                    # 创建关键词任务
                    task = KeywordTask(
                        keyword=keyword.strip(),
                        priority=priority,
                        max_products=max_products,
                        **kwargs
                    )
                    
                    # 添加到队列
                    self.keyword_queue.put(task)
                    self.total_keywords += 1
                    
                    # 记录到数据库
                    self._save_keyword_task(task)
                    
                    logging.info(f"添加关键词任务: {keyword} (优先级: {priority})")
                
                logging.info(f"成功添加 {len(keywords)} 个关键词任务")
                return True
                
        except Exception as e:
            logging.error(f"添加关键词失败: {e}")
            return False
    
    def get_next_keyword(self) -> Optional[KeywordTask]:
        """
        获取下一个待处理的关键词
        
        Returns:
            下一个关键词任务或None
        """
        try:
            # 如果当前没有任务且队列不为空，获取下一个
            if self.current_task is None and not self.keyword_queue.empty():
                # 这里可以实现优先级排序逻辑
                task = self.keyword_queue.get(timeout=1)
                self.current_task = task
                task.start_processing()
                
                logging.info(f"开始处理关键词: {task.keyword}")
                return task
            
            return self.current_task
            
        except Empty:
            return None
        except Exception as e:
            logging.error(f"获取下一个关键词失败: {e}")
            return None
    
    def complete_current_keyword(self) -> bool:
        """
        完成当前关键词处理
        
        Returns:
            是否完成成功
        """
        try:
            if self.current_task is None:
                return False
            
            with self.lock:
                # 标记完成
                self.current_task.complete_processing()
                
                # 更新统计
                self.processed_keywords += 1
                self.total_products_found += self.current_task.products_found
                self.total_products_processed += self.current_task.products_processed
                self.total_comments_published += self.current_task.comments_published
                
                # 移到已完成列表
                self.completed_tasks.append(self.current_task)
                
                # 更新数据库
                self._update_keyword_task(self.current_task)
                
                logging.info(f"关键词处理完成: {self.current_task.keyword} "
                           f"(商品: {self.current_task.products_processed}, "
                           f"评论: {self.current_task.comments_published})")
                
                # 清空当前任务
                self.current_task = None
                return True
                
        except Exception as e:
            logging.error(f"完成关键词处理失败: {e}")
            return False
    
    def fail_current_keyword(self, error_message: str = "") -> bool:
        """
        标记当前关键词处理失败
        
        Args:
            error_message: 错误信息
            
        Returns:
            是否标记成功
        """
        try:
            if self.current_task is None:
                return False
            
            with self.lock:
                # 标记失败
                self.current_task.fail_processing()
                
                # 如果启用重试，重新加入队列
                if (self.retry_failed_keywords and 
                    self.current_task.errors_count < self.max_retry_count):
                    
                    self.current_task.errors_count += 1
                    self.current_task.status = KeywordStatus.PENDING
                    self.keyword_queue.put(self.current_task)
                    
                    logging.warning(f"关键词处理失败，重新排队: {self.current_task.keyword} "
                                  f"(重试次数: {self.current_task.errors_count})")
                else:
                    # 移到已完成列表
                    self.completed_tasks.append(self.current_task)
                    self.processed_keywords += 1
                    
                    logging.error(f"关键词处理失败: {self.current_task.keyword} - {error_message}")
                
                # 更新数据库
                self._update_keyword_task(self.current_task)
                
                # 清空当前任务
                self.current_task = None
                return True
                
        except Exception as e:
            logging.error(f"标记关键词失败错误: {e}")
            return False
    
    def update_current_progress(self, **kwargs) -> bool:
        """
        更新当前关键词的处理进度
        
        Args:
            **kwargs: 进度更新参数
            
        Returns:
            是否更新成功
        """
        try:
            if self.current_task is None:
                return False
            
            # 更新任务信息
            for key, value in kwargs.items():
                if hasattr(self.current_task, key):
                    setattr(self.current_task, key, value)
            
            return True
            
        except Exception as e:
            logging.error(f"更新关键词进度失败: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态
        
        Returns:
            队列状态信息
        """
        try:
            return {
                "total_keywords": self.total_keywords,
                "processed_keywords": self.processed_keywords,
                "pending_keywords": self.keyword_queue.qsize(),
                "current_keyword": self.current_task.keyword if self.current_task else None,
                "current_status": self.current_task.status.value if self.current_task else None,
                "total_products_found": self.total_products_found,
                "total_products_processed": self.total_products_processed,
                "total_comments_published": self.total_comments_published,
                "overall_progress": self.processed_keywords / max(self.total_keywords, 1) * 100
            }
        except Exception as e:
            logging.error(f"获取队列状态失败: {e}")
            return {}
    
    def get_keyword_history(self) -> List[Dict[str, Any]]:
        """
        获取关键词处理历史
        
        Returns:
            处理历史列表
        """
        try:
            history = []
            for task in self.completed_tasks:
                history.append({
                    "keyword": task.keyword,
                    "status": task.status.value,
                    "products_found": task.products_found,
                    "products_processed": task.products_processed,
                    "comments_published": task.comments_published,
                    "success_rate": task.get_success_rate(),
                    "duration": task.get_duration(),
                    "completed_at": task.completed_at
                })
            
            # 按完成时间排序
            history.sort(key=lambda x: x.get("completed_at", 0), reverse=True)
            return history
            
        except Exception as e:
            logging.error(f"获取关键词历史失败: {e}")
            return []
    
    def clear_completed_tasks(self) -> bool:
        """
        清除已完成的任务
        
        Returns:
            是否清除成功
        """
        try:
            with self.lock:
                self.completed_tasks.clear()
                logging.info("已清除完成的关键词任务")
                return True
        except Exception as e:
            logging.error(f"清除完成任务失败: {e}")
            return False
    
    def is_empty(self) -> bool:
        """
        检查队列是否为空
        
        Returns:
            队列是否为空
        """
        return self.keyword_queue.empty() and self.current_task is None
    
    def _save_keyword_task(self, task: KeywordTask):
        """保存关键词任务到数据库"""
        try:
            cursor = self.database.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO keyword_tasks 
                (keyword, priority, max_products, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                task.keyword,
                task.priority,
                task.max_products,
                task.status.value,
                task.created_at
            ))
            self.database.commit()
        except Exception as e:
            logging.error(f"保存关键词任务失败: {e}")
    
    def _update_keyword_task(self, task: KeywordTask):
        """更新关键词任务到数据库"""
        try:
            cursor = self.database.cursor()
            cursor.execute("""
                UPDATE keyword_tasks SET
                    status = ?,
                    products_found = ?,
                    products_processed = ?,
                    comments_generated = ?,
                    comments_published = ?,
                    errors_count = ?,
                    started_at = ?,
                    completed_at = ?
                WHERE keyword = ?
            """, (
                task.status.value,
                task.products_found,
                task.products_processed,
                task.comments_generated,
                task.comments_published,
                task.errors_count,
                task.started_at,
                task.completed_at,
                task.keyword
            ))
            self.database.commit()
        except Exception as e:
            logging.error(f"更新关键词任务失败: {e}")


def create_keyword_manager() -> KeywordManager:
    """
    创建关键词管理器实例
    
    Returns:
        关键词管理器实例
    """
    return KeywordManager()