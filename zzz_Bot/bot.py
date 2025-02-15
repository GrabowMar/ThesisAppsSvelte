#!/usr/bin/env python3
import os
import time
import random
import threading
from queue import Queue
from typing import Optional, Callable

import tkinter as tk
from tkinter import messagebox, scrolledtext

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    WebDriverException,
    TimeoutException
)

from selenium.webdriver.chrome.options import Options as ChromeOptions

# Configuration
REMOTE_DEBUGGING_PORT = 9222  # Port used for remote debugging
USER_DATA_DIR = r"C:\temp\chrome_debug_profile"  # User data directory for the running Chrome instance
DEFAULT_TIMEOUT = 30

class ChatGPTAssistant:
    def __init__(self):
        self.browser: Optional[webdriver.Chrome] = None
        self.session_active = False

    def start_browser_session(self) -> None:
        try:
            # Connect to the existing Chrome session
            options = ChromeOptions()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{REMOTE_DEBUGGING_PORT}")
            self.browser = webdriver.Chrome(options=options)

            # Navigate to ChatGPT (if not already there)
            if "chat.openai.com" not in self.browser.current_url:
                self.browser.get("https://chat.openai.com")

            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            self.session_active = True
            print("Connected to existing Chrome session.")
        except Exception as e:
            print(f"Failed to connect to Chrome session: {e}")

    def submit_prompt(self, message: str) -> bool:
        if not self.session_active or not self.browser:
            print("Session not active")
            return False

        try:
            # Locate the input field and type the message
            input_field = WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "prompt-textarea"))
            )
            input_field.click()
            self._simulate_human_typing(input_field, message)
            self._random_delay_after_typing()
            return True
        except Exception as e:
            print(f"Failed to submit prompt: {e}")
            return False

    def _simulate_human_typing(self, element, text: str):
        actions = ActionChains(self.browser)
        for char in text:
            delay = random.uniform(0.1, 0.3)  # Simulate typing delay
            time.sleep(delay)
            actions.send_keys(char)
        actions.perform()

    def _random_delay_after_typing(self):
        time.sleep(random.uniform(0.5, 2.5))  # Random delay before submitting

    def submit_message(self) -> bool:
        try:
            # Locate and click the submit button
            submit_button = WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='send-button']"))
            )
            submit_button.click()
            return True
        except Exception as e:
            print(f"Error submitting message: {e}")
            return False

    def shutdown(self) -> None:
        try:
            if self.browser:
                self.browser.quit()
                self.session_active = False
                print("Browser session terminated")
        except Exception as e:
            print(f"Error during shutdown: {e}")

class AppInterface:
    def __init__(self, assistant: ChatGPTAssistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.log_display = None
        self._setup_interface()
        self._prepare_close_handling()

    def _setup_interface(self) -> None:
        self.root.title("ChatGPT Assistant")
        self._create_log_section()
        self._build_control_panel()
        self._add_preset_selector()

    def _build_control_panel(self) -> None:
        panel = tk.Frame(self.root)
        panel.pack(padx=10, pady=10)
        actions = [
            ("Start Conversation", self._queue_action(self.assistant.submit_prompt, "Hello World!")),
            ("Use Template", self._queue_action(self._apply_preset)),
            ("Insert Content", self._queue_action(self._insert_text_file)),
            ("Continue Dialogue", self._queue_action(self.assistant.submit_prompt, "Please continue")),
            ("Save Code", self._queue_action(self._save_code)),
            ("End Session", self.root.destroy)
        ]
        for row, (label, action) in enumerate(actions):
            tk.Button(panel, text=label, width=22, command=action)\
              .grid(row=row, column=0, padx=5, pady=5)

    def _add_preset_selector(self) -> None:
        selector_frame = tk.Frame(self.root)
        selector_frame.pack(padx=10, pady=10)
        available_presets = self._find_presets()
        self.preset_choice = tk.StringVar()
        if available_presets:
            self.preset_choice.set(available_presets[0])
        else:
            self.preset_choice.set("No presets available")
            available_presets = ["Create presets first"]
        tk.Label(selector_frame, text="Dialogue Templates:")\
          .grid(row=0, column=0, padx=5)
        tk.OptionMenu(selector_frame, self.preset_choice, *available_presets)\
          .grid(row=0, column=1, padx=5)
        tk.Button(selector_frame, text="Load Template", 
                  command=self._queue_action(self._load_preset))\
          .grid(row=0, column=2, padx=5)

    def _create_log_section(self) -> None:
        self.log_display = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.log_display.pack(padx=10, pady=10)

    def _prepare_close_handling(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._safe_shutdown)

    def _safe_shutdown(self) -> None:
        self.assistant.shutdown()
        self.root.destroy()

    def _queue_action(self, func: Callable, *args) -> Callable:
        def wrapper():
            try:
                func(*args)
            except Exception as e:
                self._show_error(f"Task Error: {e}")
        return wrapper

    def _apply_preset(self) -> None:
        template_path = os.path.join("zzz_Bot", "prompt_template.txt")
        try:
            with open(template_path, encoding="utf-8") as f:
                content = f.read()
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error("Template file not found")

    def _insert_text_file(self) -> None:
        file_path = "text_content.txt"
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error("Content file not found")

    def _load_preset(self) -> None:
        preset_filename = self.preset_choice.get()
        preset_path = os.path.join("dialogue_presets", preset_filename)
        try:
            with open(preset_path, encoding="utf-8") as f:
                content = f.read()
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error(f"Template not found: {preset_path}")

    def _find_presets(self) -> list:
        presets_dir = "zzz_Bot/app_templates"
        try:
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir, exist_ok=True)
                self.update_status("Created templates directory")
            return sorted([
                f for f in os.listdir(presets_dir)
                if os.path.isfile(os.path.join(presets_dir, f)) and f.endswith(".md")
            ])
        except Exception as e:
            self._show_error(f"Template directory error: {e}")
            return []

    def _save_code(self) -> None:
        if not self.assistant.browser:
            self._show_error("No browser session available")
            return
        try:
            time.sleep(1)  # small delay for page updates
            code_elements = self.assistant.browser.find_elements(By.TAG_NAME, "pre")
            if not code_elements:
                self._show_error("No code blocks found")
                return
            recent_code = code_elements[-1].text
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(title="Save Code", defaultextension=".txt")
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(recent_code)
                self.update_status(f"Code saved to {file_path}")
        except Exception as e:
            self._show_error(f"Error saving code: {e}")

    def update_status(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        safe_message = f"[{timestamp}] {message}\n"
        self.log_display.after(0, self._update_log_display, safe_message)

    def _update_log_display(self, message: str) -> None:
        self.log_display.insert(tk.END, message)
        self.log_display.see(tk.END)

    def _show_error(self, message: str) -> None:
        self.update_status(message)
        messagebox.showerror("Operation Failed", message)

    def run(self) -> None:
        self.root.mainloop()

if __name__ == "__main__":
    assistant = ChatGPTAssistant()
    try:
        assistant.start_browser_session()
    except Exception as e:
        print(f"Failed to start browser session: {e}")
    interface = AppInterface(assistant)
    interface.run()