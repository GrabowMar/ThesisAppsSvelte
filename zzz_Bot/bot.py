#!/usr/bin/env python3
import os
import time
import random
import threading
import tempfile
from pathlib import Path
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

# Use Chrome’s Options and Service classes instead of Firefox’s
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

# =============================================================================
# Configuration
# =============================================================================

# Set the path to your Chrome binary if needed (optional)
CHROME_BINARY_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# Optionally, specify a user data directory (Chrome profile)
PROFILE_PATH = r"C:\Path\To\Chrome\Profile"  # Update with real profile path
# Provide a Chrome extension (.crx) file for ad blocking (update if needed)
EXTENSION_PATH = "uBlock0.crx"  # Use a Chrome-compatible extension file

PRESETS_DIR = Path("dialogue_presets")
DEFAULT_TIMEOUT = 30
RESPONSE_WAIT_LIMIT = 60
RETRY_LIMIT = 3

# Typing simulation (delay per keystroke in seconds)
DEFAULT_TYPING_DELAY_RANGE = (0.1, 0.3)
TYPING_VARIATION = 0.3  # 30% variation

# Window sizes for randomization
RANDOM_WINDOW_SIZES = [(1366, 768), (1440, 900), (1536, 864), (1920, 1080)]

# General configuration settings
GENERAL_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ],
    "window_sizes": RANDOM_WINDOW_SIZES,
    "proxies": [
        'http://188.165.36.156:25051',
        'socks5://69.197.149.234:6665'
    ],
    "search_engines": [
        "https://www.baidu.com/s?wd={query}",
        "https://www.sogou.com/web?query={query}"
    ],
    "typing_speed": (0.1, 0.3),  # seconds per character
    "navigation_depth": (2, 5),
    "behaviour_interval": (3, 8)
}

# Polish-specific configuration settings
POLISH_CONFIG = {
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
    ],
    "accept_language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    "timezone": "Europe/Warsaw",
    "proxies": [
        "185.158.127.53:8080",    # Warsaw proxy
        "193.150.117.12:8000",    # Krakow proxy
        "178.215.228.218:8080"    # Poznan proxy
    ],
    "window_sizes": [
        (1920, 1080), (1600, 900), (1366, 768), (1440, 900)
    ],
    "typing_speed": (0.08, 0.15),  # seconds per character
    "polish_chars": "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
}

# Additional header values for general use
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Chrome/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Chrome/124.0",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:123.0) Gecko/20100101 Chrome/123.0"
]

ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.8",
    "en-AU,en;q=0.7"
]

# =============================================================================
# Core Classes
# =============================================================================

class DialogueAssistant:
    """Core assistant for managing browser sessions and interactions."""
    def __init__(self):
        self.browser: Optional[webdriver.Chrome] = None
        self.action_queue = Queue()
        self.session_active = False
        self.last_activity_time = time.time()

    def start_browser_session(self) -> None:
        """Start a Chrome session with anti-detection preferences."""
        try:
            options = ChromeOptions()
            if CHROME_BINARY_PATH:
                options.binary_location = CHROME_BINARY_PATH

            # Basic anti-detection settings for Chrome:
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(f"--user-agent={random.choice(USER_AGENTS)}")

            # Set language and window size preferences
            options.add_argument(f"--lang={random.choice(ACCEPT_LANGUAGES)}")
            width, height = random.choice(RANDOM_WINDOW_SIZES)
            # Note: we set the window size later via driver.set_window_size()

            if Path(PROFILE_PATH).exists():
                options.add_argument(f"--user-data-dir={PROFILE_PATH}")

            if Path(EXTENSION_PATH).exists():
                options.add_extension(EXTENSION_PATH)

            service = ChromeService(log_path=os.devnull)
            self.browser = webdriver.Chrome(service=service, options=options)

            # Randomize window size and position
            self.browser.set_window_size(width, height)
            self.browser.set_window_position(random.randint(0, 200), random.randint(0, 200))

            # Hide the webdriver property
            self.browser.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )

            self._simulate_pre_activity()

            # Load target page and wait for full load
            self.browser.get("https://chat.openai.com")
            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            self._random_mouse_movement()
            self._monitor_login_status()
            self.session_active = True

        except TimeoutException as te:
            self._process_error(f"Page load timeout: {te}")
        except Exception as e:
            self._process_error(f"Session setup unsuccessful: {e}")

    def _simulate_pre_activity(self):
        """Simulate natural browser actions before actual work."""
        self.browser.get("about:blank")
        time.sleep(random.uniform(1, 3))
        self.browser.execute_script("window.open()")
        self.browser.switch_to.window(self.browser.window_handles[-1])
        time.sleep(random.uniform(0.5, 1.5))
        self.browser.close()
        self.browser.switch_to.window(self.browser.window_handles[0])

    def _random_mouse_movement(self):
        """Simulate human-like mouse movements."""
        try:
            action = ActionChains(self.browser)
            for _ in range(random.randint(3, 5)):
                x_offset = random.randint(-50, 50)
                y_offset = random.randint(-50, 50)
                action.move_by_offset(x_offset, y_offset)
                action.pause(random.uniform(0.1, 0.3))
            action.perform()
        except Exception as e:
            self.update_status(f"Mouse simulation error: {e}")

    def _monitor_login_status(self) -> None:
        """Wait until the user has logged in (or prompt for manual login)."""
        try:
            WebDriverWait(self.browser, 300).until(
                lambda d: d.find_elements(By.ID, "prompt-textarea") or 
                          d.find_elements(By.XPATH, "//button[contains(text(), 'Log in')]")
            )

            if not self.browser.find_elements(By.ID, "prompt-textarea"):
                self.update_status("Please log in manually")
                WebDriverWait(self.browser, 300).until(
                    EC.presence_of_element_located((By.ID, "prompt-textarea"))
                )

            self.update_status("Successfully logged in")
            time.sleep(random.uniform(1, 2))
        except TimeoutException:
            self._process_error("Login timeout - please try again")

    def submit_prompt(self, message: str) -> bool:
        """Submit a prompt to the page simulating human typing."""
        if not self.session_active or not self.browser:
            self._process_error("Session not active")
            return False

        for attempt in range(RETRY_LIMIT):
            try:
                input_field = WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                    EC.element_to_be_clickable((By.ID, "prompt-textarea"))
                )
                input_field.click()
                self._simulate_human_typing(input_field, message)
                self._random_delay_after_typing()
                return True
            except StaleElementReferenceException:
                self.update_status(f"Stale element; retrying ({attempt + 1}/{RETRY_LIMIT})")
                time.sleep(2)
            except Exception as e:
                self.update_status(f"Failed to submit prompt: {e}")
                time.sleep(2)
        return False

    def _simulate_human_typing(self, element, text: str):
        """Type the given text into the element with human-like delays."""
        actions = ActionChains(self.browser)
        delay_range = GENERAL_CONFIG.get("typing_speed", DEFAULT_TYPING_DELAY_RANGE)
        for char in text:
            delay = random.uniform(*delay_range) * random.uniform(1 - TYPING_VARIATION, 1 + TYPING_VARIATION)
            time.sleep(delay)
            # Simulate occasional typos and corrections
            if random.random() < 0.02:
                actions.send_keys(Keys.BACKSPACE)
                time.sleep(random.uniform(0.1, 0.3))
            if char in ",.!?":
                time.sleep(random.uniform(0.2, 0.7))
            actions.send_keys(char)
            if random.random() < 0.03:
                time.sleep(random.uniform(0.5, 1.5))
        actions.perform()

    def _random_delay_after_typing(self):
        """Pause briefly after typing before submitting."""
        time.sleep(random.uniform(0.5, 2.5))
        if random.random() < 0.2:
            self._random_mouse_movement()

    def submit_message(self) -> bool:
        """Click the submit button to send the prompt."""
        try:
            submit_button = WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='send-button']"))
            )
            submit_button.click()
            self._wait_for_response()
            return True
        except Exception as e:
            self.update_status(f"Error submitting message: {e}")
            return False

    def _wait_for_response(self) -> None:
        """Wait for the response to be generated while simulating activity."""
        try:
            if random.random() < 0.7:
                self.browser.execute_script(f"window.scrollBy(0, {random.randint(50, 200)})")
            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until_not(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Stop generating')]"))
            )
            time.sleep(random.uniform(1, 3))
        except TimeoutException:
            self.update_status("Warning: Response completion not confirmed")

    def save_code_block(self, filename: str) -> bool:
        """Save the most recent code block from the page to a file."""
        try:
            time.sleep(random.uniform(0.5, 1.5))
            code_sections = WebDriverWait(self.browser, RESPONSE_WAIT_LIMIT).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "pre"))
            )
            if not code_sections:
                self.update_status("No code fragments available")
                return False
            recent_code = code_sections[-1].text
            Path(filename).write_text(recent_code, encoding='utf-8')
            self.update_status(f"Saved content to {filename}")
            return True
        except Exception as e:
            self.update_status(f"Preservation error: {e}")
            return False

    def shutdown(self) -> None:
        """Terminate the browser session cleanly."""
        try:
            if self.browser:
                self.browser.quit()
                self.session_active = False
                self.update_status("Browser session terminated")
        except Exception as e:
            self.update_status(f"Error during shutdown: {e}")

    def update_status(self, message: str) -> None:
        """Basic logging to console."""
        print(f"[System] {message}")

    def _process_error(self, message: str) -> None:
        self.update_status(f"Error: {message}")
        raise RuntimeError(message)


class EnhancedDialogueAssistant(DialogueAssistant):
    """An assistant with extra anti-detection and organic behavior measures."""
    def start_browser_session(self) -> None:
        try:
            options = ChromeOptions()
            if CHROME_BINARY_PATH:
                options.binary_location = CHROME_BINARY_PATH

            # Rotate user agent and Accept-Language header
            random_user_agent = random.choice(USER_AGENTS)
            options.add_argument(f"--user-agent={random_user_agent}")
            random_accept_language = random.choice(ACCEPT_LANGUAGES)
            options.add_argument(f"--lang={random_accept_language}")

            # Extra anti-detection settings for Chrome
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-infobars")
            options.add_argument("--start-maximized")

            # Randomize window dimensions (set later via driver.set_window_size)
            width, height = random.choice(RANDOM_WINDOW_SIZES)

            if Path(PROFILE_PATH).exists():
                options.add_argument(f"--user-data-dir={PROFILE_PATH}")

            if Path(EXTENSION_PATH).exists():
                options.add_extension(EXTENSION_PATH)

            service = ChromeService(log_path=os.devnull)
            self.browser = webdriver.Chrome(service=service, options=options)

            # Randomize window position and size
            self.browser.set_window_size(width, height)
            self.browser.set_window_position(random.randint(0, 200), random.randint(0, 200))

            # Mask WebDriver flag
            self.browser.execute_cdp_cmd(
                'Page.addScriptToEvaluateOnNewDocument',
                {'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )

            self._simulate_pre_activity()

            # Load ChatGPT and wait until fully loaded
            self.browser.get("https://chat.openai.com")
            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(self.browser, DEFAULT_TIMEOUT).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self._random_mouse_movement()
            self._monitor_login_status()
            self.session_active = True

        except Exception as e:
            self._process_error(f"Session initialization failed: {e}")

    def _mask_browser_identity(self):
        """Advanced fingerprint masking (not currently invoked)."""
        size = self.browser.get_window_size()
        width = size.get("width", 1024)
        height = size.get("height", 768)
        script = f"""
            Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
            Object.defineProperty(navigator, 'languages', {{get: () => ['zh-CN', 'zh', 'en-US', 'en']}});
            Object.defineProperty(window, 'chrome', {{get: () => undefined}});
            Object.defineProperty(navigator, 'deviceMemory', {{value: {random.choice([4, 6, 8])}}});
            Object.defineProperty(window.screen, 'availWidth', {{value: {width}}});
            Object.defineProperty(window.screen, 'availHeight', {{value: {height}}});
            Object.defineProperty(window, 'outerWidth', {{value: {width}}});
            Object.defineProperty(window, 'outerHeight', {{value: {height}}});
        """
        try:
            self.browser.execute_script(script)
        except WebDriverException:
            pass

    def _simulate_organic_browser_behavior(self):
        """Simulate organic browsing (e.g. opening/closing tabs and scrolling)."""
        num_tabs = random.randint(1, 3)
        for _ in range(num_tabs):
            self.browser.execute_script("window.open()")
            self.browser.switch_to.window(self.browser.window_handles[-1])
            self.browser.get("about:blank")
            time.sleep(random.uniform(0.5, 1.5))
            if random.random() < 0.5 and len(self.browser.window_handles) > 1:
                self.browser.close()
                self.browser.switch_to.window(self.browser.window_handles[0])
        urls = ["https://google.com", "https://wikipedia.org", "https://github.com"]
        for url in random.sample(urls, 2):
            self.browser.get(url)
            time.sleep(random.uniform(1, 3))
            self._random_mouse_movement()

    def _navigate_organically(self, target_url: str):
        """Simulate human-like navigation before landing on the target URL."""
        steps = random.randint(1, 3)
        intermediate_urls = [
            "https://google.com/search?q=chatgpt",
            "https://wikipedia.org/wiki/Artificial_intelligence",
            "https://github.com/features/copilot"
        ]
        for _ in range(steps):
            self.browser.get(random.choice(intermediate_urls))
            time.sleep(random.uniform(2, 5))
            self._random_mouse_movement()
        self.browser.get(target_url)
        time.sleep(random.uniform(1, 3))

    def _random_organic_activity(self):
        """Random organic actions such as scrolling or pausing."""
        actions = [
            self._random_mouse_movement,
            lambda: time.sleep(random.uniform(2, 5))
        ]
        random.shuffle(actions)
        for action in actions[:random.randint(2, 3)]:
            action()
            time.sleep(random.uniform(0.5, 1.5))


# =============================================================================
# GUI Interface
# =============================================================================

class AppInterface:
    """Tkinter-based GUI for managing the assistant's actions."""
    def __init__(self, assistant: EnhancedDialogueAssistant):
        self.assistant = assistant
        self.root = tk.Tk()
        self.log_display = None
        self._setup_interface()
        self._begin_action_processing()

    def _setup_interface(self) -> None:
        self.root.title("Organic Dialogue Assistant")
        self._create_log_section()
        self._build_control_panel()
        self._add_preset_selector()
        self._prepare_close_handling()

    def _build_control_panel(self) -> None:
        panel = tk.Frame(self.root)
        panel.pack(padx=10, pady=10)
        actions = [
            ("Start Conversation", self._queue_action(self.assistant.submit_prompt, "Hello!")),
            ("Use Template", self._queue_action(self._apply_preset)),
            ("Insert Content", self._queue_action(self._insert_text_file)),
            ("Continue Dialogue", self._queue_action(self.assistant.submit_prompt, "Please continue")),
            ("Save Code", self._queue_action(self.assistant.save_code_block, "output.txt")),
            ("End Session", self.root.destroy)
        ]
        for row, (label, action) in enumerate(actions):
            tk.Button(panel, text=label, width=22, command=action).grid(
                row=row, column=0, padx=5, pady=5)

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
        tk.Label(selector_frame, text="Dialogue Templates:").grid(row=0, column=0, padx=5)
        tk.OptionMenu(selector_frame, self.preset_choice, *available_presets).grid(
            row=0, column=1, padx=5)
        tk.Button(selector_frame, text="Load Template",
                  command=self._queue_action(self._load_preset)).grid(row=0, column=2, padx=5)

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
                self.assistant.action_queue.put((func, args))
            except Exception as e:
                self._show_error(f"Task Error: {e}")
        return wrapper

    def _begin_action_processing(self) -> None:
        def processor():
            while True:
                task = self.assistant.action_queue.get()
                if task is None:
                    break
                func, args = task
                try:
                    func(*args)
                except Exception as e:
                    self.update_status(f"Error processing task: {e}")
                self.assistant.action_queue.task_done()
        threading.Thread(target=processor, daemon=True).start()

    def _apply_preset(self) -> None:
        try:
            content = Path("zzz_Bot/prompt_template.txt").read_text(encoding="utf-8")
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error("Template file not found")

    def _insert_text_file(self) -> None:
        try:
            content = Path("text_content.txt").read_text(encoding="utf-8")
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error("Content file not found")

    def _load_preset(self) -> None:
        template_path = PRESETS_DIR / self.preset_choice.get()
        try:
            content = template_path.read_text(encoding="utf-8")
            self.assistant.submit_prompt(content)
        except FileNotFoundError:
            self._show_error(f"Template not found: {template_path}")

    def _find_presets(self) -> list:
        try:
            if not PRESETS_DIR.exists():
                PRESETS_DIR.mkdir(exist_ok=True)
                self.update_status("Created templates directory")
            return sorted([f.name for f in PRESETS_DIR.glob("*.md") if f.is_file()])
        except Exception as e:
            self._show_error(f"Template directory error: {e}")
            return []

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


# =============================================================================
# Stealth and Polish-Specific Drivers/Behavior
# =============================================================================

class StealthDriver:
    """Provides advanced anti-detection features."""
    @staticmethod
    def configure_options(options: ChromeOptions) -> ChromeOptions:
        # Proxy configuration
        proxy = random.choice(GENERAL_CONFIG['proxies'])
        options.add_argument(f"--proxy-server={proxy}")

        # Advanced fingerprint settings and headers
        options.add_argument(f"--user-agent={random.choice(GENERAL_CONFIG['user_agents'])}")
        options.add_argument("--lang=zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Use a temporary user data dir if no profile is provided
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")
        return options

    @staticmethod
    def apply_fingerprint_protection(driver):
        width, height = random.choice(GENERAL_CONFIG['window_sizes'])
        script = f"""
        Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
        Object.defineProperty(navigator, 'plugins', {{get: () => [{{0: {{type: 'application/pdf'}}}}, length: 1]}});
        Object.defineProperty(navigator, 'languages', {{get: () => ['zh-CN', 'zh', 'en-US', 'en']}});
        Object.defineProperty(window, 'chrome', {{get: () => undefined}});
        Object.defineProperty(window.screen, 'width', {{value: {width}}});
        Object.defineProperty(window.screen, 'height', {{value: {height}}});
        Object.defineProperty(window, 'outerWidth', {{value: {width}}});
        Object.defineProperty(window, 'outerHeight', {{value: {height}}});
        """
        try:
            driver.execute_script(script)
        except WebDriverException:
            pass

    @staticmethod
    def bezier_mouse_movement(driver, _element=None):
        """Generate human-like mouse movements using Bezier curves."""
        try:
            action = ActionChains(driver)
            cp1 = (random.randint(-100, 100), random.randint(-100, 100))
            cp2 = (random.randint(-100, 100), random.randint(-100, 100))
            end_point = (random.randint(-50, 50), random.randint(-50, 50))
            points = []
            for t in [i/20 for i in range(21)]:
                x = (1-t)**3 * 0 + 3*(1-t)**2*t * cp1[0] + 3*(1-t)*t**2 * cp2[0] + t**3 * end_point[0]
                y = (1-t)**3 * 0 + 3*(1-t)**2*t * cp1[1] + 3*(1-t)*t**2 * cp2[1] + t**3 * end_point[1]
                points.append((x, y))
            for point in points:
                action.move_by_offset(point[0], point[1])
                action.pause(random.uniform(0.05, 0.2))
            action.perform()
            if random.random() < 0.3:
                action.move_by_offset(-point[0]/4, -point[1]/4)
                action.perform()
        except Exception as e:
            print(f"Mouse simulation error: {e}")


class PolishDriverConfig:
    @staticmethod
    def get_random_profile():
        return {
            "user_agent": random.choice(POLISH_CONFIG["user_agents"]),
            "resolution": random.choice(POLISH_CONFIG["window_sizes"]),
            "timezone": POLISH_CONFIG["timezone"],
            "language": POLISH_CONFIG["accept_language"],
            "proxy": random.choice(POLISH_CONFIG["proxies"]) if POLISH_CONFIG["proxies"] else None
        }


class AntiDetectionChrome:
    """Chrome driver with Polish-specific anti-detection settings."""
    def __init__(self):
        self.profile = PolishDriverConfig.get_random_profile()
        self.driver = self._configure_driver()

    def _configure_driver(self):
        options = ChromeOptions()
        options.add_argument(f"--user-agent={self.profile['user_agent']}")
        options.add_argument(f"--lang={self.profile['language']}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        if self.profile["proxy"]:
            options.add_argument(f"--proxy-server=http://{self.profile['proxy']}")
        service = ChromeService(log_path=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)
        width, height = self.profile["resolution"]
        driver.set_window_size(width, height)
        driver.set_window_position(random.randint(0, 100), random.randint(0, 100))
        self._apply_advanced_protection(driver)
        return driver

    def _apply_advanced_protection(self, driver):
        width, height = self.profile["resolution"]
        protection_script = f"""
        Object.defineProperty(navigator, 'webdriver', {{get: () => undefined}});
        Object.defineProperty(window.screen, 'width', {{value: {width}}});
        Object.defineProperty(window.screen, 'height', {{value: {height}}});
        Object.defineProperty(window, 'outerWidth', {{value: {width}}});
        Object.defineProperty(window, 'outerHeight', {{value: {height}}});
        Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {{
            value: function() {{
                let res = Reflect.apply(Intl.DateTimeFormat.prototype.resolvedOptions, this, arguments);
                res.timeZone = "{self.profile['timezone']}";
                return res;
            }}
        }});
        navigator.getBattery = () => new Promise(resolve => resolve({{
            charging: false,
            chargingTime: Infinity,
            dischargingTime: Math.random() * 10000,
            level: Math.random()
        }}));
        const originalConsole = console.debug.bind(console);
        console.debug = function(...args) {{
            if(args.some(arg => typeof arg === 'string' && arg.includes('webdriver'))) return;
            originalConsole.apply(this, args);
        }};
        """
        try:
            driver.execute_script(protection_script)
        except WebDriverException:
            pass


class PolishBehaviorSimulator:
    """Simulate human behavior typical of Polish users."""
    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def polish_typing(self, element, text):
        element.click()
        for char in text:
            if random.random() < 0.15 and char in POLISH_CONFIG["polish_chars"]:
                self.actions.send_keys(Keys.ALT)
                time.sleep(0.1)
            self.actions.send_keys(char)
            time.sleep(random.uniform(*POLISH_CONFIG["typing_speed"]))
            if random.random() < 0.05:
                self.actions.send_keys(Keys.BACKSPACE)
                time.sleep(0.2)
                self.actions.send_keys(char)
        self.actions.perform()

    def local_navigation_pattern(self):
        """Placeholder for local Polish site navigation."""
        pass

    def _random_interaction(self):
        actions = [
            self._scroll_behavior,
            self._cookie_acceptance,
            self._random_link_click
        ]
        random.shuffle(actions)
        for action in actions[:2]:
            action()

    def _scroll_behavior(self):
        for _ in range(random.randint(3, 5)):
            self.driver.execute_script(f"window.scrollBy(0, {random.randint(300, 700)})")
            time.sleep(random.uniform(0.5, 1.5))

    def _cookie_acceptance(self):
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, 
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'akceptuj')]"
                ))
            )
            cookie_button.click()
            time.sleep(1)
        except Exception:
            pass

    def _random_link_click(self):
        try:
            links = self.driver.find_elements(By.TAG_NAME, "a")
            if links:
                random.choice(links).click()
                time.sleep(random.uniform(1, 3))
        except Exception:
            pass


class PolishAutomationSuite:
    """A high-level automation flow using Polish-specific behavior."""
    def __init__(self):
        self.browser = AntiDetectionChrome().driver
        self.behavior = PolishBehaviorSimulator(self.browser)

    def run_flow(self, target_url):
        try:
            self.behavior.local_navigation_pattern()
            self.browser.get(target_url)
            # Additional human-like interactions can be added here.
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.browser.quit()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    assistant = EnhancedDialogueAssistant()
    try:
        assistant.start_browser_session()
    except Exception as e:
        print(f"Failed to start browser session: {e}")
    interface = AppInterface(assistant)
    interface.run()
