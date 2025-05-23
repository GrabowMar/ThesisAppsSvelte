import os
import shutil
import json # Not explicitly used in the provided snippet, but often useful
import datetime
from typing import List, Dict, Tuple
from pathlib import Path

class PortManager:
    """Manages port allocation across all models"""
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501  # Moved frontend ports to 5500+ range
    PORTS_PER_APP = 2  # Each app needs 2 ports (backend + frontend)
    BUFFER_PORTS = 20  # Buffer between models to allow for future expansion
    APPS_PER_MODEL = 30 # Number of applications per model

    # Updated model list based on your requirements
    MODEL_COLORS = {
        "anthropic/claude-3.7-sonnet": "#D97706",
        "openai/gpt-4.1": "#14B8A6",
        "mistralai/devstral-small:free": "#8B5CF6",
        "google/gemma-3n-e4b-it:free": "#3B82F6",
        "meta-llama/llama-3.3-8b-instruct:free": "#F59E0B",
        "nousresearch/deephermes-3-mistral-24b-preview:free": "#EC4899",
        "microsoft/phi-4-reasoning-plus:free": "#6366F1",
        "qwen/qwen3-30b-a3b:free": "#F43F5E",
        "openai/codex-mini": "#22D3EE",
        "x-ai/grok-3-beta": "#EF4444",
        "inception/mercury-coder-small-beta": "#A855F7",
        "google/gemini-2.5-flash-preview-05-20": "#60A5FA",
        "meta-llama/llama-4-maverick:free": "#FBBF24",
        "qwen/qwen3-32b:free": "#E11D48",  # Mapped from "Qwen_Qwen3_32B"
        "meta-llama/llama-4-scout:free": "#FCD34D",
        "deepseek/deepseek-chat-v3-0324:free": "#F97316",
        "opengvlab/internvl3-14b:free": "#808080",  # Default color
        "thudm/glm-4-32b:free": "#808080",  # Default color
        "agentica-org/deepcoder-14b-preview:free": "#808080",  # Default color
        "rekaai/reka-flash-3:free": "#808080",  # Default color
        "open-r1/olympiccoder-32b:free": "#808080",  # Default color
    }

    @classmethod
    def calculate_port_range(cls, model_index: int) -> Tuple[int, int]:
        """Calculate port ranges for a specific model index"""
        # Calculate the total number of ports needed for one model's set of apps, including buffer
        ports_needed_per_model_block = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        
        backend_start = cls.BASE_BACKEND_PORT + (model_index * ports_needed_per_model_block)
        frontend_start = cls.BASE_FRONTEND_PORT + (model_index * ports_needed_per_model_block)
        return backend_start, frontend_start

    @classmethod
    def get_port_info(cls, model_index: int, app_number: int) -> Dict[str, int]:
        """Get specific ports for an app within a model. App_number is 1-based."""
        backend_base_for_model, frontend_base_for_model = cls.calculate_port_range(model_index)
        
        offset_for_app = (app_number - 1) * cls.PORTS_PER_APP
        
        return {
            'backend': backend_base_for_model + offset_for_app,
            'frontend': frontend_base_for_model + offset_for_app 
        }

class ProjectConfig:
    def __init__(self, model_name: str, model_index: int, base_project_path: str = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte"):
        self.model_name = model_name # Store original model name for display, logging, content replacement
        
        # Sanitize model_name for use in directory paths
        # Replace colon and forward slash, as they are invalid or undesired in Windows directory names for a flat structure.
        sanitized_model_name_for_dir_path = model_name.replace(":", "_").replace("/", "_")
        
        self.base_dir = os.path.join(base_project_path, "models", sanitized_model_name_for_dir_path)
        self.app_prefix = "app"
        self.total_apps = PortManager.APPS_PER_MODEL 
        
        self.backend_base_for_model, self.frontend_base_for_model = PortManager.calculate_port_range(model_index)
        
        self.python_base_image = "python:3.14-slim" 
        self.deno_base_image = "denoland/deno" 
        
        log_dir = os.path.join(base_project_path, "models", "_logs") 
        os.makedirs(log_dir, exist_ok=True)
        # Sanitize for log file *name* (different from path component sanitization)
        sanitized_model_name_for_log_filename = "".join(c if c.isalnum() else "_" for c in model_name)
        self.log_file = os.path.join(log_dir, f"setup_{sanitized_model_name_for_log_filename}.log")
        
        self.color = PortManager.MODEL_COLORS.get(model_name, "#666666") 

    def get_ports_for_app(self, app_num: int) -> Dict[str, int]:
        """Get the specific ports for an app number (1-based) for this model."""
        offset = (app_num - 1) * PortManager.PORTS_PER_APP
        return {
            'backend': self.backend_base_for_model + offset,
            'frontend': self.frontend_base_for_model + offset 
        }

    def get_port_ranges_for_model(self) -> Dict[str, Dict[str, int]]:
        """Get the full port range information for this model's apps."""
        last_app_offset = (self.total_apps - 1) * PortManager.PORTS_PER_APP
        
        return {
            'backend': {
                'start': self.backend_base_for_model,
                'end': self.backend_base_for_model + last_app_offset 
            },
            'frontend': {
                'start': self.frontend_base_for_model,
                'end': self.frontend_base_for_model + last_app_offset
            }
        }

class ResourceTracker:
    def __init__(self):
        self.directories: List[str] = []
        self.files: List[str] = []

    def track_directory(self, directory: str):
        self.directories.append(directory)

    def track_file(self, file_path: str):
        self.files.append(file_path)

    def cleanup(self):
        for directory in reversed(self.directories):
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"Deleted directory: {directory}")
                except OSError as e:
                    print(f"Error deleting directory {directory}: {e}")
        for file_path in self.files: 
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except OSError as e:
                    print(f"Error deleting file {file_path}: {e}")
        self.directories.clear()
        self.files.clear()

class MultiModelManager:
    def __init__(self, base_project_path: str = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte"):
        self.models = list(PortManager.MODEL_COLORS.keys())
        self.configs: Dict[str, ProjectConfig] = {}
        self.base_project_path = base_project_path
        self.setup_configs()

    def setup_configs(self):
        overall_models_dir = os.path.join(self.base_project_path, "models")
        os.makedirs(overall_models_dir, exist_ok=True) 

        for idx, model_name in enumerate(self.models):
            self.configs[model_name] = ProjectConfig(model_name, idx, self.base_project_path)
            ranges = self.configs[model_name].get_port_ranges_for_model()
            log_message(f"Port ranges for {model_name}:", self.configs[model_name].log_file)
            # Calculate the actual highest port used for the block (not including buffer for next model)
            highest_backend_port_in_block = ranges['backend']['end'] 
            highest_frontend_port_in_block = ranges['frontend']['end']
            if PortManager.PORTS_PER_APP > 1: # If each app uses more than one port from its base
                 highest_backend_port_in_block += (PortManager.PORTS_PER_APP -1) # Assuming backend is the first of the pair
                 highest_frontend_port_in_block += (PortManager.PORTS_PER_APP -1)


            log_message(f"  Backend: {ranges['backend']['start']}-{highest_backend_port_in_block}", self.configs[model_name].log_file)
            log_message(f"  Frontend: {ranges['frontend']['start']}-{highest_frontend_port_in_block}", self.configs[model_name].log_file)
            print(f"\nConfigured port ranges for {model_name}:") 
            print(f"  Backend: Start {ranges['backend']['start']}")
            print(f"  Frontend: Start {ranges['frontend']['start']}")

    def create_all(self):
        for model_name in self.models:
            print(f"\nCreating applications for model: {model_name}...")
            config = self.configs[model_name]
            tracker = ResourceTracker() 
            
            try:
                # config.base_dir is now sanitized
                os.makedirs(config.base_dir, exist_ok=True)
                log_message(f"Ensured base directory exists: {config.base_dir}", config.log_file)
                # tracker.track_directory(config.base_dir) # Track only if you intend to delete the whole model dir on app error

                for i in range(1, config.total_apps + 1):
                    project_dir = os.path.join(config.base_dir, f"{config.app_prefix}{i}")
                    ports = config.get_ports_for_app(i) 
                    
                    os.makedirs(project_dir, exist_ok=True)
                    tracker.track_directory(project_dir) 

                    log_message(f"Creating {config.app_prefix}{i} for {model_name} in {project_dir}", config.log_file)
                    
                    backend_dir = os.path.join(project_dir, "backend")
                    new_backend_setup(
                        backend_dir,
                        ports['backend'],
                        config.python_base_image,
                        model_name 
                    )
                    tracker.track_directory(backend_dir)

                    frontend_dir = os.path.join(project_dir, "frontend")
                    new_frontend_setup(
                        frontend_dir,
                        ports['frontend'],
                        config.deno_base_image,
                        ports['backend'], 
                        model_name 
                    )
                    tracker.track_directory(frontend_dir)

                    # Sanitize model_name for Docker Compose service prefix
                    # Replace slashes and colons, and convert to lowercase for Docker compatibility
                    service_prefix_sanitized = model_name.replace("/", "_").replace(":", "_").lower()
                    new_docker_compose(
                        project_dir, 
                        ports['backend'],
                        ports['frontend'],
                        f"{service_prefix_sanitized}_app{i}"
                    )
                    tracker.track_file(os.path.join(project_dir, "docker-compose.yml"))

                    log_message(
                        f"Application {config.app_prefix}{i} created for {model_name} "
                        f"(Backend Port: {ports['backend']}, Frontend Port: {ports['frontend']})",
                        config.log_file
                    )
                
                print(f"All {config.total_apps} applications created successfully for model: {model_name}!")
                final_ranges = config.get_port_ranges_for_model() 
                
                highest_backend_port = final_ranges['backend']['start'] + (config.total_apps - 1) * PortManager.PORTS_PER_APP
                highest_frontend_port = final_ranges['frontend']['start'] + (config.total_apps - 1) * PortManager.PORTS_PER_APP

                print(f"  Approximate ports used by {model_name}:")
                print(f"    Backend: {final_ranges['backend']['start']} to {highest_backend_port}")
                print(f"    Frontend: {final_ranges['frontend']['start']} to {highest_frontend_port}")
                log_message(f"Successfully created all apps for {model_name}.", config.log_file)

            except Exception as e:
                print(f"An error occurred while processing model {model_name}: {e}")
                log_message(f"CRITICAL ERROR for model {model_name}: {e}. Attempting cleanup...", config.log_file)
                # tracker.cleanup() # Cleanup resources for this model if an error occurs
                log_message(f"Cleanup for {model_name} attempted.", config.log_file)


def log_message(message: str, log_file_path: str):
    """Log a message with timestamp to a specific log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write to log file {log_file_path}: {e}")

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_BASE_DIR = SCRIPT_DIR / "z_code_templates"

def new_backend_setup(backend_dir: str, port: int, python_base_image: str, model_name: str):
    """Set up backend application. model_name is for template substitution."""
    os.makedirs(backend_dir, exist_ok=True)

    template_path = TEMPLATE_BASE_DIR / "backend" / "app.py.template"
    target_path = Path(backend_dir) / "app.py"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as t:
            app_py_content = t.read()
        app_py_content = app_py_content.replace("{model_name}", model_name) 
        app_py_content = app_py_content.replace("{port}", str(port))
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(app_py_content)
    else:
        print(f"Warning: Backend app.py template not found at {template_path}")

    template_req_path = TEMPLATE_BASE_DIR / "backend" / "requirements.txt" 
    target_req_path = Path(backend_dir) / "requirements.txt"
    if template_req_path.exists():
        shutil.copy(template_req_path, target_req_path)
    else:
        with open(target_req_path, "w", encoding="utf-8") as f:
            f.write("flask\nrequests\n# Add other dependencies here\n") 
        print(f"Warning: Backend requirements.txt template not found at {template_req_path}. Created a basic one.")

    template_docker_path = TEMPLATE_BASE_DIR / "backend" / "Dockerfile.template"
    target_docker_path = Path(backend_dir) / "Dockerfile"
    if template_docker_path.exists():
        with open(template_docker_path, "r", encoding="utf-8") as t:
            dockerfile_content = t.read()
        dockerfile_content = dockerfile_content.replace("{python_base_image}", python_base_image)
        dockerfile_content = dockerfile_content.replace("{port}", str(port))
        with open(target_docker_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
    else:
        print(f"Warning: Backend Dockerfile template not found at {template_docker_path}")

def new_frontend_setup(frontend_dir: str, port: int, deno_base_image: str, backend_port_for_proxy: int, model_name: str):
    """Set up frontend application. model_name is for template substitution."""
    src_dir = Path(frontend_dir) / "src"
    os.makedirs(src_dir, exist_ok=True)

    template_pkg_path = TEMPLATE_BASE_DIR / "frontend" / "package.json.template"
    target_pkg_path = Path(frontend_dir) / "package.json"
    if template_pkg_path.exists():
        with open(template_pkg_path, "r", encoding="utf-8") as t:
            package_json_content = t.read()
        sanitized_model_name_for_pkg = "".join(c if c.isalnum() or c == '-' else '_' for c in model_name.lower().replace("/", "-"))
        package_json_content = package_json_content.replace("{model_name_lower}", sanitized_model_name_for_pkg)
        with open(target_pkg_path, "w", encoding="utf-8") as f:
            f.write(package_json_content)
    else:
        print(f"Warning: Frontend package.json template not found at {template_pkg_path}")

    template_vite_path = TEMPLATE_BASE_DIR / "frontend" / "vite.config.js.template"
    target_vite_path = Path(frontend_dir) / "vite.config.js"
    if template_vite_path.exists():
        with open(template_vite_path, "r", encoding="utf-8") as t:
            vite_config_content = t.read()
        vite_config_content = vite_config_content.replace("{port}", str(port)) 
        vite_config_content = vite_config_content.replace("{backend_port_for_proxy}", str(backend_port_for_proxy))
        with open(target_vite_path, "w", encoding="utf-8") as f:
            f.write(vite_config_content)
    else:
        print(f"Warning: Frontend vite.config.js template not found at {template_vite_path}")

    template_appjsx_path = TEMPLATE_BASE_DIR / "frontend" / "src" / "App.jsx.template"
    target_appjsx_path = src_dir / "App.jsx"
    if template_appjsx_path.exists():
        with open(template_appjsx_path, "r", encoding="utf-8") as t:
            app_jsx_content = t.read()
        app_jsx_content = app_jsx_content.replace("{model_name}", model_name) 
        app_jsx_content = app_jsx_content.replace("{backend_port}", str(backend_port_for_proxy)) 
        with open(target_appjsx_path, "w", encoding="utf-8") as f:
            f.write(app_jsx_content)
    else:
        print(f"Warning: Frontend App.jsx template not found at {template_appjsx_path}")

    template_appcss_path = TEMPLATE_BASE_DIR / "frontend" / "src" / "App.css"
    target_appcss_path = src_dir / "App.css"
    if template_appcss_path.exists():
        shutil.copy(template_appcss_path, target_appcss_path)
    else:
        with open(target_appcss_path, "w", encoding="utf-8") as f:
            f.write("/* Add your styles here */\nbody { font-family: sans-serif; margin: 20px; }\n")
        print(f"Warning: Frontend App.css template not found at {template_appcss_path}. Created a basic one.")

    template_indexhtml_path = TEMPLATE_BASE_DIR / "frontend" / "index.html.template"
    target_indexhtml_path = Path(frontend_dir) / "index.html"
    if template_indexhtml_path.exists():
        with open(template_indexhtml_path, "r", encoding="utf-8") as t:
            index_html_content = t.read()
        index_html_content = index_html_content.replace("{model_name}", model_name) 
        with open(target_indexhtml_path, "w", encoding="utf-8") as f:
            f.write(index_html_content)
    else:
        print(f"Warning: Frontend index.html template not found at {template_indexhtml_path}")

    template_frontend_docker_path = TEMPLATE_BASE_DIR / "frontend" / "Dockerfile.template"
    target_frontend_docker_path = Path(frontend_dir) / "Dockerfile"
    if template_frontend_docker_path.exists():
        with open(template_frontend_docker_path, "r", encoding="utf-8") as t:
            dockerfile_content = t.read()
        dockerfile_content = dockerfile_content.replace("{deno_base_image}", deno_base_image) 
        dockerfile_content = dockerfile_content.replace("{port}", str(port)) 
        with open(target_frontend_docker_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
    else:
        print(f"Warning: Frontend Dockerfile template not found at {template_frontend_docker_path}")

def new_docker_compose(project_dir: str, backend_port_host: int, frontend_port_host: int, service_prefix: str):
    """Create docker-compose.yml file."""
    template_compose_path = TEMPLATE_BASE_DIR / "docker-compose.yml.template"
    target_compose_path = Path(project_dir) / "docker-compose.yml"

    if template_compose_path.exists():
        with open(template_compose_path, "r", encoding="utf-8") as t:
            compose_content = t.read()
        
        compose_content = compose_content.replace("{service_prefix}", service_prefix)
        compose_content = compose_content.replace("{host_backend_port}", str(backend_port_host))
        # Assuming backend container always exposes 5000 internally
        compose_content = compose_content.replace("{container_backend_port}", "5000") 
        compose_content = compose_content.replace("{host_frontend_port}", str(frontend_port_host))
        # Assuming frontend container always exposes 3000 (common for Vite dev) or 8000 (Deno serve)
        # This should match what your frontend Dockerfile EXPOSEs and what Vite/Deno serves on
        compose_content = compose_content.replace("{container_frontend_port}", "3000") # Adjust if your frontend serves on a different port

        with open(target_compose_path, "w", encoding="utf-8") as f:
            f.write(compose_content)
    else:
        print(f"Warning: docker-compose.yml template not found at {template_compose_path}")
        
if __name__ == "__main__":
    main_project_directory = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte"
    
    print(f"Script starting. Base project directory: {main_project_directory}")
    print(f"Template base directory: {TEMPLATE_BASE_DIR}")
    
    if not TEMPLATE_BASE_DIR.is_dir():
        print(f"CRITICAL ERROR: Template directory not found at {TEMPLATE_BASE_DIR}")
        print("Please ensure 'z_code_templates' directory exists in the same directory as this script.")
    else:
        print(f"Found template directory: {TEMPLATE_BASE_DIR}")
        manager = MultiModelManager(base_project_path=main_project_directory)
        manager.create_all()
        print("\nScript finished.")
