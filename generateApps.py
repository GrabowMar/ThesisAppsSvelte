import os
import shutil
import json
import datetime

class ProjectConfig:
    base_dir = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte/ChatGPT/flask_apps"
    app_prefix = "app"
    total_apps = 20
    start_port = 5001  # Backend ports
    frontend_port = 5171  # Frontend ports
    python_base_image = "python:3.10-slim"
    deno_base_image = "denoland/deno:1.37.1"
    log_file = "setup.log"

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

def log_message(message, log_file):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def new_backend_setup(backend_dir, port, python_base_image):
    os.makedirs(backend_dir, exist_ok=True)
    log_message(f"Created backend directory: {backend_dir}", config.log_file)

    app_py_content = f"""
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({{'message': 'Hello from Flask!'}})

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

def new_frontend_setup(frontend_dir, port, deno_base_image, backend_port):
    # Create necessary directories
    os.makedirs(os.path.join(frontend_dir, "src"), exist_ok=True)

    # Create package.json
    package_json = {
        "name": "svelte-app",
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

    # Create deno.json
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

    # Create vite.config.js
    vite_config = """import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: true,
    port: process.env.PORT || 5173,
    strictPort: true
  }
})
"""
    with open(os.path.join(frontend_dir, "vite.config.js"), "w") as f:
        f.write(vite_config)

    # Create src/App.svelte
    app_svelte = f"""
<script>
  let message = 'Loading...';

  async function fetchMessage() {{
    try {{
      const response = await fetch('http://localhost:{backend_port}/');
      const data = await response.json();
      message = data.message;
    }} catch (error) {{
      message = 'Error connecting to backend';
    }}
  }}

  fetchMessage();
</script>

<main>
  <p class="message">{{message}}</p>
</main>

<style>
  main {{
    text-align: center;
    padding: 2em;
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

    # Create src/main.js
    main_js = """import App from './App.svelte'

const app = new App({
  target: document.getElementById('app')
})

export default app
"""
    with open(os.path.join(frontend_dir, "src", "main.js"), "w") as f:
        f.write(main_js)

    # Create index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Svelte + Vite App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
"""
    with open(os.path.join(frontend_dir, "index.html"), "w") as f:
        f.write(index_html)

    # Create Dockerfile for frontend
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
RUN set -x && \
    npm install --verbose && \
    npm ls && \
    du -h node_modules/ && \
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

def new_docker_compose(project_dir, backend_port, frontend_port):
    compose_content = f"""version: '3.8'
services:
    backend:
        build: ./backend
        ports:
            - "{backend_port}:{backend_port}"
        volumes:
            - ./backend:/app
        restart: always

    frontend:
        build: ./frontend
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
    config = ProjectConfig()
    tracker = ResourceTracker()

    try:
        if not os.path.exists(config.base_dir):
            os.makedirs(config.base_dir)
            log_message(f"Created base directory: {config.base_dir}", config.log_file)

        for i in range(1, config.total_apps + 1):
            project_dir = os.path.join(config.base_dir, f"{config.app_prefix}{i}")
            backend_port = config.start_port + (i * 2 - 1)
            frontend_port = config.frontend_port + (i * 2 - 1)

            os.makedirs(project_dir, exist_ok=True)
            new_backend_setup(os.path.join(project_dir, "backend"), backend_port, config.python_base_image)
            new_frontend_setup(
                os.path.join(project_dir, "frontend"),
                frontend_port,
                config.deno_base_image,
                backend_port
            )
            new_docker_compose(project_dir, backend_port, frontend_port)

            tracker.track_directory(project_dir)
            log_message(f"Application {config.app_prefix}{i} created successfully.", config.log_file)

        print("All applications created successfully!")
    except Exception as e:
        print(f"Error: {e}")
        log_message(f"Error occurred: {e}", config.log_file)
        tracker.cleanup()
    finally:
        log_message("Script execution completed.", config.log_file)