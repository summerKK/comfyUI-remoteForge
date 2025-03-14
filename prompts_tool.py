#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import argparse
from pathlib import Path


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


def save_prompts_file(prompts):
    """
    Save prompts to prompts.json file
    
    Args:
        prompts: Dictionary containing prompts
    """
    try:
        with open("prompts.json", 'w', encoding='utf-8') as f:
            json.dump(prompts, f, ensure_ascii=False, indent=2)
        print("Prompts saved to prompts.json file")
    except Exception as e:
        print(f"Failed to save prompts file: {str(e)}")


def list_prompts():
    """List all available prompts"""
    prompts = load_prompts_file()
    
    print("Available prompts:")
    for i, (key, prompt) in enumerate(prompts.items(), 1):
        print(f"{i}. {key}")
        print(f"   Positive: {prompt.get('positive', '')}")
        print(f"   Negative: {prompt.get('negative', '')}")
        print()


def view_prompt(key):
    """
    View specific prompt
    
    Args:
        key: Prompt key name
    """
    prompts = load_prompts_file()
    
    if key in prompts:
        prompt = prompts[key]
        print(f"Prompt: {key}")
        print(f"Positive: {prompt.get('positive', '')}")
        print(f"Negative: {prompt.get('negative', '')}")
    else:
        print(f"Prompt '{key}' does not exist")


def add_prompt(key, positive, negative):
    """
    Add new prompt
    
    Args:
        key: Prompt key name
        positive: Positive prompt
        negative: Negative prompt
    """
    prompts = load_prompts_file()
    
    if key in prompts:
        confirm = input(f"Prompt '{key}' already exists, overwrite? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return
    
    prompts[key] = {
        "positive": positive,
        "negative": negative
    }
    
    save_prompts_file(prompts)
    print(f"Prompt '{key}' added/updated")


def delete_prompt(key):
    """
    Delete prompt
    
    Args:
        key: Key name of prompt to delete
    """
    prompts = load_prompts_file()
    
    if key not in prompts:
        print(f"Prompt '{key}' does not exist")
        return
    
    if key == "default":
        print("Warning: Cannot delete default prompt")
        return
    
    confirm = input(f"Are you sure you want to delete prompt '{key}'? (y/n): ")
    if confirm.lower() != 'y':
        print("Operation cancelled")
        return
    
    del prompts[key]
    save_prompts_file(prompts)
    print(f"Prompt '{key}' deleted")


def main():
    parser = argparse.ArgumentParser(description="Prompt Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Select command")
    
    # List all prompts
    list_parser = subparsers.add_parser("list", help="List all prompts")
    
    # View specific prompt
    view_parser = subparsers.add_parser("view", help="View specific prompt")
    view_parser.add_argument("key", help="Prompt key name")
    
    # Add/update prompt
    add_parser = subparsers.add_parser("add", help="Add or update prompt")
    add_parser.add_argument("key", help="Prompt key name")
    add_parser.add_argument("positive", help="Positive prompt")
    add_parser.add_argument("negative", help="Negative prompt")
    
    # Delete prompt
    delete_parser = subparsers.add_parser("delete", help="Delete prompt")
    delete_parser.add_argument("key", help="Key name of prompt to delete")
    
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