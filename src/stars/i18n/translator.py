"""翻译器模块，提供多语言翻译功能。"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .languages import Language, get_language_name, get_available_languages

# 设置日志记录器
logger = logging.getLogger(__name__)

# 导出类和函数以便于外部使用
__all__ = ['Translator', 'Language', 'get_language_name', 'get_available_languages', 'get_translator']

# 全局翻译器实例字典，按语言对存储 (interface_language, output_language) -> Translator
_translator_instances = {}

def get_translator(language: str = "zh-CN") -> 'Translator':
    """
    获取或创建全局翻译器实例。
    
    Args:
        language: 语言代码
        
    Returns:
        全局翻译器实例
    """
    global _translator_instances
    
    # 确保语言参数是字符串
    if hasattr(language, 'value'):
        language = language.value
    
    # 如果实例已存在，直接返回
    if language in _translator_instances:
        return _translator_instances[language]
    
    # 创建新的翻译器实例
    translator = Translator(language)
    _translator_instances[language] = translator
    
    return translator

class Translator:
    """翻译器类，负责加载翻译文件和提供翻译功能。"""
    
    def __init__(self, language: str = "zh-CN"):
        """
        初始化翻译器。
        
        Args:
            language: 语言代码
        """
        # 确保语言参数是字符串
        if hasattr(language, 'value'):
            language = language.value
            
        self.language = language
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.fallback_languages = ["en"]  # 默认使用英语作为备选语言
        
        # 初始化已加载语言集合
        self._loaded_languages = set()
        
        # 预加载必要的语言
        self._preload_essential_languages()
    
    def _get_translations_dir(self) -> Path:
        """
        获取翻译文件目录路径。
        
        Returns:
            翻译文件目录的Path对象
        """
        # 获取当前模块文件的目录
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        
        # 建立translations目录的路径
        return current_dir / "translations"
    
    def _preload_essential_languages(self) -> None:
        """预加载必要的语言翻译（当前语言和英语）。"""
        # 加载英语作为基础降级语言
        self._load_language("en")
        
        # 加载主要语言
        if self.language != "en":
            self._load_language(self.language)
    
    def _load_language(self, language_code: str) -> None:
        """
        加载特定语言的翻译文件。
        
        Args:
            language_code: 语言代码
        """
        # 如果语言已加载，直接返回
        if language_code in self._loaded_languages:
            return
            
        translations_dir = self._get_translations_dir()
        translation_file = translations_dir / f"{language_code}.yaml"
        
        # 检查文件是否存在，不存在则创建空的翻译文件
        if not translation_file.exists():
            # 创建一个空的文件并添加基本结构
            with open(translation_file, "w", encoding="utf-8") as f:
                # 添加文件头注释
                f.write(f"# {get_language_name(language_code, 'en')} translations\n")
                f.write("# This file is automatically generated. You can add translations below.\n\n")
                
                # 写入基本结构
                yaml.dump({"app": {"name": "Stars"}}, f, allow_unicode=True)
            
            logger.info(f"已创建空的翻译文件: {translation_file}")
        
        # 加载翻译
        try:
            with open(translation_file, "r", encoding="utf-8") as f:
                self.translations[language_code] = yaml.safe_load(f) or {}
            
            # 标记为已加载
            self._loaded_languages.add(language_code)
            logger.debug(f"已加载翻译文件: {translation_file}")
        except Exception as e:
            # 如果加载失败，使用空字典
            self.translations[language_code] = {}
            logger.error(f"加载翻译文件 {translation_file} 时出错: {e}")
    
    def get(self, key_path: str, language: Optional[str] = None, **kwargs) -> str:
        """
        获取指定键的翻译，支持参数替换。
        
        Args:
            key_path: 翻译键，格式为"section.subsection.key"
            language: 语言代码，如果为None则使用界面语言
            **kwargs: 用于格式化翻译字符串的参数
            
        Returns:
            翻译后的字符串
        """
        # 确定要使用的语言，并确保是字符串类型
        lang = language or self.language
        if hasattr(lang, 'value'):
            lang = lang.value
        
        # 准备要尝试的语言列表，首先是请求的语言，然后是备选语言
        languages_to_try = [lang]
        
        # 如果请求的语言不在备选语言列表中，添加备选语言
        for fallback_lang in self.fallback_languages:
            if fallback_lang != lang:
                # 确保备选语言也是字符串类型
                if hasattr(fallback_lang, 'value'):
                    fallback_lang = fallback_lang.value
                languages_to_try.append(fallback_lang)
        
        # 分解键以便于在嵌套结构中查找
        key_parts = key_path.split(".")
        
        # 尝试每种语言
        for try_lang in languages_to_try:
            # 确保语言已加载
            if try_lang not in self._loaded_languages:
                self._load_language(try_lang)
                
            # 只尝试已加载的翻译
            if try_lang not in self.translations:
                continue
                
            # 逐级获取翻译值
            value = self.translations.get(try_lang, {})
            key_found = True
            
            for part in key_parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    key_found = False
                    break
            
            # 如果找到了翻译，返回格式化后的值
            if key_found and isinstance(value, (str, int, float, bool)):
                value_str = str(value)
                
                # 应用格式化参数
                if kwargs:
                    try:
                        return value_str.format(**kwargs)
                    except KeyError as e:
                        logger.warning(f"格式化翻译键 '{key_path}' 时缺少参数: {e}")
                        return value_str
                
                return value_str
        
        # 如果所有语言都没有找到翻译，返回键名
        logger.warning(f"未找到翻译键: {key_path}")
        return key_path
    
    def get_output_translation(self, key_path: str, **kwargs) -> str:
        """
        获取指定键的翻译。
        
        Args:
            key_path: 翻译键，格式为"section.subsection.key"
            **kwargs: 用于格式化翻译字符串的参数
            
        Returns:
            翻译后的字符串
        """
        return self.get(key_path, self.language, **kwargs)
    
    def set_language(self, language: str) -> None:
        """
        设置语言。
        
        Args:
            language: 语言代码
        """
        # 确保语言参数是字符串
        if hasattr(language, 'value'):
            language = language.value
            
        if language not in get_available_languages():
            logger.warning(f"不支持的语言: {language}，将使用默认语言")
            return
            
        self.language = language

        # 确保语言已加载
        if language not in self._loaded_languages:
            self._load_language(language)
    
    def set_fallback_languages(self, languages: List[str]) -> None:
        """
        设置备选语言列表。当主要语言找不到翻译时，将按顺序尝试备选语言。
        
        Args:
            languages: 语言代码列表
        """
        # 验证语言代码
        valid_languages = []
        for lang in languages:
            # 确保语言参数是字符串
            if hasattr(lang, 'value'):
                lang = lang.value
                
            if lang in get_available_languages():
                valid_languages.append(lang)
            else:
                logger.warning(f"忽略不支持的语言: {lang}")
        
        self.fallback_languages = valid_languages
        
        # 提前加载所有备选语言，以提高后续翻译的速度
        for lang in valid_languages:
            if lang not in self._loaded_languages:
                self._load_language(lang)
    
    def get_available_translations(self) -> List[str]:
        """
        获取当前已加载的翻译语言列表。
        
        Returns:
            已加载的语言代码列表
        """
        # 确保返回的是字符串类型的语言代码
        return list(self._loaded_languages)
    
    def get_translation_completeness(self, language: str) -> float:
        """
        计算特定语言翻译的完整度（相对于英语翻译）。
        
        Args:
            language: 语言代码
            
        Returns:
            完整度百分比（0.0-1.0）
        """
        # 确保英语和目标语言已加载
        if "en" not in self._loaded_languages:
            self._load_language("en")
            
        if language != "en" and language not in self._loaded_languages:
            self._load_language(language)
            
        if language not in self.translations or "en" not in self.translations:
            return 0.0
            
        # 计算英语翻译中的键数量
        en_keys = self._count_translation_keys(self.translations["en"])
        
        # 计算目标语言中的键数量
        lang_keys = self._count_translation_keys(self.translations[language])
        
        # 计算完整度
        if en_keys == 0:
            return 1.0  # 避免除以零
            
        return lang_keys / en_keys
    
    def _count_translation_keys(self, translations: Dict, prefix: str = "") -> int:
        """
        递归计算翻译字典中的键数量。
        
        Args:
            translations: 翻译字典
            prefix: 当前键前缀
            
        Returns:
            键数量
        """
        count = 0
        for key, value in translations.items():
            current_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                count += self._count_translation_keys(value, current_key)
            else:
                count += 1
        return count
    
    def __call__(self, key_path: str, **kwargs) -> str:
        """
        使Translator实例可调用，直接返回翻译结果。
        
        Args:
            key_path: 翻译键，格式为"section.subsection.key"
            **kwargs: 用于格式化翻译字符串的参数
            
        Returns:
            翻译后的字符串
        """
        # 检查kwargs中是否有language参数，如果有，重命名为language_param避免冲突
        format_kwargs = kwargs.copy()
        if 'language' in format_kwargs:
            format_kwargs['language_param'] = format_kwargs.pop('language')
            
        # 使用interface_language作为选择语言的参数，format_kwargs用于格式化
        return self.get(key_path, self.language, **format_kwargs)