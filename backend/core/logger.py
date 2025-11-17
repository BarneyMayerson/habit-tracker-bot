import sys

from loguru import logger


def setup_logger():
    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level="INFO",
    )
    logger.add(
        sink="logs/app.log",
        rotation="50 MB",
        retention="5 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}",
        serialize=False,  # True, если хочешь JSON
    )
    return logger


app_logger = setup_logger()
