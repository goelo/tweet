#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片生成模块
整合4oimage功能，为每个话题生成相应的配图
"""

import os
import json
import base64
import requests
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class ImageGenerator:
    """图片生成器"""
    
    def __init__(self):
        self.model = os.getenv("IMAGE_MODEL", "gpt-4o-image-vip")
        self.api_url = os.getenv("IMAGE_API_URL", "https://api.tu-zi.com/v1/chat/completions")
        self.api_token = os.getenv("IMAGE_API_TOKEN")
        
        # 加载图片提示词配置
        self.image_prompts = self._load_image_prompts()
        
        if not self.api_token:
            print("⚠️ 警告：未设置IMAGE_API_TOKEN环境变量，图片生成功能将不可用")
    
    def _load_image_prompts(self) -> Dict[str, str]:
        """加载图片提示词配置"""
        prompts_file = "input/image.md"
        
        if not os.path.exists(prompts_file):
            print(f"⚠️ 图片提示词配置文件不存在: {prompts_file}")
            return {}
        
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析不同类型的提示词
            prompts = {}
            
            # 匹配各种话题的提示词
            patterns = {
                'ai_tech': r'#### AI/科技话题\s*.*?\n(.*?)(?=####|\n\n|$)',
                'code_dev': r'#### 代码/开发话题\s*.*?\n(.*?)(?=####|\n\n|$)',
                'business': r'#### 商业/财经话题\s*.*?\n(.*?)(?=####|\n\n|$)',
                'product': r'#### 产品发布话题\s*.*?\n(.*?)(?=####|\n\n|$)',
                'default': r'#### 默认通用模板\s*.*?\n(.*?)(?=####|\n\n|$)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    prompt = match.group(1).strip()
                    # 清理提示词，移除多余的格式符号
                    prompt = re.sub(r'为.*?创建配图：\s*', '', prompt)
                    prompts[key] = prompt
            
            print(f"✅ 成功加载 {len(prompts)} 个图片提示词模板")
            return prompts
            
        except Exception as e:
            print(f"❌ 加载图片提示词配置失败: {e}")
            return {}
    
    def _classify_topic(self, topic: Dict[str, str]) -> str:
        """根据话题内容分类，选择合适的图片模板"""
        title = topic.get('title', '').lower()
        keywords = topic.get('keywords', '').lower()
        summary = topic.get('summary', '').lower()
        
        # 组合所有文本内容
        content = f"{title} {keywords} {summary}"
        
        # AI/科技相关关键词
        if any(keyword in content for keyword in ['ai', 'gpt', 'claude', '人工智能', '机器学习', '深度学习', '神经网络', '算法']):
            return 'ai_tech'
        
        # 代码/开发相关关键词
        elif any(keyword in content for keyword in ['代码', '编程', 'python', 'javascript', 'github', 'api', '开发', '程序员', 'sql']):
            return 'code_dev'
        
        # 商业/财经相关关键词
        elif any(keyword in content for keyword in ['商业', '财经', '投资', '股票', '金融', '市场', '经济', '营收', '盈利']):
            return 'business'
        
        # 产品发布相关关键词
        elif any(keyword in content for keyword in ['发布', '上线', '推出', '更新', '版本', '产品', 'beta', '测试']):
            return 'product'
        
        # 默认使用通用模板
        else:
            return 'default'
    
    def _generate_topic_content(self, topic: Dict[str, str], topic_type: str) -> Dict[str, str]:
        """根据话题内容生成具体的封面文案"""
        title = topic.get('title', '')
        summary = topic.get('summary', '')
        keywords = topic.get('keywords', '')
        
        # 生成主标题（简化并突出重点）
        main_title = title
        if len(title) > 15:
            # 提取关键词作为简化标题
            key_words = [w.strip() for w in keywords.split('、')][:2] if keywords else []
            if key_words:
                main_title = f"{key_words[0]}大升级！"
            else:
                main_title = title[:12] + "..."
        
        # 根据话题类型生成二级要点
        if topic_type == 'ai_tech':
            points = [
                "AI能力暴增 🤖",
                "性能大幅提升 ⚡", 
                "应用场景更广 🎯"
            ]
            action_text = "赶紧了解一下！"
        elif topic_type == 'code_dev':
            points = [
                "开发效率翻倍 💻",
                "新功能超强 🚀",
                "代码质量提升 ⚡"
            ]
            action_text = "程序员必看！"
        elif topic_type == 'business':
            points = [
                "市场影响巨大 📈",
                "投资价值凸显 💰",
                "商机不容错过 🎯"
            ]
            action_text = "抓住机会！"
        elif topic_type == 'product':
            points = [
                "全新功能上线 ✨",
                "用户体验升级 🔥",
                "颜值性能双提升 💫"
            ]
            action_text = "快来体验！"
        else:
            points = [
                "重磅消息来袭 ✨",
                "影响力巨大 💪",
                "值得深度关注 🎨"
            ]
            action_text = "值得关注！"
        
        # 根据具体内容调整要点
        if summary:
            # 从摘要中提取关键信息
            if '效率' in summary or '提升' in summary:
                points[1] = f"效率大幅提升 ⚡"
            if '功能' in summary or '特性' in summary:
                points[0] = f"新功能震撼 🚀"
            if '性能' in summary or '速度' in summary:
                points[2] = f"性能表现惊艳 💫"
        
        return {
            'main_title': main_title,
            'points': points,
            'action_text': action_text
        }

    def generate_image_for_topic(self, topic: Dict[str, str]) -> Optional[List[str]]:
        """为话题生成图片"""
        if not self.api_token:
            print("❌ 图片生成功能不可用：缺少API Token")
            return None
        
        if not self.image_prompts:
            print("❌ 图片生成功能不可用：缺少图片提示词配置")
            return None
        
        # 分类话题并获取对应的提示词
        topic_type = self._classify_topic(topic)
        base_prompt = self.image_prompts.get(topic_type, self.image_prompts.get('default', ''))
        
        if not base_prompt:
            print("❌ 未找到合适的图片提示词模板")
            return None
        
        # 生成具体的文案内容
        content = self._generate_topic_content(topic, topic_type)
        
        # 构建完整的提示词
        enhanced_prompt = f"""{base_prompt}

实际文案内容：
1. **主标题（字号最大，醒目色）**
   {content['main_title']}

2. **二级要点（字号次大，用同色系高饱和度）**
   - {content['points'][0]}
   - {content['points'][1]}
   - {content['points'][2]}

3. **行动号召（常规字号，留白明显）**
   {content['action_text']}

请严格按照上述文案内容制作封面，确保文字清晰可读，排版美观。"""
        
        print(f"🎨 为话题生成图片: {topic.get('title', '')}")
        print(f"📝 使用模板类型: {topic_type}")
        print(f"📄 主标题: {content['main_title']}")
        
        try:
            # 准备API请求
            message_content = [{"type": "text", "text": enhanced_prompt}]
            
            data = {
                "model": self.model,
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": message_content
                    }
                ],
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
            
            # 发送请求
            response = requests.post(self.api_url, json=data, headers=headers, timeout=300)
            
            if response.status_code != 200:
                print(f"❌ API请求失败: {response.status_code} - {response.text}")
                return None
            
            result = response.json()
            
            if "error" in result:
                print(f"❌ API错误: {result['error']['message']}")
                return None
            
            # 提取和下载图片
            image_paths = self._download_images_from_response(result, topic.get('title', ''))

            if image_paths:
                print(f"✅ 成功生成 1 张图片")  # 现在每个选题只生成一张图片
                return image_paths
            else:
                print("❌ 未能从响应中提取到图片")
                return None
                
        except Exception as e:
            print(f"❌ 图片生成失败: {e}")
            return None
    
    def _download_images_from_response(self, result: Dict, topic_title: str) -> List[str]:
        """从API响应中下载图片（限制为每个选题只下载一张图片）"""
        image_paths = []

        if "choices" not in result or not isinstance(result["choices"], list):
            return image_paths

        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', topic_title)[:50]
        output_dir = os.path.join("temp_images", f"{timestamp}_{safe_title}")
        os.makedirs(output_dir, exist_ok=True)

        # 只处理第一个choice，确保每个选题只生成一张图片
        first_choice = result["choices"][0]
        if "message" not in first_choice or "content" not in first_choice["message"]:
            return image_paths

        content = first_choice["message"]["content"]

        # 提取图片下载链接
        download_links = re.findall(r'\[(?:点击下载|Click to download)\]\((https?://[^\s\)]+)\)', content)

        # 只下载第一个图片链接，确保每个选题只有一张图片
        if download_links:
            image_url = download_links[0]  # 只取第一个链接
            try:
                print(f"📥 正在下载图片: {image_url}")
                image_response = requests.get(image_url, timeout=60)
                image_response.raise_for_status()

                # 确定文件扩展名
                ext = "png"
                url_match = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", image_url)
                if url_match:
                    ext = url_match.group(1).split("?")[0]
                    if len(ext) > 5:
                        ext = "png"

                # 生成文件名（简化命名）
                file_name = f"{result.get('id', 'image')}.{ext}"
                file_path = os.path.join(output_dir, file_name)

                # 保存图片
                with open(file_path, "wb") as f:
                    f.write(image_response.content)

                image_paths.append(file_path)
                print(f"✅ 图片已保存: {file_path}")

            except Exception as e:
                print(f"❌ 下载图片失败: {image_url} - {e}")
        else:
            print("⚠️ 未在响应中找到图片下载链接")

        return image_paths
    
    def is_available(self) -> bool:
        """检查图片生成功能是否可用"""
        return bool(self.api_token and self.image_prompts)
    
    def cleanup_temp_images(self, days_old: int = 7) -> int:
        """
        清理临时图片文件夹中的旧文件
        
        Args:
            days_old: 清理多少天前的文件
            
        Returns:
            清理的文件数量
        """
        temp_dir = "temp_images"
        if not os.path.exists(temp_dir):
            return 0
        
        import time
        from datetime import timedelta
        
        now = time.time()
        cutoff = now - (days_old * 24 * 60 * 60)  # days_old天前的时间戳
        
        deleted_count = 0
        deleted_dirs = 0
        
        try:
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                
                if os.path.isdir(item_path):
                    # 检查文件夹修改时间
                    if os.path.getmtime(item_path) < cutoff:
                        try:
                            import shutil
                            shutil.rmtree(item_path)
                            deleted_dirs += 1
                            print(f"🗑️ 已删除旧图片文件夹: {item}")
                            
                            # 统计删除的文件数量
                            for root, dirs, files in os.walk(item_path):
                                deleted_count += len(files)
                        except Exception as e:
                            print(f"⚠️ 删除文件夹失败: {item_path} - {e}")
                
                elif os.path.isfile(item_path):
                    # 检查文件修改时间
                    if os.path.getmtime(item_path) < cutoff:
                        try:
                            os.remove(item_path)
                            deleted_count += 1
                            print(f"🗑️ 已删除旧图片文件: {item}")
                        except Exception as e:
                            print(f"⚠️ 删除文件失败: {item_path} - {e}")
            
            if deleted_count > 0 or deleted_dirs > 0:
                print(f"✅ 清理完成: 删除了 {deleted_count} 个文件，{deleted_dirs} 个文件夹")
            
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理临时图片失败: {e}")
            return 0


# 创建全局图片生成器实例
image_generator = ImageGenerator()