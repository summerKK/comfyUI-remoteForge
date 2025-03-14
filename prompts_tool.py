#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
from pathlib import Path


def load_prompts_file():
    """
    从prompts.json文件加载提示词
    
    Returns:
        包含提示词的字典，如果文件不存在或无法解析则返回默认提示词
    """
    try:
        # 尝试从项目根目录读取prompts.json文件
        prompts_file = Path("prompts.json")
        if prompts_file.exists():
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"读取提示词文件失败: {str(e)}，将使用默认提示词")
    
    # 如果文件不存在或无法解析，返回默认提示词
    return {
        "default": {
            "positive": "高品质，精致细节，真实感，高清摄影",
            "negative": "低品质，模糊，畸变，错误，噪点"
        }
    }


def save_prompts_file(prompts):
    """
    保存提示词到prompts.json文件
    
    Args:
        prompts: 包含提示词的字典
    """
    try:
        with open("prompts.json", 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        print("提示词已保存到prompts.json文件")
    except Exception as e:
        print(f"保存提示词文件失败: {str(e)}")


def list_prompts():
    """列出所有可用的提示词"""
    prompts = load_prompts_file()
    
    print("可用的提示词:")
    for i, (key, prompt) in enumerate(prompts.items(), 1):
        print(f"{i}. {key}")
        print(f"   正面: {prompt.get('positive', '')}")
        print(f"   负面: {prompt.get('negative', '')}")
        print()


def view_prompt(key):
    """
    查看特定提示词
    
    Args:
        key: 提示词的键名
    """
    prompts = load_prompts_file()
    
    if key in prompts:
        prompt = prompts[key]
        print(f"提示词: {key}")
        print(f"正面: {prompt.get('positive', '')}")
        print(f"负面: {prompt.get('negative', '')}")
    else:
        print(f"提示词 '{key}' 不存在")


def add_prompt(key, positive, negative):
    """
    添加新的提示词
    
    Args:
        key: 提示词的键名
        positive: 正面提示词
        negative: 负面提示词
    """
    prompts = load_prompts_file()
    
    if key in prompts:
        confirm = input(f"提示词 '{key}' 已存在，是否覆盖？ (y/n): ")
        if confirm.lower() != 'y':
            print("操作已取消")
            return
    
    prompts[key] = {
        "positive": positive,
        "negative": negative
    }
    
    save_prompts_file(prompts)
    print(f"提示词 '{key}' 已添加/更新")


def delete_prompt(key):
    """
    删除提示词
    
    Args:
        key: 要删除的提示词的键名
    """
    prompts = load_prompts_file()
    
    if key not in prompts:
        print(f"提示词 '{key}' 不存在")
        return
    
    if key == "default":
        print("警告: 不能删除默认提示词")
        return
    
    confirm = input(f"确定要删除提示词 '{key}' 吗？ (y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        return
    
    del prompts[key]
    save_prompts_file(prompts)
    print(f"提示词 '{key}' 已删除")


def main():
    parser = argparse.ArgumentParser(description="提示词管理工具")
    subparsers = parser.add_subparsers(dest="command", help="选择命令")
    
    # 列出所有提示词
    list_parser = subparsers.add_parser("list", help="列出所有提示词")
    
    # 查看特定提示词
    view_parser = subparsers.add_parser("view", help="查看特定提示词")
    view_parser.add_argument("key", help="提示词的键名")
    
    # 添加/更新提示词
    add_parser = subparsers.add_parser("add", help="添加或更新提示词")
    add_parser.add_argument("key", help="提示词的键名")
    add_parser.add_argument("positive", help="正面提示词")
    add_parser.add_argument("negative", help="负面提示词")
    
    # 删除提示词
    delete_parser = subparsers.add_parser("delete", help="删除提示词")
    delete_parser.add_argument("key", help="要删除的提示词的键名")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_prompts()
    elif args.command == "view":
        view_prompt(args.key)
    elif args.command == "add":
        add_prompt(args.key, args.positive, args.negative)
    elif args.command == "delete":
        delete_prompt(args.key)
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 