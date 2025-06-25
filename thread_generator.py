#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter Thread 生成器 - 严格按照demo代码提示词
"""

import json
import os
import sys
import re
import time
import inspect
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from core.gpt.gpt_client import gpt_client
from core.utils.logger import setup_logging, cleanup_logging

# 输出目录
OUTPUT_DIR = Path('./output')
OUTPUT_DIR.mkdir(exist_ok=True)


class ThreadGenerator:
    """Twitter Thread 生成器"""
    
    def __init__(self):
        if not gpt_client:
            raise ValueError("GPT 客户端初始化失败")
        self.gpt = gpt_client
        self.total_tokens = 0
        self.request_count = 0
        
    def debug_log(self, message: str, level: str = "DEBUG"):
        """调试日志，包含文件位置信息"""
        frame = inspect.currentframe().f_back
        filename = os.path.basename(frame.f_filename)
        line_number = frame.f_lineno
        print(f"[{level}] {filename}:{line_number} - {message}")
        
    def log_token_usage(self, usage_info: str):
        """记录token使用情况"""
        self.request_count += 1
        self.debug_log(f"请求#{self.request_count} - {usage_info}")
        self.debug_log(f"总请求数: {self.request_count}, 累计tokens: {self.total_tokens}")

    def read_topics(self, file_path: str = "input/topics.txt") -> List[str]:
        """读取话题列表"""
        self.debug_log(f"开始读取话题文件: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                topics = [line.strip() for line in f if line.strip()]
            self.debug_log(f"成功读取 {len(topics)} 个话题")
            return topics
        except FileNotFoundError:
            self.debug_log(f"话题文件 {file_path} 不存在", "ERROR")
            return []
        except Exception as e:
            self.debug_log(f"读取话题文件失败: {e}", "ERROR")
            return []

    def build_thread_prompt(self, topic: str) -> str:
        """构建Thread生成提示词 - 严格按照demo"""
        return f"""
请以「{topic}」为主题，写一条7条结构的中文X（Twitter）thread。

结构要求：
1. 每条编号用 1/, 2/, 3/ 表示；
2. 每条内容采用"短句 + 空行"排版，分段表达，增加节奏感；
3. 内容格式整体贴近如下风格：

1/
搞副业做不起来？
可能你从一开始就理解错了"副业"这两个字。

副业不是副本任务，不是闲时填空，
它是一场结构试验、一场变现演练。

...

风格要求：
- 不喊口号，不灌鸡汤
- 用冷静现实的口吻，带轻度讽刺
- 每条不超过220字
- 最后输出为完整 thread 文本，一整段文本，直接用于 X 平台发帖
"""

    def build_title_prompt(self, thread_text: str) -> str:
        """构建标题提取提示词 - 严格按照demo"""
        return f"""
请你根据下列 thread 内容，提炼一组图像封面用标题：

内容如下：
{thread_text}

返回格式：
{{
  "主标题": "不超过12字，来自核心观点",
  "副标题": "不超过18字，补充说明主标题，形成张力"
}}
"""

    def build_image_prompt(self, title: str, subtitle: str) -> str:
        """构建图像生成提示词 - 严格按照demo"""
        return f"""Black background, large bold yellow Chinese text: '{title}'.
Below that in smaller white font: '{subtitle}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, suitable for attention-grabbing social media thumbnail."""

    def clean_json_response(self, response: str) -> str:
        """清理GPT回复中的markdown格式，提取纯JSON"""
        self.debug_log(f"开始清理JSON回复，原始长度: {len(response)}")
        
        # 移除markdown代码块标记
        response = re.sub(r'^```json\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*$', '', response, flags=re.MULTILINE)
        response = response.strip()
        
        self.debug_log(f"清理后长度: {len(response)}")
        self.debug_log(f"清理后前100字符: {response[:100]}")
        
        return response

    def generate_thread(self, topic: str) -> Optional[str]:
        """生成Thread内容"""
        self.debug_log(f"开始生成Thread，话题: {topic}")
        try:
            system_prompt = "你是一个擅长写爆款 thread 的中文内容创作者，风格克制、实用、带讽刺感。"
            user_prompt = self.build_thread_prompt(topic)
            
            start_time = time.time()
            result = self.gpt.chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.85)
            end_time = time.time()
            
            self.log_token_usage(f"Thread生成 - 耗时: {end_time-start_time:.2f}s")
            
            if result:
                result = result.strip()
                self.debug_log(f"成功生成话题「{topic}」的Thread，长度: {len(result)}字符")
                self.debug_log(f"Thread前200字符: {result[:200]}...")
            else:
                self.debug_log(f"生成话题「{topic}」的Thread失败", "ERROR")
                
            return result
            
        except Exception as e:
            self.debug_log(f"生成Thread时出错: {e}", "ERROR")
            return None

    def extract_title_from_thread(self, thread_text: str) -> Optional[Dict[str, str]]:
        """从Thread中提取标题"""
        self.debug_log("开始提取标题")
        try:
            system_prompt = "你是内容包装专家，负责生成社交媒体图像用标题。"
            user_prompt = self.build_title_prompt(thread_text)
            
            start_time = time.time()
            result = self.gpt.chat_completion([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], temperature=0.7)
            end_time = time.time()
            
            self.log_token_usage(f"标题提取 - 耗时: {end_time-start_time:.2f}s")
            
            if result:
                self.debug_log(f"获得标题回复，长度: {len(result)}字符")
                
                # 清理回复格式
                cleaned_result = self.clean_json_response(result)
                
                # 安全解析JSON
                try:
                    title_data = json.loads(cleaned_result)
                    self.debug_log("成功解析标题JSON")
                    return title_data
                except json.JSONDecodeError as e:
                    self.debug_log(f"JSON解析失败: {e}", "ERROR")
                    self.debug_log(f"尝试解析的内容: {cleaned_result[:200]}", "ERROR")
                    return None
            else:
                self.debug_log("标题提取失败", "ERROR")
                return None
                
        except Exception as e:
            self.debug_log(f"提取标题时出错: {e}", "ERROR")
            return None

    def save_thread(self, topic: str, thread_text: str, title_data: Dict[str, str], image_prompt: str):
        """保存Thread到文件 - 严格按照demo格式"""
        self.debug_log(f"开始保存Thread: {topic}")
        try:
            safe_filename = topic[:30].replace('？', '').replace('?', '').replace(' ', '_')
            file_path = OUTPUT_DIR / f"{safe_filename}.txt"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"🎯 选题：{topic}\n\n")
                f.write(f"🧵 Thread：\n{thread_text}\n\n")
                f.write(f"📌 主标题：{title_data['主标题']}\n")
                f.write(f"📌 副标题：{title_data['副标题']}\n\n")
                f.write(f"🎨 图像Prompt：\n{image_prompt}\n")
            
            self.debug_log(f"Thread已保存至: {file_path}")
            print(f"✅ 已保存至：{file_path}")
            
        except Exception as e:
            self.debug_log(f"保存Thread失败: {e}", "ERROR")

    def process_topic(self, topic: str) -> bool:
        """处理单个话题"""
        self.debug_log(f"开始处理话题: {topic}")
        print(f"\n=== 🎯 正在处理选题：{topic} ===")
        
        # 生成Thread
        thread_text = self.generate_thread(topic)
        if not thread_text:
            self.debug_log(f"话题「{topic}」Thread生成失败", "ERROR")
            return False
        
        print("\n🧵 Thread 内容：\n", thread_text)
        
        # 提取标题
        title_data = self.extract_title_from_thread(thread_text)
        if not title_data or "主标题" not in title_data or "副标题" not in title_data:
            self.debug_log(f"话题「{topic}」标题提取失败", "ERROR")
            return False
        
        # 生成图像提示词
        image_prompt = self.build_image_prompt(title_data["主标题"], title_data["副标题"])
        
        # 保存结果
        self.save_thread(topic, thread_text, title_data, image_prompt)
        
        self.debug_log(f"话题「{topic}」处理完成")
        return True

    def process_all_topics(self, topics_file: str = "input/topics.txt"):
        """处理所有话题"""
        topics = self.read_topics(topics_file)
        if not topics:
            self.debug_log("没有话题需要处理", "ERROR")
            return
            
        self.debug_log(f"准备处理 {len(topics)} 个话题")
        success_count = 0
        
        for topic in topics:
            if self.process_topic(topic):
                success_count += 1
        
        print(f"\n🎉 处理完成: {success_count}/{len(topics)} 个话题成功")
        self.debug_log(f"处理完成: {success_count}/{len(topics)} 个话题成功")
        self.debug_log(f"总计API调用: {self.request_count} 次")


def main():
    """主函数"""
    # 设置日志记录到run.log
    setup_logging("run.log")
    
    try:
        print("🚀 Twitter Thread 生成器启动")
        generator = ThreadGenerator()
        
        # 处理所有话题
        generator.process_all_topics()
        
        print(f"\n🎉 程序执行完成！")
                
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理日志记录
        cleanup_logging()


if __name__ == '__main__':
    main()