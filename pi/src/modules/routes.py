from flask import Flask, send_file, render_template_string, Response
import cv2
import datetime
from config import REPORT_DATA_DIR, LOG_FILE
import time
import modules.testing as test
from modules.state import app_state as state

# Flask App
app = Flask(__name__)

# Flask Route for Viewing Logs
@app.route('/', methods=['GET'])
def view_logs():
    return send_file(f"../{LOG_FILE}", mimetype="text/plain")

# Trigger test cases by sending test data frames
@app.route("/trigger_tests", methods=["GET"])
def trigger_tests():
    """
    Manually trigger all test cases for debugging purposes.
    """
    debug_frame = cv2.imread(f"{REPORT_DATA_DIR}/debug.jpg")  # Use a debug image for testing
    if debug_frame is None:
        return "Debug image not found.", 404

    # Mock data for triggering test cases
    test_detections = [
        {
            "dog": "Mila",
            "confidence": 80,  # Low confidence case
            "confidence_values": [80, 30, 10],  # Confidence array for all classes
            "message": "Low confidence for top class"
        },
        {
            "dog": "Nova",
            "confidence": 96,
            "confidence_values": [96, 30, 28],  # High 2nd/3rd confidence
            "message": "High confidence for 2nd/3rd class"
        },
        {
            "dog": "Mila",
            "confidence": 99,
            "confidence_values": [99, 85, 10],  # Rapid switch from Mila to Nova
            "message": "Rapid dog switching detected"
        },
    ]

    current_time = datetime.datetime.now()
    last_time = current_time - datetime.timedelta(seconds=1)

    # Simulate test cases
    for detection in test_detections:
        test.test1_rapid_switching(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
        )
        time.sleep(.5)

    # Simulate test cases
    for detection in test_detections:
        test.test2_low_confidence(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
        )
        time.sleep(.5)
    
    # Simulate test cases
    for detection in test_detections:
        test.test3_mixed_confidence(
            debug_frame,
            detection["dog"],
            detection["confidence"],
            detection["confidence_values"],
            datetime.datetime.now(),
            current_time - datetime.timedelta(seconds=1),
            "Nova" if detection["dog"] == "Mila" else "Mila"  # Alternate previous dog
            )
        time.sleep(.5)
    return "Test cases triggered. Check the JSON file."


@app.route('/simulate/<dog>', methods=['GET'])
def simulate_camera(dog):
    """
    Updates the simulated images for the specified dog type and renders the video stream.
    """
    global curr_frame, USE_DUMMY_IMAGES
    status_message = ''
    try:
        if dog == "off":
            USE_DUMMY_IMAGES = False
            status_message = "Now using live camera feed."
        else:
            USE_DUMMY_IMAGES = True
            directory = f"test-photos/{dog}-dummy"
            test.update_simulated_images(directory)
            status_message = f"Simulating Camera for {dog}"

        # Render HTML with video feed
        return render_template_string(
            """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Simulate Camera</title>
            </head>
            <body>
                <h1>{{status_message}}</h1>
                <img src="/video_feed" alt="Simulated Stream" style="max-width:100%; height:auto;">
            </body>
            </html>
            """,
            status_message=status_message
        )
    except ValueError as e:
        return str(e), 404


@app.route('/video_feed')
def video_feed():
    """
    Serve the current frame as an MJPEG stream.
    This implementation adds a small delay to avoid CPU overload and ensures thread-safe access to `curr_frame`.
    """
    print("serving video feed...")
    def generate():
        
        while True:
            # Check if curr_frame is available
            if state.curr_frame is not None:
                # Encode the current frame as JPEG
                _, buffer = cv2.imencode('.jpg', state.curr_frame)
                frame = buffer.tobytes()

                # Yield the frame as part of the multipart MJPEG stream
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # Introduce a short delay to reduce CPU usage and allow other threads to run
            time.sleep(0.1)

    # Return the MJPEG stream response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stream-reversed-logs')
def stream_reversed_logs():
    """
    Streams the log file content in reversed order (bottom to top) using Server-Sent Events (SSE).
    Continuously streams new updates.
    """
    def generate():
        last_position = 0  # Track file position
        while True:
            if not os.path.exists(LOG_FILE):
                yield "data: Log file not found.\n\n"
                break

            with open(LOG_FILE, 'r') as f:
                f.seek(0, os.SEEK_END)  # Move to end of file
                new_position = f.tell()

                # If the file has grown, read from the last position
                if new_position > last_position:
                    f.seek(last_position)
                    lines = f.readlines()
                    reversed_lines = lines[::-1]  # Reverse the lines
                    for line in reversed_lines:
                        yield f"data: {line.strip()}\n\n"

                last_position = new_position  # Update the last position
                time.sleep(1)  # Wait before checking for new content

    return Response(generate(), mimetype='text/event-stream')