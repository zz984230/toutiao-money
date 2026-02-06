"""配置管理模块"""

import os
import yaml
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

DEFAULT_CONFIG = {
    # Playwright配置
    "playwright": {
        "headless": True,           # 是否无头模式
        "user_data_dir": "data/user_data",  # 用户数据目录
        "cookies_file": "data/cookies.json",     # Cookie保存路径
    },

    # 行为配置
    "behavior": {
        "confirmation_mode": True,    # 交互确认开关
        "max_comments_per_run": 5,    # 每次最多评论数
        "min_read_count": 1000,       # 最低阅读量阈值
        "comment_interval": 30,       # 评论间隔(秒)
    },

    # 评论风格
    "style": {
        "length": "50-100字",
        "stance": "理性批判",         # 科技乐观/保守谨慎等
        "emotion_level": "medium",    # low/medium/high
    },

    # 头条账号Cookie（可选）
    "toutiao": {
        "cookies": "",  # 从浏览器复制的Cookie字符串
    },
}


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.yaml"
        self.config = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self):
        """加载配置文件"""
        config_file = Path(self.config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._merge_config(user_config)

    def _merge_config(self, user_config: dict):
        """合并用户配置"""
        for key, value in user_config.items():
            if key in self.config and isinstance(self.config[key], dict):
                self.config[key].update(value)
            else:
                self.config[key] = value

    def save(self):
        """保存配置到文件"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, allow_unicode=True)

    def get(self, key_path: str, default=None):
        """获取配置值，支持点号分隔的路径"""
        keys = key_path.split('.')
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    @property
    def playwright(self):
        return self.config['playwright']

    @property
    def behavior(self):
        return self.config['behavior']

    @property
    def style(self):
        return self.config['style']

    @property
    def toutiao(self):
        return self.config['toutiao']

    def get_toutiao_credentials(self) -> tuple[Optional[str], Optional[str]]:
        """获取头条账号凭据（从环境变量）"""
        username = os.getenv('TOUTIAO_USERNAME')
        password = os.getenv('TOUTIAO_PASSWORD')
        return username, password


# 全局配置实例
config = Config()
