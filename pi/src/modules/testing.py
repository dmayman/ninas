from modules.utils import json_exists
from config import TESTS_JSON, REPORT_DATA_DIR, BUZZERS_JSON_PATH
import cv2
import os
from modules.logger import logger
import json
from config import SWITCH_DETECTION_TIME, LOW_CONFIDENCE_THRESHOLD, SECOND_THIRD_CONFIDENCE_THRESHOLD
from modules.state import app_state
import datetime
from pathlib import Path

# Ensure the required directories and files exist
json_exists(TESTS_JSON)
json_exists(BUZZERS_JSON_PATH)

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

    logger.info(f"Test case triggered. Saved to {filepath} with details: {test_data}")

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

def start_buzz_event():
    """
    Starts a new buzz event for Nova.
    """
    app_state.current_buzz_event
    now = datetime.datetime.now()

    app_state.current_buzz_event = {
        "start_time": now.isoformat(),
        "end_time": None,
        "frames": []
    }
    logger.info(f"Started new buzz event at {now}.")

def end_buzz_event():
    """
    Ends the current buzz event and writes it to buzzers.json.
    """
    if not app_state.current_buzz_event:
        return

    now = datetime.datetime.now()
    app_state.current_buzz_event["end_time"] = now.isoformat()
    logger.info(f"Ended buzz event at {now}.")

    # Write the event to buzzers.json
    with open(BUZZERS_JSON_PATH, "r+") as f:
        data = json.load(f)
        data.append(app_state.current_buzz_event)
        f.seek(0)
        json.dump(data, f, indent=4)

    app_state.current_buzz_event = None  # Reset the current event

def add_frame_to_buzz_event(frame, confidence_values):
    """
    Adds frame data to the current buzz event.
    """
    if not app_state.current_buzz_event:
        return

    # Generate a unique filename for the frame
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"BuzzFrame_{timestamp}.jpg"
    filepath = os.path.join(REPORT_DATA_DIR, filename)

    # Save the frame
    cv2.imwrite(filepath, frame)

    # Append frame data to the event
    app_state.current_buzz_event["frames"].append({
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

    app_state.use_dummy_images = True

    # Load all images from the directory
    app_state.active_images = load_test_images(directory)
    if not app_state.active_images:
        raise ValueError(f"No valid images found in directory: {directory}")

    # Reset the image index
    current_image_index = 0
    logger.info(f"Updated simulated images from directory: {directory}")

# Gets next dummy image in the queue
def get_simulated_image():
    """
    Returns the next image in the active images list.
    Cycles back to the first image after reaching the end of the list.
    """
    if not app_state.active_images:
        raise ValueError("No active images loaded. Call update_simulated_images() first.")

    # Get the current image and increment the index
    image = app_state.active_images[app_state.current_image_index]
    app_state.current_image_index = (app_state.current_image_index + 1) % len(app_state.active_images)  # Cycle back to the start
    return image
