# Tweet 内容生成工具

基于 Tuzi API 的 Twitter Thread 内容生成工具，支持内容创作、图片生成和发布管理。

## 功能特点

### 🎯 核心功能
- **内容生成**: 基于选题自动生成 7 条结构化 Twitter Thread
- **图片生成**: 自动生成配套的封面图片和提示词
- **发布管理**: 支持发布功能（默认关闭，需手动启用）

### 📋 工作流程
1. 从输入文件夹读取选题内容
2. 使用 Tuzi API 生成 Twitter Thread
3. 生成图片标题和封面图片
4. 保存结果到输出文件夹
5. 可选发布到社交媒体平台

## 目录结构

```
tweet/
├── core/                      # 核心模块
│   ├── config/               # 配置管理
│   │   ├── __init__.py
│   │   └── config.py         # 配置类
│   ├── api/                  # API 客户端
│   │   ├── __init__.py
│   │   └── tuzi_client.py    # Tuzi API 客户端
│   └── utils/                # 工具函数
│       ├── __init__.py
│       └── logger.py
├── creation/                 # 创作模块
│   ├── __init__.py
│   ├── content_generator.py  # 内容生成器
│   └── image_generator.py    # 图片生成器
├── publishing/               # 发布模块（默认关闭）
│   ├── __init__.py
│   └── publisher.py         # 发布管理器
├── input/                    # 输入文件夹
│   └── topics.txt           # 选题文件
├── output/                   # 输出文件夹
├── .env                      # 环境配置文件
├── main.py                   # 主入口文件
└── README.md                # 说明文档
```

## 安装配置

### 1. 环境要求
- Python 3.7+
- pip 包管理器

### 2. 安装依赖
```bash
pip install requests python-dotenv
```

### 3. 配置环境变量
复制 `.env` 文件并配置：

```bash
# Tuzi API 配置（必需）
OPENAI_API_KEY=your_tuzi_api_key
OPENAI_API_BASE=https://api.tu-zi.com/v1
OPENAI_MODEL=chatgpt-4o-latest

# 图片生成配置
IMAGE_API_TOKEN=your_image_api_token
IMAGE_API_URL=https://api.tu-zi.com/v1/chat/completions
IMAGE_MODEL=gpt-4o-image
IMAGE_COUNT=1

# 路径配置
INPUT_DIR=./input
OUTPUT_DIR=./output

# 功能开关
ENABLE_PUBLISHING=false          # 发布功能默认关闭
ENABLE_IMAGE_GENERATION=true     # 图片生成功能默认开启
```

## 使用方法

### 1. 基础使用
```bash
# 仅生成内容
python main.py

# 生成内容 + 图片
python main.py --enable-images

# 生成内容 + 发布
python main.py --enable-publishing

# 启用所有功能
python main.py --enable-all
```

### 2. 指定输入文件
```bash
python main.py --input my_topics.txt
```

### 3. 测试和预览
```bash
# 测试各组件
python main.py --test

# 预览最近结果
python main.py --preview

# 预览指定数量的结果
python main.py --preview --count 10
```

### 4. 准备选题内容
在 `input/topics.txt` 文件中添加选题，每行一个：

```
35岁失业的人，现在都怎么赚钱？
AI配图风格内卷，封面风格抄袭成爆款捷径
微博"评论罗伯特"被爆侵隐私：AI评论竟成"画像工具"？
```

## 输出说明

### 生成的文件
- `tweet_content_*.json`: 包含完整 Thread 内容、标题和图片提示词
- `image_*.png`: 生成的封面图片（如果启用）
- `draft_*.json`: 发布草稿文件（如果启用发布功能）

### Thread 结构
生成的 Twitter Thread 遵循以下 7 条结构：
1. 第1条：钩子，带有反常识洞察
2. 第2-4条：拆解真实路径或案例
3. 第5-6条：指出常见误区  
4. 第7条：总结建议，鼓励收藏或评论

## 提示词说明

### Thread 生成提示词
```
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
```

### 图片生成提示词
```
Black background, large bold yellow Chinese text: '{主标题}'.
Below that in smaller white font: '{副标题}'.
Center-aligned, minimalist layout, high contrast, 16:9 aspect ratio, 
suitable for attention-grabbing social media thumbnail.
```

## 发布功能

### 默认状态
发布功能默认关闭，确保内容安全。

### 启用发布
1. 在 `.env` 文件中设置 `ENABLE_PUBLISHING=true`
2. 或使用命令行参数 `--enable-publishing`

### 发布平台
当前版本支持：
- 本地草稿保存
- 其他发布平台可扩展

## 开发说明

### 模块设计
- **core**: 核心功能模块，包含配置、API 客户端等
- **creation**: 创作模块，负责内容和图片生成
- **publishing**: 发布模块，处理内容发布（默认关闭）

### 扩展指南
- 添加新的 API 客户端：在 `core/api/` 目录下创建
- 扩展内容生成器：修改 `creation/content_generator.py`
- 添加发布平台：在 `publishing/` 目录下扩展

## 故障排除

### 常见问题
1. **API Key 错误**: 检查 `.env` 文件中的 `OPENAI_API_KEY` 配置
2. **网络连接失败**: 检查 `OPENAI_API_BASE` URL 是否正确
3. **图片生成失败**: 检查图片 API 相关配置
4. **输入文件不存在**: 确保 `input/topics.txt` 文件存在

### 调试模式
```bash
# 测试组件连接
python main.py --test
```

### 日志查看
- 所有输出信息会显示在控制台
- 错误信息包含详细的调试信息

## 许可证

本项目仅供学习和研究使用。