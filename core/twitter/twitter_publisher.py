#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 直接发布模块
直接发布 Thread 到 Twitter（不通过草稿）
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


class TwitterPublisher:
    """Twitter 直接发布器"""

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
                self.username = me.data.username
                self.is_available = True
                print(f"✅ Twitter Publisher 初始化成功: @{self.username}")
            except Exception as e:
                print(f"⚠️ Twitter API 认证验证失败: {e}")
                self.is_available = False
                
        except Exception as e:
            print(f"❌ Twitter Publisher 初始化失败: {e}")
            self.client = None
            self.is_available = False

    def publish_thread(self, thread: List[Dict[str, str]], title: str = "", delay_seconds: int = 2) -> bool:
        """
        直接发布 Thread 到 Twitter
        
        Args:
            thread: Thread 内容列表，格式: [{"tweet": "内容"}, ...]
            title: Thread 标题（仅用于日志显示）
            delay_seconds: 推文之间的延迟时间（秒）
            
        Returns:
            是否发布成功
        """
        if not self.is_available or not self.client:
            print("❌ Twitter Publisher 不可用")
            return False

        if not thread:
            print("❌ Thread 内容为空")
            return False

        print(f"🚀 开始直接发布 Thread 到 Twitter")
        if title:
            print(f"📝 Thread 标题: {title}")
        print(f"📊 包含 {len(thread)} 条推文")

        # 预览推文内容
        print(f"\n📱 Thread 预览:")
        for i, tweet_obj in enumerate(thread, 1):
            tweet_text = tweet_obj.get('tweet', '')
            print(f"{i}/{len(thread)}: {tweet_text[:100]}{'...' if len(tweet_text) > 100 else ''}")

        try:
            tweet_ids = []
            published_tweets = []
            
            for i, tweet_obj in enumerate(thread):
                tweet_text = tweet_obj.get('tweet', '')
                
                if not tweet_text:
                    print(f"⚠️ 第 {i+1} 条推文内容为空，跳过")
                    continue

                print(f"\n📤 发布第 {i+1}/{len(thread)} 条推文...")
                print(f"内容: {tweet_text}")
                
                try:
                    if i == 0:
                        # 第一条推文
                        response = self.client.create_tweet(text=tweet_text)
                    else:
                        # 回复前一条推文，形成线程
                        response = self.client.create_tweet(
                            text=tweet_text,
                            in_reply_to_tweet_id=tweet_ids[-1]
                        )
                    
                    tweet_id = response.data['id']
                    tweet_ids.append(tweet_id)
                    published_tweets.append({
                        'tweet_id': tweet_id,
                        'content': tweet_text,
                        'position': i + 1
                    })
                    
                    tweet_url = f"https://twitter.com/{self.username}/status/{tweet_id}"
                    print(f"✅ 第 {i+1} 条推文发布成功")
                    print(f"🔗 链接: {tweet_url}")
                    
                    # 延迟避免限制
                    if i < len(thread) - 1:
                        print(f"⏳ 等待 {delay_seconds} 秒...")
                        time.sleep(delay_seconds)
                        
                except Exception as e:
                    print(f"❌ 第 {i+1} 条推文发布失败: {e}")
                    # 如果发布失败，返回已发布的推文信息
                    if tweet_ids:
                        print(f"⚠️ 已发布 {len(tweet_ids)} 条推文，后续发布中断")
                        self._save_partial_result(published_tweets, title)
                    return False

            print(f"\n🎉 Thread 发布完成！")
            print(f"✅ 成功发布 {len(tweet_ids)} 条推文")
            print(f"🔗 Thread 链接: https://twitter.com/{self.username}/status/{tweet_ids[0]}")
            
            # 保存发布记录
            self._save_publish_result(published_tweets, title)
            
            return True

        except Exception as e:
            print(f"❌ 发布 Thread 失败: {e}")
            return False

    def publish_thread_from_file(self, thread_file: str, delay_seconds: int = 2) -> bool:
        """
        从文件读取 Thread 并直接发布到 Twitter
        
        Args:
            thread_file: Thread 文件路径
            delay_seconds: 推文之间的延迟时间（秒）
            
        Returns:
            是否发布成功
        """
        if not os.path.exists(thread_file):
            print(f"❌ Thread 文件不存在: {thread_file}")
            return False

        try:
            with open(thread_file, 'r', encoding='utf-8') as f:
                thread_data = json.load(f)
            
            # 如果是完整的线程数据结构
            if isinstance(thread_data, dict) and 'thread' in thread_data:
                thread = thread_data['thread']
                title = thread_data.get('title', '')
            # 如果直接是线程数组
            elif isinstance(thread_data, list):
                thread = thread_data
                title = os.path.splitext(os.path.basename(thread_file))[0]
            else:
                print(f"❌ Thread 文件格式错误: {thread_file}")
                return False
            
            return self.publish_thread(thread, title, delay_seconds)
            
        except json.JSONDecodeError as e:
            print(f"❌ Thread 文件 JSON 格式错误: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 读取 Thread 文件失败: {str(e)}")
            return False

    def _save_publish_result(self, published_tweets: List[Dict], title: str):
        """保存发布结果"""
        try:
            from datetime import datetime
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            timestamp = now.strftime("%H%M%S")
            
            # 创建发布记录目录
            publish_dir = f"output/published/{date_folder}"
            os.makedirs(publish_dir, exist_ok=True)
            
            filename = f"{publish_dir}/twitter_published_{timestamp}.json"
            
            publish_data = {
                "title": title,
                "published_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tweets": len(published_tweets),
                "status": "published",
                "tweets": published_tweets,
                "thread_url": f"https://twitter.com/{self.username}/status/{published_tweets[0]['tweet_id']}" if published_tweets else ""
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(publish_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 发布记录已保存: {filename}")
            
        except Exception as e:
            print(f"⚠️ 保存发布记录失败: {e}")

    def _save_partial_result(self, published_tweets: List[Dict], title: str):
        """保存部分发布结果（发布中断时使用）"""
        try:
            from datetime import datetime
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            timestamp = now.strftime("%H%M%S")
            
            # 创建发布记录目录
            publish_dir = f"output/published/{date_folder}"
            os.makedirs(publish_dir, exist_ok=True)
            
            filename = f"{publish_dir}/twitter_partial_{timestamp}.json"
            
            publish_data = {
                "title": title,
                "published_at": now.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tweets": len(published_tweets),
                "status": "partial",
                "tweets": published_tweets,
                "thread_url": f"https://twitter.com/{self.username}/status/{published_tweets[0]['tweet_id']}" if published_tweets else "",
                "note": "部分发布，后续推文发布失败"
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(publish_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 部分发布记录已保存: {filename}")
            
        except Exception as e:
            print(f"⚠️ 保存部分发布记录失败: {e}")

    def test_connection(self) -> bool:
        """
        测试 Twitter API 连接
        
        Returns:
            连接是否正常
        """
        if not self.is_available or not self.client:
            print("❌ Twitter Publisher 不可用")
            return False
        
        try:
            me = self.client.get_me()
            print(f"✅ Twitter API 连接正常: @{me.data.username}")
            return True
        except Exception as e:
            print(f"❌ Twitter API 连接测试失败: {str(e)}")
            return False


# 全局 Twitter 发布器实例（延迟初始化）
twitter_publisher = None

def get_twitter_publisher():
    """获取 Twitter 发布器实例（延迟初始化）"""
    global twitter_publisher
    if twitter_publisher is None:
        try:
            twitter_publisher = TwitterPublisher()
        except Exception as e:
            print(f"⚠️ Twitter Publisher 初始化失败: {str(e)}")
            twitter_publisher = None
    return twitter_publisher