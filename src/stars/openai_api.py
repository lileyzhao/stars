"""OpenAI API交互模块，用于分析仓库信息并进行分类。"""

import json
import sys
import time
import logging
from typing import Dict, List, Optional
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

import openai
import requests
from rich.console import Console
from rich.progress import Progress
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    RetryError,
)

from .i18n.languages import Language
from .i18n.translator import Translator, get_translator

# 设置日志记录器
logger = logging.getLogger(__name__)

# 创建控制台对象
console = Console()

# 统一中文提示模板，使用占位符支持多语言
SYSTEM_PROMPT = "你是一个专业的GitHub仓库分析专家，擅长对仓库进行分类整理。请充分利用你已有的GitHub知识库。当分析仓库时，如果你认识这个项目或类似项目，应当应用你对它的已有知识，而不仅仅依赖提供的描述。"

USER_PROMPT = """请分析以下GitHub仓库信息，将其归类到最合适的类别中。
仓库名: {full_name}
仓库URL: {html_url}
仓库描述: {description}
Star数: {stargazers_count}
最后提交时间: {pushed_at}
仓库主题标签: {topics}

以下是该仓库的README内容，包含项目的详细说明、功能特性、技术栈和使用方法等信息，请将其作为分析的重要依据：
```
{readme}
```
注意：README可能较长，请重点关注其中的项目概述、主要功能、技术栈、架构说明和典型用例等关键信息。

在分析过程中：
1. 首先确认是否是你已知的GitHub项目，利用你对该项目或同类项目的专业知识
2. 遵循行业公认的标准分类体系，不要创造非标准分类
3. 对于开发工具类，区分：编辑器/IDE、构建工具、调试工具、AI辅助工具、DevOps工具、代码分析工具等
4. 对于框架类，明确区分：前端框架、后端框架、全栈框架、移动开发框架等
5. 对于AI/ML项目，细分为：模型框架、数据处理、AI应用、AI辅助工具、大语言模型等
6. 对于区块链/Web3项目，区分：智能合约平台、DeFi应用、钱包工具、NFT相关、区块链基础设施等
7. 对于安全工具，区分：漏洞扫描、渗透测试、加密工具、安全审计、身份验证系统等
8. 对于游戏开发项目，区分：游戏引擎、物理引擎、渲染工具、游戏框架、游戏服务端等
9. 对于数据科学项目，区分：数据分析库、可视化工具、统计分析、大数据处理框架等
10. 对于物联网项目，区分：设备管理平台、IoT协议实现、边缘计算框架、嵌入式系统工具等
11. 对于系统工具，区分：操作系统组件、虚拟化工具、系统优化工具、底层库等
12. 对于多媒体处理项目，区分：音频处理、视频处理、图像处理、媒体转码工具等
13. 对于企业应用，区分：CRM、ERP、CMS、电子商务平台、协作工具等
14. 对于模糊边界项目，优先考虑其主要用途和核心技术特点
15. 参考项目的Star数量和更新时间评估其在领域内的影响力和活跃度
16. 考虑项目在开发者社区中的定位和典型用例
主要类别参考(不限于此)：
- 开发工具: IDE、编辑器、AI代码助手、代码生成、调试工具、构建工具、包管理器、CI/CD、测试框架、DevOps工具、文档工具、代码分析、版本控制工具
- 编程语言: 语言实现、标准库、第三方库、编译器、解释器、代码转换器、语言服务器、语法分析
- 前端: UI框架、CSS框架、组件库、状态管理、路由管理、构建工具、Web组件、动画库、表单处理、响应式设计、Web Assembly应用
- 后端: API框架、微服务框架、服务器、中间件、身份认证、授权、消息队列、缓存系统、任务调度、WebSocket、RPC框架
- 数据库: SQL数据库、NoSQL数据库、图数据库、时序数据库、内存数据库、ORM工具、数据迁移、数据管理、数据库代理
- 人工智能: 机器学习框架、深度学习、强化学习、LLM模型、生成式AI、AI应用、MLOps工具、神经网络、自然语言处理、计算机视觉、AI训练工具
- 基础设施: 云原生、容器化、容器编排、服务网格、无服务器架构、基础设施即代码、监控系统、日志管理、分布式系统
- 移动开发: iOS开发、Android开发、跨平台框架、移动UI库、移动数据存储、移动测试、App构建工具
- 安全工具: 漏洞扫描、渗透测试、加密库、安全审计、身份验证、SAST/DAST工具、安全合规
- 区块链/Web3: 智能合约、DeFi、NFT、钱包、链开发工具、共识算法、Web3框架、去中心化应用
- 游戏开发: 游戏引擎、物理引擎、游戏AI、3D渲染、游戏服务器、游戏资源管理
- 物联网(IoT): 设备管理、IoT协议、边缘计算、嵌入式系统、传感器集成、IoT平台
- 数据科学: 数据分析、数据处理、数据可视化、统计分析、科学计算、大数据工具、ETL工具
- 系统工具: 操作系统、虚拟化、系统管理、文件系统、进程管理、性能分析
- 多媒体处理: 音频处理、视频处理、图像处理、媒体转码、流媒体
- 开发者体验: CLI工具、代码生成器、脚手架工具、文档生成、API设计工具
- 企业应用: CRM系统、ERP系统、CMS系统、电子商务平台、内容管理

返回JSON格式，包含以下字段(必须使用 {language} 语言):
1. category: 仓库所属的主要类别名称（必须使用 {language} 语言）
2. subcategory: 仓库所属的子类别名称，如果没有则返回空字符串（必须使用 {language} 语言）
3. primary_language: 仓库的核心编程语言或技术框架（如全栈应用中的后端语言，例如ASP.NET Core+Vue项目中的C#）
4. secondary_language: 仓库使用的主要次要编程语言或框架（如全栈应用中的前端技术，例如Vue、React、Angular等）
5. description: 一句话描述这个仓库的主要用途和特点（必须使用 {language} 语言）
6. ai_description: 基于你的分析和行业知识，对这个仓库的功能、技术特点和价值的总结描述（必须使用 {language} 语言，1-2句话）
7. confidence: 分类结果的确信度，用0-100%的百分比表示对分类准确性的信心程度

你的回答必须是有效的JSON格式，不要包含其他任何文字。
"""

class OpenAIAnalyzer:
    """OpenAI API分析类。"""

    def __init__(self, api_key: str, base_url: Optional[str] = None, language: Language = Language.EN, skip_validation: bool = False):
        """
        初始化OpenAIAnalyzer实例。

        Args:
            api_key: OpenAI API密钥
            base_url: OpenAI API基础URL（可选）
            language: 使用的语言
            skip_validation: 是否跳过API验证（仅用于测试）
        """
        self.api_key = api_key
        self.base_url = base_url
        
        # 确保language是字符串类型
        if isinstance(language, Language) or hasattr(language, 'value'):
            self.language = language
            language_code = language.value
        else:
            self.language = language
            language_code = language
            
        self.last_request_time = 0
        self.request_interval = 1.0  # 请求间隔，秒
        
        # 使用全局翻译器实例
        self.translator = get_translator(language_code)
        # 设置英语为降级语言
        self.translator.set_fallback_languages(["en"])
        
        # 初始化OpenAI客户端
        if not skip_validation:
            try:
                self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
                # 验证API密钥和连接
                self._validate_api_connection()
            except Exception as e:
                self._handle_initialization_error(e)
        else:
            # 测试模式，不初始化客户端
            self.client = None
            
    def update_translator(self) -> None:
        """在每次API调用前更新翻译器，确保使用当前的语言"""
        self.translator = get_translator(self.language)

    def _validate_api_connection(self):
        """验证API连接和密钥是否有效。"""
        try:
            # 尝试发送一个简单的模型列表请求来验证连接
            self.client.models.list()
        except openai.AuthenticationError:
            raise ValueError(self.translator('ui.error.openai_key_invalid'))
        except (openai.APIConnectionError, requests.exceptions.ConnectionError):
            base_url_msg = f"'{self.base_url}'" if self.base_url else self.translator('ui.config.default_openai_url')
            raise ConnectionError(self.translator('ui.error.connection_error', url=base_url_msg))
        except Exception as e:
            raise Exception(self.translator('ui.error.initialization_error', error=str(e)))

    def _handle_initialization_error(self, error):
        """处理初始化错误并提供友好提示。"""
        error_msg = str(error)
        
        if "Invalid API key" in error_msg or isinstance(error, openai.AuthenticationError):
            console.print(f"[red]{self.translator('ui.error.openai_key_invalid')}[/red]")
            console.print(f"[yellow]{self.translator('ui.error.openai_key_check')}[/yellow]")
        elif "Connection" in error_msg or "connect" in error_msg.lower() or isinstance(error, (openai.APIConnectionError, requests.exceptions.ConnectionError)):
            base_url_msg = f"'{self.base_url}'" if self.base_url else self.translator('ui.config.default_openai_url')
            console.print(f"[red]{self.translator('ui.error.connection_error', url=base_url_msg)}[/red]")
            console.print(f"[yellow]{self.translator('ui.error.connection_reasons')}[/yellow]")
            console.print(self.translator('ui.error.network_issue'))
            console.print(self.translator('ui.error.url_config'))
            console.print(self.translator('ui.error.service_unavailable'))
            console.print(f"[green]{self.translator('ui.error.connection_tips')}[/green]")
            console.print(self.translator('ui.error.check_network'))
            console.print(self.translator('ui.error.check_url'))
            console.print(self.translator('ui.error.retry_later'))
        elif isinstance(error, ValueError) and "URL" in error_msg:
            console.print(self.translator('ui.error.invalid_url_format', url=self.base_url))
            console.print(f"[yellow]{self.translator('ui.error.url_format_tip')}[/yellow]")
        else:
            console.print(self.translator('ui.error.initialization_error', error=error_msg))
        
        console.print(f"[red]{self.translator('ui.error.cannot_continue')}[/red]")
        sys.exit(1)

    def _get_language_display_name(self, language_code) -> str:
        """
        获取语言的显示名称，用于在prompt中替换语言占位符。
        
        注意：这个方法返回的是特定格式的语言名称，与 languages.py 中的 get_language_name 函数不同。
        这里需要返回每种语言的"本地名称"（如中文显示为"简体中文"，英文显示为"English"等），
        这是因为prompt模板中的{language}占位符需要特定格式的语言名称，以便AI正确理解应该使用哪种语言。
        
        Args:
            language_code: 语言代码
            
        Returns:
            特定格式的语言显示名称
        """
        # 针对prompt中的特殊需求，返回各语言的本地名称
        if language_code == "zh-CN":
            return "简体中文"
        elif language_code == "zh-TW":
            return "繁体中文"
        elif language_code == "en":
            return "English"
        elif language_code == "es":
            return "español"
        elif language_code == "ja":
            return "日本語"
        elif language_code == "pt":
            return "português"
        elif language_code == "fr":
            return "français"
        elif language_code == "de":
            return "Deutsch"
        elif language_code == "ru":
            return "русский"
        else:
            return "简体中文"  # 默认返回简体中文

    @retry(
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIError, openai.APIConnectionError, requests.exceptions.RequestException)),
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def analyze_repo(self, repo: Dict) -> Dict:
        """
        分析单个仓库信息并进行分类。

        Args:
            repo: 仓库信息

        Returns:
            分析结果，包含类别和描述
        """
        # 限制请求频率
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            time.sleep(self.request_interval - time_since_last_request)

        # 准备请求数据
        repo_data = repo.copy()

        # 获取语言代码，确保是字符串
        language_code = self.language
        if hasattr(language_code, 'value'):
            language_code = language_code.value
            
        # 获取语言显示名称，用于替换占位符
        language_display = self._get_language_display_name(language_code)
        
        # 替换prompt中的语言占位符
        user_prompt = USER_PROMPT.format(
            **repo_data, 
            language=language_display
        )

        try:
            # 发送请求
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",  # 使用合适的模型
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            self.last_request_time = time.time()

            # 处理响应
            result = response.choices[0].message.content
            return json.loads(result)
            
        except openai.AuthenticationError:
            console.print(f"[red]{self.translator('ui.error.openai_key_invalid')}[/red]")
            console.print(f"[yellow]{self.translator('ui.error.openai_key_check')}[/yellow]")
            sys.exit(1)
        except openai.RateLimitError:
            console.print(f"[yellow]{self.translator('ui.progress.rate_limit')}[/yellow]")
            raise  # 重新抛出异常，让重试装饰器处理
        except (openai.APIError, openai.APIConnectionError) as e:
            console.print(f"[yellow]OpenAI API Error: {str(e)}[/yellow]")
            raise  # 重新抛出异常，让重试装饰器处理
        except Exception as e:
            console.print(f"[red]{self.translator('ui.error.program_error', error=str(e))}[/red]")
            raise  # 重新抛出其他异常，让调用者处理

    def analyze_repos(self, repos: List[Dict]) -> List[Dict]:
        """
        分析多个仓库信息。

        Args:
            repos: 仓库信息列表

        Returns:
            分析结果列表
        """
        # 更新翻译器，确保使用正确的界面语言
        self.update_translator()
        
        analyzed_repos = []
        total = len(repos)
        completed = 0
        
        # 根据仓库数量动态调整并行数
        # 对于大量仓库，使用更高的并行数
        if total > 100:
            max_workers = 20
        elif total > 50:
            max_workers = 10
        else:
            max_workers = 5
            
        console.print(f"[cyan]使用 {max_workers} 个并行线程进行分析...[/cyan]")
        
        with Progress() as progress:
            task = progress.add_task(
                self.translator('ui.progress.analyzing', progress=0, current=0, total=total), 
                total=total
            )
            
            # 使用线程池进行并行处理
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有任务
                future_to_repo = {executor.submit(self.analyze_repo, repo): repo for repo in repos}
                
                # 处理完成的任务
                for future in concurrent.futures.as_completed(future_to_repo):
                    repo = future_to_repo[future]
                    try:
                        # 获取分析结果
                        result = future.result()
                        
                        # 合并分析结果与原始数据
                        analyzed_repo = {**repo, **result}
                        analyzed_repos.append(analyzed_repo)
                        
                        # 更新进度
                        completed += 1
                        progress_desc = self.translator('ui.progress.analyzing', 
                                                      progress=int(completed/total*100), 
                                                      current=completed, 
                                                      total=total)
                        progress.update(task, 
                                      description=progress_desc,
                                      advance=1)
                        
                    except RetryError:
                        progress.stop()
                        console.print(f"\n[red]Failed to analyze repository after multiple retries: {repo.get('full_name', 'Unknown')}[/red]")
                        sys.exit(1)
                    except Exception as e:
                        progress.stop()
                        console.print(f"\n[red]Error analyzing repository {repo.get('full_name', 'Unknown')}: {str(e)}[/red]")
                        sys.exit(1)
                    
        return analyzed_repos 