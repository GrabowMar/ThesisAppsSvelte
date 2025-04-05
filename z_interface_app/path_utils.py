# Add this utility module to your project: path_utils.py

import os
import logging
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

class PathUtils:
    """Centralized path handling utilities for consistent path resolution across the application."""
    
    @staticmethod
    def normalize_app_path(base_path: Union[Path, str], model: str, app_num: int) -> Path:
        """
        Normalize path for a specific app, handling special cases like z_interface_app.
        
        Args:
            base_path: Base directory path
            model: Model name (e.g., "Llama")
            app_num: Application number
            
        Returns:
            Normalized path to the app directory
        """
        # Convert string to Path if needed
        if isinstance(base_path, str):
            base_path = Path(base_path)
        
        # First try the direct path
        direct_path = base_path / f"{model}/app{app_num}"
        if direct_path.exists():
            return direct_path
            
        # Try alternate paths if direct path doesn't exist
        # 1. Check if we need to remove z_interface_app
        adjusted_path = PathUtils.remove_interface_component(base_path)
        if adjusted_path != base_path:
            alt_path = adjusted_path / f"{model}/app{app_num}"
            if alt_path.exists():
                return alt_path
        
        # 2. Check if we need to add z_interface_app
        potential_interface_path = base_path / "z_interface_app" / f"{model}/app{app_num}"
        if potential_interface_path.exists():
            return potential_interface_path
            
        # 3. Try lowercase model name
        lowercase_path = base_path / f"{model.lower()}/app{app_num}"
        if lowercase_path.exists():
            return lowercase_path
            
        # 4. Try with z_interface_app and lowercase
        interface_lowercase_path = base_path / "z_interface_app" / f"{model.lower()}/app{app_num}"
        if interface_lowercase_path.exists():
            return interface_lowercase_path
            
        # If no path exists, return the direct path and log a warning
        logger.warning(f"Could not find valid path for {model}/app{app_num}, returning default path")
        return direct_path
    
    @staticmethod
    def remove_interface_component(path: Path) -> Path:
        """
        Remove z_interface_app component from a path if it exists.
        
        Args:
            path: Path to process
            
        Returns:
            Path with z_interface_app component removed if present
        """
        try:
            parts = list(path.parts)
            interface_indices = [i for i, part in enumerate(parts) 
                                if part.lower() in ('z_interface_app', 'z_interface_apps')]
            
            if interface_indices:
                # Remove the z_interface_app component
                new_parts = parts[:interface_indices[0]] + parts[interface_indices[0]+1:]
                adjusted = Path(*new_parts)
                logger.info(f"Adjusted path from {path} to {adjusted}")
                return adjusted
                
            return path
        except Exception as e:
            logger.error(f"Error adjusting path {path}: {e}")
            return path
    
    @staticmethod
    def find_app_directory(base_path: Path, model: str, app_num: int, 
                           create_if_missing: bool = False) -> Optional[Path]:
        """
        Find the correct directory for an app, trying multiple strategies.
        
        Args:
            base_path: Base directory
            model: Model name
            app_num: App number
            create_if_missing: Whether to create directory if missing
            
        Returns:
            Path object if found, None otherwise
        """
        # Try all likely paths
        possible_paths = [
            base_path / f"{model}/app{app_num}",
            base_path / f"{model.lower()}/app{app_num}",
            base_path / "z_interface_app" / f"{model}/app{app_num}",
            base_path / "z_interface_app" / f"{model.lower()}/app{app_num}",
            PathUtils.remove_interface_component(base_path) / f"{model}/app{app_num}",
            PathUtils.remove_interface_component(base_path) / f"{model.lower()}/app{app_num}"
        ]
        
        # Check each path
        for path in possible_paths:
            if path.exists():
                return path
                
        # Create directory if requested
        if create_if_missing:
            # Use the first path as default
            path = possible_paths[0]
            os.makedirs(path, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return path
            
        return None