#!/usr/bin/env python3
import csv
import json
import logging
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime
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
    # Updated allowed_models to use the new full model names
    "allowed_models": {
        "Anthropic_Claude_3.7_Sonnet", "OpenAI_GPT-4.1", "Mistral_Devstral_Small",
        "Google_Gemma_3n_4B", "Meta-Llama_Llama_3.3_8B_Instruct",
        "NousResearch_DeepHermes_3_Mistral_24B_Preview", "Microsoft_Phi-4_Reasoning_Plus",
        "Qwen_Qwen3_30B_A3B", "OpenAI_Codex_Mini", "x-AI_Grok-3_Beta",
        "Inception_Mercury-Coder_Small-Beta", "Google_Gemini-2.5_Flash-Preview-05-20",
        "Meta-Llama_Llama-4_Maverick", "Qwen_Qwen3_235B_A22B", "Qwen_Qwen3_32B",
        "Meta-Llama_Llama-4_Scout", "DeepSeek_DeepSeek-Chat-V3-0324"
    },
    "db_path": "assistant.db",
    "log_file": "bot_prompts.log",
    "window_title": "AI Code Generation & Prompt Capture Assistant",
    "window_size": "1200x900"
}

# =============================================================================
# Model Configuration
# =============================================================================
@dataclass
class AIModel:
    name: str
    color: str

# Updated AI_MODELS list
AI_MODELS: List[AIModel] = [
    AIModel("Anthropic_Claude_3.7_Sonnet", "#7b2bf9"),
    AIModel("OpenAI_GPT-4.1", "#10a37f"),
    AIModel("Mistral_Devstral_Small", "#9333ea"),
    AIModel("Google_Gemma_3n_4B", "#87CEEB"),
    AIModel("Meta-Llama_Llama_3.3_8B_Instruct", "#f97316"),
    AIModel("NousResearch_DeepHermes_3_Mistral_24B_Preview", "#A020F0"),
    AIModel("Microsoft_Phi-4_Reasoning_Plus", "#0078D4"),
    AIModel("Qwen_Qwen3_30B_A3B", "#fa541c"),
    AIModel("OpenAI_Codex_Mini", "#43A047"),
    AIModel("x-AI_Grok-3_Beta", "#ff4d4f"),
    AIModel("Inception_Mercury-Coder_Small-Beta", "#FFD700"),
    AIModel("Google_Gemini-2.5_Flash-Preview-05-20", "#1a73e8"),
    AIModel("Meta-Llama_Llama-4_Maverick", "#f97316"),
    AIModel("Qwen_Qwen3_235B_A22B", "#fa541c"),
    AIModel("Qwen_Qwen3_32B", "#fa541c"),
    AIModel("Meta-Llama_Llama-4_Scout", "#f97316"),
    AIModel("DeepSeek_DeepSeek-Chat-V3-0324", "#ff5555")
]

# =============================================================================
# Utility Functions
# =============================================================================
def _natural_sort_key(s: str):
    """Split string into list of ints and lower-case text for natural sorting"""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

try:
    from natsort import natsorted
except ImportError:
    def natsorted(seq):
        return sorted(seq, key=_natural_sort_key)

# Helper function to get model index
def get_model_index(model_name: str) -> int:
    return next((i for i, m in enumerate(AI_MODELS) if m.name == model_name), 0)

# =============================================================================
# Port Management
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

# =============================================================================
# Logging Setup
# =============================================================================
logger = logging.getLogger("CodeGenAssistant")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(APP_CONFIG["log_file"])
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# =============================================================================
# Database Client
# =============================================================================
class DatabaseClient:
    """Handles all database interactions"""
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()
        self._create_model_app_table()
        self._create_research_table()
        self._create_web_prompts_table()
        logger.info(f"Connected to database: {db_path}")

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
    
    def _create_web_prompts_table(self) -> None:
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS web_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model TEXT NOT NULL,
                    app TEXT,
                    prompt_text TEXT NOT NULL,
                    response_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            ''')
        logger.info("Web prompts table verified/created")

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
            
    # -------------------------
    # Web Prompts
    # -------------------------
    def save_prompt(self, model: str, app: str, prompt_text: str, response_text: str = "") -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO web_prompts (model, app, prompt_text, response_text) VALUES (?, ?, ?, ?)",
                (model, app, prompt_text, response_text)
            )
        logger.info(f"Saved new prompt for {model}/{app}")

    def get_prompts(self, limit: int = 100):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, model, app, prompt_text, response_text, timestamp FROM web_prompts ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()

    def update_prompt(self, prompt_id: int, model: str, app: str, prompt_text: str, response_text: str) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE web_prompts SET model = ?, app = ?, prompt_text = ?, response_text = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?",
                (model, app, prompt_text, response_text, prompt_id)
            )
        logger.info(f"Updated prompt {prompt_id}")

    def delete_prompt(self, prompt_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM web_prompts WHERE id = ?", (prompt_id,))
        logger.info(f"Deleted prompt {prompt_id}")

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# =============================================================================
# Main GUI Application
# =============================================================================
class AssistantApp(tk.Tk):
    """Main application class containing all UI and logic."""
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_CONFIG["window_title"])
        self.geometry(APP_CONFIG["window_size"])
        self.configure(bg="white")

        self.database = DatabaseClient(APP_CONFIG["db_path"])
        
        # Track current context
        self.current_section = "backend"  # Track which section we're in
        self.undo_stack = []
        self.max_undo_stack = 5

        self._setup_menu()
        self._setup_main_ui()
        self._setup_logging_handler()

    # -------------------------------------------------------------------------
    # MENU & MAIN UI SETUP
    # -------------------------------------------------------------------------
    def _setup_menu(self) -> None:
        menubar = tk.Menu(self)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New File", command=self._create_new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open File", command=self._load_file_dialog, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_current_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Copy Path", command=self._copy_current_path)
        file_menu.add_separator()
        file_menu.add_command(label="Undo Last Change", command=self._undo_last_action, accelerator="Ctrl+Z")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Copy", command=lambda: self.event_generate("<<Copy>>"), accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self._paste_to_editor, accelerator="Ctrl+V")
        edit_menu.add_command(label="Smart Paste", command=self._paste_and_save, accelerator="Ctrl+Shift+V")
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Copy Port Info", command=self._copy_summary_port_info, accelerator="Ctrl+P")
        tools_menu.add_command(label="Copy Workflow Command", command=self._copy_workflow_command)
        tools_menu.add_command(label="Sync App Status", command=self._run_in_thread(self._sync_app_status_with_folders))
        menubar.add_cascade(label="Tools", menu=tools_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo(
            "About", "AI Code Generation & Prompt Capture Assistant\nVersion 2.0"
        ))
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)
        
        # Add keyboard shortcuts
        self.bind("<Control-s>", lambda e: self._save_current_file())
        self.bind("<Control-o>", lambda e: self._load_file_dialog())
        self.bind("<Control-p>", lambda e: self._copy_summary_port_info())
        self.bind("<Control-n>", lambda e: self._create_new_file())
        self.bind("<Control-z>", lambda e: self._undo_last_action())

    def _setup_main_ui(self) -> None:
        # Create log panel first so logging works during initialization
        self._create_log_panel()
        
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(fill="both", expand=True)

        # Only keep the essential tabs
        self._create_summary_tab()           # Tab 0: Summary Dashboard
        self._create_model_app_tab()         # Tab 1: Model & App Status
        self._create_research_tab()          # Tab 2: Research Notes
        self._create_web_prompt_tab()        # Tab 3: Web Prompt Capture

    def _setup_logging_handler(self) -> None:
        gui_handler = GuiLogHandler(self)
        logger.addHandler(gui_handler)

    def _create_log_panel(self) -> None:
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x", side="bottom")
        ttk.Label(log_frame, text="Log:").pack(anchor="w", padx=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=3)

    # -------------------------------------------------------------------------
    # TAB 0: Summary Dashboard 
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
                                                values=models, state="readonly", width=30) # Increased width for longer names
        if models:
            self.summary_model_var.set(models[0])
        self.summary_model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.summary_model_dropdown.bind("<<ComboboxSelected>>", self._on_summary_model_selected)
        
        ttk.Label(model_frame, text="App:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.summary_app_var = tk.StringVar()
        # Populate apps based on selected model, now including "models" subdirectory
        base_dir = Path('.') / "models" / self.summary_model_var.get() 
        apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], 
                        key=_natural_sort_key) if base_dir.exists() else []
        
        self.summary_app_dropdown = ttk.Combobox(model_frame, textvariable=self.summary_app_var,
                                            values=apps, state="readonly", width=20)
        if apps:
            self.summary_app_var.set(apps[0])
        self.summary_app_dropdown.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.summary_app_dropdown.bind("<<ComboboxSelected>>", self._on_summary_app_selected)
        
        ttk.Button(model_frame, text="Refresh All", 
                command=self._refresh_summary_page).grid(row=0, column=4, padx=10, pady=2)
        
        # Split pane with left and right content
        paned_window = ttk.PanedWindow(self.summary_tab, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left panel - Contains template, files, and editor
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=3)
        
        # Template section
        template_frame = ttk.LabelFrame(left_frame, text="Template")
        template_frame.pack(fill="x", padx=5, pady=5)
        
        template_select_frame = ttk.Frame(template_frame)
        template_select_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(template_select_frame, text="Template:").pack(side="left")
        self.summary_template_var = tk.StringVar()
        presets = self._scan_template_presets()
        
        # Attempt to find app-specific template
        current_app = self.summary_app_var.get()
        default_template = None
        if current_app:
            app_number = re.search(r'\d+', current_app)
            if app_number:
                app_template_name = f"app_{app_number.group()}_login.md"
                if app_template_name in presets:
                    default_template = app_template_name
        
        self.summary_template_dropdown = ttk.Combobox(
            template_select_frame, textvariable=self.summary_template_var,
            values=presets, state="readonly", width=30
        )
        if default_template:
            self.summary_template_var.set(default_template)
        elif presets:
            self.summary_template_var.set(presets[0])
        self.summary_template_dropdown.pack(side="left", padx=5)
        
        # Combined load & copy button 
        ttk.Button(template_select_frame, text="Load & Copy", 
                command=self._load_and_copy_template).pack(side="left", padx=2)
        
        # Template preview
        self.summary_template_text = scrolledtext.ScrolledText(template_frame, wrap="word", height=6)
        self.summary_template_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # File selection section - UNIFIED VIEW
        files_frame = ttk.LabelFrame(left_frame, text="Project Files")
        files_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status message area
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_frame = ttk.Frame(files_frame)
        status_frame.pack(fill="x", padx=5, pady=(0, 5))
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(side="left")
        
        # Create file sections with direct buttons
        file_browser_frame = ttk.Frame(files_frame)
        file_browser_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Backend Files section
        backend_section = ttk.LabelFrame(file_browser_frame, text="Backend Files")
        backend_section.pack(fill="x", padx=5, pady=5)
        
        backend_btn_frame = ttk.Frame(backend_section)
        backend_btn_frame.pack(fill="x", padx=5, pady=5)
        
        backend_files = [
            ("app.py", "backend"), 
            ("requirements.txt", "backend"),
            ("Dockerfile", "backend"),
            ("data.py", "backend"),
            ("utils.py", "backend")
        ]
        
        for i, (filename, section) in enumerate(backend_files):
            btn = self._create_smart_button(backend_btn_frame, filename, section)
            btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # Frontend Files section
        frontend_section = ttk.LabelFrame(file_browser_frame, text="Frontend Files")
        frontend_section.pack(fill="x", padx=5, pady=5)
        
        frontend_btn_frame = ttk.Frame(frontend_section)
        frontend_btn_frame.pack(fill="x", padx=5, pady=5)
        
        frontend_files = [
            ("App.jsx", "frontend"), 
            ("App.css", "frontend"),
            ("index.html", "frontend"),
            ("package.json", "frontend"),
            ("vite.config.js", "frontend"),
            ("Dockerfile", "frontend")
        ]
        
        for i, (filename, section) in enumerate(frontend_files):
            btn = self._create_smart_button(frontend_btn_frame, filename, section)
            btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")
        
        # Docker Files section
        docker_section = ttk.LabelFrame(file_browser_frame, text="Docker Files")
        docker_section.pack(fill="x", padx=5, pady=5)
        
        docker_btn_frame = ttk.Frame(docker_section)
        docker_btn_frame.pack(fill="x", padx=5, pady=5)
        
        # Just docker-compose.yml
        btn = self._create_smart_button(docker_btn_frame, "docker-compose.yml", "docker")
        btn.pack(side="left", padx=2, pady=2)
        
        # Quick Edit panel with shortcuts
        edit_frame = ttk.LabelFrame(left_frame, text="Quick Edit")
        edit_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        edit_toolbar = ttk.Frame(edit_frame)
        edit_toolbar.pack(fill="x", padx=5, pady=5)
        
        # Current file label
        self.current_file_var = tk.StringVar()
        self.current_file_var.set("No file selected")
        ttk.Label(edit_toolbar, textvariable=self.current_file_var, font=("", 9, "bold")).pack(side="left", padx=5)
        
        # Quick action buttons
        ttk.Button(edit_toolbar, text="New File", 
                command=self._create_new_file).pack(side="right", padx=2)
        ttk.Button(edit_toolbar, text="Paste & Save", 
                command=self._paste_and_save).pack(side="right", padx=2)
        ttk.Button(edit_toolbar, text="Save", 
                command=self._save_current_file).pack(side="right", padx=2)
        
        # Code editor
        self.summary_code_editor = scrolledtext.ScrolledText(edit_frame, wrap="none", height=15)
        self.summary_code_editor.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add keyboard shortcuts to editor
        self.summary_code_editor.bind("<Control-s>", lambda e: self._save_current_file())
        self.summary_code_editor.bind("<Control-n>", lambda e: self._create_new_file())
        
        # Right panel - Info & Actions
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)
        
        # Port information
        port_frame = ttk.LabelFrame(right_frame, text="Port Information")
        port_frame.pack(fill="x", padx=5, pady=5)
        
        port_content = ttk.Frame(port_frame)
        port_content.pack(fill="x", padx=5, pady=5)
        
        # Port info as label pairs rather than treeview
        self.port_labels = {}
        port_items = ["Model", "App", "Backend Port", "Frontend Port"]
        
        for i, item in enumerate(port_items):
            ttk.Label(port_content, text=f"{item}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.port_labels[item] = ttk.Label(port_content, text="")
            self.port_labels[item].grid(row=i, column=1, sticky="w", padx=5, pady=2)
        
        # Copy-ready format
        ttk.Label(port_content, text="Format:").grid(row=len(port_items), column=0, sticky="w", padx=5, pady=2)
        self.port_format_var = tk.StringVar()
        format_entry = ttk.Entry(port_content, textvariable=self.port_format_var, width=20)
        format_entry.grid(row=len(port_items), column=1, sticky="ew", padx=5, pady=2)
        
        ttk.Button(port_content, text="Copy", 
                command=self._copy_summary_port_info).grid(row=len(port_items)+1, column=0, columnspan=2, padx=5, pady=5, sticky="e")
        
        # App Status Section
        status_frame = ttk.LabelFrame(right_frame, text="App Generation Status")
        status_frame.pack(fill="x", padx=5, pady=5)
        
        # App status table
        self.summary_app_status = ttk.Treeview(status_frame, 
                                 columns=("app", "generated", "comment"), 
                                 show="headings", 
                                 height=5)
        self.summary_app_status.heading("app", text="App")
        self.summary_app_status.heading("generated", text="Generated")
        self.summary_app_status.heading("comment", text="Comment")
        self.summary_app_status.column("app", width=100)
        self.summary_app_status.column("generated", width=80, anchor="center")
        self.summary_app_status.column("comment", width=170)
        self.summary_app_status.pack(fill="x", padx=5, pady=5)
        self.summary_app_status.bind("<Double-1>", self._on_app_status_double_click)
        self.summary_app_status.bind("<Button-3>", self._show_app_status_context_menu)
        
        status_btn_frame = ttk.Frame(status_frame)
        status_btn_frame.pack(fill="x", padx=5, pady=2)
        ttk.Button(status_btn_frame, text="Sync Status", 
                command=self._run_in_thread(self._sync_app_status_with_folders)).pack(side="left", padx=5)
        
        # Research notes preview
        notes_frame = ttk.LabelFrame(right_frame, text="Research Notes")
        notes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.summary_notes_text = scrolledtext.ScrolledText(notes_frame, wrap="word", height=5)
        self.summary_notes_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        notes_btn_frame = ttk.Frame(notes_frame)
        notes_btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(notes_btn_frame, text="Add Note", 
                command=self._add_summary_research_note).pack(side="left", padx=5)
        ttk.Button(notes_btn_frame, text="View All", 
                command=lambda: self.main_notebook.select(2)).pack(side="left", padx=5)
        
        # Quick action buttons
        action_frame = ttk.LabelFrame(self.summary_tab, text="Actions")
        action_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(action_frame, text="Copy Workflow Command", 
                command=self._copy_workflow_command).pack(side="left", padx=5, pady=5)
        ttk.Button(action_frame, text="Web Prompts", 
                command=lambda: self.main_notebook.select(3)).pack(side="left", padx=5, pady=5)
        
        # Initialize the summary page data
        self._refresh_summary_page()

    def _create_smart_button(self, parent, filename, section):
        """Create a button with right-click menu for smart file operations"""
        btn = ttk.Button(
            parent, 
            text=filename,
            command=lambda: self._load_file_to_editor(filename, section)
        )
        
        # Create context menu
        menu = tk.Menu(btn, tearoff=0)
        menu.add_command(label=f"Open {filename}", 
                       command=lambda: self._load_file_to_editor(filename, section))
        menu.add_command(label=f"Paste to {filename}", 
                       command=lambda: self._paste_to_file(filename, section))
        menu.add_command(label="Copy Path",
                       command=lambda: self._copy_file_path(filename, section))
        
        # Bind right-click to show context menu
        btn.bind("<Button-3>", lambda e, m=menu: m.post(e.x_root, e.y_root))
        
        return btn

    def _on_summary_model_selected(self, event=None) -> None:
        """Update app dropdowns when a model is selected"""
        model = self.summary_model_var.get()
        # Path updated to include "models" subdirectory
        base_dir = Path('.') / "models" / model 
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
        
        # Refresh with new model/app
        self._refresh_summary_page()

    def _on_summary_app_selected(self, event=None) -> None:
        """When app is selected, update displays and try to find matching template"""
        # Get the newly selected app
        current_app = self.summary_app_var.get()
        if not current_app:
            return
            
        # Cancel any pending status message updates
        for after_id in self.after_ids if hasattr(self, 'after_ids') else []:
            self.after_cancel(after_id)
        
        # Initialize after_ids list if not exists
        if not hasattr(self, 'after_ids'):
            self.after_ids = []
        
        # Update UI elements
        self._update_port_info()
        self._update_app_status_display()
        self._update_summary_notes()
        
        # Try to find app-specific template
        self._log(f"Looking for template for app: {current_app}")
        
        try:
            app_number = re.search(r'(\d+)', current_app)
            if app_number:
                app_num_str = app_number.group(1)
                # Get all available templates
                presets = self._scan_template_presets()
                self._log(f"Available presets: {presets}")
                
                # Look for any template matching this app number
                matching_template = None
                prefix = f"app_{app_num_str}_"
                
                for preset in presets:
                    if preset.startswith(prefix):
                        matching_template = preset
                        break
                
                if matching_template:
                    self._log(f"Found matching template: {matching_template}")
                    self.summary_template_var.set(matching_template)
                    # Load the template automatically
                    self._load_and_copy_template()
                    # Flash status message with proper cleanup
                    self.status_var.set(f"✓ Loaded template for {current_app}")
                    
                    # Schedule status reset with proper cleanup
                    after_id = self.after(1500, lambda: self.status_var.set("Ready"))
                    self.after_ids.append(after_id)
                else:
                    self._log(f"No matching template found for {current_app}")
        except Exception as e:
            self._log(f"Error matching template for {current_app}: {e}", error=True)

    def _refresh_summary_page(self) -> None:
        """Refresh all data on the summary page"""
        self._update_port_info()
        self._update_app_status_display()
        self._update_summary_notes()
        
        # If a template is selected, load it
        if self.summary_template_var.get():
            self._load_and_copy_template()

    # -------------------------------------------------------------------------
    # File Management Methods
    # -------------------------------------------------------------------------
    def _get_file_path(self, filename, section=None) -> Optional[Path]:
        """Get the full path for a file based on current context"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            return None
            
        section = section or self.current_section
        
        # Base path now includes "models" subdirectory
        base_model_app_path = Path('.') / "models" / model / app
            
        if section == "backend":
            if filename in ["app.py", "requirements.txt", "data.py", "utils.py", "Dockerfile"]:
                return base_model_app_path / 'backend' / filename
        elif section == "frontend":
            if filename in ["App.jsx", "App.css", "index.html"]:
                return base_model_app_path / 'frontend' / 'src' / filename
            elif filename in ["package.json", "vite.config.js", "Dockerfile"]:
                return base_model_app_path / 'frontend' / filename
        elif section == "docker":
            if filename == "docker-compose.yml":
                return base_model_app_path / filename
                
        # If path not determined by section rules (fallback logic)
        if filename == "app.py":
            return base_model_app_path / 'backend' / filename
        elif filename in ["App.jsx", "App.css", "index.html"]:
            return base_model_app_path / 'frontend' / 'src' / filename
        elif filename in ["package.json", "vite.config.js"]:
            return base_model_app_path / 'frontend' / filename
        elif filename == "docker-compose.yml":
            return base_model_app_path / filename
        elif filename == "Dockerfile" and section == "backend": # Specific Dockerfile for backend
            return base_model_app_path / 'backend' / filename
        elif filename == "Dockerfile": # Default to frontend Dockerfile if section not backend
            return base_model_app_path / 'frontend' / filename
            
        # If nothing matched
        self._log(f"Could not determine path for filename: {filename} in section: {section}", error=True)
        return None

    def _load_file_to_editor(self, filename, section=None) -> None:
        """Load a file into the editor"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
        
        # Track current section for context
        if section:
            self.current_section = section
        
        # Get proper file path
        if isinstance(filename, Path):
            full_path = filename
        else:
            full_path = self._get_file_path(filename, section)
            
        if not full_path:
            self.status_var.set(f"Could not determine path for {filename}")
            self._log(f"Path resolution failed for {filename} in section {section or self.current_section}", error=True)
            return
        
        try:
            if not full_path.exists():
                if messagebox.askyesno("File Not Found", 
                                     f"{full_path} does not exist. Create it?"):
                    # Create the file and parent directories
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.touch()
                    self.status_var.set(f"Created new file: {full_path}")
                else:
                    return
            
            # Load the file content
            content = full_path.read_text(encoding="utf-8") if full_path.exists() else ""
            
            # Update the editor
            self.summary_code_editor.delete("1.0", tk.END)
            self.summary_code_editor.insert(tk.END, content)
            
            # Update current file
            self.current_file_path = full_path
            self.current_file_var.set(f"Editing: {full_path}")
            
            # Set focus to editor
            self.summary_code_editor.focus_set()
            
            self.status_var.set(f"Loaded {full_path}")
        except Exception as e:
            self.status_var.set(f"Error loading file: {e}")
            self._log(f"Error loading file {full_path}: {e}", error=True)

    def _create_new_file(self) -> None:
        """Create a new file"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
            
        # Ask user for file name and path
        filename_input = simpledialog.askstring("New File", 
                                        "Enter file name (e.g., new_utils.py, components/Header.jsx):")
        if not filename_input:
            return
        
        # Determine section based on user input or file extension
        # This logic might need refinement if users provide full paths vs just filenames
        filename = Path(filename_input).name # Get the actual filename
        relative_path_parts = Path(filename_input).parts[:-1] # Get directory parts if any

        section = self.current_section # Default to current section

        # Heuristic to determine section
        if "backend" in filename_input.lower() or filename.endswith(".py"):
            section = "backend"
        elif "frontend" in filename_input.lower() or filename.endswith((".jsx", ".css", ".html", ".js")):
            section = "frontend"
        elif filename.endswith(".yml") or filename == "docker-compose.yml":
            section = "docker"

        # Construct path, now including "models" subdirectory
        base_model_app_path = Path('.') / "models" / model / app
        
        # Construct full_path based on section and user input
        if section == "backend":
            full_path = base_model_app_path / 'backend' / Path(*relative_path_parts) / filename
        elif section == "frontend":
            # Check if it's a src file or root frontend file
            if "src" in filename_input.lower() or filename.endswith((".jsx", ".css")): # Common src files
                 full_path = base_model_app_path / 'frontend' / 'src' / Path(*relative_path_parts) / filename
            else: # Files like package.json, vite.config.js in frontend root
                 full_path = base_model_app_path / 'frontend' / Path(*relative_path_parts) / filename
        elif section == "docker": # docker-compose.yml is at app root
            full_path = base_model_app_path / filename 
        else: # Fallback or if section couldn't be determined well
            # Ask user for section if ambiguous
            chosen_section = simpledialog.askstring("Section", 
                                           "Enter section (backend, frontend, or docker):",
                                           initialvalue=section)
            if chosen_section and chosen_section.lower() in ["backend", "frontend", "docker"]:
                section = chosen_section.lower()
                # Re-construct path based on chosen section
                if section == "backend":
                    full_path = base_model_app_path / 'backend' / Path(*relative_path_parts) / filename
                elif section == "frontend":
                    if "src" in filename_input.lower() or filename.endswith((".jsx", ".css")):
                         full_path = base_model_app_path / 'frontend' / 'src' / Path(*relative_path_parts) / filename
                    else:
                         full_path = base_model_app_path / 'frontend' / Path(*relative_path_parts) / filename
                elif section == "docker":
                    full_path = base_model_app_path / filename
            else:
                self.status_var.set("Invalid section specified.")
                return

        if not full_path: # Should be set if logic above is correct
            self.status_var.set("Could not determine path for new file.")
            self._log(f"Failed to determine full_path for new file: {filename_input}", error=True)
            return
            
        try:
            # Create directories if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file if it doesn't exist
            if not full_path.exists():
                full_path.touch()
            
            # Load the file into editor
            self.current_file_path = full_path
            self.current_file_var.set(f"Editing: {full_path}")
            self.summary_code_editor.delete("1.0", tk.END)
            
            # Set focus to editor
            self.summary_code_editor.focus_set()
            
            self.status_var.set(f"Created and opened {full_path}")
            self._log(f"Created and opened new file: {full_path}")
        except Exception as e:
            self.status_var.set(f"Error creating file: {e}")
            self._log(f"Error creating file {full_path}: {e}", error=True)

    def _load_file_dialog(self) -> None:
        """Open a file dialog to select a file to load"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
        
        # Path updated to include "models" subdirectory
        base_dir = Path('.') / "models" / model / app
        file_path = filedialog.askopenfilename(
            initialdir=base_dir if base_dir.exists() else Path('.'), # Fallback if dir doesn't exist
            title="Select file to open",
            filetypes=(("All files", "*.*"), ("Python files", "*.py"), ("JavaScript files", "*.js"))
        )
        
        if file_path:
            self._load_file_to_editor(Path(file_path))

    def _paste_to_editor(self) -> None:
        """Paste clipboard content to editor"""
        try:
            content = self.clipboard_get()
            self.summary_code_editor.delete("1.0", tk.END)
            self.summary_code_editor.insert(tk.END, content)
            self.status_var.set("Pasted from clipboard")
            
            # Set focus to editor
            self.summary_code_editor.focus_set()
        except Exception as e:
            self.status_var.set(f"Clipboard error: {e}")
            self._log(f"Could not get clipboard content: {e}", error=True)

    def _save_current_file(self) -> None:
        """Save the current file"""
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            self.status_var.set("No file selected")
            return
        
        content = self.summary_code_editor.get("1.0", tk.END)
        
        try:
            # Save previous content for undo
            if self.current_file_path.exists():
                prev_content = self.current_file_path.read_text(encoding="utf-8")
                self.undo_stack.append({
                    'file': self.current_file_path,
                    'content': prev_content
                })
                # Limit stack size
                if len(self.undo_stack) > self.max_undo_stack:
                    self.undo_stack.pop(0)
            
            # Ensure parent directory exists
            self.current_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            self.current_file_path.write_text(content, encoding="utf-8")
            
            # Flash success message and icon
            self.status_var.set(f"✓ Saved: {self.current_file_path}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Saved {self.current_file_path}")
            
        except Exception as e:
            self.status_var.set(f"Error saving file: {e}")
            self._log(f"Error saving {self.current_file_path}: {e}", error=True)

    def _paste_and_save(self) -> None:
        """Paste from clipboard and immediately save the file"""
        try:
            # Check if we have a selected file
            if not hasattr(self, 'current_file_path') or not self.current_file_path:
                self.status_var.set("No file selected - select a file first")
                return
            
            # Get clipboard content
            content = self.clipboard_get()
            if not content.strip():
                self.status_var.set("Clipboard is empty")
                return
            
            # Replace port placeholders if needed
            content = self._replace_ports_in_content(content)
            
            # Update the editor
            self.summary_code_editor.delete("1.0", tk.END)
            self.summary_code_editor.insert(tk.END, content)
            
            # Save the content to file
            # Save previous content for undo
            if self.current_file_path.exists():
                prev_content = self.current_file_path.read_text(encoding="utf-8")
                self.undo_stack.append({
                    'file': self.current_file_path,
                    'content': prev_content
                })
                # Limit stack size
                if len(self.undo_stack) > self.max_undo_stack:
                    self.undo_stack.pop(0)
            
            # Ensure parent directory exists
            self.current_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            self.current_file_path.write_text(content, encoding="utf-8")
            
            # Visual feedback - flash message
            self.status_var.set(f"✓ Pasted and saved to: {self.current_file_path}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Pasted and saved to {self.current_file_path}")
            
        except Exception as e:
            self.status_var.set(f"Error pasting and saving: {e}")
            self._log(f"Error pasting and saving: {e}", error=True)

    def _paste_to_file(self, filename, section=None) -> None:
        """Paste clipboard content directly to a file without loading it first"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
            
        # Get file path
        full_path = self._get_file_path(filename, section)
        
        if not full_path:
            self.status_var.set(f"Could not determine path for {filename}")
            return
            
        try:
            # Get clipboard content
            content = self.clipboard_get()
            if not content.strip():
                self.status_var.set("Clipboard is empty")
                return
                
            # Replace port placeholders
            content = self._replace_ports_in_content(content)
            
            # Save previous content for undo if file exists
            if full_path.exists():
                prev_content = full_path.read_text(encoding="utf-8")
                self.undo_stack.append({
                    'file': full_path,
                    'content': prev_content
                })
                # Limit stack size
                if len(self.undo_stack) > self.max_undo_stack:
                    self.undo_stack.pop(0)
            
            # Ensure parent directory exists
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            full_path.write_text(content, encoding="utf-8")
            
            # Update editor and current file if it's the same
            if hasattr(self, 'current_file_path') and self.current_file_path == full_path:
                self.summary_code_editor.delete("1.0", tk.END)
                self.summary_code_editor.insert(tk.END, content)
            else: # If pasting to a different file, load it
                self._load_file_to_editor(full_path, section)

            # Visual feedback - flash status
            self.status_var.set(f"✓ Pasted directly to: {filename}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Pasted directly to {full_path}")
            
        except Exception as e:
            self.status_var.set(f"Error pasting to file: {e}")
            self._log(f"Error pasting to file: {e}", error=True)

    def _copy_file_path(self, filename, section=None) -> None:
        """Copy file path to clipboard"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
            
        # Get file path
        full_path = self._get_file_path(filename, section)
        
        if not full_path:
            self.status_var.set(f"Could not determine path for {filename}")
            return
            
        # Copy to clipboard
        self.clipboard_clear()
        self.clipboard_append(str(full_path.resolve())) # Resolve to absolute path
        
        # Visual feedback
        self.status_var.set(f"✓ Copied path: {full_path.resolve()}")
        self.after(1500, lambda: self.status_var.set("Ready"))

    def _copy_current_path(self) -> None:
        """Copy current file path to clipboard"""
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            self.status_var.set("No file selected")
            return
            
        self.clipboard_clear()
        self.clipboard_append(str(self.current_file_path.resolve())) # Resolve to absolute path
        
        # Visual feedback
        self.status_var.set(f"✓ Copied path: {self.current_file_path.resolve()}")
        self.after(1500, lambda: self.status_var.set("Ready"))

    def _undo_last_action(self) -> None:
        """Undo the last file modification"""
        if not self.undo_stack:
            self.status_var.set("Nothing to undo")
            return
        
        try:
            last_action = self.undo_stack.pop()
            file_path = last_action['file']
            content = last_action['content']
            
            # If we're editing this file, update the editor
            if hasattr(self, 'current_file_path') and self.current_file_path == file_path:
                self.summary_code_editor.delete("1.0", tk.END)
                self.summary_code_editor.insert(tk.END, content)
            
            # Write the content back
            file_path.write_text(content, encoding="utf-8")
            
            # Visual feedback
            self.status_var.set(f"✓ Undone: Changes to {file_path}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Undone changes to {file_path}")
            
        except Exception as e:
            self.status_var.set(f"Undo failed: {e}")
            self._log(f"Undo failed: {e}", error=True)

    # -------------------------------------------------------------------------
    # Template Management
    # -------------------------------------------------------------------------
    def _scan_template_presets(self) -> list:
        APP_CONFIG["presets_dir"].mkdir(exist_ok=True)
        presets = [f.name for f in APP_CONFIG["presets_dir"].glob(f"*{APP_CONFIG['default_template_ext']}")]
        return natsorted(presets)

    def _get_current_port_numbers(self) -> Dict[str, int]:
        """Get the port numbers for the current model/app selection"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            return {"frontend": 0, "backend": 0}
        
        # Extract app number from app name
        match = re.search(r'(\d+)', app)
        if not match:
            return {"frontend": 0, "backend": 0}
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        return PortManager.get_app_ports(model_idx, app_num)

    def _replace_ports_in_content(self, content: str) -> str:
        """Replace port placeholders in content with actual ports"""
        if "XXXX" not in content and "YYYY" not in content:
            return content
            
        ports = self._get_current_port_numbers()
        if ports["frontend"] == 0 or ports["backend"] == 0:
            # Log if ports are not found, but still return content to avoid breaking paste
            self._log(f"Could not get ports for {self.summary_model_var.get()}/{self.summary_app_var.get()} during placeholder replacement.", error=True)
            return content
            
        # Replace placeholders
        content = content.replace("XXXX", str(ports["frontend"]))
        content = content.replace("YYYY", str(ports["backend"]))
        
        return content

    # Also fix the _load_and_copy_template method to properly handle template not found
    def _load_and_copy_template(self) -> None:
        """Load template, replace port numbers, and copy to clipboard"""
        preset_name = self.summary_template_var.get()
        if not preset_name:
            return
            
        path = APP_CONFIG["presets_dir"] / preset_name
        if not path.exists():
            self.status_var.set(f"Template not found: {preset_name}")
            self._log(f"Template file not found: {preset_name}", error=True)
            return
            
        try:
            content = path.read_text(encoding="utf-8")
            
            # Replace port placeholders
            content = self._replace_ports_in_content(content)
            
            # Update template preview
            self.summary_template_text.delete("1.0", tk.END)
            self.summary_template_text.insert(tk.END, content)
            
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(content)
            
            # Visual feedback
            self.status_var.set(f"✓ Template copied to clipboard: {preset_name}")
            
            # Cancel any existing after callbacks to prevent conflicts
            if hasattr(self, 'after_ids'):
                for after_id in self.after_ids:
                    try:
                        self.after_cancel(after_id)
                    except:
                        pass # Ignore if already cancelled
                self.after_ids = []
                
            # Schedule status reset with tracking
            after_id = self.after(1500, lambda: self.status_var.set("Ready"))
            if not hasattr(self, 'after_ids'):
                self.after_ids = []
            self.after_ids.append(after_id)
            
            self._log(f"Loaded and copied template: {preset_name}")
        except Exception as e:
            self.status_var.set(f"Error loading template: {e}")
            self._log(f"Error loading template: {e}", error=True)

    # -------------------------------------------------------------------------
    # Port Information Management
    # -------------------------------------------------------------------------
    def _update_port_info(self) -> None:
        """Update the port information display"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.port_labels["Model"].config(text="")
            self.port_labels["App"].config(text="")
            self.port_labels["Backend Port"].config(text="")
            self.port_labels["Frontend Port"].config(text="")
            self.port_format_var.set("")
            return
        
        # Extract app number
        match = re.search(r'(\d+)', app)
        if not match:
            self.port_labels["Backend Port"].config(text="N/A")
            self.port_labels["Frontend Port"].config(text="N/A")
            self.port_format_var.set("")
            return
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        ports = PortManager.get_app_ports(model_idx, app_num)
        
        # Update label displays
        self.port_labels["Model"].config(text=model)
        self.port_labels["App"].config(text=app)
        self.port_labels["Backend Port"].config(text=str(ports["backend"]))
        self.port_labels["Frontend Port"].config(text=str(ports["frontend"]))
        
        # Update copy-ready format
        self.port_format_var.set(f"(frontend {ports['frontend']} and backend {ports['backend']})")

    def _copy_summary_port_info(self) -> None:
        """Copy port information to clipboard"""
        port_text = self.port_format_var.get()
        if not port_text:
            self.status_var.set("No port information available")
            return
            
        self.clipboard_clear()
        self.clipboard_append(port_text)
        
        # Visual feedback
        self.status_var.set(f"✓ Copied port info: {port_text}")
        self.after(1500, lambda: self.status_var.set("Ready"))
        
        self._log(f"Copied port info: {port_text}")

    def _copy_workflow_command(self) -> None:
        """Copy workflow command to clipboard"""
        model = self.summary_model_var.get()
        app = self.summary_app_var.get()
        
        if not model or not app:
            self.status_var.set("Model or App not selected")
            return
        
        match = re.search(r'(\d+)', app)
        if not match:
            self.status_var.set("Invalid app format")
            return
        
        app_num = int(match.group(1))
        model_idx = get_model_index(model)
        ports = PortManager.get_app_ports(model_idx, app_num)
        
        # Build workflow command, path updated to include "models" subdirectory
        command = (
            f"# {model} {app} Workflow\n"
            f"# Backend Port: {ports['backend']}\n"
            f"# Frontend Port: {ports['frontend']}\n"
            f"# Directory: ./models/{model}/{app}/\n\n"  # Updated path
            f"# Start application:\n"
            f"cd ./models/{model}/{app} && docker-compose up -d\n\n"  # Updated path
            f"# Stop application:\n"
            f"cd ./models/{model}/{app} && docker-compose down\n\n"  # Updated path
            f"# Access URLs:\n"
            f"# Backend: http://localhost:{ports['backend']}\n"
            f"# Frontend: http://localhost:{ports['frontend']}\n"
        )
        
        self.clipboard_clear()
        self.clipboard_append(command)
        
        # Visual feedback
        self.status_var.set("✓ Workflow command copied to clipboard")
        self.after(1500, lambda: self.status_var.set("Ready"))
        
        self._log("Copied workflow command")

    # -------------------------------------------------------------------------
    # App Status Management 
    # -------------------------------------------------------------------------
    def _update_app_status_display(self) -> None:
        """Update app generation status table"""
        # Clear existing items
        for row in self.summary_app_status.get_children():
            self.summary_app_status.delete(row)
        
        model = self.summary_model_var.get()
        if not model:
            return
        
        # Get model directory and scan for apps, path updated to include "models" subdirectory
        model_dir = Path('.') / "models" / model
        if not model_dir.is_dir():
            self._log(f"Model directory not found for status display: {model_dir}", error=True)
            return
        
        # Get app folders
        app_folders = natsorted(
            [d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")],
            key=lambda d: _natural_sort_key(d.name)
        )
        
        # Get existing status data from database
        current_app = self.summary_app_var.get()
        highlighted_item = None
        
        status_rows = self.database.get_all_model_app_status()
        comments_map = {}
        for row in status_rows:
            row_id, db_model, app_name_db, app_py, app_react, comment = row # Renamed 'app' to 'app_name_db'
            if db_model == model:
                comments_map[app_name_db] = (comment, bool(app_py or app_react))
        
        # Add each app to the status table
        for app_dir in app_folders:
            app_name = app_dir.name # This is the folder name, e.g., "app1"
            
            # Check app status
            app_py_exists = (app_dir / "backend" / "app.py").exists()
            app_jsx_exists = (app_dir / "frontend" / "src" / "App.jsx").exists()
            generated = app_py_exists or app_jsx_exists
            
            # Use existing comment if available
            comment, db_generated = comments_map.get(app_name, ("", False))
            
            # If DB says generated but files don't exist, use DB value (or consider re-syncing)
            # For now, let's prioritize file system check but allow DB to override if files are missing
            # This logic might need to be more robust based on desired behavior
            generated = generated or db_generated 
            
            # Insert into treeview
            status_text = "✅" if generated else "❌"
            item_id = self.summary_app_status.insert("", tk.END, values=(app_name, status_text, comment))
            
            # Highlight current app
            if app_name == current_app:
                highlighted_item = item_id
        
        # Select current app
        if highlighted_item:
            self.summary_app_status.selection_set(highlighted_item)
            self.summary_app_status.see(highlighted_item)

    def _on_app_status_double_click(self, event) -> None:
        """Handle double click on app status - select app or edit status"""
        item_id = self.summary_app_status.identify_row(event.y)
        column = self.summary_app_status.identify_column(event.x)
        if not item_id:
            return
        
        values = list(self.summary_app_status.item(item_id, "values"))
        app_name, status_text, comment = values
        model = self.summary_model_var.get()
        
        # Select this app in dropdown
        self.summary_app_var.set(app_name)
        self._on_summary_app_selected()
        
        if column == "#2":  # Generated column
            # Toggle generation status
            new_status = "❌" if status_text == "✅" else "✅"
            generated = (new_status == "✅")
            
            # Update database
            self._update_app_generation_status(model, app_name, generated, comment)
            
            # Update display
            self.summary_app_status.item(item_id, values=(app_name, new_status, comment))
        
        elif column == "#3":  # Comment column
            # Edit comment
            new_comment = simpledialog.askstring("Edit Comment", 
                                               f"Comment for {model}/{app_name}:",
                                               initialvalue=comment)
            if new_comment is not None:
                # Update database
                generated = (status_text == "✅")
                self._update_app_generation_status(model, app_name, generated, new_comment)
                
                # Update display
                self.summary_app_status.item(item_id, values=(app_name, status_text, new_comment))

    def _show_app_status_context_menu(self, event):
        """Show context menu for app status items"""
        item_id = self.summary_app_status.identify_row(event.y)
        if not item_id:
            return
            
        values = self.summary_app_status.item(item_id, "values")
        app_name = values[0]
        status_text = values[1]
        comment = values[2]
        model = self.summary_model_var.get()
        
        menu = tk.Menu(self.summary_app_status, tearoff=0)
        menu.add_command(label=f"Select {app_name}", 
                       command=lambda: self._select_app(app_name))
        menu.add_command(label=f"{'Mark Not Generated' if status_text == '✅' else 'Mark Generated'}", 
                       command=lambda: self._toggle_app_status(item_id, app_name, status_text, comment))
        menu.add_command(label="Edit Comment", 
                       command=lambda: self._edit_app_comment(item_id, app_name, status_text, comment))
        
        menu.post(event.x_root, event.y_root)

    def _select_app(self, app_name):
        """Select app in dropdown"""
        self.summary_app_var.set(app_name)
        self._on_summary_app_selected()

    def _toggle_app_status(self, item_id, app_name, status_text, comment):
        """Toggle generation status for app"""
        model = self.summary_model_var.get()
        new_status = "❌" if status_text == "✅" else "✅"
        generated = (new_status == "✅")
        
        # Update database
        self._update_app_generation_status(model, app_name, generated, comment)
        
        # Update display
        self.summary_app_status.item(item_id, values=(app_name, new_status, comment))

    def _edit_app_comment(self, item_id, app_name, status_text, comment):
        """Edit comment for app"""
        model = self.summary_model_var.get()
        new_comment = simpledialog.askstring("Edit Comment", 
                                           f"Comment for {model}/{app_name}:",
                                           initialvalue=comment)
        if new_comment is not None:
            # Update database
            generated = (status_text == "✅")
            self._update_app_generation_status(model, app_name, generated, new_comment)
            
            # Update display
            self.summary_app_status.item(item_id, values=(app_name, status_text, new_comment))

    def _update_app_generation_status(self, model, app, generated, comment) -> None:
        """Update app generation status in database"""
        # Find existing row for this model/app
        rows = self.database.get_all_model_app_status()
        row_id = None
        for row_data in rows: # renamed 'row' to 'row_data' to avoid conflict
            db_id, db_model, db_app, app_py, app_react, db_comment = row_data
            if db_model == model and db_app == app:
                row_id = db_id
                break
        
        # Update or insert status
        if row_id:
            self.database.update_model_app_status(row_id, model, app, generated, generated, comment)
        else:
            self.database.insert_model_app_status(model, app, generated, generated, comment)
        
        self._log(f"Updated generation status for {model}/{app}: {'Generated' if generated else 'Not Generated'}")

    def _sync_app_status_with_folders(self) -> None:
        """Sync app status with actual folder contents"""
        model = self.summary_model_var.get()
        if not model:
            self.status_var.set("No model selected")
            return
        
        self._log(f"Syncing app status for {model}...")
        
        # Get existing status rows
        rows = self.database.get_all_model_app_status()
        status_map = {}
        for row_data in rows: # renamed 'row' to 'row_data'
            row_id, db_model, app_name_db, app_py, app_react, comment = row_data
            if db_model == model:
                status_map[app_name_db] = {"id": row_id, "comment": comment}
        
        # Scan folders, path updated to include "models" subdirectory
        model_dir = Path('.') / "models" / model
        if not model_dir.is_dir():
            self._log(f"Model directory not found: {model_dir}", error=True)
            return
        
        app_dirs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")]
        
        # Update status for each app
        for app_dir in app_dirs:
            app_name = app_dir.name
            app_py_exists = (app_dir / "backend" / "app.py").exists()
            app_jsx_exists = (app_dir / "frontend" / "src" / "App.jsx").exists()
            
            if app_name in status_map:
                # Update existing record
                row_id = status_map[app_name]["id"]
                comment = status_map[app_name]["comment"]
                self.database.update_model_app_status(row_id, model, app_name, app_py_exists, app_jsx_exists, comment)
            else:
                # Insert new record
                self.database.insert_model_app_status(model, app_name, app_py_exists, app_jsx_exists, "")
        
        # Refresh display
        self._update_app_status_display()
        
        # Visual feedback
        self.status_var.set(f"✓ App status synced for {model}")
        self.after(1500, lambda: self.status_var.set("Ready"))
        
        self._log(f"App status sync complete for {model}")

    # -------------------------------------------------------------------------
    # Research Notes Management
    # -------------------------------------------------------------------------
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
        for note_data in notes: # Renamed 'note' to 'note_data'
            note_id, note_model, note_app, note_type, note_text, timestamp = note_data
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
            self.status_var.set("Model or App not selected")
            return
        
        # Switch to the research tab and set up for a new note
        self.main_notebook.select(2)  # Index of research tab
        self.research_model_var.set(model)
        self._on_research_model_selected(None)  # Update app dropdown
        self.research_app_var.set(app)
        self._new_research_note()

    # -------------------------------------------------------------------------
    # TAB 1: Model & App Status
    # -------------------------------------------------------------------------
    def _create_model_app_tab(self) -> None:
        self.model_app_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.model_app_tab, text="Model & App Status")

        self.model_app_sort_column = None
        self.model_app_sort_reverse = False
        self.model_app_data = []

        # Top controls
        top_frame = ttk.Frame(self.model_app_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Add model selector
        model_select_frame = ttk.Frame(top_frame) # Renamed 'model_frame' to avoid conflict
        model_select_frame.pack(side="left", padx=5)
        
        ttk.Label(model_select_frame, text="Filter Model:").pack(side="left")
        self.model_app_model_var = tk.StringVar()
        models = ["All"] + [model.name for model in AI_MODELS]
        self.model_app_model_dropdown = ttk.Combobox(model_select_frame, textvariable=self.model_app_model_var,
                                                  values=models, state="readonly", width=25) # Increased width
        self.model_app_model_var.set("All")
        self.model_app_model_dropdown.pack(side="left", padx=5)
        self.model_app_model_dropdown.bind("<<ComboboxSelected>>", lambda e: self._refresh_model_app_table())
        
        # Text filter
        filter_frame = ttk.Frame(top_frame)
        filter_frame.pack(side="left", padx=15)
        
        ttk.Label(filter_frame, text="Search:").pack(side="left")
        self.model_app_filter_var = tk.StringVar()
        entry = ttk.Entry(filter_frame, textvariable=self.model_app_filter_var, width=20)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda event: self._refresh_model_app_table())
        
        # Buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Sync All", 
                command=self._run_in_thread(self._sync_all_models)).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh", 
                command=self._refresh_model_app_table).pack(side="left", padx=5)

        # Status table
        columns = ("id", "model", "app", "app_py", "app_react", "comment")
        self.model_app_table = ttk.Treeview(self.model_app_tab, columns=columns, show="headings")
        self.model_app_table.heading("id", text="ID", command=lambda: self._sort_model_app_table("id"))
        self.model_app_table.heading("model", text="Model", command=lambda: self._sort_model_app_table("model"))
        self.model_app_table.heading("app", text="App", command=lambda: self._sort_model_app_table("app"))
        self.model_app_table.heading("app_py", text="app.py?", command=lambda: self._sort_model_app_table("app_py"))
        self.model_app_table.heading("app_react", text="App.jsx?", command=lambda: self._sort_model_app_table("app_react"))
        self.model_app_table.heading("comment", text="Comment", command=lambda: self._sort_model_app_table("comment"))

        self.model_app_table.column("id", width=50)
        self.model_app_table.column("model", width=200) # Increased width for longer model names
        self.model_app_table.column("app", width=100)
        self.model_app_table.column("app_py", width=80, anchor="center")
        self.model_app_table.column("app_react", width=100, anchor="center")
        self.model_app_table.column("comment", width=250)

        # Add scrollbar
        table_frame = ttk.Frame(self.model_app_tab)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.model_app_table.yview)
        self.model_app_table.configure(yscrollcommand=vsb.set)
        
        self.model_app_table.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Bind interactions
        self.model_app_table.bind("<Double-1>", self._on_model_app_table_double_click)
        self.model_app_table.bind("<Button-3>", self._show_model_app_context_menu)

        self._refresh_model_app_table()

    def _sync_all_models(self) -> None:
        """Sync app status for all models"""
        for model_obj in AI_MODELS: # Iterate through AI_MODEL objects
            model_name = model_obj.name
            # Path updated to include "models" subdirectory
            model_dir = Path('.') / "models" / model_name
            if model_dir.is_dir():
                self._log(f"Syncing {model_name}...")
                
                # Get existing status for this model
                rows = self.database.get_all_model_app_status()
                status_map = {}
                for row_data in rows: # Renamed 'row'
                    row_id, db_model, app_name_db, app_py, app_react, comment = row_data
                    if db_model == model_name:
                        status_map[app_name_db] = {"id": row_id, "comment": comment}
                
                # Scan app folders
                app_dirs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")]
                
                # Update status for each app
                for app_dir in app_dirs:
                    app_name = app_dir.name
                    app_py_exists = (app_dir / "backend" / "app.py").exists()
                    app_jsx_exists = (app_dir / "frontend" / "src" / "App.jsx").exists()
                    
                    if app_name in status_map:
                        # Update existing record
                        row_id = status_map[app_name]["id"]
                        comment = status_map[app_name]["comment"]
                        self.database.update_model_app_status(row_id, model_name, app_name, app_py_exists, app_jsx_exists, comment)
                    else:
                        # Insert new record
                        self.database.insert_model_app_status(model_name, app_name, app_py_exists, app_jsx_exists, "")
            else:
                self._log(f"Directory not found for model {model_name} at {model_dir}, skipping sync.", error=True)

        # Refresh display
        self._refresh_model_app_table()
        
        # Visual feedback
        self.status_var.set("✓ All models synced")
        self.after(1500, lambda: self.status_var.set("Ready"))
        
        self._log("All models synced successfully")

    def _refresh_model_app_table(self) -> None:
        """Refresh the model & app status table with filtering"""
        self.model_app_data = []
        rows = self.database.get_all_model_app_status()
        
        # Apply model filter first
        selected_model = self.model_app_model_var.get()
        
        for row_data in rows: # Renamed 'row'
            row_id, model_name_db, app_name_db, app_py, app_react, comment = row_data # Renamed variables
            
            # Skip if model doesn't match selected filter
            if selected_model != "All" and model_name_db != selected_model:
                continue
                
            self.model_app_data.append({
                "id": row_id,
                "model": model_name_db,
                "app": app_name_db,
                "app_py": "☑" if app_py else "☐",
                "app_react": "☑" if app_react else "☐",
                "comment": comment or ""
            })

        # Apply text filter
        filtered = self._apply_model_app_filter(self.model_app_data)
        
        # Apply sorting if set
        if self.model_app_sort_column:
            filtered = self._sort_model_app_data(filtered, self.model_app_sort_column, self.model_app_sort_reverse)
            
        # Update display
        self._populate_model_app_table(filtered)

    def _apply_model_app_filter(self, data):
        """Apply text filter to model/app data"""
        ft = self.model_app_filter_var.get().strip().lower()
        if not ft:
            return data
            
        return [
            row_data for row_data in data # Renamed 'row'
            if (ft in str(row_data["id"]).lower() or
                ft in row_data["model"].lower() or
                ft in row_data["app"].lower() or
                ft in row_data["comment"].lower())
        ]

    def _sort_model_app_table(self, col: str):
        """Sort the model/app table by column"""
        if self.model_app_sort_column == col:
            self.model_app_sort_reverse = not self.model_app_sort_reverse
        else:
            self.model_app_sort_column = col
            self.model_app_sort_reverse = False
            
        self._refresh_model_app_table()

    def _sort_model_app_data(self, data, col: str, reverse: bool):
        """Sort data by specified column"""
        def sort_key(row_data): # Renamed 'row'
            if col == "id":
                return int(row_data["id"])
            elif col in ("app_py", "app_react"):
                return 0 if row_data[col] == "☐" else 1
            else:
                return _natural_sort_key(str(row_data[col])) # Ensure string for natural sort key
                
        return sorted(data, key=sort_key, reverse=reverse)

    def _populate_model_app_table(self, data):
        """Populate the model/app table with data"""
        # Clear existing rows
        for item in self.model_app_table.get_children(): # Renamed 'row' to 'item'
            self.model_app_table.delete(item)
            
        # Insert new data
        for row_data in data: # Renamed 'row'
            self.model_app_table.insert("", tk.END, values=(
                row_data["id"],
                row_data["model"],
                row_data["app"],
                row_data["app_py"],
                row_data["app_react"],
                row_data["comment"]
            ))

    def _on_model_app_table_double_click(self, event) -> None:
        """Handle double-click on model/app table"""
        item_id = self.model_app_table.identify_row(event.y)
        col_id = self.model_app_table.identify_column(event.x)
        if not item_id:
            return

        values = list(self.model_app_table.item(item_id, "values"))
        row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment = values # Renamed variables

        # Select this app in the main interface
        self.summary_model_var.set(model_name_val)
        self._on_summary_model_selected(None)  # Update app dropdown
        self.summary_app_var.set(app_name_val)
        self._on_summary_app_selected()  # Load this app's files
        self.main_notebook.select(0)  # Go to summary tab

        # Handle column-specific actions
        if col_id == "#4":  # app.py column
            new_val = "☑" if app_py_disp == "☐" else "☐"
            values[3] = new_val
            self.database.update_model_app_status(
                row_id, model_name_val, app_name_val,
                (new_val == "☑"), (app_react_disp == "☑"), comment
            )
        elif col_id == "#5":  # App.jsx column
            new_val = "☑" if app_react_disp == "☐" else "☐"
            values[4] = new_val
            self.database.update_model_app_status(
                row_id, model_name_val, app_name_val,
                (app_py_disp == "☑"), (new_val == "☑"), comment
            )
        elif col_id == "#6":  # Comment column
            new_comment = simpledialog.askstring("Edit Comment", "Enter comment:", initialvalue=comment)
            if new_comment is not None:
                values[5] = new_comment
                self.database.update_model_app_status(
                    row_id, model_name_val, app_name_val,
                    (app_py_disp == "☑"), (app_react_disp == "☑"), new_comment
                )

        self.model_app_table.item(item_id, values=values)

    def _show_model_app_context_menu(self, event):
        """Show context menu for model/app table"""
        item_id = self.model_app_table.identify_row(event.y)
        if not item_id:
            return
            
        values = self.model_app_table.item(item_id, "values")
        row_id = values[0]
        model_name_val = values[1]  # Renamed 'model'
        app_name_val = values[2]    # Renamed 'app'
        app_py_disp = values[3]
        app_react_disp = values[4]
        comment = values[5]
        
        menu = tk.Menu(self.model_app_table, tearoff=0)
        menu.add_command(label=f"Load {model_name_val}/{app_name_val}", 
                        command=lambda: self._select_model_app(model_name_val, app_name_val))
        menu.add_separator()
        menu.add_command(label=f"Toggle app.py", 
                        command=lambda: self._toggle_app_py_status(item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment))
        menu.add_command(label=f"Toggle App.jsx", 
                        command=lambda: self._toggle_app_jsx_status(item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment))
        menu.add_separator()
        menu.add_command(label="Edit Comment", 
                        command=lambda: self._edit_model_app_comment(item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment))
        
        menu.post(event.x_root, event.y_root)

    def _select_model_app(self, model_name_val, app_name_val): # Renamed variables
        """Select model/app in main interface"""
        self.summary_model_var.set(model_name_val)
        self._on_summary_model_selected(None)
        self.summary_app_var.set(app_name_val)
        self._on_summary_app_selected()
        self.main_notebook.select(0)  # Go to summary tab

    def _toggle_app_py_status(self, item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment): # Renamed variables
        """Toggle app.py status"""
        new_val = "☑" if app_py_disp == "☐" else "☐"
        values = [row_id, model_name_val, app_name_val, new_val, app_react_disp, comment]
        
        self.database.update_model_app_status(
            row_id, model_name_val, app_name_val,
            (new_val == "☑"), (app_react_disp == "☑"), comment
        )
        
        self.model_app_table.item(item_id, values=values)

    def _toggle_app_jsx_status(self, item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment): # Renamed variables
        """Toggle App.jsx status"""
        new_val = "☑" if app_react_disp == "☐" else "☐"
        values = [row_id, model_name_val, app_name_val, app_py_disp, new_val, comment]
        
        self.database.update_model_app_status(
            row_id, model_name_val, app_name_val,
            (app_py_disp == "☑"), (new_val == "☑"), comment
        )
        
        self.model_app_table.item(item_id, values=values)

    def _edit_model_app_comment(self, item_id, row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, comment): # Renamed variables
        """Edit comment for model/app"""
        new_comment = simpledialog.askstring("Edit Comment", "Enter comment:", initialvalue=comment)
        if new_comment is not None:
            values = [row_id, model_name_val, app_name_val, app_py_disp, app_react_disp, new_comment]
            
            self.database.update_model_app_status(
                row_id, model_name_val, app_name_val,
                (app_py_disp == "☑"), (app_react_disp == "☑"), new_comment
            )
            
            self.model_app_table.item(item_id, values=values)

    # -------------------------------------------------------------------------
    # TAB 2: Research Notes
    # -------------------------------------------------------------------------
    def _create_research_tab(self) -> None:
        """Create research notes tab"""
        self.research_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.research_tab, text="Research Notes")

        # Top controls frame
        top_frame = ttk.Frame(self.research_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Model, App, and Category selectors
        selector_frame = ttk.Frame(top_frame)
        selector_frame.pack(side="left", fill="x", padx=5)
        
        ttk.Label(selector_frame, text="Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.research_model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]
        self.research_model_dropdown = ttk.Combobox(selector_frame, textvariable=self.research_model_var,
                                                    values=models, state="readonly", width=25) # Increased width
        if models:
            self.research_model_var.set(models[0])
        self.research_model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.research_model_dropdown.bind("<<ComboboxSelected>>", self._on_research_model_selected)

        ttk.Label(selector_frame, text="App:").grid(row=0, column=2, padx=5, pady=2, sticky="w")
        self.research_app_var = tk.StringVar()
        if self.research_model_var.get():
            # Path updated to include "models" subdirectory
            base_dir = Path('.') / "models" / self.research_model_var.get()
            apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], 
                           key=_natural_sort_key) if base_dir.exists() else []
        else:
            apps = []
        self.research_app_dropdown = ttk.Combobox(selector_frame, textvariable=self.research_app_var,
                                                  values=apps, state="readonly", width=15)
        if apps:
            self.research_app_var.set(apps[0])
        self.research_app_dropdown.grid(row=0, column=3, padx=5, pady=2, sticky="w")

        ttk.Label(selector_frame, text="Category:").grid(row=0, column=4, padx=5, pady=2, sticky="w")
        self.research_type_var = tk.StringVar()
        note_types = [
            "Open Issue",
            "Issue Resolved (Manual)",
            "Issue Resolved (LLM)",
            "Required Further Input",
            "Wrong Files Generated",
            "Other"
        ]
        self.research_type_dropdown = ttk.Combobox(selector_frame, textvariable=self.research_type_var,
                                                   values=note_types, state="readonly", width=20)
        self.research_type_var.set(note_types[0])
        self.research_type_dropdown.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        
        # Action buttons
        action_frame = ttk.Frame(top_frame)
        action_frame.pack(side="right", padx=5)
        
        ttk.Button(action_frame, text="New Note", 
                  command=self._new_research_note).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Save Note", 
                  command=self._save_research_note).pack(side="left", padx=5)
        ttk.Button(action_frame, text="Delete Note", 
                  command=self._delete_research_note).pack(side="left", padx=5)

        # Split view with notes list and editor
        paned_window = ttk.PanedWindow(self.research_tab, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Notes list
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=1)
        
        # Search filter
        research_filter_frame = ttk.Frame(list_frame) # Renamed 'filter_frame'
        research_filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(research_filter_frame, text="Search:").pack(side="left")
        self.research_filter_var = tk.StringVar()
        research_entry = ttk.Entry(research_filter_frame, textvariable=self.research_filter_var) # Renamed 'entry'
        research_entry.pack(side="left", fill="x", expand=True, padx=5)
        research_entry.bind("<KeyRelease>", lambda e: self._refresh_research_notes())
        
        # Notes list
        columns = ("id", "timestamp", "model", "app", "note_type", "summary")
        self.research_table = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.research_table.heading("id", text="ID")
        self.research_table.heading("timestamp", text="Date")
        self.research_table.heading("model", text="Model")
        self.research_table.heading("app", text="App")
        self.research_table.heading("note_type", text="Category")
        self.research_table.heading("summary", text="Summary")
        
        self.research_table.column("id", width=40, anchor="center")
        self.research_table.column("timestamp", width=120)
        self.research_table.column("model", width=150) # Increased width
        self.research_table.column("app", width=80)
        self.research_table.column("note_type", width=120)
        self.research_table.column("summary", width=200)
        
        # Add scrollbar
        notes_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.research_table.yview)
        self.research_table.configure(yscrollcommand=notes_scrollbar.set)
        
        notes_scrollbar.pack(side="right", fill="y")
        self.research_table.pack(fill="both", expand=True, padx=5)
        
        # Bind selection event
        self.research_table.bind("<<TreeviewSelect>>", self._on_research_note_select)
        self.research_table.bind("<Button-3>", self._show_research_context_menu)

        # Right side - Note editor
        editor_frame = ttk.Frame(paned_window)
        paned_window.add(editor_frame, weight=2)
        
        # Note editor with syntax highlighting or formatting
        self.research_note_text = scrolledtext.ScrolledText(editor_frame, wrap="word", height=15)
        self.research_note_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add keyboard shortcuts
        self.research_note_text.bind("<Control-s>", lambda e: self._save_research_note())
        
        # Initial load
        self._refresh_research_notes()

    def _on_research_model_selected(self, event) -> None:
        """Handle model selection in research tab"""
        model = self.research_model_var.get()
        # Path updated to include "models" subdirectory
        base_dir = Path('.') / "models" / model
        apps = []
        if base_dir.exists():
            apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], 
                        key=_natural_sort_key)
        else:
            self._log(f"Research tab: Directory not found for model {model} at {base_dir}", error=True)

        self.research_app_dropdown["values"] = apps
        if apps:
            self.research_app_var.set(apps[0])
        else:
            self.research_app_var.set("")

    def _refresh_research_notes(self) -> None:
        """Refresh research notes list with filtering"""
        # Clear existing items
        for item in self.research_table.get_children(): # Renamed 'row'
            self.research_table.delete(item)
        
        # Get all notes
        notes = self.database.get_research_notes(limit=100)
        self.research_notes_map = {}
        
        # Apply filter
        filter_text = self.research_filter_var.get().lower()
        
        for note_data in notes: # Renamed 'note'
            # Extract note data
            note_id, model_name_db, app_name_db, note_type, note_text, timestamp = note_data # Renamed variables
            
            # Skip if doesn't match filter
            if filter_text and not (
                filter_text in model_name_db.lower() or
                (app_name_db and filter_text in app_name_db.lower()) or # Check if app_name_db is not None
                filter_text in note_type.lower() or
                filter_text in note_text.lower()
            ):
                continue
            
            # Store note data for lookup
            self.research_notes_map[note_id] = {
                "model": model_name_db,
                "app": app_name_db,
                "note_type": note_type,
                "note": note_text
            }
            
            # Create summary preview
            summary = note_text.strip().replace("\n", " ")
            summary = summary if len(summary) <= 50 else summary[:47] + "..."
            
            # Insert into treeview
            self.research_table.insert("", tk.END, values=(
                note_id, timestamp, model_name_db, app_name_db or "", note_type, summary # Use app_name_db or ""
            ))

    def _on_research_note_select(self, event) -> None:
        """Handle selection of a research note"""
        selected = self.research_table.selection()
        if not selected:
            return
            
        # Get note ID from selected item
        note_id = self.research_table.item(selected[0])["values"][0]
        note_data = self.research_notes_map.get(note_id, {})
        
        # Update editor and selectors
        self.research_note_text.delete("1.0", tk.END)
        self.research_note_text.insert(tk.END, note_data.get("note", ""))
        
        # Update reference selectors
        self.research_model_var.set(note_data.get("model", ""))
        self._on_research_model_selected(None)  # Refresh apps for selected model
        self.research_app_var.set(note_data.get("app", ""))
        self.research_type_var.set(note_data.get("note_type", ""))

    def _show_research_context_menu(self, event):
        """Show context menu for research notes"""
        item_id = self.research_table.identify_row(event.y)
        if not item_id:
            return
            
        values = self.research_table.item(item_id, "values")
        note_id = values[0]
        
        menu = tk.Menu(self.research_table, tearoff=0)
        menu.add_command(label="Edit Note", 
                        command=lambda: self._select_research_note(item_id))
        menu.add_command(label="Delete Note", 
                        command=lambda: self._delete_research_note_by_id(note_id))
        menu.add_separator()
        
        # Add option to load the app
        note_data = self.research_notes_map.get(note_id, {})
        model_name_val = note_data.get("model", "") # Renamed 'model'
        app_name_val = note_data.get("app", "")     # Renamed 'app'
        
        if model_name_val and app_name_val:
            menu.add_command(label=f"Load {model_name_val}/{app_name_val}", 
                            command=lambda: self._select_model_app(model_name_val, app_name_val))
        
        menu.post(event.x_root, event.y_root)

    def _select_research_note(self, item_id):
        """Select a research note"""
        self.research_table.selection_set(item_id)
        self.research_table.focus(item_id)
        self.research_table.see(item_id)
        self._on_research_note_select(None)

    def _new_research_note(self) -> None:
        """Create a new research note"""
        # Clear selection
        self.research_table.selection_remove(self.research_table.selection())
        
        # Clear editor
        self.research_note_text.delete("1.0", tk.END)
        
        # Focus editor
        self.research_note_text.focus_set()

    def _save_research_note(self) -> None:
        """Save current research note"""
        note_text = self.research_note_text.get("1.0", tk.END).strip()
        if not note_text:
            self.status_var.set("Cannot save empty note")
            return
            
        # Get reference info
        model = self.research_model_var.get()
        app = self.research_app_var.get()
        note_type = self.research_type_var.get()
        
        # Check if updating existing note
        selected = self.research_table.selection()
        
        try:
            if selected:
                # Update existing note
                note_id = self.research_table.item(selected[0])["values"][0]
                self.database.update_research_note(note_id, model, app, note_type, note_text)
                self._log(f"Updated research note {note_id}")
                
                # Visual feedback
                self.status_var.set(f"✓ Updated note {note_id}")
            else:
                # Insert new note
                self.database.insert_research_note(model, app, note_type, note_text)
                self._log("Created new research note")
                
                # Visual feedback
                self.status_var.set("✓ Created new note")
            
            # Auto-clear feedback after delay
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            # Refresh notes list
            self._refresh_research_notes()
        except Exception as e:
            self.status_var.set(f"Error saving note: {e}")
            self._log(f"Error saving note: {e}", error=True)

    def _delete_research_note(self) -> None:
        """Delete the selected research note"""
        selected = self.research_table.selection()
        if not selected:
            self.status_var.set("No note selected")
            return
            
        note_id = self.research_table.item(selected[0])["values"][0]
        self._delete_research_note_by_id(note_id)

    def _delete_research_note_by_id(self, note_id) -> None:
        """Delete a research note by ID"""
        if not messagebox.askyesno("Confirm Delete", "Delete selected note?"):
            return
            
        try:
            self.database.delete_research_note_by_id(note_id)
            
            # Clear editor if the deleted note was selected
            selected_items = self.research_table.selection()
            if selected_items and self.research_table.item(selected_items[0])["values"][0] == note_id:
                self.research_note_text.delete("1.0", tk.END)

            # Refresh list
            self._refresh_research_notes()
            
            # Visual feedback
            self.status_var.set(f"✓ Deleted note {note_id}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Deleted research note {note_id}")
        except Exception as e:
            self.status_var.set(f"Error deleting note: {e}")
            self._log(f"Error deleting note: {e}", error=True)

    # -------------------------------------------------------------------------
    # TAB 3: Web Prompt Capture
    # -------------------------------------------------------------------------
    def _create_web_prompt_tab(self) -> None:
        """Create web prompt capture tab"""
        self.web_prompt_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.web_prompt_tab, text="Web Prompts")
        
        # Top controls frame
        top_frame = ttk.Frame(self.web_prompt_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - buttons and actions
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side="left", fill="x", padx=5)
        
        ttk.Button(button_frame, text="Paste & Save", 
                  command=self._paste_and_save_prompt).pack(side="left", padx=5)
        ttk.Button(button_frame, text="New Prompt", 
                  command=self._new_web_prompt).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", 
                  command=self._delete_web_prompt).pack(side="left", padx=5)
        
        # Right side - Model & App selection
        selector_frame = ttk.Frame(top_frame)
        selector_frame.pack(side="right", fill="x", padx=5)
        
        ttk.Label(selector_frame, text="Model:").pack(side="left", padx=2)
        self.web_model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]
        self.web_model_dropdown = ttk.Combobox(selector_frame, textvariable=self.web_model_var,
                                         values=models, state="readonly", width=25) # Increased width
        if models:
            self.web_model_var.set(models[0])
        self.web_model_dropdown.pack(side="left", padx=2)
        self.web_model_dropdown.bind("<<ComboboxSelected>>", self._on_web_model_selected)
        
        ttk.Label(selector_frame, text="App:").pack(side="left", padx=2)
        self.web_app_var = tk.StringVar()
        # Update app list for initial model, path updated to include "models" subdirectory
        base_dir = Path('.') / "models" / self.web_model_var.get()
        apps = natsorted([d.name for d in base_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")], 
                         key=_natural_sort_key) if base_dir.exists() else []
        
        self.web_app_dropdown = ttk.Combobox(selector_frame, textvariable=self.web_app_var,
                                       values=apps, state="readonly", width=15)
        if apps:
            self.web_app_var.set(apps[0])
        self.web_app_dropdown.pack(side="left", padx=2)
        
        # Split view - prompts list and editor
        paned_window = ttk.PanedWindow(self.web_prompt_tab, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Prompts list
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=1)
        
        # Search/filter bar
        web_filter_frame = ttk.Frame(list_frame) # Renamed 'filter_frame'
        web_filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(web_filter_frame, text="Search:").pack(side="left")
        self.web_filter_var = tk.StringVar()
        self.web_filter_entry = ttk.Entry(web_filter_frame, textvariable=self.web_filter_var)
        self.web_filter_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.web_filter_entry.bind("<KeyRelease>", lambda e: self._apply_web_filter())
        
        ttk.Button(web_filter_frame, text="Clear", 
                  command=self._clear_web_filter).pack(side="right", padx=2)
        
        # Prompts list
        columns = ("id", "timestamp", "model", "app", "preview")
        self.prompts_list = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.prompts_list.heading("id", text="ID")
        self.prompts_list.heading("timestamp", text="Date")
        self.prompts_list.heading("model", text="Model")
        self.prompts_list.heading("app", text="App")
        self.prompts_list.heading("preview", text="Preview")
        
        self.prompts_list.column("id", width=40, anchor="center")
        self.prompts_list.column("timestamp", width=120)
        self.prompts_list.column("model", width=150) # Increased width
        self.prompts_list.column("app", width=80)
        self.prompts_list.column("preview", width=200)
        
        # Add scrollbar
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.prompts_list.yview)
        self.prompts_list.configure(yscrollcommand=list_scroll.set)
        
        list_scroll.pack(side="right", fill="y")
        self.prompts_list.pack(fill="both", expand=True, padx=5)
        
        # Bind selection event
        self.prompts_list.bind("<<TreeviewSelect>>", self._on_web_prompt_selected)
        self.prompts_list.bind("<Button-3>", self._show_prompt_context_menu)
        
        # Right side - Text editors with tabs
        edit_frame = ttk.Frame(paned_window)
        paned_window.add(edit_frame, weight=2)
        
        self.prompt_notebook = ttk.Notebook(edit_frame)
        self.prompt_notebook.pack(fill="both", expand=True)
        
        # Prompt tab
        prompt_frame = ttk.Frame(self.prompt_notebook)
        self.web_prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap="word")
        self.web_prompt_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.prompt_notebook.add(prompt_frame, text="Prompt")
        
        # Response tab
        response_frame = ttk.Frame(self.prompt_notebook)
        self.web_response_text = scrolledtext.ScrolledText(response_frame, wrap="word")
        self.web_response_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.prompt_notebook.add(response_frame, text="Response")
        
        # Add keyboard shortcuts
        self.web_prompt_text.bind("<Control-s>", lambda e: self._save_web_prompt())
        self.web_response_text.bind("<Control-s>", lambda e: self._save_web_prompt())
        
        # Initialize by refreshing prompts list
        self._refresh_web_prompts_list()

    def _on_web_model_selected(self, event=None) -> None:
        """Handle model selection in web prompts tab"""
        model = self.web_model_var.get()
        # Path updated to include "models" subdirectory
        base_dir = Path('.') / "models" / model
        apps = []
        if base_dir.exists():
            apps = natsorted([d.name for d in base_dir.iterdir() 
                            if d.is_dir() and d.name.lower().startswith("app")],
                           key=_natural_sort_key)
        else:
            self._log(f"Web Prompts tab: Directory not found for model {model} at {base_dir}", error=True)
        
        self.web_app_dropdown["values"] = apps
        if apps:
            self.web_app_var.set(apps[0])
        else:
            self.web_app_var.set("")

    def _refresh_web_prompts_list(self) -> None:
        """Refresh the list of web prompts"""
        # Clear existing items
        for item in self.prompts_list.get_children():
            self.prompts_list.delete(item)
            
        # Get prompts from database
        prompts = self.database.get_prompts()
        
        # Apply filter if needed
        filter_text = self.web_filter_var.get().lower()
        
        # Add prompts to list
        for prompt_data in prompts: # Renamed 'prompt'
            prompt_id, model_name_db, app_name_db, prompt_text, response_text, timestamp = prompt_data # Renamed variables
            
            # Apply filter if set
            if filter_text and not (
                filter_text in model_name_db.lower() or 
                (app_name_db and filter_text in app_name_db.lower()) or # Check if app_name_db is not None
                filter_text in prompt_text.lower() or
                (response_text and filter_text in response_text.lower()) # Check if response_text is not None
            ):
                continue
            
            # Create preview by truncating the prompt text
            preview = prompt_text.strip().replace("\n", " ")
            preview = preview if len(preview) <= 50 else preview[:47] + "..."
            
            # Insert into the treeview
            self.prompts_list.insert("", tk.END, values=(
                prompt_id, timestamp, model_name_db, app_name_db or "", preview # Use app_name_db or ""
            ))

    def _apply_web_filter(self) -> None:
        """Apply filter to web prompts list"""
        self._refresh_web_prompts_list()
        filter_text = self.web_filter_var.get()
        if filter_text:
            self.status_var.set(f"Filtered prompts by: '{filter_text}'")
        else:
            self.status_var.set("Showing all prompts")

    def _clear_web_filter(self) -> None:
        """Clear the filter for web prompts"""
        self.web_filter_var.set("")
        self._refresh_web_prompts_list()
        self.status_var.set("Filter cleared")

    def _on_web_prompt_selected(self, event=None) -> None:
        """Handle selection of a prompt"""
        selected = self.prompts_list.selection()
        if not selected:
            return
        
        # Get prompt ID from selected item
        item = self.prompts_list.item(selected[0])
        prompt_id = item["values"][0]
        
        # Fetch prompt from database
        prompts = self.database.get_prompts() # This could be optimized by fetching only one
        prompt_data = next((p for p in prompts if p[0] == prompt_id), None)
        
        if not prompt_data:
            self._log(f"Prompt ID {prompt_id} not found in database.", error=True)
            return
        
        # Extract prompt data
        _, model_name_db, app_name_db, prompt_text, response_text, _ = prompt_data # Renamed variables
        
        # Update the fields
        self.web_model_var.set(model_name_db)
        self._on_web_model_selected()  # Update app dropdown
        
        if app_name_db and app_name_db in self.web_app_dropdown["values"]:
            self.web_app_var.set(app_name_db)
        else:
             self.web_app_var.set("") # Clear if app not found or not applicable
        
        # Replace port placeholders if needed
        prompt_text = self._replace_ports_in_content(prompt_text)
        
        # Update text areas
        self.web_prompt_text.delete("1.0", tk.END)
        self.web_prompt_text.insert(tk.END, prompt_text)
        
        self.web_response_text.delete("1.0", tk.END)
        if response_text:
            # Also replace port placeholders in response
            response_text = self._replace_ports_in_content(response_text)
            self.web_response_text.insert(tk.END, response_text)
        
        # Visual feedback
        self.status_var.set(f"Loaded prompt {prompt_id}")

    def _show_prompt_context_menu(self, event):
        """Show context menu for web prompts"""
        item_id = self.prompts_list.identify_row(event.y)
        if not item_id:
            return
            
        values = self.prompts_list.item(item_id, "values")
        prompt_id = values[0]
        model_name_val = values[2] # Renamed 'model'
        app_name_val = values[3]   # Renamed 'app'
        
        menu = tk.Menu(self.prompts_list, tearoff=0)
        menu.add_command(label="Edit Prompt", 
                        command=lambda: self._select_prompt(item_id))
        menu.add_command(label="Delete Prompt", 
                        command=lambda: self._delete_prompt_by_id(prompt_id))
        menu.add_separator()
        
        # Add option to load the app
        if model_name_val and app_name_val:
            menu.add_command(label=f"Load {model_name_val}/{app_name_val}", 
                            command=lambda: self._select_model_app(model_name_val, app_name_val))
        
        menu.post(event.x_root, event.y_root)

    def _select_prompt(self, item_id):
        """Select a prompt in the list"""
        self.prompts_list.selection_set(item_id)
        self.prompts_list.focus(item_id)
        self.prompts_list.see(item_id)
        self._on_web_prompt_selected(None)

    def _paste_and_save_prompt(self) -> None:
        """Paste from clipboard and save prompt"""
        try:
            # Get clipboard content
            content = self.clipboard_get()
            if not content.strip():
                self.status_var.set("Clipboard is empty")
                return
            
            # Replace port placeholders if needed
            content = self._replace_ports_in_content(content)
            
            # Update text editor
            self.web_prompt_text.delete("1.0", tk.END)
            self.web_prompt_text.insert(tk.END, content)
            
            # Get model and app
            model = self.web_model_var.get()
            app = self.web_app_var.get()
            
            # Get response text
            response_text = self.web_response_text.get("1.0", tk.END).strip()
            
            # Check if updating existing prompt
            selected = self.prompts_list.selection()
            
            if selected:
                # Update existing prompt
                prompt_id = self.prompts_list.item(selected[0])["values"][0]
                self.database.update_prompt(prompt_id, model, app, content, response_text)
                
                # Visual feedback
                self.status_var.set(f"✓ Updated prompt {prompt_id}")
                self._log(f"Updated prompt {prompt_id}")
            else:
                # Create new prompt
                self.database.save_prompt(model, app, content, response_text)
                
                # Visual feedback
                self.status_var.set("✓ Saved new prompt")
                self._log(f"Saved new prompt for {model}/{app}")
            
            # Auto-clear feedback after delay
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            # Refresh prompts list
            self._refresh_web_prompts_list()
            
        except Exception as e:
            self.status_var.set(f"Error saving prompt: {e}")
            self._log(f"Error saving prompt: {e}", error=True)

    def _save_web_prompt(self):
        """Save the current web prompt"""
        # Get current prompt and response
        prompt_text = self.web_prompt_text.get("1.0", tk.END).strip()
        response_text = self.web_response_text.get("1.0", tk.END).strip()
        
        if not prompt_text:
            self.status_var.set("Cannot save empty prompt")
            return
            
        # Get model and app
        model = self.web_model_var.get()
        app = self.web_app_var.get()
        
        # Check if updating existing prompt
        selected = self.prompts_list.selection()
        
        try:
            if selected:
                # Update existing prompt
                prompt_id = self.prompts_list.item(selected[0])["values"][0]
                self.database.update_prompt(prompt_id, model, app, prompt_text, response_text)
                
                # Visual feedback
                self.status_var.set(f"✓ Updated prompt {prompt_id}")
                self._log(f"Updated prompt {prompt_id}")
            else:
                # Create new prompt
                self.database.save_prompt(model, app, prompt_text, response_text)
                
                # Visual feedback
                self.status_var.set("✓ Saved new prompt")
                self._log(f"Saved new prompt for {model}/{app}")
            
            # Auto-clear feedback after delay
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            # Refresh prompts list
            self._refresh_web_prompts_list()
        except Exception as e:
            self.status_var.set(f"Error saving prompt: {e}")
            self._log(f"Error saving prompt: {e}", error=True)

    def _new_web_prompt(self) -> None:
        """Create a new web prompt"""
        # Clear selection
        for selected_item in self.prompts_list.selection(): # Renamed 'selected'
            self.prompts_list.selection_remove(selected_item)
        
        # Clear text areas
        self.web_prompt_text.delete("1.0", tk.END)
        self.web_response_text.delete("1.0", tk.END)
        
        # Switch to prompt tab
        self.prompt_notebook.select(0)
        
        # Focus prompt editor
        self.web_prompt_text.focus_set()
        
        # Visual feedback
        self.status_var.set("New prompt")

    def _delete_web_prompt(self) -> None:
        """Delete the selected web prompt"""
        selected = self.prompts_list.selection()
        if not selected:
            self.status_var.set("No prompt selected")
            return
            
        prompt_id = self.prompts_list.item(selected[0])["values"][0]
        self._delete_prompt_by_id(prompt_id)

    def _delete_prompt_by_id(self, prompt_id) -> None:
        """Delete a web prompt by ID"""
        if not messagebox.askyesno("Confirm Delete", f"Delete prompt #{prompt_id}?"):
            return
            
        try:
            self.database.delete_prompt(prompt_id)
            
            # Clear text areas if the deleted prompt was selected
            selected_items = self.prompts_list.selection()
            if selected_items and self.prompts_list.item(selected_items[0])["values"][0] == prompt_id:
                self.web_prompt_text.delete("1.0", tk.END)
                self.web_response_text.delete("1.0", tk.END)

            # Refresh list
            self._refresh_web_prompts_list()
            
            # Visual feedback
            self.status_var.set(f"✓ Deleted prompt {prompt_id}")
            self.after(1500, lambda: self.status_var.set("Ready"))
            
            self._log(f"Deleted prompt {prompt_id}")
        except Exception as e:
            self.status_var.set(f"Error deleting prompt: {e}")
            self._log(f"Error deleting prompt: {e}", error=True)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    def _log(self, message: str, error: bool = False) -> None:
        """Log a message to the console and the GUI log"""
        timestamp = time.strftime("%H:%M:%S")
        level = "ERROR" if error else "INFO"
        entry = f"[{timestamp}] {level}: {message}\n"
        
        # Update GUI log
        if hasattr(self, 'log_text') and self.log_text: # Check if log_text exists
            self.log_text.config(state="normal")
            self.log_text.insert(tk.END, entry)
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")

        # Log to file/console
        if error:
            logger.error(message)
        else:
            logger.info(message)

    def _run_in_thread(self, func):
        """Run a function in a separate thread"""
        def wrapper(*args, **kwargs):
            threading.Thread(target=self._safe_run, args=(func, *args), kwargs=kwargs, daemon=True).start()
        return wrapper

    def _safe_run(self, func, *args, **kwargs):
        """Safely run a function and catch exceptions"""
        try:
            func(*args, **kwargs)
        except Exception as e:
            self._log(f"Error in {func.__name__}: {e}", error=True)
            # Check if messagebox is available (it might not be if GUI isn't fully up)
            if hasattr(messagebox, 'showerror'):
                 messagebox.showerror("Error", str(e))
            
    def on_closing(self) -> None:
        """Handle application closing"""
        try:
            self.database.close()
            logger.info("Application shutting down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        self.destroy()

# =============================================================================
# GUI Logging Handler
# =============================================================================
class GuiLogHandler(logging.Handler):
    def __init__(self, app: AssistantApp) -> None:
        super().__init__()
        self.app = app

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        # Ensure app.log_text is available before trying to use it
        if hasattr(self.app, 'log_text') and self.app.log_text:
            try:
                self.app.log_text.config(state="normal")
                self.app.log_text.insert(tk.END, msg + "\n")
                self.app.log_text.see(tk.END)
                self.app.log_text.config(state="disabled")
            except tk.TclError:
                # Handle cases where the widget might be destroyed during shutdown
                pass


# =============================================================================
# Main Entry
# =============================================================================
if __name__ == "__main__":
    app = AssistantApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
