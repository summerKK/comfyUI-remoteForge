# ComfyUI-RemoteForge

ComfyUI-RemoteForge是一个功能强大的ComfyUI远程客户端，允许您连接到ComfyUI服务器、生成图像并将其下载到本地。它支持图形界面和命令行界面、代理设置和模板管理。

## 功能特点

- 连接到本地或远程ComfyUI服务器
- 使用简单文本提示词生成图像
- 使用高级工作流模板
- 支持代理连接
- 保存和管理工作流模板
- 自动下载生成的图像
- 用户友好的图形界面
- 支持自动化的命令行界面

## 安装

### 前提条件

- Python 3.8或更高版本
- ComfyUI服务器（本地或远程）

### 使用虚拟环境设置

1. 克隆仓库：

```bash
git@github.com:summerKK/comfyUI-remoteForge.git
cd comfyUI-remoteForge
```

2. 创建并激活虚拟环境：

```bash
# Windows系统
python -m venv venv
venv\Scripts\activate

# macOS/Linux系统
python -m venv venv
source venv/bin/activate
```

3. 安装所需依赖：

```bash
pip install -r requirements.txt
```

4. 基于提供的示例创建`.env`文件：

```bash
cp .env.example .env
```

5. 编辑`.env`文件，设置您的配置：

```
COMFYUI_SERVER=http://127.0.0.1:8188
HTTP_PROXY=
```

## 使用方法

### 图形用户界面

1. 运行GUI应用：

```bash
python gui.py
```

2. 输入您的ComfyUI服务器URL（默认：http://127.0.0.1:8188）
3. 如果需要，输入代理服务器地址
4. 点击"Connect"按钮建立与服务器的连接
5. 使用以下方式之一生成图像：
   - "Basic Generation"标签页：输入提示词和图像设置
   - "Templates"标签页：选择模板并自定义提示词

### 命令行界面

应用程序提供了几个命令行使用命令：

1. 使用基本设置生成图像：

```bash
python main.py generate --prompt "您的提示词" --negative "负面提示词"
```

2. 使用模板生成图像：

```bash
python main.py template --name "模板名称" --prompt "可选的新提示词"
```

3. 列出可用模板：

```bash
python main.py list-templates
```

4. 将工作流保存为模板：

```bash
python main.py save-template --name "模板名称" --workflow "工作流文件路径.json"
```

## 配置

应用程序可以通过以下方式配置：

1. 环境变量（在`.env`文件中）
2. 命令行参数
3. GUI设置

主要配置选项：

- `COMFYUI_SERVER`：ComfyUI服务器的URL
- `HTTP_PROXY`：连接的代理服务器地址

## 文件夹结构

- `output/`：下载图像的默认目录
- `templates/`：存储工作流模板（不包含在仓库中）
  - 模板按服务器进行组织，以便管理不同ComfyUI实例的工作流
  - 对于每个服务器，系统会使用服务器主机名/IP创建一个子目录
  - 示例：`templates/127.0.0.1_8188/`用于本地运行在8188端口的服务器
  - 示例：`templates/my-remote-server.com_8188/`用于远程服务器
  - 这种组织方式允许您为不同的ComfyUI服务器维护不同的模板
- `prompts.json`：默认提示词模板

## 开发

本项目使用：

- `tkinter`用于GUI
- `requests`用于HTTP通信
- `PIL/Pillow`用于图像处理
- `websocket-client`用于与ComfyUI进行WebSocket通信

## 许可证

本项目基于MIT许可证 - 详情请参阅LICENSE文件。

## 致谢

- ComfyUI项目提供的出色的稳定扩散界面
- 所有贡献者和测试者 