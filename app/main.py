from __future__ import annotations

from app import api
from app import settings
from app.utilities import logging

logging.configure_from_yaml()

match settings.APP_COMPONENT:
    case "fastapi":
        # Will be ran by the uvicorn CLI.
        asgi_app = api.create_app()
    case _:
        raise ValueError(f"Invalid app component: {settings.APP_COMPONENT}")
