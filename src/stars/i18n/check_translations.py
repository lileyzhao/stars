"""翻译键检查工具，用于确保所有语言文件具有完整的翻译键。"""

import os
import sys
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse

# 将父目录添加到Python路径中，以便导入模块
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from stars.i18n.languages import get_available_languages, get_language_name
from stars.i18n.translator import Translator

# 设置日志记录器
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_all_keys(translation_dict: Dict, prefix: str = "") -> Set[str]:
    """
    递归提取字典中的所有键路径。

    Args:
        translation_dict: 翻译字典
        prefix: 当前键前缀

    Returns:
        所有键路径的集合
    """
    keys = set()
    for key, value in translation_dict.items():
        current_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            # 递归提取子字典的键
            sub_keys = get_all_keys(value, current_key)
            keys.update(sub_keys)
        else:
            # 添加叶子节点键
            keys.add(current_key)
    return keys


def check_translations(translations_dir: Path) -> Tuple[Dict[str, Set[str]], Dict[str, Set[str]], Dict[str, float]]:
    """
    检查所有翻译文件的键一致性。

    Args:
        translations_dir: 翻译文件目录

    Returns:
        每个语言的键集合，每个语言缺失的键集合，以及每个语言的完整度
    """
    all_keys = set()
    language_keys = {}
    missing_keys = {}
    completeness = {}
    
    # 获取所有语言代码
    languages = get_available_languages()
    
    # 首先加载所有文件并收集所有键
    for lang in languages:
        translation_file = translations_dir / f"{lang}.yaml"
        if not translation_file.exists():
            logger.warning(f"未找到语言文件: {translation_file}")
            language_keys[lang] = set()
            continue
            
        try:
            with open(translation_file, "r", encoding="utf-8") as f:
                translations = yaml.safe_load(f) or {}
                
            # 获取该语言文件中的所有键
            keys = get_all_keys(translations)
            language_keys[lang] = keys
            
            # 更新全局键集合
            all_keys.update(keys)
            
        except Exception as e:
            logger.error(f"加载文件 {translation_file} 时出错: {e}")
            language_keys[lang] = set()
    
    # 英语作为参考语言
    reference_keys = language_keys.get("zh-CN", set())
    if not reference_keys:
        logger.error("未找到英语翻译文件或文件为空，无法进行比较")
        return language_keys, {}, {}
        
    # 计算每种语言的缺失键和完整度
    for lang, keys in language_keys.items():
        missing = reference_keys - keys
        missing_keys[lang] = missing
        
        if reference_keys:
            completeness[lang] = (len(keys) / len(reference_keys)) * 100
        else:
            completeness[lang] = 0.0
    
    return language_keys, missing_keys, completeness


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="检查翻译文件的完整性")
    parser.add_argument("--fix", action="store_true", help="自动添加缺失的键（使用英语键值）")
    parser.add_argument("--display-language", default="zh-CN", help="显示语言的代码")
    args = parser.parse_args()
    
    # 获取翻译文件目录
    translations_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "translations"
    if not translations_dir.exists():
        logger.error(f"翻译目录不存在: {translations_dir}")
        return
        
    # 执行检查
    language_keys, missing_keys, completeness = check_translations(translations_dir)
    
    # 显示结果
    print("\n====== 翻译完整度检查 ======\n")
    
    for lang in sorted(language_keys.keys()):
        lang_name = get_language_name(lang, args.display_language)
        total_keys = len(language_keys.get("en", set()))
        existing_keys = len(language_keys.get(lang, set()))
        missing_count = len(missing_keys.get(lang, set()))
        
        status = "✅ 完整" if missing_count == 0 else f"❌ 缺失 {missing_count} 个键"
        print(f"{lang} ({lang_name}): {existing_keys}/{total_keys} 键 - {completeness[lang]:.1f}% - {status}")
        
        # 如果有缺失的键，并且不是英语，显示详细信息
        if missing_count > 0 and lang != "en":
            print(f"  缺失的键:")
            for key in sorted(missing_keys[lang]):
                print(f"    - {key}")
                
            # 如果需要自动修复
            if args.fix:
                try:
                    # 加载该语言的翻译文件
                    translation_file = translations_dir / f"{lang}.yaml"
                    with open(translation_file, "r", encoding="utf-8") as f:
                        translations = yaml.safe_load(f) or {}
                    
                    # 加载英语翻译文件作为参考
                    en_file = translations_dir / "en.yaml"
                    with open(en_file, "r", encoding="utf-8") as f:
                        en_translations = yaml.safe_load(f) or {}
                    
                    # 添加缺失的键（使用英语值）
                    modified = False
                    for key in missing_keys[lang]:
                        key_parts = key.split(".")
                        
                        # 获取英语值
                        en_value = en_translations
                        for part in key_parts:
                            if isinstance(en_value, dict) and part in en_value:
                                en_value = en_value[part]
                            else:
                                en_value = None
                                break
                        
                        if en_value is not None and isinstance(en_value, (str, int, float, bool)):
                            # 在目标翻译中添加该键
                            current = translations
                            for i, part in enumerate(key_parts):
                                if i == len(key_parts) - 1:
                                    # 最后一部分是键名
                                    current[part] = en_value
                                    modified = True
                                else:
                                    # 中间部分是字典路径
                                    if part not in current:
                                        current[part] = {}
                                    current = current[part]
                    
                    # 如果有修改，写回文件
                    if modified:
                        with open(translation_file, "w", encoding="utf-8") as f:
                            yaml.dump(translations, f, allow_unicode=True, sort_keys=False)
                        print(f"  已将缺失的键添加到 {lang}.yaml")
                
                except Exception as e:
                    print(f"  修复 {lang}.yaml 时出错: {e}")
            
            print()  # 添加空行分隔
    
    # 打印总结
    all_complete = all(len(missing) == 0 for missing in missing_keys.values())
    if all_complete:
        print("\n✅ 所有翻译文件都是完整的!")
    else:
        incomplete_count = sum(1 for missing in missing_keys.values() if len(missing) > 0)
        if args.fix:
            print(f"\n🔧 已尝试修复 {incomplete_count} 个不完整的翻译文件。请重新运行检查以验证。")
        else:
            print(f"\n❌ 发现 {incomplete_count} 个不完整的翻译文件。使用 --fix 参数可以自动添加缺失的键。")
    

if __name__ == "__main__":
    main() 