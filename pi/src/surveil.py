import os
import time
import cv2
import requests
import datetime
import tflite_runtime.interpreter as tflite
import numpy as np
from flask import Flask, send_file
import pytz
import json
from pathlib import Path
from threading import Thread, Lock

# Master override to disable or enable vibration
ENABLE_VIBRATION = False  # Set to True to enable vibration, False to disable

# Configuration Variables
CONFIDENCE_THRESHOLD = 90  # Confidence threshold for detection
MOTION_DELAY_MS = 1  # Delay between frames in milliseconds
MOTION_THRESHOLD = 0.01  # Motion area threshold (fraction of total frame size)
BUFFER_PERIOD_SECONDS = 120  # Buffer period (2 minutes)
LOG_FILE = "logs/log.txt"  # Log file path

# Flask App
app = Flask(__name__)

# TensorFlow Lite model setup
interpreter = tflite.Interpreter(model_path="tm_dog_model/model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Class labels
class_labels = ["Mila", "Nova", "None"]

# Read the API key from a file
def load_api_key(file_path="api_key.txt"):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"API key file not found: {file_path}")
    with open(file_path, "r") as file:
        return file.read().strip()

# PHP API Endpoint and API Key
API_URL = "https://ninas.davidmayman.com/api/record_visit.php"
API_KEY = load_api_key()

# GPIO setup for vibration control (optional)
VIBRATE_GPIO_PIN = 17  # Example GPIO pin
DETECTION_TIMEOUT = 2  # Timeout in seconds to deactivate vibration if no motion is detected

try:
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(VIBRATE_GPIO_PIN, GPIO.OUT)
    GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)
except ImportError:
    print("RPi.GPIO not available. Vibration functionality disabled.")
    GPIO = None

# Determine the absolute path to the shared folder
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)

# Log a message to the log file
def log_message(message):
    print(message)
    # Get current time in Los Angeles timezone
    la_timezone = pytz.timezone("America/Los_Angeles")
    timestamp = datetime.datetime.now(la_timezone).strftime("%b %d %Y %H:%M:%S")
    log_entry = f"{timestamp}\t{message}\n"
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write(log_entry)
    else:
        with open(LOG_FILE, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(log_entry + content)

# Vibrate bowl based on detection
def control_vibration(detected_dog):
    if not ENABLE_VIBRATION:
        log_message("Vibration is disabled by override.")
        return

    if GPIO is None:
        log_message("GPIO functionality is disabled. No vibration control.")
        return

    if detected_dog == "Nova":
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.HIGH)
        log_message("Vibration activated for Nova.")
    else:
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)
        log_message("Vibration deactivated.")


# TEST CASES

# Directory and JSON file for test reports
REPORT_DATA_DIR = repo_root / "static" / "report-data"
TESTS_JSON = Path("report/tests.json")
BUZZERS_JSON = Path("report/buzzers.json")

# Test case parameters
SWITCH_DETECTION_TIME = 1  # Time in seconds for quick switching between dogs
LOW_CONFIDENCE_THRESHOLD = 95  # Threshold for low confidence
SECOND_THIRD_CONFIDENCE_THRESHOLD = 25  # Threshold for 2nd/3rd class confidence

# Ensure report directories and files exist
if not os.path.exists(REPORT_DATA_DIR):
    os.makedirs(REPORT_DATA_DIR)

if not os.path.exists(TESTS_JSON):
    with open(TESTS_JSON, "w") as f:
        json.dump([], f)

def test_cases(frame, dog, confidence, confidence_values, current_time, last_detected_time, last_detected_dog):
    """
    Evaluates the frame against test cases and saves it if a case is triggered.
    """
    global last_mila_end_time

    triggered_tests = []

    # Test Case 1: Rapid dog switching
    if last_detected_dog and dog != last_detected_dog and (current_time - last_detected_time).total_seconds() <= SWITCH_DETECTION_TIME:
        triggered_tests.append("Rapid dog switching detected.")

    # Test Case 2: Low confidence for top class
    if confidence < LOW_CONFIDENCE_THRESHOLD:
        triggered_tests.append(f"Low confidence for top class: {confidence:.2f}%.")

    # Test Case 3: 2nd or 3rd confidence > 25%
    other_confidences = [value for key, value in confidence_values.items() if key != dog]
    if any(c > SECOND_THIRD_CONFIDENCE_THRESHOLD for c in other_confidences):
        triggered_tests.append("High confidence for 2nd/3rd class.")

    # Save the frame and metadata if any test case is triggered
    if triggered_tests:
        timestamp = current_time.strftime('%Y%m%d%H%M%S')
        filename = f"TestCase_{timestamp}.jpg"
        filepath = os.path.join(REPORT_DATA_DIR, filename)
        cv2.imwrite(filepath, frame)

        # Prepare the metadata
        test_data = {
            "file_path": filename,
            "timestamp": timestamp,
            "confidence_values": {class_labels[i]: confidence_values[i] for i in range(len(class_labels))},
            "triggered_tests": triggered_tests
        }

        # Append the data to the JSON report
        with open(TESTS_JSON, "r+") as f:
            data = json.load(f)
            data.append(test_data)
            f.seek(0)
            json.dump(data, f, indent=4)

        log_message(f"Test case triggered. Saved to {filepath} with details: {test_data}")

    # Update the last detection details
    return current_time, dog

@app.route("/trigger_tests", methods=["GET"])
def trigger_tests():
    """
    Manually trigger all test cases for debugging purposes.
    """
    debug_frame = cv2.imread(f"{REPORT_DATA_DIR}/debug.jpg")  # Use a debug image for testing
    if debug_frame is None:
        return "Debug image not found.", 404

    # Mock data for triggering test cases
    test_detections = [
        {
            "dog": "Mila",
            "confidence": 80,  # Low confidence case
            "confidence_values": [80, 30, 10],  # Confidence array for all classes
            "message": "Low confidence for top class"
        },
        {
            "dog": "Nova",
            "confidence": 96,
            "confidence_values": [96, 30, 28],  # High 2nd/3rd confidence
            "message": "High confidence for 2nd/3rd class"
        },
        {
            "dog": "Mila",
            "confidence": 99,
            "confidence_values": [99, 85, 10],  # Rapid switch from Mila to Nova
            "message": "Rapid dog switching detected"
        },
    ]

    current_time = datetime.datetime.now()
    last_time = current_time - datetime.timedelta(seconds=1)

    # Simulate test cases
    for detection in test_detections:
        test_cases(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
        )
        time.sleep(.5)

    return "Test cases triggered. Check the JSON file."


# Ensure the BUZZERS JSON file exists
if not BUZZERS_JSON.exists():
    with open(BUZZERS_JSON, "w") as f:
        json.dump([], f)

# END TEST CASES

# Helper function to preprocess the frame for the model
def preprocess_frame(frame, input_size):
    img = cv2.resize(frame, input_size)
    img = img.astype(np.uint8)
    return np.expand_dims(img, axis=0)

# Analyze a single frame using the TensorFlow Lite model
def analyze_frame(frame):
    input_size = (224, 224)
    processed_frame = preprocess_frame(frame, input_size)
    interpreter.set_tensor(input_details[0]['index'], processed_frame)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_class = np.argmax(predictions)
    confidence = predictions[predicted_class]
    return class_labels[predicted_class], confidence

def preprocess_image(img, input_size):
    """
    Preprocesses the input image to match the model's requirements by cropping to a square and resizing.
    """
    
    
    # Get the dimensions of the image
    height, width, _ = img.shape

    # Determine the size of the square crop (smallest dimension)
    crop_size = min(height, width)

    # Calculate the top-left corner of the crop
    top = 0
    left = 0

    # Crop the image to a square
    cropped_img = img[top:top + crop_size, left:left + crop_size]

    # Resize the cropped image to the input size
    resized_img = cv2.resize(cropped_img, input_size)

    # Ensure pixel values are UINT8 (0-255)
    resized_img = resized_img.astype(np.uint8)

    # Add a batch dimension
    return np.expand_dims(resized_img, axis=0)

# Alt evaluation code
def evaluate_image(image):
    """
    Evaluates the image using the TensorFlow Lite model.
    """
    input_size = (224, 224)  # Match the input size used during training
    img = preprocess_image(image, input_size)

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    predictions = interpreter.get_tensor(output_details[0]['index'])[0]

    # Linear map from 0–255 to 0–100
    predictions = predictions / 255.0 * 100.0  # Scale to 0–100

    # Ensure predictions are valid
    predictions = np.nan_to_num(predictions, nan=0.0)  # Replace NaN values with 0
    confidence_scores = {label: float(predictions[i]) for i, label in enumerate(class_labels)}

    return {
        "class": max(confidence_scores, key=confidence_scores.get),  # Top class
        "confidence_scores": confidence_scores
    }

# Detect motion between two frames
def detect_motion(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(thresh) / float(thresh.size)
    return motion_area > MOTION_THRESHOLD

# Buffer logic
last_mila_end_time = None

def register_detection(dog, confidence):
    global last_mila_end_time

    now = datetime.datetime.now()

    if dog == "Mila":
        last_mila_end_time = now
        buffer_end_time = last_mila_end_time + datetime.timedelta(seconds=BUFFER_PERIOD_SECONDS)
        log_message(f"Buffer started due to Mila. Buffer will end at {buffer_end_time}")
        return "Mila registered"

    elif dog == "Nova":
        if last_mila_end_time and (now - last_mila_end_time).total_seconds() < BUFFER_PERIOD_SECONDS:
            log_message("Nova suppressed due to Mila's buffer.")
            return "Nova suppressed"
        else:
            if last_mila_end_time:
                log_message("Buffer ended. Nova is now being processed.")
                last_mila_end_time = None  # Clear the buffer

            # Log to buzzers.json
            with open(BUZZERS_JSON, "r+") as f:
                data = json.load(f)
                data.append({
                    "start_time": now.isoformat(),
                    "confidence": confidence
                })
                f.seek(0)
                json.dump(data, f, indent=4)

            return "Nova registered"

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
        log_message(f"Visit successfully sent for {dog}: {response.json()}")
    except requests.RequestException as e:
        log_message(f"Failed to send visit data: {e}")
        if hasattr(e, 'response') and e.response is not None:
            log_message(f"Response content: {e.response.text}")

# Main function for motion detection and visit tracking
def main():
    log_message("Starting niñas...")
    global cap
    cap = cv2.VideoCapture(0)  # Use camera 0
    _, prev_frame = cap.read()

    last_detected_dog = None
    last_detected_time = datetime.datetime.now()
    last_motion_time = time.time()
    current_visit = {"dog": None, "start_time": None, "end_time": None}

    while True:
        #_, curr_frame = cap.read()
        curr_frame = cv2.imread("test-photos/dummy.jpg")

        # Check for motion
        if detect_motion(prev_frame, curr_frame):
            log_message("Motion detected! Capturing frame...")
            result = evaluate_image(curr_frame)
            print(result)
            dog = result["class"]
            confidence = result["confidence_scores"][result["class"]]

            if confidence >= CONFIDENCE_THRESHOLD and dog != "None":
                detection_result = register_detection(dog, confidence)
                log_message(f"{detection_result}: {dog} with confidence {confidence:.2f}% {result['confidence_scores']}")

                # Run test cases on the frame
                current_time = datetime.datetime.now()
                last_detected_time, last_detected_dog = test_cases(
                    curr_frame, dog, confidence, result["confidence_scores"], current_time, last_detected_time, last_detected_dog
                )

                if detection_result == "Mila registered" or detection_result == "Nova registered":
                    if current_visit["dog"] == dog:
                        # Extend the current visit
                        current_visit["end_time"] = datetime.datetime.now()
                    else:
                        # Send the previous visit if it exists
                        if current_visit["dog"] is not None:
                            send_visit_to_api(
                                current_visit["dog"],
                                current_visit["start_time"],
                                current_visit["end_time"]
                            )
                            log_message(f"{current_visit['dog']}'s visit complete.")

                        # Start a new visit
                        current_visit = {
                            "dog": dog,
                            "start_time": datetime.datetime.now(),
                            "end_time": datetime.datetime.now()
                        }
                        log_message(f"Starting new visit for {dog}.")

            # Update the time of the last motion
            last_motion_time = time.time()

        # Finalize visit if no motion for DETECTION_TIMEOUT
        if time.time() - last_motion_time > DETECTION_TIMEOUT:
            if current_visit["dog"] == "Nova":

                # # Update buzzers.json with the end time
                # now = datetime.datetime.now()
                # with open(BUZZERS_JSON, "r+") as f:
                #     data = json.load(f)
                #     for entry in reversed(data):
                #         if entry["video_file"].endswith(f"Nova_{current_visit['start_time'].strftime('%Y%m%d%H%M%S')}.avi"):
                #             entry["end_time"] = now.isoformat()
                #             break
                #     f.seek(0)
                #     json.dump(data, f, indent=4)

            # Send the API data and reset the visit
            if current_visit["dog"] is not None:
                send_visit_to_api(
                    current_visit["dog"],
                    current_visit["start_time"],
                    current_visit["end_time"]
                )
                log_message(f"{current_visit['dog']}'s visit complete.")
                current_visit = {"dog": None, "start_time": None, "end_time": None}

        prev_frame = curr_frame

# Flask Route for Viewing Logs
@app.route('/', methods=['GET'])
def view_logs():
    return send_file(LOG_FILE, mimetype="text/plain")

@app.route('/simulate_nova', methods=['GET'])
def simulate_nova():
    # Simulated data for Nova
    dog = "Nova"
    confidence = CONFIDENCE_THRESHOLD + 1  # Ensure it's above the threshold

    # Call the register_detection function
    result = register_detection(dog, confidence)

    return f"Simulated detection result: {result}", 200

# Entry point for the script
if __name__ == "__main__":
    import threading
    try:
        # Run Flask app in a separate thread
        threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000)).start()
        main()
    except KeyboardInterrupt:
        if GPIO:
            GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)
            GPIO.cleanup()
        log_message("Exiting...")
        print("\nExiting...")