import RPi.GPIO as GPIO
from time import sleep

# Set up GPIO 0
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

try:
    while True:
        GPIO.output(17, GPIO.HIGH)  # Set GPIO 0 to HIGH
        print ("High")
        sleep(2)  # Wait for 1 second
        
        GPIO.output(17, GPIO.LOW)   # Set GPIO 0 to LOW
        print ("Low")
        sleep(2)  # Wait for 1 second
except KeyboardInterrupt:
    print("Exiting...")
finally:
    GPIO.cleanup()  # Reset GPIO settings