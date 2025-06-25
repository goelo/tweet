#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容生成器
处理选题内容生成和 Tweet Thread 创作
"""

import os
import sys
import json
from datetime import datetime
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.api.tuzi_client import tuzi_client
from core.config.config import config


class ContentGenerator:
    """内容生成器"""
    
    def __init__(self):
        if not tuzi_client:
            raise ValueError("Tuzi API 客户端未正确初始化")
        
        self.client = tuzi_client
        self.config = config
        
        # 默认提示词模板 - 更新为thread_generator风格
        self.thread_prompt_template = """请以「{topic}」为主题，写一条7条结构的中文X（Twitter）thread。

结构要求：
1. 每条编号用 1/, 2/, 3/ 表示；
2. 每条内容采用“短句 + 空行”排版，分段表达，增加节奏感；
3. 内容格式整体贴近如下风格：

1/
搞副业做不起来？
可能你从一开始就理解错了“副业”这两个字。

副业不是副本任务，不是闲时填空，
它是一场结构试验、一场变现演练。

...

风格要求：
- 不喊口号，不灌鸡汤
- 用冷静现实的口吨，带轻度讽刺
- 每条不超过220字
- 最后输出为完整 thread 文本，一整段文本，直接用于 X 平台发帖"""

        self.title_prompt_template = """请你根据下列 thread 内容，提炼一组图像封面用标题：

内容如下：
{thread_content}

返回格式：
{{
  "主标题": "不超过12字，来自核心观点",
  "副标题": "不超过18字，补充说明主标题，形成张力"
}}"""

    def read_topics_from_file(self, file_path: str) -> List[str]:
        """
        从文件读取选题列表
        
        Args:
            file_path: 选题文件路径
            
        Returns:
            选题列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 按行分割并过滤空行
            topics = [line.strip() for line in content.split('\n') if line.strip()]
            
            print(f"✅ 成功读取 {len(topics)} 个选题")
            return topics
            
        except FileNotFoundError:
            print(f"❌ 选题文件不存在: {file_path}")
            return []
        except Exception as e:
            print(f"❌ 读取选题文件失败: {e}")
            return []

    def generate_thread(self, topic: str) -> Optional[str]:
        """
        为指定选题生成 Thread - 返回纯文本格式
        
        Args:
            topic: 选题内容
            
        Returns:
            生成的 Thread 文本
        """
        print(f"🔄 正在生成 Thread: {topic}")
        
        # 构建提示词
        prompt = self.thread_prompt_template.format(topic=topic)
        
        # 调用 API 生成内容 - 使用更高的温度
        response = self.client.chat_completion(
            [
                {"role": "system", "content": "你是一个擅长写爆款 thread 的中文内容创作者，风格克制、实用、带讽刺感。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85
        )
        
        if not response:
            print(f"❌ 生成失败: {topic}")
            return None
        
        # 返回纯文本格式，不解析JSON
        response = response.strip()
        print(f"✅ 成功生成 Thread，长度: {len(response)} 字符")
        return response

    def generate_titles(self, thread_content: str) -> Optional[Dict[str, str]]:
        """
        为 Thread 内容生成标题
        
        Args:
            thread_content: Thread 内容字符串
            
        Returns:
            包含主标题和副标题的字典
        """
        print("🎨 正在生成封面标题...")
        
        # 构建提示词
        prompt = self.title_prompt_template.format(thread_content=thread_content)
        
        # 调用 API 生成标题
        response = self.client.simple_chat(
            prompt,
            system_prompt="你是内容包装专家，负责生成社交媒体图像用标题。"
        )
        
        if not response:
            print("❌ 标题生成失败")
            return None
        
        try:
            # 解析 JSON 格式回复
            title_data = json.loads(response)
            if isinstance(title_data, dict) and "主标题" in title_data and "副标题" in title_data:
                print(f"✅ 成功生成标题: {title_data['主标题']} | {title_data['副标题']}")
                return title_data
            else:
                print("⚠️ 标题格式不正确")
                return None
        except json.JSONDecodeError:
            print("⚠️ 无法解析标题 JSON 格式")
            print(f"原始回复: {response[:200]}...")
            return None

    def save_result(self, topic: str, thread_text: str, titles: Optional[Dict[str, str]] = None, image_prompt: Optional[str] = None) -> str:
        """
        保存生成结果到文件 - 按thread_generator格式保存为txt
        
        Args:
            topic: 选题
            thread_text: Thread 文本内容
            titles: 标题信息
            image_prompt: 图片提示词
            
        Returns:
            保存的文件路径
        """
        # 创建时间戳文件夹
        timestamp = datetime.now().strftime("%m%d%H%M")
        timestamp_dir = os.path.join(self.config.output_dir, timestamp)
        
        # 确保时间戳目录存在
        os.makedirs(timestamp_dir, exist_ok=True)
        
        # 安全文件名处理
        safe_filename = topic[:30].replace('？', '').replace('?', '').replace(' ', '_')
        filename = f"{safe_filename}.txt"
        filepath = os.path.join(timestamp_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"🎯 选题：{topic}\n\n")
                f.write(f"🧵 Thread：\n{thread_text}\n\n")
                
                if titles:
                    f.write(f"📌 主标题：{titles['主标题']}\n")
                    f.write(f"📌 副标题：{titles['副标题']}\n\n")
                
                if image_prompt:
                    f.write(f"🎨 图像Prompt：\n{image_prompt}\n")
            
            print(f"✅ 已保存至：{filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return ""

    def build_image_prompt(self, title: str, subtitle: str) -> str:
        """
        构建图像生成提示词 - 按thread_generator格式
        
        Args:
            title: 主标题
            subtitle: 副标题
            
        Returns:
            图像提示词
        """
        return f"""Black background, large bold yellow Chinese text: '{title}'.
Below that in smaller white font: '{subtitle}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, suitable for attention-grabbing social media thumbnail."""
    
    def process_single_topic(self, topic: str) -> Dict:
        """
        处理单个选题的完整流程 - 按thread_generator逻辑
        
        Args:
            topic: 选题内容
            
        Returns:
            处理结果字典
        """
        result = {
            "topic": topic,
            "thread": None,
            "titles": None,
            "image_prompt": None,
            "success": False,
            "file_path": ""
        }
        
        print(f"\n=== 🎯 正在处理选题：{topic} ===")
        
        # 1. 生成 Thread
        thread_text = self.generate_thread(topic)
        if not thread_text:
            return result
        
        result["thread"] = thread_text
        print("\n🧵 Thread 内容：\n", thread_text)
        
        # 2. 生成标题
        titles = self.generate_titles(thread_text)
        if not titles or "主标题" not in titles or "副标题" not in titles:
            print("⚠️ 标题生成失败，跳过图像提示词生成")
            # 仍然保存thread
            file_path = self.save_result(topic, thread_text, None, None)
            result["file_path"] = file_path
            result["success"] = True
            return result
            
        result["titles"] = titles
        
        # 3. 生成图片提示词
        image_prompt = self.build_image_prompt(titles["主标题"], titles["副标题"])
        result["image_prompt"] = image_prompt
        
        # 4. 保存结果
        file_path = self.save_result(topic, thread_text, titles, image_prompt)
        result["file_path"] = file_path
        result["success"] = True
        
        return result

    def process_all_topics(self, input_file: str = None) -> List[Dict]:
        """
        处理所有选题
        
        Args:
            input_file: 输入文件路径，默认使用配置中的输入目录
            
        Returns:
            所有处理结果列表
        """
        if not input_file:
            input_file = os.path.join(self.config.input_dir, "topics.txt")
        
        # 读取选题
        topics = self.read_topics_from_file(input_file)
        if not topics:
            print("❌ 没有找到可处理的选题")
            return []
        
        print(f"🚀 开始处理 {len(topics)} 个选题")
        print("=" * 50)
        
        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n📝 处理第 {i}/{len(topics)} 个选题")
            result = self.process_single_topic(topic)
            results.append(result)
            
            if result["success"]:
                print(f"✅ 处理成功: {topic}")
            else:
                print(f"❌ 处理失败: {topic}")
        
        # 统计结果
        successful = [r for r in results if r["success"]]
        print(f"\n📊 处理完成!")
        print(f"   总选题数: {len(topics)}")
        print(f"   成功处理: {len(successful)}")
        print(f"   失败数量: {len(topics) - len(successful)}")
        
        return results


# 创建全局内容生成器实例
try:
    content_generator = ContentGenerator()
except Exception as e:
    print(f"❌ 内容生成器初始化失败: {e}")
    content_generator = None