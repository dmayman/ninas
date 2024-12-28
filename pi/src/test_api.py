import requests
import datetime
import os

# API Endpoint and API Key
API_URL = "https://ninas.davidmayman.com/api/record_visit.php"

# Load API key from file
def load_api_key(file_path="api_key.txt"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"API key file not found: {file_path}")
    with open(file_path, "r") as file:
        return file.read().strip()

# Load API key
API_KEY = load_api_key()

# Function to send a test visit to the API
def send_test_visit(dog, start_time, end_time):
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "dog": dog,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        print(f"Test visit successfully sent for {dog}: {response.json()}")
    except requests.RequestException as e:
        print(f"Failed to send test visit data: {e}")

# Test Cases
def run_tests():
    print("Running test cases for the API...")

    # Test Case 1: Nova visit
    start_time = datetime.datetime.now()
    end_time = start_time + datetime.timedelta(minutes=5)
    send_test_visit("Nova", start_time, end_time)

    # Test Case 2: Mila visit
    start_time = datetime.datetime.now() - datetime.timedelta(minutes=10)
    end_time = start_time + datetime.timedelta(minutes=7)
    send_test_visit("Mila", start_time, end_time)

    # Test Case 3: Invalid data (no dog name)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "start_time": datetime.datetime.now().isoformat(),
        "end_time": (datetime.datetime.now() + datetime.timedelta(minutes=5)).isoformat()
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        print(f"Invalid data response: {response.status_code}, {response.text}")
    except requests.RequestException as e:
        print(f"Failed to send invalid test data: {e}")

# Run tests
if __name__ == "__main__":
    run_tests()