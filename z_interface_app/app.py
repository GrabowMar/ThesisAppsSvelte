#!/usr/bin/env python3
import csv
import os
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
    "presets_dir": Path("app_templates"),  # Folder with template files
    "default_template_ext": ".md",
    "allowed_models": {"ChatGPT4o", "ChatGPTo1", "ChatGPTo3", "ClaudeSonnet",
                       "DeepSeek", "Gemini", "Grok", "Llama", "Mixtral", "Qwen"}
}


# =============================================================================
# Database Manager for Progress Tracking
# =============================================================================
class DatabaseManager:
    def __init__(self, db_path="progress_logs.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
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

    def log_progress(self, task: str, progress: int, message: str):
        with self.conn:
            self.conn.execute(
                "INSERT INTO progress_logs (task, progress, message) VALUES (?, ?, ?)",
                (task, progress, message)
            )

    def get_recent_logs(self, limit: int = 100):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, task, progress, message, timestamp FROM progress_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,))
        return cursor.fetchall()

    def clear_logs(self):
        with self.conn:
            self.conn.execute("DELETE FROM progress_logs")


# =============================================================================
# Main Assistant UI
# =============================================================================
class AssistantUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Code Generation Assistant")
        self.geometry("1100x750")
        self.db_manager = DatabaseManager()  # Initialize progress tracking DB
        self.auto_refresh = True  # Flag to control auto-refresh of progress table
        self._create_widgets()

    def _create_widgets(self):
        # Create a Notebook to separate the workflow into distinct steps.
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self._create_template_tab()
        self._create_generate_code_tab()
        self._create_replace_files_tab()
        self._create_progress_tab()       # Progress Logs (table from DB)
        self._create_status_tab()         # New: Model & App Status

        # Bottom log frame for general messages.
        self._create_logging_frame()

    # -------------------------------------------------------------------------
    # TAB 1: Template Selection
    # -------------------------------------------------------------------------
    def _create_template_tab(self):
        self.template_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.template_tab, text="Template")

        sel_frame = ttk.Frame(self.template_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(sel_frame, text="Select Template:").pack(side="left")

        self.template_var = tk.StringVar()
        presets = self._get_presets()
        self.template_dropdown = ttk.Combobox(
            sel_frame, textvariable=self.template_var,
            values=presets, state="readonly", width=40)
        if presets:
            self.template_var.set(presets[0])
        self.template_dropdown.pack(side="left", padx=5)

        load_btn = ttk.Button(sel_frame, text="Load Template", command=self.load_template)
        load_btn.pack(side="left", padx=5)

        # Text area for template content.
        self.template_text = tk.Text(self.template_tab, wrap="word", height=20)
        self.template_text.pack(fill="both", expand=True, padx=10, pady=5)

    # -------------------------------------------------------------------------
    # TAB 2: Generate Code Files
    # -------------------------------------------------------------------------
    def _create_generate_code_tab(self):
        self.generate_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.generate_tab, text="Generate Code")

        top_frame = ttk.Frame(self.generate_tab)
        top_frame.pack(fill="x", padx=10, pady=5)

        gen_btn = ttk.Button(top_frame, text="Generate Code", command=self._threaded(self.generate_code))
        gen_btn.pack(side="left", padx=5)

        # Progress bar for code generation.
        self.gen_progress = ttk.Progressbar(top_frame, orient="horizontal", mode="determinate", maximum=100)
        self.gen_progress.pack(side="left", fill="x", expand=True, padx=5)

        # Frame that holds two code areas side by side.
        code_frame = ttk.Frame(self.generate_tab)
        code_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: app.py content.
        app_py_frame = ttk.LabelFrame(code_frame, text="app.py")
        app_py_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.app_py_text = tk.Text(app_py_frame, wrap="none")
        self.app_py_text.pack(fill="both", expand=True)

        # Right: App.svelte content.
        app_svelte_frame = ttk.LabelFrame(code_frame, text="App.svelte")
        app_svelte_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.app_svelte_text = tk.Text(app_svelte_frame, wrap="none")
        self.app_svelte_text.pack(fill="both", expand=True)

    # -------------------------------------------------------------------------
    # TAB 3: Replace Files in Model Folders
    # -------------------------------------------------------------------------
    def _create_replace_files_tab(self):
        self.replace_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.replace_tab, text="Replace Files")

        sel_frame = ttk.Frame(self.replace_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        # Model selection.
        ttk.Label(sel_frame, text="Select Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.model_var = tk.StringVar()
        models = self._get_models()
        self.model_dropdown = ttk.Combobox(sel_frame, textvariable=self.model_var,
                                           values=models, state="readonly", width=30)
        if models:
            self.model_var.set(models[0])
        self.model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.model_dropdown.bind("<<ComboboxSelected>>", self._update_app_dropdown)

        # App folder selection.
        ttk.Label(sel_frame, text="Select App:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.app_var = tk.StringVar()
        apps = self._get_apps_for_model(self.model_var.get())
        self.app_dropdown = ttk.Combobox(sel_frame, textvariable=self.app_var,
                                         values=apps, state="readonly", width=30)
        if apps:
            self.app_var.set(apps[0])
        self.app_dropdown.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Replacement buttons.
        btn_frame = ttk.Frame(self.replace_tab)
        btn_frame.pack(padx=10, pady=5)
        replace_app_py_btn = ttk.Button(
            btn_frame, text="Replace app.py",
            command=self._threaded(lambda: self.replace_file("app.py",
                                                               self.app_py_text.get("1.0", tk.END))))
        replace_app_svelte_btn = ttk.Button(
            btn_frame, text="Replace App.svelte",
            command=self._threaded(lambda: self.replace_file("App.svelte",
                                                               self.app_svelte_text.get("1.0", tk.END))))
        replace_app_py_btn.grid(row=0, column=0, padx=5, pady=5)
        replace_app_svelte_btn.grid(row=0, column=1, padx=5, pady=5)

    # -------------------------------------------------------------------------
    # TAB 4: Enhanced Progress Logs (with Table from DB)
    # -------------------------------------------------------------------------
    def _create_progress_tab(self):
        self.progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_tab, text="Progress Logs")

        top_frame = ttk.Frame(self.progress_tab)
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.progress_filter = tk.StringVar()
        self.filter_entry = ttk.Entry(top_frame, textvariable=self.progress_filter)
        self.filter_entry.pack(side="left", padx=5)

        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self.refresh_progress_logs)
        refresh_btn.pack(side="left", padx=5)
        clear_btn = ttk.Button(top_frame, text="Clear", command=self.clear_progress_logs)
        clear_btn.pack(side="left", padx=5)
        export_btn = ttk.Button(top_frame, text="Export CSV", command=self.export_progress_logs)
        export_btn.pack(side="left", padx=5)
        
        self.pause_refresh = False
        self.pause_btn = ttk.Button(top_frame, text="Pause", command=self.toggle_auto_refresh)
        self.pause_btn.pack(side="left", padx=5)

        # Create a Treeview for a progress table.
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

        # Auto-refresh the progress table every 5 seconds.
        self._auto_refresh_progress()

    def toggle_auto_refresh(self):
        self.pause_refresh = not self.pause_refresh
        self.pause_btn.config(text="Resume" if self.pause_refresh else "Pause")

    def _auto_refresh_progress(self):
        if not self.pause_refresh:
            self.refresh_progress_logs()
        self.after(5000, self._auto_refresh_progress)

    def refresh_progress_logs(self):
        filter_text = self.progress_filter.get().lower()
        # Clear existing rows.
        for row in self.progress_tree.get_children():
            self.progress_tree.delete(row)
        logs = self.db_manager.get_recent_logs(limit=100)
        for log_entry in logs:
            # log_entry: (id, task, progress, message, timestamp)
            timestamp = log_entry[4]
            task = log_entry[1]
            progress = log_entry[2]
            message = log_entry[3]
            if filter_text and filter_text not in task.lower() and filter_text not in message.lower():
                continue
            self.progress_tree.insert("", tk.END, values=(timestamp, task, f"{progress}%", message))

    def clear_progress_logs(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all progress logs?"):
            self.db_manager.clear_logs()
            self.refresh_progress_logs()
            self.log("Progress logs cleared.")

    def export_progress_logs(self):
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
    def _create_status_tab(self):
        self.status_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.status_tab, text="Model & App Status")

        top_frame = ttk.Frame(self.status_tab)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="Filter:").pack(side="left", padx=5)
        self.status_filter = tk.StringVar()
        self.status_filter_entry = ttk.Entry(top_frame, textvariable=self.status_filter)
        self.status_filter_entry.pack(side="left", padx=5)
        refresh_btn = ttk.Button(top_frame, text="Refresh", command=self.refresh_status_table)
        refresh_btn.pack(side="left", padx=5)

        # Create a Treeview for the status table.
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

        # Auto-refresh the status table every 10 seconds.
        self._auto_refresh_status_table()

    def _auto_refresh_status_table(self):
        self.refresh_status_table()
        self.after(10000, self._auto_refresh_status_table)

    def refresh_status_table(self):
        filter_text = self.status_filter.get().lower()
        # Clear the treeview.
        for row in self.status_tree.get_children():
            self.status_tree.delete(row)
        # Scan the current directory for allowed model directories.
        for model_dir in sorted(Path('.').iterdir()):
            if model_dir.is_dir() and model_dir.name in CONFIG["allowed_models"]:
                for app_dir in sorted(model_dir.iterdir()):
                    if app_dir.is_dir() and app_dir.name.lower().startswith("app"):
                        app_py_exists = (app_dir / "app.py").exists()
                        app_svelte_exists = (app_dir / "App.svelte").exists()
                        # Apply filtering if set.
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
    def _create_logging_frame(self):
        log_frame = ttk.Frame(self)
        log_frame.pack(fill="x", side="bottom")
        ttk.Label(log_frame, text="Log:").pack(anchor="w", padx=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.pack(fill="x", padx=5, pady=5)

    def log(self, message: str, error: bool = False):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {'ERROR' if error else 'INFO'}: {message}\n"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, entry)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    # -------------------------------------------------------------------------
    # Template Tab Methods
    # -------------------------------------------------------------------------
    def _get_presets(self):
        presets_dir = CONFIG["presets_dir"]
        presets_dir.mkdir(exist_ok=True)
        return [f.name for f in presets_dir.glob(f"*{CONFIG['default_template_ext']}")]

    def load_template(self):
        preset_name = self.template_var.get()
        template_path = CONFIG["presets_dir"] / preset_name
        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            self.template_text.delete("1.0", tk.END)
            self.template_text.insert(tk.END, content)
            self.log(f"Loaded template: {preset_name}")
        else:
            self.log("Template file not found", error=True)

    # -------------------------------------------------------------------------
    # Generate Code Tab Methods (with progress tracking)
    # -------------------------------------------------------------------------
    def generate_code(self):
        template_content = self.template_text.get("1.0", tk.END).strip()
        if not template_content:
            self.log("Template is empty. Please load a template first.", error=True)
            return

        task = "Generate Code"
        self.db_manager.log_progress(task, 0, "Started code generation")
        self._update_progress_bar(self.gen_progress, 0)

        # Simulate generating app.py.
        time.sleep(0.5)  # Simulated delay.
        app_py_code = (
            f"# Generated app.py code\n"
            f"# Template used: {self.template_var.get()}\n\n" +
            template_content
        )
        self.app_py_text.delete("1.0", tk.END)
        self.app_py_text.insert(tk.END, app_py_code)
        self._update_progress_bar(self.gen_progress, 50)
        self.db_manager.log_progress(task, 50, "Generated app.py")

        # Simulate generating App.svelte.
        time.sleep(0.5)  # Simulated delay.
        app_svelte_code = (
            f"<!-- Generated App.svelte code -->\n"
            f"<!-- Template used: {self.template_var.get()} -->\n\n" +
            template_content
        )
        self.app_svelte_text.delete("1.0", tk.END)
        self.app_svelte_text.insert(tk.END, app_svelte_code)
        self._update_progress_bar(self.gen_progress, 100)
        self.db_manager.log_progress(task, 100, "Generated App.svelte")
        self.log("Code generation completed.")

    # -------------------------------------------------------------------------
    # Replace Files Tab Methods (with progress logging)
    # -------------------------------------------------------------------------
    def _get_models(self):
        return sorted([d.name for d in Path('.').iterdir() if d.is_dir() and d.name in CONFIG["allowed_models"]])

    def _get_apps_for_model(self, model: str):
        model_dir = Path('.') / model
        if model_dir.exists():
            return sorted([d.name for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")])
        return []

    def _update_app_dropdown(self, event=None):
        model = self.model_var.get()
        apps = self._get_apps_for_model(model)
        self.app_dropdown['values'] = apps
        self.app_var.set(apps[0] if apps else "")

    def replace_file(self, filename: str, new_content: str):
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
            self._update_progress_bar(self.gen_progress, 100)
            self.db_manager.log_progress(task, 100, f"Replaced content of {target_file}")
            self.log(f"Replaced content of {target_file}")
        except Exception as e:
            self.log(f"Failed to replace file content: {e}", error=True)
            self.db_manager.log_progress(task, 0, f"Error: {e}")

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------
    def _update_progress_bar(self, progress_bar: ttk.Progressbar, value: int):
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


if __name__ == "__main__":
    app = AssistantUI()
    app.mainloop()
