#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布模块
处理 Tweet 内容发布（默认关闭）
"""

import os
import sys
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config.config import config


class Publisher:
    """发布管理器"""
    
    def __init__(self):
        if not config:
            raise ValueError("配置未正确加载")
        
        self.config = config
        self.enabled = config.enable_publishing
        
        if not self.enabled:
            print("📝 发布功能已禁用（默认状态）")
            print("💡 如需启用发布功能，请在 .env 文件中设置 ENABLE_PUBLISHING=true")
            return
        
        print("🚀 发布功能已启用")
        
        # 这里可以添加其他发布平台的客户端初始化
        # 例如: Twitter API, 微博 API 等

    def is_available(self) -> bool:
        """检查发布功能是否可用"""
        return self.enabled

    def publish_thread(self, thread: List[Dict], topic: str = "", images: List[str] = None) -> bool:
        """
        发布 Thread 到社交媒体平台
        
        Args:
            thread: Thread 内容列表
            topic: 选题标题
            images: 图片文件路径列表
            
        Returns:
            是否发布成功
        """
        if not self.is_available():
            print("❌ 发布功能未启用")
            return False
        
        print(f"📤 准备发布 Thread: {topic}")
        print(f"   推文数量: {len(thread)}")
        if images:
            print(f"   图片数量: {len(images)}")
        
        # 这里添加实际的发布逻辑
        # 例如调用 Twitter API、微博 API 等
        
        print("⚠️ 发布功能尚未实现具体逻辑")
        print("💡 当前仅保存到本地文件")
        
        return self._save_to_local(thread, topic, images)

    def _save_to_local(self, thread: List[Dict], topic: str, images: List[str] = None) -> bool:
        """
        保存到本地作为草稿
        
        Args:
            thread: Thread 内容
            topic: 选题
            images: 图片路径列表
            
        Returns:
            是否保存成功
        """
        try:
            from datetime import datetime
            import json
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"draft_{timestamp}_{topic[:20].replace('/', '_')}.json"
            filepath = os.path.join(self.config.output_dir, filename)
            
            draft_data = {
                "timestamp": timestamp,
                "topic": topic,
                "thread": thread,
                "images": images or [],
                "status": "draft",
                "platform": "local"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 草稿已保存: {filename}")
            return True
            
        except Exception as e:
            print(f"❌ 保存草稿失败: {e}")
            return False

    def preview_thread(self, thread: List[Dict], topic: str = "") -> None:
        """
        预览 Thread 内容
        
        Args:
            thread: Thread 内容
            topic: 选题标题
        """
        print(f"\n📋 Thread 预览: {topic}")
        print("=" * 60)
        
        for i, tweet in enumerate(thread, 1):
            content = tweet.get("tweet", "")
            print(f"{i:2d}. {content}")
            print("-" * 40)
        
        print(f"总计: {len(thread)} 条推文")
        print("=" * 60)

    def enable_publishing(self) -> None:
        """临时启用发布功能（当前会话有效）"""
        self.enabled = True
        print("✅ 发布功能已临时启用")
        print("💡 如需永久启用，请在 .env 文件中设置 ENABLE_PUBLISHING=true")

    def disable_publishing(self) -> None:
        """禁用发布功能"""
        self.enabled = False
        print("❌ 发布功能已禁用")


# 创建全局发布器实例
try:
    publisher = Publisher()
except Exception as e:
    print(f"❌ 发布器初始化失败: {e}")
    publisher = None