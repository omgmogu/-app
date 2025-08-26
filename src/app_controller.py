# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - APP控制器
专门用于控制闲鱼APP的自动化操作
"""

import time
import random
import logging
from typing import Dict, List, Any, Optional, Tuple
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

from config import get_config, get_xianyu_app_config

class XianyuAppController:
    """闲鱼APP控制器"""
    
    def __init__(self, device_id: str = None):
        """
        初始化闲鱼APP控制器
        
        Args:
            device_id: 设备ID，如果为None则使用默认设备
        """
        self.device_id = device_id
        self.driver = None
        self.wait = None
        self.app_config = get_xianyu_app_config()
        self.selectors = get_config("xianyu_selectors", {})
        self.anti_detection = get_config("anti_detection", {})
        
        # 连接状态
        self.is_connected = False
        self.current_activity = None
        
        # 操作统计
        self.operation_count = 0
        self.error_count = 0
    
    def connect(self) -> bool:
        """
        连接到闲鱼APP
        
        Returns:
            是否连接成功
        """
        try:
            # 获取Appium配置
            appium_config = get_config("appium", {})
            desired_caps = appium_config.get("desired_caps", {}).copy()
            
            # 添加设备ID（如果指定）
            if self.device_id:
                desired_caps["udid"] = self.device_id
            
            # 创建WebDriver连接
            server_url = appium_config.get("server_url", "http://localhost:4723/wd/hub")
            self.driver = webdriver.Remote(server_url, desired_caps)
            
            # 设置等待器
            implicit_wait = appium_config.get("implicit_wait", 10)
            self.driver.implicitly_wait(implicit_wait)
            self.wait = WebDriverWait(self.driver, 30)
            
            # 等待APP加载
            time.sleep(3)
            
            # 验证连接
            if self._verify_xianyu_app():
                self.is_connected = True
                logging.info("成功连接到闲鱼APP")
                return True
            else:
                logging.error("连接到APP但验证失败")
                self.disconnect()
                return False
                
        except Exception as e:
            logging.error(f"连接闲鱼APP失败: {e}")
            self.is_connected = False
            return False
    
    def _verify_xianyu_app(self) -> bool:
        """
        验证当前是否在闲鱼APP中
        
        Returns:
            是否在闲鱼APP中
        """
        try:
            # 检查APP包名
            current_package = self.driver.current_package
            if current_package != self.app_config.get("package_name", "com.taobao.idlefish"):
                logging.warning(f"当前APP包名不匹配: {current_package}")
                return False
            
            # 检查是否存在闲鱼特有的元素
            xianyu_indicators = [
                "//android.widget.TextView[@text='首页']",
                "//android.widget.TextView[@text='闲鱼']",
                "//android.widget.TabWidget",
                "//*[contains(@resource-id,'idlefish')]"
            ]
            
            for indicator in xianyu_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element:
                        logging.info("验证闲鱼APP成功")
                        return True
                except:
                    continue
            
            logging.warning("无法找到闲鱼APP特征元素")
            return False
            
        except Exception as e:
            logging.error(f"验证闲鱼APP失败: {e}")
            return False
    
    def navigate_to_product(self, product_url: str) -> bool:
        """
        导航到指定商品页面
        
        Args:
            product_url: 商品URL
            
        Returns:
            是否导航成功
        """
        if not self.is_connected:
            logging.error("未连接到APP")
            return False
        
        try:
            # 记录操作
            self.operation_count += 1
            
            # 方法1：尝试通过URL Scheme跳转
            if self._navigate_by_url_scheme(product_url):
                return True
            
            # 方法2：通过搜索功能导航
            if self._navigate_by_search(product_url):
                return True
            
            # 方法3：通过商品ID搜索
            product_id = self._extract_product_id(product_url)
            if product_id and self._navigate_by_product_id(product_id):
                return True
            
            logging.error(f"所有导航方法均失败: {product_url}")
            return False
            
        except Exception as e:
            logging.error(f"导航到商品页面失败: {e}")
            self.error_count += 1
            return False
    
    def _navigate_by_url_scheme(self, product_url: str) -> bool:
        """
        通过URL Scheme导航到商品页面
        
        Args:
            product_url: 商品URL
            
        Returns:
            是否成功
        """
        try:
            # 提取商品ID
            product_id = self._extract_product_id(product_url)
            if not product_id:
                return False
            
            # 构建闲鱼URL Scheme
            scheme_url = f"fleamarket://item?id={product_id}"
            
            # 使用深链接跳转
            self.driver.get(scheme_url)
            time.sleep(3)
            
            # 验证是否到达商品页面
            if self._verify_product_page():
                logging.info(f"URL Scheme导航成功: {product_id}")
                return True
            
            return False
            
        except Exception as e:
            logging.debug(f"URL Scheme导航失败: {e}")
            return False
    
    def _navigate_by_search(self, product_url: str) -> bool:
        """
        通过搜索功能导航到商品页面
        
        Args:
            product_url: 商品URL
            
        Returns:
            是否成功
        """
        try:
            # 首先确保在首页
            if not self._go_to_home():
                return False
            
            # 点击搜索按钮
            search_btn_selector = self.selectors.get("search_btn")
            if not search_btn_selector:
                return False
            
            search_btn = self.wait.until(
                EC.element_to_be_clickable((AppiumBy.ID, search_btn_selector))
            )
            search_btn.click()
            time.sleep(1)
            
            # 在搜索框中输入URL
            search_input_selector = self.selectors.get("search_input")
            search_input = self.wait.until(
                EC.presence_of_element_located((AppiumBy.ID, search_input_selector))
            )
            search_input.clear()
            
            # 模拟人类输入
            self._human_type(search_input, product_url)
            
            # 点击搜索
            search_confirm_selector = self.selectors.get("search_confirm")
            search_confirm = self.driver.find_element(AppiumBy.ID, search_confirm_selector)
            search_confirm.click()
            
            time.sleep(3)
            
            # 查找并点击匹配的商品
            if self._click_matching_product(product_url):
                return True
            
            return False
            
        except Exception as e:
            logging.debug(f"搜索导航失败: {e}")
            return False
    
    def _navigate_by_product_id(self, product_id: str) -> bool:
        """
        通过商品ID搜索导航
        
        Args:
            product_id: 商品ID
            
        Returns:
            是否成功
        """
        try:
            # 通过搜索商品ID
            return self._navigate_by_search(product_id)
            
        except Exception as e:
            logging.debug(f"商品ID导航失败: {e}")
            return False
    
    def _go_to_home(self) -> bool:
        """
        返回首页
        
        Returns:
            是否成功
        """
        try:
            # 查找首页标签
            home_selectors = [
                "//android.widget.TextView[@text='首页']",
                "//android.widget.TextView[@text='闲鱼']",
                "//*[contains(@resource-id,'tab_home')]"
            ]
            
            for selector in home_selectors:
                try:
                    home_tab = self.driver.find_element(AppiumBy.XPATH, selector)
                    if home_tab.is_displayed():
                        home_tab.click()
                        time.sleep(2)
                        return True
                except:
                    continue
            
            # 如果找不到首页标签，尝试返回键
            self.driver.back()
            time.sleep(1)
            return True
            
        except Exception as e:
            logging.debug(f"返回首页失败: {e}")
            return False
    
    def _extract_product_id(self, url: str) -> Optional[str]:
        """
        从URL中提取商品ID
        
        Args:
            url: 商品URL
            
        Returns:
            商品ID或None
        """
        try:
            # 闲鱼URL的几种模式
            patterns = [
                r'item[/.](\d+)',
                r'id[=:](\d+)',
                r'/(\d+)\.htm',
                r'/(\d+)$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # 如果是数字，直接返回
            if url.isdigit():
                return url
            
            return None
            
        except Exception as e:
            logging.debug(f"提取商品ID失败: {e}")
            return None
    
    def _verify_product_page(self) -> bool:
        """
        验证当前是否在商品详情页
        
        Returns:
            是否在商品页面
        """
        try:
            # 检查商品页面特征元素
            product_indicators = [
                self.selectors.get("product_title"),
                self.selectors.get("product_price"),
                "//android.widget.TextView[contains(@text,'¥')]",
                "//android.widget.Button[contains(@text,'立即购买')]",
                "//android.widget.Button[contains(@text,'我想要')]",
                "//*[contains(@text,'商品详情')]"
            ]
            
            for indicator in product_indicators:
                if not indicator:
                    continue
                    
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element and element.is_displayed():
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.debug(f"验证商品页面失败: {e}")
            return False
    
    def _click_matching_product(self, target_url: str) -> bool:
        """
        在搜索结果中点击匹配的商品
        
        Args:
            target_url: 目标商品URL
            
        Returns:
            是否找到并点击了匹配商品
        """
        try:
            # 等待搜索结果加载
            time.sleep(3)
            
            # 查找商品卡片
            product_cards = self.driver.find_elements(
                AppiumBy.XPATH,
                "//android.widget.LinearLayout[contains(@resource-id,'item')]"
            )
            
            target_id = self._extract_product_id(target_url)
            
            for card in product_cards:
                try:
                    # 点击商品卡片
                    card.click()
                    time.sleep(2)
                    
                    # 检查是否是目标商品
                    if self._verify_product_page():
                        # 如果有目标ID，进一步验证
                        if target_id:
                            current_url = self.driver.current_url
                            if target_id in current_url:
                                return True
                        else:
                            return True
                    
                    # 如果不是目标商品，返回搜索结果页
                    self.driver.back()
                    time.sleep(1)
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.debug(f"点击匹配商品失败: {e}")
            return False
    
    def search_by_keyword(self, keyword: str) -> bool:
        """
        根据关键词进行搜索
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            是否搜索成功
        """
        if not self.is_connected:
            logging.error("未连接到APP")
            return False
            
        try:
            self.operation_count += 1
            
            # 首先确保在首页
            if not self._go_to_home():
                return False
            
            # 点击搜索按钮
            search_btn_selector = self.selectors.get("search_btn")
            if not search_btn_selector:
                logging.error("未找到搜索按钮选择器配置")
                return False
            
            search_btn = self.wait.until(
                EC.element_to_be_clickable((AppiumBy.ID, search_btn_selector))
            )
            search_btn.click()
            time.sleep(1)
            
            # 在搜索框中输入关键词
            search_input_selector = self.selectors.get("search_input")
            search_input = self.wait.until(
                EC.presence_of_element_located((AppiumBy.ID, search_input_selector))
            )
            search_input.clear()
            
            # 模拟人类输入
            self._human_type(search_input, keyword)
            
            # 点击搜索确认
            search_confirm_selector = self.selectors.get("search_confirm")
            search_confirm = self.driver.find_element(AppiumBy.ID, search_confirm_selector)
            search_confirm.click()
            
            # 等待搜索结果加载
            time.sleep(3)
            
            # 验证是否到达搜索结果页面
            if self._verify_search_results_page():
                logging.info(f"关键词搜索成功: {keyword}")
                return True
            else:
                logging.error(f"搜索结果页面验证失败: {keyword}")
                return False
                
        except Exception as e:
            logging.error(f"关键词搜索失败: {e}")
            self.error_count += 1
            return False
    
    def get_all_product_cards(self) -> List[Any]:
        """
        获取当前搜索结果页面的所有商品卡
        
        Returns:
            商品卡元素列表
        """
        try:
            # 等待页面加载
            time.sleep(2)
            
            # 多种商品卡选择器策略
            card_selectors = [
                "//android.widget.LinearLayout[contains(@resource-id,'item')]",
                "//android.widget.RelativeLayout[contains(@resource-id,'item')]",
                "//android.view.ViewGroup[contains(@resource-id,'product')]",
                "//*[contains(@resource-id,'goods_item')]",
                "//*[contains(@class,'item') and contains(@clickable,'true')]"
            ]
            
            product_cards = []
            for selector in card_selectors:
                try:
                    cards = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if cards:
                        product_cards = cards
                        logging.info(f"找到 {len(cards)} 个商品卡 (使用选择器: {selector})")
                        break
                except:
                    continue
            
            if not product_cards:
                logging.warning("未找到任何商品卡")
            
            return product_cards
            
        except Exception as e:
            logging.error(f"获取商品卡失败: {e}")
            return []
    
    def click_product_card_by_index(self, index: int) -> bool:
        """
        点击指定索引的商品卡
        
        Args:
            index: 商品卡索引（从0开始）
            
        Returns:
            是否点击成功
        """
        try:
            product_cards = self.get_all_product_cards()
            
            if not product_cards or index >= len(product_cards):
                logging.error(f"商品卡索引超出范围: {index}/{len(product_cards)}")
                return False
            
            # 确保商品卡在可见区域
            card = product_cards[index]
            self.driver.execute_script("arguments[0].scrollIntoView(true);", card)
            time.sleep(0.5)
            
            # 点击商品卡
            card.click()
            time.sleep(2)
            
            # 验证是否进入商品详情页
            if self._verify_product_page():
                logging.info(f"成功点击商品卡 #{index}")
                return True
            else:
                logging.error(f"点击商品卡后页面验证失败: #{index}")
                return False
                
        except Exception as e:
            logging.error(f"点击商品卡失败 #{index}: {e}")
            return False
    
    def navigate_back_to_search_results(self) -> bool:
        """
        从商品详情页返回搜索结果页
        
        Returns:
            是否返回成功
        """
        try:
            # 尝试点击返回按钮
            back_selectors = [
                "//android.widget.ImageView[contains(@resource-id,'back')]",
                "//android.widget.ImageButton[contains(@resource-id,'back')]",
                "//android.widget.Button[contains(@content-desc,'返回')]",
                "//android.widget.TextView[contains(@text,'返回')]"
            ]
            
            for selector in back_selectors:
                try:
                    back_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                    if back_btn.is_displayed():
                        back_btn.click()
                        time.sleep(2)
                        
                        # 验证是否回到搜索结果页
                        if self._verify_search_results_page():
                            logging.info("成功返回搜索结果页")
                            return True
                        break
                except:
                    continue
            
            # 如果找不到返回按钮，使用系统返回键
            self.driver.back()
            time.sleep(2)
            
            if self._verify_search_results_page():
                logging.info("使用系统返回键返回搜索结果页")
                return True
            
            logging.error("返回搜索结果页失败")
            return False
            
        except Exception as e:
            logging.error(f"返回搜索结果页失败: {e}")
            return False
    
    def scroll_to_load_more_products(self) -> bool:
        """
        滚动页面加载更多商品
        
        Returns:
            是否滚动成功
        """
        try:
            # 获取滚动前的商品卡数量
            cards_before = len(self.get_all_product_cards())
            
            # 滚动到页面底部
            self.scroll_page("down")
            time.sleep(2)
            
            # 等待新内容加载
            for _ in range(3):
                time.sleep(1)
                cards_after = len(self.get_all_product_cards())
                if cards_after > cards_before:
                    logging.info(f"成功加载更多商品: {cards_before} → {cards_after}")
                    return True
            
            logging.info("滚动完成，但没有加载到更多商品")
            return False
            
        except Exception as e:
            logging.error(f"滚动加载更多商品失败: {e}")
            return False
    
    def has_more_products(self) -> bool:
        """
        检查是否还有更多商品可以加载
        
        Returns:
            是否还有更多商品
        """
        try:
            # 检查页面底部是否有"加载更多"、"没有更多了"等标识
            end_indicators = [
                "//android.widget.TextView[contains(@text,'没有更多')]",
                "//android.widget.TextView[contains(@text,'到底了')]",
                "//android.widget.TextView[contains(@text,'已全部加载')]",
                "//*[contains(@text,'no more')]",
                "//*[contains(@resource-id,'loading_end')]"
            ]
            
            for indicator in end_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element and element.is_displayed():
                        logging.info("检测到页面底部标识，没有更多商品")
                        return False
                except:
                    continue
            
            # 尝试滚动测试
            cards_before = len(self.get_all_product_cards())
            test_scroll = self.scroll_to_load_more_products()
            
            if not test_scroll:
                return False
            
            # 如果滚动后商品数量没有增加，可能已到底部
            cards_after = len(self.get_all_product_cards())
            return cards_after > cards_before
            
        except Exception as e:
            logging.error(f"检查更多商品失败: {e}")
            return False
    
    def _verify_search_results_page(self) -> bool:
        """
        验证当前是否在搜索结果页面
        
        Returns:
            是否在搜索结果页面
        """
        try:
            # 搜索结果页面特征元素
            search_result_indicators = [
                "//android.widget.TextView[contains(@text,'搜索结果')]",
                "//android.widget.TextView[contains(@text,'找到')]",
                "//*[contains(@resource-id,'search_result')]",
                "//*[contains(@resource-id,'goods_list')]",
                "//android.widget.RecyclerView",
                "//android.widget.ListView"
            ]
            
            for indicator in search_result_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element:
                        return True
                except:
                    continue
            
            # 如果找到商品卡，也认为是搜索结果页面
            product_cards = self.get_all_product_cards()
            return len(product_cards) > 0
            
        except Exception as e:
            logging.debug(f"验证搜索结果页面失败: {e}")
            return False
    
    def scroll_page(self, direction: str = "down", distance: int = None) -> bool:
        """
        滚动页面
        
        Args:
            direction: 滚动方向 ('up', 'down', 'left', 'right')
            distance: 滚动距离，None表示使用默认距离
            
        Returns:
            是否滚动成功
        """
        try:
            size = self.driver.get_window_size()
            width = size["width"]
            height = size["height"]
            
            # 默认滚动距离
            if distance is None:
                distance = height // 3
            
            if direction == "down":
                start_y = height * 0.8
                end_y = height * 0.2
                self.driver.swipe(width // 2, start_y, width // 2, end_y, 800)
            elif direction == "up":
                start_y = height * 0.2
                end_y = height * 0.8
                self.driver.swipe(width // 2, start_y, width // 2, end_y, 800)
            elif direction == "left":
                start_x = width * 0.8
                end_x = width * 0.2
                self.driver.swipe(start_x, height // 2, end_x, height // 2, 800)
            elif direction == "right":
                start_x = width * 0.2
                end_x = width * 0.8
                self.driver.swipe(start_x, height // 2, end_x, height // 2, 800)
            
            # 随机暂停
            if self.anti_detection.get("random_pause", True):
                pause_time = random.uniform(0.5, 1.5)
                time.sleep(pause_time)
            
            return True
            
        except Exception as e:
            logging.error(f"滚动页面失败: {e}")
            return False
    
    def _human_type(self, element, text: str):
        """
        模拟人类输入行为
        
        Args:
            element: 输入元素
            text: 要输入的文本
        """
        try:
            # 清空现有内容
            element.clear()
            time.sleep(0.2)
            
            # 获取打字速度配置
            typing_speed = self.anti_detection.get("typing_speed", {"min": 50, "max": 150})
            
            # 逐字符输入
            for char in text:
                element.send_keys(char)
                
                # 随机输入间隔
                interval = random.randint(typing_speed["min"], typing_speed["max"]) / 1000.0
                time.sleep(interval)
            
            # 输入完成后的随机暂停
            pause_time = random.uniform(0.3, 1.0)
            time.sleep(pause_time)
            
        except Exception as e:
            logging.error(f"模拟输入失败: {e}")
            # 如果模拟输入失败，使用普通输入
            element.clear()
            element.send_keys(text)
    
    def take_screenshot(self, filename: str = None) -> str:
        """
        截图
        
        Args:
            filename: 文件名，如果为None则自动生成
            
        Returns:
            截图文件路径
        """
        try:
            if filename is None:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            
            # 确保screenshots目录存在
            from pathlib import Path
            screenshots_dir = Path(__file__).parent.parent / "data" / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            
            screenshot_path = screenshots_dir / filename
            
            # 保存截图
            self.driver.save_screenshot(str(screenshot_path))
            logging.info(f"截图已保存: {screenshot_path}")
            
            return str(screenshot_path)
            
        except Exception as e:
            logging.error(f"截图失败: {e}")
            return ""
    
    def get_page_source(self) -> str:
        """
        获取当前页面源代码
        
        Returns:
            页面源代码
        """
        try:
            return self.driver.page_source
        except Exception as e:
            logging.error(f"获取页面源代码失败: {e}")
            return ""
    
    def get_current_activity(self) -> str:
        """
        获取当前Activity
        
        Returns:
            当前Activity名称
        """
        try:
            activity = self.driver.current_activity
            self.current_activity = activity
            return activity
        except Exception as e:
            logging.error(f"获取当前Activity失败: {e}")
            return ""
    
    def is_element_present(self, locator_type: str, locator_value: str) -> bool:
        """
        检查元素是否存在
        
        Args:
            locator_type: 定位器类型（id, xpath, class等）
            locator_value: 定位器值
            
        Returns:
            元素是否存在
        """
        try:
            # 临时设置较短的等待时间
            self.driver.implicitly_wait(2)
            
            if locator_type.lower() == "id":
                element = self.driver.find_element(AppiumBy.ID, locator_value)
            elif locator_type.lower() == "xpath":
                element = self.driver.find_element(AppiumBy.XPATH, locator_value)
            elif locator_type.lower() == "class":
                element = self.driver.find_element(AppiumBy.CLASS_NAME, locator_value)
            else:
                return False
            
            return element is not None
            
        except NoSuchElementException:
            return False
        except Exception as e:
            logging.debug(f"检查元素存在性失败: {e}")
            return False
        finally:
            # 恢复原来的等待时间
            implicit_wait = get_config("appium.implicit_wait", 10)
            self.driver.implicitly_wait(implicit_wait)
    
    def wait_for_element(self, locator_type: str, locator_value: str, 
                        timeout: int = 10) -> Optional[Any]:
        """
        等待元素出现
        
        Args:
            locator_type: 定位器类型
            locator_value: 定位器值
            timeout: 超时时间
            
        Returns:
            元素对象或None
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            if locator_type.lower() == "id":
                locator = (AppiumBy.ID, locator_value)
            elif locator_type.lower() == "xpath":
                locator = (AppiumBy.XPATH, locator_value)
            elif locator_type.lower() == "class":
                locator = (AppiumBy.CLASS_NAME, locator_value)
            else:
                return None
            
            element = wait.until(EC.presence_of_element_located(locator))
            return element
            
        except TimeoutException:
            logging.debug(f"等待元素超时: {locator_type}={locator_value}")
            return None
        except Exception as e:
            logging.error(f"等待元素失败: {e}")
            return None
    
    def get_network_connection(self) -> int:
        """
        获取网络连接状态
        
        Returns:
            网络连接状态码
        """
        try:
            return self.driver.network_connection
        except Exception as e:
            logging.error(f"获取网络状态失败: {e}")
            return 0
    
    def set_network_connection(self, connection_type: int) -> bool:
        """
        设置网络连接
        
        Args:
            connection_type: 连接类型 (0=无网络, 1=飞行模式, 2=WiFi, 4=移动数据, 6=全部)
            
        Returns:
            是否设置成功
        """
        try:
            self.driver.set_network_connection(connection_type)
            return True
        except Exception as e:
            logging.error(f"设置网络连接失败: {e}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """
        获取设备信息
        
        Returns:
            设备信息字典
        """
        try:
            info = {
                "platform": self.driver.capabilities.get("platformName"),
                "platform_version": self.driver.capabilities.get("platformVersion"),
                "device_name": self.driver.capabilities.get("deviceName"),
                "udid": self.driver.capabilities.get("udid"),
                "app_package": self.driver.current_package,
                "app_activity": self.driver.current_activity,
                "screen_size": self.driver.get_window_size(),
                "network_connection": self.get_network_connection()
            }
            return info
        except Exception as e:
            logging.error(f"获取设备信息失败: {e}")
            return {}
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计
        
        Returns:
            性能统计字典
        """
        return {
            "operation_count": self.operation_count,
            "error_count": self.error_count,
            "success_rate": (self.operation_count - self.error_count) / max(self.operation_count, 1) * 100
        }
    
    def disconnect(self):
        """断开连接"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self.is_connected = False
            self.wait = None
            logging.info("已断开闲鱼APP连接")
            
        except Exception as e:
            logging.error(f"断开连接失败: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


# 便捷函数
def create_xianyu_controller(device_id: str = None) -> XianyuAppController:
    """
    创建闲鱼APP控制器实例
    
    Args:
        device_id: 设备ID
        
    Returns:
        控制器实例
    """
    return XianyuAppController(device_id)