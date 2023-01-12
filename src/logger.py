import os
import logging
from logging.handlers import RotatingFileHandler

if not os.path.exists("./logs"):
    os.mkdir("./logs/")

logging.basicConfig(
        handlers=[
            RotatingFileHandler('./logs/service.log',maxBytes=10240000,backupCount=5)
        ],
        level=logging.INFO,
        format='%(asctime)s %(levelname)s PID_%(process)d %(message)s'
)

async def log_exception(
        message: str,
        payload: str | None = None,
        exception: Exception | None = None):
    logging.error("start " + '-' * 74)
    logging.error(message)
    if payload:
        logging.error(f"Payload: {payload}")
    logging.error("Stack Info:", stack_info=True)
    if exception:
        logging.error(f"Exception Info: {exception}", exc_info=True)
    logging.error("end " + '-' * 76)
