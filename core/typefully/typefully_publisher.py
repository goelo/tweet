#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Typefully 发布管理器
管理内容发布到 Typefully 平台
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from .typefully_client import TypefullyClient


class TypefullyPublisher:
    """Typefully 发布管理器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化发布管理器
        
        Args:
            api_key: Typefully API Key
        """
        try:
            self.client = TypefullyClient(api_key)
            self.is_available = True
            print("✅ Typefully 发布管理器初始化成功")
        except Exception as e:
            print(f"❌ Typefully 发布管理器初始化失败: {str(e)}")
            self.client = None
            self.is_available = False
    
    def publish_thread(self, thread: List[Dict[str, str]], title: str = "", **kwargs) -> bool:
        """
        发布线程到 Typefully
        
        Args:
            thread: 推文列表，格式: [{"tweet": "内容"}, ...]
            title: 线程标题（可选）
            **kwargs: 发布选项
                - schedule_date: 计划发布时间
                - auto_retweet_enabled: 是否启用自动转推
                - auto_plug_enabled: 是否启用自动插件
                
        Returns:
            是否发布成功
        """
        if not self.is_available:
            print("❌ Typefully 客户端不可用")
            return False
        
        if not thread:
            print("❌ 线程内容为空")
            return False
        
        try:
            # 提取推文内容
            tweets = []
            for i, tweet_obj in enumerate(thread):
                if isinstance(tweet_obj, dict) and 'tweet' in tweet_obj:
                    tweets.append(tweet_obj['tweet'])
                else:
                    print(f"❌ 第 {i+1} 条推文格式错误: {tweet_obj}")
                    return False
            
            print(f"📤 准备发布 {len(tweets)} 条推文的线程到 Typefully")
            if title:
                print(f"📝 线程标题: {title}")
            
            # 预览推文内容
            print(f"\n📱 线程预览:")
            for i, tweet in enumerate(tweets, 1):
                print(f"{i}/{len(tweets)}: {tweet[:100]}{'...' if len(tweet) > 100 else ''}")
            
            # 创建草稿
            result = self.client.create_thread_draft(tweets, **kwargs)
            
            if result:
                print(f"✅ 线程草稿创建成功")
                
                # 打印结果信息
                if 'id' in result:
                    print(f"📋 草稿ID: {result['id']}")
                if 'url' in result:
                    print(f"🔗 草稿链接: {result['url']}")
                if 'scheduled_date' in result:
                    print(f"⏰ 计划发布时间: {result['scheduled_date']}")
                
                return True
            else:
                print(f"❌ 线程草稿创建失败")
                return False
                
        except Exception as e:
            print(f"❌ 发布线程时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def publish_thread_from_file(self, thread_file: str, **kwargs) -> bool:
        """
        从文件读取线程并发布到 Typefully
        
        Args:
            thread_file: 线程文件路径
            **kwargs: 发布选项
                
        Returns:
            是否发布成功
        """
        if not os.path.exists(thread_file):
            print(f"❌ 线程文件不存在: {thread_file}")
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
                print(f"❌ 线程文件格式错误: {thread_file}")
                return False
            
            return self.publish_thread(thread, title, **kwargs)
            
        except json.JSONDecodeError as e:
            print(f"❌ 线程文件 JSON 格式错误: {str(e)}")
            return False
        except Exception as e:
            print(f"❌ 读取线程文件失败: {str(e)}")
            return False
    
    def schedule_thread(self, thread: List[Dict[str, str]], schedule_date: str, title: str = "") -> bool:
        """
        计划发布线程
        
        Args:
            thread: 推文列表
            schedule_date: 计划发布时间 (ISO 8601 格式)
            title: 线程标题
            
        Returns:
            是否计划成功
        """
        return self.publish_thread(
            thread=thread,
            title=title,
            schedule_date=schedule_date
        )
    
    def get_recent_drafts(self, limit: int = 10) -> Optional[List[Dict]]:
        """
        获取最近的草稿
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最近的草稿列表
        """
        if not self.is_available:
            print("❌ Typefully 客户端不可用")
            return None
        
        try:
            # 获取最近计划和发布的草稿
            scheduled = self.client.get_recently_scheduled() or []
            published = self.client.get_recently_published() or []
            
            # 合并并排序
            all_drafts = scheduled + published
            all_drafts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            return all_drafts[:limit]
            
        except Exception as e:
            print(f"❌ 获取草稿列表失败: {str(e)}")
            return None
    
    def print_recent_drafts(self, limit: int = 10):
        """
        打印最近的草稿
        
        Args:
            limit: 显示数量限制
        """
        drafts = self.get_recent_drafts(limit)
        
        if not drafts:
            print("📭 没有找到最近的草稿")
            return
        
        print(f"📋 最近 {len(drafts)} 个草稿:")
        print("=" * 60)
        
        for i, draft in enumerate(drafts, 1):
            title = draft.get('title', '无标题')
            status = draft.get('status', '未知状态')
            created_at = draft.get('created_at', '未知时间')
            
            print(f"{i:2d}. {title}")
            print(f"    状态: {status}")
            print(f"    创建时间: {created_at}")
            if 'url' in draft:
                print(f"    链接: {draft['url']}")
            print("-" * 40)
    
    def test_api(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否正常
        """
        if not self.is_available:
            print("❌ Typefully 客户端不可用")
            return False
        
        return self.client.test_connection()


# 全局实例
typefully_publisher = None

try:
    # 尝试从环境变量初始化
    api_key = os.getenv('TYPEFULLY_API_KEY')
    if api_key:
        typefully_publisher = TypefullyPublisher(api_key)
    else:
        print("⚠️ 未设置 TYPEFULLY_API_KEY 环境变量，Typefully 发布功能不可用")
        print("💡 请在 .env 文件中添加: TYPEFULLY_API_KEY=your_api_key")
except Exception as e:
    print(f"⚠️ Typefully 发布管理器初始化失败: {str(e)}")
    typefully_publisher = None