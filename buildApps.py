import os
import subprocess
from pathlib import Path

def build_app(app_dir: str, app_num: int) -> bool:
    """Build single Flask/Svelte application."""
    try:
        # Check backend Dockerfile
        backend_dir = os.path.join(app_dir, "backend")
        if not os.path.exists(os.path.join(backend_dir, "Dockerfile")):
            print(f"No Dockerfile found in {backend_dir}")
            return False

        # Build backend
        print(f"Building backend for app{app_num}...")
        subprocess.run(
            ["docker", "build", "-t", f"app{app_num}-backend", backend_dir], 
            check=True
        )

        # Check frontend Dockerfile
        frontend_dir = os.path.join(app_dir, "frontend")
        if not os.path.exists(os.path.join(frontend_dir, "Dockerfile")):
            print(f"No Dockerfile found in {frontend_dir}")
            return False

        # Build frontend
        print(f"Building frontend for app{app_num}...")
        subprocess.run(
            ["docker", "build", "-t", f"app{app_num}-frontend", frontend_dir],
            check=True
        )

        # Create docker-compose.yml
        compose_content = f"""version: '3.8'
services:
    backend:
        image: app{app_num}-backend
        ports:
            - "{5000 + app_num}:5000"
        restart: always

    frontend:
        image: app{app_num}-frontend
        ports:
            - "{5173 + app_num}:5173"
        volumes:
            - ./frontend:/app
        depends_on:
            - backend
        restart: always
"""
        compose_path = os.path.join(app_dir, "docker-compose.yml")
        with open(compose_path, "w") as f:
            f.write(compose_content)

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error building app{app_num}: {e}")
        return False

def main():
    base_dir = Path("ChatGPT/flask_apps")
    successful_builds = []
    failed_builds = []

    for i in range(1, 21):
        app_dir = base_dir / f"app{i}"
        if app_dir.exists():
            print(f"\nBuilding app{i}...")
            if build_app(str(app_dir), i):
                successful_builds.append(i)
            else:
                failed_builds.append(i)
        else:
            print(f"Directory {app_dir} not found. Skipping...")

    print("\nBuild Summary:")
    print(f"Successful builds: {successful_builds}")
    if failed_builds:
        print(f"Failed builds: {failed_builds}")

if __name__ == "__main__":
    main()