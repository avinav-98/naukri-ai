import logging
import os

LOG_PATH = "storage/logs/automation.log"

os.makedirs("storage/logs", exist_ok=True)

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def log(message):

    logging.info(message)