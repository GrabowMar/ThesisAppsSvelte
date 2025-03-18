# Generate template structure for multi-model app setup
$ErrorActionPreference = "Stop"

# Base directory for templates
$templateDir = "code_templates"

# Template content
$templates = @{
    # Backend templates
    "backend/app.py.template" = @'
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({'message': 'Hello from {model_name} Flask Backend!'})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port={port})
'@

    "backend/Dockerfile.template" = @'
FROM {python_base_image}
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE {port}
CMD ["python", "app.py"]
'@

    "backend/requirements.txt" = @'
flask
flask-cors
'@

    # Frontend templates
    "frontend/package.json.template" = @'
{
  "name": "react-{model_name_lower}-app",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "devDependencies": {
    "@reactjs/vite-plugin-react": "^3.0.1",
    "react": "^4.2.8",
    "vite": "^5.0.8"
  }
}
'@

    "frontend/deno.json.template" = @'
{
  "tasks": {
    "dev": "npm run dev"
  },
  "imports": {
    "@reactjs/vite-plugin-react": "npm:@reactjs/vite-plugin-react@^3.0.1",
    "react": "npm:react@^4.2.8",
    "vite": "npm:vite@^5.0.8"
  }
}
'@

    "frontend/vite.config.js.template" = @'
import { defineConfig } from 'vite'
import { react } from '@reactjs/vite-plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: {port},
    strictPort: true
  }
})
'@

    "frontend/src/App.jsx.template" = @'
<script>
  let message = 'Loading...';

  async function fetchMessage() {
    try {
      const response = await fetch('http://localhost:{backend_port}/');
      const data = await response.json();
      message = data.message;
    } catch (error) {
      message = 'Error connecting to {model_name} backend';
    }
  }

  fetchMessage();
</script>

<main>
  <h1>{model_name} App</h1>
  <p class="message">{message}</p>
</main>

<style>
  main {
    text-align: center;
    padding: 2em;
  }
  h1 {
    color: #333;
    font-size: 2em;
    margin-bottom: 0.5em;
  }
  .message {
    color: #444;
    font-size: 1.2em;
    margin: 1em;
  }
</style>
'@

    "frontend/src/main.js" = @'
import App from './App.jsx'

const app = new App({
  target: document.getElementById('app')
})

export default app
'@

    "frontend/index.html.template" = @'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{model_name} react App</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
'@

    "frontend/Dockerfile.template" = @'
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
'@

    "docker-compose.yml.template" = @'
version: '3.8'
services:
    backend:
        build: ./backend
        container_name: {model_prefix}_backend_{backend_port}
        ports:
            - "{backend_port}:{backend_port}"
        volumes:
            - ./backend/src:/app/src
        restart: always

    frontend:
        build: ./frontend
        container_name: {model_prefix}_frontend_{frontend_port}
        ports:
            - "{frontend_port}:{frontend_port}"
        volumes:
            - ./frontend/src:/app/src 
            - ./frontend/vite.config.js:/app/vite.config.js
            - ./frontend/index.html:/app/index.html
        environment:
            - PORT={frontend_port}
        restart: always
        depends_on:
            - backend
'@
}

function Create-Template {
    param (
        [string]$Path,
        [string]$Content
    )
    
    try {
        # Create directory if it doesn't exist
        $dir = Split-Path -Parent $Path
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "Created directory: $dir" -ForegroundColor Green
        }

        # Create file with content
        Set-Content -Path $Path -Value $Content -Encoding UTF8
        Write-Host "Created file: $Path" -ForegroundColor Green
    }
    catch {
        Write-Host "Error creating $Path : $_" -ForegroundColor Red
    }
}

# Main execution
try {
    Write-Host "Starting template generation..." -ForegroundColor Cyan

    # Create base template directory if it doesn't exist
    if (Test-Path $templateDir) {
        Write-Host "Template directory exists. Cleaning..." -ForegroundColor Yellow
        Remove-Item -Path $templateDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $templateDir -Force | Out-Null
    Write-Host "Created template directory: $templateDir" -ForegroundColor Green

    # Create all templates
    foreach ($template in $templates.GetEnumerator()) {
        $path = Join-Path $templateDir $template.Key
        Create-Template -Path $path -Content $template.Value
    }

    Write-Host "`nTemplate generation completed successfully!" -ForegroundColor Cyan
}
catch {
    Write-Host "Error during template generation: $_" -ForegroundColor Red
}