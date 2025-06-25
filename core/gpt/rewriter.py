#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPT 内容改写模块
将内容改写为 Twitter Thread 格式
"""

import os
import json
import time
import random
from typing import List, Dict, Optional
from .gpt_client import gpt_client


class GPTRewriter:
    """GPT 内容改写器"""

    def __init__(self, template_type: str = "twitter", custom_prompt_file: str = None):
        """
        初始化 GPT 改写器
        
        Args:
            template_type: 模板类型 ("twitter", "article")
            custom_prompt_file: 自定义提示词文件路径，如果提供则忽略 template_type
        """
        self.template_type = template_type
        self.custom_prompt_file = custom_prompt_file
        
        if not gpt_client:
            raise ValueError("GPT 客户端未正确初始化，请检查配置")

        # 设置提示词文件路径
        if custom_prompt_file:
            self.thread_prompt_file = custom_prompt_file
        else:
            self.thread_prompt_file = self._get_template_file(template_type)

        # 加载 Thread 提示词模板
        self.thread_prompt = self.load_thread_prompt()

    def _get_template_file(self, template_type: str) -> str:
        """根据模板类型获取对应的提示词文件路径"""
        template_files = {
            "twitter": "input/thread_prompt_twitter.md",
            "article": "input/thread_prompt_article.md"
        }
        
        if template_type not in template_files:
            print(f"⚠️ 未知的模板类型: {template_type}，使用默认twitter模板")
            template_type = "twitter"
        
        return template_files[template_type]

    def load_thread_prompt(self) -> str:
        """加载 Thread 提示词模板文件"""
        try:
            with open(self.thread_prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"✅ 成功加载 {self.thread_prompt_file} 文件")
                return content
        except FileNotFoundError:
            print(f"⚠️ {self.thread_prompt_file} 文件不存在，将使用默认模板")
            return self._get_default_thread_prompt()
        except Exception as e:
            print(f"⚠️ 读取 {self.thread_prompt_file} 失败: {e}")
            return self._get_default_thread_prompt()

    def _get_default_thread_prompt(self) -> str:
        """获取默认的 Thread 提示词模板"""
        return """请将以下内容改写为 Twitter Thread 格式，要求：

1. **Thread 结构**：
   - 第1条：吸引人的开头，包含核心观点和钩子
   - 第2-5条：展开详细内容，每条推文控制在280字符以内
   - 最后1条：总结和行动号召

2. **内容要求**：
   - 保持原文的核心信息和价值
   - 使用更加口语化和社交媒体友好的语言
   - 添加适当的表情符号和话题标签
   - 每条推文都要有独立的价值

3. **输出格式**：
   返回一个包含6条推文的JSON数组，格式如下：
   ```json
   [
     {{"tweet": "第1条推文内容..."}},
     {{"tweet": "第2条推文内容..."}},
     {{"tweet": "第3条推文内容..."}},
     {{"tweet": "第4条推文内容..."}},
     {{"tweet": "第5条推文内容..."}},
     {{"tweet": "第6条推文内容..."}}
   ]
   ```

原始内容：
标题：{title}
描述：{description}
标签：{tags}
内容简介：{summary}
总结：{conclusion}
级别：{level} (1=Confirmed官方确认, 2=Likely可能属实, 3=Rumor传闻待证)

请开始改写："""

    def _get_english_thread_prompt(self) -> str:
        """获取英文 Thread 提示词模板"""
        return """Please rewrite the following content into an English Twitter Thread format with these requirements:

1. **Thread Structure**:
   - Tweet 1: Compelling hook with core insight
   - Tweets 2-5: Detailed breakdown, each tweet under 280 characters
   - Final tweet: Summary and call-to-action

2. **Content Requirements**:
   - Maintain core information and value from original
   - Use conversational, social media-friendly language
   - Add appropriate emojis and relevant hashtags
   - Each tweet should provide standalone value
   - Natural English expression, not literal translation

3. **Output Format**:
   Return a JSON array with 6 tweets in this format:
   ```json
   [
     {{"tweet": "First tweet content..."}},
     {{"tweet": "Second tweet content..."}},
     {{"tweet": "Third tweet content..."}},
     {{"tweet": "Fourth tweet content..."}},
     {{"tweet": "Fifth tweet content..."}},
     {{"tweet": "Sixth tweet content..."}}
   ]
   ```

Original Content:
Title: {title}
Description: {description}
Tags: {tags}
Summary: {summary}
Conclusion: {conclusion}
Level: {level} (1=Confirmed, 2=Likely, 3=Rumor)

Please begin rewriting:"""

    def reload_thread_prompt(self, new_file_path: str = None) -> bool:
        """重新加载 Thread 提示词模板文件"""
        if new_file_path:
            self.thread_prompt_file = new_file_path
        
        try:
            self.thread_prompt = self.load_thread_prompt()
            print(f"✅ 成功重新加载 {self.thread_prompt_file}")
            return True
        except Exception as e:
            print(f"❌ 重新加载失败: {e}")
            return False

    def get_thread_prompt_info(self) -> Dict[str, any]:
        """获取当前 Thread 提示词的信息"""
        return {
            "file_path": self.thread_prompt_file,
            "content_length": len(self.thread_prompt),
            "line_count": len(self.thread_prompt.split('\n')),
            "has_title_placeholder": '{title}' in self.thread_prompt,
            "has_description_placeholder": '{description}' in self.thread_prompt,
            "has_tags_placeholder": '{tags}' in self.thread_prompt,
            "has_summary_placeholder": '{summary}' in self.thread_prompt,
            "has_conclusion_placeholder": '{conclusion}' in self.thread_prompt,
            "has_level_placeholder": '{level}' in self.thread_prompt
        }

    def rewrite_note_to_thread(self, title: str, description: str, tags: str = "", summary: str = "", conclusion: str = "", level: int = 3) -> Optional[List[Dict[str, str]]]:
        """
        将单个笔记改写为 Twitter Thread
        
        Args:
            title: 笔记标题
            description: 笔记描述
            tags: 笔记标签
            summary: 内容简介
            conclusion: 总结
            level: 内容级别 (1=Confirmed, 2=Likely, 3=Rumor)
            
        Returns:
            Thread 列表，每个元素包含一条推文
        """
        try:
            # 构建用户提示词
            user_prompt = self.thread_prompt.format(
                title=title,
                description=description,
                tags=tags,
                summary=summary,
                conclusion=conclusion,
                level=level
            )
            
            # 直接使用用户提示词，thread_prompt已包含所需的指导信息
            response = gpt_client.simple_chat(user_prompt)

            if not response:
                print(f"❌ GPT 改写失败: 没有返回内容")
                return None

            print(f"🔍 GPT 原始响应: {response[:500]}...")  # 调试信息
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start == -1 or json_end == 0:
                    print(f"❌ GPT 返回格式错误: 找不到 JSON 数组")
                    return None
                
                json_str = response[json_start:json_end]
                thread = json.loads(json_str)
                
                # 验证格式
                if not isinstance(thread, list) or len(thread) == 0:
                    print(f"❌ GPT 返回格式错误: 不是有效的数组")
                    return None
                
                # 确保每个元素都有 tweet 字段
                for i, tweet_obj in enumerate(thread):
                    if not isinstance(tweet_obj, dict) or 'tweet' not in tweet_obj:
                        print(f"❌ 第 {i+1} 条推文格式错误")
                        return None
                
                print(f"✅ 成功改写为 {len(thread)} 条推文的 Thread")
                return thread
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON 解析失败: {str(e)}")
                print(f"原始响应: {response[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ 改写过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def rewrite_note_to_english_thread(self, title: str, description: str, tags: str = "", summary: str = "", conclusion: str = "", level: int = 3) -> Optional[List[Dict[str, str]]]:
        """
        将单个笔记改写为英文 Twitter Thread
        
        Args:
            title: 笔记标题
            description: 笔记描述
            tags: 笔记标签
            summary: 内容简介
            conclusion: 总结
            level: 内容级别 (1=Confirmed, 2=Likely, 3=Rumor)
            
        Returns:
            英文Thread 列表，每个元素包含一条推文
        """
        try:
            # 构建英文提示词
            english_prompt = self._get_english_thread_prompt().format(
                title=title,
                description=description,
                tags=tags,
                summary=summary,
                conclusion=conclusion,
                level=level
            )
            
            # 使用英文风格指南
            english_style_guide = "You are a professional English content creator. Create engaging, natural English social media content suitable for international audiences."
            response = gpt_client.simple_chat(english_prompt, english_style_guide)

            if not response:
                print(f"❌ 英文GPT 改写失败: 没有返回内容")
                return None

            print(f"🔍 英文GPT 原始响应: {response[:500]}...")  # 调试信息
            
            # 尝试解析 JSON
            try:
                # 提取 JSON 部分
                json_start = response.find('[')
                json_end = response.rfind(']') + 1
                
                if json_start == -1 or json_end == 0:
                    print(f"❌ 英文GPT 返回格式错误: 找不到 JSON 数组")
                    return None
                
                json_str = response[json_start:json_end]
                thread = json.loads(json_str)
                
                # 验证格式
                if not isinstance(thread, list) or len(thread) == 0:
                    print(f"❌ 英文GPT 返回格式错误: 不是有效的数组")
                    return None
                
                # 确保每个元素都有 tweet 字段
                for i, tweet_obj in enumerate(thread):
                    if not isinstance(tweet_obj, dict) or 'tweet' not in tweet_obj:
                        print(f"❌ 英文第 {i+1} 条推文格式错误")
                        return None
                
                print(f"✅ 成功改写为 {len(thread)} 条英文推文的 Thread")
                return thread
                
            except json.JSONDecodeError as e:
                print(f"❌ 英文JSON 解析失败: {str(e)}")
                print(f"原始响应: {response[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ 英文改写过程中出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def preview_thread(self, thread: List[Dict[str, str]]):
        """预览 Thread 内容"""
        print("\n📱 Thread 预览:")
        print("=" * 50)
        
        for i, tweet_obj in enumerate(thread, 1):
            tweet = tweet_obj.get('tweet', '')
            print(f"{i}/{len(thread)}: {tweet}")
            print("-" * 30)

    def save_thread(self, thread: List[Dict[str, str]], filename: str = None, topic_title: str = ""):
        """保存 Thread 到文件"""
        if not filename:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 使用选题标题作为文件名的一部分
            if topic_title:
                # 清理文件名中的非法字符
                import re
                safe_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', topic_title)
                safe_title = safe_title.replace(' ', '_').strip()[:30]  # 限制长度
                filename = f"output/thread_{timestamp}_{safe_title}.json"
            else:
                filename = f"output/thread_{timestamp}.json"
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(thread, f, ensure_ascii=False, indent=2)
            print(f"💾 Thread 已保存到 {filename}")
            return filename
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
            return None
