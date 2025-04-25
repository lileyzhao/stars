"""命令行界面模块，提供用户交互功能。"""

import os
import sys
import re
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from rich.console import Console
from rich.prompt import Confirm, Prompt, IntPrompt

from .config import AppConfig
from .i18n.languages import Language, get_language_name, get_language_dict, get_available_languages
from .i18n.translator import get_translator
from . import __version__

# 设置日志记录器
logger = logging.getLogger(__name__)


class CLI:
    """命令行界面类。"""

    def __init__(self):
        """初始化CLI实例。"""
        self.console = Console()
        # 使用全局翻译器实例，初始默认为简体中文
        self.translator = get_translator()
        
    def setup_language(self, language: str) -> None:
        """
        设置语言。
        
        Args:
            language: 语言代码
        """
        # 确保 language 是字符串
        if isinstance(language, Language):
            language = language.value
        
        # 更新全局翻译器实例的语言设置
        self.translator = get_translator(language)
        
        logger.debug(f"Language set to: {language}")
    
    def get_initial_language_selection(self) -> str:
        """
        在程序启动时获取初始语言选择。
        
        Returns:
            选择的语言代码
        """
        # 以多种语言显示选择提示
        # 这里不使用翻译器，因为我们还不知道用户的语言偏好
        self.console.print("\n[bold blue]╭─────────────────────────────────────────────────╮[/bold blue]")
        self.console.print("[bold blue]│[/bold blue]       [bold yellow]✨  欢迎 / Welcome / Bienvenido  ✨[/bold yellow]       [bold blue]│[/bold blue]")
        self.console.print("[bold blue]╰─────────────────────────────────────────────────╯[/bold blue]\n")
        
        self.console.print("[bold]请选择语言 / Please select your language / Por favor, selecciona tu idioma:[/bold]\n")
        
        # 使用Language枚举直接创建选项
        language_options = [(lang, get_language_name(lang, lang)) for lang in get_available_languages()]
        
        # 显示选项
        for i, (code, name) in enumerate(language_options, 1):
            self.console.print(f"  {i}. {name}")
        
        # 获取用户选择
        while True:
            choice = IntPrompt.ask("\n[bold]Enter number / 输入数字 / Introduce número / 番号を入力[/bold]", default=1)
            if 1 <= choice <= len(language_options):
                selected_language = language_options[choice-1][0]
                
                # 使用通用方式显示确认信息
                language_name = get_language_name(selected_language, selected_language)
                self.console.print(f"\n[green]Language set to: {language_name}[/green]\n")
                
                return selected_language
            else:
                self.console.print("[red]Invalid choice / 无效选择 / Selección no válida / 無効な選択[/red]")

    def parse_args(self) -> argparse.Namespace:
        """
        解析命令行参数。
        
        Returns:
            解析后的参数命名空间
        """
        parser = argparse.ArgumentParser(description="GitHub星标仓库分析工具")
        
        # 语言参数
        parser.add_argument("--language", "-l", 
                          help="指定语言 (en, zh-CN, zh-TW, es, ja, pt, fr, de, ru)",
                          choices=[lang.value for lang in Language])
        
        # GitHub相关参数
        parser.add_argument("--github-username", "-u",
                          help="GitHub用户名")
        parser.add_argument("--github-token", "-t",
                          help="GitHub个人访问令牌")
        
        # OpenAI相关参数
        parser.add_argument("--openai-key", "-k",
                          help="OpenAI API密钥")
        parser.add_argument("--openai-url", "-o",
                          help="OpenAI API代理URL")
        
        # 跳过确认参数
        parser.add_argument("--no-confirm", "-y",
                          help="跳过所有确认步骤",
                          action="store_true")
        
        # 覆盖README参数
        parser.add_argument("--overwrite-readme", "-r",
                          help="将输出内容覆盖到README.md文件",
                          action="store_true")
        
        return parser.parse_args()

    def display_welcome(self):
        """显示欢迎信息。"""
        self.console.print("\n[bold blue]───────────────────────────────────────────────────[/bold blue]")
        self.console.print(f"[bold yellow]✨  {self.translator('app.name')}[/bold yellow]  [bold cyan]{self.translator('ui.welcome.subtitle')}[/bold cyan]  [bold yellow]✨[/bold yellow]")
        self.console.print("[bold blue]───────────────────────────────────────────────────[/bold blue]")
        
        self.console.print(f"\n[cyan]{self.translator('ui.welcome.description')}[/cyan]")
        # self.console.print("[green]┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈[/green]")
        
        self.console.print(self.translator('ui.welcome.version', version=__version__))
        self.console.print(self.translator('ui.welcome.author', author="LileyZhao"))
        
        self.console.print(f"\n[bold magenta]{self.translator('ui.welcome.start')}[/bold magenta]\n")
        self.console.print(f"[cyan italic]{self.translator('ui.welcome.tagline')}[/cyan italic]\n")

    def normalize_base_url(self, url: str) -> str:
        """
        规范化API基础URL。

        Args:
            url: 用户输入的URL

        Returns:
            规范化后的URL
        """
        url = url.strip()
        
        # 如果输入为空，返回None
        if not url:
            return None
            
        # 添加https://前缀（如果没有协议前缀）
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # 确保URL不以/结尾
        url = url.rstrip('/')
            
        # 添加/v1后缀（如果没有）
        if not url.endswith('/v1'):
            url = url + '/v1'
            
        return url

    def validate_base_url(self, url: str) -> bool:
        """
        验证API基础URL格式是否有效。

        Args:
            url: 规范化后的URL

        Returns:
            URL是否有效
        """
        if not url:
            return True
            
        # 验证URL格式
        pattern = r'^https?://[a-zA-Z0-9][-a-zA-Z0-9.]*(\.[a-zA-Z0-9][-a-zA-Z0-9.]*)+(:\d+)?(/[-a-zA-Z0-9_%]+)*(/v1)$'
        return bool(re.match(pattern, url))

    def select_language(self, display_language: str) -> str:
        """
        让用户选择语言。
        
        Args:
            display_language: 显示语言
            
        Returns:
            选择的语言代码
        """
        # 确保语言定义的顺序与初始语言选择一致
        language_options = [
            (Language.EN, get_language_name(Language.EN, display_language)),
            (Language.ZH_CN, get_language_name(Language.ZH_CN, display_language)),
            (Language.ZH_TW, get_language_name(Language.ZH_TW, display_language)),
            (Language.ES, get_language_name(Language.ES, display_language)),
            (Language.JA, get_language_name(Language.JA, display_language)),
            (Language.PT, get_language_name(Language.PT, display_language)),
            (Language.FR, get_language_name(Language.FR, display_language)),
            (Language.DE, get_language_name(Language.DE, display_language)),
            (Language.RU, get_language_name(Language.RU, display_language))
        ]
        
        # 构建语言选择提示
        language_prompt = f"\n[bold green]{self.translator('ui.language.select')}\n"
        
        for i, (code, name) in enumerate(language_options, 1):
            language_prompt += f"  {i}. {name}\n"
            
        language_prompt += self.translator('ui.language.choice_prompt', count=len(language_options))
        
        # 获取用户选择
        while True:
            choice = IntPrompt.ask(language_prompt, default=1)
            if 1 <= choice <= len(language_options):
                selected_language = language_options[choice-1][0]
                
                # 显示确认消息
                self.console.print(f"[green]{self.translator('ui.language.success', language_param=get_language_name(selected_language, display_language))}[/green]\n")
                
                return selected_language
            else:
                self.console.print("[red]Invalid choice / 无效选择 / Selección no válida[/red]")

    def get_user_config(self) -> AppConfig:
        """
        获取用户配置信息。

        Returns:
            应用配置对象
        """
        # 解析命令行参数
        args = self.parse_args()
        self.args = args  # 保存参数供其他方法使用
        
        # 从环境变量加载配置
        config = AppConfig.from_env()
        
        # 如果命令行指定了语言，直接使用
        if args.language:
            config.language = args.language
            self.setup_language(args.language)
        else:
            # 否则让用户选择语言
            selected_language = self.get_initial_language_selection()
            config.language = selected_language
            self.setup_language(selected_language)
        
        # 显示欢迎信息（使用已设置的语言）
        self.display_welcome()
        
        # 如果命令行指定了GitHub用户名，直接使用
        if args.github_username:
            config.github_username = args.github_username
            
        # 如果命令行指定了GitHub令牌，直接使用
        if args.github_token:
            config.github_token = args.github_token
            
        # 如果命令行指定了OpenAI API密钥，直接使用
        if args.openai_key:
            config.openai_api_key = args.openai_key
            
        # 如果命令行指定了OpenAI API代理URL，规范化并使用
        if args.openai_url:
            config.openai_base_url = self.normalize_base_url(args.openai_url)
        elif config.openai_base_url:
            config.openai_base_url = self.normalize_base_url(config.openai_base_url)
        
        # 检查是否有环境变量或命令行配置
        has_configs = any([
            config.github_username, 
            config.github_token, 
            config.openai_api_key, 
            config.openai_base_url
        ])
        
        if has_configs:
            # 显示检测到的配置
            self.console.print(f"\n[bold]{self.translator('ui.config.env_detected')}[/bold]")
            
            if config.github_username:
                self.console.print(self.translator('ui.config.github_username', username=config.github_username))
            if config.github_token:
                self.console.print(self.translator('ui.config.github_token', token=self.translator('ui.config.masked_token')))
            if config.openai_api_key:
                self.console.print(self.translator('ui.config.openai_key', key=self.translator('ui.config.masked_key')))
            if config.openai_base_url:
                self.console.print(self.translator('ui.config.openai_url', url=config.openai_base_url))
            
            # 如果指定了跳过确认，直接使用配置
            if args.no_confirm:
                self.console.print(f"\n[green]{self.translator('ui.config.using_env')}[/green]")
                return config
            
            # 询问是否使用检测到的配置
            if Confirm.ask(self.translator('ui.config.use_env')):
                self.console.print(f"\n[green]{self.translator('ui.config.using_env')}[/green]")
                return config
            else:
                self.console.print(f"\n[yellow]{self.translator('ui.config.clear_env')}[/yellow]")
                # 清空配置
                config.github_username = ""
                config.github_token = ""
                config.openai_api_key = ""
                config.openai_base_url = None
        
        # 获取GitHub用户名
        while not config.github_username:
            config.github_username = Prompt.ask(self.translator('ui.input.github_username'))
        
        # 获取GitHub令牌
        self.console.print(f"\n[yellow]{self.translator('ui.input.github_token_notice')}[/yellow]")
        config.github_token = Prompt.ask(self.translator('ui.input.github_token'), default="")
        
        # 获取OpenAI API密钥
        while not config.openai_api_key:
            config.openai_api_key = Prompt.ask(self.translator('ui.input.openai_key'))
        
        # 获取OpenAI API代理URL
        self.console.print(f"\n[yellow]{self.translator('ui.input.openai_url_notice')}[/yellow]")
        base_url = Prompt.ask(self.translator('ui.input.openai_url'), default="")
        if base_url:
            config.openai_base_url = self.normalize_base_url(base_url)
            self.console.print(self.translator('ui.input.url_set', url=config.openai_base_url))
        
        return config

    def display_current_config(self, config: AppConfig) -> None:
        """
        显示当前配置。

        Args:
            config: 配置对象
        """
        self.console.print(f"\n[bold]{self.translator('ui.config.current')}[/bold]")
        self.console.print(self.translator('ui.config.github_username', username=config.github_username))
        
        if config.github_token:
            token_display = '*' * 10 + config.github_token[-4:] if len(config.github_token) > 10 else self.translator('ui.config.masked_token')
            self.console.print(self.translator('ui.config.github_token', token=token_display))
        else:
            self.console.print(self.translator('ui.config.no_github_token'))
        
        key_display = '*' * 10 + config.openai_api_key[-4:] if len(config.openai_api_key) > 10 else self.translator('ui.config.masked_key')
        self.console.print(self.translator('ui.config.openai_key', key=key_display))
        
        if config.openai_base_url:
            self.console.print(self.translator('ui.config.openai_url', url=config.openai_base_url))
        else:
            self.console.print(self.translator('ui.config.default_openai_url'))
        
        self.console.print(self.translator('ui.config.language', 
                                     language_param=get_language_name(config.language, config.language)))
        self.console.print(self.translator('ui.config.output_dir', dir=config.output_dir))

    def confirm_analysis(self, repo_count: int) -> bool:
        """
        确认是否分析仓库。
        
        Args:
            repo_count: 仓库数量
            
        Returns:
            用户是否确认
        """
        # 如果指定了跳过确认，直接返回True
        if hasattr(self, 'args') and self.args.no_confirm:
            return True
            
        return Confirm.ask(
            self.translator('ui.confirmation.analyze_repos', count=repo_count),
            default=True
        )
        
    def confirm_export(self) -> bool:
        """
        确认是否导出结果。
        
        Returns:
            用户是否确认
        """
        # 如果指定了跳过确认，直接返回True
        if hasattr(self, 'args') and self.args.no_confirm:
            return True
            
        return Confirm.ask(
            self.translator('ui.confirmation.export_results'),
            default=True
        )
        
    def should_overwrite_readme(self) -> bool:
        """
        是否应该覆盖README.md文件。
        
        Returns:
            是否覆盖README.md
        """
        return hasattr(self, 'args') and self.args.overwrite_readme
        
    def display_analysis_summary(self, analyzed_repos: List[dict]) -> None:
        """
        显示分析摘要。
        
        Args:
            analyzed_repos: 分析结果列表
        """
        if not analyzed_repos:
            self.console.print(f"[yellow]{self.translator('ui.results.no_repos')}[/yellow]")
            return
            
        # 按类别分组
        categories = {}
        for repo in analyzed_repos:
            category = repo.get("category", self.translator('ui.results.uncategorized'))
            if category not in categories:
                categories[category] = []
            categories[category].append(repo)
            
        # 显示分类摘要
        self.console.print(f"\n[bold green]{self.translator('ui.results.analysis_complete')}[/bold green]")
        
        for category, repos in sorted(categories.items()):
            self.console.print(self.translator('ui.results.category_count', category=category, count=len(repos)))
    
    def display_completion(self, markdown_path: Optional[str], json_path: Optional[str]) -> None:
        """
        显示完成信息。
        
        Args:
            markdown_path: Markdown文件路径
            json_path: JSON文件路径
        """
        self.console.print(f"\n[bold green]{self.translator('ui.completion.success')}[/bold green]")
        self.console.print(f"[cyan]{self.translator('ui.completion.view_results')}[/cyan]")
        
        if markdown_path:
            self.console.print(self.translator('ui.completion.markdown', path=markdown_path))
        if json_path:
            self.console.print(self.translator('ui.completion.json', path=json_path))
            
        self.console.print(f"\n[bold]{self.translator('ui.completion.thank_you')}[/bold]") 