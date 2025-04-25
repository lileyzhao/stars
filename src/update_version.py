#!/usr/bin/env python3
"""更新Stars的版本号。

此脚本会更新stars/__init__.py中的版本号，完成版本控制的单一真相来源更新。
使用方法: python update_version.py <版本号>
例如: python update_version.py 0.1.0
"""

import argparse
import re
import sys
from pathlib import Path


def update_version(version: str) -> None:
    """
    更新__init__.py文件中的版本号。
    
    Args:
        version: 新版本号（如"0.1.0"）
    """
    # 确保版本号格式正确
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError(f"版本号 '{version}' 不符合语义化版本格式 (x.y.z)")
    
    # 获取项目根目录
    root_dir = Path(__file__).parent.absolute()
    
    # 文件路径
    init_file = root_dir / "stars" / "__init__.py"
    
    # 确保文件存在
    if not init_file.exists():
        raise FileNotFoundError(f"找不到文件: {init_file}")
    
    # 读取文件内容
    content = init_file.read_text(encoding="utf-8")
    
    # 更新版本号
    updated_content = re.sub(
        r'__version__\s*=\s*"[^"]+"', 
        f'__version__ = "{version}"', 
        content
    )
    
    # 检查是否成功更新
    if content == updated_content:
        print("警告: 未找到版本号定义或版本号未改变")
        sys.exit(1)
    
    # 写回文件
    init_file.write_text(updated_content, encoding="utf-8")
    
    print(f"版本号已更新到 {version}")


def main():
    """主函数。"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="更新Stars版本号")
    parser.add_argument("version", help="新版本号 (如 '0.1.0')")
    args = parser.parse_args()
    
    update_version(args.version) 


if __name__ == "__main__":
    main() 