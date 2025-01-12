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
from tkinter import font
from PIL import ImageTk, Image 
from datetime import datetime
from dotenv import load_dotenv
from PyQt5.QtCore import QTimer, Qt
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMessageBox
from alive_progress import alive_bar

# Load environment variables
load_dotenv()

# Configuration (initially empty)
DISCORD_WEBHOOK_URL = ""
USERID = ""
COOKIES = {}

TRANSACTION_API_URL = ""
CURRENCY_API_URL = ""

# ICON URLS
icon_url = "https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/Robux.png"
AVATAR_URL = "" # Custom icon for Discord notification

VERSION = "V0.6.8"

SETUSERNAME = "anything"
SETPASSWORD = "anything2"

system = platform.system()

UPDATEEVERY = 60  # Monitor interval

TIMEZONE = pytz.timezone("America/New_York")  # Default timezone
shutdown_flag = False  # Graceful shutdown flag

# Define the hidden directory path based on the operating system
home_dir = os.path.expanduser("~")

def show_popup(message, title="Error"):
    """Display a custom popup with the specified message using PyQt5."""
    app = QApplication([])  # Initializes the application
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Information)  # Change the icon if desired
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec_()

def set_hidden_attribute(path):
    """Set the hidden attribute on a file or directory."""
    if not os.path.exists(path):
        show_popup(f"The specified path does not exist: {path}")
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    try:
        if system == "Windows":
            # Use the `attrib` command to set the hidden attribute
            subprocess.run(["attrib", "+H", path], check=True)
        else:
            show_popup(f"Unsupported operating system: {system}")
            raise RuntimeError(f"Unsupported operating system: {system}")
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

if system == "Windows":
    appdata_dir = os.path.join(home_dir, "AppData", "Roaming", "HiddenRobux")
    ensure_hidden_directory_exists(appdata_dir)
else:
    show_popup("Unsupported operating system")

def download_icon():
    """Download the icon to the AppData directory and set it hidden."""
    icon_path = os.path.join(appdata_dir, "robux_icon.png")
    ensure_hidden_directory_exists(appdata_dir)

    # Check if the icon already exists
    if not os.path.exists(icon_path):
        urllib.request.urlretrieve(icon_url, icon_path)
        set_hidden_attribute(icon_path)

    return icon_path

def get_hidden_file_path(filename):
    """Return the path for a hidden file in the AppData directory."""
    hidden_file_path = os.path.join(appdata_dir, filename)
    ensure_hidden_directory_exists(appdata_dir)
    return hidden_file_path

# Modify paths for storing JSON files in hidden directory
TRANSACTION_DATA_PATH = get_hidden_file_path("transaction_data.json")
ROBUX_BALANCE_PATH = get_hidden_file_path("robux_balance.json")

class RobloxMonitorApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.discord_webhook_url = ""
        self.user_id = ""
        self.cookies = {}
        self.transaction_api_url = ""
        self.currency_api_url = ""
        self.timezone = TIMEZONE
        self.shutdown_flag = False
        self.last_transaction_data = self.load_json_data(TRANSACTION_DATA_PATH, {})
        self.last_robux_balance = self.load_json_data(ROBUX_BALANCE_PATH, {"robux": 0})

        self.init_ui()

    def init_ui(self):
        """Set up the UI elements."""
        self.setWindowTitle(f'Welcome To Roblox Transaction Monitor {VERSION}')
        self.setGeometry(200, 200, 600, 400)
        self.setFixedSize(600, 500)

        # Set app icon from GitHub image URL or local file
        icon_path = download_icon()  # Download the image
        app_icon = QtGui.QIcon(icon_path)  # Load the icon from the downloaded image
        self.setWindowIcon(app_icon)  # Set the window icon

        layout = QtWidgets.QVBoxLayout()

        self.creditlabel = QtWidgets.QLabel("Roblox Transaction Monitoring App", self)
        layout.addWidget(self.creditlabel)

        self.robux_balance_label = QtWidgets.QLabel("Current Robux Balance: 0", self)
        layout.addWidget(self.robux_balance_label)

        # GUI Logs with Credits
        self.gui_logs = QtWidgets.QTextEdit(self)
        self.gui_logs.setReadOnly(True)
        self.gui_logs.setStyleSheet("""
            border-radius: 10px;  /* Set corner radius */
            border: 2px solid #808080;
            background-color: #f9f9f9;  /* Optional: Add a subtle background color */
            padding: 5px;  /* Optional: Add padding for better text alignment */
        """)
        self.gui_logs.setFixedHeight(150)  # Adjust height to make it larger
        layout.addWidget(self.gui_logs)

        # Add credits to the logs
        self.add_credits_to_logs()

        self.discord_webhook_username_input = QtWidgets.QLineEdit(self)
        self.discord_webhook_username_input.setPlaceholderText("Discord Webhook Username")
        self.discord_webhook_username_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.discord_webhook_username_input)

        self.discord_webhook_input = QtWidgets.QLineEdit(self)
        self.discord_webhook_input.setPlaceholderText("Discord Webhook URL")
        self.discord_webhook_input.setEchoMode(QtWidgets.QLineEdit.Password)  # Censor input
        self.discord_webhook_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.discord_webhook_input)

        self.image_url = QtWidgets.QLineEdit(self)
        self.image_url.setPlaceholderText("Any Image URL")
        self.image_url.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.image_url)

        self.user_id_input = QtWidgets.QLineEdit(self)
        self.user_id_input.setPlaceholderText("Roblox User ID")
        self.user_id_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.user_id_input)

        self.roblox_cookies_input = QtWidgets.QLineEdit(self)
        self.roblox_cookies_input.setPlaceholderText(".ROBLOSECURITY Cookie Here")
        self.roblox_cookies_input.setEchoMode(QtWidgets.QLineEdit.Password)  # Censor input
        self.roblox_cookies_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.roblox_cookies_input)

        # Timezone dropdown menu
        self.timezone_dropdown = QtWidgets.QComboBox(self)
        self.timezone_dropdown.addItems([
            "UTC",
            # North America
            "America/New_York", 
            "America/Chicago", 
            "America/Denver", 
            "America/Los_Angeles", 
            "America/Toronto", 
            "America/Vancouver", 
            "America/Phoenix",
            "America/Anchorage",
            "America/Halifax",
            "America/Mexico_City", 
            "America/Sao_Paulo", 
            "America/Argentina/Buenos_Aires", 
            # Europe
            "Europe/London", 
            "Europe/Berlin", 
            "Europe/Paris", 
            "Europe/Madrid", 
            "Europe/Rome",
            "Europe/Athens", 
            "Europe/Moscow", 
            "Europe/Amsterdam", 
            "Europe/Zurich", 
            "Europe/Stockholm", 
            "Europe/Dublin", 
            # Asia
            "Asia/Dubai", 
            "Asia/Tokyo", 
            "Asia/Shanghai", 
            "Asia/Singapore", 
            "Asia/Kolkata", 
            "Asia/Seoul", 
            "Asia/Bangkok", 
            "Asia/Manila", 
            "Asia/Hong_Kong", 
            "Asia/Jakarta", 
            "Asia/Karachi", 
            "Asia/Tehran", 
            "Asia/Beirut", 
            "Asia/Riyadh", 
            "Asia/Kathmandu", 
            # Oceania
            "Australia/Sydney", 
            "Australia/Melbourne", 
            "Australia/Brisbane", 
            "Australia/Perth", 
            "Pacific/Auckland", 
            "Pacific/Fiji", 
            "Pacific/Tahiti",
            # Pacific Islands
            "Pacific/Honolulu", 
            "Pacific/Guam", 
            "Pacific/Samoa", 
            # Africa
            "Africa/Johannesburg", 
            "Africa/Nairobi", 
            "Africa/Cairo", 
            "Africa/Lagos", 
            "Africa/Accra", 
            "Africa/Algiers", 
            "Africa/Casablanca", 
            # Middle East
            "Asia/Jerusalem",
            "Asia/Baghdad", 
            "Asia/Istanbul",
            # Additional timezones
            "Asia/Almaty", 
            "Asia/Manila", 
            "Asia/Colombo", 
            "Asia/Karachi", 
            "Asia/Kathmandu", 
            "Africa/Abidjan", 
            "Africa/Porto-Novo", 
            "Europe/Prague", 
            "Europe/Oslo", 
            "Europe/Warsaw", 
            "Europe/Sofia", 
            "Europe/Belgrade", 
            "Europe/Zagreb",
            "Europe/Chisinau", 
            "Europe/Skopje",
            "Europe/Tirane",
            "Pacific/Apia", 
            "Pacific/Pago_Pago", 
            "Pacific/Majuro",
            "Pacific/Nauru", 
            "Pacific/Wallis", 
            "Pacific/Efate"
        ])
        self.timezone_dropdown.setStyleSheet("""
                border-radius: 7px;
                border: 2px solid #808080;
        """)
        layout.addWidget(self.timezone_dropdown)

        # Buttons
        self.start_button = QtWidgets.QPushButton('Start Monitoring', self)
        self.start_button.clicked.connect(self.start_monitoring)
        self.start_button.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        self.start_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.start_button)

        # Set layout
        self.setLayout(layout)

    def add_credits_to_logs(self):
        """Add credits to the GUI logs."""
        credits_text = (
            "Credits:\n"
            "Komas19 (For Sending Me This Source Code)\n"
            "MrAndi Scripted (For Modifing The Source Code To Make An Gui Application)\n"
            "Developed Using: Frameworks (Written In Python)\n"
        )
        self.gui_logs.append(credits_text)

    def load_json_data(self, filepath, default_data):
        """Load data from a JSON file."""
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                return json.load(file)
        return default_data

    def save_json_data(self, filepath, data):
        """Save data to a JSON file."""
        with open(filepath, 'w') as file:
            json.dump(data, file, indent=4)

    async def fetch_avatar_thumbnail(self, user_id):
        """Fetches the avatar thumbnail for a given user from Roblox's API."""
        avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=150x150&format=Png"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data'][0]['imageUrl']  # Returns the image URL
                else:
                    return None  # If the request fails

    def get_current_time(self, timezone=None):
        """Get the current time in the specified timezone (12-hour format)."""
        tz = timezone or self.get_selected_timezone()
        return datetime.now(tz).strftime('%m/%d/%Y %I:%M:%S %p')

    def get_selected_timezone(self):
        """Get the selected timezone from the dropdown."""
        selected_timezone = self.timezone_dropdown.currentText()
        return pytz.timezone(selected_timezone)

    async def send_discord_notification(self, embed: dict, avatar_url: str = None):
        """Send a notification to the Discord webhook."""
        USERNAMES = self.discord_webhook_username_input.text()  # Assuming this is a GUI input element
        IMAGE_URL = self.image_url.text()  # Assuming this is a GUI input element
        payload = {
            "embeds": [embed],
            "username": USERNAMES,
            "avatar_url": IMAGE_URL
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.discord_webhook_url, json=payload, timeout=30) as response:
                    response.raise_for_status()
                    print("Sent Discord notification successfully.")
            except aiohttp.ClientError as e:
                print(f"Error sending Discord notification: {e}")

    async def send_discord_notification_for_changes(self, title: str, description: str, changes: dict, footer: str, avatar_url: str):
        """Send a notification for changes detected in transaction data."""
        fields = [{"name": key, "value": f"**{old}** → **{new}**", "inline": False} for key, (old, new) in changes.items()]
        
        # Get the current time in the selected timezone
        current_time_in_timezone = self.get_current_time(self.get_selected_timezone())

        embed = {
            "title": title,
            "description": description,
            "fields": fields,
            "color": 720640,
            "footer": {"text": f"{footer} | Timezone: {self.get_selected_timezone().zone} | Time: {current_time_in_timezone}"}
        }
        
        await self.send_discord_notification(embed, avatar_url)

    async def fetch_data(self, url: str):
        """Fetch data from the provided URL."""
        retries = 3
        async with aiohttp.ClientSession() as session:
            for _ in range(retries):
                try:
                    async with session.get(url, cookies=self.cookies, timeout=30) as response:
                        response.raise_for_status()
                        return await response.json()
                except aiohttp.ClientError as e:
                    print(f"Failed to fetch data from {url}: {e}")
                    await asyncio.sleep(5)
        return None

    async def fetch_transaction_data(self):
        """Fetch transaction data."""
        return await self.fetch_data(self.transaction_api_url)

    async def fetch_robux_balance(self):
        """Fetch the current Robux balance."""
        response = await self.fetch_data(self.currency_api_url)
        return response.get("robux", 0) if response else 0

    async def monitor(self):
        """Monitor Roblox transaction and Robux data for changes."""
        iteration_count = 0
        USER_ID = self.user_id_input.text()  # Replace with actual user ID for avatar
        AVATAR_URL = await self.fetch_avatar_thumbnail(USER_ID)

        with alive_bar(title="Monitoring Roblox Data", spinner="dots_waves") as bar:
            while not self.shutdown_flag:
                iteration_count += 1

                current_transaction_data, current_robux_balance = await asyncio.gather(
                    self.fetch_transaction_data(),
                    self.fetch_robux_balance()
                )

                self.robux_balance_label.setText(f"Current Robux Balance: {current_robux_balance}")

                if current_transaction_data:
                    changes = {
                        key: (self.last_transaction_data.get(key, 0), current_transaction_data[key])
                        for key in current_transaction_data if current_transaction_data[key] != self.last_transaction_data.get(key, 0)
                    }

                    if changes:
                        await self.send_discord_notification_for_changes(
                            "\U0001F514 Roblox Transaction Data Changed!",
                            f"Changes detected at {self.get_current_time()}",
                            changes,
                            "Fetched From Roblox's API",
                            avatar_url=AVATAR_URL  # Adding the avatar to the notification
                        )
                        self.last_transaction_data.update(current_transaction_data)
                        self.save_json_data(TRANSACTION_DATA_PATH, self.last_transaction_data)

                robux_change = current_robux_balance - self.last_robux_balance['robux']
                if robux_change != 0:
                    color = 0x00FF00 if robux_change > 0 else 0xFF0000  # Green for gain, Red for spent
                    change_type = "gained" if robux_change > 0 else "spent"
                    await self.send_discord_notification({
                        "title": "\U0001F4B8 Robux Balance Update",
                        "description": f"You have **{change_type}** Robux.",
                        "fields": [
                            {"name": "Previous Balance", "value": f"**{self.last_robux_balance['robux']}**", "inline": True},
                            {"name": "Current Balance", "value": f"**{current_robux_balance}**", "inline": True},
                            {"name": "Change", "value": f"**{'+' if robux_change > 0 else ''}{robux_change}**", "inline": True}
                        ],
                        "color": color,
                        "footer": {"text": f"Change detected at {self.get_current_time()}"},
                        "thumbnail": {"url": AVATAR_URL},  # Add Roblox icon as a thumbnail
                    })
                    self.last_robux_balance['robux'] = current_robux_balance
                    self.save_json_data(ROBUX_BALANCE_PATH, self.last_robux_balance)

                bar()

                await asyncio.sleep(UPDATEEVERY)

    async def delay_monitor_start(self, delay_seconds: int):
        """Adds a delay before starting monitoring."""
        print(f"Delaying start for {delay_seconds} seconds...")
        await asyncio.sleep(delay_seconds)  # Non-blocking delay

    def _start_async_monitoring_with_delay(self):
        """Initialize and start the async loop for monitoring with a delay."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Set the delay time in seconds
            delay_seconds = 3  # Adjust this value to change the delay duration
            loop.run_until_complete(self.delay_monitor_start(delay_seconds))
            
            # Run the monitor after the delay
            loop.run_in_executor(None, lambda: loop.run_until_complete(self.monitor()))
            print(f"Monitoring started after {delay_seconds} second delay")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Monitoring Error', f"An error occurred: {e}")
            print(f"Error starting async monitoring with delay: {e}")

    def start_monitoring(self):
        """Start monitoring in a separate thread to avoid blocking the GUI."""
        
        # Retrieve user inputs
        self.discord_webhook_url = self.discord_webhook_input.text()
        self.user_id = self.user_id_input.text()
        self.cookies['.ROBLOSECURITY'] = self.roblox_cookies_input.text()
        self.dcusernameinput = self.discord_webhook_username_input.text()
        
        # Validate required fields
        if not self.discord_webhook_url or not self.user_id or not self.cookies.get('.ROBLOSECURITY') or not self.dcusernameinput:
            QtWidgets.QMessageBox.warning(self, 'Input Error', 'Please fill in some of the fields!')
            return
        
        # Define API URLs
        self.transaction_api_url = f"https://economy.roblox.com/v2/users/{self.user_id}/transaction-totals?timeFrame=Year&transactionType=summary"
        self.currency_api_url = f"https://economy.roblox.com/v1/users/{self.user_id}/currency"
        
        # Start async monitoring with delay
        self._start_async_monitoring_with_delay()

    def _start_async_monitoring_with_delay(self):
        """Initialize and start the async loop for monitoring with a delay."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Set the delay time in seconds
            delay_seconds = 3 # Adjust this value to change the delay duration
            loop.run_until_complete(self.delay_monitor_start(delay_seconds))
            
            # Run the monitor after the delay
            loop.run_in_executor(None, lambda: loop.run_until_complete(self.monitor()))
            print(f"Monitoring started after {delay_seconds} second delay")
        
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Monitoring Error', f"An error occurred: {e}")
            print(f"Error starting async monitoring with delay: {e}")

async def delay_monitor_start(self, delay_seconds: int):
    """Adds a delay before starting monitoring."""
    print(f"Delaying start for {delay_seconds} seconds...")
    await asyncio.sleep(delay_seconds)  # Non-blocking delay

class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login to Roblox Monitor")
        self.setGeometry(100, 100, 400, 200)

        icon_path = download_icon()  # Download the image
        app_icon = QtGui.QIcon(icon_path)  # Load the icon from the downloaded image
        self.setWindowIcon(app_icon)  # Set the window icon

        # Create layout
        layout = QtWidgets.QVBoxLayout()

        # Username field
        self.username_label = QtWidgets.QLabel("Username:")
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        # Password field
        self.password_label = QtWidgets.QLabel("Password:")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        # Login button
        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.login_button)

        # Status label
        self.status_label = QtWidgets.QLabel()
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def launch_main_app(self):
        self.main_app = RobloxMonitorApp()
        self.main_app.show()

    def authenticate(self, username, password):
        # Replace with actual authentication logic
        authentication = username == SETUSERNAME and password == SETPASSWORD
        return authentication

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.authenticate(username, password):
            self.status_label.setText("Login successful!")
            self.launch_main_app()
            self.close()
        else:
            self.status_label.setText("Invalid username or a password. Please try again.")

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
    label1.place(relx=0.5, rely=0.3, anchor=CENTER)  # Center the label

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
        os.path.join(appdata_dir, 'c1.png'),
        os.path.join(appdata_dir, 'c2.png')
    ]
    
    for url, path in zip(image_urls, image_paths):
        if not os.path.exists(path):
            urllib.request.urlretrieve(url, path)
    
    images = [ImageTk.PhotoImage(Image.open(path)) for path in image_paths]

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
