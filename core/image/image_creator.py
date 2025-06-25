#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片创建模块
使用 gpt-4o-image-vip 模型生成图片
"""

import os
import re
import requests
import time
import threading
from datetime import datetime
from typing import Optional, List
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 加载环境变量
load_dotenv()


# 创建一个令牌桶，用于API限流
class TokenBucket:
    def __init__(self, rate_limit=1.0):
        self.rate_limit = rate_limit  # 时间间隔（秒）
        self.last_request_time = 0
        self.lock = threading.Lock()
        
    def consume(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.rate_limit:
                sleep_time = self.rate_limit - time_since_last
                time.sleep(sleep_time)
                
            self.last_request_time = time.time()
            return True


class ImageCreator:
    """图片创建器 - 使用 gpt-4o-image-vip 模型（改进超时和限流处理）"""
    
    def __init__(self):
        self.model = os.getenv("IMAGE_MODEL", "gpt-4o-image-vip")
        self.api_url = os.getenv("IMAGE_API_URL", "https://api.tu-zi.com/v1/chat/completions")
        self.api_token = os.getenv("IMAGE_API_TOKEN")
        
        # 创建令牌桶进行限流
        self.token_bucket = TokenBucket(rate_limit=1.0)  # 每秒最多1个请求
        
        # 创建带重试机制的session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        if not self.api_token:
            print("⚠️ 警告：未设置IMAGE_API_TOKEN环境变量，图片生成功能将不可用")
    
    def create_image(self, image_prompt: str, topic_title: str = "") -> Optional[List[str]]:
        """
        使用 gpt-4o-image-vip 模型创建图片
        
        Args:
            image_prompt: 图片生成提示词
            topic_title: 话题标题（用于文件命名）
            
        Returns:
            生成的图片文件路径列表
        """
        if not self.api_token:
            print("❌ 图片生成功能不可用：缺少API Token")
            return None
        
        if not image_prompt:
            print("❌ 图片生成失败：提示词为空")
            return None
        
        print(f"🎨 正在使用 {self.model} 模型生成图片...")
        print(f"📝 提示词长度: {len(image_prompt)} 字符")
        
        try:
            # 准备API请求
            message_content = [{"type": "text", "text": image_prompt}]
            
            data = {
                "model": self.model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            print(f"🔄 正在向 {self.model} 发送请求...")
            
            # 限流：等待令牌
            self.token_bucket.consume()
            
            # 发送请求（使用改进的超时设置）
            response = self.session.post(
                self.api_url, 
                json=data, 
                headers=headers, 
                timeout=(30, 600)  # (连接超时30秒, 读取超时600秒/10分钟)
            )
            
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            if "error" in result:
                print(f"❌ API错误: {result['error']['message']}")
                return None
            
            print(f"✅ {self.model} 模型响应成功")
            
            # 下载生成的图片
            image_paths = self._download_images_from_response(result, topic_title)
            
            if image_paths:
                print(f"✅ 成功生成并下载 {len(image_paths)} 张图片")
                return image_paths
            else:
                print("❌ 未能从响应中提取到图片")
                return None
                
        except requests.exceptions.Timeout as e:
            print(f"❌ 图片生成超时: {e}")
            print(f"💡 建议：API服务器响应较慢，请稍后重试或使用 --text-only 选项跳过图片生成")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 图片生成连接错误: {e}")
            print(f"💡 建议：检查网络连接或API服务器状态")
            return None
        except Exception as e:
            print(f"❌ 图片生成失败: {e}")
            return None
    
    def _download_images_from_response(self, result: dict, topic_title: str) -> List[str]:
        """从API响应中下载图片"""
        image_paths = []

        if "choices" not in result or not isinstance(result["choices"], list):
            print("❌ API响应格式错误：缺少choices字段")
            return image_paths

        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', topic_title)[:50] if topic_title else "image"
        output_dir = os.path.join("temp_images", f"{timestamp}_{safe_title}")
        os.makedirs(output_dir, exist_ok=True)

        print(f"📁 创建输出目录: {output_dir}")

        # 处理第一个choice（通常只有一个）
        first_choice = result["choices"][0]
        if "message" not in first_choice or "content" not in first_choice["message"]:
            print("❌ API响应格式错误：缺少message或content字段")
            return image_paths

        content = first_choice["message"]["content"]
        print(f"🔍 响应内容长度: {len(content)} 字符")

        # 提取图片下载链接（改进版）
        download_patterns = [
            r'\[(?:点击下载|Click to download)\]\((https?://[^\s\)]+)\)',  # 标准格式
            r'(https?://filesystem\.site/[^\s]+\.(?:png|jpg|jpeg|gif|webp))',  # filesystem.site直接链接
            r'(https?://[^\s]+/cdn/[^\s]+\.(?:png|jpg|jpeg|gif|webp))',  # CDN链接
            r'!\[.*?\]\((https?://[^\s\)]+)\)',  # Markdown图片格式
        ]
        
        download_links = []
        for pattern in download_patterns:
            links = re.findall(pattern, content)
            download_links.extend(links)
        
        # 去重并过滤有效链接
        download_links = list(set(download_links))
        
        # 过滤掉已知的无效链接
        valid_links = []
        for link in download_links:
            # 跳过 OpenAI 视频链接（这些通常无法下载）
            if "videos.openai.com" in link:
                print(f"⚠️ 跳过无效的OpenAI视频链接: {link[:100]}...")
                continue
            # 优先选择 filesystem.site 链接
            if "filesystem.site" in link:
                valid_links.insert(0, link)  # 插入到前面，优先尝试
            else:
                valid_links.append(link)
        
        download_links = valid_links
        
        if not download_links:
            print("⚠️ 未在响应中找到图片下载链接")
            print(f"响应内容预览: {content[:500]}...")
            return image_paths

        print(f"🔗 找到 {len(download_links)} 个有效图片链接")
        if download_links:
            for i, link in enumerate(download_links, 1):
                print(f"   {i}. {link[:80]}{'...' if len(link) > 80 else ''}")

        # 下载所有有效的图片链接
        for i, image_url in enumerate(download_links):
            try:
                print(f"📥 正在下载图片: {image_url}")
                
                # 下载图片（使用改进的超时和重试）
                image_response = self.session.get(image_url, timeout=(10, 120))  # 连接10秒，下载120秒
                image_response.raise_for_status()

                # 确定文件扩展名
                ext = "png"  # 默认扩展名
                url_match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", image_url)
                if url_match:
                    ext = url_match.group(1).split("?")[0]
                    if len(ext) > 5 or ext not in ['png', 'jpg', 'jpeg', 'gif', 'webp']:
                        ext = "png"

                # 生成文件名
                file_name = f"{result.get('id', f'image_{i+1}')}.{ext}"
                file_path = os.path.join(output_dir, file_name)

                # 保存图片
                with open(file_path, "wb") as f:
                    f.write(image_response.content)

                image_paths.append(file_path)
                print(f"✅ 图片已保存: {file_path}")
                
                # 获取文件大小信息
                file_size = len(image_response.content)
                print(f"📊 文件大小: {file_size / 1024:.1f} KB")
                
                # 成功下载一张图片后就停止（按需求每个选题只生成一张图片）
                break

            except requests.exceptions.Timeout as e:
                print(f"⏰ 下载图片超时: {image_url} - {e}")
                print(f"💡 正在尝试下一个图片链接...")
                continue
            except requests.exceptions.ConnectionError as e:
                print(f"🌐 下载图片连接错误: {image_url} - {e}")
                continue
            except Exception as e:
                print(f"❌ 下载图片失败: {image_url} - {e}")
                continue

        return image_paths
    
    def is_available(self) -> bool:
        """检查图片生成功能是否可用"""
        return bool(self.api_token)
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model": self.model,
            "api_url": self.api_url,
            "available": self.is_available()
        }


# 创建全局图片创建器实例
image_creator = ImageCreator()