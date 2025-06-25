#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章格式草稿管理器
用于保存和管理完整文章格式的草稿（非Twitter Thread格式）
适用于微博、公众号等平台
"""

import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional


class ArticleDraftManager:
    """文章格式草稿管理器"""
    
    def __init__(self, drafts_dir: str = "output/articles"):
        """
        初始化草稿管理器
        
        Args:
            drafts_dir: 草稿存储目录
        """
        self.drafts_dir = drafts_dir
        os.makedirs(self.drafts_dir, exist_ok=True)
    
    def thread_to_article(self, thread: List[Dict[str, str]], title: str = "", topic_info: Dict = None) -> str:
        """
        将Thread转换为富文本格式文章
        
        Args:
            thread: Thread列表
            title: 文章标题
            topic_info: 话题信息（包含级别、关键词等）
            
        Returns:
            富文本格式的文章内容
        """
        if not thread:
            return ""
        
        # 提取所有推文内容
        tweets = []
        for item in thread:
            tweet_content = item.get('tweet', '').strip()
            if tweet_content:
                tweets.append(tweet_content)
        
        if not tweets:
            return ""
        
        # 开始构建富文本文章
        article_parts = []
        
        # 添加标题
        if title:
            article_parts.append(f"【{title}】")
            article_parts.append("")
        
        # 处理推文内容，智能合并成段落
        processed_content = self._smart_merge_tweets(tweets, topic_info)
        article_parts.append(processed_content)
        
        # 添加总结（不显示"总结"标签）
        if topic_info and topic_info.get('conclusion'):
            article_parts.append("")
            article_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            article_parts.append("")
            article_parts.append(f"{topic_info['conclusion']}")
        
        return "\n".join(article_parts)
    
    def _smart_merge_tweets(self, tweets: List[str], topic_info: Dict = None) -> str:
        """
        智能合并推文为连贯的文章内容，并自然融入级别和关键词信息
        
        Args:
            tweets: 推文列表
            topic_info: 话题信息（包含级别、关键词等）
            
        Returns:
            合并后的文章内容
        """
        if not tweets:
            return ""
        
        # 清理和处理每条推文
        processed_tweets = []
        
        for i, tweet in enumerate(tweets):
            # 移除话题标签 (#xxx)
            clean_tweet = re.sub(r'#\w+', '', tweet)
            
            # 移除过多的表情符号（保留少量）
            clean_tweet = re.sub(r'[🚗💨🧐😰⚠️🤔👇⬇️]{2,}', ' ', clean_tweet)
            
            # 移除数字编号（1. 2. 3.等）
            clean_tweet = re.sub(r'^\d+[.、]\s*', '', clean_tweet)
            
            # 移除"转发+评论"等社交媒体特有内容
            clean_tweet = re.sub(r'转发\+评论.*$', '', clean_tweet)
            clean_tweet = re.sub(r'转发.*评论.*$', '', clean_tweet)
            
            # 清理多余空格
            clean_tweet = ' '.join(clean_tweet.split())
            
            if clean_tweet.strip():
                processed_tweets.append(clean_tweet.strip())
        
        if not processed_tweets:
            return ""
        
        # 智能合并为段落
        paragraphs = []
        current_paragraph = []
        
        for i, tweet in enumerate(processed_tweets):
            # 第一条推文通常是引言/开头
            if i == 0:
                paragraphs.append(tweet)
                continue
            
            # 检查是否应该开始新段落
            should_start_new_paragraph = (
                # 包含问题关键词
                any(keyword in tweet for keyword in ['问题来了', '核心问题', '关键问题', '那么', '所以']) or
                # 包含总结关键词  
                any(keyword in tweet for keyword in ['总结', '结论', '最后', '综上']) or
                # 包含对比关键词
                any(keyword in tweet for keyword in ['然而', '但是', '相比之下', '另一方面']) or
                # 当前段落已经比较长了
                len('\n'.join(current_paragraph)) > 200
            )
            
            if should_start_new_paragraph and current_paragraph:
                # 完成当前段落
                paragraphs.append('\n'.join(current_paragraph))
                current_paragraph = [tweet]
            else:
                current_paragraph.append(tweet)
        
        # 添加最后一个段落
        if current_paragraph:
            paragraphs.append('\n'.join(current_paragraph))
        
        # 后处理：清理段落内容
        final_paragraphs = []
        for paragraph in paragraphs:
            # 移除段落开头的转折词
            paragraph = re.sub(r'^(问题来了|核心问题来了|关键问题|那么问题来了)[：:]?\s*', '', paragraph)
            
            # 处理A/B选择题格式
            if re.search(r'[AB][.、]\s*', paragraph):
                paragraph = re.sub(r'到底是[：:]?\s*A[.、]\s*', '可能是', paragraph)
                paragraph = re.sub(r'\s*B[.、]\s*', '，也可能是', paragraph)
                paragraph = re.sub(r'\s*？$', '。', paragraph)
            
            # 清理多余空格和标点
            paragraph = re.sub(r'\s+', ' ', paragraph)
            paragraph = re.sub(r'([。！？])\s*([^A-Za-z])', r'\1\2', paragraph)
            
            if paragraph.strip():
                final_paragraphs.append(paragraph.strip())
        
        # 自然融入级别和关键词信息
        result_text = '\n\n'.join(final_paragraphs)
        
        # 在文章末尾自然添加级别和关键词信息
        if topic_info:
            additional_info = []
            
            # 根据级别添加可信度说明
            if topic_info.get('level') == 1:
                additional_info.append("📋 该消息已得到官方确认或多家主流媒体报道。")
            elif topic_info.get('level') == 2:
                additional_info.append("📋 该消息来源可靠，但仍待官方最终确认。")
            elif topic_info.get('level') == 3:
                additional_info.append("📋 该消息仍为传闻，请关注后续官方消息。")
            
            # 添加关键词标签
            if topic_info.get('keywords'):
                keywords_list = [kw.strip() for kw in topic_info['keywords'].split('、')]
                hashtags = ' '.join([f"#{kw}" for kw in keywords_list])
                additional_info.append(f"🏷️ {hashtags}")
            
            if additional_info:
                result_text += '\n\n' + '\n'.join(additional_info)
        
        return result_text
    
    def save_article_draft(self, thread: List[Dict[str, str]], title: str = "", topic_info: Dict = None, images: List[str] = None) -> Optional[str]:
        """
        保存文章格式草稿（支持文件夹结构，包含图片）
        
        Args:
            thread: Thread列表
            title: 文章标题
            topic_info: 话题信息
            images: 图片文件路径列表
            
        Returns:
            保存的文件夹路径，失败返回None
        """
        try:
            # 转换为文章格式
            article_content = self.thread_to_article(thread, title, topic_info)
            
            if not article_content:
                print("❌ 无法生成文章内容")
                return None
            
            # 创建日期文件夹
            now = datetime.now()
            date_folder = now.strftime("%Y-%m-%d")
            date_path = os.path.join(self.drafts_dir, date_folder)
            os.makedirs(date_path, exist_ok=True)
            
            # 生成文章文件夹名
            timestamp = now.strftime("%H%M%S")
            safe_title = re.sub(r'[^\w\s\u4e00-\u9fff-]', '', title)[:30] if title else "untitled"
            safe_title = re.sub(r'\s+', '_', safe_title)
            folder_name = f"article_{safe_title}_{timestamp}"
            article_folder = os.path.join(date_path, folder_name)
            os.makedirs(article_folder, exist_ok=True)
            
            # 保存文章内容
            content_file = os.path.join(article_folder, "content.txt")
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(article_content)
            
            # 保存图片文件
            if images:
                images_folder = os.path.join(article_folder, "images")
                os.makedirs(images_folder, exist_ok=True)
                
                for i, image_path in enumerate(images):
                    if os.path.exists(image_path):
                        try:
                            # 获取文件扩展名
                            _, ext = os.path.splitext(image_path)
                            new_image_name = f"image_{i+1}{ext}"
                            new_image_path = os.path.join(images_folder, new_image_name)
                            
                            # 复制图片文件
                            import shutil
                            shutil.copy2(image_path, new_image_path)
                            print(f"📷 图片已保存: {new_image_path}")
                        except Exception as e:
                            print(f"⚠️ 复制图片失败: {image_path} - {e}")
            
            # 创建元数据文件
            metadata = {
                "title": title,
                "created_at": now.isoformat(),
                "topic_info": topic_info,
                "has_images": bool(images),
                "image_count": len(images) if images else 0,
                "content_file": "content.txt",
                "images_folder": "images" if images else None
            }
            
            metadata_file = os.path.join(article_folder, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"📝 文章草稿已保存到文件夹: {article_folder}")
            if images:
                print(f"📷 包含 {len(images)} 张图片")
            return article_folder
            
        except Exception as e:
            print(f"❌ 保存文章草稿失败: {str(e)}")
            return None
    
    def list_article_drafts(self) -> List[str]:
        """
        列出所有文章草稿
        
        Returns:
            草稿文件路径列表，按修改时间倒序
        """
        try:
            if not os.path.exists(self.drafts_dir):
                return []
            
            # 获取所有.txt文件（包括日期文件夹内的文件）
            draft_files = []
            
            # 遍历主目录中的直接文件（向后兼容）
            for filename in os.listdir(self.drafts_dir):
                file_path = os.path.join(self.drafts_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.txt') and filename.startswith('article_'):
                    draft_files.append(file_path)
            
            # 遍历日期文件夹
            for item in os.listdir(self.drafts_dir):
                item_path = os.path.join(self.drafts_dir, item)
                if os.path.isdir(item_path) and re.match(r'\d{4}-\d{2}-\d{2}', item):
                    # 这是一个日期文件夹
                    try:
                        for filename in os.listdir(item_path):
                            file_path = os.path.join(item_path, filename)
                            if os.path.isfile(file_path) and filename.endswith('.txt') and filename.startswith('article_'):
                                draft_files.append(file_path)
                    except OSError:
                        continue
            
            # 按修改时间排序（最新的在前）
            draft_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            return draft_files
            
        except Exception as e:
            print(f"❌ 列出草稿失败: {str(e)}")
            return []
    
    def preview_article_draft(self, file_path: str):
        """
        预览文章草稿
        
        Args:
            file_path: 草稿文件路径
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📖 文章草稿预览: {os.path.basename(file_path)}")
            print("=" * 60)
            print(content)
            print("=" * 60)
            print(f"📊 文章统计: {len(content)} 字符，{len(content.split())} 词")
            
        except Exception as e:
            print(f"❌ 预览草稿失败: {str(e)}")
    
    def delete_article_draft(self, file_path: str) -> bool:
        """
        删除文章草稿
        
        Args:
            file_path: 草稿文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if not os.path.exists(file_path):
                print(f"❌ 文件不存在: {file_path}")
                return False
            
            os.remove(file_path)
            print(f"✅ 已删除文章草稿: {os.path.basename(file_path)}")
            return True
            
        except Exception as e:
            print(f"❌ 删除草稿失败: {str(e)}")
            return False


# 全局实例
article_draft_manager = ArticleDraftManager()