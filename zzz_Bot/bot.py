#!/usr/bin/env python3
import csv
import json
import logging
import re
import sqlite3
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog

# =============================================================================
# Application Configuration
# =============================================================================
APP_CONFIG = {
    "presets_dir": Path("zzz_Bot/app_templates"),  # Folder with template files
    "default_template_ext": ".md",
    "allowed_models": {
        "Llama", "Mistral", "DeepSeek", "GPT4o", "Claude", 
        "Gemini", "Grok", "R1", "O3"
    },
    "db_path": "assistant.db"
}

# =============================================================================
# Model Configuration - IMPORTANT: Order must match app.py
# =============================================================================
@dataclass
class AIModel:
    name: str
    color: str

AI_MODELS: List[AIModel] = [
    AIModel("Llama", "#f97316"),
    AIModel("Mistral", "#9333ea"),
    AIModel("DeepSeek", "#ff5555"),
    AIModel("GPT4o", "#10a37f"),
    AIModel("Claude", "#7b2bf9"),
    AIModel("Gemini", "#1a73e8"),
    AIModel("Grok", "#ff4d4f"),
    AIModel("R1", "#fa541c"),
    AIModel("O3", "#0ca57f")
]

# =============================================================================
# Natural Sort Helper
# =============================================================================
def _natural_sort_key(s: str):
    """
    Split string into list of ints and lower-case text for natural sorting,
    so "app2" < "app10".
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

try:
    from natsort import natsorted
except ImportError:
    def natsorted(seq):
        return sorted(seq, key=_natural_sort_key)

# =============================================================================
# Logging Setup
# =============================================================================
logger = logging.getLogger("CodeGenAssistant")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("assistant.log")
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt="%H:%M:%S"))
logger.addHandler(file_handler)

# =============================================================================
# Port Management - Synchronized with app.py
# =============================================================================
class PortManager:
    BASE_BACKEND_PORT = 5001
    BASE_FRONTEND_PORT = 5501
    PORTS_PER_APP = 2
    BUFFER_PORTS = 20
    APPS_PER_MODEL = 30

    @classmethod
    def get_port_range(cls, model_idx: int) -> Dict[str, Dict[str, int]]:
        total_needed = cls.APPS_PER_MODEL * cls.PORTS_PER_APP + cls.BUFFER_PORTS
        return {
            "backend": {
                "start": cls.BASE_BACKEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_BACKEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
            },
            "frontend": {
                "start": cls.BASE_FRONTEND_PORT + (model_idx * total_needed),
                "end": cls.BASE_FRONTEND_PORT + ((model_idx + 1) * total_needed) - cls.BUFFER_PORTS,
            },
        }

    @classmethod
    def get_app_ports(cls, model_idx: int, app_num: int) -> Dict[str, int]:
        rng = cls.get_port_range(model_idx)
        return {
            "backend": rng["backend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
            "frontend": rng["frontend"]["start"] + (app_num - 1) * cls.PORTS_PER_APP,
        }

# Helper function to get model index (consistent with app.py)
def get_model_index(model_name: str) -> int:
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)

# =============================================================================
# DatabaseClient
# =============================================================================
class DatabaseClient:
    """
    Handles all database interactions for progress logs, model/app status, and research notes.
    Note: The research_notes table now includes model, app, and note_type.
    """
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()
        self._create_model_app_table()
        self._create_research_table()

    def _create_tables(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS progress_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    def _create_model_app_table(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS model_app_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    app TEXT NOT NULL,
                    app_py INTEGER NOT NULL DEFAULT 0,
                    app_react INTEGER NOT NULL DEFAULT 0,
                    comment TEXT
                );
            ''')

    def _create_research_table(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS research_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT,
                    app TEXT,
                    note_type TEXT,
                    note TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')

    # -------------------------
    # Progress Logs
    # -------------------------
    def log_progress(self, task: str, progress: int, message: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO progress_logs (task, progress, message) VALUES (?, ?, ?)",
                (task, progress, message)
            )
        logger.info(f"{task} - {progress}%: {message}")

    def get_recent_logs(self, limit: int = 100):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, task, progress, message, timestamp FROM progress_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,))
        return cursor.fetchall()

    def clear_logs(self) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM progress_logs")
        logger.info("Cleared all progress logs.")

    # -------------------------
    # Model & App Status
    # -------------------------
    def get_all_model_app_status(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, model, app, app_py, app_react, comment FROM model_app_status")
        return cursor.fetchall()

    def insert_model_app_status(self, model: str, app: str, app_py=False, app_react=False, comment=""):
        with self.conn:
            self.conn.execute('''
                INSERT INTO model_app_status (model, app, app_py, app_react, comment)
                VALUES (?, ?, ?, ?, ?)
            ''', (model, app, int(app_py), int(app_react), comment))

    def update_model_app_status(self, row_id: int, model: str, app: str,
                                  app_py: bool, app_react: bool, comment: str):
        with self.conn:
            self.conn.execute('''
                UPDATE model_app_status
                SET model = ?, app = ?, app_py = ?, app_react = ?, comment = ?
                WHERE id = ?
            ''', (model, app, int(app_py), int(app_react), comment, row_id))

    def delete_model_app_status_by_id(self, row_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM model_app_status WHERE id = ?", (row_id,))

    # -------------------------
    # Research Notes
    # -------------------------
    def insert_research_note(self, model: str, app: str, note_type: str, note: str) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO research_notes (model, app, note_type, note) VALUES (?, ?, ?, ?)",
                (model, app, note_type, note)
            )

    def update_research_note(self, row_id: int, model: str, app: str, note_type: str, note: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE research_notes SET model = ?, app = ?, note_type = ?, note = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?",
                (model, app, note_type, note, row_id)
            )

    def delete_research_note_by_id(self, row_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM research_notes WHERE id = ?", (row_id,))

    def get_research_notes(self, limit: int = 100):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, model, app, note_type, note, timestamp FROM research_notes ORDER BY timestamp DESC LIMIT ?",
            (limit,))
        return cursor.fetchall()

# =============================================================================
# Main GUI Application
# =============================================================================
class AssistantApp(tk.Tk):
    """Main application class containing all tabs and UI logic."""
    def __init__(self) -> None:
        super().__init__()
        self.title("Code Generation Assistant")
        self.geometry("1200x900")
        self.configure(bg="white")

        self.database = DatabaseClient(APP_CONFIG["db_path"])
        self.pause_refresh = False

        self._setup_menu()
        self._setup_main_ui()
        self._setup_logging_handler()

    # -------------------------------------------------------------------------
    # MENU
    # -------------------------------------------------------------------------
    def _setup_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", "Code Generation Assistant\nVersion 1.0"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    # -------------------------------------------------------------------------
    # MAIN UI
    # -------------------------------------------------------------------------
    def _setup_main_ui(self) -> None:
        # Create log panel first so logging works during initialization
        self._create_log_panel()  # This needs to happen first!
        
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill="both", expand=True)

        self._create_summary_tab()           # Tab 0: Summary Dashboard
        self._create_template_manager_tab()  # Tab 1: Template Manager
        self._create_ports_info_tab()        # Tab 2: Ports
        self._create_generate_code_tab()     # Tab 3: Generate Code
        self._create_file_replace_tab()      # Tab 4: Replace Files
        self._create_model_app_tab()         # Tab 5: Model & App Status
        self._create_research_tab()          # Tab 6: Research Notes
        self._create_progress_log_tab()      # Tab 7: Progress Notes

    def _setup_logging_handler(self) -> None:
        gui_handler = GuiLogHandler(self)
        logger.addHandler(gui_handler)

# -------------------------------------------------------------------------
# TAB 0: Summary Dashboard - One-stop workflow center
# -------------------------------------------------------------------------
    def _create_summary_tab(self) -> None:
        self.summary_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.summary_tab, text="Summary")
        self.main_notebook.select(0)  # Make Summary tab the default
        
        # Top frame with model and app selection
        top_frame = ttk.LabelFrame(self.summary_tab, text="Project Selection")
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Model & App Selection
        model_frame = ttk.Frame(top_frame)
        model_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(model_frame, text="Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.summary_model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]
        self.summary_model_dropdown = ttk.Combobox(model_frame, textvariable=self.summary_model_var,
                                                values=models, state="readonly", width=20)
        if models:
            self.summary_model_var.set(models[0])
        self.summary_model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.summary_model_dropdown.bind("<<ComboboxSelected>>", self._on_summary_model_selected)
        
        ttk.Label(model_frame, text="App:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.summary_app_var = tk.StringVar()
        # Populate apps based on selected model
        base_dir = Path('.') / self.summary_model_var.get()
        apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], 
                        key=_natural_sort_key) if base_dir.exists() else []
        
        self.summary_app_dropdown = ttk.Combobox(model_frame, textvariable=self.summary_app_var,
                                            values=apps, state="readonly", width=20)
        if apps:
            self.summary_app_var.set(apps[0])
        self.summary_app_dropdown.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        
        ttk.Button(model_frame, text="Refresh All", 
                command=self._refresh_summary_page).grid(row=0, column=4, padx=10, pady=2)
        
        # Main content frame - split into three columns
        content_frame = ttk.Frame(self.summary_tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left panel - Template selection & Preview
        left_frame = ttk.LabelFrame(content_frame, text="Template")
        left_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        template_select_frame = ttk.Frame(left_frame)
        template_select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(template_select_frame, text="Select Template:").pack(side="left")
        self.summary_template_var = tk.StringVar()
        presets = self._scan_template_presets()
        self.summary_template_dropdown = ttk.Combobox(
            template_select_frame, textvariable=self.summary_template_var,
            values=presets, state="readonly", width=30
        )
        if presets:
            self.summary_template_var.set(presets[0])
        self.summary_template_dropdown.pack(side="left", padx=5)
        
        ttk.Button(template_select_frame, text="Load", 
                command=self._load_summary_template).pack(side="left", padx=5)
        ttk.Button(template_select_frame, text="Copy Template", 
                command=self._copy_summary_template).pack(side="left", padx=5)
        
        # Template preview
        template_frame = ttk.Frame(left_frame)
        template_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.summary_template_text = scrolledtext.ScrolledText(template_frame, wrap="word", height=10)
        self.summary_template_text.pack(fill="both", expand=True)
        
        # Middle panel - Quick Paste & Replace
        middle_frame = ttk.LabelFrame(content_frame, text="Quick Paste & Replace")
        middle_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # File type selector
        file_type_frame = ttk.Frame(middle_frame)
        file_type_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(file_type_frame, text="File Type:").pack(side="left", padx=5)
        self.summary_file_type_var = tk.StringVar()
        file_types = ["app.py", "App.jsx", "App.css", "requirements.txt", "package.json", "vite.config.js"]
        self.summary_file_type_dropdown = ttk.Combobox(
            file_type_frame, textvariable=self.summary_file_type_var,
            values=file_types, state="readonly", width=20
        )
        self.summary_file_type_var.set(file_types[0])
        self.summary_file_type_dropdown.pack(side="left", padx=5)
        
        # Quick paste buttons 
        paste_btn_frame = ttk.Frame(file_type_frame)
        paste_btn_frame.pack(side="left", padx=5)
        
        ttk.Button(paste_btn_frame, text="Paste Code", 
                command=self._paste_to_summary_editor).pack(side="left", padx=5)
        ttk.Button(paste_btn_frame, text="One-Click Paste & Replace", 
                command=self._one_click_paste_and_replace).pack(side="left", padx=5)
        
        # Code editor
        code_frame = ttk.Frame(middle_frame)
        code_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.summary_code_editor = scrolledtext.ScrolledText(code_frame, wrap="none", height=10)
        self.summary_code_editor.pack(fill="both", expand=True)
        
        # Replace button
        ttk.Button(middle_frame, text="Replace File with Content Above", 
                command=self._replace_from_summary_editor).pack(side="bottom", padx=5, pady=5)
        
        # Right panel - Info & Actions
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # Port information
        port_frame = ttk.LabelFrame(right_frame, text="Port Information")
        port_frame.pack(fill="x", padx=5, pady=5)
        
        self.summary_port_info = ttk.Treeview(port_frame, columns=("name", "value"), 
                                            show="headings", height=4)
        self.summary_port_info.heading("name", text="Item")
        self.summary_port_info.heading("value", text="Value")
        self.summary_port_info.column("name", width=150)
        self.summary_port_info.column("value", width=200)
        self.summary_port_info.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(port_frame, text="Copy Port Info", 
                command=self._copy_summary_port_info).pack(side="right", padx=5, pady=5)
        
        # Status information
        status_frame = ttk.LabelFrame(right_frame, text="Code Status")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        self.summary_status_info = ttk.Treeview(status_frame, columns=("file", "status"), 
                                            show="headings", height=5)
        self.summary_status_info.heading("file", text="File")
        self.summary_status_info.heading("status", text="Status")
        self.summary_status_info.column("file", width=150)
        self.summary_status_info.column("status", width=200)
        self.summary_status_info.pack(fill="x", padx=5, pady=5)
        
        # Research notes
        notes_frame = ttk.LabelFrame(right_frame, text="Research Notes")
        notes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.summary_notes_text = scrolledtext.ScrolledText(notes_frame, wrap="word", height=5)
        self.summary_notes_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        notes_btn_frame = ttk.Frame(notes_frame)
        notes_btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(notes_btn_frame, text="Add Note", 
                command=self._add_summary_research_note).pack(side="left", padx=5)
        ttk.Button(notes_btn_frame, text="View All Notes", 
                command=lambda: self.main_notebook.select(6)).pack(side="left", padx=5)
        
        # Quick action buttons
        action_frame = ttk.LabelFrame(self.summary_tab, text="Actions")
        action_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(action_frame, text="Generate Code", 
                command=lambda: self.main_notebook.select(3)).pack(side="left", padx=5, pady=5)
        ttk.Button(action_frame, text="Replace Files", 
                command=lambda: self.main_notebook.select(4)).pack(side="left", padx=5, pady=5)
        ttk.Button(action_frame, text="Copy Workflow Command", 
                command=self._copy_workflow_command).pack(side="left", padx=5, pady=5)
        
        # Initialize the summary page data
        self._refresh_summary_page()

    def _paste_to_summary_editor(self) -> None:
        """Paste clipboard content to the summary code editor"""
        try:
            content = self.clipboard_get()
            self.summary_code_editor.delete("1.0", tk.END)
            self.summary_code_editor.insert(tk.END, content)
            self._log("Code pasted to editor")
        except Exception as e:
            self._log(f"Could not get clipboard content: {e}", error=True)

    def _replace_from_summary_editor(self) -> None:
        """Replace the selected file type with content from the summary code editor"""
        file_type = self.summary_file_type_var.get()
        content = self.summary_code_editor.get("1.0", tk.END)
        
        if not content.strip():
            self._log("No content to replace with", error=True)
            return
        
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self._log("Model or App not selected", error=True)
            return
        
        self._run_in_thread(lambda: self._replace_file_content(file_type, content))()
        
        # Update status info after replacement
        self.after(1000, self._update_summary_status_info)

    def _one_click_paste_and_replace(self) -> None:
        """One-click operation to paste from clipboard and immediately replace file"""
        try:
            # Get content from clipboard
            content = self.clipboard_get()
            
            # Update the code editor for user reference
            self.summary_code_editor.delete("1.0", tk.END)
            self.summary_code_editor.insert(tk.END, content)
            
            # Immediately replace the file
            file_type = self.summary_file_type_var.get()
            model = self.summary_model_var.get()
            app = self.summary_app_var.get()
            
            if not content.strip():
                self._log("Clipboard is empty", error=True)
                return
                
            if not model or not app:
                self._log("Model or App not selected", error=True)
                return
            
            # Confirm replacement with a more streamlined dialog
            if messagebox.askyesno("Quick Replace", 
                                f"Replace {file_type} in {model}/{app}?",
                                icon='question'):
                self._run_in_thread(lambda: self._replace_file_content(file_type, content))()
                
                # Update status info after replacement
                self.after(1000, self._update_summary_status_info)
                
                self._log(f"One-click replacement complete: {file_type}")
            else:
                self._log("One-click replacement cancelled")
                
        except Exception as e:
            self._log(f"One-click paste and replace failed: {e}", error=True)

    def _on_summary_model_selected(self, event=None) -> None:
        """Update app dropdowns when a model is selected in summary tab"""
        model = self.summary_model_var.get()
        base_dir = Path('.') / model
        apps = []
        if base_dir.exists():
            apps = natsorted([d.name for d in base_dir.iterdir() 
                        if d.is_dir() and d.name.lower().startswith("app")],
                        key=_natural_sort_key)
        
        self.summary_app_dropdown["values"] = apps
        if apps:
            self.summary_app_var.set(apps[0])
        else:
            self.summary_app_var.set("")
        
        # Refresh all data with new model/app
        self._refresh_summary_page()

    def _refresh_summary_page(self) -> None:
        """Refresh all data on the summary page"""
        self._update_summary_port_info()
        self._update_summary_status_info()
        self._update_summary_notes()
        
        # If a template is selected, load it
        if self.summary_template_var.get():
            self._load_summary_template()

    def _load_summary_template(self) -> None:
        """Load the selected template into the summary preview"""
        preset_name = self.summary_template_var.get()
        path = APP_CONFIG["presets_dir"] / preset_name
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                self.summary_template_text.delete("1.0", tk.END)
                self.summary_template_text.insert(tk.END, content)
                self._log(f"Loaded template: {preset_name}")
            except Exception as e:
                self._log(f"Error loading template: {e}", error=True)
        else:
            self._log("Template file not found", error=True)

    def _copy_summary_template(self) -> None:
        """Copy the template content to clipboard"""
        content = self.summary_template_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        self._log("Template copied to clipboard.")

    def _update_summary_port_info(self) -> None:
        """Update the port information display"""
        # Clear existing items
        for row in self.summary_port_info.get_children():
            self.summary_port_info.delete(row)
        
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            return
        
        # Extract app number from app name (e.g., "app5" -> 5)
        match = re.search(r'(\d+)', app)
        if not match:
            return
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        ports = PortManager.get_app_ports(model_idx, app_num)
        
        # Insert port information
        self.summary_port_info.insert("", tk.END, values=("Model", model))
        self.summary_port_info.insert("", tk.END, values=("App", app))
        self.summary_port_info.insert("", tk.END, values=("Backend Port", ports["backend"]))
        self.summary_port_info.insert("", tk.END, values=("Frontend Port", ports["frontend"]))
        
        # Add copy-ready format
        ready_text = f"(frontend {ports['frontend']} and backend {ports['backend']})"
        self.summary_port_info.insert("", tk.END, values=("Copy-Ready Format", ready_text))

    def _copy_summary_port_info(self) -> None:
        """Copy the port information in a ready-to-use format"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self._log("Model or app not selected", error=True)
            return
        
        match = re.search(r'(\d+)', app)
        if not match:
            self._log("Invalid app format", error=True)
            return
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        ports = PortManager.get_app_ports(model_idx, app_num)
        
        copy_text = f"(frontend {ports['frontend']} and backend {ports['backend']})"
        self.clipboard_clear()
        self.clipboard_append(copy_text)
        self._log(f"Copied port info: {copy_text}")

    def _update_summary_status_info(self) -> None:
        """Update the code status information display"""
        # Clear existing items
        for row in self.summary_status_info.get_children():
            self.summary_status_info.delete(row)
        
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            return
        
        app_path = Path('.') / model / app
        
        # Check various file statuses
        files_to_check = [
            ("app.py", app_path / "backend" / "app.py"),
            ("App.jsx", app_path / "frontend" / "src" / "App.jsx"),
            ("App.css", app_path / "frontend" / "src" / "App.css"),
            ("requirements.txt", app_path / "backend" / "requirements.txt"),
            ("package.json", app_path / "frontend" / "package.json"),
            ("vite.config.js", app_path / "frontend" / "vite.config.js")
        ]
        
        for file_name, file_path in files_to_check:
            status = "✅ Present" if file_path.exists() else "❌ Missing"
            self.summary_status_info.insert("", tk.END, values=(file_name, status))

    def _update_summary_notes(self) -> None:
        """Update the research notes display"""
        self.summary_notes_text.delete("1.0", tk.END)
        
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            return
        
        # Get recent notes for this model/app
        notes = self.database.get_research_notes(limit=100)
        relevant_notes = []
        for note in notes:
            note_id, note_model, note_app, note_type, note_text, timestamp = note
            if note_model == model and note_app == app:
                relevant_notes.append((timestamp, note_type, note_text))
        
        if not relevant_notes:
            self.summary_notes_text.insert(tk.END, "No research notes for this model/app.")
            return
        
        # Display the most recent notes (limit to 3)
        for i, (timestamp, note_type, note_text) in enumerate(relevant_notes[:3]):
            if i > 0:
                self.summary_notes_text.insert(tk.END, "\n\n" + "-"*50 + "\n\n")
            
            self.summary_notes_text.insert(tk.END, f"[{timestamp}] {note_type}\n\n")
            self.summary_notes_text.insert(tk.END, note_text)

    def _add_summary_research_note(self) -> None:
        """Add a new research note from the summary tab"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self._log("Model or app not selected", error=True)
            return
        
        # Switch to the research tab and set up for a new note
        self.main_notebook.select(6)  # Index of research tab
        self.research_model_var.set(model)
        self._on_research_model_selected(None)  # Update app dropdown
        self.research_app_var.set(app)
        self._new_research_note()

    def _copy_workflow_command(self) -> None:
        """Copy a complete workflow command for reference"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self._log("Model or app not selected", error=True)
            return
        
        match = re.search(r'(\d+)', app)
        if not match:
            self._log("Invalid app format", error=True)
            return
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        ports = PortManager.get_app_ports(model_idx, app_num)
        
        # Build comprehensive command with all relevant info
        command = (
            f"# {model} {app} Workflow\n"
            f"# Backend Port: {ports['backend']}\n"
            f"# Frontend Port: {ports['frontend']}\n"
            f"# Directory: ./{model}/{app}/\n\n"
            f"# Start application:\n"
            f"cd ./{model}/{app} && docker-compose up -d\n\n"
            f"# Stop application:\n"
            f"cd ./{model}/{app} && docker-compose down\n\n"
            f"# Access URLs:\n"
            f"# Backend: http://localhost:{ports['backend']}\n"
            f"# Frontend: http://localhost:{ports['frontend']}\n"
        )
        
        self.clipboard_clear()
        self.clipboard_append(command)
        self._log("Copied workflow command.")



    # -------------------------------------------------------------------------
    # TAB 1: Template Manager
    # -------------------------------------------------------------------------
    def _create_template_manager_tab(self) -> None:
        self.template_manager_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.template_manager_tab, text="Template Manager")

        top_frame = ttk.Frame(self.template_manager_tab)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Select Template:").pack(side="left")
        self.template_var = tk.StringVar()

        presets = self._scan_template_presets()
        self.template_dropdown = ttk.Combobox(
            top_frame, textvariable=self.template_var,
            values=presets, state="readonly", width=40
        )
        if presets:
            self.template_var.set(presets[0])
        self.template_dropdown.pack(side="left", padx=5)

        ttk.Button(top_frame, text="Load", command=self._load_template).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Copy to Clipboard", command=self._copy_template_to_clipboard).pack(side="left", padx=5)

        self.template_text = tk.Text(self.template_manager_tab, wrap="word", height=25)
        self.template_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _scan_template_presets(self) -> list:
        APP_CONFIG["presets_dir"].mkdir(exist_ok=True)
        presets = [f.name for f in APP_CONFIG["presets_dir"].glob(f"*{APP_CONFIG['default_template_ext']}")]
        return natsorted(presets)

    def _load_template(self) -> None:
        preset_name = self.template_var.get()
        path = APP_CONFIG["presets_dir"] / preset_name
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8")
                self.template_text.delete("1.0", tk.END)
                self.template_text.insert(tk.END, content)
                self._log(f"Loaded template: {preset_name}")
            except Exception as e:
                self._log(f"Error loading template: {e}", error=True)
        else:
            self._log("Template file not found", error=True)

    def _copy_template_to_clipboard(self) -> None:
        content = self.template_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        self._log("Template copied to clipboard.")

    # -------------------------------------------------------------------------
    # TAB 2: Generate Code
    # -------------------------------------------------------------------------
    def _create_generate_code_tab(self) -> None:
        self.generate_code_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.generate_code_tab, text="Generate Code")

        top_frame = ttk.Frame(self.generate_code_tab)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(top_frame, text="Paste LLM Output", command=self._paste_from_clipboard).pack(side="left", padx=5)

        self.code_notebook = ttk.Notebook(self.generate_code_tab)
        self.code_notebook.pack(fill="both", expand=True, padx=10, pady=5)

        # Existing tabs...
        self.app_py_frame = ttk.Frame(self.code_notebook)
        self.app_py_text = tk.Text(self.app_py_frame, wrap="none")
        self.app_py_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.app_py_frame, text="app.py")

        self.app_css_frame = ttk.Frame(self.code_notebook)
        self.app_css_text = tk.Text(self.app_css_frame, wrap="none")
        self.app_css_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.app_css_frame, text="App.css")

        self.app_react_frame = ttk.Frame(self.code_notebook)
        self.app_react_text = tk.Text(self.app_react_frame, wrap="none")
        self.app_react_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.app_react_frame, text="App.jsx")

        self.requirements_frame = ttk.Frame(self.code_notebook)
        self.requirements_text = tk.Text(self.requirements_frame, wrap="none")
        self.requirements_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.requirements_frame, text="requirements.txt")

        self.package_json_frame = ttk.Frame(self.code_notebook)
        self.package_json_text = tk.Text(self.package_json_frame, wrap="none")
        self.package_json_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.package_json_frame, text="package.json")

        # New tab for vite.config.js
        self.vite_config_frame = ttk.Frame(self.code_notebook)
        self.vite_config_text = tk.Text(self.vite_config_frame, wrap="none")
        self.vite_config_text.pack(fill="both", expand=True)
        self.code_notebook.add(self.vite_config_frame, text="vite.config.js")


    def _paste_from_clipboard(self) -> None:
        try:
            text = self.clipboard_get()
        except Exception as e:
            self._log(f"Could not get clipboard content: {e}", error=True)
            return

        current_index = self.code_notebook.index(self.code_notebook.select())
        target_widget = [
            self.app_py_text,
            self.app_css_text,
            self.app_react_text,
            self.requirements_text,
            self.package_json_text,
            self.vite_config_text
        ][current_index]

        target_widget.delete("1.0", tk.END)
        target_widget.insert(tk.END, text)
        self._log("Clipboard content pasted successfully.")

    # -------------------------------------------------------------------------
    # TAB 3: Replace Files
    # -------------------------------------------------------------------------
    def _create_file_replace_tab(self) -> None:
        self.file_replace_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.file_replace_tab, text="Replace Files")

        sel_frame = ttk.Frame(self.file_replace_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(sel_frame, text="Select Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.replace_model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]  # Use the same order as app.py
        self.replace_model_dropdown = ttk.Combobox(sel_frame, textvariable=self.replace_model_var,
                                                   values=models, state="readonly", width=30)
        if models:
            self.replace_model_var.set(models[0])
        self.replace_model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.replace_model_dropdown.bind("<<ComboboxSelected>>", self._on_replace_model_selected)

        ttk.Label(sel_frame, text="Select App:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.replace_app_var = tk.StringVar()

        if self.replace_model_var.get():
            base_dir = Path('.') / self.replace_model_var.get()
            apps = natsorted(
                [d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")],
                key=_natural_sort_key
            )
        else:
            apps = []

        self.replace_app_dropdown = ttk.Combobox(sel_frame, textvariable=self.replace_app_var,
                                                 values=apps, state="readonly", width=30)
        if apps:
            self.replace_app_var.set(apps[0])
        self.replace_app_dropdown.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        btn_frame = ttk.Frame(self.file_replace_tab)
        btn_frame.pack(padx=10, pady=5)

        ttk.Button(btn_frame, text="Replace app.py",
                command=self._run_in_thread(lambda: self._replace_file_content("app.py", self.app_py_text.get("1.0", tk.END)))).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace App.jsx",
                command=self._run_in_thread(lambda: self._replace_file_content("App.jsx", self.app_react_text.get("1.0", tk.END)))).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace requirements.txt",
                command=self._run_in_thread(lambda: self._replace_file_content("requirements.txt", self.requirements_text.get("1.0", tk.END)))).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace package.json",
                command=self._run_in_thread(lambda: self._replace_file_content("package.json", self.package_json_text.get("1.0", tk.END)))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace App.css",
                command=self._run_in_thread(lambda: self._replace_file_content("App.css", self.app_css_text.get("1.0", tk.END)))).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace All",
                command=self._run_in_thread(self._replace_all_files)).grid(row=2, column=0, padx=5, pady=5)
        # New button for vite.config.js
        ttk.Button(btn_frame, text="Replace vite.config.js",
                command=self._run_in_thread(lambda: self._replace_file_content("vite.config.js", self.vite_config_text.get("1.0", tk.END)))).grid(row=3, column=0, padx=5, pady=5)
                
    def _on_replace_model_selected(self, event=None) -> None:
        model = self.replace_model_var.get()
        base_dir = Path('.') / model
        apps = natsorted(
            [d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")],
            key=_natural_sort_key
        )
        self.replace_app_dropdown["values"] = apps
        self.replace_app_var.set(apps[0] if apps else "")

    def _replace_file_content(self, filename: str, new_content: str) -> None:
        task = f"Replace {filename}"
        self.database.log_progress(task, 0, "Starting file replacement")

        model = self.replace_model_var.get()
        app_name = self.replace_app_var.get()
        if not model or not app_name:
            self._log("Model or App not selected", error=True)
            return

        # Determine target subfolder based on filename
        if filename in ("app.py", "requirements.txt"):
            subfolder = "backend"
        elif filename in ("App.jsx", "App.css"):
            subfolder = "frontend/src"
        elif filename in ("package.json", "vite.config.js"):  # Added vite.config.js here
            subfolder = "frontend"
        else:
            subfolder = ""

        target_dir = Path('.') / model / app_name / subfolder
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / filename
        if not messagebox.askyesno("Confirm Replacement", f"Replace the content of {target_file}?"):
            self._log("Replacement canceled.")
            return

        new_content = new_content.strip()
        if not new_content:
            self._log("No content provided for replacement.", error=True)
            return

        try:
            target_file.write_text(new_content, encoding="utf-8")
            self.database.log_progress(task, 100, f"Replaced content of {target_file}")
            self._log(f"Replaced content of {target_file}")
        except Exception as e:
            self._log(f"Failed to replace file content: {e}", error=True)
            self.database.log_progress(task, 0, f"Error: {e}")

    def _replace_all_files(self) -> None:
        self._replace_file_content("app.py", self.app_py_text.get("1.0", tk.END))
        self._replace_file_content("App.jsx", self.app_react_text.get("1.0", tk.END))
        self._replace_file_content("requirements.txt", self.requirements_text.get("1.0", tk.END))
        self._replace_file_content("package.json", self.package_json_text.get("1.0", tk.END))
        self._replace_file_content("App.css", self.app_css_text.get("1.0", tk.END))
        self._replace_file_content("vite.config.js", self.vite_config_text.get("1.0", tk.END))

    # -------------------------------------------------------------------------
    # TAB 4: Ports Info with Filtering & Sorting
    # -------------------------------------------------------------------------
    def _create_ports_info_tab(self) -> None:
        self.ports_info_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.ports_info_tab, text="Ports")

        self.ports_sort_column = None
        self.ports_sort_reverse = False
        self.ports_data = []

        top_frame = ttk.Frame(self.ports_info_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(top_frame, text="Refresh Ports", command=self._refresh_ports_table).pack(side="left", padx=5)

        tk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.ports_filter_var = tk.StringVar()
        entry = tk.Entry(top_frame, textvariable=self.ports_filter_var)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda event: self._refresh_ports_table())
        ttk.Button(top_frame, text="Apply Filter", command=self._refresh_ports_table).pack(side="left", padx=5)

        columns = ("model", "app_folder", "app_num", "backend", "frontend", "backend_range", "frontend_range")
        self.ports_table = ttk.Treeview(self.ports_info_tab, columns=columns, show="headings")

        self.ports_table.heading("model", text="Model", command=lambda: self._sort_ports_table("model"))
        self.ports_table.heading("app_folder", text="App Folder", command=lambda: self._sort_ports_table("app_folder"))
        self.ports_table.heading("app_num", text="App #", command=lambda: self._sort_ports_table("app_num"))
        self.ports_table.heading("backend", text="Backend Port", command=lambda: self._sort_ports_table("backend"))
        self.ports_table.heading("frontend", text="Frontend Port", command=lambda: self._sort_ports_table("frontend"))
        self.ports_table.heading("backend_range", text="Backend Range", command=lambda: self._sort_ports_table("backend_range"))
        self.ports_table.heading("frontend_range", text="Frontend Range", command=lambda: self._sort_ports_table("frontend_range"))

        self.ports_table.column("model", width=100)
        self.ports_table.column("app_folder", width=150)
        self.ports_table.column("app_num", width=70, anchor="center")
        self.ports_table.column("backend", width=100, anchor="center")
        self.ports_table.column("frontend", width=100, anchor="center")
        self.ports_table.column("backend_range", width=150, anchor="center")
        self.ports_table.column("frontend_range", width=150, anchor="center")

        vsb = ttk.Scrollbar(self.ports_info_tab, orient="vertical", command=self.ports_table.yview)
        self.ports_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.ports_table.pack(fill="both", expand=True, padx=10, pady=5)
        self.ports_table.bind("<Double-1>", self._on_ports_table_double_click)

        self._refresh_ports_table()

    def _refresh_ports_table(self) -> None:
        self.ports_data.clear()

        # Use the same order of models as app.py
        for i, model in enumerate(AI_MODELS):
            model_name = model.name
            model_dir = Path('.') / model_name
            if not model_dir.is_dir():
                continue

            rng = PortManager.get_port_range(i)
            backend_range_str = f"{rng['backend']['start']}-{rng['backend']['end']}"
            frontend_range_str = f"{rng['frontend']['start']}-{rng['frontend']['end']}"

            apps = sorted(
                [d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")],
                key=lambda d: _natural_sort_key(d.name)
            )
            for app_dir in apps:
                match = re.search(r'(\d+)', app_dir.name)
                app_num = int(match.group(1)) if match else 1
                ports = PortManager.get_app_ports(i, app_num)
                self.ports_data.append({
                    "model": model_name,
                    "app_folder": app_dir.name,
                    "app_num": app_num,
                    "backend": ports["backend"],
                    "frontend": ports["frontend"],
                    "backend_range": backend_range_str,
                    "frontend_range": frontend_range_str
                })

        filtered = self._apply_ports_filter(self.ports_data)
        if self.ports_sort_column:
            filtered = self._sort_ports_data(filtered, self.ports_sort_column, self.ports_sort_reverse)
        self._populate_ports_table(filtered)

    def _apply_ports_filter(self, data):
        ft = self.ports_filter_var.get().strip().lower()
        if not ft:
            return data
        result = []
        for row in data:
            if (ft in row["model"].lower() or
                ft in row["app_folder"].lower() or
                ft in str(row["app_num"]).lower() or
                ft in str(row["backend"]).lower() or
                ft in str(row["frontend"]).lower() or
                ft in row["backend_range"].lower() or
                ft in row["frontend_range"].lower()):
                result.append(row)
        return result

    def _sort_ports_table(self, col: str):
        if self.ports_sort_column == col:
            self.ports_sort_reverse = not self.ports_sort_reverse
        else:
            self.ports_sort_column = col
            self.ports_sort_reverse = False
        self._refresh_ports_table()

    def _sort_ports_data(self, data, col: str, reverse: bool):
        def sort_key(row):
            if col in ("app_num", "backend", "frontend"):
                return int(row[col])
            else:
                return _natural_sort_key(str(row[col]))
        return sorted(data, key=sort_key, reverse=reverse)

    def _populate_ports_table(self, data):
        for row in self.ports_table.get_children():
            self.ports_table.delete(row)
        for row in data:
            self.ports_table.insert("", tk.END, values=(
                row["model"],
                row["app_folder"],
                row["app_num"],
                row["backend"],
                row["frontend"],
                row["backend_range"],
                row["frontend_range"]
            ))

    def _on_ports_table_double_click(self, event) -> None:
        item_id = self.ports_table.identify_row(event.y)
        if not item_id:
            return
        vals = self.ports_table.item(item_id, "values")
        backend_port = vals[3]
        frontend_port = vals[4]
        text_to_copy = f"(frontend {frontend_port} and backend {backend_port})"
        self.clipboard_clear()
        self.clipboard_append(text_to_copy)
        self._log(f"Copied port numbers: {text_to_copy}")

    # -------------------------------------------------------------------------
    # TAB 5: Model & App Status (Auto-Discovered) with Filtering & Sorting
    # -------------------------------------------------------------------------
    def _create_model_app_tab(self) -> None:
        self.model_app_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.model_app_tab, text="Model & App Status")

        self.model_app_sort_column = None
        self.model_app_sort_reverse = False
        self.model_app_data = []

        top_frame = ttk.Frame(self.model_app_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(top_frame, text="Sync with Folders", command=self._run_in_thread(self._sync_folders_with_db)).pack(side="left", padx=5)

        tk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.model_app_filter_var = tk.StringVar()
        entry = tk.Entry(top_frame, textvariable=self.model_app_filter_var)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda event: self._refresh_model_app_table())

        ttk.Button(top_frame, text="Refresh", command=self._refresh_model_app_table).pack(side="left", padx=5)

        columns = ("id", "model", "app", "app_py", "app_react", "comment")
        self.model_app_table = ttk.Treeview(self.model_app_tab, columns=columns, show="headings")
        self.model_app_table.heading("id", text="ID", command=lambda: self._sort_model_app_table("id"))
        self.model_app_table.heading("model", text="Model", command=lambda: self._sort_model_app_table("model"))
        self.model_app_table.heading("app", text="App", command=lambda: self._sort_model_app_table("app"))
        self.model_app_table.heading("app_py", text="app.py?", command=lambda: self._sort_model_app_table("app_py"))
        self.model_app_table.heading("app_react", text="App.jsx?", command=lambda: self._sort_model_app_table("app_react"))
        self.model_app_table.heading("comment", text="Comment", command=lambda: self._sort_model_app_table("comment"))

        self.model_app_table.column("id", width=50)
        self.model_app_table.column("model", width=100)
        self.model_app_table.column("app", width=100)
        self.model_app_table.column("app_py", width=80, anchor="center")
        self.model_app_table.column("app_react", width=100, anchor="center")
        self.model_app_table.column("comment", width=250)

        vsb = ttk.Scrollbar(self.model_app_tab, orient="vertical", command=self.model_app_table.yview)
        self.model_app_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.model_app_table.pack(fill="both", expand=True, padx=10, pady=5)
        self.model_app_table.bind("<Double-1>", self._on_model_app_table_double_click)

        self._refresh_model_app_table()

    def _sync_folders_with_db(self) -> None:
        existing_rows = self.database.get_all_model_app_status()
        existing_map = {}
        for row in existing_rows:
            row_id, model, app, app_py, app_react, comment = row
            existing_map[(model, app)] = {"id": row_id, "comment": comment}

        discovered = []
        for model in AI_MODELS:  # Use model list from app.py
            model_name = model.name
            model_dir = Path('.') / model_name
            if model_dir.is_dir():
                apps = sorted(
                    [d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")],
                    key=lambda d: _natural_sort_key(d.name)
                )
                for subdir in apps:
                    discovered.append((model_name, subdir.name))

        discovered_set = set(discovered)

        for (model, app) in list(existing_map.keys()):
            if (model, app) not in discovered_set:
                self.database.delete_model_app_status_by_id(existing_map[(model, app)]["id"])

        for (model, app) in discovered:
            app_path = Path('.') / model / app
            has_app_py = (app_path / "backend" / "app.py").exists()
            has_react = (app_path / "frontend" / "src" / "App.jsx").exists()
            if (model, app) in existing_map:
                row_data = existing_map[(model, app)]
                self.database.update_model_app_status(
                    row_data["id"], model, app, has_app_py, has_react, row_data.get("comment", "")
                )
            else:
                self.database.insert_model_app_status(model, app, has_app_py, has_react, "")

        self._refresh_model_app_table()
        self._log("Model/App data synced with folders.")

    def _refresh_model_app_table(self) -> None:
        self.model_app_data = []
        rows = self.database.get_all_model_app_status()
        for row in rows:
            row_id, model, app, app_py, app_react, comment = row
            self.model_app_data.append({
                "id": row_id,
                "model": model,
                "app": app,
                "app_py": "☑" if app_py else "☐",
                "app_react": "☑" if app_react else "☐",
                "comment": comment or ""
            })

        filtered = self._apply_model_app_filter(self.model_app_data)
        if self.model_app_sort_column:
            filtered = self._sort_model_app_data(filtered, self.model_app_sort_column, self.model_app_sort_reverse)
        self._populate_model_app_table(filtered)

    def _apply_model_app_filter(self, data):
        ft = self.model_app_filter_var.get().strip().lower()
        if not ft:
            return data
        return [
            row for row in data
            if (ft in str(row["id"]).lower()
                or ft in row["model"].lower()
                or ft in row["app"].lower()
                or ft in row["app_py"].lower()
                or ft in row["app_react"].lower()
                or ft in row["comment"].lower())
        ]

    def _sort_model_app_table(self, col: str):
        if self.model_app_sort_column == col:
            self.model_app_sort_reverse = not self.model_app_sort_reverse
        else:
            self.model_app_sort_column = col
            self.model_app_sort_reverse = False
        self._refresh_model_app_table()

    def _sort_model_app_data(self, data, col: str, reverse: bool):
        def sort_key(row):
            if col == "id":
                return int(row["id"])
            elif col in ("app_py", "app_react"):
                return 0 if row[col] == "☐" else 1
            else:
                return _natural_sort_key(row[col])
        return sorted(data, key=sort_key, reverse=reverse)

    def _populate_model_app_table(self, data):
        for row in self.model_app_table.get_children():
            self.model_app_table.delete(row)
        for row in data:
            self.model_app_table.insert("", tk.END, values=(
                row["id"],
                row["model"],
                row["app"],
                row["app_py"],
                row["app_react"],
                row["comment"]
            ))

    def _on_model_app_table_double_click(self, event) -> None:
        item_id = self.model_app_table.identify_row(event.y)
        col_id = self.model_app_table.identify_column(event.x)
        if not item_id:
            return

        values = list(self.model_app_table.item(item_id, "values"))
        row_id, model, app, app_py_disp, app_react_disp, comment = values

        if col_id == "#4":
            new_val = "☑" if app_py_disp == "☐" else "☐"
            values[3] = new_val
            self.database.update_model_app_status(
                row_id, model, app,
                (new_val == "☑"), (app_react_disp == "☑"), comment
            )
        elif col_id == "#5":
            new_val = "☑" if app_react_disp == "☐" else "☐"
            values[4] = new_val
            self.database.update_model_app_status(
                row_id, model, app,
                (app_py_disp == "☑"), (new_val == "☑"), comment
            )
        elif col_id == "#6":
            new_comment = simpledialog.askstring("Edit Comment", "Enter comment:", initialvalue=comment)
            if new_comment is not None:
                values[5] = new_comment
                self.database.update_model_app_status(
                    row_id, model, app,
                    (app_py_disp == "☑"), (app_react_disp == "☑"), new_comment
                )

        self.model_app_table.item(item_id, values=values)

    # -------------------------------------------------------------------------
    # TAB 6: Research Notes
    # -------------------------------------------------------------------------
    def _create_research_tab(self) -> None:
        self.research_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.research_tab, text="Research Notes")

        # Reference selectors: Model, App, and Category
        ref_frame = ttk.Frame(self.research_tab)
        ref_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(ref_frame, text="Model:").pack(side="left", padx=5)
        self.research_model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]  # Use the same order as app.py
        self.research_model_dropdown = ttk.Combobox(ref_frame, textvariable=self.research_model_var,
                                                    values=models, state="readonly", width=20)
        if models:
            self.research_model_var.set(models[0])
        self.research_model_dropdown.pack(side="left", padx=5)
        self.research_model_dropdown.bind("<<ComboboxSelected>>", self._on_research_model_selected)

        ttk.Label(ref_frame, text="App:").pack(side="left", padx=5)
        self.research_app_var = tk.StringVar()
        if self.research_model_var.get():
            base_dir = Path('.') / self.research_model_var.get()
            apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], key=_natural_sort_key)
        else:
            apps = []
        self.research_app_dropdown = ttk.Combobox(ref_frame, textvariable=self.research_app_var,
                                                  values=apps, state="readonly", width=20)
        if apps:
            self.research_app_var.set(apps[0])
        self.research_app_dropdown.pack(side="left", padx=5)

        ttk.Label(ref_frame, text="Category:").pack(side="left", padx=5)
        self.research_type_var = tk.StringVar()
        # Updated note types with extra categories for fix status:
        note_types = [
            "Open Issue",
            "Issue Resolved (Manual)",
            "Issue Resolved (LLM)",
            "Required Further Input",
            "Wrong Files Generated",
            "Other"
        ]
        self.research_type_dropdown = ttk.Combobox(ref_frame, textvariable=self.research_type_var,
                                                   values=note_types, state="readonly", width=25)
        self.research_type_var.set(note_types[0])
        self.research_type_dropdown.pack(side="left", padx=5)

        # Research notes table
        table_frame = ttk.Frame(self.research_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        columns = ("id", "timestamp", "model", "app", "note_type", "summary")
        self.research_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.research_table.heading("id", text="ID")
        self.research_table.heading("timestamp", text="Timestamp")
        self.research_table.heading("model", text="Model")
        self.research_table.heading("app", text="App")
        # Change header from "Type" to "Category"
        self.research_table.heading("note_type", text="Category")
        self.research_table.heading("summary", text="Summary")
        self.research_table.column("id", width=50, anchor="center")
        self.research_table.column("timestamp", width=150)
        self.research_table.column("model", width=100)
        self.research_table.column("app", width=100)
        self.research_table.column("note_type", width=150)
        self.research_table.column("summary", width=400)
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.research_table.yview)
        self.research_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.research_table.pack(fill="both", expand=True)
        self.research_table.bind("<<TreeviewSelect>>", self._on_research_note_select)

        # Text area for note details
        self.research_note_text = tk.Text(self.research_tab, height=10, wrap="word")
        self.research_note_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Buttons for note actions
        btn_frame = ttk.Frame(self.research_tab)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="New Note", command=self._new_research_note).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save Note", command=self._save_research_note).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Delete Note", command=self._delete_research_note).pack(side="left", padx=5)

        self._refresh_research_notes()

    def _on_research_model_selected(self, event) -> None:
        # When a new model is selected, update the App dropdown.
        model = self.research_model_var.get()
        base_dir = Path('.') / model
        apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], key=_natural_sort_key)
        self.research_app_dropdown["values"] = apps
        if apps:
            self.research_app_var.set(apps[0])
        else:
            self.research_app_var.set("")

    def _refresh_research_notes(self) -> None:
        for row in self.research_table.get_children():
            self.research_table.delete(row)
        notes = self.database.get_research_notes(limit=100)
        self.research_notes_map = {}
        for note in notes:
            # note: (id, model, app, note_type, note, timestamp)
            note_id, model, app, note_type, note_text, timestamp = note
            self.research_notes_map[note_id] = {
                "model": model,
                "app": app,
                "note_type": note_type,
                "note": note_text
            }
            summary = note_text.strip().replace("\n", " ")
            summary = summary if len(summary) <= 50 else summary[:47] + "..."
            self.research_table.insert("", tk.END, values=(note_id, timestamp, model, app, note_type, summary))

    def _on_research_note_select(self, event) -> None:
        selected = self.research_table.selection()
        if selected:
            note_id = self.research_table.item(selected[0])["values"][0]
            note_data = self.research_notes_map.get(note_id, {})
            self.research_note_text.delete("1.0", tk.END)
            self.research_note_text.insert(tk.END, note_data.get("note", ""))
            # Also update the reference selectors
            self.research_model_var.set(note_data.get("model", ""))
            self._on_research_model_selected(None)  # Refresh apps for selected model
            self.research_app_var.set(note_data.get("app", ""))
            self.research_type_var.set(note_data.get("note_type", ""))

    def _new_research_note(self) -> None:
        self.research_table.selection_remove(self.research_table.selection())
        self.research_note_text.delete("1.0", tk.END)
        # Optionally, reset the reference selectors to default values
        models = [model.name for model in AI_MODELS]  # Use model list from app.py
        if models:
            self.research_model_var.set(models[0])
            self._on_research_model_selected(None)
        # Set default category to "Open Issue"
        self.research_type_var.set("Open Issue")

    def _save_research_note(self) -> None:
        note_text = self.research_note_text.get("1.0", tk.END).strip()
        if not note_text:
            self._log("Cannot save empty note", error=True)
            return
        model = self.research_model_var.get()
        app = self.research_app_var.get()
        note_type = self.research_type_var.get()
        selected = self.research_table.selection()
        if selected:
            note_id = self.research_table.item(selected[0])["values"][0]
            self.database.update_research_note(note_id, model, app, note_type, note_text)
            self._log(f"Updated research note {note_id}.")
        else:
            self.database.insert_research_note(model, app, note_type, note_text)
            self._log("Inserted new research note.")
        self._refresh_research_notes()

    def _delete_research_note(self) -> None:
        selected = self.research_table.selection()
        if not selected:
            self._log("No research note selected.", error=True)
            return
        note_id = self.research_table.item(selected[0])["values"][0]
        if messagebox.askyesno("Confirm Delete", "Delete selected research note?"):
            self.database.delete_research_note_by_id(note_id)
            self._log(f"Deleted research note {note_id}.")
            self._refresh_research_notes()
            self.research_note_text.delete("1.0", tk.END)

    # -------------------------------------------------------------------------
    # TAB 7: Progress Log
    # -------------------------------------------------------------------------
    def _create_progress_log_tab(self) -> None:
        self.progress_log_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.progress_log_tab, text="Progress Logs")

        top_frame = ttk.Frame(self.progress_log_tab)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.progress_search_var = tk.StringVar()
        entry = tk.Entry(top_frame, textvariable=self.progress_search_var)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda event: self._refresh_progress_logs())
        ttk.Button(top_frame, text="Refresh", command=self._refresh_progress_logs).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Clear", command=self._clear_progress_logs).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self._export_progress_logs).pack(side="left", padx=5)

        self.pause_btn = ttk.Button(top_frame, text="Pause", command=self._toggle_auto_refresh)
        self.pause_btn.pack(side="left", padx=5)

        columns = ("timestamp", "task", "progress", "message")
        self.progress_table = ttk.Treeview(self.progress_log_tab, columns=columns, show="headings")
        self.progress_table.heading("timestamp", text="Timestamp")
        self.progress_table.heading("task", text="Task")
        self.progress_table.heading("progress", text="Progress")
        self.progress_table.heading("message", text="Message")
        self.progress_table.column("timestamp", width=150)
        self.progress_table.column("task", width=150)
        self.progress_table.column("progress", width=80, anchor="center")
        self.progress_table.column("message", width=400)
        vsb = ttk.Scrollbar(self.progress_log_tab, orient="vertical", command=self.progress_table.yview)
        self.progress_table.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.progress_table.pack(fill="both", expand=True, padx=10, pady=5)

        self._auto_refresh_progress_logs()

    def _toggle_auto_refresh(self) -> None:
        self.pause_refresh = not self.pause_refresh
        self.pause_btn.config(text="Resume" if self.pause_refresh else "Pause")

    def _auto_refresh_progress_logs(self) -> None:
        if not self.pause_refresh:
            self._refresh_progress_logs()
        self.after(5000, self._auto_refresh_progress_logs)

    def _refresh_progress_logs(self) -> None:
        filter_text = self.progress_search_var.get().lower()
        for row in self.progress_table.get_children():
            self.progress_table.delete(row)
        logs = self.database.get_recent_logs(limit=100)
        for entry in logs:
            timestamp = entry[4]
            task = entry[1]
            progress = entry[2]
            message = entry[3]
            if filter_text and (filter_text not in task.lower() and filter_text not in message.lower()):
                continue
            self.progress_table.insert("", tk.END, values=(timestamp, task, f"{progress}%", message))

    def _clear_progress_logs(self) -> None:
        if messagebox.askyesno("Confirm", "Clear all progress logs?"):
            self.database.clear_logs()
            self._refresh_progress_logs()
            self._log("Progress logs cleared.")

    def _export_progress_logs(self) -> None:
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export progress logs to CSV"
        )
        if not export_path:
            return
        logs = self.database.get_recent_logs(limit=1000)
        try:
            with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Task", "Progress", "Message"])
                for entry in logs:
                    writer.writerow([entry[4], entry[1], f"{entry[2]}%", entry[3]])
            self._log(f"Progress logs exported to {export_path}")
        except Exception as e:
            self._log(f"Export failed: {e}", error=True)

    # -------------------------------------------------------------------------
    # LOG PANEL
    # -------------------------------------------------------------------------
    def _create_log_panel(self) -> None:
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x", side="bottom")
        ttk.Label(log_frame, text="Log:").pack(anchor="w", padx=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=5)

    # -------------------------------------------------------------------------
    # Utility / Logging
    # -------------------------------------------------------------------------
    def _log(self, message: str, error: bool = False) -> None:
        timestamp = time.strftime("%H:%M:%S")
        level = "ERROR" if error else "INFO"
        entry = f"[{timestamp}] {level}: {message}\n"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, entry)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

        if error:
            logger.error(message)
        else:
            logger.info(message)

    def _set_progress_bar(self, bar: ttk.Progressbar, value: int) -> None:
        bar["value"] = value
        self.update_idletasks()

    def _run_in_thread(self, func):
        def wrapper(*args, **kwargs):
            threading.Thread(target=self._safe_run, args=(func, *args), kwargs=kwargs, daemon=True).start()
        return wrapper

    def _safe_run(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            self._log(f"Error in {func.__name__}: {e}", error=True)
            messagebox.showerror("Error", str(e))

# =============================================================================
# GUI Logging Handler
# =============================================================================
class GuiLogHandler(logging.Handler):
    def __init__(self, app: AssistantApp) -> None:
        super().__init__()
        self.app = app

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.app.log_text.config(state="normal")
        self.app.log_text.insert(tk.END, msg + "\n")
        self.app.log_text.see(tk.END)
        self.app.log_text.config(state="disabled")

# Missing imports that were implied but not explicitly included in the initial code
from dataclasses import dataclass

# =============================================================================
# Main Entry
# =============================================================================
if __name__ == "__main__":
    app = AssistantApp()
    app.mainloop()