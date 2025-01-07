import os
import asyncio
import aiohttp
import signal
import sys
import json
import requests
from datetime import datetime
import pytz
from dotenv import load_dotenv
import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
from threading import Thread
from PIL import Image, ImageTk
from io import BytesIO
from alive_progress import alive_bar

# Load environment variables
load_dotenv()

# Configuration (initially empty)
DISCORD_WEBHOOK_URL = ""
USERID = ""
COOKIES = {}

TRANSACTION_API_URL = ""
CURRENCY_API_URL = ""

AVATAR_URL = "https://img.icons8.com/plasticine/2x/robux.png"  # Custom icon for Discord notification

UPDATEEVERY = 60  # Monitor interval

# Timezone setup (default timezone)
TIMEZONE = pytz.timezone("America/New_York")

# Graceful shutdown flag
shutdown_flag = False

# JSON storage paths
TRANSACTION_DATA_PATH = "transaction_data.json"
ROBUX_BALANCE_PATH = "robux_balance.json"

def signal_handler(signal, frame):
    """Handle graceful shutdown."""
    global shutdown_flag
    print("Shutting down...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)

def load_json_data(filepath, default_data):
    """Load data from a JSON file."""
    if os.path.exists(filepath):
        with open(filepath, 'r') as file:
            return json.load(file)
    return default_data

def save_json_data(filepath, data):
    """Save data to a JSON file."""
    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def get_current_time():
    """Get the current time in the specified timezone (12-hour format)."""
    return datetime.now(TIMEZONE).strftime('%m/%d/%Y %I:%M:%S %p')

async def send_discord_notification(embed: dict):
    """Send a notification to the Discord webhook."""
    payload = {
        "embeds": [embed],
        "username": "Roblox Transaction Info",
        "avatar_url": AVATAR_URL
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DISCORD_WEBHOOK_URL, json=payload, timeout=30) as response:
                response.raise_for_status()
                print("Sent Discord notification successfully.")
        except aiohttp.ClientError as e:
            print(f"Error sending Discord notification: {e}")

async def send_discord_notification_for_changes(title: str, description: str, changes: dict, footer: str):
    """Send a notification for changes detected in transaction data."""
    fields = [{"name": key, "value": f"**{old}** → **{new}**", "inline": False} for key, (old, new) in changes.items()]
    embed = {
        "title": title,
        "description": description,
        "fields": fields,
        "color": 720640,
        "footer": {
            "text": footer
        }
    }
    await send_discord_notification(embed)

async def fetch_data(url: str):
    """Fetch data from the provided URL."""
    retries = 3
    async with aiohttp.ClientSession() as session:
        for _ in range(retries):
            try:
                async with session.get(url, cookies=COOKIES, timeout=30) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                print(f"Failed to fetch data from {url}: {e}")
                await asyncio.sleep(5)
    return None

async def fetch_transaction_data():
    """Fetch transaction data."""
    return await fetch_data(TRANSACTION_API_URL)


async def fetch_robux_balance():
    """Fetch the current Robux balance."""
    response = await fetch_data(CURRENCY_API_URL)
    return response.get("robux", 0) if response else 0

async def monitor(gui_vars):
    """Monitor Roblox transaction and Robux data for changes."""
    last_transaction_data = load_json_data(TRANSACTION_DATA_PATH, {})
    last_robux_balance = load_json_data(ROBUX_BALANCE_PATH, {"robux": 0})

    iteration_count = 0

    # Using alive_bar with indefinite progress tracking
    with alive_bar(title="Monitoring Roblox Data", spinner="dots_waves") as bar:
        while not shutdown_flag:
            iteration_count += 1

            # Fetch transaction and balance data concurrently
            current_transaction_data, current_robux_balance = await asyncio.gather(
                fetch_transaction_data(),
                fetch_robux_balance()
            )

            # Update the GUI with the current balance
            gui_vars["robux_balance"].set(f"Current Robux Balance: {current_robux_balance}")

            # Check for changes in transaction data
            if current_transaction_data:
                changes = {
                    key: (last_transaction_data.get(key, 0), current_transaction_data[key])
                    for key in current_transaction_data if current_transaction_data[key] != last_transaction_data.get(key, 0)
                }

                if changes:
                    await send_discord_notification_for_changes(
                        "\U0001F514 Roblox Transaction Data Changed!",
                        f"Changes detected at {get_current_time()}",
                        changes,
                        f"Timestamp: {get_current_time()}"
                    )
                    last_transaction_data.update(current_transaction_data)
                    save_json_data(TRANSACTION_DATA_PATH, last_transaction_data)

            # Check for changes in Robux balance
            robux_change = current_robux_balance - last_robux_balance['robux']
            if robux_change != 0:
                color = 0x00FF00 if robux_change > 0 else 0xFF0000  # Green for gain, Red for spent
                change_type = "gained" if robux_change > 0 else "spent"
                await send_discord_notification({
                    "title": "\U0001F4B8 Robux Balance Update",
                    "description": f"You have **{change_type}** Robux.",
                    "fields": [
                        {"name": "Previous Balance", "value": f"**{last_robux_balance['robux']}**", "inline": True},
                        {"name": "Current Balance", "value": f"**{current_robux_balance}**", "inline": True},
                        {"name": "Change", "value": f"**{'+' if robux_change > 0 else ''}{robux_change}**", "inline": True}
                    ],
                    "color": color,
                    "footer": {"text": f"Change detected at {get_current_time()}"}
                })

                last_robux_balance['robux'] = current_robux_balance
                save_json_data(ROBUX_BALANCE_PATH, last_robux_balance)

            # Increment alive_bar to show activity
            bar()

            await asyncio.sleep(UPDATEEVERY)

def stop_monitoring():
    """Stop the monitoring process."""
    global shutdown_flag
    shutdown_flag = True
    print("Monitoring stopped.")

def start_monitoring(gui_vars):
    """Start monitoring in a separate thread to avoid blocking the GUI.""" 
    global DISCORD_WEBHOOK_URL, USERID, COOKIES, TRANSACTION_API_URL, CURRENCY_API_URL, TIMEZONE

    # Get the values from the input fields
    DISCORD_WEBHOOK_URL = gui_vars["discord_webhook"].get()
    USERID = gui_vars["user_id"].get()
    COOKIES['.ROBLOSECURITY'] = gui_vars["roblox_cookies"].get()

    # Update the selected timezone
    selected_timezone = gui_vars["timezone"].get()
    TIMEZONE = pytz.timezone(selected_timezone)

    # Update the API URLs
    TRANSACTION_API_URL = f"https://economy.roblox.com/v2/users/{USERID}/transaction-totals?timeFrame=Year&transactionType=summary"
    CURRENCY_API_URL = f"https://economy.roblox.com/v1/users/{USERID}/currency"

    # Validate inputs
    if not DISCORD_WEBHOOK_URL or not USERID or not COOKIES['.ROBLOSECURITY']:
        messagebox.showerror("Error", "Please fill in all the fields!")
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor(gui_vars))

def on_dropdown_click(event, dropdown):
    """Resize dropdown to smaller width when clicked."""
    dropdown.config(width=15)  # Set a smaller width when clicked

def on_dropdown_leave(event, dropdown):
    """Reset dropdown width back to normal when focus is lost."""
    dropdown.config(width=20)  # Set a larger width when focus is lost

def create_gui():
    """Create the GUI window and components."""
    root = tk.Tk()
    root.title("Roblox Monitoring")

    # Set the app icon from a URL (replace with your GitHub image URL)
    icon_url = "https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/Robux.png"
    
    # Fetch the image data
    response = requests.get(icon_url, allow_redirects=True)

    # Print response details for debugging
    print("Status Code:", response.status_code)
    print("Content Type:", response.headers['Content-Type'])

    if response.status_code == 200 and "image" in response.headers['Content-Type']:
        icon_data = response.content
        try:
            # Open the image using Pillow and convert it to an ImageTk format
            image = Image.open(BytesIO(icon_data))
            icon_image = ImageTk.PhotoImage(image)

            # Set the icon to the window
            root.iconphoto(True, icon_image)

        except Exception as e:
            print("Error opening image:", e)
            print("Image data length:", len(icon_data))  # Check if data is received
            return
    else:
        print("Failed to retrieve a valid image. Status code:", response.status_code)
        return

    gui_vars = {
        "robux_balance": tk.StringVar(value="Current Robux Balance: 0"),
        "discord_webhook": tk.StringVar(),
        "user_id": tk.StringVar(),
        "roblox_cookies": tk.StringVar(),
        "timezone": tk.StringVar(value="America/New_York")
    }

    # Discord Webhook input field
    tk.Label(root, text="Discord Webhook URL").pack(pady=5)
    discord_webhook_entry = tk.Entry(root, textvariable=gui_vars["discord_webhook"], width=50)
    discord_webhook_entry.pack(pady=5)

    # User ID input field
    tk.Label(root, text="Roblox User ID").pack(pady=5)
    user_id_entry = tk.Entry(root, textvariable=gui_vars["user_id"], width=50)
    user_id_entry.pack(pady=5)

    # Roblox Cookies input field
    tk.Label(root, text="Roblox Cookies").pack(pady=5)
    roblox_cookies_entry = tk.Entry(root, textvariable=gui_vars["roblox_cookies"], width=50)
    roblox_cookies_entry.pack(pady=5)

    # Timezone dropdown
    tk.Label(root, text="Select Timezone").pack(pady=5)
    timezone_options = [
        "America/New_York", "America/Chicago", "America/Los_Angeles", "America/Denver", 
        "America/Phoenix", "America/Seattle", "Europe/London", "Europe/Paris", 
        "Europe/Berlin", "Europe/Moscow", "Asia/Tokyo", "Asia/Singapore", 
        "Asia/Kolkata", "Asia/Seoul", "Asia/Shanghai", "Asia/Dubai", "Asia/Kuala_Lumpur", 
        "Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane", "Australia/Perth", 
        "Africa/Johannesburg", "Africa/Nairobi", "Africa/Cairo", "Africa/Lagos", 
        "Pacific/Auckland", "Pacific/Fiji", "Pacific/Guam", "Pacific/Honolulu", 
        "Pacific/Tahiti", "America/Toronto", "America/Vancouver", "America/Edmonton", 
        "America/Winnipeg", "America/Calgary", "America/Regina", "Asia/Taipei", 
        "Asia/Manila", "Asia/Hong_Kong", "Europe/Madrid", "Europe/Amsterdam", 
        "Europe/Stockholm", "America/Sao_Paulo", "America/Argentina/Buenos_Aires", 
        "America/Montevideo", "America/Caracas", "America/Chile", "America/Lima", 
        "America/Guayaquil", "Europe/Zurich", "Europe/Oslo", "Europe/Brussels", 
        "Europe/Athens", "Europe/Rome", "Europe/Prague", "Asia/Ho_Chi_Minh"
    ]
    timezone_dropdown = tk.OptionMenu(root, gui_vars["timezone"], *timezone_options)
    timezone_dropdown.config(width=20)  # Set initial width
    
    # Bind events to change dropdown width on click and leave
    timezone_dropdown.bind("<Enter>", lambda event: on_dropdown_click(event, timezone_dropdown))
    timezone_dropdown.bind("<Leave>", lambda event: on_dropdown_leave(event, timezone_dropdown))

    timezone_dropdown.pack(pady=5)

    # Robux balance label
    robux_label = tk.Label(root, textvariable=gui_vars["robux_balance"], font=("Arial", 14))
    robux_label.pack(pady=20)

    # Start button
    start_button = tk.Button(root, text="Start Monitoring", command=lambda: Thread(target=start_monitoring, args=(gui_vars,)).start())
    start_button.pack(pady=10)

    # Stop button
    stop_button = tk.Button(root, text="Stop Monitoring", command=stop_monitoring)
    stop_button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    try:
        create_gui()
    except KeyboardInterrupt:
        print("Script interrupted by user. Exiting...")
        sys.exit(0)
