import os
import subprocess
import urllib.request
from PyQt5 import QtCore, QtGui, QtWidgets

ICON_URL = "https://raw.githubusercontent.com/MrAndiGamesDev/Roblox-Transaction-Application/refs/heads/main/Robux.png"

def show_popup(message):
    """Show a popup message."""
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Information)
    msg.setText(message)
    msg.setWindowTitle("Info")
    msg.exec_()

def set_hidden_attribute(path):
    """Set the hidden attribute on a file or directory."""
    if not os.path.exists(path):
        show_popup(f"The specified path does not exist: {path}")
        raise FileNotFoundError(f"The specified path does not exist: {path}")

    try:
        if os.name == "nt":
            subprocess.run(["attrib", "+H", path], check=True)
        else:
            show_popup(f"Unsupported operating system: {os.name}")
            raise RuntimeError(f"Unsupported operating system: {os.name}")
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

if os.name == "nt":
    home_dir = os.path.expanduser("~")
    appdata_dir = os.path.join(home_dir, "AppData", "Roaming", "HiddenRobux")
    ensure_hidden_directory_exists(appdata_dir)
else:
    show_popup("Unsupported operating system")

def download_icon():
    """Download the icon to the AppData directory and set it hidden."""
    icon_url = ICON_URL  # Replace with actual URL
    icon_path = os.path.join(appdata_dir, "robux_icon.png")
    ensure_hidden_directory_exists(appdata_dir)

    if not os.path.exists(icon_path):
        urllib.request.urlretrieve(icon_url, icon_path)
        set_hidden_attribute(icon_path)

    return icon_path

def get_hidden_file_path(filename):
    """Return the path for a hidden file in the AppData directory."""
    hidden_file_path = os.path.join(appdata_dir, filename)
    ensure_hidden_directory_exists(appdata_dir)
    return hidden_file_path

class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Login to Roblox Monitor")
        self.setGeometry(100, 100, 400, 200)

        icon_path = download_icon()
        app_icon = QtGui.QIcon(icon_path)
        self.setWindowIcon(app_icon)

        layout = QtWidgets.QVBoxLayout()

        self.username_label = QtWidgets.QLabel("Username:")
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setStyleSheet("border-radius: 7px; border: 2px solid #808080;")
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)

        self.password_label = QtWidgets.QLabel("Password:")
        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password_input.setStyleSheet("border-radius: 7px; border: 2px solid #808080;")
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        self.login_button.setStyleSheet("border-radius: 7px; border: 2px solid #808080;")
        layout.addWidget(self.login_button)

        self.status_label = QtWidgets.QLabel()
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def launch_main_app(self):
        self.main_app = RobloxMonitorApp()
        self.main_app.show()

    def authenticate(self, username, password):
        # Replace with actual authentication logic
        SETUSERNAME = "anything"
        SETPASSWORD = "anything"
        return username == SETUSERNAME and password == SETPASSWORD

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if self.authenticate(username, password):
            self.status_label.setText("Login successful!")
            self.launch_main_app()
            self.close()
        else:
            self.status_label.setText("Invalid username or password. Please try again.")
