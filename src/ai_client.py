# -*- coding: utf-8 -*-
"""
移动端闲鱼自动评论助手 - AI客户端
封装DeepSeek API调用功能
"""

import asyncio
import aiohttp
import logging
import time
import json
from typing import Dict, List, Any, Optional
from config import get_config

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(self):
        """初始化DeepSeek客户端"""
        api_config = get_config("deepseek_api", {})
        
        self.api_key = api_config.get("api_key", "")
        self.base_url = api_config.get("base_url", "https://api.deepseek.com/v1")
        self.model = api_config.get("model", "deepseek-chat")
        self.max_tokens = api_config.get("max_tokens", 200)
        self.temperature = api_config.get("temperature", 0.7)
        self.timeout = api_config.get("timeout", 30)
        self.retry_count = api_config.get("retry_count", 3)
        
        # API调用统计
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        
        # 速率限制
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 最小请求间隔（秒）
    
    async def generate_content(self, prompt: str, 
                             max_tokens: Optional[int] = None,
                             temperature: Optional[float] = None) -> str:
        """
        生成内容
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            生成的内容
        """
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置")
        
        # 使用传入参数或默认配置
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature or self.temperature
        
        # 构建请求数据
        request_data = {
            "model": self.model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        # 执行请求（带重试）
        for attempt in range(self.retry_count):
            try:
                result = await self._make_request(request_data)
                if result:
                    self.successful_requests += 1
                    return result
                    
            except Exception as e:
                logging.warning(f"DeepSeek API请求失败 (尝试 {attempt + 1}/{self.retry_count}): {e}")
                if attempt < self.retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避
        
        self.failed_requests += 1
        raise Exception("DeepSeek API请求最终失败")
    
    async def _make_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        执行单次API请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            生成的内容或None
        """
        # 速率限制
        await self._rate_limit()
        
        self.total_requests += 1
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/chat/completions"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(url, headers=headers, json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_response(data)
                else:
                    error_text = await response.text()
                    logging.error(f"DeepSeek API错误 {response.status}: {error_text}")
                    
                    # 根据错误类型决定是否重试
                    if response.status in [429, 500, 502, 503, 504]:
                        raise Exception(f"可重试错误: {response.status}")
                    else:
                        raise Exception(f"不可重试错误: {response.status}")
    
    def _parse_response(self, data: Dict[str, Any]) -> str:
        """
        解析API响应
        
        Args:
            data: 响应数据
            
        Returns:
            生成的内容
        """
        try:
            # 提取生成的内容
            content = data["choices"][0]["message"]["content"]
            
            # 更新token使用统计
            usage = data.get("usage", {})
            self.total_tokens_used += usage.get("total_tokens", 0)
            
            logging.info(f"DeepSeek API响应成功，内容长度: {len(content)}")
            return content.strip()
            
        except (KeyError, IndexError) as e:
            logging.error(f"解析DeepSeek响应失败: {e}")
            logging.debug(f"响应数据: {data}")
            raise Exception("API响应格式错误")
    
    async def _rate_limit(self):
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def generate_content_sync(self, prompt: str, 
                            max_tokens: Optional[int] = None,
                            temperature: Optional[float] = None) -> str:
        """
        同步版本的内容生成
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            temperature: 温度参数
            
        Returns:
            生成的内容
        """
        try:
            # 创建新的事件循环（如果当前没有）
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果已有运行的循环，使用异步方式
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(
                            asyncio.run,
                            self.generate_content(prompt, max_tokens, temperature)
                        )
                        return future.result()
                else:
                    return loop.run_until_complete(
                        self.generate_content(prompt, max_tokens, temperature)
                    )
            except RuntimeError:
                # 创建新的事件循环
                return asyncio.run(
                    self.generate_content(prompt, max_tokens, temperature)
                )
                
        except Exception as e:
            logging.error(f"同步调用DeepSeek API失败: {e}")
            raise
    
    async def batch_generate(self, prompts: List[str], 
                           max_tokens: Optional[int] = None,
                           temperature: Optional[float] = None,
                           max_concurrent: int = 3) -> List[Optional[str]]:
        """
        批量生成内容
        
        Args:
            prompts: 提示词列表
            max_tokens: 最大token数
            temperature: 温度参数
            max_concurrent: 最大并发数
            
        Returns:
            生成结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(prompt: str) -> Optional[str]:
            async with semaphore:
                try:
                    return await self.generate_content(prompt, max_tokens, temperature)
                except Exception as e:
                    logging.error(f"批量生成失败: {e}")
                    return None
        
        tasks = [generate_with_semaphore(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"批量生成出现异常: {result}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            是否连接成功
        """
        try:
            test_prompt = "请回复'连接成功'"
            result = self.generate_content_sync(test_prompt, max_tokens=10)
            
            if result and "连接成功" in result:
                logging.info("DeepSeek API连接测试成功")
                return True
            else:
                logging.warning("DeepSeek API连接测试失败: 响应异常")
                return False
                
        except Exception as e:
            logging.error(f"DeepSeek API连接测试失败: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        获取API使用统计
        
        Returns:
            使用统计字典
        """
        success_rate = 0
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(success_rate, 2),
            "total_tokens_used": self.total_tokens_used,
            "average_tokens_per_request": (
                self.total_tokens_used / max(self.successful_requests, 1)
            )
        }
    
    def estimate_cost(self, token_count: int = None) -> Dict[str, float]:
        """
        估算使用成本
        
        Args:
            token_count: token数量，如果为None则使用累计使用量
            
        Returns:
            成本估算字典
        """
        if token_count is None:
            token_count = self.total_tokens_used
        
        # DeepSeek定价（需要根据实际情况调整）
        # 这里使用示例定价，实际使用时需要查看官方定价
        price_per_1k_tokens = 0.0014  # 美元/1000 tokens（示例价格）
        
        cost_usd = (token_count / 1000) * price_per_1k_tokens
        cost_cny = cost_usd * 7.2  # 按汇率7.2计算人民币
        
        return {
            "tokens": token_count,
            "cost_usd": round(cost_usd, 4),
            "cost_cny": round(cost_cny, 4)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_tokens_used = 0
        logging.info("DeepSeek API统计信息已重置")
    
    def update_config(self, **kwargs):
        """
        更新配置参数
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logging.info(f"更新DeepSeek配置 {key}: {value}")
    
    def is_configured(self) -> bool:
        """
        检查是否已正确配置
        
        Returns:
            是否已配置
        """
        return bool(self.api_key and self.api_key.strip())


# 全局DeepSeek客户端实例
_deepseek_client = None

def get_deepseek_client() -> DeepSeekClient:
    """
    获取DeepSeek客户端单例
    
    Returns:
        DeepSeek客户端实例
    """
    global _deepseek_client
    if _deepseek_client is None:
        _deepseek_client = DeepSeekClient()
    return _deepseek_client

def test_deepseek_connection() -> bool:
    """
    测试DeepSeek连接的便捷函数
    
    Returns:
        是否连接成功
    """
    client = get_deepseek_client()
    return client.test_connection()

async def generate_text_async(prompt: str, **kwargs) -> str:
    """
    异步生成文本的便捷函数
    
    Args:
        prompt: 提示词
        **kwargs: 其他参数
        
    Returns:
        生成的文本
    """
    client = get_deepseek_client()
    return await client.generate_content(prompt, **kwargs)

def generate_text_sync(prompt: str, **kwargs) -> str:
    """
    同步生成文本的便捷函数
    
    Args:
        prompt: 提示词
        **kwargs: 其他参数
        
    Returns:
        生成的文本
    """
    client = get_deepseek_client()
    return client.generate_content_sync(prompt, **kwargs)