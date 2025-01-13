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
    BUFFER_PORTS = 5  # Buffer between models to allow for future expansion
    APPS_PER_MODEL = 20

    MODEL_COLORS = {
        "ChatGPT": "#10a37f",
        "ChatGPTo1": "#0ea47f",
        "ClaudeSonnet": "#7b2bf9",
        "CodeLlama": "#f97316",
        "Gemini": "#1a73e8",
        "Grok": "#ff4d4f",
        "Mixtral": "#9333ea"
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
        self.base_dir = f"C:/Users/grabowmar/Desktop/ThesisAppsSvelte/{model_name}/flask_apps"
        self.app_prefix = "app"
        self.total_apps = 20
        # Get port ranges from PortManager
        self.backend_base, self.frontend_base = PortManager.calculate_port_range(model_index)
        self.python_base_image = "python:3.10-slim"
        self.deno_base_image = "denoland/deno:1.37.1"
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

    app_py_content = f"""
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({{'message': 'Hello from {model_name} Flask Backend!'}})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port={port})
"""
    
    with open(os.path.join(backend_dir, "app.py"), "w") as f:
        f.write(app_py_content)

    with open(os.path.join(backend_dir, "requirements.txt"), "w") as f:
        f.write("flask\nflask-cors")

    dockerfile_content = f"""
FROM {python_base_image}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]
"""
    
    with open(os.path.join(backend_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

def new_frontend_setup(frontend_dir: str, port: int, deno_base_image: str, backend_port: int, model_name: str):
    """Set up frontend application"""
    os.makedirs(os.path.join(frontend_dir, "src"), exist_ok=True)

    package_json = {
        "name": f"svelte-{model_name.lower()}-app",
        "private": True,
        "version": "0.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
        },
        "devDependencies": {
            "@sveltejs/vite-plugin-svelte": "^3.0.1",
            "svelte": "^4.2.8",
            "vite": "^5.0.8"
        }
    }
    
    with open(os.path.join(frontend_dir, "package.json"), "w") as f:
        json.dump(package_json, f, indent=2)

    deno_config = {
        "tasks": {
            "dev": "npm run dev"
        },
        "imports": {
            "@sveltejs/vite-plugin-svelte": "npm:@sveltejs/vite-plugin-svelte@^3.0.1",
            "svelte": "npm:svelte@^4.2.8",
            "vite": "npm:vite@^5.0.8"
        }
    }
    
    with open(os.path.join(frontend_dir, "deno.json"), "w") as f:
        json.dump(deno_config, f, indent=2)

    vite_config = f"""import {{ defineConfig }} from 'vite'
import {{ svelte }} from '@sveltejs/vite-plugin-svelte'

export default defineConfig({{
  plugins: [svelte()],
  server: {{
    host: true,
    port: {port},
    strictPort: true
  }}
}})
"""
    with open(os.path.join(frontend_dir, "vite.config.js"), "w") as f:
        f.write(vite_config)

    app_svelte = f"""
<script>
  let message = 'Loading...';

  async function fetchMessage() {{
    try {{
      const response = await fetch('http://localhost:{backend_port}/');
      const data = await response.json();
      message = data.message;
    }} catch (error) {{
      message = 'Error connecting to {model_name} backend';
    }}
  }}

  fetchMessage();
</script>

<main>
  <h1>{model_name} App</h1>
  <p class="message">{{message}}</p>
</main>

<style>
  main {{
    text-align: center;
    padding: 2em;
  }}
  h1 {{
    color: #333;
    font-size: 2em;
    margin-bottom: 0.5em;
  }}
  .message {{
    color: #444;
    font-size: 1.2em;
    margin: 1em;
  }}
</style>
"""
    with open(os.path.join(frontend_dir, "src", "App.svelte"), "w") as f:
        f.write(app_svelte)

    main_js = """import App from './App.svelte'

const app = new App({
  target: document.getElementById('app')
})

export default app
"""
    with open(os.path.join(frontend_dir, "src", "main.js"), "w") as f:
        f.write(main_js)

    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model_name} Svelte App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
"""
    with open(os.path.join(frontend_dir, "index.html"), "w") as f:
        f.write(index_html)

    dockerfile_content = f"""
FROM {deno_base_image}

WORKDIR /app

# Install Node.js and npm
ENV NODE_VERSION=18.x
RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_$NODE_VERSION | bash -
RUN apt-get install -y nodejs

# Copy package files
COPY package.json .
COPY vite.config.js .
COPY index.html .

# Install dependencies with detailed logging
RUN set -x && \\
    npm install --verbose && \\
    npm ls && \\
    du -h node_modules/ && \\
    find node_modules/ -type f | wc -l

# Copy source files
COPY src src/

EXPOSE {port}
ENV PORT={port}

# Start the development server
CMD ["npm", "run", "dev"]
"""
    with open(os.path.join(frontend_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

def new_docker_compose(project_dir: str, backend_port: int, frontend_port: int, model_prefix: str):
    """Create docker-compose.yml file"""
    compose_content = f"""version: '3.8'
services:
    backend:
        build: ./backend
        container_name: {model_prefix}_backend_{backend_port}
        ports:
            - "{backend_port}:{backend_port}"
        volumes:
            - ./backend:/app
        restart: always

    frontend:
        build: ./frontend
        container_name: {model_prefix}_frontend_{frontend_port}
        ports:
            - "{frontend_port}:{frontend_port}"
        volumes:
            - ./frontend:/app
            - /app/node_modules
        environment:
            - PORT={frontend_port}
        restart: always
        depends_on:
            - backend
"""
    with open(os.path.join(project_dir, "docker-compose.yml"), "w") as f:
        f.write(compose_content)

if __name__ == "__main__":
    manager = MultiModelManager()
    manager.create_all()