# ComfyUI-RemoteForge

A powerful remote client for ComfyUI that allows you to connect to ComfyUI servers, generate images, and download them to your local machine. It supports both GUI and command-line interfaces, proxy settings, and template management.

## Features

- Connect to local or remote ComfyUI servers
- Generate images with simple text prompts
- Use advanced workflow templates
- Support for proxy connections
- Save and manage workflow templates
- Download generated images automatically
- User-friendly graphical interface
- Command-line interface for automation

## Installation

### Prerequisites

- Python 3.8 or higher
- ComfyUI server (local or remote)

### Setup with Virtual Environment

1. Clone the repository:

```bash
git clone https://github.com/yourusername/ComfyUI-RemoteForge.git
cd ComfyUI-RemoteForge
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

## Usage

### Graphical User Interface

1. Run the GUI application:

```bash
python gui.py
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
python main.py generate --prompt "your prompt here" --negative "negative prompt here"
```

2. Use a template to generate an image:

```bash
python main.py template --name "template_name" --prompt "optional new prompt"
```

3. List available templates:

```bash
python main.py list-templates
```

4. Save a workflow as a template:

```bash
python main.py save-template --name "template_name" --workflow "path/to/workflow.json"
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