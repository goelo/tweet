#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成器
处理封面图片和配图生成
"""

import os
import sys
import json
import requests
import base64
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.config import config


class ImageGenerator:
    """图片生成器"""
    
    def __init__(self):
        if not config:
            raise ValueError("配置未正确加载")
        
        self.config = config
        image_config = config.get_image_config()
        
        self.api_key = image_config['api_key']
        self.api_url = image_config['api_url']
        self.model = image_config['model']
        self.image_count = image_config['count']
        self.enabled = image_config['enabled']
        
        if not self.enabled:
            print("⚠️ 图片生成功能已禁用")
            return
        
        if not self.api_key:
            print("⚠️ 图片生成 API Key 未设置")
            self.enabled = False
            return
        
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        print(f"🎨 图片生成配置:")
        print(f"   API URL: {self.api_url}")
        print(f"   Model: {self.model}")
        print(f"   Count: {self.image_count}")
        print(f"   Enabled: {self.enabled}")

    def is_available(self) -> bool:
        """检查图片生成功能是否可用"""
        return self.enabled and bool(self.api_key)

    def generate_image_prompt(self, main_title: str, subtitle: str) -> str:
        """
        生成图片提示词
        
        Args:
            main_title: 主标题
            subtitle: 副标题
            
        Returns:
            图片生成提示词
        """
        prompt = f"""Black background, large bold yellow Chinese text: '{main_title}'.
Below that in smaller white font: '{subtitle}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, suitable for attention-grabbing social media thumbnail."""
        
        return prompt

    def generate_image(self, prompt: str, topic: str = "") -> Optional[List[str]]:
        """
        生成图片
        
        Args:
            prompt: 图片生成提示词
            topic: 选题（用于文件命名）
            
        Returns:
            生成的图片文件路径列表
        """
        if not self.is_available():
            print("❌ 图片生成功能不可用")
            return None
        
        print(f"🎨 正在生成图片...")
        print(f"   提示词: {prompt[:100]}...")
        
        try:
            # 构建请求数据
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1000,
                "n": self.image_count
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=120  # 图片生成可能需要更长时间
            )
            
            if response.status_code != 200:
                print(f"❌ 图片生成失败: {response.status_code}")
                print(f"   响应内容: {response.text}")
                return None
            
            result = response.json()
            
            # 检查响应格式
            if 'choices' not in result or not result['choices']:
                print("❌ 图片生成响应格式错误")
                return None
            
            # 保存图片
            image_paths = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            for i, choice in enumerate(result['choices']):
                # 根据不同的返回格式处理
                image_data = None
                
                # 检查是否有图片数据
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
                    # 如果内容是 base64 图片数据
                    if content.startswith('data:image'):
                        # 提取 base64 数据
                        header, encoded = content.split(',', 1)
                        image_data = base64.b64decode(encoded)
                    elif len(content) > 1000:  # 可能是 base64 数据
                        try:
                            image_data = base64.b64decode(content)
                        except:
                            pass
                
                if image_data:
                    # 保存图片文件
                    filename = f"image_{timestamp}_{topic[:20].replace('/', '_')}_{i+1}.png"
                    filepath = os.path.join(self.config.output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    image_paths.append(filepath)
                    print(f"✅ 图片已保存: {filename}")
                else:
                    print(f"⚠️ 第 {i+1} 张图片数据无效")
            
            if image_paths:
                print(f"🎉 成功生成 {len(image_paths)} 张图片")
                return image_paths
            else:
                print("❌ 没有成功生成任何图片")
                return None
                
        except Exception as e:
            print(f"❌ 图片生成异常: {e}")
            return None

    def generate_cover_image(self, main_title: str, subtitle: str, topic: str = "") -> Optional[str]:
        """
        生成封面图片
        
        Args:
            main_title: 主标题
            subtitle: 副标题  
            topic: 选题
            
        Returns:
            生成的封面图片路径
        """
        if not self.is_available():
            return None
        
        # 生成封面图片提示词
        prompt = self.generate_image_prompt(main_title, subtitle)
        
        # 生成图片
        image_paths = self.generate_image(prompt, topic)
        
        if image_paths and len(image_paths) > 0:
            return image_paths[0]  # 返回第一张图片作为封面
        
        return None

    def test_generation(self) -> bool:
        """
        测试图片生成功能
        
        Returns:
            是否成功
        """
        if not self.is_available():
            return False
        
        test_prompt = "A simple test image with red background and white text 'TEST'"
        result = self.generate_image(test_prompt, "test")
        
        return result is not None and len(result) > 0

    def save_prompt(self, prompt: str, topic: str, main_title: str = "", subtitle: str = "") -> str:
        """
        保存图片提示词到文件
        
        Args:
            prompt: 图片提示词
            topic: 选题
            main_title: 主标题
            subtitle: 副标题
            
        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"image_prompt_{timestamp}_{topic[:20].replace('/', '_')}.txt"
        filepath = os.path.join(self.config.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"选题: {topic}\n")
                f.write(f"主标题: {main_title}\n")
                f.write(f"副标题: {subtitle}\n")
                f.write(f"生成时间: {timestamp}\n")
                f.write("=" * 50 + "\n")
                f.write(f"图片提示词:\n{prompt}\n")
            
            print(f"✅ 提示词已保存: {filename}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存提示词失败: {e}")
            return ""


# 创建全局图片生成器实例
try:
    image_generator = ImageGenerator()
except Exception as e:
    print(f"❌ 图片生成器初始化失败: {e}")
    image_generator = None