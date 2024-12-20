import RPi.GPIO as GPIO
from time import sleep

# Set up GPIO 0
GPIO.setmode(GPIO.BCM)
GPIO.setup(0, GPIO.OUT)

try:
    while True:
        GPIO.output(0, GPIO.HIGH)  # Set GPIO 0 to HIGH
        sleep(1)  # Wait for 1 second
        GPIO.output(0, GPIO.LOW)   # Set GPIO 0 to LOW
        sleep(1)  # Wait for 1 second
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()  # Reset GPIO settings