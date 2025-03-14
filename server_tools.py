#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from comfy_client import ComfyUIClient
from prompt_manager import PromptManager

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description="ComfyUI服务器工具")
    parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                      help="ComfyUI服务器URL")
    
    subparsers = parser.add_subparsers(dest="command", help="选择命令")
    
    # 列出可用模型
    list_models_parser = subparsers.add_parser("list-models", help="列出可用模型")
    
    # 列出服务器信息
    server_info_parser = subparsers.add_parser("server-info", help="获取服务器信息")
    
    # 创建兼容工作流
    create_workflow_parser = subparsers.add_parser("create-workflow", help="创建兼容工作流")
    create_workflow_parser.add_argument("--name", "-n", required=True, help="工作流名称")
    create_workflow_parser.add_argument("--model", "-m", help="模型名称")
    
    # 解析命令行参数
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # 初始化客户端
        client = ComfyUIClient(args.server)
        
        if args.command == "list-models":
            models = client.get_available_models()
            if models:
                print("可用模型:")
                for i, model in enumerate(models, 1):
                    print(f"{i}. {model}")
            else:
                print("未找到可用模型")
        
        elif args.command == "server-info":
            info = client.get_server_info()
            print("服务器信息:")
            # 保存到文件
            with open("server_info.json", "w") as f:
                json.dump(info, f, indent=2)
            print(f"服务器信息已保存到server_info.json")
            
            # 打印一些关键信息
            if "object_info" in info:
                print("\n可用节点类型:")
                for node_type in info["object_info"].keys():
                    print(f"- {node_type}")
        
        elif args.command == "create-workflow":
            # 获取可用模型
            models = client.get_available_models()
            if not models:
                print("未找到可用模型")
                return
            
            # 选择模型
            model = args.model
            if not model:
                print("可用模型:")
                for i, m in enumerate(models, 1):
                    print(f"{i}. {m}")
                model_idx = int(input("请选择模型 (输入序号): ")) - 1
                if 0 <= model_idx < len(models):
                    model = models[model_idx]
                else:
                    print("无效的选择")
                    return
            
            # 创建基本工作流
            workflow = create_compatible_workflow(model)
            
            # 保存工作流
            manager = PromptManager(server_url=args.server)
            manager.save_template(args.name, workflow)
            print(f"兼容工作流已保存为模板: {args.name}")
            
            # 同时保存为扁平格式
            with open(f"templates/{args.name}_flat.json", "w") as f:
                json.dump(workflow["nodes"], f, indent=2)
            print(f"扁平格式工作流已保存为: templates/{args.name}_flat.json")
    
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

def create_compatible_workflow(model_name):
    """创建与大多数ComfyUI服务器兼容的工作流"""
    workflow = {
        "nodes": {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": model_name
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "高品质，精致细节，8k，高清摄影",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "低品质，模糊，不完整，变形",
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": 512,
                    "height": 512,
                    "batch_size": 1
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 12345,
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler_a",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "images": ["6", 0],
                    "filename_prefix": "ComfyUI"
                }
            }
        }
    }
    
    return workflow

if __name__ == "__main__":
    main() 