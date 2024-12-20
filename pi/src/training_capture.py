import cv2
import os
from gpiozero import DistanceSensor
from time import sleep
from pathlib import Path

# Configuration
TRIG = 4  # GPIO pin for Trig
ECHO = 17  # GPIO pin for Echo
DETECTION_DISTANCE = 0.5  # Detection threshold in meters (adjustable)

# Initialize ultrasonic sensor
sensor = DistanceSensor(echo=ECHO, trigger=TRIG)

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

# Ensure the directory for saving images exists
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Prompt for dog name
dog_name = input("Enter the dog's name (Mila or Nova): ").strip()
if dog_name not in ["Mila", "Nova"]:
    print("Invalid name. Please enter 'Mila' or 'Nova'.")
    exit()

# Directory for saving images
output_dir = photos_dir / dog_name
ensure_directory(output_dir)

# Open the camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print(f"Training for {dog_name}. Photos will be saved in '{output_dir}'.")

photo_count = 0

try:
    while True:
        # Check distance from the sensor
        if sensor.distance <= DETECTION_DISTANCE:
            print(f"Dog detected {sensor.distance}m away. Capturing photo...")

            # Capture a single frame
            ret, frame = cap.read()
            if not ret:
                print("Error: Failed to capture frame.")
                continue

            # Save the captured frame
            filename = output_dir / f"{dog_name}_{photo_count:04d}.jpg"
            cv2.imwrite(str(filename), frame)
            print(f"Image saved as {filename}")
            photo_count += 1

            # Avoid capturing too quickly
            sleep(1)
        else:
            print("No dog detected. Waiting...")
        sleep(0.5)
except KeyboardInterrupt:
    print("Training capture stopped by user.")
finally:
    # Release the camera
    cap.release()
    print("Camera released.")