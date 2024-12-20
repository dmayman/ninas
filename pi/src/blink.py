from gpiozero import LED
from time import sleep

# Initialize the LED on GPIO 0
led = LED(0)

try:
    while True:
        led.on()  # Turn the LED on
        sleep(1)  # Wait for 1 second
        led.off()  # Turn the LED off
        sleep(1)  # Wait for 1 second
except KeyboardInterrupt:
    print("Exiting...")
    led.off()  # Ensure the LED is off before exiting