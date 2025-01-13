import os
import shutil
import json
import datetime

class ProjectConfig:
    base_dir = "C:/Users/grabowmar/Desktop/ThesisAppsSvelte/ChatGPT/flask_apps"
    app_prefix = "app"  # Prefix for app folders (e.g., app1, app2, etc.)
    total_apps = 20
    start_port = 5001  # Updated to start from 5001 for backend
    frontend_port = 5171  # Updated to start from 5171 for frontend
    python_base_image = "python:3.10-slim"
    deno_base_image = "denoland/deno:1.37.1"
    log_file = "setup.log"  # Log file for setup events

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

    log_message(f"Backend setup complete for port {port}", config.log_file)

def new_frontend_setup(frontend_dir, port, deno_base_image):
    os.makedirs(os.path.join(frontend_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(frontend_dir, "public"), exist_ok=True)

    deno_config = {
        "tasks": {
            "start": "deno run --allow-net --allow-read mod.ts",
            "dev": "deno run --watch --allow-net --allow-read mod.ts"
        },
        "imports": {
            "svelte": "https://esm.sh/svelte@3.59.2"
        }
    }
    
    with open(os.path.join(frontend_dir, "deno.json"), "w") as f:
        json.dump(deno_config, f, indent=2)

    mod_ts = f"""
import {{ serve }} from "https://deno.land/std@0.140.0/http/server.ts";

async function handleRequest(req) {{
    const url = new URL(req.url);

    if (url.pathname === "/") {{
        return new Response(`\
<!DOCTYPE html>\
<html>\
  <head>\
    <title>Deno App</title>\
  </head>\
  <body>\
    <div id=\"app\"></div>\
    <script type=\"module\">\
      import App from './src/App.js';\
      const app = document.getElementById('app');\
      new App(app);\
    </script>\
  </body>\
</html>`, {{
            headers: {{ "content-type": "text/html; charset=utf-8" }}
        }});
    }}

    if (url.pathname.startsWith("/src/")) {{
        try {{
            const file = await Deno.readFile(`.${{url.pathname}}`);
            const contentType = url.pathname.endsWith(".js") ? "application/javascript" : "text/plain";
            return new Response(file, {{ headers: {{ "content-type": contentType }} }});
        }} catch {{
            return new Response("Not found", {{ status: 404 }});
        }}
    }}

    return new Response("Not found", {{ status: 404 }});
}}

console.log("Server running at http://localhost:{port}");
await serve(handleRequest, {{ port: {port} }});
"""
    
    with open(os.path.join(frontend_dir, "mod.ts"), "w") as f:
        f.write(mod_ts)

    app_js = """
class App {
    constructor(target) {
        this.message = 'Loading...';
        this.target = target;
        this.render();
        this.fetchMessage();
    }

    async fetchMessage() {
        try {
            const response = await fetch('http://localhost:5002/');
            const data = await response.json();
            this.message = data.message;
            this.render();
        } catch (error) {
            this.message = 'Error connecting to backend';
            this.render();
        }
    }

    render() {
        this.target.innerHTML = `
            <div class="app">
                <p class="message">${this.message}</p>
            </div>
            <style>
                .app {{
                    text-align: center;
                    padding: 2em;
                }}
                .message {{
                    color: #444;
                    font-size: 1.2em;
                    margin: 1em;
                }}
            </style>
        `;
    }
}

export default App;
"""
    
    with open(os.path.join(frontend_dir, "src", "App.js"), "w") as f:
        f.write(app_js)

    dockerfile_content = f"""
FROM {deno_base_image}
WORKDIR /app
COPY . .
EXPOSE {port}
CMD ["deno", "task", "start"]
"""
    
    with open(os.path.join(frontend_dir, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)

    log_message(f"Frontend setup complete for port {port}", config.log_file)

def new_docker_compose(project_dir, backend_port, frontend_port):
    compose_content = f"""
version: '3.8'
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
        restart: always
        depends_on:
            - backend
"""
    
    with open(os.path.join(project_dir, "docker-compose.yml"), "w") as f:
        f.write(compose_content)

    log_message(f"Docker Compose file created for backend port {backend_port} and frontend port {frontend_port}", config.log_file)

if __name__ == "__main__":
    config = ProjectConfig()
    tracker = ResourceTracker()

    try:
        if not os.path.exists(config.base_dir):
            os.makedirs(config.base_dir)
            log_message(f"Created base directory: {config.base_dir}", config.log_file)

        for i in range(1, config.total_apps + 1):
            project_dir = os.path.join(config.base_dir, f"{config.app_prefix}{i}")
            backend_port = config.start_port + (i * 2 - 1)  # Start backend ports from 5001
            frontend_port = config.frontend_port + (i * 2 - 2)  # Start frontend ports from 5171

            new_backend_setup(os.path.join(project_dir, "backend"), backend_port, config.python_base_image)
            new_frontend_setup(os.path.join(project_dir, "frontend"), frontend_port, config.deno_base_image)
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
