#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能图片提示词匹配器
根据选题内容从image_prompt_template.md中匹配最适合的提示词模板
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from ..gpt.gpt_client import gpt_client


class SmartPromptMatcher:
    """智能提示词匹配器"""
    
    def __init__(self, template_file: str = "input/image_prompt_template.md"):
        self.template_file = template_file
        self.templates = []
        self.load_templates()
    
    def load_templates(self) -> bool:
        """加载提示词模板"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析模板
            self.templates = self._parse_templates(content)
            print(f"✅ 成功加载 {len(self.templates)} 个图片提示词模板")
            return True
            
        except FileNotFoundError:
            print(f"❌ 模板文件不存在: {self.template_file}")
            return False
        except Exception as e:
            print(f"❌ 加载模板文件失败: {e}")
            return False
    
    def _parse_templates(self, content: str) -> List[Dict[str, str]]:
        """解析提示词模板"""
        templates = []
        
        # 使用正则表达式匹配案例
        pattern = r'##\s*案例\s*(\d+)：([^\n]+)\n(.*?)(?=##\s*案例|\Z)'
        matches = re.findall(pattern, content, re.DOTALL)
        
        for match in matches:
            case_num, title, content_block = match
            
            # 提取提示词内容
            prompt_match = re.search(r'```\n(.*?)\n```', content_block, re.DOTALL)
            if prompt_match:
                prompt = prompt_match.group(1).strip()
                
                # 提取关键词
                keywords = self._extract_keywords_from_title(title)
                
                templates.append({
                    'case_number': case_num,
                    'title': title.strip(),
                    'prompt': prompt,
                    'keywords': keywords,
                    'content': content_block.strip()
                })
        
        return templates
    
    def _extract_keywords_from_title(self, title: str) -> List[str]:
        """从标题中提取关键词"""
        keywords = []
        
        # 常见的图片类型关键词映射
        keyword_mapping = {
            '广告': ['广告', '营销', '宣传', '推广'],
            '海报': ['海报', '宣传', '设计'],
            '名片': ['名片', '商务', '联系'],
            '3D': ['3D', '立体', '渲染'],
            '水晶球': ['水晶球', '场景', '故事'],
            '书架': ['书架', '家具', 'Logo'],
            '冰棒': ['冰棒', '食品', '创意'],
            '推文': ['推文', '社交', '截图'],
            '矢量': ['矢量', '艺术', '插画'],
            '建筑': ['建筑', '迷你', 'Q版'],
            '信息图': ['信息图', '卡片', '手绘'],
            '折叠': ['折叠', '纸雕', '立体'],
            '小红书': ['小红书', '封面', '社交'],
            '极简': ['极简', '未来', '海报'],
            '复古': ['复古', '宣传', '海报'],
            '键盘': ['键盘', '键帽', '品牌'],
            '徽章': ['徽章', 'emoji', '金属'],
            '字母': ['字母', '融合', '创意']
        }
        
        # 从标题中匹配关键词
        for key, values in keyword_mapping.items():
            if key in title:
                keywords.extend(values)
        
        # 移除重复并返回
        return list(set(keywords))
    
    def find_best_match(self, topic: Dict[str, str]) -> Optional[Dict[str, str]]:
        """为选题找到最佳匹配的提示词模板"""
        if not self.templates:
            print("❌ 没有可用的提示词模板")
            return None
        
        print(f"🔍 为选题寻找最佳提示词模板: {topic.get('title', '未知选题')}")
        
        # 使用GPT进行智能匹配
        best_template = self._gpt_match_template(topic)
        
        if best_template:
            print(f"✅ 找到最佳匹配: 案例{best_template['case_number']} - {best_template['title']}")
            return best_template
        else:
            # 如果GPT匹配失败，使用关键词匹配作为后备
            print("⚠️ GPT匹配失败，使用关键词匹配")
            return self._keyword_match_template(topic)
    
    def _gpt_match_template(self, topic: Dict[str, str]) -> Optional[Dict[str, str]]:
        """使用GPT进行智能模板匹配"""
        if not gpt_client:
            return None
        
        try:
            # 构建模板列表描述
            template_descriptions = []
            for template in self.templates:
                template_descriptions.append(
                    f"案例{template['case_number']}: {template['title']}"
                )
            
            # 构建匹配提示词
            match_prompt = f"""
我需要为以下选题找到最适合的图片提示词模板：

选题信息：
- 标题：{topic.get('title', '')}
- 核心争议：{topic.get('controversy', '')}
- 关键词：{topic.get('keywords', '')}
- 内容简介：{topic.get('summary', '')[:200]}...

可选模板列表：
{chr(10).join(template_descriptions)}

请分析选题的内容类型、情感色彩和视觉需求，从上述模板中选择最适合的一个。

要求：
1. 考虑选题的内容属性（科技/商业/争议/新闻等）
2. 考虑适合的视觉风格（正式/创意/简约/复古等）
3. 只返回案例编号，如：87

请选择："""

            response = gpt_client.simple_chat(match_prompt)
            
            if response:
                # 提取案例编号
                case_number = re.search(r'\d+', response.strip())
                if case_number:
                    case_num = case_number.group()
                    # 查找对应的模板
                    for template in self.templates:
                        if template['case_number'] == case_num:
                            return template
            
            return None
            
        except Exception as e:
            print(f"❌ GPT匹配过程出错: {e}")
            return None
    
    def _keyword_match_template(self, topic: Dict[str, str]) -> Optional[Dict[str, str]]:
        """使用关键词进行模板匹配（后备方案）"""
        topic_text = f"{topic.get('title', '')} {topic.get('keywords', '')} {topic.get('summary', '')}"
        topic_text = topic_text.lower()
        
        best_score = 0
        best_template = None
        
        for template in self.templates:
            score = 0
            # 计算关键词匹配分数
            for keyword in template['keywords']:
                if keyword.lower() in topic_text:
                    score += 1
            
            # 标题匹配额外加分
            if any(word in topic_text for word in template['title'].lower().split()):
                score += 2
            
            if score > best_score:
                best_score = score
                best_template = template
        
        # 如果没有找到匹配，返回第一个模板作为默认
        if not best_template and self.templates:
            best_template = self.templates[0]
            print(f"⚠️ 使用默认模板: 案例{best_template['case_number']}")
        
        return best_template
    
    def customize_prompt_for_topic(self, template: Dict[str, str], topic: Dict[str, str]) -> str:
        """为特定选题定制提示词"""
        base_prompt = template['prompt']
        topic_title = topic.get('title', '')
        topic_keywords = topic.get('keywords', '')
        
        # 使用GPT来定制提示词
        if gpt_client:
            customize_prompt = f"""
请根据以下选题信息，定制这个图片生成提示词：

选题信息：
- 标题：{topic_title}
- 关键词：{topic_keywords}
- 核心争议：{topic.get('controversy', '')}

原始提示词模板：
{base_prompt}

请保持原始提示词的基本结构和风格，但根据选题内容进行适当的定制，使图片更符合选题主题。

注意：
1. 保持提示词的专业性和可执行性
2. 适当融入选题相关的元素或概念
3. 保持原有的视觉风格
4. 确保提示词清晰明确

定制后的提示词："""
            
            try:
                customized = gpt_client.simple_chat(customize_prompt)
                if customized and len(customized.strip()) > 50:
                    return customized.strip()
            except Exception as e:
                print(f"⚠️ 提示词定制失败: {e}")
        
        # 如果GPT定制失败，返回原始模板
        return base_prompt
    
    def get_template_by_number(self, case_number: str) -> Optional[Dict[str, str]]:
        """根据案例编号获取模板"""
        for template in self.templates:
            if template['case_number'] == case_number:
                return template
        return None
    
    def list_all_templates(self) -> List[Dict[str, str]]:
        """列出所有模板"""
        return self.templates
    
    def get_statistics(self) -> Dict[str, any]:
        """获取模板统计信息"""
        return {
            'total_templates': len(self.templates),
            'template_file': self.template_file,
            'categories': self._get_template_categories()
        }
    
    def _get_template_categories(self) -> Dict[str, int]:
        """获取模板分类统计"""
        categories = {}
        for template in self.templates:
            for keyword in template['keywords']:
                categories[keyword] = categories.get(keyword, 0) + 1
        return categories


# 创建全局智能提示词匹配器实例
smart_prompt_matcher = SmartPromptMatcher()