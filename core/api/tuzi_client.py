#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tuzi API 客户端
处理与 Tuzi API 的交互
"""

import os
import sys
import json
import requests
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.config.config import config


class TuziClient:
    """Tuzi API 客户端"""

    def __init__(self):
        if not config:
            raise ValueError("配置未正确加载，请检查 .env 文件")
        
        tuzi_config = config.get_tuzi_config()
        self.api_key = tuzi_config['api_key']
        self.api_base = tuzi_config['api_base']
        self.model = tuzi_config['model']
        
        if not self.api_key:
            raise ValueError("Tuzi API Key 未设置")
        
        # 确保 API 基础 URL 正确
        if not self.api_base.endswith('/chat/completions'):
            if self.api_base.endswith('/v1'):
                self.api_base = self.api_base + '/chat/completions'
            else:
                self.api_base = self.api_base.rstrip('/') + '/v1/chat/completions'
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"🤖 Tuzi API 配置:")
        print(f"   API Base: {self.api_base}")
        print(f"   Model: {self.model}")
        print(f"   API Key: {self.api_key[:10]}...{self.api_key[-4:]}")

    def chat_completion(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 2000) -> Optional[str]:
        """
        调用 Tuzi Chat Completion API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            GPT 的回答内容
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                self.api_base,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"❌ Tuzi API 调用失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Tuzi API 调用异常: {e}")
            return None

    def simple_chat(self, question: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        简单的对话接口
        
        Args:
            question: 用户问题
            system_prompt: 系统提示词（可选）
        
        Returns:
            GPT 的回答
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": question})
        
        return self.chat_completion(messages)

    def generate_thread(self, topic: str, thread_prompt: str) -> Optional[List[Dict]]:
        """
        生成 Twitter Thread
        
        Args:
            topic: 话题标题
            thread_prompt: Thread 生成提示词模板
            
        Returns:
            生成的 Thread 列表
        """
        # 构建完整的提示词
        full_prompt = thread_prompt.replace('${topic}', topic)
        
        response = self.simple_chat(
            full_prompt,
            system_prompt="你是一个擅长写搞钱 thread 的社交媒体内容创作者。"
        )
        
        if not response:
            return None
        
        try:
            # 尝试解析 JSON 格式的回复
            thread_data = json.loads(response)
            if isinstance(thread_data, list):
                return thread_data
            else:
                print("⚠️ 返回格式不是预期的列表格式")
                return None
        except json.JSONDecodeError:
            print("⚠️ 无法解析返回的 JSON 格式")
            print(f"原始回复: {response}")
            return None

    def generate_image_prompt(self, topic: str, main_title: str, subtitle: str) -> str:
        """
        生成图片提示词
        
        Args:
            topic: 话题内容
            main_title: 主标题
            subtitle: 副标题
            
        Returns:
            图片生成提示词
        """
        # 使用你提供的图片提示词模板
        image_prompt = f"""Black background, large bold yellow Chinese text: '{main_title}'.
Below that in smaller white font: '{subtitle}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, suitable for attention-grabbing social media thumbnail."""
        
        return image_prompt

    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        test_response = self.simple_chat("Hello", "You are a helpful assistant.")
        return test_response is not None


# 创建全局 Tuzi 客户端实例
try:
    tuzi_client = TuziClient()
except Exception as e:
    print(f"❌ Tuzi 客户端初始化失败: {e}")
    tuzi_client = None