import logging
from modules.utils import folder_exists
from config import REPORT_DATA_DIR

# Create a logger
logger = logging.getLogger("ninas")
logger.setLevel(logging.DEBUG)  # Overall logger level to allow all logs

# 1. **File Handler**: Logs only `INFO` and above to the file
file_handler = logging.FileHandler("logs/app.log")
file_handler.setLevel(logging.INFO)  # Only logs `INFO`, `WARNING`, `ERROR`, `CRITICAL`
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

# 2. **Console Handler**: Logs **everything** (including `DEBUG`)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)  # Logs `DEBUG` and above to console
console_formatter = logging.Formatter("%(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Ensure the report data directory exists
folder_exists(REPORT_DATA_DIR)