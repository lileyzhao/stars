#!/usr/bin/env python3
"""Stars - 智能分析并分类GitHub用户的Starred仓库。"""

import sys

from stars.app import Application

def main():
    """主函数，程序入口点。"""
    app = Application()
    app.run()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 