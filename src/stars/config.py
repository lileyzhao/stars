"""配置管理模块，处理环境变量和用户配置。"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Confirm

# 导入语言模块
from .i18n.languages import Language

# 加载.env文件中的环境变量
load_dotenv()

# 创建控制台对象用于友好输出
console = Console()


@dataclass
class AppConfig:
    """应用配置类。"""

    github_username: str
    github_token: str
    openai_api_key: str
    openai_base_url: Optional[str] = None
    language: Language = Language.EN  # 语言设置
    output_dir: Optional[Path] = None
    include_urls: bool = False
    include_stats: bool = False

    def __post_init__(self):
        """初始化后处理。"""
        # 直接使用当前脚本运行目录
        self.output_dir = Path.cwd() / "../versions"
        
        # 确保输出目录存在，添加友好的错误处理
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            console.print(f"[red]错误: 无法创建或访问输出目录 '{self.output_dir}'[/red]")
            console.print(f"[yellow]原因: {str(e)}[/yellow]")
            console.print("[red]程序无法继续运行，请确保当前目录有写入权限后重试。[/red]")
            sys.exit(1)

    @classmethod
    def from_env(cls):
        """从环境变量创建配置。"""
        return cls(
            github_username=os.getenv("GITHUB_USERNAME", ""),
            github_token=os.getenv("GITHUB_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_base_url=os.getenv("OPENAI_BASE_URL", None),
            language=Language.EN,  # 默认使用英语
            output_dir=None,
            include_urls=False,
            include_stats=False,
        ) 