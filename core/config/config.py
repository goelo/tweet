import os
import sys

# 尝试导入 dotenv，如果没有安装则提示
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("⚠️ python-dotenv 未安装，请运行: pip install python-dotenv")

class Config:
    """配置管理类，用于管理 Tuzi API 和其他配置"""

    def __init__(self):
        # 加载 .env 文件（如果 dotenv 可用）
        if DOTENV_AVAILABLE:
            # 获取项目根目录（从 core/config/ 回到根目录）
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            env_path = os.path.join(current_dir, '.env')
            load_dotenv(env_path)
        
        # Tuzi API 配置（兼容 OpenAI 格式）
        self.tuzi_api_key = os.getenv('OPENAI_API_KEY')  # 使用现有的 OPENAI_API_KEY
        self.tuzi_api_base = os.getenv('OPENAI_API_BASE', 'https://api.tu-zi.com/v1')
        self.tuzi_model = os.getenv('OPENAI_MODEL', 'chatgpt-4o-latest')
        
        # 输入输出目录配置
        self.input_dir = os.getenv('INPUT_DIR', './input')
        self.output_dir = os.getenv('OUTPUT_DIR', './output')
        
        # 发布模块配置（默认关闭）
        self.enable_publishing = os.getenv('ENABLE_PUBLISHING', 'false').lower() == 'true'
        
        # 图片生成配置
        self.enable_image_generation = os.getenv('ENABLE_IMAGE_GENERATION', 'true').lower() == 'true'
        self.image_api_key = os.getenv('IMAGE_API_TOKEN', self.tuzi_api_key)
        self.image_api_url = os.getenv('IMAGE_API_URL', 'https://api.tu-zi.com/v1/chat/completions')
        self.image_model = os.getenv('IMAGE_MODEL', 'gpt-4o-image')
        self.image_count = int(os.getenv('IMAGE_COUNT', '1'))

        # Twitter API 配置
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.twitter_api_key = os.getenv('TWITTER_API_KEY')
        self.twitter_api_secret = os.getenv('TWITTER_API_SECRET')
        self.twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        self.twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        # Twitter 爬虫配置
        self.twitter_safe_mode = os.getenv('TWITTER_SAFE_MODE', 'true').lower() == 'true'
        self.twitter_max_requests_per_minute = int(os.getenv('TWITTER_MAX_REQUESTS_PER_MINUTE', '15'))
        self.twitter_max_requests_per_hour = int(os.getenv('TWITTER_MAX_REQUESTS_PER_HOUR', '500'))
        self.twitter_base_delay = float(os.getenv('TWITTER_BASE_DELAY', '3.0'))
        self.twitter_max_delay = float(os.getenv('TWITTER_MAX_DELAY', '30.0'))
        self.twitter_max_retries = int(os.getenv('TWITTER_MAX_RETRIES', '3'))

        # Twitter 爆款内容阈值
        self.twitter_min_likes = int(os.getenv('TWITTER_MIN_LIKES', '1000'))
        self.twitter_min_retweets = int(os.getenv('TWITTER_MIN_RETWEETS', '100'))
        self.twitter_min_engagement_score = int(os.getenv('TWITTER_MIN_ENGAGEMENT_SCORE', '2000'))
        self.twitter_min_viral_score = int(os.getenv('TWITTER_MIN_VIRAL_SCORE', '500'))

        # Twitter 搜索配置
        self.twitter_default_count = int(os.getenv('TWITTER_DEFAULT_COUNT', '10'))
        self.twitter_default_woeid = int(os.getenv('TWITTER_DEFAULT_WOEID', '1'))  # 1=全球
        self.twitter_max_results_per_keyword = int(os.getenv('TWITTER_MAX_RESULTS_PER_KEYWORD', '20'))

        # Typefully API 配置
        self.typefully_api_key = os.getenv('TYPEFULLY_API_KEY')

        # 反封号配置（通用）
        self.max_requests_per_minute = int(os.getenv('MAX_REQUESTS_PER_MINUTE', '20'))
        self.max_requests_per_hour = int(os.getenv('MAX_REQUESTS_PER_HOUR', '800'))
        self.base_delay = float(os.getenv('BASE_DELAY', '2.0'))
        self.max_delay = float(os.getenv('MAX_DELAY', '30.0'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))

        # 代理配置
        proxies_str = os.getenv('PROXIES', '')
        self.proxies = [p.strip() for p in proxies_str.split(',') if p.strip()] if proxies_str else []

        # 确保输入输出目录存在
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 验证必要的配置
        if not self.tuzi_api_key:
            print("⚠️ OPENAI_API_KEY 未设置，Tuzi API 功能将不可用")
        
        if self.enable_publishing and not self.twitter_bearer_token:
            print("⚠️ 发布功能已启用但 TWITTER_BEARER_TOKEN 未设置")
            
        if self.enable_publishing and not self.typefully_api_key:
            print("⚠️ 发布功能已启用但 TYPEFULLY_API_KEY 未设置")
    
    def get_tuzi_config(self):
        """获取 Tuzi API 配置"""
        return {
            'api_key': self.tuzi_api_key,
            'api_base': self.tuzi_api_base,
            'model': self.tuzi_model
        }
    
    def get_image_config(self):
        """获取图片生成配置"""
        return {
            'api_key': self.image_api_key,
            'api_url': self.image_api_url,
            'model': self.image_model,
            'count': self.image_count,
            'enabled': self.enable_image_generation
        }
    
    def get_paths_config(self):
        """获取路径配置"""
        return {
            'input_dir': self.input_dir,
            'output_dir': self.output_dir
        }

    def get_twitter_config(self):
        """获取 Twitter API 配置"""
        return {
            'bearer_token': self.twitter_bearer_token,
            'api_key': self.twitter_api_key,
            'api_secret': self.twitter_api_secret,
            'access_token': self.twitter_access_token,
            'access_token_secret': self.twitter_access_token_secret
        }

    def get_twitter_crawler_config(self):
        """获取 Twitter 爬虫配置"""
        return {
            'safe_mode': self.twitter_safe_mode,
            'max_requests_per_minute': self.twitter_max_requests_per_minute,
            'max_requests_per_hour': self.twitter_max_requests_per_hour,
            'base_delay': self.twitter_base_delay,
            'max_delay': self.twitter_max_delay,
            'max_retries': self.twitter_max_retries,
            'proxies': self.proxies
        }

    def get_twitter_viral_thresholds(self):
        """获取 Twitter 爆款内容阈值"""
        return {
            'min_likes': self.twitter_min_likes,
            'min_retweets': self.twitter_min_retweets,
            'min_engagement_score': self.twitter_min_engagement_score,
            'min_viral_score': self.twitter_min_viral_score
        }

    def get_twitter_search_config(self):
        """获取 Twitter 搜索配置"""
        return {
            'default_count': self.twitter_default_count,
            'default_woeid': self.twitter_default_woeid,
            'max_results_per_keyword': self.twitter_max_results_per_keyword
        }

    def get_anti_ban_config(self):
        """获取反封号配置"""
        return {
            'max_requests_per_minute': self.max_requests_per_minute,
            'max_requests_per_hour': self.max_requests_per_hour,
            'base_delay': self.base_delay,
            'max_delay': self.max_delay,
            'max_retries': self.max_retries,
            'proxies': self.proxies
        }

    def get_typefully_config(self):
        """获取 Typefully API 配置"""
        return {
            'api_key': self.typefully_api_key
        }
    
    def print_config(self):
        """打印当前配置（隐藏敏感信息）"""
        print("🤖 GPT API 配置:")
        print(f"   API Base: {self.openai_api_base}")
        print(f"   Model: {self.openai_model}")
        print(f"   API Key: {self.openai_api_key[:10]}...{self.openai_api_key[-4:] if self.openai_api_key else 'None'}")
        print()

        print("🐦 Twitter API 配置:")
        bearer_display = f"{self.twitter_bearer_token[:10]}...{self.twitter_bearer_token[-4:]}" if self.twitter_bearer_token else 'None'
        api_key_display = f"{self.twitter_api_key[:10]}...{self.twitter_api_key[-4:]}" if self.twitter_api_key else 'None'
        print(f"   Bearer Token: {bearer_display}")
        print(f"   API Key: {api_key_display}")
        print(f"   安全模式: {'✅ 开启' if self.twitter_safe_mode else '❌ 关闭'}")
        print(f"   每分钟最大请求数: {self.twitter_max_requests_per_minute}")
        print(f"   基础延时: {self.twitter_base_delay}秒")
        print()

        print("🔥 Twitter 爆款内容阈值:")
        print(f"   最小点赞数: {self.twitter_min_likes:,}")
        print(f"   最小转发数: {self.twitter_min_retweets:,}")
        print(f"   最小参与度分数: {self.twitter_min_engagement_score:,}")
        print(f"   最小病毒传播分数: {self.twitter_min_viral_score:,}")
        print()

        print("🔍 Twitter 搜索配置:")
        print(f"   默认获取数量: {self.twitter_default_count}")
        print(f"   默认地区ID: {self.twitter_default_woeid}")
        print(f"   每关键词最大结果数: {self.twitter_max_results_per_keyword}")
        print()

        print("🛡️ 反封号配置:")
        print(f"   每分钟最大请求数: {self.max_requests_per_minute}")
        print(f"   每小时最大请求数: {self.max_requests_per_hour}")
        print(f"   基础延时: {self.base_delay}秒")
        print(f"   最大延时: {self.max_delay}秒")
        print(f"   最大重试次数: {self.max_retries}")
        print(f"   代理数量: {len(self.proxies)}")
        print()

        print("📝 Typefully API 配置:")
        typefully_display = f"{self.typefully_api_key[:10]}...{self.typefully_api_key[-4:]}" if self.typefully_api_key else 'None'
        print(f"   API Key: {typefully_display}")

# 创建全局配置实例
try:
    config = Config()
except ValueError as e:
    print(f"配置错误: {e}")
    config = None
