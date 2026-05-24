import json
import logging
import sys
from typing import Any


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(message)s",
)

logger = logging.getLogger("weather_app")


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, default=str))
