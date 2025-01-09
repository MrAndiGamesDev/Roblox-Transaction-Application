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

hidden_dir = ".resources"
Supported = "Windows"

# ICON URLS
icon_url = "https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/Robux.png"
AVATAR_URL = "" # Custom icon for Discord notification

UPDATEEVERY = 60  # Monitor interval

TIMEZONE = pytz.timezone("America/New_York")  # Default timezone
shutdown_flag = False  # Graceful shutdown flag

# Define the hidden directory path based on the operating system
home_dir = os.path.expanduser("~")

#https://img.icons8.com/plasticine/2x/robux.png

def show_popup(message, title="Error"):
    """Display a custom popup with the specified message using PyQt5."""
    app = QApplication([])
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.exec_()

def set_hidden_attribute(path):
    """Set the hidden attribute on a file or directory."""
    if not os.path.exists(path):
        show_popup(f"The specified path does not exist: {path}")
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    system = platform.system()
    try:
        if system == Supported:
            # Use the `attrib` command to set the hidden attribute
            subprocess.run(["attrib", "+H", path], check=True)
        else:
            show_popup(f"Unsupported operating system: {system}")
            raise RuntimeError(f"Unsupported operating system: {system}")
    except Exception as e:
        show_popup(f"An error occurred while setting the hidden attribute: {e}")
        raise RuntimeError(f"An error occurred while setting the hidden attribute: {e}")

if platform.system() == Supported:
    appdata_dir = os.path.join(home_dir, "AppData", "Roaming", "HiddenRobux")
    
    # Example usage
    try:
        os.makedirs(appdata_dir, exist_ok=True)  # Ensure the directory exists
        set_hidden_attribute(appdata_dir)
    except Exception as e:
        print(f"Error: {e}")
else:
    show_popup("Unsupported operating system")

def download_icon():
    """Download the icon to the AppData directory and set it hidden."""
    icon_path = os.path.join(appdata_dir, "robux_icon.png")
    
    # Ensure the hidden directory exists
    os.makedirs(appdata_dir, exist_ok=True)

    # Set the hidden attribute for the directory
    set_hidden_attribute(appdata_dir)

    # Check if the icon already exists
    if not os.path.exists(icon_path):
        urllib.request.urlretrieve(icon_url, icon_path)

        # Set the hidden attribute for the file
        set_hidden_attribute(icon_path)

    return icon_path

def get_hidden_file_path(filename):
    """Return the path for a hidden file in the AppData directory."""
    hidden_file_path = os.path.join(appdata_dir, filename)
    
    # Ensure the hidden directory exists
    os.makedirs(appdata_dir, exist_ok=True)
    set_hidden_attribute(appdata_dir)

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
        self.setWindowTitle('Welcome To Roblox Transaction Monitor')
        self.setGeometry(200, 200, 600, 400)
        self.setFixedSize(500, 300)

        # Set app icon from GitHub image URL or local file
        icon_path = download_icon()  # Download the image
        app_icon = QtGui.QIcon(icon_path)  # Load the icon from the downloaded image
        self.setWindowIcon(app_icon)  # Set the window icon

        # Create layout and widgets
        layout = QtWidgets.QVBoxLayout()

        self.creditlabel = QtWidgets.QLabel("Roblox Transaction Monitoring App By (MrAndi Scripted)", self)
        layout.addWidget(self.creditlabel)

        self.robux_balance_label = QtWidgets.QLabel("Current Robux Balance: 0", self)
        layout.addWidget(self.robux_balance_label)

        self.discord_webhook_input = QtWidgets.QLineEdit(self)
        self.discord_webhook_input.setPlaceholderText("Discord Webhook URL")
        self.discord_webhook_input.setEchoMode(QtWidgets.QLineEdit.Password)  # Censor input
        self.discord_webhook_input.setStyleSheet("""
                  border-radius: 7px;
                  border: 2px solid #808080;
        """)
        layout.addWidget(self.discord_webhook_input)

        self.image_url = QtWidgets.QLineEdit(self)
        self.image_url.setPlaceholderText("Image URL")
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

    async def send_discord_notification(self, embed: dict):
        """Send a notification to the Discord webhook."""
        AVATAR_URL = self.image_url.text()
        payload = {
            "embeds": [embed],
            "username": "Roblox Transaction Info",
            "avatar_url": AVATAR_URL
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.discord_webhook_url, json=payload, timeout=30) as response:
                    response.raise_for_status()
                    print("Sent Discord notification successfully.")
            except aiohttp.ClientError as e:
                print(f"Error sending Discord notification: {e}")

    def get_current_time(self, timezone=None):
        """Get the current time in the specified timezone (12-hour format)."""
        # Use the provided timezone or default to the application's timezone
        tz = timezone or self.get_selected_timezone()
        return datetime.now(tz).strftime('%m/%d/%Y %I:%M:%S %p')

    async def send_discord_notification_for_changes(self, title: str, description: str, changes: dict, footer: str):
        """Send a notification for changes detected in transaction data."""
        fields = [{"name": key, "value": f"**{old}** → **{new}**", "inline": False} for key, (old, new) in changes.items()]
        
        # Get the current time in the selected timezone
        current_time_in_timezone = self.get_current_time(self.get_selected_timezone())

        embed = {
            "title": title,
            "description": description,
            "fields": fields,
            "color": 720640,
            "footer": {"text": f"{footer} Timezone: {self.get_selected_timezone().zone} | Time: {current_time_in_timezone}"}
        }
        await self.send_discord_notification(embed)

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

    def get_selected_timezone(self):
        """Get the selected timezone from the dropdown."""
        selected_timezone = self.timezone_dropdown.currentText()
        return pytz.timezone(selected_timezone)

    async def monitor(self):
        """Monitor Roblox transaction and Robux data for changes."""
        iteration_count = 0

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
                            "Fetched From Roblox's API"
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
                        "footer": {"text": f"Change detected at {self.get_current_time()}"}
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
        
        # Validate required fields
        if not self.discord_webhook_url or not self.user_id or not self.cookies.get('.ROBLOSECURITY'):
            QtWidgets.QMessageBox.warning(self, 'Input Error', 'Please fill in all the fields!')
            return
        
        # Define API URLs
        self.transaction_api_url = f"https://economy.roblox.com/v2/users/{self.user_id}/transaction-totals?timeFrame=Year&transactionType=summary"
        self.currency_api_url = f"https://economy.roblox.com/v1/users/{self.user_id}/currency"
        
        # Start async monitoring with delay
        self._start_async_monitoring_with_delay()

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

async def delay_monitor_start(self, delay_seconds: int):
    """Adds a delay before starting monitoring."""
    print(f"Delaying start for {delay_seconds} seconds...")
    await asyncio.sleep(delay_seconds)  # Non-blocking delay

class RotatingCircle(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0  # Starting angle for the rotation
        self.setFixedSize(100, 100)  # Set a fixed size for the circle

        # Create a timer to update the angle and trigger a repaint
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_angle)
        self.timer.start(30)  # Update the angle every 30ms (adjust speed here)

    def update_angle(self):
        """Update the rotation angle."""
        self.angle += 5  # Increment angle by 5 degrees
        if self.angle >= 360:
            self.angle = 0  # Reset the angle once it completes a full circle
        self.update()  # Request a repaint

    def paintEvent(self, event):
        """Draw the rotating circle."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)  # Smooth rendering
        painter.setPen(QtCore.Qt.NoPen)  # No border for the circle
        painter.setBrush(QtGui.QColor(0, 169, 224))  # Set the fill color (Roblox-like)

        # Calculate the center and radius of the circle
        center = self.rect().center()
        radius = self.width() // 3  # Set the radius as a third of the widget size

        # Rotate the painter around the center of the circle
        painter.translate(center)
        painter.rotate(self.angle)
        painter.translate(-center)

        # Draw the circle
        painter.drawEllipse(center, radius, radius)

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
        return username == "anything" and password == "anything"

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.authenticate(username, password):
            self.status_label.setText("Login successful!")
            time.sleep(1)
            self.launch_main_app()
            self.close()
        else:
            self.status_label.setText("Invalid username or a password. Please try again.")

def create_splash_screen():
    """Create and return a styled splash screen with animated loading dots."""
    background_color = QtGui.QColor("#000000")  # Dark background similar to Roblox
    splash_pix = QtGui.QPixmap(download_icon())  # Use the hidden icon file
    splash_pix = splash_pix.scaled(150, 150, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)

    # Create main splash window widget
    splash_widget = QtWidgets.QWidget()
    splash_widget.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
    splash_widget.setFixedSize(400, 300)  # Smaller, more compact size
    splash_widget.setStyleSheet(f"background-color: {background_color.name()}")

    # Layout setup
    layout = QtWidgets.QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(15)

    # Logo with smooth scaling
    logo_label = QtWidgets.QLabel()
    logo_label.setPixmap(splash_pix)
    logo_label.setAlignment(QtCore.Qt.AlignCenter)
    layout.addWidget(logo_label)

    # Create progress bar with subtle animation and modern look
    progress_bar = QtWidgets.QProgressBar()
    progress_bar.setRange(0, 100)
    progress_bar.setTextVisible(False)
    progress_bar.setStyleSheet("""
        QProgressBar {
            border: none;
            background: #333333;
            height: 5px;
        }
        QProgressBar::chunk {
            background: #00A9E0;  /* Roblox-inspired color */
            width: 10px;
        }
    """)
    layout.addWidget(progress_bar)

    # Loading message with modern font style
    loading_message = QtWidgets.QLabel("Initializing Roblox Monitor...")
    loading_message.setAlignment(QtCore.Qt.AlignCenter)
    loading_message.setStyleSheet("color: white; font-size: 16px; font-family: 'Segoe UI', sans-serif;")
    layout.addWidget(loading_message)

    # Set the layout for the splash widget
    splash_widget.setLayout(layout)

    return splash_widget, progress_bar, loading_message

def animate_loading_dots(loading_message):
    """Animate loading dots for the loading message."""
    dots = ""
    def update_message():
        nonlocal dots
        dots = "." * (dots.count(".") % 3 + 1)
        loading_message.setText(f"Initializing Roblox Monitor{dots}")
    
    # Set up a timer to update the loading message
    timer = QTimer()
    timer.timeout.connect(update_message)
    timer.start(1000)  # Update every 500 milliseconds
    
    return timer

def show_splash_screen(app):
    """Show a splash screen with a Roblox-like loading bar, animated dots, and logo."""
    splash_widget, progress_bar, loading_message = create_splash_screen()

    splash_widget.show()

    # Animate loading dots
    timer = animate_loading_dots(loading_message)

    # Simulate the loading process, updating the progress bar
    for i in range(101):
        app.processEvents()
        progress_bar.setValue(i)
        QtCore.QThread.msleep(60)  # Control the speed of progress bar update

        # Update the loading message with dynamic dots every 2% progress
        if i % 2 == 0:
            loading_message.setText(f"Initializing Roblox Monitor{'...' * (i % 3 + 1)}")

    # Stop the timer once the splash screen is finished
    timer.stop()
    splash_widget.close()

def main():
    app = QtWidgets.QApplication(sys.argv)
    show_splash_screen(app)
    login_window = LoginWindow()
    login_window.show()
    app.exec_()

if __name__ == "__main__":
    main()
