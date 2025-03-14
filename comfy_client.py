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
    """ComfyUI API client for interacting with ComfyUI server to generate images"""
    
    def __init__(self, server_url=None, proxy=None):
        """
        Initialize ComfyUI client
        
        Args:
            server_url: ComfyUI server URL, defaults to local address
            proxy: Proxy server address, format "http://host:port" or "socks5://host:port"
        """
        # Set default server URL
        if server_url is None:
            server_url = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188/api")
        
        # Process URL format
        if server_url.endswith("/"):
            server_url = server_url[:-1]
        if not server_url.endswith("/api"):
            if "/api" not in server_url:
                server_url = f"{server_url}/api"
        
        self.server_url = server_url
        self.client_id = str(uuid.uuid4())
        
        # Parse URL to get WebSocket URL
        url_parts = urlparse(server_url)
        scheme = "ws" if url_parts.scheme == "http" else "wss"
        base_url = f"{scheme}://{url_parts.netloc}"
        api_path = url_parts.path
        if api_path.endswith("/api"):
            api_path = api_path[:-4]
        self.ws_url = f"{base_url}{api_path}/ws?clientId={self.client_id}"
        
        # Set up proxy
        self.proxy = proxy
        self.proxies = None
        if proxy:
            if proxy.startswith(("http://", "https://", "socks5://", "socks4://")):
                self.proxies = {
                    "http": proxy,
                    "https": proxy
                }
            else:
                print(f"Warning: Unsupported proxy format: {proxy}, format should be 'http://host:port' or 'socks5://host:port'")
        
        print(f"ComfyUI client initialization complete")
        print(f"Server URL: {self.server_url}")
        print(f"WebSocket URL: {self.ws_url}")
        if self.proxies:
            print(f"Proxy settings: {self.proxy}")
        else:
            print("No proxy set")
        
        # Check server connection
        self.check_server_connection()
    
    def check_server_connection(self):
        """Check server connection status"""
        try:
            response = requests.get(f"{self.server_url}/system_stats", proxies=self.proxies)
            if response.status_code != 200:
                raise ConnectionError(f"Unable to connect to ComfyUI server, status code: {response.status_code}")
            print(f"Successfully connected to ComfyUI server: {self.server_url}")
            return True
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to ComfyUI server: {str(e)}")
    
    def get_workflow_api(self, workflow_api_id):
        """
        Get specified workflow API
        
        Args:
            workflow_api_id: Workflow API ID or name
        
        Returns:
            Workflow API JSON object
        """
        try:
            response = requests.get(f"{self.server_url}/object_info", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"Failed to get workflow API, status code: {response.status_code}")
            
            workflow_apis = response.json().get("api", {}).get("workflow", [])
            for api in workflow_apis:
                if api.get("id") == workflow_api_id or api.get("name") == workflow_api_id:
                    return api
            
            raise ValueError(f"No workflow API found with ID or name '{workflow_api_id}'")
        except requests.RequestException as e:
            raise Exception(f"Failed to get workflow API: {str(e)}")
    
    def queue_prompt(self, workflow):
        """
        Submit workflow to queue
        
        Args:
            workflow: Workflow JSON object
            
        Returns:
            Prompt ID and workflow ID
        """
        try:
            # Add debug info
            print(f"Submitting workflow to: {self.server_url}/prompt")
            
            # Ensure workflow has proper structure
            if "nodes" in workflow and "links" not in workflow:
                print("Warning: Workflow missing links field, this may cause errors")
            
            # Prepare submission data
            prompt_data = {
                "prompt": workflow,
                "client_id": self.client_id
            }
            
            # Debug print workflow structure (first level keys only)
            print(f"Workflow structure contains these keys: {list(workflow.keys())}")
            
            response = requests.post(
                f"{self.server_url}/prompt",
                json=prompt_data,
                proxies=self.proxies
            )
            
            if response.status_code != 200:
                print(f"Server response: {response.text[:200]}...")  # Print partial response for debugging
                raise Exception(f"Failed to submit workflow, status code: {response.status_code}")
            
            data = response.json()
            return data.get("prompt_id"), data.get("node_id", None)
        except requests.RequestException as e:
            raise Exception(f"Failed to submit workflow: {str(e)}")
    
    def wait_for_generation(self, prompt_id, timeout=300):
        """
        Wait for image generation to complete
        
        Args:
            prompt_id: Prompt ID
            timeout: Timeout in seconds
            
        Returns:
            Generated image info
        """
        # Set up WebSocket proxy
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
            raise ConnectionError(f"WebSocket connection failed: {str(e)}")
        
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                message = ws.recv()
                if not message:
                    continue
                
                data = json.loads(message)
                
                # Handle different message types
                if data["type"] == "executing":
                    node_id = data["data"]["node"]
                    print(f"Executing node: {node_id}")
                
                elif data["type"] == "progress":
                    progress = data["data"]["value"]
                    max_progress = data["data"]["max"]
                    percent = (progress / max_progress) * 100
                    print(f"Generation progress: {percent:.2f}%")
                
                elif data["type"] == "executed":
                    # Add debug info
                    print(f"Execution completed message: {json.dumps(data['data'], indent=2, ensure_ascii=False)[:500]}...")
                    
                    # Check for image output - SaveImage
                    if "output" in data["data"] and "images" in data["data"]["output"]:
                        images_info = []
                        for image in data["data"]["output"]["images"]:
                            # Add complete image data, including possible base64 content or other info
                            img_data = {
                                "filename": image["filename"],
                                "subfolder": image.get("subfolder", ""),
                                "type": image.get("type", "output")
                            }
                            if "image" in image:  # Some servers return base64 image data directly
                                img_data["image_data"] = image["image"]
                            images_info.append(img_data)
                        if images_info:
                            print("Image generation complete!")
                            return images_info
                    
                    # Check if it's PreviewImage node returning image data
                    elif "output" in data["data"] and isinstance(data["data"]["output"], dict):
                        node_type = data["data"].get("class_type", "")
                        node_id = data["data"].get("node_id", "unknown")
                        
                        # Look for possible image data fields
                        for key, value in data["data"]["output"].items():
                            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                                # Possibly an image data list
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
                                        print(f"Found PreviewImage node({node_id}) image data!")
                                        return images_info
                    
                    # Check for single image data
                    elif "output" in data["data"] and "image" in data["data"]["output"]:
                        node_id = data["data"].get("node_id", "unknown")
                        image_data = data["data"]["output"]["image"]
                        images_info = [{
                            "filename": f"preview_{node_id}.png",
                            "subfolder": "",
                            "type": "preview",
                            "image_data": image_data
                        }]
                        print(f"Found single image data!")
                        return images_info
                
                elif data["type"] == "status":
                    if data["data"]["status"]["exec_info"]["queue_remaining"] == 0:
                        print("All tasks in queue completed!")
                
                elif data["type"] == "error":
                    raise Exception(f"Error during generation: {data['data']['message']}")
                
            raise TimeoutError(f"Waiting for image generation timed out ({timeout} seconds)")
        finally:
            ws.close()
    
    def get_image_url(self, filename, subfolder=""):
        """
        Get URL for generated image
        
        Args:
            filename: Image filename
            subfolder: Subfolder name
            
        Returns:
            Image URL
        """
        # Ensure server URL is correct (remove /api if present)
        base_url = self.server_url
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
            
        if subfolder:
            return f"{base_url}/view?filename={filename}&subfolder={subfolder}"
        return f"{base_url}/view?filename={filename}"
    
    def get_history(self, prompt_id):
        """
        Get history record
        
        Args:
            prompt_id: Prompt ID
            
        Returns:
            History record details
        """
        try:
            response = requests.get(f"{self.server_url}/history/{prompt_id}", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"Failed to get history, status code: {response.status_code}")
            
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get history: {str(e)}")
    
    def generate_image(self, workflow, wait=True, timeout=300):
        """
        Main method to generate image
        
        Args:
            workflow: Workflow JSON object
            wait: Whether to wait for generation to complete
            timeout: Timeout in seconds
            
        Returns:
            Generated image info and prompt ID
        """
        prompt_id, _ = self.queue_prompt(workflow)
        print(f"Workflow submitted, prompt ID: {prompt_id}")
        
        if wait:
            images_info = self.wait_for_generation(prompt_id, timeout)
            return images_info, prompt_id
        
        return None, prompt_id
    
    def get_server_info(self):
        """
        Get server information, including available models
        
        Returns:
            Server info JSON object
        """
        try:
            response = requests.get(f"{self.server_url}/object_info", proxies=self.proxies)
            if response.status_code != 200:
                raise Exception(f"Failed to get server info, status code: {response.status_code}")
            
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to get server info: {str(e)}")
            
    def get_available_models(self):
        """
        Get list of available models on the server
        
        Returns:
            List of available models
        """
        try:
            info = self.get_server_info()
            if "CheckpointLoaderSimple" in info.get("object_info", {}):
                input_info = info["object_info"]["CheckpointLoaderSimple"]["input"]["required"]["ckpt_name"]
                if isinstance(input_info, list) and len(input_info) > 0:
                    return input_info
            
            return []
        except Exception as e:
            print(f"Unable to get available models list: {str(e)}")
            return [] 