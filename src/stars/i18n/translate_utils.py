"""翻译工具模块，提供翻译键规范化和管理功能。"""

import os
import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
import argparse

# 设置日志记录器
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TranslationKeyStandard:
    """翻译键标准化类，定义翻译键的命名规则和组织结构。"""
    
    # 定义主要的命名空间
    NAMESPACES = {
        "app": "应用基本信息",
        "ui": "用户界面元素",
        "error": "错误信息",
        "success": "成功信息",
        "warning": "警告信息",
        "validation": "验证信息",
        "export": "导出功能",
        "import": "导入功能",
        "help": "帮助信息",
    }
    
    # UI子命名空间
    UI_SUBNAMESPACES = {
        "welcome": "欢迎页面",
        "config": "配置页面",
        "input": "输入提示",
        "button": "按钮文字",
        "menu": "菜单项",
        "dialog": "对话框",
        "confirmation": "确认提示",
        "progress": "进度提示",
        "results": "结果显示",
        "completion": "完成提示",
    }
    
    # 错误子命名空间
    ERROR_SUBNAMESPACES = {
        "api": "API错误",
        "network": "网络错误",
        "file": "文件错误",
        "input": "输入错误",
        "validation": "验证错误",
        "permission": "权限错误",
        "system": "系统错误",
    }
    
    @classmethod
    def validate_key(cls, key: str) -> Tuple[bool, str]:
        """
        验证翻译键是否符合规范。

        Args:
            key: 翻译键

        Returns:
            是否有效，错误信息（如果无效）
        """
        # 检查基本格式
        if not key or not isinstance(key, str):
            return False, "键不能为空且必须是字符串"
            
        # 检查格式和字符
        if not re.match(r'^[a-z0-9_]+(\.[a-z0-9_]+)+$', key):
            return False, "键必须使用小写字母、数字、下划线，并使用点分隔层级"
            
        # 检查命名空间
        parts = key.split(".")
        if parts[0] not in cls.NAMESPACES:
            return False, f"顶级命名空间 '{parts[0]}' 不在预定义列表中: {', '.join(cls.NAMESPACES.keys())}"
            
        # 检查UI子命名空间
        if parts[0] == "ui" and len(parts) >= 2 and parts[1] not in cls.UI_SUBNAMESPACES:
            return False, f"UI子命名空间 '{parts[1]}' 不在预定义列表中: {', '.join(cls.UI_SUBNAMESPACES.keys())}"
            
        # 检查错误子命名空间
        if parts[0] == "error" and len(parts) >= 2 and parts[1] not in cls.ERROR_SUBNAMESPACES:
            return False, f"错误子命名空间 '{parts[1]}' 不在预定义列表中: {', '.join(cls.ERROR_SUBNAMESPACES.keys())}"
            
        return True, ""
    
    @classmethod
    def suggest_key(cls, old_key: str) -> str:
        """
        为不规范的键建议更好的替代方案。

        Args:
            old_key: 原始键

        Returns:
            建议的新键
        """
        # 转换为小写并替换非法字符
        new_key = old_key.lower()
        new_key = re.sub(r'[^a-z0-9_.]', '_', new_key)
        
        # 分析键结构
        parts = new_key.split(".")
        
        # 如果不是以命名空间开头，尝试添加适当的命名空间
        if parts[0] not in cls.NAMESPACES:
            # 尝试基于键的内容推断命名空间
            if any(word in old_key.lower() for word in ["error", "exception", "fail", "invalid"]):
                new_key = f"error.system.{new_key}"
            elif any(word in old_key.lower() for word in ["success", "complete", "done"]):
                new_key = f"success.{new_key}"
            elif any(word in old_key.lower() for word in ["warning", "alert", "caution"]):
                new_key = f"warning.{new_key}"
            elif any(word in old_key.lower() for word in ["button", "menu", "dialog", "input", "form"]):
                new_key = f"ui.{new_key}"
            else:
                new_key = f"app.{new_key}"
        
        return new_key


def analyze_translation_files(translations_dir: Path) -> Dict[str, Dict]:
    """
    分析翻译文件中的键命名情况。

    Args:
        translations_dir: 翻译文件目录

    Returns:
        分析结果字典
    """
    results = {
        "files_analyzed": [],
        "total_keys": 0,
        "valid_keys": 0,
        "invalid_keys": 0,
        "invalid_key_details": {},
        "namespace_distribution": {},
    }
    
    # 检查目录存在
    if not translations_dir.exists() or not translations_dir.is_dir():
        logger.error(f"翻译目录不存在: {translations_dir}")
        return results
    
    # 查找所有YAML文件
    yaml_files = list(translations_dir.glob("*.yaml"))
    if not yaml_files:
        logger.warning(f"在 {translations_dir} 中未找到YAML文件")
        return results
    
    # 分析英语文件（作为主要参考）
    en_file = translations_dir / "en.yaml"
    if not en_file.exists():
        logger.warning("未找到英语翻译文件，将使用第一个找到的文件作为参考")
        reference_file = yaml_files[0]
    else:
        reference_file = en_file
    
    # 加载参考文件
    try:
        with open(reference_file, "r", encoding="utf-8") as f:
            reference_translations = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"加载参考文件 {reference_file} 时出错: {e}")
        return results
    
    # 记录已分析的文件
    results["files_analyzed"].append(reference_file.name)
    
    # 提取和分析所有键
    all_keys = _extract_keys(reference_translations)
    results["total_keys"] = len(all_keys)
    
    # 验证每个键
    for key in all_keys:
        is_valid, error_message = TranslationKeyStandard.validate_key(key)
        if is_valid:
            results["valid_keys"] += 1
        else:
            results["invalid_keys"] += 1
            results["invalid_key_details"][key] = {
                "error": error_message,
                "suggestion": TranslationKeyStandard.suggest_key(key)
            }
    
    # 分析命名空间分布
    namespace_counts = {}
    for key in all_keys:
        namespace = key.split(".")[0]
        namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
    
    results["namespace_distribution"] = namespace_counts
    
    return results


def _extract_keys(translation_dict: Dict, prefix: str = "") -> List[str]:
    """
    提取翻译字典中的所有键。

    Args:
        translation_dict: 翻译字典
        prefix: 当前键前缀

    Returns:
        所有键的列表
    """
    keys = []
    for key, value in translation_dict.items():
        current_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.extend(_extract_keys(value, current_key))
        else:
            keys.append(current_key)
    return keys


def migrate_translation_structure(translations_dir: Path, backup: bool = True) -> bool:
    """
    迁移翻译文件结构到符合规范的结构。

    Args:
        translations_dir: 翻译文件目录
        backup: 是否创建备份

    Returns:
        是否成功
    """
    # 检查目录存在
    if not translations_dir.exists() or not translations_dir.is_dir():
        logger.error(f"翻译目录不存在: {translations_dir}")
        return False
    
    # 查找所有YAML文件
    yaml_files = list(translations_dir.glob("*.yaml"))
    if not yaml_files:
        logger.warning(f"在 {translations_dir} 中未找到YAML文件")
        return False
    
    # 分析结果
    results = analyze_translation_files(translations_dir)
    
    # 如果没有无效键，不需要迁移
    if results["invalid_keys"] == 0:
        logger.info("所有翻译键都符合规范，不需要迁移")
        return True
    
    # 创建键映射 (旧键 -> 新键)
    key_mapping = {k: v["suggestion"] for k, v in results["invalid_key_details"].items()}
    
    # 对每个翻译文件执行迁移
    successful_migrations = 0
    for yaml_file in yaml_files:
        try:
            # 加载翻译文件
            with open(yaml_file, "r", encoding="utf-8") as f:
                translations = yaml.safe_load(f) or {}
            
            # 创建备份
            if backup:
                backup_file = yaml_file.with_suffix(f".backup.yaml")
                with open(backup_file, "w", encoding="utf-8") as f:
                    yaml.dump(translations, f, allow_unicode=True)
                    
            # 执行迁移
            new_translations = _migrate_dict(translations, key_mapping)
            
            # 写回文件
            with open(yaml_file, "w", encoding="utf-8") as f:
                yaml.dump(new_translations, f, allow_unicode=True, sort_keys=False)
                
            successful_migrations += 1
            logger.info(f"成功迁移文件: {yaml_file}")
            
        except Exception as e:
            logger.error(f"迁移文件 {yaml_file} 时出错: {e}")
    
    return successful_migrations == len(yaml_files)


def _migrate_dict(translation_dict: Dict, key_mapping: Dict[str, str], current_path: str = "") -> Dict:
    """
    递归迁移字典结构中的键。

    Args:
        translation_dict: 翻译字典
        key_mapping: 键映射 (旧键 -> 新键)
        current_path: 当前路径

    Returns:
        迁移后的字典
    """
    new_dict = {}
    
    for key, value in translation_dict.items():
        # 构建完整键路径
        full_key = f"{current_path}.{key}" if current_path else key
        
        # 如果是字典，递归处理
        if isinstance(value, dict):
            new_dict[key] = _migrate_dict(value, key_mapping, full_key)
        else:
            # 检查是否需要迁移
            if full_key in key_mapping:
                # 解析新键路径
                new_key_parts = key_mapping[full_key].split(".")
                
                # 在新结构中创建嵌套字典
                target_dict = new_dict
                for i, part in enumerate(new_key_parts):
                    if i == len(new_key_parts) - 1:
                        # 最后一个部分是叶子节点，设置值
                        target_dict[part] = value
                    else:
                        # 创建中间节点
                        if part not in target_dict:
                            target_dict[part] = {}
                        target_dict = target_dict[part]
            else:
                # 保持原样
                new_dict[key] = value
    
    return new_dict


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(description="翻译键规范化工具")
    parser.add_argument("--analyze", action="store_true", help="分析翻译键命名")
    parser.add_argument("--migrate", action="store_true", help="迁移翻译键结构")
    parser.add_argument("--no-backup", action="store_true", help="迁移时不创建备份")
    args = parser.parse_args()
    
    # 获取翻译文件目录
    translations_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "translations"
    
    if args.analyze:
        results = analyze_translation_files(translations_dir)
        
        print("\n====== 翻译键分析结果 ======\n")
        print(f"分析文件: {', '.join(results['files_analyzed'])}")
        print(f"总键数: {results['total_keys']}")
        print(f"有效键: {results['valid_keys']} ({results['valid_keys']/results['total_keys']*100 if results['total_keys'] else 0:.1f}%)")
        print(f"无效键: {results['invalid_keys']} ({results['invalid_keys']/results['total_keys']*100 if results['total_keys'] else 0:.1f}%)")
        
        if results["invalid_keys"] > 0:
            print("\n无效键详情:")
            for key, details in results["invalid_key_details"].items():
                print(f"  {key}")
                print(f"    - 错误: {details['error']}")
                print(f"    - 建议: {details['suggestion']}")
                
        print("\n命名空间分布:")
        for namespace, count in results["namespace_distribution"].items():
            print(f"  {namespace}: {count} 键 ({count/results['total_keys']*100 if results['total_keys'] else 0:.1f}%)")
    
    if args.migrate:
        print("\n====== 开始迁移翻译键结构 ======\n")
        success = migrate_translation_structure(translations_dir, not args.no_backup)
        if success:
            print("✅ 翻译键结构迁移成功!")
        else:
            print("❌ 翻译键结构迁移失败。请查看日志获取详细信息。")
    
    if not args.analyze and not args.migrate:
        print("请指定至少一个操作: --analyze 或 --migrate")
        parser.print_help()


if __name__ == "__main__":
    main() 