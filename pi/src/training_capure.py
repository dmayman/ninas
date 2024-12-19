import os
from time import sleep
from gpiozero import DistanceSensor
from picamera import PiCamera

# Configuration
TRIG = 4  # GPIO pin for Trig
ECHO = 17  # GPIO pin for Echo
DETECTION_DISTANCE = 0.2  # Detection threshold in meters (adjust as needed)

# Initialize components
sensor = DistanceSensor(echo=ECHO, trigger=TRIG)
camera = PiCamera()

# Function to ensure directory exists
def ensure_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Prompt for dog name
dog_name = input("Enter the dog's name (Mila or Nova): ").strip()
if dog_name not in ["Mila", "Nova"]:
    print("Invalid name. Please enter 'Mila' or 'Nova'.")
    exit()

# Create directory for the dog
output_dir = f"../../shared/training_photos/{dog_name}"
ensure_directory(output_dir)

print(f"Training for {dog_name}. Photos will be saved in '{output_dir}'.")

# Start capturing photos
photo_count = 0
try:
    while True:
        # Check distance
        if sensor.distance <= DETECTION_DISTANCE:
            # Capture photo
            photo_path = f"{output_dir}/{dog_name}_{photo_count:04d}.jpg"
            camera.capture(photo_path)
            print(f"Captured: {photo_path}")
            photo_count += 1
            sleep(1)  # Avoid capturing multiple photos too quickly
        else:
            print("No dog detected. Waiting...")
        sleep(0.5)
except KeyboardInterrupt:
    print("Photo capture stopped by user.")
finally:
    camera.close()