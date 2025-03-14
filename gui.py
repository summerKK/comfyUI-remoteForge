#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from PIL import Image, ImageTk
from pathlib import Path
from dotenv import load_dotenv

from comfy_client import ComfyUIClient
from prompt_manager import PromptManager
from image_downloader import ImageDownloader


class ComfyUIRemoteGUI:
    """ComfyUI Remote Client GUI Interface"""
    
    def __init__(self, root):
        """
        Initialize GUI
        
        Args:
            root: tkinter root window
        """
        # Load environment variables
        load_dotenv()
        
        self.root = root
        self.root.title("ComfyUI Remote Client")
        self.root.geometry("960x720")
        self.root.resizable(True, True)
        
        # Create styles
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TEntry", font=("Arial", 10))
        
        # Initialize components
        self.client = None
        self.prompt_manager = PromptManager()
        self.downloader = ImageDownloader()
        self.current_workflow = None
        self.current_template = None
        self.last_image_path = None
        
        # Create main frame
        self.create_main_frame()
        
        # Default server URL
        default_server = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188")
        self.server_var.set(default_server)
        
        # Try to load template list
        self.load_templates()
    
    def create_main_frame(self):
        """Create main frame"""
        # Create tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create basic generation page
        self.create_generate_tab()
        
        # Create template page
        self.create_template_tab()
        
        # Create settings page
        self.create_settings_tab()
        
        # Create log panel
        self.create_log_panel()
    
    def create_generate_tab(self):
        """Create basic generation tab"""
        generate_frame = ttk.Frame(self.notebook)
        self.notebook.add(generate_frame, text="Basic Generation")
        
        # Server settings
        server_frame = ttk.LabelFrame(generate_frame, text="Server Settings")
        server_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(server_frame, text="Server URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_var = tk.StringVar()
        server_entry = ttk.Entry(server_frame, textvariable=self.server_var, width=40)
        server_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        connect_btn = ttk.Button(server_frame, text="Connect", command=self.connect_server)
        connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Add proxy settings
        ttk.Label(server_frame, text="Proxy Server:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.proxy_var = tk.StringVar(value=os.environ.get("HTTP_PROXY", ""))
        proxy_entry = ttk.Entry(server_frame, textvariable=self.proxy_var, width=40)
        proxy_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Prompt settings
        prompt_frame = ttk.LabelFrame(generate_frame, text="Prompt Settings")
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(prompt_frame, text="Positive Prompt:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=5, width=60, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(prompt_frame, text="Negative Prompt:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        self.negative_text = scrolledtext.ScrolledText(prompt_frame, height=3, width=60, wrap=tk.WORD)
        self.negative_text.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Image settings
        image_frame = ttk.LabelFrame(generate_frame, text="Image Settings")
        image_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(image_frame, text="Width:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.width_var = tk.IntVar(value=512)
        width_entry = ttk.Entry(image_frame, textvariable=self.width_var, width=6)
        width_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(image_frame, text="Height:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.height_var = tk.IntVar(value=512)
        height_entry = ttk.Entry(image_frame, textvariable=self.height_var, width=6)
        height_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(image_frame, text="Seed:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.seed_var = tk.IntVar(value=-1)
        seed_entry = ttk.Entry(image_frame, textvariable=self.seed_var, width=8)
        seed_entry.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Generate button
        generate_btn = ttk.Button(generate_frame, text="Generate Image", command=self.generate_image)
        generate_btn.pack(padx=10, pady=10)
        
        # Image preview
        self.preview_frame = ttk.LabelFrame(generate_frame, text="Image Preview")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.image_label = ttk.Label(self.preview_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Save image button
        save_btn = ttk.Button(generate_frame, text="Save Image", command=self.save_current_image)
        save_btn.pack(padx=10, pady=5)
    
    def create_template_tab(self):
        """Create template tab"""
        template_frame = ttk.Frame(self.notebook)
        self.notebook.add(template_frame, text="Templates")
        
        # Template list
        template_list_frame = ttk.LabelFrame(template_frame, text="Template List")
        template_list_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(template_list_frame, textvariable=self.template_var, state="readonly", width=30)
        self.template_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.template_combobox.bind("<<ComboboxSelected>>", self.on_template_selected)
        
        refresh_btn = ttk.Button(template_list_frame, text="Refresh", command=self.load_templates)
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Template management
        template_manage_frame = ttk.LabelFrame(template_frame, text="Template Management")
        template_manage_frame.pack(fill=tk.X, padx=10, pady=5)
        
        import_btn = ttk.Button(template_manage_frame, text="Import Workflow", command=self.import_workflow)
        import_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        save_template_btn = ttk.Button(template_manage_frame, text="Save as Template", command=self.save_as_template)
        save_template_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        delete_template_btn = ttk.Button(template_manage_frame, text="Delete Template", command=self.delete_template)
        delete_template_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Use template
        use_template_frame = ttk.LabelFrame(template_frame, text="Use Template")
        use_template_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(use_template_frame, text="Prompt Node ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.prompt_node_var = tk.StringVar(value="6")
        prompt_node_entry = ttk.Entry(use_template_frame, textvariable=self.prompt_node_var, width=5)
        prompt_node_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(use_template_frame, text="Negative Prompt Node ID:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.negative_node_var = tk.StringVar(value="7")
        negative_node_entry = ttk.Entry(use_template_frame, textvariable=self.negative_node_var, width=5)
        negative_node_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(use_template_frame, text="New Prompt (Optional):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W, columnspan=4)
        self.template_prompt_text = scrolledtext.ScrolledText(use_template_frame, height=4, width=60, wrap=tk.WORD)
        self.template_prompt_text.grid(row=2, column=0, padx=5, pady=5, sticky=tk.EW, columnspan=4)
        
        ttk.Label(use_template_frame, text="New Negative Prompt (Optional):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W, columnspan=4)
        self.template_negative_text = scrolledtext.ScrolledText(use_template_frame, height=3, width=60, wrap=tk.WORD)
        self.template_negative_text.grid(row=4, column=0, padx=5, pady=5, sticky=tk.EW, columnspan=4)
        
        # Use template button
        use_template_btn = ttk.Button(template_frame, text="Generate Image with Template", command=self.use_template)
        use_template_btn.pack(padx=10, pady=10)
    
    def create_settings_tab(self):
        """Create settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Output settings
        output_frame = ttk.LabelFrame(settings_frame, text="Output Settings")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(output_frame, text="Output Directory:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_var = tk.StringVar(value="output")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        browse_btn = ttk.Button(output_frame, text="Browse", command=self.browse_output_dir)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Save settings button
        save_settings_btn = ttk.Button(settings_frame, text="Save Settings", command=self.save_settings)
        save_settings_btn.pack(padx=10, pady=10)
        
        # About information
        about_frame = ttk.LabelFrame(settings_frame, text="About")
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        about_text = """ComfyUI Remote Client

This is a tool for connecting to ComfyUI servers, generating images, and downloading them locally.
You can generate images directly with prompts or use saved workflow templates.

Usage:
1. Connect to a ComfyUI server
2. Enter prompts or select a template
3. Click the generate button

Project: https://github.com/summerKK/comfyUI-remoteForge
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT)
        about_label.pack(padx=10, pady=10)
    
    def create_log_panel(self):
        """Create log panel"""
        log_frame = ttk.LabelFrame(self.root, text="Log")
        log_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def log(self, message):
        """
        Record log message
        
        Args:
            message: Log message
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        print(message)
    
    def clear_log(self):
        """Clear log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def connect_server(self):
        """Connect to server"""
        server_url = self.server_var.get()
        proxy = self.proxy_var.get()
        
        if not server_url:
            messagebox.showerror("Error", "Please enter server URL")
            return
        
        try:
            self.log(f"Connecting to server: {server_url}")
            if proxy:
                self.log(f"Using proxy: {proxy}")
            
            self.client = ComfyUIClient(server_url, proxy=proxy)
            self.log("Server connection successful")
            
            # Update prompt manager with server URL
            self.prompt_manager = PromptManager(server_url=server_url)
            self.log(f"Updated template manager to use server-specific directory")
            
            # Ensure there's a default template with SaveImage node
            self.prompt_manager.ensure_save_image_template("default_save")
            
            # Reload template list
            self.load_templates()
            
            # Update downloader
            self.downloader = ImageDownloader(self.output_var.get())
            
            messagebox.showinfo("Success", "Server connection successful")
        except Exception as e:
            self.log(f"Failed to connect to server: {str(e)}")
            messagebox.showerror("Error", f"Failed to connect to server: {str(e)}")
    
    def generate_image(self):
        """Generate image"""
        if not self.client:
            messagebox.showerror("Error", "Please connect to the server first")
            return
        
        positive_prompt = self.prompt_text.get(1.0, tk.END).strip()
        negative_prompt = self.negative_text.get(1.0, tk.END).strip()
        width = self.width_var.get()
        height = self.height_var.get()
        seed = self.seed_var.get()
        
        if not positive_prompt:
            messagebox.showerror("Error", "Please enter a positive prompt")
            return
        
        try:
            # Create workflow
            self.log(f"Creating basic workflow, prompt: {positive_prompt}")
            workflow = self.prompt_manager.create_basic_text2img_workflow(
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                width=width,
                height=height
            )
            
            # Generate image
            self.log("Starting image generation...")
            
            # Run generation process in a new thread
            threading.Thread(
                target=self._generate_thread,
                args=(workflow,),
                daemon=True
            ).start()
        
        except Exception as e:
            self.log(f"Failed to generate image: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate image: {str(e)}")
    
    def _generate_thread(self, workflow):
        """
        Generate image in a thread
        
        Args:
            workflow: Workflow JSON object
        """
        try:
            images_info, prompt_id = self.client.generate_image(workflow)
            
            # Download images
            if images_info:
                self.log(f"Image generation completed, starting download...")
                proxy = self.proxy_var.get()
                if proxy:
                    self.log(f"Using proxy to download image: {proxy}")
                saved_paths = self.downloader.download_images(self.client.server_url, images_info, proxy=proxy)
                
                if saved_paths:
                    self.log(f"Downloaded {len(saved_paths)} images")
                    # Update preview
                    self.last_image_path = saved_paths[0]
                    self.update_image_preview(saved_paths[0])
                else:
                    self.log("Failed to download images")
            else:
                self.log("No images were generated")
        
        except Exception as e:
            self.root.after(0, lambda: self.log(f"Failed to generate or download image: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to generate or download image: {str(e)}"))
    
    def update_image_preview(self, image_path):
        """
        Update image preview
        
        Args:
            image_path: Image path
        """
        try:
            # Update image preview in the main thread
            self.root.after(0, lambda: self._update_preview(image_path))
        except Exception as e:
            self.log(f"Failed to update image preview: {str(e)}")
    
    def _update_preview(self, image_path):
        """
        Update image preview in the main thread
        
        Args:
            image_path: Image path
        """
        try:
            image = Image.open(image_path)
            
            # Resize image to fit preview area
            preview_width = self.preview_frame.winfo_width() - 20
            preview_height = self.preview_frame.winfo_height() - 20
            
            if preview_width <= 0 or preview_height <= 0:
                preview_width = 400
                preview_height = 400
            
            # Maintain aspect ratio
            width, height = image.size
            ratio = min(preview_width / width, preview_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # Resize image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Display image
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # Keep a reference
            
            self.log(f"Image preview updated: {image_path}")
        except Exception as e:
            self.log(f"Failed to update image preview: {str(e)}")
    
    def save_current_image(self):
        """Save current preview image"""
        if not self.last_image_path:
            messagebox.showerror("Error", "No image to save")
            return
        
        try:
            # Open file dialog
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
            )
            
            if save_path:
                # Copy image
                image = Image.open(self.last_image_path)
                image.save(save_path)
                self.log(f"Image saved to: {save_path}")
                messagebox.showinfo("Success", f"Image saved to: {save_path}")
        
        except Exception as e:
            self.log(f"Failed to save image: {str(e)}")
            messagebox.showerror("Error", f"Failed to save image: {str(e)}")
    
    def load_templates(self):
        """Load template list"""
        try:
            templates = self.prompt_manager.list_templates()
            self.template_combobox["values"] = templates
            
            if templates:
                self.template_combobox.current(0)
                self.log(f"Loaded {len(templates)} templates")
            else:
                self.log("No templates available")
        
        except Exception as e:
            self.log(f"Failed to load template list: {str(e)}")
    
    def on_template_selected(self, event):
        """
        Callback when template is selected
        
        Args:
            event: Event object
        """
        template_name = self.template_var.get()
        if not template_name:
            return
        
        try:
            self.current_template = template_name
            self.log(f"Selected template: {template_name}")
            
            # Try to load template and auto-detect prompt node IDs
            try:
                workflow = self.prompt_manager.load_template(template_name)
                prompt_nodes = self.prompt_manager.detect_prompt_nodes(workflow)
                
                positive_node_id = prompt_nodes.get("positive")
                if positive_node_id:
                    self.prompt_node_var.set(positive_node_id)
                    self.log(f"Auto-set positive prompt node ID: {positive_node_id}")
                
                negative_node_id = prompt_nodes.get("negative")
                if negative_node_id:
                    self.negative_node_var.set(negative_node_id)
                    self.log(f"Auto-set negative prompt node ID: {negative_node_id}")
            except Exception as e:
                self.log(f"Failed to detect prompt node IDs: {str(e)}")
        
        except Exception as e:
            self.log(f"Failed to select template: {str(e)}")
    
    def import_workflow(self):
        """Import workflow JSON file"""
        try:
            # Open file dialog
            workflow_path = filedialog.askopenfilename(
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
            )
            
            if workflow_path:
                # Read workflow file
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    self.current_workflow = json.load(f)
                
                workflow_name = Path(workflow_path).stem
                self.log(f"Imported workflow: {workflow_name}")
                messagebox.showinfo("Success", f"Workflow imported: {workflow_name}")
        
        except Exception as e:
            self.log(f"Failed to import workflow: {str(e)}")
            messagebox.showerror("Error", f"Failed to import workflow: {str(e)}")
    
    def save_as_template(self):
        """Save current workflow as template"""
        if not self.current_workflow:
            messagebox.showerror("Error", "No current workflow to save")
            return
        
        try:
            # Show dialog to get template name
            template_name = simpledialog.askstring("Save Template", "Enter template name:")
            
            if not template_name:
                return
            
            # Save template
            self.prompt_manager.save_template(template_name, self.current_workflow)
            self.log(f"Template saved: {template_name}")
            messagebox.showinfo("Success", f"Template saved: {template_name}")
            
            # Refresh template list
            self.load_templates()
        
        except Exception as e:
            self.log(f"Failed to save template: {str(e)}")
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")
    
    def delete_template(self):
        """Delete currently selected template"""
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showerror("Error", "Please select a template first")
            return
        
        try:
            # Confirm deletion
            confirm = messagebox.askyesno("Confirm", f"Are you sure you want to delete template '{template_name}'?")
            
            if not confirm:
                return
            
            # Delete template
            self.prompt_manager.delete_template(template_name)
            self.log(f"Template deleted: {template_name}")
            messagebox.showinfo("Success", f"Template deleted: {template_name}")
            
            # Refresh template list
            self.load_templates()
        
        except Exception as e:
            self.log(f"Failed to delete template: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete template: {str(e)}")
    
    def use_template(self):
        """Use template to generate image"""
        if not self.client:
            messagebox.showerror("Error", "Please connect to the server first")
            return
        
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showerror("Error", "Please select a template first")
            return
        
        try:
            # Load template
            workflow = self.prompt_manager.load_template(template_name)
            
            # Auto-detect prompt node IDs
            prompt_nodes = self.prompt_manager.detect_prompt_nodes(workflow)
            positive_node_id = prompt_nodes.get("positive")
            negative_node_id = prompt_nodes.get("negative")
            
            # If auto-detection fails, use user-input node IDs
            if not positive_node_id:
                positive_node_id = self.prompt_node_var.get()
                self.log(f"Could not auto-detect positive prompt node, using user-provided ID: {positive_node_id}")
            else:
                self.log(f"Auto-detected positive prompt node ID: {positive_node_id}")
                # Update display
                self.prompt_node_var.set(positive_node_id)
            
            if not negative_node_id:
                negative_node_id = self.negative_node_var.get()
                self.log(f"Could not auto-detect negative prompt node, using user-provided ID: {negative_node_id}")
            else:
                self.log(f"Auto-detected negative prompt node ID: {negative_node_id}")
                # Update display
                self.negative_node_var.set(negative_node_id)
            
            # Update prompt (if provided)
            new_prompt = self.template_prompt_text.get(1.0, tk.END).strip()
            if new_prompt and positive_node_id:
                workflow = self.prompt_manager.update_prompt(workflow, positive_node_id, new_prompt)
                self.log(f"Updated positive prompt (Node ID: {positive_node_id}): {new_prompt}")
            elif new_prompt:
                self.log(f"Warning: Cannot update positive prompt because no valid prompt node ID was found")
            
            # Update negative prompt (if provided)
            new_negative = self.template_negative_text.get(1.0, tk.END).strip()
            if new_negative and negative_node_id:
                workflow = self.prompt_manager.update_negative_prompt(workflow, negative_node_id, new_negative)
                self.log(f"Updated negative prompt (Node ID: {negative_node_id}): {new_negative}")
            elif new_negative:
                self.log(f"Warning: Cannot update negative prompt because no valid negative prompt node ID was found")
            
            # Generate image
            self.log(f"Using template '{template_name}' to generate image...")
            
            # Run generation process in a new thread
            threading.Thread(
                target=self._generate_thread,
                args=(workflow,),
                daemon=True
            ).start()
        
        except Exception as e:
            self.log(f"Failed to generate image with template: {str(e)}")
            messagebox.showerror("Error", f"Failed to generate image with template: {str(e)}")
    
    def browse_output_dir(self):
        """Browse output directory"""
        output_dir = filedialog.askdirectory()
        if output_dir:
            self.output_var.set(output_dir)
            self.log(f"Output directory set to: {output_dir}")
    
    def save_settings(self):
        """Save settings"""
        try:
            # Update downloader's output directory
            output_dir = self.output_var.get()
            self.downloader = ImageDownloader(output_dir)
            
            self.log(f"Settings saved, output directory: {output_dir}")
            messagebox.showinfo("Success", "Settings saved")
        
        except Exception as e:
            self.log(f"Failed to save settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")


def main():
    """Main program entry"""
    root = tk.Tk()
    from tkinter import simpledialog
    app = ComfyUIRemoteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 