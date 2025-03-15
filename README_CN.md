# ComfyUI-RemoteForge

一个功能强大的ComfyUI远程客户端，允许您连接到ComfyUI服务器，生成图像并将其下载到本地机器。它支持图形界面和命令行界面、代理设置和模板管理。

## 功能特点

- 连接本地或远程ComfyUI服务器
- 使用简单的文本提示生成图像
- 使用高级工作流模板
- 支持代理连接
- 保存和管理工作流模板
- 自动下载生成的图像
- 用户友好的图形界面
- 用于自动化的命令行界面

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

5. 编辑`.env`文件设置您的配置：

```
COMFYUI_SERVER=http://127.0.0.1:8188
HTTP_PROXY=
```

## 使用方法

### 图形用户界面

1. 运行GUI应用程序：

```bash
python run.py --gui
```

2. 输入您的ComfyUI服务器URL（默认：http://127.0.0.1:8188）
3. 如果需要，输入代理服务器地址
4. 点击"连接"建立与服务器的连接
5. 使用以下方式生成图像：
   - "基本生成"选项卡：输入提示词和图像设置
   - "模板"选项卡：选择一个模板并自定义提示词

### 命令行界面

应用程序提供了多个命令行使用命令：

1. 使用基本设置生成图像：

```bash
python run.py generate --prompt="您的提示词" --negative="负面提示词"
```

2. 使用模板生成图像：

```bash
python run.py template --name=模板名称 --prompt="可选的新提示词"
```

3. 列出可用模板：

```bash
python run.py list-templates
```

4. 将工作流保存为模板：

```bash
python run.py save-template --name=模板名称 --workflow=工作流文件路径.json
```

## 配置

应用程序可以通过以下方式配置：

1. 环境变量（在`.env`文件中）
2. 命令行参数
3. GUI设置

主要配置选项：

- `COMFYUI_SERVER`：ComfyUI服务器URL
- `HTTP_PROXY`：连接用的代理服务器地址

## 文件夹结构

- `output/`：下载图像的默认目录
- `templates/`：存储工作流模板（不包含在仓库中）
  - 模板按服务器组织，以便管理不同ComfyUI实例的工作流
  - 为每个服务器创建一个使用服务器主机名/IP的子目录
  - 示例：`templates/127.0.0.1_8188/`用于本地端口8188上运行的服务器
  - 示例：`templates/my-remote-server.com_8188/`用于远程服务器
  - 这种组织方式允许您为不同的ComfyUI服务器维护不同的模板

## 模板和随机种子

使用模板时，您可以控制种子行为：

- 在模板中设置`seed=-1`将在每次加载模板时生成一个随机种子
- 设置特定的种子值（例如`seed=123456789`）将始终使用该确切的种子
- 当加载带有`seed=-1`的模板时，随机种子生成会自动发生
- 这允许您创建每次产生不同结果（使用随机种子）或一致结果（使用固定种子）的模板

## 开发

本项目使用：

- `tkinter`用于GUI
- `requests`用于HTTP通信
- `PIL/Pillow`用于图像处理
- `websocket-client`用于与ComfyUI的WebSocket通信

## 许可证

本项目根据MIT许可证授权 - 详情请参阅LICENSE文件。

## 致谢

- ComfyUI项目提供了出色的稳定扩散界面
- 所有贡献者和测试者

## 提示词管理

该工具使用`prompts.json`文件存储和管理提示词。提供了一个示例模板文件`prompts.json.example`。

使用步骤：

1. 复制示例文件创建您自己的提示词文件：
   ```bash
   cp prompts.json.example prompts.json
   ```

2. 编辑`prompts.json`文件添加您自己的提示词。

3. 使用提示词管理工具查看、添加或删除提示词：
   ```bash
   # 列出所有提示词
   python run.py prompts list
   
   # 查看特定提示词
   python run.py prompts view default
   
   # 添加新提示词
   python run.py prompts add --key=my_prompt --positive="正面提示词文本" --negative="负面提示词文本"
   
   # 删除提示词
   python run.py prompts delete --key=my_prompt
   ```

注意：`prompts.json`文件被排除在版本控制之外，以避免共享个人提示词。

## 服务器工具

```bash
# 列出服务器上可用的模型
python run.py server-tools list-models --server=http://您的服务器:8188

# 获取服务器信息
python run.py server-tools server-info --server=http://您的服务器:8188

# 创建兼容工作流
python run.py server-tools create-workflow --name=my_workflow --server=http://您的服务器:8188
``` 