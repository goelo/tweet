#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT 客户端模块
处理与 OpenAI API 的交互
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ openai 库未安装，请运行: pip install openai")

from core.config.config import config


class GPTClient:
    """GPT API 客户端"""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 库未安装，请先安装: pip install openai")

        if config is None:
            raise ValueError("配置未正确加载，请检查 .env 文件")

        # 设置 OpenAI 配置
        self.api_key = config.openai_api_key
        # 确保 API 基础 URL 以 /v1 结尾
        api_base = config.openai_api_base
        if not api_base.endswith('/v1'):
            api_base = api_base.rstrip('/') + '/v1'
        self.api_base = api_base
        self.model = config.openai_model

        # 检查 openai 版本并设置客户端
        try:
            # 尝试新版本 API (1.x)
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.api_base
            )
            self.use_new_api = True
        except:
            # 使用旧版本 API (0.28.x)
            openai.api_key = self.api_key
            openai.api_base = self.api_base
            self.use_new_api = False

        print(f"🤖 GPT API 配置:")
        print(f"   API Base: {self.api_base}")
        print(f"   Model: {self.model}")
        print(f"   API Key: {self.api_key[:10]}...{self.api_key[-4:] if self.api_key else 'None'}")

    def chat_completion(self, messages, temperature=0.7, max_tokens=2000):
        """
        调用 GPT Chat Completion API
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            
        Returns:
            GPT 的回答内容
        """
        try:
            if self.use_new_api:
                # 新版本 API (1.x)
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            else:
                # 旧版本 API (0.28.x)
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
        except Exception as e:
            print(f"GPT API 调用失败: {e}")
            return None

    def simple_chat(self, question, system_prompt=None):
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

    def rewrite_with_style_guide(self, content, style_guide_file="input/style_guide.md", task_instruction="请改写以下内容"):
        """
        使用风格指南改写内容
        
        Args:
            content: 要改写的内容
            style_guide_file: 风格指南文件路径
            task_instruction: 任务指令
        
        Returns:
            改写后的内容
        """
        try:
            # 读取风格指南
            with open(style_guide_file, 'r', encoding='utf-8') as f:
                style_guide = f.read()
        except FileNotFoundError:
            print(f"❌ 风格指南文件 {style_guide_file} 不存在")
            return None
        except Exception as e:
            print(f"❌ 读取风格指南文件失败: {e}")
            return None

        # 构建消息
        messages = [
            {"role": "system", "content": style_guide},
            {"role": "user", "content": f"{task_instruction}\n\n{content}"}
        ]

        return self.chat_completion(messages)


# 创建全局 GPT 客户端实例
try:
    gpt_client = GPTClient()
except Exception as e:
    print(f"GPT 客户端初始化失败: {e}")
    gpt_client = None
