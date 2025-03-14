#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import argparse
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

from comfy_client import ComfyUIClient
from prompt_manager import PromptManager
from image_downloader import ImageDownloader


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


def get_prompt_from_file(prompt_key=None):
    """
    从提示词文件中获取提示词
    
    Args:
        prompt_key: 提示词的键名，如果为None则使用'default'
        
    Returns:
        包含正面提示词和负面提示词的元组(positive, negative)
    """
    prompts = load_prompts_file()
    
    # 如果未指定键名或键名不存在，则使用默认提示词
    if not prompt_key or prompt_key not in prompts:
        prompt_key = "default"
        
    prompt_data = prompts.get(prompt_key, prompts.get("default", {"positive": "", "negative": ""}))
    return prompt_data.get("positive", ""), prompt_data.get("negative", "")


def main():
    """主程序入口"""
    
    # 加载环境变量
    load_dotenv()
    
    # 创建解析器
    parser = argparse.ArgumentParser(description="ComfyUI远程客户端 - 生成并下载图像")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="选择命令")
    
    # 生成图像命令
    generate_parser = subparsers.add_parser("generate", help="生成图像")
    generate_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="ComfyUI服务器URL")
    generate_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                               help="代理服务器地址，例如 http://127.0.0.1:1080 或 socks5://127.0.0.1:1080")
    generate_parser.add_argument("--prompt", "-p", help="提示词文本，如果不提供将从prompts.json读取")
    generate_parser.add_argument("--prompt-key", "-pk", help="从prompts.json中读取的提示词键名，默认为'default'")
    generate_parser.add_argument("--negative", "-n", help="负面提示词，如果不提供将从prompts.json读取")
    generate_parser.add_argument("--width", "-W", type=int, default=512, help="图像宽度")
    generate_parser.add_argument("--height", "-H", type=int, default=512, help="图像高度")
    generate_parser.add_argument("--seed", type=int, default=-1, help="随机种子")
    generate_parser.add_argument("--output", "-o", default="output", help="输出目录")
    
    # 使用模板命令
    template_parser = subparsers.add_parser("template", help="使用模板生成图像")
    template_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="ComfyUI服务器URL")
    template_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                               help="代理服务器地址，例如 http://127.0.0.1:1080 或 socks5://127.0.0.1:1080")
    template_parser.add_argument("--name", "-n", required=True, help="模板名称")
    template_parser.add_argument("--prompt", "-p", help="提示词文本（覆盖模板中的提示词），如果不提供将从prompts.json读取")
    template_parser.add_argument("--prompt-key", "-pk", help="从prompts.json中读取的提示词键名，默认为'default'")
    template_parser.add_argument("--negative", "-N", help="负面提示词（覆盖模板中的负面提示词），如果不提供将从prompts.json读取")
    template_parser.add_argument("--prompt-node", default="6", help="提示词节点ID")
    template_parser.add_argument("--negative-node", default="7", help="负面提示词节点ID")
    template_parser.add_argument("--output", "-o", default="output", help="输出目录")
    
    # 保存模板命令
    save_template_parser = subparsers.add_parser("save-template", help="保存模板")
    save_template_parser.add_argument("--name", "-n", required=True, help="模板名称")
    save_template_parser.add_argument("--workflow", "-w", required=True, help="工作流JSON文件路径")
    save_template_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="服务器URL（用于创建服务器特定的模板目录）")
    
    # 列出模板命令
    list_templates_parser = subparsers.add_parser("list-templates", help="列出所有模板")
    list_templates_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="服务器URL（用于列出服务器特定的模板）")
    list_templates_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                                     help="代理服务器地址，例如 http://127.0.0.1:1080 或 socks5://127.0.0.1:1080")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助信息
    if not args.command:
        parser.print_help()
        return
    
    # 处理不同的命令
    if args.command == "generate":
        generate_image(args)
    
    elif args.command == "template":
        use_template(args)
    
    elif args.command == "save-template":
        save_template(args)
    
    elif args.command == "list-templates":
        list_templates(args)


def generate_image(args):
    """使用基本工作流生成图像"""
    
    try:
        # 初始化客户端
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # 初始化提示词管理器，传递服务器URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # 如果未提供提示词，则从文件读取
        positive_prompt = args.prompt
        negative_prompt = args.negative
        
        if not positive_prompt or not negative_prompt:
            file_positive, file_negative = get_prompt_from_file(args.prompt_key)
            
            if not positive_prompt:
                positive_prompt = file_positive
                print(f"使用文件中的正面提示词: {positive_prompt}")
                
            if not negative_prompt:
                negative_prompt = file_negative
                print(f"使用文件中的负面提示词: {negative_prompt}")
        
        # 创建基本工作流
        workflow = prompt_manager.create_basic_text2img_workflow(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            seed=args.seed,
            width=args.width,
            height=args.height
        )
        
        # 生成图像
        print(f"使用提示词生成图像: {positive_prompt}")
        if negative_prompt:
            print(f"负面提示词: {negative_prompt}")
        
        images_info, prompt_id = client.generate_image(workflow)
        
        # 下载图像
        if images_info:
            downloader = ImageDownloader(args.output)
            saved_paths = downloader.download_images(args.server, images_info, proxy=args.proxy)
            print(f"已下载 {len(saved_paths)} 张图像")
        else:
            print("未生成任何图像")
    
    except Exception as e:
        print(f"生成图像失败: {str(e)}")
        sys.exit(1)


def use_template(args):
    """使用模板生成图像"""
    
    try:
        # 初始化客户端
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # 初始化提示词管理器，传递服务器URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # 确保存在带有SaveImage节点的默认模板
        if args.name == "default" or args.name == "default_save":
            template_name = prompt_manager.ensure_save_image_template(args.name)
            args.name = template_name
            print(f"使用默认SaveImage模板: {template_name}")
        
        # 加载模板
        try:
            workflow = prompt_manager.load_template(args.name)
        except FileNotFoundError:
            print(f"模板 '{args.name}' 不存在，尝试创建默认模板...")
            template_name = prompt_manager.ensure_save_image_template("default_save")
            args.name = template_name
            workflow = prompt_manager.load_template(template_name)
            print(f"已创建并使用默认模板: {template_name}")
        
        # 自动检测提示词节点ID
        prompt_nodes = prompt_manager.detect_prompt_nodes(workflow)
        positive_node_id = prompt_nodes.get("positive")
        negative_node_id = prompt_nodes.get("negative")
        
        # 如果找不到相应的节点ID，则使用命令行参数中指定的ID
        if not positive_node_id and args.prompt_node:
            positive_node_id = args.prompt_node
            print(f"未能自动检测正面提示词节点，使用命令行参数指定的ID: {positive_node_id}")
        
        if not negative_node_id and args.negative_node:
            negative_node_id = args.negative_node
            print(f"未能自动检测负面提示词节点，使用命令行参数指定的ID: {negative_node_id}")
        
        # 如果未提供提示词，则从文件读取
        prompt_text = args.prompt
        negative_text = args.negative
        
        if not prompt_text or not negative_text:
            file_positive, file_negative = get_prompt_from_file(args.prompt_key)
            
            if not prompt_text:
                prompt_text = file_positive
                print(f"使用文件中的正面提示词: {prompt_text}")
                
            if not negative_text:
                negative_text = file_negative
                print(f"使用文件中的负面提示词: {negative_text}")
        
        # 更新提示词（如果提供）
        if prompt_text and positive_node_id:
            workflow = prompt_manager.update_prompt(workflow, positive_node_id, prompt_text)
            print(f"已更新正面提示词 (节点ID: {positive_node_id}): {prompt_text}")
        elif prompt_text:
            print(f"警告: 无法更新正面提示词，因为未找到有效的提示词节点ID")
        
        # 更新负面提示词（如果提供）
        if negative_text and negative_node_id:
            workflow = prompt_manager.update_negative_prompt(workflow, negative_node_id, negative_text)
            print(f"已更新负面提示词 (节点ID: {negative_node_id}): {negative_text}")
        elif negative_text:
            print(f"警告: 无法更新负面提示词，因为未找到有效的负面提示词节点ID")
        
        # 生成图像
        print(f"使用模板 '{args.name}' 生成图像")
        images_info, prompt_id = client.generate_image(workflow)
        
        # 下载图像
        if images_info:
            downloader = ImageDownloader(args.output)
            saved_paths = downloader.download_images(args.server, images_info, proxy=args.proxy)
            print(f"已下载 {len(saved_paths)} 张图像")
        else:
            print("未生成任何图像")
    
    except Exception as e:
        print(f"使用模板生成图像失败: {str(e)}")
        sys.exit(1)


def save_template(args):
    """保存工作流作为模板"""
    
    try:
        # 初始化提示词管理器，传递服务器URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # 读取工作流文件
        try:
            with open(args.workflow, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"读取工作流文件失败: {str(e)}")
            sys.exit(1)
        
        # 保存模板
        prompt_manager.save_template(args.name, workflow)
        print(f"模板 '{args.name}' 已保存")
    
    except Exception as e:
        print(f"保存模板失败: {str(e)}")
        sys.exit(1)


def list_templates(args):
    """列出所有可用的模板"""
    
    try:
        # 初始化提示词管理器，传递服务器URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # 初始化客户端（如果需要检查服务器特定模板）
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # 获取模板列表
        templates = prompt_manager.list_templates()
        
        if templates:
            print("可用的模板:")
            for i, template in enumerate(templates, 1):
                print(f"{i}. {template}")
        else:
            print("没有可用的模板")
    
    except Exception as e:
        print(f"列出模板失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 