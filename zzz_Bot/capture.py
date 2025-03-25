#!/usr/bin/env python3
import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from pathlib import Path
import re
import threading
import time
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# =============================================================================
# Application Configuration
# =============================================================================
APP_CONFIG = {
    "db_path": "assistant.db",
    "log_file": "bot_prompts.log",
    "window_title": "Web Prompt Capture Bot",
    "window_size": "1000x800"
}

# =============================================================================
# Model Configuration
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
# Logging Setup
# =============================================================================
logger = logging.getLogger("WebPromptBot")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(APP_CONFIG["log_file"])
file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S"))
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# =============================================================================
# Utility Functions
# =============================================================================
def _natural_sort_key(s: str):
    """
    Split string into list of ints and lower-case text for natural sorting,
    so "app2" < "app10".
    """
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]

def natsorted(seq):
    return sorted(seq, key=_natural_sort_key)

# =============================================================================
# Database Client
# =============================================================================
class DatabaseClient:
    """
    Handles all database interactions for web prompts.
    """
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_web_prompts_table()
        logger.info(f"Connected to database: {db_path}")

    def _create_web_prompts_table(self) -> None:
        """Create the web prompts table if it doesn't exist"""
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

    def save_prompt(self, model: str, app: str, prompt_text: str, response_text: str = "") -> None:
        """Save a new prompt to the database"""
        with self.conn:
            self.conn.execute(
                "INSERT INTO web_prompts (model, app, prompt_text, response_text) VALUES (?, ?, ?, ?)",
                (model, app, prompt_text, response_text)
            )
        logger.info(f"Saved new prompt for {model}/{app}")

    def get_prompts(self, limit: int = 100):
        """Get recent prompts from the database"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, model, app, prompt_text, response_text, timestamp FROM web_prompts ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()

    def update_prompt(self, prompt_id: int, model: str, app: str, prompt_text: str, response_text: str) -> None:
        """Update an existing prompt in the database"""
        with self.conn:
            self.conn.execute(
                "UPDATE web_prompts SET model = ?, app = ?, prompt_text = ?, response_text = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?",
                (model, app, prompt_text, response_text, prompt_id)
            )
        logger.info(f"Updated prompt {prompt_id}")

    def delete_prompt(self, prompt_id: int) -> None:
        """Delete a prompt from the database"""
        with self.conn:
            self.conn.execute("DELETE FROM web_prompts WHERE id = ?", (prompt_id,))
        logger.info(f"Deleted prompt {prompt_id}")

    def close(self) -> None:
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

# =============================================================================
# Main GUI Application
# =============================================================================
class WebPromptBot(tk.Tk):
    """Main application for capturing and managing web prompts"""
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_CONFIG["window_title"])
        self.geometry(APP_CONFIG["window_size"])
        self.minsize(800, 600)

        # Initialize database
        self.database = DatabaseClient(APP_CONFIG["db_path"])
        
        # Setup UI
        self._create_ui()
        
        # Load initial data
        self._refresh_prompts_list()
        
        # Initialize status message
        self.status_var.set("Ready to capture prompts")
        
        # Keyboard shortcuts
        self.bind("<Control-v>", lambda e: self._paste_from_clipboard())
        self.bind("<Control-s>", lambda e: self._save_current_prompt())
        self.bind("<Control-n>", lambda e: self._new_prompt())
        
        logger.info("Web Prompt Bot started")

    def _create_ui(self) -> None:
        """Create the application's user interface"""
        # Top frame for controls
        top_frame = ttk.Frame(self)
        top_frame.pack(fill="x", padx=10, pady=5)
        
        # Left side - buttons
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side="left", fill="x", padx=5)
        
        ttk.Button(button_frame, text="Paste from Clipboard", 
                  command=self._paste_from_clipboard).pack(side="left", padx=5)
        ttk.Button(button_frame, text="New Prompt", 
                  command=self._new_prompt).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Save Prompt", 
                  command=self._save_current_prompt).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Delete", 
                  command=self._delete_prompt).pack(side="left", padx=5)
        
        # Right side - Model & App selection
        selector_frame = ttk.Frame(top_frame)
        selector_frame.pack(side="right", fill="x", padx=5)
        
        ttk.Label(selector_frame, text="Model:").pack(side="left", padx=2)
        self.model_var = tk.StringVar()
        models = [model.name for model in AI_MODELS]
        self.model_dropdown = ttk.Combobox(selector_frame, textvariable=self.model_var,
                                         values=models, state="readonly", width=15)
        if models:
            self.model_var.set(models[0])
        self.model_dropdown.pack(side="left", padx=2)
        self.model_dropdown.bind("<<ComboboxSelected>>", self._on_model_selected)
        
        ttk.Label(selector_frame, text="App:").pack(side="left", padx=2)
        self.app_var = tk.StringVar()
        self.app_dropdown = ttk.Combobox(selector_frame, textvariable=self.app_var,
                                       values=[], state="readonly", width=15)
        self.app_dropdown.pack(side="left", padx=2)
        
        # Update app list for initial model
        self._update_app_list()
        
        # Split view - Prompts list on left, editor on right
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - List of prompts
        list_frame = ttk.Frame(paned_window)
        paned_window.add(list_frame, weight=1)
        
        # Search/filter bar
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var)
        self.filter_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())
        
        ttk.Button(filter_frame, text="Clear Filter", 
                  command=self._clear_filter).pack(side="right", padx=2)
        
        # Prompts list
        columns = ("id", "timestamp", "model", "app", "preview")
        self.prompts_list = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.prompts_list.heading("id", text="ID")
        self.prompts_list.heading("timestamp", text="Timestamp")
        self.prompts_list.heading("model", text="Model")
        self.prompts_list.heading("app", text="App")
        self.prompts_list.heading("preview", text="Preview")
        
        self.prompts_list.column("id", width=40, anchor="center")
        self.prompts_list.column("timestamp", width=130)
        self.prompts_list.column("model", width=80)
        self.prompts_list.column("app", width=80)
        self.prompts_list.column("preview", width=200)
        
        # Add scrollbar
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.prompts_list.yview)
        self.prompts_list.configure(yscrollcommand=list_scroll.set)
        
        list_scroll.pack(side="right", fill="y")
        self.prompts_list.pack(fill="both", expand=True, padx=5)
        
        # Bind selection event
        self.prompts_list.bind("<<TreeviewSelect>>", self._on_prompt_selected)
        
        # Right side - Text editors with tabs for prompt and response
        edit_frame = ttk.Frame(paned_window)
        paned_window.add(edit_frame, weight=2)
        
        self.edit_notebook = ttk.Notebook(edit_frame)
        self.edit_notebook.pack(fill="both", expand=True)
        
        # Prompt tab
        prompt_frame = ttk.Frame(self.edit_notebook)
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, wrap="word")
        self.prompt_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.edit_notebook.add(prompt_frame, text="Prompt")
        
        # Response tab
        response_frame = ttk.Frame(self.edit_notebook)
        self.response_text = scrolledtext.ScrolledText(response_frame, wrap="word")
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.edit_notebook.add(response_frame, text="Response (Optional)")
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

    def _update_app_list(self) -> None:
        """Update the app dropdown based on selected model"""
        model = self.model_var.get()
        model_dir = Path(".") / model
        
        apps = []
        if model_dir.exists():
            app_dirs = [d for d in model_dir.iterdir() 
                      if d.is_dir() and d.name.lower().startswith("app")]
            apps = natsorted([d.name for d in app_dirs])
        
        self.app_dropdown["values"] = apps
        if apps:
            self.app_var.set(apps[0])
        else:
            self.app_var.set("")

    def _on_model_selected(self, event=None) -> None:
        """Handle model selection and update app list"""
        self._update_app_list()

    def _refresh_prompts_list(self) -> None:
        """Refresh the list of prompts from the database"""
        # Clear existing items
        for item in self.prompts_list.get_children():
            self.prompts_list.delete(item)
            
        # Get prompts from database
        prompts = self.database.get_prompts()
        
        # Apply filter if needed
        filter_text = self.filter_var.get().lower()
        
        # Add prompts to list
        for prompt in prompts:
            prompt_id, model, app, prompt_text, response_text, timestamp = prompt
            
            # Apply filter if set
            if filter_text and not (
                filter_text in model.lower() or 
                (app and filter_text in app.lower()) or 
                filter_text in prompt_text.lower()
            ):
                continue
            
            # Create preview by truncating the prompt text
            preview = prompt_text.strip().replace("\n", " ")
            preview = preview if len(preview) <= 50 else preview[:47] + "..."
            
            # Insert into the treeview
            self.prompts_list.insert("", tk.END, values=(
                prompt_id, timestamp, model, app or "", preview
            ))

    def _apply_filter(self) -> None:
        """Apply the filter to the prompts list"""
        self._refresh_prompts_list()
        filter_text = self.filter_var.get()
        if filter_text:
            self.status_var.set(f"Filtered prompts by: '{filter_text}'")
        else:
            self.status_var.set("Showing all prompts")

    def _clear_filter(self) -> None:
        """Clear the filter and show all prompts"""
        self.filter_var.set("")
        self._refresh_prompts_list()
        self.status_var.set("Filter cleared")

    def _on_prompt_selected(self, event=None) -> None:
        """Handle selection of a prompt from the list"""
        selected = self.prompts_list.selection()
        if not selected:
            return
        
        # Get the prompt ID from the selected item
        item = self.prompts_list.item(selected[0])
        prompt_id = item["values"][0]
        
        # Fetch the prompt from the database
        prompts = self.database.get_prompts()
        prompt_data = next((p for p in prompts if p[0] == prompt_id), None)
        
        if not prompt_data:
            return
        
        # Extract prompt data
        _, model, app, prompt_text, response_text, _ = prompt_data
        
        # Update the fields
        self.model_var.set(model)
        self._on_model_selected()  # Update app dropdown
        
        if app and app in self.app_dropdown["values"]:
            self.app_var.set(app)
        
        # Update text areas
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, prompt_text)
        
        self.response_text.delete("1.0", tk.END)
        if response_text:
            self.response_text.insert(tk.END, response_text)
        
        self.status_var.set(f"Loaded prompt {prompt_id}")

    def _paste_from_clipboard(self) -> None:
        """Paste clipboard content to the prompt text area"""
        try:
            content = self.clipboard_get()
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert(tk.END, content)
            self.status_var.set("Content pasted from clipboard")
            
            # Switch to prompt tab if we're not already there
            self.edit_notebook.select(0)
        except Exception as e:
            self.status_var.set(f"Error pasting from clipboard: {e}")
            logger.error(f"Failed to paste from clipboard: {e}")

    def _new_prompt(self) -> None:
        """Create a new prompt (clear fields)"""
        # Clear selection in list
        for selected in self.prompts_list.selection():
            self.prompts_list.selection_remove(selected)
        
        # Clear text areas
        self.prompt_text.delete("1.0", tk.END)
        self.response_text.delete("1.0", tk.END)
        
        # Switch to prompt tab
        self.edit_notebook.select(0)
        
        self.status_var.set("New prompt")

    def _save_current_prompt(self) -> None:
        """Save the current prompt to the database"""
        # Get the content from text widgets
        prompt_text = self.prompt_text.get("1.0", tk.END).strip()
        response_text = self.response_text.get("1.0", tk.END).strip()
        
        # Check if prompt is empty
        if not prompt_text:
            messagebox.showwarning("Empty Prompt", "Cannot save an empty prompt")
            self.status_var.set("Cannot save empty prompt")
            return
        
        # Get model and app
        model = self.model_var.get()
        app = self.app_var.get()
        
        # Check if updating existing prompt
        selected = self.prompts_list.selection()
        
        try:
            if selected:
                # Update existing prompt
                prompt_id = self.prompts_list.item(selected[0])["values"][0]
                self.database.update_prompt(prompt_id, model, app, prompt_text, response_text)
                self.status_var.set(f"Updated prompt {prompt_id}")
                logger.info(f"Updated prompt {prompt_id}")
            else:
                # Create new prompt
                self.database.save_prompt(model, app, prompt_text, response_text)
                self.status_var.set("Saved new prompt")
                logger.info(f"Saved new prompt for {model}/{app}")
            
            # Refresh the prompts list
            self._refresh_prompts_list()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save prompt: {e}")
            self.status_var.set(f"Error saving prompt: {e}")
            logger.error(f"Failed to save prompt: {e}")

    def _delete_prompt(self) -> None:
        """Delete the selected prompt"""
        selected = self.prompts_list.selection()
        if not selected:
            self.status_var.set("No prompt selected to delete")
            return
        
        prompt_id = self.prompts_list.item(selected[0])["values"][0]
        
        if messagebox.askyesno("Confirm Delete", 
                              f"Are you sure you want to delete prompt #{prompt_id}?"):
            try:
                self.database.delete_prompt(prompt_id)
                
                # Clear text areas
                self.prompt_text.delete("1.0", tk.END)
                self.response_text.delete("1.0", tk.END)
                
                # Refresh list
                self._refresh_prompts_list()
                
                self.status_var.set(f"Deleted prompt {prompt_id}")
                logger.info(f"Deleted prompt {prompt_id}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete prompt: {e}")
                self.status_var.set(f"Error deleting prompt: {e}")
                logger.error(f"Failed to delete prompt: {e}")

    def on_closing(self) -> None:
        """Handle application closing"""
        try:
            self.database.close()
            logger.info("Web Prompt Bot shutting down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        self.destroy()

# =============================================================================
# Main Entry
# =============================================================================
if __name__ == "__main__":
    app = WebPromptBot()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()