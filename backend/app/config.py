import os
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database SQLite Path
DB_PATH = DATA_DIR / "aurora_cafe.db"

# Server Settings
APP_NAME = "Teras Manis POS & Management System"
API_PREFIX = "/api"
VERSION = "1.0.0"
