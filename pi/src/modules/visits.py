from modules.state import app_state
from modules.vibration import control_vibration
from modules.api import send_visit_to_api
from config import SAFETY_BUFFER
from modules.logger import logger
import datetime

def register_detection(dog):
    """
    Handles the registration of visits based on the detection of Mila or Nova.
    """
    now = datetime.datetime.now()

    if dog == "Mila":
        # Record Mila's detection and disable vibration
        app_state.last_mila_end_time = now  # Used for buffer suppression logic
        control_vibration("off")  # Turn off the buzzer
        update_visit(dog)
        return "Mila registered"

    elif dog == "Nova":
        # Suppress Nova detection if Mila's visit ended recently (within the buffer period)
        if app_state.safety_buffer_active:
            return "Nova suppressed due to Mila's buffer"

        # Register Nova's visit if buffer period has passed
        control_vibration("on")  # Turn on the buzzer
        update_visit(dog)
        return "Nova registered"

    else:
        # No detection
        return "No detection"
    

def update_visit(dog):
    """
    Updates the current visit with the current end time.
    """
    if (dog) == app_state.current_visit["dog"]:
        app_state.current_visit["end_time"] = datetime.datetime.now()
    else:
        finalize_visit()
        new_visit(dog)

def new_visit(dog):
    """
    Starts a new visit for the specified dog.
    """
    app_state.current_visit["dog"] = dog
    app_state.current_visit["start_time"] = datetime.datetime.now()
    app_state.current_visit["end_time"] = datetime.datetime.now()
    logger.info(f"Starting new visit for {dog}.")

def finalize_visit():
    """
    Finalizes the current visit and sends data to the API.
    """
    logger.info(f"{app_state.current_visit['dog']}'s visit complete. Dog: {app_state.current_visit['dog']}, Start: {app_state.current_visit['start_time']}, End: {app_state.current_visit['end_time']}")

    if app_state.current_visit["dog"] is not None:
        send_visit_to_api(
            app_state.current_visit["dog"],
            app_state.current_visit["start_time"],
            app_state.current_visit["end_time"]
        )
    # Reset the current visit
    app_state.current_visit = {"dog": None, "start_time": None, "end_time": None}