#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tweet 内容生成工具
主入口文件 - 重构版本
"""

import os
import sys
import argparse
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config.config import config
from creation.content_generator import content_generator
from creation.image_generator import image_generator
from publishing.publisher import publisher


def process_topics_workflow(input_file: str = None, enable_images: bool = True, enable_publishing: bool = False) -> List[Dict]:
    """
    处理选题的完整工作流程
    
    Args:
        input_file: 输入文件路径
        enable_images: 是否生成图片
        enable_publishing: 是否发布内容
        
    Returns:
        处理结果列表
    """
    print("🚀 Tweet 内容生成工具")
    print("=" * 60)
    
    if not content_generator:
        print("❌ 内容生成器未正确初始化")
        return []
    
    # 设置默认输入文件
    if not input_file:
        input_file = os.path.join(config.input_dir, "topics.txt")
    
    print(f"📋 工作流程配置:")
    print(f"   输入文件: {input_file}")
    print(f"   生成图片: {'✅' if enable_images else '❌'}")
    print(f"   发布内容: {'✅' if enable_publishing else '❌'}")
    print("=" * 60)
    
    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"❌ 输入文件不存在: {input_file}")
        print("💡 请在 input/ 目录下创建 topics.txt 文件并添加选题内容")
        return []
    
    # 1. 生成内容
    print("\n📝 步骤 1: 生成 Tweet 内容")
    results = content_generator.process_all_topics(input_file)
    
    if not results:
        print("❌ 没有成功处理任何选题")
        return []
    
    successful_results = [r for r in results if r["success"]]
    print(f"✅ 内容生成完成: {len(successful_results)}/{len(results)}")
    
    # 2. 生成图片（如果启用）
    if enable_images and image_generator and image_generator.is_available():
        print("\n🎨 步骤 2: 生成封面图片")
        
        for result in successful_results:
            if result["titles"]:
                main_title = result["titles"]["主标题"]
                subtitle = result["titles"]["副标题"]
                topic = result["topic"]
                
                print(f"🎨 为选题生成图片: {topic}")
                image_path = image_generator.generate_cover_image(main_title, subtitle, topic)
                
                if image_path:
                    result["cover_image"] = image_path
                    print(f"✅ 图片生成成功")
                else:
                    print(f"⚠️ 图片生成失败")
    elif enable_images:
        print("\n⚠️ 图片生成功能不可用，跳过图片生成")
    else:
        print("\n⏭️ 跳过图片生成")
    
    # 3. 发布内容（如果启用）
    if enable_publishing and publisher and publisher.is_available():
        print("\n📤 步骤 3: 发布内容")
        
        for result in successful_results:
            if result["thread"]:
                topic = result["topic"]
                thread = result["thread"]
                images = [result.get("cover_image")] if result.get("cover_image") else []
                
                print(f"📤 发布选题: {topic}")
                success = publisher.publish_thread(thread, topic, images)
                
                result["published"] = success
                if success:
                    print(f"✅ 发布成功")
                else:
                    print(f"❌ 发布失败")
    elif enable_publishing:
        print("\n⚠️ 发布功能不可用，跳过发布")
    else:
        print("\n⏭️ 跳过发布（发布功能默认关闭）")
    
    # 4. 显示最终统计
    print("\n📊 处理结果统计:")
    print("=" * 60)
    
    total_topics = len(results)
    successful_content = len(successful_results)
    successful_images = len([r for r in successful_results if r.get("cover_image")])
    successful_publish = len([r for r in successful_results if r.get("published")])
    
    print(f"总选题数量: {total_topics}")
    print(f"内容生成成功: {successful_content}")
    
    if enable_images:
        print(f"图片生成成功: {successful_images}")
    
    if enable_publishing:
        print(f"发布成功: {successful_publish}")
    
    print("\n🎉 工作流程完成!")
    print(f"📁 结果已保存到: {config.output_dir}")
    
    return results


def preview_recent_results(count: int = 5) -> None:
    """
    预览最近的生成结果
    
    Args:
        count: 显示数量
    """
    print(f"📋 最近 {count} 个生成结果:")
    print("=" * 60)
    
    try:
        import json
        import glob
        from datetime import datetime
        
        # 查找所有结果文件
        pattern = os.path.join(config.output_dir, "tweet_content_*.json")
        files = glob.glob(pattern)
        
        if not files:
            print("📭 没有找到生成结果")
            return
        
        # 按修改时间排序
        files.sort(key=os.path.getmtime, reverse=True)
        
        for i, file_path in enumerate(files[:count], 1):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                filename = os.path.basename(file_path)
                topic = data.get("topic", "未知选题")
                timestamp = data.get("timestamp", "未知时间")
                thread_count = data.get("thread_count", 0)
                
                print(f"{i:2d}. {filename}")
                print(f"    选题: {topic}")
                print(f"    时间: {timestamp}")
                print(f"    推文数: {thread_count}")
                print("-" * 40)
                
            except Exception as e:
                print(f"⚠️ 读取文件失败: {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"❌ 预览失败: {e}")


def test_components() -> None:
    """测试各个组件是否正常工作"""
    print("🧪 组件测试")
    print("=" * 60)
    
    # 测试配置
    print("1. 配置测试:")
    if config:
        print("   ✅ 配置加载成功")
        tuzi_config = config.get_tuzi_config()
        print(f"   API Base: {tuzi_config['api_base']}")
        print(f"   Model: {tuzi_config['model']}")
    else:
        print("   ❌ 配置加载失败")
    
    # 测试内容生成器
    print("\n2. 内容生成器测试:")
    if content_generator:
        print("   ✅ 内容生成器初始化成功")
    else:
        print("   ❌ 内容生成器初始化失败")
    
    # 测试图片生成器
    print("\n3. 图片生成器测试:")
    if image_generator:
        if image_generator.is_available():
            print("   ✅ 图片生成器可用")
        else:
            print("   ⚠️ 图片生成器已禁用")
    else:
        print("   ❌ 图片生成器初始化失败")
    
    # 测试发布器
    print("\n4. 发布器测试:")
    if publisher:
        if publisher.is_available():
            print("   ✅ 发布器可用")
        else:
            print("   ⚠️ 发布器已禁用（默认状态）")
    else:
        print("   ❌ 发布器初始化失败")
    
    print("\n🎯 测试完成!")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Tweet 内容生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py                          # 运行完整工作流程（仅生成内容）
  python main.py --enable-images          # 生成内容 + 图片
  python main.py --enable-publishing      # 生成内容 + 发布
  python main.py --enable-all             # 生成内容 + 图片 + 发布
  python main.py --input topics.txt       # 指定输入文件
  python main.py --test                   # 测试各组件
  python main.py --preview                # 预览最近结果
        """
    )
    
    parser.add_argument("--input", type=str, help="输入文件路径")
    parser.add_argument("--enable-images", action="store_true", help="启用图片生成")
    parser.add_argument("--enable-publishing", action="store_true", help="启用内容发布")
    parser.add_argument("--enable-all", action="store_true", help="启用所有功能")
    parser.add_argument("--test", action="store_true", help="测试各个组件")
    parser.add_argument("--preview", action="store_true", help="预览最近的生成结果")
    parser.add_argument("--count", type=int, default=5, help="预览结果数量（默认5个）")
    
    args = parser.parse_args()
    
    if args.test:
        test_components()
        return
    
    if args.preview:
        preview_recent_results(args.count)
        return
    
    # 确定启用的功能
    enable_images = args.enable_images or args.enable_all
    enable_publishing = args.enable_publishing or args.enable_all
    
    # 运行主工作流程
    results = process_topics_workflow(
        input_file=args.input,
        enable_images=enable_images,
        enable_publishing=enable_publishing
    )
    
    if results:
        successful = len([r for r in results if r["success"]])
        print(f"\n✨ 处理完成! 成功处理 {successful}/{len(results)} 个选题")
    else:
        print("\n❌ 没有成功处理任何选题")


if __name__ == "__main__":
    main()