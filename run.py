#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from pathlib import Path

# Ensure directory structure exists
os.makedirs("output", exist_ok=True)
os.makedirs("templates", exist_ok=True)

def main():
    """Main program entry"""
    parser = argparse.ArgumentParser(description="ComfyUI Remote Client - Choose run mode")
    parser.add_argument("--gui", "-g", action="store_true", help="Run in GUI mode")
    parser.add_argument("--cli", "-c", action="store_true", help="Run in CLI mode")
    parser.add_argument("command", nargs="?", help="CLI command")
    parser.add_argument("args", nargs="*", help="Arguments passed to CLI mode")
    
    args, unknown = parser.parse_known_args()
    
    # CLI command list
    cli_commands = ["template", "generate", "save-template", "list-templates", "prompts"]
    
    # Check if CLI mode should be used
    # If --cli is explicitly specified or the command is a CLI command, use CLI mode
    should_use_cli = args.cli or (args.command in cli_commands)
    
    # If no mode is specified, and no CLI command detected, default to GUI mode
    if not args.gui and not should_use_cli:
        args.gui = True
    
    # Run in selected mode
    if args.gui:
        print("Starting GUI mode...")
        from gui import main as gui_main
        gui_main()
    
    elif should_use_cli:
        print("Starting CLI mode...")
        from main import main as cli_main
        
        # If there's a command, add it back to sys.argv and run the CLI
        if args.command:
            # Create new argv starting with the script name, then the command and args
            # Note: unknown args are passed through directly
            new_argv = [sys.argv[0], args.command] + args.args + unknown
            
            # Replace sys.argv with our new list
            sys.argv = new_argv
        
        # Run the CLI main function
        cli_main()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 