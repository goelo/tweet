#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量图片提示词生成器
支持并发处理多个选题的图片提示词生成
"""

import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
from .smart_prompt_matcher import smart_prompt_matcher
from ..gpt.gpt_client import gpt_client


class BatchPromptGenerator:
    """批量图片提示词生成器"""
    
    def __init__(self, max_concurrent: int = 3):  # 降低并发数从5到3以减少超时风险
        self.max_concurrent = max_concurrent
        self.smart_matcher = smart_prompt_matcher
        
    def generate_prompts_for_all_topics(self, topics: List[Dict[str, str]], save_prompts: bool = False) -> List[Dict[str, any]]:
        """
        为所有选题生成图片提示词
        
        Args:
            topics: 选题列表
            save_prompts: 是否保存提示词到本地文件
            
        Returns:
            包含提示词生成结果的列表
        """
        print(f"🚀 开始批量生成图片提示词")
        print(f"📊 选题数量: {len(topics)}")
        print(f"⚡ 最大并发数: {self.max_concurrent}")
        print("=" * 60)
        
        if not topics:
            print("❌ 没有选题需要处理")
            return []
        
        # 检查依赖
        if not self._check_dependencies():
            return []
        
        # 第一阶段：为所有选题匹配提示词模板
        print("🔍 第一阶段：为所有选题匹配最适合的提示词模板...")
        template_results = self._match_templates_for_all_topics(topics)
        
        if not template_results:
            print("❌ 模板匹配阶段失败")
            return []
        
        print(f"✅ 模板匹配完成: {len(template_results)} 个选题成功匹配")
        print("-" * 60)
        
        # 第二阶段：并发生成定制化的图片提示词
        print("🎨 第二阶段：并发生成定制化图片提示词...")
        prompt_results = self._generate_prompts_concurrently(template_results)
        
        # 保存结果
        if save_prompts:
            self._save_batch_results(prompt_results)
            # 保存详细的提示词文件
            self._save_detailed_prompts(prompt_results)
        
        # 统计结果
        successful_count = sum(1 for result in prompt_results if result['success'])
        print(f"\n📊 批量生成完成:")
        print(f"   总选题数: {len(topics)}")
        print(f"   成功生成: {successful_count}")
        print(f"   失败数量: {len(topics) - successful_count}")
        print("=" * 60)
        
        return prompt_results
    
    def _check_dependencies(self) -> bool:
        """检查依赖项"""
        if not self.smart_matcher.templates:
            print("❌ 智能匹配器没有加载模板")
            return False
        
        if not gpt_client:
            print("❌ GPT客户端不可用")
            return False
        
        return True
    
    def _match_templates_for_all_topics(self, topics: List[Dict[str, str]]) -> List[Dict[str, any]]:
        """为所有选题匹配提示词模板"""
        results = []
        
        for i, topic in enumerate(topics, 1):
            print(f"🔍 匹配 {i}/{len(topics)}: {topic.get('title', '未知选题')}")
            
            # 找到最佳匹配的模板
            best_template = self.smart_matcher.find_best_match(topic)
            
            if best_template:
                results.append({
                    'topic': topic,
                    'template': best_template,
                    'success': True
                })
                print(f"   ✅ 匹配成功: 案例{best_template['case_number']}")
            else:
                results.append({
                    'topic': topic,
                    'template': None,
                    'success': False
                })
                print(f"   ❌ 匹配失败")
        
        return results
    
    def _generate_prompts_concurrently(self, template_results: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """并发生成图片提示词"""
        # 过滤出成功匹配模板的结果
        valid_results = [r for r in template_results if r['success']]
        
        if not valid_results:
            print("❌ 没有有效的模板匹配结果")
            return []
        
        print(f"⚡ 开始并发生成提示词 (并发数: {self.max_concurrent})")
        
        # 使用线程池进行并发处理
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有任务
            future_to_result = {
                executor.submit(self._generate_single_prompt, result): result
                for result in valid_results
            }
            
            # 收集结果
            for i, future in enumerate(concurrent.futures.as_completed(future_to_result), 1):
                result_data = future_to_result[future]
                topic_title = result_data['topic'].get('title', '未知选题')
                
                try:
                    prompt_result = future.result()
                    results.append(prompt_result)
                    
                    if prompt_result['success']:
                        print(f"   ✅ {i}/{len(valid_results)} 完成: {topic_title}")
                    else:
                        print(f"   ❌ {i}/{len(valid_results)} 失败: {topic_title}")
                        
                except Exception as e:
                    print(f"   ❌ {i}/{len(valid_results)} 异常: {topic_title} - {e}")
                    results.append({
                        'topic': result_data['topic'],
                        'template': result_data['template'],
                        'prompt': None,
                        'success': False,
                        'error': str(e)
                    })
        
        # 添加模板匹配失败的结果
        for result in template_results:
            if not result['success']:
                results.append({
                    'topic': result['topic'],
                    'template': None,
                    'prompt': None,
                    'success': False,
                    'error': '模板匹配失败'
                })
        
        return results
    
    def _generate_single_prompt(self, template_result: Dict[str, any]) -> Dict[str, any]:
        """为单个选题生成提示词"""
        topic = template_result['topic']
        template = template_result['template']
        
        try:
            # 使用智能匹配器定制提示词
            customized_prompt = self.smart_matcher.customize_prompt_for_topic(template, topic)
            
            if customized_prompt:
                return {
                    'topic': topic,
                    'template': template,
                    'prompt': customized_prompt,
                    'success': True
                }
            else:
                return {
                    'topic': topic,
                    'template': template,
                    'prompt': None,
                    'success': False,
                    'error': '提示词定制失败'
                }
                
        except Exception as e:
            return {
                'topic': topic,
                'template': template,
                'prompt': None,
                'success': False,
                'error': str(e)
            }
    
    def _save_batch_results(self, results: List[Dict[str, any]]) -> str:
        """保存批量处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/batch_prompts_{timestamp}.json"
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 准备保存的数据
            save_data = {
                'timestamp': timestamp,
                'total_topics': len(results),
                'successful_count': sum(1 for r in results if r['success']),
                'results': []
            }
            
            for result in results:
                save_data['results'].append({
                    'topic_title': result['topic'].get('title', ''),
                    'topic_id': result['topic'].get('id', ''),
                    'template_case_number': result['template']['case_number'] if result['template'] else None,
                    'template_title': result['template']['title'] if result['template'] else None,
                    'prompt': result['prompt'],
                    'success': result['success'],
                    'error': result.get('error', '')
                })
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 批量结果已保存到: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 保存批量结果失败: {e}")
            return ""
    
    def _save_detailed_prompts(self, results: List[Dict[str, any]]) -> str:
        """保存详细的提示词到单独文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/detailed_prompts_{timestamp}.md"
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            content = f"# 图片提示词详细报告\n\n"
            content += f"**生成时间:** {timestamp}\n"
            content += f"**总选题数:** {len(results)}\n"
            content += f"**成功生成:** {sum(1 for r in results if r['success'])}\n\n"
            content += "---\n\n"
            
            for i, result in enumerate(results, 1):
                topic = result['topic']
                template = result['template']
                
                content += f"## {i}. {topic.get('title', '未知选题')}\n\n"
                
                # 选题信息
                content += f"### 选题信息\n"
                content += f"- **标题:** {topic.get('title', '')}\n"
                content += f"- **核心争议:** {topic.get('controversy', '')}\n"
                content += f"- **关键词:** {topic.get('keywords', '')}\n"
                content += f"- **级别:** {topic.get('level', 3)}\n\n"
                
                if result['success'] and template:
                    # 匹配的模板信息
                    content += f"### 匹配的模板\n"
                    content += f"- **案例编号:** {template['case_number']}\n"
                    content += f"- **模板标题:** {template['title']}\n"
                    content += f"- **模板关键词:** {', '.join(template.get('keywords', []))}\n\n"
                    
                    # 原始模板提示词
                    content += f"### 原始模板提示词\n"
                    content += f"```\n{template['prompt']}\n```\n\n"
                    
                    # 定制化提示词
                    if result['prompt']:
                        content += f"### 定制化提示词\n"
                        content += f"```\n{result['prompt']}\n```\n\n"
                    else:
                        content += f"### ❌ 定制化提示词生成失败\n\n"
                else:
                    content += f"### ❌ 模板匹配失败\n"
                    if result.get('error'):
                        content += f"**错误信息:** {result['error']}\n\n"
                
                content += "---\n\n"
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📝 详细提示词报告已保存到: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 保存详细提示词报告失败: {e}")
            return ""
    
    def generate_images_for_prompts(self, prompt_results: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        为生成的提示词批量生成图片
        
        Args:
            prompt_results: 提示词生成结果列表
            
        Returns:
            包含图片生成结果的列表
        """
        print(f"🎨 开始批量生成图片")
        print(f"📊 提示词数量: {len(prompt_results)}")
        print(f"⚡ 最大并发数: {self.max_concurrent}")
        print("=" * 60)
        
        # 过滤出成功生成提示词的结果
        valid_prompts = [r for r in prompt_results if r['success'] and r['prompt']]
        
        if not valid_prompts:
            print("❌ 没有有效的提示词可用于生成图片")
            return []
        
        print(f"📝 有效提示词数量: {len(valid_prompts)}")
        
        # 导入图片创建器
        try:
            from .image_creator import image_creator
        except ImportError:
            print("❌ 无法导入图片创建器")
            return []
        
        if not image_creator.is_available():
            print("❌ 图片创建器不可用")
            return []
        
        # 使用线程池进行并发图片生成
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            # 提交所有任务
            future_to_prompt = {
                executor.submit(self._generate_single_image, prompt_result, image_creator): prompt_result
                for prompt_result in valid_prompts
            }
            
            # 收集结果
            for i, future in enumerate(concurrent.futures.as_completed(future_to_prompt), 1):
                prompt_result = future_to_prompt[future]
                topic_title = prompt_result['topic'].get('title', '未知选题')
                
                try:
                    image_result = future.result()
                    results.append(image_result)
                    
                    if image_result['success']:
                        image_count = len(image_result['image_paths'])
                        print(f"   ✅ {i}/{len(valid_prompts)} 完成: {topic_title} ({image_count}张图片)")
                    else:
                        print(f"   ❌ {i}/{len(valid_prompts)} 失败: {topic_title}")
                        
                except Exception as e:
                    print(f"   ❌ {i}/{len(valid_prompts)} 异常: {topic_title} - {e}")
                    results.append({
                        'topic': prompt_result['topic'],
                        'prompt': prompt_result['prompt'],
                        'image_paths': [],
                        'success': False,
                        'error': str(e)
                    })
        
        # 统计结果
        successful_count = sum(1 for result in results if result['success'])
        total_images = sum(len(result.get('image_paths', [])) for result in results)
        
        print(f"\n📊 批量图片生成完成:")
        print(f"   处理提示词: {len(valid_prompts)}")
        print(f"   成功生成: {successful_count}")
        print(f"   总图片数: {total_images}")
        print("=" * 60)
        
        return results
    
    def _generate_single_image(self, prompt_result: Dict[str, any], image_creator) -> Dict[str, any]:
        """为单个提示词生成图片"""
        topic = prompt_result['topic']
        prompt = prompt_result['prompt']
        topic_title = topic.get('title', '')
        
        try:
            image_paths = image_creator.create_image(prompt, topic_title)
            
            if image_paths:
                return {
                    'topic': topic,
                    'prompt': prompt,
                    'image_paths': image_paths,
                    'success': True
                }
            else:
                return {
                    'topic': topic,
                    'prompt': prompt,
                    'image_paths': [],
                    'success': False,
                    'error': '图片生成失败'
                }
                
        except Exception as e:
            return {
                'topic': topic,
                'prompt': prompt,
                'image_paths': [],
                'success': False,
                'error': str(e)
            }
    
    def get_statistics(self) -> Dict[str, any]:
        """获取统计信息"""
        return {
            'max_concurrent': self.max_concurrent,
            'templates_loaded': len(self.smart_matcher.templates),
            'gpt_available': gpt_client is not None
        }


# 创建全局批量提示词生成器实例
batch_prompt_generator = BatchPromptGenerator()