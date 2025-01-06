import sys
import asyncio
import aiohttp
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit, QLineEdit, QLabel, QMenu
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QIcon

from PIL import Image, ImageDraw

class MonitorThread(QThread):
    log_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, webhook_url, cookie, user_id, durations):
        super().__init__()
        self.webhook_url = webhook_url
        self.cookie = cookie
        self.user_id = user_id
        self.durations = durations
        self.transaction_api_url = f"https://economy.roblox.com/v2/users/{user_id}/transaction-totals?timeFrame=Year&transactionType=summary"
        self.currency_api_url = f"https://economy.roblox.com/v1/users/{user_id}/currency"
        self.cookies = {'.ROBLOSECURITY': self.cookie}

    async def fetch_data(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, cookies=self.cookies, timeout=30) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            self.error_signal.emit(f"Failed to fetch data: {e}")
            return None

    async def send_webhook(self, content, embed=None):
        try:
            payload = {"content": content, "embeds": [embed] if embed else []}
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status != 204:
                        self.error_signal.emit(f"Failed to send webhook: {response.status}")
        except aiohttp.ClientError as e:
            self.error_signal.emit(f"Webhook error: {e}")

    async def process_transaction_data(self, transaction_data):
        color = self.determine_color_based_on_transaction(transaction_data)
        embed = self.create_transaction_embed(transaction_data, color)
        await self.send_webhook("Here are the transaction details:", embed)

    def determine_color_based_on_transaction(self, transaction_data):
        for value in transaction_data.values():
            if isinstance(value, str) and ('-' in value or value.startswith('-')):  # Negative value
                return 16711680  # Red
        return 3066993  # Green

    def create_transaction_embed(self, transaction_data, color):
        fields = [{"name": key, "value": str(value), "inline": False} for key, value in transaction_data.items()]
        return {
            "title": "Transaction Data",
            "description": "Details about the recent transactions.",
            "fields": fields,
            "color": color
        }

    async def process_robux_balance_change(self, robux_balance, last_robux_balance):
        """Handle the change in Robux balance"""
        if robux_balance > last_robux_balance:
            change = robux_balance - last_robux_balance
            embed = {
                "title": "Robux Balance Increased",
                "description": f"Your Robux balance increased by {change} Robux.",
                "color": 3066993  # Green
            }
            await self.send_webhook("Your Robux balance has changed.", embed)
        elif robux_balance < last_robux_balance:
            change = last_robux_balance - robux_balance
            embed = {
                "title": "Robux Balance Decreased",
                "description": f"Your Robux balance decreased by {change} Robux.",
                "color": 16711680  # Red
            }
            await self.send_webhook("Your Robux balance has changed.", embed)

    async def monitor(self):
        last_robux_balance = 0

        while True:
            transaction_data = await self.fetch_data(self.transaction_api_url)
            robux_data = await self.fetch_data(self.currency_api_url)

            if transaction_data:
                await self.process_transaction_data(transaction_data)

            if robux_data:
                robux_balance = robux_data.get("robux", 0)
                if robux_balance != last_robux_balance:
                    await self.process_robux_balance_change(robux_balance, last_robux_balance)
                    last_robux_balance = robux_balance

            await asyncio.sleep(self.durations)

    def run(self):
        # Start the async monitor method without blocking the main thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self.monitor())
        loop.run_forever()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Roblox Transaction Monitor")
        self.setGeometry(100, 100, 400, 300)
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon("Robux.png"))  # Set window icon

        layout = QVBoxLayout()
        self.add_input_widgets(layout)
        self.add_log_display(layout)
        self.add_start_button(layout)
 
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.monitor_thread = None

    def add_input_widgets(self, layout):
        self.webhook_label = QLabel("Discord Webhook URL:")
        self.webhook_input = QLineEdit()

        self.cookie_label = QLabel(".ROBLOSECURITY Cookie:")
        self.cookie_input = QLineEdit()

        self.user_id_label = QLabel("Roblox User ID:")
        self.user_id_input = QLineEdit()

        self.seconds_label = QLabel("Seconds:")
        self.seconds_input = QLineEdit()

        layout.addWidget(self.webhook_label)
        layout.addWidget(self.webhook_input)
        layout.addWidget(self.cookie_label)
        layout.addWidget(self.cookie_input)
        layout.addWidget(self.user_id_label)
        layout.addWidget(self.user_id_input)
        layout.addWidget(self.seconds_label)
        layout.addWidget(self.seconds_input)

    def add_log_display(self, layout):
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)

    def add_start_button(self, layout):
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)

        layout.addWidget(self.start_button)

    def start_monitoring(self):
        if self.monitor_thread and self.monitor_thread.isRunning():
            self.log_display.append("Monitor is already running.")
            return

        webhook_url = self.webhook_input.text()
        cookie = self.cookie_input.text()
        user_id = self.user_id_input.text()
        durations = int(self.seconds_input.text())

        if not webhook_url or not cookie or not user_id or not durations:
            self.log_display.append("Please fill in all fields.")
            return

        self.monitor_thread = MonitorThread(webhook_url, cookie, user_id, durations)
        self.monitor_thread.log_signal.connect(self.log_display.append)
        self.monitor_thread.error_signal.connect(self.log_display.append)
        self.monitor_thread.start()

    def closeEvent(self, event):
        """Override the close event to minimize the app to the tray instead of quitting."""
        self.hide()
        event.ignore()

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())  # Ensure QApplication.exec() is in the main thread

if __name__ == "__main__":
    main()