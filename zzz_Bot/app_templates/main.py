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
import os

# Global variables to hold our Selenium driver and the user-selected CSS selector.
driver = None
selected_textarea_selector = None

def is_driver_valid():
    global driver
    if driver is None:
        return False
    try:
        # Try a simple command that should work if the driver is alive
        driver.current_url
        return True
    except Exception:
        return False
    
print(is_driver_valid())