#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import time

# --- Configuration ---
CONFIG = {
    "presets_dir": Path("zzz_Bot/app_templates"),  # Folder with template files
    "default_template_ext": ".md",
    "allowed_models": {"ChatGPT4o", "ChatGPTo1", "ChatGPTo3", "ClaudeSonnet",
                       "DeepSeek", "Gemini", "Grok", "Llama", "Mixtral", "Qwen"}
}


# --- Main Application ---
class AssistantUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Code Generation Assistant")
        self.geometry("1000x700")
        self._create_widgets()

    def _create_widgets(self):
        # Create a Notebook to separate the workflow into three steps.
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self._create_template_tab()
        self._create_generate_code_tab()
        self._create_replace_files_tab()
        self._create_logging_frame()

    # === TAB 1: Template Selection ===
    def _create_template_tab(self):
        self.template_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.template_tab, text="Template")

        # Frame for template selection
        sel_frame = ttk.Frame(self.template_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(sel_frame, text="Select Template:").pack(side="left")

        self.template_var = tk.StringVar()
        presets = self._get_presets()
        self.template_dropdown = ttk.Combobox(sel_frame, textvariable=self.template_var,
                                              values=presets, state="readonly", width=40)
        if presets:
            self.template_var.set(presets[0])
        self.template_dropdown.pack(side="left", padx=5)

        load_btn = ttk.Button(sel_frame, text="Load Template", command=self.load_template)
        load_btn.pack(side="left", padx=5)

        # Text area for template content
        self.template_text = tk.Text(self.template_tab, wrap="word", height=20)
        self.template_text.pack(fill="both", expand=True, padx=10, pady=5)

    # === TAB 2: Generate Code Files ===
    def _create_generate_code_tab(self):
        self.generate_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.generate_tab, text="Generate Code")

        gen_btn = ttk.Button(self.generate_tab, text="Generate Code", command=self.generate_code)
        gen_btn.pack(pady=5)

        # Frame that holds two code areas side by side.
        code_frame = ttk.Frame(self.generate_tab)
        code_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Left: app.py
        app_py_frame = ttk.LabelFrame(code_frame, text="app.py")
        app_py_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.app_py_text = tk.Text(app_py_frame, wrap="none")
        self.app_py_text.pack(fill="both", expand=True)

        # Right: App.svelte
        app_svelte_frame = ttk.LabelFrame(code_frame, text="App.svelte")
        app_svelte_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.app_svelte_text = tk.Text(app_svelte_frame, wrap="none")
        self.app_svelte_text.pack(fill="both", expand=True)

    # === TAB 3: Replace Files in Model Folders ===
    def _create_replace_files_tab(self):
        self.replace_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.replace_tab, text="Replace Files")

        sel_frame = ttk.Frame(self.replace_tab)
        sel_frame.pack(fill="x", padx=10, pady=5)
        # Model selection
        ttk.Label(sel_frame, text="Select Model:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.model_var = tk.StringVar()
        models = self._get_models()
        self.model_dropdown = ttk.Combobox(sel_frame, textvariable=self.model_var,
                                           values=models, state="readonly", width=30)
        if models:
            self.model_var.set(models[0])
        self.model_dropdown.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.model_dropdown.bind("<<ComboboxSelected>>", self._update_app_dropdown)

        # App folder selection
        ttk.Label(sel_frame, text="Select App:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.app_var = tk.StringVar()
        apps = self._get_apps_for_model(self.model_var.get())
        self.app_dropdown = ttk.Combobox(sel_frame, textvariable=self.app_var,
                                         values=apps, state="readonly", width=30)
        if apps:
            self.app_var.set(apps[0])
        self.app_dropdown.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        # Replacement buttons
        btn_frame = ttk.Frame(self.replace_tab)
        btn_frame.pack(padx=10, pady=5)
        replace_app_py_btn = ttk.Button(btn_frame, text="Replace app.py",
                                        command=lambda: self.replace_file("app.py",
                                                                           self.app_py_text.get("1.0", tk.END)))
        replace_app_svelte_btn = ttk.Button(btn_frame, text="Replace App.svelte",
                                            command=lambda: self.replace_file("App.svelte",
                                                                               self.app_svelte_text.get("1.0", tk.END)))
        replace_app_py_btn.grid(row=0, column=0, padx=5, pady=5)
        replace_app_svelte_btn.grid(row=0, column=1, padx=5, pady=5)

    # === Logging Frame ===
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

    # === Template Tab Methods ===
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

    # === Generate Code Tab Methods ===
    def generate_code(self):
        template_content = self.template_text.get("1.0", tk.END).strip()
        if not template_content:
            self.log("Template is empty. Please load a template first.", error=True)
            return

        # Here you can add your custom code-generation logic.
        # For demo, we prepend a header (which could include substitutions, etc.)
        app_py_code = (
            f"# Generated app.py code\n"
            f"# Template used: {self.template_var.get()}\n\n"
            + template_content
        )
        app_svelte_code = (
            f"<!-- Generated App.svelte code -->\n"
            f"<!-- Template used: {self.template_var.get()} -->\n\n"
            + template_content
        )
        self.app_py_text.delete("1.0", tk.END)
        self.app_py_text.insert(tk.END, app_py_code)
        self.app_svelte_text.delete("1.0", tk.END)
        self.app_svelte_text.insert(tk.END, app_svelte_code)
        self.log("Generated code for app.py and App.svelte")

    # === Replace Files Tab Methods ===
    def _get_models(self):
        # Look for folders in the current directory matching allowed model names.
        return sorted([d.name for d in Path('.').iterdir() if d.is_dir() and d.name in CONFIG["allowed_models"]])

    def _get_apps_for_model(self, model: str):
        model_dir = Path('.') / model
        if model_dir.exists():
            # Look for subdirectories starting with "app"
            return sorted([d.name for d in model_dir.iterdir() if d.is_dir() and d.name.lower().startswith("app")])
        return []

    def _update_app_dropdown(self, event=None):
        model = self.model_var.get()
        apps = self._get_apps_for_model(model)
        self.app_dropdown['values'] = apps
        self.app_var.set(apps[0] if apps else "")

    def replace_file(self, filename: str, new_content: str):
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
        if target_file.exists():
            confirm = messagebox.askyesno("Confirm Replacement",
                                          f"Replace the content of {target_file}?")
            if not confirm:
                self.log("Replacement canceled")
                return
        else:
            confirm = messagebox.askyesno("Confirm Creation",
                                          f"{target_file} does not exist. Create new file?")
            if not confirm:
                self.log("File creation canceled")
                return

        try:
            target_file.write_text(new_content, encoding="utf-8")
            self.log(f"Replaced content of {target_file}")
        except Exception as e:
            self.log(f"Error replacing file content: {str(e)}", error=True)


if __name__ == "__main__":
    app = AssistantUI()
    app.mainloop()
