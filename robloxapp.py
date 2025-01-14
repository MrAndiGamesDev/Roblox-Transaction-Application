from PyQt5 import QtCore, QtGui, QtWidgets
from alive_progress import alive_bar
import os
import json
import aiohttp
import asyncio
from datetime import datetime
import pytz

VERSION = "V0.6.9"
AVATAR_URL = "" # Custom icon for Discord notification
ICON_URL = "https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/Robux.png"
UPDATE_INTERVAL = 60 # Monitor interval

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
        self.timezone_dropdown.addItems(self.get_timezones())
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
        self.start_button.setCursor(QtCore.Qt.PointingHandCursor)
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
        fields = []
        for key, (old, new) in changes.items():
            change_indicator = "+" if new > old else "-"
            fields.append({"name": key, "value": f"**{old}** → **{new}** ({change_indicator}{abs(new - old)})", "inline": False})
        
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

                await asyncio.sleep(UPDATE_INTERVAL)

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

    def get_timezones(self):
        """Return a list of timezones."""
        return [
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
        ]
