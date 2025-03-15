# ComfyUI-RemoteForge

A powerful remote client for ComfyUI that allows you to connect to ComfyUI servers, generate images, and download them to your local machine. It supports both GUI and command-line interfaces, proxy settings, and template management.

## Features

- Connect to local or remote ComfyUI servers
- Generate images with simple text prompts
- Use advanced workflow templates
- Support for proxy connections
- Save and manage workflow templates
- Download generated images automatically
- Clean up server images after download
- User-friendly graphical interface
- Command-line interface for automation

## Installation

### Prerequisites

- Python 3.8 or higher
- ComfyUI server (local or remote)

### Setup with Virtual Environment

1. Clone the repository:

```bash
git clone git@github.com:summerKK/comfyUI-remoteForge.git
cd comfyUI-remoteForge
```

2. Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on the provided example:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your configuration:

```
COMFYUI_SERVER=http://127.0.0.1:8188
HTTP_PROXY=
```

### Server-side Setup for Image Deletion

To enable the "Delete from server after download" feature, you need to install the `comfyui_extra_api` plugin on your ComfyUI server:

1. Navigate to your ComfyUI custom_nodes directory:

```bash
cd ComfyUI/custom_nodes/
```

2. Clone the comfyui_extra_api repository:

```bash
git clone https://github.com/injet-zhou/comfyui_extra_api.git
```

3. Restart your ComfyUI server

After installation, the client will be able to delete images from the server after downloading them.

## Usage

### Graphical User Interface

1. Run the GUI application:

```bash
python run.py --gui
```

2. Enter your ComfyUI server URL (default: http://127.0.0.1:8188)
3. If needed, enter a proxy server address
4. Click "Connect" to establish connection to the server
5. Generate images using either:
   - The "Basic Generation" tab: Enter prompts and image settings
   - The "Templates" tab: Select a template and customize prompts

### Command Line Interface

The application provides several commands for command-line usage:

1. Generate an image with basic settings:

```bash
python run.py generate --prompt="your prompt here" --negative="negative prompt here"
```

2. Use a template to generate an image:

```bash
python run.py template --name=template_name --prompt="optional new prompt"
```

3. List available templates:

```bash
python run.py list-templates
```

4. Save a workflow as a template:

```bash
python run.py save-template --name=template_name --workflow=path/to/workflow.json
```

5. Delete images from server after download:

```bash
python run.py generate --prompt="your prompt here" --delete-after-download
python run.py template --name=template_name --delete-after-download
```

## Configuration

The application can be configured via:

1. Environment variables (in `.env` file)
2. Command-line arguments
3. GUI settings

Key configuration options:

- `COMFYUI_SERVER`: URL of the ComfyUI server
- `HTTP_PROXY`: Proxy server address for connections

## Folder Structure

- `output/`: Default directory for downloaded images
- `templates/`: Stores workflow templates (not included in repository)
  - The templates are organized by server to allow managing workflows for different ComfyUI instances
  - For each server, a subdirectory is created using the server hostname/IP
  - Example: `templates/127.0.0.1_8188/` for a local server running on port 8188
  - Example: `templates/my-remote-server.com_8188/` for a remote server
  - This organization allows you to maintain different templates for different ComfyUI servers
- `prompts.json`: Default prompt templates

## Templates and Random Seeds

When using templates, you can control the seed behavior:

- Setting `seed=-1` in a template will generate a random seed each time the template is loaded
- Setting a specific seed value (e.g., `seed=123456789`) will always use that exact seed
- The random seed generation happens automatically when loading templates with `seed=-1`
- This allows you to create templates that produce different results each time (with random seeds) or consistent results (with fixed seeds)

## Development

This project uses:

- `tkinter` for the GUI
- `requests` for HTTP communication
- `PIL/Pillow` for image processing
- `websocket-client` for WebSocket communication with ComfyUI

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ComfyUI project for the amazing stable diffusion interface
- All contributors and testers

## Prompt Management

The tool uses a `prompts.json` file to store and manage prompts. A sample template file `prompts.json.example` is provided.

To get started:

1. Copy the example file to create your own prompts file:
   ```bash
   cp prompts.json.example prompts.json
   ```

2. Edit the `prompts.json` file to add your own prompts.

3. Use the prompt management tool to view, add, or delete prompts:
   ```bash
   # List all prompts
   python run.py prompts list
   
   # View a specific prompt
   python run.py prompts view default
   
   # Add a new prompt
   python run.py prompts add --key=my_prompt --positive="positive prompt text" --negative="negative prompt text"
   
   # Delete a prompt
   python run.py prompts delete --key=my_prompt
   ```

Note: The `prompts.json` file is excluded from version control to avoid sharing personal prompts.

## Server Tools

```bash
# List available models on the server
python run.py server-tools list-models --server=http://your-server:8188

# Get server information
python run.py server-tools server-info --server=http://your-server:8188

# Create compatible workflow
python run.py server-tools create-workflow --name=my_workflow --server=http://your-server:8188
``` 