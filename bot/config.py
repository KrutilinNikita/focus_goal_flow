from pathlib import Path
from dotenv import load_dotenv
import os

# Paths
BOT_DIR = Path(__file__).resolve().parent
BASE_DIR = BOT_DIR.parent
DB_PATH = BASE_DIR / "app.db"
LOGS_DIR = BASE_DIR / "logs"
ADMINS_FILE = BOT_DIR / "admins.txt"
ENV_FILE = BOT_DIR / ".env"

# Load .env
load_dotenv(ENV_FILE)

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Reminder times (HH:MM)
REMINDER_TIMES = ["09:00", "12:00", "17:00", "19:00", "21:00", "23:00"]

# Goal edit deadline (hours after midnight)
GOAL_EDIT_DEADLINE_HOUR = 3
