#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse


class PromptManager:
    """提示词管理类，用于构建和管理提示词模板"""
    
    def __init__(self, templates_dir="templates", server_url=None):
        """
        初始化提示词管理器
        
        Args:
            templates_dir: 主模板目录路径
            server_url: 服务器URL，用于确定特定服务器的模板子目录
        """
        self.base_templates_dir = templates_dir
        self.server_url = server_url
        
        # 如果提供了服务器URL，则创建特定服务器的模板子目录
        if server_url:
            # 从URL中提取服务器地址和端口
            parsed_url = urlparse(server_url)
            # 处理URL，移除末尾的"/api"如果存在
            path = parsed_url.path
            if path.endswith('/api'):
                path = path[:-4]
            
            # 创建安全的目录名（移除协议部分和非法字符）
            server_dir = f"{parsed_url.netloc}{path}".replace(':', '_').replace('/', '_')
            self.templates_dir = os.path.join(templates_dir, server_dir)
            print(f"使用服务器特定的模板目录: {self.templates_dir}")
        else:
            self.templates_dir = templates_dir
        
        self._ensure_templates_dir_exists()
    
    def _ensure_templates_dir_exists(self):
        """确保模板目录存在"""
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # 同时确保基本模板目录也存在
        if self.templates_dir != self.base_templates_dir:
            os.makedirs(self.base_templates_dir, exist_ok=True)
    
    def save_template(self, name, workflow):
        """
        保存工作流模板
        
        Args:
            name: 模板名称
            workflow: 工作流JSON对象
        """
        template_path = Path(self.templates_dir) / f"{name}.json"
        with open(template_path, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        print(f"模板已保存: {template_path}")
    
    def load_template(self, name):
        """
        加载工作流模板。首先尝试从服务器特定目录加载，如果不存在，则从基本目录加载。
        
        Args:
            name: 模板名称
            
        Returns:
            工作流JSON对象
        """
        # 首先尝试从服务器特定目录加载
        template_path = Path(self.templates_dir) / f"{name}.json"
        
        # 如果服务器特定目录中不存在该模板，则尝试从基本目录加载
        if not template_path.exists() and self.templates_dir != self.base_templates_dir:
            base_template_path = Path(self.base_templates_dir) / f"{name}.json"
            if base_template_path.exists():
                template_path = base_template_path
                print(f"使用基本目录中的模板: {template_path}")
            else:
                raise FileNotFoundError(f"模板不存在: 已检查 {template_path} 和 {base_template_path}")
        elif not template_path.exists():
            raise FileNotFoundError(f"模板不存在: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
            
        # 检查并转换模板格式，以适应不同的ComfyUI服务器版本
        # 有些服务器期望直接以节点ID为键的对象，而不是嵌套在"nodes"中
        if "nodes" in workflow:
            print(f"转换模板格式：从嵌套的nodes格式转换为扁平格式")
            return workflow["nodes"]
        
        return workflow
    
    def list_templates(self, include_base=True):
        """
        列出所有可用的模板
        
        Args:
            include_base: 是否包含基本目录中的模板
            
        Returns:
            模板名称列表
        """
        self._ensure_templates_dir_exists()
        templates = set()
        
        # 添加服务器特定目录中的模板
        for file in Path(self.templates_dir).glob("*.json"):
            templates.add(file.stem)
        
        # 如果请求且路径不同，则添加基本目录中的模板
        if include_base and self.templates_dir != self.base_templates_dir:
            for file in Path(self.base_templates_dir).glob("*.json"):
                templates.add(file.stem)
        
        return sorted(list(templates))
    
    def delete_template(self, name):
        """
        删除模板
        
        Args:
            name: 模板名称
        """
        template_path = Path(self.templates_dir) / f"{name}.json"
        if not template_path.exists() and self.templates_dir != self.base_templates_dir:
            # 检查基本目录
            base_template_path = Path(self.base_templates_dir) / f"{name}.json"
            if base_template_path.exists():
                template_path = base_template_path
            else:
                raise FileNotFoundError(f"模板不存在: 已检查 {template_path} 和 {base_template_path}")
        elif not template_path.exists():
            raise FileNotFoundError(f"模板不存在: {template_path}")
        
        os.remove(template_path)
        print(f"模板已删除: {template_path}")
    
    def update_prompt(self, workflow, node_id, prompt_text):
        """
        更新工作流中的提示词文本
        
        Args:
            workflow: 工作流JSON对象
            node_id: 提示词节点ID
            prompt_text: 新的提示词文本
            
        Returns:
            更新后的工作流JSON对象
        """
        # 如果工作流是嵌套格式
        if "nodes" in workflow and node_id in workflow["nodes"]:
            node = workflow["nodes"][node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            else:
                raise ValueError(f"节点 {node_id} 不是有效的提示词节点")
        # 如果工作流是扁平格式
        elif node_id in workflow:
            node = workflow[node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = prompt_text
            else:
                raise ValueError(f"节点 {node_id} 不是有效的提示词节点")
        else:
            raise ValueError(f"节点ID不存在: {node_id}")
        
        return workflow
    
    def update_negative_prompt(self, workflow, node_id, negative_prompt):
        """
        更新工作流中的负面提示词文本
        
        Args:
            workflow: 工作流JSON对象
            node_id: 负面提示词节点ID
            negative_prompt: 新的负面提示词文本
            
        Returns:
            更新后的工作流JSON对象
        """
        # 如果工作流是嵌套格式
        if "nodes" in workflow and node_id in workflow["nodes"]:
            node = workflow["nodes"][node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = negative_prompt
            else:
                raise ValueError(f"节点 {node_id} 不是有效的提示词节点")
        # 如果工作流是扁平格式
        elif node_id in workflow:
            node = workflow[node_id]
            if "inputs" in node and "text" in node["inputs"]:
                node["inputs"]["text"] = negative_prompt
            else:
                raise ValueError(f"节点 {node_id} 不是有效的提示词节点")
        else:
            raise ValueError(f"节点ID不存在: {node_id}")
        
        return workflow
    
    def create_basic_text2img_workflow(self, positive_prompt, negative_prompt="", seed=-1, width=512, height=512):
        """
        创建基本的文本到图像工作流
        
        Args:
            positive_prompt: 正面提示词
            negative_prompt: 负面提示词
            seed: 随机种子
            width: 图像宽度
            height: 图像高度
            
        Returns:
            工作流JSON对象
        """
        # 为了兼容大多数ComfyUI服务器，使用更简化的工作流
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
        
        # ComfyUI API现在预期直接使用节点对象，而不是嵌套在nodes中
        return workflow
    
    def ensure_save_image_template(self, template_name="default"):
        """
        确保有一个带SaveImage节点的模板可用。
        如果不存在，则创建一个基本的模板。
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板名称
        """
        # 检查模板是否存在
        template_path = Path(self.templates_dir) / f"{template_name}.json"
        if template_path.exists():
            return template_name
            
        # 创建基本模板
        workflow = {
            "1": {
                "inputs": {
                    "ckpt_name": "v1-5-pruned-emaonly.safetensors"
                },
                "class_type": "CheckpointLoaderSimple"
            },
            "2": {
                "inputs": {
                    "text": "高品质，精致细节，真实感，高清摄影",
                    "clip": ["1", 1]
                },
                "class_type": "CLIPTextEncode"
            },
            "3": {
                "inputs": {
                    "text": "低品质，模糊，畸变，错误，噪点",
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
        
        # 保存模板
        self.save_template(template_name, workflow)
        print(f"已创建默认SaveImage模板: {template_name}")
        
        return template_name 
        
    def detect_prompt_nodes(self, workflow):
        """
        自动检测工作流中的提示词节点ID
        
        Args:
            workflow: 工作流JSON对象
            
        Returns:
            包含正面提示词节点ID和负面提示词节点ID的字典
        """
        positive_node_id = None
        negative_node_id = None
        
        # 首先找到KSampler节点
        ksampler_node_id = None
        
        # 检查工作流格式
        is_nested = "nodes" in workflow
        nodes_dict = workflow["nodes"] if is_nested else workflow
        
        # 查找KSampler节点
        for node_id, node in nodes_dict.items():
            if node.get("class_type") == "KSampler":
                ksampler_node_id = node_id
                break
        
        if not ksampler_node_id:
            print("警告: 未找到KSampler节点，无法通过采样器检测提示词节点")
            # 继续尝试其他方法
        else:
            # 获取KSampler节点的输入配置
            sampler_node = nodes_dict[ksampler_node_id]
            sampler_inputs = sampler_node.get("inputs", {})
            
            # 获取positive和negative输入的源节点
            positive_input = sampler_inputs.get("positive")
            negative_input = sampler_inputs.get("negative")
            
            # 提取源节点ID
            if positive_input and isinstance(positive_input, list) and len(positive_input) > 0:
                positive_node_id = positive_input[0]
                print(f"通过KSampler节点的positive输入检测到正面提示词节点ID: {positive_node_id}")
            
            if negative_input and isinstance(negative_input, list) and len(negative_input) > 0:
                negative_node_id = negative_input[0]
                print(f"通过KSampler节点的negative输入检测到负面提示词节点ID: {negative_node_id}")
            
            # 验证这些节点是否为CLIPTextEncode类型
            if positive_node_id and positive_node_id in nodes_dict:
                if nodes_dict[positive_node_id].get("class_type") != "CLIPTextEncode":
                    print(f"警告: 节点 {positive_node_id} 不是CLIPTextEncode类型")
                    positive_node_id = None
                    
            if negative_node_id and negative_node_id in nodes_dict:
                if nodes_dict[negative_node_id].get("class_type") != "CLIPTextEncode":
                    print(f"警告: 节点 {negative_node_id} 不是CLIPTextEncode类型")
                    negative_node_id = None
        
        # 如果使用KSampler无法确定或确定失败，则尝试通过类型和名称启发式查找
        if not positive_node_id or not negative_node_id:
            # 找出所有CLIPTextEncode节点
            clip_nodes = []
            
            for node_id, node in nodes_dict.items():
                if node.get("class_type") == "CLIPTextEncode":
                    meta = node.get("_meta", {})
                    title = meta.get("title", "").lower()
                    inputs = node.get("inputs", {})
                    input_text = inputs.get("text", "").lower()
                    
                    # 收集节点信息以便分析
                    clip_nodes.append({
                        "id": node_id,
                        "title": title,
                        "text": input_text,
                        "is_negative": False
                    })
            
            # 如果找到了多个CLIPTextEncode节点，尝试通过内容分析区分正负面提示词
            if len(clip_nodes) == 2:  # 最常见的情况：一个正面一个负面
                # 尝试区分正负面
                for node in clip_nodes:
                    title = node["title"]
                    text = node["text"]
                    
                    # 检查标题
                    if ("负面" in title or "negative" in title or "反向" in title):
                        node["is_negative"] = True
                    # 检查内容中的负面关键词
                    elif any(term in text for term in ["低质量", "low quality", "bad", "worst", 
                                                      "ugly", "丑陋", "错误", "扭曲", "模糊", 
                                                      "噪点", "失真", "变形"]):
                        node["is_negative"] = True
                    
                # 分配节点ID
                for node in clip_nodes:
                    if node["is_negative"] and not negative_node_id:
                        negative_node_id = node["id"]
                        print(f"通过内容分析检测到负面提示词节点ID: {negative_node_id}")
                    elif not node["is_negative"] and not positive_node_id:
                        positive_node_id = node["id"]
                        print(f"通过内容分析检测到正面提示词节点ID: {positive_node_id}")
                
                # 如果只确定了一个，且另一个未确定，则假设另一个是相反的类型
                if positive_node_id and not negative_node_id and len(clip_nodes) == 2:
                    for node in clip_nodes:
                        if node["id"] != positive_node_id:
                            negative_node_id = node["id"]
                            print(f"通过排除法确定负面提示词节点ID: {negative_node_id}")
                            break
                            
                elif negative_node_id and not positive_node_id and len(clip_nodes) == 2:
                    for node in clip_nodes:
                        if node["id"] != negative_node_id:
                            positive_node_id = node["id"]
                            print(f"通过排除法确定正面提示词节点ID: {positive_node_id}")
                            break
            
            # 如果只有一个CLIPTextEncode节点，则假设它是正面提示词
            elif len(clip_nodes) == 1:
                positive_node_id = clip_nodes[0]["id"]
                print(f"只找到一个CLIPTextEncode节点，假设为正面提示词节点ID: {positive_node_id}")
            
            # 如果存在多个CLIPTextEncode节点但无法确定，则使用第一个作为正面提示词
            elif len(clip_nodes) > 2:
                print(f"找到多个CLIPTextEncode节点({len(clip_nodes)}个)，但无法确定哪个是正面/负面提示词")
                # 使用第一个作为正面提示词
                if not positive_node_id and clip_nodes:
                    positive_node_id = clip_nodes[0]["id"]
                    print(f"选择第一个CLIPTextEncode节点作为正面提示词节点ID: {positive_node_id}")
        
        result = {
            "positive": positive_node_id,
            "negative": negative_node_id
        }
        
        print(f"检测结果 - 正面提示词节点: {positive_node_id}, 负面提示词节点: {negative_node_id}")
        return result 