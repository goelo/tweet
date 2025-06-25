#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片提示词生成模块
使用改写模型生成优化的图片提示词
"""

import os
import json
import re
from typing import Dict, Optional
from dotenv import load_dotenv
from ..gpt.gpt_client import gpt_client

# 加载环境变量
load_dotenv()


class ImagePromptGenerator:
    """图片提示词生成器"""
    
    def __init__(self):
        self.rewrite_model = os.getenv("OPENAI_MODEL", "gpt-4.1-2025-04-14")
        
        # 图片提示词生成的系统提示
        self.system_prompt = """你是一个专业的图片提示词生成专家。你的任务是根据用户提供的选题信息，生成一个完整的、可直接用于图片生成的提示词。

你需要：
1. 分析选题的主题类型和关键信息
2. 选择合适的视觉风格和布局
3. 生成具体的文案内容（标题、要点、行动号召）
4. 输出完整的图片生成提示词

请严格按照以下JSON格式输出：
```json
{
  "image_prompt": "完整的图片生成提示词内容..."
}
```"""
        
        # 基础图片模板
        self.base_template = """画图：画一个小红书封面。
要求：
- 有足够的吸引力吸引用户点击
- 字体醒目，选择有个性的字体
- 文字大小按重要度分级，体现文案的逻辑结构
- 标题是普通文字的至少2倍
- 文字段落之间留白
- 只对要强调的文字用醒目色吸引用户注意
- 背景使用时尚图案（例如：纸张纹理、记事本页面、简约几何图形等）
- 使用通用图标或装饰性小插画增加视觉层次
- 画面比例 9:16

实际文案内容："""

    def generate_image_prompt(self, topic: Dict[str, str]) -> Optional[str]:
        """
        生成图片提示词
        
        Args:
            topic: 话题信息字典，包含 title, keywords, summary 等
            
        Returns:
            生成的图片提示词字符串
        """
        try:
            # 构建用户提示
            user_prompt = self._build_user_prompt(topic)
            
            print(f"🔄 正在为话题生成图片提示词: {topic.get('title', '未知话题')}")
            
            # 调用改写模型生成提示词
            response = gpt_client.simple_chat(user_prompt, self.system_prompt)
            
            if not response:
                print(f"❌ 提示词生成失败: 模型无响应")
                return None
            
            print(f"🔍 模型响应: {response[:200]}...")
            
            # 解析JSON响应
            prompt = self._parse_response(response)
            
            if prompt:
                print(f"✅ 成功生成图片提示词")
                return prompt
            else:
                print(f"❌ 提示词解析失败")
                return None
                
        except Exception as e:
            print(f"❌ 生成图片提示词时出错: {e}")
            return None
    
    def _build_user_prompt(self, topic: Dict[str, str]) -> str:
        """构建用户提示"""
        title = topic.get('title', '')
        keywords = topic.get('keywords', '')
        summary = topic.get('summary', '')
        
        # 分析话题类型
        topic_type = self._classify_topic(topic)
        
        # 生成具体内容
        content = self._generate_content_for_type(topic, topic_type)
        
        user_prompt = f"""请为以下选题生成一个完整的图片提示词：

选题信息：
- 标题：{title}
- 关键词：{keywords}
- 摘要：{summary}
- 话题类型：{topic_type}

请基于以下模板生成完整的图片提示词：

{self.base_template}

1. **主标题（字号最大，醒目色）**
   {content['main_title']}

2. **二级要点（字号次大，用同色系高饱和度）**
   - {content['points'][0]}
   - {content['points'][1]}
   - {content['points'][2]}

3. **行动号召（常规字号，留白明显）**
   {content['action_text']}

请将上述模板和具体文案合并，生成一个完整的、可直接用于图片生成的提示词。确保文案清晰可读，排版美观。"""

        return user_prompt
    
    def _classify_topic(self, topic: Dict[str, str]) -> str:
        """分类话题类型"""
        title = topic.get('title', '').lower()
        keywords = topic.get('keywords', '').lower()
        summary = topic.get('summary', '').lower()
        
        content = f"{title} {keywords} {summary}"
        
        if any(keyword in content for keyword in ['ai', 'gpt', 'claude', '人工智能', '机器学习', '深度学习']):
            return 'AI科技'
        elif any(keyword in content for keyword in ['代码', '编程', 'python', 'javascript', 'github', '开发']):
            return '代码开发'
        elif any(keyword in content for keyword in ['商业', '财经', '投资', '股票', '金融', '市场']):
            return '商业财经'
        elif any(keyword in content for keyword in ['发布', '上线', '推出', '更新', '版本', '产品']):
            return '产品发布'
        else:
            return '通用话题'
    
    def _generate_content_for_type(self, topic: Dict[str, str], topic_type: str) -> Dict[str, any]:
        """根据话题类型生成内容"""
        title = topic.get('title', '')
        summary = topic.get('summary', '')
        keywords = topic.get('keywords', '')
        
        # 生成主标题
        main_title = title
        if len(title) > 15:
            key_words = [w.strip() for w in keywords.split('、')][:2] if keywords else []
            if key_words:
                main_title = f"{key_words[0]}大升级！"
            else:
                main_title = title[:12] + "..."
        
        # 根据类型生成要点
        if topic_type == 'AI科技':
            points = ["AI能力暴增 🤖", "性能大幅提升 ⚡", "应用场景更广 🎯"]
            action_text = "赶紧了解一下！"
        elif topic_type == '代码开发':
            points = ["开发效率翻倍 💻", "新功能超强 🚀", "代码质量提升 ⚡"]
            action_text = "程序员必看！"
        elif topic_type == '商业财经':
            points = ["市场影响巨大 📈", "投资价值凸显 💰", "商机不容错过 🎯"]
            action_text = "抓住机会！"
        elif topic_type == '产品发布':
            points = ["全新功能上线 ✨", "用户体验升级 🔥", "颜值性能双提升 💫"]
            action_text = "快来体验！"
        else:
            points = ["重磅消息来袭 ✨", "影响力巨大 💪", "值得深度关注 🎨"]
            action_text = "值得关注！"
        
        # 根据摘要调整要点
        if summary:
            if '效率' in summary or '提升' in summary:
                points[1] = "效率大幅提升 ⚡"
            if '功能' in summary or '特性' in summary:
                points[0] = "新功能震撼 🚀"
            if '性能' in summary or '速度' in summary:
                points[2] = "性能表现惊艳 💫"
        
        return {
            'main_title': main_title,
            'points': points,
            'action_text': action_text
        }
    
    def _parse_response(self, response: str) -> Optional[str]:
        """解析模型响应，提取图片提示词"""
        try:
            # 查找JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                print(f"❌ 响应中找不到JSON格式")
                return None
            
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            
            if 'image_prompt' in result:
                return result['image_prompt']
            else:
                print(f"❌ JSON中缺少image_prompt字段")
                return None
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            # 如果JSON解析失败，尝试直接提取内容
            return self._extract_fallback_prompt(response)
        except Exception as e:
            print(f"❌ 解析响应时出错: {e}")
            return None
    
    def _extract_fallback_prompt(self, response: str) -> Optional[str]:
        """备用提取方法，当JSON解析失败时使用"""
        try:
            # 尝试查找类似提示词的内容
            lines = response.split('\n')
            prompt_lines = []
            in_prompt = False
            
            for line in lines:
                line = line.strip()
                if '画图：' in line or '要求：' in line:
                    in_prompt = True
                    prompt_lines.append(line)
                elif in_prompt and line:
                    prompt_lines.append(line)
                elif in_prompt and not line:
                    # 空行可能表示提示词结束
                    continue
            
            if prompt_lines:
                return '\n'.join(prompt_lines)
            else:
                print("❌ 无法从响应中提取有效提示词")
                return None
                
        except Exception as e:
            print(f"❌ 备用提取失败: {e}")
            return None


# 创建全局提示词生成器实例
prompt_generator = ImagePromptGenerator()