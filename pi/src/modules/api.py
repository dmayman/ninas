import requests
import json
from config import API_URL, API_KEY_FILE
from modules.state import app_state
from modules.logger import logger
import os

# Read the API key from a file
def load_api_key(file_path=API_KEY_FILE):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"API key file not found: {file_path}")
    with open(file_path, "r") as file:
        return file.read().strip()
    
API_KEY = load_api_key()
    
# Send visit data to the PHP API
def send_visit_to_api(dog, start_time, end_time):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "ninas-script/1.0 (+https://github.com/dmayman/ninas)"
    }
    payload = {
        "dog": dog,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Visit successfully sent for {dog}: {response.json()}")
    except requests.RequestException as e:
        logger.info(f"Failed to send visit data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.info(f"Response content: {e.response.text}")