import time
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Global variables to hold our Selenium driver and the user-selected CSS selector.
driver = None
selected_textarea_selector = None

# --- Selenium / ChatGPT Functions ---

def setup_driver():
    global driver
    # Set up Firefox Developer Edition options.
    options = FirefoxOptions()
    # *** Adjust the path below to point to your Firefox Developer Edition binary ***
    options.binary_location = "C:\Program Files\Firefox Developer Edition\firefox.exe"
    service = FirefoxService()  # Assumes geckodriver is in your PATH.
    driver = webdriver.Firefox(service=service, options=options)
    driver.get("https://chat.openai.com")
    log_to_ui("Opened ChatGPT. Please log in if required.")
    try:
        # Wait until a textarea is available (i.e. after logging in)
        WebDriverWait(driver, 300).until(
            EC.presence_of_element_located((By.TAG_NAME, "textarea"))
        )
    except Exception as e:
        log_to_ui("Error: Chat input not found. Are you logged in?")
        driver.quit()

def send_message(message):
    """
    Uses the selected text area (if set) or falls back to finding the <textarea> by tag.
    """
    global driver, selected_textarea_selector
    try:
        if selected_textarea_selector:
            textarea = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selected_textarea_selector))
            )
        else:
            textarea = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.TAG_NAME, "textarea"))
            )
        textarea.clear()
        textarea.send_keys(message)
        textarea.send_keys(Keys.ENTER)
        log_to_ui(f"Sent message: {message}")
    except Exception as e:
        log_to_ui(f"Error sending message: {e}")

def wait_for_new_code_block(previous_count, timeout=120):
    """
    Wait until the number of <pre> tags (code blocks) increases beyond previous_count,
    then return the text of the new code block.
    """
    global driver
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "pre")) > previous_count
        )
        time.sleep(2)  # extra wait to let the code block fully render
        code_blocks = driver.find_elements(By.TAG_NAME, "pre")
        return code_blocks[-1].text
    except Exception as e:
        log_to_ui(f"Error waiting for code block: {e}")
        return ""

# --- UI Logging ---

def log_to_ui(message):
    """ Append a log message to the UI log box. """
    timestamp = time.strftime("%H:%M:%S")
    log_box.insert(tk.END, f"[{timestamp}] {message}\n")
    log_box.see(tk.END)

# --- UI Button Callback Functions ---

def on_select_text_area():
    """ Inject JavaScript to let the user click on an element to select the text area. """
    global driver, selected_textarea_selector
    if not driver:
        log_to_ui("Driver not ready.")
        return

    # Inject JS that defines a function to get a unique CSS selector and records the clicked element.
    js_code = """
    window.lastClickedSelector = "";
    function getCssSelector(el) {
        if (!(el instanceof Element)) return;
        var path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            var selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
            } else {
                var sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() == selector)
                        nth++;
                }
                if (nth != 1)
                    selector += ":nth-of-type(" + nth + ")";
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(" > ");
    }
    document.addEventListener('click', function(e) {
        window.lastClickedSelector = getCssSelector(e.target);
        // Optionally highlight the element:
        e.target.style.outline = "3px solid red";
    }, { once: true });
    """
    try:
        driver.execute_script(js_code)
        log_to_ui("Please click on the desired text area in the browser.")
    except Exception as e:
        log_to_ui(f"Error injecting JS: {e}")
        return

    # Poll for the variable window.lastClickedSelector
    def poll_for_selector():
        global selected_textarea_selector
        timeout = 60
        start = time.time()
        selector = ""
        while time.time() - start < timeout:
            try:
                selector = driver.execute_script("return window.lastClickedSelector;")
            except Exception as e:
                log_to_ui(f"Error retrieving selector: {e}")
                break
            if selector:
                selected_textarea_selector = selector
                log_to_ui(f"Selected text area: {selector}")
                return
            time.sleep(0.5)
        log_to_ui("Timed out waiting for text area selection.")
    threading.Thread(target=poll_for_selector, daemon=True).start()

def on_send_prompt_template():
    """ Read prompt_template.txt and send it as a message. """
    try:
        with open("prompt_template.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read().strip()
        send_message(prompt_template)
    except Exception as e:
        log_to_ui(f"Error reading prompt_template.txt: {e}")

def on_send_text_string():
    """ Read text_string.txt and send it as a message. """
    try:
        with open("text_string.txt", "r", encoding="utf-8") as f:
            text_string = f.read().strip()
        send_message(text_string)
    except Exception as e:
        log_to_ui(f"Error reading text_string.txt: {e}")

def on_send_continue():
    """ Send the word 'continue' as a message. """
    send_message("continue")

def on_save_code_block(filename):
    """
    Wait for a new code block (by counting existing <pre> elements),
    then save the code block text to the given filename.
    """
    def worker():
        try:
            prev_count = len(driver.find_elements(By.TAG_NAME, "pre"))
            log_to_ui("Waiting for a new code block from ChatGPT...")
            code_block = wait_for_new_code_block(prev_count)
            if code_block:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(code_block)
                log_to_ui(f"Saved code block to {filename}")
            else:
                log_to_ui("No code block found.")
        except Exception as e:
            log_to_ui(f"Error saving code block: {e}")
    threading.Thread(target=worker, daemon=True).start()

# --- UI Setup ---

def start_ui():
    global log_box
    root = tk.Tk()
    root.title("ChatGPT Automation Control")

    frame = tk.Frame(root)
    frame.pack(padx=10, pady=10)

    # Buttons for actions:
    btn_select = tk.Button(frame, text="Select Text Area", width=25, command=lambda: threading.Thread(target=on_select_text_area, daemon=True).start())
    btn_select.grid(row=0, column=0, padx=5, pady=5)

    btn_prompt = tk.Button(frame, text="Send Prompt Template", width=25, command=lambda: threading.Thread(target=on_send_prompt_template, daemon=True).start())
    btn_prompt.grid(row=1, column=0, padx=5, pady=5)

    btn_text = tk.Button(frame, text="Send Text String", width=25, command=lambda: threading.Thread(target=on_send_text_string, daemon=True).start())
    btn_text.grid(row=2, column=0, padx=5, pady=5)

    btn_save1 = tk.Button(frame, text="Save Code Block (output1.txt)", width=25, command=lambda: on_save_code_block("output1.txt"))
    btn_save1.grid(row=3, column=0, padx=5, pady=5)

    btn_continue = tk.Button(frame, text="Send 'continue'", width=25, command=lambda: threading.Thread(target=on_send_continue, daemon=True).start())
    btn_continue.grid(row=4, column=0, padx=5, pady=5)

    btn_save2 = tk.Button(frame, text="Save Code Block (output2.txt)", width=25, command=lambda: on_save_code_block("output2.txt"))
    btn_save2.grid(row=5, column=0, padx=5, pady=5)

    btn_exit = tk.Button(frame, text="Exit", width=25, command=lambda: root.destroy())
    btn_exit.grid(row=6, column=0, padx=5, pady=5)

    # Log box (scrolled text)
    log_box = scrolledtext.ScrolledText(root, width=70, height=15)
    log_box.pack(padx=10, pady=10)

    # Start the Tkinter mainloop.
    root.mainloop()

# --- Main ---

def main():
    # Start Selenium in a separate thread so that it can initialize before UI interactions.
    threading.Thread(target=setup_driver, daemon=True).start()
    # Start the UI (this call blocks until the UI is closed)
    start_ui()
    # When the UI is closed, you can optionally quit the browser.
    if driver:
        driver.quit()

if __name__ == "__main__":
    main()
