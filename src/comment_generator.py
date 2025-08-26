# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - 评论生成器
使用AI生成符合闲鱼平台特色的高质量评论
"""

import random
import logging
import re
import time
import jieba
from typing import Dict, List, Any, Optional, Tuple
from ai_client import get_deepseek_client
from config import get_config, get_comment_templates

class XianyuCommentGenerator:
    """闲鱼评论生成器"""
    
    def __init__(self):
        """初始化评论生成器"""
        self.ai_client = get_deepseek_client()
        self.templates = get_comment_templates()
        
        # 评论类型定义
        self.comment_types = {
            'inquiry': '询价型评论',
            'interest': '感兴趣型评论', 
            'comparison': '对比咨询型评论',
            'compliment': '夸赞型评论',
            'concern': '关注型评论',
            'negotiation': '议价型评论',
            'question': '疑问型评论'
        }
        
        # 闲鱼平台用语特色
        self.xianyu_expressions = {
            'positive': ['不错', '很好', '挺好的', '看起来不错', '质量好', '很新'],
            'inquiry': ['还在吗', '在不在', '还有吗', '可以吗', '怎么样'],
            'price': ['包邮吗', '能便宜点吗', '可以刀吗', '小刀', '大刀', '价格可以商量吗'],
            'interest': ['很感兴趣', '想要', '考虑一下', '很心动', '正好需要'],
            'polite': ['谢谢', '辛苦了', '麻烦了', '打扰了']
        }
        
        # 质量过滤配置
        self.quality_filters = {
            'min_length': 5,
            'max_length': 50,
            'forbidden_words': ['垃圾', '骗子', '假货', '差评', '举报'],
            'required_elements': {
                'inquiry': ['吗', '?', '？'],
                'compliment': ['不错', '好', '很', '真'],
                'interest': ['想', '要', '考虑', '需要']
            }
        }
        
        # 生成统计
        self.generation_stats = {
            'total_generated': 0,
            'successful_generated': 0,
            'filtered_out': 0,
            'by_type': {}
        }
    
    def generate_comments(self, product_info: Dict[str, Any], 
                         comment_types: List[str],
                         count_per_type: int = 3) -> List[Dict[str, Any]]:
        """
        为商品生成多种类型的评论
        
        Args:
            product_info: 商品信息
            comment_types: 要生成的评论类型列表
            count_per_type: 每种类型生成的数量
            
        Returns:
            评论列表
        """
        try:
            all_comments = []
            
            for comment_type in comment_types:
                if comment_type not in self.comment_types:
                    logging.warning(f"未知的评论类型: {comment_type}")
                    continue
                
                # 生成该类型的评论
                type_comments = self._generate_type_comments(
                    product_info, comment_type, count_per_type
                )
                all_comments.extend(type_comments)
            
            # 质量过滤和去重
            filtered_comments = self._filter_and_deduplicate(all_comments)
            
            # 随机排序
            random.shuffle(filtered_comments)
            
            # 更新统计
            self.generation_stats['total_generated'] += len(all_comments)
            self.generation_stats['successful_generated'] += len(filtered_comments)
            self.generation_stats['filtered_out'] += len(all_comments) - len(filtered_comments)
            
            logging.info(f"为商品生成评论完成: 原始{len(all_comments)}条，过滤后{len(filtered_comments)}条")
            
            return filtered_comments
            
        except Exception as e:
            logging.error(f"生成评论失败: {e}")
            return []
    
    def _generate_type_comments(self, product_info: Dict[str, Any], 
                              comment_type: str, count: int) -> List[Dict[str, Any]]:
        """
        生成特定类型的评论
        
        Args:
            product_info: 商品信息
            comment_type: 评论类型
            count: 生成数量
            
        Returns:
            评论列表
        """
        try:
            comments = []
            
            # 更新类型统计
            if comment_type not in self.generation_stats['by_type']:
                self.generation_stats['by_type'][comment_type] = 0
            
            # 尝试AI生成和模板生成相结合
            ai_count = max(1, count // 2)  # 至少1条AI生成
            template_count = count - ai_count
            
            # AI生成评论
            ai_comments = self._generate_ai_comments(product_info, comment_type, ai_count)
            comments.extend(ai_comments)
            
            # 模板生成评论
            template_comments = self._generate_template_comments(
                product_info, comment_type, template_count
            )
            comments.extend(template_comments)
            
            # 如果生成数量不足，用模板补充
            if len(comments) < count:
                additional_comments = self._generate_template_comments(
                    product_info, comment_type, count - len(comments)
                )
                comments.extend(additional_comments)
            
            self.generation_stats['by_type'][comment_type] += len(comments)
            
            return comments[:count]  # 确保不超过要求数量
            
        except Exception as e:
            logging.error(f"生成{comment_type}类型评论失败: {e}")
            return []
    
    def _generate_ai_comments(self, product_info: Dict[str, Any], 
                            comment_type: str, count: int) -> List[Dict[str, Any]]:
        """
        使用AI生成评论
        
        Args:
            product_info: 商品信息
            comment_type: 评论类型
            count: 生成数量
            
        Returns:
            AI生成的评论列表
        """
        try:
            if not self.ai_client.is_configured():
                logging.warning("AI客户端未配置，跳过AI生成")
                return []
            
            # 构建针对闲鱼平台的提示词
            prompt = self._build_xianyu_prompt(product_info, comment_type, count)
            
            # 调用AI生成
            generated_text = self.ai_client.generate_content_sync(
                prompt, max_tokens=300, temperature=0.8
            )
            
            # 解析生成的评论
            parsed_comments = self._parse_ai_generated_comments(
                generated_text, comment_type, product_info
            )
            
            logging.info(f"AI生成{comment_type}评论{len(parsed_comments)}条")
            return parsed_comments
            
        except Exception as e:
            logging.error(f"AI生成评论失败: {e}")
            return []
    
    def _build_xianyu_prompt(self, product_info: Dict[str, Any], 
                           comment_type: str, count: int) -> str:
        """
        构建针对闲鱼平台的AI提示词
        
        Args:
            product_info: 商品信息
            comment_type: 评论类型  
            count: 生成数量
            
        Returns:
            提示词字符串
        """
        # 基础商品信息
        title = product_info.get('title', '商品')
        price = product_info.get('price', 0)
        condition = product_info.get('condition', {}).get('condition', '未知')
        seller = product_info.get('seller', {}).get('name', '卖家')
        location = product_info.get('location', '未知位置')
        
        # 市场分析信息
        market_analysis = product_info.get('market_analysis', {})
        price_level = market_analysis.get('price_level', '中价')
        
        # 构建基础上下文
        base_context = f"""
        你是一个在闲鱼平台购物的真实用户，正在浏览以下商品：
        
        商品标题：{title}
        售价：¥{price}
        成色：{condition}
        卖家：{seller}
        位置：{location}
        价格定位：{price_level}
        """
        
        # 根据评论类型构建不同的提示
        if comment_type == 'inquiry':
            specific_prompt = f"""
            请生成{count}条询价型评论，要求：
            1. 体现对商品的兴趣，但关心价格
            2. 语气自然友善，像真实买家
            3. 可以询问是否包邮、能否优惠等
            4. 每条评论8-25字
            5. 使用闲鱼用户常用表达方式
            6. 可以适当使用"还在吗"、"包邮吗"、"能便宜点吗"等表达
            
            示例风格：
            - 这个价格还能优惠一些吗？
            - 包邮吗？可以小刀一下吗？
            - 还在吗？能便宜点不？
            """
        
        elif comment_type == 'interest':
            specific_prompt = f"""
            请生成{count}条感兴趣型评论，要求：
            1. 表达对商品的兴趣和购买意向
            2. 语气积极正面，显示购买诚意
            3. 可以询问使用情况、成色等细节
            4. 每条评论6-20字
            5. 体现闲鱼用户的表达习惯
            
            示例风格：
            - 这个还在吗？很感兴趣
            - 正好需要这个，成色怎么样？
            - 看起来不错，用了多久？
            """
        
        elif comment_type == 'compliment':
            specific_prompt = f"""
            请生成{count}条夸赞型评论，要求：
            1. 夸赞商品品质、卖家用心或价格合理
            2. 语气真诚自然，不过分夸张
            3. 可以夸成色好、保养得好等
            4. 每条评论6-18字
            5. 符合闲鱼用户赞美习惯
            
            示例风格：
            - 保养得真好，卖家很用心
            - 这个价格很合理，良心价
            - 东西看起来跟新的一样
            """
        
        elif comment_type == 'comparison':
            specific_prompt = f"""
            请生成{count}条对比咨询型评论，要求：
            1. 询问与其他商品或新品的对比
            2. 显示理性的购买考虑
            3. 可以问功能差异、性价比等
            4. 每条评论12-30字
            5. 体现专业买家的询问方式
            
            示例风格：
            - 和新的比起来性价比怎么样？
            - 这款和XX品牌的有什么区别？
            - 比全新便宜多少？功能一样吗？
            """
        
        elif comment_type == 'concern':
            specific_prompt = f"""
            请生成{count}条关注型评论，要求：
            1. 表达关注但暂时不购买
            2. 暗示可能的后续购买意向
            3. 语气友善，留有余地
            4. 每条评论6-15字
            5. 符合闲鱼"先关注再考虑"的习惯
            
            示例风格：
            - 先关注一下，考虑考虑
            - 收藏了，过几天联系
            - 关注了，有优惠通知我
            """
        
        elif comment_type == 'negotiation':
            specific_prompt = f"""
            请生成{count}条议价型评论，要求：
            1. 表达购买意向但希望议价
            2. 语气诚恳，不能太强硬
            3. 可以说明自己的预算或理由
            4. 每条评论10-25字
            5. 体现闲鱼议价文化
            
            示例风格：
            - 诚心想要，XXX元可以吗？
            - 能接受XXX的价格，怎么样？
            - 预算有限，XXX元行不行？
            """
        
        elif comment_type == 'question':
            specific_prompt = f"""
            请生成{count}条疑问型评论，要求：
            1. 询问商品的具体细节或使用情况
            2. 显示认真的购买考虑
            3. 问题具体且合理
            4. 每条评论8-25字
            5. 体现负责任买家的提问方式
            
            示例风格：
            - 有什么小毛病吗？实话实说
            - 平时怎么保养的？
            - 还有原包装盒吗？
            """
        
        else:
            # 默认通用提示
            specific_prompt = f"""
            请生成{count}条闲鱼评论，要求：
            1. 语气自然真实，像真实买家
            2. 每条评论6-25字
            3. 符合闲鱼用户表达习惯
            """
        
        # 组合完整提示词
        full_prompt = base_context + specific_prompt + f"""
        
        注意事项：
        1. 每条评论独占一行，前面加序号
        2. 语言要接地气，避免太正式
        3. 可以适当使用疑问句和感叹句
        4. 避免重复和雷同
        5. 不要包含任何负面或不当内容
        6. 体现闲鱼平台的轻松氛围
        
        请生成评论：
        """
        
        return full_prompt
    
    def _parse_ai_generated_comments(self, generated_text: str, 
                                   comment_type: str,
                                   product_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析AI生成的评论文本
        
        Args:
            generated_text: AI生成的原始文本
            comment_type: 评论类型
            product_info: 商品信息
            
        Returns:
            解析后的评论列表
        """
        try:
            comments = []
            lines = generated_text.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 移除序号和格式符号
                cleaned_content = re.sub(r'^\d+[\.\)、]\s*', '', line)
                cleaned_content = re.sub(r'^[-•*]\s*', '', cleaned_content)
                cleaned_content = cleaned_content.strip()
                
                # 验证评论质量
                if self._validate_comment_quality(cleaned_content, comment_type):
                    comment_data = {
                        'content': cleaned_content,
                        'type': comment_type,
                        'length': len(cleaned_content),
                        'generated_by': 'ai',
                        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_id': product_info.get('id', ''),
                        'ai_prompt_type': comment_type
                    }
                    comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            logging.error(f"解析AI生成评论失败: {e}")
            return []
    
    def _generate_template_comments(self, product_info: Dict[str, Any],
                                  comment_type: str, count: int) -> List[Dict[str, Any]]:
        """
        基于模板生成评论
        
        Args:
            product_info: 商品信息
            comment_type: 评论类型
            count: 生成数量
            
        Returns:
            模板生成的评论列表
        """
        try:
            comments = []
            templates = self.templates.get(comment_type, [])
            
            if not templates:
                logging.warning(f"未找到{comment_type}类型的模板")
                return []
            
            # 获取商品相关信息用于个性化
            price = product_info.get('price', 0)
            title_words = self._extract_title_keywords(product_info.get('title', ''))
            
            for i in range(count):
                # 选择模板（循环使用）
                template = templates[i % len(templates)]
                
                # 个性化模板
                personalized_comment = self._personalize_template(
                    template, product_info, comment_type
                )
                
                if personalized_comment and self._validate_comment_quality(
                    personalized_comment, comment_type
                ):
                    comment_data = {
                        'content': personalized_comment,
                        'type': comment_type,
                        'length': len(personalized_comment),
                        'generated_by': 'template',
                        'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'product_id': product_info.get('id', ''),
                        'template_used': template
                    }
                    comments.append(comment_data)
            
            return comments
            
        except Exception as e:
            logging.error(f"模板生成评论失败: {e}")
            return []
    
    def _personalize_template(self, template: str, product_info: Dict[str, Any],
                            comment_type: str) -> str:
        """
        个性化模板评论
        
        Args:
            template: 原始模板
            product_info: 商品信息
            comment_type: 评论类型
            
        Returns:
            个性化后的评论
        """
        try:
            personalized = template
            
            # 价格相关个性化
            price = product_info.get('price', 0)
            if '{price_comment}' in template:
                if price <= 50:
                    price_comment = "价格很亲民"
                elif price <= 200:
                    price_comment = "价格还不错"
                elif price <= 500:
                    price_comment = "价格合理"
                else:
                    price_comment = "价格偏高但看起来值"
                personalized = personalized.replace('{price_comment}', price_comment)
            
            # 成色相关个性化
            condition_info = product_info.get('condition', {})
            condition = condition_info.get('condition', '未知')
            if '{condition_comment}' in template:
                if '全新' in condition:
                    condition_comment = "成色很好"
                elif '几乎全新' in condition:
                    condition_comment = "保养得不错"
                else:
                    condition_comment = "看起来还可以"
                personalized = personalized.replace('{condition_comment}', condition_comment)
            
            # 添加随机化元素
            if comment_type == 'inquiry':
                # 随机添加语气词
                mood_particles = ['呢', '呀', '吗', '？']
                if personalized.endswith('吗') and random.random() < 0.3:
                    personalized = personalized[:-1] + random.choice(mood_particles)
            
            # 随机添加表情
            if random.random() < 0.2:  # 20%概率添加表情
                emotions = ['😊', '🤔', '👍', '😄']
                personalized += random.choice(emotions)
            
            return personalized
            
        except Exception as e:
            logging.debug(f"个性化模板失败: {e}")
            return template
    
    def _extract_title_keywords(self, title: str) -> List[str]:
        """
        从商品标题提取关键词
        
        Args:
            title: 商品标题
            
        Returns:
            关键词列表
        """
        try:
            # 使用jieba分词
            words = jieba.lcut(title)
            
            # 过滤停用词和短词
            stop_words = {'的', '是', '在', '了', '有', '和', '就', '都', '而', '及'}
            keywords = [word for word in words 
                       if len(word) > 1 and word not in stop_words]
            
            return keywords[:5]  # 返回前5个关键词
            
        except Exception as e:
            logging.debug(f"提取标题关键词失败: {e}")
            return []
    
    def _validate_comment_quality(self, content: str, comment_type: str) -> bool:
        """
        验证评论质量
        
        Args:
            content: 评论内容
            comment_type: 评论类型
            
        Returns:
            是否通过质量检查
        """
        if not content:
            return False
        
        # 长度检查
        min_len = self.quality_filters['min_length']
        max_len = self.quality_filters['max_length']
        if not (min_len <= len(content) <= max_len):
            return False
        
        # 禁词检查
        forbidden_words = self.quality_filters['forbidden_words']
        if any(word in content for word in forbidden_words):
            return False
        
        # 重复字符检查
        if re.search(r'(.)\1{3,}', content):  # 同一字符连续4次以上
            return False
        
        # 类型特定检查
        required_elements = self.quality_filters.get('required_elements', {}).get(comment_type, [])
        if required_elements:
            if not any(element in content for element in required_elements):
                return False
        
        # 内容合理性检查
        if self._is_nonsense_content(content):
            return False
        
        return True
    
    def _is_nonsense_content(self, content: str) -> bool:
        """
        检查是否为无意义内容
        
        Args:
            content: 评论内容
            
        Returns:
            是否为无意义内容
        """
        # 检查是否包含过多标点符号
        punctuation_ratio = len(re.findall(r'[。，！？；：、]', content)) / len(content)
        if punctuation_ratio > 0.5:
            return True
        
        # 检查是否包含有效的中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', content)
        if len(chinese_chars) < 3:
            return True
        
        # 检查是否为纯数字或符号
        if re.match(r'^[\d\s\W]+$', content):
            return True
        
        return False
    
    def _filter_and_deduplicate(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        过滤和去重评论
        
        Args:
            comments: 原始评论列表
            
        Returns:
            过滤后的评论列表
        """
        try:
            # 去重
            seen_contents = set()
            unique_comments = []
            
            for comment in comments:
                content = comment['content']
                
                # 简单去重：相同内容
                if content in seen_contents:
                    continue
                
                # 相似度去重：内容过于相似
                is_similar = False
                for seen_content in seen_contents:
                    if self._calculate_similarity(content, seen_content) > 0.8:
                        is_similar = True
                        break
                
                if not is_similar:
                    seen_contents.add(content)
                    unique_comments.append(comment)
            
            # 按类型平衡数量
            balanced_comments = self._balance_comment_types(unique_comments)
            
            # 质量排序
            quality_sorted = self._sort_by_quality(balanced_comments)
            
            return quality_sorted
            
        except Exception as e:
            logging.error(f"过滤和去重评论失败: {e}")
            return comments
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度
        
        Args:
            text1: 文本1
            text2: 文本2
            
        Returns:
            相似度 (0-1)
        """
        try:
            # 简单的字符级相似度计算
            set1 = set(text1)
            set2 = set(text2)
            
            if not set1 or not set2:
                return 0.0
            
            intersection = len(set1 & set2)
            union = len(set1 | set2)
            
            return intersection / union if union > 0 else 0.0
            
        except Exception:
            return 0.0
    
    def _balance_comment_types(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        平衡不同类型评论的数量
        
        Args:
            comments: 评论列表
            
        Returns:
            平衡后的评论列表
        """
        try:
            # 按类型分组
            type_groups = {}
            for comment in comments:
                comment_type = comment['type']
                if comment_type not in type_groups:
                    type_groups[comment_type] = []
                type_groups[comment_type].append(comment)
            
            # 每种类型最多保留一定数量
            max_per_type = 5
            balanced = []
            
            for comment_type, type_comments in type_groups.items():
                # 按质量排序，取前N个
                sorted_comments = sorted(
                    type_comments, 
                    key=lambda x: self._calculate_comment_score(x),
                    reverse=True
                )
                balanced.extend(sorted_comments[:max_per_type])
            
            return balanced
            
        except Exception as e:
            logging.error(f"平衡评论类型失败: {e}")
            return comments
    
    def _calculate_comment_score(self, comment: Dict[str, Any]) -> float:
        """
        计算评论质量得分
        
        Args:
            comment: 评论字典
            
        Returns:
            质量得分
        """
        score = 0.0
        content = comment['content']
        
        # 长度得分（适中长度得分高）
        length = len(content)
        if 8 <= length <= 20:
            score += 2.0
        elif 5 <= length <= 25:
            score += 1.0
        
        # AI生成的评论加分
        if comment.get('generated_by') == 'ai':
            score += 1.0
        
        # 包含闲鱼特色表达加分
        for expressions in self.xianyu_expressions.values():
            if any(expr in content for expr in expressions):
                score += 0.5
                break
        
        # 避免过多标点符号
        punctuation_count = len(re.findall(r'[！？。，]', content))
        if punctuation_count <= 2:
            score += 0.5
        
        return score
    
    def _sort_by_quality(self, comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        按质量排序评论
        
        Args:
            comments: 评论列表
            
        Returns:
            排序后的评论列表
        """
        try:
            return sorted(
                comments,
                key=lambda x: self._calculate_comment_score(x),
                reverse=True
            )
        except Exception as e:
            logging.error(f"质量排序失败: {e}")
            return comments
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """
        获取生成统计信息
        
        Returns:
            统计信息字典
        """
        stats = self.generation_stats.copy()
        
        # 计算成功率
        if stats['total_generated'] > 0:
            stats['success_rate'] = (stats['successful_generated'] / 
                                   stats['total_generated']) * 100
        else:
            stats['success_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """重置统计信息"""
        self.generation_stats = {
            'total_generated': 0,
            'successful_generated': 0,
            'filtered_out': 0,
            'by_type': {}
        }
        logging.info("评论生成统计信息已重置")
    
    def customize_for_product(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据商品特征自定义生成策略
        
        Args:
            product_info: 商品信息
            
        Returns:
            自定义策略配置
        """
        try:
            strategy = {}
            
            # 根据价格调整策略
            price = product_info.get('price', 0)
            if price <= 50:
                strategy['preferred_types'] = ['inquiry', 'interest']
                strategy['tone'] = 'casual'
            elif price <= 500:
                strategy['preferred_types'] = ['inquiry', 'compliment', 'interest'] 
                strategy['tone'] = 'friendly'
            else:
                strategy['preferred_types'] = ['comparison', 'question', 'compliment']
                strategy['tone'] = 'polite'
            
            # 根据竞争程度调整
            existing_comments = product_info.get('existing_comments', [])
            if len(existing_comments) < 3:
                strategy['urgency'] = 'high'  # 竞争少，可以表现更积极
            else:
                strategy['urgency'] = 'low'   # 竞争多，需要更谨慎
            
            return strategy
            
        except Exception as e:
            logging.error(f"自定义策略失败: {e}")
            return {}


# 便捷函数
def create_comment_generator() -> XianyuCommentGenerator:
    """
    创建评论生成器实例
    
    Returns:
        评论生成器实例
    """
    return XianyuCommentGenerator()

def generate_xianyu_comments(product_info: Dict[str, Any], 
                           comment_types: List[str],
                           count_per_type: int = 3) -> List[Dict[str, Any]]:
    """
    生成闲鱼评论的便捷函数
    
    Args:
        product_info: 商品信息
        comment_types: 评论类型列表
        count_per_type: 每种类型生成数量
        
    Returns:
        生成的评论列表
    """
    generator = create_comment_generator()
    return generator.generate_comments(product_info, comment_types, count_per_type)