"""语言定义模块，提供所有支持语言的定义和获取函数。"""

from enum import Enum
from typing import Dict, List, Tuple


class Language(str, Enum):
    """语言枚举，使用ISO 639-1代码。"""

    EN = "en"  # 英语
    ZH_CN = "zh-CN"  # 简体中文
    ZH_TW = "zh-TW"  # 繁体中文
    ES = "es"  # 西班牙语
    JA = "ja"  # 日语
    PT = "pt"  # 葡萄牙语
    FR = "fr"  # 法语
    DE = "de"  # 德语
    RU = "ru"  # 俄语


# 语言名称映射：第一级键是显示语言，第二级键是目标语言代码
LANGUAGE_NAMES = {
    Language.ZH_CN: {
        Language.EN: "英语",
        Language.ZH_CN: "简体中文",
        Language.ZH_TW: "繁体中文",
        Language.ES: "西班牙语",
        Language.JA: "日语",
        Language.PT: "葡萄牙语",
        Language.FR: "法语",
        Language.DE: "德语",
        Language.RU: "俄语",
    },
    Language.EN: {
        Language.EN: "English",
        Language.ZH_CN: "Simplified Chinese",
        Language.ZH_TW: "Traditional Chinese",
        Language.ES: "Spanish",
        Language.JA: "Japanese",
        Language.PT: "Portuguese",
        Language.FR: "French",
        Language.DE: "German",
        Language.RU: "Russian",
    },
    Language.ES: {
        Language.EN: "Inglés",
        Language.ZH_CN: "Chino simplificado",
        Language.ZH_TW: "Chino tradicional",
        Language.ES: "Español",
        Language.JA: "Japonés",
        Language.PT: "Portugués",
        Language.FR: "Francés",
        Language.DE: "Alemán",
        Language.RU: "Ruso",
    },
    Language.ZH_TW: {
        Language.EN: "英語",
        Language.ZH_CN: "簡體中文",
        Language.ZH_TW: "繁體中文",
        Language.ES: "西班牙語",
        Language.JA: "日語",
        Language.PT: "葡萄牙語",
        Language.FR: "法語",
        Language.DE: "德語",
        Language.RU: "俄語",
    },
    Language.JA: {
        Language.EN: "英語",
        Language.ZH_CN: "簡体中国語",
        Language.ZH_TW: "繁体中国語",
        Language.ES: "スペイン語",
        Language.JA: "日本語",
        Language.PT: "ポルトガル語",
        Language.FR: "フランス語",
        Language.DE: "ドイツ語",
        Language.RU: "ロシア語",
    },
    Language.PT: {
        Language.EN: "Inglês",
        Language.ZH_CN: "Chinês simplificado",
        Language.ZH_TW: "Chinês tradicional",
        Language.ES: "Espanhol",
        Language.JA: "Japonês",
        Language.PT: "Português",
        Language.FR: "Francês",
        Language.DE: "Alemão",
        Language.RU: "Russo",
    },
    Language.FR: {
        Language.EN: "Anglais",
        Language.ZH_CN: "Chinois simplifié",
        Language.ZH_TW: "Chinois traditionnel",
        Language.ES: "Espagnol",
        Language.JA: "Japonais",
        Language.PT: "Portugais",
        Language.FR: "Français",
        Language.DE: "Allemand",
        Language.RU: "Russe",
    },
    Language.DE: {
        Language.EN: "Englisch",
        Language.ZH_CN: "Vereinfachtes Chinesisch",
        Language.ZH_TW: "Traditionelles Chinesisch",
        Language.ES: "Spanisch",
        Language.JA: "Japanisch",
        Language.PT: "Portugiesisch",
        Language.FR: "Französisch",
        Language.DE: "Deutsch",
        Language.RU: "Russisch",
    },
    Language.RU: {
        Language.EN: "Английский",
        Language.ZH_CN: "Упрощенный китайский",
        Language.ZH_TW: "Традиционный китайский",
        Language.ES: "Испанский",
        Language.JA: "Японский",
        Language.PT: "Португальский",
        Language.FR: "Французский",
        Language.DE: "Немецкий",
        Language.RU: "Русский",
    },
}


def get_language_name(code: str, display_language: str = "zh-CN") -> str:
    """
    获取语言代码对应的本地化名称。
    
    Args:
        code: 语言代码
        display_language: 显示名称使用的语言
        
    Returns:
        语言的本地化名称
    """
    # 确保语言代码是字符串
    if hasattr(code, 'value'):
        code = code.value
        
    if hasattr(display_language, 'value'):
        display_language = display_language.value
    
    # 如果显示语言不在支持列表中，默认使用英语
    if display_language not in LANGUAGE_NAMES:
        display_language = Language.EN
        
    # 获取对应显示语言下的语言名称字典
    names = LANGUAGE_NAMES.get(display_language, LANGUAGE_NAMES[Language.EN])
    
    # 返回语言名称，如果没有找到则返回代码
    return names.get(code, f"Unknown ({code})")


def get_available_languages() -> List[str]:
    """
    获取所有可用的语言代码列表。
    
    Returns:
        语言代码列表
    """
    return [lang.value for lang in Language]


def get_language_choices(display_language: str = "zh-CN") -> List[Tuple[str, str]]:
    """
    获取格式化的语言选项列表，用于显示。
    
    Args:
        display_language: 显示名称使用的语言
        
    Returns:
        (代码, 名称)元组的列表
    """
    return [(lang.value, get_language_name(lang.value, display_language)) 
            for lang in Language]


def get_language_dict(display_language: str = "zh-CN") -> Dict[str, str]:
    """
    获取语言代码到名称的映射字典。
    
    Args:
        display_language: 显示名称使用的语言
        
    Returns:
        语言代码到名称的映射字典
    """
    return {lang.value: get_language_name(lang.value, display_language) 
            for lang in Language} 