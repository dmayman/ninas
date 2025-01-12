from config import VIBRATE_GPIO_PIN, ENABLE_VIBRATION
from modules.testing import start_buzz_event, end_buzz_event
from modules.state import app_state
from modules.logger import logger

# Initialize the GPIO library
try:
    import RPi.GPIO as GPIO
    app_state.gpio = GPIO

    app_state.gpio.setmode(app_state.gpio.BCM)
    app_state.gpio.setup(VIBRATE_GPIO_PIN, app_state.gpio.OUT)
    app_state.gpio.output(VIBRATE_GPIO_PIN, app_state.gpio.LOW)
except ImportError:
    print("RPi.GPIO not available. Vibration functionality disabled.")
    app_state.gpio = None


# Vibrate bowl based on detection
def control_vibration(position):

    # For buzz reporting only
    if position == "on":
        if not app_state.current_buzz_event:
            start_buzz_event()
    else:
        if app_state.current_buzz_event:
            end_buzz_event()
    
    # Main evaluation
    if app_state.gpio is None:
        logger.info("GPIO functionality is disabled. No vibration control.")
        return
    
    if app_state.safety_buffer_active:
        logger.info("Safety buffer is active. Vibration suppressed.")
        return

    if position == "on":
        if not ENABLE_VIBRATION:
            logger.info("Vibration is disabled by override.")
            return
    
        app_state.gpio.output(VIBRATE_GPIO_PIN, app_state.gpio.HIGH)
        logger.info("Vibration activated for Nova.")
    else:
        if app_state.gpio.input(VIBRATE_GPIO_PIN):
            logger.info("Vibration deactivated.")
        app_state.gpio.output(VIBRATE_GPIO_PIN, app_state.gpio.LOW)
        
