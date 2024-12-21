import cv2
import os
from pathlib import Path
from time import sleep
from datetime import datetime

# Configuration
DETECTION_THRESHOLD = 15  # Threshold for detecting motion (adjustable)
CAPTURE_DELAY = 1  # Delay between captures in seconds

# Determine the absolute path to the shared folder
def find_repo_root(start_path):
    current_path = Path(start_path).resolve()
    while not (current_path / ".repo_root").exists():
        if current_path.parent == current_path:
            raise FileNotFoundError("Could not locate repo root marker (.repo_root)")
        current_path = current_path.parent
    return current_path

repo_root = find_repo_root(__file__)

photos_dir = repo_root / "static" / "training_photos"
untagged_dir = photos_dir / "untagged"

# Ensure the directory for saving images exists
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

ensure_directory(untagged_dir)

# Open the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print(f"Capturing photos to '{untagged_dir}'.")

previous_frame = None

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            continue

        # Convert the frame to grayscale and blur it for motion detection
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

        if previous_frame is None:
            previous_frame = gray_frame
            continue

        # Compute the absolute difference between the current frame and the previous frame
        frame_delta = cv2.absdiff(previous_frame, gray_frame)
        _, thresh = cv2.threshold(frame_delta, DETECTION_THRESHOLD, 255, cv2.THRESH_BINARY)

        # Detect contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        motion_detected = any(cv2.contourArea(contour) > 500 for contour in contours)

        if motion_detected:
            print("Motion detected! Capturing photo...")

            # Use a timestamp for the photo filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")
            filename = untagged_dir / f"{timestamp}.jpg"
            cv2.imwrite(str(filename), frame)
            print(f"Image saved as {filename}")

            sleep(CAPTURE_DELAY)

        # Update the previous frame
        previous_frame = gray_frame

except KeyboardInterrupt:
    print("Training capture stopped by user.")
finally:
    # Release the camera
    cap.release()
    print("Camera released.")