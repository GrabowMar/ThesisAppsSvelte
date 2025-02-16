#!/usr/bin/env python3
import csv
import json
import logging
import os
import re
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# =============================================================================
# Configuration
# =============================================================================
CONFIG = {
    "presets_dir": Path("zzz_Bot/app_templates"),  # Folder with template files
    "default_template_ext": ".md",
    "allowed_models": {"ChatGPT4o", "ChatGPTo1", "ChatGPTo3", "ClaudeSonnet",
                       "DeepSeek", "Gemini", "Grok", "Llama", "Mixtral", "Qwen"}
}

# -----------------------------------------------------------------------------
# Logger Setup
# -----------------------------------------------------------------------------
logger = logging.getLogger("CodeGenAssistant")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt="%H:%M:%S")
file_handler = logging.FileHandler("assistant.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# =============================================================================
# Natural Sort Helper: Using natsort if available; fallback if not.
# =============================================================================
try:
    from natsort import natsorted
except ImportError:
    def natural_sort_key(s: str):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)
]
    def natsorted(seq):
        return sorted(seq, key=natural_sort_key)

# =============================================================================
# Database Manager for Progress Tracking
# =============================================================================
class DatabaseManager:
    def __init__(self, db_path: str = "progress_logs.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

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

# =============================================================================
# Main Assistant UI
# =============================================================================
class AssistantUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Code Generation Assistant")
        self.geometry("1200x850")
        self.configure(bg="white")
        self.db_manager = DatabaseManager()  # Initialize progress tracking DB
        self.pause_refresh = False
        self._create_menu()
        self._create_widgets()
        self._setup_logging_handler()

    def _create_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("About", "Code Generation Assistant\nVersion 1.0"))
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _create_widgets(self) -> None:
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        self._create_template_tab()
        self._create_generate_code_tab()
        self._create_replace_files_tab()
        self._create_progress_tab()
        self._create_status_tab()
        self._create_logging_frame()

    def _setup_logging_handler(self) -> None:
        gui_handler = GuiLogHandler(self)
        gui_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(gui_handler)

    # -------------------------------------------------------------------------
    # TAB 1: Template Management
    # -------------------------------------------------------------------------
    def _create_template_tab(self) -> None:
        self.template_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.template_tab, text="Template")
        top_frame = ttk.Frame(self.template_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="Select Template:").pack(side="left")
        self.template_var = tk.StringVar()
        presets = self._get_presets()
        self.template_dropdown = ttk.Combobox(
            top_frame, textvariable=self.template_var,
            values=presets, state="readonly", width=40)
        if presets:
            self.template_var.set(presets[0])
        self.template_dropdown.pack(side="left", padx=5)
        ttk.Button(top_frame, text="Load Template", command=self.load_template).pack(side="left", padx=5)
        # ttk.Button(top_frame, text="Save Template", command=self.save_template).pack(side="left", padx=5)
        # ttk.Button(top_frame, text="New Template", command=self.new_template).pack(side="left", padx=5)
        # ttk.Button(top_frame, text="Delete Template", command=self.delete_template).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Copy Template to Clipboard", command=self.copy_template_to_clipboard).pack(side="left", padx=5)
        self.template_text = tk.Text(self.template_tab, wrap="word", height=25)
        self.template_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _get_presets(self) -> list:
        presets_dir = CONFIG["presets_dir"]
        presets_dir.mkdir(exist_ok=True)
        presets = [f.name for f in presets_dir.glob(f"*{CONFIG['default_template_ext']}")]
        return natsorted(presets)

    def load_template(self) -> None:
        preset_name = self.template_var.get()
        template_path = CONFIG["presets_dir"] / preset_name
        if template_path.exists():
            try:
                content = template_path.read_text(encoding="utf-8")
                self.template_text.delete("1.0", tk.END)
                self.template_text.insert(tk.END, content)
                self.log(f"Loaded template: {preset_name}")
            except Exception as e:
                self.log(f"Error loading template: {e}", error=True)
        else:
            self.log("Template file not found", error=True)

    def save_template(self) -> None:
        preset_name = self.template_var.get()
        template_path = CONFIG["presets_dir"] / preset_name
        try:
            content = self.template_text.get("1.0", tk.END).strip()
            template_path.write_text(content, encoding="utf-8")
            self.log(f"Template '{preset_name}' saved successfully.")
        except Exception as e:
            self.log(f"Error saving template: {e}", error=True)

    def new_template(self) -> None:
        new_name = filedialog.asksaveasfilename(
            initialdir=CONFIG["presets_dir"],
            defaultextension=CONFIG["default_template_ext"],
            filetypes=[("Markdown Files", f"*{CONFIG['default_template_ext']}")],
            title="Create New Template"
        )
        if new_name:
            new_path = Path(new_name)
            if new_path.exists():
                messagebox.showwarning("Warning", "Template already exists.")
                return
            try:
                new_path.write_text("", encoding="utf-8")
                self.log(f"Created new template: {new_path.name}")
                self.template_dropdown['values'] = self._get_presets()
                self.template_var.set(new_path.name)
                self.template_text.delete("1.0", tk.END)
            except Exception as e:
                self.log(f"Error creating new template: {e}", error=True)

    def delete_template(self) -> None:
        preset_name = self.template_var.get()
        template_path = CONFIG["presets_dir"] / preset_name
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete template '{preset_name}'?"):
            try:
                template_path.unlink()
                self.log(f"Deleted template: {preset_name}")
                self.template_dropdown['values'] = self._get_presets()
                presets = self._get_presets()
                if presets:
                    self.template_var.set(presets[0])
                self.template_text.delete("1.0", tk.END)
            except Exception as e:
                self.log(f"Error deleting template: {e}", error=True)

    def copy_template_to_clipboard(self) -> None:
        content = self.template_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(content)
        self.log("Template copied to clipboard.")

    # -------------------------------------------------------------------------
    # TAB 2: Generate Code (Auto & LLM Paste)
    # -------------------------------------------------------------------------
    def _create_generate_code_tab(self) -> None:
        self.generate_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.generate_tab, text="Generate Code")
        top_frame = ttk.Frame(self.generate_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(top_frame, text="Generate Code", command=self._threaded(self.generate_code)).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Paste LLM Output", command=self.paste_llm_output).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Save Generated Files", command=self.save_generated_files).pack(side="left", padx=5)
        # Notebook for generated file outputs.
        self.generated_nb = ttk.Notebook(self.generate_tab)
        self.generated_nb.pack(fill="both", expand=True, padx=10, pady=5)
        # app.py tab
        self.app_py_frame = ttk.Frame(self.generated_nb)
        self.app_py_text = tk.Text(self.app_py_frame, wrap="none")
        self.app_py_text.pack(fill="both", expand=True)
        self.generated_nb.add(self.app_py_frame, text="app.py")
        # App.svelte tab
        self.app_svelte_frame = ttk.Frame(self.generated_nb)
        self.app_svelte_text = tk.Text(self.app_svelte_frame, wrap="none")
        self.app_svelte_text.pack(fill="both", expand=True)
        self.generated_nb.add(self.app_svelte_frame, text="App.svelte")
        # requirements.txt tab
        self.requirements_frame = ttk.Frame(self.generated_nb)
        self.requirements_text = tk.Text(self.requirements_frame, wrap="none")
        self.requirements_text.pack(fill="both", expand=True)
        self.generated_nb.add(self.requirements_frame, text="requirements.txt")
        # package.json tab
        self.package_json_frame = ttk.Frame(self.generated_nb)
        self.package_json_text = tk.Text(self.package_json_frame, wrap="none")
        self.package_json_text.pack(fill="both", expand=True)
        self.generated_nb.add(self.package_json_frame, text="package.json")

    def generate_code(self) -> None:
        template_content = self.template_text.get("1.0", tk.END).strip()
        if not template_content:
            self.log("Template is empty. Please load or create a template first.", error=True)
            return

        task = "Generate Code"
        self.db_manager.log_progress(task, 0, "Started code generation")
        self._update_progress_bar(self.gen_progress, 0)  # using a shared progress bar later if desired

        # Simulate gradual progress update.
        steps = [("Generating app.py", 25),
                 ("Generating App.svelte", 50),
                 ("Generating requirements.txt", 75),
                 ("Generating package.json", 100)]
        for message, prog in steps:
            for i in range(prog - 5, prog + 1, 5):
                time.sleep(0.05)
                self._update_progress_bar(self.gen_progress, i)
            self.db_manager.log_progress(task, prog, message)
            self.log(message)

        # Generate file content based on the template.
        self.app_py_text.delete("1.0", tk.END)
        self.app_py_text.insert(tk.END, f"# Generated app.py code\n# Template: {self.template_var.get()}\n\n{template_content}")
        
        self.app_svelte_text.delete("1.0", tk.END)
        self.app_svelte_text.insert(tk.END, f"<!-- Generated App.svelte code -->\n<!-- Template: {self.template_var.get()} -->\n\n{template_content}")
        
        self.requirements_text.delete("1.0", tk.END)
        self.requirements_text.insert(tk.END, f"# Auto-generated requirements.txt\n# Template: {self.template_var.get()}\n\n{template_content}")
        
        # Create a simple package.json structure.
        pkg = {
            "name": "generated-app",
            "version": "1.0.0",
            "description": f"Generated from template {self.template_var.get()}",
            "dependencies": {}
        }
        self.package_json_text.delete("1.0", tk.END)
        self.package_json_text.insert(tk.END, json.dumps(pkg, indent=2))
        self.log("Code generation completed.")

    def paste_llm_output(self) -> None:
        """
        Expects clipboard text in the following format:
        
        === app.py ===
        <content>
        === App.svelte ===
        <content>
        === requirements.txt ===
        <content>
        === package.json ===
        <content>
        """
        try:
            text = self.clipboard_get()
        except Exception as e:
            self.log(f"Could not get clipboard content: {e}", error=True)
            return

        # Define regex to extract sections.
        pattern = re.compile(r"===\s*(app\.py|App\.svelte|requirements\.txt|package\.json)\s*===\s*(.*?)\s*(?=^===|\Z)", re.DOTALL | re.MULTILINE)
        matches = pattern.findall(text)
        if not matches:
            self.log("No valid LLM output sections found.", error=True)
            return

        for filename, content in matches:
            content = content.strip()
            if filename.lower() == "app.py":
                self.app_py_text.delete("1.0", tk.END)
                self.app_py_text.insert(tk.END, content)
            elif filename.lower() == "app.svelte":
                self.app_svelte_text.delete("1.0", tk.END)
                self.app_svelte_text.insert(tk.END, content)
            elif filename.lower() == "requirements.txt":
                self.requirements_text.delete("1.0", tk.END)
                self.requirements_text.insert(tk.END, content)
            elif filename.lower() == "package.json":
                self.package_json_text.delete("1.0", tk.END)
                self.package_json_text.insert(tk.END, content)
        self.log("LLM output pasted successfully.")

    def save_generated_files(self) -> None:
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        try:
            out_path = Path(output_dir)
            (out_path / "app.py").write_text(self.app_py_text.get("1.0", tk.END), encoding="utf-8")
            (out_path / "App.svelte").write_text(self.app_svelte_text.get("1.0", tk.END), encoding="utf-8")
            (out_path / "requirements.txt").write_text(self.requirements_text.get("1.0", tk.END), encoding="utf-8")
            (out_path / "package.json").write_text(self.package_json_text.get("1.0", tk.END), encoding="utf-8")
            self.log(f"Generated files saved to {output_dir}")
        except Exception as e:
            self.log(f"Error saving generated files: {e}", error=True)

    # -------------------------------------------------------------------------
    # TAB 3: Replace Files in Model Folders
    # -------------------------------------------------------------------------
    def _create_replace_files_tab(self) -> None:
        self.replace_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.replace_tab, text="Replace Files")
        sel_frame = ttk.Frame(self.replace_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(sel_frame, text="Select Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.model_var = tk.StringVar()
        models = self._get_models()
        self.model_dropdown = ttk.Combobox(sel_frame, textvariable=self.model_var,
                                           values=models, state="readonly", width=30)
        if models:
            self.model_var.set(models[0])
        self.model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.model_dropdown.bind("<<ComboboxSelected>>", self._update_app_dropdown)
        ttk.Label(sel_frame, text="Select App:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.app_var = tk.StringVar()
        apps = self._get_apps_for_model(self.model_var.get())
        self.app_dropdown = ttk.Combobox(sel_frame, textvariable=self.app_var,
                                         values=apps, state="readonly", width=30)
        if apps:
            self.app_var.set(apps[0])
        self.app_dropdown.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        # File replacement buttons.
        btn_frame = ttk.Frame(self.replace_tab)
        btn_frame.pack(padx=10, pady=5)
        ttk.Button(btn_frame, text="Replace app.py",
                   command=self._threaded(lambda: self.replace_file("app.py", self.app_py_text.get("1.0", tk.END)))).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace App.svelte",
                   command=self._threaded(lambda: self.replace_file("App.svelte", self.app_svelte_text.get("1.0", tk.END)))).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace requirements.txt",
                   command=self._threaded(lambda: self.replace_file("requirements.txt", self.requirements_text.get("1.0", tk.END)))).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace package.json",
                   command=self._threaded(lambda: self.replace_file("package.json", self.package_json_text.get("1.0", tk.END)))).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(btn_frame, text="Replace All Files",
                   command=self._threaded(self.replace_all_files)).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

    def _get_models(self) -> list:
        return sorted([d.name for d in Path('.').iterdir() if d.is_dir() and d.name in CONFIG["allowed_models"]])

    def _get_apps_for_model(self, model: str) -> list:
        model_dir = Path('.') / model
        if model_dir.exists():
            return natsorted([d.name for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")])
        return []

    def _update_app_dropdown(self, event=None) -> None:
        model = self.model_var.get()
        apps = self._get_apps_for_model(model)
        self.app_dropdown['values'] = apps
        self.app_var.set(apps[0] if apps else "")

    def replace_file(self, filename: str, new_content: str) -> None:
        task = f"Replace {filename}"
        self.db_manager.log_progress(task, 0, "Starting file replacement")
        model = self.model_var.get()
        app_folder = self.app_var.get()
        if not model or not app_folder:
            self.log("Model or App not selected", error=True)
            return

        target_dir = Path('.') / model / app_folder
        if not target_dir.exists():
            self.log(f"Target folder {target_dir} does not exist", error=True)
            return

        target_file = target_dir / filename
        if not messagebox.askyesno("Confirm Replacement",
                                   f"Replace the content of {target_file} with the new content?"):
            self.log("Replacement canceled")
            return

        try:
            new_content = new_content.strip()
            if not new_content:
                self.log("No content provided for replacement.", error=True)
                return
            target_file.write_text(new_content, encoding="utf-8")
            self.db_manager.log_progress(task, 100, f"Replaced content of {target_file}")
            self.log(f"Replaced content of {target_file}")
        except Exception as e:
            self.log(f"Failed to replace file content: {e}", error=True)
            self.db_manager.log_progress(task, 0, f"Error: {e}")

    def replace_all_files(self) -> None:
        self.replace_file("app.py", self.app_py_text.get("1.0", tk.END))
        self.replace_file("App.svelte", self.app_svelte_text.get("1.0", tk.END))
        self.replace_file("requirements.txt", self.requirements_text.get("1.0", tk.END))
        self.replace_file("package.json", self.package_json_text.get("1.0", tk.END))

    # -------------------------------------------------------------------------
    # TAB 4: Progress Logs
    # -------------------------------------------------------------------------
    def _create_progress_tab(self) -> None:
        self.progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_tab, text="Progress Logs")
        top_frame = ttk.Frame(self.progress_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.progress_filter = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.progress_filter).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Refresh", command=self.refresh_progress_logs).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Clear", command=self.clear_progress_logs).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Export CSV", command=self.export_progress_logs).pack(side="left", padx=5)
        self.pause_btn = ttk.Button(top_frame, text="Pause", command=self.toggle_auto_refresh)
        self.pause_btn.pack(side="left", padx=5)
        columns = ("timestamp", "task", "progress", "message")
        self.progress_tree = ttk.Treeview(self.progress_tab, columns=columns, show="headings")
        self.progress_tree.heading("timestamp", text="Timestamp")
        self.progress_tree.heading("task", text="Task")
        self.progress_tree.heading("progress", text="Progress")
        self.progress_tree.heading("message", text="Message")
        self.progress_tree.column("timestamp", width=150)
        self.progress_tree.column("task", width=150)
        self.progress_tree.column("progress", width=80, anchor="center")
        self.progress_tree.column("message", width=400)
        vsb = ttk.Scrollbar(self.progress_tab, orient="vertical", command=self.progress_tree.yview)
        self.progress_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.progress_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self.gen_progress = ttk.Progressbar(top_frame, orient="horizontal", mode="determinate", maximum=100)
        self.gen_progress.pack(side="left", fill="x", expand=True, padx=5)
        self._auto_refresh_progress()

    def toggle_auto_refresh(self) -> None:
        self.pause_refresh = not self.pause_refresh
        self.pause_btn.config(text="Resume" if self.pause_refresh else "Pause")

    def _auto_refresh_progress(self) -> None:
        if not self.pause_refresh:
            self.refresh_progress_logs()
        self.after(5000, self._auto_refresh_progress)

    def refresh_progress_logs(self) -> None:
        filter_text = self.progress_filter.get().lower()
        for row in self.progress_tree.get_children():
            self.progress_tree.delete(row)
        logs = self.db_manager.get_recent_logs(limit=100)
        for log_entry in logs:
            timestamp = log_entry[4]
            task = log_entry[1]
            progress = log_entry[2]
            message = log_entry[3]
            if filter_text and filter_text not in task.lower() and filter_text not in message.lower():
                continue
            self.progress_tree.insert("", tk.END, values=(timestamp, task, f"{progress}%", message))

    def clear_progress_logs(self) -> None:
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all progress logs?"):
            self.db_manager.clear_logs()
            self.refresh_progress_logs()
            self.log("Progress logs cleared.")

    def export_progress_logs(self) -> None:
        export_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Export progress logs to CSV"
        )
        if not export_path:
            return
        logs = self.db_manager.get_recent_logs(limit=1000)
        try:
            with open(export_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Timestamp", "Task", "Progress", "Message"])
                for log_entry in logs:
                    writer.writerow([log_entry[4], log_entry[1], f"{log_entry[2]}%", log_entry[3]])
            self.log(f"Progress logs exported to {export_path}")
        except Exception as e:
            self.log(f"Export failed: {e}", error=True)

    # -------------------------------------------------------------------------
    # TAB 5: Model & App Status
    # -------------------------------------------------------------------------
    def _create_status_tab(self) -> None:
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="Model & App Status")
        top_frame = ttk.Frame(self.status_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.status_filter = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.status_filter).pack(side="left", padx=5)
        ttk.Button(top_frame, text="Refresh", command=self.refresh_status_table).pack(side="left", padx=5)
        columns = ("model", "app", "app_py", "app_svelte")
        self.status_tree = ttk.Treeview(self.status_tab, columns=columns, show="headings")
        self.status_tree.heading("model", text="Model")
        self.status_tree.heading("app", text="App")
        self.status_tree.heading("app_py", text="app.py Generated")
        self.status_tree.heading("app_svelte", text="App.svelte Generated")
        self.status_tree.column("model", width=100)
        self.status_tree.column("app", width=100)
        self.status_tree.column("app_py", width=150, anchor="center")
        self.status_tree.column("app_svelte", width=150, anchor="center")
        vsb = ttk.Scrollbar(self.status_tab, orient="vertical", command=self.status_tree.yview)
        self.status_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.status_tree.pack(fill="both", expand=True, padx=10, pady=5)
        self._auto_refresh_status_table()

    def _auto_refresh_status_table(self) -> None:
        self.refresh_status_table()
        self.after(10000, self._auto_refresh_status_table)

    def refresh_status_table(self) -> None:
        filter_text = self.status_filter.get().lower()
        for row in self.status_tree.get_children():
            self.status_tree.delete(row)
        for model_dir in sorted(Path('.').iterdir()):
            if model_dir.is_dir() and model_dir.name in CONFIG["allowed_models"]:
                app_dirs = natsorted([d for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")])
                for app_dir in app_dirs:
                    app_py_exists = (app_dir / "app.py").exists()
                    app_svelte_exists = (app_dir / "App.svelte").exists()
                    if filter_text:
                        if filter_text not in model_dir.name.lower() and filter_text not in app_dir.name.lower():
                            continue
                    self.status_tree.insert("", tk.END, values=(
                        model_dir.name,
                        app_dir.name,
                        "Yes" if app_py_exists else "No",
                        "Yes" if app_svelte_exists else "No"
                    ))

    # -------------------------------------------------------------------------
    # Logging Frame at Bottom
    # -------------------------------------------------------------------------
    def _create_logging_frame(self) -> None:
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x", side="bottom")
        ttk.Label(log_frame, text="Log:").pack(anchor="w", padx=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=5)

    def log(self, message: str, error: bool = False) -> None:
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

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    def _update_progress_bar(self, progress_bar: ttk.Progressbar, value: int) -> None:
        progress_bar['value'] = value
        self.update_idletasks()

    def _threaded(self, func):
        def wrapper(*args, **kwargs):
            threading.Thread(target=self._run_safe, args=(func, *args), kwargs=kwargs, daemon=True).start()
        return wrapper

    def _run_safe(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            self.log(f"Error in {func.__name__}: {e}", error=True)
            messagebox.showerror("Error", str(e))

# =============================================================================
# Custom Logging Handler for GUI Log Output
# =============================================================================
class GuiLogHandler(logging.Handler):
    def __init__(self, ui: AssistantUI) -> None:
        super().__init__()
        self.ui = ui

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self.ui.log_text.config(state="normal")
        self.ui.log_text.insert(tk.END, msg + "\n")
        self.ui.log_text.see(tk.END)
        self.ui.log_text.config(state="disabled")

if __name__ == "__main__":
    app = AssistantUI()
    app.mainloop()
