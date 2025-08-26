# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 数据库管理模块
管理商品数据、评论记录和统计信息
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import threading

class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        if db_path is None:
            self.db_path = Path(__file__).parent.parent / "data" / "xianyu_assistant.db"
        else:
            self.db_path = Path(db_path)
        
        # 确保数据目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程锁，确保数据库操作的线程安全
        self._lock = threading.Lock()
        
        # 初始化数据库表
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row  # 启用字典式访问
        return conn
    
    def init_database(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # 创建商品信息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id TEXT PRIMARY KEY,
                        url TEXT NOT NULL UNIQUE,
                        title TEXT,
                        price REAL,
                        seller TEXT,
                        location TEXT,
                        condition_score INTEGER,
                        description TEXT,
                        existing_comments TEXT,  -- JSON格式存储现有评论
                        market_analysis TEXT,    -- JSON格式存储市场分析
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建评论记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        comment_type TEXT,  -- inquiry, interest, compliment等
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        published_at TIMESTAMP,
                        status TEXT DEFAULT 'pending',  -- pending, published, failed
                        error_message TEXT,
                        ai_prompt TEXT,  -- 生成评论使用的AI提示词
                        FOREIGN KEY (product_id) REFERENCES products (id)
                    )
                ''')
                
                # 创建任务记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_name TEXT,
                        product_urls TEXT,  -- JSON格式存储URL列表
                        comment_types TEXT,  -- JSON格式存储评论类型
                        total_products INTEGER,
                        completed_products INTEGER,
                        successful_comments INTEGER,
                        failed_comments INTEGER,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        status TEXT DEFAULT 'running',  -- running, completed, failed, stopped
                        error_log TEXT
                    )
                ''')
                
                # 创建系统统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS statistics (
                        date TEXT PRIMARY KEY,  -- YYYY-MM-DD格式
                        products_processed INTEGER DEFAULT 0,
                        comments_generated INTEGER DEFAULT 0,
                        comments_published INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 0.0,
                        avg_processing_time REAL DEFAULT 0.0,
                        error_count INTEGER DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建错误日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS error_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        module TEXT,
                        function TEXT,
                        error_type TEXT,
                        error_message TEXT,
                        traceback TEXT,
                        product_id TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建配置表（用于存储运行时配置）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS runtime_config (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建关键词任务表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyword_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        keyword TEXT NOT NULL,
                        priority INTEGER DEFAULT 1,
                        max_products INTEGER DEFAULT 50,
                        status TEXT DEFAULT 'pending',
                        products_found INTEGER DEFAULT 0,
                        products_processed INTEGER DEFAULT 0,
                        comments_generated INTEGER DEFAULT 0,
                        comments_published INTEGER DEFAULT 0,
                        errors_count INTEGER DEFAULT 0,
                        created_at REAL,
                        started_at REAL,
                        completed_at REAL,
                        enable_pagination BOOLEAN DEFAULT 1,
                        max_pages INTEGER DEFAULT 5,
                        UNIQUE(keyword, status) ON CONFLICT REPLACE
                    )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_url ON products (url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_product_id ON comments (product_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_status ON comments (status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_published_at ON comments (published_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON error_logs (created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_tasks_status ON keyword_tasks (status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword_tasks_priority ON keyword_tasks (priority)')
                
                conn.commit()
                logging.info("数据库初始化完成")
                
            except sqlite3.Error as e:
                logging.error(f"数据库初始化失败: {e}")
                conn.rollback()
                raise
            finally:
                conn.close()
    
    def save_product(self, product_info: Dict[str, Any]) -> bool:
        """
        保存商品信息
        
        Args:
            product_info: 商品信息字典
            
        Returns:
            是否保存成功
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # 准备数据
                existing_comments = json.dumps(product_info.get('existing_comments', []), 
                                             ensure_ascii=False)
                market_analysis = json.dumps(product_info.get('market_analysis', {}), 
                                           ensure_ascii=False)
                
                # 使用REPLACE语句实现插入或更新
                cursor.execute('''
                    REPLACE INTO products (
                        id, url, title, price, seller, location, condition_score,
                        description, existing_comments, market_analysis, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    product_info.get('id'),
                    product_info.get('url'),
                    product_info.get('title'),
                    product_info.get('price'),
                    product_info.get('seller'),
                    product_info.get('location'),
                    product_info.get('condition_score'),
                    product_info.get('description'),
                    existing_comments,
                    market_analysis
                ))
                
                conn.commit()
                logging.info(f"商品信息已保存: {product_info.get('title')}")
                return True
                
            except sqlite3.Error as e:
                logging.error(f"保存商品信息失败: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
    
    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        获取商品信息
        
        Args:
            product_id: 商品ID
            
        Returns:
            商品信息字典或None
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
                row = cursor.fetchone()
                
                if row:
                    product = dict(row)
                    # 解析JSON字段
                    product['existing_comments'] = json.loads(product['existing_comments'] or '[]')
                    product['market_analysis'] = json.loads(product['market_analysis'] or '{}')
                    return product
                
                return None
                
            except sqlite3.Error as e:
                logging.error(f"获取商品信息失败: {e}")
                return None
            finally:
                conn.close()
    
    def save_comment(self, comment_data: Dict[str, Any]) -> Optional[int]:
        """
        保存评论记录
        
        Args:
            comment_data: 评论数据字典
            
        Returns:
            评论ID或None
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO comments (
                        product_id, content, comment_type, ai_prompt, status
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    comment_data.get('product_id'),
                    comment_data.get('content'),
                    comment_data.get('type'),
                    comment_data.get('ai_prompt'),
                    comment_data.get('status', 'pending')
                ))
                
                comment_id = cursor.lastrowid
                conn.commit()
                logging.info(f"评论记录已保存: ID {comment_id}")
                return comment_id
                
            except sqlite3.Error as e:
                logging.error(f"保存评论记录失败: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
    
    def update_comment_status(self, comment_id: int, status: str, 
                             error_message: str = None) -> bool:
        """
        更新评论发布状态
        
        Args:
            comment_id: 评论ID
            status: 新状态 (published, failed)
            error_message: 错误消息（可选）
            
        Returns:
            是否更新成功
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                if status == 'published':
                    cursor.execute('''
                        UPDATE comments 
                        SET status = ?, published_at = CURRENT_TIMESTAMP, error_message = NULL
                        WHERE id = ?
                    ''', (status, comment_id))
                else:
                    cursor.execute('''
                        UPDATE comments 
                        SET status = ?, error_message = ?
                        WHERE id = ?
                    ''', (status, error_message, comment_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
            except sqlite3.Error as e:
                logging.error(f"更新评论状态失败: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
    
    def save_task(self, task_data: Dict[str, Any]) -> Optional[int]:
        """
        保存任务记录
        
        Args:
            task_data: 任务数据字典
            
        Returns:
            任务ID或None
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                product_urls = json.dumps(task_data.get('product_urls', []))
                comment_types = json.dumps(task_data.get('comment_types', []))
                
                cursor.execute('''
                    INSERT INTO tasks (
                        task_name, product_urls, comment_types, total_products,
                        completed_products, successful_comments, failed_comments, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_data.get('task_name'),
                    product_urls,
                    comment_types,
                    task_data.get('total_products', 0),
                    task_data.get('completed_products', 0),
                    task_data.get('successful_comments', 0),
                    task_data.get('failed_comments', 0),
                    task_data.get('status', 'running')
                ))
                
                task_id = cursor.lastrowid
                conn.commit()
                return task_id
                
            except sqlite3.Error as e:
                logging.error(f"保存任务记录失败: {e}")
                conn.rollback()
                return None
            finally:
                conn.close()
    
    def update_task_progress(self, task_id: int, progress_data: Dict[str, Any]) -> bool:
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress_data: 进度数据
            
        Returns:
            是否更新成功
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # 构建更新语句
                update_fields = []
                values = []
                
                for field in ['completed_products', 'successful_comments', 
                             'failed_comments', 'status', 'error_log']:
                    if field in progress_data:
                        update_fields.append(f"{field} = ?")
                        values.append(progress_data[field])
                
                if progress_data.get('status') in ['completed', 'failed', 'stopped']:
                    update_fields.append("end_time = CURRENT_TIMESTAMP")
                
                if update_fields:
                    values.append(task_id)
                    sql = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
                    cursor.execute(sql, values)
                    conn.commit()
                    return cursor.rowcount > 0
                
                return True
                
            except sqlite3.Error as e:
                logging.error(f"更新任务进度失败: {e}")
                conn.rollback()
                return False
            finally:
                conn.close()
    
    def get_today_statistics(self) -> Dict[str, Any]:
        """
        获取今日统计数据
        
        Returns:
            统计数据字典
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # 获取今日基本统计
                cursor.execute('''
                    SELECT * FROM statistics WHERE date = ?
                ''', (today,))
                
                stats_row = cursor.fetchone()
                if stats_row:
                    stats = dict(stats_row)
                else:
                    # 如果没有今日记录，创建默认统计
                    stats = {
                        'date': today,
                        'products_processed': 0,
                        'comments_generated': 0,
                        'comments_published': 0,
                        'success_rate': 0.0,
                        'avg_processing_time': 0.0,
                        'error_count': 0
                    }
                
                # 获取实时统计数据
                cursor.execute('''
                    SELECT 
                        COUNT(DISTINCT product_id) as products_today,
                        COUNT(*) as comments_today,
                        SUM(CASE WHEN status = 'published' THEN 1 ELSE 0 END) as published_today
                    FROM comments 
                    WHERE DATE(generated_at) = ?
                ''', (today,))
                
                real_time = cursor.fetchone()
                if real_time:
                    stats.update({
                        'products_processed': real_time['products_today'] or 0,
                        'comments_generated': real_time['comments_today'] or 0,
                        'comments_published': real_time['published_today'] or 0
                    })
                    
                    # 计算成功率
                    if stats['comments_generated'] > 0:
                        stats['success_rate'] = (stats['comments_published'] / 
                                               stats['comments_generated']) * 100
                
                return stats
                
            except sqlite3.Error as e:
                logging.error(f"获取今日统计失败: {e}")
                return {}
            finally:
                conn.close()
    
    def update_daily_statistics(self):
        """更新每日统计数据"""
        today = datetime.now().strftime('%Y-%m-%d')
        stats = self.get_today_statistics()
        
        if not stats:
            return
        
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    REPLACE INTO statistics (
                        date, products_processed, comments_generated, 
                        comments_published, success_rate, error_count, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (
                    today,
                    stats.get('products_processed', 0),
                    stats.get('comments_generated', 0),
                    stats.get('comments_published', 0),
                    stats.get('success_rate', 0.0),
                    stats.get('error_count', 0)
                ))
                
                conn.commit()
                
            except sqlite3.Error as e:
                logging.error(f"更新每日统计失败: {e}")
                conn.rollback()
            finally:
                conn.close()
    
    def log_error(self, module: str, function: str, error_type: str, 
                  error_message: str, traceback_str: str = None, 
                  product_id: str = None):
        """
        记录错误日志
        
        Args:
            module: 模块名
            function: 函数名
            error_type: 错误类型
            error_message: 错误消息
            traceback_str: 异常堆栈（可选）
            product_id: 相关商品ID（可选）
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO error_logs (
                        module, function, error_type, error_message, 
                        traceback, product_id
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (module, function, error_type, error_message, 
                      traceback_str, product_id))
                
                conn.commit()
                
            except sqlite3.Error as e:
                logging.error(f"记录错误日志失败: {e}")
                conn.rollback()
            finally:
                conn.close()
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取最近的错误记录
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            错误记录列表
        """
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM error_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
                
            except sqlite3.Error as e:
                logging.error(f"获取错误记录失败: {e}")
                return []
            finally:
                conn.close()
    
    def cleanup_old_data(self, days: int = 30):
        """
        清理旧数据
        
        Args:
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        with self._lock:
            conn = self.get_connection()
            try:
                cursor = conn.cursor()
                
                # 清理旧的错误日志
                cursor.execute('DELETE FROM error_logs WHERE created_at < ?', (cutoff_str,))
                
                # 清理旧的任务记录
                cursor.execute('DELETE FROM tasks WHERE end_time < ?', (cutoff_str,))
                
                # 清理旧的统计数据（保留更长时间，比如90天）
                stats_cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                cursor.execute('DELETE FROM statistics WHERE date < ?', (stats_cutoff,))
                
                conn.commit()
                logging.info(f"已清理 {days} 天前的旧数据")
                
            except sqlite3.Error as e:
                logging.error(f"清理旧数据失败: {e}")
                conn.rollback()
            finally:
                conn.close()
    
    def backup_database(self, backup_path: str = None) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否备份成功
        """
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = self.db_path.parent / f"backup_xianyu_assistant_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"数据库已备份到: {backup_path}")
            return True
            
        except Exception as e:
            logging.error(f"数据库备份失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        # SQLite连接是自动管理的，这里主要做一些清理工作
        pass


# 全局数据库实例
db = Database()

# 便捷访问函数
def get_db() -> Database:
    """获取数据库实例"""
    return db