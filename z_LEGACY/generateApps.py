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
        "Anthropic_Claude_3.7_Sonnet": "#D97706",
        "OpenAI_GPT-4.1": "#14B8A6",
        "Mistral_Devstral_Small": "#8B5CF6",
        "Google_Gemma_3n_4B": "#3B82F6",
        "Meta-Llama_Llama_3.3_8B_Instruct": "#F59E0B",
        "NousResearch_DeepHermes_3_Mistral_24B_Preview": "#EC4899",
        "Microsoft_Phi-4_Reasoning_Plus": "#6366F1",
        "Qwen_Qwen3_30B_A3B": "#F43F5E",
        "OpenAI_Codex_Mini": "#22D3EE",
        "x-AI_Grok-3_Beta": "#EF4444",
        "Inception_Mercury-Coder_Small-Beta": "#A855F7",
        "Google_Gemini-2.5_Flash-Preview-05-20": "#60A5FA",
        "Meta-Llama_Llama-4_Maverick": "#FBBF24",
        "Qwen_Qwen3_235B_A22B": "#FB7185",
        "Qwen_Qwen3_32B": "#E11D48",
        "Meta-Llama_Llama-4_Scout": "#FCD34D",
        "DeepSeek_DeepSeek-Chat-V3-0324": "#F97316"
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
        
        # Each app uses PORTS_PER_APP (e.g., 2 ports).
        # For app_number 1 (0-indexed as app_number-1), offset is 0.
        # For app_number 2 (0-indexed as app_number-1), offset is PORTS_PER_APP.
        offset_for_app = (app_number - 1) * cls.PORTS_PER_APP
        
        return {
            'backend': backend_base_for_model + offset_for_app,
            'frontend': frontend_base_for_model + offset_for_app 
                        # Assuming frontend port is backend_port + 1 or similar fixed offset
                        # If frontend and backend ports for the same app are not consecutive
                        # or have a different scheme, this needs adjustment.
                        # The original script implies backend and frontend ports for an app are (base + i*2) and (base_frontend + i*2)
                        # So, the offset applies similarly.
        }

class ProjectConfig:
    def __init__(self, model_name: str, model_index: int, base_project_path: str = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte"):
        self.model_name = model_name
        # Ensure the base directory includes the "models" folder
        self.base_dir = os.path.join(base_project_path, "models", model_name)
        self.app_prefix = "app"
        self.total_apps = PortManager.APPS_PER_MODEL # Use APPS_PER_MODEL from PortManager
        
        # Get port ranges from PortManager for this specific model_index
        self.backend_base_for_model, self.frontend_base_for_model = PortManager.calculate_port_range(model_index)
        
        self.python_base_image = "python:3.14-slim" # Consistent with original
        self.deno_base_image = "denoland/deno" # Consistent with original
        
        # Log file will be in the specific model's directory inside "models"
        # To avoid issues with long model names in file names, we can sanitize it or place logs elsewhere
        # For now, placing it inside the model's generated directory.
        # Ensure the log directory exists before writing.
        log_dir = os.path.join(base_project_path, "models", "_logs") # Central log directory for all models
        os.makedirs(log_dir, exist_ok=True)
        sanitized_model_name_for_log = "".join(c if c.isalnum() else "_" for c in model_name)
        self.log_file = os.path.join(log_dir, f"setup_{sanitized_model_name_for_log}.log")
        
        self.color = PortManager.MODEL_COLORS.get(model_name, "#666666") # Default color

    def get_ports_for_app(self, app_num: int) -> Dict[str, int]:
        """Get the specific ports for an app number (1-based) for this model."""
        # app_num is 1-based. Offset calculation: (app_num - 1) * PORTS_PER_APP
        offset = (app_num - 1) * PortManager.PORTS_PER_APP
        return {
            'backend': self.backend_base_for_model + offset,
            'frontend': self.frontend_base_for_model + offset # Each app's frontend port starts from its own base
        }

    def get_port_ranges_for_model(self) -> Dict[str, Dict[str, int]]:
        """Get the full port range information for this model's apps."""
        # The last port used by the last app for this model
        backend_end = self.backend_base_for_model + (self.total_apps * PortManager.PORTS_PER_APP) - PortManager.PORTS_PER_APP # if backend is the first of the pair
        # Or, if backend and frontend are separate and each app takes one from each block:
        backend_end = self.backend_base_for_model + (self.total_apps -1) * PortManager.PORTS_PER_APP # if backend is the first port of the pair for an app
        # If backend port is P and frontend is P+1, then the last backend port is base + (N-1)*2
        # and the last frontend port is base_frontend + (N-1)*2 + (PORTS_PER_APP -1) (if frontend is the last port of the pair)
        # Given the setup, it's simpler:
        # Backend ports: base_backend, base_backend+2, ..., base_backend + (total_apps-1)*2
        # Frontend ports: base_frontend, base_frontend+2, ..., base_frontend + (total_apps-1)*2
        
        # Correct calculation for the end port of the block assigned to this model's apps
        # (does not include the BUFFER_PORTS here, as that's for separation between models)
        last_app_offset = (self.total_apps - 1) * PortManager.PORTS_PER_APP
        
        return {
            'backend': {
                'start': self.backend_base_for_model,
                'end': self.backend_base_for_model + last_app_offset # The first port of the last app's pair
                       # If PORTS_PER_APP is 2, and backend is the first, frontend is second.
                       # The highest backend port used by this model's apps.
            },
            'frontend': {
                'start': self.frontend_base_for_model,
                'end': self.frontend_base_for_model + last_app_offset # The first port of the last app's pair
                       # The highest frontend port used by this model's apps.
                       # If frontend is backend_port + 1, then end is self.backend_base_for_model + last_app_offset + 1
                       # But the original script structure implies frontend ports are also gapped by 2 for each new app.
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
        # Important: Reverse order for directories to remove subdirs first
        for directory in reversed(self.directories):
            if os.path.exists(directory):
                try:
                    shutil.rmtree(directory)
                    print(f"Deleted directory: {directory}")
                except OSError as e:
                    print(f"Error deleting directory {directory}: {e}")
        for file_path in self.files: # Files can be deleted in any order
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
        # The order of models from MODEL_COLORS.keys() determines their index
        self.models = list(PortManager.MODEL_COLORS.keys())
        self.configs: Dict[str, ProjectConfig] = {}
        self.base_project_path = base_project_path
        self.setup_configs()

    def setup_configs(self):
        # The main "models" directory that will contain all individual model folders
        overall_models_dir = os.path.join(self.base_project_path, "models")
        os.makedirs(overall_models_dir, exist_ok=True) # Create the main "models" directory if it doesn't exist

        for idx, model_name in enumerate(self.models):
            self.configs[model_name] = ProjectConfig(model_name, idx, self.base_project_path)
            # Log port ranges for verification
            ranges = self.configs[model_name].get_port_ranges_for_model()
            log_message(f"Port ranges for {model_name}:", self.configs[model_name].log_file)
            log_message(f"  Backend: {ranges['backend']['start']}-{ranges['backend']['end'] + (PortManager.PORTS_PER_APP -1 if PortManager.PORTS_PER_APP > 0 else 0)} (approx range end)", self.configs[model_name].log_file)
            log_message(f"  Frontend: {ranges['frontend']['start']}-{ranges['frontend']['end'] + (PortManager.PORTS_PER_APP -1 if PortManager.PORTS_PER_APP > 0 else 0)} (approx range end)", self.configs[model_name].log_file)
            print(f"\nConfigured port ranges for {model_name}:") # Also print to console
            print(f"  Backend: Start {ranges['backend']['start']}")
            print(f"  Frontend: Start {ranges['frontend']['start']}")


    def create_all(self):
        for model_name in self.models:
            print(f"\nCreating applications for model: {model_name}...")
            config = self.configs[model_name]
            tracker = ResourceTracker() # One tracker per model processing
            
            try:
                # Base directory for this specific model (e.g., .../models/Anthropic_Claude_3.7_Sonnet)
                # This directory is now created by ProjectConfig if it doesn't exist,
                # but we ensure it here as well, or handle its creation more explicitly.
                os.makedirs(config.base_dir, exist_ok=True)
                log_message(f"Ensured base directory exists: {config.base_dir}", config.log_file)
                tracker.track_directory(config.base_dir) # Track it for potential cleanup on error for this model

                for i in range(1, config.total_apps + 1):
                    # project_dir is for a single app, e.g., .../models/Anthropic_Claude_3.7_Sonnet/app1
                    project_dir = os.path.join(config.base_dir, f"{config.app_prefix}{i}")
                    ports = config.get_ports_for_app(i) # Get ports for app 'i' of the current model
                    
                    # Ensure app-specific project directory exists
                    os.makedirs(project_dir, exist_ok=True)
                    tracker.track_directory(project_dir) # Track each app's directory

                    log_message(f"Creating {config.app_prefix}{i} for {model_name} in {project_dir}", config.log_file)
                    
                    # Setup backend
                    backend_dir = os.path.join(project_dir, "backend")
                    new_backend_setup(
                        backend_dir,
                        ports['backend'],
                        config.python_base_image,
                        model_name # Pass the full model name
                    )
                    tracker.track_directory(backend_dir)

                    # Setup frontend
                    frontend_dir = os.path.join(project_dir, "frontend")
                    new_frontend_setup(
                        frontend_dir,
                        ports['frontend'],
                        config.deno_base_image,
                        ports['backend'], # Backend port for frontend to connect to
                        model_name # Pass the full model name
                    )
                    tracker.track_directory(frontend_dir)

                    # Create Docker Compose file
                    new_docker_compose(
                        project_dir, 
                        ports['backend'],
                        ports['frontend'],
                        # Use a sanitized model prefix for service names in docker-compose
                        "".join(c if c.isalnum() else "_" for c in model_name.lower()) + f"_app{i}"
                    )
                    tracker.track_file(os.path.join(project_dir, "docker-compose.yml"))

                    log_message(
                        f"Application {config.app_prefix}{i} created for {model_name} "
                        f"(Backend Port: {ports['backend']}, Frontend Port: {ports['frontend']})",
                        config.log_file
                    )
                
                print(f"All {config.total_apps} applications created successfully for model: {model_name}!")
                final_ranges = config.get_port_ranges_for_model() # Get ranges for this model
                # The 'end' port in get_port_ranges_for_model is the *start* port of the last app.
                # To show the actual highest port number used:
                highest_backend_port = final_ranges['backend']['start'] + (config.total_apps - 1) * PortManager.PORTS_PER_APP
                highest_frontend_port = final_ranges['frontend']['start'] + (config.total_apps - 1) * PortManager.PORTS_PER_APP

                # If PORTS_PER_APP includes multiple ports (e.g., backend is X, frontend is X+1 for the *same* app number in the sequence)
                # then the highest port would be + (PORTS_PER_APP - 1).
                # The current script implies distinct port sequences for backend and frontend based on model_index and app_number.
                # Example: App1 (Backend: 5001, Frontend: 5501), App2 (Backend: 5003, Frontend: 5503) for Model0.

                print(f"  Approximate ports used by {model_name}:")
                print(f"    Backend: {final_ranges['backend']['start']} to {highest_backend_port}")
                print(f"    Frontend: {final_ranges['frontend']['start']} to {highest_frontend_port}")
                log_message(f"Successfully created all apps for {model_name}.", config.log_file)

            except Exception as e:
                print(f"An error occurred while processing model {model_name}: {e}")
                log_message(f"CRITICAL ERROR for model {model_name}: {e}. Attempting cleanup...", config.log_file)
                # tracker.cleanup() # Cleanup resources created *for this model* if an error occurs
                log_message(f"Cleanup for {model_name} attempted.", config.log_file)
                # Decide if you want to continue with other models or stop
                # raise # Reraise if you want to stop the whole script

def log_message(message: str, log_file_path: str):
    """Log a message with timestamp to a specific log file."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        # Ensure the directory for the log file exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to write to log file {log_file_path}: {e}")


# Assume template files are in a subdirectory "z_code_templates" relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_BASE_DIR = SCRIPT_DIR / "z_code_templates"

def new_backend_setup(backend_dir: str, port: int, python_base_image: str, model_name: str):
    """Set up backend application. model_name is for template substitution."""
    os.makedirs(backend_dir, exist_ok=True)

    # app.py
    template_path = TEMPLATE_BASE_DIR / "backend" / "app.py.template"
    target_path = Path(backend_dir) / "app.py"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as t:
            app_py_content = t.read()
        app_py_content = app_py_content.replace("{model_name}", model_name) # Use full model name
        app_py_content = app_py_content.replace("{port}", str(port))
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(app_py_content)
    else:
        print(f"Warning: Backend app.py template not found at {template_path}")


    # requirements.txt
    template_req_path = TEMPLATE_BASE_DIR / "backend" / "requirements.txt" # Assuming it's a direct copy
    target_req_path = Path(backend_dir) / "requirements.txt"
    if template_req_path.exists():
        shutil.copy(template_req_path, target_req_path)
    else:
        # Create a dummy requirements.txt if template is missing, or log warning
        with open(target_req_path, "w", encoding="utf-8") as f:
            f.write("flask\nrequests\n# Add other dependencies here\n") # Basic placeholder
        print(f"Warning: Backend requirements.txt template not found at {template_req_path}. Created a basic one.")


    # Dockerfile
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

    # package.json
    template_pkg_path = TEMPLATE_BASE_DIR / "frontend" / "package.json.template"
    target_pkg_path = Path(frontend_dir) / "package.json"
    if template_pkg_path.exists():
        with open(template_pkg_path, "r", encoding="utf-8") as t:
            package_json_content = t.read()
        # Sanitize model_name for package.json name field if necessary (e.g. lowercase, no special chars)
        sanitized_model_name_for_pkg = "".join(c if c.isalnum() or c == '-' else '_' for c in model_name.lower())
        package_json_content = package_json_content.replace("{model_name_lower}", sanitized_model_name_for_pkg)
        with open(target_pkg_path, "w", encoding="utf-8") as f:
            f.write(package_json_content)
    else:
        print(f"Warning: Frontend package.json template not found at {template_pkg_path}")


    # vite.config.js
    template_vite_path = TEMPLATE_BASE_DIR / "frontend" / "vite.config.js.template"
    target_vite_path = Path(frontend_dir) / "vite.config.js"
    if template_vite_path.exists():
        with open(template_vite_path, "r", encoding="utf-8") as t:
            vite_config_content = t.read()
        vite_config_content = vite_config_content.replace("{port}", str(port)) # Vite dev server port
        # The original script had "{port_b}", str(port-500). This implies the backend port.
        # It's better to pass the actual backend_port_for_proxy.
        vite_config_content = vite_config_content.replace("{backend_port_for_proxy}", str(backend_port_for_proxy))
        with open(target_vite_path, "w", encoding="utf-8") as f:
            f.write(vite_config_content)
    else:
        print(f"Warning: Frontend vite.config.js template not found at {template_vite_path}")


    # src/App.jsx
    template_appjsx_path = TEMPLATE_BASE_DIR / "frontend" / "src" / "App.jsx.template"
    target_appjsx_path = src_dir / "App.jsx"
    if template_appjsx_path.exists():
        with open(template_appjsx_path, "r", encoding="utf-8") as t:
            app_jsx_content = t.read()
        app_jsx_content = app_jsx_content.replace("{model_name}", model_name) # Use full model name for display
        app_jsx_content = app_jsx_content.replace("{backend_port}", str(backend_port_for_proxy)) # For API calls
        with open(target_appjsx_path, "w", encoding="utf-8") as f:
            f.write(app_jsx_content)
    else:
        print(f"Warning: Frontend App.jsx template not found at {template_appjsx_path}")


    # src/App.css (direct copy)
    template_appcss_path = TEMPLATE_BASE_DIR / "frontend" / "src" / "App.css"
    target_appcss_path = src_dir / "App.css"
    if template_appcss_path.exists():
        shutil.copy(template_appcss_path, target_appcss_path)
    else:
        # Create a dummy App.css if template is missing
        with open(target_appcss_path, "w", encoding="utf-8") as f:
            f.write("/* Add your styles here */\nbody { font-family: sans-serif; margin: 20px; }\n")
        print(f"Warning: Frontend App.css template not found at {template_appcss_path}. Created a basic one.")


    # index.html (root of frontend)
    template_indexhtml_path = TEMPLATE_BASE_DIR / "frontend" / "index.html.template"
    target_indexhtml_path = Path(frontend_dir) / "index.html"
    if template_indexhtml_path.exists():
        with open(template_indexhtml_path, "r", encoding="utf-8") as t:
            index_html_content = t.read()
        index_html_content = index_html_content.replace("{model_name}", model_name) # For title or display
        with open(target_indexhtml_path, "w", encoding="utf-8") as f:
            f.write(index_html_content)
    else:
        print(f"Warning: Frontend index.html template not found at {template_indexhtml_path}")


    # Dockerfile
    template_frontend_docker_path = TEMPLATE_BASE_DIR / "frontend" / "Dockerfile.template"
    target_frontend_docker_path = Path(frontend_dir) / "Dockerfile"
    if template_frontend_docker_path.exists():
        with open(template_frontend_docker_path, "r", encoding="utf-8") as t:
            dockerfile_content = t.read()
        dockerfile_content = dockerfile_content.replace("{deno_base_image}", deno_base_image) # Or node, if using node
        dockerfile_content = dockerfile_content.replace("{port}", str(port)) # Port the container will expose
        with open(target_frontend_docker_path, "w", encoding="utf-8") as f:
            f.write(dockerfile_content)
    else:
        print(f"Warning: Frontend Dockerfile template not found at {template_frontend_docker_path}")


def new_docker_compose(project_dir: str, backend_port_host: int, frontend_port_host: int, service_prefix: str):
    """Create docker-compose.yml file.
    service_prefix is used to make service names unique, e.g., modelname_app1_backend.
    Ports are host ports. Container ports are assumed to be fixed (e.g., 5000 for backend, 3000 for frontend dev server).
    """
    template_compose_path = TEMPLATE_BASE_DIR / "docker-compose.yml.template"
    target_compose_path = Path(project_dir) / "docker-compose.yml"

    if template_compose_path.exists():
        with open(template_compose_path, "r", encoding="utf-8") as t:
            compose_content = t.read()
        
        # Replace placeholders for service names and ports
        # Assuming template has {service_prefix}_backend and {service_prefix}_frontend
        # And {host_backend_port}, {container_backend_port}, {host_frontend_port}, {container_frontend_port}
        
        # Example replacements (adjust based on your template's placeholders)
        compose_content = compose_content.replace("{service_prefix}", service_prefix)
        compose_content = compose_content.replace("{host_backend_port}", str(backend_port_host))
        # Assuming your backend Dockerfile EXPOSEs a fixed port, e.g., 5000
        # compose_content = compose_content.replace("{container_backend_port}", "5000") # Or get from config

        compose_content = compose_content.replace("{host_frontend_port}", str(frontend_port_host))
        # Assuming your frontend Dockerfile EXPOSEs a fixed port (e.g., Vite's default or what's in Dockerfile)
        # compose_content = compose_content.replace("{container_frontend_port}", "5173") # Vite default, or Deno's serve port

        # Fallback for original placeholders if they exist, for compatibility
        compose_content = compose_content.replace("{model_prefix}", service_prefix) # old placeholder
        compose_content = compose_content.replace("{backend_port}", str(backend_port_host)) # old placeholder
        compose_content = compose_content.replace("{frontend_port}", str(frontend_port_host)) # old placeholder

        with open(target_compose_path, "w", encoding="utf-8") as f:
            f.write(compose_content)
    else:
        print(f"Warning: docker-compose.yml template not found at {template_compose_path}")
        

if __name__ == "__main__":
    # Define the base path where the "models" folder and logs will be created.
    # This should be an absolute path or a path relative to where you run the script.
    # For consistency with the original script's hardcoded path:
    main_project_directory = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte"
    
    print(f"Script starting. Base project directory: {main_project_directory}")
    print(f"Template base directory: {TEMPLATE_BASE_DIR}")
    
    # Check if template directory exists
    if not TEMPLATE_BASE_DIR.is_dir():
        print(f"CRITICAL ERROR: Template directory not found at {TEMPLATE_BASE_DIR}")
        print("Please ensure 'z_code_templates' directory exists in the same directory as this script.")
    else:
        print(f"Found template directory: {TEMPLATE_BASE_DIR}")
        manager = MultiModelManager(base_project_path=main_project_directory)
        manager.create_all()
        print("\nScript finished.")