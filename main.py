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
    Load prompts from prompts.json file
    
    Returns:
        Dictionary containing prompts, or default prompts if file doesn't exist or can't be parsed
    """
    try:
        # Try to read prompts.json file from project root directory
        prompts_file = Path("prompts.json")
        if prompts_file.exists():
            with open(prompts_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Failed to read prompts file: {str(e)}, will use default prompts")
    
    # If file doesn't exist or can't be parsed, return default prompts
    return {
        "default": {
            "positive": "high quality, fine details, realistic, high definition photography",
            "negative": "low quality, blurry, distorted, error, noise"
        }
    }


def get_prompt_from_file(prompt_key=None):
    """
    Get prompts from prompts file
    
    Args:
        prompt_key: Prompt key name, if None uses 'default'
        
    Returns:
        Tuple containing (positive, negative) prompts
    """
    prompts = load_prompts_file()
    
    # If key not specified or doesn't exist, use default prompt
    if not prompt_key or prompt_key not in prompts:
        prompt_key = "default"
        
    prompt_data = prompts.get(prompt_key, prompts.get("default", {"positive": "", "negative": ""}))
    return prompt_data.get("positive", ""), prompt_data.get("negative", "")


def main():
    """Main program entry"""
    
    # Load environment variables
    load_dotenv()
    
    # Create parser
    parser = argparse.ArgumentParser(description="ComfyUI Remote Client - Generate and download images")
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Select command")
    
    # Generate image command
    generate_parser = subparsers.add_parser("generate", help="Generate image")
    generate_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="ComfyUI server URL")
    generate_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                               help="Proxy server address, e.g. http://127.0.0.1:1080 or socks5://127.0.0.1:1080")
    generate_parser.add_argument("--prompt", "-p", help="Prompt text, if not provided will read from prompts.json")
    generate_parser.add_argument("--prompt-key", "-pk", help="Prompt key name to read from prompts.json, default is 'default'")
    generate_parser.add_argument("--negative", "-n", help="Negative prompt, if not provided will read from prompts.json")
    generate_parser.add_argument("--width", "-W", type=int, default=512, help="Image width")
    generate_parser.add_argument("--height", "-H", type=int, default=512, help="Image height")
    generate_parser.add_argument("--seed", type=int, default=-1, help="Random seed")
    generate_parser.add_argument("--output", "-o", default="output", help="Output directory")
    
    # Use template command
    template_parser = subparsers.add_parser("template", help="Use template to generate image")
    template_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="ComfyUI server URL")
    template_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                               help="Proxy server address, e.g. http://127.0.0.1:1080 or socks5://127.0.0.1:1080")
    template_parser.add_argument("--name", "-n", required=True, help="Template name")
    template_parser.add_argument("--prompt", "-p", help="Prompt text (overrides template prompt), if not provided will read from prompts.json")
    template_parser.add_argument("--prompt-key", "-pk", help="Prompt key name to read from prompts.json, default is 'default'")
    template_parser.add_argument("--negative", "-N", help="Negative prompt (overrides template negative prompt), if not provided will read from prompts.json")
    template_parser.add_argument("--prompt-node", default="6", help="Prompt node ID")
    template_parser.add_argument("--negative-node", default="7", help="Negative prompt node ID")
    template_parser.add_argument("--output", "-o", default="output", help="Output directory")
    
    # Save template command
    save_template_parser = subparsers.add_parser("save-template", help="Save template")
    save_template_parser.add_argument("--name", "-n", required=True, help="Template name")
    save_template_parser.add_argument("--workflow", "-w", required=True, help="Workflow JSON file path")
    save_template_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="Server URL (used to create server-specific template directory)")
    
    # List templates command
    list_templates_parser = subparsers.add_parser("list-templates", help="List all templates")
    list_templates_parser.add_argument("--server", "-s", default=os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188"),
                                help="Server URL (used to list server-specific templates)")
    list_templates_parser.add_argument("--proxy", default=os.environ.get("HTTP_PROXY"), 
                                     help="Proxy server address, e.g. http://127.0.0.1:1080 or socks5://127.0.0.1:1080")
    
    # Parse command line arguments
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return
    
    # Handle different commands
    if args.command == "generate":
        generate_image(args)
    
    elif args.command == "template":
        use_template(args)
    
    elif args.command == "save-template":
        save_template(args)
    
    elif args.command == "list-templates":
        list_templates(args)


def generate_image(args):
    """Generate image using basic workflow"""
    
    try:
        # Initialize client
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # Initialize prompt manager, pass server URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # If prompt not provided, read from file
        positive_prompt = args.prompt
        negative_prompt = args.negative
        
        if not positive_prompt or not negative_prompt:
            file_positive, file_negative = get_prompt_from_file(args.prompt_key)
            
            if not positive_prompt:
                positive_prompt = file_positive
                print(f"Using positive prompt from file: {positive_prompt}")
                
            if not negative_prompt:
                negative_prompt = file_negative
                print(f"Using negative prompt from file: {negative_prompt}")
        
        # Create basic workflow
        workflow = prompt_manager.create_basic_text2img_workflow(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            seed=args.seed,
            width=args.width,
            height=args.height
        )
        
        # Generate image
        print(f"Generating image with prompt: {positive_prompt}")
        if negative_prompt:
            print(f"Negative prompt: {negative_prompt}")
        
        images_info, prompt_id = client.generate_image(workflow)
        
        # Download images
        if images_info:
            downloader = ImageDownloader(args.output)
            saved_paths = downloader.download_images(args.server, images_info, proxy=args.proxy)
            print(f"Downloaded {len(saved_paths)} images")
        else:
            print("No images were generated")
    
    except Exception as e:
        print(f"Failed to generate image: {str(e)}")
        sys.exit(1)


def use_template(args):
    """Use template to generate image"""
    
    try:
        # Initialize client
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # Initialize prompt manager, pass server URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # Ensure default template with SaveImage node exists
        if args.name == "default" or args.name == "default_save":
            template_name = prompt_manager.ensure_save_image_template(args.name)
            args.name = template_name
            print(f"Using default SaveImage template: {template_name}")
        
        # Load template
        try:
            workflow = prompt_manager.load_template(args.name)
        except FileNotFoundError:
            print(f"Template '{args.name}' does not exist, trying to create default template...")
            template_name = prompt_manager.ensure_save_image_template("default_save")
            args.name = template_name
            workflow = prompt_manager.load_template(template_name)
            print(f"Created and using default template: {template_name}")
        
        # Auto-detect prompt node IDs
        prompt_nodes = prompt_manager.detect_prompt_nodes(workflow)
        positive_node_id = prompt_nodes.get("positive")
        negative_node_id = prompt_nodes.get("negative")
        
        # If node IDs not found, use command line parameters
        if not positive_node_id and args.prompt_node:
            positive_node_id = args.prompt_node
            print(f"Could not auto-detect positive prompt node, using command line parameter ID: {positive_node_id}")
        
        if not negative_node_id and args.negative_node:
            negative_node_id = args.negative_node
            print(f"Could not auto-detect negative prompt node, using command line parameter ID: {negative_node_id}")
        
        # If prompt not provided, read from file
        prompt_text = args.prompt
        negative_text = args.negative
        
        if not prompt_text or not negative_text:
            file_positive, file_negative = get_prompt_from_file(args.prompt_key)
            
            if not prompt_text:
                prompt_text = file_positive
                print(f"Using positive prompt from file: {prompt_text}")
                
            if not negative_text:
                negative_text = file_negative
                print(f"Using negative prompt from file: {negative_text}")
        
        # Update prompt (if provided)
        if prompt_text and positive_node_id:
            workflow = prompt_manager.update_prompt(workflow, positive_node_id, prompt_text)
            print(f"Updated positive prompt (Node ID: {positive_node_id}): {prompt_text}")
        elif prompt_text:
            print(f"Warning: Cannot update positive prompt because no valid prompt node ID was found")
        
        # Update negative prompt (if provided)
        if negative_text and negative_node_id:
            workflow = prompt_manager.update_negative_prompt(workflow, negative_node_id, negative_text)
            print(f"Updated negative prompt (Node ID: {negative_node_id}): {negative_text}")
        elif negative_text:
            print(f"Warning: Cannot update negative prompt because no valid negative prompt node ID was found")
        
        # Generate image
        print(f"Using template '{args.name}' to generate image")
        images_info, prompt_id = client.generate_image(workflow)
        
        # Download images
        if images_info:
            downloader = ImageDownloader(args.output)
            saved_paths = downloader.download_images(args.server, images_info, proxy=args.proxy)
            print(f"Downloaded {len(saved_paths)} images")
        else:
            print("No images were generated")
    
    except Exception as e:
        print(f"Failed to generate image with template: {str(e)}")
        sys.exit(1)


def save_template(args):
    """Save workflow as template"""
    
    try:
        # Initialize prompt manager, pass server URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # Read workflow file
        try:
            with open(args.workflow, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Failed to read workflow file: {str(e)}")
            sys.exit(1)
        
        # Save template
        prompt_manager.save_template(args.name, workflow)
        print(f"Template '{args.name}' saved")
    
    except Exception as e:
        print(f"Failed to save template: {str(e)}")
        sys.exit(1)


def list_templates(args):
    """List all available templates"""
    
    try:
        # Initialize prompt manager, pass server URL
        prompt_manager = PromptManager(server_url=args.server)
        
        # Initialize client (if needed to check server-specific templates)
        client = ComfyUIClient(args.server, proxy=args.proxy)
        
        # Get template list
        templates = prompt_manager.list_templates()
        
        if templates:
            print("Available templates:")
            for i, template in enumerate(templates, 1):
                print(f"{i}. {template}")
        else:
            print("No templates available")
    
    except Exception as e:
        print(f"Failed to list templates: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 