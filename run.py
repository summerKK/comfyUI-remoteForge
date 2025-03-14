#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from pathlib import Path

# 确保目录结构存在
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="ComfyUI远程客户端 - 选择运行模式")
    parser.add_argument("--gui", "-g", action="store_true", help="以图形界面模式运行")
    parser.add_argument("--cli", "-c", action="store_true", help="以命令行模式运行")
    parser.add_argument("command", nargs="?", help="命令行命令")
    parser.add_argument("args", nargs="*", help="传递给命令行模式的参数")
    
    args, unknown = parser.parse_known_args()
    
    # CLI命令列表
    cli_commands = ["template", "generate", "save-template", "list-templates", "prompts"]
    
    # 检查是否应该使用CLI模式
    # 如果明确指定--cli或命令是CLI命令之一，则使用CLI模式
    should_use_cli = args.cli or (args.command in cli_commands)
    
    # 如果没有指定模式，且没有检测到CLI命令，默认使用GUI模式
    if not args.gui and not should_use_cli:
        args.gui = True
    
    if args.gui and not should_use_cli:
        try:
            # 导入并运行GUI
            from gui import main as gui_main
            gui_main()
        except ImportError as e:
            print(f"启动GUI失败: {str(e)}")
            print("可能是缺少tkinter库。请安装tkinter或使用命令行模式。")
            sys.exit(1)
    
    else:  # CLI模式
        # 处理提示词管理命令
        if args.command == "prompts":
            # 导入并运行提示词管理工具
            try:
                from prompts_tool import main as prompts_main
                # 重构参数列表，移除"prompts"命令
                sys.argv = [sys.argv[0]] + args.args + unknown
                prompts_main()
                return
            except ImportError as e:
                print(f"启动提示词管理工具失败: {str(e)}")
                sys.exit(1)
        
        # 导入并运行命令行
        from main import main as cli_main
        cli_main()


if __name__ == "__main__":
    main() 