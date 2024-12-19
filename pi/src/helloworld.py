import RPi.GPIO as GPIO
import time

# Pin configuration
LED_PIN = 23

# GPIO setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(LED_PIN, GPIO.OUT)

try:
    while True:
        GPIO.output(LED_PIN, GPIO.LOW)  # Turn LED on (sinking current)
        time.sleep(0.5)                # Wait 0.5 seconds
        GPIO.output(LED_PIN, GPIO.HIGH) # Turn LED off
        time.sleep(0.5)                # Wait 0.5 seconds
except KeyboardInterrupt:
    print("Exiting...")

# Cleanup
GPIO.cleanup()