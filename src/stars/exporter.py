"""结果导出模块，用于将分析结果导出为不同格式的文件。"""

import csv
import os
import sys
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
from rich.console import Console
from jinja2 import Environment, FileSystemLoader

from .i18n.languages import Language, get_language_name
from .i18n.translator import get_translator

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建控制台对象
console = Console()


class ResultExporter:
    """结果导出类。"""

    def __init__(self, github_username: str, output_dir: Optional[str] = None, language: str = "zh-CN", template_dir: Optional[str] = None):
        """
        初始化ResultExporter实例。

        Args:
            github_username: GitHub用户名
            output_dir: 输出目录，默认为程序上级目录的'../versions'
            language: 使用的语言
            template_dir: 模板目录，默认为程序目录下的'templates'
        """
        self.github_username = github_username
        
        # 确保language是字符串类型
        if hasattr(language, 'value'):
            language = language.value
            
        self.language = language
        
        # 设置输出目录
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            # 默认为上级目录的'../versions'
            self.output_dir = Path(os.getcwd()) / "../versions"
            
        # 确保输出目录存在
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 设置模板目录
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            self.template_dir = Path(os.getcwd()) / "../templates"
            
        # 创建Jinja2环境
        self.template_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )
        
        # 创建翻译器实例
        self.translator = get_translator(language)
        
        # 初始化输出文件名
        timestamp = datetime.now().strftime("%y.%m.%d")
        self.timestamp = timestamp
        self.file_prefix = f"stars-{self.github_username}-v{self.timestamp}"
        self.latest_file_prefix = f"stars-{self.github_username}-latest"
        
        # 日志调试
        logger.debug(f"ResultExporter initialized with language: {language}")
    
    def update_translator(self) -> None:
        """更新翻译器实例，确保使用最新的语言设置"""
        self.translator = get_translator(self.language)

    def _sort_repos_by_category(self, repos: List[Dict]) -> List[Dict]:
        """
        按照主分类和子分类对仓库列表进行排序。

        Args:
            repos: 仓库信息列表

        Returns:
            排序后的仓库列表
        """
        def get_sort_key(repo: Dict) -> Tuple[str, str]:
            category = repo.get("category", self.translator.get_output_translation('ui.results.uncategorized'))
            subcategory = repo.get("subcategory", "")
            return (category, subcategory)

        return sorted(repos, key=get_sort_key)

    def export_markdown(self, analyzed_repos: List[Dict], template_name: str = "github.md", overwrite_readme: bool = False) -> Optional[str]:
        """
        将分析结果导出为Markdown格式。

        Args:
            analyzed_repos: 分析后的仓库信息列表
            template_name: 使用的模板文件名，默认为'default.md'
            overwrite_readme: 是否覆盖根目录的README.md文件

        Returns:
            输出文件路径，如果出错则返回None
        """
        # 更新翻译器，确保使用最新的语言设置
        self.update_translator()
        
        # 对仓库列表进行排序
        sorted_repos = self._sort_repos_by_category(analyzed_repos)
        
        # 按类别分组
        groups = {}
        for repo in sorted_repos:
            category = repo.get("category", self.translator.get_output_translation('ui.results.uncategorized'))
            if category not in groups:
                groups[category] = []
            groups[category].append(repo)

        # 准备模板数据
        template_data = {
            "title": self.translator.get_output_translation('export.md.title'),
            "slogan": self.translator.get_output_translation('export.md.slogan'),
            "generated_by": self.translator.get_output_translation('export.md.generated_by', date=datetime.now().strftime('%Y/%m/%d'), username=self.github_username),
            "github_username": self.github_username,
            "generated_at": datetime.now().strftime('%Y/%m/%d'),
            "groups": groups,
            "last_updated": self.translator.get_output_translation('export.md.last_updated'),
            "created_at": self.translator.get_output_translation('export.md.created_at'),
            "last_pushed": self.translator.get_output_translation('export.md.last_pushed'),
            "license": self.translator.get_output_translation('export.md.license'),
            "topics": self.translator.get_output_translation('export.md.topics'),
            "github_pages": self.translator.get_output_translation('export.md.github_pages'),
            "none": self.translator.get_output_translation('export.md.none'),
            "table_of_contents": self.translator.get_output_translation('export.md.table_of_contents'),
            "tech_stack": self.translator.get_output_translation('export.md.tech_stack'),
            "keywords": self.translator.get_output_translation('export.md.keywords'),
            "about_title": self.translator.get_output_translation('export.md.about.title'),
            "about_description": self.translator.get_output_translation('export.md.about.description'),
            "about_subtitle": self.translator.get_output_translation('export.md.about.subtitle'),
        }

        # 渲染模板
        try:
            template = self.template_env.get_template(template_name)
            md_content = template.render(**template_data)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            console.print(self.translator('ui.export.template_error', error=str(e)))
            return None

        # 写入文件
        output_file = self.output_dir / f"{self.file_prefix}.md"
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(md_content)
                
            # 创建latest版本文件
            latest_file = self.output_dir / f"{self.latest_file_prefix}.md"
            shutil.copy2(output_file, latest_file)
            
            # 如果指定了覆盖README.md，则复制到根目录
            if overwrite_readme:
                try:
                    root_readme = Path(os.getcwd()) / "../README.md"
                    shutil.copy2(latest_file, root_readme)
                    console.print(self.translator('ui.export.readme_overwrite_success'))
                except Exception as e:
                    console.print(self.translator('ui.export.readme_overwrite_error', error=str(e)))
                    logger.error(f"Error overwriting README.md: {e}")
                
            # 显示成功消息
            console.print(self.translator('ui.export.markdown_success', path=output_file))
            return str(output_file)
        except (PermissionError, OSError) as e:
            # 显示错误消息
            console.print(self.translator('ui.export.export_error', path=output_file))
            console.print(self.translator('ui.export.export_error_reason', reason=str(e)))
            console.print(self.translator('ui.export.export_error_tip'))
            logger.error(f"Error exporting to Markdown: {e}")
            return None

    def export_json(self, analyzed_repos: List[Dict]) -> Optional[str]:
        """
        将分析结果导出为JSON格式。

        Args:
            analyzed_repos: 分析后的仓库信息列表

        Returns:
            输出文件路径，如果出错则返回None
        """
        # 更新翻译器，确保使用最新的语言设置
        self.update_translator()
        
        # 对仓库列表进行排序
        sorted_repos = self._sort_repos_by_category(analyzed_repos)
        
        # 准备JSON数据
        data = []
        for repo in sorted_repos:
            data.append({
                # 主要识别信息
                "full_name": repo.get("full_name", ""),
                "name": repo.get("name", ""),
                "id": repo.get("id", ""),
                "html_url": repo.get("html_url", ""),
                
                # 分类和描述信息
                "category": repo.get("category", self.translator.get_output_translation('ui.results.uncategorized')),
                "subcategory": repo.get("subcategory", ""),
                "description": repo.get("description", ""),
                "ai_description": repo.get("ai_description", ""),
                
                # 编程语言信息
                "git_language": repo.get("git_language", ""),
                "primary_language": repo.get("primary_language", ""),
                "secondary_language": repo.get("secondary_language", ""),
                
                # 重要统计指标
                "stargazers_count": repo.get("stargazers_count", 0),
                "forks_count": repo.get("forks_count", 0),
                "watchers_count": repo.get("watchers_count", 0),
                "open_issues_count": repo.get("open_issues_count", 0),
                
                # 时间信息
                "created_at": repo.get("created_at", ""),
                "updated_at": repo.get("updated_at", ""),
                "pushed_at": repo.get("pushed_at", ""),
                
                # 许可证信息
                "license_name": repo.get("license_name", ""),
                "license_spdx_id": repo.get("license_spdx_id", ""),
                "license_url": repo.get("license_url", ""),
                
                # 标签
                "topics": repo.get("topics", ""),
                
                # 其他属性
                "fork": repo.get("fork", False),
                "size": repo.get("size", 0),
                "is_template": repo.get("is_template", False),
                "has_github_pages": repo.get("has_github_pages", False),
                "github_pages_url": repo.get("github_pages_url", ""),
                "homepage": repo.get("homepage", ""),
                "confidence": repo.get("confidence", ""),
                
                # 元信息
                "language": self.language,
                
                # 大文本内容始终放在最后
                "readme": repo.get("readme", ""),
            })

        # 导出到JSON，直接使用原始字段名，不进行国际化处理
        output_file = self.output_dir / f"{self.file_prefix}.json"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 创建latest版本文件
            latest_file = self.output_dir / f"{self.latest_file_prefix}.json"
            shutil.copy2(output_file, latest_file)
            
            # 显示成功消息
            console.print(self.translator('ui.export.json_success', path=output_file))
            return str(output_file)
        except (PermissionError, OSError) as e:
            # 显示错误消息
            console.print(self.translator('ui.export.export_error', path=output_file))
            console.print(self.translator('ui.export.export_error_reason', reason=str(e)))
            console.print(self.translator('ui.export.export_error_tip'))
            logger.error(f"Error exporting to JSON: {e}")
            return None 