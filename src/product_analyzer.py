# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 商品信息分析器
专门用于从闲鱼商品页面提取和分析商品信息
"""

import time
import re
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from config import get_config

class XianyuProductAnalyzer:
    """闲鱼商品信息分析器"""
    
    def __init__(self, app_controller):
        """
        初始化商品分析器
        
        Args:
            app_controller: APP控制器实例
        """
        self.app = app_controller
        self.driver = app_controller.driver
        self.wait = app_controller.wait
        self.selectors = get_config("xianyu_selectors", {})
        
        # 分析结果缓存
        self.current_product = None
        self.extraction_errors = []
    
    def extract_product_info(self) -> Optional[Dict[str, Any]]:
        """
        从当前商品页面提取完整商品信息
        
        Returns:
            商品信息字典或None
        """
        try:
            self.extraction_errors = []
            
            if not self.app.is_connected:
                logging.error("APP未连接")
                return None
            
            # 验证当前是否在商品页面
            if not self.app._verify_product_page():
                logging.error("当前不在商品页面")
                return None
            
            # 提取基本信息
            product_info = {}
            
            # 提取商品标题
            product_info['title'] = self._extract_title()
            
            # 提取价格信息
            product_info['price'] = self._extract_price()
            
            # 提取卖家信息
            product_info['seller'] = self._extract_seller_info()
            
            # 提取位置信息
            product_info['location'] = self._extract_location()
            
            # 提取商品成色/状态
            product_info['condition'] = self._extract_condition()
            
            # 提取商品描述
            product_info['description'] = self._extract_description()
            
            # 提取商品图片信息
            product_info['images'] = self._extract_image_info()
            
            # 提取发布时间
            product_info['publish_time'] = self._extract_publish_time()
            
            # 提取浏览量和点赞数
            product_info['view_count'] = self._extract_view_count()
            product_info['like_count'] = self._extract_like_count()
            
            # 提取现有评论
            product_info['existing_comments'] = self._extract_existing_comments()
            
            # 生成商品唯一ID
            product_info['id'] = self._generate_product_id(product_info)
            
            # 分析市场定位
            product_info['market_analysis'] = self._analyze_market_position(product_info)
            
            # 记录提取时间
            product_info['extracted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 记录提取过程中的错误
            if self.extraction_errors:
                product_info['extraction_errors'] = self.extraction_errors
            
            self.current_product = product_info
            logging.info(f"商品信息提取完成: {product_info.get('title', '未知商品')}")
            
            return product_info
            
        except Exception as e:
            logging.error(f"提取商品信息失败: {e}")
            self.extraction_errors.append(f"总体提取失败: {str(e)}")
            return None
    
    def _extract_title(self) -> str:
        """
        提取商品标题
        
        Returns:
            商品标题
        """
        try:
            # 闲鱼商品标题的多种可能选择器
            title_selectors = [
                self.selectors.get("product_title"),
                "//android.widget.TextView[contains(@resource-id,'title')]",
                "//android.widget.TextView[contains(@resource-id,'product_title')]",
                "//android.widget.TextView[contains(@resource-id,'item_title')]",
                "//*[@resource-id='com.taobao.idlefish:id/title']",
                "//android.widget.TextView[@index='0'][string-length(@text) > 5]",
                "//*[contains(@class,'TextView')][1][string-length(@text) > 5]"
            ]
            
            for selector in title_selectors:
                if not selector:
                    continue
                    
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 3 and not self._is_ui_element_text(text):
                            logging.info(f"提取到商品标题: {text}")
                            return text
                except Exception as e:
                    continue
            
            # 如果特定选择器失败，尝试通用方法
            return self._extract_title_generic()
            
        except Exception as e:
            error_msg = f"提取商品标题失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return "未知商品"
    
    def _extract_title_generic(self) -> str:
        """
        通用方法提取标题
        
        Returns:
            商品标题
        """
        try:
            # 获取所有TextView元素
            text_elements = self.driver.find_elements(
                AppiumBy.XPATH, "//android.widget.TextView"
            )
            
            # 按照文本长度和位置排序，找到最可能是标题的元素
            candidates = []
            for element in text_elements:
                try:
                    text = element.text.strip()
                    location = element.location
                    
                    # 标题特征：长度适中，位置靠上，不是UI元素
                    if (5 <= len(text) <= 100 and 
                        location['y'] < 800 and  # 在屏幕上半部分
                        not self._is_ui_element_text(text)):
                        
                        candidates.append((text, location['y'], len(text)))
                        
                except:
                    continue
            
            if candidates:
                # 按y坐标排序，取位置最靠上的长文本
                candidates.sort(key=lambda x: (x[1], -x[2]))
                return candidates[0][0]
            
            return "未知商品"
            
        except Exception as e:
            logging.debug(f"通用标题提取失败: {e}")
            return "未知商品"
    
    def _extract_price(self) -> float:
        """
        提取商品价格
        
        Returns:
            价格（元）
        """
        try:
            # 闲鱼价格的多种可能格式
            price_selectors = [
                self.selectors.get("product_price"),
                "//android.widget.TextView[contains(@text,'¥')]",
                "//android.widget.TextView[contains(@text,'元')]",
                "//*[contains(@resource-id,'price')]",
                "//*[contains(@resource-id,'money')]"
            ]
            
            for selector in price_selectors:
                if not selector:
                    continue
                    
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        price = self._parse_price_text(text)
                        if price > 0:
                            logging.info(f"提取到商品价格: ¥{price}")
                            return price
                except:
                    continue
            
            # 通用价格提取
            return self._extract_price_generic()
            
        except Exception as e:
            error_msg = f"提取商品价格失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return 0.0
    
    def _parse_price_text(self, text: str) -> float:
        """
        解析价格文本
        
        Args:
            text: 包含价格的文本
            
        Returns:
            价格数值
        """
        try:
            # 移除所有非数字和小数点的字符，但保留¥符号用于验证
            price_patterns = [
                r'¥\s*(\d+(?:\.\d{1,2})?)',  # ¥123.45
                r'(\d+(?:\.\d{1,2})?)\s*元',  # 123.45元
                r'(\d+(?:\.\d{1,2})?)',      # 纯数字
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    price_str = match.group(1)
                    price = float(price_str)
                    
                    # 价格合理性检查（1分到100万元）
                    if 0.01 <= price <= 1000000:
                        return price
            
            return 0.0
            
        except Exception as e:
            logging.debug(f"价格解析失败: {text} - {e}")
            return 0.0
    
    def _extract_price_generic(self) -> float:
        """
        通用价格提取方法
        
        Returns:
            价格
        """
        try:
            # 获取所有可能包含价格的元素
            all_texts = []
            elements = self.driver.find_elements(
                AppiumBy.XPATH, "//android.widget.TextView"
            )
            
            for element in elements:
                try:
                    text = element.text.strip()
                    if '¥' in text or '元' in text or re.search(r'\d+\.\d{2}', text):
                        price = self._parse_price_text(text)
                        if price > 0:
                            return price
                except:
                    continue
            
            return 0.0
            
        except Exception as e:
            logging.debug(f"通用价格提取失败: {e}")
            return 0.0
    
    def _extract_seller_info(self) -> Dict[str, Any]:
        """
        提取卖家信息
        
        Returns:
            卖家信息字典
        """
        try:
            seller_info = {}
            
            # 卖家名称选择器
            seller_selectors = [
                self.selectors.get("product_seller"),
                "//android.widget.TextView[contains(@resource-id,'seller')]",
                "//android.widget.TextView[contains(@resource-id,'user')]",
                "//android.widget.TextView[contains(@resource-id,'nick')]",
                "//*[contains(@text,'卖家')]/..//android.widget.TextView",
                "//*[contains(@text,'用户')]/..//android.widget.TextView"
            ]
            
            for selector in seller_selectors:
                if not selector:
                    continue
                    
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if (text and len(text) > 1 and 
                            not text.isdigit() and 
                            not self._is_ui_element_text(text)):
                            seller_info['name'] = text
                            break
                    
                    if 'name' in seller_info:
                        break
                        
                except:
                    continue
            
            # 如果没找到卖家名称，设置默认值
            if 'name' not in seller_info:
                seller_info['name'] = "未知卖家"
            
            # 尝试提取卖家信誉等级
            seller_info['level'] = self._extract_seller_level()
            
            # 尝试提取卖家认证信息
            seller_info['verification'] = self._extract_seller_verification()
            
            logging.info(f"提取到卖家信息: {seller_info['name']}")
            return seller_info
            
        except Exception as e:
            error_msg = f"提取卖家信息失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return {"name": "未知卖家", "level": "", "verification": []}
    
    def _extract_seller_level(self) -> str:
        """提取卖家等级"""
        try:
            level_indicators = [
                "//android.widget.TextView[contains(@text,'钻')]",
                "//android.widget.TextView[contains(@text,'星')]",
                "//android.widget.TextView[contains(@text,'级')]",
                "//*[contains(@resource-id,'level')]"
            ]
            
            for selector in level_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logging.debug(f"提取卖家等级失败: {e}")
            return ""
    
    def _extract_seller_verification(self) -> List[str]:
        """提取卖家认证信息"""
        try:
            verifications = []
            
            verification_indicators = [
                "//android.widget.TextView[contains(@text,'实名认证')]",
                "//android.widget.TextView[contains(@text,'身份认证')]",
                "//android.widget.TextView[contains(@text,'芝麻信用')]",
                "//android.widget.TextView[contains(@text,'认证')]"
            ]
            
            for selector in verification_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and text not in verifications:
                            verifications.append(text)
                except:
                    continue
            
            return verifications
            
        except Exception as e:
            logging.debug(f"提取卖家认证信息失败: {e}")
            return []
    
    def _extract_location(self) -> str:
        """
        提取位置信息
        
        Returns:
            位置信息
        """
        try:
            location_selectors = [
                self.selectors.get("product_location"),
                "//android.widget.TextView[contains(@text,'市')]",
                "//android.widget.TextView[contains(@text,'区')]",
                "//android.widget.TextView[contains(@text,'县')]",
                "//android.widget.TextView[contains(@text,'省')]",
                "//*[contains(@resource-id,'location')]",
                "//*[contains(@resource-id,'address')]"
            ]
            
            for selector in location_selectors:
                if not selector:
                    continue
                    
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        text = element.text.strip()
                        if self._is_location_text(text):
                            logging.info(f"提取到位置信息: {text}")
                            return text
                except:
                    continue
            
            return "未知位置"
            
        except Exception as e:
            error_msg = f"提取位置信息失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return "未知位置"
    
    def _is_location_text(self, text: str) -> bool:
        """
        判断文本是否为位置信息
        
        Args:
            text: 文本内容
            
        Returns:
            是否为位置信息
        """
        if not text or len(text) < 2:
            return False
        
        # 包含地理标识词
        location_keywords = ['市', '区', '县', '省', '镇', '街道', '路']
        if any(keyword in text for keyword in location_keywords):
            return True
        
        # 排除明显不是地名的文本
        exclude_keywords = ['购买', '联系', '价格', '商品', '卖家']
        if any(keyword in text for keyword in exclude_keywords):
            return False
        
        return False
    
    def _extract_condition(self) -> Dict[str, Any]:
        """
        提取商品成色/状态信息
        
        Returns:
            成色信息字典
        """
        try:
            condition_info = {}
            
            # 闲鱼成色的标准分类
            condition_keywords = {
                "全新": 5,
                "几乎全新": 4, 
                "轻微使用痕迹": 3,
                "明显使用痕迹": 2,
                "重度使用痕迹": 1
            }
            
            # 查找成色相关文本
            all_elements = self.driver.find_elements(
                AppiumBy.XPATH, "//android.widget.TextView"
            )
            
            for element in all_elements:
                try:
                    text = element.text.strip()
                    for condition, score in condition_keywords.items():
                        if condition in text:
                            condition_info['condition'] = condition
                            condition_info['score'] = score
                            logging.info(f"提取到商品成色: {condition}")
                            return condition_info
                except:
                    continue
            
            # 如果没找到标准成色，查找其他描述
            condition_patterns = [
                r'(全新|九成新|八成新|七成新|六成新)',
                r'(未拆封|未使用|很新|较新)',
                r'(使用.*痕迹|磨损|划痕)'
            ]
            
            page_source = self.driver.page_source
            for pattern in condition_patterns:
                match = re.search(pattern, page_source)
                if match:
                    found_condition = match.group(1)
                    condition_info['condition'] = found_condition
                    condition_info['score'] = self._score_condition_text(found_condition)
                    return condition_info
            
            # 默认成色
            condition_info['condition'] = "未知成色"
            condition_info['score'] = 3
            return condition_info
            
        except Exception as e:
            error_msg = f"提取商品成色失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return {"condition": "未知成色", "score": 3}
    
    def _score_condition_text(self, condition_text: str) -> int:
        """
        根据成色文本评分
        
        Args:
            condition_text: 成色描述文本
            
        Returns:
            成色评分 (1-5)
        """
        if not condition_text:
            return 3
        
        # 正面词汇
        positive_words = ['全新', '未拆封', '未使用', '很新', '九成新']
        if any(word in condition_text for word in positive_words):
            return 5
        
        # 中性偏上词汇
        good_words = ['八成新', '较新', '几乎全新']
        if any(word in condition_text for word in good_words):
            return 4
        
        # 中性词汇
        neutral_words = ['七成新', '轻微']
        if any(word in condition_text for word in neutral_words):
            return 3
        
        # 负面词汇
        negative_words = ['六成新', '明显', '磨损', '划痕']
        if any(word in condition_text for word in negative_words):
            return 2
        
        # 很负面词汇
        very_negative_words = ['重度', '严重', '破损']
        if any(word in condition_text for word in very_negative_words):
            return 1
        
        return 3  # 默认中等
    
    def _extract_description(self) -> str:
        """
        提取商品描述
        
        Returns:
            商品描述
        """
        try:
            # 首先滚动到描述区域
            self.app.scroll_page("down")
            time.sleep(1)
            
            # 商品描述通常在页面中下部分
            description_parts = []
            
            # 获取所有文本元素
            text_elements = self.driver.find_elements(
                AppiumBy.XPATH, "//android.widget.TextView"
            )
            
            for element in text_elements:
                try:
                    text = element.text.strip()
                    location = element.location
                    
                    # 描述特征：文本较长，位置在中下部，不是UI元素
                    if (len(text) > 10 and 
                        location['y'] > 600 and  # 在屏幕中下部分
                        not self._is_ui_element_text(text) and
                        not self._is_price_text(text) and
                        not self._is_location_text(text)):
                        
                        description_parts.append(text)
                        
                except:
                    continue
            
            # 合并描述，限制总长度
            full_description = ' '.join(description_parts[:5])  # 最多取前5段
            if len(full_description) > 500:
                full_description = full_description[:500] + "..."
            
            if full_description:
                logging.info(f"提取到商品描述: {full_description[:50]}...")
                return full_description
            
            return "暂无描述"
            
        except Exception as e:
            error_msg = f"提取商品描述失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return "暂无描述"
    
    def _extract_image_info(self) -> Dict[str, Any]:
        """
        提取商品图片信息
        
        Returns:
            图片信息字典
        """
        try:
            image_info = {"count": 0, "has_main_image": False}
            
            # 查找图片元素
            image_selectors = [
                "//android.widget.ImageView[contains(@resource-id,'image')]",
                "//android.widget.ImageView[contains(@resource-id,'photo')]", 
                "//android.widget.ImageView[contains(@resource-id,'pic')]"
            ]
            
            total_images = 0
            for selector in image_selectors:
                try:
                    images = self.driver.find_elements(AppiumBy.XPATH, selector)
                    total_images += len(images)
                except:
                    continue
            
            image_info["count"] = total_images
            image_info["has_main_image"] = total_images > 0
            
            if total_images > 0:
                logging.info(f"发现商品图片数量: {total_images}")
            
            return image_info
            
        except Exception as e:
            logging.debug(f"提取图片信息失败: {e}")
            return {"count": 0, "has_main_image": False}
    
    def _extract_publish_time(self) -> str:
        """
        提取发布时间
        
        Returns:
            发布时间字符串
        """
        try:
            time_patterns = [
                r'(\d{1,2}分钟前)',
                r'(\d{1,2}小时前)',
                r'(\d{1,2}天前)',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{2}-\d{2})'
            ]
            
            page_source = self.driver.page_source
            for pattern in time_patterns:
                match = re.search(pattern, page_source)
                if match:
                    time_str = match.group(1)
                    logging.info(f"提取到发布时间: {time_str}")
                    return time_str
            
            return "未知时间"
            
        except Exception as e:
            logging.debug(f"提取发布时间失败: {e}")
            return "未知时间"
    
    def _extract_view_count(self) -> int:
        """提取浏览量"""
        try:
            view_patterns = [
                r'(\d+)人看过',
                r'浏览(\d+)',
                r'(\d+)次浏览'
            ]
            
            page_source = self.driver.page_source
            for pattern in view_patterns:
                match = re.search(pattern, page_source)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            logging.debug(f"提取浏览量失败: {e}")
            return 0
    
    def _extract_like_count(self) -> int:
        """提取点赞数"""
        try:
            like_patterns = [
                r'(\d+)人想要',
                r'(\d+)赞',
                r'点赞(\d+)'
            ]
            
            page_source = self.driver.page_source
            for pattern in like_patterns:
                match = re.search(pattern, page_source)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            logging.debug(f"提取点赞数失败: {e}")
            return 0
    
    def _extract_existing_comments(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        提取现有评论
        
        Args:
            limit: 最大提取数量
            
        Returns:
            评论列表
        """
        try:
            comments = []
            
            # 滚动到评论区域
            if not self._scroll_to_comments():
                return comments
            
            # 查找评论元素
            comment_selectors = [
                "//android.widget.LinearLayout[contains(@resource-id,'comment')]",
                "//android.widget.RelativeLayout[contains(@resource-id,'comment')]",
                "//*[contains(@resource-id,'message')]",
                "//*[contains(@text,'说:')]/.."
            ]
            
            for selector in comment_selectors:
                try:
                    comment_elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    
                    for element in comment_elements[:limit]:
                        comment_data = self._parse_comment_element(element)
                        if comment_data:
                            comments.append(comment_data)
                            
                except:
                    continue
            
            # 去重
            seen_contents = set()
            unique_comments = []
            for comment in comments:
                content = comment.get('content', '')
                if content and content not in seen_contents:
                    seen_contents.add(content)
                    unique_comments.append(comment)
            
            if unique_comments:
                logging.info(f"提取到现有评论数量: {len(unique_comments)}")
            
            return unique_comments[:limit]
            
        except Exception as e:
            error_msg = f"提取现有评论失败: {e}"
            logging.error(error_msg)
            self.extraction_errors.append(error_msg)
            return []
    
    def _scroll_to_comments(self) -> bool:
        """滚动到评论区域"""
        try:
            # 多次向下滚动寻找评论区
            for _ in range(5):
                self.app.scroll_page('down')
                time.sleep(1)
                
                # 检查是否找到评论区标识
                comment_indicators = [
                    "//android.widget.TextView[contains(@text,'评论')]",
                    "//android.widget.TextView[contains(@text,'留言')]",
                    "//android.widget.TextView[contains(@text,'大家都在说')]",
                    "//*[contains(@resource-id,'comment')]"
                ]
                
                for indicator in comment_indicators:
                    try:
                        self.driver.find_element(AppiumBy.XPATH, indicator)
                        return True
                    except:
                        continue
            
            return False
            
        except Exception as e:
            logging.debug(f"滚动到评论区失败: {e}")
            return False
    
    def _parse_comment_element(self, element) -> Optional[Dict[str, Any]]:
        """解析单个评论元素"""
        try:
            comment_data = {}
            
            # 提取评论内容
            text_elements = element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
            
            for text_elem in text_elements:
                text = text_elem.text.strip()
                
                # 判断是否为评论内容（长度适中，不是UI元素）
                if (5 <= len(text) <= 200 and 
                    not self._is_ui_element_text(text) and
                    ':' not in text):  # 避免用户名:内容的格式
                    
                    comment_data['content'] = text
                    break
            
            # 如果找到了评论内容，添加其他信息
            if 'content' in comment_data:
                comment_data['extracted_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
                comment_data['length'] = len(comment_data['content'])
                return comment_data
            
            return None
            
        except Exception as e:
            logging.debug(f"解析评论元素失败: {e}")
            return None
    
    def _is_ui_element_text(self, text: str) -> bool:
        """
        判断文本是否为UI元素文本
        
        Args:
            text: 文本内容
            
        Returns:
            是否为UI元素文本
        """
        ui_keywords = [
            '立即购买', '我想要', '加入购物车', '收藏', '分享', '举报',
            '联系卖家', '查看详情', '评论', '留言', '点赞', '关注',
            '取消', '确定', '返回', '首页', '搜索', '发布',
            '登录', '注册', '设置', '更多', '刷新', '加载'
        ]
        
        return any(keyword in text for keyword in ui_keywords)
    
    def _is_price_text(self, text: str) -> bool:
        """判断是否为价格文本"""
        return '¥' in text or '元' in text or re.search(r'\d+\.\d{2}', text)
    
    def _generate_product_id(self, product_info: Dict[str, Any]) -> str:
        """
        生成商品唯一ID
        
        Args:
            product_info: 商品信息
            
        Returns:
            唯一ID
        """
        try:
            # 使用标题、价格和卖家生成唯一标识
            content_parts = [
                product_info.get('title', ''),
                str(product_info.get('price', 0)),
                product_info.get('seller', {}).get('name', '')
            ]
            
            content = ''.join(content_parts)
            product_id = hashlib.md5(content.encode('utf-8')).hexdigest()[:12]
            
            return f"xianyu_{product_id}"
            
        except Exception as e:
            logging.error(f"生成商品ID失败: {e}")
            return f"xianyu_{int(time.time())}"
    
    def _analyze_market_position(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析商品市场定位
        
        Args:
            product_info: 商品信息
            
        Returns:
            市场分析结果
        """
        try:
            analysis = {}
            
            # 价格定位
            price = product_info.get('price', 0)
            analysis['price_level'] = self._categorize_price(price)
            
            # 成色评分
            condition_info = product_info.get('condition', {})
            analysis['condition_score'] = condition_info.get('score', 3)
            
            # 描述质量评分
            description = product_info.get('description', '')
            analysis['description_quality'] = self._score_description_quality(description)
            
            # 竞争程度（根据现有评论数量）
            existing_comments = product_info.get('existing_comments', [])
            analysis['competition_level'] = len(existing_comments)
            
            # 综合评分
            analysis['overall_score'] = self._calculate_overall_score(analysis)
            
            # 推荐评论策略
            analysis['recommended_strategy'] = self._recommend_comment_strategy(analysis)
            
            return analysis
            
        except Exception as e:
            logging.error(f"市场定位分析失败: {e}")
            return {}
    
    def _categorize_price(self, price: float) -> str:
        """价格分类"""
        if price <= 50:
            return "低价"
        elif price <= 200:
            return "中低价"
        elif price <= 500:
            return "中价"
        elif price <= 1000:
            return "中高价"
        else:
            return "高价"
    
    def _score_description_quality(self, description: str) -> int:
        """描述质量评分"""
        if len(description) > 200:
            return 5
        elif len(description) > 100:
            return 4
        elif len(description) > 50:
            return 3
        elif len(description) > 10:
            return 2
        else:
            return 1
    
    def _calculate_overall_score(self, analysis: Dict[str, Any]) -> float:
        """计算综合评分"""
        try:
            condition_score = analysis.get('condition_score', 3)
            desc_quality = analysis.get('description_quality', 3)
            competition = min(analysis.get('competition_level', 0), 10)  # 最高10分
            
            # 加权计算
            overall = (condition_score * 0.4 + desc_quality * 0.3 + 
                      (10 - competition) * 0.3)
            
            return round(overall, 1)
            
        except Exception as e:
            logging.error(f"计算综合评分失败: {e}")
            return 3.0
    
    def _recommend_comment_strategy(self, analysis: Dict[str, Any]) -> List[str]:
        """推荐评论策略"""
        strategies = []
        
        price_level = analysis.get('price_level', '中价')
        condition_score = analysis.get('condition_score', 3)
        competition = analysis.get('competition_level', 0)
        
        # 根据价格推荐策略
        if price_level in ['低价', '中低价']:
            strategies.append('inquiry')  # 询价型
        
        # 根据成色推荐策略
        if condition_score >= 4:
            strategies.append('compliment')  # 夸赞型
        
        # 根据竞争程度推荐策略
        if competition < 3:
            strategies.append('interest')  # 感兴趣型
        else:
            strategies.append('comparison')  # 对比咨询型
        
        return strategies if strategies else ['interest']
    
    def get_current_product(self) -> Optional[Dict[str, Any]]:
        """
        获取当前分析的商品信息
        
        Returns:
            当前商品信息或None
        """
        return self.current_product
    
    def get_extraction_errors(self) -> List[str]:
        """
        获取提取过程中的错误信息
        
        Returns:
            错误信息列表
        """
        return self.extraction_errors.copy()


# 便捷函数
def create_product_analyzer(app_controller) -> XianyuProductAnalyzer:
    """
    创建商品分析器实例
    
    Args:
        app_controller: APP控制器实例
        
    Returns:
        商品分析器实例
    """
    return XianyuProductAnalyzer(app_controller)