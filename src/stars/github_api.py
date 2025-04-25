"""GitHub API交互模块，用于获取用户的Starred仓库信息。"""

import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import requests
from rich.console import Console
from rich.progress import Progress
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    RetryError
)

from .i18n.translator import get_translator
from .i18n.languages import Language

console = Console()


class GitHubAPI:
    """GitHub API交互类。"""

    BASE_URL = "https://api.github.com"
    STARRED_ENDPOINT = "/users/{username}/starred"
    USER_ENDPOINT = "/users/{username}"
    README_ENDPOINT = "/repos/{owner}/{repo}/readme"

    def __init__(self, username: str, token: Optional[str] = None, language: str = Language.EN):
        """
        初始化GitHubAPI实例。

        Args:
            username: GitHub用户名
            token: GitHub个人访问令牌 (可选)
            language: 使用的语言
        """
        self.username = username
        self.token = token
        self.language = language
        self.translator = get_translator(language)
        
        # 设置请求头
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        
        if token:
            self.headers["Authorization"] = f"token {token}"
            
        # 验证用户名和令牌
        try:
            self._validate_credentials()
        except Exception as e:
            self._handle_validation_error(e)

    def _validate_credentials(self):
        """验证GitHub用户名和令牌的有效性。"""
        try:
            user_url = f"{self.BASE_URL}{self.USER_ENDPOINT.format(username=self.username)}"
            response = requests.get(user_url, headers=self.headers)
            
            if response.status_code == 404:
                raise ValueError(f"GitHub用户名 '{self.username}' 不存在")
                
            if response.status_code == 401:
                raise ValueError("GitHub个人访问令牌无效或已过期")
                
            response.raise_for_status()
            
            # 获取API限制信息
            rate_limit = {
                "limit": int(response.headers.get("X-RateLimit-Limit", 0)),
                "remaining": int(response.headers.get("X-RateLimit-Remaining", 0)),
                "reset": int(response.headers.get("X-RateLimit-Reset", 0)),
            }
            
            if not self.token and rate_limit["limit"] <= 60:
                console.print("[yellow]警告: 正在使用匿名访问，API请求限制较低，建议提供GitHub令牌以提高限制[/yellow]")
                
        except requests.exceptions.ConnectionError:
            raise ConnectionError("无法连接到GitHub服务器，请检查网络连接")
        except requests.exceptions.Timeout:
            raise TimeoutError("连接GitHub服务器超时，请稍后重试")
        except requests.exceptions.RequestException as e:
            raise Exception(f"验证GitHub凭据时发生错误: {str(e)}")

    def _handle_validation_error(self, error):
        """处理验证错误并提供友好提示。"""
        error_msg = str(error)
        
        if "不存在" in error_msg:
            console.print(f"[red]错误: {error_msg}[/red]")
            console.print("[yellow]请检查GitHub用户名是否拼写正确[/yellow]")
        elif "令牌无效" in error_msg or "已过期" in error_msg:
            console.print(f"[red]错误: {error_msg}[/red]")
            console.print("[yellow]可能的原因:[/yellow]")
            console.print("  1. 令牌输入错误")
            console.print("  2. 令牌已过期")
            console.print("  3. 令牌已被撤销")
            console.print("[green]建议:[/green]")
            console.print("  1. 检查令牌是否正确复制")
            console.print("  2. 在GitHub设置中验证令牌状态")
            console.print("  3. 如需要，创建新的个人访问令牌")
        elif "网络连接" in error_msg:
            console.print(f"[red]错误: {error_msg}[/red]")
            console.print("[yellow]请检查您的网络连接并重试[/yellow]")
        else:
            console.print(f"[red]初始化GitHub API客户端时发生错误: {error_msg}[/red]")
        
        console.print("[red]程序无法继续执行，请修正问题后重试[/red]")
        sys.exit(1)

    @retry(
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Tuple[Dict, Dict]:
        """
        发送API请求并处理速率限制。

        Args:
            url: 请求URL
            params: 请求参数

        Returns:
            请求结果和速率限制信息
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            # 处理特定的HTTP错误
            if response.status_code == 404:
                console.print(f"[red]错误: 请求的资源不存在 ({url})[/red]")
                return [], {}
            elif response.status_code == 401:
                console.print("[red]错误: 认证失败，GitHub令牌可能已失效[/red]")
                console.print("[yellow]请检查您的GitHub令牌并重新运行程序[/yellow]")
                sys.exit(1)
            elif response.status_code == 403 and "rate limit exceeded" in response.text.lower():
                reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                wait_seconds = max(0, reset_time - int(time.time()))
                reset_time_str = datetime.fromtimestamp(reset_time).strftime("%Y-%m-%d %H:%M:%S")
                
                console.print(f"[yellow]GitHub API速率限制已达到，限制将在 {reset_time_str} (约 {wait_seconds // 60} 分钟后) 重置[/yellow]")
                
                if wait_seconds > 300:  # 如果等待时间超过5分钟
                    console.print("[red]等待时间过长，程序将退出[/red]")
                    console.print("[green]提示: 使用GitHub个人访问令牌可以提高API限制[/green]")
                    sys.exit(1)
                
                console.print(f"[yellow]等待 {wait_seconds} 秒后继续...[/yellow]")
                time.sleep(wait_seconds + 2)  # 额外等待2秒确保限制解除
                return self._make_request(url, params)  # 重新尝试请求
                
            # 其他错误
            response.raise_for_status()

            rate_limit = {
                "limit": int(response.headers.get("X-RateLimit-Limit", 0)),
                "remaining": int(response.headers.get("X-RateLimit-Remaining", 0)),
                "reset": int(response.headers.get("X-RateLimit-Reset", 0)),
            }

            # 处理速率限制
            if rate_limit["remaining"] == 0:
                reset_time = datetime.fromtimestamp(rate_limit["reset"])
                sleep_time = (reset_time - datetime.now()).total_seconds()
                if sleep_time > 0:
                    console.print(f"[yellow]API速率限制已达到，等待{sleep_time:.1f}秒后继续...[/yellow]")
                    time.sleep(sleep_time + 1)  # 额外等待1秒以确保限制解除

            return response.json(), rate_limit
            
        except requests.exceptions.ConnectionError:
            console.print("[yellow]警告: 连接GitHub服务器失败，正在重试...[/yellow]")
            raise  # 让retry装饰器处理重试
        except requests.exceptions.Timeout:
            console.print("[yellow]警告: 请求GitHub API超时，正在重试...[/yellow]")
            raise  # 让retry装饰器处理重试
        except requests.exceptions.HTTPError as e:
            console.print(f"[red]请求失败 ({url}): {str(e)}[/red]")
            raise
        except Exception as e:
            console.print(f"[red]发送GitHub API请求时发生未知错误: {str(e)}[/red]")
            return [], {}

    def get_starred_repos(self) -> List[Dict]:
        """
        获取用户所有的Starred仓库。

        Returns:
            仓库列表，每个仓库包含相关信息
        """
        self.update_translator()
        
        all_repos = []
        page = 1
        per_page = 100 # GitHub API最大每页数量

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{self.translator('ui.progress.fetching_repos')}", 
                total=None
            )

            try:
                while True:
                    params = {"page": page, "per_page": per_page, "sort": "created", "direction": "desc"}
                    url = f"{self.BASE_URL}{self.STARRED_ENDPOINT.format(username=self.username)}"

                    try:
                        repos, _ = self._make_request(url, params)
                        if not repos:
                            break

                        # 首次获取时更新总任务数
                        if page == 1:
                            # 初始估计值
                            progress.update(task, total=len(repos) * 10)

                        all_repos.extend(repos)
                        progress.update(
                            task,
                            advance=len(repos),
                            description=f"[cyan]{self.translator('ui.progress.fetched_repos', count=len(all_repos), latest=repos[0]['full_name'] if repos else '')}",
                        )

                        if len(repos) < per_page:
                            break

                        page += 1
                    except Exception as e:
                        console.print(f"[red]{self.translator('ui.error.fetch_page_error', page=page, error=str(e))}[/red]")
                        break

                # 更新最终的任务进度
                progress.update(task, completed=len(all_repos), total=len(all_repos))
                
                if not all_repos:
                    console.print(f"[yellow]{self.translator('ui.error.no_starred_repos', username=self.username)}[/yellow]")
                
            except RetryError:
                console.print(f"[red]{self.translator('ui.error.fetch_repos_retry_failed')}[/red]")
                sys.exit(1)
            except Exception as e:
                console.print(f"[red]{self.translator('ui.error.fetch_repos_error', error=str(e))}[/red]")
                sys.exit(1)

        return all_repos

    def enrich_repo_data(self, repos: List[Dict]) -> List[Dict]:
        """
        处理仓库数据，确保包含所有必要字段并将topics转为逗号连接的字符串格式。
        只处理公开（public）仓库，跳过私有仓库。

        Args:
            repos: 基础仓库信息列表

        Returns:
            处理后的仓库信息列表
        """
        self.update_translator()
        
        # 过滤掉私有仓库，只保留公开仓库
        public_repos = [repo for repo in repos if repo.get("visibility") != "private"]
        console.print(f"[cyan]{self.translator('ui.info.filtered_private', total=len(repos), public=len(public_repos))}[/cyan]")
        
        processed_repos = []

        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{self.translator('ui.progress.processing_data')}", 
                total=len(public_repos)
            )

            for repo in public_repos:
                try:
                    # 创建新的结构，只包含必要的字段
                    processed_repo = {
                        "id": repo.get("id", 0),
                        "name": repo.get("name", ""),
                        "full_name": repo.get("full_name", ""),
                        "html_url": repo.get("html_url", ""),
                        "description": repo.get("description", ""),
                        "fork": repo.get("fork", False),
                        "created_at": repo.get("created_at", ""),
                        "updated_at": repo.get("updated_at", ""),
                        "pushed_at": repo.get("pushed_at", ""),
                        "homepage": repo.get("homepage", ""),
                        "size": repo.get("size", 0),
                        "stargazers_count": repo.get("stargazers_count", 0),
                        "watchers_count": repo.get("watchers_count", 0),
                        "forks_count": repo.get("forks_count", 0),
                        "open_issues_count": repo.get("open_issues_count", 0),
                        "git_language": repo.get("language", ""),
                        "is_template": repo.get("is_template", False),
                        "has_github_pages": repo.get("has_pages", False)
                    }
                    
                    # 添加GitHub Pages信息
                    if processed_repo["has_github_pages"]:
                        owner, name = processed_repo["full_name"].split("/")
                        processed_repo["github_pages_url"] = f"https://{owner}.github.io/{name}"
                    else:
                        processed_repo["github_pages_url"] = ""

                    # 处理license信息
                    if "license" in repo and repo["license"] and isinstance(repo["license"], dict):
                        processed_repo["license_name"] = repo["license"].get("name", "")
                        processed_repo["license_spdx_id"] = repo["license"].get("spdx_id", "")
                        processed_repo["license_url"] = repo["license"].get("url", "")
                    else:
                        processed_repo["license_name"] = ""
                        processed_repo["license_spdx_id"] = ""
                        processed_repo["license_url"] = ""
                    
                    # 处理topics信息
                    if "topics" in repo and isinstance(repo["topics"], list):
                        processed_repo["topics"] = ",".join(repo["topics"])
                    else:
                        processed_repo["topics"] = ""

                    processed_repos.append(processed_repo)

                except Exception as e:
                    console.print(f"[red]{self.translator('ui.error.process_data_error', repo=repo.get('full_name', self.translator('ui.error.unknown')), error=str(e))}[/red]")
                    # 创建简化的错误仓库信息
                    error_repo = {
                        "id": repo.get("id", 0),
                        "full_name": repo.get("full_name", "未知仓库"),
                        "html_url": repo.get("html_url", ""),
                        "error": str(e)
                    }
                    processed_repos.append(error_repo)

                progress.update(task, advance=1)

        return processed_repos

    def update_translator(self) -> None:
        """更新翻译器实例"""
        self.translator = get_translator(self.language) 

    def get_repo_readme(self, owner: str, repo: str) -> str:
        """
        获取仓库的README内容。

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README内容，如果获取失败则返回空字符串
        """
        try:
            url = f"{self.BASE_URL}{self.README_ENDPOINT.format(owner=owner, repo=repo)}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 404:
                return ""
                
            response.raise_for_status()
            data = response.json()
            
            # GitHub API返回的是base64编码的内容
            import base64
            content = base64.b64decode(data.get("content", "")).decode("utf-8")
            return content
            
        except Exception as e:
            console.print(f"[yellow]获取仓库 {owner}/{repo} 的README失败: {str(e)}[/yellow]")
            return ""

    def get_repos_readme(self, repos: List[Dict], cached_results=None) -> List[Dict]:
        """
        并行获取多个仓库的README内容。
        如果提供了缓存结果，且仓库在缓存中且pushed_at相同，则直接使用缓存的README。

        Args:
            repos: 仓库信息列表
            cached_results: 缓存的仓库结果，以仓库full_name为键

        Returns:
            添加了README内容的仓库信息列表
        """
        self.update_translator()
        
        # 如果未提供缓存结果，初始化为空字典
        if cached_results is None:
            cached_results = {}
            
        # 筛选需要获取README的仓库
        repos_to_fetch = []
        cached_count = 0
        
        for repo in repos:
            full_name = repo.get("full_name", "")
            pushed_at = repo.get("pushed_at", "")
            
            # 检查是否在缓存中且pushed_at相同
            if (full_name in cached_results and 
                cached_results[full_name].get("pushed_at", "") == pushed_at and
                "readme" in cached_results[full_name]):
                # 直接使用缓存的README
                repo["readme"] = cached_results[full_name]["readme"]
                cached_count += 1
            else:
                # 需要重新获取README
                repos_to_fetch.append(repo)
                
        if not repos_to_fetch:
            console.print(f"[green]{self.translator('cache.readme_all_cached', total=len(repos))}[/green]")
            return repos
            
        # 输出缓存使用情况的汇总信息
        if cached_count > 0:
            console.print(f"[green]{self.translator('cache.readme_summary', cached=cached_count, total=len(repos), fetch=len(repos_to_fetch))}[/green]")
        
        # 根据仓库数量动态调整并行数
        if len(repos_to_fetch) > 100:
            max_workers = 20
        elif len(repos_to_fetch) > 50:
            max_workers = 10
        else:
            max_workers = 5
            
        console.print(f"[cyan]{self.translator('ui.progress.fetching_readme_count', count=len(repos_to_fetch))}[/cyan]")
        
        with Progress() as progress:
            task = progress.add_task(
                f"[cyan]{self.translator('ui.progress.fetching_readme')}", 
                total=len(repos_to_fetch)
            )
            
            # 使用线程池进行并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_repo = {
                    executor.submit(
                        self.get_repo_readme,
                        repo["full_name"].split("/")[0],
                        repo["full_name"].split("/")[1]
                    ): repo for repo in repos_to_fetch
                }
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_repo):
                    repo = future_to_repo[future]
                    try:
                        # 获取README内容
                        readme_content = future.result()
                        # 添加README内容到仓库信息中
                        repo["readme"] = readme_content
                        
                    except Exception as e:
                        console.print(f"[red]处理仓库 {repo.get('full_name', 'Unknown')} 的README时出错: {str(e)}[/red]")
                        repo["readme"] = ""
                        
                    progress.update(task, advance=1)
                    
        return repos 