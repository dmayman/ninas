from gpiozero import DistanceSensor
from time import sleep

# Pin configuration
TRIG = 4  # GPIO pin for Trig
ECHO = 17  # GPIO pin for Echo

# Initialize the DistanceSensor
sensor = DistanceSensor(echo=ECHO, trigger=TRIG)

try:
    while True:
        # Get the distance in meters
        distance_m = sensor.distance
        # Convert to centimeters
        distance_cm = distance_m * 100
        print(f"Distance: {distance_cm:.2f} cm")
        sleep(1)  # Wait 1 second between readings
except KeyboardInterrupt:
    print("Measurement stopped by user.")