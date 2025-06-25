#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容级别枚举定义
用于分类不同可信度的内容
"""

from enum import Enum


class ContentLevel(Enum):
    """内容级别枚举"""
    CONFIRMED = 1    # 官方文件 / 多家主流媒体已报道
    LIKELY = 2       # 路透社或头部记者首发，官方未否认
    RUMOR = 3        # 仅社媒爆料，待跟进


# 级别描述映射
LEVEL_DESCRIPTIONS = {
    1: "Confirmed：官方文件 / 多家主流媒体已报道",
    2: "Likely：路透社或头部记者首发，官方未否认", 
    3: "Rumor：仅社媒爆料，待跟进"
}

# 级别名称映射  
LEVEL_NAMES = {
    1: "Confirmed",
    2: "Likely", 
    3: "Rumor"
}


def get_level_description(level: int) -> str:
    """获取级别描述"""
    return LEVEL_DESCRIPTIONS.get(level, f"未知级别: {level}")


def get_level_name(level: int) -> str:
    """获取级别名称"""
    return LEVEL_NAMES.get(level, f"Level{level}")


def is_valid_level(level: int) -> bool:
    """检查级别是否有效"""
    return level in LEVEL_DESCRIPTIONS


def get_all_levels():
    """获取所有级别信息"""
    return [
        {
            "level": level,
            "name": get_level_name(level),
            "description": description
        }
        for level, description in LEVEL_DESCRIPTIONS.items()
    ]