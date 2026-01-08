from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

APP_COMPONENT = os.environ["APP_COMPONENT"]

# MySQL configuration
MYSQL_HOST = os.environ["MYSQL_HOST"]  # Non-standard
MYSQL_TCP_PORT = int(os.environ["MYSQL_TCP_PORT"])
MYSQL_USER = os.environ["MYSQL_USER"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
MYSQL_DATABASE = os.environ["MYSQL_DATABASE"]

REDIS_HOST = os.environ["REDIS_HOST"]  # Non-standard
REDIS_PORT = int(os.environ["REDIS_PORT"])  # Non-standard
REDIS_DATABASE = int(os.environ["REDIS_DATABASE"])  # Non-standard
