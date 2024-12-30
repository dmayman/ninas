import os
import time
import cv2
import requests
import datetime
import tflite_runtime.interpreter as tflite
import numpy as np
from flask import Flask, send_file, render_template_string, Response
import pytz
import json
from pathlib import Path
from threading import Thread, Lock
import base64

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
def control_vibration(position):

    # For buzz reporting only
    if position == "on":
        if not current_buzz_event:
            start_buzz_event()
    else:
        if current_buzz_event:
            end_buzz_event()
    
    # Main evaluation
    if GPIO is None:
        log_message("GPIO functionality is disabled. No vibration control.")
        return

    if position == "on":
        if not ENABLE_VIBRATION:
            log_message("Vibration is disabled by override.")
        return
    
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.HIGH)
        log_message("Vibration activated for Nova.")
    else:
        if GPIO.input(VIBRATE_GPIO_PIN):
            log_message("Vibration deactivated.")
        GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)
        


# TEST CASES

# Directory and JSON file for test reports
REPORT_DATA_DIR = repo_root / "static" / "report-data"
TESTS_JSON = Path("report/tests.json")
BUZZERS_JSON = Path("report/buzzers.json")

# Test case parameters
SWITCH_DETECTION_TIME = 1  # Time in seconds for quick switching between dogs
LOW_CONFIDENCE_THRESHOLD = 95  # Threshold for low confidence
SECOND_THIRD_CONFIDENCE_THRESHOLD = 25  # Threshold for 2nd/3rd class confidence

current_buzz_event = None  # Holds the ongoing buzz event

# For loading in dummy images
USE_DUMMY_IMAGES = False
active_images = []  # List of loaded images
current_image_index = 0  # Current index in the active_images list

# Ensure report directories and files exist
if not os.path.exists(REPORT_DATA_DIR):
    os.makedirs(REPORT_DATA_DIR)

if not os.path.exists(TESTS_JSON):
    with open(TESTS_JSON, "w") as f:
        json.dump([], f)


def save_test_case(frame, triggered_tests, confidence_values, timestamp, dog):
    """
    Saves the frame as an image, updates the JSON file, and logs the event.
    """
    # Generate filename and file path
    filename = f"TestCase_{timestamp}.jpg"
    filepath = os.path.join(REPORT_DATA_DIR, filename)

    # Save the frame
    cv2.imwrite(filepath, frame)

    # Prepare metadata
    test_data = {
        "file_path": filename,
        "timestamp": timestamp,
        "confidence_values": confidence_values,
        "triggered_tests": triggered_tests,
        "dog": dog
    }

    # Append the data to the JSON report
    with open(TESTS_JSON, "r+") as f:
        data = json.load(f)
        data.append(test_data)
        f.seek(0)
        json.dump(data, f, indent=4)

    log_message(f"Test case triggered. Saved to {filepath} with details: {test_data}")

def test1_rapid_switching(dog, current_time, last_detected_time, last_detected_dog):
    """
    Test Case 1: Rapid dog switching.
    """
    if last_detected_dog and dog != last_detected_dog and (current_time - last_detected_time).total_seconds() <= SWITCH_DETECTION_TIME:
        return ["Rapid dog switching detected."]
    return []

def test2_low_confidence(confidence):
    """
    Test Case 2: Low confidence for top class.
    """
    if confidence < LOW_CONFIDENCE_THRESHOLD and confidence > LOW_CONFIDENCE_THRESHOLD - 20:
        return [f"Low confidence for top class: {confidence:.2f}%."]
    return []

def test3_mixed_confidence(dog, confidence_values):
    """
    Test Case 3: 2nd or 3rd confidence > 25%.
    """
    other_confidences = [value for key, value in confidence_values.items() if key != dog]
    if any(c > SECOND_THIRD_CONFIDENCE_THRESHOLD for c in other_confidences):
        return ["High confidence for 2nd/3rd class."]
    return []

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
        test1_rapid_switching(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
        )
        time.sleep(.5)

    # Simulate test cases
    for detection in test_detections:
        test2_low_confidence(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
        )
        time.sleep(.5)
    
    # Simulate test cases
    for detection in test_detections:
        test3_mixed_confidence(
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


def start_buzz_event():
    """
    Starts a new buzz event for Nova.
    """
    global current_buzz_event
    now = datetime.datetime.now()

    current_buzz_event = {
        "start_time": now.isoformat(),
        "end_time": None,
        "frames": []
    }
    log_message(f"Started new buzz event at {now}.")

def end_buzz_event():
    """
    Ends the current buzz event and writes it to buzzers.json.
    """
    global current_buzz_event, BUZZERS_JSON

    if not current_buzz_event:
        return

    now = datetime.datetime.now()
    current_buzz_event["end_time"] = now.isoformat()
    log_message(f"Ended buzz event for {current_buzz_event['dog']} at {now}.")

    # Write the event to buzzers.json
    with open(BUZZERS_JSON, "r+") as f:
        data = json.load(f)
        data.append(current_buzz_event)
        f.seek(0)
        json.dump(data, f, indent=4)

    current_buzz_event = None  # Reset the current event

def add_frame_to_buzz_event(frame, confidence_values):
    """
    Adds frame data to the current buzz event.
    """
    global current_buzz_event, REPORT_DATA_DIR

    if not current_buzz_event:
        return

    # Generate a unique filename for the frame
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"BuzzFrame_{timestamp}.jpg"
    filepath = os.path.join(REPORT_DATA_DIR, filename)

    # Save the frame
    cv2.imwrite(filepath, frame)

    # Append frame data to the event
    current_buzz_event["frames"].append({
        "filename": filename,
        "confidence_values": {
            "Mila" : confidence_values.get("Mila", 0.0),
            "Nova" : confidence_values.get("Nova", 0.0),
            "None" : confidence_values.get("None", 0.0)
        }
    })

def load_test_images(directory):
    """
    Loads all images from the specified directory in sorted order.
    """
    image_paths = sorted(Path(directory).glob("*.jpg"))
    return [cv2.imread(str(image_path)) for image_path in image_paths if cv2.imread(str(image_path)) is not None]

# Updates the dummy images that get fed in lieu of actual captured frames
def update_simulated_images(directory):
    """
    Updates the active images list based on the specified directory.
    Resets the current image index to 0.
    """
    global active_images, current_image_index, USE_DUMMY_IMAGES

    USE_DUMMY_IMAGES = True

    # Load all images from the directory
    active_images = load_test_images(directory)
    if not active_images:
        raise ValueError(f"No valid images found in directory: {directory}")

    # Reset the image index
    current_image_index = 0
    log_message(f"Updated simulated images from directory: {directory}")

# Gets next dummy image in the queue
def get_simulated_image():
    """
    Returns the next image in the active images list.
    Cycles back to the first image after reaching the end of the list.
    """
    global active_images, current_image_index
    print (get_simulated_image)
    if not active_images:
        raise ValueError("No active images loaded. Call update_simulated_images() first.")

    # Get the current image and increment the index
    image = active_images[current_image_index]
    current_image_index = (current_image_index + 1) % len(active_images)  # Cycle back to the start
    return image



# END TEST CASES


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

# Determine if the next visit should begin based on a buffer logic
def register_detection(dog, confidence):
    global last_mila_end_time

    now = datetime.datetime.now()

    if dog == "Mila":
        last_mila_end_time = now
        buffer_end_time = last_mila_end_time + datetime.timedelta(seconds=BUFFER_PERIOD_SECONDS)
        # log_message(f"Buffer started due to Mila. Buffer will end at {buffer_end_time}")
        control_vibration("off")
        return "Mila registered"

    elif dog == "Nova":
        if last_mila_end_time and (now - last_mila_end_time).total_seconds() < BUFFER_PERIOD_SECONDS:
            log_message("Nova suppressed due to Mila's buffer.")
            return "Nova suppressed"
        else:
            if last_mila_end_time:
                log_message("Mila buffer ended. Nova is now being processed.")
                last_mila_end_time = None  # Clear the buffer
            
            control_vibration("on");
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
    global cap, curr_frame, USE_DUMMY_IMAGES
    cap = cv2.VideoCapture(0)  # Use camera 0
    cap.set(cv2.CAP_PROP_FPS, 5)  # Reduce capture rate for performance
    _, prev_frame = cap.read()

    last_detected_dog = None
    last_detected_time = datetime.datetime.now()
    last_motion_time = time.time()
    current_visit = {"dog": None, "start_time": None, "end_time": None}

    while True:
        print(f"USE_DUMMY_IMAGES: {USE_DUMMY_IMAGES}")
        if USE_DUMMY_IMAGES == False:
            _, curr_frame = cap.read()
        else:
            # Simulate getting the next frame from the active image set
            try:
                curr_frame = get_simulated_image()
            except ValueError as e:
                log_message(f"Simulation error: {e}")
                break

        # Current time
        current_time = datetime.datetime.now(),

        # Check for motion
        if detect_motion(prev_frame, curr_frame):
            log_message("Motion detected! Evaluating frame...")
            result = evaluate_image(curr_frame)
            dog = result["class"]
            confidence_scores = result["confidence_scores"]
            confidence = confidence_scores[dog]
            
            # Test cases
            triggered_tests = []
            triggered_tests += test2_low_confidence(confidence) # test if there was slightly lower confidence than required

            if confidence >= CONFIDENCE_THRESHOLD and dog != "None":
                detection_result = register_detection(dog, confidence)
                log_message(f"{detection_result}: {dog} with confidence {confidence:.2f}% {confidence_scores}")

                # Tests
                triggered_tests += test1_rapid_switching(dog, current_time, last_detected_time, last_detected_dog) # test if dog rapidly switched
                triggered_tests += test3_mixed_confidence(dog, confidence_scores) # test if dog passed but there were mixed confidence scores
                if detection_result == "Nova suppressed":
                    triggered_tests += "Nova suppressed due to Mila's buffer."

                # Proceed if a dog has been registered
                if detection_result == "Mila registered" or detection_result == "Nova registered":

                    # Tests: Add frame to current buzz event
                    if dog == "Nova":
                        add_frame_to_buzz_event(curr_frame, confidence_scores)

                    if current_visit["dog"] == dog:
                        # Same dog, so extend the current visit
                        current_visit["end_time"] = datetime.datetime.now()
                    else:
                        # New dog, so finish and send the previous visit if it exists
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
                            "start_time": current_time,
                            "end_time": current_time
                        }
                        log_message(f"Starting new visit for {dog}.")

            # Vibration stops as soon as None is detected confidently
            elif confidence >= CONFIDENCE_THRESHOLD and dog == "None":
                control_vibration("off")

            # Save the frame if any test case is triggered
            if triggered_tests:
                timestamp = current_time.strftime('%Y%m%d%H%M%S')
                save_test_case(curr_frame, triggered_tests, confidence_scores, timestamp, dog)
            
            # Update the time of the last motion
            last_motion_time = time.time()

        # Finalize visit if no motion for DETECTION_TIMEOUT
        if time.time() - last_motion_time > DETECTION_TIMEOUT:
            control_vibration ("off")

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

@app.route('/simulate/<dog>', methods=['GET'])
def simulate_camera(dog):
    """
    Updates the simulated images for the specified dog type and renders the video stream.
    """
    global curr_frame, USE_DUMMY_IMAGES
    status_message = ''
    try:
        if dog == "off":
            USE_DUMMY_IMAGES = False
            status_message = "Now using live camera feed."
        else:
            USE_DUMMY_IMAGES = True
            directory = f"test-photos/{dog}-dummy"
            update_simulated_images(directory)
            status_message = f"Simulating Camera for {dog}"

        # Render HTML with video feed
        return render_template_string(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Simulate Camera</title>
            </head>
            <body>
                <h1>{{status_message}}</h1>
                <img src="/video_feed" alt="Simulated Stream" style="max-width:100%; height:auto;">
            </body>
            </html>
            """,
            status_message=status_message
        )
    except ValueError as e:
        return str(e), 404

last_frame_hash = None
@app.route('/video_feed')
def video_feed():
    """
    Serve the current frame only if it has changed since the last request.
    """
    print ("serving video feed...")
    global curr_frame, last_frame_hash

    # Encode the current frame
    if curr_frame is not None:
        _, buffer = cv2.imencode('.jpg', curr_frame)
        frame_bytes = buffer.tobytes()
        frame_hash = hash(frame_bytes)

        # Check if the frame has changed
        if frame_hash != last_frame_hash:
            last_frame_hash = frame_hash
            # Return the updated frame
            return Response(
                frame_bytes,
                mimetype='image/jpeg'
            )

    # No new frame; wait briefly before retrying
    time.sleep(0.1)  # Simulate a delay for polling
    return "", 204  # No content

# Entry point for the script
if __name__ == "__main__":
    import threading
    try:
        # Run Flask app in a separate thread with threading enabled
        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, threaded=True)).start()
        main()
    except KeyboardInterrupt:
        if GPIO:
            GPIO.output(VIBRATE_GPIO_PIN, GPIO.LOW)
            GPIO.cleanup()
        log_message("Exiting...")
        print("\nExiting...")