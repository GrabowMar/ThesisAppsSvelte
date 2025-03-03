import os
import shutil
import json
import datetime
from typing import List, Dict, Tuple
from pathlib import Path

class PortManager:
    """Manages port allocation across all models"""
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501  # Moved frontend ports to 5500+ range
    PORTS_PER_APP = 2  # Each app needs 2 ports (backend + frontend)
    BUFFER_PORTS = 20  # Buffer between models to allow for future expansion
    APPS_PER_MODEL = 30

    # Updated model list based on your requirements
    MODEL_COLORS = {
        "Llama": "#f97316",
        "Mistral": "#9333ea",  # Updated from Mixtral to Mistral
        "DeepSeek": "#fa8c16",
        "GPT4o": "#10a37f",    # Updated from ChatGPT4o to GPT4o
        "Claude": "#7b2bf9",   # Updated from ClaudeSonnet to Claude
        "Gemini": "#1a73e8",
        "Grok": "#ff4d4f",
        "R1": "#fa541c",       # New model, using Qwen's color
        "O3": "#0ca57f"        # Updated from ChatGPTo3 to O3
    }

    @classmethod
    def calculate_port_range(cls, model_index: int) -> Tuple[int, int]:
        """Calculate port ranges for a specific model index"""
        ports_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        backend_start = cls.BASE_BACKEND_PORT + (model_index * ports_needed)
        frontend_start = cls.BASE_FRONTEND_PORT + (model_index * ports_needed)
        return backend_start, frontend_start

    @classmethod
    def get_port_info(cls, model_index: int, app_number: int) -> Dict[str, int]:
        """Get specific ports for an app within a model"""
        backend_base, frontend_base = cls.calculate_port_range(model_index)
        return {
            'backend': backend_base + (app_number - 1) * 2,
            'frontend': frontend_base + (app_number - 1) * 2
        }

class ProjectConfig:
    def __init__(self, model_name: str, model_index: int):
        self.model_name = model_name
        self.base_dir = f"C:/Users/grabowmar/Desktop/ThesisAppsSvelte/{model_name}"
        self.app_prefix = "app"
        self.total_apps = 20
        # Get port ranges from PortManager
        self.backend_base, self.frontend_base = PortManager.calculate_port_range(model_index)
        self.python_base_image = "python:3.14-slim"
        self.deno_base_image = "denoland/deno"
        self.log_file = f"setup_{model_name.lower()}.log"
        self.color = PortManager.MODEL_COLORS.get(model_name, "#666666")

    def get_ports_for_app(self, app_num: int) -> Dict[str, int]:
        """Get the specific ports for an app number"""
        return {
            'backend': self.backend_base + (app_num - 1) * 2,
            'frontend': self.frontend_base + (app_num - 1) * 2
        }

    def get_port_ranges(self) -> Dict[str, Dict[str, int]]:
        """Get the full port range information for this model"""
        return {
            'backend': {
                'start': self.backend_base,
                'end': self.backend_base + (self.total_apps * 2)
            },
            'frontend': {
                'start': self.frontend_base,
                'end': self.frontend_base + (self.total_apps * 2)
            }
        }

class ResourceTracker:
    def __init__(self):
        self.directories = []
        self.files = []

    def track_directory(self, directory):
        self.directories.append(directory)

    def track_file(self, file):
        self.files.append(file)

    def cleanup(self):
        for directory in self.directories:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                print(f"Deleted directory: {directory}")
        for file in self.files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Deleted file: {file}")

class MultiModelManager:
    def __init__(self):
        self.models = list(PortManager.MODEL_COLORS.keys())
        self.configs: Dict[str, ProjectConfig] = {}
        self.setup_configs()

    def setup_configs(self):
        for idx, model in enumerate(self.models):
            self.configs[model] = ProjectConfig(model, idx)
            # Log port ranges for verification
            ranges = self.configs[model].get_port_ranges()
            print(f"\nPort ranges for {model}:")
            print(f"Backend: {ranges['backend']['start']}-{ranges['backend']['end']}")
            print(f"Frontend: {ranges['frontend']['start']}-{ranges['frontend']['end']}")

    def create_all(self):
        for model in self.models:
            print(f"\nCreating apps for {model}...")
            config = self.configs[model]
            tracker = ResourceTracker()
            
            try:
                if not os.path.exists(config.base_dir):
                    os.makedirs(config.base_dir)
                    log_message(f"Created base directory: {config.base_dir}", config.log_file)

                for i in range(1, config.total_apps + 1):
                    project_dir = os.path.join(config.base_dir, f"{config.app_prefix}{i}")
                    ports = config.get_ports_for_app(i)
                    
                    os.makedirs(project_dir, exist_ok=True)
                    new_backend_setup(
                        os.path.join(project_dir, "backend"),
                        ports['backend'],
                        config.python_base_image,
                        model
                    )
                    new_frontend_setup(
                        os.path.join(project_dir, "frontend"),
                        ports['frontend'],
                        config.deno_base_image,
                        ports['backend'],
                        model
                    )
                    new_docker_compose(
                        project_dir, 
                        ports['backend'],
                        ports['frontend'],
                        model.lower()
                    )

                    tracker.track_directory(project_dir)
                    log_message(
                        f"Application {config.app_prefix}{i} created successfully for {model} "
                        f"(Backend: {ports['backend']}, Frontend: {ports['frontend']})",
                        config.log_file
                    )

                print(f"All applications created successfully for {model}!")
                ranges = config.get_port_ranges()
                print(f"Ports used - Backend: {ranges['backend']['start']}-{ranges['backend']['end']}")
                print(f"Ports used - Frontend: {ranges['frontend']['start']}-{ranges['frontend']['end']}")
                
            except Exception as e:
                print(f"Error in {model}: {e}")
                log_message(f"Error occurred in {model}: {e}", config.log_file)
                tracker.cleanup()

def log_message(message: str, log_file: str):
    """Log a message with timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def new_backend_setup(backend_dir: str, port: int, python_base_image: str, model_name: str):
    """Set up backend application"""
    os.makedirs(backend_dir, exist_ok=True)

    # Read and process app.py template
    with open("z_code_templates/backend/app.py.template", "r") as t:
        app_py_content = t.read()
    app_py_content = app_py_content.replace("{model_name}", model_name)
    app_py_content = app_py_content.replace("{port}", str(port))
    with open(os.path.join(backend_dir, "app.py"), "w") as f:
        f.write(app_py_content)

    # Copy requirements.txt
    with open("z_code_templates/backend/requirements.txt", "r") as t:
        reqs_content = t.read()
    with open(os.path.join(backend_dir, "requirements.txt"), "w") as f:
        f.write(reqs_content)

    # Read and process Dockerfile template
    with open("z_code_templates/backend/Dockerfile.template", "r") as t:
        dockerfile_content = t.read()
    dockerfile_content = dockerfile_content.replace("{python_base_image}", python_base_image)
    dockerfile_content = dockerfile_content.replace("{port}", str(port))
    with open(os.path.join(backend_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

def new_frontend_setup(frontend_dir: str, port: int, deno_base_image: str, backend_port: int, model_name: str):
    """Set up frontend application"""
    os.makedirs(os.path.join(frontend_dir, "src"), exist_ok=True)

    # package.json
    with open("z_code_templates/frontend/package.json.template", "r") as t:
        package_json = t.read()
    package_json = package_json.replace("{model_name_lower}", model_name.lower())
    with open(os.path.join(frontend_dir, "package.json"), "w") as f:
        f.write(package_json)

    # vite.config.js
    with open("z_code_templates/frontend/vite.config.js.template", "r") as t:
        vite_config = t.read()
    vite_config = vite_config.replace("{port}", str(port))
    with open(os.path.join(frontend_dir, "vite.config.js"), "w") as f:
        f.write(vite_config)

    # App.jsx
    with open("z_code_templates/frontend/src/App.jsx.template", "r") as t:
        app_react = t.read()
    app_react = app_react.replace("{model_name}", model_name)
    app_react = app_react.replace("{backend_port}", str(backend_port))
    with open(os.path.join(frontend_dir, "src", "App.jsx"), "w") as f:
        f.write(app_react)

    # App.css
    shutil.copy(
        "z_code_templates/frontend/src/App.css",
        os.path.join(frontend_dir, "src", "App.css")
    )

    # index.html
    with open("z_code_templates/frontend/index.html.template", "r") as t:
        index_html = t.read()
    index_html = index_html.replace("{model_name}", model_name)
    with open(os.path.join(frontend_dir, "index.html"), "w") as f:
        f.write(index_html)

    # Dockerfile
    with open("z_code_templates/frontend/Dockerfile.template", "r") as t:
        dockerfile_content = t.read()
    dockerfile_content = dockerfile_content.replace("{deno_base_image}", deno_base_image)
    dockerfile_content = dockerfile_content.replace("{port}", str(port))
    with open(os.path.join(frontend_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

def new_docker_compose(project_dir: str, backend_port: int, frontend_port: int, model_prefix: str):
    """Create docker-compose.yml file"""
    with open("z_code_templates/docker-compose.yml.template", "r") as t:
        compose_content = t.read()
    compose_content = compose_content.replace("{model_prefix}", model_prefix)
    compose_content = compose_content.replace("{backend_port}", str(backend_port))
    compose_content = compose_content.replace("{frontend_port}", str(frontend_port))
    with open(os.path.join(project_dir, "docker-compose.yml"), "w") as f:
        f.write(compose_content)
        
if __name__ == "__main__":
    manager = MultiModelManager()
    manager.create_all()
