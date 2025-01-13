import time
import datetime
import cv2
from config import CONFIDENCE_THRESHOLD, DETECTION_TIMEOUT, SAFETY_BUFFER, VISIT_TIMEOUT, VIBRATE_GPIO_PIN, REPORT_DATA_DIR
from modules.state import app_state as state  # Importing the shared app state object
from modules.logger import logger  # Importing the shared logger
from modules.image_processing import evaluate_frames, detect_motion
import modules.visits as visits
import modules.api as api
import modules.testing as testing
import modules.vibration as vibration
from modules.utils import repo_root
from modules.routes import app

def main():
    logger.info("Starting niñas...")
    state.cap = cv2.VideoCapture(0)  # Open the default camera
    state.cap.set(cv2.CAP_PROP_FPS, 5)  # Limit FPS for performance
    _, state.prev_frame = state.cap.read()  # Read the first frame

    last_detected_dog = None
    last_detected_time = datetime.datetime.now()
    last_motion_time = time.time()

    while True:
        # Capture the next frame
        if not state.use_dummy_images:
            _, state.curr_frame = state.cap.read()
        else:
            try:
                state.curr_frame = testing.get_simulated_image()
            except ValueError as e:
                logger.error(f"Simulation error: {e}")
                break

        current_time = datetime.datetime.now()

        # Evaluate and flip Mila's safety buffer status if needed
        new_safety_buffer_status = state.last_mila_end_time is not None and (current_time - state.last_mila_end_time).total_seconds() < SAFETY_BUFFER
        if new_safety_buffer_status != state.safety_buffer_active:
            state.safety_buffer_active = new_safety_buffer_status
            status = "ON" if state.safety_buffer_active else "OFF"
            logger.info(f"Mila's safety buffer is now {status}.")

        # Check for motion before running inference
        if detect_motion(state.prev_frame, state.curr_frame):
            logger.debug("Motion detected. Evaluating frame...")
            result = evaluate_frames()
            dog = result["class"]
            confidence_scores = result["confidence_scores"]
            confidence = confidence_scores[dog]

            # Set up test cases
            triggered_tests = []
            triggered_tests = testing.test2_low_confidence(confidence)

            # Continue processing if confidence is above threshold for a dog
            if confidence >= CONFIDENCE_THRESHOLD and dog != "None":
                
                # TEMP Record an image of the detected dog
                try:
                    filename = f"{repo_root}/{REPORT_DATA_DIR}/{dog}-{current_time.strftime('%Y%m%d%H%M%S')}.jpg"
                    cv2.imwrite(filename, state.curr_frame)
                except Exception as e:
                    logger.error(f"Failed to save image: {e}")

                detection_result = visits.register_detection(dog)
                logger.info(f"{detection_result}: {dog} with confidence {confidence:.2f}% {confidence_scores}")

                # Tests
                triggered_tests += testing.test1_rapid_switching(dog, current_time, last_detected_time, last_detected_dog)
                triggered_tests += testing.test3_mixed_confidence(dog, confidence_scores)
                if detection_result == "Nova suppressed":
                    triggered_tests.append("Nova suppressed due to Mila's buffer.")

                # Buzz event handling
                if detection_result == "Nova registered":
                    testing.add_frame_to_buzz_event(state.curr_frame, confidence_scores)
            
            elif confidence >= CONFIDENCE_THRESHOLD and dog == "None":
                vibration.control_vibration("off")

            # Save frame if any test case is triggered
            if triggered_tests:
                timestamp = current_time.strftime('%Y%m%d%H%M%S')
                testing.save_test_case(state.curr_frame, triggered_tests, confidence_scores, timestamp, dog)

            # Update the last motion time
            last_motion_time = time.time()

        # Finalize visit if no motion for DETECTION_TIMEOUT seconds
        if time.time() - last_motion_time > DETECTION_TIMEOUT:
            vibration.control_vibration("off")

        # Finalize visit if VISIT_TIMEOUT seconds have passed since last registered
        if state.current_visit["dog"] is not None and time.time() - state.current_visit["end_time"].timestamp() > VISIT_TIMEOUT:
            visits.finalize_visit()

        state.prev_frame = state.curr_frame  # Update the previous frame




# Entry point for the script
if __name__ == "__main__":
    import threading
    try:
        # Run Flask app in a separate thread with threading enabled
        threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, threaded=True)).start()
        main()
    except KeyboardInterrupt:
        if state.gpio:
            state.gpio.output(VIBRATE_GPIO_PIN, state.gpio.LOW)
            state.gpio.cleanup()
        logger.info("Exiting...")
        print("\nExiting...")