#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import requests
from pathlib import Path
from tqdm import tqdm
from PIL import Image
from io import BytesIO
import datetime


class ImageDownloader:
    """用于下载和保存ComfyUI生成的图像"""
    
    def __init__(self, output_dir="output"):
        """
        初始化图像下载器
        
        Args:
            output_dir: 图像保存目录
        """
        self.output_dir = output_dir
        self._ensure_output_dir_exists()
    
    def _ensure_output_dir_exists(self):
        """确保输出目录存在"""
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _generate_filename(self, original_filename=None, prefix=None, extension=".png"):
        """
        生成文件名
        
        Args:
            original_filename: 原始文件名
            prefix: 文件名前缀
            extension: 文件扩展名
            
        Returns:
            生成的文件名
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if original_filename:
            # 保留原始文件名，但添加时间戳以避免冲突
            basename = Path(original_filename).stem
            return f"{basename}_{timestamp}{extension}"
        elif prefix:
            return f"{prefix}_{timestamp}{extension}"
        else:
            return f"image_{timestamp}{extension}"
    
    def download_image(self, image_url, filename=None, prefix=None, proxy=None):
        """
        下载单个图像
        
        Args:
            image_url: 图像URL
            filename: 保存的文件名
            prefix: 文件名前缀（如果未提供filename）
            proxy: 代理服务器地址，例如 "http://127.0.0.1:1080" 或 "socks5://127.0.0.1:1080"
            
        Returns:
            保存的图像路径
        """
        try:
            # 设置代理
            proxies = None
            if proxy:
                proxies = {
                    "http": proxy,
                    "https": proxy
                }
                print(f"使用代理下载图像: {proxy}")
            
            response = requests.get(image_url, stream=True, proxies=proxies)
            response.raise_for_status()
            
            # 确定文件名
            if not filename:
                filename = self._generate_filename(prefix=prefix)
            
            # 保存路径
            save_path = Path(self.output_dir) / filename
            
            # 下载图像
            file_size = int(response.headers.get('content-length', 0))
            progress = tqdm(total=file_size, unit='B', unit_scale=True, desc=f"下载 {filename}")
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))
            
            progress.close()
            print(f"图像已保存到: {save_path}")
            return str(save_path)
        
        except requests.RequestException as e:
            print(f"下载图像失败: {str(e)}")
            return None
    
    def download_images(self, server_url, images_info, proxy=None):
        """
        下载多个图像
        
        Args:
            server_url: ComfyUI服务器URL
            images_info: 图像信息列表
            proxy: 代理服务器地址，例如 "http://127.0.0.1:1080" 或 "socks5://127.0.0.1:1080"
            
        Returns:
            保存的图像路径列表
        """
        saved_paths = []
        
        # 确保服务器URL正确（去掉/api如果存在）
        base_url = server_url
        if base_url.endswith('/api'):
            base_url = base_url[:-4]
        
        for image_info in images_info:
            filename = image_info["filename"]
            subfolder = image_info.get("subfolder", "")
            
            # 优先使用图像数据（如果存在）
            if "image_data" in image_info:
                try:
                    # 从base64解码图像数据
                    import base64
                    from io import BytesIO
                    from PIL import Image
                    
                    # 提取base64数据（可能包含header）
                    image_data = image_info["image_data"]
                    if "," in image_data:  # 处理"data:image/png;base64,"格式
                        image_data = image_data.split(",", 1)[1]
                    
                    image_bytes = base64.b64decode(image_data)
                    image = Image.open(BytesIO(image_bytes))
                    
                    # 保存路径
                    save_path = os.path.join(self.output_dir, filename)
                    image.save(save_path)
                    
                    print(f"图像已保存到: {save_path}")
                    saved_paths.append(save_path)
                    continue
                except Exception as e:
                    print(f"处理图像数据失败，将尝试使用URL下载: {str(e)}")
            
            # 构建图像URL
            if subfolder:
                image_url = f"{base_url}/view?filename={filename}&subfolder={subfolder}"
            else:
                image_url = f"{base_url}/view?filename={filename}"
            
            # 下载图像
            saved_path = self.download_image(image_url, filename, proxy=proxy)
            if saved_path:
                saved_paths.append(saved_path)
        
        return saved_paths
    
    def save_image_from_bytes(self, image_bytes, filename=None, prefix=None):
        """
        从字节数据保存图像
        
        Args:
            image_bytes: 图像字节数据
            filename: 保存的文件名
            prefix: 文件名前缀（如果未提供filename）
            
        Returns:
            保存的图像路径
        """
        try:
            # 确定文件名
            if not filename:
                filename = self._generate_filename(prefix=prefix)
            
            # 保存路径
            save_path = Path(self.output_dir) / filename
            
            # 保存图像
            image = Image.open(BytesIO(image_bytes))
            image.save(save_path)
            
            print(f"图像已保存到: {save_path}")
            return str(save_path)
        
        except Exception as e:
            print(f"保存图像失败: {str(e)}")
            return None 