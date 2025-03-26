import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import socket
from pythonjsonlogger import jsonlogger
import requests


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO8601 format for Logstash
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname.lower()
        log_record["logger"] = record.name
        log_record["service"] = {
            "name": "frost-service",
            "version": "1.0.0",
        }

        # Add host information
        log_record["host"] = {
            "name": socket.gethostname(),
            "ip": socket.gethostbyname(socket.gethostname()),
        }

        # Add type field for Logstash filtering
        log_record["type"] = "app"

        # Remove fields that were added to message_dict
        if "timestamp" in message_dict:
            del message_dict["timestamp"]


def setup_logging() -> logging.Logger:
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Disable httpx logs
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("botbrigade-llm").setLevel(logging.CRITICAL)

    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    # Disable propagation to root logger
    logger.propagate = False

    # Format for JSON logging
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s", json_ensure_ascii=False
    )

    # File handler for JSON logs
    json_handler = logging.FileHandler("logs/app.json.log")
    json_handler.setFormatter(formatter)

    # Console handler with more readable format
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(json_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()
