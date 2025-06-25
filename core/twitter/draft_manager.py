#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 草稿管理模块
将 Thread 保存到 Twitter 草稿箱
"""

import os
import sys
import json
import time
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False
    print("⚠️ tweepy 库未安装，请运行: pip install tweepy")

from core.config.config import config


class TwitterDraftManager:
    """Twitter 草稿管理器"""

    def __init__(self):
        if not TWEEPY_AVAILABLE:
            raise ImportError("Tweepy 库未安装，请先安装: pip install tweepy")

        if config is None:
            raise ValueError("配置未正确加载，请检查 .env 文件")

        # 设置 Twitter API 配置
        self.api_key = config.twitter_api_key
        self.api_secret = config.twitter_api_secret
        self.access_token = config.twitter_access_token
        self.access_token_secret = config.twitter_access_token_secret
        self.bearer_token = config.twitter_bearer_token

        # 初始化 Twitter API 客户端
        try:
            # 使用 API v2
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_token_secret,
                wait_on_rate_limit=True
            )
            
            # 验证认证
            try:
                me = self.client.get_me()
                print(f"✅ Twitter API 认证成功: @{me.data.username}")
            except Exception as e:
                print(f"⚠️ Twitter API 认证验证失败: {e}")
                
        except Exception as e:
            print(f"❌ Twitter API 初始化失败: {e}")
            self.client = None

    def save_thread_as_drafts(self, thread: List[Dict[str, str]], thread_title: str = "Thread") -> bool:
        """
        将 Thread 保存为 Twitter 草稿
        
        Args:
            thread: Thread 内容列表
            thread_title: Thread 标题
            
        Returns:
            是否保存成功
        """
        if not self.client:
            print("❌ Twitter API 客户端未初始化")
            return False

        print(f"📝 开始保存 Thread 到草稿箱: {thread_title}")
        print(f"📊 Thread 包含 {len(thread)} 条推文")

        try:
            # 注意: Twitter API v2 目前不直接支持创建草稿
            # 这里我们将 Thread 保存到本地文件，作为草稿管理
            draft_data = {
                "title": thread_title,
                "thread": thread,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "draft",
                "total_tweets": len(thread)
            }

            # 保存到本地草稿文件
            draft_filename = self._save_local_draft(draft_data)
            
            if draft_filename:
                print(f"✅ Thread 已保存为草稿: {draft_filename}")
                print("💡 你可以稍后使用 publish_draft() 方法发布这个 Thread")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ 保存草稿失败: {e}")
            return False

    def _save_local_draft(self, draft_data: Dict) -> Optional[str]:
        """保存草稿到本地文件"""
        try:
            from datetime import datetime
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            timestamp = now.strftime("%H%M%S")
            
            # 创建按日期分类的目录
            draft_dir = f"output/drafts/{date_folder}"
            os.makedirs(draft_dir, exist_ok=True)
            
            filename = f"{draft_dir}/twitter_draft_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            return filename
        except Exception as e:
            print(f"❌ 保存本地草稿失败: {e}")
            return None

    def list_drafts(self) -> List[str]:
        """列出所有草稿文件"""
        try:
            draft_files = []
            drafts_dir = "output/drafts"
            
            # 查找新的目录结构中的草稿
            if os.path.exists(drafts_dir):
                for date_folder in os.listdir(drafts_dir):
                    date_path = os.path.join(drafts_dir, date_folder)
                    if os.path.isdir(date_path):
                        for filename in os.listdir(date_path):
                            if filename.startswith("twitter_draft_") and filename.endswith(".json"):
                                draft_files.append(os.path.join(date_path, filename))
            
            # 同时查找旧的目录结构中的草稿（向后兼容）
            output_dir = "output"
            if os.path.exists(output_dir):
                for filename in os.listdir(output_dir):
                    if filename.startswith("twitter_draft_") and filename.endswith(".json"):
                        draft_files.append(os.path.join(output_dir, filename))
            
            return sorted(draft_files, reverse=True)  # 最新的在前面
        except Exception as e:
            print(f"❌ 列出草稿失败: {e}")
            return []

    def load_draft(self, draft_file: str) -> Optional[Dict]:
        """加载草稿文件"""
        try:
            with open(draft_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载草稿失败: {e}")
            return None

    def publish_draft(self, draft_file: str, delay_seconds: int = 2) -> bool:
        """
        发布草稿 Thread
        
        Args:
            draft_file: 草稿文件路径
            delay_seconds: 推文之间的延迟时间（秒）
            
        Returns:
            是否发布成功
        """
        if not self.client:
            print("❌ Twitter API 客户端未初始化")
            return False

        # 加载草稿
        draft_data = self.load_draft(draft_file)
        if not draft_data:
            return False

        thread = draft_data.get('thread', [])
        if not thread:
            print("❌ 草稿中没有 Thread 内容")
            return False

        print(f"🚀 开始发布 Thread: {draft_data.get('title', 'Untitled')}")
        print(f"📊 包含 {len(thread)} 条推文")

        try:
            tweet_ids = []
            
            for i, tweet_obj in enumerate(thread):
                tweet_text = tweet_obj.get('tweet', '')
                
                if not tweet_text:
                    print(f"⚠️ 第 {i+1} 条推文内容为空，跳过")
                    continue

                print(f"📤 发布第 {i+1}/{len(thread)} 条推文...")
                
                try:
                    if i == 0:
                        # 第一条推文
                        response = self.client.create_tweet(text=tweet_text)
                    else:
                        # 回复前一条推文
                        response = self.client.create_tweet(
                            text=tweet_text,
                            in_reply_to_tweet_id=tweet_ids[-1]
                        )
                    
                    tweet_ids.append(response.data['id'])
                    print(f"✅ 第 {i+1} 条推文发布成功")
                    
                    # 延迟避免限制
                    if i < len(thread) - 1:
                        time.sleep(delay_seconds)
                        
                except Exception as e:
                    print(f"❌ 第 {i+1} 条推文发布失败: {e}")
                    return False

            print(f"🎉 Thread 发布完成！共发布 {len(tweet_ids)} 条推文")
            
            # 更新草稿状态
            draft_data['status'] = 'published'
            draft_data['published_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            draft_data['tweet_ids'] = tweet_ids
            
            # 保存更新后的草稿
            with open(draft_file, 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)
            
            return True

        except Exception as e:
            print(f"❌ 发布 Thread 失败: {e}")
            return False

    def preview_draft(self, draft_file: str):
        """预览草稿内容"""
        draft_data = self.load_draft(draft_file)
        if not draft_data:
            return

        print(f"\n📋 草稿预览: {draft_data.get('title', 'Untitled')}")
        print(f"📅 创建时间: {draft_data.get('created_at', 'Unknown')}")
        print(f"📊 状态: {draft_data.get('status', 'Unknown')}")
        print(f"🔢 推文数量: {draft_data.get('total_tweets', 0)}")
        print("=" * 50)

        thread = draft_data.get('thread', [])
        for i, tweet_obj in enumerate(thread, 1):
            tweet = tweet_obj.get('tweet', '')
            print(f"{i}/{len(thread)}: {tweet}")
            print("-" * 30)


# 全局 Twitter 草稿管理器实例（延迟初始化）
twitter_draft_manager = None

def get_twitter_draft_manager():
    """获取 Twitter 草稿管理器实例（延迟初始化）"""
    global twitter_draft_manager
    if twitter_draft_manager is None:
        try:
            twitter_draft_manager = TwitterDraftManager()
        except Exception as e:
            print(f"Twitter 草稿管理器初始化失败: {e}")
            twitter_draft_manager = None
    return twitter_draft_manager
