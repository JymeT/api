import os
import sys
from pathlib import Path
from loguru import logger

from app.core.config import settings


def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    os.makedirs(log_dir, exist_ok=True)

    # Configure loguru
    config = {
        "handlers": [
            {
                "sink": sys.stderr,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": settings.LOG_LEVEL,
            },
            {
                "sink": settings.LOG_FILE,
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
                "level": settings.LOG_LEVEL,
                "rotation": "10 MB",
                "retention": "1 month",
            },
        ],
    }

    # Remove default logger
    logger.remove()
    
    # Add new configurations
    for handler in config["handlers"]:
        logger.add(**handler)

    return logger


# Create logger instance
logger = setup_logging() 