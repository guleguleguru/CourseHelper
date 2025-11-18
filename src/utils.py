"""
工具函数模块
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


def load_config() -> Dict[str, Any]:
    """
    加载配置文件
    
    Returns:
        配置字典
    """
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def load_env():
    """
    加载环境变量
    """
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    env_path = project_root / "config" / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # 尝试加载根目录的 .env
        load_dotenv()
        # 如果还是没有，尝试当前目录
        if not os.getenv("OPENAI_API_KEY"):
            load_dotenv("config/.env")


def get_project_root() -> Path:
    """
    获取项目根目录
    
    Returns:
        项目根目录路径
    """
    return Path(__file__).parent.parent


def ensure_dir(path: Path):
    """
    确保目录存在
    
    Args:
        path: 目录路径
    """
    path.mkdir(parents=True, exist_ok=True)


def get_openai_api_key() -> str:
    """
    获取 OpenAI API Key
    
    Returns:
        API Key
        
    Raises:
        ValueError: 如果未设置 API Key
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        raise ValueError(
            "未设置 OPENAI_API_KEY！\n"
            "请在 config/.env 文件中设置您的 API key，"
            "或设置环境变量 OPENAI_API_KEY"
        )
    return api_key

