#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse


class PromptManager:
    """Prompt manager class, used to build and manage prompt templates"""
    
    def __init__(self, templates_dir="templates", server_url=None):
        """
        Initialize prompt manager
        
        Args:
            templates_dir: Main templates directory path
            server_url: Server URL, used to determine server-specific template subdirectory
        """
        self.base_templates_dir = templates_dir
        self.server_url = server_url
        
        # If server URL is provided, create server-specific template subdirectory
        if server_url:
            # Extract server address and port from URL
            parsed_url = urlparse(server_url)
            # Process URL, remove trailing "/api" if exists
            path = parsed_url.path
            if path.endswith('/api'):
                path = path[:-4]
            
            # Create safe directory name (remove protocol part and illegal characters)
            server_dir = f"{parsed_url.netloc}{path}".replace(':', '_').replace('/', '_')
            self.templates_dir = os.path.join(templates_dir, server_dir)
            print(f"Using server-specific template directory: {self.templates_dir}")
        else:
            self.templates_dir = templates_dir
        
        self._ensure_templates_dir_exists()
    
    def _ensure_templates_dir_exists(self):
        """Ensure template directory exists"""
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Also ensure the base template directory exists
        if self.templates_dir != self.base_templates_dir:
            os.makedirs(self.base_templates_dir, exist_ok=True)
    
    def save_template(self, name, workflow):
        """
        Save workflow template
        
        Args:
            name: Template name
            workflow: Workflow JSON object
        """
        template_path = Path(self.templates_dir) / f"{name}.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        print(f"Template saved: {template_path}")
    
    def load_template(self, name):
        """
        Load workflow template. First try to load from server-specific directory, if not exists, then load from base directory.
        
        Args:
            name: Template name
            
        Returns:
            Workflow JSON object
        """
        # First try to load from server-specific directory
        template_path = Path(self.templates_dir) / f"{name}.json"
        
        # If the template doesn't exist in server-specific directory, try to load from base directory
        if not template_path.exists() and self.templates_dir != self.base_templates_dir:
            base_template_path = Path(self.base_templates_dir) / f"{name}.json"
            if base_template_path.exists():
                template_path = base_template_path
                print(f"Using template from base directory: {template_path}")
            else:
                raise FileNotFoundError(f"Template not found: Checked {template_path} and {base_template_path}")
        elif not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
            
        # Check and convert template format to adapt to different ComfyUI server versions
        # Some servers expect a direct object with node IDs as keys, not nested in "nodes"
        if "nodes" in workflow:
            print(f"Converting template format: from nested nodes format to flat format")
            return workflow["nodes"]
        
        return workflow
    
    def list_templates(self, include_base=True):
        """
        List all available templates
        
        Args:
            include_base: Whether to include templates from base directory
            
        Returns:
            List of template names
        """
        self._ensure_templates_dir_exists()
        templates = set()
        
        # Add templates from server-specific directory
        for file in Path(self.templates_dir).glob("*.json"):
            templates.add(file.stem)
        
        # If requested and paths are different, add templates from base directory
        if include_base and self.templates_dir != self.base_templates_dir:
            for file in Path(self.base_templates_dir).glob("*.json"):
                templates.add(file.stem)
        
        return sorted(list(templates))
    
    def delete_template(self, name):
        """
        Delete template
        
        Args:
            name: Template name
        """
        template_path = Path(self.templates_dir) / f"{name}.json"
        if not template_path.exists() and self.templates_dir != self.base_templates_dir:
            # Check base directory
            base_template_path = Path(self.base_templates_dir) / f"{name}.json"
            if base_template_path.exists():
                template_path = base_template_path
            else:
                raise FileNotFoundError(f"Template not found: Checked {template_path} and {base_template_path}")
        elif not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        os.remove(template_path)
        print(f"Template deleted: {template_path}")
    
    def update_prompt(self, workflow, node_id, prompt_text):
        """
        Update prompt text in workflow
        
        Args:
            workflow: Workflow JSON object
            node_id: Prompt node ID
            prompt_text: New prompt text
            
        Returns:
            Updated workflow JSON object
        """
        # If workflow is in nested format
        if "nodes" in workflow and node_id in workflow["nodes"]:
            node = workflow["nodes"][node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            else:
                raise ValueError(f"Node {node_id} is not a valid prompt node")
        # If workflow is in flat format
        elif node_id in workflow:
            node = workflow[node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            else:
                raise ValueError(f"Node {node_id} is not a valid prompt node")
        else:
            raise ValueError(f"Node ID does not exist: {node_id}")
        
        return workflow
    
    def update_negative_prompt(self, workflow, node_id, negative_prompt):
        """
        Update negative prompt text in workflow
        
        Args:
            workflow: Workflow JSON object
            node_id: Negative prompt node ID
            negative_prompt: New negative prompt text
            
        Returns:
            Updated workflow JSON object
        """
        # If workflow is in nested format
        if "nodes" in workflow and node_id in workflow["nodes"]:
            node = workflow["nodes"][node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = negative_prompt
            else:
                raise ValueError(f"Node {node_id} is not a valid prompt node")
        # If workflow is in flat format
        elif node_id in workflow:
            node = workflow[node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = negative_prompt
            else:
                raise ValueError(f"Node {node_id} is not a valid prompt node")
        else:
            raise ValueError(f"Node ID does not exist: {node_id}")
        
        return workflow
    
    def create_basic_text2img_workflow(self, positive_prompt, negative_prompt="", seed=-1, width=512, height=512):
        """
        Create basic text-to-image workflow
        
        Args:
            positive_prompt: Positive prompt
            negative_prompt: Negative prompt
            seed: Random seed
            width: Image width
            height: Image height
            
        Returns:
            Workflow JSON object
        """
        # For compatibility with most ComfyUI servers, use a simplified workflow
        workflow = {
            "3": {
                "inputs": {
                    "seed": seed if seed >= 0 else 0,
                    "steps": 20,
                    "cfg": 7.5,
                    "sampler_name": "euler_a",
                    "scheduler": "normal",
                    "denoise": 1.0,
                    "model": ["4", 0],
                    "positive": ["6", 0],
                    "negative": ["7", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "KSampler"
            },
            "4": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "5": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "6": {
                "inputs": {
                    "text": positive_prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "7": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["4", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "8": {
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                },
                "class_type": "VAEDecode"
            },
            "9": {
                "inputs": {
                    "images": ["8", 0],
                    "filename_prefix": "ComfyUI"
                },
                "class_type": "SaveImage"
            }
        }
        
        # ComfyUI API now expects direct node objects, not nested in nodes
        return workflow
    
    def ensure_save_image_template(self, template_name="default"):
        """
        Ensure a template with SaveImage node is available.
        If it doesn't exist, create a basic template.
        
        Args:
            template_name: Template name
            
        Returns:
            Template name
        """
        # Check if template exists
        template_path = Path(self.templates_dir) / f"{template_name}.json"
        if template_path.exists():
            return template_name
            
        # Create basic template
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": "high quality, fine details, realistic, high definition photography",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "text": "low quality, blurry, distorted, error, noise",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "4": {
                "inputs": {
                    "width": 512,
                    "height": 768,
                    "batch_size": 1
                },
                "class_type": "EmptyLatentImage"
            },
            "5": {
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
                },
                "class_type": "KSampler"
            },
            "6": {
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            "7": {
                "inputs": {
                    "images": ["6", 0],
                    "filename_prefix": "ComfyUI"
                },
                "class_type": "SaveImage"
            }
        }
        
        # Save template
        self.save_template(template_name, workflow)
        print(f"Created default SaveImage template: {template_name}")
        
        return template_name 
        
    def detect_prompt_nodes(self, workflow):
        """
        Automatically detect prompt node IDs in workflow
        
        Args:
            workflow: Workflow JSON object
            
        Returns:
            Dictionary containing positive and negative prompt node IDs
        """
        positive_node_id = None
        negative_node_id = None
        
        # First find KSampler node
        ksampler_node_id = None
        
        # Check workflow format
        is_nested = "nodes" in workflow
        nodes_dict = workflow["nodes"] if is_nested else workflow
        
        # Find KSampler node
        for node_id, node in nodes_dict.items():
            if node.get("class_type") == "KSampler":
                ksampler_node_id = node_id
                break
        
        if not ksampler_node_id:
            print("Warning: KSampler node not found, cannot detect prompt nodes through sampler")
            # Continue with other methods
        else:
            # Get KSampler node input configuration
            sampler_node = nodes_dict[ksampler_node_id]
            sampler_inputs = sampler_node.get("inputs", {})
            
            # Get source nodes for positive and negative inputs
            positive_input = sampler_inputs.get("positive")
            negative_input = sampler_inputs.get("negative")
            
            # Extract source node IDs
            if positive_input and isinstance(positive_input, list) and len(positive_input) > 0:
                positive_node_id = positive_input[0]
                print(f"Detected positive prompt node ID through KSampler positive input: {positive_node_id}")
            
            if negative_input and isinstance(negative_input, list) and len(negative_input) > 0:
                negative_node_id = negative_input[0]
                print(f"Detected negative prompt node ID through KSampler negative input: {negative_node_id}")
            
            # Verify these nodes are CLIPTextEncode type
            if positive_node_id and positive_node_id in nodes_dict:
                if nodes_dict[positive_node_id].get("class_type") != "CLIPTextEncode":
                    print(f"Warning: Node {positive_node_id} is not CLIPTextEncode type")
                    positive_node_id = None
                    
            if negative_node_id and negative_node_id in nodes_dict:
                if nodes_dict[negative_node_id].get("class_type") != "CLIPTextEncode":
                    print(f"Warning: Node {negative_node_id} is not CLIPTextEncode type")
                    negative_node_id = None
        
        # If cannot determine or failed to determine using KSampler, try to find through type and name heuristics
        if not positive_node_id or not negative_node_id:
            # Find all CLIPTextEncode nodes
            clip_nodes = []
            
            for node_id, node in nodes_dict.items():
                if node.get("class_type") == "CLIPTextEncode":
                    meta = node.get("_meta", {})
                    title = meta.get("title", "").lower()
                    inputs = node.get("inputs", {})
                    input_text = inputs.get("text", "").lower()
                    
                    # Collect node information for analysis
                    clip_nodes.append({
                        "id": node_id,
                        "title": title,
                        "text": input_text,
                        "is_negative": False
                    })
            
            # If multiple CLIPTextEncode nodes found, try to distinguish positive and negative prompts through content analysis
            if len(clip_nodes) == 2:  # Most common case: one positive, one negative
                # Try to distinguish positive/negative
                for node in clip_nodes:
                    title = node["title"]
                    text = node["text"]
                    
                    # Check title
                    if ("negative" in title or "neg" in title):
                        node["is_negative"] = True
                    # Check content for negative keywords
                    elif any(term in text for term in ["low quality", "bad", "worst", 
                                                      "ugly", "error", "distortion", "blur", 
                                                      "noise", "distorted", "deformed"]):
                        node["is_negative"] = True
                    
                # Assign node IDs
                for node in clip_nodes:
                    if node["is_negative"] and not negative_node_id:
                        negative_node_id = node["id"]
                        print(f"Detected negative prompt node ID through content analysis: {negative_node_id}")
                    elif not node["is_negative"] and not positive_node_id:
                        positive_node_id = node["id"]
                        print(f"Detected positive prompt node ID through content analysis: {positive_node_id}")
                
                # If only one was determined and the other wasn't, assume the other one is the opposite type
                if positive_node_id and not negative_node_id and len(clip_nodes) == 2:
                    for node in clip_nodes:
                        if node["id"] != positive_node_id:
                            negative_node_id = node["id"]
                            print(f"Determined negative prompt node ID by elimination: {negative_node_id}")
                            break
                            
                elif negative_node_id and not positive_node_id and len(clip_nodes) == 2:
                    for node in clip_nodes:
                        if node["id"] != negative_node_id:
                            positive_node_id = node["id"]
                            print(f"Determined positive prompt node ID by elimination: {positive_node_id}")
                            break
            
            # If only one CLIPTextEncode node, assume it's the positive prompt
            elif len(clip_nodes) == 1:
                positive_node_id = clip_nodes[0]["id"]
                print(f"Found only one CLIPTextEncode node, assuming it's positive prompt node ID: {positive_node_id}")
            
            # If multiple CLIPTextEncode nodes but can't determine, use the first one as positive prompt
            elif len(clip_nodes) > 2:
                print(f"Found multiple CLIPTextEncode nodes({len(clip_nodes)}), but cannot determine which one is positive/negative")
                # Use the first one as positive prompt
                if not positive_node_id and clip_nodes:
                    positive_node_id = clip_nodes[0]["id"]
                    print(f"Selected first CLIPTextEncode node as positive prompt node ID: {positive_node_id}")
        
        result = {
            "positive": positive_node_id,
            "negative": negative_node_id
        }
        
        print(f"Detection result - Positive prompt node: {positive_node_id}, Negative prompt node: {negative_node_id}")
        return result 