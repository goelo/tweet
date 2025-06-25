#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双模型图片生成器
整合两步调用流程：
1. 使用改写模型生成图片提示词
2. 使用 gpt-4o-image-vip 模型生成图片
"""

import os
from typing import Dict, Optional, List, Tuple
from .prompt_generator import prompt_generator
from .image_creator import image_creator


class DualModelImageGenerator:
    """双模型图片生成器"""
    
    def __init__(self):
        self.prompt_generator = prompt_generator
        self.image_creator = image_creator
    
    def generate_image_with_dual_models(self, topic: Dict[str, str]) -> Optional[Tuple[str, List[str]]]:
        """
        使用双模型生成图片
        
        Args:
            topic: 话题信息字典，包含 title, keywords, summary 等
            
        Returns:
            元组 (生成的提示词, 图片文件路径列表) 或 None
        """
        print(f"🚀 开始双模型图片生成流程")
        print(f"📋 话题: {topic.get('title', '未知话题')}")
        print("-" * 60)
        
        # 检查两个模型是否都可用
        if not self._check_availability():
            return None
        
        # 第一步：使用改写模型生成图片提示词
        print("🔄 第一步：生成图片提示词...")
        image_prompt = self.prompt_generator.generate_image_prompt(topic)
        
        if not image_prompt:
            print("❌ 第一步失败：无法生成图片提示词")
            return None
        
        print(f"✅ 第一步完成：成功生成提示词 ({len(image_prompt)} 字符)")
        print(f"📝 提示词预览: {image_prompt[:200]}...")
        print("-" * 60)
        
        # 第二步：使用 gpt-4o-image-vip 模型生成图片
        print("🎨 第二步：生成图片...")
        image_paths = self.image_creator.create_image(image_prompt, topic.get('title', ''))
        
        if not image_paths:
            print("❌ 第二步失败：无法生成图片")
            return None
        
        print(f"✅ 第二步完成：成功生成 {len(image_paths)} 张图片")
        print("📁 图片路径:")
        for i, path in enumerate(image_paths, 1):
            print(f"   {i}. {path}")
        
        print("-" * 60)
        print("🎉 双模型图片生成流程完成！")
        
        return image_prompt, image_paths
    
    def generate_image_for_topic(self, topic: Dict[str, str]) -> Optional[List[str]]:
        """
        为话题生成图片（兼容原有接口）
        
        Args:
            topic: 话题信息字典
            
        Returns:
            图片文件路径列表
        """
        result = self.generate_image_with_dual_models(topic)
        if result:
            _, image_paths = result
            return image_paths
        return None
    
    def generate_prompt_only(self, topic: Dict[str, str]) -> Optional[str]:
        """
        仅生成图片提示词（不生成图片）
        
        Args:
            topic: 话题信息字典
            
        Returns:
            生成的图片提示词
        """
        print(f"📝 仅生成提示词模式")
        print(f"📋 话题: {topic.get('title', '未知话题')}")
        
        if not self.prompt_generator:
            print("❌ 提示词生成器不可用")
            return None
        
        return self.prompt_generator.generate_image_prompt(topic)
    
    def create_image_from_prompt(self, image_prompt: str, topic_title: str = "") -> Optional[List[str]]:
        """
        使用现有提示词生成图片
        
        Args:
            image_prompt: 图片提示词
            topic_title: 话题标题
            
        Returns:
            图片文件路径列表
        """
        print(f"🎨 使用现有提示词生成图片")
        print(f"📝 提示词长度: {len(image_prompt)} 字符")
        
        if not self.image_creator.is_available():
            print("❌ 图片创建器不可用")
            return None
        
        return self.image_creator.create_image(image_prompt, topic_title)
    
    def _check_availability(self) -> bool:
        """检查双模型是否都可用"""
        prompt_available = self.prompt_generator is not None
        image_available = self.image_creator.is_available()
        
        if not prompt_available:
            print("❌ 提示词生成器不可用")
        
        if not image_available:
            print("❌ 图片创建器不可用")
        
        return prompt_available and image_available
    
    def is_available(self) -> bool:
        """检查双模型图片生成功能是否可用"""
        return self._check_availability()
    
    def get_system_info(self) -> Dict[str, any]:
        """获取系统信息"""
        return {
            "prompt_generator": {
                "available": self.prompt_generator is not None,
                "model": getattr(self.prompt_generator, 'rewrite_model', 'unknown')
            },
            "image_creator": self.image_creator.get_model_info() if self.image_creator else {},
            "overall_available": self.is_available()
        }
    
    def test_system(self) -> bool:
        """测试系统功能"""
        print("🧪 测试双模型图片生成系统")
        print("=" * 60)
        
        # 创建测试话题
        test_topic = {
            'title': '测试话题：双模型图片生成验证',
            'keywords': '双模型, 图片生成, 测试验证',
            'summary': '这是一个用于测试双模型图片生成功能的话题，验证两步调用流程是否正常工作。'
        }
        
        # 检查系统可用性
        if not self.is_available():
            print("❌ 系统不可用，测试失败")
            return False
        
        print("✅ 系统可用性检查通过")
        print("🔄 开始生成测试...")
        
        # 执行测试
        result = self.generate_image_with_dual_models(test_topic)
        
        if result:
            prompt, image_paths = result
            print(f"\n🎉 测试成功！")
            print(f"📝 生成提示词长度: {len(prompt)} 字符")
            print(f"🖼️  生成图片数量: {len(image_paths)}")
            print("=" * 60)
            return True
        else:
            print(f"\n❌ 测试失败")
            print("=" * 60)
            return False


# 创建全局双模型图片生成器实例
dual_model_generator = DualModelImageGenerator()