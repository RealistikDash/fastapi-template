from __future__ import annotations

import logging
import sys

logger = logging.getLogger(__name__)


def install_optimal_loop() -> None:
    if sys.platform in ("linux", "linux2", "darwin"):
        logger.debug(
            "Installing uvloop based on the OS platform.",
            extra={"platform": sys.platform},
        )
        try:
            import uvloop

            uvloop.install()
        except ImportError:
            logger.warning(
                "uvloop is not installed, falling back to the default asyncio event loop.",
                extra={"platform": sys.platform},
            )
    elif sys.platform == "win32":
        logger.debug(
            "Installing winloop based on the OS platform.",
            extra={"platform": sys.platform},
        )
        try:
            import winloop

            winloop.install()
        except ImportError:
            logger.warning(
                "winloop is not installed, falling back to the default asyncio event loop.",
                extra={"platform": sys.platform},
            )

    else:
        logger.debug(
            "Falling back to the default asyncio event loop based on the OS platform.",
            extra={"platform": sys.platform},
        )
