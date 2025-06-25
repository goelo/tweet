#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于Thread的双模型图片生成器
使用改写后的Thread内容生成图片提示词，然后调用图片生成
"""

import os
from typing import Dict, Optional, List, Tuple
from ..gpt.rewriter import GPTRewriter
from .prompt_generator import prompt_generator
from .image_creator import image_creator


class ThreadBasedImageGenerator:
    """基于Thread的双模型图片生成器"""
    
    def __init__(self):
        self.rewriter = None
        self.prompt_generator = prompt_generator
        self.image_creator = image_creator
        
        # 初始化改写器
        try:
            self.rewriter = GPTRewriter()
            print("✅ Thread改写器初始化成功")
        except Exception as e:
            print(f"❌ Thread改写器初始化失败: {e}")
    
    def generate_image_with_thread_content(self, topic: Dict[str, str], english_mode: bool = False) -> Optional[Tuple[str, str, List[str]]]:
        """
        基于Thread内容生成图片
        
        Args:
            topic: 话题信息字典，包含 title, keywords, summary 等
            english_mode: 是否生成英文Thread
            
        Returns:
            元组 (生成的Thread内容, 图片提示词, 图片文件路径列表) 或 None
        """
        print(f"🚀 开始基于Thread的图片生成流程")
        print(f"📋 话题: {topic.get('title', '未知话题')}")
        print(f"🌐 语言: {'英文' if english_mode else '中文'}")
        print("-" * 60)
        
        # 检查系统可用性
        if not self._check_availability():
            return None
        
        # 第一步：生成Thread内容
        print("🔄 第一步：改写为Thread内容...")
        thread = self._generate_thread(topic, english_mode)
        
        if not thread:
            print("❌ 第一步失败：无法生成Thread内容")
            return None
        
        print(f"✅ 第一步完成：成功生成 {len(thread)} 条Thread")
        
        # 提取Thread文本内容
        thread_content = self._extract_thread_content(thread)
        print(f"📝 Thread内容预览: {thread_content[:200]}...")
        print("-" * 60)
        
        # 第二步：基于Thread内容生成图片提示词
        print("🔄 第二步：基于Thread内容生成图片提示词...")
        
        # 创建基于Thread的topic
        thread_topic = self._create_thread_based_topic(topic, thread_content)
        image_prompt = self.prompt_generator.generate_image_prompt(thread_topic)
        
        if not image_prompt:
            print("❌ 第二步失败：无法生成图片提示词")
            return None
        
        print(f"✅ 第二步完成：成功生成提示词 ({len(image_prompt)} 字符)")
        print(f"📝 提示词预览: {image_prompt[:200]}...")
        print("-" * 60)
        
        # 第三步：使用 gpt-4o-image-vip 模型生成图片
        print("🎨 第三步：生成图片...")
        image_paths = self.image_creator.create_image(image_prompt, topic.get('title', ''))
        
        if not image_paths:
            print("❌ 第三步失败：无法生成图片")
            return None
        
        print(f"✅ 第三步完成：成功生成 {len(image_paths)} 张图片")
        print("📁 图片路径:")
        for i, path in enumerate(image_paths, 1):
            print(f"   {i}. {path}")
        
        print("-" * 60)
        print("🎉 基于Thread的图片生成流程完成！")
        
        return thread_content, image_prompt, image_paths
    
    def _generate_thread(self, topic: Dict[str, str], english_mode: bool = False) -> Optional[List[Dict[str, str]]]:
        """生成Thread内容"""
        try:
            if english_mode:
                thread = self.rewriter.rewrite_note_to_english_thread(
                    title=topic.get('title', ''),
                    description=topic.get('controversy', topic.get('summary', '')),
                    tags=topic.get('keywords', ''),
                    summary=topic.get('summary', ''),
                    conclusion=topic.get('conclusion', ''),
                    level=topic.get('level', 3)
                )
            else:
                thread = self.rewriter.rewrite_note_to_thread(
                    title=topic.get('title', ''),
                    description=topic.get('controversy', topic.get('summary', '')),
                    tags=topic.get('keywords', ''),
                    summary=topic.get('summary', ''),
                    conclusion=topic.get('conclusion', ''),
                    level=topic.get('level', 3)
                )
            return thread
        except Exception as e:
            print(f"❌ Thread生成失败: {e}")
            return None
    
    def _extract_thread_content(self, thread: List[Dict[str, str]]) -> str:
        """提取Thread的文本内容"""
        if not thread:
            return ""
        
        # 合并所有Thread内容
        content_parts = []
        for tweet in thread:
            tweet_text = tweet.get('tweet', '').strip()
            if tweet_text:
                content_parts.append(tweet_text)
        
        return ' '.join(content_parts)
    
    def _create_thread_based_topic(self, original_topic: Dict[str, str], thread_content: str) -> Dict[str, str]:
        """基于Thread内容创建新的topic"""
        # 限制thread_content长度，避免提示词过长
        max_summary_length = 800
        summary = thread_content[:max_summary_length] + '...' if len(thread_content) > max_summary_length else thread_content
        
        return {
            'title': original_topic.get('title', ''),
            'keywords': original_topic.get('keywords', ''),
            'summary': summary,
            'controversy': original_topic.get('controversy', ''),
            'level': original_topic.get('level', 3)
        }
    
    def generate_image_for_topic(self, topic: Dict[str, str], english_mode: bool = False) -> Optional[List[str]]:
        """
        为话题生成图片（兼容原有接口）
        
        Args:
            topic: 话题信息字典
            english_mode: 是否使用英文模式
            
        Returns:
            图片文件路径列表
        """
        result = self.generate_image_with_thread_content(topic, english_mode)
        if result:
            _, _, image_paths = result
            return image_paths
        return None
    
    def generate_image_from_existing_thread(self, topic: Dict[str, str], thread: List[Dict[str, str]]) -> Optional[List[str]]:
        """
        使用已经生成的Thread内容生成图片（避免重复改写）
        
        Args:
            topic: 话题信息字典
            thread: 已经生成的Thread内容
            
        Returns:
            图片文件路径列表
        """
        print(f"🚀 使用已有Thread内容生成图片")
        print(f"📋 话题: {topic.get('title', '未知话题')}")
        print(f"📝 Thread条数: {len(thread)}")
        print("-" * 60)
        
        # 检查必要组件
        if not self.prompt_generator or not self.image_creator.is_available():
            print("❌ 图片生成组件不可用")
            return None
        
        # 提取Thread文本内容
        thread_content = self._extract_thread_content(thread)
        print(f"📝 Thread内容预览: {thread_content[:200]}...")
        print("-" * 60)
        
        # 基于Thread内容生成图片提示词
        print("🔄 步骤1：基于Thread内容生成图片提示词...")
        thread_topic = self._create_thread_based_topic(topic, thread_content)
        image_prompt = self.prompt_generator.generate_image_prompt(thread_topic)
        
        if not image_prompt:
            print("❌ 步骤1失败：无法生成图片提示词")
            return None
        
        print(f"✅ 步骤1完成：成功生成提示词 ({len(image_prompt)} 字符)")
        print(f"📝 提示词预览: {image_prompt[:200]}...")
        print("-" * 60)
        
        # 使用 gpt-4o-image-vip 模型生成图片
        print("🎨 步骤2：生成图片...")
        image_paths = self.image_creator.create_image(image_prompt, topic.get('title', ''))
        
        if not image_paths:
            print("❌ 步骤2失败：无法生成图片")
            return None
        
        print(f"✅ 步骤2完成：成功生成 {len(image_paths)} 张图片")
        print("📁 图片路径:")
        for i, path in enumerate(image_paths, 1):
            print(f"   {i}. {path}")
        
        print("-" * 60)
        print("🎉 使用已有Thread的图片生成完成！")
        
        return image_paths
    
    def generate_thread_and_prompt_only(self, topic: Dict[str, str], english_mode: bool = False) -> Optional[Tuple[str, str]]:
        """
        仅生成Thread和图片提示词（不生成图片）
        
        Args:
            topic: 话题信息字典
            english_mode: 是否使用英文模式
            
        Returns:
            元组 (Thread内容, 图片提示词) 或 None
        """
        print(f"📝 仅生成Thread和提示词模式")
        print(f"📋 话题: {topic.get('title', '未知话题')}")
        print(f"🌐 语言: {'英文' if english_mode else '中文'}")
        
        if not self.rewriter or not self.prompt_generator:
            print("❌ 组件不可用")
            return None
        
        # 生成Thread
        thread = self._generate_thread(topic, english_mode)
        if not thread:
            print("❌ Thread生成失败")
            return None
        
        # 提取Thread内容
        thread_content = self._extract_thread_content(thread)
        
        # 生成图片提示词
        thread_topic = self._create_thread_based_topic(topic, thread_content)
        image_prompt = self.prompt_generator.generate_image_prompt(thread_topic)
        
        if not image_prompt:
            print("❌ 图片提示词生成失败")
            return None
        
        return thread_content, image_prompt
    
    def _check_availability(self) -> bool:
        """检查系统可用性"""
        rewriter_available = self.rewriter is not None
        prompt_available = self.prompt_generator is not None
        image_available = self.image_creator.is_available()
        
        if not rewriter_available:
            print("❌ Thread改写器不可用")
        
        if not prompt_available:
            print("❌ 提示词生成器不可用")
        
        if not image_available:
            print("❌ 图片创建器不可用")
        
        return rewriter_available and prompt_available and image_available
    
    def is_available(self) -> bool:
        """检查系统是否可用"""
        return self._check_availability()
    
    def get_system_info(self) -> Dict[str, any]:
        """获取系统信息"""
        return {
            "rewriter": {
                "available": self.rewriter is not None,
                "model": getattr(self.rewriter, 'thread_prompt_file', 'unknown')
            },
            "prompt_generator": {
                "available": self.prompt_generator is not None,
                "model": getattr(self.prompt_generator, 'rewrite_model', 'unknown')
            },
            "image_creator": self.image_creator.get_model_info() if self.image_creator else {},
            "overall_available": self.is_available()
        }
    
    def test_system(self, english_mode: bool = False) -> bool:
        """测试系统功能"""
        print("🧪 测试基于Thread的图片生成系统")
        print("=" * 60)
        
        # 创建测试话题
        test_topic = {
            'title': '测试话题：基于Thread的图片生成验证',
            'keywords': 'Thread生成, 图片创建, 测试验证',
            'summary': '这是一个用于测试基于Thread内容的图片生成功能的话题，验证三步调用流程是否正常工作。',
            'controversy': 'Thread生成和图片创建的整合存在技术挑战',
            'level': 2
        }
        
        # 检查系统可用性
        if not self.is_available():
            print("❌ 系统不可用，测试失败")
            return False
        
        print("✅ 系统可用性检查通过")
        print("🔄 开始生成测试...")
        
        # 执行测试
        result = self.generate_image_with_thread_content(test_topic, english_mode)
        
        if result:
            thread_content, prompt, image_paths = result
            print(f"\n🎉 测试成功！")
            print(f"📝 Thread内容长度: {len(thread_content)} 字符")
            print(f"📝 生成提示词长度: {len(prompt)} 字符")
            print(f"🖼️  生成图片数量: {len(image_paths)}")
            print("=" * 60)
            return True
        else:
            print(f"\n❌ 测试失败")
            print("=" * 60)
            return False


# 创建全局基于Thread的图片生成器实例
thread_based_generator = ThreadBasedImageGenerator()