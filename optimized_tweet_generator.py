#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的Twitter Thread生成器
"""

import json
import os
import sys
import re
import time
import inspect
from typing import List, Dict, Optional

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from core.gpt.gpt_client import gpt_client
from core.utils.logger import setup_logging, cleanup_logging


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
        # 这里可以根据实际API返回的token信息进行统计
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
        """构建Thread生成提示词"""
        return f"""
请以「{topic}」为主题，写一条7条结构的中文X（Twitter）thread。

结构要求：
1. 第1条是钩子，带有反常识洞察；
2. 第2-4条拆解真实路径或案例；
3. 第5-6条指出常见误区；
4. 第7条是一句总结建议，鼓励收藏或评论。

风格要求：
- 不喊口号，不空谈方法论，语言具体有画面感；
- 适度讽刺、冷静现实；
- 每条 140~220 字，用短句断行；
- 用 JSON 格式输出，如：
[
  {{"tweet": "第1条内容"}},
  ...
]
"""

    def build_title_prompt(self, thread_text: str) -> str:
        """构建标题提取提示词"""
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
        """构建图像生成提示词"""
        return f"""Black background, large bold yellow Chinese text: '{title}'.
Below that in smaller white font: '{subtitle}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, suitable for attention-grabbing social media thumbnail."""

    def generate_thread(self, topic: str) -> Optional[str]:
        """生成Thread内容"""
        self.debug_log(f"开始生成Thread，话题: {topic}")
        try:
            system_prompt = "你是一个擅长写搞钱 thread 的中文社交媒体内容创作者。"
            user_prompt = self.build_thread_prompt(topic)
            
            start_time = time.time()
            result = self.gpt.simple_chat(user_prompt, system_prompt)
            end_time = time.time()
            
            self.log_token_usage(f"Thread生成 - 耗时: {end_time-start_time:.2f}s")
            
            if result:
                self.debug_log(f"成功生成话题「{topic}」的Thread，长度: {len(result)}字符")
                self.debug_log(f"原始回复前100字符: {result[:100]}...")
            else:
                self.debug_log(f"生成话题「{topic}」的Thread失败", "ERROR")
                
            return result
            
        except Exception as e:
            self.debug_log(f"生成Thread时出错: {e}", "ERROR")
            return None

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
    
    def extract_title_from_thread(self, thread_text: str) -> Optional[Dict[str, str]]:
        """从Thread中提取标题"""
        self.debug_log("开始提取标题")
        try:
            system_prompt = "你是内容包装专家，负责生成社交媒体图像用标题。"
            user_prompt = self.build_title_prompt(thread_text)
            
            start_time = time.time()
            result = self.gpt.simple_chat(user_prompt, system_prompt)
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
                    
                    # 如果JSON解析失败，尝试使用eval（不推荐，但作为fallback）
                    try:
                        title_data = eval(cleaned_result)
                        self.debug_log("使用eval解析标题数据", "WARNING")
                        return title_data
                    except Exception as eval_e:
                        self.debug_log(f"eval解析也失败: {eval_e}", "ERROR")
                        return None
            else:
                self.debug_log("标题提取失败", "ERROR")
                return None
                
        except Exception as e:
            self.debug_log(f"提取标题时出错: {e}", "ERROR")
            return None

    def process_single_topic(self, topic: str) -> Dict:
        """处理单个话题"""
        result = {
            "topic": topic,
            "thread": None,
            "title_data": None,
            "image_prompt": None,
            "success": False
        }
        
        self.debug_log(f"开始处理话题: {topic}")
        
        # 生成Thread
        thread = self.generate_thread(topic)
        if not thread:
            self.debug_log(f"话题「{topic}」Thread生成失败", "ERROR")
            return result
            
        # 清理Thread回复格式
        cleaned_thread = self.clean_json_response(thread)
        result["thread"] = cleaned_thread
        
        # 验证Thread格式
        try:
            thread_json = json.loads(cleaned_thread)
            self.debug_log(f"Thread JSON解析成功，包含 {len(thread_json)} 条推文")
        except json.JSONDecodeError:
            self.debug_log(f"Thread JSON格式有误，但继续处理", "WARNING")
        
        # 提取标题
        title_data = self.extract_title_from_thread(thread)
        if not title_data:
            self.debug_log(f"话题「{topic}」标题提取失败", "ERROR")
            return result
            
        result["title_data"] = title_data
        
        # 生成图像提示词
        if "主标题" in title_data and "副标题" in title_data:
            image_prompt = self.build_image_prompt(
                title_data["主标题"], 
                title_data["副标题"]
            )
            result["image_prompt"] = image_prompt
            result["success"] = True
            self.debug_log(f"话题「{topic}」处理完成")
        else:
            self.debug_log(f"话题「{topic}」标题数据格式错误: {title_data}", "ERROR")
            
        return result

    def process_all_topics(self, topics_file: str = "input/topics.txt") -> List[Dict]:
        """处理所有话题"""
        topics = self.read_topics(topics_file)
        if not topics:
            self.debug_log("没有话题需要处理", "ERROR")
            return []
            
        self.debug_log(f"准备处理 {len(topics)} 个话题")
        results = []
        
        for i, topic in enumerate(topics, 1):
            self.debug_log(f"📝 处理第 {i}/{len(topics)} 个选题")
            print(f"🔄 正在生成 Thread: \"{topic}\"")
            
            result = self.process_single_topic(topic)
            results.append(result)
            
            if result["success"]:
                print(f"✅ 处理成功: \"{topic}\"")
            else:
                print(f"❌ 处理失败: \"{topic}\"")
            
        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        self.debug_log(f"处理完成: {success_count}/{len(results)} 个话题成功")
        self.debug_log(f"总计API调用: {self.request_count} 次")
        
        return results

    def save_results(self, results: List[Dict], output_file: str = "output/thread_results.json"):
        """保存结果到文件"""
        self.debug_log(f"开始保存结果到: {output_file}")
        try:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            self.debug_log(f"结果已保存到: {output_file}")
            print(f"💾 结果已保存到: {output_file}")
        except Exception as e:
            self.debug_log(f"保存结果失败: {e}", "ERROR")


def main():
    """主函数"""
    # 设置日志记录到run.log
    setup_logging("run.log")
    
    try:
        print("🚀 Twitter Thread 生成器启动")
        generator = ThreadGenerator()
        
        # 处理所有话题
        results = generator.process_all_topics()
        
        # 保存结果
        generator.save_results(results)
        
        # 打印结果摘要
        success_results = [r for r in results if r["success"]]
        print(f"\n📊 处理结果: {len(success_results)}/{len(results)} 成功")
        
        for result in success_results:
            print(f"\n=== 🎯 Topic: {result['topic']} ===")
            
            # 尝试解析并美化显示Thread
            try:
                thread_data = json.loads(result['thread'])
                print(f"\n🧵 Thread ({len(thread_data)} 条):")
                for i, tweet in enumerate(thread_data, 1):
                    print(f"  {i}. {tweet.get('tweet', '')}")
            except:
                print(f"\n🧵 Thread (原始):\n{result['thread'][:200]}...")
            
            title_data = result['title_data']
            print(f"\n📌 标题: {title_data['主标题']} ｜ {title_data['副标题']}")
            
            print(f"\n🎨 配图 Prompt:\n{result['image_prompt']}")
        
        # 显示失败的话题
        failed_results = [r for r in results if not r["success"]]
        if failed_results:
            print(f"\n❌ 失败的话题 ({len(failed_results)}个):")
            for result in failed_results:
                print(f"  - {result['topic']}")
        
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