"""应用主逻辑模块，集成其他模块完成整个程序流程。"""

import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .cli import CLI
from .config import AppConfig
from .exporter import ResultExporter
from .github_api import GitHubAPI
from .openai_api import OpenAIAnalyzer
from .i18n.languages import Language
from .i18n.translator import get_translator

# 设置日志记录器
logger = logging.getLogger(__name__)


class Application:
    """应用主类。"""

    def __init__(self):
        """初始化Application实例。"""
        self.cli = CLI()
        self.config = None
        self.github_api = None
        self.openai_analyzer = None
        self.exporter = None
        self.translator = None
        self.language = None

    def setup(self) -> None:
        """设置应用程序。"""
        # 获取用户配置
        self.config = self.cli.get_user_config()
        
        # 获取语言值
        language = self.config.language
        if hasattr(language, 'value'):
            language = language.value
        
        # 保存语言值为实例属性
        self.language = language
        
        # 获取全局翻译器实例
        self.translator = get_translator(language)
        # 设置英语为降级语言
        self.translator.set_fallback_languages(["en"])
        
        # 初始化API客户端，传递翻译器实例而不是重新创建
        self.github_api = GitHubAPI(
            self.config.github_username, 
            self.config.github_token,
            language=language
        )
        self.openai_analyzer = OpenAIAnalyzer(
            self.config.openai_api_key,
            self.config.openai_base_url,
            language=language
        )
        
        # 初始化导出器
        self.exporter = ResultExporter(
            self.config.github_username,
            self.config.output_dir,
            language=language,
        )

    def fetch_starred_repos(self) -> List[Dict]:
        """
        获取用户的Starred仓库。

        Returns:
            仓库列表
        """
        return self.github_api.get_starred_repos()

    def enrich_repo_data(self, repos: List[Dict], cached_results=None) -> List[Dict]:
        """
        丰富仓库数据。

        Args:
            repos: 基础仓库信息列表
            cached_results: 缓存的仓库结果，以仓库full_name为键

        Returns:
            丰富后的仓库信息列表
        """
        # 首先获取基本仓库信息
        enriched_repos = self.github_api.enrich_repo_data(repos)
        
        # 然后获取README内容，传递缓存结果
        enriched_repos = self.github_api.get_repos_readme(enriched_repos, cached_results)
        
        return enriched_repos

    def analyze_repos(self, repos: List[Dict]) -> List[Dict]:
        """
        分析仓库信息。

        Args:
            repos: 仓库信息列表

        Returns:
            分析结果列表
        """
        return self.openai_analyzer.analyze_repos(repos)

    def export_results(self, analyzed_repos: List[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """
        导出分析结果。
        
        Args:
            analyzed_repos: 分析后的仓库信息列表
            
        Returns:
            导出的Markdown和JSON文件路径
        """
        # 检查是否需要导出
        if not self.cli.confirm_export():
            return None, None
            
        # 导出Markdown
        markdown_path = self.exporter.export_markdown(
            analyzed_repos,
            overwrite_readme=self.cli.should_overwrite_readme()
        )
        
        # 导出JSON
        json_path = self.exporter.export_json(analyzed_repos)
        
        return markdown_path, json_path

    def run(self) -> None:
        """运行应用程序。"""
        # 设置应用
        self.setup()
        
        try:
            # 加载缓存的分析结果
            cached_results = self.load_cached_results()
            
            # 获取Starred仓库
            repos = self.fetch_starred_repos()
            
            # 检查是否有获取到仓库
            if not repos:
                self.cli.console.print(f"[red]{self.translator('ui.error.no_repos')}[/red]")
                return
            
            # 获取更多仓库详情，传递缓存结果来优化README获取
            enriched_repos = self.enrich_repo_data(repos, cached_results)
            
            # 筛选需要重新分析的仓库
            analyzed_repos = []
            analysis_time = 0
            
            # 将仓库分为需要分析和已有缓存结果的两部分
            to_analyze = []
            from_cache = []
            
            for repo in enriched_repos:
                full_name = repo.get("full_name", "")
                pushed_at = repo.get("pushed_at", "")
                
                # 检查是否在缓存中且更新时间和language字段都相同
                if (full_name in cached_results and 
                    cached_results[full_name].get("pushed_at", "") == pushed_at and
                    cached_results[full_name].get("language", "") == self.language):
                    # 复用缓存的分析结果
                    cached_repo = cached_results[full_name]
                    
                    # 确保有基本的分类信息
                    if cached_repo.get("category"):
                        # 合并原始数据和缓存的分析结果
                        merged_repo = {**repo}
                        
                        # 添加分析字段
                        for field in ["category", "subcategory", "ai_description", 
                                     "primary_language", "secondary_language", "confidence"]:
                            if field in cached_repo and cached_repo[field]:
                                merged_repo[field] = cached_repo[field]
                        
                        from_cache.append(merged_repo)
                        continue
                
                # 需要重新分析
                to_analyze.append(repo)
            
            # 显示缓存使用情况
            if from_cache:
                self.cli.console.print(
                    f"[green]{self.translator('cache.reused', count=len(from_cache), total=len(enriched_repos))}[/green]")
            
            # 分析需要更新的仓库
            if to_analyze:
                self.cli.console.print(f"[cyan]{self.translator('cache.analyzing_new', count=len(to_analyze))}[/cyan]")
                start_time = time.time()
                newly_analyzed = self.analyze_repos(to_analyze)
                analysis_time = time.time() - start_time
                analyzed_repos.extend(newly_analyzed)
            
            # 添加缓存的结果
            if from_cache:
                self.cli.console.print(f"[cyan]{self.translator('cache.using_cached', count=len(from_cache))}[/cyan]")
                analyzed_repos.extend(from_cache)
            
            # 显示分析摘要
            self.cli.display_analysis_summary(analyzed_repos)
            
            # 显示平均分析时间
            if to_analyze:
                avg_time = analysis_time / len(to_analyze) if to_analyze else 0
                avg_time_text = self.translator('ui.results.avg_time', time=f"{avg_time:.2f}")
                self.cli.console.print(avg_time_text)
            
            # 导出结果
            markdown_path, json_path = self.export_results(analyzed_repos)
            
            # 检查是否有导出成功的文件
            if not markdown_path and not json_path:
                self.cli.console.print(f"[red]{self.translator('ui.export.all_failed')}[/red]")
                return
            
            # 显示完成信息
            self.cli.display_completion(markdown_path, json_path)
            
        except Exception as e:
            self.cli.console.print(f"[red]{self.translator('ui.error.program_error', error=str(e))}[/red]")
            logger.error(f"程序运行出错: {e}", exc_info=True)

    def load_cached_results(self) -> Dict[str, Dict]:
        """
        从最新的JSON文件加载缓存的仓库分析结果。

        Returns:
            已缓存的仓库分析结果字典，以仓库全名为键
        """
        cached_results = {}
        
        # 构建最新JSON文件路径
        latest_json_path = Path(self.config.output_dir) / f"stars-{self.config.github_username}-latest.json"
        
        if not latest_json_path.exists():
            self.cli.console.print(f"[yellow]{self.translator('cache.no_cache_found')}[/yellow]")
            return cached_results
            
        try:
            with open(latest_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 将数据转换为以仓库全名为键的字典，方便查询
            for repo in data:
                # 在JSON导出中，仓库的完整名称储存在name字段中
                full_name = repo.get("full_name", "")
                if full_name:
                    # 确保日期格式一致性
                    if "updated_at" in repo and repo["updated_at"]:
                        # 去除可能的前后空格
                        repo["updated_at"] = repo["updated_at"].strip()
                    cached_results[full_name] = repo
                    
            self.cli.console.print(f"[green]{self.translator('cache.loaded', count=len(cached_results))}[/green]")
        except Exception as e:
            self.cli.console.print(f"[yellow]{self.translator('cache.load_error', error=str(e))}[/yellow]")
            
        return cached_results