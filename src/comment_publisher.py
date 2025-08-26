# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 评论发布器
实现自动发布评论到闲鱼平台，包含反检测机制
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

from config import get_config
from database import get_db

class XianyuCommentPublisher:
    """闲鱼评论发布器"""
    
    def __init__(self, app_controller):
        """
        初始化评论发布器
        
        Args:
            app_controller: APP控制器实例
        """
        self.app = app_controller
        self.driver = app_controller.driver
        self.wait = app_controller.wait
        self.selectors = get_config("xianyu_selectors", {})
        self.anti_detection = get_config("anti_detection", {})
        self.db = get_db()
        
        # 反检测配置
        self.comment_interval = self.anti_detection.get("comment_interval", {"min": 15, "max": 45})
        self.typing_speed = self.anti_detection.get("typing_speed", {"min": 50, "max": 150})
        self.daily_limit = self.anti_detection.get("daily_limit", 100)
        self.hourly_limit = self.anti_detection.get("hourly_limit", 20)
        
        # 发布统计
        self.publish_stats = {
            'total_attempts': 0,
            'successful_publishes': 0,
            'failed_publishes': 0,
            'blocked_attempts': 0,
            'current_session_count': 0
        }
        
        # 发布状态
        self.last_publish_time = 0
        self.current_hour_count = 0
        self.current_hour = time.strftime('%Y-%m-%d %H')
        
        # 错误处理
        self.consecutive_errors = 0
        self.max_consecutive_errors = 5
    
    def publish_comments(self, comments: List[Dict[str, Any]], 
                        product_id: str) -> Dict[str, Any]:
        """
        批量发布评论
        
        Args:
            comments: 评论列表
            product_id: 商品ID
            
        Returns:
            发布结果统计
        """
        try:
            results = {
                'total': len(comments),
                'successful': 0,
                'failed': 0,
                'blocked': 0,
                'details': []
            }
            
            if not self.app.is_connected:
                logging.error("APP未连接，无法发布评论")
                return results
            
            # 检查发布限制
            if not self._check_publish_limits():
                logging.warning("达到发布限制，停止发布")
                results['blocked'] = len(comments)
                return results
            
            logging.info(f"开始批量发布{len(comments)}条评论")
            
            for i, comment in enumerate(comments):
                try:
                    # 检查是否应该停止
                    if not self._should_continue_publishing():
                        logging.info("发布被中断")
                        break
                    
                    # 发布单条评论
                    publish_result = self._publish_single_comment(comment, product_id)
                    
                    # 记录结果
                    if publish_result['success']:
                        results['successful'] += 1
                        self.publish_stats['successful_publishes'] += 1
                        self.consecutive_errors = 0
                    else:
                        results['failed'] += 1
                        self.publish_stats['failed_publishes'] += 1
                        self.consecutive_errors += 1
                    
                    results['details'].append(publish_result)
                    
                    # 更新数据库记录
                    if 'comment_id' in comment:
                        self.db.update_comment_status(
                            comment['comment_id'],
                            'published' if publish_result['success'] else 'failed',
                            publish_result.get('error_message')
                        )
                    
                    # 检查连续错误
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        logging.error("连续错误过多，停止发布")
                        break
                    
                    # 发布间隔控制
                    if i < len(comments) - 1:  # 不是最后一条
                        self._wait_between_comments()
                    
                except Exception as e:
                    logging.error(f"发布第{i+1}条评论异常: {e}")
                    results['failed'] += 1
                    results['details'].append({
                        'success': False,
                        'error_message': str(e),
                        'content': comment.get('content', '')
                    })
            
            # 更新统计
            self.publish_stats['total_attempts'] += len(comments)
            
            logging.info(f"批量发布完成: 成功{results['successful']}条，失败{results['failed']}条")
            return results
            
        except Exception as e:
            logging.error(f"批量发布评论失败: {e}")
            return {
                'total': len(comments),
                'successful': 0,
                'failed': len(comments),
                'blocked': 0,
                'error': str(e)
            }
    
    def _publish_single_comment(self, comment: Dict[str, Any], 
                               product_id: str) -> Dict[str, Any]:
        """
        发布单条评论
        
        Args:
            comment: 评论数据
            product_id: 商品ID
            
        Returns:
            发布结果
        """
        try:
            content = comment.get('content', '')
            comment_type = comment.get('type', 'unknown')
            
            logging.info(f"开始发布评论: {content}")
            
            result = {
                'content': content,
                'type': comment_type,
                'success': False,
                'error_message': None,
                'publish_time': None
            }
            
            # 1. 导航到评论区
            if not self._navigate_to_comment_area():
                result['error_message'] = "无法导航到评论区"
                return result
            
            # 2. 检查评论限制
            if not self._check_comment_restrictions():
                result['error_message'] = "评论受限或被禁止"
                return result
            
            # 3. 点击评论输入框
            input_element = self._find_comment_input()
            if not input_element:
                result['error_message'] = "无法找到评论输入框"
                return result
            
            # 4. 模拟人类输入
            if not self._simulate_human_input(input_element, content):
                result['error_message'] = "输入评论内容失败"
                return result
            
            # 5. 提交评论
            if not self._submit_comment():
                result['error_message'] = "提交评论失败"
                return result
            
            # 6. 验证发布成功
            if self._verify_comment_published():
                result['success'] = True
                result['publish_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                self._update_publish_counters()
                logging.info(f"评论发布成功: {content}")
            else:
                result['error_message'] = "评论发布验证失败"
                logging.warning(f"评论发布验证失败: {content}")
            
            return result
            
        except Exception as e:
            logging.error(f"发布单条评论异常: {e}")
            return {
                'content': comment.get('content', ''),
                'success': False,
                'error_message': str(e)
            }
    
    def _navigate_to_comment_area(self) -> bool:
        """
        导航到评论区域
        
        Returns:
            是否成功导航到评论区
        """
        try:
            # 首先检查当前页面是否已经在评论区附近
            if self._is_comment_area_visible():
                return True
            
            # 尝试滚动到评论区
            max_scrolls = 8
            for scroll_count in range(max_scrolls):
                self.app.scroll_page('down')
                
                # 随机暂停，模拟人类浏览行为
                pause_time = random.uniform(1.0, 2.5)
                time.sleep(pause_time)
                
                # 检查评论区域标识
                if self._is_comment_area_visible():
                    logging.info(f"经过{scroll_count + 1}次滚动找到评论区")
                    return True
            
            # 尝试点击评论按钮（如果存在）
            comment_button_selectors = [
                "//android.widget.TextView[contains(@text,'评论')]",
                "//android.widget.TextView[contains(@text,'留言')]",
                "//android.widget.ImageView[contains(@resource-id,'comment')]",
                "//android.widget.Button[contains(@text,'评论')]"
            ]
            
            for selector in comment_button_selectors:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        element.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            
            logging.warning("无法导航到评论区域")
            return False
            
        except Exception as e:
            logging.error(f"导航到评论区域失败: {e}")
            return False
    
    def _is_comment_area_visible(self) -> bool:
        """
        检查评论区域是否可见
        
        Returns:
            评论区域是否可见
        """
        try:
            # 检查评论相关的标识元素
            comment_indicators = [
                "//android.widget.TextView[contains(@text,'评论')]",
                "//android.widget.TextView[contains(@text,'留言')]", 
                "//android.widget.TextView[contains(@text,'大家都在说')]",
                "//android.widget.EditText[contains(@hint,'评论')]",
                "//android.widget.EditText[contains(@hint,'留言')]",
                "//android.widget.EditText[contains(@hint,'说点什么')]"
            ]
            
            for indicator in comment_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                    for element in elements:
                        if element.is_displayed():
                            return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.debug(f"检查评论区域可见性失败: {e}")
            return False
    
    def _check_comment_restrictions(self) -> bool:
        """
        检查评论限制
        
        Returns:
            是否可以评论
        """
        try:
            # 检查常见的评论限制提示
            restriction_texts = [
                "评论太频繁",
                "请稍后再试",
                "评论功能暂时不可用",
                "系统维护中",
                "账号异常",
                "评论被限制"
            ]
            
            page_source = self.driver.page_source
            for restriction in restriction_texts:
                if restriction in page_source:
                    logging.warning(f"检测到评论限制: {restriction}")
                    return False
            
            # 检查是否需要登录
            login_indicators = ["登录", "请先登录"]
            for indicator in login_indicators:
                if indicator in page_source:
                    logging.warning("需要登录后才能评论")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"检查评论限制失败: {e}")
            return True  # 如果检查失败，默认允许尝试
    
    def _find_comment_input(self) -> Optional[Any]:
        """
        查找评论输入框
        
        Returns:
            评论输入框元素或None
        """
        try:
            # 闲鱼评论输入框的多种可能选择器
            input_selectors = self.selectors.get("comment_input", [])
            
            # 如果配置中没有，使用默认选择器
            if not input_selectors:
                input_selectors = [
                    "//android.widget.EditText[contains(@hint,'评论')]",
                    "//android.widget.EditText[contains(@hint,'留言')]",
                    "//android.widget.EditText[contains(@hint,'说点什么')]",
                    "//android.widget.EditText[contains(@hint,'写评论')]",
                    "//*[contains(@resource-id,'comment_input')]",
                    "//*[contains(@resource-id,'edit_text')]"
                ]
            
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        if (element.is_displayed() and 
                            element.is_enabled() and
                            self._is_valid_input_element(element)):
                            
                            # 点击激活输入框
                            element.click()
                            time.sleep(0.5)
                            
                            logging.info("找到并激活评论输入框")
                            return element
                            
                except Exception as e:
                    logging.debug(f"尝试选择器失败: {selector} - {e}")
                    continue
            
            # 如果没有找到，尝试通用方法
            return self._find_input_generic()
            
        except Exception as e:
            logging.error(f"查找评论输入框失败: {e}")
            return None
    
    def _is_valid_input_element(self, element) -> bool:
        """
        验证是否为有效的输入元素
        
        Args:
            element: 元素对象
            
        Returns:
            是否为有效输入元素
        """
        try:
            # 检查元素类型
            if element.tag_name.lower() != 'android.widget.edittext':
                return False
            
            # 检查位置（应该在屏幕可见区域）
            location = element.location
            size = element.size
            
            if location['y'] < 0 or size['height'] <= 0:
                return False
            
            # 检查提示文本
            hint_text = element.get_attribute('hint') or ''
            content_desc = element.get_attribute('contentDescription') or ''
            
            comment_hints = ['评论', '留言', '说点什么', '写评论', '回复']
            if any(hint in hint_text or hint in content_desc for hint in comment_hints):
                return True
            
            # 如果没有明确提示，但是可编辑且位置合适，也认为有效
            return True
            
        except Exception as e:
            logging.debug(f"验证输入元素失败: {e}")
            return False
    
    def _find_input_generic(self) -> Optional[Any]:
        """
        通用方法查找输入框
        
        Returns:
            输入框元素或None
        """
        try:
            # 获取所有EditText元素
            edit_elements = self.driver.find_elements(
                AppiumBy.XPATH, "//android.widget.EditText"
            )
            
            # 按位置筛选，通常评论框在屏幕下半部分
            screen_size = self.driver.get_window_size()
            candidates = []
            
            for element in edit_elements:
                try:
                    if element.is_displayed() and element.is_enabled():
                        location = element.location
                        # 评论框通常在屏幕下半部分
                        if location['y'] > screen_size['height'] * 0.3:
                            candidates.append((element, location['y']))
                except:
                    continue
            
            if candidates:
                # 按Y坐标排序，选择最下面的输入框（通常是评论框）
                candidates.sort(key=lambda x: x[1], reverse=True)
                selected_element = candidates[0][0]
                
                # 点击激活
                selected_element.click()
                time.sleep(0.5)
                return selected_element
            
            return None
            
        except Exception as e:
            logging.error(f"通用查找输入框失败: {e}")
            return None
    
    def _simulate_human_input(self, input_element, content: str) -> bool:
        """
        模拟人类输入行为
        
        Args:
            input_element: 输入框元素
            content: 要输入的内容
            
        Returns:
            是否输入成功
        """
        try:
            # 清空现有内容
            input_element.clear()
            time.sleep(random.uniform(0.2, 0.5))
            
            # 模拟思考暂停
            if self.anti_detection.get("random_pause", True):
                think_time = random.uniform(0.5, 2.0)
                time.sleep(think_time)
            
            # 逐字符输入，模拟打字速度
            for i, char in enumerate(content):
                input_element.send_keys(char)
                
                # 随机打字间隔
                min_speed = self.typing_speed.get("min", 50)
                max_speed = self.typing_speed.get("max", 150)
                interval = random.randint(min_speed, max_speed) / 1000.0
                time.sleep(interval)
                
                # 偶尔暂停，模拟思考
                if i > 0 and i % random.randint(3, 8) == 0:
                    pause_time = random.uniform(0.1, 0.8)
                    time.sleep(pause_time)
            
            # 输入完成后的暂停
            final_pause = random.uniform(0.5, 1.5)
            time.sleep(final_pause)
            
            # 验证输入内容
            input_text = input_element.text or input_element.get_attribute('text') or ''
            if content in input_text:
                logging.info("评论内容输入成功")
                return True
            else:
                logging.warning(f"输入验证失败: 期望'{content}', 实际'{input_text}'")
                return False
            
        except Exception as e:
            logging.error(f"模拟人类输入失败: {e}")
            return False
    
    def _submit_comment(self) -> bool:
        """
        提交评论
        
        Returns:
            是否提交成功
        """
        try:
            # 查找发送按钮
            send_selectors = self.selectors.get("comment_send", [])
            
            if not send_selectors:
                send_selectors = [
                    "//android.widget.Button[contains(@text,'发送')]",
                    "//android.widget.Button[contains(@text,'提交')]",
                    "//android.widget.TextView[contains(@text,'发送')]",
                    "//android.widget.TextView[contains(@text,'提交')]",
                    "//*[contains(@resource-id,'send')]",
                    "//*[contains(@resource-id,'submit')]",
                    "//android.widget.ImageView[contains(@resource-id,'send')]"
                ]
            
            for selector in send_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # 提交前的随机延迟
                            submit_delay = random.uniform(0.3, 1.2)
                            time.sleep(submit_delay)
                            
                            element.click()
                            time.sleep(2)  # 等待提交处理
                            
                            logging.info("评论提交成功")
                            return True
                            
                except Exception as e:
                    logging.debug(f"尝试发送按钮失败: {selector} - {e}")
                    continue
            
            # 如果没有找到发送按钮，尝试回车键
            try:
                self.driver.press_keycode(66)  # KEYCODE_ENTER
                time.sleep(2)
                logging.info("使用回车键提交评论")
                return True
            except:
                pass
            
            # 最后尝试搜索按钮
            try:
                self.driver.press_keycode(84)  # KEYCODE_SEARCH
                time.sleep(2)
                logging.info("使用搜索键提交评论")
                return True
            except:
                pass
            
            logging.error("无法找到可用的提交方法")
            return False
            
        except Exception as e:
            logging.error(f"提交评论失败: {e}")
            return False
    
    def _verify_comment_published(self) -> bool:
        """
        验证评论是否发布成功
        
        Returns:
            是否发布成功
        """
        try:
            # 等待一段时间让评论显示
            time.sleep(3)
            
            # 检查成功提示
            success_indicators = [
                "//android.widget.TextView[contains(@text,'评论成功')]",
                "//android.widget.TextView[contains(@text,'发送成功')]",
                "//android.widget.TextView[contains(@text,'评论已发布')]",
                "//android.widget.Toast[contains(@text,'成功')]"
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element.is_displayed():
                        logging.info("发现评论成功提示")
                        return True
                except:
                    continue
            
            # 检查输入框是否已清空（通常表示发送成功）
            try:
                input_elements = self.driver.find_elements(
                    AppiumBy.XPATH, "//android.widget.EditText"
                )
                
                for element in input_elements:
                    if element.is_displayed():
                        text = element.text or element.get_attribute('text') or ''
                        if text.strip() == '':
                            logging.info("输入框已清空，评论可能发布成功")
                            return True
            except:
                pass
            
            # 检查页面是否有新的评论内容出现
            # 这个方法不够可靠，因为评论可能需要审核
            
            # 检查是否出现错误提示
            error_indicators = [
                "评论失败", "发送失败", "网络异常", "系统错误",
                "评论太频繁", "请稍后再试"
            ]
            
            page_source = self.driver.page_source
            for error_text in error_indicators:
                if error_text in page_source:
                    logging.warning(f"发现错误提示: {error_text}")
                    return False
            
            # 如果没有明确的错误提示，默认认为成功
            # 这是因为有些平台的评论需要审核，不会立即显示
            logging.info("未发现明确错误，假定评论发布成功")
            return True
            
        except Exception as e:
            logging.error(f"验证评论发布状态失败: {e}")
            return True  # 验证失败时默认认为成功
    
    def _update_publish_counters(self):
        """更新发布计数器"""
        current_time = time.time()
        current_hour = time.strftime('%Y-%m-%d %H')
        
        # 更新小时计数器
        if current_hour != self.current_hour:
            self.current_hour = current_hour
            self.current_hour_count = 0
        
        self.current_hour_count += 1
        self.last_publish_time = current_time
        self.publish_stats['current_session_count'] += 1
    
    def _check_publish_limits(self) -> bool:
        """
        检查发布限制
        
        Returns:
            是否允许发布
        """
        try:
            # 检查小时限制
            current_hour = time.strftime('%Y-%m-%d %H')
            if current_hour != self.current_hour:
                self.current_hour = current_hour
                self.current_hour_count = 0
            
            if self.current_hour_count >= self.hourly_limit:
                logging.warning(f"达到小时发布限制: {self.hourly_limit}")
                return False
            
            # 检查每日限制（从数据库获取今日发布数量）
            today_stats = self.db.get_today_statistics()
            today_published = today_stats.get('comments_published', 0)
            
            if today_published >= self.daily_limit:
                logging.warning(f"达到每日发布限制: {self.daily_limit}")
                return False
            
            return True
            
        except Exception as e:
            logging.error(f"检查发布限制失败: {e}")
            return True  # 检查失败时默认允许
    
    def _should_continue_publishing(self) -> bool:
        """
        检查是否应该继续发布
        
        Returns:
            是否应该继续
        """
        # 检查连续错误数
        if self.consecutive_errors >= self.max_consecutive_errors:
            return False
        
        # 检查APP连接状态
        if not self.app.is_connected:
            return False
        
        # 检查发布限制
        if not self._check_publish_limits():
            return False
        
        return True
    
    def _wait_between_comments(self):
        """评论间隔等待"""
        try:
            min_interval = self.comment_interval.get("min", 15)
            max_interval = self.comment_interval.get("max", 45)
            
            # 基础间隔
            base_interval = random.randint(min_interval, max_interval)
            
            # 根据当前发布频率动态调整
            if self.current_hour_count > 10:
                # 发布较多时，增加间隔
                base_interval = int(base_interval * 1.5)
            
            # 添加随机性
            actual_interval = base_interval + random.uniform(-3, 8)
            actual_interval = max(5, actual_interval)  # 最小5秒间隔
            
            logging.info(f"评论间隔等待: {actual_interval:.1f}秒")
            time.sleep(actual_interval)
            
        except Exception as e:
            logging.error(f"间隔等待失败: {e}")
            time.sleep(15)  # 默认15秒间隔
    
    def get_publish_statistics(self) -> Dict[str, Any]:
        """
        获取发布统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.publish_stats.copy()
        
        # 计算成功率
        if stats['total_attempts'] > 0:
            stats['success_rate'] = (stats['successful_publishes'] / 
                                   stats['total_attempts']) * 100
        else:
            stats['success_rate'] = 0.0
        
        # 添加当前状态
        stats['current_hour_count'] = self.current_hour_count
        stats['hourly_limit'] = self.hourly_limit
        stats['daily_limit'] = self.daily_limit
        stats['consecutive_errors'] = self.consecutive_errors
        
        # 从数据库获取今日统计
        today_stats = self.db.get_today_statistics()
        stats['today_published'] = today_stats.get('comments_published', 0)
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.publish_stats = {
            'total_attempts': 0,
            'successful_publishes': 0,
            'failed_publishes': 0,
            'blocked_attempts': 0,
            'current_session_count': 0
        }
        self.consecutive_errors = 0
        logging.info("发布统计信息已重置")
    
    def set_limits(self, hourly_limit: int = None, daily_limit: int = None):
        """
        设置发布限制
        
        Args:
            hourly_limit: 小时限制
            daily_limit: 每日限制
        """
        if hourly_limit is not None:
            self.hourly_limit = hourly_limit
            logging.info(f"更新小时发布限制: {hourly_limit}")
        
        if daily_limit is not None:
            self.daily_limit = daily_limit
            logging.info(f"更新每日发布限制: {daily_limit}")
    
    def pause_publishing(self, duration: int):
        """
        暂停发布指定时间
        
        Args:
            duration: 暂停时长（秒）
        """
        logging.info(f"暂停发布 {duration} 秒")
        time.sleep(duration)
    
    def emergency_stop(self):
        """紧急停止发布"""
        logging.warning("紧急停止评论发布")
        self.consecutive_errors = self.max_consecutive_errors
    
    def test_comment_function(self) -> bool:
        """
        测试评论功能是否正常
        
        Returns:
            评论功能是否正常
        """
        try:
            # 导航到评论区
            if not self._navigate_to_comment_area():
                return False
            
            # 查找输入框
            input_element = self._find_comment_input()
            if not input_element:
                return False
            
            # 测试输入（不提交）
            test_content = "测试"
            input_element.clear()
            input_element.send_keys(test_content)
            time.sleep(1)
            
            # 清空测试内容
            input_element.clear()
            
            logging.info("评论功能测试通过")
            return True
            
        except Exception as e:
            logging.error(f"评论功能测试失败: {e}")
            return False


# 便捷函数
def create_comment_publisher(app_controller) -> XianyuCommentPublisher:
    """
    创建评论发布器实例
    
    Args:
        app_controller: APP控制器实例
        
    Returns:
        评论发布器实例
    """
    return XianyuCommentPublisher(app_controller)

def publish_xianyu_comments(app_controller, comments: List[Dict[str, Any]], 
                          product_id: str) -> Dict[str, Any]:
    """
    发布闲鱼评论的便捷函数
    
    Args:
        app_controller: APP控制器
        comments: 评论列表
        product_id: 商品ID
        
    Returns:
        发布结果
    """
    publisher = create_comment_publisher(app_controller)
    return publisher.publish_comments(comments, product_id)