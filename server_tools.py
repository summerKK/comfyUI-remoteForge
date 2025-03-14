#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from comfy_client import ComfyUIClient
from prompt_manager import PromptManager

def main():
    """Main program entry"""
    parser = argparse.ArgumentParser(description="ComfyUI Server Tools")
    parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                      help="ComfyUI server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Select command")
    
    # List available models
    list_models_parser = subparsers.add_parser("list-models", help="List available models")
    
    # Get server information
    server_info_parser = subparsers.add_parser("server-info", help="Get server information")
    
    # Create compatible workflow
    create_workflow_parser = subparsers.add_parser("create-workflow", help="Create compatible workflow")
    create_workflow_parser.add_argument("--name", "-n", required=True, help="Workflow name")
    create_workflow_parser.add_argument("--model", "-m", help="Model name")
    
    # Parse command line arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        # Initialize client
        client = ComfyUIClient(args.server)
        
        if args.command == "list-models":
            models = client.get_available_models()
            if models:
                print("Available models:")
                for i, model in enumerate(models, 1):
                    print(f"{i}. {model}")
            else:
                print("No available models found")
        
        elif args.command == "server-info":
            info = client.get_server_info()
            print("Server information:")
            # Save to file
            with open("server_info.json", "w") as f:
                json.dump(info, f, indent=2)
            print(f"Server information saved to server_info.json")
            
            # Print some key information
            if "object_info" in info:
                print("\nAvailable node types:")
                for node_type in info["object_info"].keys():
                    print(f"- {node_type}")
        
        elif args.command == "create-workflow":
            # Get available models
            models = client.get_available_models()
            if not models:
                print("No available models found")
                return
            
            # Select model
            model = args.model
            if not model:
                print("Available models:")
                for i, m in enumerate(models, 1):
                    print(f"{i}. {m}")
                model_idx = int(input("Select a model (enter number): ")) - 1
                if 0 <= model_idx < len(models):
                    model = models[model_idx]
                else:
                    print("Invalid selection")
                    return
            
            # Create basic workflow
            workflow = create_compatible_workflow(model)
            
            # Save workflow
            manager = PromptManager(server_url=args.server)
            manager.save_template(args.name, workflow)
            print(f"Compatible workflow saved as template: {args.name}")
            
            # Also save as flat format
            with open(f"templates/{args.name}_flat.json", "w") as f:
                json.dump(workflow["nodes"], f, indent=2)
            print(f"Flat format workflow saved as: templates/{args.name}_flat.json")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

def create_compatible_workflow(model_name):
    """Create a workflow compatible with most ComfyUI servers"""
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
                    "text": "high quality, fine details, 8k, high definition photography",
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "low quality, blurry, incomplete, deformed",
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