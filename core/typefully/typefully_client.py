#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Typefully API 客户端
处理与 Typefully API 的通信
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime


class TypefullyClient:
    """Typefully API 客户端"""
    
    def __init__(self, api_key: str = None):
        """
        初始化 Typefully 客户端
        
        Args:
            api_key: Typefully API Key，如果未提供则从环境变量读取
        """
        self.api_key = api_key or os.getenv('TYPEFULLY_API_KEY')
        if not self.api_key:
            raise ValueError("未找到 Typefully API Key，请设置环境变量 TYPEFULLY_API_KEY 或传入 api_key 参数")
        
        self.base_url = "https://api.typefully.com/v1"
        self.headers = {
            "X-API-KEY": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"✅ Typefully 客户端初始化成功")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """
        发送请求到 Typefully API
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            data: 请求数据
            
        Returns:
            API 响应
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")
            
            # 打印请求详情（调试用）
            print(f"🔍 API 请求: {method} {url}")
            print(f"📤 请求数据: {json.dumps(data, ensure_ascii=False) if data else 'None'}")
            print(f"📥 响应状态: {response.status_code}")
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                print(f"✅ API 请求成功")
                return result
            else:
                print(f"❌ API 请求失败: {response.status_code}")
                print(f"📄 错误信息: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {str(e)}")
            return None
        except Exception as e:
            print(f"❌ 未知错误: {str(e)}")
            return None
    
    def create_draft(self, content: str, **kwargs) -> Optional[Dict]:
        """
        创建草稿
        
        Args:
            content: 推文内容
            **kwargs: 可选参数
                - threadify: 是否自动分片为线程
                - share: 是否包含分享 URL
                - schedule_date: 计划发布时间
                - auto_retweet_enabled: 是否启用自动转推
                - auto_plug_enabled: 是否启用自动插件
                
        Returns:
            创建的草稿信息
        """
        data = {"content": content}
        
        # 添加可选参数
        if kwargs.get('threadify'):
            data['threadify'] = kwargs['threadify']
        if kwargs.get('share'):
            data['share'] = kwargs['share']
        if kwargs.get('schedule_date'):
            data['schedule-date'] = kwargs['schedule_date']
        if kwargs.get('auto_retweet_enabled'):
            data['auto_retweet_enabled'] = kwargs['auto_retweet_enabled']
        if kwargs.get('auto_plug_enabled'):
            data['auto_plug_enabled'] = kwargs['auto_plug_enabled']
        
        return self._make_request("POST", "/drafts/", data)
    
    def create_thread_draft(self, tweets: List[str], **kwargs) -> Optional[Dict]:
        """
        创建线程草稿
        
        Args:
            tweets: 推文列表
            **kwargs: 可选参数
                
        Returns:
            创建的草稿信息
        """
        # 使用 4 个连续换行符分隔推文来创建线程
        content = "\n\n\n\n".join(tweets)
        
        return self.create_draft(content, **kwargs)
    
    def get_recently_scheduled(self) -> Optional[List[Dict]]:
        """
        获取最近计划的草稿
        
        Returns:
            最近计划的草稿列表
        """
        return self._make_request("GET", "/drafts/recently-scheduled/")
    
    def get_recently_published(self) -> Optional[List[Dict]]:
        """
        获取最近发布的草稿
        
        Returns:
            最近发布的草稿列表
        """
        return self._make_request("GET", "/drafts/recently-published/")
    
    def get_notifications(self) -> Optional[List[Dict]]:
        """
        获取通知
        
        Returns:
            通知列表
        """
        return self._make_request("GET", "/notifications/")
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            result = self.get_notifications()
            if result is not None:
                print("✅ Typefully API 连接测试成功")
                return True
            else:
                print("❌ Typefully API 连接测试失败")
                return False
        except Exception as e:
            print(f"❌ Typefully API 连接测试失败: {str(e)}")
            return False