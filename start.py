#!/usr/bin/env python3
"""
iOS Real Run 启动器
支持GUI和命令行两种模式
"""

import sys
import os
import argparse


def main():
    parser = argparse.ArgumentParser(description='iOS Real Run - 跑步模拟器')
    parser.add_argument('--gui', action='store_true', help='启动GUI界面')
    parser.add_argument('--cli', action='store_true', help='启动命令行界面')
    
    args = parser.parse_args()
    
    # 如果没有指定模式，默认启动GUI
    if not args.cli and not args.gui:
        args.gui = True
    
    if args.gui:
        try:
            # 检查tkinter是否可用
            import tkinter as tk
            from gui import main as gui_main
            print("启动GUI界面...")
            gui_main()
        except ImportError as e:
            print(f"GUI模式不可用: {e}")
            print("请安装tkinter或使用命令行模式: python start.py --cli")
            sys.exit(1)
        except Exception as e:
            print(f"启动GUI失败: {e}")
            sys.exit(1)
            
    elif args.cli:
        try:
            from main import main as cli_main
            import asyncio
            print("启动命令行界面...")
            asyncio.run(cli_main())
        except Exception as e:
            print(f"启动命令行模式失败: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
