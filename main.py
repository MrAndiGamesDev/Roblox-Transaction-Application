import os
import json
import asyncio
import aiohttp
import platform
import pytz
import subprocess
import urllib.request
import sys
import time
from tkinter import *
from tkinter import ttk
from tkinter import font
from PIL import ImageTk, Image 
from datetime import datetime
from dotenv import load_dotenv
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox
from robloxapp import RobloxMonitorApp
from login import LoginWindow

# Load environment variables
load_dotenv()

# Configuration (initially empty)
DISCORD_WEBHOOK_URL = ""
USERID = ""
COOKIES = {}

TRANSACTION_API_URL = ""
CURRENCY_API_URL = ""

# ICON URLS
SYSTEM = platform.system()

UPDATE_INTERVAL = 60 # Monitor interval

TIMEZONE = pytz.timezone("America/New_York") # Default timezone
SHUTDOWN_FLAG = False # Graceful shutdown flag

# Define the hidden directory path based on the operating system
HOME_DIR = os.path.expanduser("~")

def show_popup(message, title="Error"):
    """Display a custom popup with the specified message using PyQt5."""
    app = QApplication([]) # Initializes the application
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information) # Change the icon if desired
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec_()

def set_hidden_attribute(path):
    """Set the hidden attribute on a file or directory."""
    if not os.path.exists(path):
        show_popup(f"The specified path does not exist: {path}")
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    try:
        if SYSTEM == "Windows":
            # Use the `attrib` command to set the hidden attribute
            subprocess.run(["attrib", "+H", path], check=True)
        else:
            show_popup(f"Unsupported operating system: {SYSTEM}")
            raise RuntimeError(f"Unsupported operating system: {SYSTEM}")
    except Exception as e:
        show_popup(f"An error occurred while setting the hidden attribute: {e}")
        raise RuntimeError(f"An error occurred while setting the hidden attribute: {e}")

def ensure_hidden_directory_exists(directory):
    """Ensure the hidden directory exists and set its attribute."""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            set_hidden_attribute(directory)
    except Exception as e:
        show_popup(f"Error creating hidden directory: {e}")
        raise RuntimeError(f"Error creating hidden directory: {e}")

if SYSTEM == "Windows":
    APPDATA_DIR = os.path.join(HOME_DIR, "AppData", "Roaming", "HiddenRobux")
    ensure_hidden_directory_exists(APPDATA_DIR)
else:
    show_popup("Unsupported operating system")

def download_icon():
    """Download the icon to the AppData directory and set it hidden."""
    icon_path = os.path.join(APPDATA_DIR, "robux_icon.png")
    ensure_hidden_directory_exists(APPDATA_DIR)

    # Check if the icon already exists
    if not os.path.exists(icon_path):
        urllib.request.urlretrieve(ICON_URL, icon_path)
        set_hidden_attribute(icon_path)

    return icon_path

def get_hidden_file_path(filename):
    """Return the path for a hidden file in the AppData directory."""
    hidden_file_path = os.path.join(APPDATA_DIR, filename)
    ensure_hidden_directory_exists(APPDATA_DIR)
    return hidden_file_path

# Modify paths for storing JSON files in hidden directory
TRANSACTION_DATA_PATH = get_hidden_file_path("transaction_data.json")
ROBUX_BALANCE_PATH = get_hidden_file_path("robux_balance.json")

def create_window():
    w = Tk()
    width_of_window = 427
    height_of_window = 250
    screen_width = w.winfo_screenwidth()
    screen_height = w.winfo_screenheight()
    x_coordinate = (screen_width / 2) - (width_of_window / 2)
    y_coordinate = (screen_height / 2) - (height_of_window / 2)
    w.geometry("%dx%d+%d+%d" % (width_of_window, height_of_window, x_coordinate, y_coordinate))
    w.overrideredirect(1) # for hiding titlebar

    # Set app icon
    icon_path = download_icon() # Download the image
    img = ImageTk.PhotoImage(Image.open(icon_path))
    w.iconphoto(False, img)
    return w

def create_labels(w):
    Frame(w, width=427, height=250, bg='#272727').place(x=0, y=0)
    label1 = Label(w, text='Robux Monitor', fg='white', bg='#272727')
    label1.configure(font=("Game Of Squids", 24, "bold"))
    label1.place(relx=0.5, rely=0.3, anchor=CENTER) # Center the label

    label2 = Label(w, text='Loading...', fg='white', bg='#272727')
    label2.configure(font=("Game Of Squids", 11))
    label2.place(x=10, y=215)

def animate(w, image_a, image_b):
    positions = [(180, 145), (200, 145), (220, 145), (240, 145)]
    forthrange = 4
    
    for _ in range(2): # 2 loops to last around 5 seconds
        for i in range(forthrange):
            for j in range(forthrange):
                img = image_a if i == j else image_b
                Label(w, image=img, border=0, relief=SUNKEN).place(x=positions[j][0], y=positions[j][1])
            w.update_idletasks()
            time.sleep(0.5)

def show_splash_screen():
    w = create_window()
    create_labels(w)

    image_urls = [
        'https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/c1.png',
        'https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/c2.png'
    ]
    
    image_paths = [
        os.path.join(APPDATA_DIR, 'c1.png'),
        os.path.join(APPDATA_DIR, 'c2.png')
    ]
    
    for url, path in zip(image_urls, image_paths):
        if not os.path.exists(path):
            urllib.request.urlretrieve(url, path)
    
    images = [ImageTk.PhotoImage(Image.open(path)) for path in image_paths]

    # Add progress bar
    progress = ttk.Progressbar(w, orient=HORIZONTAL, length=400, mode='determinate')
    progress.place(relx=0.5, rely=0.8, anchor=CENTER)
    
    for i in range(100):
        w.update_idletasks()
        progress['value'] += 1
        time.sleep(0.05) # Adjust the sleep time to control the speed of the progress bar

    animate(w, images[0], images[1])
    w.destroy() # Close the Tkinter window after animation

def main():
    # Show a popup when the app is started
    show_popup("Just a quick note if the api is having issue or not sending webhooks that could be roblox's end or it could be that we published somthing thats buggy", title="NOTE")
    show_splash_screen()
    app = QtWidgets.QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    app.exec_()

if __name__ == "__main__":
    main()