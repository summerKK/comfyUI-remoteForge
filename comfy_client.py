#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
import time
import websocket
import requests
import os
from urllib.parse import urlparse, urlunparse


class ComfyUIClient:
    """ComfyUI API客户端，用于与ComfyUI服务器交互生成图像"""
    
    def __init__(self, server_url=None, proxy=None):
        """
        初始化ComfyUI客户端
        
        Args:
            server_url: ComfyUI服务器URL，默认为本地地址
            proxy: 代理服务器地址，格式为"http://host:port"或"socks5://host:port"
        """
        # 设置默认服务器URL
        if server_url is None:
            server_url = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188/api")
        
        # 处理URL格式
        if server_url.endswith("/"):
            server_url = server_url[:-1]
        if not server_url.endswith("/api"):
            if "/api" not in server_url:
                server_url = f"{server_url}/api"
        
        self.server_url = server_url
        self.client_id = str(uuid.uuid4())
        
        # 解析URL，获取WebSocket URL
        url_parts = urlparse(server_url)
        scheme = "ws" if url_parts.scheme == "http" else "wss"
        base_url = f"{scheme}://{url_parts.netloc}"
        api_path = url_parts.path
        if api_path.endswith("/api"):
            api_path = api_path[:-4]
        self.ws_url = f"{base_url}{api_path}/ws?clientId={self.client_id}"
        
        # 设置代理
        self.proxy = proxy
        self.proxies = None
        if proxy:
            if proxy.startswith(("http://", "https://", "socks5://", "socks4://")):
                self.proxies = {
                    "http": proxy,
                    "https": proxy
                }
            else:
                print(f"警告: 不支持的代理格式: {proxy}，格式应为 'http://host:port' 或 'socks5://host:port'")
        
        print(f"ComfyUI 客户端初始化完成")
        print(f"服务器URL: {self.server_url}")
        print(f"WebSocket URL: {self.ws_url}")
        if self.proxies:
            print(f"代理设置: {self.proxy}")
        else:
            print("未设置代理")
        
        # 检查服务器连接
        self.check_server_connection()
    
    def check_server_connection(self):
        """检查服务器连接状态"""
        try:
            response = requests.get(f"{self.server_url}/system_stats", proxies=self.proxies)
            if response.status_code != 200:
                raise ConnectionError(f"无法连接到ComfyUI服务器，状态码: {response.status_code}")
            print(f"成功连接到ComfyUI服务器: {self.server_url}")
            return True
        except requests.RequestException as e:
            raise ConnectionError(f"连接ComfyUI服务器失败: {str(e)}")
    
    def get_workflow_api(self, workflow_api_id):
        """
        获取指定的工作流API
        
        Args:
            workflow_api_id: 工作流API ID或名称
        
        Returns:
            工作流API JSON对象
        """
        try:
            response = requests.get(f"{self.server_url}/object_info", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"获取工作流API失败，状态码: {response.status_code}")
            
            workflow_apis = response.json().get("api", {}).get("workflow", [])
            for api in workflow_apis:
                if api.get("id") == workflow_api_id or api.get("name") == workflow_api_id:
                    return api
            
            raise ValueError(f"未找到ID或名称为 '{workflow_api_id}' 的工作流API")
        except requests.RequestException as e:
            raise Exception(f"获取工作流API失败: {str(e)}")
    
    def queue_prompt(self, workflow):
        """
        将工作流提交到队列
        
        Args:
            workflow: 工作流JSON对象
            
        Returns:
            提示ID和工作流ID
        """
        try:
            # 添加调试信息
            print(f"正在提交工作流到: {self.server_url}/prompt")
            
            # 确保工作流具有正确的结构
            if "nodes" in workflow and "links" not in workflow:
                print("警告: 工作流缺少links字段，这可能导致错误")
            
            # 准备提交数据
            prompt_data = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            
            # 调试时打印工作流结构（仅首层键）
            print(f"工作流结构包含以下键: {list(workflow.keys())}")
            
            response = requests.post(
                f"{self.server_url}/prompt",
                json=prompt_data,
                proxies=self.proxies
            )
            
            if response.status_code != 200:
                print(f"服务器响应: {response.text[:200]}...")  # 打印部分响应以便调试
                raise Exception(f"提交工作流失败，状态码: {response.status_code}")
            
            data = response.json()
            return data.get("prompt_id"), data.get("node_id", None)
        except requests.RequestException as e:
            raise Exception(f"提交工作流失败: {str(e)}")
    
    def wait_for_generation(self, prompt_id, timeout=300):
        """
        等待图像生成完成
        
        Args:
            prompt_id: 提示ID
            timeout: 超时时间（秒）
            
        Returns:
            生成的图像信息
        """
        # 设置WebSocket代理
        ws_opts = {}
        if self.proxy:
            if self.proxy.startswith("http://"):
                ws_opts["http_proxy_host"] = self.proxy.split("://")[1].split(":")[0]
                ws_opts["http_proxy_port"] = int(self.proxy.split("://")[1].split(":")[1])
            elif self.proxy.startswith("socks5://"):
                ws_opts["socks5_host"] = self.proxy.split("://")[1].split(":")[0]
                ws_opts["socks5_port"] = int(self.proxy.split("://")[1].split(":")[1])
        
        ws = websocket.WebSocket()
        try:
            ws.connect(self.ws_url, **ws_opts)
        except Exception as e:
            raise ConnectionError(f"WebSocket连接失败: {str(e)}")
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                message = ws.recv()
                if not message:
                    continue
                
                data = json.loads(message)
                
                # 处理不同类型的消息
                if data["type"] == "executing":
                    node_id = data["data"]["node"]
                    print(f"正在执行节点: {node_id}")
                
                elif data["type"] == "progress":
                    progress = data["data"]["value"]
                    max_progress = data["data"]["max"]
                    percent = (progress / max_progress) * 100
                    print(f"生成进度: {percent:.2f}%")
                
                elif data["type"] == "executed":
                    # 添加调试信息
                    print(f"执行完成消息：{json.dumps(data['data'], indent=2, ensure_ascii=False)[:500]}...")
                    
                    # 检查是否有图像输出 - SaveImage
                    if "output" in data["data"] and "images" in data["data"]["output"]:
                        images_info = []
                        for image in data["data"]["output"]["images"]:
                            # 添加图像的完整数据，包括可能的base64内容或其他信息
                            img_data = {
                                "filename": image["filename"],
                                "subfolder": image.get("subfolder", ""),
                                "type": image.get("type", "output")
                            }
                            if "image" in image:  # 有些服务器直接返回base64图像数据
                                img_data["image_data"] = image["image"]
                            images_info.append(img_data)
                        if images_info:
                            print("图像生成完成！")
                            return images_info
                    
                    # 检查是否为PreviewImage节点返回的图像数据
                    elif "output" in data["data"] and isinstance(data["data"]["output"], dict):
                        node_type = data["data"].get("class_type", "")
                        node_id = data["data"].get("node_id", "unknown")
                        
                        # 查找可能的图像数据字段
                        for key, value in data["data"]["output"].items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                # 可能是图像数据列表
                                if "image" in value[0] or "tensor" in value[0]:
                                    images_info = []
                                    for i, img in enumerate(value):
                                        img_data = {
                                            "filename": f"preview_{node_id}_{i}.png",
                                            "subfolder": "",
                                            "type": "preview"
                                        }
                                        if "image" in img:
                                            img_data["image_data"] = img["image"]
                                        elif "tensor" in img:
                                            img_data["image_data"] = img["tensor"]
                                        images_info.append(img_data)
                                    
                                    if images_info:
                                        print(f"找到PreviewImage节点({node_id})返回的图像数据！")
                                        return images_info
                    
                    # 检查是否为单张图像数据
                    elif "output" in data["data"] and "image" in data["data"]["output"]:
                        node_id = data["data"].get("node_id", "unknown")
                        image_data = data["data"]["output"]["image"]
                        images_info = [{
                            "filename": f"preview_{node_id}.png",
                            "subfolder": "",
                            "type": "preview",
                            "image_data": image_data
                        }]
                        print(f"找到单张图像数据！")
                        return images_info
                
                elif data["type"] == "status":
                    if data["data"]["status"]["exec_info"]["queue_remaining"] == 0:
                        print("队列中所有任务已完成！")
                
                elif data["type"] == "error":
                    raise Exception(f"生成过程中出错: {data['data']['message']}")
                
            raise TimeoutError(f"等待图像生成超时（{timeout}秒）")
        finally:
            ws.close()
    
    def get_image_url(self, filename, subfolder=""):
        """
        获取生成图像的URL
        
        Args:
            filename: 图像文件名
            subfolder: 子文件夹名称
            
        Returns:
            图像URL
        """
        # 确保服务器URL正确（去掉/api如果存在）
        base_url = self.server_url
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
            
        if subfolder:
            return f"{base_url}/view?filename={filename}&subfolder={subfolder}"
        return f"{base_url}/view?filename={filename}"
    
    def get_history(self, prompt_id):
        """
        获取历史记录
        
        Args:
            prompt_id: 提示ID
            
        Returns:
            历史记录详情
        """
        try:
            response = requests.get(f"{self.server_url}/history/{prompt_id}", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"获取历史记录失败，状态码: {response.status_code}")
            
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"获取历史记录失败: {str(e)}")
    
    def generate_image(self, workflow, wait=True, timeout=300):
        """
        生成图像的主要方法
        
        Args:
            workflow: 工作流JSON对象
            wait: 是否等待生成完成
            timeout: 超时时间（秒）
            
        Returns:
            生成的图像信息和提示ID
        """
        prompt_id, _ = self.queue_prompt(workflow)
        print(f"工作流已提交，提示ID: {prompt_id}")
        
        if wait:
            images_info = self.wait_for_generation(prompt_id, timeout)
            return images_info, prompt_id
        
        return None, prompt_id
    
    def get_server_info(self):
        """
        获取服务器信息，包括可用模型等
        
        Returns:
            服务器信息JSON对象
        """
        try:
            response = requests.get(f"{self.server_url}/object_info", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"获取服务器信息失败，状态码: {response.status_code}")
            
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"获取服务器信息失败: {str(e)}")
            
    def get_available_models(self):
        """
        获取服务器上可用的模型列表
        
        Returns:
            可用模型列表
        """
        try:
            info = self.get_server_info()
            if "CheckpointLoaderSimple" in info.get("object_info", {}):
                input_info = info["object_info"]["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"]
                if isinstance(input_info, list) and len(input_info) > 0:
                    return input_info
            
            return []
        except Exception as e:
            print(f"无法获取可用模型列表: {str(e)}")
            return [] 