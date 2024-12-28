import os
import time
import cv2
import requests
import datetime
import tflite_runtime.interpreter as tflite
import numpy as np
from flask import Flask, send_file
import pytz

# Configuration Variables
CONFIDENCE_THRESHOLD = 90  # Confidence threshold for detection
MOTION_DELAY_MS = 1  # Delay between frames in milliseconds
MOTION_THRESHOLD = 0.01  # Motion area threshold (fraction of total frame size)
VISIT_BUFFER_SECONDS = 10  # Buffer time to merge visits
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

# Detect motion between two frames
def detect_motion(prev_frame, curr_frame):
    diff = cv2.absdiff(prev_frame, curr_frame)
    gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 25, 255, cv2.THRESH_BINARY)
    motion_area = cv2.countNonZero(thresh) / float(thresh.size)
    return motion_area > MOTION_THRESHOLD

# Vibrate bowl based on detection
def control_vibration(detected_dog):
    if GPIO is None:
        log_message("GPIO functionality is disabled. No vibration control.")
        return

    if detected_dog == "Nova":
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.HIGH)
    else:
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)

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
    cap = cv2.VideoCapture(0)  # Use camera 0
    _, prev_frame = cap.read()

    last_detected_dog = "None"
    last_motion_time = time.time()
    current_visit = {"dog": None, "start_time": None, "end_time": None}

    while True:
        _, curr_frame = cap.read()

        # Check for motion
        if detect_motion(prev_frame, curr_frame):
            log_message("Motion detected! Capturing frame...")
            dog, confidence = analyze_frame(curr_frame)

            if confidence >= CONFIDENCE_THRESHOLD and dog != "None":
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

                log_message(f"Detected dog: {dog} (Confidence: {confidence:.2f}%)")

            # Set vibration control based on detection
            control_vibration(dog)

            # Update the time of the last motion
            last_motion_time = time.time()

        # Finalize visit if no motion for DETECTION_TIMEOUT
        if time.time() - last_motion_time > DETECTION_TIMEOUT:
            if current_visit["dog"] is not None:
                send_visit_to_api(
                    current_visit["dog"],
                    current_visit["start_time"],
                    current_visit["end_time"]
                )
                log_message(f"{current_visit['dog']}'s visit complete.")
                current_visit = {"dog": None, "start_time": None, "end_time": None}
            control_vibration("None")

        prev_frame = curr_frame

# Flask Route for Viewing Logs
@app.route('/', methods=['GET'])
def view_logs():
    return send_file(LOG_FILE, mimetype="text/plain")

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