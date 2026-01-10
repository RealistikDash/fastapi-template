from __future__ import annotations

from app import api
from app import settings
from app.utilities import logging
from app.utilities import loop

logging.configure_from_yaml()
loop.install_optimal_loop()

match settings.APP_COMPONENT:
    case "fastapi":
        # Will be ran by the uvicorn CLI.
        asgi_app = api.create_app()
    case _:
        raise ValueError(f"Invalid app component: {settings.APP_COMPONENT}")
