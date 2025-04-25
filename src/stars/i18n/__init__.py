"""国际化和本地化模块，提供多语言支持。"""

from .translator import Translator, Language, get_language_name
from .languages import get_available_languages, get_language_dict

__all__ = [
    'Translator', 
    'Language', 
    'get_language_name',
    'get_available_languages',
    'get_language_dict'
] 