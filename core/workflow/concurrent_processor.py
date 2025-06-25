#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
并发处理器
实现选题改写内容和图片生成的并发处理
"""

import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import json
import os
import time
from ..gpt.rewriter import GPTRewriter
from ..image.batch_prompt_generator import batch_prompt_generator
from ..image.smart_prompt_matcher import smart_prompt_matcher


class ConcurrentProcessor:
    """并发处理器"""
    
    def __init__(self, max_workers: int = 3):  # 降低并发数从5到3以减少API超时风险
        self.max_workers = max_workers
        self.batch_generator = batch_prompt_generator
        self.smart_matcher = smart_prompt_matcher
    
    def process_topics_concurrently(self, 
                                   topics: List[Dict[str, str]], 
                                   english_mode: bool = False,
                                   generate_images: bool = True,
                                   save_prompts: bool = False,
                                   template_type: str = "twitter") -> List[Dict[str, any]]:
        """
        并发处理所有选题（内容改写 + 图片生成）
        
        Args:
            topics: 选题列表
            english_mode: 是否生成英文内容
            generate_images: 是否生成图片
            save_prompts: 是否保存提示词到本地文件
            template_type: 模板类型 ("twitter", "article")
            
        Returns:
            处理结果列表
        """
        print(f"🚀 开始并发处理选题")
        print(f"📊 选题数量: {len(topics)}")
        print(f"⚡ 最大并发数: {self.max_workers}")
        print(f"🌐 语言模式: {'英文' if english_mode else '中文'}")
        print(f"🎨 图片生成: {'是' if generate_images else '否'}")
        print(f"💾 保存提示词: {'是' if save_prompts else '否'}")
        print("=" * 60)
        
        if not topics:
            print("❌ 没有选题需要处理")
            return []
        
        # 第一步：并发处理内容改写
        print("📝 第一步：并发处理内容改写...")
        content_results = self._process_content_concurrently(topics, english_mode, template_type)
        
        if not generate_images:
            print("⏭️ 跳过图片生成")
            return content_results
        
        # 第二步：并发生成图片提示词
        print("\n🔍 第二步：并发生成图片提示词...")
        prompt_results = self.batch_generator.generate_prompts_for_all_topics(topics, save_prompts=save_prompts)
        
        # 第三步：并发生成图片
        print("\n🎨 第三步：并发生成图片...")
        image_results = self.batch_generator.generate_images_for_prompts(prompt_results)
        
        # 第四步：合并结果
        print("\n🔗 第四步：合并处理结果...")
        merged_results = self._merge_results(content_results, image_results)
        
        # 保存完整结果
        self._save_final_results(merged_results, english_mode)
        
        # 统计并显示结果
        self._print_final_statistics(merged_results)
        
        return merged_results
    
    def _process_content_concurrently(self, topics: List[Dict[str, str]], english_mode: bool, template_type: str = "twitter") -> List[Dict[str, any]]:
        """并发处理内容改写"""
        try:
            rewriter = GPTRewriter(template_type=template_type)
        except Exception as e:
            print(f"❌ GPT改写器初始化失败: {e}")
            return []
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_topic = {
                executor.submit(self._process_single_content, rewriter, topic, english_mode): topic
                for topic in topics
            }
            
            # 收集结果
            for i, future in enumerate(concurrent.futures.as_completed(future_to_topic), 1):
                topic = future_to_topic[future]
                topic_title = topic.get('title', '未知选题')
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        thread_count = len(result['thread']) if result['thread'] else 0
                        print(f"   ✅ {i}/{len(topics)} 完成: {topic_title} ({thread_count}条推文)")
                    else:
                        print(f"   ❌ {i}/{len(topics)} 失败: {topic_title}")
                        
                except Exception as e:
                    print(f"   ❌ {i}/{len(topics)} 异常: {topic_title} - {e}")
                    results.append({
                        'topic': topic,
                        'thread': None,
                        'thread_file': None,
                        'success': False,
                        'error': str(e)
                    })
                
                # 添加延时避免过度并发和API超时
                time.sleep(1.0)  # 增加延时从0.5秒到1秒
        
        successful_count = sum(1 for r in results if r['success'])
        print(f"📊 内容改写完成: 成功 {successful_count}/{len(topics)}")
        
        return results
    
    def _process_single_content(self, rewriter: GPTRewriter, topic: Dict[str, str], english_mode: bool) -> Dict[str, any]:
        """处理单个选题的内容改写"""
        try:
            # 使用改写器处理内容
            if english_mode:
                thread = rewriter.rewrite_note_to_english_thread(
                    title=topic['title'],
                    description=topic['controversy'],
                    tags=topic['keywords'],
                    summary=topic.get('summary', ''),
                    conclusion=topic.get('conclusion', ''),
                    level=topic.get('level', 3)
                )
            else:
                thread = rewriter.rewrite_note_to_thread(
                    title=topic['title'],
                    description=topic['controversy'],
                    tags=topic['keywords'],
                    summary=topic.get('summary', ''),
                    conclusion=topic.get('conclusion', ''),
                    level=topic.get('level', 3)
                )
            
            if thread:
                # 保存thread文件
                thread_filename = rewriter.save_thread(thread, topic_title=topic['title'])
                
                return {
                    'topic': topic,
                    'thread': thread,
                    'thread_file': thread_filename,
                    'success': True
                }
            else:
                return {
                    'topic': topic,
                    'thread': None,
                    'thread_file': None,
                    'success': False,
                    'error': '内容改写失败'
                }
                
        except Exception as e:
            return {
                'topic': topic,
                'thread': None,
                'thread_file': None,
                'success': False,
                'error': str(e)
            }
    
    def _merge_results(self, content_results: List[Dict[str, any]], image_results: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """合并内容和图片处理结果"""
        merged_results = []
        
        # 创建图片结果的索引（基于topic_title）
        image_index = {}
        for img_result in image_results:
            topic_title = img_result['topic'].get('title', '')
            image_index[topic_title] = img_result
        
        # 合并结果
        for content_result in content_results:
            topic_title = content_result['topic'].get('title', '')
            
            # 查找对应的图片结果
            image_result = image_index.get(topic_title, {})
            
            merged_result = {
                'topic': content_result['topic'],
                'thread': content_result['thread'],
                'thread_file': content_result['thread_file'],
                'content_success': content_result['success'],
                'content_error': content_result.get('error', ''),
                'images': image_result.get('image_paths', []),
                'image_prompt': image_result.get('prompt', ''),
                'image_success': image_result.get('success', False),
                'image_error': image_result.get('error', ''),
                'overall_success': content_result['success'] and image_result.get('success', False)
            }
            
            merged_results.append(merged_result)
        
        return merged_results
    
    def _save_final_results(self, results: List[Dict[str, any]], english_mode: bool) -> str:
        """保存最终处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lang_suffix = "_english" if english_mode else "_chinese"
        filename = f"output/concurrent_results{lang_suffix}_{timestamp}.json"
        
        try:
            # 确保输出目录存在
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # 准备保存的数据
            save_data = {
                'timestamp': timestamp,
                'language_mode': 'english' if english_mode else 'chinese',
                'total_topics': len(results),
                'content_success_count': sum(1 for r in results if r['content_success']),
                'image_success_count': sum(1 for r in results if r['image_success']),
                'overall_success_count': sum(1 for r in results if r['overall_success']),
                'total_images_generated': sum(len(r['images']) for r in results),
                'results': []
            }
            
            for result in results:
                save_data['results'].append({
                    'topic_title': result['topic'].get('title', ''),
                    'topic_id': result['topic'].get('id', ''),
                    'thread_file': result['thread_file'],
                    'thread_count': len(result['thread']) if result['thread'] else 0,
                    'content_success': result['content_success'],
                    'content_error': result['content_error'],
                    'image_count': len(result['images']),
                    'image_paths': result['images'],
                    'image_prompt_length': len(result['image_prompt']) if result['image_prompt'] else 0,
                    'image_success': result['image_success'],
                    'image_error': result['image_error'],
                    'overall_success': result['overall_success']
                })
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 最终结果已保存到: {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ 保存最终结果失败: {e}")
            return ""
    
    def _print_final_statistics(self, results: List[Dict[str, any]]):
        """打印最终统计信息"""
        total_topics = len(results)
        content_success = sum(1 for r in results if r['content_success'])
        image_success = sum(1 for r in results if r['image_success'])
        overall_success = sum(1 for r in results if r['overall_success'])
        total_images = sum(len(r['images']) for r in results)
        
        print(f"\n🎉 并发处理完成!")
        print("=" * 60)
        print(f"📊 处理统计:")
        print(f"   总选题数: {total_topics}")
        print(f"   内容改写成功: {content_success}/{total_topics}")
        print(f"   图片生成成功: {image_success}/{total_topics}")
        print(f"   整体成功: {overall_success}/{total_topics}")
        print(f"   总图片数: {total_images}")
        print(f"   成功率: {(overall_success/total_topics*100):.1f}%")
        print("=" * 60)
    
    def process_with_custom_workflow(self, 
                                   topics: List[Dict[str, str]],
                                   content_processor: Optional[Callable] = None,
                                   image_processor: Optional[Callable] = None) -> List[Dict[str, any]]:
        """
        使用自定义工作流程处理选题
        
        Args:
            topics: 选题列表
            content_processor: 自定义内容处理器
            image_processor: 自定义图片处理器
            
        Returns:
            处理结果列表
        """
        print(f"🔧 使用自定义工作流程处理 {len(topics)} 个选题")
        
        results = []
        
        # 如果提供了自定义处理器，使用它们
        if content_processor or image_processor:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for topic in topics:
                    future = executor.submit(
                        self._process_with_custom_handlers,
                        topic,
                        content_processor,
                        image_processor
                    )
                    futures.append((future, topic))
                
                # 收集结果
                for i, (future, topic) in enumerate(futures, 1):
                    try:
                        result = future.result()
                        results.append(result)
                        topic_title = topic.get('title', '未知选题')
                        print(f"   ✅ {i}/{len(topics)} 完成: {topic_title}")
                    except Exception as e:
                        topic_title = topic.get('title', '未知选题')
                        print(f"   ❌ {i}/{len(topics)} 失败: {topic_title} - {e}")
                        results.append({
                            'topic': topic,
                            'success': False,
                            'error': str(e)
                        })
        
        return results
    
    def _process_with_custom_handlers(self, 
                                    topic: Dict[str, str],
                                    content_processor: Optional[Callable],
                                    image_processor: Optional[Callable]) -> Dict[str, any]:
        """使用自定义处理器处理单个选题"""
        result = {'topic': topic}
        
        try:
            # 处理内容
            if content_processor:
                content_result = content_processor(topic)
                result.update(content_result)
            
            # 处理图片
            if image_processor:
                image_result = image_processor(topic)
                result.update(image_result)
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result
    
    def get_processing_status(self) -> Dict[str, any]:
        """获取处理状态信息"""
        return {
            'max_workers': self.max_workers,
            'batch_generator_available': self.batch_generator is not None,
            'smart_matcher_available': self.smart_matcher is not None,
            'templates_loaded': len(self.smart_matcher.templates) if self.smart_matcher else 0
        }


# 创建全局并发处理器实例
concurrent_processor = ConcurrentProcessor()