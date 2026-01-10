from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import response
from app.api.v1.context import RequiresContext
from app.utilities import logging

logger = logging.get_logger(__name__)

router = APIRouter(
    prefix="/example",
)
