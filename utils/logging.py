import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def setup_logging():
    logger = logging.getLogger("PennyApp")
    logger.setLevel(logging.DEBUG)

    handler = RotatingFileHandler("penny_errors.log", maxBytes=5*1024*1024, backupCount=3)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - UserID: %(user_id)s - %(message)s - %(pathname)s:%(lineno)d")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

def log_info(user_id, message):
    logging.getLogger("PennyApp").info(message, extra={"user_id": user_id})

def log_error(user_id, message):
    logging.getLogger("PennyApp").error(message, extra={"user_id": user_id}, exc_info=True)

def log_debug(user_id, message):
    logging.getLogger("PennyApp").debug(message, extra={"user_id": user_id})