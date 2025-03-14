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
    """ComfyUI远程客户端GUI界面"""
    
    def __init__(self, root):
        """
        初始化GUI
        
        Args:
            root: tkinter根窗口
        """
        # 加载环境变量
        load_dotenv()
        
        self.root = root
        self.root.title("ComfyUI 远程客户端")
        self.root.geometry("960x720")
        self.root.resizable(True, True)
        
        # 创建样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10))
        self.style.configure("TEntry", font=("Arial", 10))
        
        # 初始化组件
        self.client = None
        self.prompt_manager = PromptManager()
        self.downloader = ImageDownloader()
        self.current_workflow = None
        self.current_template = None
        self.last_image_path = None
        
        # 创建主框架
        self.create_main_frame()
        
        # 默认服务器URL
        default_server = os.environ.get("COMFYUI_SERVER", "http://127.0.0.1:8188")
        self.server_var.set(default_server)
        
        # 尝试加载模板列表
        self.load_templates()
    
    def create_main_frame(self):
        """创建主框架"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建基本生成页面
        self.create_generate_tab()
        
        # 创建模板页面
        self.create_template_tab()
        
        # 创建设置页面
        self.create_settings_tab()
        
        # 创建日志面板
        self.create_log_panel()
    
    def create_generate_tab(self):
        """创建基本生成页面"""
        generate_frame = ttk.Frame(self.notebook)
        self.notebook.add(generate_frame, text="基本生成")
        
        # 服务器设置
        server_frame = ttk.LabelFrame(generate_frame, text="服务器设置")
        server_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(server_frame, text="服务器URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.server_var = tk.StringVar()
        server_entry = ttk.Entry(server_frame, textvariable=self.server_var, width=40)
        server_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        connect_btn = ttk.Button(server_frame, text="连接", command=self.connect_server)
        connect_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 添加代理设置
        ttk.Label(server_frame, text="代理服务器:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.proxy_var = tk.StringVar(value=os.environ.get("HTTP_PROXY", ""))
        proxy_entry = ttk.Entry(server_frame, textvariable=self.proxy_var, width=40)
        proxy_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # 提示词设置
        prompt_frame = ttk.LabelFrame(generate_frame, text="提示词设置")
        prompt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(prompt_frame, text="正面提示词:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=5, width=60, wrap=tk.WORD)
        self.prompt_text.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        ttk.Label(prompt_frame, text="负面提示词:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.NW)
        self.negative_text = scrolledtext.ScrolledText(prompt_frame, height=3, width=60, wrap=tk.WORD)
        self.negative_text.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # 图像设置
        image_frame = ttk.LabelFrame(generate_frame, text="图像设置")
        image_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(image_frame, text="宽度:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.width_var = tk.IntVar(value=512)
        width_entry = ttk.Entry(image_frame, textvariable=self.width_var, width=6)
        width_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(image_frame, text="高度:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.height_var = tk.IntVar(value=512)
        height_entry = ttk.Entry(image_frame, textvariable=self.height_var, width=6)
        height_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(image_frame, text="种子:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.seed_var = tk.IntVar(value=-1)
        seed_entry = ttk.Entry(image_frame, textvariable=self.seed_var, width=8)
        seed_entry.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # 生成按钮
        generate_btn = ttk.Button(generate_frame, text="生成图像", command=self.generate_image)
        generate_btn.pack(padx=10, pady=10)
        
        # 图像预览
        self.preview_frame = ttk.LabelFrame(generate_frame, text="图像预览")
        self.preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.image_label = ttk.Label(self.preview_frame)
        self.image_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 保存图像按钮
        save_btn = ttk.Button(generate_frame, text="保存图像", command=self.save_current_image)
        save_btn.pack(padx=10, pady=5)
    
    def create_template_tab(self):
        """创建模板页面"""
        template_frame = ttk.Frame(self.notebook)
        self.notebook.add(template_frame, text="模板")
        
        # 模板列表
        template_list_frame = ttk.LabelFrame(template_frame, text="模板列表")
        template_list_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.template_var = tk.StringVar()
        self.template_combobox = ttk.Combobox(template_list_frame, textvariable=self.template_var, state="readonly", width=30)
        self.template_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        self.template_combobox.bind("<<ComboboxSelected>>", self.on_template_selected)
        
        refresh_btn = ttk.Button(template_list_frame, text="刷新", command=self.load_templates)
        refresh_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 模板管理
        template_manage_frame = ttk.LabelFrame(template_frame, text="模板管理")
        template_manage_frame.pack(fill=tk.X, padx=10, pady=5)
        
        import_btn = ttk.Button(template_manage_frame, text="导入工作流", command=self.import_workflow)
        import_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        save_template_btn = ttk.Button(template_manage_frame, text="保存为模板", command=self.save_as_template)
        save_template_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        delete_template_btn = ttk.Button(template_manage_frame, text="删除模板", command=self.delete_template)
        delete_template_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 使用模板
        use_template_frame = ttk.LabelFrame(template_frame, text="使用模板")
        use_template_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Label(use_template_frame, text="提示词节点ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.prompt_node_var = tk.StringVar(value="6")
        prompt_node_entry = ttk.Entry(use_template_frame, textvariable=self.prompt_node_var, width=5)
        prompt_node_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(use_template_frame, text="负面提示词节点ID:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.negative_node_var = tk.StringVar(value="7")
        negative_node_entry = ttk.Entry(use_template_frame, textvariable=self.negative_node_var, width=5)
        negative_node_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(use_template_frame, text="新提示词 (可选):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W, columnspan=4)
        self.template_prompt_text = scrolledtext.ScrolledText(use_template_frame, height=4, width=60, wrap=tk.WORD)
        self.template_prompt_text.grid(row=2, column=0, padx=5, pady=5, sticky=tk.EW, columnspan=4)
        
        ttk.Label(use_template_frame, text="新负面提示词 (可选):").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W, columnspan=4)
        self.template_negative_text = scrolledtext.ScrolledText(use_template_frame, height=3, width=60, wrap=tk.WORD)
        self.template_negative_text.grid(row=4, column=0, padx=5, pady=5, sticky=tk.EW, columnspan=4)
        
        # 使用模板按钮
        use_template_btn = ttk.Button(template_frame, text="使用模板生成图像", command=self.use_template)
        use_template_btn.pack(padx=10, pady=10)
    
    def create_settings_tab(self):
        """创建设置页面"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="设置")
        
        # 输出设置
        output_frame = ttk.LabelFrame(settings_frame, text="输出设置")
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(output_frame, text="输出目录:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.output_var = tk.StringVar(value="output")
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=40)
        output_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        browse_btn = ttk.Button(output_frame, text="浏览", command=self.browse_output_dir)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # 保存设置按钮
        save_settings_btn = ttk.Button(settings_frame, text="保存设置", command=self.save_settings)
        save_settings_btn.pack(padx=10, pady=10)
        
        # 关于信息
        about_frame = ttk.LabelFrame(settings_frame, text="关于")
        about_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        about_text = """ComfyUI 远程客户端

这是一个用于连接ComfyUI服务器、生成图像并下载到本地的工具。
可以通过提示词直接生成图像，也可以使用保存的工作流模板。

使用方法：
1. 连接到ComfyUI服务器
2. 输入提示词或选择模板
3. 点击生成按钮

项目地址：https://github.com/yourusername/comfyui-remote-client
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT)
        about_label.pack(padx=10, pady=10)
    
    def create_log_panel(self):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(self.root, text="日志")
        log_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 清除日志按钮
        clear_log_btn = ttk.Button(log_frame, text="清除日志", command=self.clear_log)
        clear_log_btn.pack(side=tk.RIGHT, padx=5, pady=2)
    
    def log(self, message):
        """
        记录日志
        
        Args:
            message: 日志消息
        """
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        print(message)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def connect_server(self):
        """连接服务器"""
        server_url = self.server_var.get()
        proxy = self.proxy_var.get()
        
        if not server_url:
            messagebox.showerror("错误", "请输入服务器URL")
            return
        
        try:
            self.log(f"正在连接服务器: {server_url}")
            if proxy:
                self.log(f"使用代理: {proxy}")
            
            self.client = ComfyUIClient(server_url, proxy=proxy)
            self.log("服务器连接成功")
            
            # 更新提示词管理器，使用服务器URL
            self.prompt_manager = PromptManager(server_url=server_url)
            self.log(f"已更新模板管理器使用服务器特定目录")
            
            # 确保存在带有SaveImage节点的默认模板
            self.prompt_manager.ensure_save_image_template("default_save")
            
            # 重新加载模板列表
            self.load_templates()
            
            # 更新下载器
            self.downloader = ImageDownloader(self.output_var.get())
            
            messagebox.showinfo("成功", "服务器连接成功")
        except Exception as e:
            self.log(f"连接服务器失败: {str(e)}")
            messagebox.showerror("错误", f"连接服务器失败: {str(e)}")
    
    def generate_image(self):
        """生成图像"""
        if not self.client:
            messagebox.showerror("错误", "请先连接服务器")
            return
        
        positive_prompt = self.prompt_text.get(1.0, tk.END).strip()
        negative_prompt = self.negative_text.get(1.0, tk.END).strip()
        width = self.width_var.get()
        height = self.height_var.get()
        seed = self.seed_var.get()
        
        if not positive_prompt:
            messagebox.showerror("错误", "请输入正面提示词")
            return
        
        try:
            # 创建工作流
            self.log(f"创建基本工作流，提示词: {positive_prompt}")
            workflow = self.prompt_manager.create_basic_text2img_workflow(
                positive_prompt=positive_prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                width=width,
                height=height
            )
            
            # 生成图像
            self.log("开始生成图像...")
            
            # 在新线程中运行生成过程
            threading.Thread(
                target=self._generate_thread,
                args=(workflow,),
                daemon=True
            ).start()
        
        except Exception as e:
            self.log(f"生成图像失败: {str(e)}")
            messagebox.showerror("错误", f"生成图像失败: {str(e)}")
    
    def _generate_thread(self, workflow):
        """
        在线程中生成图像
        
        Args:
            workflow: 工作流JSON对象
        """
        try:
            images_info, prompt_id = self.client.generate_image(workflow)
            
            # 下载图像
            if images_info:
                self.log(f"图像生成完成，开始下载...")
                proxy = self.proxy_var.get()
                if proxy:
                    self.log(f"使用代理下载图像: {proxy}")
                saved_paths = self.downloader.download_images(self.client.server_url, images_info, proxy=proxy)
                
                if saved_paths:
                    self.log(f"已下载 {len(saved_paths)} 张图像")
                    # 更新预览
                    self.last_image_path = saved_paths[0]
                    self.update_image_preview(saved_paths[0])
                else:
                    self.log("下载图像失败")
            else:
                self.log("未生成任何图像")
        
        except Exception as e:
            self.root.after(0, lambda: self.log(f"生成或下载图像失败: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("错误", f"生成或下载图像失败: {str(e)}"))
    
    def update_image_preview(self, image_path):
        """
        更新图像预览
        
        Args:
            image_path: 图像路径
        """
        try:
            # 在主线程中更新图像预览
            self.root.after(0, lambda: self._update_preview(image_path))
        except Exception as e:
            self.log(f"更新图像预览失败: {str(e)}")
    
    def _update_preview(self, image_path):
        """
        在主线程中更新图像预览
        
        Args:
            image_path: 图像路径
        """
        try:
            image = Image.open(image_path)
            
            # 调整图像大小以适应预览区域
            preview_width = self.preview_frame.winfo_width() - 20
            preview_height = self.preview_frame.winfo_height() - 20
            
            if preview_width <= 0 or preview_height <= 0:
                preview_width = 400
                preview_height = 400
            
            # 保持纵横比
            width, height = image.size
            ratio = min(preview_width / width, preview_height / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            
            # 调整图像大小
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 显示图像
            photo = ImageTk.PhotoImage(image)
            self.image_label.config(image=photo)
            self.image_label.image = photo  # 保持引用
            
            self.log(f"图像预览已更新: {image_path}")
        except Exception as e:
            self.log(f"更新图像预览失败: {str(e)}")
    
    def save_current_image(self):
        """保存当前预览的图像"""
        if not self.last_image_path:
            messagebox.showerror("错误", "没有可保存的图像")
            return
        
        try:
            # 打开文件对话框
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG 图像", "*.png"), ("所有文件", "*.*")]
            )
            
            if save_path:
                # 复制图像
                image = Image.open(self.last_image_path)
                image.save(save_path)
                self.log(f"图像已保存到: {save_path}")
                messagebox.showinfo("成功", f"图像已保存到: {save_path}")
        
        except Exception as e:
            self.log(f"保存图像失败: {str(e)}")
            messagebox.showerror("错误", f"保存图像失败: {str(e)}")
    
    def load_templates(self):
        """加载模板列表"""
        try:
            templates = self.prompt_manager.list_templates()
            self.template_combobox["values"] = templates
            
            if templates:
                self.template_combobox.current(0)
                self.log(f"已加载 {len(templates)} 个模板")
            else:
                self.log("没有可用的模板")
        
        except Exception as e:
            self.log(f"加载模板列表失败: {str(e)}")
    
    def on_template_selected(self, event):
        """
        选择模板时的回调函数
        
        Args:
            event: 事件对象
        """
        template_name = self.template_var.get()
        if not template_name:
            return
        
        try:
            self.current_template = template_name
            self.log(f"已选择模板: {template_name}")
            
            # 尝试加载模板并自动检测提示词节点ID
            try:
                workflow = self.prompt_manager.load_template(template_name)
                prompt_nodes = self.prompt_manager.detect_prompt_nodes(workflow)
                
                positive_node_id = prompt_nodes.get("positive")
                if positive_node_id:
                    self.prompt_node_var.set(positive_node_id)
                    self.log(f"已自动设置正面提示词节点ID: {positive_node_id}")
                
                negative_node_id = prompt_nodes.get("negative")
                if negative_node_id:
                    self.negative_node_var.set(negative_node_id)
                    self.log(f"已自动设置负面提示词节点ID: {negative_node_id}")
            except Exception as e:
                self.log(f"检测提示词节点ID失败: {str(e)}")
        
        except Exception as e:
            self.log(f"选择模板失败: {str(e)}")
    
    def import_workflow(self):
        """导入工作流JSON文件"""
        try:
            # 打开文件对话框
            workflow_path = filedialog.askopenfilename(
                filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
            )
            
            if workflow_path:
                # 读取工作流文件
                with open(workflow_path, 'r', encoding='utf-8') as f:
                    self.current_workflow = json.load(f)
                
                workflow_name = Path(workflow_path).stem
                self.log(f"已导入工作流: {workflow_name}")
                messagebox.showinfo("成功", f"工作流已导入: {workflow_name}")
        
        except Exception as e:
            self.log(f"导入工作流失败: {str(e)}")
            messagebox.showerror("错误", f"导入工作流失败: {str(e)}")
    
    def save_as_template(self):
        """将当前工作流保存为模板"""
        if not self.current_workflow:
            messagebox.showerror("错误", "没有当前工作流可保存")
            return
        
        try:
            # 弹出对话框获取模板名称
            template_name = simpledialog.askstring("保存模板", "请输入模板名称:")
            
            if not template_name:
                return
            
            # 保存模板
            self.prompt_manager.save_template(template_name, self.current_workflow)
            self.log(f"模板已保存: {template_name}")
            messagebox.showinfo("成功", f"模板已保存: {template_name}")
            
            # 刷新模板列表
            self.load_templates()
        
        except Exception as e:
            self.log(f"保存模板失败: {str(e)}")
            messagebox.showerror("错误", f"保存模板失败: {str(e)}")
    
    def delete_template(self):
        """删除当前选中的模板"""
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showerror("错误", "请先选择模板")
            return
        
        try:
            # 确认删除
            confirm = messagebox.askyesno("确认", f"确定要删除模板 '{template_name}' 吗？")
            
            if not confirm:
                return
            
            # 删除模板
            self.prompt_manager.delete_template(template_name)
            self.log(f"模板已删除: {template_name}")
            messagebox.showinfo("成功", f"模板已删除: {template_name}")
            
            # 刷新模板列表
            self.load_templates()
        
        except Exception as e:
            self.log(f"删除模板失败: {str(e)}")
            messagebox.showerror("错误", f"删除模板失败: {str(e)}")
    
    def use_template(self):
        """使用模板生成图像"""
        if not self.client:
            messagebox.showerror("错误", "请先连接服务器")
            return
        
        template_name = self.template_var.get()
        if not template_name:
            messagebox.showerror("错误", "请先选择模板")
            return
        
        try:
            # 加载模板
            workflow = self.prompt_manager.load_template(template_name)
            
            # 自动检测提示词节点ID
            prompt_nodes = self.prompt_manager.detect_prompt_nodes(workflow)
            positive_node_id = prompt_nodes.get("positive")
            negative_node_id = prompt_nodes.get("negative")
            
            # 如果无法自动检测，则使用用户输入的节点ID
            if not positive_node_id:
                positive_node_id = self.prompt_node_var.get()
                self.log(f"未能自动检测正面提示词节点，使用用户输入的ID: {positive_node_id}")
            else:
                self.log(f"自动检测到正面提示词节点ID: {positive_node_id}")
                # 更新界面显示
                self.prompt_node_var.set(positive_node_id)
            
            if not negative_node_id:
                negative_node_id = self.negative_node_var.get()
                self.log(f"未能自动检测负面提示词节点，使用用户输入的ID: {negative_node_id}")
            else:
                self.log(f"自动检测到负面提示词节点ID: {negative_node_id}")
                # 更新界面显示
                self.negative_node_var.set(negative_node_id)
            
            # 更新提示词（如果提供）
            new_prompt = self.template_prompt_text.get(1.0, tk.END).strip()
            if new_prompt and positive_node_id:
                workflow = self.prompt_manager.update_prompt(workflow, positive_node_id, new_prompt)
                self.log(f"已更新正面提示词 (节点ID: {positive_node_id}): {new_prompt}")
            elif new_prompt:
                self.log(f"警告: 无法更新正面提示词，因为未找到有效的提示词节点ID")
            
            # 更新负面提示词（如果提供）
            new_negative = self.template_negative_text.get(1.0, tk.END).strip()
            if new_negative and negative_node_id:
                workflow = self.prompt_manager.update_negative_prompt(workflow, negative_node_id, new_negative)
                self.log(f"已更新负面提示词 (节点ID: {negative_node_id}): {new_negative}")
            elif new_negative:
                self.log(f"警告: 无法更新负面提示词，因为未找到有效的负面提示词节点ID")
            
            # 生成图像
            self.log(f"使用模板 '{template_name}' 生成图像...")
            
            # 在新线程中运行生成过程
            threading.Thread(
                target=self._generate_thread,
                args=(workflow,),
                daemon=True
            ).start()
        
        except Exception as e:
            self.log(f"使用模板生成图像失败: {str(e)}")
            messagebox.showerror("错误", f"使用模板生成图像失败: {str(e)}")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        output_dir = filedialog.askdirectory()
        if output_dir:
            self.output_var.set(output_dir)
            self.log(f"输出目录已设置为: {output_dir}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 更新下载器的输出目录
            output_dir = self.output_var.get()
            self.downloader = ImageDownloader(output_dir)
            
            self.log(f"设置已保存，输出目录: {output_dir}")
            messagebox.showinfo("成功", "设置已保存")
        
        except Exception as e:
            self.log(f"保存设置失败: {str(e)}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")


def main():
    """主程序入口"""
    root = tk.Tk()
    from tkinter import simpledialog
    app = ComfyUIRemoteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 